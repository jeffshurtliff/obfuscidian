# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.transactions
:Synopsis:          Internal staged publication and conservative explicit recovery
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     06 Oct 2026
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import stat
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.manifest import _verify_mirror
from obfuscidian.paths import (
    _directory_handle,
    _Fingerprint,
    _inspect_path,
    _is_link,
    _PathState,
    _recheck_path,
    _TargetRules,
    _validate_target_paths,
)


class _TransactionError(_OperationalError):
    """Report incomplete work without exposing paths, names, or plaintext.

    :param recovery_required: Whether ownership/artifacts remain for explicit recovery.
    """

    def __init__(self, *, recovery_required: bool) -> None:
        self.recovery_required = recovery_required
        super().__init__(
            'Transaction failed; retained artifacts require explicit recovery.'
            if recovery_required
            else 'Transaction failed; the previous payload was restored and artifacts retained.'
        )


@dataclass(frozen=True, repr=False)
class _TransactionPlan:
    """Hold private read-only observations; never a durable write capability."""

    source: Path
    destination: Path
    workspace_parent: Path
    lock: Path
    mirror: bool
    preserve_config: bool
    required_bytes: int
    fernet: Fernet | None = field(repr=False)
    destination_state: _PathState = field(repr=False)
    parent_state: _PathState = field(repr=False)
    source_state: _PathState = field(repr=False)
    target_rules: _TargetRules
    before: dict = field(repr=False)
    protected: dict = field(repr=False)


@dataclass(frozen=True, repr=False)
class _TransactionResult:
    """Return private locations and retention status for deliberate caller reporting."""

    workspace: Path
    rollback: Path
    plaintext: bool
    warnings: tuple[str, ...] = ()
    retained: bool = True


def _identity(info: os.stat_result) -> list[int]:
    """Record rename-stable identity and type/mode, without access/change times."""
    return [info.st_dev, info.st_ino, info.st_mode]


def _entry_exists(path: Path) -> bool:
    """Detect any entry, including broken links, without following it."""
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def _capture(path: Path, *, git_control: bool = False) -> dict:
    """Hash an inspected tree, rejecting links, special files and nested repositories.

    Git directories are identity-only protected controls and never traversed.
    Files use anchored no-follow reads with before/after stat comparisons.
    """
    info = path.lstat()
    if _is_link(info) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
        raise _ConfigurationError('Transaction entries must be regular files or directories without links.')
    state = _inspect_path(path, kind='directory' if stat.S_ISDIR(info.st_mode) else 'file')
    result: dict = {'identity': _identity(info)}
    if stat.S_ISREG(info.st_mode):
        digest = hashlib.sha256()
        with _directory_handle(_inspect_path(path.parent)) as handle:
            descriptor = os.open(
                path.name if handle is not None else path,
                os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0),
                dir_fd=handle,
            )
            try:
                with os.fdopen(descriptor, 'rb', closefd=False) as stream:
                    before = os.fstat(descriptor)
                    expected = _Fingerprint._from_stat(info)
                    if _is_link(before) or not expected._matches_open_stat(before):
                        raise _OperationalError('Transaction content changed before reading.')
                    for block in iter(lambda: stream.read(const.TRANSACTION_READ_BYTES), b''):
                        digest.update(block)
                    after = os.fstat(descriptor)
                    # Access time may change merely by reading.
                    if not expected._matches_open_stat(after) or _file_mark(before) != _file_mark(after):
                        raise _OperationalError('Transaction content changed while reading.')
            finally:
                os.close(descriptor)
        _recheck_path(state, content=True)
        result.update(size=info.st_size, mtime=info.st_mtime_ns, digest=digest.hexdigest())
    elif not git_control:
        with _directory_handle(state):
            children = {}
            for child in sorted(path.iterdir()):
                if child.name == const.GIT_METADATA:
                    raise _ConfigurationError('Replacement cannot remove nested repositories.')
                children[child.name] = _capture(child)
            result['children'] = children
        if set(children) != {child.name for child in path.iterdir()}:
            raise _OperationalError('Transaction namespace changed while reading.')
    _recheck_path(state)
    return result


def _file_mark(info: os.stat_result) -> tuple:
    """Compare stat content marks while allowing read-induced access time."""
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _protected_names(preserve_config: bool) -> set[str]:
    """Select root controls that publication must leave in place."""
    return {const.GIT_METADATA, const.GIT_IGNORE} | ({const.OBSIDIAN_DIRECTORY} if preserve_config else set())


def _observe(destination: Path, preserve_config: bool) -> tuple[dict, dict]:
    """Capture payload and protected controls separately without application writes."""
    if not _entry_exists(destination):
        return {}, {}
    payload, protected = {}, {}
    with _directory_handle(_inspect_path(destination)):
        for child in sorted(destination.iterdir()):
            if child.name == const.GIT_IGNORE:
                _inspect_path(child, kind='file')
            if preserve_config and child.name == const.OBSIDIAN_DIRECTORY:
                _inspect_path(child)
            target = protected if child.name in _protected_names(preserve_config) else payload
            target[child.name] = _capture(child, git_control=child.name == const.GIT_METADATA)
    return payload, protected


def _outside_git(path: Path) -> bool:
    """Recognize worktree markers without executing Git or reading its metadata."""
    return not any(_entry_exists(parent / const.GIT_METADATA) for parent in (path, *path.parents))


def _lock_name(destination: Path, rules: _TargetRules) -> str:
    """Use the caller's actual name comparison rules to lock destination aliases."""
    name = str(destination)
    if rules.normalization is not None:
        name = unicodedata.normalize(rules.normalization, name)
    if not rules.case_sensitive:
        name = name.casefold()
    return const.TRANSACTION_PREFIX + hashlib.sha256(os.fsencode(name)).hexdigest() + '.lock'


def _select_parent(source: Path, destination: Path) -> Path:
    """Choose the nearest existing same-device ancestor outside vaults/worktrees."""
    device = destination.parent.stat().st_dev
    for candidate in destination.parents:
        _inspect_path(candidate)
        if candidate.stat().st_dev != device:
            break
        if candidate == source or candidate.is_relative_to(source) or not _outside_git(candidate):
            continue
        # An ancestor shared with the source is safe: the new private child is a sibling.
        if os.access(candidate, os.W_OK | os.X_OK) and candidate.stat().st_mode & 0o222:
            return candidate
    raise _ConfigurationError('No writable same-filesystem staging location outside vaults and Git worktrees is available.')


def _plan_transaction(
    source: Path,
    destination: Path,
    *,
    mirror: bool = False,
    fernet: Fernet | None = None,
    preserve_config: bool = False,
    required_bytes: int = 0,
    allow_pending: bool = False,
    target_rules: _TargetRules | None = None,
) -> _TransactionPlan:
    """Perform read-only preflight, also suitable for dry run and pending inspection.

    :param source: Existing origin or validated encrypted source, read-only here.
    :param destination: Existing directory or missing final component.
    :param mirror: Require authenticated managed layout for an existing mirror.
    :param fernet: Key context required for mirror validation.
    :param preserve_config: Protect root Obsidian settings during restore.
    :param required_bytes: Caller estimate plus transaction metadata reserve is checked.
    :param allow_pending: Permit inspection for explicit recovery, without repairing.
    :param target_rules: Caller-supplied actual target naming rules; required.
    :returns: Observations rechecked by execution; no locks or paths are created.
    :raises _ConfigurationError: Paths, layout, platform, or estimates are unsafe.
    :raises _OperationalError: Space/access/state or pending ownership prevents work.
    """
    try:
        if target_rules is None:
            raise _ConfigurationError('Actual target filesystem naming rules are required.')
        source_state = _inspect_path(source)
        state = _inspect_path(destination, allow_missing=True)
        if destination == Path(destination.anchor) or source == destination:
            raise _ConfigurationError('Replacement requires separate non-root locations.')
        if source.is_relative_to(destination) or destination.is_relative_to(source):
            raise _ConfigurationError('Source and destination must not overlap.')
        if type(required_bytes) is not int or required_bytes < 0:
            raise _ConfigurationError('Staging byte estimates must be nonnegative integers.')
        if mirror and (fernet is None or preserve_config):
            raise _ConfigurationError('Mirror publication requires a key and cannot preserve restore settings.')
        parent = _select_parent(source, destination)
        parent_state = _inspect_path(parent)
        if state.exists and destination.stat().st_dev != parent.stat().st_dev:
            raise _ConfigurationError('Destination and staging must share one filesystem.')
        if not os.access(destination if state.exists else destination.parent, os.W_OK | os.X_OK):
            raise _OperationalError('Destination is not writable.')
        if (
            len(
                json.dumps(
                    {'id': '0' * 32, 'destination': str(destination), 'original_exists': True, 'baseline_digest': '0' * 64}
                ).encode()
            )
            > const.TRANSACTION_LOCK_BYTES
        ):
            raise _ConfigurationError('Destination exceeds the bounded ownership record limit.')
        lock_name = _lock_name(destination, target_rules)
        pending = [ancestor / lock_name for ancestor in destination.parents if _entry_exists(ancestor / lock_name)]
        if pending:
            if not allow_pending or len(pending) != 1:
                raise _OperationalError('Destination has pending ownership; explicit recovery is required.')
            parent = pending[0].parent
            parent_state = _inspect_path(parent)
        lock = parent / lock_name
        if mirror and state.exists and not allow_pending:
            entries = {entry.name for entry in destination.iterdir()}
            if const.MANAGED_DIRECTORY in entries:
                _verify_mirror(destination, fernet)
            elif entries - _protected_names(False):
                raise _ConfigurationError('Unmanaged mirror destinations cannot be replaced.')
        before, protected = _observe(destination, preserve_config)
        if mirror and state.exists and const.MANAGED_DIRECTORY in before and not allow_pending:
            _verify_mirror(destination, fernet)
            if _observe(destination, preserve_config) != (before, protected):
                raise _OperationalError('Mirror changed during transaction preflight.')
        if shutil.disk_usage(parent).free < required_bytes + const.TRANSACTION_RESERVE_BYTES:
            raise _OperationalError('Insufficient free space for staging and retained recovery data.')
        _recheck_path(source_state)
        _recheck_path(state)
        return _TransactionPlan(
            source,
            destination,
            parent,
            lock,
            mirror,
            preserve_config,
            required_bytes,
            fernet,
            state,
            parent_state,
            source_state,
            target_rules,
            before,
            protected,
        )
    except OSError:
        raise _OperationalError('Transaction preflight failed; check permissions and space.') from None


def _confirm_action(*, yes: bool, non_interactive: bool, prompt: Callable[[], bool] | None = None) -> None:
    """Require explicit affirmative consent; non-interactive never implies yes.

    :param yes: Explicit caller consent for replacement or recovery.
    :param non_interactive: Prohibit prompting.
    :param prompt: Caller-owned terminal-aware affirmative prompt.
    :raises _OperationalError: Consent was unavailable, declined, or interrupted by EOF.
    """
    if yes:
        return
    if non_interactive or prompt is None:
        raise _OperationalError('Explicit confirmation is required; non-interactive does not imply yes.')
    try:
        if prompt() is not True:
            raise _OperationalError('Confirmation declined; no transaction was started.')
    except EOFError:
        raise _OperationalError('Confirmation unavailable; no transaction was started.') from None


def _sync_directory(path: Path) -> None:
    """Flush directory entries through a protected POSIX handle."""
    with _directory_handle(_inspect_path(path)) as descriptor:
        os.fsync(descriptor)


def _checkpoint(workspace: Path, journal: dict) -> None:
    """Persist complete write-ahead state via exclusive write, fsync, rename, fsync."""
    if journal.get('workspace_identity') != _identity(workspace.lstat()):
        raise _OperationalError('Transaction workspace identity changed; artifacts are preserved.')
    for label, identity in journal.get('containers', {}).items():
        path = workspace / (const.TRANSACTION_STAGE if label == 'stage' else const.TRANSACTION_ROLLBACK)
        if _identity(path.lstat()) != identity:
            raise _OperationalError('Transaction container identity changed; artifacts are preserved.')
    data = json.dumps(journal, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()
    if len(data) > const.TRANSACTION_JOURNAL_BYTES:
        raise _OperationalError('Transaction journal exceeds its bounded metadata limit.')
    temporary = workspace / ('journal-' + secrets.token_hex(16) + '.tmp')
    with _directory_handle(_inspect_path(workspace)) as handle:
        descriptor = os.open(temporary.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=handle)
        try:
            with os.fdopen(descriptor, 'wb', closefd=False) as stream:
                if stream.write(data) != len(data):
                    raise _OperationalError('Incomplete journal write; artifacts are preserved.')
                stream.flush()
                os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary.name, const.TRANSACTION_JOURNAL, src_dir_fd=handle, dst_dir_fd=handle)
        os.fsync(handle)


def _lock_descriptor(plan: _TransactionPlan, *, recovery: bool) -> int:
    """Acquire an OS lifetime lock; retained pathname alone blocks ordinary writes."""
    if os.name != 'posix':
        raise _ConfigurationError('Transaction writes require POSIX locking/private modes; native Windows support is deferred.')
    import fcntl

    _recheck_path(plan.parent_state)
    with _directory_handle(plan.parent_state) as handle:
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
        descriptor = os.open(plan.lock.name, flags | (0 if recovery else os.O_CREAT | os.O_EXCL), 0o600, dir_fd=handle)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise _OperationalError('Ownership record is unsafe; artifacts are preserved.')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if _identity(os.stat(plan.lock.name, dir_fd=handle, follow_symlinks=False)) != _identity(info):
                raise _OperationalError('Ownership identity changed; artifacts are preserved.')
            if not recovery:
                os.fsync(handle)
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise


def _release_lock(plan: _TransactionPlan, descriptor: int) -> tuple[str, ...]:
    """Remove only the held lock identity, while keeping OS ownership until unlink."""
    with _directory_handle(plan.parent_state) as handle:
        info = os.stat(plan.lock.name, dir_fd=handle, follow_symlinks=False)
        if _identity(info) != _identity(os.fstat(descriptor)):
            raise _OperationalError('Ownership changed; recovery remains blocked.')
        os.unlink(plan.lock.name, dir_fd=handle)
        try:
            os.fsync(handle)
        except OSError:
            # Payload and terminal journal are already durable. Unlink is the final
            # completion point; failure to flush it may resurrect pending ownership
            # after power loss, but cannot authorize a partial payload as success.
            return ('Ownership removal durability is unconfirmed; recovery may be required after restart.',)
    return ()


def _move(source: Path, destination: Path, expected: dict) -> None:
    """Rename an unchanged entry into an absent target using anchored parent handles."""
    if _capture(source) != expected or _entry_exists(destination):
        raise _OperationalError('Publication entry changed or target appeared; artifacts are preserved.')
    source_parent, target_parent = _inspect_path(source.parent), _inspect_path(destination.parent)
    with _directory_handle(source_parent) as source_handle, _directory_handle(target_parent) as target_handle:
        if _capture(source) != expected or _entry_exists(destination):
            raise _OperationalError('Publication entry changed at rename; artifacts are preserved.')
        os.rename(source.name, destination.name, src_dir_fd=source_handle, dst_dir_fd=target_handle)
        os.fsync(source_handle)
        os.fsync(target_handle)
    if _capture(destination) != expected:
        raise _OperationalError('Published entry changed; artifacts are preserved.')


def _check_destination(plan: _TransactionPlan, expected_payload: dict) -> None:
    """Recheck destination identity, full payload, and protected controls."""
    _recheck_path(plan.destination_state)
    payload, protected = _observe(plan.destination, plan.preserve_config)
    if payload != expected_payload or protected != plan.protected:
        raise _OperationalError('Destination changed; publication/recovery is blocked and artifacts are preserved.')


def _tree_names(entries: dict, prefix: str = '') -> list[str]:
    """List every recorded target name, including preserved ancestors."""
    result = []
    for name, value in entries.items():
        path = prefix + name
        result.append(path)
        if 'children' in value:
            result.extend(_tree_names(value['children'], path + '/'))
    return result


def _sync_tree(root: Path) -> None:
    """Flush validated staged bytes and directories before any destination rename."""
    _inspect_path(root)
    for path in root.iterdir():
        if path.is_dir():
            _sync_tree(path)
        else:
            state = _inspect_path(path, kind='file')
            with _directory_handle(_inspect_path(path.parent)) as handle:
                descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=handle)
                try:
                    if _identity(os.fstat(descriptor)) != _identity(path.lstat()):
                        raise _OperationalError('Staged identity changed before flush.')
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            _recheck_path(state, content=True)
    _sync_directory(root)


def _execute_transaction(
    plan: _TransactionPlan,
    build: Callable[[Path], None],
    verify: Callable[[Path], None],
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
    dry_run: bool = False,
    prepublish: Callable[[], None] | None = None,
    retain_rollback: bool = True,
) -> _TransactionResult | None:
    """Stage, completely verify, then journal and publish an internal payload.

    Builder and verifier are trusted internal orchestration callbacks, never
    loaded from vault content. Restore callers must authenticate every required
    source object before calling this primitive. Mirror validation is mandatory
    in addition to the caller verifier.

    :param plan: Read-only preflight observations and caller resource estimate.
    :param build: Populate only the supplied private empty staging directory.
    :param verify: Validate the entire proposal; returning authorizes publication.
    :param yes: Explicit replacement confirmation.
    :param non_interactive: Never invoke the optional prompt.
    :param prompt: Trusted terminal-aware caller confirmation.
    :param dry_run: Recheck observations only, without builder, prompt, or artifacts.
    :param prepublish: Recheck caller-owned source content immediately before publication.
    :param retain_rollback: Keep recovery data after success; merge may clean its proven workspace.
    :returns: Private rollback locations and retention status, or no result for dry run.
    :raises _TransactionError: Failed work was rolled back or remains blocked.
    :raises KeyboardInterrupt: Interrupt after attempted conservative rollback.
    :raises _OperationalError: Preflight/confirmation failed before ownership.
    """
    _recheck_path(plan.parent_state)
    _recheck_path(plan.source_state)
    _check_destination(plan, plan.before)
    if any(_entry_exists(parent / plan.lock.name) for parent in plan.destination.parents):
        raise _OperationalError('Destination has pending ownership; explicit recovery is required.')
    if dry_run:
        return None
    _confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    descriptor = None
    workspace = None
    journal = None
    try:
        if shutil.disk_usage(plan.workspace_parent).free < plan.required_bytes + const.TRANSACTION_RESERVE_BYTES:
            raise _OperationalError('Insufficient space before transaction ownership.')
        descriptor = _lock_descriptor(plan, recovery=False)
        transaction_id = secrets.token_hex(16)
        workspace = plan.workspace_parent / (const.TRANSACTION_PREFIX + transaction_id)
        # Persist location before creating it: a crash here leaves recognizable ownership.
        record = json.dumps(
            {
                'id': transaction_id,
                'destination': str(plan.destination),
                'original_exists': plan.destination_state.exists,
                'baseline_digest': _metadata_digest({'before': plan.before, 'protected': plan.protected}),
            }
        ).encode()
        if os.write(descriptor, record) != len(record):
            raise _OperationalError('Incomplete ownership write; artifacts are preserved.')
        os.fsync(descriptor)
        with _directory_handle(plan.parent_state) as handle:
            os.mkdir(workspace.name, 0o700, dir_fd=handle)
            os.fsync(handle)
        journal = {
            'version': const.TRANSACTION_VERSION,
            'id': transaction_id,
            'destination': str(plan.destination),
            'destination_identity': _identity(plan.destination.lstat()) if plan.destination_state.exists else None,
            'original_exists': plan.destination_state.exists,
            'workspace_identity': _identity(workspace.lstat()),
            'parent_identity': _identity(plan.workspace_parent.lstat()),
            'ancestors': {
                str(p): [f.device, f.inode, f.mode] for p, f in plan.destination_state.components if p != plan.destination
            },
            'mirror': plan.mirror,
            'preserve_config': plan.preserve_config,
            'before': plan.before,
            'protected': plan.protected,
            'after': None,
            'phase': 'preparing',
        }
        _checkpoint(workspace, journal)
        stage, rollback = workspace / const.TRANSACTION_STAGE, workspace / const.TRANSACTION_ROLLBACK
        workspace_state = _inspect_path(workspace)
        if _identity(workspace.lstat()) != journal['workspace_identity']:
            raise _OperationalError('Transaction workspace changed before staging creation.')
        with _directory_handle(workspace_state) as handle:
            os.mkdir(stage.name, 0o700, dir_fd=handle)
            os.mkdir(rollback.name, 0o700, dir_fd=handle)
            os.fsync(handle)
        journal['containers'] = {'stage': _identity(stage.lstat()), 'rollback': _identity(rollback.lstat())}
        _checkpoint(workspace, journal)
        build(stage)
        proposal = _observe(stage, False)
        verify(stage)
        if plan.mirror:
            _verify_mirror(stage, plan.fernet)
        after, staged_protected = _observe(stage, False)
        if (after, staged_protected) != proposal:
            raise _OperationalError('Staging changed during complete proposal validation.')
        if staged_protected or set(after) & _protected_names(plan.preserve_config):
            raise _ConfigurationError('Staging cannot replace protected root controls.')
        _validate_target_paths(
            (*_tree_names(after), *_tree_names(plan.protected)),
            plan.target_rules,
            destination=plan.destination,
        )
        _sync_tree(stage)
        if _observe(stage, False)[0] != after:
            raise _OperationalError('Staging changed during validation.')
        journal.update(after=after, phase='ready')
        _checkpoint(workspace, journal)
        _recheck_path(plan.source_state)
        _check_destination(plan, plan.before)
        if plan.mirror and const.MANAGED_DIRECTORY in plan.before:
            _verify_mirror(plan.destination, plan.fernet)
            _check_destination(plan, plan.before)
        if prepublish is not None:
            prepublish()
        if not plan.destination_state.exists:
            # Journal intent before root creation; uncertain identity is preserved on recovery.
            journal['phase'] = 'creating-root'
            _checkpoint(workspace, journal)
            with _directory_handle(_inspect_path(plan.destination.parent)) as handle:
                os.mkdir(plan.destination.name, 0o700, dir_fd=handle)
                os.fsync(handle)
            journal['destination_identity'] = _identity(plan.destination.lstat())
            plan = _with_destination_state(plan)
            _checkpoint(workspace, journal)
        if not _outside_git(plan.workspace_parent):
            raise _OperationalError('Staging location entered a Git worktree; artifacts are preserved.')
        journal['phase'] = 'publishing'
        _checkpoint(workspace, journal)
        current = dict(plan.before)
        for name, expected in plan.before.items():
            _check_destination(plan, current)
            _checkpoint(workspace, journal)
            _move(plan.destination / name, rollback / name, expected)
            del current[name]
            _checkpoint(workspace, journal)
        for name, expected in after.items():
            _check_destination(plan, current)
            _checkpoint(workspace, journal)
            _move(stage / name, plan.destination / name, expected)
            current[name] = expected
            _checkpoint(workspace, journal)
        _check_destination(plan, after)
        if plan.mirror:
            _verify_mirror(plan.destination, plan.fernet)
        journal['phase'] = 'published'
        _checkpoint(workspace, journal)
        warnings = _release_lock(plan, descriptor)
        result = _TransactionResult(workspace, rollback, not plan.mirror, warnings)
    except BaseException as error:
        if descriptor is None:
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise _OperationalError('Cannot obtain exclusive transaction ownership; no payload was published.') from None
        recovered = False
        if workspace is not None and journal is not None:
            try:
                # Use only durable disk state, including failures between rename/checkpoint.
                _recover_owned(plan, workspace, descriptor)
                recovered = True
            except (
                OSError,
                _ConfigurationError,
                _OperationalError,
                ValueError,
                KeyError,
                TypeError,
                RecursionError,
                MemoryError,
            ):
                pass
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            if not recovered:
                error.add_note('Transaction artifacts retained; explicit recovery is required.')
            raise
        raise _TransactionError(recovery_required=not recovered) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if not retain_rollback and not result.warnings:
        try:
            _cleanup_published(plan, workspace, journal)
        except (OSError, _ConfigurationError, _OperationalError, ValueError, KeyError, TypeError, RecursionError, MemoryError):
            return _TransactionResult(
                workspace,
                rollback,
                not plan.mirror,
                ('Snapshot published; temporary recovery cleanup incomplete or durability unconfirmed.',),
                retained=_entry_exists(workspace),
            )
        return _TransactionResult(workspace, rollback, not plan.mirror, retained=False)
    return result


def _remove_captured(path: Path, expected: dict) -> None:
    """Remove only an unchanged captured entry, anchored through no-follow handles.

    Recheck the complete tree before the first unlink and every descendant at
    removal. Partial cleanup may leave proven data; uncertain data is never
    recursively swept. This is best effort against same-authority writers.
    """
    if _capture(path) != expected:
        raise _OperationalError('Temporary recovery data changed; remaining artifacts are retained.')
    state = _inspect_path(path, kind='directory' if 'children' in expected else 'file')
    with _directory_handle(_inspect_path(path.parent)) as parent:
        if 'children' not in expected:
            if _capture(path) != expected:
                raise _OperationalError('Temporary recovery file changed; artifacts are retained.')
            os.unlink(path.name, dir_fd=parent)
        else:
            with _directory_handle(state):
                # Keep the terminal journal until other owned entries are removed.
                for name in sorted(expected['children'], key=lambda name: (name == const.TRANSACTION_JOURNAL, name)):
                    _remove_captured(path / name, expected['children'][name])
                _recheck_path(state)
                if any(path.iterdir()):
                    raise _OperationalError('Unexpected temporary data appeared; artifacts are retained.')
            os.rmdir(path.name, dir_fd=parent)
        os.fsync(parent)


def _cleanup_published(plan: _TransactionPlan, workspace: Path, journal: dict) -> None:
    """Clean only this successfully published operation after ownership release.

    Compare complete namespaces, identities and bytes against the publication
    journal before removing anything. Never scan or prune older workspaces.
    Cleanup failures cannot trigger rollback of an already published snapshot.
    """
    if _entry_exists(plan.lock) or not _outside_git(plan.workspace_parent):
        raise _OperationalError('Cleanup ownership or location is uncertain; artifacts are retained.')
    _check_destination(plan, journal['after'])
    with _directory_handle(_inspect_path(workspace)):
        if {path.name for path in workspace.iterdir()} != {
            const.TRANSACTION_STAGE,
            const.TRANSACTION_ROLLBACK,
            const.TRANSACTION_JOURNAL,
        }:
            raise _OperationalError('Unexpected temporary recovery entries; artifacts are retained.')
    if _read_private_json(workspace / const.TRANSACTION_JOURNAL, const.TRANSACTION_JOURNAL_BYTES) != journal:
        raise _OperationalError('Published journal changed; artifacts are retained.')
    captured = _capture(workspace)
    children = captured.get('children', {})
    if (
        captured['identity'] != journal['workspace_identity']
        or set(children) != {const.TRANSACTION_STAGE, const.TRANSACTION_ROLLBACK, const.TRANSACTION_JOURNAL}
        or children[const.TRANSACTION_STAGE] != {'identity': journal['containers']['stage'], 'children': {}}
        or children[const.TRANSACTION_ROLLBACK] != {'identity': journal['containers']['rollback'], 'children': journal['before']}
    ):
        raise _OperationalError('Temporary recovery namespace changed; artifacts are retained.')
    _remove_captured(workspace, captured)


def _with_destination_state(plan: _TransactionPlan) -> _TransactionPlan:
    """Refresh only the root created by this transaction, keeping prior observations."""
    from dataclasses import replace

    return replace(plan, destination_state=_inspect_path(plan.destination))


def _metadata_digest(value: dict) -> str:
    """Bind the original destination observation to its separately held ownership record."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _read_private_json(path: Path, limit: int) -> dict:
    """Read bounded private metadata without following links or accepting duplicate keys."""
    state = _inspect_path(path, kind='file')
    info = path.lstat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > limit:
        raise _OperationalError('Recovery metadata ownership or size is unsafe; artifacts are preserved.')
    with _directory_handle(_inspect_path(path.parent)) as handle:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=handle)
        try:
            if _identity(os.fstat(descriptor)) != _identity(info):
                raise _OperationalError('Recovery metadata identity changed.')
            with os.fdopen(descriptor, 'rb', closefd=False) as stream:
                data = stream.read(limit + 1)
        finally:
            os.close(descriptor)
    _recheck_path(state, content=True)

    def unique(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate recovery fields.')
            result[key] = value
        return result

    result = json.loads(data, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError('Invalid recovery metadata.')
    return result


def _recover_owned(plan: _TransactionPlan, workspace: Path, descriptor: int) -> _TransactionResult:
    """Prove all payload locations before conservative inverse moves; delete no data."""
    if not _outside_git(plan.workspace_parent):
        raise _OperationalError('Recovery artifacts entered a Git worktree; artifacts are preserved.')
    record = _read_private_json(plan.lock, const.TRANSACTION_LOCK_BYTES)
    journal = _read_private_json(workspace / const.TRANSACTION_JOURNAL, const.TRANSACTION_JOURNAL_BYTES)
    if (
        journal.get('version') != const.TRANSACTION_VERSION
        or journal.get('id') != record.get('id')
        or journal.get('destination') != str(plan.destination)
        or record.get('destination') != str(plan.destination)
        or journal.get('workspace_identity') != _identity(workspace.lstat())
        or journal.get('parent_identity') != _identity(plan.workspace_parent.lstat())
        or journal.get('mirror') != plan.mirror
        or journal.get('preserve_config') != plan.preserve_config
    ):
        raise _OperationalError('Recovery ownership/state mismatch; artifacts are preserved.')
    if workspace.stat().st_uid != os.getuid() or workspace.stat().st_mode & 0o077:
        raise _OperationalError('Recovery directory is not private; artifacts are preserved.')
    for path, identity in journal['ancestors'].items():
        state = _inspect_path(Path(path))
        if _identity(state.path.lstat()) != identity:
            raise _OperationalError('Recovery ancestor identity changed; artifacts are preserved.')
    if (
        type(journal.get('original_exists')) is not bool
        or journal['original_exists'] != record.get('original_exists')
        or _metadata_digest({'before': journal['before'], 'protected': journal['protected']}) != record.get('baseline_digest')
        or journal.get('phase') not in const.TRANSACTION_PHASES
    ):
        raise _OperationalError('Recovery baseline/state was modified; artifacts are preserved.')
    expected_root = journal['destination_identity']
    if expected_root is None:
        if _entry_exists(plan.destination):
            raise _OperationalError('Uncertain created destination; artifacts are preserved.')
    elif not _entry_exists(plan.destination):
        if journal['phase'] != 'removing-root' or journal['original_exists']:
            raise _OperationalError('Recovery destination is missing; artifacts are preserved.')
    elif _identity(plan.destination.lstat()) != expected_root:
        raise _OperationalError('Recovery destination identity changed; artifacts are preserved.')
    before, after = journal['before'], journal['after']
    payload, protected = _observe(plan.destination, plan.preserve_config)
    if protected != journal['protected']:
        raise _OperationalError('Protected destination controls changed; artifacts are preserved.')
    stage, rollback = workspace / const.TRANSACTION_STAGE, workspace / const.TRANSACTION_ROLLBACK
    if after is None:
        # No publication was authorized. Preserve incomplete/uncertain staged data in place.
        if payload != before:
            raise _OperationalError('Destination changed before publication; artifacts are preserved.')
        if plan.mirror and const.MANAGED_DIRECTORY in before:
            _verify_mirror(plan.destination, plan.fernet)
    else:
        for label, path in (('stage', stage), ('rollback', rollback)):
            if journal.get('containers', {}).get(label) != _identity(path.lstat()):
                raise _OperationalError('Recovery container identity changed; artifacts are preserved.')
        staged, stage_controls = _observe(stage, False)
        saved, saved_controls = _observe(rollback, False)
        if stage_controls or saved_controls:
            raise _OperationalError('Unexpected recovery controls; artifacts are preserved.')
        # Each recorded old/new entry must exist exactly once in an authorized location.
        old_locations, new_locations = {}, {}
        for name, expected in before.items():
            matches = [
                root for root, observed in ((plan.destination, payload), (rollback, saved)) if observed.get(name) == expected
            ]
            if len(matches) != 1:
                raise _OperationalError('Previous payload changed or is missing; artifacts are preserved.')
            old_locations[name] = matches[0]
        for name, expected in after.items():
            matches = [
                root for root, observed in ((plan.destination, payload), (stage, staged)) if observed.get(name) == expected
            ]
            if len(matches) != 1:
                raise _OperationalError('Proposed payload changed or is missing; artifacts are preserved.')
            new_locations[name] = matches[0]
        for observed, _root, allowed in (
            (
                payload,
                plan.destination,
                {
                    **{n: before[n] for n, p in old_locations.items() if p == plan.destination},
                    **{n: after[n] for n, p in new_locations.items() if p == plan.destination},
                },
            ),
            (saved, rollback, {n: before[n] for n, p in old_locations.items() if p == rollback}),
            (staged, stage, {n: after[n] for n, p in new_locations.items() if p == stage}),
        ):
            if observed != allowed:
                raise _OperationalError('Unexpected or modified recovery payload; artifacts are preserved.')
        # All uncertainty checks precede the first inverse mutation.
        if plan.mirror:
            for root in set(old_locations.values()) | set(new_locations.values()):
                _verify_mirror(root, plan.fernet)
        journal['phase'] = 'recovering'
        _checkpoint(workspace, journal)
        for name, root in new_locations.items():
            if root == plan.destination:
                _recheck_path(plan.destination_state)
                _move(root / name, stage / name, after[name])
                _checkpoint(workspace, journal)
        for name, root in old_locations.items():
            if root == rollback:
                _recheck_path(plan.destination_state)
                _move(root / name, plan.destination / name, before[name])
                _checkpoint(workspace, journal)
        if _observe(plan.destination, plan.preserve_config) != (before, journal['protected']):
            raise _OperationalError('Recovery is incomplete; artifacts are preserved.')
    if not journal['original_exists'] and _entry_exists(plan.destination):
        if _observe(plan.destination, plan.preserve_config) != ({}, {}):
            raise _OperationalError('Created destination is not empty; artifacts are preserved.')
        journal['phase'] = 'removing-root'
        _checkpoint(workspace, journal)
        with _directory_handle(_inspect_path(plan.destination.parent)) as handle:
            if _identity(plan.destination.lstat()) != journal['destination_identity']:
                raise _OperationalError('Created root identity changed; artifacts are preserved.')
            os.rmdir(plan.destination.name, dir_fd=handle)
            os.fsync(handle)
        journal['destination_identity'] = None
    journal['phase'] = 'recovered'
    _checkpoint(workspace, journal)
    warnings = _release_lock(plan, descriptor)
    return _TransactionResult(workspace, rollback, not plan.mirror, warnings)


def _recover_transaction(
    plan: _TransactionPlan,
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
) -> _TransactionResult:
    """Explicitly restore previous complete state, refusing live/uncertain ownership.

    No stale lock is removed by age or PID. OS ownership must be obtainable and
    private bounded journal identities, hashes, namespaces and controls must
    agree. Unknown or modified artifacts are retained without inverse writes.
    Even known proposed data is retained rather than deleted during recovery.

    :param plan: Read-only preflight with allow_pending, matching the original mode.
    :param yes: Explicit recovery consent (required in non-interactive operation).
    :param non_interactive: Prohibit prompts.
    :param prompt: Caller-owned terminal-aware affirmative recovery prompt.
    :returns: Retained locations after demonstrably complete recovery.
    :raises _TransactionError: Ownership, state, I/O, or content cannot be proven.
    """
    _confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    descriptor = None
    try:
        descriptor = _lock_descriptor(plan, recovery=True)
        record = _read_private_json(plan.lock, const.TRANSACTION_LOCK_BYTES)
        transaction_id = record.get('id')
        if (
            not isinstance(transaction_id, str)
            or len(transaction_id) != 32
            or any(c not in '0123456789abcdef' for c in transaction_id)
        ):
            raise _OperationalError('Invalid recovery ownership record; artifacts are preserved.')
        workspace = plan.workspace_parent / (const.TRANSACTION_PREFIX + transaction_id)
        _inspect_path(workspace)
        return _recover_owned(plan, workspace, descriptor)
    except (OSError, ValueError, KeyError, TypeError, RecursionError, MemoryError, _ConfigurationError, _OperationalError):
        raise _TransactionError(recovery_required=True) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.git_restore
:Synopsis:          Validated additive restore into an isolated uncommitted Git worktree
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil

# Git plumbing uses validated argument lists and no shell.
import subprocess  # nosec B404
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from obfuscidian import backup, manifest, paths, restore, verification
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.errors import _ConfigurationError, _OperationalError


@dataclass(frozen=True)
class _BaseFile:
    """Describe a validated regular Git blob without retaining its contents."""

    path: str
    oid: str
    size: int
    executable: bool


@dataclass(frozen=True, repr=False)
class _MergePlan:
    """Keep read-only Git and authenticated restore observations."""

    executable: str
    origin: Path
    gitdir: Path
    common: Path
    output: Path
    branch: str
    base_branch: str
    base_oid: str
    head: bytes
    head_control: dict
    index: dict
    origin_tree: tuple[dict, dict]
    origin_state: paths._PathState
    git_state: paths._PathState
    common_state: paths._PathState
    configurations: tuple[tuple[Path, dict | None], ...]
    reconstruction: restore._RestorePlan
    base_files: tuple[_BaseFile, ...]
    base_directories: tuple[str, ...]


@dataclass(frozen=True)
class _MergeResult:
    """Report an uncommitted additive worktree and sensitive retention."""

    output: Path
    branch: str
    ignored: tuple[str, ...]
    warnings: tuple[str, ...]
    retained: tuple[Path, ...]


class _MergeFailure(_OperationalError):
    """Report failure with opt-in locations for conservative manual recovery."""

    def __init__(self, message: str, plan: _MergePlan, retained: tuple[Path, ...]) -> None:
        super().__init__(message)
        self.output = plan.output
        self.branch = plan.branch
        self.retained = retained


def _git(executable: str, root: Path, *arguments: str, accepted: tuple[int, ...] = (0,)) -> bytes:
    """Run local plumbing with no inherited Git selectors, hooks, helpers or lazy fetching.

    Git diagnostics are deliberately discarded: they may contain private paths.
    No checkout, status, diff or attribute conversion is used internally, so
    repository clean/smudge/process filters and diff drivers cannot execute.
    """
    environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    environment.update(
        GIT_CONFIG_NOSYSTEM='1',
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT='0',
        GIT_OPTIONAL_LOCKS='0',
        GIT_NO_LAZY_FETCH='1',
    )
    try:
        # Resolved Git, validated refs/absolute paths, no shell or checkout helpers.
        result = subprocess.run(  # nosec B603
            [
                executable,
                '-c',
                'core.hooksPath=' + os.devnull,
                '-c',
                'core.fsmonitor=false',
                '-c',
                'core.untrackedCache=false',
                '-c',
                'core.sparseCheckout=false',
                '-c',
                'core.splitIndex=false',
                '-c',
                'submodule.recurse=false',
                '-c',
                'gc.auto=0',
                '-c',
                'maintenance.auto=false',
                '-C',
                str(root),
                *arguments,
            ],
            env=environment,
            capture_output=True,
            check=False,
        )
    except OSError:
        raise _OperationalError('Git could not run; check Git availability and access.') from None
    if result.returncode not in accepted:
        raise _OperationalError('Git validation or worktree operation failed; check repository, refs and access.')
    return result.stdout


def _decode(data: bytes) -> str:
    """Decode Git names strictly rather than silently substituting names."""
    try:
        return data.decode('utf-8')
    except UnicodeError:
        raise _ConfigurationError('Git names must be representable as UTF-8 restore paths.') from None


def _text(data: bytes) -> str:
    """Decode line-oriented Git scalar output without retaining its newline."""
    return _decode(data).removesuffix('\n')


def _ref(executable: str, origin: Path, branch: str) -> str:
    """Resolve exactly a local branch, never a tag, remote, option or expression."""
    if not branch:
        raise _ConfigurationError('Select a valid local --base-branch.')
    try:
        _git(executable, origin, 'check-ref-format', 'refs/heads/' + branch)
        _git(executable, origin, 'check-ref-format', '--branch', branch)
        return _text(_git(executable, origin, 'rev-parse', '--verify', 'refs/heads/' + branch + '^{commit}'))
    except _OperationalError:
        raise _ConfigurationError('The selected --base-branch must be an existing local committed branch.') from None


def _tree(executable: str, origin: Path, oid: str) -> tuple[tuple[_BaseFile, ...], tuple[str, ...], bytes]:
    """Read regular committed blobs, rejecting links, gitlinks and unsafe controls."""
    files, directories, index = [], set(), []
    for entry in _git(executable, origin, 'ls-tree', '-r', '-z', oid).split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.split()
        relative = _decode(name)
        parts = paths._validate_relative_path(relative)
        compared = [unicodedata.normalize('NFC', p).casefold() for p in parts]
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise _ConfigurationError('Merge restore refuses symlinks, submodules and non-regular Git tree entries.')
        if const.GIT_METADATA in compared or '.gitmodules' in compared:
            raise _ConfigurationError('Merge restore refuses nested Git controls and submodule layouts.')
        if compared[0] == const.GIT_IGNORE and len(parts) > 1:
            raise _ConfigurationError('Git base root .gitignore must be a regular file.')
        if compared[0] in (const.GIT_IGNORE, const.OBSIDIAN_DIRECTORY) and compared[0] != parts[0]:
            raise _ConfigurationError('Git base contains a protected control alias.')
        object_text = object_id.decode('ascii')
        size = int(_git(executable, origin, 'cat-file', '-s', object_text))
        if size > const.MAX_PLAINTEXT_BYTES:
            raise _OperationalError('A Git base blob exceeds the bounded reconstruction limit.')
        files.append(_BaseFile(relative, object_text, size, mode == b'100755'))
        for parent in Path(relative).parents:
            if parent != Path('.'):
                directories.add(parent.as_posix())
        index.append(mode + b' ' + object_id + b' 0\t' + name + b'\0')
    return tuple(files), tuple(sorted(directories)), b''.join(index)


def _blob(plan: _MergePlan, entry: _BaseFile) -> bytes:
    """Read one size-checked raw blob; never run filters or external conversions."""
    data = _git(plan.executable, plan.origin, 'cat-file', 'blob', entry.oid)
    if len(data) != entry.size:
        raise _OperationalError('Git base blob size changed during reconstruction.')
    return data


def _flatten(entries: dict, prefix: str = '') -> dict[str, dict]:
    """Flatten a captured namespace for identity, type and content comparisons."""
    result = {}
    for name, item in entries.items():
        relative = prefix + name
        result[relative] = item
        result.update(_flatten(item.get('children', {}), relative + '/'))
    return result


def _worktrees(executable: str, origin: Path) -> tuple[tuple[Path, str], ...]:
    """Inspect registered worktrees without parsing quoted human output."""
    result = []
    for block in _git(executable, origin, 'worktree', 'list', '--porcelain', '-z').split(b'\0\0'):
        fields = block.split(b'\0')
        values = {field.split(b' ', 1)[0]: field.split(b' ', 1)[1] for field in fields if b' ' in field}
        if b'worktree' in values:
            result.append((Path(os.fsdecode(values[b'worktree'])), _text(values.get(b'branch', b''))))
    return tuple(result)


def _overlap(first: Path, second: Path) -> bool:
    """Detect both directions of lexical overlap after no-link inspection."""
    return first.is_relative_to(second) or second.is_relative_to(first)


def _plan_merge(
    origin: Path,
    mirror: Path,
    key: Path,
    *,
    gitdir: Path | None = None,
    worktree: Path | None = None,
    branch: str | None = None,
    base_branch: str = 'main',
    preserve_config: bool = False,
) -> _MergePlan:
    """Validate clean origin, explicit refs/output and the complete backup without writes.

    :param origin: Existing non-bare repository worktree root.
    :param mirror: Complete encrypted backup source.
    :param key: Selected external key.
    :param gitdir: Optional exact Git directory belonging to origin.
    :param worktree: New absent output with an existing parent; otherwise a timestamped sibling.
    :param branch: New suffix under the mandatory obfuscidian/ prefix.
    :param base_branch: Existing local committed base, default main.
    :param preserve_config: Keep the base settings, including their absence.
    :returns: Authenticated proposal with captured Git/filesystem observations.
    :raises _ConfigurationError: Unsupported repository, unsafe paths, names or refs.
    :raises _OperationalError: Dirty origin, pending operation, integrity or resource failure.
    """
    executable = shutil.which('git')
    if executable is None:
        raise _ConfigurationError('Merge restore requires Git on PATH.')
    origin_state = paths._inspect_path(origin)
    paths._preflight_vault_paths(origin, mirror, key, restore=True)
    try:
        if _git(executable, origin, 'rev-parse', '--is-bare-repository') != b'false\n':
            raise _ConfigurationError('Merge restore requires a non-bare origin repository.')
        root = Path(_text(_git(executable, origin, 'rev-parse', '--show-toplevel')))
        actual_gitdir = Path(_text(_git(executable, origin, 'rev-parse', '--absolute-git-dir')))
        common = Path(_text(_git(executable, origin, 'rev-parse', '--path-format=absolute', '--git-common-dir')))
        promisor = _git(
            executable,
            origin,
            'config',
            '--local',
            '--get-regexp',
            r'^(extensions\.partialclone|remote\..*\.promisor)$',
            accepted=(0, 1),
        )
        if promisor:
            raise _ConfigurationError(
                'Merge restore requires locally complete Git objects; partial/promisor clones are unsupported.'
            )
        head = _git(executable, origin, 'rev-parse', '--verify', 'HEAD^{commit}')
    except _OperationalError:
        raise _ConfigurationError('Origin must be the root of an existing local repository with a commit.') from None
    if root != origin:
        raise _ConfigurationError('--origin must select its Git worktree root.')
    git_state, common_state = paths._inspect_path(actual_gitdir), paths._inspect_path(common)
    if gitdir is not None:
        paths._inspect_path(gitdir)
        if gitdir != actual_gitdir:
            raise _ConfigurationError('--gitdir must select the exact Git directory belonging to --origin.')
    for directory in {actual_gitdir, common}:
        if any(tx._entry_exists(directory / name) for name in const.GIT_PENDING_NAMES):
            raise _OperationalError('Origin has a pending Git operation or index lock; finish it first.')
        if _overlap(directory, mirror) or key.is_relative_to(directory):
            raise _ConfigurationError('Mirror and selected key must remain outside Git administration.')
    origin_tree = tx._observe(origin, False)
    restore._reject_git_aliases({**origin_tree[0], **origin_tree[1]})
    selected = paths._inspect_path(key, kind='file').components[-1][1]
    if restore._contains_key({**origin_tree[0], **origin_tree[1]}, (selected.device, selected.inode)):
        raise _ConfigurationError('Selected key has a file alias inside origin.')
    committed, committed_dirs, expected_index = _tree(executable, origin, _text(head))
    if _git(executable, origin, 'ls-files', '--stage', '-z') != expected_index:
        raise _OperationalError('Origin index must be clean and match HEAD.')
    actual = _flatten({**origin_tree[0], **{k: v for k, v in origin_tree[1].items() if k != const.GIT_METADATA}})
    if set(actual) != {f.path for f in committed} | set(committed_dirs):
        raise _OperationalError('Origin must have no untracked or ignored vault entries.')
    for entry in committed:
        data = _git(executable, origin, 'cat-file', 'blob', entry.oid)
        if (
            actual[entry.path].get('digest') != hashlib.sha256(data).hexdigest()
            or bool(actual[entry.path]['identity'][2] & 0o111) != entry.executable
        ):
            raise _OperationalError('Origin working tree must match committed bytes; pause writers and review Git conversions.')
    index = tx._capture(actual_gitdir / 'index')
    stamp = datetime.now().strftime(const.TIMESTAMP_FORMAT)
    suffix = branch if branch is not None else 'restore-' + stamp
    full_branch = const.RESTORE_BRANCH_PREFIX + suffix
    try:
        _git(executable, origin, 'check-ref-format', '--branch', full_branch)
    except _OperationalError:
        raise _ConfigurationError('--branch must be a valid new suffix under obfuscidian/.') from None
    if not suffix or suffix.startswith(const.RESTORE_BRANCH_PREFIX):
        raise _ConfigurationError('--branch is a suffix, not a complete obfuscidian/ branch name.')
    candidate = 'refs/heads/' + full_branch
    refs = _git(executable, origin, 'for-each-ref', '--format=%(refname)', 'refs/heads/').decode('utf-8').splitlines()
    if any(ref == candidate or ref.startswith(candidate + '/') or candidate.startswith(ref + '/') for ref in refs):
        raise _ConfigurationError('Restore branch already exists or conflicts with an existing namespace; choose --branch.')
    base_oid = _ref(executable, origin, base_branch)
    base_files, base_directories, _ = _tree(executable, origin, base_oid)
    output = worktree if worktree is not None else origin.with_name(origin.name + '-restore-' + stamp)
    output_state = paths._inspect_path(output, allow_missing=True)
    if output_state.exists:
        raise _ConfigurationError('--worktree must be a new non-existing directory.')
    if not tx._outside_git(output.parent):
        raise _ConfigurationError('--worktree parent must be outside Git worktrees.')
    for location in (origin, mirror, actual_gitdir, common, key):
        location_info = location.lstat()
        aliases_ancestor = any(
            (fingerprint.device, fingerprint.inode) == (location_info.st_dev, location_info.st_ino)
            for _, fingerprint in output_state.components
        )
        if _overlap(output, location) or aliases_ancestor:
            raise _ConfigurationError('Restore output must not overlap origin, mirror, key or Git administration.')
    for registered, _ in _worktrees(executable, origin):
        if _overlap(output, registered):
            raise _ConfigurationError('Restore output must not overlap a registered Git worktree.')
    reconstruction = restore._plan_restore(output, mirror, key, preserve_config=preserve_config)
    kinds = {name: 'directory' for name in base_directories} | {f.path: 'file' for f in base_files}
    for record in reconstruction.directories:
        if kinds.get(record.path, 'directory') != 'directory':
            raise _ConfigurationError('Backup/base file-directory conflict; use fresh restore into a separate destination.')
        kinds[record.path] = 'directory'
    for record in reconstruction.files:
        if kinds.get(record.path, 'file') != 'file':
            raise _ConfigurationError('Backup/base file-directory conflict; use fresh restore into a separate destination.')
        kinds[record.path] = 'file'
    rules = reconstruction.transaction.target_rules
    paths._validate_target_paths(kinds, rules, destination=output)
    for label in ('backup', 'overlay'):
        staged = reconstruction.transaction.workspace_parent / (const.GIT_STAGE_PREFIX + '0' * 32) / label
        paths._validate_target_paths(kinds, rules, destination=staged)
    required = reconstruction.transaction.required_bytes * 3 + sum(f.size for f in base_files) * 2
    required += len(kinds) * const.RESTORE_ENTRY_RESERVE_BYTES * 2
    if shutil.disk_usage(reconstruction.transaction.workspace_parent).free < required + const.TRANSACTION_RESERVE_BYTES:
        raise _OperationalError('Insufficient space for private reconstruction and publication staging.')
    plan = _MergePlan(
        executable,
        origin,
        actual_gitdir,
        common,
        output,
        full_branch,
        base_branch,
        base_oid,
        head,
        tx._capture(actual_gitdir / 'HEAD'),
        index,
        origin_tree,
        origin_state,
        git_state,
        common_state,
        tuple(
            (file, tx._capture(file) if tx._entry_exists(file) else None)
            for file in {common / 'config', common / 'config.worktree', actual_gitdir / 'config.worktree'}
        ),
        reconstruction,
        base_files,
        base_directories,
    )
    _recheck_origin(plan)
    return plan


def _recheck_origin(plan: _MergePlan, *, output_absent: bool = True) -> None:
    """Revalidate clean origin/index/base/source and output before irreversible boundaries."""
    for state in (plan.origin_state, plan.git_state, plan.common_state):
        paths._recheck_path(state)
    for directory in {plan.gitdir, plan.common}:
        if any(tx._entry_exists(directory / name) for name in const.GIT_PENDING_NAMES):
            raise _OperationalError('A pending Git operation appeared; restore is blocked.')
    if (
        _git(plan.executable, plan.origin, 'rev-parse', '--verify', 'HEAD^{commit}') != plan.head
        or tx._capture(plan.gitdir / 'HEAD') != plan.head_control
        or tx._capture(plan.gitdir / 'index') != plan.index
        or tx._observe(plan.origin, False) != plan.origin_tree
        or _ref(plan.executable, plan.origin, plan.base_branch) != plan.base_oid
    ):
        raise _OperationalError('Origin, index or base changed; restore is blocked.')
    for file, captured in plan.configurations:
        observed = tx._capture(file) if tx._entry_exists(file) else None
        if observed != captured:
            raise _OperationalError('Git configuration changed; restore is blocked.')
    restore._recheck_source(plan.reconstruction)
    paths._recheck_path(plan.reconstruction.transaction.parent_state)
    if output_absent:
        paths._recheck_path(plan.reconstruction.locations.origin)


def _copy_tree(source: Path, target: Path, captured: dict, unsupported: set[str], prefix: str = '') -> None:
    """Copy known private content with no-follow reads and exclusive target creation."""
    if tx._capture(source) != captured:
        raise _OperationalError('Private staging changed; retain it for manual inspection.')
    for name, entry in captured['children'].items():
        src, dst = source / name, target / name
        if 'children' in entry:
            with paths._directory_handle(paths._inspect_path(target)) as handle:
                os.mkdir(name, 0o700, dir_fd=handle)
            _copy_tree(src, dst, entry, unsupported, prefix + name + '/')
            restore._set_time(dst, src.lstat().st_mtime_ns, unsupported, prefix + name)
        else:
            with paths._directory_handle(paths._inspect_path(source)) as handle:
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=handle)
                with os.fdopen(descriptor, 'rb') as stream:
                    data = stream.read(entry['size'] + 1)
            if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['digest']:
                raise _OperationalError('Private staged bytes changed; artifacts are retained.')
            backup._write_token(target, name, data)
            if entry['identity'][2] & 0o111:
                with paths._directory_handle(paths._inspect_path(target)) as handle:
                    os.chmod(name, 0o700, dir_fd=handle, follow_symlinks=False)
        if 'mtime' in entry:
            restore._set_time(dst, entry['mtime'], unsupported, prefix + name)
    if tx._capture(source) != captured:
        raise _OperationalError('Private staging changed while copying; artifacts are retained.')


def _stage_overlay(plan: _MergePlan, workspace: Path, unsupported: set[str]) -> tuple[Path, dict, dict]:
    """Reconstruct and verify the entire additive union before any branch/worktree exists."""
    restored, overlay = workspace / 'backup', workspace / 'overlay'
    with paths._directory_handle(paths._inspect_path(workspace)) as descriptor:
        os.mkdir(restored.name, 0o700, dir_fd=descriptor)
        os.mkdir(overlay.name, 0o700, dir_fd=descriptor)
    restore._build_restore(plan.reconstruction, restored, unsupported)
    restored_capture = tx._capture(restored)
    restore._verify_stage(plan.reconstruction, restored, unsupported)
    if tx._capture(restored) != restored_capture:
        raise _OperationalError('Reconstruction changed during validation; artifacts are retained.')
    for relative in sorted(
        set(plan.base_directories) | {r.path for r in plan.reconstruction.directories}, key=lambda p: (p.count('/'), p)
    ):
        target = overlay / relative
        with paths._directory_handle(paths._inspect_path(target.parent)) as descriptor:
            os.mkdir(target.name, 0o700, dir_fd=descriptor)
    incoming = {r.path: r for r in plan.reconstruction.files}
    for entry in plan.base_files:
        if entry.path not in incoming:
            target = overlay / entry.path
            backup._write_token(target.parent, target.name, _blob(plan, entry))
            if entry.executable:
                with paths._directory_handle(paths._inspect_path(target.parent)) as handle:
                    os.chmod(target.name, 0o700, dir_fd=handle, follow_symlinks=False)
    for record in plan.reconstruction.files:
        data = manifest._read_validated_file(plan.reconstruction.snapshot, record, plan.reconstruction.fernet)
        target = overlay / record.path
        backup._write_token(target.parent, target.name, data)
        restore._set_time(target, record.mtime_ns, unsupported, record.path)
    for record in sorted(plan.reconstruction.directories, key=lambda r: (-r.path.count('/'), r.path)):
        restore._set_time(overlay / record.path, record.mtime_ns, unsupported, record.path)
    captured = tx._capture(overlay)
    flat = _flatten(captured['children'])
    expected = set(plan.base_directories) | {f.path for f in plan.base_files}
    expected |= {r.path for r in (*plan.reconstruction.directories, *plan.reconstruction.files)}
    if set(flat) != expected:
        raise _OperationalError('Additive staged namespace differs from its proposal.')
    for entry in plan.base_files:
        digest = (
            incoming[entry.path].plaintext_sha256 if entry.path in incoming else hashlib.sha256(_blob(plan, entry)).hexdigest()
        )
        if flat[entry.path].get('digest') != digest:
            raise _OperationalError('Additive staged base content differs from its proposal.')
    for record in plan.reconstruction.files:
        if flat[record.path].get('digest') != record.plaintext_sha256 or flat[record.path].get('size') != record.size:
            raise _OperationalError('Additive staged backup content differs from its authenticated proposal.')
    workspace_capture = {
        'identity': tx._identity(workspace.lstat()),
        'children': {'backup': restored_capture, 'overlay': captured},
    }
    if tx._capture(workspace) != workspace_capture:
        raise _OperationalError('Private workspace changed during reconstruction; artifacts are retained.')
    _recheck_origin(plan)
    return overlay, captured, workspace_capture


def _cleanup_git(
    plan: _MergePlan, expected: tuple[dict, dict] | None, index: dict | None, output_state: paths._PathState | None
) -> bool:
    """Remove only a proven owned worktree and unchanged new branch; retain uncertainty."""
    try:
        _recheck_origin(plan, output_absent=False)
        ref = 'refs/heads/' + plan.branch
        if _text(_git(plan.executable, plan.origin, 'rev-parse', '--verify', ref)) != plan.base_oid:
            return False
        registered = _worktrees(plan.executable, plan.origin)
        attached = [root for root, branch in registered if branch == ref]
        if tx._entry_exists(plan.output):
            if expected is None or index is None or output_state is None or attached != [plan.output]:
                return False
            paths._recheck_path(output_state)
            verification._reject_pending(plan.output)
            gitdir = Path(_text(_git(plan.executable, plan.output, 'rev-parse', '--absolute-git-dir')))
            if tx._observe(plan.output, False) != expected or tx._capture(gitdir / 'index') != index:
                return False
            if _git(plan.executable, plan.output, 'symbolic-ref', 'HEAD') != (ref + '\n').encode():
                return False
            _git(plan.executable, plan.origin, 'worktree', 'remove', '--force', str(plan.output))
        elif attached or any(root == plan.output for root, _ in registered):
            return False
        _git(plan.executable, plan.origin, 'update-ref', '-d', ref, plan.base_oid)
        return True
    except (OSError, _ConfigurationError, _OperationalError, MemoryError):
        return False


def _publish_merge(plan: _MergePlan, *, dry_run: bool = False) -> _MergeResult | None:
    """Publish an authenticated additive worktree without staging restored differences.

    Only the new worktree index is initialized to the chosen committed base.
    Restored differences remain unstaged/uncommitted. On ordinary failures,
    remove known owned Git artifacts only after full identity/content checks.
    Unknown staging, user edits and incomplete journaled recovery are retained.

    :param plan: Completely validated read-only proposal.
    :param dry_run: Recheck only; no Git refs, locks or plaintext writes.
    :returns: Worktree/manual-review evidence, or None for a read-only dry run.
    :raises _MergeFailure: Operation failed, with retained locations for opt-in guidance.
    :raises KeyboardInterrupt: Interrupt after conservative cleanup.
    """
    _recheck_origin(plan)
    if dry_run:
        return None
    if os.name != 'posix':
        raise _ConfigurationError('Merge restore writes require POSIX private modes; native Windows support is deferred.')
    workspace = plan.reconstruction.transaction.workspace_parent / (const.GIT_STAGE_PREFIX + secrets.token_hex(16))
    with paths._directory_handle(plan.reconstruction.transaction.parent_state) as descriptor:
        os.mkdir(workspace.name, 0o700, dir_fd=descriptor)
    workspace_identity = tx._identity(workspace.lstat())
    workspace_capture = None
    created = False
    branch_attempted = False
    expected = index = output_state = None
    retained: list[Path] = []
    warnings: list[str] = []
    unsupported: set[str] = set()
    failure = None
    outcome = None
    try:
        overlay, captured, workspace_capture = _stage_overlay(plan, workspace, unsupported)
        if tx._capture(workspace) != workspace_capture or workspace_capture['identity'] != workspace_identity:
            raise _OperationalError('Private staging changed after validation; artifacts are retained.')
        _recheck_origin(plan)
        # Compare-and-create prevents resetting a collision, including SHA-256 repositories.
        branch_attempted = True
        _git(plan.executable, plan.origin, 'update-ref', 'refs/heads/' + plan.branch, plan.base_oid, '0' * len(plan.base_oid))
        created = True
        _git(plan.executable, plan.origin, 'worktree', 'add', '--no-checkout', str(plan.output), plan.branch)
        output_state = paths._inspect_path(plan.output)
        with paths._directory_handle(output_state) as descriptor:
            os.fchmod(descriptor, 0o700)
        output_state = paths._inspect_path(plan.output)
        expected = tx._observe(plan.output, False)
        _git(plan.executable, plan.output, 'read-tree', plan.base_oid)
        output_gitdir = Path(_text(_git(plan.executable, plan.output, 'rev-parse', '--absolute-git-dir')))
        index = tx._capture(output_gitdir / 'index')
        if expected[0] or set(expected[1]) != {const.GIT_METADATA}:
            raise _OperationalError('New worktree contains unexpected data; preserve it for manual inspection.')
        # Install the base control separately; transaction publication preserves its identity.
        if const.GIT_IGNORE in captured['children']:
            control = captured['children'][const.GIT_IGNORE]
            tx._move(overlay / const.GIT_IGNORE, plan.output / const.GIT_IGNORE, control)
            expected = (expected[0], {**expected[1], const.GIT_IGNORE: control})
            captured = {**captured, 'children': {n: e for n, e in captured['children'].items() if n != const.GIT_IGNORE}}
            workspace_capture = {**workspace_capture, 'children': {**workspace_capture['children'], 'overlay': captured}}
        transaction = tx._plan_transaction(
            plan.reconstruction.locations.mirror.path,
            plan.output,
            required_bytes=plan.reconstruction.transaction.required_bytes + sum(f.size for f in plan.base_files),
            target_rules=plan.reconstruction.transaction.target_rules,
        )
        if (transaction.before, transaction.protected) != expected:
            raise _OperationalError('New worktree changed before publication; artifacts are retained.')
        proposed = None

        def build(stage: Path) -> None:
            _copy_tree(overlay, stage, captured, unsupported)

        def verify(stage: Path) -> None:
            nonlocal proposed
            actual = _flatten(tx._capture(stage)['children'])
            known = _flatten(captured['children'])
            if set(actual) != set(known) or any(
                {
                    k: v
                    for k, v in actual[n].items()
                    if k not in {'identity', 'children'} | ({'mtime'} if n in unsupported else set())
                }
                != {
                    k: v
                    for k, v in known[n].items()
                    if k not in {'identity', 'children'} | ({'mtime'} if n in unsupported else set())
                }
                for n in known
            ):
                raise _OperationalError('Publication staging differs from the verified additive union.')
            proposed = tx._observe(stage, False)
            _recheck_origin(plan, output_absent=False)

        result = tx._execute_transaction(
            transaction,
            build,
            verify,
            yes=True,
            non_interactive=True,
            retain_rollback=False,
            prepublish=lambda: _recheck_origin(plan, output_absent=False),
        )
        expected = (proposed[0], transaction.protected)
        warnings.extend(result.warnings)
        if result.retained:
            retained.append(result.workspace)
        # Ask Git only about ignored paths; this does not invoke attributes or filters.
        ignored = tuple(
            _decode(p)
            for p in _git(plan.executable, plan.output, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z').split(
                b'\0'
            )
            if p
        )
        _recheck_origin(plan, output_absent=False)
        if tx._observe(plan.output, False) != expected or tx._capture(output_gitdir / 'index') != index:
            raise _OperationalError('Review worktree changed before handoff; artifacts are retained.')
        if unsupported:
            warnings.append('Some modification times could not be preserved on this filesystem.')
        outcome = ignored
    except BaseException as error:
        clean = not branch_attempted
        if created:
            clean = _cleanup_git(plan, expected, index, output_state)
        elif branch_attempted:
            try:
                clean = not _git(plan.executable, plan.origin, 'for-each-ref', '--format=%(refname)', 'refs/heads/' + plan.branch)
            except _OperationalError:
                clean = False
        if not clean and tx._entry_exists(plan.output):
            retained.append(plan.output)
        if isinstance(error, tx._TransactionError):
            # Recovery deliberately retains its private journal/staging; never sweep it.
            warnings.append('Journaled recovery data retained; inspect private transaction workspaces.')
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            error.add_note('Merge restore failed; inspect retained private staging and worktree artifacts before retrying.')
            failure = error
        message = 'Merge restore failed. '
        message += (
            'Owned branch/worktree cleaned safely.'
            if clean
            else 'Branch/worktree retained because ownership or data is uncertain.'
        )
        if warnings:
            message += ' ' + ' '.join(warnings)
        if failure is None:
            failure = message
    finally:
        try:
            if workspace_capture is not None and tx._identity(workspace.lstat()) == workspace_identity:
                tx._remove_captured(workspace, workspace_capture)
            else:
                retained.append(workspace)
        except (OSError, _ConfigurationError, _OperationalError, MemoryError):
            retained.append(workspace)

    if isinstance(failure, BaseException):
        raise failure
    if failure is not None:
        raise _MergeFailure(failure, plan, tuple(retained)) from None
    if workspace in retained:
        warnings.append('Private reconstruction cleanup incomplete; sensitive plaintext retained.')
    return _MergeResult(plan.output, plan.branch, outcome, tuple(warnings), tuple(retained))

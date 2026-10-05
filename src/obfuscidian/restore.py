# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.restore
:Synopsis:          Internal complete verification, private reconstruction and fresh restore
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import fnmatch
import os
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from cryptography.fernet import Fernet

from obfuscidian import backup, keys, manifest, paths, transactions, verification
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError


@dataclass(frozen=True, repr=False)
class _RestorePlan:
    """Keep authenticated metadata and observations without retained plaintext."""

    locations: paths._VaultPaths
    snapshot: manifest._VerifiedMirror
    transaction: transactions._TransactionPlan
    fernet: Fernet = field(repr=False)
    directories: tuple[manifest._DirectoryRecord, ...]
    files: tuple[manifest._FileRecord, ...]
    warnings: tuple[str, ...]


def _protected_path(record: manifest._DirectoryRecord | manifest._FileRecord, preserve_config: bool) -> bool:
    """Reject protected aliases and historic exclusions; skip only exact preserved settings."""
    parts = record.path.split('/')
    compared = [unicodedata.normalize('NFC', part).casefold() for part in parts]
    if const.GIT_METADATA in compared or compared[0] == const.GIT_IGNORE:
        raise _ConfigurationError('Restore cannot introduce protected Git controls or their name aliases.')
    if isinstance(record, manifest._FileRecord) and (
        compared[-1] == const.GIT_IGNORE or fnmatch.fnmatchcase(compared[-1], f'{const.KEY_PREFIX}*{const.KEY_SUFFIX}')
    ):
        raise _ConfigurationError('Restore cannot introduce excluded Git or key files or their name aliases.')
    if preserve_config and compared[0] == const.OBSIDIAN_DIRECTORY:
        if parts[0] != const.OBSIDIAN_DIRECTORY:
            raise _ConfigurationError('Restored configuration aliases conflict with protected settings.')
        return True
    return False


def _contains_key(entries: dict, identity: tuple[int, int]) -> bool:
    """Detect a selected-key hard link in captured payload or non-Git protected settings."""
    return any(
        tuple(entry['identity'][:2]) == identity or _contains_key(entry.get('children', {}), identity)
        for entry in entries.values()
    )


def _reject_git_aliases(entries: dict, *, root: bool = True, preserve_config: bool = False) -> None:
    """Refuse potentially active Git metadata aliases instead of moving them to rollback."""
    for name, entry in entries.items():
        compared = unicodedata.normalize('NFC', name).casefold()
        if compared == const.GIT_METADATA and (not root or name != const.GIT_METADATA):
            raise _ConfigurationError('Fresh restore cannot remove nested repositories or Git metadata aliases.')
        root_controls = {const.GIT_IGNORE} | ({const.OBSIDIAN_DIRECTORY} if preserve_config else set())
        if root and compared in root_controls and compared != name:
            raise _ConfigurationError('Fresh restore cannot replace protected root control aliases.')
        if name != const.GIT_METADATA:
            _reject_git_aliases(entry.get('children', {}), root=False, preserve_config=preserve_config)


def _plan_restore(
    origin: Path, mirror: Path, key: Path, *, preserve_config: bool = False, allow_pending: bool = False
) -> _RestorePlan:
    """Authenticate every object and validate all target names before any write.

    Naming checks use a conservative case-folded NFC envelope, including on
    case-sensitive filesystems; ambiguous names fail rather than being renamed.
    Actual component/path length limits are read from the destination filesystem.
    The complete backup is verified even when configuration records are skipped.

    :param origin: Plaintext destination; only its final component may be absent.
    :param mirror: Existing complete encrypted source.
    :param key: Existing external selected key.
    :param preserve_config: Leave root settings in place, including their absence.
    :param allow_pending: Permit destination ownership inspection for explicit recovery.
    :returns: Complete read-only reconstruction proposal.
    :raises _ConfigurationError: Unsafe locations, names, custody or destination shape.
    :raises _OperationalError: Integrity, pending ownership, stability or resource failure.
    """
    locations = paths._preflight_vault_paths(origin, mirror, key, restore=True)
    verification._reject_pending(mirror)
    fernet, warnings = keys._load_key(key)
    rules = backup._mirror_rules(origin if locations.origin.exists else origin.parent)
    snapshot = manifest._verify_mirror(mirror, fernet, target_rules=rules, destination=origin)
    directories = tuple(r for r in snapshot.manifest.directories if not _protected_path(r, preserve_config))
    files = tuple(r for r in snapshot.manifest.files if not _protected_path(r, preserve_config))
    required = sum(r.size for r in files)
    # Reserve directory/file allocation units, including zero-length files.
    required += (len(directories) + len(files)) * const.RESTORE_ENTRY_RESERVE_BYTES
    transaction = transactions._plan_transaction(
        mirror,
        origin,
        preserve_config=preserve_config,
        required_bytes=required,
        allow_pending=allow_pending,
        target_rules=rules,
    )
    _reject_git_aliases({**transaction.before, **transaction.protected}, preserve_config=preserve_config)
    selected = locations.key.components[-1][1]
    if _contains_key({**transaction.before, **transaction.protected}, (selected.device, selected.inode)):
        raise _ConfigurationError('Selected key has a file alias inside the restore destination.')
    paths._validate_target_paths(
        [r.path for r in (*directories, *files)] + transactions._tree_names(transaction.protected),
        rules,
        destination=origin,
    )
    # Validate the longest staging prefix too, before ownership or plaintext.
    staged = transaction.workspace_parent / (const.TRANSACTION_PREFIX + '0' * 32) / const.TRANSACTION_STAGE
    paths._validate_target_paths((r.path for r in (*directories, *files)), rules, destination=staged)
    locations._recheck()
    manifest._recheck_mirror(snapshot)
    verification._reject_pending(mirror)
    return _RestorePlan(locations, snapshot, transaction, fernet, directories, files, warnings)


def _recheck_source(plan: _RestorePlan) -> None:
    """Recheck complete encrypted observations, source ownership and selected key identity."""
    manifest._recheck_mirror(plan.snapshot)
    paths._recheck_path(plan.locations.key, content=True)
    verification._reject_pending(plan.locations.mirror.path)


def _set_time(path: Path, mtime_ns: int, unsupported: set[str], relative: str) -> None:
    """Preserve supported times, recording a redacted warning for limitations."""
    state = paths._inspect_path(path, kind='directory' if path.is_dir() else 'file')
    with paths._directory_handle(paths._inspect_path(path.parent)) as handle:
        try:
            os.utime(path.name, ns=(mtime_ns, mtime_ns), dir_fd=handle, follow_symlinks=False)
        except (OSError, OverflowError, ValueError):
            unsupported.add(relative)
    if path.stat().st_mtime_ns != mtime_ns:
        unsupported.add(relative)
    paths._recheck_path(state)


def _build_restore(plan: _RestorePlan, stage: Path, unsupported: set[str]) -> None:
    """Reconstruct authenticated bytes exclusively with private files and directories."""
    for record in sorted(plan.directories, key=lambda r: (r.path.count('/'), r.path)):
        target = stage / record.path
        with paths._directory_handle(paths._inspect_path(target.parent)) as handle:
            os.mkdir(target.name, 0o700, dir_fd=handle)
    for record in plan.files:
        data = manifest._read_validated_file(plan.snapshot, record, plan.fernet)
        target = stage / record.path
        backup._write_token(target.parent, target.name, data)
        del data
        _set_time(target, record.mtime_ns, unsupported, record.path)
    # Children must be finished before restoring directory times.
    for record in sorted(plan.directories, key=lambda r: (-r.path.count('/'), r.path)):
        _set_time(stage / record.path, record.mtime_ns, unsupported, record.path)


def _verify_stage(plan: _RestorePlan, stage: Path, unsupported: set[str]) -> None:
    """Compare the entire proposed plaintext namespace, hashes, sizes and supported times."""
    payload, controls = transactions._observe(stage, False)
    names = set(transactions._tree_names(payload))
    expected = {r.path for r in (*plan.directories, *plan.files)}
    if controls or names != expected:
        raise _OperationalError('Reconstructed namespace differs from the authenticated proposal.')
    for record in (*plan.directories, *plan.files):
        entry = payload
        for index, component in enumerate(record.path.split('/')):
            observed = entry[component]
            if index < len(record.path.split('/')) - 1:
                entry = observed['children']
        if isinstance(record, manifest._FileRecord):
            if observed.get('size') != record.size or observed.get('digest') != record.plaintext_sha256:
                raise _OperationalError('Reconstructed file differs from its authenticated content binding.')
        elif 'children' not in observed:
            raise _OperationalError('Reconstructed directory has an unexpected type.')
        if record.path not in unsupported and (stage / record.path).stat().st_mtime_ns != record.mtime_ns:
            raise _OperationalError('Reconstructed modification time changed during staging.')
    _recheck_source(plan)


def _publish_restore(
    plan: _RestorePlan,
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
    dry_run: bool = False,
) -> transactions._TransactionResult | None:
    """Publish only a completely verified proposal, retaining plaintext rollback.

    :param plan: Complete authenticated read-only proposal.
    :param yes: Explicit replacement consent; never bypasses safety checks.
    :param non_interactive: Prohibit prompts.
    :param prompt: Terminal-aware replacement prompt.
    :param dry_run: Recheck only; create no locks, plaintext or destinations.
    :returns: Retained sensitive plaintext workspace, or None for a dry run.
    :raises _OperationalError: Consent, integrity, stability, publication or recovery failure.
    :raises KeyboardInterrupt: Interrupt after attempted conservative rollback.
    """
    _recheck_source(plan)
    unsupported: set[str] = set()
    result = transactions._execute_transaction(
        plan.transaction,
        lambda stage: _build_restore(plan, stage, unsupported),
        lambda stage: _verify_stage(plan, stage, unsupported),
        yes=yes or not plan.transaction.before,
        non_interactive=non_interactive,
        prompt=prompt,
        dry_run=dry_run,
        prepublish=lambda: _recheck_source(plan),
    )
    if result is not None and unsupported:
        result = replace(
            result, warnings=(*result.warnings, 'Some modification times could not be preserved on this filesystem.')
        )
    return result


def _recover_restore(
    origin: Path,
    mirror: Path,
    key: Path,
    *,
    preserve_config: bool = False,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
) -> transactions._TransactionResult:
    """Verify the complete source before explicitly recovering old plaintext, then replan separately."""
    plan = _plan_restore(origin, mirror, key, preserve_config=preserve_config, allow_pending=True)
    _recheck_source(plan)
    return transactions._recover_transaction(plan.transaction, yes=yes, non_interactive=non_interactive, prompt=prompt)

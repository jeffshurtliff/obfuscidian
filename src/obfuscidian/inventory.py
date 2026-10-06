# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.inventory
:Synopsis:          Internal deterministic read-only inventory and resource estimates
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import fnmatch
import os
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Literal

from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.paths import (
    _child_state,
    _directory_handle,
    _Fingerprint,
    _inspect_path,
    _is_link,
    _PathState,
    _recheck_path,
    _validate_relative_path,
    _VaultPaths,
)


@dataclass(frozen=True)
class _Exclusion:
    """Retain one validated root-relative component glob and directory-only flag."""

    components: tuple[str, ...]
    directory_only: bool


def _compile_exclusions(patterns: tuple[str, ...]) -> tuple[_Exclusion, ...]:
    """Validate portable component globs without negation or re-inclusion."""
    result = []
    for pattern in patterns:
        if (
            not isinstance(pattern, str)
            or not pattern
            or pattern.startswith(('!', '/'))
            or '\\' in pattern
            or '\0' in pattern
            or PureWindowsPath(pattern).drive
        ):
            raise _ConfigurationError('Exclusions must be relative forward-slash globs without negation or drives.')
        directory_only = pattern.endswith('/')
        parts = tuple((pattern[:-1] if directory_only else pattern).split('/'))
        if any(part in {'', '.', '..'} for part in parts):
            raise _ConfigurationError('Exclusions must not contain empty or traversal components.')
        result.append(_Exclusion(parts, directory_only))
    return tuple(result)


def _glob_matches(pattern: tuple[str, ...], parts: tuple[str, ...]) -> bool:
    """Match case-sensitively; only standalone ** crosses path components."""

    matched = [True] + [False] * len(parts)
    for component in pattern:
        previous = matched
        matched = [False] * (len(parts) + 1)
        if component == '**':
            matched[0] = previous[0]
            for index in range(1, len(matched)):
                matched[index] = previous[index] or matched[index - 1]
        else:
            for index, part in enumerate(parts, start=1):
                matched[index] = previous[index - 1] and fnmatch.fnmatchcase(part, component)
    return matched[-1]


def _is_excluded(parts: tuple[str, ...], *, directory: bool, rules: tuple[_Exclusion, ...]) -> bool:
    """Combine unoverrideable Git/key exclusions with approved user globs."""
    if const.GIT_METADATA in parts:
        return True
    if not directory and (
        parts[-1] == const.GIT_IGNORE or fnmatch.fnmatchcase(parts[-1], f'{const.KEY_PREFIX}*{const.KEY_SUFFIX}')
    ):
        return True
    return any((not rule.directory_only or directory) and _glob_matches(rule.components, parts) for rule in rules)


def _fernet_size(plaintext_bytes: int) -> int:
    """Calculate exact standard encoded Fernet size without allocating a token.

    :param plaintext_bytes: Nonnegative integer plaintext length.
    :returns: Encoded token bytes including standard Base64 padding.
    :raises _ConfigurationError: The supplied length is not a nonnegative integer.
    """
    if type(plaintext_bytes) is not int or plaintext_bytes < 0:
        raise _ConfigurationError('Resource sizes must be nonnegative integers.')
    padded = const.FERNET_BLOCK_BYTES * (plaintext_bytes // const.FERNET_BLOCK_BYTES + 1)
    return 4 * ((const.FERNET_FIXED_BYTES + padded + 2) // 3)


def _check_encrypted_size(size: int) -> None:
    """Enforce the shared object/manifest cap, accepting exactly the limit."""
    if type(size) is not int or size < 0 or size > const.MAX_ENCRYPTED_BYTES:
        raise _ConfigurationError('Encrypted objects and manifests must stay within the 50 MiB v1 limit.')


@dataclass(frozen=True)
class _InventoryEntry:
    """Describe one included relative file/directory without reading its contents."""

    path: str
    kind: Literal['file', 'directory']
    fingerprint: _Fingerprint

    @property
    def size(self) -> int:
        """Return plaintext file bytes; directory payload has no content bytes."""
        return self.fingerprint.size if self.kind == 'file' else 0

    @property
    def mtime_ns(self) -> int:
        """Return the lossless signed source modification time."""
        return self.fingerprint.mtime_ns


@dataclass(frozen=True)
class _Inventory:
    """Retain sorted included entries, pruning counts, and private recheck state."""

    root: _PathState = field(repr=False, compare=False)
    root_fingerprint: _Fingerprint
    entries: tuple[_InventoryEntry, ...]
    excluded_entries: int
    exclusions: tuple[str, ...] = field(repr=False)
    selected_key: _Fingerprint | None = field(default=None, repr=False)

    @property
    def file_count(self) -> int:
        """Count included files, including zero-byte files."""
        return sum(entry.kind == 'file' for entry in self.entries)

    @property
    def directory_count(self) -> int:
        """Count included directories, including empty directories, excluding the root."""
        return sum(entry.kind == 'directory' for entry in self.entries)

    @property
    def plaintext_bytes(self) -> int:
        """Sum included file sizes without reading or decoding source bytes."""
        return sum(entry.size for entry in self.entries)


def _scan_inventory(root: Path, *, exclusions: tuple[str, ...] = (), selected_key: _Fingerprint | None = None) -> _Inventory:
    """Inventory all included source types deterministically without mutation.

    Excluded directories are pruned before descent; excluded_entries counts
    encountered entries, never unvisited descendants. Paths are sorted by
    case-sensitive Python string order, independent of locale. Root/entry stat
    comparisons catch observed changes but cannot provide an atomic snapshot.

    :param root: Existing absolute source directory with no link components.
    :param exclusions: Approved portable component globs.
    :param selected_key: Optional key identity to refuse included or excluded hard-link aliases.
    :returns: Included records, totals, and protected source identity.
    :raises _ConfigurationError: Unsafe entries, names, keys, or size limits are detected.
    :raises _OperationalError: Traversal fails or source changes are detected.
    """
    rules = _compile_exclusions(exclusions)
    source = _inspect_path(root)
    entries = []
    directories = [source]
    excluded = 0
    pending = [(source, ())]
    try:
        while pending:
            parent, relative_parts = pending.pop()
            with _directory_handle(parent) as handle:
                _recheck_path(parent, content=True)
                with os.scandir(handle if handle is not None else parent.path) as scan:
                    children = sorted(scan, key=lambda child: child.name)
                for child in children:
                    parts = (*relative_parts, child.name)
                    # Git metadata is never opened, inspected, or traversed.
                    if child.name == const.GIT_METADATA:
                        excluded += 1
                        continue
                    info = child.stat(follow_symlinks=False)
                    if selected_key is not None and selected_key._same_object(info):
                        raise _ConfigurationError('Selected key has a file alias inside the source vault.')
                    directory = stat.S_ISDIR(info.st_mode) and not _is_link(info)
                    if _is_excluded(parts, directory=directory, rules=rules):
                        excluded += 1
                        continue
                    if _is_link(info) or not (directory or stat.S_ISREG(info.st_mode)):
                        raise _ConfigurationError(
                            'Included vault entries must be regular files or directories without links or junctions.'
                        )
                    relative = '/'.join(parts)
                    _validate_relative_path(relative, windows=os.name == 'nt')
                    record = _InventoryEntry(relative, 'directory' if directory else 'file', _Fingerprint._from_stat(info))
                    if not directory:
                        _check_encrypted_size(_fernet_size(record.size))
                    entries.append(record)
                    if directory:
                        state = _child_state(parent, child.name, info)
                        directories.append(state)
                        pending.append((state, parts))
                _recheck_path(parent, content=True)
        # Catch changes in earlier subtrees, not just the directory currently scanned.
        for directory_state in directories:
            _recheck_path(directory_state, content=True)
        for entry in entries:
            current = (root / entry.path).lstat()
            if _is_link(current) or entry.fingerprint != _Fingerprint._from_stat(current):
                raise _OperationalError('Source inventory changed during scanning; stop other writers and retry.')
        _recheck_path(source, content=True)
    except OSError:
        raise _OperationalError('Cannot inventory the source safely; check access permissions and other writers.') from None
    return _Inventory(
        root=source,
        root_fingerprint=source.components[-1][1],
        entries=tuple(sorted(entries, key=lambda entry: entry.path)),
        excluded_entries=excluded,
        exclusions=exclusions,
        selected_key=selected_key,
    )


def _inventory_vault(paths: _VaultPaths, *, exclusions: tuple[str, ...] = ()) -> _Inventory:
    """Combine path preflight identities with source inventory and key-alias checks."""
    paths._recheck()
    inventory = _scan_inventory(paths.origin.path, exclusions=exclusions, selected_key=paths.key.components[-1][1])
    paths._recheck()
    return inventory


def _verify_inventory(inventory: _Inventory) -> None:
    """Re-inventory after reading and abort on included changes, additions, or deletions.

    Excluded subtree contents remain intentionally unvisited. Rechecks compare
    identities, types, sizes, mode, mtime, ctime, and encountered exclusion count.

    :param inventory: Previously collected source records.
    :raises _OperationalError: Current inventory differs or cannot be inspected.
    :raises _ConfigurationError: Newly unsafe entries are discovered.
    """
    _recheck_path(inventory.root, content=True)
    current = _scan_inventory(inventory.root.path, exclusions=inventory.exclusions, selected_key=inventory.selected_key)
    if current != inventory:
        raise _OperationalError('Source inventory changed after reading; stop other writers and retry.')


def _read_file(inventory: _Inventory, entry: _InventoryEntry) -> bytes:
    """Read one bounded binary file and refuse detected identity/content changes.

    POSIX reads use no-follow descriptors anchored to inspected directories.
    Other hosts use no-follow inspection and pre/post-I/O identity checks;
    native Windows race hardening remains Thread 12. No content is decoded.

    :param inventory: Source inventory containing this entry.
    :param entry: Included regular file record to read.
    :returns: Exact original bytes only after stability checks pass.
    :raises _ConfigurationError: The record is invalid, unsafe, or oversized.
    :raises _OperationalError: Reading fails or observed state changes.
    """
    if entry.kind != 'file' or entry not in inventory.entries:
        raise _ConfigurationError('Stable reads require an included file record.')
    parts = _validate_relative_path(entry.path, windows=os.name == 'nt')
    _check_encrypted_size(_fernet_size(entry.size))
    path = inventory.root.path.joinpath(*parts)
    try:
        _recheck_path(inventory.root)
        parent = _inspect_path(path.parent)
        # Bind every directory to its original inventory identity, not a fresh replacement.
        recorded = {item.path: item.fingerprint for item in inventory.entries if item.kind == 'directory'}
        for component, fingerprint in parent.components:
            if component == inventory.root.path:
                expected = inventory.root.components[-1][1]
            elif component.is_relative_to(inventory.root.path):
                expected = recorded.get(component.relative_to(inventory.root.path).as_posix())
                if expected is None:
                    raise _OperationalError('File parent is absent from the original inventory.')
            else:
                continue
            if fingerprint != expected:
                raise _OperationalError('Source directory changed before reading; stop other writers and retry.')
        with _directory_handle(parent) as handle:
            descriptor = os.open(
                path.name if handle is not None else path,
                os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0),
                dir_fd=handle,
            )
            try:
                source = os.fdopen(descriptor, 'rb')
            except (OSError, MemoryError):
                os.close(descriptor)
                raise
            with source:
                before = os.fstat(source.fileno())
                if _is_link(before) or not stat.S_ISREG(before.st_mode) or entry.fingerprint != _Fingerprint._from_stat(before):
                    raise _OperationalError('Source file changed before reading; stop other writers and retry.')
                data = source.read(entry.size + 1)
                if len(data) != entry.size or entry.fingerprint != _Fingerprint._from_stat(os.fstat(source.fileno())):
                    raise _OperationalError('Source file changed while reading; no content is accepted.')
                current = os.stat(path.name if handle is not None else path, dir_fd=handle, follow_symlinks=False)
                if _is_link(current) or entry.fingerprint != _Fingerprint._from_stat(current):
                    raise _OperationalError('Source file identity changed while reading; no content is accepted.')
        _recheck_path(inventory.root)
        return data
    except (OSError, MemoryError):
        raise _OperationalError(
            'Cannot read the source safely; check permissions, available memory, and other writers.'
        ) from None


@dataclass(frozen=True)
class _ResourceEstimate:
    """Separate ciphertext payload, retained objects, and additional copy space."""

    object_bytes: int
    manifest_bytes: int
    retained_bytes: int
    rollback_copy_bytes: int

    @property
    def staging_bytes(self) -> int:
        """Return additional staged payload, excluding filesystem bookkeeping."""
        return self.object_bytes + self.manifest_bytes + self.retained_bytes

    @property
    def required_free_bytes(self) -> int:
        """Include explicitly requested rollback copying, not already allocated data."""
        return self.staging_bytes + self.rollback_copy_bytes


def _estimate_resources(
    inventory: _Inventory, *, manifest_plaintext_bytes: int, retained_bytes: int = 0, rollback_copy_bytes: int = 0
) -> _ResourceEstimate:
    """Account for bounded actual manifest serialization and future staging payload.

    The caller supplies actual serialized manifest length once Thread 04 exists;
    inventory alone cannot know its IDs/metadata serialization. Retained bytes
    and rollback-copy bytes are explicit hooks for later merge/transactions.
    Estimates exclude filesystem allocation, journals, and metadata overhead.

    :param inventory: Included plaintext file records.
    :param manifest_plaintext_bytes: Actual serialized manifest length, before encryption.
    :param retained_bytes: Existing ciphertext that later merge planning must stage.
    :param rollback_copy_bytes: Additional copies required by a later transaction plan.
    :returns: Payload totals without allocation, encryption, or destination creation.
    :raises _ConfigurationError: A size or object/manifest cap is invalid.
    """
    for size in (retained_bytes, rollback_copy_bytes):
        if type(size) is not int or size < 0:
            raise _ConfigurationError('Resource sizes must be nonnegative integers.')
    manifest_bytes = _fernet_size(manifest_plaintext_bytes)
    _check_encrypted_size(manifest_bytes)
    object_bytes = 0
    for entry in inventory.entries:
        if entry.kind == 'file':
            size = _fernet_size(entry.size)
            _check_encrypted_size(size)
            object_bytes += size
    return _ResourceEstimate(object_bytes, manifest_bytes, retained_bytes, rollback_copy_bytes)


def _check_space(parent: Path, estimate: _ResourceEstimate) -> None:
    """Check existing staging-parent permissions/free space without reserving it.

    :param parent: Existing location chosen by future transaction planning.
    :param estimate: Additional payload bytes required there.
    :raises _OperationalError: Access, free space, or filesystem identity checks fail.
    :raises _ConfigurationError: The parent is missing, unsafe, or incorrectly typed.
    """
    state = _inspect_path(parent)
    try:
        if not os.access(parent, os.W_OK | os.X_OK):
            raise _OperationalError('Staging parent is not writable/searchable; no paths were created.')
        if shutil.disk_usage(parent).free < estimate.required_free_bytes:
            raise _OperationalError('Insufficient free staging space; no paths were created.')
        _recheck_path(state)
    except OSError:
        raise _OperationalError('Cannot estimate staging space; check directory access permissions.') from None

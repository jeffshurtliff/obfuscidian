# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.paths
:Synopsis:          Internal read-only filesystem and target path preflight
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from __future__ import annotations

import os
import re
import stat
import unicodedata
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError


@dataclass(frozen=True)
class _Fingerprint:
    """Capture identity and change indicators, excluding read-sensitive access time."""

    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def _from_stat(cls, info: os.stat_result) -> _Fingerprint:
        """Capture one no-follow stat result."""
        return cls(info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    def _same_object(self, info: os.stat_result) -> bool:
        """Compare identity and type without treating directory time as identity."""
        return (self.device, self.inode, stat.S_IFMT(self.mode)) == (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


@dataclass(frozen=True)
class _PathState:
    """Retain existing component identities and an optional absent final component.

    Paths are private in-memory state, never diagnostic output. Consumers must
    recheck immediately before I/O; this is not an atomic filesystem snapshot.
    """

    path: Path = field(repr=False)
    components: tuple[tuple[Path, _Fingerprint], ...] = field(repr=False)
    exists: bool


def _is_link(info: os.stat_result) -> bool:
    """Recognize symlinks and all Windows reparse points, including junctions."""
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    )


def _absolute_path(path: Path) -> Path:
    """Require resolved configuration without silently collapsing traversal or links."""
    if not path.is_absolute() or '..' in path.parts or '\0' in str(path):
        raise _ConfigurationError('Preflight requires absolute paths without parent traversal or null characters.')
    return path


def _inspect_path(path: Path, *, kind: str = 'directory', allow_missing: bool = False) -> _PathState:
    """Inspect every path component without resolving or following links.

    :param path: Absolute source, destination, or key location.
    :param kind: Required final type, either directory or file.
    :param allow_missing: Permit only an absent final directory component.
    :returns: Protected filesystem identities for subsequent rechecks.
    :raises _ConfigurationError: An unsafe, missing, or incorrectly typed component exists.
    :raises _OperationalError: Filesystem inspection fails.
    """
    _absolute_path(path)
    if kind not in {'directory', 'file'}:
        raise _ConfigurationError('Unsupported preflight path type.')
    components = []
    try:
        for component in (*reversed(path.parents), path):
            final = component == path
            try:
                info = component.lstat()
            except FileNotFoundError:
                if final and allow_missing and kind == 'directory':
                    return _PathState(path, tuple(components), False)
                raise _ConfigurationError('Required path parents and source locations must already exist.') from None
            expected = stat.S_ISREG if final and kind == 'file' else stat.S_ISDIR
            if _is_link(info) or not expected(info.st_mode):
                raise _ConfigurationError('Path components must have the required type without links or junctions.')
            components.append((component, _Fingerprint._from_stat(info)))
        return _PathState(path, tuple(components), True)
    except OSError:
        raise _OperationalError('Cannot inspect the selected location; check access permissions.') from None


def _recheck_path(state: _PathState, *, content: bool = False) -> None:
    """Reject replaced ancestors, changed final metadata, or a newly created target.

    :param state: A previously inspected location.
    :param content: Also compare final size, mode, and modification/change times.
    :raises _OperationalError: The location changed or cannot be rechecked.
    """
    try:
        for path, recorded in state.components:
            current = path.lstat()
            if _is_link(current) or not recorded._same_object(current):
                raise _OperationalError('Filesystem identity changed; stop other writers and retry.')
            if content and path == state.path and recorded != _Fingerprint._from_stat(current):
                raise _OperationalError('Filesystem content changed; stop other writers and retry.')
        if not state.exists:
            try:
                state.path.lstat()
            except FileNotFoundError:
                return
            raise _OperationalError('Destination appeared during preflight; stop other writers and retry.')
    except OSError:
        raise _OperationalError('Cannot recheck the selected location; no successful operation is reported.') from None


@contextmanager
def _directory_handle(state: _PathState) -> Iterator[int | None]:
    """Anchor POSIX traversal to no-follow handles; recheck on other platforms."""
    descriptors = []
    try:
        if not state.exists:
            raise _ConfigurationError('Traversal requires an existing directory.')
        if os.name == 'posix':
            for path, recorded in state.components:
                descriptor = os.open(
                    str(path) if not descriptors else path.name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptors[-1] if descriptors else None,
                )
                descriptors.append(descriptor)
                info = os.fstat(descriptor)
                if _is_link(info) or not recorded._same_object(info):
                    raise _OperationalError('Directory identity changed during traversal; retry after stopping other writers.')
        _recheck_path(state)
        yield descriptors[-1] if descriptors else None
        _recheck_path(state)
    except OSError:
        raise _OperationalError('Cannot access the selected directory safely; check permissions and other writers.') from None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _child_state(parent: _PathState, name: str, info: os.stat_result) -> _PathState:
    """Extend a protected directory chain with a no-follow inspected child."""
    path = parent.path / name
    return _PathState(path, (*parent.components, (path, _Fingerprint._from_stat(info))), True)


def _validate_relative_path(value: str, *, windows: bool = False) -> tuple[str, ...]:
    """Validate lossless manifest-relative names for a selected target platform.

    POSIX control characters and Unicode are preserved. Windows additionally
    rejects reserved devices, forbidden characters, and trailing dots/spaces.

    :param value: A forward-slash relative file or directory path.
    :param windows: Apply Windows component restrictions.
    :returns: Validated components without normalization or renaming.
    :raises _ConfigurationError: A path is unsafe or unrepresentable.
    """
    if not isinstance(value, str) or not value or '\\' in value or '\0' in value or PureWindowsPath(value).drive:
        raise _ConfigurationError('Relative paths must be nonempty and contain no drives, backslashes, or null characters.')
    parts = tuple(value.split('/'))
    if any(part in {'', '.', '..'} for part in parts):
        raise _ConfigurationError('Relative paths must not contain absolute, empty, or traversal components.')
    try:
        value.encode('utf-8', errors='strict')
    except UnicodeError:
        raise _ConfigurationError('Names must be losslessly representable in UTF-8.') from None
    if windows:
        for part in parts:
            stem = part.split('.')[0].rstrip(' ').upper()
            if (
                stem in const.WINDOWS_RESERVED_NAMES
                or part.endswith(('.', ' '))
                or any(ord(character) < 32 or character in '<>:"|?*' for character in part)
            ):
                raise _ConfigurationError('A relative path cannot be represented on the Windows target.')
    return parts


@dataclass(frozen=True)
class _TargetRules:
    """Describe target filesystem comparison and length constraints without writes.

    Callers must supply the actual target's case/normalization behavior. No
    writable probe or platform-wide filesystem assumption is made here.

    :param case_sensitive: Whether differently cased components stay distinct.
    :param normalization: Unicode comparison form, or None for exact comparison.
    :param windows: Apply Windows naming and UTF-16 length rules.
    :param component_limit: Maximum component length in bytes or Windows UTF-16 units.
    :param path_limit: Maximum full target length in the same units, or None.
    """

    case_sensitive: bool
    normalization: str | None = None
    windows: bool = False
    component_limit: int | None = None
    path_limit: int | None = None


def _validate_target_paths(paths: Iterable[str], rules: _TargetRules, *, destination: Path | None = None) -> None:
    """Reject duplicate, case/Unicode, ancestor-name, and length collisions.

    :param paths: Included relative paths; parent prefixes are checked too.
    :param rules: Explicit target filesystem constraints.
    :param destination: Required absolute target prefix when enforcing full path length.
    :raises _ConfigurationError: Names collide or exceed the selected constraints.
    """
    if rules.normalization not in {None, 'NFC', 'NFD', 'NFKC', 'NFKD'}:
        raise _ConfigurationError('Unsupported target Unicode comparison form.')
    if any(limit is not None and (type(limit) is not int or limit < 1) for limit in (rules.component_limit, rules.path_limit)):
        raise _ConfigurationError('Target path limits must be positive integers.')
    if rules.path_limit is not None and destination is None:
        raise _ConfigurationError('A target prefix is required to check full path length.')
    if destination is not None:
        _absolute_path(destination)
    seen = set()
    prefixes: dict[tuple[str, ...], tuple[str, ...]] = {}
    for value in paths:
        parts = _validate_relative_path(value, windows=rules.windows)
        if value in seen:
            raise _ConfigurationError('Included paths contain a duplicate target name.')
        seen.add(value)
        canonical = []
        for index, part in enumerate(parts):
            length = len(part.encode('utf-16-le')) // 2 if rules.windows else len(part.encode('utf-8'))
            if rules.component_limit is not None and length > rules.component_limit:
                raise _ConfigurationError('A target component exceeds the filesystem length limit.')
            compared = unicodedata.normalize(rules.normalization, part) if rules.normalization else part
            canonical.append(compared if rules.case_sensitive else compared.casefold())
            key, original = tuple(canonical), parts[: index + 1]
            if key in prefixes and prefixes[key] != original:
                raise _ConfigurationError('Included paths collide under target case or Unicode comparison.')
            prefixes[key] = original
        if rules.path_limit is not None:
            full = str(destination / Path(*parts))
            length = len(full.encode('utf-16-le')) // 2 if rules.windows else len(full.encode('utf-8'))
            if length > rules.path_limit:
                raise _ConfigurationError('A target path exceeds the filesystem length limit.')


@dataclass(frozen=True)
class _VaultPaths:
    """Retain read-only source, destination, key, and mirror namespace identities."""

    origin: _PathState
    mirror: _PathState
    key: _PathState
    mirror_entries: tuple[_PathState, ...]

    def _recheck(self) -> None:
        """Reject location or inspected mirror changes before later operations."""
        for state in (self.origin, self.mirror, self.key, *self.mirror_entries):
            _recheck_path(state, content=True)


def _check_mirror_namespace(mirror: _PathState) -> tuple[_PathState, ...]:
    """Refuse unmanaged names/types without authenticating the future backup format."""
    if not mirror.exists:
        return ()
    inspected = []
    pending = [(mirror, 'root')]
    while pending:
        parent, level = pending.pop()
        with _directory_handle(parent) as handle:
            with os.scandir(handle if handle is not None else parent.path) as scan:
                for entry in scan:
                    name = entry.name
                    if level == 'root':
                        allowed = name in {const.GIT_METADATA, const.GIT_IGNORE, const.MANAGED_DIRECTORY}
                    elif level == 'managed':
                        allowed = name in {const.MANIFEST_FILENAME, const.OBJECTS_DIRECTORY}
                    else:
                        allowed = re.fullmatch(const.OBJECT_FILENAME_PATTERN, name) is not None
                    if not allowed:
                        raise _ConfigurationError(
                            'Mirror contains unmanaged entries; move them outside the mirror before retrying.'
                        )
                    info = entry.stat(follow_symlinks=False)
                    directory = (level == 'root' and name == const.MANAGED_DIRECTORY) or (
                        level == 'managed' and name == const.OBJECTS_DIRECTORY
                    )
                    valid_type = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
                    if level == 'root' and name == const.GIT_METADATA:
                        valid_type = stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
                    if _is_link(info) or not valid_type:
                        raise _ConfigurationError(
                            'Mirror controls and managed entries must have safe types without links or junctions.'
                        )
                    child = _child_state(parent, name, info)
                    inspected.append(child)
                    if directory:
                        pending.append((child, 'managed' if level == 'root' else 'objects'))
            _recheck_path(parent, content=True)
    return tuple(sorted(inspected, key=lambda item: item.path.parts))


def _preflight_vault_paths(origin: Path, mirror: Path, key: Path) -> _VaultPaths:
    """Validate separated vault locations and external key custody without writes.

    Only the mirror's last component may be missing. Mirror namespace checks
    do not authenticate its manifest, validate Git metadata contents, choose
    staging locations, or authorize publication; those remain later threads.

    :param origin: Existing read-only source directory.
    :param mirror: Existing mirror or absent final destination directory.
    :param key: Existing regular selected key outside both vaults.
    :returns: Protected identities to recheck during future operations.
    :raises _ConfigurationError: A location violates the approved safety contract.
    :raises _OperationalError: Filesystem inspection fails or changes.
    """
    source = _inspect_path(origin)
    target = _inspect_path(mirror, allow_missing=True)
    selected_key = _inspect_path(key, kind='file')
    if origin == Path(origin.anchor) or mirror == Path(mirror.anchor):
        raise _ConfigurationError('Filesystem roots cannot be vault operation targets.')
    if origin.is_relative_to(mirror) or mirror.is_relative_to(origin):
        raise _ConfigurationError('Origin and mirror must be separate and must not overlap or nest.')
    # Check protected ancestor identities as well as spelling (case variants and aliases).
    for vault in (source, target):
        identity = vault.components[-1][1] if vault.exists else None
        other = target if vault is source else source
        if identity is not None and any(
            (identity.device, identity.inode) == (recorded.device, recorded.inode) for _, recorded in other.components
        ):
            raise _ConfigurationError('Vault locations overlap by filesystem identity.')
        if key.is_relative_to(vault.path) or (
            identity is not None
            and any(
                (identity.device, identity.inode) == (recorded.device, recorded.inode) for _, recorded in selected_key.components
            )
        ):
            raise _ConfigurationError('Selected key must remain outside both vault locations.')
    # A hard-linked key is inside a vault too, even if its selected name is outside.
    try:
        namespace = _check_mirror_namespace(target)
    except OSError:
        raise _OperationalError('Cannot inspect mirror entries safely; check permissions and other writers.') from None
    key_identity = selected_key.components[-1][1]
    if any(
        (key_identity.device, key_identity.inode) == (item.components[-1][1].device, item.components[-1][1].inode)
        for item in namespace
    ):
        raise _ConfigurationError('Selected key has a file alias inside the mirror.')
    result = _VaultPaths(source, target, selected_key, namespace)
    result._recheck()
    return result

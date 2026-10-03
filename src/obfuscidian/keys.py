# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.keys
:Synopsis:          Internal secure Fernet key creation and bounded loading
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from __future__ import annotations

import base64
import binascii
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError


@dataclass(frozen=True)
class _Identity:
    """Retain a path and filesystem identity for immediate pre/post-I/O rechecks."""

    path: Path
    device: int
    inode: int


def _is_link(info: os.stat_result) -> bool:
    """Reject symlinks and Windows reparse points, including junctions."""
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    )


def _same_identity(info: os.stat_result, identity: _Identity) -> bool:
    """Compare recorded object identity with a current stat result."""
    return (info.st_dev, info.st_ino) == (identity.device, identity.inode)


def _inspect(path: Path, *, creating: bool) -> tuple[_Identity, ...]:
    """Validate existing directory components and key type without following links."""
    identities = []
    try:
        for parent in reversed(path.parents):
            info = parent.lstat()
            if _is_link(info) or not stat.S_ISDIR(info.st_mode):
                raise _ConfigurationError('Key directory components must be existing directories without links or junctions.')
            identities.append(_Identity(parent, info.st_dev, info.st_ino))
        try:
            info = path.lstat()
        except FileNotFoundError:
            if creating:
                return tuple(identities)
            raise _ConfigurationError(
                'Selected key is missing; supply the existing key. Loading never generates a replacement.'
            ) from None
        if creating:
            raise _ConfigurationError('Key target already exists; keys are never overwritten. Choose a different alias.')
        if _is_link(info) or not stat.S_ISREG(info.st_mode):
            raise _ConfigurationError('Selected key must be a regular file without links or junctions.')
        identities.append(_Identity(path, info.st_dev, info.st_ino))
        return tuple(identities)
    except FileNotFoundError:
        raise _ConfigurationError('Key directory must already exist; no parent directories are created.') from None
    except OSError:
        raise _OperationalError('Cannot inspect the key location; check directory access permissions.') from None


def _recheck(identities: tuple[_Identity, ...]) -> None:
    """Refuse a path whose protected identity changed since inspection."""
    try:
        for identity in identities:
            info = identity.path.lstat()
            if _is_link(info) or not _same_identity(info, identity):
                raise _ConfigurationError('Key location changed during the operation; retry after stopping other writers.')
    except OSError:
        raise _OperationalError('Cannot recheck the key location; no successful operation is reported.') from None


@contextmanager
def _parent_handle(identities: tuple[_Identity, ...]) -> Iterator[int | None]:
    """Anchor POSIX I/O to no-follow directory handles; recheck on other hosts."""
    descriptors = []
    try:
        if os.name == 'posix':
            for identity in identities:
                name = str(identity.path) if not descriptors else identity.path.name
                descriptor = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptors[-1] if descriptors else None,
                )
                descriptors.append(descriptor)
                if not _same_identity(os.fstat(descriptor), identity):
                    raise _ConfigurationError('Key directory changed during the operation; no key is accepted.')
        _recheck(identities)
        yield descriptors[-1] if descriptors else None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _entry_stat(path: Path, parent: int | None) -> os.stat_result:
    """Inspect the key entry relative to a protected parent when available."""
    return os.stat(path.name if parent is not None else path, dir_fd=parent, follow_symlinks=False)


def _remove_created(path: Path, parent: int | None, identity: _Identity) -> None:
    """Remove only this operation's failed key, never a replacement entry."""
    try:
        info = _entry_stat(path, parent)
        if not _same_identity(info, identity) or _is_link(info):
            raise _OperationalError('Key creation failed and the target changed; inspect the selected location before retrying.')
        os.unlink(path.name if parent is not None else path, dir_fd=parent)
    except FileNotFoundError:
        return
    except OSError:
        raise _OperationalError(
            'Key creation failed; an incomplete key may remain. Inspect the selected location before retrying.'
        ) from None


def _generate_key(path: Path, *, dry_run: bool = False) -> tuple[str, ...]:
    """Create one exclusive key, or perform read-only target validation.

    POSIX creation uses mode 0600 and anchored directory handles. Windows uses
    an owner-only protected DACL at creation; filesystem/ACL enforcement and
    concurrent parent changes remain platform constraints. No existing entry
    is deleted or overwritten. Failed creation removes only our own new entry.
    """
    identities = _inspect(path, creating=True)
    if os.name == 'nt':
        from obfuscidian._windows import _check_private_directory

        try:
            _check_private_directory(path.parent)
        except OSError:
            raise _OperationalError(
                'Cannot establish private Windows key storage; use an accessible ACL-capable volume.'
            ) from None
    if dry_run:
        _recheck(identities)
        if not os.access(path.parent, os.W_OK | os.X_OK):
            raise _OperationalError('Key directory is not writable/searchable; no key was created.')
        return ()
    try:
        with _parent_handle(identities) as parent:
            if os.name == 'nt':
                from obfuscidian._windows import _create_private_key

                descriptor = _create_private_key(path)
            else:
                descriptor = os.open(
                    path.name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    const.KEY_MODE,
                    dir_fd=parent,
                )
            try:
                try:
                    info = os.fstat(descriptor)
                except OSError:
                    raise _OperationalError(
                        'Cannot verify the new key entry; an incomplete key may remain. '
                        'Inspect the selected location before retrying.'
                    ) from None
                identity = _Identity(path, info.st_dev, info.st_ino)
                try:
                    if os.name == 'posix':
                        os.fchmod(descriptor, const.KEY_MODE)
                    _recheck(identities)
                    data = Fernet.generate_key()
                    # Validate the library-generated material before writing it.
                    Fernet(data)
                    remaining = memoryview(data)
                    while remaining:
                        written = os.write(descriptor, remaining)
                        if written == 0:
                            raise _OperationalError('Key write made no progress; creation failed.')
                        remaining = remaining[written:]
                    os.fsync(descriptor)
                    if os.name == 'nt':
                        # Release Windows exclusive sharing before path-based identity inspection.
                        os.close(descriptor)
                        descriptor = -1
                    _recheck(identities)
                    current = _entry_stat(path, parent)
                    if _is_link(current) or not _same_identity(current, identity):
                        raise _OperationalError('Key target changed during creation; no successful operation is reported.')
                except BaseException:
                    # Windows must close the handle before deleting the owned entry.
                    if descriptor != -1:
                        os.close(descriptor)
                        descriptor = -1
                    _remove_created(path, parent, identity)
                    raise
            finally:
                if descriptor != -1:
                    os.close(descriptor)
    except FileExistsError:
        raise _ConfigurationError('Key target already exists; keys are never overwritten. Choose a different alias.') from None
    except OSError:
        raise _OperationalError(
            'Cannot create the key; check directory permissions and available space. Existing keys were preserved.'
        ) from None
    return ()


def _load_key(path: Path) -> tuple[Fernet, tuple[str, ...]]:
    """Load and validate the entire bounded key without disclosure or fallback.

    Accept a canonical 44-byte URL-safe Fernet key, optionally followed by one
    LF or CRLF line ending. Reject extra data, whitespace, malformed encoding,
    special files and links. Permission warnings never modify an existing key.
    """
    identities = _inspect(path, creating=False)
    try:
        with _parent_handle(identities[:-1]) as parent:
            descriptor = os.open(
                path.name if parent is not None else path,
                os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0),
                dir_fd=parent,
            )
            with os.fdopen(descriptor, 'rb') as source:
                before = os.fstat(source.fileno())
                if not stat.S_ISREG(before.st_mode) or not _same_identity(before, identities[-1]):
                    raise _ConfigurationError('Selected key changed during loading; no key is accepted.')
                data = source.read(const.KEY_ENCODED_SIZE + 3)
                after = os.fstat(source.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                ):
                    raise _OperationalError('Selected key changed during loading; retry after stopping other writers.')
                _recheck(identities)
    except OSError:
        raise _OperationalError(
            'Cannot read the selected key; check file access permissions. No replacement was generated.'
        ) from None
    if data.endswith(b'\r\n'):
        data = data[:-2]
    elif data.endswith(b'\n'):
        data = data[:-1]
    try:
        decoded = base64.b64decode(data, altchars=b'-_', validate=True)
        if len(data) != const.KEY_ENCODED_SIZE or base64.urlsafe_b64encode(decoded) != data:
            raise ValueError
        cipher = Fernet(data)
    except (ValueError, binascii.Error):
        raise _ConfigurationError(
            'Selected key is not a complete valid Fernet key; supply the original key. No replacement was generated.'
        ) from None
    warnings = []
    if os.name == 'posix':
        if stat.S_IMODE(after.st_mode) & 0o077 or after.st_uid != os.getuid():
            warnings.append('Selected key permissions or ownership are insecure; restrict access to the key owner (mode 0600).')
    else:
        warnings.append(const.WINDOWS_PERMISSION_WARNING)
    return cipher, tuple(warnings)

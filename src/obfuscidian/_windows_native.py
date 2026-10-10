# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows_native
:Synopsis:          Internal native Windows safety primitives awaiting qualification
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import ctypes
import hashlib
import ntpath
import os
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from obfuscidian import constants as const


class _NativeSafetyError(OSError):
    """Report a redacted native refusal without exposing a path or payload."""


def _fail(message: str = 'Native Windows safety check failed; preserve pending artifacts.') -> _NativeSafetyError:
    """Return a path-free failure, including for ambiguous native I/O results."""
    return _NativeSafetyError(message)


def _component(name: str) -> str:
    """Validate one conservative Windows namespace component before any API call."""
    try:
        units = len(name.encode('utf-16-le')) // 2 if isinstance(name, str) else 0
    except UnicodeError:
        raise _fail('Invalid Windows component encoding.') from None
    if (
        not isinstance(name, str)
        or not name
        or name in ('.', '..')
        or name[-1] in ' .'
        or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in name)
        or name.split('.')[0].rstrip(' ').upper() in const.WINDOWS_RESERVED_NAMES
        or units > 255
    ):
        raise _fail('Unsafe Windows component refused.')
    return name


def _absolute(path: Path | str) -> str:
    """Reject relative, UNC/device, traversal and unresolved short-name locations."""
    text = str(path)
    drive, tail = ntpath.splitdrive(text)
    if len(drive) != 2 or drive[1] != ':' or not drive[0].isascii() or not drive[0].isalpha() or not tail.startswith('\\'):
        raise _fail('Windows mutation requires an ordinary absolute local drive path.')
    parts = tail.split('\\')[1:]
    if parts and parts[-1] == '':
        parts.pop()
    for part in parts:
        _component(part)
    if '/' in text or '~' in text or len(text.encode('utf-16-le')) // 2 >= const.WINDOWS_PATH_CHARS:
        raise _fail('Unresolved Windows path alias refused.')
    return drive.upper() + '\\' + '\\'.join(parts)


def _sid_bytes(data: bytes) -> bytes:
    """Require an exact bounded revision-1 SID representation."""
    if len(data) < 8 or data[0] != 1 or data[1] > 15 or len(data) != 8 + 4 * data[1]:
        raise _fail('Invalid Windows owner SID.')
    return data


def _private_acl(data: bytes, owner: bytes, *, directory: bool) -> None:
    """Parse the entire bounded ACL and require precisely the creator's one ACE.

    The explicit file policy has no ACE flags; directories have OI|CI so future
    trusted children can inherit. Reused controls still require protection and
    an explicit ACE, checked separately on the opened security descriptor.
    """
    _sid_bytes(owner)
    if len(data) < 8 or len(data) > const.WINDOWS_SECURITY_BYTES:
        raise _fail('Invalid private Windows ACL.')
    revision, reserved, size, count, reserved2 = struct.unpack_from('<BBHHH', data)
    if revision != 2 or reserved or reserved2 or size != len(data) or count != 1:
        raise _fail('Unexpected private Windows ACL policy.')
    if len(data) < 16:
        raise _fail('Incomplete private Windows ACE.')
    kind, flags, ace_size, mask = struct.unpack_from('<BBHI', data, 8)
    if kind != 0 or flags != (3 if directory else 0) or ace_size != len(data) - 8 or mask != const.WINDOWS_FILE_ALL_ACCESS:
        raise _fail('Unsafe or unsupported private Windows grant.')
    if _sid_bytes(data[16:]) != owner:
        raise _fail('Private Windows grant belongs to an unexpected owner.')


@dataclass(frozen=True)
class _Identity:
    """Retain full native identity and mutable metadata for explicit rechecks."""

    volume: int
    file_id: bytes
    directory: bool
    attributes: int
    size: int
    links: int
    created: int
    accessed: int
    written: int
    changed: int

    def _same_object(self, other: _Identity) -> bool:
        """Compare the stable full ID and kind, without hiding mutable changes."""
        return (self.volume, self.file_id, self.directory) == (other.volume, other.file_id, other.directory)


class _Api:
    """Load precisely typed Win32 declarations only on native 64-bit Windows."""

    def __init__(self) -> None:
        if os.name != 'nt' or ctypes.sizeof(ctypes.c_void_p) != 8:
            raise _fail('These primitives require native 64-bit Windows.')
        from ctypes import wintypes as wt

        self.wt = wt
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.advapi = ctypes.WinDLL('advapi32', use_last_error=True)
        ptr = ctypes.c_void_p
        dword = wt.DWORD
        boolean = wt.BOOL
        handle = wt.HANDLE
        wide = wt.LPCWSTR
        lpwide = wt.LPWSTR
        pword = ctypes.POINTER(dword)
        pptr = ctypes.POINTER(ptr)

        class _SecurityAttributes(ctypes.Structure):
            _fields_ = [('length', dword), ('descriptor', ptr), ('inherit', boolean)]

        class _Basic(ctypes.Structure):
            _fields_ = [(name, ctypes.c_int64) for name in ('created', 'accessed', 'written', 'changed')] + [
                ('attributes', dword)
            ]

        class _Standard(ctypes.Structure):
            _fields_ = [
                ('allocation', ctypes.c_int64),
                ('size', ctypes.c_int64),
                ('links', dword),
                ('pending', ctypes.c_ubyte),
                ('directory', ctypes.c_ubyte),
            ]

        class _Id(ctypes.Structure):
            _fields_ = [('volume', ctypes.c_uint64), ('file_id', ctypes.c_ubyte * 16)]

        class _Rename(ctypes.Structure):
            # The first union occupies a DWORD even for FileRenameInfo's BOOLEAN.
            _fields_ = [('flags', dword), ('root', handle), ('length', dword), ('name', ctypes.c_uint16 * 1)]

        self.SecurityAttributes = _SecurityAttributes
        self.Basic = _Basic
        self.Standard = _Standard
        self.Id = _Id
        self.Rename = _Rename
        declarations = (
            ('CreateFileW', handle, [wide, dword, dword, ctypes.POINTER(_SecurityAttributes), dword, dword, handle]),
            ('CreateDirectoryW', boolean, [wide, ctypes.POINTER(_SecurityAttributes)]),
            ('CloseHandle', boolean, [handle]),
            ('GetHandleInformation', boolean, [handle, pword]),
            ('GetFileType', dword, [handle]),
            ('GetFileInformationByHandleEx', boolean, [handle, ctypes.c_int, ptr, dword]),
            ('SetFileInformationByHandle', boolean, [handle, ctypes.c_int, ptr, dword]),
            ('GetFinalPathNameByHandleW', dword, [handle, lpwide, dword, dword]),
            ('GetVolumeInformationByHandleW', boolean, [handle, lpwide, dword, pword, pword, pword, lpwide, dword]),
            ('GetDriveTypeW', dword, [wide]),
            ('GetCurrentProcess', handle, []),
            ('GetCurrentThread', handle, []),
            ('LocalFree', ptr, [ptr]),
            ('SetFilePointerEx', boolean, [handle, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), dword]),
            ('ReadFile', boolean, [handle, ptr, dword, pword, ptr]),
            ('WriteFile', boolean, [handle, ptr, dword, pword, ptr]),
            ('FlushFileBuffers', boolean, [handle]),
            ('SetEndOfFile', boolean, [handle]),
        )
        for name, result, arguments in declarations:
            self._bind(self.kernel, name, result, arguments)
        security = (
            ('OpenThreadToken', boolean, [handle, dword, boolean, ctypes.POINTER(handle)]),
            ('OpenProcessToken', boolean, [handle, dword, ctypes.POINTER(handle)]),
            ('GetTokenInformation', boolean, [handle, ctypes.c_int, ptr, dword, pword]),
            ('IsValidSid', boolean, [ptr]),
            ('GetLengthSid', dword, [ptr]),
            ('ConvertSidToStringSidW', boolean, [ptr, ctypes.POINTER(lpwide)]),
            ('ConvertStringSecurityDescriptorToSecurityDescriptorW', boolean, [wide, dword, pptr, pword]),
            ('GetSecurityInfo', dword, [handle, dword, dword, pptr, pptr, pptr, pptr, pptr]),
            ('IsValidSecurityDescriptor', boolean, [ptr]),
            ('GetSecurityDescriptorControl', boolean, [ptr, ctypes.POINTER(ctypes.c_uint16), pword]),
            ('GetSecurityDescriptorDacl', boolean, [ptr, ctypes.POINTER(boolean), pptr, ctypes.POINTER(boolean)]),
            ('IsValidAcl', boolean, [ptr]),
        )
        for name, result, arguments in security:
            self._bind(self.advapi, name, result, arguments)

    @staticmethod
    def _bind(library: object, name: str, result: object, arguments: list[object]) -> None:
        """Set pointer-width-safe signatures without relying on ctypes defaults."""
        function = getattr(library, name)
        function.argtypes = arguments
        function.restype = result

    def _check(self, success: object) -> None:
        """Refuse a failed native call without formatting a sensitive OS message."""
        if not success:
            raise _fail()

    def _owner(self) -> tuple[bytes, str]:
        """Read the effective user token; fall back only for ERROR_NO_TOKEN."""
        token = self.wt.HANDLE()
        if not self.advapi.OpenThreadToken(self.kernel.GetCurrentThread(), const.WINDOWS_TOKEN_QUERY, True, ctypes.byref(token)):
            if ctypes.get_last_error() != 1008:
                raise _fail('Cannot query the effective Windows owner.')
            self._check(
                self.advapi.OpenProcessToken(self.kernel.GetCurrentProcess(), const.WINDOWS_TOKEN_QUERY, ctypes.byref(token))
            )
        try:
            needed = self.wt.DWORD()
            self.advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
            if not 8 <= needed.value <= const.WINDOWS_SECURITY_BYTES:
                raise _fail('Invalid effective Windows owner information.')
            buffer = ctypes.create_string_buffer(needed.value)
            self._check(self.advapi.GetTokenInformation(token, 1, buffer, len(buffer), ctypes.byref(needed)))
            sid = ctypes.c_void_p.from_buffer(buffer).value
            # TOKEN_USER's pointer must point into the returned bounded buffer.
            start = ctypes.addressof(buffer)
            if sid is None or not start <= sid <= start + len(buffer) - 8:
                raise _fail()
            length = 8 + 4 * ctypes.string_at(sid, 2)[1]
            if sid + length > start + len(buffer):
                raise _fail()
            raw = _sid_bytes(ctypes.string_at(sid, length))
            text = self.wt.LPWSTR()
            self._check(self.advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)))
            try:
                return raw, text.value
            finally:
                self._check(self.kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p)) is None)
        finally:
            self._check(self.kernel.CloseHandle(token))

    @contextmanager
    def _security(self, *, directory: bool) -> Iterator[object]:
        """Apply the effective owner and exact protected ACL during creation."""
        _, sid = self._owner()
        flags = 'OICI' if directory else ''
        descriptor = ctypes.c_void_p()
        sddl = f'O:{sid}D:P(A;{flags};FA;;;{sid})'
        self._check(self.advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, ctypes.byref(descriptor), None))
        try:
            yield self.SecurityAttributes(ctypes.sizeof(self.SecurityAttributes), descriptor, False)
        finally:
            self._check(self.kernel.LocalFree(descriptor) is None)

    def _open(
        self,
        path: str,
        *,
        directory: bool,
        create: bool = False,
        writable: bool = False,
        exclusive: bool = False,
        removable: bool = False,
        security: object = None,
    ) -> _Handle:
        """Open a non-inherited no-follow handle with explicit sharing and rights."""
        rights = const.WINDOWS_READ_CONTROL | const.WINDOWS_GENERIC_READ
        if writable:
            rights |= const.WINDOWS_GENERIC_WRITE
        if removable:
            rights |= const.WINDOWS_DELETE
        raw = self.kernel.CreateFileW(
            path,
            rights,
            0 if exclusive else const.WINDOWS_SHARE_READ,
            ctypes.byref(security) if security is not None else None,
            const.WINDOWS_CREATE_NEW if create else const.WINDOWS_OPEN_EXISTING,
            const.WINDOWS_OPEN_FLAGS,
            None,
        )
        if raw == self.wt.HANDLE(-1).value:
            error = ctypes.get_last_error()
            if error in (80, 183):
                raise FileExistsError('Native Windows target already exists.')
            raise _fail('Native Windows open refused; an entry may be missing, unsafe or held by another process.')
        handle = _Handle(self, raw, path)
        try:
            flags = self.wt.DWORD()
            self._check(self.kernel.GetHandleInformation(raw, ctypes.byref(flags)))
            if flags.value & 1:
                raise _fail('Inherited native Windows handle refused.')
            identity = handle._identity()
            if identity.directory != directory:
                raise _fail('Unexpected Windows object kind.')
            handle.identity = identity
            return handle
        except BaseException:
            handle._close()
            raise


class _Handle:
    """Own exactly one native handle; closing never deletes pending evidence."""

    def __init__(self, api: _Api, raw: int, path: str) -> None:
        self.api = api
        self.raw = raw
        self.path = path
        self.identity: _Identity | None = None
        self.parent: _Guard | None = None
        self.can_write_record = False
        self.ownership = False

    def __enter__(self) -> _Handle:
        return self

    def __exit__(self, *args: object) -> None:
        self._close()

    def _close(self) -> None:
        """Check close failure and prevent double close/accidental handle reuse."""
        if self.raw is not None:
            raw, self.raw = self.raw, None
            self.api._check(self.api.kernel.CloseHandle(raw))

    def _require_open(self) -> None:
        """Refuse use after ownership release before invoking a native API."""
        if self.raw is None:
            raise _fail('Native Windows handle is closed.')

    def _information(self, kind: int, record: object) -> object:
        """Query a fully sized typed record on the held object."""
        self._require_open()
        self.api._check(self.api.kernel.GetFileInformationByHandleEx(self.raw, kind, ctypes.byref(record), ctypes.sizeof(record)))
        return record

    def _identity(self) -> _Identity:
        """Require disk, nonreparse ordinary objects and full nonzero native IDs."""
        self._require_open()
        if self.api.kernel.GetFileType(self.raw) != 1:
            raise _fail('Non-disk Windows object refused.')
        basic = self._information(const.WINDOWS_BASIC_INFORMATION, self.api.Basic())
        standard = self._information(const.WINDOWS_STANDARD_INFORMATION, self.api.Standard())
        identifier = self._information(const.WINDOWS_ID_INFORMATION, self.api.Id())
        directory = bool(standard.directory)
        if (
            basic.attributes & const.WINDOWS_UNSAFE_ATTRIBUTES
            or standard.pending
            or bool(basic.attributes & const.WINDOWS_ATTRIBUTE_DIRECTORY) != directory
            or (not directory and standard.links != 1)
            or standard.size < 0
            or not identifier.volume
            or not any(identifier.file_id)
        ):
            raise _fail('Unsafe Windows identity, attributes or multiple file links refused.')
        return _Identity(
            identifier.volume,
            bytes(identifier.file_id),
            directory,
            basic.attributes,
            standard.size,
            standard.links,
            basic.created,
            basic.accessed,
            basic.written,
            basic.changed,
        )

    def _recheck(self, expected: _Identity, *, metadata: bool = True) -> _Identity:
        """Refuse substitution or mutable metadata changes on the held object."""
        actual = self._identity()
        if not expected._same_object(actual) or (metadata and actual != expected):
            raise _fail('Windows object changed; preserve pending artifacts.')
        return actual

    def _final_path(self) -> str:
        """Obtain a normalized DOS path from the held handle, never resolve a link."""
        self._require_open()
        buffer = ctypes.create_unicode_buffer(const.WINDOWS_PATH_CHARS)
        length = self.api.kernel.GetFinalPathNameByHandleW(self.raw, buffer, len(buffer), 0)
        if not 0 < length < len(buffer) or not buffer.value.startswith('\\\\?\\'):
            raise _fail('Cannot bind the Windows namespace to its held handle.')
        return _absolute(Path(buffer.value[4:]))

    def _private(self) -> None:
        """Validate owner, protected non-null DACL and every ACE on this handle."""
        self._require_open()
        owner, dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
        result = self.api.advapi.GetSecurityInfo(
            self.raw,
            1,
            const.WINDOWS_SECURITY_INFORMATION,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0:
            raise _fail('Cannot inspect private Windows access controls.')
        try:
            self.api._check(self.api.advapi.IsValidSecurityDescriptor(descriptor))
            control, revision = ctypes.c_uint16(), self.api.wt.DWORD()
            self.api._check(
                self.api.advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision))
            )
            present, defaulted = self.api.wt.BOOL(), self.api.wt.BOOL()
            self.api._check(
                self.api.advapi.GetSecurityDescriptorDacl(
                    descriptor,
                    ctypes.byref(present),
                    ctypes.byref(dacl),
                    ctypes.byref(defaulted),
                )
            )
            if (
                not owner.value
                or not dacl.value
                or not present.value
                or defaulted.value
                or not control.value & const.WINDOWS_SD_PROTECTED
            ):
                raise _fail('Unprotected, missing or null private Windows access controls refused.')
            self.api._check(self.api.advapi.IsValidSid(owner))
            length = self.api.advapi.GetLengthSid(owner)
            if not 8 <= length <= 68:
                raise _fail()
            actual_owner = _sid_bytes(ctypes.string_at(owner, length))
            expected_owner, _ = self.api._owner()
            if actual_owner != expected_owner:
                raise _fail('Unexpected Windows artifact owner refused.')
            self.api._check(self.api.advapi.IsValidAcl(dacl))
            size = struct.unpack('<H', ctypes.string_at(dacl.value + 2, 2))[0]
            if not 8 <= size <= const.WINDOWS_SECURITY_BYTES:
                raise _fail()
            _private_acl(ctypes.string_at(dacl, size), expected_owner, directory=self._identity().directory)
        finally:
            self.api._check(self.api.kernel.LocalFree(descriptor) is None)

    def _seek_start(self) -> None:
        """Rewind a held file without reopening its exclusive pathname."""
        self._require_open()
        self.api._check(self.api.kernel.SetFilePointerEx(self.raw, 0, None, 0))

    def _read(self, limit: int) -> bytes:
        """Read at most a caller bound and reject size/content changes or overflow."""
        if type(limit) is not int or limit < 0 or limit > const.MAX_ENCRYPTED_BYTES:
            raise _fail('Invalid Windows metadata read bound.')
        before = self._identity()
        if before.directory or before.size > limit:
            raise _fail('Windows control record exceeds its bound.')
        self._seek_start()
        result = bytearray()
        while len(result) <= before.size:
            buffer = ctypes.create_string_buffer(min(const.WINDOWS_IO_CHUNK, before.size + 1 - len(result)))
            read = self.api.wt.DWORD()
            self.api._check(self.api.kernel.ReadFile(self.raw, buffer, len(buffer), ctypes.byref(read), None))
            if not read.value:
                break
            if read.value > len(buffer):
                raise _fail()
            result.extend(buffer.raw[: read.value])
        after = self._recheck(before, metadata=False)
        if len(result) != before.size or (before.size, before.written, before.changed) != (
            after.size,
            after.written,
            after.changed,
        ):
            raise _fail('Windows control record changed during its bounded read.')
        return bytes(result)

    def _write(self, data: bytes, limit: int) -> None:
        """Write bounded complete binary bytes, truncate exactly and require flush.

        Only newly created controls or explicitly held ownership records may be
        written in place. This is not an interrupted-journal replacement API.
        Failure retains the handle/artifact; callers must not claim completion.
        """
        if not isinstance(data, bytes) or type(limit) is not int or not 0 <= len(data) <= limit <= const.MAX_ENCRYPTED_BYTES:
            raise _fail('Windows write exceeds its bound.')
        if not self.can_write_record:
            raise _fail('In-place Windows writes require a new file or held ownership record.')
        if self.parent is None:
            raise _fail('Windows writes require a live parent guard.')
        self.parent._check()
        self._private()
        self._seek_start()
        offset = 0
        while offset < len(data):
            chunk = data[offset : offset + const.WINDOWS_IO_CHUNK]
            buffer = ctypes.create_string_buffer(chunk)
            written = self.api.wt.DWORD()
            self.api._check(self.api.kernel.WriteFile(self.raw, buffer, len(chunk), ctypes.byref(written), None))
            if not 0 < written.value <= len(chunk):
                raise _fail('Incomplete Windows binary write; preserve pending artifacts.')
            offset += written.value
        self.api._check(self.api.kernel.SetEndOfFile(self.raw))
        self._flush()
        if self._identity().size != len(data):
            raise _fail('Windows binary write size verification failed.')

    def _flush(self) -> None:
        """Require file flush success; make no directory/power-loss guarantee."""
        self._require_open()
        self.api._check(self.api.kernel.FlushFileBuffers(self.raw))

    def _set_time(self, mtime_ns: int) -> None:
        """Set a held object's mtime at Windows 100 ns precision and verify it."""
        if type(mtime_ns) is not int or mtime_ns < 0:
            raise _fail('Invalid Windows timestamp.')
        ticks = mtime_ns // 100 + const.WINDOWS_FILETIME_EPOCH
        if ticks >= 2**63:
            raise _fail('Windows timestamp exceeds the native range.')
        if self.parent is None:
            raise _fail('Windows timestamps require a live parent guard.')
        self.parent._check()
        self._private()
        before = self._identity()
        record = self.api.Basic()
        record.written = ticks
        self.api._check(
            self.api.kernel.SetFileInformationByHandle(
                self.raw, const.WINDOWS_BASIC_INFORMATION, ctypes.byref(record), ctypes.sizeof(record)
            )
        )
        after = self._recheck(before, metadata=False)
        if after.written != ticks:
            raise _fail('Windows timestamp verification failed.')

    def _delete(self, expected: _Identity) -> None:
        """Mark only the exact held entry for deletion; nonempty directories fail.

        This never traverses children. The caller must prove its transaction's
        terminal state before deleting ownership. Deletion completes on close.
        """
        if self.parent is None:
            raise _fail('Windows deletion requires its live parent guard.')
        self.parent._check()
        self._recheck(expected)
        self._private()
        disposition = ctypes.c_ubyte(1)
        self.api._check(
            self.api.kernel.SetFileInformationByHandle(
                self.raw,
                const.WINDOWS_DISPOSITION_INFORMATION,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            )
        )

    def _release_ownership(self, terminal_record: bytes) -> None:
        """Release only held ownership whose exact bounded terminal bytes match.

        The transaction backend must validate the terminal schema/state before
        calling this primitive. No timestamp/PID heuristic or empty record can
        authorize release. A failed disposition or close remains an error.
        """
        if not self.ownership or not isinstance(terminal_record, bytes) or not terminal_record:
            raise _fail('Windows ownership release requires an explicit terminal record.')
        if self._read(const.TRANSACTION_LOCK_BYTES) != terminal_record:
            raise _fail('Windows terminal ownership record changed.')
        self._delete(self._identity())
        self._close()


class _Guard:
    """Hold every ancestor with no write/delete sharing through a primitive.

    Directory attribute access is not covered by all sharing restrictions.
    Native reparse-conversion proof remains mandatory before write integration.
    This module is internal and the CLI still refuses native transactions.
    """

    def __init__(self, path: Path) -> None:
        self.path = _absolute(path)
        self.api = _Api()
        self.handles: list[_Handle] = []

    def __enter__(self) -> _Guard:
        drive, tail = ntpath.splitdrive(self.path)
        parts = tail.split('\\')[1:]
        if parts and not parts[-1]:
            parts.pop()
        current = drive + '\\'
        try:
            for part in [None, *parts]:
                if part is not None:
                    current = ntpath.join(current, part)
                handle = self.api._open(current, directory=True)
                self.handles.append(handle)
                if ntpath.normcase(handle._final_path()) != ntpath.normcase(current):
                    raise _fail('Windows drive or namespace alias refused.')
                self._eligible(handle)
            self._check()
            return self
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *args: object) -> None:
        failure = None
        while self.handles:
            try:
                self.handles.pop()._close()
            except _NativeSafetyError as error:
                failure = error
        if failure is not None:
            raise failure

    def _eligible(self, handle: _Handle) -> None:
        """Check the opened location's volume, canonical drive type and ACL flags."""
        flags, serial = self.api.wt.DWORD(), self.api.wt.DWORD()
        filesystem = ctypes.create_unicode_buffer(261)
        self.api._check(
            self.api.kernel.GetVolumeInformationByHandleW(
                handle.raw,
                None,
                0,
                ctypes.byref(serial),
                None,
                ctypes.byref(flags),
                filesystem,
                len(filesystem),
            )
        )
        root = ntpath.splitdrive(handle._final_path())[0] + '\\'
        if (
            self.api.kernel.GetDriveTypeW(root) != const.WINDOWS_DRIVE_FIXED
            or filesystem.value != 'NTFS'
            or not flags.value & const.WINDOWS_PERSISTENT_ACLS
            or flags.value & const.WINDOWS_READ_ONLY_VOLUME
            or serial.value != handle.identity.volume & 0xFFFFFFFF
        ):
            raise _fail('Native writes require eligible local NTFS storage with persistent access controls.')

    def _check(self) -> None:
        """Requery retained ancestors; directory metadata can change with children."""
        if not self.handles:
            raise _fail('Windows parent guard is not held.')
        for handle in self.handles:
            handle._recheck(handle.identity, metadata=False)
            if ntpath.normcase(handle._final_path()) != ntpath.normcase(handle.path):
                raise _fail('Windows guarded namespace changed.')

    def _child(self, name: str) -> str:
        """Derive exactly one child beneath a live, rechecked parent."""
        self._check()
        return ntpath.join(self.path, _component(name))

    def _open_file(self, name: str, *, create: bool = False, writable: bool = False, ownership: bool = False) -> _Handle:
        """Exclusively create or acquire a private file without repairing it."""
        path = self._child(name)
        if create:
            with self.api._security(directory=False) as security:
                handle = self.api._open(
                    path, directory=False, create=True, writable=True, exclusive=ownership, removable=True, security=security
                )
        else:
            handle = self.api._open(path, directory=False, writable=writable, exclusive=ownership, removable=True)
        try:
            handle.parent = self
            handle.can_write_record = create or ownership
            handle.ownership = ownership
            handle._private()
            self._check()
            if ntpath.normcase(handle._final_path()) != ntpath.normcase(path):
                raise _fail('Windows leaf namespace alias refused.')
            return handle
        except BaseException:
            handle._close()
            raise

    def _create_directory(self, name: str) -> _Handle:
        """Create protected directory security before any descendant or payload.

        CreateDirectoryW returns no handle. If the following acquisition fails,
        retain the uncertain empty artifact instead of removing it by pathname.
        """
        path = self._child(name)
        with self.api._security(directory=True) as security:
            if not self.api.kernel.CreateDirectoryW(path, ctypes.byref(security)):
                if ctypes.get_last_error() in (80, 183):
                    raise FileExistsError('Native Windows directory already exists.')
                raise _fail('Cannot create a private Windows directory.')
        handle = self.api._open(path, directory=True, writable=True, removable=True)
        try:
            handle.parent = self
            handle._private()
            self._check()
            if ntpath.normcase(handle._final_path()) != ntpath.normcase(path):
                raise _fail('Windows leaf namespace alias refused.')
            return handle
        except BaseException:
            handle._close()
            raise

    def _rename(self, source: _Handle, name: str, expected: _Identity) -> None:
        """Publish one exact private held entry without overwriting a late target.

        Uses a full target DOS path under the retained complete guard chain;
        RootDirectory is NULL. No source handle is dropped for rename. There is
        no overwrite, copy/delete or sharing-failure fallback.
        """
        target = self._child(name)
        if source.parent is None:
            raise _fail('Windows publication requires its live source parent guard.')
        source.parent._check()
        source._recheck(expected)
        source._private()
        if expected.volume != self.handles[-1].identity.volume:
            raise _fail('Cross-volume Windows publication refused.')
        digest = None if expected.directory else hashlib.sha256(source._read(const.MAX_ENCRYPTED_BYTES)).digest()
        encoded = target.encode('utf-16-le')
        record = self.api.Rename
        size = max(ctypes.sizeof(record), record.name.offset + len(encoded) + 2)
        buffer = ctypes.create_string_buffer(size)
        header = record.from_buffer(buffer)
        header.flags, header.root, header.length = 0, None, len(encoded)
        ctypes.memmove(ctypes.addressof(buffer) + record.name.offset, encoded, len(encoded))
        self.api._check(
            self.api.kernel.SetFileInformationByHandle(
                source.raw,
                const.WINDOWS_RENAME_INFORMATION,
                buffer,
                size,
            )
        )
        # Record the new spelling even if a postcheck fails; retain the handle.
        source.path = target
        source.parent = self
        source._recheck(expected, metadata=False)
        source._private()
        if digest is not None and hashlib.sha256(source._read(const.MAX_ENCRYPTED_BYTES)).digest() != digest:
            raise _fail('Windows publication content changed; preserve pending artifacts.')
        self._check()
        if ntpath.normcase(source._final_path()) != ntpath.normcase(target):
            raise _fail('Windows publication namespace verification failed.')

    def _checkpoint(self, name: str, data: bytes, *, previous: _Handle | None = None) -> _Handle:
        """Create a bounded, flushed private checkpoint; refuse existing replacement.

        FileRenameInfo overwrite cannot compare-and-replace an exact destination
        ID while a deny-delete target handle remains held. Releasing that guard
        is unsafe. Thread 2 must resolve a separately reviewed journal protocol;
        this helper never introduces a path-based overwrite fallback.
        """
        if not isinstance(data, bytes) or len(data) > const.TRANSACTION_JOURNAL_BYTES:
            raise _fail('Windows journal exceeds its bound.')
        if previous is not None:
            raise _fail('Exact guarded Windows journal replacement remains unqualified.')
        handle = self._open_file(name, create=True)
        try:
            handle._write(data, const.TRANSACTION_JOURNAL_BYTES)
            return handle
        except BaseException:
            handle._close()
            raise

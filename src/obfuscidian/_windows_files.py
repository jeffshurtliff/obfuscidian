# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows_files
:Synopsis:          Private Windows lifecycle observations and binary reconstruction
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import ctypes
import hashlib
import ntpath
import os
import struct
from contextlib import contextmanager
from pathlib import Path

from obfuscidian import constants as const
from obfuscidian._windows_native import _api_path, _component, _fail, _Guard, _sid_bytes


def _acl(data: bytes, owner: bytes, directory: bool) -> None:
    """Accept only restorable protected allow-ACE baselines with explicit owner access.

    Inherited/unprotected/deny/object ACLs remain unsupported rather than being
    repaired. Every descendant is independently protected, so finalizing a
    directory cannot propagate grants into an unprotected reconstruction child.
    """
    if not isinstance(data, bytes) or not 8 <= len(data) <= const.WINDOWS_SECURITY_BYTES:
        raise _fail('Unsupported Windows baseline ACL.')
    revision, _, size, count, reserved = struct.unpack_from('<BBHHH', data)
    if revision != 2 or size != len(data) or reserved or data[1]:
        raise _fail('Unsupported Windows baseline ACL framing.')
    offset, owner_access = 8, False
    for _ in range(count):
        if offset + 8 > len(data):
            raise _fail()
        kind, flags, length, mask = struct.unpack_from('<BBHI', data, offset)
        if kind != 0 or flags & ~(3 if directory else 0) or length < 16 or offset + length > len(data):
            raise _fail('Unsupported Windows baseline ACE.')
        sid = _sid_bytes(data[offset + 8 : offset + length])
        owner_access |= sid == owner and mask == const.WINDOWS_FILE_ALL_ACCESS
        offset += length
    if offset != len(data) or not owner_access:
        raise _fail('Baseline must retain explicit full current-owner access.')


def _security(handle, *, baseline: bool = True) -> dict:
    """Capture exact handle-bound owner/DACL without changing production validation."""
    api = handle.api
    owner, dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    result = api.advapi.GetSecurityInfo(
        handle.raw,
        1,
        const.WINDOWS_SECURITY_INFORMATION,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result:
        raise _fail('Cannot inspect Windows baseline security.')
    try:
        api._check(api.advapi.IsValidSecurityDescriptor(descriptor))
        control, revision = ctypes.c_uint16(), api.wt.DWORD()
        api._check(api.advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)))
        if not owner.value or not dacl.value:
            raise _fail('Missing Windows baseline owner/DACL.')
        api._check(api.advapi.IsValidSid(owner))
        length = api.advapi.GetLengthSid(owner)
        if not 8 <= length <= 68:
            raise _fail()
        sid = _sid_bytes(ctypes.string_at(owner, length))
        api._check(api.advapi.IsValidAcl(dacl))
        size = struct.unpack('<H', ctypes.string_at(dacl.value + 2, 2))[0]
        if not 8 <= size <= const.WINDOWS_SECURITY_BYTES:
            raise _fail()
        acl = ctypes.string_at(dacl, size)
        protected = bool(control.value & const.WINDOWS_SD_PROTECTED)
        if baseline:
            if sid != api._owner()[0] or not protected:
                raise _fail('Unrestorable Windows baseline owner or inherited DACL refused.')
            _acl(acl, sid, handle._identity().directory)
        return {'owner': sid.hex(), 'acl': acl.hex(), 'protected': protected}
    finally:
        api._check(api.kernel.LocalFree(descriptor) is None)


def _streams(handle) -> None:
    """Refuse named streams, overflow and unknown stream enumeration responses."""
    buffer = ctypes.create_string_buffer(const.WINDOWS_SECURITY_BYTES)
    success = handle.api.kernel.GetFileInformationByHandleEx(handle.raw, const.WINDOWS_STREAM_INFORMATION, buffer, len(buffer))
    if not success:
        # Directories without a primary data stream may return EOF. All other
        # errors, including an undersized buffer, remain refusal.
        if handle._identity().directory and ctypes.get_last_error() == 38:
            return
        raise _fail('Cannot prove the absence of named Windows streams.')
    next_entry, size = struct.unpack_from('<II', buffer.raw)
    if next_entry or size > len(buffer) - 24 or size % 2:
        raise _fail('Additional or unbounded Windows streams refused.')
    name = buffer.raw[24 : 24 + size].decode('utf-16-le')
    if name != '::$DATA':
        raise _fail('Named Windows streams cannot be replaced.')


@contextmanager
def _entry(parent: Path, name: str, directory: bool, *, private: bool = False, writable: bool = False, removable: bool = False):
    """Acquire one leaf relative to a held guard, never a pathname mutation open."""
    with _Guard(parent) as guard:
        guard._check()
        handle = guard.api._open_relative(
            guard.handles[-1],
            _component(name),
            directory=directory,
            writable=writable,
            removable=removable,
            security_write=writable,
        )
        with handle:
            handle.parent = guard
            if ntpath.normcase(handle._final_path()) != ntpath.normcase(guard._child(name)):
                raise _fail('Windows lifecycle namespace alias refused.')
            if private:
                handle._private()
            yield handle
            guard._check()


def _id(handle) -> list:
    """Keep full stable native identity, never truncate the 128-bit file ID."""
    identity = handle._identity()
    return [identity.volume, identity.file_id.hex(), identity.directory]


def _record(handle, *, private: bool = False) -> dict:
    """Observe bytes, supported metadata, exact descriptor and absence of streams."""
    if private:
        handle._private()
    before = handle._identity()
    if before.attributes & ~const.WINDOWS_SUPPORTED_ATTRIBUTES:
        raise _fail('Unsupported baseline Windows attributes refused.')
    _streams(handle)
    security = _security(handle)
    data = None if before.directory else handle._read(const.MAX_ENCRYPTED_BYTES)
    after = handle._recheck(before, metadata=False)
    if (before.size, before.created, before.written, before.changed, before.attributes) != (
        after.size,
        after.created,
        after.written,
        after.changed,
        after.attributes,
    ) or _security(handle) != security:
        raise _fail('Windows payload changed during observation.')
    return {
        'id': _id(handle),
        'size': 0 if before.directory else before.size,
        'digest': None if data is None else hashlib.sha256(data).hexdigest(),
        'created': before.created,
        'written': before.written,
        'attributes': before.attributes,
        'security': security,
    }


def _names(root: Path) -> list[str]:
    """Bound observational enumeration and reject unsafe component spellings."""
    with _Guard(root) as guard:
        with os.scandir(_api_path(guard.path)) as entries:
            names = []
            for entry in entries:
                names.append(_component(entry.name))
                if len(names) > const.WINDOWS_TRANSACTION_ENTRIES:
                    raise _fail('Windows lifecycle namespace exceeds its bound.')
        guard._check()
    return sorted(names)


def _capture(root: Path, *, protected: set[str] = frozenset(), private: bool = False) -> dict:
    """Capture a bounded flat payload tree through checked native handles."""
    result = {}

    def visit(parent: Path, prefix: str, depth: int) -> None:
        if depth > const.WINDOWS_TRANSACTION_DEPTH:
            raise _fail('Windows lifecycle nesting exceeds its bound.')
        names = _names(parent)
        for name in names:
            if not prefix and name in protected:
                continue
            if name.casefold() == const.GIT_METADATA:
                raise _fail('Nested Git controls cannot be replaced.')
            relative = prefix + name
            # Type observation cannot authorize the open: the relative native
            # acquisition independently checks type, links, IDs and namespace.
            directory = (parent / name).is_dir()
            with _entry(parent, name, directory, private=private) as handle:
                result[relative] = _record(handle, private=private)
                if directory:
                    visit(parent / name, relative + '/', depth + 1)
            if len(result) > const.WINDOWS_TRANSACTION_ENTRIES:
                raise _fail('Windows lifecycle entries exceed their bound.')
        if _names(parent) != names:
            raise _fail('Windows lifecycle namespace changed during capture.')

    visit(root, '', 0)
    return result


def _mkdir(parent: Path, name: str) -> list:
    """Create an independently protected private directory and return its identity."""
    with _Guard(parent) as guard, guard._create_directory(name) as handle:
        return _id(handle)


def _write(parent: Path, name: str, data: bytes) -> None:
    """Create, flush and verify primary-stream binary data privately."""
    with _Guard(parent) as guard, guard._open_file(name, create=True) as handle:
        handle._write(data, const.MAX_ENCRYPTED_BYTES)
        if handle._read(const.MAX_ENCRYPTED_BYTES) != data:
            raise _fail('Windows staged bytes failed verification.')


def _metadata(handle, record: dict) -> None:
    """Restore supported creation/write times and attributes on a private handle."""
    handle._private()
    basic = handle.api.Basic()
    basic.created, basic.written, basic.attributes = record['created'], record['written'], record['attributes']
    handle.api._check(
        handle.api.kernel.SetFileInformationByHandle(
            handle.raw, const.WINDOWS_BASIC_INFORMATION, ctypes.byref(basic), ctypes.sizeof(basic)
        )
    )
    actual = handle._identity()
    if (actual.created, actual.written, actual.attributes) != (basic.created, basic.written, basic.attributes):
        raise _fail('Windows reconstruction metadata verification failed.')


def _copy(source: Path, saved: Path, record: dict) -> dict:
    """Create a separate verified private copy; never consume the only rollback copy."""
    directory = record['id'][2]
    with _entry(source.parent, source.name, directory) as original:
        if _record(original) != record:
            raise _fail('Original Windows payload changed before private copy.')
        if directory:
            _mkdir(saved.parent, saved.name)
        else:
            _write(saved.parent, saved.name, original._read(const.MAX_ENCRYPTED_BYTES))
        with _entry(saved.parent, saved.name, directory, private=True, writable=True) as copy:
            _metadata(copy, record)
            result = _record(copy, private=True)
        if _record(original) != record or not _logical(result, record):
            raise _fail('Windows private rollback copy verification failed.')
        return result


def _logical(actual: dict, expected: dict) -> bool:
    """Compare recoverable bytes/metadata independently of copy IDs and private ACLs."""
    return actual['id'][2] == expected['id'][2] and all(
        actual[key] == expected[key] for key in ('size', 'digest', 'created', 'written', 'attributes')
    )


def _finalize(handle, record: dict) -> None:
    """Restore an exact supported baseline DACL only at its intended destination."""
    handle._private()
    data = bytes.fromhex(record['security']['acl'])
    _acl(data, handle.api._owner()[0], handle._identity().directory)
    buffer = ctypes.create_string_buffer(data)
    _metadata(handle, record)
    handle.api._bind(
        handle.api.advapi,
        'SetSecurityInfo',
        handle.api.wt.DWORD,
        [handle.api.wt.HANDLE, handle.api.wt.DWORD, handle.api.wt.DWORD] + [ctypes.c_void_p] * 4,
    )
    result = handle.api.advapi.SetSecurityInfo(handle.raw, 1, const.WINDOWS_PROTECTED_DACL_INFORMATION, None, None, buffer, None)
    if result or _security(handle) != record['security']:
        raise _fail('Windows baseline DACL finalization failed; preserve artifacts.')


def _delete(path: Path, record: dict) -> None:
    """Dispose an exact unchanged original, using its baseline instead of private ACL policy."""
    with _entry(path.parent, path.name, record['id'][2], writable=True, removable=True) as handle:
        actual = _record(handle)
        if actual != record:
            raise _fail('Windows original changed before removal.')
        if record['id'][2]:
            with os.scandir(_api_path(handle.path)) as children:
                if next(children, None) is not None:
                    raise _fail('Unknown Windows children prevent removal.')
        disposition = ctypes.c_ubyte(1)
        handle.parent._check()
        handle.api._check(
            handle.api.kernel.SetFileInformationByHandle(
                handle.raw, const.WINDOWS_DISPOSITION_INFORMATION, ctypes.byref(disposition), ctypes.sizeof(disposition)
            )
        )


def _publication_boundary(label: str) -> None:
    """Provide private synthetic observation points while the moved handle stays held."""


def _move(source: Path, target: Path, record: dict) -> dict:
    """No-clobber publish an exact private proposal or reconstruction leaf."""
    with _entry(source.parent, source.name, record['id'][2], private=True, writable=True, removable=True) as handle:
        if _record(handle, private=True) != record:
            raise _fail('Windows proposal changed before publication.')
        with _Guard(target.parent) as guard:
            guard._rename(handle, target.name, handle._identity())
            actual = _record(handle, private=True)
            # NTFS can tunnel a removed same-name entry's creation time into a
            # rename. The exact private proposal was checked before this held
            # handle's own operation. No other metadata/content/security drift
            # may be accepted or rewritten. Recovery still requires exact records.
            if actual != {**record, 'created': actual['created']}:
                raise _fail('Windows publication changed beyond creation time; preserve pending artifacts.')
            _publication_boundary('publication-before-metadata')
            if actual['created'] != record['created']:
                _metadata(handle, record)
            actual = _record(handle, private=True)
            if actual != record:
                raise _fail('Windows publication metadata verification failed; preserve pending artifacts.')
            _publication_boundary('publication-after-metadata')
            return actual


def _directory_time(handle, record: dict) -> None:
    """Restore a surviving directory time after its fully reconciled child operations."""
    actual = _record(handle)
    expected = {**record, 'written': actual['written']}
    if actual != expected or not record['id'][2]:
        raise _fail('Surviving Windows directory changed before time restoration.')
    basic = handle.api.Basic()
    basic.written = record['written']
    handle.api._check(
        handle.api.kernel.SetFileInformationByHandle(
            handle.raw, const.WINDOWS_BASIC_INFORMATION, ctypes.byref(basic), ctypes.sizeof(basic)
        )
    )
    if _record(handle) != record:
        raise _fail('Surviving Windows directory time restoration failed.')

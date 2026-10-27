# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_native
:Synopsis:          Test portable validation and native boundary refusal
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     11 Oct 2026
"""

from __future__ import annotations

import ctypes
import os
import struct
from pathlib import Path

import pytest

from obfuscidian import _windows_native as native
from obfuscidian import constants as const

# Synthetic S-1-5-21, used only for parser fixtures, never a live access policy.
SID = b'\x01\x01\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00'


def _acl(*, directory: bool = False) -> bytes:
    """Build one explicitly synthetic exact owner grant."""
    ace = struct.pack('<BBHI', 0, 3 if directory else 0, 8 + len(SID), const.WINDOWS_FILE_ALL_ACCESS) + SID
    return struct.pack('<BBHHH', 2, 0, 8 + len(ace), 1, 0) + ace


@pytest.mark.parametrize('directory', [False, True])
def test_exact_acl_policy(directory: bool) -> None:
    native._private_acl(_acl(directory=directory), SID, directory=directory)


@pytest.mark.parametrize(
    'offset,value', [(0, 4), (1, 1), (2, 1), (4, 0), (4, 2), (6, 1), (8, 1), (8, 5), (9, 16), (9, 8), (12, 1)]
)
def test_unsafe_acl_policy_refused(offset: int, value: int) -> None:
    acl = bytearray(_acl())
    acl[offset] = value
    with pytest.raises(native._NativeSafetyError):
        native._private_acl(bytes(acl), SID, directory=False)


@pytest.mark.parametrize('data', [b'', b'\x02' * 8, b'\x01\x10' + b'\x00' * 70, SID[:-1], SID + b'\x00'])
def test_malformed_sid_refused(data: bytes) -> None:
    with pytest.raises(native._NativeSafetyError):
        native._sid_bytes(data)


def test_extra_grant_and_wrong_owner_refused() -> None:
    for data, owner in [(_acl() + _acl()[8:], SID), (_acl(), SID[:-4] + b'\x16\x00\x00\x00')]:
        with pytest.raises(native._NativeSafetyError):
            native._private_acl(data, owner, directory=False)


@pytest.mark.parametrize('foreign_owner', [False, True])
def test_descriptor_owner_validation_and_release_with_injected_metadata(foreign_owner: bool) -> None:
    """Exercise the validator and descriptor release portably, without kernel proof."""
    from types import SimpleNamespace

    owner = ctypes.create_string_buffer(SID[:-1] + b'\x01' if foreign_owner else SID)
    acl = ctypes.create_string_buffer(_acl())
    descriptor = ctypes.create_string_buffer(b'SYNTHETIC DESCRIPTOR')
    released = []

    def information(raw, kind, flags, owner_out, group, dacl_out, sacl, descriptor_out):
        owner_out._obj.value = ctypes.addressof(owner)
        dacl_out._obj.value = ctypes.addressof(acl)
        descriptor_out._obj.value = ctypes.addressof(descriptor)
        return 0

    def control(raw, flags, revision):
        flags._obj.value, revision._obj.value = const.WINDOWS_SD_PROTECTED, 1
        return True

    def dacl(raw, present, output, defaulted):
        present._obj.value, output._obj.value, defaulted._obj.value = True, ctypes.addressof(acl), False
        return True

    def release(raw):
        released.append(raw.value)
        return None

    api = object.__new__(native._Api)
    api.wt = SimpleNamespace(DWORD=ctypes.c_uint32, BOOL=ctypes.c_int32)
    api._owner = lambda: (SID, 'SYNTHETIC SID')
    api.kernel = SimpleNamespace(LocalFree=release)
    api.advapi = SimpleNamespace(
        GetSecurityInfo=information,
        IsValidSecurityDescriptor=lambda ptr: True,
        GetSecurityDescriptorControl=control,
        GetSecurityDescriptorDacl=dacl,
        IsValidSid=lambda ptr: True,
        GetLengthSid=lambda ptr: len(SID),
        IsValidAcl=lambda ptr: True,
    )
    record = native._Handle(api, 42, 'C:\\synthetic')
    record._identity = lambda: SimpleNamespace(directory=False)
    before = owner.raw, acl.raw, descriptor.raw
    if foreign_owner:
        with pytest.raises(native._NativeSafetyError, match='Unexpected Windows artifact owner'):
            record._private()
    else:
        record._private()
    assert released == [ctypes.addressof(descriptor)]
    assert (owner.raw, acl.raw, descriptor.raw) == before


@pytest.mark.parametrize(
    'name',
    [
        '',
        '.',
        '..',
        'AUX.txt',
        'NUL .txt',
        '\ud800',
        'COM¹',
        'bad:stream',
        'trailing.',
        'space ',
        'a/b',
        'a\\b',
        '\x00',
        'x' * 256,
    ],
)
def test_unsafe_component_refused(name: str) -> None:
    with pytest.raises(native._NativeSafetyError):
        native._component(name)


@pytest.mark.parametrize(
    'path', ['relative', 'C:relative', '\\\\server\\share', '\\\\?\\C:\\demo', 'C:\\a\\..\\b', 'C:\\SHORT~1', 'C:/demo']
)
def test_unsafe_path_refused_without_loading_windows(path: str) -> None:
    with pytest.raises(native._NativeSafetyError):
        native._absolute(path)


def test_safe_local_path_and_unicode_component() -> None:
    assert native._absolute(Path('C:\\synthetic\\notes')) == 'C:\\synthetic\\notes'
    assert native._component('日本語.md') == '日本語.md'


def test_internal_long_path_spelling_validates_before_adding_prefix() -> None:
    ordinary = 'C:\\' + '\\'.join(['synthetic' * 15] * 3)
    assert len(ordinary) > 260
    assert native._api_path(ordinary) == '\\\\?\\' + ordinary
    for unsafe in ['\\\\?\\C:\\synthetic', 'C:\\a\\..\\b', 'C:\\SHORT~1', '\\\\server\\share']:
        with pytest.raises(native._NativeSafetyError):
            native._api_path(unsafe)


def test_internal_long_path_bound_includes_prefix(monkeypatch) -> None:
    monkeypatch.setattr(const, 'WINDOWS_PATH_CHARS', 20)
    with pytest.raises(native._NativeSafetyError, match='native path exceeds'):
        native._api_path('C:\\' + 'x' * 13)


@pytest.mark.skipif(os.name == 'nt', reason='POSIX refusal only; native tests exercise actual APIs.')
def test_native_loader_refuses_posix() -> None:
    with pytest.raises(native._NativeSafetyError, match='native 64-bit Windows'):
        native._Api()


def test_checkpoint_replacement_refuses_before_open() -> None:
    # No simulated OS: exact overwrites are unconditionally refused.
    guard = object.__new__(native._Guard)
    with pytest.raises(native._NativeSafetyError, match='overwrite refused'):
        guard._checkpoint('journal.json', b'{}', previous=object())
    with pytest.raises(native._NativeSafetyError, match='bound'):
        guard._checkpoint('journal.json', b'x' * (const.TRANSACTION_JOURNAL_BYTES + 1))


def test_full_file_id_not_truncated() -> None:
    """Different high-order ID bytes never alias even if the low bytes match."""
    from dataclasses import replace

    identity = native._Identity(1, b'\x01' + b'\x00' * 15, False, 128, 0, 1, 1, 1, 1, 1)
    different = replace(identity, file_id=b'\x01' + b'\x00' * 14 + b'\x01')
    assert not identity._same_object(different)
    assert not identity._same_object(replace(identity, volume=2))


def test_new_checkpoint_failure_closes_handle_and_retains_artifact() -> None:
    """Supplementary fake-I/O test: failed flush never returns a successful record."""
    from types import SimpleNamespace

    events = []

    def failure(data, limit):
        events.append('partial-artifact-retained')
        raise native._NativeSafetyError('SYNTHETIC FAILURE')

    record = SimpleNamespace(_write=failure, _close=lambda: events.append('closed'))
    guard = object.__new__(native._Guard)
    guard._open_file = lambda *args, **kwargs: record
    with pytest.raises(native._NativeSafetyError):
        guard._checkpoint('journal', b'{}')
    assert events == ['partial-artifact-retained', 'closed']


def test_native_64bit_structure_layout() -> None:
    """Supplementary ABI checks use Windows fixed-width fields even on POSIX."""
    assert ctypes.sizeof(ctypes.c_void_p) == 8
    assert (ctypes.sizeof(native._UnicodeString), native._UnicodeString.buffer.offset) == (16, 8)
    assert (ctypes.sizeof(native._ObjectAttributes), native._ObjectAttributes.root.offset) == (48, 8)
    assert (native._ObjectAttributes.name.offset, native._ObjectAttributes.security.offset) == (16, 32)
    assert ctypes.sizeof(native._IoStatus) == 16
    assert (native._Rename.root.offset, native._Rename.length.offset, native._Rename.name.offset) == (8, 16, 20)
    assert ctypes.sizeof(native._Rename) == 24


@pytest.mark.parametrize('directory', [False, True])
@pytest.mark.parametrize('create', [False, True])
def test_relative_open_binds_native_root_without_pathname(directory: bool, create: bool) -> None:
    """Inspect the actual ctypes boundary; these injected calls are not Windows proof."""
    from types import SimpleNamespace

    api = object.__new__(native._Api)
    parent = SimpleNamespace(
        raw=42, path='C:\\synthetic', identity=object(), _require_open=lambda: None, _recheck=lambda *args, **kwargs: None
    )
    adopted = []
    api._adopt = lambda *args, **kwargs: adopted.append((args, kwargs))

    def create_file(raw, rights, attributes, result, allocation, file_attributes, share, disposition, options, ea, ea_length):
        actual = attributes._obj
        assert actual.root == 42
        assert actual.attributes == const.WINDOWS_OBJECT_ATTRIBUTES
        assert actual.security == (123 if create else None)
        name = actual.name.contents
        assert ctypes.string_at(name.buffer, name.length).decode('utf-16-le') == '日本語-😀'
        assert rights & const.WINDOWS_SYNCHRONIZE
        assert rights & const.WINDOWS_DELETE
        assert share == 0
        assert disposition == (2 if create else 1)
        assert options & const.WINDOWS_NATIVE_OPEN_OPTIONS == const.WINDOWS_NATIVE_OPEN_OPTIONS
        assert options & (1 | 0x40) == (1 if directory else 0x40)
        assert allocation is None and ea is None and ea_length == 0
        raw._obj.value = 99
        result._obj.information = 2 if create else 1
        return 0

    api.ntdll = SimpleNamespace(NtCreateFile=create_file)
    api._open_relative(
        parent,
        '日本語-😀',
        directory=directory,
        create=create,
        exclusive=True,
        removable=True,
        security=SimpleNamespace(descriptor=123) if create else None,
    )
    assert adopted == [((99, 'C:\\synthetic\\日本語-😀'), {'directory': directory})]


def test_path_mutation_acquisition_refuses_without_native_call() -> None:
    api = object.__new__(native._Api)
    for options in [{'create': True}, {'writable': True}, {'exclusive': True}, {'removable': True}, {'security': object()}]:
        with pytest.raises(native._NativeSafetyError, match='retained relative root'):
            api._open('C:\\synthetic', directory=True, **options)


def test_numeric_native_errors_and_uncertain_status_refuse() -> None:
    api = object.__new__(native._Api)
    with pytest.raises(FileExistsError):
        api._nt_check(-1073741771, native._IoStatus(), collision=True)
    for status, io_status in [(0x103, 0), (0xC0000022, 0), (0, 0xC0000022)]:
        with pytest.raises(native._NativeSafetyError, match='NTSTATUS') as caught:
            api._nt_check(status, native._IoStatus(io_status, 0))
        assert 'C:\\' not in str(caught.value)


def test_publication_uses_held_target_root_and_no_overwrite() -> None:
    """Inspect the rename buffer at the injected native boundary, never a DOS target."""
    from types import SimpleNamespace

    guard = object.__new__(native._Guard)
    identity = native._Identity(1, b'\x01' * 16, True, 16, 0, 1, 1, 1, 1, 1)
    root = SimpleNamespace(raw=42, identity=identity)
    guard.handles = [root]
    guard.path = 'C:\\synthetic'
    guard._check = lambda: None
    source = SimpleNamespace(
        raw=99,
        parent=guard,
        path='C:\\synthetic\\proposal',
        _recheck=lambda *args, **kwargs: identity,
        _private=lambda: None,
        _final_path=lambda: 'C:\\synthetic\\published',
    )

    def rename(raw, status, buffer, length, information_class):
        header = native._Rename.from_buffer(buffer)
        assert raw == 99 and header.root == 42 and header.flags == 0
        assert length == ctypes.sizeof(native._Rename) + header.length
        assert (
            ctypes.string_at(ctypes.addressof(buffer) + native._Rename.name.offset, header.length).decode('utf-16-le')
            == 'published'
        )
        assert information_class == 10
        return 0

    guard.api = SimpleNamespace(
        Rename=native._Rename, ntdll=SimpleNamespace(NtSetInformationFile=rename), _nt_check=native._Api._nt_check
    )
    guard._rename(source, 'published', identity)
    assert source.parent is guard and source.path == 'C:\\synthetic\\published'

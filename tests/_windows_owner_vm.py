# -*- coding: utf-8 -*-
"""
:Module:            tests._windows_owner_vm
:Synopsis:          Explicit two-standard-account synthetic owner proof with retained custody
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     15 Oct 2026
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import ntpath
import os
import re
import struct
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

# The peer needs only an existing supported CPython, not A's private Poetry venv.
# Isolated ``python -I -S tests/_windows_owner_vm.py`` uses this reviewed source.
if __name__ == '__main__' and __package__ is None:
    _source_root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(_source_root), str(_source_root / 'src')]

from obfuscidian import _windows_native as native
from obfuscidian import constants as const
from tests._windows_owner import _security_state

# Test-only access masks; no production permission or architecture policy changes.
_PARENT_ACCESS = const.WINDOWS_READ_CONTROL | const.WINDOWS_SYNCHRONIZE | const.WINDOWS_READ_ATTRIBUTES | 0x20
_PEER_ACCESS = const.WINDOWS_READ_CONTROL | const.WINDOWS_SYNCHRONIZE | const.WINDOWS_READ_ATTRIBUTES | 0x80000
_ADMINISTRATORS = bytes.fromhex('01020000000000052000000020020000')


def _classify_machine(process: int, machine: int) -> str:
    """Distinguish guest architecture from an emulated process; reject unknown pairs."""
    if (machine, process) == (0x8664, 0):
        return 'native AMD64 Windows'
    if (machine, process) == (0xAA64, 0):
        return 'native ARM64 Windows; diagnostic scope pending acceptance'
    if (machine, process) == (0xAA64, 0x8664):
        return 'emulated AMD64 process on ARM64 Windows; diagnostic scope pending acceptance'
    raise AssertionError('Unsupported or unestablished guest/process architecture.')


def _runtime(api: native._Api) -> dict:
    """Observe this actual CPython process without activating any token privilege."""
    if not __debug__:
        raise RuntimeError('Optimized Python is forbidden for the synthetic owner harness.')
    assert sys.platform == 'win32' and sys.implementation.name == 'cpython', 'Actual Windows CPython required.'
    assert sys.version_info[:2] in ((3, 12), (3, 13), (3, 14)) and struct.calcsize('P') == 8
    assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Use an unelevated standard test account.'
    api._bind(api.kernel, 'IsWow64Process2', api.wt.BOOL, [api.wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p])
    process, machine = ctypes.c_uint16(), ctypes.c_uint16()
    api._check(api.kernel.IsWow64Process2(api.kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(machine)))
    root = Path(__file__).resolve().parents[1]
    assert Path.cwd().resolve() == root, 'Run from the reviewed source root.'
    assert Path(native.__file__).resolve() == root / 'src/obfuscidian/_windows_native.py', 'Unexpected native module source.'
    sources = (
        'tests/_windows_owner_vm.py',
        'tests/_windows_owner.py',
        'src/obfuscidian/_windows_native.py',
        'src/obfuscidian/constants.py',
    )
    return {
        'native_machine_code': machine.value,
        'process_machine_code': process.value,
        'architecture_evidence': _classify_machine(process.value, machine.value),
        'python': sys.version.split()[0],
        'implementation': sys.implementation.name,
        'windows_build': sys.getwindowsversion().build,
        'bits': 64,
        'elevated': False,
        'source_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources},
    }


def _local_account(api: native._Api, name: str) -> tuple[bytes, str]:
    """Resolve only the two named VM accounts in this computer's local namespace."""
    assert name in ('ObfOwnerA', 'ObfOwnerB')
    wt, ptr = api.wt, ctypes.c_void_p
    api._bind(api.kernel, 'GetComputerNameW', wt.BOOL, [wt.LPWSTR, ptr])
    computer, length = ctypes.create_unicode_buffer(256), wt.DWORD(256)
    api._check(api.kernel.GetComputerNameW(computer, ctypes.byref(length)))
    api._bind(api.advapi, 'LookupAccountNameW', wt.BOOL, [wt.LPCWSTR, wt.LPCWSTR, ptr, ptr, wt.LPWSTR, ptr, ptr])
    sid, domain, sid_size, domain_size, kind = (
        ctypes.create_string_buffer(68),
        ctypes.create_unicode_buffer(256),
        wt.DWORD(68),
        wt.DWORD(256),
        wt.DWORD(),
    )
    api._check(
        api.advapi.LookupAccountNameW(
            None, computer.value + '\\' + name, sid, ctypes.byref(sid_size), domain, ctypes.byref(domain_size), ctypes.byref(kind)
        )
    )
    assert kind.value == 1 and domain.value.casefold() == computer.value.casefold(), 'Expected an existing local user.'
    # LookupAccountNameW need not replace the buffer capacity on success.
    # Validate the SID itself, then use its actual bounded length.
    api._check(api.advapi.IsValidSid(sid))
    size = api.advapi.GetLengthSid(sid)
    assert 8 <= size <= len(sid), 'Invalid local account SID length.'
    raw = native._sid_bytes(sid.raw[:size])
    converted = wt.LPWSTR()
    api._check(api.advapi.ConvertSidToStringSidW(sid, ctypes.byref(converted)))
    try:
        return raw, converted.value
    finally:
        api._check(api.kernel.LocalFree(ctypes.cast(converted, ptr)) is None)


def _require_account(api: native._Api, name: str) -> tuple[bytes, str]:
    """Reject administrators, including filtered administrator tokens, and wrong users."""
    expected = _local_account(api, name)
    assert api._owner() == expected, 'Switch to the designated existing standard test account.'
    token, needed = api.wt.HANDLE(), api.wt.DWORD()
    api._check(api.advapi.OpenProcessToken(api.kernel.GetCurrentProcess(), const.WINDOWS_TOKEN_QUERY, ctypes.byref(token)))
    try:
        api.advapi.GetTokenInformation(token, 2, None, 0, ctypes.byref(needed))
        assert 8 <= needed.value <= const.WINDOWS_SECURITY_BYTES
        storage = ctypes.create_string_buffer(needed.value)
        api._check(api.advapi.GetTokenInformation(token, 2, storage, len(storage), ctypes.byref(needed)))

        class Group(ctypes.Structure):
            _fields_ = [('sid', ctypes.c_void_p), ('attributes', api.wt.DWORD)]

        class Groups(ctypes.Structure):
            _fields_ = [('count', api.wt.DWORD), ('groups', Group * 1)]

        count, offset = Groups.from_buffer(storage).count, Groups.groups.offset
        assert offset + count * ctypes.sizeof(Group) <= len(storage)
        for group in (Group * count).from_buffer(storage, offset):
            start, sid = ctypes.addressof(storage), group.sid
            assert sid is not None and start <= sid <= start + len(storage) - 8
            length = 8 + 4 * ctypes.string_at(sid, 2)[1]
            assert 8 <= length <= 68 and sid + length <= start + len(storage)
            assert native._sid_bytes(ctypes.string_at(sid, length)) != _ADMINISTRATORS, 'Administrator membership refused.'
    finally:
        api._check(api.kernel.CloseHandle(token))
    return expected


def _fixture_path(value: str, public: str) -> str:
    """Confine peer mutation to one UUID-named new fixture beneath Public Documents."""
    result = native._absolute(value)
    parent, name = ntpath.split(result)
    assert ntpath.normcase(parent) == ntpath.normcase(ntpath.join(native._absolute(public), 'Documents'))
    assert re.fullmatch(r'obfuscidian-owner29-[0-9a-f]{32}', name), 'Not a designated synthetic VM fixture.'
    return result


def _bind_setter(api: native._Api) -> None:
    """Bind only handle-bound owner/DACL changes for the designated synthetic fixture."""
    ptr = ctypes.c_void_p
    api._bind(api.advapi, 'SetSecurityInfo', api.wt.DWORD, [api.wt.HANDLE, api.wt.DWORD, api.wt.DWORD, ptr, ptr, ptr, ptr])


def _set_dacl(handle: native._Handle, acl: bytes, *, control: int) -> None:
    """Set exact protected DACL/control through retained WRITE_DAC, without tree propagation."""
    assert control in (0x9004, 0x9404), 'Unexpected fixture descriptor control; preserve evidence.'
    assert 8 <= len(acl) <= const.WINDOWS_SECURITY_BYTES - 20
    api = handle.api
    # SetSecurityInfo imposes its inheritance model and can add AUTO_INHERITED.
    # Supply the complete self-relative DACL descriptor to the native handle setter
    # instead. Select DACL only: absent owner/group/SACL fields are never applied.
    buffer = ctypes.create_string_buffer(acl)
    api._check(api.advapi.IsValidAcl(buffer))
    descriptor = ctypes.create_string_buffer(struct.pack('<BBHIIII', 1, 0, control, 0, 0, 0, 20) + acl)
    api._check(api.advapi.IsValidSecurityDescriptor(descriptor))
    api._bind(api.ntdll, 'NtSetSecurityObject', ctypes.c_int32, [api.wt.HANDLE, api.wt.DWORD, ctypes.c_void_p])
    status = api.ntdll.NtSetSecurityObject(handle.raw, 4, descriptor)
    assert status == 0, f'Fixture DACL setter refused (NTSTATUS 0x{status & 0xFFFFFFFF:08X}); preserve evidence.'


def _restore_fixture_dacl(handle: native._Handle, before: tuple, temporary: tuple | None, owners: set[bytes]) -> None:
    """Restore only a recognized temporary fixture grant; preserve unexpected security states."""
    state = _security_state(handle)
    assert state[0] in owners, 'Unexpected fixture owner; preserve synthetic evidence.'
    if state[1:] == before[1:]:
        return
    assert temporary is not None and state[1:] == temporary[1:], 'Unexpected fixture DACL; preserve synthetic evidence.'
    _set_dacl(handle, before[2], control=before[1])
    assert _security_state(handle) == (state[0], before[1], before[2])


@contextmanager
def _grant_acl(api: native._Api, creator: str, peer: str, *, directory: bool):
    """Build the narrowly scoped temporary ACL; grant no peer file-data or delete rights."""
    descriptor, dacl, present, defaulted = ctypes.c_void_p(), ctypes.c_void_p(), api.wt.BOOL(), api.wt.BOOL()
    flags, access = ('OICI', _PARENT_ACCESS) if directory else ('', _PEER_ACCESS)
    text = f'D:P(A;{flags};FA;;;{creator})(A;;0x{access:08x};;;{peer})'
    api._check(api.advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(text, 1, ctypes.byref(descriptor), None))
    try:
        api._check(
            api.advapi.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted))
        )
        assert present.value and not defaulted.value and dacl.value
        size = struct.unpack('<H', ctypes.string_at(dacl.value + 2, 2))[0]
        assert 8 <= size <= const.WINDOWS_SECURITY_BYTES
        yield ctypes.string_at(dacl, size)
    finally:
        api._check(api.kernel.LocalFree(descriptor) is None)


def _open_leaf(guard: native._Guard, rights: int) -> native._Handle:
    """Open the one fixture leaf relative to pinned ancestors, with fully shared custody."""
    guard._check()
    api = guard.api
    encoded = 'changed-owner'.encode('utf-16-le')
    storage = ctypes.create_string_buffer(encoded + b'\0\0')
    name = native._UnicodeString(len(encoded), len(encoded) + 2, ctypes.addressof(storage))
    attributes = native._ObjectAttributes(
        ctypes.sizeof(native._ObjectAttributes),
        guard.handles[-1].raw,
        ctypes.pointer(name),
        const.WINDOWS_OBJECT_ATTRIBUTES,
        None,
        None,
    )
    raw, result = ctypes.c_void_p(), native._IoStatus()
    status = api.ntdll.NtCreateFile(
        ctypes.byref(raw),
        rights | const.WINDOWS_SYNCHRONIZE,
        ctypes.byref(attributes),
        ctypes.byref(result),
        None,
        0,
        7,
        const.WINDOWS_NATIVE_OPEN,
        const.WINDOWS_NATIVE_OPEN_OPTIONS | const.WINDOWS_NATIVE_FILE,
        None,
        0,
    )
    try:
        api._nt_check(status, result)
    except BaseException:
        if raw.value not in (None, ctypes.c_void_p(-1).value):
            api._check(api.kernel.CloseHandle(raw))
        raise
    assert raw.value not in (None, ctypes.c_void_p(-1).value)
    held = api._adopt(raw.value, ntpath.join(guard.path, 'changed-owner'), directory=False)
    try:
        guard._check()
        assert ntpath.normcase(held._final_path()) == ntpath.normcase(held.path)
        return held
    except BaseException:
        held._close()
        raise


@contextmanager
def _creator_fixture(record_property):
    """Hold A's custody through B's manual session switch, then restore exact permissions."""
    api = native._Api()
    evidence = _runtime(api)
    current, creator = _require_account(api, 'ObfOwnerA')
    selected, peer = _local_account(api, 'ObfOwnerB')
    assert current != selected
    for key, value in evidence.items():
        record_property(key, value)
    record_property('owner_fixture_strategy', 'two-existing-standard-VM-accounts')
    public = os.environ['PUBLIC']
    path = Path(_fixture_path(ntpath.join(public, 'Documents', 'obfuscidian-owner29-' + uuid.uuid4().hex), public))
    _bind_setter(api)
    with native._Guard(path.parent) as parent:
        with parent._create_directory(path.name):
            pass
        # Acquire WRITE_DAC while A owns the directory; retain it until grant restoration.
        with parent.api._open_relative(parent.handles[-1], path.name, directory=True, security_write=True) as directory:
            directory_before = _security_state(directory)
            directory._private()
            with native._Guard(path) as guard:
                with guard._open_file('changed-owner', create=True) as created:
                    created._write(b'KEEP', 100)
                with _open_leaf(guard, const.WINDOWS_GENERIC_READ | const.WINDOWS_READ_CONTROL | const.WINDOWS_WRITE_DAC) as held:
                    held._private()
                    with guard._open_file('changed-owner') as positive:
                        positive._private()
                        assert positive._read(100) == b'KEEP'
                    record_property('owner_fixture_positive_guarded_open', True)
                    before = _security_state(held)
                    assert before[0] == current and held._read(100) == b'KEEP'
                    identity = held._identity()
                    directory_temporary = file_temporary = None
                    try:
                        with _grant_acl(api, creator, peer, directory=True) as acl:
                            directory_temporary = (current, directory_before[1], acl)
                            _set_dacl(directory, acl, control=directory_before[1])
                            assert _security_state(directory) == directory_temporary
                        with _grant_acl(api, creator, peer, directory=False) as acl:
                            file_temporary = (current, before[1], acl)
                            _set_dacl(held, acl, control=before[1])
                            assert _security_state(held) == file_temporary
                        print('\nSwitch user to ObfOwnerB; keep this A process/session alive. In the reviewed source root run:')
                        print(
                            'python -I -S tests/_windows_owner_vm.py peer --fixture "'
                            + str(path)
                            + '" --volume '
                            + str(identity.volume)
                            + ' --file-id '
                            + identity.file_id.hex()
                        )
                        assert input('After B exits successfully, switch back to A and type OWNER-CHANGED: ') == 'OWNER-CHANGED'
                        state = _security_state(held)
                        assert state[0] == selected, 'Actual peer owner transition is mandatory.'
                        assert state[1:] == file_temporary[1:], 'Only the intended owner may change during B participation.'
                        _restore_fixture_dacl(held, before, file_temporary, {current, selected})
                        record_property('retained_write_dac_restored_exact_original', True)
                        yield path, held, identity, before, current, selected
                    finally:
                        # Only our new fixture and retained handles are eligible for grant restoration.
                        # Do not restore owners, remove evidence or reopen an uncertain file for repair.
                        try:
                            _restore_fixture_dacl(held, before, file_temporary, {current, selected})
                        finally:
                            _restore_fixture_dacl(directory, directory_before, directory_temporary, {current})


def _peer(fixture: str, volume: int, file_id: str) -> dict:
    """Take ownership as B only after verifying the exact designated A-created file."""
    assert re.fullmatch('[0-9a-f]{32}', file_id) and 0 < volume <= 0xFFFFFFFFFFFFFFFF
    path = Path(_fixture_path(fixture, os.environ['PUBLIC']))
    api = native._Api()
    evidence = _runtime(api)
    selected, peer = _require_account(api, 'ObfOwnerB')
    current, creator = _local_account(api, 'ObfOwnerA')
    assert current != selected
    _bind_setter(api)
    with native._Guard(path) as guard:
        with _open_leaf(guard, _PEER_ACCESS) as held:
            identity = held._identity()
            assert identity.volume == volume and identity.file_id.hex() == file_id and not identity.directory
            before = _security_state(held)
            assert before[0] == current
            with _grant_acl(api, creator, peer, directory=False) as acl:
                assert before[2] == acl, 'Temporary leaf policy must match exactly.'
            sid = ctypes.create_string_buffer(selected)
            assert api.advapi.SetSecurityInfo(held.raw, 1, 1, sid, None, None, None) == 0
            after = _security_state(held)
            assert after[0] == selected and after[1:] == before[1:]
            changed = held._identity()
            assert identity._same_object(changed)
            assert (identity.attributes, identity.size, identity.links, identity.created, identity.written) == (
                changed.attributes,
                changed.size,
                changed.links,
                changed.created,
                changed.written,
            )
    return {**evidence, 'peer_owner_setter_completed': True, 'scope': 'peer transition only; A must prove production refusal'}


def _main() -> None:
    """Run only the peer transition or a no-fixture account/runtime observation."""
    parser = argparse.ArgumentParser(description=_main.__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    probe = actions.add_parser('probe')
    probe.add_argument('--account', choices=('ObfOwnerA', 'ObfOwnerB'), required=True)
    peer = actions.add_parser('peer')
    peer.add_argument('--fixture', required=True)
    peer.add_argument('--volume', type=int, required=True)
    peer.add_argument('--file-id', required=True)
    options = parser.parse_args()
    if options.action == 'peer':
        result = _peer(options.fixture, options.volume, options.file_id)
    else:
        api = native._Api()
        result = _runtime(api)
        _require_account(api, options.account)
        result['scope'] = 'read-only account/runtime observation; no owner fixture'
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    _main()

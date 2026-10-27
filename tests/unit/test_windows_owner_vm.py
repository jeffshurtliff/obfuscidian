# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_owner_vm
:Synopsis:          Portable refusal boundaries for the two-account VM test harness
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     15 Oct 2026
"""

from __future__ import annotations

import ctypes
import struct
from types import SimpleNamespace

import pytest

from obfuscidian import constants as const
from tests import _windows_owner_vm as vm


@pytest.mark.parametrize(
    'process,machine,label',
    [(0, 0x8664, 'native AMD64'), (0, 0xAA64, 'native ARM64'), (0x8664, 0xAA64, 'emulated AMD64')],
)
def test_machine_evidence_does_not_turn_arm_guest_into_amd64(process, machine, label):
    result = vm._classify_machine(process, machine)
    assert result.startswith(label)
    assert ('pending acceptance' in result) is (machine == 0xAA64)


@pytest.mark.parametrize('process,machine', [(0, 0), (0x14C, 0xAA64), (0x8664, 0x8664), (0, 0x14C), (0xA641, 0xAA64)])
def test_unknown_or_unsupported_process_pairs_refuse(process, machine):
    with pytest.raises(AssertionError, match='architecture'):
        vm._classify_machine(process, machine)


def test_peer_target_is_one_uuid_under_public_documents():
    path = 'C:\\Users\\Public\\Documents\\obfuscidian-owner29-' + 'a' * 32
    assert vm._fixture_path(path, 'C:\\Users\\Public') == path


@pytest.mark.parametrize(
    'value',
    [
        'C:\\Users\\Public\\Documents\\real-data',
        'C:\\Users\\Other\\Documents\\obfuscidian-owner29-' + 'a' * 32,
        'C:\\Users\\Public\\Documents\\obfuscidian-owner29-' + 'a' * 31,
        'C:\\Users\\Public\\Documents\\obfuscidian-owner29-' + 'A' * 32,
        'C:\\Users\\Public\\Documents\\..\\obfuscidian-owner29-' + 'a' * 32,
        '\\\\server\\share\\obfuscidian-owner29-' + 'a' * 32,
        'C:\\Users\\Public\\Documents\\obfuscidian-owner29-' + 'a' * 32 + '\\child',
    ],
)
def test_peer_cannot_accept_arbitrary_real_or_aliased_targets(value):
    with pytest.raises((AssertionError, OSError)):
        vm._fixture_path(value, 'C:\\Users\\Public')


def test_vm_fixture_grants_no_peer_data_write_delete_or_dacl_write():
    forbidden = const.WINDOWS_GENERIC_WRITE | const.WINDOWS_DELETE | const.WINDOWS_WRITE_DAC | 2 | 4
    assert not vm._PEER_ACCESS & forbidden
    assert not vm._PARENT_ACCESS & forbidden
    assert vm._PEER_ACCESS & 0x80000
    assert not vm._PARENT_ACCESS & 0x80000


def test_runtime_refuses_posix_before_native_probe(monkeypatch):
    monkeypatch.setattr(vm.sys, 'platform', 'darwin')
    with pytest.raises(AssertionError, match='Actual Windows'):
        vm._runtime(object())


@pytest.mark.parametrize('control', [0x9004, 0x9404])
def test_exact_dacl_setter_binds_full_width_handle_and_preserves_descriptor_control(control):
    """Native call-contract evidence only; actual descriptor round trips need Windows."""
    calls, bindings = [], []

    def setter(raw, information, descriptor):
        header = struct.unpack('<BBHIIII', descriptor.raw[:20])
        assert header == (1, 0, control, 0, 0, 0, 20)
        assert descriptor.raw[20:-1] == acl
        calls.append((raw, information))
        return 0

    api = SimpleNamespace(
        wt=SimpleNamespace(DWORD=ctypes.c_uint32, HANDLE=ctypes.c_void_p),
        ntdll=SimpleNamespace(NtSetSecurityObject=setter),
        advapi=SimpleNamespace(IsValidAcl=lambda pointer: True, IsValidSecurityDescriptor=lambda pointer: True),
        _bind=lambda *args: bindings.append(args),
        _check=lambda ok: ok or pytest.fail('Synthetic descriptor validation failed.'),
    )
    held = SimpleNamespace(api=api, raw=0x123456789)
    acl = struct.pack('<BBHHH', 2, 0, 8, 0, 0)  # Synthetic non-null ACL for an injected ABI contract only.
    vm._set_dacl(held, acl, control=control)
    assert bindings[0][1] == 'NtSetSecurityObject'
    assert bindings[0][2] is ctypes.c_int32
    assert bindings[0][3][0] is ctypes.c_void_p
    assert calls == [(held.raw, 4)]  # DACL only: never owner, group, SACL or privilege access.


@pytest.mark.parametrize('acl', [b'', b'bad', b'x' * (const.WINDOWS_SECURITY_BYTES + 1)])
def test_dacl_setter_never_supplies_a_null_or_unbounded_acl(acl):
    with pytest.raises(AssertionError):
        vm._set_dacl(SimpleNamespace(), acl, control=0x9004)


@pytest.mark.parametrize('control', [0, 4, 0x8004, 0x9104, 0xD004, 0x19004])
def test_dacl_setter_refuses_unprotected_or_unknown_control_before_native_access(control):
    with pytest.raises(AssertionError, match='Unexpected fixture descriptor control'):
        vm._set_dacl(SimpleNamespace(), b'ACL BYTES', control=control)


@pytest.mark.parametrize('invalid', ['acl', 'descriptor', 'status'])
def test_injected_dacl_setter_refusals_never_fall_back_to_tree_propagation(invalid):
    calls = []

    def check(ok):
        if not ok:
            raise OSError('Synthetic invalid descriptor.')

    api = SimpleNamespace(
        wt=SimpleNamespace(DWORD=ctypes.c_uint32, HANDLE=ctypes.c_void_p),
        advapi=SimpleNamespace(
            IsValidAcl=lambda pointer: invalid != 'acl',
            IsValidSecurityDescriptor=lambda pointer: invalid != 'descriptor',
            SetSecurityInfo=lambda *args: pytest.fail('No setter fallback is permitted.'),
        ),
        ntdll=SimpleNamespace(NtSetSecurityObject=lambda *args: calls.append(args) or -1073741790),
        _bind=lambda *args: None,
        _check=check,
    )
    with pytest.raises(AssertionError if invalid == 'status' else OSError):
        vm._set_dacl(SimpleNamespace(api=api, raw=0x123456789), b'ACL BYTES', control=0x9004)
    assert len(calls) == (1 if invalid == 'status' else 0)


@pytest.mark.parametrize(
    'rights', [const.WINDOWS_GENERIC_READ | const.WINDOWS_READ_CONTROL | const.WINDOWS_WRITE_DAC, vm._PEER_ACCESS]
)
def test_injected_leaf_open_explicitly_requests_synchronous_access_and_retains_relative_custody(rights):
    """Exercise the real test opener's native-call contract, not an injected owner transition."""
    calls, closed = [], []
    path = 'C:\\Users\\Public\\Documents\\obfuscidian-owner29-' + 'a' * 32
    expected = path + '\\changed-owner'
    raw, parent = 0x123456789, 0x987654321
    held = SimpleNamespace(path=expected, _final_path=lambda: expected, _close=lambda: closed.append(raw))

    def create(output, access, attributes, result, allocation, file_attributes, sharing, disposition, options, ea, ea_size):
        assert access & const.WINDOWS_SYNCHRONIZE, 'Synchronous NtCreateFile needs explicit SYNCHRONIZE.'
        assert access == rights | const.WINDOWS_SYNCHRONIZE
        assert attributes._obj.root == parent and attributes._obj.attributes == const.WINDOWS_OBJECT_ATTRIBUTES
        name = attributes._obj.name.contents
        assert ctypes.string_at(name.buffer, name.length).decode('utf-16-le') == 'changed-owner'
        assert sharing == 7 and disposition == const.WINDOWS_NATIVE_OPEN
        assert options == const.WINDOWS_NATIVE_OPEN_OPTIONS | const.WINDOWS_NATIVE_FILE
        assert allocation is None and file_attributes == 0 and ea is None and ea_size == 0
        output._obj.value = raw
        calls.append('native open')
        return 0

    def adopt(value, resolved, *, directory):
        assert value == raw and resolved == expected and not directory
        calls.append('adopt full-width handle')
        return held

    guard = SimpleNamespace(
        path=path,
        handles=[SimpleNamespace(raw=parent)],
        _check=lambda: calls.append('guard recheck'),
        api=SimpleNamespace(ntdll=SimpleNamespace(NtCreateFile=create), _nt_check=vm.native._Api._nt_check, _adopt=adopt),
    )
    assert vm._open_leaf(guard, rights) is held
    assert calls == ['guard recheck', 'native open', 'adopt full-width handle', 'guard recheck']
    assert not closed


def _account_api(*, reported_size=68, actual_size=12, valid=True):
    """Model documented SID-buffer capacity behavior with explicitly synthetic bytes."""
    raw = bytes.fromhex('010100000000000515000000')
    freed = []

    def computer_name(output, length):
        output.value = 'SYNTHETICVM'
        length._obj.value = len(output.value)
        return True

    def lookup(system, account, sid, sid_size, domain, domain_size, kind):
        assert system is None and account in ('SYNTHETICVM\\ObfOwnerA', 'SYNTHETICVM\\ObfOwnerB')
        assert sid_size._obj.value == 68 and domain_size._obj.value == 256
        ctypes.memmove(sid, raw, len(raw))
        sid_size._obj.value = reported_size
        domain.value, kind._obj.value = 'SYNTHETICVM', 1
        return True

    def convert(sid, output):
        assert sid.raw[: len(raw)] == raw
        output._obj.value = 'SYNTHETIC SID TEXT'
        return True

    def check(ok):
        if not ok:
            raise OSError('Synthetic API refusal.')

    api = SimpleNamespace(
        wt=SimpleNamespace(DWORD=ctypes.c_uint32, BOOL=ctypes.c_int32, LPWSTR=ctypes.c_wchar_p, LPCWSTR=ctypes.c_wchar_p),
        _bind=lambda *args: None,
        _check=check,
        kernel=SimpleNamespace(GetComputerNameW=computer_name, LocalFree=lambda pointer: freed.append(pointer.value)),
        advapi=SimpleNamespace(
            LookupAccountNameW=lookup,
            IsValidSid=lambda sid: valid,
            GetLengthSid=lambda sid: actual_size,
            ConvertSidToStringSidW=convert,
        ),
    )
    return api, raw, freed


@pytest.mark.parametrize('name', ['ObfOwnerA', 'ObfOwnerB'])
@pytest.mark.parametrize('reported_size', [12, 68])
def test_injected_account_lookup_uses_actual_sid_length_not_capacity(name, reported_size):
    """A successful lookup may retain capacity; padding must not enter SID validation."""
    api, raw, freed = _account_api(reported_size=reported_size)
    assert vm._local_account(api, name) == (raw, 'SYNTHETIC SID TEXT')
    assert len(freed) == 1


@pytest.mark.parametrize('actual_size', [7, 69])
def test_injected_account_lookup_refuses_out_of_bounds_sid_length(actual_size):
    api, _, freed = _account_api(actual_size=actual_size)
    with pytest.raises(AssertionError, match='Invalid local account SID length'):
        vm._local_account(api, 'ObfOwnerA')
    assert not freed  # No converted SID was allocated.


def test_injected_account_lookup_refuses_invalid_sid_before_conversion():
    api, _, freed = _account_api(valid=False)
    api.advapi.GetLengthSid = lambda sid: pytest.fail('Invalid SID must be refused before measuring it.')
    with pytest.raises(OSError, match='Synthetic API refusal'):
        vm._local_account(api, 'ObfOwnerA')
    assert not freed


@pytest.mark.parametrize('administrator', [False, True])
def test_injected_token_membership_rejects_even_deny_only_administrators(monkeypatch, administrator):
    """Injected token bytes test harness refusal only; no Windows owner proof is claimed."""

    class Group(ctypes.Structure):
        _fields_ = [('sid', ctypes.c_void_p), ('attributes', ctypes.c_uint32)]

    class Groups(ctypes.Structure):
        _fields_ = [('count', ctypes.c_uint32), ('groups', Group * 1)]

    selected = vm._ADMINISTRATORS if administrator else bytes.fromhex('0101000000000005d2040000')
    expected = (b'EXPECTED SYNTHETIC USER', 'SYNTHETIC USER TEXT')
    total = ctypes.sizeof(Groups) + len(selected)
    closed = []

    def open_token(process, rights, output):
        assert rights == const.WINDOWS_TOKEN_QUERY
        output._obj.value = 99
        return True

    def query(token, kind, storage, length, needed):
        assert kind == 2
        needed._obj.value = total
        if storage is None:
            return False
        groups = Groups.from_buffer(storage)
        groups.count = 1
        groups.groups[0].sid = ctypes.addressof(storage) + ctypes.sizeof(Groups)
        groups.groups[0].attributes = 16  # Deny-only administrators still mean a filtered admin account.
        ctypes.memmove(groups.groups[0].sid, selected, len(selected))
        return True

    api = SimpleNamespace(
        wt=SimpleNamespace(DWORD=ctypes.c_uint32, HANDLE=ctypes.c_void_p),
        _owner=lambda: expected,
        _check=lambda ok: ok or pytest.fail('Synthetic API failure.'),
        kernel=SimpleNamespace(GetCurrentProcess=lambda: 1, CloseHandle=lambda token: closed.append(token.value) or True),
        advapi=SimpleNamespace(OpenProcessToken=open_token, GetTokenInformation=query),
    )
    monkeypatch.setattr(vm, '_local_account', lambda api, name: expected)
    if administrator:
        with pytest.raises(AssertionError, match='Administrator membership'):
            vm._require_account(api, 'ObfOwnerA')
    else:
        assert vm._require_account(api, 'ObfOwnerA') == expected
    assert closed == [99]


@pytest.mark.parametrize('interrupt', [False, True])
@pytest.mark.parametrize('control', [0x9004, 0x9404])
def test_injected_session_barrier_preserves_custody_and_restores_only_fixture_grants(monkeypatch, interrupt, control):
    """A synthetic model checks cleanup ordering; it is not native transition evidence."""
    from contextlib import contextmanager
    from pathlib import PureWindowsPath

    from obfuscidian import _windows_native as native

    original_acl, directory_acl = b'ORIGINAL FILE ACL', b'ORIGINAL DIR ACL'
    identity = native._Identity(9, b'x' * 16, False, 32, 4, 1, 11, 12, 13, 14)
    timeline, properties = [], {}

    class Held:
        def __init__(self, acl):
            self.state = (b'A', control, acl)
            self.api = SimpleNamespace(_open_relative=lambda *args, **kwargs: directory)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def _private(self):
            assert self.state[0] == b'A'

        def _write(self, data, limit):
            assert data == b'KEEP'

        def _read(self, limit):
            return b'KEEP'

        def _identity(self):
            return identity

    file, directory = Held(original_acl), Held(directory_acl)

    class Guard(Held):
        def __init__(self, path):
            super().__init__(directory_acl)
            self.handles = [directory]
            self.path = str(path)

        def _create_directory(self, name):
            timeline.append('new synthetic directory')
            return directory

        def _open_file(self, name, **kwargs):
            assert name == 'changed-owner'
            return file

    @contextmanager
    def grant(api, creator, peer, *, directory):
        yield b'TEMPORARY DIR ACL' if directory else b'TEMPORARY FILE ACL'

    def retained(guard, rights):
        assert rights & const.WINDOWS_WRITE_DAC
        timeline.append('retained WRITE_DAC before peer')
        return file

    def set_dacl(held, acl, *, control):
        assert control == held.state[1]
        held.state = (held.state[0], control, acl)
        timeline.append(('directory' if held is directory else 'file', acl))

    def peer_barrier(prompt):
        assert timeline.index('retained WRITE_DAC before peer') < len(timeline) - 1
        assert file.state[2] == b'TEMPORARY FILE ACL' and directory.state[2] == b'TEMPORARY DIR ACL'
        if interrupt:
            raise EOFError('Synthetic interrupted session barrier.')
        file.state = (b'B', file.state[1], file.state[2])
        return 'OWNER-CHANGED'

    monkeypatch.setattr(vm.native, '_Api', lambda: object())
    monkeypatch.setattr(vm.native, '_Guard', Guard)
    monkeypatch.setattr(vm, '_runtime', lambda api: {'architecture_evidence': 'injected model only'})
    monkeypatch.setattr(vm, '_require_account', lambda api, name: (b'A', 'CREATOR'))
    monkeypatch.setattr(vm, '_local_account', lambda api, name: (b'B', 'PEER'))
    monkeypatch.setattr(vm, '_bind_setter', lambda api: None)
    monkeypatch.setattr(vm, '_grant_acl', grant)
    monkeypatch.setattr(vm, '_open_leaf', retained)
    monkeypatch.setattr(vm, '_set_dacl', set_dacl)
    monkeypatch.setattr(vm, '_security_state', lambda held: held.state)
    monkeypatch.setattr(vm, 'Path', PureWindowsPath)
    monkeypatch.setenv('PUBLIC', 'C:\\Users\\Public')
    monkeypatch.setattr('builtins.input', peer_barrier)
    with pytest.raises(EOFError if interrupt else RuntimeError):
        with vm._creator_fixture(properties.__setitem__) as (_, held, _, before, _, selected):
            assert not interrupt and selected == b'B'
            assert held.state == (b'B', before[1], before[2])
            raise RuntimeError('Synthetic assertion failure after transition.')
    assert file.state == (b'A' if interrupt else b'B', control, original_acl)
    assert directory.state == (b'A', control, directory_acl)
    assert ('file', original_acl) in timeline and timeline[-1] == ('directory', directory_acl)


def test_peer_help_bootstraps_reviewed_source_without_site_packages():
    """B's entry point needs stdlib only; help must load without a Poetry installation."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, '-I', '-S', 'tests/_windows_owner_vm.py', 'peer', '--help'],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert '--fixture' in result.stdout and '--file-id' in result.stdout


@pytest.mark.parametrize(
    'owner,control,acl', [(b'FOREIGN', 0x9004, b'TEMP'), (b'A', 0x9004, b'UNKNOWN'), (b'A', 0x9404, b'TEMP')]
)
def test_injected_unexpected_security_is_preserved_without_fixture_repair(monkeypatch, owner, control, acl):
    monkeypatch.setattr(vm, '_security_state', lambda held: (owner, control, acl))
    monkeypatch.setattr(vm, '_set_dacl', lambda *args: pytest.fail('Unknown state must never be repaired.'))
    with pytest.raises(AssertionError, match='preserve synthetic evidence'):
        vm._restore_fixture_dacl(object(), (b'A', 0x9004, b'ORIGINAL'), (b'A', 0x9004, b'TEMP'), {b'A', b'B'})

# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_owner_qualification
:Synopsis:          Refuse unavailable owner setup without privileged or filesystem fallback
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     15 Oct 2026
"""

from __future__ import annotations

import ctypes
import json
from types import SimpleNamespace

import pytest

from tests import _windows_owner as owner
from tests import _windows_owner_vm as vm


@pytest.mark.parametrize(
    'attributes,foreign,eligible',
    [
        (12, True, True),
        (8, True, False),
        (4, True, False),
        (28, True, False),
        (12, False, False),
        (0, True, False),
    ],
)
def test_owner_group_requires_all_existing_membership_rights(attributes, foreign, eligible):
    """Missing/deny-only/current-owner membership cannot authorize a real fixture."""
    current = b'SYNTHETIC CURRENT SID'
    assert owner._eligible_group(attributes, b'SYNTHETIC OTHER SID' if foreign else current, current) is eligible


@pytest.mark.parametrize('available', [True, False])
def test_injected_preflight_reports_blocker_without_sids_or_files(monkeypatch, capsys, available):
    """Token-response injection supplements setup handling, never real owner proof."""
    monkeypatch.setattr(owner.sys, 'platform', 'win32')
    monkeypatch.setattr(owner.sys, 'version_info', (3, 13, 14))
    monkeypatch.setattr(owner.platform, 'machine', lambda: 'AMD64')
    monkeypatch.setattr(owner.platform, 'python_version', lambda: '3.13.14')
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 0)), raising=False)
    monkeypatch.setattr(owner.native, '_Api', lambda: object())
    monkeypatch.setattr(vm, '_runtime', lambda api: {'native_machine_code': 0x8664, 'process_machine_code': 0})
    monkeypatch.setattr(owner, '_owner_candidate', lambda api: b'SYNTHETIC SID MUST NOT PRINT' if available else None)
    assert owner._preflight() == (0 if available else 2)
    output = capsys.readouterr()
    assert 'SID' not in output.out and output.err == ''
    report = json.loads(output.out)
    assert report['assignable_owner_group_available'] is available
    assert report['scope'] == 'read-only token preflight; no filesystem owner proof'


@pytest.mark.parametrize('process', [0, 0x8664])
def test_injected_amd64_process_label_cannot_qualify_arm_guest(monkeypatch, process):
    """The old process architecture string cannot override actual native-machine evidence."""
    monkeypatch.setattr(owner.sys, 'platform', 'win32')
    monkeypatch.setattr(owner.sys, 'version_info', (3, 13, 14))
    monkeypatch.setattr(owner.platform, 'machine', lambda: 'AMD64')
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 0)), raising=False)
    monkeypatch.setattr(owner.native, '_Api', lambda: object())
    monkeypatch.setattr(vm, '_runtime', lambda api: {'native_machine_code': 0xAA64, 'process_machine_code': process})
    monkeypatch.setattr(owner, '_owner_candidate', lambda api: pytest.fail('Owner group query must not run.'))
    with pytest.raises(AssertionError, match='Native AMD64'):
        owner._preflight()


def test_preflight_refuses_posix_before_loading_native_api(monkeypatch, capsys):
    """POSIX cannot produce even an owner-fixture eligibility result."""
    monkeypatch.setattr(owner.sys, 'platform', 'darwin')
    monkeypatch.setattr(owner.native, '_Api', lambda: pytest.fail('Native API must not load on POSIX.'))
    with pytest.raises(AssertionError, match='Native Windows CPython'):
        owner._preflight()
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('malformed', [False, True])
def test_injected_token_query_closes_handle_and_copies_candidate_sid(malformed):
    """Token query failures close custody; valid SID bytes outlive the query buffer."""

    class Group(ctypes.Structure):
        _fields_ = [('sid', ctypes.c_void_p), ('attributes', ctypes.c_uint32)]

    class Groups(ctypes.Structure):
        _fields_ = [('count', ctypes.c_uint32), ('groups', Group * 1)]

    sid = ctypes.create_string_buffer(b'SYNTHSID')
    groups = Groups(1, (Group * 1)(Group(ctypes.cast(sid, ctypes.c_void_p), 12)))
    closed = []

    def open_token(process, rights, output):
        output._obj.value = 99
        return True

    def information(token, kind, buffer, size, length):
        assert token.value == 99 and kind == 2
        length._obj.value = 1 if malformed else ctypes.sizeof(groups)
        if buffer is not None:
            assert size == ctypes.sizeof(groups)
            ctypes.memmove(buffer, ctypes.byref(groups), size)
        return buffer is not None

    def check(success):
        assert success

    api = SimpleNamespace(
        wt=SimpleNamespace(DWORD=ctypes.c_uint32, HANDLE=ctypes.c_void_p),
        advapi=SimpleNamespace(
            OpenProcessToken=open_token,
            GetTokenInformation=information,
            IsValidSid=lambda pointer: True,
            GetLengthSid=lambda pointer: 8,
        ),
        kernel=SimpleNamespace(GetCurrentProcess=lambda: 1, CloseHandle=lambda handle: closed.append(handle.value) or True),
        _owner=lambda: (b'CURRENT!', 'SYNTHETIC'),
        _check=check,
    )
    if malformed:
        with pytest.raises(AssertionError):
            owner._owner_candidate(api)
    else:
        assert owner._owner_candidate(api) == b'SYNTHSID'
    assert closed == [99]


def _run_injected_owner_measurement(monkeypatch, tmp_path, *, mutation=None, boundary=None, corrupt_bytes=False):
    """Execute the actual mandatory test with an explicit model, never native qualification."""
    from contextlib import contextmanager
    from dataclasses import replace

    from tests.integration import test_windows_native as cases

    identity = owner.native._Identity(17, b'SYNTHETIC FILEID', False, 32, 4, 1, 10, 11, 12, 13)
    properties = {}
    (tmp_path / 'changed-owner').write_bytes(b'KEEP')

    class Held:
        current = identity
        reads = 0

        def _identity(self):
            return self.current

        def _read(self, limit):
            assert limit == 100
            self.reads += 1
            self.current = replace(self.current, accessed=self.current.accessed + 1)
            if self.reads == 2:
                change('verification read')
                if corrupt_bytes:
                    return b'FAIL'
            return b'KEEP'

        def _private(self):
            change('handle refusal')
            raise owner.native._NativeSafetyError('Unexpected Windows artifact owner.')

    held = Held()

    def change(where):
        if where == boundary:
            value = getattr(held.current, mutation)
            altered = not value if isinstance(value, bool) else b'CHANGED FILE ID!' if isinstance(value, bytes) else value + 1
            held.current = replace(held.current, **{mutation: altered})

    class Guard:
        def __init__(self, path):
            assert path == tmp_path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def _open_file(self, name):
            assert name == 'changed-owner'
            change('guarded-open refusal')
            raise owner.native._NativeSafetyError('Unexpected Windows artifact owner.')

    @contextmanager
    def fixture(record_property):
        yield tmp_path, held, identity, (b'A', 0x9004, b'ORIGINAL ACL'), b'A', b'B'

    monkeypatch.setattr(owner.native, '_Api', lambda: SimpleNamespace(wt=SimpleNamespace()))
    monkeypatch.setattr(owner.native, '_Guard', Guard)
    monkeypatch.setattr(vm, '_creator_fixture', fixture)
    monkeypatch.setattr(cases, '_security_state', lambda target: (b'B', 0x9004, b'ORIGINAL ACL'))
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 0)), raising=False)
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda option: option == '--owner-vm-two-account'))
    cases.test_changed_native_owner_refused_without_privilege_activation(tmp_path, properties.__setitem__, request)
    return properties, held


def test_injected_owner_measurement_does_not_charge_verification_read_time_to_refusals(monkeypatch, tmp_path):
    """A read may alter access time; the complete production-refusal snapshot must not."""
    properties, held = _run_injected_owner_measurement(monkeypatch, tmp_path)
    assert held.reads == 2
    assert properties['actual_native_identity_before_refusal'] == properties['actual_native_identity_after_refusal']
    assert properties['verification_read_access_time_changed'] is True
    assert properties['full_native_identity_preserved'] is True
    assert properties['original_bytes_preserved'] is True


@pytest.mark.parametrize('boundary', ['handle refusal', 'guarded-open refusal'])
@pytest.mark.parametrize(
    'field', ['volume', 'file_id', 'directory', 'attributes', 'size', 'links', 'created', 'accessed', 'written', 'changed']
)
def test_injected_owner_measurement_rejects_every_identity_field_changed_by_refusal(monkeypatch, tmp_path, boundary, field):
    with pytest.raises(AssertionError):
        _run_injected_owner_measurement(monkeypatch, tmp_path, mutation=field, boundary=boundary)


def test_injected_owner_measurement_still_rejects_changed_verification_bytes(monkeypatch, tmp_path):
    with pytest.raises(AssertionError):
        _run_injected_owner_measurement(monkeypatch, tmp_path, corrupt_bytes=True)


@pytest.mark.parametrize(
    'field', ['volume', 'file_id', 'directory', 'attributes', 'size', 'links', 'created', 'written', 'changed']
)
def test_injected_owner_measurement_rejects_non_access_metadata_change_during_verification(monkeypatch, tmp_path, field):
    with pytest.raises(AssertionError):
        _run_injected_owner_measurement(monkeypatch, tmp_path, mutation=field, boundary='verification read')

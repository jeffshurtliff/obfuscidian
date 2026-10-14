# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_owner_qualification
:Synopsis:          Refuse unavailable owner setup without privileged or filesystem fallback
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import ctypes
import json
from types import SimpleNamespace

import pytest

from tests import _windows_owner as owner


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
    monkeypatch.setattr(owner, '_owner_candidate', lambda api: b'SYNTHETIC SID MUST NOT PRINT' if available else None)
    assert owner._preflight() == (0 if available else 2)
    output = capsys.readouterr()
    assert 'SID' not in output.out and output.err == ''
    report = json.loads(output.out)
    assert report['assignable_owner_group_available'] is available
    assert report['scope'] == 'read-only token preflight; no filesystem owner proof'


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

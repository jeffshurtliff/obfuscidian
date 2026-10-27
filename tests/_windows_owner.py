# -*- coding: utf-8 -*-
"""
:Module:            tests._windows_owner
:Synopsis:          Read-only token eligibility for mandatory real filesystem owner proof
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     15 Oct 2026
"""

from __future__ import annotations

import ctypes
import json
import platform
import struct
import sys

from obfuscidian import _windows_native as native
from obfuscidian import constants as const


def _eligible_group(attributes: int, sid: bytes, current: bytes) -> bool:
    """Require enabled owner-assignable membership, excluding deny-only/current SID."""
    return bool(attributes & 8 and attributes & 4 and not attributes & 16 and sid != current)


def _owner_candidate(api: native._Api) -> bytes | None:
    """Read an existing token without activating privileges or changing membership."""
    wt, ptr = api.wt, ctypes.c_void_p

    class _Group(ctypes.Structure):
        _fields_ = [('sid', ptr), ('attributes', wt.DWORD)]

    class _Groups(ctypes.Structure):
        _fields_ = [('count', wt.DWORD), ('groups', _Group * 1)]

    token = wt.HANDLE()
    api._check(api.advapi.OpenProcessToken(api.kernel.GetCurrentProcess(), const.WINDOWS_TOKEN_QUERY, ctypes.byref(token)))
    try:
        length = wt.DWORD()
        api.advapi.GetTokenInformation(token, 2, None, 0, ctypes.byref(length))
        assert 8 <= length.value <= const.WINDOWS_SECURITY_BYTES
        buffer = ctypes.create_string_buffer(length.value)
        api._check(api.advapi.GetTokenInformation(token, 2, buffer, len(buffer), ctypes.byref(length)))
        count = _Groups.from_buffer(buffer).count
        assert _Groups.groups.offset + count * ctypes.sizeof(_Group) <= len(buffer)
        groups = (_Group * count).from_buffer(buffer, _Groups.groups.offset)
        current, _ = api._owner()
        for group in groups:
            api._check(api.advapi.IsValidSid(group.sid))
            size = api.advapi.GetLengthSid(group.sid)
            assert 8 <= size <= 68
            sid = ctypes.string_at(group.sid, size)
            if _eligible_group(group.attributes, sid, current):
                return sid
        return None
    finally:
        api._check(api.kernel.CloseHandle(token))


def _security_state(handle: native._Handle) -> tuple[bytes, int, bytes]:
    """Observe actual owner and exact protected DACL on a retained filesystem handle."""
    api, ptr = handle.api, ctypes.c_void_p
    owner, dacl, descriptor = ptr(), ptr(), ptr()
    assert (
        api.advapi.GetSecurityInfo(
            handle.raw,
            1,
            const.WINDOWS_SECURITY_INFORMATION,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        == 0
    )
    try:
        api._check(api.advapi.IsValidSid(owner))
        api._check(api.advapi.IsValidAcl(dacl))
        control, revision = ctypes.c_uint16(), api.wt.DWORD()
        api._check(api.advapi.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)))
        assert control.value & const.WINDOWS_SD_PROTECTED
        size = struct.unpack('<H', ctypes.string_at(dacl.value + 2, 2))[0]
        assert 8 <= size <= const.WINDOWS_SECURITY_BYTES
        return ctypes.string_at(owner, api.advapi.GetLengthSid(owner)), control.value, ctypes.string_at(dacl, size)
    finally:
        api._check(api.kernel.LocalFree(descriptor) is None)


def _preflight() -> int:
    """Emit no SIDs/paths; unavailable setup is a blocker, never a qualification pass."""
    assert sys.platform == 'win32' and sys.implementation.name == 'cpython', 'Native Windows CPython required.'
    assert sys.version_info[:2] in ((3, 12), (3, 13), (3, 14)), 'Use supported Python 3.12–3.14.'
    assert struct.calcsize('P') == 8, '64-bit required.'
    assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Use an existing unelevated token.'
    from tests._windows_owner_vm import _runtime

    api = native._Api()
    runtime = _runtime(api)
    assert runtime['native_machine_code'] == 0x8664 and runtime['process_machine_code'] == 0, (
        'Native AMD64 guest/process required; ARM and emulation evidence is separate.'
    )
    available = _owner_candidate(api) is not None
    print(
        json.dumps(
            {
                'assignable_owner_group_available': available,
                'elevated': False,
                'version': platform.python_version(),
                'architecture': platform.machine(),
                'native_machine_code': runtime['native_machine_code'],
                'process_machine_code': runtime['process_machine_code'],
                'bits': 64,
                'store_package_path_detected': 'PythonSoftwareFoundation.Python.'
                in getattr(sys, '_base_executable', sys.executable),
                'scope': 'read-only token preflight; no filesystem owner proof',
            }
        )
    )
    return 0 if available else 2


if __name__ == '__main__':
    raise SystemExit(_preflight())

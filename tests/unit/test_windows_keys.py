# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_keys
:Synopsis:          Verify native Windows owner-only key access control
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

import ctypes
import os
from pathlib import Path

import pytest

from obfuscidian import keys
from obfuscidian.errors import _ConfigurationError


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows security APIs and ACL-capable storage.')
def test_native_owner_only_dacl(tmp_path: Path) -> None:
    """Check the actual created DACL, valid loading, and collision preservation."""
    from ctypes import wintypes

    path = tmp_path.resolve() / 'obfuscidian-synthetic.key'
    keys._generate_key(path)
    material = path.read_bytes()
    cipher, warnings = keys._load_key(path)
    assert cipher.decrypt(cipher.encrypt(b'SYNTHETIC')) == b'SYNTHETIC'
    assert warnings
    with pytest.raises(_ConfigurationError):
        keys._generate_key(path)
    assert path.read_bytes() == material

    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    get_security = advapi.GetNamedSecurityInfoW
    get_security.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD] + [ctypes.POINTER(wintypes.LPVOID)] * 5
    get_security.restype = wintypes.DWORD
    convert = advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(wintypes.DWORD),
    ]
    convert.restype = wintypes.BOOL
    free = kernel.LocalFree
    free.argtypes = [wintypes.LPVOID]
    free.restype = wintypes.LPVOID
    security = wintypes.LPVOID()
    text = wintypes.LPWSTR()
    assert get_security(str(path), 1, 4, None, None, None, None, ctypes.byref(security)) == 0
    try:
        assert convert(security, 1, 4, ctypes.byref(text), None)
        try:
            assert text.value.startswith('D:P')
            assert text.value.count('(') == 1
            assert ';;;OW)' in text.value
        finally:
            free(ctypes.cast(text, wintypes.LPVOID))
    finally:
        free(security)

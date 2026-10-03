# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows
:Synopsis:          Internal Windows exclusive key creation with a private DACL
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

from obfuscidian import constants as const


def _check_private_directory(path: Path) -> None:
    """Refuse volumes without persistent ACLs before creating any key entry."""
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    volume_path = kernel.GetVolumePathNameW
    volume_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    volume_path.restype = wintypes.BOOL
    information = kernel.GetVolumeInformationW
    information.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        wintypes.DWORD,
    ]
    information.restype = wintypes.BOOL
    volume = ctypes.create_unicode_buffer(32768)
    flags = wintypes.DWORD()
    if not volume_path(str(path), volume, len(volume)) or not information(
        volume.value, None, 0, None, None, ctypes.byref(flags), None, 0
    ):
        raise OSError('Cannot assess Windows volume access controls; no key was created.')
    if not flags.value & const.WINDOWS_PERSISTENT_ACLS:
        raise OSError('Key directory requires a Windows filesystem with persistent ACL support.')


def _create_private_key(path: Path) -> int:
    """Create a new binary key handle with a protected owner-only access list.

    Uses Windows CREATE_NEW, applying the DACL at creation rather than after
    writing. Privileged administrators/backup operators and filesystems without
    ACL enforcement remain outside this access restriction. Tested on Windows
    only when platform validation is available; no POSIX ACL claim is made.
    """
    import msvcrt
    from ctypes import wintypes

    class _SecurityAttributes(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('descriptor', wintypes.LPVOID), ('inherit', wintypes.BOOL)]

    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_SecurityAttributes),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    free = kernel.LocalFree
    free.argtypes = [wintypes.LPVOID]
    free.restype = wintypes.LPVOID
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    security = wintypes.LPVOID()
    # Protected DACL: generic-all access for OWNER RIGHTS, no inherited grants.
    if not convert(const.WINDOWS_KEY_DACL, 1, ctypes.byref(security), None):
        raise OSError('Cannot establish private key access permissions.')
    try:
        attributes = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), security, False)
        handle = create(str(path), 0x40000000, 0, ctypes.byref(attributes), 1, 0x00200080, None)
        if handle == wintypes.HANDLE(-1).value:
            error = ctypes.get_last_error()
            if error in (80, 183):
                raise FileExistsError('Key target already exists.')
            raise OSError('Cannot create a private key file.')
        try:
            return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
        except BaseException:
            close(handle)
            raise
    finally:
        free(security)

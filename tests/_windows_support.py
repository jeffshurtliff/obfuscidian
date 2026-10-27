# -*- coding: utf-8 -*-
"""
:Module:            tests._windows_support
:Synopsis:          Private fixture I/O, worker termination and path-free failure diagnostics
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import ctypes
import os
import re
import subprocess
from pathlib import Path

from obfuscidian._windows_native import _api_path, _NativeSafetyError


def _failure_details(error: BaseException) -> str:
    """Expose suppressed backend locations/numeric API codes without private arguments.

    Production transaction failures suppress their exception context for output
    privacy. The context still exists in memory; synthetic tests can identify its
    code locations without printing exception arguments or filesystem state.
    """
    details, seen = [], set()
    for _ in range(16):
        if error is None or id(error) in seen:
            break
        seen.add(id(error))
        frames = []
        traceback = error.__traceback__
        while traceback is not None:
            frame = traceback.tb_frame
            module = frame.f_globals.get('__name__', '')
            if isinstance(module, str) and module.startswith('obfuscidian.'):
                frames.append(f'{module}.{frame.f_code.co_name}:{traceback.tb_lineno}')
            traceback = traceback.tb_next
        status = ''
        if type(error) is _NativeSafetyError and len(error.args) == 1 and isinstance(error.args[0], str):
            # Accept only the native loader's two complete, path-free templates;
            # never format arbitrary OS/exception text, even from this class.
            codes = re.fullmatch(
                r'Native Windows call refused \((WinError [0-9]{1,10}|NTSTATUS 0x[0-9A-F]{8}, I/O 0x[0-9A-F]{8})\); '
                r'preserve pending artifacts\.',
                error.args[0],
            )
            if codes is not None:
                status = ' [' + codes.group(1) + ']'
            else:
                attributes = re.fullmatch(r'Unsupported Windows Git attributes refused \((0x[0-9a-f]{8})\)\.', error.args[0])
                if attributes is not None:
                    status = ' [Git attributes ' + attributes.group(1) + ']'
        details.append(type(error).__name__ + status + (': ' + ' -> '.join(frames) if frames else ': no backend frame'))
        error = error.__cause__ if error.__cause__ is not None else error.__context__
    return 'Synthetic lifecycle failure chain (code locations/numeric API status only):\n' + '\n'.join(details)


def _io_path(path: Path) -> Path:
    """Spell synthetic fixture I/O for long Windows paths without changing logical bindings."""
    return Path(_api_path(str(path))) if os.name == 'nt' else path


def _worker_pid(message: bytes, marker: bytes) -> int:
    """Require a complete readiness marker and the actual interpreter worker PID."""
    prefix = marker + b' '
    message = message.rstrip(b'\r\n')
    if not message.startswith(prefix):
        raise AssertionError('Synthetic worker did not reach its interruption boundary.')
    value = message[len(prefix) :]
    if not value.isdigit() or not 0 < int(value) <= 0xFFFFFFFF:
        raise AssertionError('Invalid synthetic worker PID.')
    return int(value)


def _descendant(worker: int, launcher: int, parents: dict[int, int]) -> bool:
    """Allow only the spawned launcher or its bounded, observed descendant chain."""
    seen = set()
    for _ in range(16):
        if worker == launcher:
            return True
        if worker in seen or worker not in parents:
            return False
        seen.add(worker)
        worker = parents[worker]
    return False


class _ProcessEntry(ctypes.Structure):
    _fields_ = [
        ('size', ctypes.c_uint32),
        ('usage', ctypes.c_uint32),
        ('pid', ctypes.c_uint32),
        ('heap', ctypes.c_size_t),
        ('module', ctypes.c_uint32),
        ('threads', ctypes.c_uint32),
        ('parent', ctypes.c_uint32),
        ('priority', ctypes.c_int32),
        ('flags', ctypes.c_uint32),
        ('executable', ctypes.c_wchar * 260),
    ]


def _process_api():
    """Bind test-only kernel calls with pointer-width-safe signatures."""
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'OpenProcess': ([ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32], ctypes.c_void_p),
        'CreateToolhelp32Snapshot': ([ctypes.c_uint32, ctypes.c_uint32], ctypes.c_void_p),
        'Process32FirstW': ([ctypes.c_void_p, ctypes.POINTER(_ProcessEntry)], ctypes.c_int),
        'Process32NextW': ([ctypes.c_void_p, ctypes.POINTER(_ProcessEntry)], ctypes.c_int),
        'TerminateProcess': ([ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
        'WaitForSingleObject': ([ctypes.c_void_p, ctypes.c_uint32], ctypes.c_uint32),
        'GetExitCodeProcess': ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)], ctypes.c_int),
        'CloseHandle': ([ctypes.c_void_p], ctypes.c_int),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = arguments, result
    return api


def _parents(api) -> dict[int, int]:
    """Read process ancestry without retaining or reporting machine process details."""
    snapshot = api.CreateToolhelp32Snapshot(2, 0)  # TH32CS_SNAPPROCESS
    if snapshot in (None, ctypes.c_void_p(-1).value):
        raise AssertionError('Synthetic worker ancestry snapshot failed.')
    try:
        entry = _ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        if not api.Process32FirstW(snapshot, ctypes.byref(entry)):
            raise AssertionError('Synthetic worker ancestry enumeration failed.')
        parents = {}
        while True:
            parents[entry.pid] = entry.parent
            if not api.Process32NextW(snapshot, ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                    raise AssertionError('Synthetic worker ancestry enumeration incomplete.')
                return parents
    finally:
        if not api.CloseHandle(snapshot):
            raise AssertionError('Synthetic worker snapshot close failed.')


def _terminate_worker(process: subprocess.Popen, message: bytes, marker: bytes = b'READY') -> None:
    """Kill and await the paused interpreter before releasing its input barrier.

    Windows venv executables can be redirectors. Waiting for the launcher alone
    does not establish worker death. Only the reported spawned worker is targeted;
    no privilege activation, policy change or filesystem operation is performed.
    """
    worker = _worker_pid(message, marker)
    if os.name != 'nt' or worker == os.getpid() or process.poll() is not None:
        raise AssertionError('Expected a live synthetic Windows child.')
    if process.stdin is None or process.stdin.closed:
        raise AssertionError('Synthetic worker input barrier was released before termination.')
    api = _process_api()
    # Hold the process object before ancestry validation/termination, preventing
    # a subsequent PID reuse from selecting a different process for termination.
    handle = api.OpenProcess(0x00101001, False, worker)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION | PROCESS_TERMINATE
    if not handle:
        raise AssertionError('Synthetic worker handle acquisition failed.')
    try:
        if not _descendant(worker, process.pid, _parents(api)):
            raise AssertionError('Reported worker is not a spawned synthetic descendant.')
        if not api.TerminateProcess(handle, 97):
            raise AssertionError('Synthetic worker termination failed.')
        if api.WaitForSingleObject(handle, 20_000) != 0:
            raise AssertionError('Actual synthetic worker death was not observed.')
        code = ctypes.c_uint32()
        if not api.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 97:
            raise AssertionError('Synthetic worker termination status mismatch.')
        if process.stdin.closed:
            raise AssertionError('Synthetic worker barrier released before death verification.')
    finally:
        if not api.CloseHandle(handle):
            raise AssertionError('Synthetic worker handle close failed.')
    process.wait(timeout=20)
    if process.returncode != 97:
        raise AssertionError('Synthetic launcher did not report the terminated worker status.')

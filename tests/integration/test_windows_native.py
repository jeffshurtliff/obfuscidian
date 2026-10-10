# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_windows_native
:Synopsis:          Native synthetic Windows primitive safety qualification tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import ctypes
import os
import queue
import struct
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from obfuscidian import _windows_native as native
from obfuscidian import constants as const

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Actual native Windows APIs required; mocks are not qualification.')


@pytest.fixture
def parent(tmp_path: Path) -> Path:
    """Require eligible runner storage; fail rather than silently skip native tests."""
    path = tmp_path.resolve()
    with native._Guard(path):
        pass
    return path


def test_binary_checkpoint_collision_and_no_write_inspection(parent: Path) -> None:
    before = set(parent.iterdir())
    with native._Guard(parent):
        pass
    assert set(parent.iterdir()) == before
    with native._Guard(parent) as guard:
        with guard._checkpoint('journal.json', b'\x00\xff\r\nSYNTHETIC') as record:
            assert record._read(const.TRANSACTION_JOURNAL_BYTES) == b'\x00\xff\r\nSYNTHETIC'
            record._private()
            flags = guard.api.wt.DWORD()
            assert guard.api.kernel.GetHandleInformation(record.raw, ctypes.byref(flags))
            assert not flags.value & 1
            with pytest.raises(FileExistsError):
                guard._checkpoint('journal.json', b'REPLACEMENT')
            with pytest.raises(native._NativeSafetyError):
                record._read(2)
    assert (parent / 'journal.json').read_bytes() == b'\x00\xff\r\nSYNTHETIC'


def test_private_directory_children_timestamp_and_delete(parent: Path) -> None:
    with native._Guard(parent) as guard:
        with guard._create_directory('private') as directory:
            directory._private()
            identity = directory._identity()
            assert identity.directory and len(identity.file_id) == 16
    with native._Guard(parent / 'private') as guard:
        with guard._open_file('payload', create=True) as payload:
            payload._write(b'SYNTHETIC\x00\xff', 100)
            payload._set_time(1_700_000_000_123_456_789)
            assert payload._identity().written == const.WINDOWS_FILETIME_EPOCH + 17_000_000_001_234_567
            payload._delete(payload._identity())
    assert not (parent / 'private' / 'payload').exists()
    with native._Guard(parent) as guard:
        # Open the existing directory with one mutation handle; do not duplicate
        # a guard whose sharing policy would conflict with DELETE access.
        with guard.api._open(str(parent / 'private'), directory=True, writable=True, removable=True) as directory:
            directory.parent = guard
            directory._delete(directory._identity())
    assert not (parent / 'private').exists()


def test_no_clobber_rename_full_identity_and_guard_lifetime(parent: Path) -> None:
    with native._Guard(parent) as guard:
        with guard._open_file('proposal', create=True) as proposal:
            proposal._write(b'SYNTHETIC', 100)
            expected = proposal._identity()
            (parent / 'late-target').write_bytes(b'KEEP')
            with pytest.raises(native._NativeSafetyError):
                guard._rename(proposal, 'late-target', expected)
            assert proposal._read(100) == b'SYNTHETIC'
            guard._rename(proposal, 'published', proposal._identity())
            assert expected._same_object(proposal._identity())
            assert proposal._read(100) == b'SYNTHETIC'
            proposal._private()
    assert (parent / 'late-target').read_bytes() == b'KEEP'
    assert not (parent / 'proposal').exists()


def test_guard_blocks_substitution_and_sharing_writers(parent: Path) -> None:
    child = parent / 'guarded'
    child.mkdir()
    with native._Guard(child) as guard:
        with pytest.raises(OSError):
            child.rename(parent / 'substituted')
        with pytest.raises(native._NativeSafetyError):
            guard.api._open(str(child), directory=True, writable=True)
        with guard._open_file('private', create=True, ownership=True) as record:
            record._write(b'SYNTHETIC OWNERSHIP', const.TRANSACTION_LOCK_BYTES)
            with pytest.raises(native._NativeSafetyError):
                guard._open_file('private', writable=True, ownership=True)
            with pytest.raises(OSError):
                (child / 'private').rename(child / 'changed')
            assert record._read(const.TRANSACTION_LOCK_BYTES) == b'SYNTHETIC OWNERSHIP'


def test_hard_link_refusal_preserves_bytes(parent: Path) -> None:
    with native._Guard(parent) as guard:
        with guard._open_file('original', create=True) as record:
            record._write(b'KEEP', 100)
    os.link(parent / 'original', parent / 'alias')
    with native._Guard(parent) as guard:
        with pytest.raises(native._NativeSafetyError, match='multiple file links'):
            guard._open_file('alias', writable=True)
    assert (parent / 'original').read_bytes() == (parent / 'alias').read_bytes() == b'KEEP'


def test_junction_refusal_and_in_place_reparse_guard(parent: Path) -> None:
    """Use unelevated junctions and actual FSCTL_SET_REPARSE_POINT attempts."""
    target, link = parent / 'target', parent / 'junction'
    target.mkdir()
    completed = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True, check=False)
    assert completed.returncode == 0, 'Required unelevated junction fixture unavailable.'
    try:
        with pytest.raises(native._NativeSafetyError):
            with native._Guard(link):
                pass
    finally:
        link.rmdir()
    api = native._Api()
    api._bind(
        api.kernel,
        'DeviceIoControl',
        api.wt.BOOL,
        [
            api.wt.HANDLE,
            api.wt.DWORD,
            ctypes.c_void_p,
            api.wt.DWORD,
            ctypes.c_void_p,
            api.wt.DWORD,
            ctypes.POINTER(api.wt.DWORD),
            ctypes.c_void_p,
        ],
    )
    substitute = ('\\??\\' + str(target)).encode('utf-16-le')
    printable = str(target).encode('utf-16-le')
    names = substitute + b'\x00\x00' + printable + b'\x00\x00'
    payload = (
        struct.pack('<IHHHHHH', 0xA0000003, 8 + len(names), 0, 0, len(substitute), len(substitute) + 2, len(printable)) + names
    )
    buffer = ctypes.create_string_buffer(payload)

    def convert(handle):
        returned = api.wt.DWORD()
        return api.kernel.DeviceIoControl(handle, 0x000900A4, buffer, len(payload), None, 0, ctypes.byref(returned), None)

    # A successful unguarded conversion establishes a working unelevated
    # fixture, rather than treating a malformed IOCTL/privilege failure as proof.
    positive = parent / 'positive-conversion'
    positive.mkdir()
    raw = api.kernel.CreateFileW(str(positive), const.WINDOWS_GENERIC_WRITE, 7, None, 3, const.WINDOWS_OPEN_FLAGS, None)
    assert raw != api.wt.HANDLE(-1).value
    try:
        assert convert(raw), 'Required valid unelevated junction conversion unavailable.'
    finally:
        api._check(api.kernel.CloseHandle(raw))
        positive.rmdir()

    victim = parent / 'guarded-conversion'
    victim.mkdir()
    # Attribute opens are not covered by ordinary write-sharing restrictions.
    # Retain one from BEFORE guard acquisition and attempt actual conversion.
    raw = api.kernel.CreateFileW(str(victim), 0x100, 7, None, 3, const.WINDOWS_OPEN_FLAGS, None)
    assert raw != api.wt.HANDLE(-1).value
    try:
        with native._Guard(victim) as guard:
            assert not convert(raw), 'Guard failed to prevent in-place reparse conversion.'
            assert ctypes.get_last_error() in (5, 32), 'Denial must be access/sharing enforcement.'
            guard._check()
            with pytest.raises(native._NativeSafetyError):
                guard.api._open(str(victim), directory=True, writable=True)
    finally:
        api._check(api.kernel.CloseHandle(raw))
        victim.rmdir()


def _set_descriptor(api: native._Api, path: Path, text: str) -> None:
    """Install synthetic unsafe access controls for refusal tests only."""
    api._bind(api.advapi, 'SetFileSecurityW', api.wt.BOOL, [api.wt.LPCWSTR, api.wt.DWORD, ctypes.c_void_p])
    descriptor = ctypes.c_void_p()
    api._check(api.advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(text, 1, ctypes.byref(descriptor), None))
    try:
        api._check(api.advapi.SetFileSecurityW(str(path), 0x80000004, descriptor))
    finally:
        api._check(api.kernel.LocalFree(descriptor) is None)


@pytest.mark.parametrize('policy', ['null', 'extra', 'inherited', 'owner-rights', 'object-ace'])
def test_existing_unsafe_acl_refused_without_repair(parent: Path, policy: str) -> None:
    path = parent / 'unsafe'
    api = native._Api()
    _, sid = api._owner()
    path.write_bytes(b'KEEP')
    descriptors = {
        'null': f'O:{sid}D:NO_ACCESS_CONTROL',
        'extra': f'O:{sid}D:P(A;;FA;;;{sid})(A;;GR;;;WD)',
        'inherited': f'O:{sid}D:P(A;ID;FA;;;{sid})',
        # OWNER RIGHTS keeps the actual owner able to read this synthetic file;
        # it is deliberately not the effective owner policy accepted by #26.
        'owner-rights': 'D:P(A;;FA;;;OW)',
        'object-ace': f'O:{sid}D:P(OA;;FA;00000000-0000-0000-0000-000000000001;;{sid})',
    }
    _set_descriptor(api, path, descriptors[policy])
    with native._Guard(parent) as guard:
        with pytest.raises(native._NativeSafetyError):
            guard._open_file('unsafe')
    assert path.read_bytes() == b'KEEP'


def test_exclusive_process_death_reacquisition_and_retained_record(parent: Path) -> None:
    """Terminate a real owner and reacquire its retained complete private record."""
    script = """
import sys
from pathlib import Path
from obfuscidian._windows_native import _Guard
from obfuscidian.constants import TRANSACTION_LOCK_BYTES
with _Guard(Path(sys.argv[1])) as guard:
    with guard._open_file('ownership', create=True, ownership=True) as record:
        record._write(b'SYNTHETIC COMPLETE OWNERSHIP', TRANSACTION_LOCK_BYTES)
        print('READY', flush=True)
        sys.stdin.buffer.read(1)
"""
    child = subprocess.Popen(
        [sys.executable, '-c', script, str(parent)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    messages: queue.Queue[bytes] = queue.Queue()
    reader = threading.Thread(target=lambda: messages.put(child.stdout.readline()), daemon=True)
    reader.start()
    try:
        assert messages.get(timeout=20).strip() == b'READY'
        with native._Guard(parent) as guard:
            with pytest.raises(native._NativeSafetyError):
                guard._open_file('ownership', writable=True, ownership=True)
        child.terminate()
        child.wait(timeout=20)
        with native._Guard(parent) as guard:
            with guard._open_file('ownership', writable=True, ownership=True) as record:
                assert record._read(const.TRANSACTION_LOCK_BYTES) == b'SYNTHETIC COMPLETE OWNERSHIP'
                # Mere reacquisition/close never removes pending ownership.
        assert (parent / 'ownership').read_bytes() == b'SYNTHETIC COMPLETE OWNERSHIP'
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=20)
        reader.join(timeout=5)


def test_restricted_token_accesscheck_and_actual_kernel_denial(parent: Path) -> None:
    """Require descriptor denial AND a denied real open with a restricted token.

    The token's restricting SID is Everyone, which is absent from private DACLs.
    This creates no user account and activates no privileges. Setup failure is
    a qualification failure, not a skip. A permissive synthetic control must
    open successfully to prove denial is attributable to the private object.
    """
    api = native._Api()
    wt, ptr = api.wt, ctypes.c_void_p
    phandle = ctypes.POINTER(wt.HANDLE)
    pword = ctypes.POINTER(wt.DWORD)

    class _SidAndAttributes(ctypes.Structure):
        _fields_ = [('sid', ptr), ('attributes', wt.DWORD)]

    class _Mapping(ctypes.Structure):
        _fields_ = [(name, wt.DWORD) for name in ('read', 'write', 'execute', 'all')]

    api._bind(api.advapi, 'ConvertStringSidToSidW', wt.BOOL, [wt.LPCWSTR, ctypes.POINTER(ptr)])
    api._bind(
        api.advapi, 'CreateRestrictedToken', wt.BOOL, [wt.HANDLE, wt.DWORD, wt.DWORD, ptr, wt.DWORD, ptr, wt.DWORD, ptr, phandle]
    )
    api._bind(api.advapi, 'DuplicateToken', wt.BOOL, [wt.HANDLE, ctypes.c_int, phandle])
    api._bind(api.advapi, 'ImpersonateLoggedOnUser', wt.BOOL, [wt.HANDLE])
    api._bind(api.advapi, 'RevertToSelf', wt.BOOL, [])
    api._bind(
        api.advapi,
        'AccessCheck',
        wt.BOOL,
        [ptr, wt.HANDLE, wt.DWORD, ctypes.POINTER(_Mapping), ptr, pword, pword, ctypes.POINTER(wt.BOOL)],
    )
    process_token, restricted, impersonation = wt.HANDLE(), wt.HANDLE(), wt.HANDLE()
    everyone = ptr()
    private_path, control_path = parent / 'private-file', parent / 'public-control'
    with native._Guard(parent) as guard:
        with guard._open_file('private-file', create=True) as record:
            record._write(b'SYNTHETIC PRIVATE', 100)
    control_path.write_bytes(b'SYNTHETIC PUBLIC')
    _, sid = api._owner()
    _set_descriptor(api, control_path, f'O:{sid}D:P(A;;FA;;;{sid})(A;;GR;;;WD)')
    # Give the restricted token traversal/list rights on this synthetic parent
    # only. The private file's explicit protected DACL remains unchanged.
    _set_descriptor(api, parent, f'O:{sid}D:P(A;OICI;FA;;;{sid})(A;OICI;GRGX;;;WD)')
    try:
        api._check(api.advapi.OpenProcessToken(api.kernel.GetCurrentProcess(), 0xA, ctypes.byref(process_token)))
        api._check(api.advapi.ConvertStringSidToSidW('S-1-1-0', ctypes.byref(everyone)))
        restricting = _SidAndAttributes(everyone, 0)
        api._check(
            api.advapi.CreateRestrictedToken(
                process_token, 1, 0, None, 0, None, 1, ctypes.byref(restricting), ctypes.byref(restricted)
            )
        )
        api._check(api.advapi.DuplicateToken(restricted, 2, ctypes.byref(impersonation)))
        with native._Guard(parent) as guard:
            with guard._open_file('private-file') as record:
                owner, group, dacl, descriptor = ptr(), ptr(), ptr(), ptr()
                assert (
                    api.advapi.GetSecurityInfo(
                        record.raw,
                        1,
                        7,
                        ctypes.byref(owner),
                        ctypes.byref(group),
                        ctypes.byref(dacl),
                        None,
                        ctypes.byref(descriptor),
                    )
                    == 0
                )
                try:
                    mapping = _Mapping(0x120089, 0x120116, 0x1200A0, const.WINDOWS_FILE_ALL_ACCESS)
                    privileges = ctypes.create_string_buffer(4096)
                    length, granted, access = wt.DWORD(len(privileges)), wt.DWORD(), wt.BOOL()
                    api._check(
                        api.advapi.AccessCheck(
                            descriptor,
                            impersonation,
                            1,
                            ctypes.byref(mapping),
                            privileges,
                            ctypes.byref(length),
                            ctypes.byref(granted),
                            ctypes.byref(access),
                        )
                    )
                    assert not access.value and not granted.value
                finally:
                    api._check(api.kernel.LocalFree(descriptor) is None)
        api._check(api.advapi.ImpersonateLoggedOnUser(impersonation))
        try:
            # Raw CreateFileW is intentional: test enforcement, without the
            # validator's earlier rejection or exclusive sharing hiding it.
            opened = api.kernel.CreateFileW(str(private_path), 1, 7, None, 3, const.WINDOWS_OPEN_FLAGS, None)
            if opened != wt.HANDLE(-1).value:
                api.kernel.CloseHandle(opened)
                pytest.fail('Restricted token opened private synthetic content.')
            assert ctypes.get_last_error() == 5
            opened = api.kernel.CreateFileW(str(control_path), 1, 7, None, 3, const.WINDOWS_OPEN_FLAGS, None)
            assert opened != wt.HANDLE(-1).value, 'Restricted token positive access control failed.'
            api._check(api.kernel.CloseHandle(opened))
        finally:
            api._check(api.advapi.RevertToSelf())
    finally:
        for token in (impersonation, restricted, process_token):
            if token.value:
                api._check(api.kernel.CloseHandle(token))
        if everyone.value:
            api._check(api.kernel.LocalFree(everyone) is None)
    assert private_path.read_bytes() == b'SYNTHETIC PRIVATE'


def test_native_short_write_flush_failure_and_pending_preservation(parent: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Injected API failures supplement native handles; they are not native proof."""
    with native._Guard(parent) as guard:
        with guard._open_file('pending', create=True, ownership=True) as record:
            write = guard.api.kernel.WriteFile

            def partial(handle, buffer, length, output, overlapped):
                return write(handle, buffer, min(length, 2), output, overlapped)

            monkeypatch.setattr(guard.api.kernel, 'WriteFile', partial)
            record._write(b'SYNTHETIC', 100)
            assert record._read(100) == b'SYNTHETIC'
            monkeypatch.setattr(guard.api.kernel, 'FlushFileBuffers', lambda _: False)
            with pytest.raises(native._NativeSafetyError):
                record._write(b'RETAIN', 100)
    assert (parent / 'pending').read_bytes() == b'RETAIN'


def test_native_directory_rename_and_unknown_child_deletion_refusal(parent: Path) -> None:
    with native._Guard(parent) as guard:
        with guard._create_directory('proposal-dir') as directory:
            expected = directory._identity()
            guard._rename(directory, 'published-dir', expected)
            assert expected._same_object(directory._identity())
            (parent / 'published-dir' / 'unknown').write_bytes(b'KEEP')
            with pytest.raises(native._NativeSafetyError):
                directory._delete(directory._identity())
    assert (parent / 'published-dir' / 'unknown').read_bytes() == b'KEEP'


def test_explicit_terminal_release_and_closed_guard_refusal(parent: Path) -> None:
    with native._Guard(parent) as guard:
        record = guard._open_file('ownership', create=True, ownership=True)
        try:
            record._write(b'SYNTHETIC TERMINAL', const.TRANSACTION_LOCK_BYTES)
            with pytest.raises(native._NativeSafetyError):
                record._release_ownership(b'WRONG')
            record._release_ownership(b'SYNTHETIC TERMINAL')
            assert record.raw is None
        finally:
            record._close()
        pending = guard._open_file('pending', create=True)
    try:
        with pytest.raises(native._NativeSafetyError, match='parent guard'):
            pending._write(b'UNSAFE', 100)
    finally:
        pending._close()
    assert not (parent / 'ownership').exists()
    assert (parent / 'pending').read_bytes() == b''

# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_native
:Synopsis:          Test portable validation and native boundary refusal
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

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


@pytest.mark.skipif(os.name == 'nt', reason='POSIX refusal only; native tests exercise actual APIs.')
def test_native_loader_refuses_posix() -> None:
    with pytest.raises(native._NativeSafetyError, match='native 64-bit Windows'):
        native._Api()


def test_checkpoint_replacement_refuses_before_open() -> None:
    # No simulated OS: this tests the unconditional unqualified-operation gate.
    guard = object.__new__(native._Guard)
    with pytest.raises(native._NativeSafetyError, match='replacement remains unqualified'):
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

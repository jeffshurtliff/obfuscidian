# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_opened_metadata
:Synopsis:          Windows descriptor timestamp compatibility and change rejection
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     06 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from obfuscidian import inventory, manifest, paths, transactions
from obfuscidian.errors import _OperationalError


@pytest.fixture
def windows_descriptor_metadata(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Model path creation time versus descriptor change time without hiding either."""
    real_fstat = os.fstat
    native_windows = os.name == 'nt'
    control = {'calls': 0, 'change': None}

    def descriptor_stat(descriptor: int) -> SimpleNamespace:
        info = real_fstat(descriptor)
        fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
        if stat.S_ISREG(info.st_mode):
            control['calls'] += 1
            # POSIX path ctime represents change time; use it as the synthetic
            # creation value to match the unchanged path observation in this model.
            fields['st_birthtime_ns'] = info.st_birthtime_ns if native_windows else info.st_ctime_ns
            fields['st_ctime_ns'] = info.st_ctime_ns + 10000
            if control['calls'] == 2 and control['change']:
                fields[control['change']] += 1
        return SimpleNamespace(**fields)

    monkeypatch.setattr(os, 'fstat', descriptor_stat)
    monkeypatch.setattr(paths, 'os', SimpleNamespace(name='nt', stat=os.stat, scandir=os.scandir))
    return control


def _reader(tmp_path: Path, mode: str):
    """Build an actual temporary binary source/token and return its production reader."""
    root = tmp_path.resolve() / 'synthetic'
    root.mkdir()
    file = root / 'payload.bin'
    data = bytes(range(256)) + b'\r\n\x00\xff'
    if mode == 'token':
        data = Fernet(Fernet.generate_key()).encrypt(data)
    file.write_bytes(data)
    if mode == 'source':
        observed = inventory._scan_inventory(root)
        return lambda: inventory._read_file(observed, observed.entries[0]), data
    if mode == 'token':
        observed = paths._inspect_path(file, kind='file')
        return lambda: manifest._read_token(observed), data
    return lambda: transactions._capture(file)['digest'], hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize('mode', ['source', 'token', 'capture'])
def test_distinct_descriptor_change_time_allows_stable_read(tmp_path: Path, windows_descriptor_metadata: dict, mode: str) -> None:
    """Stable files read successfully despite distinct path/descriptor ctime semantics."""
    read, expected = _reader(tmp_path, mode)
    assert read() == expected
    assert windows_descriptor_metadata['calls'] == 2


@pytest.mark.parametrize('mode', ['source', 'token', 'capture'])
@pytest.mark.parametrize('change', ['st_ctime_ns', 'st_birthtime_ns', 'st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns'])
def test_descriptor_change_rejects_all_payloads(
    tmp_path: Path, windows_descriptor_metadata: dict, mode: str, change: str
) -> None:
    """Reject even change-time-only drift when creation time, size and mtime stay stable."""
    read, _ = _reader(tmp_path, mode)
    windows_descriptor_metadata['change'] = change
    with pytest.raises(_OperationalError, match='changed'):
        read()
    assert windows_descriptor_metadata['calls'] == 2


@pytest.mark.parametrize('field', ['st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_birthtime_ns'])
def test_opened_metadata_still_binds_every_comparable_field(monkeypatch: pytest.MonkeyPatch, field: str) -> None:
    """Timestamp compatibility must never accept a different file or payload observation."""
    monkeypatch.setattr(paths, 'os', SimpleNamespace(name='nt'))
    expected = paths._Fingerprint(10, 20, stat.S_IFREG | 0o600, 30, 40, 50)
    observed = dict(
        st_dev=10, st_ino=20, st_mode=stat.S_IFREG | 0o600, st_size=30, st_mtime_ns=40, st_ctime_ns=60, st_birthtime_ns=50
    )
    assert expected._matches_open_stat(SimpleNamespace(**observed))
    observed[field] += 1
    assert not expected._matches_open_stat(SimpleNamespace(**observed))


@pytest.mark.parametrize('birthtime', [None, True, '50'])
def test_invalid_creation_metadata_cannot_bypass_ctime(monkeypatch: pytest.MonkeyPatch, birthtime: object) -> None:
    """Absent or malformed creation metadata cannot justify a ctime mismatch."""
    monkeypatch.setattr(paths, 'os', SimpleNamespace(name='nt'))
    expected = paths._Fingerprint(10, 20, stat.S_IFREG | 0o600, 30, 40, 50)
    observed = SimpleNamespace(
        st_dev=10, st_ino=20, st_mode=stat.S_IFREG | 0o600, st_size=30, st_mtime_ns=40, st_ctime_ns=60, st_birthtime_ns=birthtime
    )
    assert not expected._matches_open_stat(observed)


@pytest.mark.parametrize('platform', ['nt', 'posix'])
def test_exact_ctime_matches_and_posix_has_no_creation_fallback(monkeypatch: pytest.MonkeyPatch, platform: str) -> None:
    """Allow exact metadata on every host and never substitute POSIX change time."""
    monkeypatch.setattr(paths, 'os', SimpleNamespace(name=platform))
    expected = paths._Fingerprint(10, 20, stat.S_IFREG | 0o600, 30, 40, 50)
    observed = SimpleNamespace(
        st_dev=10, st_ino=20, st_mode=stat.S_IFREG | 0o600, st_size=30, st_mtime_ns=40, st_ctime_ns=50, st_birthtime_ns=40
    )
    assert expected._matches_open_stat(observed)
    observed.st_ctime_ns = 60
    assert not expected._matches_open_stat(observed)

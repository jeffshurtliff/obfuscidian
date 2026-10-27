# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_checkpoints
:Synopsis:          Bounded checkpoint framing and supplementary failure tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from obfuscidian import _windows_checkpoints as checkpoints
from obfuscidian import constants as const
from obfuscidian._windows_native import _NativeSafetyError

OWNER = bytes(range(16))  # Synthetic ID only; never a native runtime identity.


def test_framing_preserves_binary_bytes_and_binds_previous_record() -> None:
    payload = bytes(range(256)) + b'\r\n'
    first = checkpoints._encode(payload, 1, 1, OWNER, bytes(32))
    assert checkpoints._decode(first, 1, 1, OWNER, bytes(32)) == payload
    predecessor = hashlib.sha256(first).digest()
    second = checkpoints._encode(b'SYNTHETIC SECOND', 2, 1, OWNER, predecessor)
    assert checkpoints._decode(second, 2, 1, OWNER, predecessor) == b'SYNTHETIC SECOND'
    for generation, volume, owner, previous in [
        (1, 1, OWNER, predecessor),
        (2, 2, OWNER, predecessor),
        (2, 1, OWNER[::-1], predecessor),
        (2, 1, OWNER, bytes(32)),
    ]:
        with pytest.raises(_NativeSafetyError):
            checkpoints._decode(second, generation, volume, owner, previous)


@pytest.mark.parametrize('offset', [0, 8, 16, 24, 40, 72])
def test_malformed_framing_refused(offset: int) -> None:
    record = bytearray(checkpoints._encode(b'SYNTHETIC', 1, 1, OWNER, bytes(32)))
    record[offset] ^= 1
    with pytest.raises(_NativeSafetyError):
        checkpoints._decode(bytes(record), 1, 1, OWNER, bytes(32))


def test_frame_exact_bound_and_truncation() -> None:
    limit = const.TRANSACTION_JOURNAL_BYTES - checkpoints._HEADER.size
    record = checkpoints._encode(b'x' * limit, 1, 1, OWNER, bytes(32))
    assert len(record) == const.TRANSACTION_JOURNAL_BYTES
    assert len(checkpoints._decode(record, 1, 1, OWNER, bytes(32))) == limit
    for broken in [record[:-1], record + b'x', b'', record[:20]]:
        with pytest.raises(_NativeSafetyError):
            checkpoints._decode(broken, 1, 1, OWNER, bytes(32))
    with pytest.raises(_NativeSafetyError):
        checkpoints._encode(b'x' * (limit + 1), 1, 1, OWNER, bytes(32))


class _SupplementaryGuard:
    """Use synthetic files to test sequencing only, without a native safety claim."""

    def __init__(self, root: Path):
        self.path = str(root)
        self.fail_rename = False
        self.fail_write = False

    @contextmanager
    def _open_file(self, name):
        path = Path(self.path) / name
        yield SimpleNamespace(_identity=lambda: SimpleNamespace(size=path.stat().st_size), _read=lambda limit: path.read_bytes())

    @contextmanager
    def _checkpoint(self, name, record):
        path = Path(self.path) / name
        with path.open('xb') as output:
            output.write(record[:3] if self.fail_write else record)
        if self.fail_write:
            raise _NativeSafetyError('SYNTHETIC WRITE FAILURE')
        yield SimpleNamespace(path=path, _identity=lambda: None)

    def _rename(self, handle, target, expected):
        if self.fail_rename:
            raise _NativeSafetyError('SYNTHETIC SHARING FAILURE')
        destination = Path(self.path) / target
        if destination.exists():
            raise FileExistsError('SYNTHETIC COLLISION')
        handle.path.rename(destination)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Bypass native setup solely for portable algorithm/failure regression."""
    result = object.__new__(checkpoints._CheckpointStore)
    result.guard = _SupplementaryGuard(tmp_path)
    result.owner_identity = SimpleNamespace(volume=1, file_id=OWNER)
    result.prefix = const.WINDOWS_CHECKPOINT_PREFIX + 'synthetic-'
    result._check = lambda: None
    monkeypatch.setattr(checkpoints, '_api_path', lambda path: path)
    return result


def test_logical_replacement_retains_old_bytes_and_rejects_stale_observation(store) -> None:
    first = store._append(b'SYNTHETIC OLD')
    root = Path(store.guard.path)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    second = store._append(b'SYNTHETIC NEW', previous=first)
    assert second.generation == 2 and second.payload == b'SYNTHETIC NEW'
    assert all((root / name).read_bytes() == data for name, data in before.items())
    assert store._read() == second
    for previous in [None, first, replace(second, digest=bytes(32))]:
        with pytest.raises(_NativeSafetyError):
            store._append(b'UNSAFE', previous=previous)
    assert store._read() == second


@pytest.mark.parametrize('failure', ['fail_write', 'fail_rename'])
def test_interrupted_candidate_does_not_replace_authoritative_checkpoint(store, failure) -> None:
    first = store._append(b'KEEP')
    setattr(store.guard, failure, True)
    with pytest.raises(_NativeSafetyError):
        store._append(b'PROPOSED', previous=first)
    after = store._read()
    assert after.generation == first.generation and after.digest == first.digest and after.payload == b'KEEP'
    assert after.pending is not None
    with pytest.raises(_NativeSafetyError, match='reconciliation'):
        store._append(b'RETRY', previous=after)


@pytest.mark.parametrize('problem', ['gap', 'duplicate', 'corrupt', 'unknown', 'foreign', 'pending-generation'])
def test_ambiguous_or_changed_control_namespace_refused(store, problem) -> None:
    first = store._append(b'KEEP')
    store._append(b'NEW', previous=first)
    root = Path(store.guard.path)
    paths = sorted(root.iterdir())
    if problem == 'gap':
        paths[0].unlink()
    elif problem == 'duplicate':
        extra = paths[0].name.replace(paths[0].name[-68:-4], '0' * 64)
        (root / extra).write_bytes(paths[0].read_bytes())
    elif problem == 'corrupt':
        paths[0].write_bytes(b'CHANGED')
    elif problem == 'unknown':
        (root / 'unknown').write_bytes(b'KEEP')
    elif problem == 'foreign':
        (root / (store.prefix.upper() + 'unknown')).write_bytes(b'KEEP')
    else:
        (root / f'{store.prefix}{1:016x}.pending').write_bytes(b'INCOMPLETE')
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    with pytest.raises(_NativeSafetyError):
        store._read()
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}


def test_count_and_storage_budget_refused_before_candidate_create(store, monkeypatch) -> None:
    first = store._append(b'KEEP')
    root = Path(store.guard.path)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    monkeypatch.setattr(const, 'WINDOWS_CHECKPOINT_COUNT', 1)
    with pytest.raises(_NativeSafetyError):
        store._append(b'NEW', previous=first)
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}
    monkeypatch.setattr(const, 'WINDOWS_CHECKPOINT_COUNT', 4096)
    monkeypatch.setattr(const, 'WINDOWS_CHECKPOINT_TOTAL_BYTES', first.total_bytes)
    with pytest.raises(_NativeSafetyError):
        store._append(b'NEW', previous=first)
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}


def test_publication_postcheck_failure_is_an_error_with_committed_record_retained(store, monkeypatch) -> None:
    first = store._append(b'KEEP')
    original = store.guard._rename

    def rename_then_fail(handle, target, expected):
        original(handle, target, expected)
        raise _NativeSafetyError('SYNTHETIC POST-PUBLICATION FAILURE')

    with monkeypatch.context() as injected:
        injected.setattr(store.guard, '_rename', rename_then_fail)
        with pytest.raises(_NativeSafetyError):
            store._append(b'NEXT', previous=first)
    actual = store._read()
    assert (actual.generation, actual.payload, actual.pending) == (2, b'NEXT', None)


def test_namespace_change_during_read_refused_before_append(store, monkeypatch) -> None:
    first = store._append(b'KEEP')
    original = store._names
    calls = 0

    def changing_names():
        nonlocal calls
        calls += 1
        names = original()
        return names if calls == 1 else names + ['SYNTHETIC CHANGED ENUMERATION']

    before = original()
    monkeypatch.setattr(store, '_names', changing_names)
    with pytest.raises(_NativeSafetyError, match='namespace changed'):
        store._append(b'REFUSED', previous=first)
    assert original() == before

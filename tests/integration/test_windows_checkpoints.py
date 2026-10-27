# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_windows_checkpoints
:Synopsis:          Native immutable checkpoint and interruption qualification
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import queue
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import _windows_native as native
from obfuscidian import constants as const
from obfuscidian import keys
from obfuscidian._windows_checkpoints import _CheckpointStore, _encode
from obfuscidian.cli import cli
from tests._windows_support import _terminate_worker

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Actual native Windows APIs required; mocks are not qualification.')


@pytest.fixture
def parent(tmp_path: Path) -> Path:
    """Require eligible actual storage instead of skipping fixture failures."""
    path = tmp_path.resolve()
    with native._Guard(path):
        pass
    return path


@contextmanager
def _store(parent: Path):
    """Hold exclusive ownership and a separately guarded private control folder."""
    with native._Guard(parent) as guard:
        with guard._open_file('ownership', create=True, ownership=True) as ownership:
            ownership._write(b'SYNTHETIC OWNERSHIP', const.TRANSACTION_LOCK_BYTES)
            with guard._create_directory('controls'):
                pass
            with native._Guard(parent / 'controls') as controls:
                yield _CheckpointStore(controls, ownership)


@pytest.mark.parametrize('existing_log', [False, True])
def test_native_primitives_do_not_enable_cli_mutation_or_existing_log_append(parent: Path, existing_log: bool) -> None:
    source, mirror, key = parent / 'source', parent / 'mirror', parent / 'synthetic.key'
    source.mkdir()
    (source / 'note.md').write_bytes(b'SYNTHETIC KEEP\r\n\x00\xff')
    keys._generate_key(key)
    arguments = ['shroud', 'fresh', '--origin', str(source), '--mirror', str(mirror), '--key', str(key), '--non-interactive']
    if existing_log:
        log = parent / 'existing.jsonl'
        log.write_bytes(b'SYNTHETIC EXISTING LOG KEEP\n')
        arguments += ['--log-file', str(log)]
    before = {path.relative_to(parent): path.read_bytes() for path in parent.rglob('*') if path.is_file()}
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == (2 if existing_log else 1), result.output
    assert (
        'Appending existing Windows logs' if existing_log else 'Cannot obtain exclusive transaction ownership'
    ) in result.output
    if not existing_log:
        assert 'no payload was published' in result.output
    assert not mirror.exists()
    assert {path.relative_to(parent): path.read_bytes() for path in parent.rglob('*') if path.is_file()} == before
    assert set(parent.iterdir()) == {source, key, *([log] if existing_log else [])}


def test_logical_replacement_retains_full_old_identity_and_binary_bytes(parent: Path) -> None:
    with _store(parent) as store:
        first = store._append(b'FIRST\x00\xff\r\n')
        old_name = store._names()[0]
        with store.guard._open_file(old_name) as old:
            old_identity, old_bytes = old._identity(), old._read(const.TRANSACTION_JOURNAL_BYTES)
        second = store._append(b'SECOND\xff\x00', previous=first)
        assert (second.generation, second.payload, second.pending) == (2, b'SECOND\xff\x00', None)
        with store.guard._open_file(old_name) as old:
            assert old_identity._same_object(old._identity())
            assert old._read(const.TRANSACTION_JOURNAL_BYTES) == old_bytes
            old._private()
        before = store._names()
        with pytest.raises(native._NativeSafetyError):
            store._append(b'STALE', previous=first)
        assert store._names() == before


def test_long_checkpoint_namespace_does_not_require_global_long_path_policy(parent: Path) -> None:
    """Exercise actual native create/read/rename beyond the legacy 260 bound."""
    child = 'synthetic-long-parent-' + 'x' * 140
    with native._Guard(parent) as guard:
        with guard._create_directory(child):
            pass
    with _store(parent / child) as store:
        first = store._append(b'KEEP')
        second = store._append(b'NEXT', previous=first)
        assert all(len(store.guard.path + '\\' + name) > 260 for name in store._names())
        assert store._read() == second


@pytest.mark.parametrize('failure', ['flush', 'rename', 'after-rename'])
def test_failed_publication_preserves_previous_and_reports_actual_namespace(parent: Path, monkeypatch, failure: str) -> None:
    with _store(parent) as store:
        first = store._append(b'KEEP')
        old_name = store._names()[0]
        original_rename = store.guard._rename

        def rename(handle, name, expected):
            if failure == 'after-rename':
                original_rename(handle, name, expected)
            raise native._fail('Synthetic publication failure.')

        with monkeypatch.context() as injected:
            if failure == 'flush':
                injected.setattr(store.guard.api.kernel, 'FlushFileBuffers', lambda handle: False)
            else:
                injected.setattr(store.guard, '_rename', rename)
            with pytest.raises(native._NativeSafetyError):
                store._append(b'NEXT', previous=first)
        actual = store._read()
        if failure == 'after-rename':
            assert (actual.generation, actual.payload, actual.pending) == (2, b'NEXT', None)
        else:
            assert (actual.generation, actual.payload) == (1, b'KEEP')
            assert actual.pending is not None
            with pytest.raises(native._NativeSafetyError):
                store._append(b'RETRY', previous=actual)
        with store.guard._open_file(old_name) as old:
            assert hashlib.sha256(old._read(const.TRANSACTION_JOURNAL_BYTES)).digest() == first.digest


def test_late_target_is_never_overwritten(parent: Path, monkeypatch) -> None:
    with _store(parent) as store:
        first = store._append(b'KEEP')
        original_rename = store.guard._rename
        collided = []

        def collide(handle, name, expected):
            with store.guard._checkpoint(name, b'LATE TARGET KEEP'):
                pass
            collided.append(name)
            original_rename(handle, name, expected)

        monkeypatch.setattr(store.guard, '_rename', collide)
        with pytest.raises(native._NativeSafetyError):
            store._append(b'PROPOSAL', previous=first)
        with store.guard._open_file(collided[0]) as target:
            assert target._read(100) == b'LATE TARGET KEEP'
        with pytest.raises(native._NativeSafetyError):
            store._read()
        assert len(store._names()) == 3  # Old record, uncertain candidate, preserved collision.


@pytest.mark.parametrize('unsafe', ['foreign', 'gap', 'digest', 'owner-binding', 'hard-link'])
def test_unsafe_control_chain_refused_without_cleanup(parent: Path, unsafe: str) -> None:
    with _store(parent) as store:
        first = store._append(b'KEEP')
        if unsafe == 'hard-link':
            name = store._names()[0]
            os.link(native._api_path(str(parent / 'controls' / name)), parent / 'outside-alias')
        else:
            record = _encode(
                b'UNTRUSTED',
                3 if unsafe == 'gap' else 2,
                store.owner_identity.volume,
                bytes([42]) * 16 if unsafe == 'owner-binding' else store.owner_identity.file_id,
                first.digest,
            )
            digest = bytes(32) if unsafe == 'digest' else hashlib.sha256(record).digest()
            name = 'foreign' if unsafe == 'foreign' else f'{store.prefix}{3 if unsafe == "gap" else 2:016x}-{digest.hex()}.bin'
            with store.guard._checkpoint(name, record):
                pass
        controls_path = Path(native._api_path(str(parent / 'controls')))
        before = {entry.name: entry.read_bytes() for entry in controls_path.iterdir()}
        with pytest.raises(native._NativeSafetyError):
            store._read()
        with pytest.raises(native._NativeSafetyError):
            store._append(b'REFUSED', previous=first)
        assert {entry.name: entry.read_bytes() for entry in controls_path.iterdir()} == before


_INTERRUPTED = """
import os, sys
from pathlib import Path
from obfuscidian import _windows_native as native
from obfuscidian import constants as const
from obfuscidian._windows_checkpoints import _CheckpointStore
parent, boundary = Path(sys.argv[1]), sys.argv[2]
def pause():
    print('READY', os.getpid(), flush=True)
    sys.stdin.buffer.read(1)
with native._Guard(parent) as guard:
    if boundary == 'directory-acquisition':
        original_adopt = guard.api._adopt
        def adopt(raw, path, **options):
            pause()
            return original_adopt(raw, path, **options)
        guard.api._adopt = adopt
        with guard._create_directory('controls'):
            pass
    else:
        with guard._open_file('ownership', create=True, ownership=True) as ownership:
            ownership._write(b'SYNTHETIC OWNERSHIP', const.TRANSACTION_LOCK_BYTES)
            with guard._create_directory('controls'):
                pass
            with native._Guard(parent / 'controls') as controls:
                store = _CheckpointStore(controls, ownership)
                first = store._append(b'KEEP')
                original_rename = controls._rename
                if boundary == 'partial-write':
                    original_write = native._Handle._write
                    def write(handle, data, limit):
                        original_write(handle, b'PARTIAL', limit)
                        pause()
                    native._Handle._write = write
                else:
                    def rename(handle, name, expected):
                        if boundary == 'after-publication':
                            original_rename(handle, name, expected)
                        pause()
                        if boundary == 'before-publication':
                            original_rename(handle, name, expected)
                    controls._rename = rename
                store._append(b'NEXT', previous=first)
"""


@pytest.mark.parametrize('boundary', ['partial-write', 'before-publication', 'after-publication', 'directory-acquisition'])
def test_actual_process_termination_retains_reconcilable_controls(parent: Path, boundary: str) -> None:
    """Terminate an actual native child at controlled filesystem boundaries.

    Injection chooses the boundary; Win32 handles, creation, writes, flushes,
    publication, process death and subsequent reacquisition are real. This
    exercises primitive retention, not transaction/recovery schema behavior.
    """
    child = subprocess.Popen(
        [sys.executable, '-c', _INTERRUPTED, str(parent), boundary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    messages: queue.Queue[bytes] = queue.Queue()
    reader = threading.Thread(target=lambda: messages.put(child.stdout.readline()), daemon=True)
    reader.start()
    try:
        message = messages.get(timeout=20)
        if not message.startswith(b'READY '):
            child.wait(timeout=20)
            diagnostic = child.stderr.read(8192).decode(errors='replace').replace(str(parent), '<synthetic-root>')
            pytest.fail(f'Native child exited {child.returncode} before the interruption boundary: {diagnostic}')
        if boundary != 'directory-acquisition':
            with native._Guard(parent) as guard:
                with pytest.raises(native._NativeSafetyError):
                    guard._open_file('ownership', writable=True, ownership=True)
        _terminate_worker(child, message)
        if boundary == 'directory-acquisition':
            with native._Guard(parent / 'controls') as guard:
                guard.handles[-1]._private()
            assert list((parent / 'controls').iterdir()) == []
            assert not (parent / 'ownership').exists()
        else:
            with native._Guard(parent) as guard:
                with guard._open_file('ownership', writable=True, ownership=True) as ownership:
                    assert ownership._read(const.TRANSACTION_LOCK_BYTES) == b'SYNTHETIC OWNERSHIP'
                    with native._Guard(parent / 'controls') as controls:
                        store = _CheckpointStore(controls, ownership)
                        actual = store._read()
                        if boundary == 'after-publication':
                            assert (actual.generation, actual.payload, actual.pending) == (2, b'NEXT', None)
                        else:
                            assert (actual.generation, actual.payload) == (1, b'KEEP')
                            assert actual.pending is not None
                            with pytest.raises(native._NativeSafetyError):
                                store._append(b'RETRY', previous=actual)
            assert (parent / 'ownership').exists()
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=20)
        reader.join(timeout=5)

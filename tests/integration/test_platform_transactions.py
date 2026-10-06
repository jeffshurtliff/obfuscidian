# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_platform_transactions
:Synopsis:          Resource loss and native process interruption recovery contracts
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import errno
import os
import select
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.errors import _OperationalError
from obfuscidian.paths import _TargetRules

pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Publication/recovery requires POSIX ownership and directory handles.')


@pytest.fixture
def locations(tmp_path: Path):
    """Keep transaction payload and protected controls entirely synthetic."""
    root = tmp_path.resolve()
    source, destination = root / 'source', root / 'destination'
    source.mkdir()
    (source / 'sentinel.bin').write_bytes(b'SYNTHETIC SOURCE')
    destination.mkdir()
    (destination / 'note.bin').write_bytes(b'SYNTHETIC OLD\r\n\x00\xff')
    (destination / '.git').mkdir()
    (destination / '.git/HEAD').write_bytes(b'SYNTHETIC PROTECTED CONTROL')
    return source, destination


def _plan(source: Path, destination: Path, **options):
    return tx._plan_transaction(source, destination, target_rules=_TargetRules(False, 'NFC'), **options)


def _build(stage: Path) -> None:
    (stage / 'note.bin').write_bytes(bytes(range(256)))


def test_space_disappearing_after_plan_has_no_ownership(locations, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stale free-space estimate never authorizes the first transaction write."""
    source, destination = locations
    plan = _plan(source, destination, required_bytes=123)
    monkeypatch.setattr(tx.shutil, 'disk_usage', lambda _: SimpleNamespace(free=123 + const.TRANSACTION_RESERVE_BYTES - 1))
    before = set(source.parent.iterdir())
    with pytest.raises(_OperationalError):
        tx._execute_transaction(plan, _build, lambda _: None, yes=True)
    assert set(source.parent.iterdir()) == before
    assert (destination / 'note.bin').read_bytes() == b'SYNTHETIC OLD\r\n\x00\xff'
    assert not plan.lock.exists()


@pytest.mark.parametrize('number', [errno.ENOSPC, errno.EDQUOT, errno.EIO])
def test_staged_flush_resource_failure_preserves_old_payload(locations, monkeypatch: pytest.MonkeyPatch, number: int) -> None:
    """Disk-full/quota/I/O failures at payload flush cannot publish partial data."""
    source, destination = locations
    plan = _plan(source, destination)
    original = tx._sync_tree

    def failed(root: Path) -> None:
        sync = os.fsync

        def fail_file(descriptor: int) -> None:
            if stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError(number, 'SYNTHETIC RESOURCE FAILURE')
            sync(descriptor)

        with monkeypatch.context() as patch:
            patch.setattr(os, 'fsync', fail_file)
            original(root)

    monkeypatch.setattr(tx, '_sync_tree', failed)
    with pytest.raises(tx._TransactionError) as error:
        tx._execute_transaction(plan, _build, lambda _: None, yes=True)
    assert not error.value.recovery_required
    assert (destination / 'note.bin').read_bytes() == b'SYNTHETIC OLD\r\n\x00\xff'
    assert (destination / '.git/HEAD').read_bytes() == b'SYNTHETIC PROTECTED CONTROL'
    assert (source / 'sentinel.bin').read_bytes() == b'SYNTHETIC SOURCE'
    assert not plan.lock.exists()


def test_native_termination_after_move_retains_recoverable_payload(locations) -> None:
    """Terminate a live writer after a rename and explicitly recover its durable state."""
    source, destination = locations
    worker = """
import sys
from pathlib import Path
from obfuscidian import transactions as tx
from obfuscidian.paths import _TargetRules
source, destination = map(Path, sys.argv[1:])
plan = tx._plan_transaction(source, destination, target_rules=_TargetRules(False, 'NFC'))
original = tx._move
def move(*args):
    original(*args)
    print('SYNTHETIC READY', flush=True)
    sys.stdin.readline()
tx._move = move
def build(stage):
    (stage / 'note.bin').write_bytes(bytes(range(256)))
tx._execute_transaction(plan, build, lambda _: None, yes=True)
"""
    process = subprocess.Popen(
        [sys.executable, '-c', worker, str(source), str(destination)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        readable, _, _ = select.select([process.stdout], [], [], 15)
        assert readable, 'Synthetic writer did not reach the publication boundary.'
        assert process.stdout.readline() == b'SYNTHETIC READY\n'
        process.terminate()
        _, errors = process.communicate(timeout=15)
        assert process.returncode < 0, errors
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=15)
    pending = _plan(source, destination, allow_pending=True)
    assert pending.lock.exists()
    with pytest.raises(_OperationalError, match='pending'):
        _plan(source, destination)
    tx._recover_transaction(pending, yes=True)
    assert (destination / 'note.bin').read_bytes() == b'SYNTHETIC OLD\r\n\x00\xff'
    assert (destination / '.git/HEAD').read_bytes() == b'SYNTHETIC PROTECTED CONTROL'
    assert not pending.lock.exists()

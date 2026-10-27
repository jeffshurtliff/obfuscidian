# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_windows_lifecycle
:Synopsis:          Synthetic private native Windows lifecycle and real child termination tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import errno
import os
import queue
import subprocess
import sys
import threading
from dataclasses import replace
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import _windows_files as files
from obfuscidian import _windows_transactions as win
from obfuscidian import backup, keys, manifest, restore
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian._windows_native import _Guard, _NativeSafetyError
from obfuscidian.cli import cli
from tests._windows_support import _failure_details, _io_path, _terminate_worker

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Actual native Windows lifecycle APIs required.')


@pytest.fixture
def locations(tmp_path):
    """Require eligible unelevated local storage; unavailable setup is a failure."""
    parent = tmp_path.resolve()
    with _Guard(parent):
        pass
    source, destination = parent / 'source', parent / 'destination'
    source.mkdir()
    (source / 'note.md').write_bytes(b'SYNTHETIC SOURCE\r\n')
    files._mkdir(parent, 'destination')
    files._mkdir(destination, 'old')
    files._write(destination / 'old', 'a.bin', b'SYNTHETIC OLD\r\n\x00\xff')
    files._write(destination / 'old', 'b.bin', bytes(range(256)))
    (destination / '.git').mkdir()
    (destination / '.git/HEAD').write_bytes(b'SYNTHETIC CONTROL')
    return source, destination


def _plan(locations, **options):
    return tx._plan_transaction(*locations, target_rules=backup._mirror_rules(locations[1].parent), **options)


def _build(stage):
    files._mkdir(stage, 'new')
    files._write(stage / 'new', 'binary.bin', bytes(range(256)) + b'\r\n')
    files._write(stage, 'top.bin', b'SYNTHETIC NEW')


def _snapshot(root):
    root = _io_path(root)
    return {str(p.relative_to(root)): None if p.is_dir() else p.read_bytes() for p in root.rglob('*')}


def test_private_native_success_preserves_binary_controls_and_plaintext_privacy(locations):
    source, destination = locations
    original = files._capture(destination, protected={'.git'})
    result = win._execute(_plan(locations), _build, lambda _: None, yes=True)
    assert (destination / 'new/binary.bin').read_bytes() == bytes(range(256)) + b'\r\n'
    assert (destination / '.git/HEAD').read_bytes() == b'SYNTHETIC CONTROL'
    assert (source / 'note.md').read_bytes() == b'SYNTHETIC SOURCE\r\n'
    assert not _plan(locations).lock.exists()
    for path in result.rollback.iterdir():
        with files._entry(path.parent, path.name, path.is_dir(), private=True) as handle:
            saved = files._record(handle, private=True)
            assert saved['id'] not in [r['id'] for r in original.values()]
    assert len(list(result.rollback.iterdir())) == 3


def test_private_native_backup_fresh_merge_noop_and_restore_roundtrip(locations):
    source, _destination = locations
    mirror, restored, key = source.parent / 'mirror', source.parent / 'restored', source.parent / 'synthetic.key'
    keys._generate_key(key)
    (source / 'binary.bin').write_bytes(bytes(range(256)) + b'\r\n\x00\xff')
    (source / 'empty').mkdir()
    backup._publish_windows_backup(backup._plan_fresh(source, mirror, key))
    previous = manifest._verify_mirror(mirror, keys._load_key(key)[0])
    before = _snapshot(source.parent)
    assert backup._publish_windows_backup(backup._plan_merge(source, mirror, key)) is None
    assert _snapshot(source.parent) == before
    (source / 'note.md').unlink()
    (source / 'added.md').write_bytes(b'SYNTHETIC ADDITION')
    backup._publish_windows_backup(backup._plan_merge(source, mirror, key))
    merged = manifest._verify_mirror(mirror, keys._load_key(key)[0])
    assert merged.manifest.vault_id == previous.manifest.vault_id
    assert {r.path for r in merged.manifest.files} == {'note.md', 'binary.bin', 'added.md'}
    restore._publish_windows_restore(restore._plan_restore(restored, mirror, key))
    assert (restored / 'binary.bin').read_bytes() == bytes(range(256)) + b'\r\n\x00\xff'
    assert (restored / 'note.md').read_bytes() == b'SYNTHETIC SOURCE\r\n'
    assert (restored / 'empty').is_dir()
    plan = backup._plan_fresh(source, mirror, key)
    assert plan.confirmation
    before = _snapshot(source.parent)
    with pytest.raises(tx._OperationalError, match='confirmation'):
        backup._publish_windows_backup(plan, non_interactive=True)
    assert _snapshot(source.parent) == before
    backup._publish_windows_backup(plan, yes=True)
    assert {r.path for r in manifest._verify_mirror(mirror, keys._load_key(key)[0]).manifest.files} == {'binary.bin', 'added.md'}
    # Replace existing plaintext only with explicit consent; retain original copies.
    try:
        restore._publish_windows_restore(restore._plan_restore(restored, mirror, key), yes=True)
    except tx._TransactionError as error:
        pytest.fail(_failure_details(error), pytrace=False)
    assert not (restored / 'note.md').exists()


@pytest.mark.parametrize('dry_run', [False, True])
def test_confirmation_and_preview_create_no_artifacts(locations, dry_run):
    before = _snapshot(locations[0].parent)
    if dry_run:
        assert win._execute(_plan(locations), _build, lambda _: None, dry_run=True) is None
    else:
        with pytest.raises(tx._OperationalError, match='confirmation'):
            win._execute(_plan(locations), _build, lambda _: None, non_interactive=True)
    assert _snapshot(locations[0].parent) == before


@pytest.mark.parametrize('command', ['backup', 'restore', 'recovery', 'log'])
def test_production_cli_refusal_is_retained(locations, command):
    source, destination = locations
    key, mirror = source.parent / 'synthetic.key', source.parent / 'mirror'
    keys._generate_key(key)
    backup._publish_windows_backup(backup._plan_fresh(source, mirror, key))
    arguments = [
        'shroud',
        'fresh',
        '--origin',
        str(source),
        '--mirror',
        str(source.parent / 'cli-mirror'),
        '--key',
        str(key),
        '--yes',
    ]
    if command in {'restore', 'recovery'}:
        arguments = ['unshroud', 'fresh', '--origin', str(destination), '--mirror', str(mirror), '--key', str(key), '--yes']
    if command == 'recovery':
        arguments += ['--recover']
    if command == 'log':
        log = source.parent / 'synthetic.jsonl'
        log.write_bytes(b'SYNTHETIC EXISTING LOG\n')
        arguments += ['--log-file', str(log)]
    before = _snapshot(source.parent)
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code != 0
    assert _snapshot(source.parent) == before


# Each occurrence selects a real destructive call; readiness precedes a real
# TerminateProcess, not an exception pretending to be process termination.
FORWARD = [
    ('ownership', 1, False),
    ('preparing', 1, True),
    ('rollback-copy', 1, True),
    ('ready', 1, True),
    ('original-delete', 1, True),
    ('original-delete', 2, True),
    ('original-delete', 3, True),
    ('proposal-publish', 1, True),
    ('proposal-publish', 2, True),
    ('published', 1, True),
    ('terminal-release', 1, True),
    ('checkpoint-intent', 1, False),
    ('checkpoint-published', 1, True),
]

WORKER = r"""
import os, sys
from pathlib import Path
from obfuscidian import _windows_transactions as win, _windows_files as files, backup, transactions as tx
source, destination = map(Path, sys.argv[1:3])
boundary, occurrence, recovery = sys.argv[3], int(sys.argv[4]), sys.argv[5] == 'recover'
count = 0
def observe(label):
    global count
    if label == boundary:
        count += 1
        if count == occurrence:
            print('SYNTHETIC READY', os.getpid(), flush=True)
            sys.stdin.readline()
win._boundary = observe
files._publication_boundary = observe
plan = tx._plan_transaction(source, destination, target_rules=backup._mirror_rules(destination.parent), allow_pending=recovery)
def build(stage):
    files._mkdir(stage, 'new')
    files._write(stage / 'new', 'binary.bin', bytes(range(256)) + b'\r\n')
    files._write(stage, 'top.bin', b'SYNTHETIC NEW')
if recovery:
    win._recover(plan, yes=True)
else:
    win._execute(plan, build, lambda _: None, yes=True)
"""


def _terminate(locations, boundary, occurrence=1, recovery=False):
    process = subprocess.Popen(
        [
            sys.executable,
            '-c',
            WORKER,
            *(str(p) for p in locations),
            boundary,
            str(occurrence),
            'recover' if recovery else 'write',
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ready = queue.Queue()
    thread = threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True)
    thread.start()
    try:
        _terminate_worker(process, ready.get(timeout=45), b'SYNTHETIC READY')
        _, errors = process.communicate(timeout=15)
        assert process.returncode != 0, errors
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=15)
        thread.join(timeout=1)


@pytest.mark.parametrize('boundary,occurrence,recoverable', FORWARD)
def test_actual_child_termination_each_forward_boundary(locations, boundary, occurrence, recoverable):
    before = _snapshot(locations[1])
    _terminate(locations, boundary, occurrence)
    plan = _plan(locations, allow_pending=True)
    if recoverable:
        win._recover(plan, yes=True)
        assert _snapshot(locations[1]) == before
        assert not plan.lock.exists()
    else:
        retained = _snapshot(locations[0].parent)
        with pytest.raises(tx._TransactionError):
            win._recover(plan, yes=True)
        assert _snapshot(locations[0].parent) == retained
        assert plan.lock.exists()


@pytest.mark.parametrize('boundary', ['publication-before-metadata', 'publication-after-metadata'])
@pytest.mark.parametrize('phase', ['forward', 'inverse-proposal', 'inverse-reconstruction'])
def test_actual_same_name_publication_death_at_metadata_boundary(locations, boundary, phase, record_property):
    """Kill the real worker around same-name metadata sealing; retain any uncertain state."""
    destination = locations[1]
    files._write(destination, 'top.bin', b'SYNTHETIC PREVIOUS\x00\xff')
    with files._entry(destination, 'top.bin', False, private=True, writable=True) as handle:
        original = files._record(handle, private=True)
        # A clearly older synthetic creation time distinguishes the tunnel cache
        # from the fresh proposal. This changes only a temporary fixture file.
        original['created'] = const.WINDOWS_FILETIME_EPOCH
        files._metadata(handle, original)
    before = _snapshot(destination)
    if phase == 'forward':
        # The builder publishes new/ first, then the same-name top.bin file.
        _terminate(locations, boundary, occurrence=2)
    else:
        _terminate(locations, 'published')
        # Inverse work first returns both proposal tops, then reconstructs old/
        # and top.bin before its nested original files.
        occurrence = 2 if phase == 'inverse-proposal' else 4
        _terminate(locations, boundary, occurrence=occurrence, recovery=True)
    plan = _plan(locations, allow_pending=True)
    with win._Session(plan, recovery=True) as session:
        owner = win._json(session.owner._read(const.TRANSACTION_LOCK_BYTES), const.TRANSACTION_LOCK_BYTES)
        session._controls(plan.workspace_parent / (const.TRANSACTION_PREFIX + owner['binding']['id']))
        # Inspection only: this store read never authorizes inverse work. The
        # production recovery below still requires ownership/cursor/artifact proof.
        journal = win._json(session.store._read().payload, const.TRANSACTION_JOURNAL_BYTES)
        win._schema(journal)
        workspace = session.workspace
    expected = journal['inverse']['top.bin'] if phase == 'inverse-reconstruction' else journal['after']['top.bin']
    observed_root = workspace / 'stage' if phase == 'inverse-proposal' else destination
    # Observe payload with the transaction's root-control exclusions. The
    # fixture's protected .git remains included in the whole-tree snapshots.
    actual = files._capture(observed_root, protected=tx._protected_names(plan.preserve_config))['top.bin']
    drift = actual['created'] != expected['created']
    record_property('actual_creation_time_tunnel_observed', drift)
    assert actual == {**expected, 'created': actual['created']}
    if drift:
        assert boundary == 'publication-before-metadata'
        if phase == 'forward':
            assert actual['created'] == original['created']
        elif phase == 'inverse-reconstruction':
            assert actual['created'] == journal['after']['top.bin']['created']
        retained = _snapshot(locations[0].parent)
        with pytest.raises(tx._TransactionError):
            win._recover(plan, yes=True)
        assert _snapshot(locations[0].parent) == retained
        assert plan.lock.exists()
    else:
        win._recover(plan, yes=True)
        assert _snapshot(destination) == before
        assert not plan.lock.exists()


@pytest.mark.parametrize(
    'boundary,occurrence,recoverable',
    [
        ('inverse-copy', 1, False),
        ('inverse-ready', 1, True),
        ('inverse-proposal', 1, True),
        ('inverse-proposal', 2, True),
        ('inverse-publish', 1, True),
        ('inverse-publish', 2, True),
        ('inverse-publish', 3, True),
        ('inverse-acl', 1, True),
        ('inverse-acl', 2, True),
        ('inverse-acl', 3, True),
        ('terminal-release', 1, True),
    ],
)
def test_actual_recovery_child_termination_again(locations, boundary, occurrence, recoverable):
    before = _snapshot(locations[1])
    _terminate(locations, 'published')
    _terminate(locations, boundary, occurrence, recovery=True)
    plan = _plan(locations, allow_pending=True)
    if recoverable:
        win._recover(plan, yes=True)
        assert _snapshot(locations[1]) == before
    else:
        retained = _snapshot(locations[0].parent)
        with pytest.raises(tx._TransactionError):
            win._recover(plan, yes=True)
        assert _snapshot(locations[0].parent) == retained


@pytest.mark.parametrize('boundary,recoverable', [('root-created-unbound', False), ('root-created', True)])
def test_actual_created_root_termination(locations, boundary, recoverable):
    missing = locations[0].parent / 'new-destination'
    pair = locations[0], missing
    _terminate(pair, boundary)
    plan = _plan(pair, allow_pending=True)
    if recoverable:
        win._recover(plan, yes=True)
        assert not missing.exists()
    else:
        before = _snapshot(locations[0].parent)
        with pytest.raises(tx._TransactionError):
            win._recover(plan, yes=True)
        assert _snapshot(locations[0].parent) == before


@pytest.mark.parametrize('artifact', ['rollback', 'proposal', 'checkpoint', 'latest-truncated', 'unknown', 'dacl'])
def test_native_changed_or_uncertain_artifacts_refuse_before_inverse_writes(locations, artifact):
    _terminate(locations, 'published')
    plan = _plan(locations, allow_pending=True)
    workspace = next(p for p in plan.workspace_parent.glob(const.TRANSACTION_PREFIX + '*') if p.is_dir())
    if artifact == 'rollback':
        next(p for p in _io_path(workspace / 'rollback').iterdir() if p.is_file()).write_bytes(b'SYNTHETIC EDIT')
    elif artifact == 'proposal':
        (locations[1] / 'top.bin').write_bytes(b'SYNTHETIC EDIT')
    elif artifact == 'checkpoint':
        next(_io_path(workspace / 'controls').iterdir()).write_bytes(b'CORRUPT')
    elif artifact == 'latest-truncated':
        sorted(_io_path(workspace / 'controls').iterdir())[-1].unlink()
    elif artifact == 'unknown':
        (workspace / 'foreign.bin').write_bytes(b'SYNTHETIC KEEP')
    else:
        # This changes only a synthetic copy. A protected permissive descriptor
        # must be refused; never repair it or change real host policies.
        from tests.integration.test_windows_native import _set_descriptor

        observed = next(p for p in _io_path(workspace / 'rollback').iterdir() if p.is_file())
        target = workspace / 'rollback' / observed.name
        with _Guard(target.parent) as guard:
            _, sid = guard.api._owner()
            _set_descriptor(guard.api, _io_path(target), f'D:P(A;;FA;;;{sid})(A;;GR;;;WD)')
    before = _snapshot(locations[0].parent)
    with pytest.raises(tx._TransactionError):
        win._recover(plan, yes=True)
    assert _snapshot(locations[0].parent) == before


@pytest.mark.parametrize('number', [errno.ENOSPC, errno.EIO, errno.EACCES])
def test_injected_native_write_failures_preserve_originals(locations, monkeypatch, number):
    before = _snapshot(locations[1])

    def fail(*args, **kwargs):
        raise OSError(number, 'SYNTHETIC I/O FAILURE')

    monkeypatch.setattr(files, '_write', fail)
    with pytest.raises(tx._TransactionError):
        win._execute(_plan(locations), _build, lambda _: None, yes=True)
    assert _snapshot(locations[1]) == before


def test_insufficient_copy_space_refuses_without_ownership(locations, monkeypatch):
    plan = _plan(locations)
    before = _snapshot(locations[0].parent)
    monkeypatch.setattr(win.shutil, 'disk_usage', lambda _: SimpleNamespace(free=plan.required_bytes))
    with pytest.raises(OSError):
        win._execute(plan, _build, lambda _: None, yes=True)
    assert _snapshot(locations[0].parent) == before


def test_native_sharing_refusal_keeps_original_payload(locations):
    plan = _plan(locations)
    before = _snapshot(locations[1])
    with _Guard(locations[1] / 'old') as guard:
        with guard._open_file('a.bin', ownership=True):
            with pytest.raises((_NativeSafetyError, tx._OperationalError)):
                win._execute(plan, _build, lambda _: None, yes=True)
    assert _snapshot(locations[1]) == before
    assert not plan.lock.exists()


@pytest.mark.parametrize('failure', ['wrong-key', 'corrupt-object', 'missing-object'])
def test_authentication_failures_precede_plaintext_writes(locations, failure):
    source, _destination = locations
    mirror, target, key = source.parent / 'mirror', source.parent / 'target', source.parent / 'synthetic.key'
    keys._generate_key(key)
    backup._publish_windows_backup(backup._plan_fresh(source, mirror, key))
    if failure == 'wrong-key':
        key = source.parent / 'wrong-synthetic.key'
        keys._generate_key(key)
    else:
        obj = next((mirror / const.MANAGED_DIRECTORY / const.OBJECTS_DIRECTORY).iterdir())
        if failure == 'corrupt-object':
            obj.write_bytes(b'SYNTHETIC CORRUPTION')
        else:
            obj.unlink()
    before = _snapshot(source.parent)
    with pytest.raises(tx._OperationalError):
        restore._plan_restore(target, mirror, key)
    assert _snapshot(source.parent) == before


def test_wrong_recovery_key_refuses_without_inverse_writes(locations):
    # The generic private lifecycle's mirror flag remains bound to ownership;
    # backup recovery must authenticate the saved/proposed v1 objects as well.
    source, _destination = locations
    mirror, key = source.parent / 'mirror', source.parent / 'synthetic.key'
    keys._generate_key(key)
    plan = backup._plan_fresh(source, mirror, key)
    # A replacement pending snapshot with real native checkpoints is required.
    backup._publish_windows_backup(plan)
    (source / 'note.md').write_bytes(b'SYNTHETIC CHANGED')
    plan = backup._plan_fresh(source, mirror, key)
    original_boundary = win._boundary

    def stop(label):
        if label == 'published':
            raise KeyboardInterrupt()

    original_recovery = win._recover
    try:
        win._boundary = stop
        win._recover = lambda *a, **kw: (_ for _ in ()).throw(OSError('SYNTHETIC RETAIN'))
        with pytest.raises(KeyboardInterrupt):
            backup._publish_windows_backup(plan, yes=True)
    finally:
        win._boundary, win._recover = original_boundary, original_recovery
    pending = tx._plan_transaction(
        source,
        mirror,
        mirror=True,
        fernet=Fernet(Fernet.generate_key()),
        allow_pending=True,
        target_rules=backup._mirror_rules(mirror.parent),
    )
    before = _snapshot(source.parent)
    with pytest.raises(tx._TransactionError):
        win._recover(pending, yes=True)
    assert _snapshot(source.parent) == before
    correct = replace(pending, fernet=keys._load_key(key)[0])
    win._recover(correct, yes=True)


def test_supported_broader_baseline_dacl_is_restored_exactly_after_private_copy_recovery(locations):
    from tests.integration.test_windows_native import _set_descriptor

    path = locations[1] / 'old/a.bin'
    with _Guard(path.parent) as guard:
        _, sid = guard.api._owner()
        _set_descriptor(guard.api, path, f'D:P(A;;FA;;;{sid})(A;;GR;;;WD)')
    with files._entry(path.parent, path.name, False) as handle:
        original = files._record(handle)
    _terminate(locations, 'published')
    win._recover(_plan(locations, allow_pending=True), yes=True)
    with files._entry(path.parent, path.name, False) as handle:
        recovered = files._record(handle)
    assert recovered['id'] != original['id']
    assert files._logical(recovered, original)
    assert recovered['security'] == original['security']


@pytest.mark.parametrize('case', ['inherited-dacl', 'named-stream', 'junction'])
def test_native_unsupported_baselines_and_namespace_refused_without_repair(locations, case):
    destination = locations[1]
    if case == 'inherited-dacl':
        # Ordinary pathname creation intentionally yields an unsupported
        # inherited baseline; transaction code must refuse rather than tighten it.
        (destination / 'ordinary.bin').write_bytes(b'SYNTHETIC KEEP')
    elif case == 'named-stream':
        (destination / 'old/a.bin:synthetic-stream').write_bytes(b'SYNTHETIC STREAM KEEP')
    else:
        outside = destination.parent / 'outside'
        outside.mkdir()
        (outside / 'keep.bin').write_bytes(b'SYNTHETIC OUTSIDE KEEP')
        result = subprocess.run(
            ['cmd', '/c', 'mklink', '/J', str(destination / 'junction'), str(outside)], capture_output=True, timeout=15
        )
        assert result.returncode == 0, 'Mandatory synthetic junction fixture unavailable.'
    before = _snapshot(locations[0].parent)
    with pytest.raises((OSError, tx._OperationalError, tx._ConfigurationError)):
        win._execute(_plan(locations), _build, lambda _: None, yes=True)
    assert _snapshot(locations[0].parent) == before
    if case == 'named-stream':
        assert (destination / 'old/a.bin:synthetic-stream').read_bytes() == b'SYNTHETIC STREAM KEEP'


def test_actual_termination_after_broader_dacl_finalization_is_resumable(locations):
    from tests.integration.test_windows_native import _set_descriptor

    path = locations[1] / 'old/a.bin'
    with _Guard(path.parent) as guard:
        _, sid = guard.api._owner()
        _set_descriptor(guard.api, path, f'D:P(A;;FA;;;{sid})(A;;GR;;;WD)')
    with files._entry(path.parent, path.name, False) as handle:
        original = files._record(handle)
    _terminate(locations, 'published')
    _terminate(locations, 'inverse-acl', recovery=True)
    win._recover(_plan(locations, allow_pending=True), yes=True)
    with files._entry(path.parent, path.name, False) as handle:
        actual = files._record(handle)
    assert files._logical(actual, original) and actual['security'] == original['security']


def test_actual_termination_after_created_root_inverse_removal(locations):
    pair = locations[0], locations[0].parent / 'new-destination'
    _terminate(pair, 'published')
    _terminate(pair, 'inverse-root', recovery=True)
    win._recover(_plan(pair, allow_pending=True), yes=True)
    assert not pair[1].exists()

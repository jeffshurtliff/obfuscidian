# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_transactions
:Synopsis:          Portable injected Windows lifecycle model and strict metadata tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import struct
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from obfuscidian import _windows_files as files
from obfuscidian import _windows_transactions as win
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian._windows_checkpoints import _CheckpointStore
from obfuscidian._windows_native import _Identity
from obfuscidian.paths import _TargetRules
from tests._windows_support import _io_path

# Explicitly synthetic SID; the injected model is not native ACL/identity proof.
SID = b'\x01\x01\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00'


def _security(directory=False):
    ace = struct.pack('<BBHI', 0, 3 if directory else 0, len(SID) + 8, const.WINDOWS_FILE_ALL_ACCESS) + SID
    acl = struct.pack('<BBHHH', 2, 0, len(ace) + 8, 1, 0) + ace
    return {'owner': SID.hex(), 'acl': acl.hex(), 'protected': True}


class _ModelHandle:
    def __init__(self, path, parent=None, ownership=False):
        self.path = Path(path)
        self.parent = parent
        self.ownership = ownership
        self.api = SimpleNamespace(_owner=lambda: (SID, 'SYNTHETIC'))
        self.identity = self._identity()
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._close()

    def _close(self):
        self.closed = True

    def _private(self):
        if _io_path(self.path).is_symlink():
            raise win._fail()

    def _identity(self):
        path = _io_path(self.path)
        info = path.stat()
        return _Identity(
            1,
            info.st_ino.to_bytes(16, 'little'),
            path.is_dir(),
            0x10 if path.is_dir() else 0x20,
            info.st_size,
            1,
            1,
            1,
            info.st_mtime_ns,
            1,
        )

    def _recheck(self, expected, metadata=True):
        actual = self._identity()
        if not actual._same_object(expected):
            raise win._fail()
        return actual

    def _read(self, limit):
        data = _io_path(self.path).read_bytes()
        if len(data) > limit:
            raise win._fail()
        return data

    def _write(self, data, limit):
        if len(data) > limit:
            raise win._fail()
        _io_path(self.path).write_bytes(data)

    def _set_time(self, mtime_ns):
        os.utime(_io_path(self.path), ns=(mtime_ns, mtime_ns))

    def _release_ownership(self, terminal):
        assert _io_path(self.path).read_bytes() == terminal
        _io_path(self.path).unlink()
        self._close()

    def _delete(self, expected):
        self._recheck(expected)
        path = _io_path(self.path)
        path.rmdir() if path.is_dir() else path.unlink()


class _ModelGuard:
    def __init__(self, path):
        self.path = Path(path)
        self.handles = [_ModelHandle(p) for p in reversed([self.path, *self.path.parents])]
        self.api = SimpleNamespace(_owner=lambda: (SID, 'SYNTHETIC'))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _check(self):
        for handle in self.handles:
            handle._recheck(handle.identity, metadata=False)

    def _open_file(self, name, create=False, ownership=False, writable=False):
        if create:
            with _io_path(self.path / name).open('xb'):
                pass
        return _ModelHandle(self.path / name, self, ownership)

    def _create_directory(self, name):
        _io_path(self.path / name).mkdir()
        return _ModelHandle(self.path / name, self)

    def _checkpoint(self, name, data):
        handle = self._open_file(name, create=True)
        handle._write(data, const.TRANSACTION_JOURNAL_BYTES)
        return handle

    def _rename(self, source, name, expected):
        target = self.path / name
        if _io_path(target).exists():
            raise win._fail()
        source._recheck(expected)
        _io_path(source.path).rename(_io_path(target))
        source.path, source.parent = target, self


class _ModelStore(_CheckpointStore):
    def _names(self):
        self._check()
        return sorted(p.name for p in _io_path(self.guard.path).iterdir())


@pytest.fixture
def model(tmp_path, monkeypatch):
    """Inject a deterministic filesystem model; never advertise it as Windows evidence."""

    @contextmanager
    def entry(parent, name, directory, **options):
        path = parent / name
        if _io_path(path).is_symlink() or _io_path(path).is_dir() != directory:
            raise win._fail()
        yield _ModelHandle(path, _ModelGuard(parent))

    def record(handle, **options):
        identity = handle._identity()
        data = None if identity.directory else handle._read(const.MAX_ENCRYPTED_BYTES)
        return {
            'id': files._id(handle),
            'size': 0 if data is None else len(data),
            'digest': None if data is None else hashlib.sha256(data).hexdigest(),
            'created': 1,
            'written': identity.written,
            'attributes': identity.attributes,
            'security': _security(identity.directory),
        }

    def delete(path, expected):
        handle = _ModelHandle(path)
        assert record(handle) == expected
        handle._delete(handle._identity())

    monkeypatch.setattr(win, '_Guard', _ModelGuard)
    monkeypatch.setattr(files, '_Guard', _ModelGuard)
    monkeypatch.setattr(win, '_CheckpointStore', _ModelStore)
    monkeypatch.setattr(files, '_entry', entry)
    monkeypatch.setattr(files, '_record', record)
    monkeypatch.setattr(files, '_security', lambda handle, **kw: _security(_io_path(handle.path).is_dir()))
    monkeypatch.setattr(files, '_names', lambda path: sorted(p.name for p in _io_path(path).iterdir()))
    monkeypatch.setattr(files, '_metadata', lambda handle, record: handle._set_time(record['written']))
    monkeypatch.setattr(files, '_directory_time', lambda handle, record: handle._set_time(record['written']))
    monkeypatch.setattr(files, '_finalize', lambda handle, record: handle._set_time(record['written']))
    monkeypatch.setattr(files, '_delete', delete)
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.mkdir()
    destination.mkdir()
    (source / 'source.bin').write_bytes(b'SYNTHETIC SOURCE')
    (destination / 'old').mkdir()
    (destination / 'old/a.bin').write_bytes(b'SYNTHETIC OLD\x00\xff\r\n')
    (destination / 'old/b.bin').write_bytes(bytes(range(256)))
    (destination / '.git').mkdir()
    (destination / '.git/HEAD').write_bytes(b'SYNTHETIC CONTROL')
    return source, destination


def _plan(model, **options):
    return tx._plan_transaction(*model, target_rules=_TargetRules(False, 'NFC'), **options)


def _build(stage):
    files._mkdir(stage, 'new')
    files._write(stage / 'new', 'binary.bin', bytes(range(256)) + b'\r\n')


def _snapshot(root):
    root = _io_path(root)
    return {str(p.relative_to(root)): None if p.is_dir() else p.read_bytes() for p in root.rglob('*')}


def test_injected_private_success_retains_verified_distinct_copies(model):
    result = win._execute(_plan(model), _build, lambda _: None, yes=True)
    assert (model[1] / 'new/binary.bin').read_bytes() == bytes(range(256)) + b'\r\n'
    assert (model[1] / '.git/HEAD').read_bytes() == b'SYNTHETIC CONTROL'
    assert not _plan(model).lock.exists()
    assert len(list(result.rollback.iterdir())) == 3


@pytest.mark.parametrize('boundary', ['ready', 'original-delete', 'proposal-publish', 'published', 'terminal-release'])
def test_injected_interruption_and_recovery(model, monkeypatch, boundary):
    before = _snapshot(model[1])
    # Model abrupt death by leaving ownership on disk and deliberately disabling
    # ordinary-error recovery. Genuine process termination is in native tests.
    recover = win._recover
    monkeypatch.setattr(win, '_recover', lambda *a, **kw: (_ for _ in ()).throw(win._fail()))

    def stop(label):
        if label == boundary:
            raise OSError('SYNTHETIC INTERRUPT')

    monkeypatch.setattr(win, '_boundary', stop)
    with pytest.raises(tx._TransactionError):
        win._execute(_plan(model), _build, lambda _: None, yes=True)
    monkeypatch.setattr(win, '_boundary', lambda _: None)
    monkeypatch.setattr(win, '_recover', recover)
    win._recover(_plan(model, allow_pending=True), yes=True)
    assert _snapshot(model[1]) == before


@pytest.mark.parametrize('dry_run,yes', [(True, False), (False, False)])
def test_no_write_and_confirmation(model, dry_run, yes):
    before = _snapshot(model[0].parent)
    if dry_run:
        assert win._execute(_plan(model), _build, lambda _: None, dry_run=True) is None
    else:
        with pytest.raises(tx._OperationalError):
            win._execute(_plan(model), _build, lambda _: None, non_interactive=True)
    assert _snapshot(model[0].parent) == before


def test_duplicate_and_nested_metadata_refused():
    for data in [b'{"a":1,"a":2}', b'[' * 33 + b']' * 33, b'[]']:
        with pytest.raises((OSError, ValueError)):
            win._json(data, 4096)


@pytest.mark.parametrize('field,value', [('size', True), ('id', [1, '0' * 32, False]), ('digest', 'bad'), ('created', -1)])
def test_bounded_entry_metadata(field, value):
    record = {
        'id': [1, '1' * 32, False],
        'size': 1,
        'digest': '0' * 64,
        'created': 1,
        'written': 2,
        'attributes': 0x20,
        'security': _security(),
    }
    record[field] = value
    with pytest.raises(OSError):
        win._tree({'test.bin': record})


def test_copy_estimate_includes_saved_and_inverse_copies():
    reserve = const.RESTORE_ENTRY_RESERVE_BYTES
    assert win._storage_bytes({'a': {'size': 12}, 'b': {'size': 0}}, 30) == 30 + 24 + 4 * reserve
    assert tx._windows_copy_reserve({'a': {'size': 12}, 'd': {'children': {'b': {'size': 0}}}}) == 24 + 6 * reserve


def _leave_pending(model, monkeypatch, boundary='published'):
    original = win._recover
    monkeypatch.setattr(win, '_recover', lambda *a, **kw: (_ for _ in ()).throw(win._fail()))

    def stop(label):
        if label == boundary:
            raise OSError('SYNTHETIC MODEL INTERRUPTION')

    monkeypatch.setattr(win, '_boundary', stop)
    with pytest.raises(tx._TransactionError):
        win._execute(_plan(model), _build, lambda _: None, yes=True)
    monkeypatch.setattr(win, '_recover', original)
    monkeypatch.setattr(win, '_boundary', lambda _: None)
    return _plan(model, allow_pending=True)


@pytest.mark.parametrize('artifact', ['copy', 'proposal', 'unknown', 'truncated', 'corrupt', 'owner', 'copy-missing'])
def test_injected_changed_artifacts_preserved_before_inverse(model, monkeypatch, artifact):
    plan = _leave_pending(model, monkeypatch)
    workspace = next(p for p in model[0].parent.glob(const.TRANSACTION_PREFIX + '*') if p.is_dir())
    if artifact == 'copy':
        next(p for p in _io_path(workspace / 'rollback').iterdir() if p.is_file()).write_bytes(b'EDIT')
    elif artifact == 'proposal':
        (model[1] / 'new/binary.bin').write_bytes(b'EDIT')
    elif artifact == 'unknown':
        (workspace / 'keep').write_bytes(b'KEEP')
    elif artifact in {'truncated', 'corrupt'}:
        latest = sorted((workspace / 'controls').iterdir())[-1]
        latest = _io_path(latest)
        latest.unlink() if artifact == 'truncated' else latest.write_bytes(b'CORRUPT')
    elif artifact == 'owner':
        plan.lock.write_bytes(b'CORRUPT')
    else:
        next(p for p in _io_path(workspace / 'rollback').iterdir() if p.is_file()).unlink()
    before = _snapshot(model[0].parent)
    with pytest.raises(tx._TransactionError):
        win._recover(plan, yes=True)
    assert _snapshot(model[0].parent) == before


@pytest.mark.parametrize('boundary', ['inverse-ready', 'inverse-proposal', 'inverse-publish', 'inverse-acl', 'terminal-release'])
def test_injected_inverse_interruption_is_resumable(model, monkeypatch, boundary):
    before = _snapshot(model[1])
    plan = _leave_pending(model, monkeypatch)

    def stop(label):
        if label == boundary:
            raise OSError('SYNTHETIC MODEL INTERRUPTION')

    monkeypatch.setattr(win, '_boundary', stop)
    with pytest.raises(tx._TransactionError):
        win._recover(plan, yes=True)
    monkeypatch.setattr(win, '_boundary', lambda _: None)
    win._recover(_plan(model, allow_pending=True), yes=True)
    assert _snapshot(model[1]) == before


@pytest.mark.parametrize('boundary,recoverable', [('root-created', True), ('root-created-unbound', False)])
def test_injected_created_root_binding(model, monkeypatch, boundary, recoverable):
    pair = model[0], model[0].parent / 'new-destination'
    plan = _leave_pending(pair, monkeypatch, boundary)
    if recoverable:
        win._recover(plan, yes=True)
        assert not pair[1].exists()
    else:
        before = _snapshot(model[0].parent)
        with pytest.raises(tx._TransactionError):
            win._recover(plan, yes=True)
        assert _snapshot(model[0].parent) == before


def test_injected_backend_backup_restore_v1_roundtrip(model):
    from obfuscidian import backup, keys, manifest, restore

    source = model[0]
    mirror, target, key = source.parent / 'mirror', source.parent / 'target', source.parent / 'synthetic.key'
    keys._generate_key(key)
    backup._publish_windows_backup(backup._plan_fresh(source, mirror, key))
    before = _snapshot(source.parent)
    assert backup._publish_windows_backup(backup._plan_merge(source, mirror, key)) is None
    assert _snapshot(source.parent) == before
    (source / 'add.bin').write_bytes(bytes(range(256)))
    backup._publish_windows_backup(backup._plan_merge(source, mirror, key))
    restore._publish_windows_restore(restore._plan_restore(target, mirror, key))
    assert (target / 'add.bin').read_bytes() == bytes(range(256))
    assert manifest._verify_mirror(mirror, keys._load_key(key)[0]).manifest.format_version == 1


def _creation_tunnel(monkeypatch):
    """Inject creation-time changes after model rename; never call this native evidence."""
    record, metadata, rename = files._record, files._metadata, _ModelGuard._rename
    created = {}

    def observe(handle, **options):
        result = record(handle, **options)
        return {**result, 'created': created.get(tuple(result['id']), result['created'])}

    def set_metadata(handle, expected):
        metadata(handle, expected)
        created[tuple(files._id(handle))] = expected['created']

    def move(guard, handle, name, expected):
        rename(guard, handle, name, expected)
        if not expected.directory and name == 'top.bin':
            created[tuple(files._id(handle))] = 22

    monkeypatch.setattr(files, '_record', observe)
    monkeypatch.setattr(files, '_metadata', set_metadata)
    monkeypatch.setattr(_ModelGuard, '_rename', move)


def _same_name_build(stage):
    _build(stage)
    files._write(stage, 'top.bin', b'SYNTHETIC NEW\x00\xff')


def test_injected_creation_tunnel_publication_and_inverse_preserve_exact_records(model, monkeypatch):
    (model[1] / 'top.bin').write_bytes(b'SYNTHETIC OLD\x00\xff')
    _creation_tunnel(monkeypatch)
    result = win._execute(_plan(model), _same_name_build, lambda _: None, yes=True)
    assert (model[1] / 'top.bin').read_bytes() == b'SYNTHETIC NEW\x00\xff'
    # Saved copies are independent and never consumed by normalization/recovery.
    saved = _snapshot(result.rollback)
    # Use a second pending transaction so explicit inverse publication exercises
    # the same injected rename effect without changing the completed journal.
    original_recover = win._recover
    monkeypatch.setattr(win, '_recover', lambda *a, **kw: (_ for _ in ()).throw(win._fail()))

    def stop(label):
        if label == 'published':
            raise OSError('SYNTHETIC STOP')

    monkeypatch.setattr(win, '_boundary', stop)
    with pytest.raises(tx._TransactionError):
        win._execute(_plan(model), lambda stage: files._write(stage, 'top.bin', b'SYNTHETIC NEXT'), lambda _: None, yes=True)
    monkeypatch.setattr(win, '_boundary', lambda _: None)
    monkeypatch.setattr(win, '_recover', original_recover)
    win._recover(_plan(model, allow_pending=True), yes=True)
    assert (model[1] / 'top.bin').read_bytes() == b'SYNTHETIC NEW\x00\xff'
    assert _snapshot(result.rollback) == saved
    assert b'SYNTHETIC OLD\x00\xff' in saved.values()


def test_injected_creation_normalization_failure_preserves_uncertain_state(model, monkeypatch):
    _creation_tunnel(monkeypatch)
    metadata = files._metadata

    def refuse(handle, expected):
        if handle.path == model[1] / 'top.bin':
            raise OSError('SYNTHETIC METADATA FAILURE')
        metadata(handle, expected)

    monkeypatch.setattr(files, '_metadata', refuse)
    with pytest.raises(tx._TransactionError):
        win._execute(_plan(model), _same_name_build, lambda _: None, yes=True)
    retained = _snapshot(model[0].parent)
    with pytest.raises(tx._TransactionError):
        win._recover(_plan(model, allow_pending=True), yes=True)
    assert _snapshot(model[0].parent) == retained


@pytest.mark.parametrize('field', ['id', 'size', 'digest', 'written', 'attributes', 'security'])
def test_injected_post_rename_other_changes_refused_without_metadata_rewrite(model, monkeypatch, field):
    source = model[0] / 'proposal.bin'
    source.write_bytes(b'SYNTHETIC PROPOSAL')
    with files._entry(source.parent, source.name, False) as handle:
        expected = files._record(handle)
    record = files._record
    target = model[1] / 'top.bin'

    def altered(handle, **options):
        result = record(handle, **options)
        if handle.path == target:
            result[field] = None
        return result

    monkeypatch.setattr(files, '_record', altered)
    monkeypatch.setattr(files, '_metadata', lambda *a: pytest.fail('Unexpected metadata rewrite after non-creation drift.'))
    with pytest.raises(OSError, match='beyond creation time'):
        files._move(source, target, expected)
    assert target.read_bytes() == b'SYNTHETIC PROPOSAL'

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows_transactions
:Synopsis:          Private copy-based Windows lifecycle with production CLI gates retained
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path

from obfuscidian import _windows_files as files
from obfuscidian import constants as const
from obfuscidian import transactions as posix
from obfuscidian._windows_checkpoints import _CheckpointStore, _decode
from obfuscidian._windows_native import _fail, _Guard


def _boundary(label: str) -> None:
    """Provide a private deterministic test observation point; never invoke vault code."""


def _bytes(value: dict) -> bytes:
    """Serialize private controls canonically and within existing journal bounds."""
    result = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()
    if len(result) > const.TRANSACTION_JOURNAL_BYTES:
        raise _fail('Windows lifecycle metadata exceeds its bound.')
    return result


def _hash(value: dict) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _json(data: bytes, limit: int) -> dict:
    """Reject duplicate fields and excessive JSON nesting before decoding."""
    if len(data) > limit:
        raise _fail('Windows recovery metadata exceeds its bound.')
    depth, string, escaped = 0, False, False
    for char in data:
        if string:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                string = False
        elif char == 34:
            string = True
        elif char in (91, 123):
            depth += 1
            if depth > const.WINDOWS_TRANSACTION_DEPTH:
                raise _fail('Windows recovery JSON nesting exceeds its bound.')
        elif char in (93, 125):
            depth -= 1

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _fail('Duplicate Windows recovery fields.')
            result[key] = value
        return result

    result = json.loads(data, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise _fail('Invalid Windows recovery metadata.')
    return result


def _hex(value, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def _identity(value) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or type(value[0]) is not int
        or not 0 < value[0] < 2**64
        or not _hex(value[1], 32)
        or value[1] == '0' * 32
        or type(value[2]) is not bool
    ):
        raise _fail('Invalid full Windows lifecycle identity.')


def _tree(tree: dict, *, flat: bool = False) -> None:
    """Validate exact bounded records and namespace without trusting saved paths."""
    if not isinstance(tree, dict) or len(tree) > const.WINDOWS_TRANSACTION_ENTRIES:
        raise _fail('Invalid Windows lifecycle tree bound.')
    ids = set()
    for name, record in tree.items():
        if not isinstance(name, str) or len(name) > const.WINDOWS_PATH_CHARS:
            raise _fail()
        parts = name.split('/')
        if len(parts) > const.WINDOWS_TRANSACTION_DEPTH:
            raise _fail()
        for part in parts:
            files._component(part)
        if not isinstance(record, dict) or set(record) != {
            'id',
            'size',
            'digest',
            'created',
            'written',
            'attributes',
            'security',
        }:
            raise _fail('Unknown Windows recovery entry fields.')
        _identity(record['id'])
        identifier = tuple(record['id'])
        if identifier in ids:
            raise _fail('Duplicate Windows payload identities.')
        ids.add(identifier)
        for field in ('size', 'created', 'written', 'attributes'):
            if type(record[field]) is not int or not 0 <= record[field] < 2**63:
                raise _fail('Invalid Windows recovery entry metadata.')
        if record['size'] > const.MAX_ENCRYPTED_BYTES or record['attributes'] & ~const.WINDOWS_SUPPORTED_ATTRIBUTES:
            raise _fail()
        if record['id'][2]:
            if record['digest'] is not None or record['size'] != 0:
                raise _fail()
        elif not _hex(record['digest'], 64):
            raise _fail()
        security = record['security']
        if not isinstance(security, dict) or set(security) != {'owner', 'acl', 'protected'} or security['protected'] is not True:
            raise _fail('Unsupported saved Windows security.')
        if not isinstance(security['owner'], str) or not isinstance(security['acl'], str):
            raise _fail()
        if len(security['owner']) > 136 or len(security['acl']) > const.WINDOWS_SECURITY_BYTES * 2:
            raise _fail()
        owner = files._sid_bytes(bytes.fromhex(security['owner']))
        files._acl(bytes.fromhex(security['acl']), owner, record['id'][2])
        if not flat and len(parts) > 1:
            parent = '/'.join(parts[:-1])
            if parent not in tree or not tree[parent]['id'][2]:
                raise _fail('Missing Windows recovery parent.')


def _schema(journal: dict) -> None:
    """Validate every field before its values can authorize inverse mutation."""
    required = {
        'schema',
        'binding',
        'before',
        'protected',
        'root',
        'workspace',
        'containers',
        'after',
        'copies',
        'phase',
        'remove',
        'publish',
        'inverse',
        'restore',
        'finalize',
        'root_intent',
        'root_security',
        'protected_native',
    }
    if set(journal) != required or journal['schema'] != const.WINDOWS_TRANSACTION_SCHEMA:
        raise _fail('Unknown Windows recovery schema.')
    if journal['phase'] not in {'preparing', 'ready', 'publishing', 'published', 'inverse-building', 'recovering', 'recovered'}:
        raise _fail('Unknown Windows recovery phase.')
    _identity(journal['workspace'])
    if journal['root'] is not None:
        _identity(journal['root'])
    if journal['root_intent'] not in {'none', 'create', 'remove'}:
        raise _fail()
    if not isinstance(journal['binding'], dict) or not isinstance(journal['protected'], dict):
        raise _fail()
    _tree(journal['before'])
    _tree(journal['copies'], flat=True)
    _tree(journal['inverse'], flat=True)
    if journal['after'] is not None:
        _tree(journal['after'])
    for label in ('remove', 'publish', 'restore', 'finalize'):
        value = journal[label]
        allowed = journal['before'] if label != 'publish' else (journal['after'] or {})
        if (
            not isinstance(value, dict)
            or not set(value) <= set(allowed)
            or any(state not in ('intent', 'done') for state in value.values())
        ):
            raise _fail('Invalid Windows recovery progress.')
        if label == 'publish' and any('/' in name for name in value):
            raise _fail()
    if set(journal['copies']) - set(journal['before']) or set(journal['inverse']) - set(journal['before']):
        raise _fail()
    if not isinstance(journal['containers'], dict) or set(journal['containers']) != {'stage', 'rollback', 'inverse', 'controls'}:
        raise _fail()
    for identity in journal['containers'].values():
        _identity(identity)
    if journal['phase'] != 'preparing':
        if set(journal['copies']) != set(journal['before']) or journal['after'] is None:
            raise _fail('Incomplete Windows ready state.')
        for name, original in journal['before'].items():
            if not files._logical(journal['copies'][name], original):
                raise _fail('Windows copy content is not bound to its original.')
        if journal['phase'] in {'recovering', 'recovered'} and set(journal['inverse']) != set(journal['before']):
            raise _fail('Incomplete Windows inverse binding.')
        for name, inverse in journal['inverse'].items():
            if not files._logical(inverse, journal['before'][name]):
                raise _fail('Windows inverse content is not bound to its original.')
    ids = []
    for tree in (journal['before'], journal['copies'], journal['after'] or {}, journal['inverse']):
        ids.extend(tuple(r['id']) for r in tree.values())
    if len(ids) != len(set(ids)):
        raise _fail('Windows original/copy/proposal/inverse identities must remain distinct.')
    if journal['phase'] == 'preparing' and (
        journal['after'] is not None or any(journal[k] for k in ('remove', 'publish', 'restore', 'finalize'))
    ):
        raise _fail('Windows preparing state cannot authorize destructive progress.')
    if journal['phase'] == 'ready' and any(journal[k] for k in ('remove', 'publish', 'restore', 'finalize')):
        raise _fail('Windows ready state cannot imply publication progress.')
    if journal['phase'] == 'published':
        if journal['remove'] != dict.fromkeys(journal['before'], 'done') or journal['publish'] != dict.fromkeys(
            {n.split('/')[0] for n in journal['after']}, 'done'
        ):
            raise _fail('Incomplete Windows published state.')


def _slot(journal: dict, name: str) -> str:
    """Derive opaque saved names solely from the validated baseline namespace."""
    return f'{sorted(journal["before"]).index(name):08x}'


def _protected_native(plan) -> dict:
    """Bind full native IDs and exact descriptors of controls that stay in place."""
    result = {}
    if not posix._entry_exists(plan.destination):
        return result

    def visit(path: Path, name: str, opaque: bool = False):
        with files._entry(path.parent, path.name, path.is_dir()) as handle:
            result[name] = {'id': files._id(handle), 'security': files._security(handle, baseline=False)}
        if path.is_dir() and not opaque:
            for child in files._names(path):
                visit(path / child, name + '/' + child)
        if len(result) > const.WINDOWS_TRANSACTION_ENTRIES:
            raise _fail('Protected Windows control metadata exceeds its bound.')

    for name in sorted(posix._protected_names(plan.preserve_config)):
        if posix._entry_exists(plan.destination / name):
            visit(plan.destination / name, name, opaque=name == const.GIT_METADATA)
    return result


def _storage_bytes(before: dict, required: int) -> int:
    """Include original private copies, inverse copies and allocation reserves."""
    return required + 2 * sum(r['size'] + const.RESTORE_ENTRY_RESERVE_BYTES for r in before.values())


class _Session:
    """Retain native ownership and parent/control guards for one private lifecycle."""

    def __init__(self, plan: posix._TransactionPlan, *, recovery: bool) -> None:
        self.plan, self.recovery = plan, recovery
        self.stack = ExitStack()
        self.record = None
        self.snapshot = None

    def __enter__(self):
        try:
            self.parent = self.stack.enter_context(_Guard(self.plan.workspace_parent))
            self.destination_parent_guard = self.stack.enter_context(_Guard(self.plan.destination.parent))
            self.source_guard = self.stack.enter_context(_Guard(self.plan.source))
            self.owner = self.stack.enter_context(
                self.parent._open_file(self.plan.lock.name, create=not self.recovery, ownership=True, writable=True)
            )
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        self.stack.__exit__(*args)

    def _owner_write(self, record: dict) -> None:
        if self.record is not None and self.owner._read(const.TRANSACTION_LOCK_BYTES) != _bytes(self.record):
            raise _fail('Windows ownership cursor changed.')
        data = _bytes(record)
        if len(data) > const.TRANSACTION_LOCK_BYTES:
            raise _fail('Windows ownership exceeds its existing bound.')
        self.owner._write(data, const.TRANSACTION_LOCK_BYTES)
        self.record = record

    def _controls(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace_guard = self.stack.enter_context(_Guard(workspace))
        self.controls = self.stack.enter_context(_Guard(workspace / const.WINDOWS_TRANSACTION_CONTROLS))
        self.store = _CheckpointStore(self.controls, self.owner)

    def _checkpoint(self, journal: dict) -> None:
        _schema(journal)
        payload = _bytes(journal)
        current = self.store._read()
        if self.snapshot is not None and current != self.snapshot:
            raise _fail('Windows checkpoint state changed.')
        pending = {'generation': current.generation + 1, 'payload': hashlib.sha256(payload).hexdigest()}
        self._owner_write({**self.record, 'pending': pending})
        _boundary('checkpoint-intent')
        snapshot = self.store._append(payload, previous=current if current.generation else None)
        _boundary('checkpoint-published')
        self._owner_write(
            {**self.record, 'cursor': {'generation': snapshot.generation, 'digest': snapshot.digest.hex()}, 'pending': None}
        )
        self.snapshot = snapshot

    def _load(self) -> dict:
        record = _json(self.owner._read(const.TRANSACTION_LOCK_BYTES), const.TRANSACTION_LOCK_BYTES)
        if set(record) != {'schema', 'binding', 'baseline', 'cursor', 'pending', 'terminal'}:
            raise _fail('Invalid Windows ownership fields.')
        binding = record['binding']
        if (
            record['schema'] != const.WINDOWS_TRANSACTION_SCHEMA
            or not isinstance(binding, dict)
            or set(binding)
            != {
                'id',
                'destination',
                'source',
                'mirror',
                'preserve_config',
                'original_exists',
                'owner',
                'ownership',
                'parent',
                'destination_parent',
                'source_root',
                'ancestors',
            }
            or not _hex(binding.get('id'), 32)
            or binding['destination'] != str(self.plan.destination)
            or binding['source'] != str(self.plan.source)
            or binding['mirror'] is not self.plan.mirror
            or binding['preserve_config'] is not self.plan.preserve_config
            or type(binding['original_exists']) is not bool
            or binding['owner'] != self.parent.api._owner()[0].hex()
            or binding['ownership'] != files._id(self.owner)
            or binding['parent'] != files._id(self.parent.handles[-1])
            or not _hex(record['baseline'], 64)
            or record['terminal'] not in (None, 'published', 'recovered')
        ):
            raise _fail('Windows ownership binding mismatch.')
        for root, field in ((self.plan.destination.parent, 'destination_parent'), (self.plan.source, 'source_root')):
            with _Guard(root) as guard:
                if files._id(guard.handles[-1]) != binding[field]:
                    raise _fail('Windows recovery parent/source identity changed.')
        with _Guard(self.plan.destination.parent) as guard:
            if [files._id(h) for h in guard.handles] != binding['ancestors']:
                raise _fail('Windows recovery ancestor identity changed.')
        self.record = record
        self._controls(self.plan.workspace_parent / (const.TRANSACTION_PREFIX + binding['id']))
        snapshot = self.store._read()
        cursor, pending = record['cursor'], record['pending']
        if (
            not isinstance(cursor, dict)
            or set(cursor) != {'generation', 'digest'}
            or type(cursor['generation']) is not int
            or not 0 <= cursor['generation'] <= const.WINDOWS_CHECKPOINT_COUNT
            or not _hex(cursor['digest'], 64)
            or snapshot.pending is not None
            or not snapshot.generation
        ):
            raise _fail('Incomplete Windows latest checkpoint state.')
        if pending is None:
            if (snapshot.generation, snapshot.digest.hex()) != (cursor['generation'], cursor['digest']):
                raise _fail('Windows latest checkpoint was removed or replaced.')
        elif (
            not isinstance(pending, dict)
            or set(pending) != {'generation', 'payload'}
            or pending['generation'] != cursor['generation'] + 1
            or snapshot.generation != pending['generation']
            or hashlib.sha256(snapshot.payload).hexdigest() != pending['payload']
        ):
            raise _fail('Uncertain Windows checkpoint publication retained.')
        if pending is not None:
            if type(pending['generation']) is not int or not _hex(pending['payload'], 64):
                raise _fail('Invalid Windows checkpoint intent types.')
            name = f'{self.store.prefix}{snapshot.generation:016x}-{snapshot.digest.hex()}.bin'
            with self.controls._open_file(name) as handle:
                framed = handle._read(const.TRANSACTION_JOURNAL_BYTES)
            if (
                _decode(
                    framed,
                    snapshot.generation,
                    self.owner._identity().volume,
                    self.owner._identity().file_id,
                    bytes.fromhex(cursor['digest']),
                )
                != snapshot.payload
            ):
                raise _fail('Windows ownership cursor predecessor changed.')
        journal = _json(snapshot.payload, const.TRANSACTION_JOURNAL_BYTES)
        _schema(journal)
        if (
            journal['binding'] != binding
            or _hash(
                {
                    'before': journal['before'],
                    'protected': journal['protected'],
                    'root': journal['root'] if binding['original_exists'] else None,
                    'root_security': journal['root_security'] if binding['original_exists'] else None,
                    'protected_native': journal['protected_native'],
                }
            )
            != record['baseline']
        ):
            raise _fail('Windows baseline changed independently of ownership.')
        self.snapshot = snapshot
        # Reconcile every artifact before completing a interrupted ownership cursor.
        self._reconcile(journal)
        if pending is not None:
            self._owner_write(
                {**record, 'cursor': {'generation': snapshot.generation, 'digest': snapshot.digest.hex()}, 'pending': None}
            )
        return journal

    def _containers(self, journal: dict) -> None:
        self.parent._check()
        self.destination_parent_guard._check()
        self.source_guard._check()
        if files._id(self.workspace_guard.handles[-1]) != journal['workspace']:
            raise _fail('Windows workspace identity changed.')
        if files._names(self.workspace) != sorted(journal['containers']):
            raise _fail('Unknown Windows workspace artifacts retained.')
        for name, identity in journal['containers'].items():
            with _Guard(self.workspace / name) as guard:
                guard.handles[-1]._private()
                if files._id(guard.handles[-1]) != identity:
                    raise _fail('Windows container identity changed.')
        if not posix._outside_git(self.plan.workspace_parent):
            raise _fail('Windows workspace entered a Git worktree.')

    def _flat(self, journal: dict, label: str, expected: dict, moved: set[str] = frozenset()) -> None:
        root = self.workspace / label
        names = {_slot(journal, n): n for n in expected if n not in moved}
        if set(files._names(root)) != set(names):
            raise _fail('Incomplete or foreign Windows copy/reconstruction artifacts retained.')
        for slot, name in names.items():
            record = expected[name]
            with files._entry(root, slot, record['id'][2], private=True) as handle:
                if files._record(handle, private=True) != record:
                    raise _fail('Windows private copy changed.')

    def _reconcile(self, journal: dict) -> tuple[dict, set[str], set[str]]:
        """Prove complete expected progress, never infer intact state from controls alone."""
        self._containers(journal)
        exists = posix._entry_exists(self.plan.destination)
        if journal['root'] is None:
            if exists:
                raise _fail('Uncertain Windows root creation retained.')
            payload, protected = {}, {}
        elif not exists:
            if journal['root_intent'] != 'remove' or journal['binding']['original_exists']:
                raise _fail('Windows destination unexpectedly missing.')
            payload, protected = {}, {}
        else:
            with _Guard(self.plan.destination) as guard:
                if files._id(guard.handles[-1]) != journal['root']:
                    raise _fail('Windows destination root changed.')
                if files._security(guard.handles[-1], baseline=False) != journal['root_security']:
                    raise _fail('Windows destination root owner/DACL changed.')
            _, protected = posix._observe(self.plan.destination, self.plan.preserve_config)
            payload = files._capture(self.plan.destination, protected=posix._protected_names(self.plan.preserve_config))
        if _protected_native(self.plan) != journal['protected_native']:
            raise _fail('Protected Windows control native security or identities changed.')
        if protected != journal['protected']:
            raise _fail('Protected Windows controls changed.')
        if journal['phase'] == 'preparing':
            if payload != journal['before']:
                raise _fail('Windows original changed before ready.')
            # Incomplete stage/copies are retained; no inverse writes needed.
            return payload, set(), set()
        self._flat(journal, 'rollback', journal['copies'])
        stage = files._capture(self.workspace / 'stage', private=True)
        after = journal['after']
        published = set()
        expected_payload = {}
        expected_stage = dict(after)
        for top in sorted({n.split('/')[0] for n in after}):
            group = {n: r for n, r in after.items() if n == top or n.startswith(top + '/')}
            at_target = all(payload.get(n) == r for n, r in group.items())
            at_stage = all(stage.get(n) == r for n, r in group.items())
            if at_target == at_stage or (at_target and top not in journal['publish']):
                raise _fail('Windows proposal missing, duplicated or unauthorized.')
            if journal['publish'].get(top) == 'done' and not at_target and journal['phase'] not in {'recovering', 'recovered'}:
                raise _fail('Windows completed publication was reversed unexpectedly.')
            if at_target:
                published.add(top)
                expected_payload.update(group)
                for n in group:
                    del expected_stage[n]
        restored = set()
        for name, original in journal['before'].items():
            actual = payload.get(name)
            surviving = dict(original)
            if journal['phase'] != 'recovered' and original['id'][2] and any(n.startswith(name + '/') for n in journal['remove']):
                if actual is not None:
                    surviving['written'] = actual['written']
            if actual == surviving:
                if journal['remove'].get(name) == 'done':
                    raise _fail('Removed Windows original unexpectedly reappeared.')
                expected_payload[name] = actual
            elif name in journal['restore']:
                inverse = journal['inverse'].get(name)
                if inverse is None:
                    raise _fail()
                # Directory mtimes change while children are installed. Their
                # exact logical metadata is required again at finalization.
                if actual is not None and actual['id'] == inverse['id']:
                    candidate = dict(inverse)
                    if original['id'][2] and journal['finalize'].get(name) != 'done':
                        candidate['written'] = actual['written']
                    if name in journal['finalize']:
                        candidate['written'] = (
                            original['written'] if actual['written'] == original['written'] else candidate['written']
                        )
                        candidate['security'] = (
                            original['security'] if actual['security'] == original['security'] else inverse['security']
                        )
                    if actual != candidate or (
                        journal['finalize'].get(name) == 'done' and actual['security'] != original['security']
                    ):
                        raise _fail('Windows reconstructed payload changed.')
                    restored.add(name)
                    expected_payload[name] = actual
                elif journal['restore'][name] == 'done':
                    raise _fail('Windows completed reconstruction missing.')
            elif actual is None or name in expected_payload:
                if name not in journal['remove']:
                    raise _fail('Windows original missing without removal intent.')
            else:
                raise _fail('Windows surviving original changed.')
        if payload != expected_payload or stage != expected_stage:
            raise _fail('Unexpected Windows namespace or partial progress retained.')
        if journal['phase'] in {'recovering', 'recovered'}:
            self._flat(journal, 'inverse', journal['inverse'], restored)
        elif files._names(self.workspace / 'inverse'):
            raise _fail('Incomplete Windows inverse staging retained.')
        return payload, published, restored

    def _release(self, journal: dict) -> None:
        self._reconcile(journal)
        self._owner_write({**self.record, 'terminal': journal['phase']})
        _boundary('terminal-release')
        self.owner._release_ownership(_bytes(self.record))

    def _recover(self, journal: dict):
        """Reconcile all locations first, then perform resumable conservative inverse work."""
        _, published, restored = self._reconcile(journal)
        if self.plan.mirror:
            if journal['phase'] == 'preparing':
                if const.MANAGED_DIRECTORY in journal['before']:
                    posix._verify_mirror(self.plan.destination, self.plan.fernet)
            else:
                _authenticate_saved(self, journal)
                proposed = self.plan.destination if const.MANAGED_DIRECTORY in published else self.workspace / 'stage'
                posix._verify_mirror(proposed, self.plan.fernet)
        if journal['phase'] == 'preparing':
            # Preparing artifacts may be incomplete; retain state as preparing
            # for the terminal checkpoint, with no inverse mutation authorized.
            journal['phase'] = 'preparing'
            self._checkpoint(journal)
            self._owner_write({**self.record, 'terminal': 'recovered'})
            self.owner._release_ownership(_bytes(self.record))
            return posix._TransactionResult(self.workspace, self.workspace / 'rollback', not self.plan.mirror)
        inverse_bytes = sum(r['size'] + const.RESTORE_ENTRY_RESERVE_BYTES for r in journal['before'].values())
        if shutil.disk_usage(self.plan.workspace_parent).free < inverse_bytes + const.TRANSACTION_RESERVE_BYTES:
            raise _fail('Insufficient space for Windows inverse reconstruction.')
        if journal['phase'] not in {'recovering', 'recovered'}:
            journal['phase'] = 'inverse-building'
            self._checkpoint(journal)
            for name, saved in journal['copies'].items():
                slot = _slot(journal, name)
                journal['inverse'][name] = files._copy(
                    self.workspace / 'rollback' / slot, self.workspace / 'inverse' / slot, saved
                )
                _boundary('inverse-copy')
            journal['phase'] = 'recovering'
            self._checkpoint(journal)
            _boundary('inverse-ready')
        for top in sorted(published):
            self._reconcile(journal)
            record = journal['after'][top]
            journal['publish'][top] = 'intent'
            self._checkpoint(journal)
            files._move(self.plan.destination / top, self.workspace / 'stage' / top, record)
            _boundary('inverse-proposal')
            self._checkpoint(journal)
        _, _, restored = self._reconcile(journal)
        if journal['root'] is None and journal['before']:
            raise _fail('Missing Windows original root cannot be repaired.')
        for name in sorted(journal['before'], key=lambda n: (n.count('/'), n)):
            if name in restored:
                continue
            target = self.plan.destination / name
            if posix._entry_exists(target):
                continue
            self._reconcile(journal)
            journal['restore'][name] = 'intent'
            self._checkpoint(journal)
            record = journal['inverse'][name]
            files._move(self.workspace / 'inverse' / _slot(journal, name), target, record)
            _boundary('inverse-publish')
            journal['restore'][name] = 'done'
            self._checkpoint(journal)
        # Restore all directories' original mtimes after child operations,
        # including surviving directories whose children were removed.
        payload, _, restored = self._reconcile(journal)
        for name in sorted(journal['before'], key=lambda n: (-n.count('/'), n)):
            if name not in restored:
                continue
            original = journal['before'][name]
            self._reconcile(journal)
            journal['finalize'][name] = 'intent'
            self._checkpoint(journal)
            with files._entry((self.plan.destination / name).parent, Path(name).name, original['id'][2], writable=True) as handle:
                if files._security(handle) != original['security']:
                    files._finalize(handle, original)
                elif files._logical(files._record(handle), original) is False:
                    files._metadata(handle, original)
            _boundary('inverse-acl')
            journal['finalize'][name] = 'done'
            self._checkpoint(journal)
        # Surviving original directories need supported times restored without
        # changing their DACL. They remain bound to their original identity.
        for name, original in journal['before'].items():
            if original['id'][2] and name not in restored:
                with files._entry((self.plan.destination / name).parent, Path(name).name, True, writable=True) as handle:
                    if files._id(handle) != original['id']:
                        raise _fail()
                    files._directory_time(handle, original)
        if not journal['binding']['original_exists'] and posix._entry_exists(self.plan.destination):
            if files._names(self.plan.destination):
                raise _fail('Created Windows root is not empty.')
            journal['root_intent'] = 'remove'
            self._checkpoint(journal)
            with files._entry(
                self.plan.destination.parent, self.plan.destination.name, True, private=True, writable=True, removable=True
            ) as handle:
                if files._id(handle) != journal['root']:
                    raise _fail()
                handle._delete(handle._identity())
            _boundary('inverse-root')
            journal['root'] = None
        journal['phase'] = 'recovered'
        self._reconcile(journal)
        self._checkpoint(journal)
        self._release(journal)
        return posix._TransactionResult(self.workspace, self.workspace / 'rollback', not self.plan.mirror)


def _authenticate_saved(session: _Session, journal: dict) -> None:
    """Authenticate the old encrypted manifest and every old object from private copies."""
    from obfuscidian import manifest

    if const.MANAGED_DIRECTORY not in journal['before']:
        return

    def read(name):
        with files._entry(session.workspace / 'rollback', _slot(journal, name), False, private=True) as handle:
            return handle._read(const.MAX_ENCRYPTED_BYTES)

    metadata = manifest._decrypt_manifest(read(const.MANAGED_DIRECTORY + '/' + const.MANIFEST_FILENAME), session.plan.fernet)
    expected = {
        const.MANAGED_DIRECTORY,
        f'{const.MANAGED_DIRECTORY}/{const.OBJECTS_DIRECTORY}',
        f'{const.MANAGED_DIRECTORY}/{const.MANIFEST_FILENAME}',
    }
    expected.update(f'{const.MANAGED_DIRECTORY}/{const.OBJECTS_DIRECTORY}/{r.object_id}.obf' for r in metadata.files)
    if set(journal['before']) != expected:
        raise _fail('Saved Windows mirror namespace differs from its authenticated v1 manifest.')
    for record in metadata.files:
        name = f'{const.MANAGED_DIRECTORY}/{const.OBJECTS_DIRECTORY}/{record.object_id}.obf'
        token = read(name)
        # Reuse the format's complete content-binding validator.
        manifest._decode_file(record, token, session.plan.fernet)


def _execute(
    plan: posix._TransactionPlan,
    build: Callable[[Path], None],
    verify: Callable[[Path], None],
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
    dry_run: bool = False,
    prepublish: Callable[[], None] | None = None,
) -> posix._TransactionResult | None:
    """Execute only private backend calls; the production POSIX/CLI gate is untouched."""
    posix._recheck_path(plan.parent_state)
    posix._recheck_path(plan.source_state)
    posix._check_destination(plan, plan.before)
    if any(posix._entry_exists(parent / plan.lock.name) for parent in plan.destination.parents):
        raise _fail('Pending Windows ownership requires explicit recovery.')
    if dry_run:
        return None
    posix._confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    before = (
        files._capture(plan.destination, protected=posix._protected_names(plan.preserve_config))
        if plan.destination_state.exists
        else {}
    )
    required = _storage_bytes(before, plan.required_bytes - plan.windows_copy_bytes)
    if shutil.disk_usage(plan.workspace_parent).free < required + const.TRANSACTION_RESERVE_BYTES:
        raise _fail('Insufficient space for Windows copies and inverse reconstruction.')
    try:
        with _Session(plan, recovery=False) as session:
            root = None
            root_security = None
            protected_native = _protected_native(plan)
            with _Guard(plan.destination.parent) as guard:
                destination_parent = files._id(guard.handles[-1])
                ancestors = [files._id(h) for h in guard.handles]
            with _Guard(plan.source) as guard:
                source_root = files._id(guard.handles[-1])
            if plan.destination_state.exists:
                with _Guard(plan.destination) as guard:
                    root = files._id(guard.handles[-1])
                    root_security = files._security(guard.handles[-1], baseline=False)
            required = _storage_bytes(before, plan.required_bytes - plan.windows_copy_bytes)
            if shutil.disk_usage(plan.workspace_parent).free < required + const.TRANSACTION_RESERVE_BYTES:
                raise _fail('Insufficient space for Windows copies and inverse reconstruction.')
            binding = {
                'id': secrets.token_hex(16),
                'destination': str(plan.destination),
                'source': str(plan.source),
                'mirror': plan.mirror,
                'preserve_config': plan.preserve_config,
                'original_exists': root is not None,
                'owner': session.parent.api._owner()[0].hex(),
                'ownership': files._id(session.owner),
                'parent': files._id(session.parent.handles[-1]),
                'destination_parent': destination_parent,
                'source_root': source_root,
                'ancestors': ancestors,
            }
            record = {
                'schema': const.WINDOWS_TRANSACTION_SCHEMA,
                'binding': binding,
                'baseline': _hash(
                    {
                        'before': before,
                        'protected': plan.protected,
                        'root': root,
                        'root_security': root_security,
                        'protected_native': protected_native,
                    }
                ),
                'cursor': {'generation': 0, 'digest': '0' * 64},
                'pending': None,
                'terminal': None,
            }
            session._owner_write(record)
            _boundary('ownership')
            workspace = plan.workspace_parent / (const.TRANSACTION_PREFIX + binding['id'])
            workspace_id = files._mkdir(plan.workspace_parent, workspace.name)
            containers = {name: files._mkdir(workspace, name) for name in ('stage', 'rollback', 'inverse', 'controls')}
            session._controls(workspace)
            journal = {
                'schema': const.WINDOWS_TRANSACTION_SCHEMA,
                'binding': binding,
                'before': before,
                'protected': plan.protected,
                'root': root,
                'workspace': workspace_id,
                'containers': containers,
                'phase': 'preparing',
                'after': None,
                'copies': {},
                'remove': {},
                'publish': {},
                'inverse': {},
                'restore': {},
                'finalize': {},
                'root_intent': 'none',
                'root_security': root_security,
                'protected_native': protected_native,
            }
            session._checkpoint(journal)
            _boundary('preparing')
            build(workspace / 'stage')
            verify(workspace / 'stage')
            if plan.mirror:
                posix._verify_mirror(workspace / 'stage', plan.fernet)
            after = files._capture(workspace / 'stage', private=True)
            if any(n.split('/')[0] in posix._protected_names(plan.preserve_config) for n in after):
                raise _fail('Proposal includes protected Windows controls.')
            posix._validate_target_paths(
                tuple(after) + tuple(posix._tree_names(plan.protected)), plan.target_rules, destination=plan.destination
            )
            for name, original in before.items():
                journal['copies'][name] = files._copy(
                    plan.destination / name, workspace / 'rollback' / _slot(journal, name), original
                )
                _boundary('rollback-copy')
            journal.update(after=after, phase='ready')
            # Reserve the entire worst-case checkpoint history before any
            # original removal. No disk reservation/power-loss guarantee implied.
            count = 12 + 8 * (len(before) + len(after))
            if (
                count > const.WINDOWS_CHECKPOINT_COUNT
                or count * (2 * len(_bytes(journal)) + 8192) > const.WINDOWS_CHECKPOINT_TOTAL_BYTES
            ):
                raise _fail('Windows lifecycle checkpoint budget exceeds its bound.')
            if shutil.disk_usage(plan.workspace_parent).free < required + const.TRANSACTION_RESERVE_BYTES:
                raise _fail('Windows copy-inclusive space changed before publication.')
            session._checkpoint(journal)
            session._reconcile(journal)
            _boundary('ready')
            posix._check_destination(plan, plan.before)
            if prepublish is not None:
                prepublish()
            if root is None:
                journal['root_intent'] = 'create'
                session._checkpoint(journal)
                root = files._mkdir(plan.destination.parent, plan.destination.name)
                _boundary('root-created-unbound')
                journal['root'] = root
                with _Guard(plan.destination) as guard:
                    journal['root_security'] = files._security(guard.handles[-1], baseline=False)
                session._checkpoint(journal)
                _boundary('root-created')
            journal['phase'] = 'publishing'
            session._checkpoint(journal)
            for name in sorted(before, key=lambda n: (-n.count('/'), n)):
                payload, _, _ = session._reconcile(journal)
                journal['remove'][name] = 'intent'
                session._checkpoint(journal)
                files._delete(plan.destination / name, payload[name])
                _boundary('original-delete')
                journal['remove'][name] = 'done'
                session._checkpoint(journal)
            for top in sorted({n.split('/')[0] for n in after}):
                session._reconcile(journal)
                journal['publish'][top] = 'intent'
                session._checkpoint(journal)
                files._move(workspace / 'stage' / top, plan.destination / top, after[top])
                _boundary('proposal-publish')
                journal['publish'][top] = 'done'
                session._checkpoint(journal)
            session._reconcile(journal)
            if plan.mirror:
                posix._verify_mirror(plan.destination, plan.fernet)
            journal['phase'] = 'published'
            session._checkpoint(journal)
            _boundary('published')
            session._release(journal)
            return posix._TransactionResult(workspace, workspace / 'rollback', not plan.mirror)
    except BaseException as error:
        # Ordinary errors use the exact explicit protocol; malformed/partial
        # control writes and edited artifacts stay retained. No broad cleanup.
        recovered = False
        if posix._entry_exists(plan.lock):
            try:
                _recover(plan, yes=True)
                recovered = True
            except (OSError, ValueError, TypeError, KeyError, posix._OperationalError, posix._ConfigurationError):
                pass
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        raise posix._TransactionError(recovery_required=not recovered) from None


def _recover(
    plan: posix._TransactionPlan,
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
) -> posix._TransactionResult:
    """Privately restore the previous logical tree, keeping immutable rollback data."""
    posix._confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    try:
        with _Session(plan, recovery=True) as session:
            return session._recover(session._load())
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        MemoryError,
        posix._ConfigurationError,
        posix._OperationalError,
    ):
        raise posix._TransactionError(recovery_required=True) from None

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows_checkpoints
:Synopsis:          Internal bounded immutable Windows checkpoint publication
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import re
import struct
from dataclasses import dataclass

from obfuscidian import constants as const
from obfuscidian._windows_native import _api_path, _component, _fail, _Guard, _Handle

_HEADER = struct.Struct(const.WINDOWS_CHECKPOINT_HEADER)


def _encode(payload: bytes, generation: int, volume: int, owner_id: bytes, previous: bytes) -> bytes:
    """Frame one bounded snapshot with its ownership identity and predecessor hash."""
    if (
        not isinstance(payload, bytes)
        or len(payload) > const.TRANSACTION_JOURNAL_BYTES - _HEADER.size
        or type(generation) is not int
        or not 1 <= generation <= const.WINDOWS_CHECKPOINT_COUNT
        or type(volume) is not int
        or not 0 < volume < 2**64
        or not isinstance(owner_id, bytes)
        or len(owner_id) != 16
        or not any(owner_id)
        or not isinstance(previous, bytes)
        or len(previous) != 32
        or (generation == 1 and any(previous))
        or (generation > 1 and not any(previous))
    ):
        raise _fail('Invalid bounded Windows checkpoint framing.')
    return _HEADER.pack(const.WINDOWS_CHECKPOINT_MAGIC, generation, volume, owner_id, previous, len(payload)) + payload


def _decode(record: bytes, generation: int, volume: int, owner_id: bytes, previous: bytes) -> bytes:
    """Require an exact bounded frame before returning a checkpoint payload.

    The digest is integrity/sequence binding for private controls, not encryption
    or authentication against the owner. Payload schema validation belongs to
    the future lifecycle backend; this primitive never parses recovery JSON.
    """
    if not isinstance(record, bytes) or not _HEADER.size <= len(record) <= const.TRANSACTION_JOURNAL_BYTES:
        raise _fail('Invalid Windows checkpoint record size.')
    magic, number, actual_volume, actual_owner, predecessor, size = _HEADER.unpack_from(record)
    if (
        magic != const.WINDOWS_CHECKPOINT_MAGIC
        or number != generation
        or actual_volume != volume
        or actual_owner != owner_id
        or predecessor != previous
        or size != len(record) - _HEADER.size
    ):
        raise _fail('Windows checkpoint sequence or ownership changed.')
    payload = record[_HEADER.size :]
    if _encode(payload, generation, volume, owner_id, previous) != record:
        raise _fail('Noncanonical Windows checkpoint frame.')
    return payload


@dataclass(frozen=True)
class _Snapshot:
    """Return a validated immutable generation and separately identified pending data."""

    generation: int
    digest: bytes
    payload: bytes
    total_bytes: int
    pending: str | None


class _CheckpointStore:
    """Publish logical replacements without overwriting any previous checkpoint.

    A live exclusive ownership handle and private guarded workspace are required
    for writes and reads. Every committed generation is verified from the first,
    with bounded count/aggregate bytes and a full ownership ID binding. Pending
    candidates are never authoritative and never automatically deleted. A pending
    entry may be partial after process death; its private identity/type/size are
    still required. The caller must reconcile it before another checkpoint.

    This class implements controls only; it does not integrate transactions or
    authorize CLI writes, cleanup, inverse restoration or JSON schema changes.
    """

    def __init__(self, guard: _Guard, ownership: _Handle, name: str = 'journal') -> None:
        _component(name)
        self.guard = guard
        self.ownership = ownership
        self.owner_identity = ownership._identity()
        self.namespace = hashlib.sha256(name.encode('utf-8')).hexdigest()
        self.prefix = f'{const.WINDOWS_CHECKPOINT_PREFIX}{self.namespace}-{self.owner_identity.file_id.hex()}-'
        self._check()

    def _check(self) -> None:
        """Require the same exclusively held owner and private workspace each time."""
        self.guard._check()
        self.guard.handles[-1]._private()
        if not self.ownership.ownership or self.ownership.parent is None:
            raise _fail('Windows checkpoints require held exclusive ownership.')
        self.ownership.parent._check()
        self.ownership._recheck(self.owner_identity, metadata=False)
        self.ownership._private()
        if self.owner_identity.volume != self.guard.handles[-1].identity.volume:
            raise _fail('Windows checkpoints require the ownership volume.')

    def _names(self) -> list[str]:
        """Enumerate only bounded controls beneath the retained private guard.

        Enumeration is observational. Every selected entry is then opened and
        checked by the native guarded helper, rather than trusted DirEntry data.
        Unknown control namespaces and aliases are refused, never cleaned up.
        """
        self._check()
        names = []
        try:
            # Use the same validated native spelling for enumeration, without
            # depending on machine-wide long-path policy.
            with os.scandir(_api_path(self.guard.path)) as entries:
                for entry in entries:
                    # The dedicated private control directory contains only
                    # this store's generations; unknown children are retained.
                    if not entry.name.startswith(self.prefix):
                        raise _fail('Foreign or aliased Windows checkpoint namespace refused.')
                    names.append(entry.name)
                    if len(names) > const.WINDOWS_CHECKPOINT_COUNT + 1:
                        raise _fail('Windows checkpoint count exceeds its bound.')
        except OSError:
            raise _fail('Cannot inspect the Windows checkpoint namespace.') from None
        self._check()
        return sorted(names)

    def _read(self) -> _Snapshot:
        """Verify all immutable generations and identify one nonauthoritative candidate."""
        names = self._names()
        committed = {}
        pending = None
        pattern = re.compile(re.escape(self.prefix) + r'([0-9a-f]{16})-([0-9a-f]{64})\.bin')
        pending_pattern = re.compile(re.escape(self.prefix) + r'([0-9a-f]{16})\.pending')
        for name in names:
            match = pattern.fullmatch(name)
            if match:
                generation = int(match[1], 16)
                if not 1 <= generation <= const.WINDOWS_CHECKPOINT_COUNT or generation in committed:
                    raise _fail('Duplicate or out-of-range Windows checkpoint generation.')
                committed[generation] = (name, bytes.fromhex(match[2]))
            else:
                match = pending_pattern.fullmatch(name)
                if match is None or pending is not None:
                    raise _fail('Unknown or ambiguous Windows checkpoint candidate.')
                pending = (int(match[1], 16), name)
        if sorted(committed) != list(range(1, len(committed) + 1)):
            raise _fail('Missing Windows checkpoint generation.')
        previous, payload, total = bytes(32), b'', 0
        for generation in range(1, len(committed) + 1):
            name, digest = committed[generation]
            with self.guard._open_file(name) as handle:
                size = handle._identity().size
                if size > const.TRANSACTION_JOURNAL_BYTES or total + size > const.WINDOWS_CHECKPOINT_TOTAL_BYTES:
                    raise _fail('Windows checkpoint storage exceeds its bound.')
                record = handle._read(const.TRANSACTION_JOURNAL_BYTES)
                if hashlib.sha256(record).digest() != digest:
                    raise _fail('Windows checkpoint content changed.')
                payload = _decode(record, generation, self.owner_identity.volume, self.owner_identity.file_id, previous)
                total += size
                previous = digest
        if pending is not None:
            if pending[0] != len(committed) + 1 or pending[0] > const.WINDOWS_CHECKPOINT_COUNT:
                raise _fail('Windows checkpoint candidate has an unexpected generation.')
            with self.guard._open_file(pending[1]) as handle:
                size = handle._identity().size
                if size > const.TRANSACTION_JOURNAL_BYTES or total + size > const.WINDOWS_CHECKPOINT_TOTAL_BYTES:
                    raise _fail('Windows checkpoint candidate exceeds its bound.')
                total += size
        if self._names() != names:
            raise _fail('Windows checkpoint namespace changed during inspection.')
        return _Snapshot(len(committed), previous, payload, total, pending[1] if pending is not None else None)

    def _append(self, payload: bytes, *, previous: _Snapshot | None = None) -> _Snapshot:
        """Flush and publish one logical replacement, retaining all old generations.

        A post-publication failure remains an error even when the new generation
        is observable. Recovery rereads the complete chain; no caller may infer
        completion solely from the return path or retry over a pending candidate.
        """
        current = self._read()
        if current.pending is not None:
            raise _fail('Pending Windows checkpoint candidate requires explicit reconciliation.')
        if previous is not None and previous != current:
            raise _fail('Windows checkpoint advanced or changed since observation.')
        if current.generation and previous is None:
            raise _fail('Windows checkpoint replacement requires the observed previous generation.')
        generation = current.generation + 1
        record = _encode(payload, generation, self.owner_identity.volume, self.owner_identity.file_id, current.digest)
        if current.total_bytes + len(record) > const.WINDOWS_CHECKPOINT_TOTAL_BYTES:
            raise _fail('Windows checkpoint storage budget exhausted before publication.')
        digest = hashlib.sha256(record).digest()
        pending = f'{self.prefix}{generation:016x}{const.WINDOWS_CHECKPOINT_PENDING}'
        target = f'{self.prefix}{generation:016x}-{digest.hex()}.bin'
        with self.guard._checkpoint(pending, record) as candidate:
            self._check()
            self.guard._rename(candidate, target, candidate._identity())
        result = self._read()
        if result.generation != generation or result.digest != digest or result.payload != payload or result.pending is not None:
            raise _fail('Windows checkpoint publication verification failed.')
        return result

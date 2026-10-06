# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.backup
:Synopsis:          Internal read-only fresh/merge planning and encrypted publication
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import crypto, inventory, keys, manifest, paths, transactions
from obfuscidian.errors import _ConfigurationError, _OperationalError


@dataclass(frozen=True, repr=False)
class _BackupPlan:
    """Keep a private, bounded logical proposal without staged bytes or randomness."""

    locations: paths._VaultPaths
    source: inventory._Inventory
    previous: manifest._VerifiedMirror | None
    proposal: manifest._Manifest
    transaction: transactions._TransactionPlan
    fernet: Fernet = field(repr=False)
    warnings: tuple[str, ...]
    no_op: bool
    confirmation: bool
    merge: bool
    changes: _Changes


@dataclass(frozen=True)
class _Changes:
    """Classify current files and retained absent/excluded files without exposing names."""

    new: int = 0
    changed: int = 0
    metadata_only: int = 0
    unchanged: int = 0
    retained: int = 0


def _mirror_rules(parent: Path) -> paths._TargetRules:
    """Restrict managed ASCII names and coordinate even case/Unicode path aliases.

    Backup writes only fixed lowercase ASCII names and opaque lowercase hex IDs,
    so their comparisons agree on case-sensitive and insensitive filesystems.
    Conservative lock comparison also serializes case/Unicode aliases of the
    destination without a writable probe. Source names live only in encrypted
    metadata; this does not impose restore naming rules on original paths.
    POSIX length limits are read from the actual destination filesystem.
    """
    if os.name == 'nt':
        return paths._TargetRules(case_sensitive=False, normalization='NFC', windows=True, component_limit=255)
    try:
        name_max = os.pathconf(parent, 'PC_NAME_MAX')
        path_max = os.pathconf(parent, 'PC_PATH_MAX')
        return paths._TargetRules(
            case_sensitive=False,
            normalization='NFC',
            component_limit=name_max if name_max > 0 else None,
            path_limit=path_max if path_max > 0 else None,
        )
    except (OSError, ValueError):
        raise _OperationalError('Cannot establish destination naming limits read-only.') from None


def _plan_fresh(origin: Path, mirror: Path, key: Path, *, exclusions: tuple[str, ...] = ()) -> _BackupPlan:
    """Plan the current included inventory, dropping absent/excluded historic paths."""
    return _plan_backup(origin, mirror, key, exclusions=exclusions, merge=False)


def _plan_merge(origin: Path, mirror: Path, key: Path, *, exclusions: tuple[str, ...] = ()) -> _BackupPlan:
    """Plan the additive union, retaining absent/excluded historic files and directories."""
    return _plan_backup(origin, mirror, key, exclusions=exclusions, merge=True)


def _plan_backup(origin: Path, mirror: Path, key: Path, *, exclusions: tuple[str, ...], merge: bool) -> _BackupPlan:
    """Authenticate, hash one source file at a time, and plan without writes.

    Placeholder IDs/hashes/timestamps have the same serialized widths as the
    eventual values. No-op planning never generates IDs, timestamps or tokens.
    Existing object IDs, content bindings and lineage come only from complete
    authenticated mirror validation. Merge retains old absent/excluded records;
    fresh drops them. Neither infers renames from matching content.

    :param origin: Existing read-only source.
    :param mirror: Existing mirror or missing final component.
    :param key: Selected existing external key.
    :param exclusions: Portable original-relative component globs.
    :param merge: Retain absent/excluded historic paths instead of dropping them.
    :returns: Private proposal, exact ciphertext estimate and consent requirement.
    :raises _ConfigurationError: Unsafe locations, content, or exclusions.
    :raises _OperationalError: Integrity, stability, resource or I/O failure.
    """
    locations = paths._preflight_vault_paths(origin, mirror, key)
    fernet, warnings = keys._load_key(key)
    # Observe pending ownership before attempting to interpret a partial mirror.
    rules = _mirror_rules(mirror.parent)
    initial = transactions._plan_transaction(origin, mirror, mirror=True, fernet=fernet, target_rules=rules)
    source = inventory._inventory_vault(locations, exclusions=exclusions)
    previous = manifest._verify_mirror(mirror, fernet) if const.MANAGED_DIRECTORY in initial.before else None
    old_files = {record.path: record for record in previous.manifest.files} if previous else {}
    old_directories = {record.path: record for record in previous.manifest.directories} if previous else {}
    current_files = {entry.path for entry in source.entries if entry.kind == 'file'}
    current_directories = {entry.path for entry in source.entries if entry.kind == 'directory'}
    if merge and (current_files & old_directories.keys() or current_directories & old_files.keys()):
        raise _ConfigurationError('Merge cannot discard a retained file/directory type conflict; use shroud fresh.')
    retained = tuple(record for name, record in old_files.items() if name not in current_files) if merge else ()
    counts = {'new': 0, 'changed': 0, 'metadata_only': 0, 'unchanged': 0, 'retained': len(retained)}
    reserved = {record.object_id for record in old_files.values()}
    records = []
    placeholder = 0
    for entry in source.entries:
        if entry.kind != 'file':
            continue
        data = inventory._read_file(source, entry)
        digest = crypto._sha256(data)
        del data
        old = old_files.get(entry.path)
        if old is None:
            while f'{placeholder:032x}' in reserved:
                placeholder += 1
            object_id = f'{placeholder:032x}'
            reserved.add(object_id)
        else:
            object_id = old.object_id
        same = old is not None and old.size == entry.size and old.plaintext_sha256 == digest
        if old is None:
            category = 'new'
        elif not same:
            category = 'changed'
        elif old.mtime_ns != entry.mtime_ns:
            category = 'metadata_only'
        else:
            category = 'unchanged'
        counts[category] += 1
        records.append(
            manifest._FileRecord(
                entry.path, object_id, entry.size, entry.mtime_ns, digest, old.ciphertext_sha256 if same else '0' * 64
            )
        )
    directories = tuple(
        manifest._DirectoryRecord(entry.path, entry.mtime_ns) for entry in source.entries if entry.kind == 'directory'
    )
    if merge:
        records.extend(retained)
        directory_union = dict(old_directories)
        directory_union.update({record.path: record for record in directories})
        directories = tuple(sorted(directory_union.values(), key=lambda record: record.path))
    records.sort(key=lambda record: record.path)
    proposal = manifest._Manifest(
        const.FORMAT_VERSION,
        previous.manifest.vault_id if previous else '0' * 32,
        '0' * 32,
        '2000-01-01T00:00:00.000000Z',
        directories,
        tuple(records),
    )
    no_op = previous is not None and directories == previous.manifest.directories and proposal.files == previous.manifest.files
    current = {record.path: record for record in records}
    removed_directories = previous is not None and bool(
        {record.path for record in previous.manifest.directories} - {record.path for record in directories}
    )
    confirmation = removed_directories or any(
        name not in current or (record.size, record.plaintext_sha256) != (current[name].size, current[name].plaintext_sha256)
        for name, record in old_files.items()
    )
    serialized = manifest._serialize_manifest(proposal)
    retained_bytes = sum(inventory._fernet_size(record.size) for record in retained)
    estimate = inventory._estimate_resources(source, manifest_plaintext_bytes=len(serialized), retained_bytes=retained_bytes)
    transaction = transactions._plan_transaction(
        origin,
        mirror,
        mirror=True,
        fernet=fernet,
        required_bytes=0 if no_op else estimate.required_free_bytes,
        target_rules=rules,
    )
    inventory._verify_inventory(source)
    locations._recheck()
    if previous is not None:
        manifest._recheck_mirror(previous)
    return _BackupPlan(
        locations, source, previous, proposal, transaction, fernet, warnings, no_op, confirmation, merge, _Changes(**counts)
    )


def _write_token(parent: Path, name: str, token: bytes) -> None:
    """Create one private staged file exclusively under an anchored directory."""
    with paths._directory_handle(paths._inspect_path(parent)) as handle:
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=handle)
        try:
            stream = os.fdopen(descriptor, 'wb')
        except (OSError, MemoryError):
            os.close(descriptor)
            raise
        with stream:
            if stream.write(token) != len(token):
                raise _OperationalError('Incomplete staged token write; no partial snapshot is accepted.')


def _build_backup(plan: _BackupPlan, stage: Path) -> None:
    """Build either mode from stable current bytes and authenticated retained ciphertext."""
    managed = stage / const.MANAGED_DIRECTORY
    objects = managed / const.OBJECTS_DIRECTORY
    for parent, child in ((stage, managed), (managed, objects)):
        with paths._directory_handle(paths._inspect_path(parent)) as handle:
            os.mkdir(child.name, 0o700, dir_fd=handle)
    old_files = {record.path: record for record in plan.previous.manifest.files} if plan.previous else {}
    entries = {entry.path: entry for entry in plan.source.entries if entry.kind == 'file'}
    reserved = {record.object_id for record in old_files.values()}
    records = []
    for proposed in plan.proposal.files:
        entry = entries.get(proposed.path)
        if entry is None:
            # Only additive merge proposals can contain a historic, absent path.
            token, data = manifest._validated_token(plan.previous, proposed, plan.fernet)
            del data
            _write_token(objects, f'{proposed.object_id}.obf', token)
            del token
            records.append(proposed)
            continue
        data = inventory._read_file(plan.source, entry)
        if len(data) != proposed.size or crypto._sha256(data) != proposed.plaintext_sha256:
            raise _OperationalError('Source content changed after planning; no snapshot was published.')
        old = old_files.get(entry.path)
        if old is not None and (old.size, old.plaintext_sha256) == (proposed.size, proposed.plaintext_sha256):
            token = manifest._reuse_object(plan.previous, old, data, plan.fernet)
            record = replace(old, mtime_ns=entry.mtime_ns)
        else:
            object_id = old.object_id if old is not None else crypto._new_id(reserved)
            reserved.add(object_id)
            record, token = manifest._encode_file(entry.path, data, entry.mtime_ns, object_id, plan.fernet)
        del data
        _write_token(objects, f'{record.object_id}.obf', token)
        del token
        records.append(record)
    final = replace(
        plan.proposal,
        vault_id=plan.previous.manifest.vault_id if plan.previous else crypto._new_id(),
        snapshot_id=crypto._new_id({plan.previous.manifest.snapshot_id} if plan.previous else ()),
        created_at=datetime.now(UTC).isoformat(timespec='microseconds').replace('+00:00', 'Z'),
        files=tuple(records),
    )
    _write_token(managed, const.MANIFEST_FILENAME, manifest._encrypt_manifest(final, plan.fernet))


def _recheck_source(plan: _BackupPlan) -> None:
    """Re-inventory all included names/content marks and recheck selected key custody."""
    inventory._verify_inventory(plan.source)
    paths._recheck_path(plan.locations.key, content=True)


def _publish_backup(
    plan: _BackupPlan,
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
    dry_run: bool = False,
) -> transactions._TransactionResult | None:
    """Publish a changed verified backup in either mode, or perform no writes.

    :param plan: Complete read-only proposal.
    :param yes: Explicit consent for replacement.
    :param non_interactive: Prohibit consent prompts.
    :param prompt: Terminal-aware replacement prompt.
    :param dry_run: Validate only, without consent, randomness, or artifacts.
    :returns: Retained private locations for a write; no result for no-op/dry run.
    :raises _OperationalError: Consent, stability, transaction or integrity failure.
    :raises KeyboardInterrupt: Interruption after conservative recovery was attempted.
    """
    _recheck_source(plan)
    plan.locations._recheck()
    if plan.previous is not None:
        manifest._recheck_mirror(plan.previous)
    read_only = dry_run or plan.no_op
    return transactions._execute_transaction(
        plan.transaction,
        lambda stage: _build_backup(plan, stage),
        lambda stage: _recheck_source(plan),
        yes=yes or not plan.confirmation,
        non_interactive=non_interactive,
        prompt=prompt,
        dry_run=read_only,
        prepublish=lambda: _recheck_source(plan),
        retain_rollback=not plan.merge,
    )


def _recover_backup(
    origin: Path,
    mirror: Path,
    key: Path,
    *,
    yes: bool = False,
    non_interactive: bool = False,
    prompt: Callable[[], bool] | None = None,
    exclusions: tuple[str, ...] = (),
) -> transactions._TransactionResult:
    """Validate custody and explicitly recover old state before the CLI replans.

    Recovery cannot bypass selected-key authentication of complete mirror
    payloads. Incomplete unapproved staging remains retained. The origin is
    inventoried before recovery to refuse unsafe types and hard-linked keys.
    """
    locations = paths._preflight_vault_paths(origin, mirror, key)
    inventory._inventory_vault(locations, exclusions=exclusions)
    fernet, _warnings = keys._load_key(key)
    plan = transactions._plan_transaction(
        origin, mirror, mirror=True, fernet=fernet, allow_pending=True, target_rules=_mirror_rules(mirror.parent)
    )
    return transactions._recover_transaction(plan, yes=yes, non_interactive=non_interactive, prompt=prompt)

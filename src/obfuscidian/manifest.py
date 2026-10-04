# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.manifest
:Synopsis:          Internal frozen v1 manifest codec and complete read-only validation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import stat
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian.crypto import _check_token_size, _decrypt_bytes, _encrypt_bytes, _sha256
from obfuscidian.errors import _ConfigurationError, _FormatError, _OperationalError
from obfuscidian.inventory import _fernet_size
from obfuscidian.paths import (
    _check_mirror_namespace,
    _directory_handle,
    _Fingerprint,
    _inspect_path,
    _is_link,
    _PathState,
    _recheck_path,
    _TargetRules,
    _validate_relative_path,
    _validate_target_paths,
)


@dataclass(frozen=True)
class _DirectoryRecord:
    """Retain a lossless relative directory name and signed nanosecond time."""

    path: str = field(repr=False)
    mtime_ns: int


@dataclass(frozen=True)
class _FileRecord:
    """Bind a relative path to exact encrypted and plaintext bytes in a manifest."""

    path: str = field(repr=False)
    object_id: str
    size: int
    mtime_ns: int
    plaintext_sha256: str = field(repr=False)
    ciphertext_sha256: str = field(repr=False)


@dataclass(frozen=True)
class _Manifest:
    """Describe the complete immutable v1 logical snapshot, sorted by path."""

    format_version: int
    vault_id: str
    snapshot_id: str
    created_at: str
    directories: tuple[_DirectoryRecord, ...] = field(repr=False)
    files: tuple[_FileRecord, ...] = field(repr=False)


@dataclass(frozen=True)
class _VerifiedMirror:
    """Return complete verification metadata without retaining all object payloads.

    This is a best-effort read-only observation. File helpers recheck its state
    and authenticate the selected object again; future publication must still
    revalidate. No destination is inspected or modified.
    """

    manifest: _Manifest = field(repr=False)
    root: _PathState = field(repr=False)
    states: tuple[_PathState, ...] = field(repr=False)
    encrypted_bytes: int

    @property
    def file_count(self) -> int:
        """Count fully authenticated file objects."""
        return len(self.manifest.files)

    @property
    def directory_count(self) -> int:
        """Count manifest directories, including empty directories, excluding root."""
        return len(self.manifest.directories)

    @property
    def plaintext_bytes(self) -> int:
        """Sum the validated original file sizes."""
        return sum(record.size for record in self.manifest.files)


def _exact_fields(value: Any, expected: frozenset[str]) -> dict[str, Any]:
    """Require one schema object with exactly the specified member names."""
    if not isinstance(value, dict) or value.keys() != expected:
        raise _FormatError('Manifest fields do not match the v1 schema.')
    return value


def _match(value: Any, pattern: str) -> None:
    """Validate a fixed-format string without including its contents in errors."""
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise _FormatError('Manifest contains an invalid identifier, digest, or timestamp.')


def _manifest_path(value: Any, *, directory: bool) -> tuple[str, ...]:
    """Validate portable relative syntax and mandatory source exclusions."""
    try:
        parts = _validate_relative_path(value)
    except _ConfigurationError:
        raise _FormatError('Manifest contains an unsafe or non-UTF-8 relative path.') from None
    if const.GIT_METADATA in parts or (
        not directory
        and (parts[-1] == const.GIT_IGNORE or fnmatch.fnmatchcase(parts[-1], f'{const.KEY_PREFIX}*{const.KEY_SUFFIX}'))
    ):
        raise _FormatError('Manifest includes mandatory excluded Git or key content.')
    return parts


def _integer(value: Any, *, size: bool = False) -> None:
    """Require integer times or a nonnegative size fitting the Fernet cap."""
    if type(value) is not int:
        raise _FormatError('Manifest sizes and modification times must be integers.')
    if size and (value < 0 or _fernet_size(value) > const.MAX_ENCRYPTED_BYTES):
        raise _FormatError('Manifest file size exceeds the bounded v1 object format.')


def _from_mapping(value: Any) -> _Manifest:
    """Validate all schema and path relationships before returning immutable records."""
    data = _exact_fields(value, const.MANIFEST_FIELDS)
    version = data['format_version']
    if type(version) is not int:
        raise _FormatError('Backup format version must be an integer.')
    if version != const.FORMAT_VERSION:
        raise _FormatError('Unsupported backup format version; this reader supports v1 only.')
    _match(data['vault_id'], const.ID_PATTERN)
    _match(data['snapshot_id'], const.ID_PATTERN)
    _match(data['created_at'], const.CREATED_AT_PATTERN)
    try:
        datetime.fromisoformat(data['created_at'])
    except ValueError:
        raise _FormatError('Manifest publication timestamp is not a valid UTC calendar time.') from None
    if not isinstance(data['directories'], list) or not isinstance(data['files'], list):
        raise _FormatError('Manifest records must be arrays.')
    directories, files = [], []
    paths, directory_paths, identifiers = set(), set(), set()
    for directory in data['directories']:
        record = _exact_fields(directory, const.DIRECTORY_FIELDS)
        _manifest_path(record['path'], directory=True)
        _integer(record['mtime_ns'])
        if record['path'] in paths:
            raise _FormatError('Manifest contains duplicate or conflicting paths.')
        paths.add(record['path'])
        directory_paths.add(record['path'])
        directories.append(_DirectoryRecord(**record))
    for file in data['files']:
        record = _exact_fields(file, const.FILE_FIELDS)
        _manifest_path(record['path'], directory=False)
        _match(record['object_id'], const.ID_PATTERN)
        _match(record['plaintext_sha256'], const.SHA256_PATTERN)
        _match(record['ciphertext_sha256'], const.SHA256_PATTERN)
        _integer(record['mtime_ns'])
        _integer(record['size'], size=True)
        if record['path'] in paths or record['object_id'] in identifiers:
            raise _FormatError('Manifest contains duplicate or conflicting paths or object identifiers.')
        paths.add(record['path'])
        identifiers.add(record['object_id'])
        files.append(_FileRecord(**record))
    for path in paths:
        # Checking the immediate parent of every record also checks the entire chain,
        # without quadratic rescans of all ancestor prefixes for deep paths.
        parent = path.rpartition('/')[0]
        if parent and parent not in directory_paths:
            raise _FormatError('Manifest is missing a required parent directory record.')
    return _Manifest(
        version,
        data['vault_id'],
        data['snapshot_id'],
        data['created_at'],
        tuple(sorted(directories, key=lambda record: record.path)),
        tuple(sorted(files, key=lambda record: record.path)),
    )


def _unique_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys at every object level."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise _FormatError('Manifest JSON contains duplicate member names.')
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    """Reject JavaScript non-finite values accepted by Python's default decoder."""
    raise _FormatError('Manifest JSON contains a non-finite number.')


def _check_json_depth(text: str) -> None:
    """Bound structural nesting before invoking the JSON parser, honoring strings."""
    depth, quoted, escaped = 0, False, False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in '[{':
            depth += 1
            if depth > const.MANIFEST_MAX_DEPTH:
                raise _FormatError('Manifest JSON exceeds the v1 structural nesting limit.')
        elif character in ']}':
            depth -= 1


def _parse_manifest(data: bytes) -> _Manifest:
    """Parse bounded authenticated UTF-8 JSON and validate the complete schema.

    :param data: Plaintext bytes obtained only after manifest authentication.
    :returns: Immutable, canonically sorted records.
    :raises _FormatError: JSON, encoding, limits, version, or schema is invalid.
    :raises _OperationalError: Parsing cannot allocate its bounded input.
    """
    if not isinstance(data, bytes) or len(data) > const.MAX_PLAINTEXT_BYTES:
        raise _FormatError('Manifest plaintext must be bounded binary UTF-8 JSON.')
    try:
        text = data.decode('utf-8', errors='strict')
        _check_json_depth(text)
        value = json.loads(text, object_pairs_hook=_unique_members, parse_constant=_reject_constant)
        return _from_mapping(value)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise _FormatError('Manifest JSON or UTF-8 encoding is invalid.') from None
    except MemoryError:
        raise _OperationalError('Cannot allocate manifest validation; no partial result is accepted.') from None


def _serialize_manifest(manifest: _Manifest) -> bytes:
    """Validate and canonically serialize v1 without writing a file.

    :param manifest: Proposed logical metadata; paths and hashes stay private.
    :returns: Compact UTF-8 JSON within the projected encrypted size cap.
    :raises _FormatError: Records or serialized size do not fit v1.
    :raises _OperationalError: Serialization cannot allocate its bounded output.
    """
    try:
        if not isinstance(manifest, _Manifest):
            raise _FormatError('Serialization requires v1 manifest records.')
        mapping = asdict(manifest)
        mapping['directories'] = list(mapping['directories'])
        mapping['files'] = list(mapping['files'])
        validated = _from_mapping(mapping)
        mapping = asdict(validated)
        # Stream JSON chunks into a bounded buffer instead of allocating an
        # arbitrarily large serialized string before checking its final size.
        output = bytearray()
        encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
        for chunk in encoder.iterencode(mapping):
            encoded = chunk.encode('utf-8', errors='strict')
            _check_token_size(_fernet_size(len(output) + len(encoded)))
            output.extend(encoded)
        return bytes(output)
    except (ValueError, UnicodeError, TypeError, RecursionError, OverflowError):
        raise _FormatError('Manifest cannot be serialized as bounded v1 UTF-8 JSON.') from None
    except MemoryError:
        raise _OperationalError('Cannot allocate manifest serialization; no partial result is accepted.') from None


def _encrypt_manifest(manifest: _Manifest, fernet: Fernet) -> bytes:
    """Return a bounded standard token for a validated canonical manifest.

    :param manifest: Complete logical snapshot metadata.
    :param fernet: Selected single-key context.
    :returns: Encrypted canonical manifest bytes, without filesystem writes.
    :raises _FormatError: The schema or encrypted size is invalid.
    :raises _OperationalError: Serialization or encryption fails.
    """
    return _encrypt_bytes(_serialize_manifest(manifest), fernet)


def _decrypt_manifest(token: bytes, fernet: Fernet) -> _Manifest:
    """Authenticate a manifest before parsing or exposing any metadata.

    :param token: Complete encoded manifest token.
    :param fernet: Selected single-key context.
    :returns: Fully validated immutable v1 metadata.
    :raises _FormatError: Authentication, limits, JSON, or schema fails.
    :raises _OperationalError: Decryption or parsing cannot complete.
    """
    return _parse_manifest(_decrypt_bytes(token, fernet))


def _encode_file(path: str, data: bytes, mtime_ns: int, object_id: str, fernet: Fernet) -> tuple[_FileRecord, bytes]:
    """Encode one file entirely in memory, preserving its caller-assigned ID.

    The caller generates collision-free IDs for new paths; changed content at
    an existing path uses the existing ID. No source or mirror file is written.

    :param path: Original portable relative name.
    :param data: Exact original binary bytes.
    :param mtime_ns: Signed original modification time.
    :param object_id: Secure opaque ID reserved by the caller.
    :param fernet: Selected single-key context.
    :returns: Bound manifest record and complete standard encrypted bytes.
    :raises _FormatError: The name, time, ID, or size is invalid.
    :raises _OperationalError: Encryption or allocation fails.
    """
    _manifest_path(path, directory=False)
    _integer(mtime_ns)
    _match(object_id, const.ID_PATTERN)
    token = _encrypt_bytes(data, fernet)
    try:
        return _FileRecord(path, object_id, len(data), mtime_ns, _sha256(data), _sha256(token)), token
    except MemoryError:
        raise _OperationalError('Cannot allocate object binding; no partial result is accepted.') from None


def _decode_file(record: _FileRecord, token: bytes, fernet: Fernet) -> bytes:
    """Verify ciphertext binding, authentication, plaintext size, and plaintext binding."""
    if not isinstance(token, bytes):
        raise _FormatError('Object validation requires binary token bytes.')
    _check_token_size(len(token))
    try:
        if _sha256(token) != record.ciphertext_sha256:
            raise _FormatError('Encrypted object digest differs from its authenticated manifest binding.')
        data = _decrypt_bytes(token, fernet)
        if len(data) != record.size or _sha256(data) != record.plaintext_sha256:
            raise _FormatError('Object plaintext size or digest differs from its authenticated manifest binding.')
        return data
    except MemoryError:
        raise _OperationalError('Cannot allocate object validation; no partial result is accepted.') from None


def _read_token(state: _PathState) -> bytes:
    """Read a single bounded token from its recorded no-follow filesystem identity."""
    expected = state.components[-1][1]
    _check_token_size(expected.size)
    try:
        _recheck_path(state, content=True)
        parent = _inspect_path(state.path.parent)
        # Bind fresh parent handles to the original inspected ancestors.
        for (_, recorded), (_, current) in zip(state.components[:-1], parent.components, strict=True):
            if (recorded.device, recorded.inode, recorded.mode) != (current.device, current.inode, current.mode):
                raise _OperationalError('Backup parent identity changed; stop other writers and retry.')
        with _directory_handle(parent) as handle:
            descriptor = os.open(
                state.path.name if handle is not None else state.path,
                os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0),
                dir_fd=handle,
            )
            try:
                source = os.fdopen(descriptor, 'rb')
            except (OSError, MemoryError):
                os.close(descriptor)
                raise
            with source:
                before = os.fstat(source.fileno())
                if _is_link(before) or not stat.S_ISREG(before.st_mode) or _Fingerprint._from_stat(before) != expected:
                    raise _OperationalError('Backup file identity changed before reading.')
                token = source.read(expected.size + 1)
                if len(token) != expected.size or _Fingerprint._from_stat(os.fstat(source.fileno())) != expected:
                    raise _OperationalError('Backup file changed while reading; no partial result is accepted.')
                current = os.stat(state.path.name if handle is not None else state.path, dir_fd=handle, follow_symlinks=False)
                if _is_link(current) or _Fingerprint._from_stat(current) != expected:
                    raise _OperationalError('Backup file identity changed while reading.')
        _recheck_path(state, content=True)
        return token
    except (OSError, MemoryError):
        raise _OperationalError('Cannot safely read the backup; check permissions, memory, and other writers.') from None


def _mirror_states(root: _PathState) -> tuple[_PathState, ...]:
    """Check safe layout and require all structural entries for a complete mirror."""
    states = _check_mirror_namespace(root)
    names = {state.path.relative_to(root.path).as_posix() for state in states}
    required = {
        const.MANAGED_DIRECTORY,
        f'{const.MANAGED_DIRECTORY}/{const.OBJECTS_DIRECTORY}',
        f'{const.MANAGED_DIRECTORY}/{const.MANIFEST_FILENAME}',
    }
    if not required <= names:
        raise _FormatError('Backup is incomplete; a managed manifest and objects directory are required.')
    return states


def _recheck_mirror(result: _VerifiedMirror) -> None:
    """Refuse changes to identities, managed content, or the complete namespace."""
    _recheck_path(result.root, content=True)
    for state in result.states:
        managed = state.path.is_relative_to(result.root.path / const.MANAGED_DIRECTORY)
        _recheck_path(state, content=managed)
    current = _mirror_states(result.root)
    previous = tuple((state.path, state.components[-1][1]) for state in result.states)
    observed = tuple((state.path, state.components[-1][1]) for state in current)
    if previous != observed:
        raise _OperationalError('Backup namespace changed during validation; stop other writers and retry.')


def _verify_mirror(
    mirror: Path,
    fernet: Fernet,
    *,
    target_rules: _TargetRules | None = None,
    destination: Path | None = None,
) -> _VerifiedMirror:
    """Validate the complete v1 mirror read-only, with optional explicit target rules.

    No plaintext or reusable object is returned before every required object
    passes. One file is processed at a time; plaintext is discarded after each
    validation. Results are observations, not atomic filesystem snapshots.

    :param mirror: Absolute existing mirror location, with safe ancestors.
    :param fernet: Selected single-key context; no key mixing or TTL.
    :param target_rules: Actual target naming rules, if checking restorability.
    :param destination: Optional absolute prefix used for full target path limits.
    :returns: Complete validated metadata, counts, sizes, and private recheck state.
    :raises _FormatError: The format is unsupported, unsafe, incomplete, or corrupt.
    :raises _ConfigurationError: Locations/types or target naming rules are unsafe.
    :raises _OperationalError: Reads fail, memory is unavailable, or state changes.
    """
    try:
        root = _inspect_path(mirror)
        states = _mirror_states(root)
        manifest_path = mirror / const.MANAGED_DIRECTORY / const.MANIFEST_FILENAME
        manifest_state = next(state for state in states if state.path == manifest_path)
        manifest_token = _read_token(manifest_state)
        manifest = _decrypt_manifest(manifest_token, fernet)
        encrypted_bytes = len(manifest_token)
        del manifest_token
        if target_rules is not None:
            _validate_target_paths(
                (record.path for record in (*manifest.directories, *manifest.files)),
                target_rules,
                destination=destination,
            )
        elif destination is not None:
            raise _ConfigurationError('A destination prefix requires explicit target filesystem rules.')
        objects_path = mirror / const.MANAGED_DIRECTORY / const.OBJECTS_DIRECTORY
        objects = {state.path.name: state for state in states if state.path.parent == objects_path}
        required = {f'{record.object_id}.obf' for record in manifest.files}
        if objects.keys() != required:
            raise _FormatError('Backup contains missing or unexpected encrypted objects.')
        for record in manifest.files:
            token = _read_token(objects[f'{record.object_id}.obf'])
            data = _decode_file(record, token, fernet)
            encrypted_bytes += len(token)
            del data, token
        result = _VerifiedMirror(manifest, root, states, encrypted_bytes)
        _recheck_mirror(result)
        return result
    except MemoryError:
        raise _OperationalError('Cannot allocate complete backup validation; no partial result is accepted.') from None


def _validated_token(result: _VerifiedMirror, record: _FileRecord, fernet: Fernet) -> tuple[bytes, bytes]:
    """Recheck a complete observation and return one freshly authenticated token/payload."""
    if record not in result.manifest.files:
        raise _FormatError('Object reuse requires a file record from the fully verified snapshot.')
    try:
        _recheck_mirror(result)
        path = result.root.path / const.MANAGED_DIRECTORY / const.OBJECTS_DIRECTORY / f'{record.object_id}.obf'
        state = next(state for state in result.states if state.path == path)
        token = _read_token(state)
        data = _decode_file(record, token, fernet)
        _recheck_mirror(result)
        return token, data
    except MemoryError:
        raise _OperationalError('Cannot allocate a validated object read; no partial result is accepted.') from None


def _read_validated_file(result: _VerifiedMirror, record: _FileRecord, fernet: Fernet) -> bytes:
    """Read exact bytes only from an entirely verified snapshot, rechecking stability.

    :param result: A prior complete read-only mirror validation.
    :param record: An unchanged record belonging to that snapshot.
    :param fernet: The same single-key context.
    :returns: Freshly authenticated and hash/size-bound original bytes.
    :raises _FormatError: Record binding or authentication fails.
    :raises _OperationalError: The snapshot changed or the read fails.
    """
    _, data = _validated_token(result, record, fernet)
    return data


def _reuse_object(result: _VerifiedMirror, record: _FileRecord, data: bytes, fernet: Fernet) -> bytes:
    """Return exact validated ciphertext only when proposed content is unchanged.

    Callers retain the old object ID and can change only logical metadata for
    metadata-only updates. Changed content must be encrypted as a new token.

    :param result: A prior complete read-only mirror validation.
    :param record: The old bound file record from that snapshot.
    :param data: Proposed full binary content.
    :param fernet: The same single-key context.
    :returns: Original ciphertext, unchanged byte-for-byte.
    :raises _FormatError: Proposed content changed or old binding/authentication fails.
    :raises _OperationalError: The old snapshot changed or cannot be read safely.
    """
    if not isinstance(data, bytes) or len(data) != record.size or _sha256(data) != record.plaintext_sha256:
        raise _FormatError('Changed content cannot reuse an existing encrypted object.')
    token, _ = _validated_token(result, record, fernet)
    return token

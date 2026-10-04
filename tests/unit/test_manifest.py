# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_manifest
:Synopsis:          Frozen v1 schema, topology, canonicalization, and hostile JSON tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import manifest as fmt
from obfuscidian.errors import _FormatError, _OperationalError


@pytest.fixture
def mapping() -> dict:
    """Create independent public synthetic v1 metadata for parser tests."""
    return {
        'format_version': 1,
        'vault_id': 'a' * 32,
        'snapshot_id': 'b' * 32,
        'created_at': '2026-10-04T01:02:03.123456Z',
        'directories': [{'path': 'notes', 'mtime_ns': -123}],
        'files': [
            {
                'path': 'notes/日本語.md',
                'object_id': 'c' * 32,
                'size': 0,
                'mtime_ns': -456,
                'plaintext_sha256': 'd' * 64,
                'ciphertext_sha256': 'e' * 64,
            }
        ],
    }


def parse(mapping: object) -> fmt._Manifest:
    """Serialize test metadata independently of the production serializer."""
    return fmt._parse_manifest(json.dumps(mapping, ensure_ascii=True).encode())


def test_canonical_utf8_and_immutable_round_trip(mapping: dict) -> None:
    """Unsorted input becomes stable UTF-8 JSON without path normalization."""
    mapping['directories'] = [{'path': 'z', 'mtime_ns': 0}, *mapping['directories'], {'path': 'a', 'mtime_ns': -1}]
    mapping['files'].append({**mapping['files'][0], 'path': 'notes/e\u0301.md', 'object_id': 'f' * 32})
    manifest = parse(mapping)
    assert [record.path for record in manifest.directories] == ['a', 'notes', 'z']
    assert [record.path for record in manifest.files] == ['notes/e\u0301.md', 'notes/日本語.md']
    raw = fmt._serialize_manifest(manifest)
    assert '日本語'.encode() in raw
    assert b'\\u' not in raw
    assert b': ' not in raw
    assert fmt._parse_manifest(raw) == manifest
    assert fmt._serialize_manifest(replace(manifest, directories=tuple(reversed(manifest.directories)))) == raw
    fernet = Fernet(Fernet.generate_key())
    token = fmt._encrypt_manifest(manifest, fernet)
    assert fernet.decrypt(token) == raw
    assert fmt._decrypt_manifest(token, fernet) == manifest
    with pytest.raises(AttributeError):
        manifest.files[0].size = 1
    assert '日本語' not in repr(manifest)
    assert '日本語' not in repr(manifest.files[1])
    assert 'd' * 64 not in repr(manifest.files[0])


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('format_version', True),
        ('format_version', 1.0),
        ('format_version', '1'),
        ('format_version', 0),
        ('format_version', 2),
        ('vault_id', None),
        ('vault_id', 'a' * 31),
        ('vault_id', 'A' * 32),
        ('snapshot_id', '../' + 'a' * 32),
        ('snapshot_id', 1),
        ('created_at', '2026-10-04T01:02:03+00:00'),
        ('created_at', '2026-02-30T01:02:03Z'),
        ('created_at', '0000-10-04T01:02:03Z'),
        ('created_at', '2026-10-04T01:02:60Z'),
        ('created_at', '2026-10-04T01:02:03.1234567Z'),
        ('created_at', '2026-10-04'),
        ('directories', {}),
        ('files', {}),
        ('directories', None),
        ('files', 'bad'),
    ],
)
def test_root_types_versions_and_timestamp(mapping: dict, field: str, value: object) -> None:
    """Strict types and unknown versions fail before any object processing."""
    mapping[field] = value
    with pytest.raises(_FormatError):
        parse(mapping)


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('path', None),
        ('path', 1),
        ('object_id', 'C' * 32),
        ('object_id', 'c' * 33),
        ('object_id', '../bad'),
        ('size', True),
        ('size', -1),
        ('size', 0.0),
        ('size', '0'),
        ('size', const.MAX_PLAINTEXT_BYTES + 1),
        ('mtime_ns', False),
        ('mtime_ns', 0.1),
        ('plaintext_sha256', 'D' * 64),
        ('plaintext_sha256', 'd' * 63),
        ('plaintext_sha256', None),
        ('ciphertext_sha256', 'e' * 65),
        ('ciphertext_sha256', 1),
    ],
)
def test_file_fields(mapping: dict, field: str, value: object) -> None:
    """Require exact size/time types and complete lowercase IDs and digests."""
    mapping['files'][0][field] = value
    with pytest.raises(_FormatError):
        parse(mapping)


@pytest.mark.parametrize(
    'path',
    [
        '',
        '/',
        '/escape',
        '../escape',
        'notes/../escape',
        './escape',
        'notes//escape',
        'notes/',
        'C:/escape',
        'C:escape',
        '//server/share',
        '\\server\\share',
        'notes\\escape',
        'notes/\0escape',
        'notes/\ud800',
        '.git/config',
        'notes/.git',
        '.gitignore',
        'notes/.gitignore',
        'notes/obfuscidian-synthetic.key',
    ],
)
def test_hostile_paths_are_rejected_redacted(mapping: dict, path: str) -> None:
    """No untrusted absolute/traversal/drive/link-control path becomes accepted metadata."""
    mapping['files'][0]['path'] = path
    with pytest.raises(_FormatError) as error:
        parse(mapping)
    assert 'escape' not in str(error.value)
    assert 'synthetic.key' not in str(error.value)


@pytest.mark.parametrize(
    'case', ['duplicate-file', 'duplicate-directory', 'duplicate-id', 'conflict', 'missing-parent', 'file-parent']
)
def test_duplicate_and_topology_failures(mapping: dict, case: str) -> None:
    """Records define one complete tree with unique path and object namespaces."""
    if case == 'duplicate-file':
        mapping['files'].append({**mapping['files'][0], 'object_id': 'f' * 32})
    elif case == 'duplicate-directory':
        mapping['directories'] *= 2
    elif case == 'duplicate-id':
        mapping['files'].append({**mapping['files'][0], 'path': 'notes/other.md'})
    elif case == 'conflict':
        mapping['directories'].append({'path': mapping['files'][0]['path'], 'mtime_ns': 0})
    elif case == 'missing-parent':
        mapping['directories'] = []
    else:
        mapping['files'].append({**mapping['files'][0], 'path': 'notes/日本語.md/child', 'object_id': 'f' * 32})
    with pytest.raises(_FormatError):
        parse(mapping)


@pytest.mark.parametrize('level', ['root', 'file', 'directory'])
@pytest.mark.parametrize('change', ['extra', 'missing', 'non-object'])
def test_exact_record_fields(mapping: dict, level: str, change: str) -> None:
    """Unexpected and absent members are not silently ignored."""
    record = mapping if level == 'root' else mapping['files' if level == 'file' else 'directories'][0]
    if change == 'extra':
        record['unknown'] = 0
    elif change == 'missing':
        record.pop(next(iter(record)))
    elif level == 'root':
        mapping = []
    else:
        mapping['files' if level == 'file' else 'directories'][0] = 'bad'
    with pytest.raises(_FormatError):
        parse(mapping)


@pytest.mark.parametrize(
    'raw',
    [
        b'{}',
        b'[]',
        b'null',
        b'\xef\xbb\xbf{}',
        b'\xff',
        b'{',
        b'{}{}',
        b'{"format_version":1,"format_version":1}',
        b'{"directories":[{"path":"a","path":"b"}]}',
        b'{"files":[{"size":NaN}]}',
        b'{"files":[{"size":Infinity}]}',
        b'{"files":[{"size":-Infinity}]}',
        b'[' * 10000 + b']' * 10000,
        b'{"files":[{"path":{"nested":[]}}]}',
        b'{"size":' + b'1' * 5000 + b'}',
    ],
)
def test_hostile_json_is_bounded(raw: bytes) -> None:
    """Malformed, deep, duplicate-key, and non-finite JSON fails safely."""
    with pytest.raises(_FormatError):
        fmt._parse_manifest(raw)


def test_brackets_and_escapes_in_valid_names(mapping: dict) -> None:
    """Depth limiting treats string contents as lossless names, not JSON structure."""
    mapping['files'][0]['path'] = 'notes/[[[{{{"name.md'
    assert parse(mapping).files[0].path == mapping['files'][0]['path']


def test_schema_bounds_and_allocation_failures(mapping: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Serialization checks actual bytes and parsing redacts allocation errors."""
    manifest = parse(mapping)
    monkeypatch.setattr(const, 'MAX_ENCRYPTED_BYTES', 200)
    with pytest.raises(_FormatError):
        fmt._serialize_manifest(manifest)
    monkeypatch.setattr(const, 'MAX_PLAINTEXT_BYTES', 2)
    with pytest.raises(_FormatError):
        fmt._parse_manifest(b'123')
    monkeypatch.undo()

    def fail(*args: object, **kwargs: object) -> None:
        raise MemoryError('SYNTHETIC PRIVATE CONTENT')

    monkeypatch.setattr(fmt.json, 'loads', fail)
    with pytest.raises(_OperationalError) as error:
        fmt._parse_manifest(b'{}')
    assert 'SYNTHETIC PRIVATE' not in str(error.value)
    monkeypatch.setattr(fmt, 'asdict', fail)
    with pytest.raises(_OperationalError):
        fmt._serialize_manifest(manifest)


def test_signed_timestamps_and_empty_snapshot(mapping: dict) -> None:
    """Empty vaults and signed pre-epoch nanoseconds remain valid."""
    mapping['files'] = []
    mapping['directories'] = []
    assert fmt._parse_manifest(fmt._serialize_manifest(parse(mapping))) == parse(mapping)

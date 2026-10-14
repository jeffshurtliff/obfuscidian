# -*- coding: utf-8 -*-
"""
:Module:            tests._v1_exchange
:Synopsis:          Generate and consume only synthetic v1 qualification exchanges
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path

from obfuscidian import backup, keys, manifest, restore

_PAYLOAD = {
    'note.md': b'SYNTHETIC V1 EXCHANGE\r\n\x00\xff',
    'spaced folder/binary.bin': bytes(range(256)),
    'spaced folder/empty.bin': b'',
}
_DIRECTORIES = {'empty', 'spaced folder'}
_MARKER = 'obfuscidian-29-generated-synthetic-v1-only'


def _new_directory(path: Path) -> None:
    """Create a new synthetic directory exclusively using the actual platform."""
    if os.name == 'nt':
        from obfuscidian import _windows_files as files

        files._mkdir(path.parent, path.name)
    else:
        path.mkdir(mode=0o700)


def _output_root(path: Path) -> Path:
    """Refuse checkout output or reused paths before generating synthetic artifacts."""
    root = Path(__file__).resolve().parents[1]
    path = path.absolute()
    assert not path.is_symlink() and not path.exists(), 'Use a new disposable output directory.'
    assert path.parent.is_dir() and not path.parent.is_symlink(), 'Require an existing safe parent.'
    assert not path.resolve().is_relative_to(root), 'Keep generated keys/data outside the checkout.'
    _new_directory(path)
    return path


def _tree(root: Path) -> dict[str, str | None]:
    """Hash primary bytes and directory names without putting key contents in reports."""
    result = {}
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink(), 'Synthetic exchange must contain no links.'
        name = path.relative_to(root).as_posix()
        assert path.is_file() or path.is_dir(), 'Synthetic exchange requires ordinary files/directories.'
        result[name] = None if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _expected_tree() -> dict[str, str | None]:
    return {**dict.fromkeys(_DIRECTORIES), **{name: hashlib.sha256(data).hexdigest() for name, data in _PAYLOAD.items()}}


def _export(output: Path, source_id: str) -> dict:
    """Produce a newly encrypted v1 backup with a newly generated external key."""
    assert re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', source_id), 'Record a full commit or candidate source digest.'
    root = _output_root(output)
    source, mirror, bundle = root / 'source', root / 'producer-mirror', root / 'bundle'
    _new_directory(source)
    _new_directory(bundle)
    for name in sorted(_DIRECTORIES):
        _new_directory(source / name)
    for name, data in _PAYLOAD.items():
        (source / name).write_bytes(data)
    key = bundle / 'synthetic.key'
    keys._generate_key(key)
    before = _tree(source)
    plan = backup._plan_fresh(source, mirror, key)
    publish = backup._publish_windows_backup if os.name == 'nt' else backup._publish_backup
    publish(plan, non_interactive=True)
    assert _tree(source) == before == _expected_tree()
    verified = manifest._verify_mirror(mirror, keys._load_key(key)[0])
    assert verified.file_count == len(_PAYLOAD) and verified.directory_count == len(_DIRECTORIES)
    # Transfer only the encrypted layout, its generated synthetic key and metadata.
    # Original/source/transaction trees stay in the producer's disposable run root.
    shutil.copytree(mirror, bundle / 'mirror')
    metadata = {
        'marker': _MARKER,
        'format': 1,
        'producer': sys.platform,
        'python': platform.python_version(),
        'source_id': source_id,
        'tree': _tree(bundle / 'mirror'),
    }
    (bundle / 'exchange.json').write_text(json.dumps(metadata, sort_keys=True) + '\n', encoding='utf-8')
    return {
        'scope': 'generated synthetic v1 export; private backend on Windows',
        'producer': sys.platform,
        'source_id': source_id,
        'files': verified.file_count,
        'directories': verified.directory_count,
    }


def _import(bundle: Path, output: Path) -> dict:
    """Authenticate expected synthetic bytes before creating any restore output."""
    assert not bundle.is_symlink(), 'Synthetic bundle links refused.'
    assert {p.name for p in bundle.iterdir()} == {'mirror', 'synthetic.key', 'exchange.json'}, 'Unexpected bundle entries.'
    assert not (bundle / 'synthetic.key').is_symlink() and not (bundle / 'exchange.json').is_symlink()
    metadata = json.loads((bundle / 'exchange.json').read_text(encoding='utf-8'))
    assert metadata['marker'] == _MARKER and metadata['format'] == 1, 'Require generated synthetic v1 evidence.'
    assert metadata['producer'] in ('win32', 'darwin', 'linux')
    assert re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', metadata['source_id'])
    mirror, key = bundle / 'mirror', bundle / 'synthetic.key'
    assert not mirror.is_symlink() and _tree(mirror) == metadata['tree'], 'Encrypted transfer changed.'
    fernet = keys._load_key(key)[0]
    verified = manifest._verify_mirror(mirror, fernet)
    assert {item.path: manifest._read_validated_file(verified, item, fernet) for item in verified.manifest.files} == _PAYLOAD
    assert {item.path for item in verified.manifest.directories} == _DIRECTORIES
    before = _tree(mirror)
    root = _output_root(output)
    restored = root / 'restored'
    plan = restore._plan_restore(restored, mirror, key)
    publish = restore._publish_windows_restore if os.name == 'nt' else restore._publish_restore
    publish(plan, non_interactive=True)
    assert _tree(restored) == _expected_tree()
    assert _tree(mirror) == before
    return {
        'scope': 'generated synthetic v1 consumption; private backend on Windows',
        'producer': metadata['producer'],
        'consumer': sys.platform,
        'cross_platform': metadata['producer'] != sys.platform,
        'producer_source_id': metadata['source_id'],
        'python': platform.python_version(),
        'exact_bytes_and_directories': True,
        'source_unchanged': True,
    }


def _main() -> None:
    """Run the internal source-test exchange tool; this is not an installed CLI test."""
    parser = argparse.ArgumentParser(description=_main.__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    export = sub.add_parser('export')
    export.add_argument('--output', type=Path, required=True)
    export.add_argument('--source-id', required=True)
    consume = sub.add_parser('import')
    consume.add_argument('--bundle', type=Path, required=True)
    consume.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    report = _export(options.output, options.source_id) if options.action == 'export' else _import(options.bundle, options.output)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    _main()

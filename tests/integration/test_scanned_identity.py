# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_scanned_identity
:Synopsis:          Regression coverage for incomplete cached enumeration identities
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     06 Oct 2026
"""

from __future__ import annotations

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from obfuscidian import inventory, manifest, paths
from obfuscidian.errors import _ConfigurationError, _OperationalError


@pytest.fixture(params=['native', 'fallback'])
def incomplete_cached_stats(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Model Windows zero-identity DirEntry metadata with native or unanchored traversal."""
    real_scan = os.scandir

    class CachedEntry:
        def __init__(self, entry: os.DirEntry[str]) -> None:
            self.entry = entry

        def __getattr__(self, name: str):
            return getattr(self.entry, name)

        def __fspath__(self) -> str:
            return os.fspath(self.entry)

        def stat(self, *, follow_symlinks: bool = True) -> SimpleNamespace:
            info = self.entry.stat(follow_symlinks=follow_symlinks)
            fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
            fields.update(st_dev=0, st_ino=0, st_nlink=0)
            return SimpleNamespace(**fields)

    @contextmanager
    def scan(location):
        with real_scan(location) as entries:
            yield (CachedEntry(entry) for entry in entries)

    monkeypatch.setattr(os, 'scandir', scan)
    if request.param == 'fallback':
        # Substitute only the paths module's OS view, leaving pathlib/pytest intact.
        monkeypatch.setattr(paths, 'os', SimpleNamespace(name='nt', scandir=scan, stat=os.stat))


def _mirror(tmp_path: Path) -> tuple[Path, Fernet]:
    """Copy the public frozen synthetic fixture, never production ciphertext or keys."""
    fixture = Path(__file__).resolve().parents[1] / 'fixtures/v1'
    root = tmp_path.resolve() / 'mirror'
    shutil.copytree(fixture / 'mirror', root)
    return root, Fernet((fixture / 'synthetic-fernet-key.txt').read_bytes().strip())


def test_inventory_reads_real_identities_and_exact_bytes(tmp_path: Path, incomplete_cached_stats: None) -> None:
    """Fresh metadata supports stable nested reads without accepting zero cached identities."""
    root = tmp_path.resolve() / 'source'
    (root / 'nested/empty').mkdir(parents=True)
    file = root / 'nested/synthetic.bin'
    content = bytes(range(256)) + b'\r\n\x00\xff'
    file.write_bytes(content)
    before = file.lstat()
    observed = inventory._scan_inventory(root)
    entry = next(item for item in observed.entries if item.kind == 'file')
    assert entry.fingerprint == paths._Fingerprint._from_stat(before)
    assert inventory._read_file(observed, entry) == content
    inventory._verify_inventory(observed)
    assert file.read_bytes() == content
    assert file.lstat().st_mtime_ns == before.st_mtime_ns


@pytest.mark.parametrize('excluded', [False, True])
def test_key_hardlink_is_rejected_with_incomplete_cache(tmp_path: Path, incomplete_cached_stats: None, excluded: bool) -> None:
    """Full entry identities still detect key aliases before exclusion pruning."""
    root = tmp_path.resolve() / 'source'
    root.mkdir()
    key = root.parent / 'synthetic.key'
    key.write_bytes(Fernet.generate_key())
    try:
        (root / 'alias.key').hardlink_to(key)
    except OSError:
        pytest.skip('This host cannot create a synthetic hard-link fixture.')
    with pytest.raises(_ConfigurationError, match='key'):
        inventory._scan_inventory(
            root, exclusions=('*.key',) if excluded else (), selected_key=paths._Fingerprint._from_stat(key.lstat())
        )


@pytest.mark.parametrize('change', ['replace', 'edit'])
def test_changed_source_is_rejected_with_incomplete_cache(tmp_path: Path, incomplete_cached_stats: None, change: str) -> None:
    """Retain identity/content rejection even when enumeration metadata is incomplete."""
    root = tmp_path.resolve() / 'source'
    root.mkdir()
    file = root / 'synthetic.bin'
    file.write_bytes(b'OLD')
    observed = inventory._scan_inventory(root)
    if change == 'replace':
        file.rename(root / 'retained.bin')
    file.write_bytes(b'NEW')
    with pytest.raises(_OperationalError):
        inventory._read_file(observed, observed.entries[0])
    assert file.read_bytes() == b'NEW'


def test_complete_mirror_and_late_replacement(tmp_path: Path, incomplete_cached_stats: None) -> None:
    """Authenticate all tokens using full identities and reject a same-byte replacement."""
    root, cipher = _mirror(tmp_path)
    verified = manifest._verify_mirror(root, cipher)
    assert verified.file_count == 5
    assert verified.directory_count == 4
    for record in verified.manifest.files:
        content = manifest._read_validated_file(verified, record, cipher)
        assert len(content) == record.size
    manifest._recheck_mirror(verified)
    object = next((root / '.obfuscidian/objects').iterdir())
    before = object.lstat()
    token = object.read_bytes()
    object.rename(tmp_path / 'retained.obf')
    object.write_bytes(token)
    os.utime(object, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(_OperationalError):
        manifest._recheck_mirror(verified)
    assert object.read_bytes() == token


@pytest.mark.parametrize('location', ['source', 'mirror'])
def test_scanned_links_are_rejected(tmp_path: Path, incomplete_cached_stats: None, location: str) -> None:
    """Fresh entry metadata must remain no-follow, preserving an external link target."""
    external = tmp_path.resolve() / 'external.bin'
    external.write_bytes(b'SYNTHETIC EXTERNAL BYTES')
    if location == 'source':
        root = tmp_path.resolve() / 'source'
        root.mkdir()
        link = root / 'synthetic.bin'
    else:
        root, cipher = _mirror(tmp_path)
        link = root / '.obfuscidian/manifest.obf'
        link.unlink()
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip('This host cannot create a synthetic symlink fixture.')
    with pytest.raises(_ConfigurationError, match='links'):
        if location == 'source':
            inventory._scan_inventory(root)
        else:
            manifest._verify_mirror(root, cipher)
    assert external.read_bytes() == b'SYNTHETIC EXTERNAL BYTES'
    assert link.is_symlink()

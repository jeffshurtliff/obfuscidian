# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_inventory
:Synopsis:          Synthetic glob, size, inventory, and stable-read tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import inventory as inv
from obfuscidian.errors import _ConfigurationError, _OperationalError


@pytest.mark.parametrize(
    ('pattern', 'path', 'directory', 'expected'),
    [
        ('*.tmp', 'a.tmp', False, True),
        ('*.tmp', 'folder/a.tmp', False, False),
        ('**/*.tmp', 'a.tmp', False, True),
        ('**/*.tmp', 'one/two/a.tmp', False, True),
        ('**/*.tmp', 'a.TMP', False, False),
        ('one/*/x', 'one/two/x', False, True),
        ('one/*/x', 'one/two/three/x', False, False),
        ('one/**/x', 'one/x', False, True),
        ('one/**/x', 'one/two/three/x', False, True),
        ('a/**/b/**/c', 'a/b/c', False, True),
        ('a/**/b/**/c', 'a/x/b/y/z/c', False, True),
        ('a?/[0-9].bin', 'ab/3.bin', False, True),
        ('a?/[!0-9].bin', 'ab/x.bin', False, True),
        ('a?/[!0-9].bin', 'ab/3.bin', False, False),
        ('.obsidian/', '.obsidian', True, True),
        ('.obsidian/', '.obsidian', False, False),
        ('attachments/**', 'attachments', True, True),
        ('attachments/**', 'attachments/a.bin', False, True),
        ('**/.DS_Store', '.DS_Store', False, True),
        ('**/.DS_Store', 'nested/.DS_Store', False, True),
        ('no-match', '.git', True, True),
        ('no-match', 'nested/.git', False, True),
        ('no-match', 'nested/.gitignore', False, True),
        ('no-match', '.gitignore', True, False),
        ('no-match', 'nested/obfuscidian-synthetic.key', False, True),
        ('no-match', 'obfuscidian-synthetic.key', True, False),
        ('no-match', 'another.key', False, False),
        ('no-match', '.GITIGNORE', False, False),
    ],
)
def test_exclusion_contract(pattern: str, path: str, directory: bool, expected: bool) -> None:
    """Check anchored case-sensitive components and mandatory rules."""
    assert inv._is_excluded(tuple(path.split('/')), directory=directory, rules=inv._compile_exclusions((pattern,))) is expected


@pytest.mark.parametrize('pattern', ['', '/', '/vault/*', '../*', 'a/../b', './a', 'a//b', 'a\\b', '!keep', 'C:/x', 'C:x', '\0'])
def test_invalid_exclusions(pattern: str) -> None:
    """Reject ambiguous/traversing/absolute globs without disclosing them."""
    with pytest.raises(_ConfigurationError) as error:
        inv._compile_exclusions((pattern,))
    assert repr(pattern) not in str(error.value)


@pytest.mark.parametrize('size', [0, 1, 2, 14, 15, 16, 17, 30, 31, 32, 33, 47, 48, 49, 63, 64, 65, 1024])
def test_exact_fernet_estimate(size: int) -> None:
    """Compare estimates with actual standard tokens at block/Base64 boundaries."""
    cipher = Fernet(Fernet.generate_key())
    assert inv._fernet_size(size) == len(cipher.encrypt(bytes(size)))


@pytest.mark.parametrize('size', [-1, True, 1.5, '1'])
def test_invalid_size(size: object) -> None:
    """Refuse noninteger/negative accounting values."""
    with pytest.raises(_ConfigurationError):
        inv._fernet_size(size)


def test_cap_and_largest_plaintext() -> None:
    """Accept exactly the encrypted cap and reject the first oversized block."""
    inv._check_encrypted_size(const.MAX_ENCRYPTED_BYTES)
    assert inv._fernet_size(const.MAX_PLAINTEXT_BYTES) <= const.MAX_ENCRYPTED_BYTES
    assert inv._fernet_size(const.MAX_PLAINTEXT_BYTES + 1) > const.MAX_ENCRYPTED_BYTES
    with pytest.raises(_ConfigurationError, match='50 MiB'):
        inv._check_encrypted_size(const.MAX_ENCRYPTED_BYTES + 1)


def test_oversize_source(tmp_path: Path) -> None:
    """Refuse a sparse oversized synthetic attachment without reading/omitting it."""
    root = tmp_path.resolve()
    path = root / 'synthetic.bin'
    with path.open('wb') as output:
        output.truncate(const.MAX_PLAINTEXT_BYTES + 1)
    with pytest.raises(_ConfigurationError, match='50 MiB'):
        inv._scan_inventory(root)
    assert path.stat().st_size == const.MAX_PLAINTEXT_BYTES + 1
    assert inv._scan_inventory(root, exclusions=('*.bin',)).excluded_entries == 1


def test_size_and_space_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Account for all objects, actual manifest bytes, retained content, and copies."""
    root = tmp_path.resolve()
    (root / 'empty').mkdir()
    (root / 'zero.bin').write_bytes(b'')
    (root / 'block.bin').write_bytes(bytes(16))
    inventory = inv._scan_inventory(root)
    estimate = inv._estimate_resources(inventory, manifest_plaintext_bytes=16, retained_bytes=99, rollback_copy_bytes=123)
    assert estimate.object_bytes == inv._fernet_size(0) + inv._fernet_size(16)
    assert estimate.manifest_bytes == inv._fernet_size(16)
    assert estimate.staging_bytes == estimate.object_bytes + estimate.manifest_bytes + 99
    assert estimate.required_free_bytes == estimate.staging_bytes + 123
    monkeypatch.setattr(inv.shutil, 'disk_usage', lambda _: SimpleNamespace(free=estimate.required_free_bytes))
    inv._check_space(root, estimate)
    monkeypatch.setattr(inv.shutil, 'disk_usage', lambda _: SimpleNamespace(free=estimate.required_free_bytes - 1))
    with pytest.raises(_OperationalError, match='Insufficient'):
        inv._check_space(root, estimate)
    monkeypatch.setattr(inv.os, 'access', lambda *_: False)
    with pytest.raises(_OperationalError, match='writable'):
        inv._check_space(root, estimate)
    with pytest.raises(_ConfigurationError, match='50 MiB'):
        inv._estimate_resources(inventory, manifest_plaintext_bytes=const.MAX_PLAINTEXT_BYTES + 1)
    for kwargs in ({'retained_bytes': -1}, {'rollback_copy_bytes': True}):
        with pytest.raises(_ConfigurationError):
            inv._estimate_resources(inventory, manifest_plaintext_bytes=0, **kwargs)
    assert sorted(item.name for item in root.iterdir()) == ['block.bin', 'empty', 'zero.bin']


def test_scan_and_read_permission_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Report inaccessible files/trees without skipping entries or exposing paths."""
    root = tmp_path.resolve()
    path = root / 'SYNTHETIC-PRIVATE-NAME.bin'
    path.write_bytes(b'synthetic binary')
    inventory = inv._scan_inventory(root)
    real_open = os.open

    def deny_file(name: str | Path, flags: int, *args: object, **kwargs: object) -> int:
        if str(name).endswith(path.name):
            raise PermissionError(str(path))
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(inv.os, 'open', deny_file)
    with pytest.raises(_OperationalError) as error:
        inv._read_file(inventory, inventory.entries[0])
    assert path.name not in str(error.value) and str(root) not in str(error.value)

    def deny_scan(*_: object) -> None:
        raise PermissionError(str(root))

    monkeypatch.setattr(inv.os, 'scandir', deny_scan)
    with pytest.raises(_OperationalError) as error:
        inv._scan_inventory(root)
    assert str(root) not in str(error.value)


def test_special_files(tmp_path: Path) -> None:
    """Reject a synthetic FIFO without opening or blocking on it."""
    if not hasattr(os, 'mkfifo'):
        pytest.skip('The host cannot create FIFO fixtures.')
    root = tmp_path.resolve()
    os.mkfifo(root / 'synthetic-fifo')
    with pytest.raises(_ConfigurationError, match='regular files'):
        inv._scan_inventory(root)
    assert inv._scan_inventory(root, exclusions=('synthetic-fifo',)).excluded_entries == 1


def test_reparse_point_detection() -> None:
    """Exercise junction/reparse rejection on all hosts with synthetic metadata."""
    from obfuscidian.paths import _is_link

    reparse = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    assert _is_link(SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=reparse))


def test_long_globs_do_not_require_recursion() -> None:
    """Component matching remains bounded by iterative state for long inputs."""
    components = tuple('synthetic' for _ in range(1500))
    assert inv._glob_matches(('**',), components)
    assert inv._glob_matches(components, components)


def test_scan_does_not_read_file_contents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inventory is metadata-only even for arbitrary binary file types."""
    root = tmp_path.resolve()
    (root / 'binary.bin').write_bytes(bytes(range(256)))
    real_open = os.open

    def directories_only(name: str | Path, flags: int, *args: object, **kwargs: object) -> int:
        assert not str(name).endswith('binary.bin'), 'Inventory read file content.'
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(inv.os, 'open', directories_only)
    inventory = inv._scan_inventory(root)
    assert inventory.plaintext_bytes == 256


@pytest.mark.skipif(os.name != 'posix', reason='POSIX chmod read-denial fixture is not portable to Windows ACLs.')
def test_real_directory_permission_denial(tmp_path: Path) -> None:
    """Refuse an inaccessible included subtree rather than reporting partial success."""
    root = tmp_path.resolve()
    private = root / 'synthetic-inaccessible'
    private.mkdir()
    (private / 'synthetic.txt').write_bytes(b'SYNTHETIC')
    private.chmod(0)
    try:
        if os.access(private, os.R_OK | os.X_OK):
            pytest.skip('The current process bypasses POSIX mode permission denial.')
        with pytest.raises(_OperationalError):
            inv._scan_inventory(root)
        assert inv._scan_inventory(root, exclusions=('synthetic-inaccessible/',)).excluded_entries == 1
    finally:
        private.chmod(0o700)

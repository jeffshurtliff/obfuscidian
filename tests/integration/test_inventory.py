# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_inventory
:Synopsis:          Synthetic preservation and changing-source preflight scenarios
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import inventory as inv
from obfuscidian.cli import cli
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.paths import _preflight_vault_paths


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Create representative synthetic bytes, directories, config, and Git controls."""
    root = tmp_path.resolve() / 'synthetic-vault'
    root.mkdir()
    for relative in ('empty', 'nested/empty', '.obsidian', '.git', 'attachments', 'ignored'):
        (root / relative).mkdir(parents=True, exist_ok=True)
    for relative, data in {
        'note.md': b'# SYNTHETIC\r\n\x00\xff\n',
        'attachments/image.bin': bytes(range(256)),
        'zero.bin': b'',
        '.hidden': b'SYNTHETIC HIDDEN',
        '.obsidian/settings.json': b'{"synthetic": true}\n',
        'nested/日本語.md': 'SYNTHETIC café\n'.encode(),
        '.git/control': b'SYNTHETIC GIT CONTROL',
        '.gitignore': b'SYNTHETIC ROOT IGNORE',
        'nested/.gitignore': b'SYNTHETIC NESTED IGNORE',
        'nested/.git': b'gitdir: ../synthetic-metadata\n',
        'nested/obfuscidian-placeholder.key': b'SYNTHETIC EXCLUDED PLACEHOLDER; NOT A REAL KEY',
        'ignored/never-visited': b'SYNTHETIC EXCLUDED SUBTREE',
        'root.tmp': b'SYNTHETIC EXCLUDED FILE',
    }.items():
        (root / relative).write_bytes(data)
    return root


def _snapshot(root: Path) -> dict[str, tuple[int, int, int, int, int, int, str | None]]:
    """Capture names/types/identities/mode/times and full hashes, excluding atime."""
    result = {}
    for path in [root, *root.rglob('*')]:
        info = path.lstat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if stat.S_ISREG(info.st_mode) else None
        result[path.relative_to(root).as_posix()] = (
            info.st_mode,
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            digest,
        )
    return result


def test_read_only_fixture_preservation(vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Inventory twice, read all exact bytes, and prove the full source is preserved."""
    key = vault.parent / 'synthetic.key'
    key.write_bytes(b'SYNTHETIC PREFLIGHT PLACEHOLDER; NOT A REAL KEY')
    mirror = vault.parent / 'new-mirror'
    before = _snapshot(vault.parent)
    paths = _preflight_vault_paths(vault, mirror, key)
    first = inv._inventory_vault(paths, exclusions=('ignored/', '**/*.tmp'))
    second = inv._inventory_vault(paths, exclusions=('ignored/', '**/*.tmp'))
    assert first == second
    assert [entry.path for entry in first.entries] == sorted(entry.path for entry in first.entries)
    assert (first.file_count, first.directory_count, first.excluded_entries) == (6, 5, 7)
    expected = {'.hidden', '.obsidian/settings.json', 'attachments/image.bin', 'nested/日本語.md', 'note.md', 'zero.bin'}
    assert {entry.path for entry in first.entries if entry.kind == 'file'} == expected
    assert {'empty', 'nested/empty'} <= {entry.path for entry in first.entries if entry.kind == 'directory'}
    for entry in first.entries:
        if entry.kind == 'file':
            assert inv._read_file(first, entry) == (vault / entry.path).read_bytes()
    inv._verify_inventory(first)
    assert _snapshot(vault.parent) == before
    assert not mirror.exists()
    output = capsys.readouterr()
    assert output.out == output.err == ''


@pytest.mark.skipif(os.name == 'nt', reason='Windows cannot create filenames containing control characters.')
def test_control_character_names(vault: Path) -> None:
    """Preserve POSIX names containing newlines/tabs without logging them."""
    name = 'SYNTHETIC\ncontrol\tname.bin'
    (vault / name).write_bytes(b'\x00\xff\r\n')
    before = _snapshot(vault)
    inventory = inv._scan_inventory(vault)
    entry = next(entry for entry in inventory.entries if entry.path == name)
    assert inv._read_file(inventory, entry) == b'\x00\xff\r\n'
    inv._verify_inventory(inventory)
    assert _snapshot(vault) == before


def test_pruned_subtrees_are_never_traversed(vault: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Excluded directories may contain otherwise unsafe entries without descent."""
    forbidden = [vault / '.git', vault / 'ignored', vault / '.obsidian']
    real_scan = os.scandir
    identities = {(item.stat().st_dev, item.stat().st_ino) for item in forbidden}

    def guarded_scan(location: int | Path):
        info = os.fstat(location) if isinstance(location, int) else location.stat()
        assert (info.st_dev, info.st_ino) not in identities, 'Excluded subtree was traversed.'
        return real_scan(location)

    if hasattr(os, 'mkfifo'):
        os.mkfifo(vault / 'ignored' / 'unsafe-fifo')
    monkeypatch.setattr(inv.os, 'scandir', guarded_scan)
    inventory = inv._scan_inventory(vault, exclusions=('ignored/', '.obsidian/'))
    assert '.obsidian' not in {entry.path for entry in inventory.entries}
    assert inventory.excluded_entries == 7


def test_links_and_exclusions(vault: Path) -> None:
    """Refuse non-excluded file/directory links and never follow excluded links."""
    linked = vault / 'synthetic-link'
    try:
        linked.symlink_to(vault.parent, target_is_directory=True)
    except OSError:
        pytest.skip('This host cannot create directory symlink fixtures.')
    with pytest.raises(_ConfigurationError, match='links'):
        inv._scan_inventory(vault)
    assert inv._scan_inventory(vault, exclusions=('synthetic-link',)).excluded_entries == 6
    with pytest.raises(_ConfigurationError, match='links'):
        inv._scan_inventory(vault, exclusions=('synthetic-link/',))
    linked.unlink()
    linked.symlink_to(vault / 'note.md')
    with pytest.raises(_ConfigurationError, match='links'):
        inv._scan_inventory(vault)
    linked.unlink()
    linked.symlink_to(vault / 'absent')
    with pytest.raises(_ConfigurationError, match='links'):
        inv._scan_inventory(vault)


@pytest.mark.parametrize('change', ['add', 'delete', 'edit', 'rename', 'replace', 'directory-replace', 'mtime'])
def test_post_read_source_changes(vault: Path, change: str) -> None:
    """Detect additions/deletions/content/identity/time changes after reads."""
    inventory = inv._scan_inventory(vault)
    path = vault / 'note.md'
    entry = next(item for item in inventory.entries if item.path == 'note.md')
    inv._read_file(inventory, entry)
    if change == 'add':
        (vault / 'new.bin').write_bytes(b'SYNTHETIC NEW')
    elif change == 'delete':
        path.unlink()
    elif change == 'edit':
        path.write_bytes(b'SYNTHETIC CHANGED')
    elif change == 'rename':
        path.rename(vault / 'renamed.md')
    elif change == 'replace':
        replacement = vault / 'replacement'
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)
    elif change == 'directory-replace':
        (vault / 'empty').rename(vault / 'saved-empty')
        (vault / 'empty').mkdir()
    else:
        info = path.stat()
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 10_000_000))
    with pytest.raises(_OperationalError):
        inv._verify_inventory(inventory)


@pytest.mark.parametrize('change', ['edit', 'replace', 'truncate'])
def test_changes_during_file_read(vault: Path, monkeypatch: pytest.MonkeyPatch, change: str) -> None:
    """Inject real changes between reading bytes and the post-read stat check."""
    inventory = inv._scan_inventory(vault)
    path = vault / 'note.md'
    entry = next(item for item in inventory.entries if item.path == 'note.md')
    real_stat = os.fstat
    calls = 0

    def changing_stat(descriptor: int):
        nonlocal calls
        info = real_stat(descriptor)
        if stat.S_ISREG(info.st_mode):
            calls += 1
            if calls == 2:
                if change == 'replace':
                    replacement = vault / 'replacement'
                    replacement.write_bytes(path.read_bytes())
                    replacement.replace(path)
                elif change == 'edit':
                    path.write_bytes(b'SYNTHETIC CHANGED')
                else:
                    path.write_bytes(b'')
                info = real_stat(descriptor)
        return info

    monkeypatch.setattr(inv.os, 'fstat', changing_stat)
    # Windows may deny replacement of an open file; either detected change or
    # that sharing denial must refuse the read, never return a partial payload.
    with pytest.raises(_OperationalError, match='changed|Cannot read the source safely'):
        inv._read_file(inventory, entry)
    assert calls >= 2


def test_addition_during_scan(vault: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse a source that changes after directory enumeration begins."""
    real_scan = os.scandir
    changed = False

    class ChangingScan:
        def __init__(self, location: int | Path) -> None:
            self.iterator = real_scan(location)

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.iterator.close()

        def __iter__(self):
            nonlocal changed
            children = list(self.iterator)
            if not changed:
                changed = True
                (vault / 'late.bin').write_bytes(b'SYNTHETIC ADDITION')
            return iter(children)

    monkeypatch.setattr(inv.os, 'scandir', ChangingScan)
    with pytest.raises(_OperationalError, match='changed'):
        inv._scan_inventory(vault)


def test_replaced_parent_before_read(vault: Path) -> None:
    """Do not accept a new parent tree containing identically named files."""
    inventory = inv._scan_inventory(vault)
    entry = next(item for item in inventory.entries if item.path == 'attachments/image.bin')
    parent = vault / 'attachments'
    parent.rename(vault / 'saved-attachments')
    parent.mkdir()
    (parent / 'image.bin').write_bytes(bytes(range(256)))
    with pytest.raises(_OperationalError, match='changed'):
        inv._read_file(inventory, entry)


@pytest.mark.parametrize('alias_name', ['synthetic-alias.bin', 'obfuscidian-synthetic.key'])
def test_external_key_hardlink(vault: Path, alias_name: str) -> None:
    """Refuse selected-key aliases inside the source, including excluded key names."""
    key = vault.parent / 'external-synthetic.key'
    key.write_bytes(b'SYNTHETIC PLACEHOLDER; NOT A REAL KEY')
    try:
        (vault / alias_name).hardlink_to(key)
    except OSError:
        pytest.skip('The host cannot create hard-link fixtures.')
    paths = _preflight_vault_paths(vault, vault.parent / 'mirror', key)
    with pytest.raises(_ConfigurationError, match='key'):
        inv._inventory_vault(paths)


def test_only_implemented_commands_exposed() -> None:
    """Expose fresh and merge restore while requiring their complete configuration."""
    runner = CliRunner()
    assert set(cli.commands) == {'keygen', 'shroud', 'unshroud', 'verify'}
    for command in ('unshroud',):
        result = runner.invoke(cli, [command, 'merge'])
        assert result.exit_code == 2 and 'Select --origin and --mirror' in result.output
    assert runner.invoke(cli, ['shroud', 'merge']).exit_code == 2


def test_unrelated_sibling_changes_are_not_source_changes(vault: Path) -> None:
    """Later staging beside a vault must not invalidate an unchanged source."""
    first = inv._scan_inventory(vault)
    sibling = vault.parent / 'synthetic-unrelated-directory'
    sibling.mkdir()
    (sibling / 'synthetic.txt').write_bytes(b'SYNTHETIC UNRELATED CONTENT')
    second = inv._scan_inventory(vault)
    assert first == second
    inv._verify_inventory(first)


def test_empty_source_is_valid(tmp_path: Path) -> None:
    """Accept a truly empty source without requiring Obsidian configuration."""
    root = tmp_path.resolve()
    first = inv._scan_inventory(root)
    assert first == inv._scan_inventory(root)
    assert (first.file_count, first.directory_count, first.excluded_entries, first.plaintext_bytes) == (0, 0, 0, 0)
    inv._verify_inventory(first)
    assert list(root.iterdir()) == []


def test_unsafe_change_after_inventory(vault: Path) -> None:
    """Detect an included path replaced by a link without reading linked content."""
    first = inv._scan_inventory(vault)
    path = vault / 'note.md'
    entry = next(item for item in first.entries if item.path == 'note.md')
    path.unlink()
    try:
        path.symlink_to(vault.parent / 'nonexistent-synthetic-target')
    except OSError:
        pytest.skip('The host cannot create file symlink fixtures.')
    with pytest.raises(_OperationalError):
        inv._read_file(first, entry)
    with pytest.raises((_OperationalError, _ConfigurationError)):
        inv._verify_inventory(first)


def test_memory_failure_is_redacted(vault: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Never return partial binary data after an allocation failure."""
    inventory = inv._scan_inventory(vault)
    entry = next(item for item in inventory.entries if item.path == 'note.md')
    real_fdopen = os.fdopen

    class FailingRead:
        def __init__(self, descriptor: int, mode: str) -> None:
            self.source = real_fdopen(descriptor, mode)

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            self.source.close()

        def fileno(self) -> int:
            return self.source.fileno()

        def read(self, size: int) -> bytes:
            raise MemoryError('SYNTHETIC PRIVATE ALLOCATION FAILURE')

    monkeypatch.setattr(inv.os, 'fdopen', FailingRead)
    with pytest.raises(_OperationalError, match='memory') as error:
        inv._read_file(inventory, entry)
    assert 'SYNTHETIC PRIVATE' not in str(error.value)

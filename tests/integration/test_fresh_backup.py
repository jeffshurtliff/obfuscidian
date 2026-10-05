# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_fresh_backup
:Synopsis:          Synthetic end-to-end fresh backup, preservation and recovery
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import errno
import importlib
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import backup, crypto, inventory, keys, manifest
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from obfuscidian.errors import _OperationalError

cli_module = importlib.import_module('obfuscidian.cli')
pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Fresh mutation fails closed pending native platform hardening.')


@pytest.fixture
def vaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    """Keep selectors, synthetic content, keys, and actual Git metadata isolated."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path.resolve()
    source = root / 'origin'
    source.mkdir()
    for name, data in {
        'note.md': b'SYNTHETIC NOTE\r\n',
        'nested/attachment.bin': bytes(range(256)),
        'nested/zero.bin': b'',
        '.obsidian/settings.json': b'{"synthetic":true}\n',
        'nested/unicode-\u2603.md': b'SYNTHETIC UNICODE',
        '.gitignore': b'SYNTHETIC ORIGIN GIT IGNORE',
        'nested/.gitignore': b'SYNTHETIC NESTED GIT IGNORE',
        'nested/obfuscidian-never.key': b'SYNTHETIC EXCLUDED KEY SENTINEL',
        '.hidden': b'SYNTHETIC HIDDEN',
    }.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (source / 'nested/empty').mkdir()
    (source / 'nested/.git').mkdir()
    (source / 'nested/.git/sentinel').write_bytes(b'SYNTHETIC NESTED GIT')
    subprocess.run(['git', 'init', '-q', str(source)], capture_output=True, check=True)
    repository = root / 'repository'
    subprocess.run(['git', 'init', '-q', str(repository)], capture_output=True, check=True)
    mirror = repository / 'mirror'
    mirror.mkdir()
    (mirror / '.git').write_bytes(b'gitdir: ../.git\n')
    (mirror / '.gitignore').write_bytes(b'SYNTHETIC MIRROR CONTROL\n')
    key = root / 'obfuscidian-synthetic.key'
    keys._generate_key(key)
    return source, mirror, key


def _snapshot(root: Path) -> dict:
    """Record namespace, bytes, identity, permissions and timestamps except read-induced atime."""
    result = {}
    for path in (root, *sorted(root.rglob('*'))):
        info = path.lstat()
        result[path.relative_to(root).as_posix()] = (
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            path.read_bytes() if stat.S_ISREG(info.st_mode) else None,
        )
    return result


def _args(vaults: tuple[Path, Path, Path]) -> list[str]:
    """Use absolute isolated paths and the implemented fresh positional mode."""
    source, mirror, key = vaults
    return ['shroud', 'fresh', '--origin', str(source), '--mirror', str(mirror), '--key', str(key), '--non-interactive']


def _invoke(vaults: tuple[Path, Path, Path], *options: str, input: str | None = None):
    """Invoke sequential Click CLI operations only."""
    return CliRunner().invoke(cli, _args(vaults) + list(options), input=input)


def _verified(vaults: tuple[Path, Path, Path], root: Path | None = None) -> manifest._VerifiedMirror:
    """Independently authenticate each resulting snapshot with the shared validator."""
    _, mirror, key = vaults
    fernet, _ = keys._load_key(key)
    return manifest._verify_mirror(mirror if root is None else root, fernet)


def _payload(vaults: tuple[Path, Path, Path], root: Path | None = None) -> dict[str, bytes]:
    """Decode bytes through the validated file reader, never a restore operation."""
    result = _verified(vaults, root)
    fernet, _ = keys._load_key(vaults[2])
    return {record.path: manifest._read_validated_file(result, record, fernet) for record in result.manifest.files}


def _workspaces(vaults: tuple[Path, Path, Path]) -> list[Path]:
    """Find only this isolated fixture's private transaction directories."""
    return sorted(path for path in vaults[0].parent.glob(const.TRANSACTION_PREFIX + '*') if path.is_dir())


def _first(vaults: tuple[Path, Path, Path]) -> manifest._VerifiedMirror:
    """Require an initially empty protected mirror to need no overwrite consent."""
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    assert 'published' in result.output
    return _verified(vaults)


def test_mixed_vault_preserves_origin_git_controls_and_exact_binary(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Back up hidden/config/binary/zero/empty/nested content without any Git operations."""
    source, mirror, key = vaults
    source_before = _snapshot(source)
    controls = {name: _snapshot(mirror / name) for name in ('.git', '.gitignore')}
    repository_git = _snapshot(mirror.parent / '.git')

    def forbid_git(*args, **kwargs):
        pytest.fail('Backup must not execute Git or vault content.')

    monkeypatch.setattr(subprocess, 'run', forbid_git)
    checked = _first(vaults)
    expected = {
        entry.path: (source / entry.path).read_bytes()
        for entry in inventory._scan_inventory(source).entries
        if entry.kind == 'file'
    }
    assert _payload(vaults) == expected
    assert 'nested/empty' in {record.path for record in checked.manifest.directories}
    assert checked.file_count == 6
    assert _snapshot(source) == source_before
    assert _snapshot(mirror.parent / '.git') == repository_git
    assert all(_snapshot(mirror / name) == value for name, value in controls.items())
    assert {path.name for path in mirror.iterdir()} == {'.git', '.gitignore', '.obfuscidian'}
    assert all(path.parent == source.parent for path in _workspaces(vaults))
    assert key.read_bytes().decode() not in _invoke(vaults).output


def test_stale_removal_ciphertext_reuse_changed_ids_and_retained_rollback(vaults: tuple[Path, Path, Path]) -> None:
    """Fresh purges absent/excluded paths, retains old data, and preserves lineage and unchanged tokens."""
    source, mirror, _ = vaults
    old = _first(vaults)
    old_tokens = {
        record.path: (mirror / '.obfuscidian/objects' / f'{record.object_id}.obf').read_bytes() for record in old.manifest.files
    }
    old_payload = _payload(vaults)
    (source / 'nested/zero.bin').unlink()
    (source / 'note.md').write_bytes(b'SYNTHETIC CHANGED\x00\xff')
    (source / 'new.md').write_bytes(b'SYNTHETIC ADDITION')
    result = _invoke(vaults, '--yes', '--exclude', '.obsidian/')
    assert result.exit_code == 0, result.output
    new = _verified(vaults)
    new_files = {record.path: record for record in new.manifest.files}
    old_files = {record.path: record for record in old.manifest.files}
    assert 'nested/zero.bin' not in new_files and '.obsidian/settings.json' not in new_files
    assert 'new.md' in new_files
    assert new.manifest.vault_id == old.manifest.vault_id
    assert new.manifest.snapshot_id != old.manifest.snapshot_id
    assert new_files['note.md'].object_id == old_files['note.md'].object_id
    assert (mirror / '.obfuscidian/objects' / f'{new_files["note.md"].object_id}.obf').read_bytes() != old_tokens['note.md']
    for name in ('.hidden', 'nested/attachment.bin'):
        assert new_files[name] == old_files[name]
        assert (mirror / '.obfuscidian/objects' / f'{new_files[name].object_id}.obf').read_bytes() == old_tokens[name]
    rollback = next(
        path / const.TRANSACTION_ROLLBACK for path in _workspaces(vaults) if (path / 'rollback/.obfuscidian').exists()
    )
    assert _payload(vaults, rollback) == old_payload
    assert _verified(vaults, rollback).manifest == old.manifest
    assert rollback.parent.stat().st_mode & 0o077 == 0
    assert 'Previous complete encrypted snapshot retained' in result.output
    assert str(rollback) not in result.output


def test_noop_has_no_writes_randomness_or_new_snapshot(vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """No-op preserves identities, mtimes, bytes, namespace and retained artifact count."""
    old = _first(vaults)
    before = _snapshot(vaults[0].parent)

    def forbidden(*args, **kwargs):
        pytest.fail('No-op cannot allocate randomness, tokens, staging, or ownership.')

    monkeypatch.setattr(crypto, '_new_id', forbidden)
    monkeypatch.setattr(crypto, '_encrypt_bytes', forbidden)
    monkeypatch.setattr(tx, '_lock_descriptor', forbidden)
    monkeypatch.setattr(backup, '_build_fresh', forbidden)
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    assert 'no-op' in result.output
    assert _snapshot(vaults[0].parent) == before
    assert _verified(vaults).manifest == old.manifest


@pytest.mark.parametrize('state', ['absent', 'empty', 'replacement', 'noop'])
def test_dry_run_never_writes_or_confirms(vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, state: str) -> None:
    """Read-only plans authenticate/hash/estimate, without creating a missing mirror or any artifact."""
    source, mirror, key = vaults
    if state in {'replacement', 'noop'}:
        _first(vaults)
    if state == 'replacement':
        (source / 'note.md').write_bytes(b'SYNTHETIC REPLACEMENT')
    if state == 'absent':
        mirror = mirror.parent / 'absent'
        vaults = source, mirror, key
    before = _snapshot(source.parent)

    def forbidden(*args, **kwargs):
        pytest.fail('Dry run cannot encrypt, generate IDs, create ownership or prompt for consent.')

    monkeypatch.setattr(crypto, '_new_id', forbidden)
    monkeypatch.setattr(backup, '_write_token', forbidden)
    monkeypatch.setattr(tx, '_confirm_action', forbidden)
    monkeypatch.setattr(tx, '_lock_descriptor', forbidden)
    result = _invoke(vaults, '--dry-run')
    assert result.exit_code == 0, result.output
    assert 'Dry run:' in result.output and 'estimated' in result.output
    assert _snapshot(source.parent) == before
    assert mirror.exists() == (state != 'absent')


@pytest.mark.parametrize('change', ['content', 'delete', 'exclude', 'empty-directory'])
def test_unattended_destructive_change_needs_yes(vaults: tuple[Path, Path, Path], change: str) -> None:
    """Non-interactive or redirected affirmative input never implies replacement consent."""
    source, _, _ = vaults
    _first(vaults)
    options = []
    if change == 'content':
        (source / 'note.md').write_bytes(b'SYNTHETIC CHANGED')
    elif change == 'delete':
        (source / 'note.md').unlink()
    elif change == 'exclude':
        options = ['--exclude', 'note.md']
    else:
        (source / 'nested/empty').rmdir()
    before = _snapshot(source.parent)
    result = _invoke(vaults, *options, input='y\n')
    assert result.exit_code == 1, result.output
    assert 'confirmation' in result.output
    assert _snapshot(source.parent) == before
    result = _invoke(vaults, *options, '--yes')
    assert result.exit_code == 0, result.output
    _verified(vaults)


@pytest.mark.parametrize('response', ['n\n', '', 'y\n'])
def test_terminal_confirmation_after_preflight(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, response: str
) -> None:
    """Decline and EOF write nothing; affirmative terminal consent permits fresh replacement."""
    _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC CHANGED')
    before = _snapshot(vaults[0].parent)
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    arguments = _args(vaults)
    arguments.remove('--non-interactive')
    result = CliRunner().invoke(cli, arguments, input=response)
    assert result.exit_code == (0 if response == 'y\n' else 1), result.output
    assert 'Replace existing contents' in result.output
    if response != 'y\n':
        assert _snapshot(vaults[0].parent) == before


@pytest.mark.parametrize('change', ['file-mtime', 'directory-mtime', 'addition'])
def test_metadata_and_additions_need_no_confirmation(vaults: tuple[Path, Path, Path], change: str) -> None:
    """Logical metadata changes preserve ciphertext and need no content-overwrite consent."""
    old = _first(vaults)
    source, mirror, _ = vaults
    old_tokens = {p.name: p.read_bytes() for p in (mirror / '.obfuscidian/objects').iterdir()}
    if change == 'addition':
        (source / 'additional.bin').write_bytes(b'SYNTHETIC ADDED')
    else:
        target = source / ('note.md' if change == 'file-mtime' else 'nested/empty')
        info = target.stat()
        os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000_000))
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    new = _verified(vaults)
    assert new.manifest.snapshot_id != old.manifest.snapshot_id
    for name, token in old_tokens.items():
        assert (mirror / '.obfuscidian/objects' / name).read_bytes() == token


@pytest.mark.parametrize('corruption', ['wrong-key', 'manifest', 'object', 'missing', 'extra', 'unsupported'])
@pytest.mark.parametrize('dry_run', [False, True])
def test_existing_mirror_must_authenticate_before_artifacts(
    vaults: tuple[Path, Path, Path], corruption: str, dry_run: bool
) -> None:
    """Fresh and dry run never bypass whole-mirror authentication, even with --yes."""
    old = _first(vaults)
    source, mirror, key = vaults
    if corruption == 'wrong-key':
        key = source.parent / 'obfuscidian-wrong.key'
        keys._generate_key(key)
        vaults = source, mirror, key
    elif corruption == 'manifest':
        (mirror / '.obfuscidian/manifest.obf').write_bytes(b'SYNTHETIC CORRUPTION')
    elif corruption in {'object', 'missing'}:
        path = mirror / '.obfuscidian/objects' / f'{old.manifest.files[0].object_id}.obf'
        path.unlink() if corruption == 'missing' else path.write_bytes(b'SYNTHETIC CORRUPTION')
    elif corruption == 'extra':
        (mirror / '.obfuscidian/objects' / ('f' * 32 + '.obf')).write_bytes(b'SYNTHETIC EXTRA')
    else:
        fernet, _ = keys._load_key(key)
        plaintext = manifest._serialize_manifest(old.manifest).replace(b'"format_version":1', b'"format_version":2')
        (mirror / '.obfuscidian/manifest.obf').write_bytes(fernet.encrypt(plaintext))
    before = _snapshot(source.parent)
    result = _invoke(vaults, '--yes', *(['--dry-run'] if dry_run else []))
    assert result.exit_code == 1, result.output
    assert _snapshot(source.parent) == before
    assert str(source.parent) not in result.output
    assert key.read_bytes().decode() not in result.output


@pytest.mark.parametrize(
    'unsafe', ['unmanaged', 'overlap', 'link', 'key-inside', 'key-hardlink', 'missing-parent', 'source-link']
)
def test_unsafe_locations_fail_without_writes(vaults: tuple[Path, Path, Path], unsafe: str) -> None:
    """--yes cannot bypass namespace, overlap, link, selected-key custody or parent checks."""
    source, mirror, key = vaults
    if unsafe == 'unmanaged':
        (mirror / 'unmanaged.md').write_bytes(b'SYNTHETIC USER DATA')
    elif unsafe == 'overlap':
        mirror = source / 'mirror'
    elif unsafe == 'link':
        linked = mirror.parent / 'linked'
        linked.symlink_to(mirror, target_is_directory=True)
        mirror = linked
    elif unsafe == 'key-inside':
        inside = source / 'obfuscidian-selected.key'
        inside.write_bytes(key.read_bytes())
        key = inside
    elif unsafe == 'key-hardlink':
        os.link(key, source / 'obfuscidian-alias.key')
    elif unsafe == 'missing-parent':
        mirror = mirror.parent / 'missing/mirror'
    else:
        (source / 'unsafe-link').symlink_to(key)
    before = _snapshot(source.parent)
    result = _invoke((source, mirror, key), '--yes')
    assert result.exit_code == 2, result.output
    assert _snapshot(source.parent) == before


@pytest.mark.parametrize('change', ['edit', 'add', 'delete', 'replace-parent', 'late-edit'])
def test_detected_source_changes_never_publish(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """Changed sources after planning or after ready checkpoint leave the old complete snapshot."""
    old = _first(vaults)
    source, _, key = vaults
    (source / 'note.md').write_bytes(b'SYNTHETIC PLANNED UPDATE')
    plan = backup._plan_fresh(source, vaults[1], key)
    if change == 'edit':
        (source / 'nested/attachment.bin').write_bytes(b'SYNTHETIC CONCURRENT EDIT')
    elif change == 'add':
        (source / 'nested/new.bin').write_bytes(b'SYNTHETIC CONCURRENT ADD')
    elif change == 'delete':
        (source / 'nested/attachment.bin').unlink()
    elif change == 'replace-parent':
        (source / 'nested').rename(source / 'original-nested')
        (source / 'nested').mkdir()
    else:
        original = tx._checkpoint

        def checkpoint(workspace, journal):
            nonlocal source_after_edit
            original(workspace, journal)
            if journal['phase'] == 'ready':
                (source / 'nested/attachment.bin').write_bytes(b'SYNTHETIC LATE EDIT')
                source_after_edit = _snapshot(source)

        monkeypatch.setattr(tx, '_checkpoint', checkpoint)
    source_after_edit = _snapshot(source)
    with pytest.raises(_OperationalError):
        backup._publish_fresh(plan, yes=True, non_interactive=True)
    assert _verified(vaults).manifest == old.manifest
    assert _snapshot(source) == source_after_edit


@pytest.mark.parametrize('failure', ['write', 'encrypt', 'verify', 'move', 'interrupt'])
def test_normal_failures_recover_complete_old_snapshot(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """Stage/encryption/validation/rename failures and interrupts never report partial success."""
    old = _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC CHANGED')
    source_before = _snapshot(vaults[0])
    if failure == 'write':

        def fail_write(*args, **kwargs):
            raise OSError(errno.ENOSPC, 'SYNTHETIC PRIVATE ERROR')

        monkeypatch.setattr(backup, '_write_token', fail_write)
    elif failure == 'encrypt':

        def fail_encrypt(*args, **kwargs):
            raise MemoryError('SYNTHETIC PRIVATE ERROR')

        monkeypatch.setattr(manifest, '_encode_file', fail_encrypt)
    elif failure == 'verify':
        original_verify = tx._verify_mirror

        def fail_verify(root, *args, **kwargs):
            if root.name == const.TRANSACTION_STAGE:
                raise _OperationalError('SYNTHETIC PRIVATE ERROR')
            return original_verify(root, *args, **kwargs)

        monkeypatch.setattr(tx, '_verify_mirror', fail_verify)
    else:
        original_move = tx._move
        count = 0

        def fail_move(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                if failure == 'interrupt':
                    raise KeyboardInterrupt
                raise OSError(errno.EACCES, 'SYNTHETIC PRIVATE ERROR')
            return original_move(*args, **kwargs)

        monkeypatch.setattr(tx, '_move', fail_move)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == (130 if failure == 'interrupt' else 1), result.output
    assert 'published' not in result.output
    assert 'SYNTHETIC PRIVATE ERROR' not in result.output
    assert _verified(vaults).manifest == old.manifest
    assert _snapshot(vaults[0]) == source_before
    assert not list(vaults[0].parent.glob('*.lock'))


def _block_replacement(vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> manifest._VerifiedMirror:
    """Leave the old snapshot in rollback and exclusive pending ownership through injected failure."""
    old = _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC CHANGED')
    original_move = tx._move
    count = 0

    def fail_move(*args, **kwargs):
        nonlocal count
        count += 1
        if count > 1:
            raise OSError(errno.EACCES, 'SYNTHETIC RECOVERY FAILURE')
        return original_move(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(tx, '_move', fail_move)
        result = _invoke(vaults, '--yes')
        assert result.exit_code == 1 and 'explicit recovery' in result.output
    return old


def test_pending_blocks_dryrun_and_write_recovery_requires_consent_then_retries(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Blocked writes preserve artifacts; explicit consent restores old then publishes the replanned fresh snapshot."""
    old = _block_replacement(vaults, monkeypatch)
    before = _snapshot(vaults[0].parent)
    for options in ([], ['--dry-run'], ['--recover']):
        result = _invoke(vaults, *options)
        assert result.exit_code == 1, result.output
        assert _snapshot(vaults[0].parent) == before
    rollback = next(path / 'rollback' for path in _workspaces(vaults) if (path / 'rollback/.obfuscidian').exists())
    assert _verified(vaults, rollback).manifest == old.manifest
    source_before = _snapshot(vaults[0])
    result = _invoke(vaults, '--recover', '--yes')
    assert result.exit_code == 0, result.output
    assert 'Previous state recovered; replanning' in result.output and 'published' in result.output
    assert _payload(vaults)['note.md'] == b'SYNTHETIC CHANGED'
    assert _snapshot(vaults[0]) == source_before
    assert not list(vaults[0].parent.glob('*.lock'))


def test_wrong_key_cannot_mutate_pending_recovery(vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Even --recover --yes must authenticate complete retained mirror payloads before inverse moves."""
    _block_replacement(vaults, monkeypatch)
    wrong_key = vaults[0].parent / 'obfuscidian-wrong.key'
    keys._generate_key(wrong_key)
    before = _snapshot(vaults[0].parent)
    result = _invoke((vaults[0], vaults[1], wrong_key), '--recover', '--yes')
    assert result.exit_code == 1, result.output
    assert _snapshot(vaults[0].parent) == before


def test_recovery_refuses_user_modified_retained_bytes(vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not delete or overwrite uncertain retained data even when recovery is explicitly requested."""
    _block_replacement(vaults, monkeypatch)
    rollback = next(path / 'rollback' for path in _workspaces(vaults) if (path / 'rollback/.obfuscidian').exists())
    next((rollback / '.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC USER EDIT')
    before = _snapshot(vaults[0].parent)
    result = _invoke(vaults, '--recover', '--yes')
    assert result.exit_code == 1, result.output
    assert _snapshot(vaults[0].parent) == before


@pytest.mark.parametrize('limit', ['object', 'manifest', 'space'])
def test_size_and_space_limits_fail_before_artifacts(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """Reject projected object/actual serialized manifest caps and unavailable space before writes."""
    before = _snapshot(vaults[0].parent)
    if limit == 'object':
        monkeypatch.setattr(const, 'MAX_ENCRYPTED_BYTES', 100)
    elif limit == 'manifest':
        monkeypatch.setattr(const, 'MAX_ENCRYPTED_BYTES', 1000)
    else:
        original = tx.shutil.disk_usage
        monkeypatch.setattr(tx.shutil, 'disk_usage', lambda path: original(path)._replace(free=0))
    result = _invoke(vaults, '--yes')
    assert result.exit_code in {1, 2}, result.output
    assert _snapshot(vaults[0].parent) == before


def test_configuration_precedence_prompts_privacy_and_exclusions(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use environment paths/alias; exclude before encryption and escape terminal controls under explicit verbose."""
    source, mirror, key = vaults
    (source / 'SYNTHETIC\x1b\nNAME.md').write_bytes(b'SYNTHETIC FILE CONTENT')
    (source / 'nested/private.tmp').write_bytes(b'SYNTHETIC EXCLUDED')
    monkeypatch.setenv(const.ENV_ORIGIN, str(source))
    monkeypatch.setenv(const.ENV_MIRROR, str(mirror))
    monkeypatch.setenv(const.ENV_KEY_ALIAS, 'synthetic')
    monkeypatch.setenv(const.ENV_KEY_DIR, str(key.parent))
    args = ['shroud', 'fresh', '--exclude', '**/*.tmp', '--non-interactive']
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    assert 'private.tmp' not in _payload(vaults)
    assert 'nested/private.tmp' not in _payload(vaults)
    assert 'SYNTHETIC' not in result.output
    assert str(source.parent) not in result.output and key.read_bytes().decode() not in result.output
    result = CliRunner().invoke(cli, args + ['--verbose'])
    assert result.exit_code == 0
    assert '\\x1b\\nNAME.md' in result.output
    assert '\x1b' not in result.output and 'SYNTHETIC FILE CONTENT' not in result.output
    assert key.read_bytes().decode() not in result.output
    invalid = CliRunner().invoke(cli, args + ['--origin', str(source.parent / 'missing')])
    assert invalid.exit_code == 2


@pytest.mark.parametrize(
    'arguments',
    [
        [],
        ['fresh', '--recover', '--dry-run'],
        ['merge'],
        ['fresh', '--log-file', 'x'],
        ['fresh', '--log-paths'],
        ['fresh', '--exclude', '../bad'],
        ['fresh', '--key', 'x', '--alias', 'x'],
    ],
)
def test_invalid_combinations_have_no_side_effects(vaults: tuple[Path, Path, Path], arguments: list[str]) -> None:
    """Unsupported modes/options, missing inputs and invalid combinations never write."""
    before = _snapshot(vaults[0].parent)
    result = CliRunner().invoke(cli, ['shroud', *arguments])
    assert result.exit_code == 2, result.output
    assert _snapshot(vaults[0].parent) == before


def test_first_backup_creates_only_final_mirror_component(vaults: tuple[Path, Path, Path]) -> None:
    """Publish a fully authenticated snapshot into an absent final destination with no overwrite prompt."""
    source, mirror, key = vaults
    absent = mirror.parent / 'absent'
    vaults = source, absent, key
    _first(vaults)
    assert absent.stat().st_mode & 0o077 == 0
    assert _payload(vaults)['nested/attachment.bin'] == bytes(range(256))


@pytest.mark.parametrize('boundary', ['ready', 'old-moved', 'new-moved'])
def test_process_death_and_cli_recovery(vaults: tuple[Path, Path, Path], boundary: str) -> None:
    """Abrupt process death retains old/new complete data and blocks writes until explicit CLI recovery."""
    old = _first(vaults)
    source, mirror, key = vaults
    (source / 'note.md').write_bytes(b'SYNTHETIC PROCESS UPDATE')
    source_before = _snapshot(source)
    script = """
import os, sys
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
boundary = sys.argv[1]
checkpoint = tx._checkpoint
move = tx._move
count = 0
def stop_checkpoint(workspace, journal):
    checkpoint(workspace, journal)
    if boundary == 'ready' and journal['phase'] == 'ready':
        os._exit(77)
def stop_move(*args, **kwargs):
    global count
    move(*args, **kwargs)
    count += 1
    if (boundary == 'old-moved' and count == 1) or (boundary == 'new-moved' and count == 2):
        os._exit(77)
tx._checkpoint = stop_checkpoint
tx._move = stop_move
cli(args=sys.argv[2:], prog_name='obfuscidian')
"""
    process = subprocess.run(
        [sys.executable, '-c', script, boundary, *_args(vaults), '--yes'],
        cwd=source.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert process.returncode == 77, process.stdout + process.stderr
    assert key.read_bytes().decode() not in process.stdout + process.stderr
    before_retry = _snapshot(source.parent)
    blocked = _invoke(vaults, '--yes')
    assert blocked.exit_code == 1 and 'pending' in blocked.output
    assert _snapshot(source.parent) == before_retry
    result = _invoke(vaults, '--recover', '--yes')
    assert result.exit_code == 0, result.output
    assert _verified(vaults).manifest.vault_id == old.manifest.vault_id
    assert _payload(vaults)['note.md'] == b'SYNTHETIC PROCESS UPDATE'
    assert _snapshot(source) == source_before
    assert not list(source.parent.glob('*.lock'))


@pytest.mark.parametrize('git_control', ['directory', 'absent'])
def test_root_git_directory_or_absent_controls_stay_in_place(vaults: tuple[Path, Path, Path], git_control: str) -> None:
    """Mirror Git directory identity/contents are preserved; backup never initializes missing Git controls."""
    source, mirror, _ = vaults
    (mirror / '.git').unlink()
    if git_control == 'directory':
        subprocess.run(['git', 'init', '-q', str(mirror)], capture_output=True, check=True)
        controls_before = _snapshot(mirror / '.git')
    else:
        (mirror / '.gitignore').unlink()
    _first(vaults)
    (source / 'note.md').write_bytes(b'SYNTHETIC SECOND BACKUP')
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0, result.output
    if git_control == 'directory':
        assert _snapshot(mirror / '.git') == controls_before
    else:
        assert not (mirror / '.git').exists() and not (mirror / '.gitignore').exists()


def test_source_read_permission_failure_is_redacted_and_read_only(
    vaults: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unreadable source fails without creating artifacts or leaking exception paths."""
    before = _snapshot(vaults[0].parent)

    def fail(*args, **kwargs):
        raise PermissionError(f'SYNTHETIC PRIVATE {vaults[0]}')

    monkeypatch.setattr(inventory, '_read_file', fail)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 1, result.output
    assert str(vaults[0]) not in result.output and 'SYNTHETIC PRIVATE' not in result.output
    assert _snapshot(vaults[0].parent) == before


def test_options_and_exclusion_validation_precede_writes(vaults: tuple[Path, Path, Path]) -> None:
    """Reject validly selected but invalid globs or selector conflicts before any transaction artifact."""
    before = _snapshot(vaults[0].parent)
    for options in (
        ['--exclude', '../bad'],
        ['--exclude', '/absolute'],
        ['--exclude', 'bad\\glob'],
        ['--alias', 'synthetic'],
        ['--keydir', str(vaults[2].parent)],
    ):
        result = _invoke(vaults, *options, '--yes')
        assert result.exit_code == 2, result.output
        assert _snapshot(vaults[0].parent) == before

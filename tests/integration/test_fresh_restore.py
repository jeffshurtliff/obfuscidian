# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_fresh_restore
:Synopsis:          Synthetic fresh restore, complete preflight, preservation and recovery
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import errno
import importlib
import json
import os
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import backup, keys, manifest, restore
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from obfuscidian.errors import _OperationalError

cli_module = importlib.import_module('obfuscidian.cli')
pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Restore writes fail closed pending native Windows hardening.')


def _snapshot(root: Path) -> dict:
    """Record all bytes, namespace, identities and times except read-induced atime."""
    return {
        p.relative_to(root).as_posix(): (
            p.lstat().st_ino,
            p.lstat().st_mode,
            p.lstat().st_mtime_ns,
            p.lstat().st_ctime_ns,
            p.read_bytes() if stat.S_ISREG(p.lstat().st_mode) else None,
        )
        for p in (root, *sorted(root.rglob('*')))
    }


@pytest.fixture
def vaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path]:
    """Use complete synthetic backups, an external key and a separate plaintext destination."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path.resolve()
    source, mirror, origin, key = (root / name for name in ('source', 'mirror', 'destination', 'obfuscidian-synthetic.key'))
    source.mkdir()
    for name, data in {
        'note.md': b'SYNTHETIC NOTE\r\n',
        'nested/binary.bin': bytes(range(256)),
        'nested/zero.bin': b'',
        '.hidden': b'SYNTHETIC HIDDEN',
        '.obsidian/settings.json': b'{"synthetic":"backup"}\n',
        'nested/unicode-\u2603.md': b'SYNTHETIC UNICODE',
        '.gitignore': b'SYNTHETIC EXCLUDED',
        'obfuscidian-excluded.key': b'SYNTHETIC EXCLUDED',
    }.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (source / 'nested/empty').mkdir()
    (source / 'nested/.git').mkdir()
    (source / 'nested/.git/sentinel').write_bytes(b'SYNTHETIC EXCLUDED')
    keys._generate_key(key)
    backup._publish_backup(backup._plan_fresh(source, mirror, key), non_interactive=True)
    origin.mkdir()
    (origin / 'old.md').write_bytes(b'SYNTHETIC OLD PLAINTEXT')
    (origin / 'obfuscidian-old.key').write_bytes(b'SYNTHETIC OLD EXCLUDED')
    (origin / '.gitignore').write_bytes(b'SYNTHETIC DESTINATION CONTROL')
    (origin / '.obsidian').mkdir()
    (origin / '.obsidian/settings.json').write_bytes(b'{"synthetic":"destination"}')
    return source, mirror, origin, key


def _args(vaults: tuple[Path, Path, Path, Path]) -> list[str]:
    """Restore direction is mirror to origin, using absolute temporary paths."""
    _, mirror, origin, key = vaults
    return ['unshroud', 'fresh', '--origin', str(origin), '--mirror', str(mirror), '--key', str(key), '--non-interactive']


def _invoke(vaults, *options, input=None):
    """Keep Click runner invocations sequential."""
    return CliRunner().invoke(cli, [*_args(vaults), *options], input=input)


def _verified(vaults):
    """Independently authenticate fixture metadata."""
    fernet, _ = keys._load_key(vaults[3])
    return manifest._verify_mirror(vaults[1], fernet)


def _rollback(vaults: tuple[Path, Path, Path, Path]) -> Path:
    """Locate only the old plaintext rollback, ignoring prior encrypted backup workspaces."""
    return next(p for p in vaults[0].parent.glob(const.TRANSACTION_PREFIX + '*/rollback') if (p / 'old.md').exists())


@pytest.mark.parametrize('preserve', [False, True])
@pytest.mark.parametrize('git_control', ['directory', 'file', 'absent'])
def test_roundtrip_bytes_directories_times_controls_and_private_rollback(vaults, preserve, git_control) -> None:
    """Restore the complete included tree; protect controls/settings identities and retain old sensitive payload."""
    source, mirror, origin, _ = vaults
    if git_control == 'directory':
        subprocess.run(['git', 'init', '-q', str(origin)], check=True, capture_output=True)
    elif git_control == 'file':
        (origin / '.git').write_bytes(b'gitdir: ../SYNTHETIC-GIT-DIRECTORY\n')
    mirror_before = _snapshot(mirror)
    ignore_before = _snapshot(origin / '.gitignore')
    git_before = _snapshot(origin / '.git') if git_control != 'absent' else None
    settings_before = _snapshot(origin / '.obsidian')
    result = _invoke(vaults, '--yes', *(['--preserve-config'] if preserve else []))
    assert result.exit_code == 0, result.output
    assert 'Plaintext recovery data is sensitive' in result.output
    assert str(source.parent) not in result.output and 'settings.json' not in result.output
    assert _snapshot(mirror) == mirror_before
    assert _snapshot(origin / '.gitignore') == ignore_before
    assert (_snapshot(origin / '.git') if git_control != 'absent' else None) == git_before
    verified = _verified(vaults)
    expected = {r.path for r in (*verified.manifest.directories, *verified.manifest.files)}
    actual = {p.relative_to(origin).as_posix() for p in origin.rglob('*') if '.git' not in p.relative_to(origin).parts}
    assert actual - {'.gitignore'} == expected
    for record in verified.manifest.files:
        if preserve and record.path.startswith('.obsidian/'):
            continue
        path = origin / record.path
        assert path.read_bytes() == (source / record.path).read_bytes()
        assert path.stat().st_mtime_ns == record.mtime_ns
        assert path.stat().st_mode & 0o077 == 0
    for record in verified.manifest.directories:
        if preserve and record.path == '.obsidian':
            continue
        assert (origin / record.path).stat().st_mtime_ns == record.mtime_ns
        assert (origin / record.path).stat().st_mode & 0o077 == 0
    rollback = _rollback(vaults)
    assert rollback.parent.parent == source.parent
    assert rollback.stat().st_mode & 0o077 == rollback.parent.stat().st_mode & 0o077 == 0
    assert (rollback / 'old.md').read_bytes() == b'SYNTHETIC OLD PLAINTEXT'
    assert (rollback / 'obfuscidian-old.key').read_bytes() == b'SYNTHETIC OLD EXCLUDED'
    assert not (rollback / '.git').exists() and not (rollback / '.gitignore').exists()
    if preserve:
        assert _snapshot(origin / '.obsidian') == settings_before
        assert not (rollback / '.obsidian').exists()
    else:
        assert (rollback / '.obsidian/settings.json').read_bytes() == settings_before['settings.json'][-1]


def test_merge_backup_restores_retained_stale_excluded_and_empty_entries(vaults) -> None:
    """Additive backup history remains reconstructible with fresh restore."""
    source, mirror, origin, key = vaults
    (source / 'note.md').unlink()
    (source / 'nested/empty').rmdir()
    (source / 'new.md').write_bytes(b'SYNTHETIC NEW')
    backup._publish_backup(backup._plan_merge(source, mirror, key, exclusions=('nested/binary.bin',)), non_interactive=True)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0, result.output
    assert (origin / 'note.md').read_bytes() == b'SYNTHETIC NOTE\r\n'
    assert (origin / 'nested/binary.bin').read_bytes() == bytes(range(256))
    assert (origin / 'nested/empty').is_dir() and (origin / 'new.md').exists()


@pytest.mark.parametrize('absent', [False, True])
def test_dryrun_has_no_writes_randomness_plaintext_or_confirmation(vaults, monkeypatch, absent) -> None:
    """Complete verification and target checks create no artifacts, even with a missing final destination."""
    if absent:
        vaults = vaults[:2] + (vaults[2].parent / 'absent', vaults[3])
    before = _snapshot(vaults[0].parent)

    def forbidden(*args, **kwargs):
        pytest.fail('Dry run must never stage, lock, generate randomness or prompt')

    monkeypatch.setattr(restore, '_build_restore', forbidden)
    monkeypatch.setattr(tx, '_confirm_action', forbidden)
    monkeypatch.setattr(tx.secrets, 'token_hex', forbidden)
    result = _invoke(vaults, '--dry-run')
    assert result.exit_code == 0, result.output
    assert 'no files or transaction artifacts created' in result.output
    assert _snapshot(vaults[0].parent) == before


@pytest.mark.parametrize('empty', ['absent', 'empty', 'protected-only'])
def test_empty_destination_needs_no_consent(vaults, empty) -> None:
    """Create only the final component or populate an empty/protected-only destination."""
    origin = vaults[2].parent / 'empty-destination'
    vaults = vaults[:2] + (origin, vaults[3])
    if empty != 'absent':
        origin.mkdir()
        if empty == 'protected-only':
            (origin / '.gitignore').write_bytes(b'SYNTHETIC CONTROL')
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    assert (origin / 'nested/binary.bin').read_bytes() == bytes(range(256))
    if empty == 'absent':
        assert origin.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize('response', ['n\n', '', 'y\n'])
def test_terminal_confirmation_refusal_eof_and_success(vaults, monkeypatch, response) -> None:
    """Ask only after complete preflight; declined/ended consent writes nothing."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    args = _args(vaults)
    args.remove('--non-interactive')
    before = _snapshot(vaults[0].parent)
    result = CliRunner().invoke(cli, args, input=response)
    assert result.exit_code == (0 if response == 'y\n' else 1), result.output
    assert 'Replace existing plaintext' in result.output
    if response != 'y\n':
        assert _snapshot(vaults[0].parent) == before
    else:
        assert 'Recovery workspace:' in result.output


def test_unattended_never_prompts_or_infers_consent(vaults) -> None:
    """A nonterminal input stream containing yes cannot waive destructive consent."""
    before = _snapshot(vaults[0].parent)
    args = _args(vaults)
    args.remove('--non-interactive')
    result = CliRunner().invoke(cli, args, input='y\n')
    assert result.exit_code == 1 and 'Explicit confirmation' in result.output
    assert _snapshot(vaults[0].parent) == before


@pytest.mark.parametrize(
    'corruption',
    [
        'key',
        'manifest',
        'object',
        'missing',
        'extra',
        'unsupported',
        'substitution',
        'traversal',
        'parent',
        'git',
        'key-entry',
        'collision',
        'git-alias',
    ],
)
@pytest.mark.parametrize('dry_run', [False, True])
def test_complete_verification_and_name_checks_precede_all_artifacts(vaults, corruption, dry_run) -> None:
    """Even --yes and preserved settings cannot bypass authentication or target safety."""
    source, mirror, origin, key = vaults
    verified = _verified(vaults)
    fernet, _ = keys._load_key(key)
    token = mirror / '.obfuscidian/manifest.obf'
    objects = mirror / '.obfuscidian/objects'
    if corruption == 'key':
        key = source.parent / 'obfuscidian-wrong.key'
        keys._generate_key(key)
        vaults = source, mirror, origin, key
    elif corruption == 'manifest':
        token.write_bytes(b'SYNTHETIC CORRUPTION')
    elif corruption in {'object', 'missing', 'substitution'}:
        first, second = verified.manifest.files[:2]
        path = objects / f'{first.object_id}.obf'
        if corruption == 'missing':
            path.unlink()
        elif corruption == 'substitution':
            path.write_bytes((objects / f'{second.object_id}.obf').read_bytes())
        else:
            path.write_bytes(b'SYNTHETIC CORRUPTION')
    elif corruption == 'extra':
        (objects / ('f' * 32 + '.obf')).write_bytes(b'SYNTHETIC EXTRA')
    else:
        data = json.loads(manifest._serialize_manifest(verified.manifest))
        if corruption == 'unsupported':
            data['format_version'] = 2
        elif corruption == 'parent':
            data['directories'] = [r for r in data['directories'] if r['path'] != 'nested']
        elif corruption == 'collision':
            other = dict(data['files'][-1], path='NOTE.md', object_id='f' * 32)
            data['files'].append(other)
        else:
            data['files'][0]['path'] = {
                'traversal': '../unsafe',
                'git': '.git',
                'key-entry': 'obfuscidian-unsafe.key',
                'git-alias': '.GIT',
            }[corruption]
        token.write_bytes(fernet.encrypt(json.dumps(data).encode()))
    before = _snapshot(source.parent)
    result = _invoke(vaults, '--yes', '--preserve-config', *(['--dry-run'] if dry_run else []))
    assert result.exit_code in {1, 2}, result.output
    assert 'published' not in result.output and str(source.parent) not in result.output
    assert key.read_bytes().decode() not in result.output
    assert _snapshot(source.parent) == before


@pytest.mark.parametrize(
    'unsafe',
    [
        'overlap',
        'inside-source',
        'key-inside',
        'key-hardlink',
        'missing-parent',
        'link',
        'destination-file',
        'nested-git',
        'source-link',
        'payload-link',
        'fifo',
    ],
)
def test_unsafe_destinations_preserve_everything(vaults, unsafe) -> None:
    """Refuse unsafe shape, links, overlap, key aliases and nested repository destruction before artifacts."""
    source, mirror, origin, key = vaults
    if unsafe == 'overlap':
        origin = mirror
    elif unsafe == 'inside-source':
        origin = mirror / 'restore'
    elif unsafe == 'key-inside':
        key = origin / 'obfuscidian-selected.key'
        key.write_bytes(vaults[3].read_bytes())
    elif unsafe == 'key-hardlink':
        os.link(key, origin / 'obfuscidian-alias.key')
    elif unsafe == 'missing-parent':
        origin = origin.parent / 'missing/restore'
    elif unsafe in {'link', 'source-link'}:
        linked = origin.parent / 'linked'
        linked.symlink_to(origin if unsafe == 'link' else mirror, target_is_directory=True)
        if unsafe == 'link':
            origin = linked
        else:
            mirror = linked
    elif unsafe == 'destination-file':
        origin = origin.parent / 'file'
        origin.write_bytes(b'SYNTHETIC FILE')
    elif unsafe == 'nested-git':
        (origin / 'nested/.git').mkdir(parents=True)
    elif unsafe == 'payload-link':
        (origin / 'unsafe').symlink_to(key)
    else:
        os.mkfifo(origin / 'fifo')
    before = _snapshot(source.parent)
    result = _invoke((source, mirror, origin, key), '--yes')
    assert result.exit_code == 2, result.output
    assert _snapshot(source.parent) == before


@pytest.mark.parametrize('failure', ['write', 'memory', 'stage-verify', 'move', 'interrupt'])
def test_failed_restore_recovers_old_complete_plaintext(vaults, monkeypatch, failure) -> None:
    """Injection before and during publication never claims success or destroys old payload."""
    mirror_before = _snapshot(vaults[1])
    old = {p.relative_to(vaults[2]).as_posix(): p.read_bytes() for p in vaults[2].rglob('*') if p.is_file()}
    if failure in {'write', 'memory'}:

        def fail(*args, **kwargs):
            if failure == 'memory':
                raise MemoryError('SYNTHETIC PRIVATE ERROR')
            raise OSError(errno.ENOSPC, 'SYNTHETIC PRIVATE ERROR')

        monkeypatch.setattr(backup, '_write_token', fail)
    elif failure == 'stage-verify':

        def fail(*args, **kwargs):
            raise _OperationalError('SYNTHETIC PRIVATE ERROR')

        monkeypatch.setattr(restore, '_verify_stage', fail)
    else:
        original = tx._move
        count = 0

        def fail(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                if failure == 'interrupt':
                    raise KeyboardInterrupt
                raise PermissionError('SYNTHETIC PRIVATE ERROR')
            return original(*args, **kwargs)

        monkeypatch.setattr(tx, '_move', fail)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == (130 if failure == 'interrupt' else 1), result.output
    assert 'published' not in result.output and 'SYNTHETIC PRIVATE ERROR' not in result.output
    assert {p.relative_to(vaults[2]).as_posix(): p.read_bytes() for p in vaults[2].rglob('*') if p.is_file()} == old
    assert _snapshot(vaults[1]) == mirror_before
    assert not list(vaults[0].parent.glob('*.lock'))


@pytest.mark.parametrize('change', ['source', 'key', 'destination', 'late-source', 'stage-content', 'stage-extra'])
def test_changes_after_planning_or_staging_block_publication(vaults, monkeypatch, change) -> None:
    """Late changes cannot authorize a mixed snapshot; user edits are retained."""
    _, mirror, origin, key = vaults
    plan = restore._plan_restore(origin, mirror, key)
    before = {p.name: p.read_bytes() for p in origin.iterdir() if p.is_file()}
    if change == 'source':
        next((mirror / '.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC CHANGE')
    elif change == 'key':
        os.utime(key, ns=(key.stat().st_atime_ns, key.stat().st_mtime_ns + 1000000000))
    elif change == 'destination':
        (origin / 'user-edit').write_bytes(b'SYNTHETIC USER EDIT')
    elif change == 'late-source':
        original = tx._checkpoint

        def checkpoint(workspace, journal):
            original(workspace, journal)
            if journal['phase'] == 'ready':
                next((mirror / '.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC LATE CHANGE')

        monkeypatch.setattr(tx, '_checkpoint', checkpoint)
    else:
        original = restore._build_restore

        def build(plan, stage, unsupported):
            original(plan, stage, unsupported)
            (stage / ('note.md' if change == 'stage-content' else 'unexpected')).write_bytes(b'SYNTHETIC WRONG')

        monkeypatch.setattr(restore, '_build_restore', build)
    with pytest.raises(_OperationalError):
        restore._publish_restore(plan, yes=True, non_interactive=True)
    for name, data in before.items():
        assert (origin / name).read_bytes() == data
    if change == 'destination':
        assert (origin / 'user-edit').read_bytes() == b'SYNTHETIC USER EDIT'


@pytest.mark.parametrize('boundary', ['ready', 'old-moved', 'new-moved'])
def test_process_death_blocks_then_explicitly_recovers_and_retries(vaults, boundary) -> None:
    """Durable restore checkpoints recover old plaintext before a new complete retry."""
    script = """
import os, sys
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
boundary = sys.argv[1]
checkpoint, move = tx._checkpoint, tx._move
count = 0
def stop_checkpoint(workspace, journal):
    checkpoint(workspace, journal)
    if boundary == 'ready' and journal['phase'] == 'ready':
        os._exit(77)
def stop_move(*args, **kwargs):
    global count
    move(*args, **kwargs)
    count += 1
    if (boundary == 'old-moved' and count == 1) or (boundary == 'new-moved' and count == 4):
        os._exit(77)
tx._checkpoint, tx._move = stop_checkpoint, stop_move
cli(args=sys.argv[2:], prog_name='obfuscidian')
"""
    before_mirror = _snapshot(vaults[1])
    process = subprocess.run(
        [sys.executable, '-c', script, boundary, *_args(vaults), '--yes'], capture_output=True, text=True, timeout=30, check=False
    )
    assert process.returncode == 77, process.stdout + process.stderr
    before = _snapshot(vaults[0].parent)
    for options in (['--yes'], ['--dry-run'], ['--recover']):
        result = _invoke(vaults, *options)
        assert result.exit_code == 1, result.output
        assert _snapshot(vaults[0].parent) == before
    result = _invoke(vaults, '--recover', '--yes')
    assert result.exit_code == 0, result.output
    assert 'Previous state recovered; replanning' in result.output
    assert (vaults[2] / 'nested/binary.bin').read_bytes() == bytes(range(256))
    assert _snapshot(vaults[1]) == before_mirror
    assert (_rollback(vaults) / 'old.md').read_bytes() == b'SYNTHETIC OLD PLAINTEXT'


@pytest.mark.parametrize('limit', ['space', 'access', 'names', 'length'])
def test_resource_or_target_failures_before_artifacts(vaults, monkeypatch, limit) -> None:
    """Failed estimates/permissions and target naming/length constraints cannot create plaintext."""
    before = _snapshot(vaults[0].parent)
    if limit == 'space':
        original = tx.shutil.disk_usage
        monkeypatch.setattr(tx.shutil, 'disk_usage', lambda path: original(path)._replace(free=0))
    elif limit == 'access':
        monkeypatch.setattr(tx.os, 'access', lambda *args: False)
    else:
        rules = backup._mirror_rules(vaults[2])
        monkeypatch.setattr(
            backup,
            '_mirror_rules',
            lambda path: replace(
                rules, component_limit=2 if limit == 'names' else 255, path_limit=5 if limit == 'length' else rules.path_limit
            ),
        )
    result = _invoke(vaults, '--yes')
    assert result.exit_code in {1, 2}, result.output
    assert _snapshot(vaults[0].parent) == before


def test_timestamp_limit_warns_without_losing_required_content(vaults) -> None:
    """Out-of-range authenticated timestamps warn rather than skipping required bytes."""
    verified = _verified(vaults)
    updated = replace(verified.manifest, files=tuple(replace(r, mtime_ns=10**100) for r in verified.manifest.files))
    fernet, _ = keys._load_key(vaults[3])
    (vaults[1] / '.obfuscidian/manifest.obf').write_bytes(manifest._encrypt_manifest(updated, fernet))
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0, result.output
    assert 'Some modification times could not be preserved' in result.output
    assert (vaults[2] / 'nested/binary.bin').read_bytes() == bytes(range(256))


def test_preserve_configuration_absence_and_environment_resolution(vaults, monkeypatch) -> None:
    """Preserving absent configuration skips backup settings; use environment path and alias selectors."""
    (vaults[2] / '.obsidian/settings.json').unlink()
    (vaults[2] / '.obsidian').rmdir()
    monkeypatch.setenv(const.ENV_ORIGIN, str(vaults[2]))
    monkeypatch.setenv(const.ENV_MIRROR, str(vaults[1]))
    monkeypatch.setenv(const.ENV_KEY_ALIAS, 'synthetic')
    monkeypatch.setenv(const.ENV_KEY_DIR, str(vaults[3].parent))
    result = CliRunner().invoke(cli, ['unshroud', 'fresh', '--yes', '--preserve-config', '--non-interactive'])
    assert result.exit_code == 0, result.output
    assert not (vaults[2] / '.obsidian').exists()
    invalid = _invoke(vaults, '--origin', str(vaults[2].parent / 'missing/child'), '--yes')
    assert invalid.exit_code == 2


@pytest.mark.parametrize(
    'arguments',
    [
        [],
        ['merge'],
        ['fresh', '--recover', '--dry-run'],
        ['fresh', '--exclude', '*.tmp'],
        ['fresh', '--gitdir', 'x'],
        ['fresh', '--log-file', 'x'],
        ['fresh', '--log-paths'],
        ['fresh', '--key', 'x', '--alias', 'x'],
    ],
)
def test_unavailable_modes_and_invalid_options_never_write(vaults, arguments) -> None:
    """Do not expose Git merge restore, exclusions or logging as silent no-ops."""
    before = _snapshot(vaults[0].parent)
    result = CliRunner().invoke(cli, ['unshroud', *arguments])
    assert result.exit_code == 2, result.output
    assert _snapshot(vaults[0].parent) == before


def _block_restore(vaults, monkeypatch) -> None:
    """Leave a recorded interrupted replacement whose old payload remains retained."""
    original = tx._move
    count = 0

    def fail_move(*args, **kwargs):
        nonlocal count
        count += 1
        if count > 1:
            raise PermissionError('SYNTHETIC BLOCKED RECOVERY')
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(tx, '_move', fail_move)
        result = _invoke(vaults, '--yes')
        assert result.exit_code == 1 and 'explicit recovery' in result.output


@pytest.mark.parametrize('change', ['wrong-key', 'corrupt-source', 'rollback', 'stage', 'settings-choice'])
def test_recovery_refuses_unverifiable_source_or_user_modified_artifacts(vaults, monkeypatch, change) -> None:
    """Explicit consent never bypasses complete source validation or conservative recovery evidence."""
    _block_restore(vaults, monkeypatch)
    source, mirror, origin, key = vaults
    options = []
    if change == 'wrong-key':
        key = source.parent / 'obfuscidian-wrong.key'
        keys._generate_key(key)
        vaults = source, mirror, origin, key
    elif change == 'corrupt-source':
        next((mirror / '.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC CORRUPTION')
    elif change == 'settings-choice':
        options = ['--preserve-config']
    else:
        workspace = next(
            p for p in source.parent.glob(const.TRANSACTION_PREFIX + '*') if p.is_dir() and (p / 'rollback/.obsidian').exists()
        )
        target = workspace / ('rollback/.obsidian/settings.json' if change == 'rollback' else 'stage/note.md')
        target.write_bytes(b'SYNTHETIC USER MODIFICATION')
    before = _snapshot(source.parent)
    result = _invoke(vaults, '--recover', '--yes', *options)
    assert result.exit_code == 1, result.output
    assert _snapshot(source.parent) == before


@pytest.mark.parametrize('alias', ['.GIT', 'nested/.GIT', '.GITIGNORE', '.OBSIDIAN'])
def test_existing_control_aliases_are_never_destroyed(vaults, alias) -> None:
    """Potential protected metadata aliases fail closed rather than moving them to rollback."""
    source, _, origin, _ = vaults
    target = origin / alias
    # Rename real controls to exercise their actual spelling even on insensitive volumes.
    if alias == '.GITIGNORE':
        (origin / '.gitignore').rename(target)
    elif alias == '.OBSIDIAN':
        (origin / '.obsidian').rename(target)
    else:
        target.parent.mkdir(exist_ok=True)
        target.mkdir()
        (target / 'sentinel').write_bytes(b'SYNTHETIC CONTROL')
    before = _snapshot(source.parent)
    result = _invoke(vaults, '--yes', '--preserve-config')
    assert result.exit_code == 2, result.output
    assert _snapshot(source.parent) == before


def test_skipped_configuration_is_still_completely_authenticated(vaults, monkeypatch) -> None:
    """A corrupt skipped-settings object refuses before consent, ownership and plaintext staging."""
    verified = _verified(vaults)
    settings = next(r for r in verified.manifest.files if r.path.startswith('.obsidian/'))
    (vaults[1] / '.obfuscidian/objects' / f'{settings.object_id}.obf').write_bytes(b'SYNTHETIC CORRUPTION')
    before = _snapshot(vaults[0].parent)

    def forbidden(*args, **kwargs):
        pytest.fail('Corrupt input must fail before confirmation, ownership or staging')

    monkeypatch.setattr(tx, '_confirm_action', forbidden)
    monkeypatch.setattr(tx, '_lock_descriptor', forbidden)
    monkeypatch.setattr(restore, '_build_restore', forbidden)
    result = _invoke(vaults, '--yes', '--preserve-config')
    assert result.exit_code == 1, result.output
    assert _snapshot(vaults[0].parent) == before


def test_restore_verbose_escapes_names_and_never_discloses_contents(vaults) -> None:
    """Only explicit verbose paths reveal names; all terminal controls remain escaped."""
    source, mirror, _, key = vaults
    (source / 'SYNTHETIC\x1b\nNAME.md').write_bytes(b'SYNTHETIC PRIVATE CONTENT')
    backup._publish_backup(backup._plan_fresh(source, mirror, key), non_interactive=True)
    result = _invoke(vaults, '--yes', '--verbose')
    assert result.exit_code == 0, result.output
    assert '\\x1b\\nNAME.md' in result.output and '\x1b' not in result.output
    assert 'SYNTHETIC PRIVATE CONTENT' not in result.output
    assert key.read_bytes().decode() not in result.output
    assert 'Rollback location:' in result.output


def test_destination_inside_repository_keeps_plaintext_recovery_outside_git(vaults) -> None:
    """Restore into a nested vault without exposing plaintext staging/rollback to routine commits."""
    source, _, _, _ = vaults
    repository = source.parent / 'destination-repository'
    subprocess.run(['git', 'init', '-q', str(repository)], check=True, capture_output=True)
    origin = repository / 'vault'
    origin.mkdir()
    (origin / 'old.md').write_bytes(b'SYNTHETIC OLD PLAINTEXT')
    vaults = vaults[:2] + (origin, vaults[3])
    git_before = _snapshot(repository / '.git')
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0, result.output
    assert _rollback(vaults).parent.parent == source.parent
    assert _snapshot(repository / '.git') == git_before
    assert not list(repository.glob(const.TRANSACTION_PREFIX + '*'))


def test_timestamp_operation_failure_warns_and_keeps_bytes(vaults, monkeypatch) -> None:
    """Unsupported filesystem timestamp operations report a warning but exact bytes remain required."""

    def unsupported(*args, **kwargs):
        raise OSError(errno.ENOTSUP, 'SYNTHETIC UNSUPPORTED TIME')

    monkeypatch.setattr(restore.os, 'utime', unsupported)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0, result.output
    assert 'Some modification times could not be preserved' in result.output
    assert (vaults[2] / 'nested/binary.bin').read_bytes() == bytes(range(256))

# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_merge_backup
:Synopsis:          Synthetic additive backup, stable ciphertext and no-write safety
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import backup, crypto, keys, manifest
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from tests.integration import test_fresh_backup as fresh

pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Merge mutation fails closed pending native platform hardening.')
vaults = fresh.vaults


def _args(vaults: tuple[Path, Path, Path]) -> list[str]:
    """Select additive merge using absolute synthetic locations."""
    source, mirror, key = vaults
    return ['shroud', 'merge', '--origin', str(source), '--mirror', str(mirror), '--key', str(key), '--non-interactive']


def _invoke(vaults: tuple[Path, Path, Path], *options: str):
    """Invoke sequential Click operations without implicit consent."""
    return CliRunner().invoke(cli, _args(vaults) + list(options))


def _first(vaults: tuple[Path, Path, Path]) -> manifest._VerifiedMirror:
    """Initialize a new merge mirror with no replacement prompt or retained workspace."""
    before = fresh._snapshot(vaults[0])
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    assert 'snapshot published' in result.output and 'recovery data removed' in result.output
    assert fresh._snapshot(vaults[0]) == before
    assert fresh._workspaces(vaults) == []
    return fresh._verified(vaults)


def _tokens(vaults: tuple[Path, Path, Path]) -> dict[str, bytes]:
    """Map authenticated logical names to exact opaque ciphertext bytes."""
    return {
        record.path: (vaults[1] / '.obfuscidian/objects' / f'{record.object_id}.obf').read_bytes()
        for record in fresh._verified(vaults).manifest.files
    }


@pytest.mark.parametrize('missing', [False, True])
def test_initialize_merge_preserves_source_controls_and_all_bytes(vaults, missing) -> None:
    """An empty or absent mirror initializes with binary/hidden/config/empty-directory fidelity."""
    if missing:
        vaults = vaults[0], vaults[1].parent / 'absent-mirror', vaults[2]
    else:
        controls = {name: fresh._snapshot(vaults[1] / name) for name in ('.git', '.gitignore')}
    checked = _first(vaults)
    assert fresh._payload(vaults)['nested/attachment.bin'] == bytes(range(256))
    assert fresh._payload(vaults)['nested/zero.bin'] == b''
    assert '.obsidian/settings.json' in fresh._payload(vaults)
    assert 'nested/empty' in {record.path for record in checked.manifest.directories}
    if not missing:
        assert {name: fresh._snapshot(vaults[1] / name) for name in controls} == controls


def test_add_edit_delete_rename_exclude_retains_exact_historic_content(vaults) -> None:
    """Retain deleted/renamed/excluded records and empty directories, while fresh later drops them."""
    old = _first(vaults)
    old_payload, old_tokens = fresh._payload(vaults), _tokens(vaults)
    source, mirror, key = vaults
    old_files = {record.path: record for record in old.manifest.files}
    (source / 'nested/attachment.bin').unlink()
    (source / 'nested/unicode-\u2603.md').rename(source / 'renamed.md')
    (source / 'nested/empty').rmdir()
    (source / 'nested/zero.bin').unlink()
    (source / 'note.md').write_bytes(b'SYNTHETIC CHANGED\x00\xff')
    (source / 'new.bin').write_bytes(bytes(reversed(range(256))))
    (source / '.obsidian/settings.json').write_bytes(b'SYNTHETIC EXCLUDED CHANGE')
    (source / '.obsidian/new.json').write_bytes(b'SYNTHETIC NEVER BACKED UP')
    before_source = fresh._snapshot(source)
    result = _invoke(vaults, '--yes', '--exclude', '.obsidian/')
    assert result.exit_code == 0, result.output
    new = fresh._verified(vaults)
    new_files = {record.path: record for record in new.manifest.files}
    payload = fresh._payload(vaults)
    assert payload['note.md'] == b'SYNTHETIC CHANGED\x00\xff'
    assert payload['renamed.md'] == old_payload['nested/unicode-\u2603.md']
    assert '.obsidian/new.json' not in payload
    assert new.manifest.vault_id == old.manifest.vault_id
    assert new.manifest.snapshot_id != old.manifest.snapshot_id
    assert '2 new, 1 changed, 0 metadata-only, 1 unchanged, 4 retained' in result.output
    assert new_files['note.md'].object_id == old_files['note.md'].object_id
    assert new_files['renamed.md'].object_id not in {record.object_id for record in old_files.values()}
    assert _tokens(vaults)['renamed.md'] != old_tokens['nested/unicode-\u2603.md']
    for name, record in old_files.items():
        if name != 'note.md':
            assert payload[name] == old_payload[name]
            assert _tokens(vaults)[name] == old_tokens[name]
            assert new_files[name] == record
    assert {record.path for record in new.manifest.directories} >= {record.path for record in old.manifest.directories}
    assert fresh._snapshot(source) == before_source
    assert fresh._workspaces(vaults) == []
    assert str(source.parent) not in result.output and key.read_bytes().decode() not in result.output
    # Complete authenticated reads prove that historic paths remain reconstructible;
    # no restore command is introduced by this thread.
    fresh_result = fresh._invoke(vaults, '--yes', '--exclude', '.obsidian/')
    assert fresh_result.exit_code == 0, fresh_result.output
    final = fresh._payload(vaults)
    for name in ('nested/attachment.bin', 'nested/unicode-\u2603.md', 'nested/zero.bin', '.obsidian/settings.json'):
        assert name not in final
    assert 'nested/empty' not in {record.path for record in fresh._verified(vaults).manifest.directories}
    assert len(fresh._workspaces(vaults)) == 1


@pytest.mark.parametrize('change', ['file-mtime', 'directory-mtime', 'new-file'])
def test_metadata_only_and_additions_need_no_confirmation(vaults, change) -> None:
    """Metadata changes/new files change the snapshot but preserve all prior IDs and tokens."""
    old = _first(vaults)
    old_tokens = _tokens(vaults)
    if change == 'new-file':
        (vaults[0] / 'new.md').write_bytes(b'SYNTHETIC ADDITION')
    else:
        path = vaults[0] / ('note.md' if change == 'file-mtime' else 'nested/empty')
        info = path.stat()
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000_000))
    result = _invoke(vaults)
    assert result.exit_code == 0, result.output
    new = fresh._verified(vaults)
    assert new.manifest.snapshot_id != old.manifest.snapshot_id
    assert new.manifest.vault_id == old.manifest.vault_id
    for name, token in old_tokens.items():
        assert _tokens(vaults)[name] == token
    if change == 'file-mtime':
        assert '1 metadata-only' in result.output
    elif change == 'directory-mtime':
        assert new.manifest.directories != old.manifest.directories
    assert fresh._workspaces(vaults) == []


@pytest.mark.parametrize('historic', [False, True])
def test_noop_preserves_sorted_hashes_mtimes_ids_and_creates_nothing(vaults, monkeypatch, historic) -> None:
    """No-op includes stale-only/excluded unions and never allocates tokens, IDs, time or ownership."""
    _first(vaults)
    exclusions = ()
    if historic:
        (vaults[0] / 'note.md').unlink()
        exclusions = ('--exclude', 'nested/')
        assert _invoke(vaults, *exclusions).exit_code == 0
    old = fresh._verified(vaults)
    before = fresh._snapshot(vaults[0].parent)

    def forbidden(*args, **kwargs):
        pytest.fail('No-op cannot create randomness, timestamps, ciphertext, consent or write artifacts.')

    monkeypatch.setattr(crypto, '_new_id', forbidden)
    monkeypatch.setattr(crypto, '_encrypt_bytes', forbidden)
    monkeypatch.setattr(backup, 'datetime', type('ForbiddenTime', (), {'now': forbidden}))
    monkeypatch.setattr(tx, '_lock_descriptor', forbidden)
    monkeypatch.setattr(tx, '_confirm_action', forbidden)
    monkeypatch.setattr(backup, '_build_backup', forbidden)
    for _ in range(2):
        result = _invoke(vaults, *exclusions)
        assert result.exit_code == 0 and 'no-op' in result.output, result.output
        assert fresh._snapshot(vaults[0].parent) == before
        assert fresh._verified(vaults).manifest == old.manifest


@pytest.mark.parametrize('transition', ['file-to-dir', 'dir-to-file', 'ancestor-to-file', 'excluded-conflict'])
@pytest.mark.parametrize('dry_run', [False, True])
def test_type_conflicts_refuse_without_writes_and_explain_fresh(vaults, transition, dry_run) -> None:
    """Retained historic paths cannot be silently deleted to resolve type/ancestor conflicts."""
    old = _first(vaults)
    source = vaults[0]
    if transition in {'file-to-dir', 'excluded-conflict'}:
        (source / 'note.md').unlink()
        (source / 'note.md').mkdir()
        (source / 'note.md/child.md').write_bytes(b'SYNTHETIC CHILD')
    elif transition == 'dir-to-file':
        (source / 'nested/empty').rmdir()
        (source / 'nested/empty').write_bytes(b'SYNTHETIC FILE')
    else:
        shutil.rmtree(source / 'nested')
        (source / 'nested').write_bytes(b'SYNTHETIC ANCESTOR FILE')
    options = ['--yes'] + (['--dry-run'] if dry_run else [])
    if transition == 'excluded-conflict':
        options += ['--exclude', 'note.md/']
    before = fresh._snapshot(source.parent)
    result = _invoke(vaults, *options)
    if transition == 'excluded-conflict':
        # Exclusion prunes the new directory, so the old file is simply retained.
        assert result.exit_code == 0, result.output
        if not dry_run:
            assert 'no-op' in result.output
    else:
        assert result.exit_code == 2 and 'shroud fresh' in result.output, result.output
    assert fresh._snapshot(source.parent) == before
    assert fresh._verified(vaults).manifest == old.manifest
    if transition != 'excluded-conflict' and not dry_run:
        fresh_result = fresh._invoke(vaults, '--yes')
        assert fresh_result.exit_code == 0, fresh_result.output


@pytest.mark.parametrize('response', ['n\n', '', 'y\n'])
def test_content_confirmation_only_and_refusal_has_no_writes(vaults, monkeypatch, response) -> None:
    """Merge prompts only for changing existing file content; decline/EOF preserve all observations."""
    _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC NEW CONTENT')
    before = fresh._snapshot(vaults[0].parent)
    no_consent = _invoke(vaults)
    assert no_consent.exit_code == 1 and 'confirmation is required' in no_consent.output
    assert fresh._snapshot(vaults[0].parent) == before
    monkeypatch.setattr(fresh.cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    args = _args(vaults)
    args.remove('--non-interactive')
    result = CliRunner().invoke(cli, args, input=response)
    assert 'Replace existing file contents?' in result.output
    assert result.exit_code == (0 if response == 'y\n' else 1), result.output
    if response != 'y\n':
        assert fresh._snapshot(vaults[0].parent) == before


@pytest.mark.parametrize('kind', ['deleted', 'excluded'])
def test_corrupt_retained_ciphertext_is_not_skipped(vaults, kind) -> None:
    """Even absent/excluded objects must authenticate before any merge artifacts."""
    old = _first(vaults)
    note = next(record for record in old.manifest.files if record.path == 'note.md')
    if kind == 'deleted':
        (vaults[0] / 'note.md').unlink()
    (vaults[1] / '.obfuscidian/objects' / f'{note.object_id}.obf').write_bytes(b'SYNTHETIC CORRUPTION')
    before = fresh._snapshot(vaults[0].parent)
    result = _invoke(vaults, '--yes', '--exclude', 'note.md')
    assert result.exit_code == 1 and fresh._snapshot(vaults[0].parent) == before


@pytest.mark.parametrize('invalid', ['missing', 'malformed', 'wrong'])
def test_explicit_invalid_key_never_falls_back_or_prompts(vaults, monkeypatch, invalid) -> None:
    """A valid environment alias never overrides an explicit invalid selected key."""
    _first(vaults)
    source, mirror, key = vaults
    monkeypatch.setenv(const.ENV_KEY_ALIAS, 'synthetic')
    monkeypatch.setenv(const.ENV_KEY_DIR, str(key.parent))
    bad = key.parent / 'obfuscidian-invalid.key'
    if invalid == 'malformed':
        bad.write_bytes(b'SYNTHETIC INVALID')
    elif invalid == 'wrong':
        keys._generate_key(bad)
    before = fresh._snapshot(source.parent)
    result = _invoke((source, mirror, bad), '--yes')
    assert result.exit_code in {1, 2}, result.output
    assert 'Key alias:' not in result.output
    assert fresh._snapshot(source.parent) == before
    if bad.exists():
        assert bad.read_bytes().decode() not in result.output


def test_retained_tokens_count_toward_staging_space(vaults, monkeypatch) -> None:
    """Excluded historic ciphertext still needs space in the complete staged union."""
    checked = _first(vaults)
    all_plan = backup._plan_merge(*vaults)
    retained_plan = backup._plan_merge(*vaults, exclusions=('**',))
    assert retained_plan.source.file_count == 0
    assert retained_plan.no_op
    # Force a logical metadata update while all file objects remain historic.
    (vaults[0] / 'empty-new').mkdir()
    retained_plan = backup._plan_merge(*vaults, exclusions=('**/*.*', '.hidden'))
    assert retained_plan.changes.retained == checked.file_count
    assert retained_plan.transaction.required_bytes >= all_plan.previous.encrypted_bytes
    original = tx.shutil.disk_usage
    monkeypatch.setattr(tx.shutil, 'disk_usage', lambda path: original(path)._replace(free=const.TRANSACTION_RESERVE_BYTES))
    before = fresh._snapshot(vaults[0].parent)
    result = _invoke(vaults, '--exclude', '**/*.*', '--exclude', '.hidden')
    assert result.exit_code == 1 and fresh._snapshot(vaults[0].parent) == before


def test_success_cleans_only_own_workspace_and_preserves_fresh_rollback(vaults) -> None:
    """Successful merge never prunes older retained fresh snapshots or unrelated private workspaces."""
    fresh._first(vaults)
    older = {path: fresh._snapshot(path) for path in fresh._workspaces(vaults)}
    unrelated = vaults[0].parent / (const.TRANSACTION_PREFIX + 'f' * 32)
    unrelated.mkdir()
    (unrelated / 'sentinel').write_bytes(b'SYNTHETIC UNRELATED')
    older[unrelated] = fresh._snapshot(unrelated)
    (vaults[0] / 'new.md').write_bytes(b'SYNTHETIC NEW')
    result = _invoke(vaults)
    assert result.exit_code == 0 and 'recovery data removed' in result.output, result.output
    assert set(fresh._workspaces(vaults)) == set(older)
    assert {path: fresh._snapshot(path) for path in older} == older


@pytest.mark.parametrize('change', ['unexpected', 'rollback', 'link', 'journal', 'malformed-journal', 'unlink-failure'])
def test_cleanup_preserves_uncertain_data_and_published_snapshot(vaults, monkeypatch, change) -> None:
    """Changed recovery artifacts and cleanup I/O failure cannot reverse a successful publication."""
    old = _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC PUBLISHED CHANGE')
    cleanup = tx._cleanup_published
    retained = []

    def mutate(plan, workspace, journal):
        if change == 'unexpected':
            target = workspace / 'user-data'
            target.write_bytes(b'SYNTHETIC USER DATA')
        elif change == 'rollback':
            target = next((workspace / 'rollback/.obfuscidian/objects').iterdir())
            target.write_bytes(b'SYNTHETIC USER CHANGE')
        elif change == 'link':
            target = workspace / 'user-link'
            target.symlink_to(vaults[0] / 'note.md')
        elif change in {'journal', 'malformed-journal'}:
            target = workspace / 'journal.json'
            target.write_bytes(b'{' if change == 'malformed-journal' else b'{"synthetic":true}')
        else:
            target = workspace / 'journal.json'

            def fail(*args, **kwargs):
                raise PermissionError('SYNTHETIC PRIVATE CLEANUP FAILURE')

            monkeypatch.setattr(tx, '_remove_captured', fail)
        retained.append((target, fresh._snapshot(workspace)))
        cleanup(plan, workspace, journal)

    monkeypatch.setattr(tx, '_cleanup_published', mutate)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0 and 'cleanup incomplete' in result.output, result.output
    assert 'SYNTHETIC' not in result.output and str(vaults[0].parent) not in result.output
    assert fresh._payload(vaults)['note.md'] == b'SYNTHETIC PUBLISHED CHANGE'
    assert fresh._verified(vaults).manifest.snapshot_id != old.manifest.snapshot_id
    assert fresh._snapshot(fresh._workspaces(vaults)[0]) == retained[0][1]
    assert fresh._workspaces(vaults)


@pytest.fixture
def shared_merge(monkeypatch):
    """Exercise existing safety scenarios through merge CLI and the additive planner."""
    monkeypatch.setattr(fresh, '_args', _args)
    monkeypatch.setattr(backup, '_plan_fresh', backup._plan_merge)


@pytest.mark.parametrize('corruption', ['wrong-key', 'manifest', 'object', 'missing', 'extra', 'unsupported'])
@pytest.mark.parametrize('dry_run', [False, True])
def test_shared_authentication_safety(vaults, shared_merge, corruption, dry_run) -> None:
    """Run the whole-mirror corruption matrix through merge and merge dry run."""
    fresh.test_existing_mirror_must_authenticate_before_artifacts(vaults, corruption, dry_run)


@pytest.mark.parametrize(
    'unsafe', ['unmanaged', 'overlap', 'link', 'key-inside', 'key-hardlink', 'missing-parent', 'source-link']
)
def test_shared_location_safety(vaults, shared_merge, unsafe) -> None:
    """The additive command obeys the shared location and key-custody refusals."""
    fresh.test_unsafe_locations_fail_without_writes(vaults, unsafe)


@pytest.mark.parametrize('change', ['edit', 'add', 'delete', 'replace-parent', 'late-edit'])
def test_shared_source_stability(vaults, shared_merge, monkeypatch, change) -> None:
    """Detected source changes including the ready checkpoint never publish the additive proposal."""
    fresh.test_detected_source_changes_never_publish(vaults, monkeypatch, change)


@pytest.mark.parametrize('failure', ['write', 'encrypt', 'verify', 'move', 'interrupt'])
def test_shared_failure_recovery(vaults, shared_merge, monkeypatch, failure) -> None:
    """Normal merge failures and interrupts restore the previous authenticated complete snapshot."""
    fresh.test_normal_failures_recover_complete_old_snapshot(vaults, monkeypatch, failure)


@pytest.mark.parametrize('boundary', ['ready', 'old-moved', 'new-moved'])
def test_shared_process_death_recovery(vaults, shared_merge, boundary) -> None:
    """Abrupt process death blocks writes until explicit merge recovery/retry."""
    fresh.test_process_death_and_cli_recovery(vaults, boundary)


def test_shared_pending_and_consent(vaults, shared_merge, monkeypatch) -> None:
    """Merge recovery requires consent and dry run never repairs pending state."""
    fresh.test_pending_blocks_dryrun_and_write_recovery_requires_consent_then_retries(vaults, monkeypatch)


def test_shared_recovery_wrong_key(vaults, shared_merge, monkeypatch) -> None:
    """Wrong selected keys cannot recover retained merge artifacts."""
    fresh.test_wrong_key_cannot_mutate_pending_recovery(vaults, monkeypatch)


def test_shared_recovery_user_changes(vaults, shared_merge, monkeypatch) -> None:
    """Explicit consent cannot bypass changed retained bytes."""
    fresh.test_recovery_refuses_user_modified_retained_bytes(vaults, monkeypatch)


@pytest.mark.parametrize('state', ['absent', 'empty', 'replacement', 'noop'])
def test_shared_dry_run(vaults, shared_merge, monkeypatch, state) -> None:
    """Merge dry run never prompts or creates ownership/staging even for replacement."""
    fresh.test_dry_run_never_writes_or_confirms(vaults, monkeypatch, state)


@pytest.mark.parametrize('limit', ['object', 'manifest', 'space'])
def test_shared_limits(vaults, shared_merge, monkeypatch, limit) -> None:
    """Resource failures occur during read-only preflight for merge too."""
    fresh.test_size_and_space_limits_fail_before_artifacts(vaults, monkeypatch, limit)


def test_changed_exclusions_reinclude_paths_with_stable_ids(vaults) -> None:
    """Exclusions preserve old bytes; removing them later updates the same path only with consent."""
    old = _first(vaults)
    old_file = next(record for record in old.manifest.files if record.path == '.obsidian/settings.json')
    token = _tokens(vaults)[old_file.path]
    (vaults[0] / old_file.path).write_bytes(b'SYNTHETIC REINCLUDED UPDATE')
    before = fresh._snapshot(vaults[0].parent)
    excluded = _invoke(vaults, '--exclude', '.obsidian/')
    assert excluded.exit_code == 0 and 'no-op' in excluded.output, excluded.output
    assert fresh._snapshot(vaults[0].parent) == before
    assert _tokens(vaults)[old_file.path] == token
    refused = _invoke(vaults)
    assert refused.exit_code == 1
    assert fresh._snapshot(vaults[0].parent) == before
    included = _invoke(vaults, '--yes')
    assert included.exit_code == 0, included.output
    checked = fresh._verified(vaults)
    record = next(record for record in checked.manifest.files if record.path == old_file.path)
    assert record.object_id == old_file.object_id
    assert _tokens(vaults)[old_file.path] != token
    assert fresh._payload(vaults)[old_file.path] == b'SYNTHETIC REINCLUDED UPDATE'


def test_empty_current_vault_retains_all_old_files_and_directories_without_writes(vaults) -> None:
    """Deleting every included entry is a no-op when merge retains the complete old logical snapshot."""
    old = _first(vaults)
    for path in vaults[0].iterdir():
        if path.name in {'.git', '.gitignore'}:
            continue
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    before = fresh._snapshot(vaults[0].parent)
    result = _invoke(vaults)
    assert result.exit_code == 0 and 'no-op' in result.output, result.output
    assert fresh._snapshot(vaults[0].parent) == before
    assert fresh._verified(vaults).manifest == old.manifest


def test_same_size_mtime_content_edit_requires_content_confirmation(vaults) -> None:
    """Hash comparison detects changed content even when size and mtime match the previous snapshot."""
    _first(vaults)
    target = vaults[0] / 'note.md'
    info = target.stat()
    data = target.read_bytes()
    target.write_bytes(b'X' * len(data))
    os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))
    before = fresh._snapshot(vaults[0].parent)
    result = _invoke(vaults)
    assert result.exit_code == 1 and '1 changed' in result.output, result.output
    assert fresh._snapshot(vaults[0].parent) == before
    assert _invoke(vaults, '--yes').exit_code == 0
    assert fresh._payload(vaults)['note.md'] == b'X' * len(data)


def test_cleanup_interrupt_never_rolls_back_published_snapshot(vaults, monkeypatch) -> None:
    """An interrupt after completion reports exit 130 and retains data without inverse publication."""
    _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC PUBLISHED BEFORE INTERRUPT')

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(tx, '_remove_captured', interrupt)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 130 and 'snapshot published' not in result.output, result.output
    assert fresh._payload(vaults)['note.md'] == b'SYNTHETIC PUBLISHED BEFORE INTERRUPT'
    assert fresh._workspaces(vaults)
    assert not list(vaults[0].parent.glob('*.lock'))


def test_cleanup_final_flush_failure_reports_actual_retention(vaults, monkeypatch) -> None:
    """Failed final directory flush warns about durability without claiming absent recovery data exists."""
    _first(vaults)
    (vaults[0] / 'note.md').write_bytes(b'SYNTHETIC DURABLE PUBLICATION')
    cleanup = tx._cleanup_published
    sync = tx.os.fsync
    active = []

    def checked_sync(descriptor):
        if active and not active[0].exists():
            raise OSError('SYNTHETIC FINAL CLEANUP FLUSH FAILURE')
        sync(descriptor)

    def checked_cleanup(plan, workspace, journal):
        active.append(workspace)
        cleanup(plan, workspace, journal)

    monkeypatch.setattr(tx.os, 'fsync', checked_sync)
    monkeypatch.setattr(tx, '_cleanup_published', checked_cleanup)
    result = _invoke(vaults, '--yes')
    assert result.exit_code == 0 and 'durability unconfirmed' in result.output, result.output
    assert 'recovery data retained' not in result.output
    assert fresh._workspaces(vaults) == []
    assert fresh._payload(vaults)['note.md'] == b'SYNTHETIC DURABLE PUBLICATION'

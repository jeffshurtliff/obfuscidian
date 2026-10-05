# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_merge_restore
:Synopsis:          Offline temporary Git merge restores and conservative failure cleanup
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import ast
import importlib
import os
import shlex
import stat
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import backup, git_restore, keys
from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from obfuscidian.errors import _ConfigurationError, _OperationalError

cli_module = importlib.import_module('obfuscidian.cli')
pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Git restore mutation requires POSIX private modes.')


def _git(root: Path, *args: str) -> bytes:
    """Run fixture Git with isolated global/system config and external hooks disabled."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    return subprocess.run(
        [
            'git',
            '-c',
            'core.hooksPath=' + os.devnull,
            '-c',
            'core.fsmonitor=false',
            '-c',
            'user.name=Synthetic Tester',
            '-c',
            'user.email=synthetic@example.invalid',
            '-C',
            str(root),
            *args,
        ],
        env=env,
        capture_output=True,
        check=True,
    ).stdout


def _commit(root: Path) -> None:
    """Create synthetic fixture history, never application restore commits."""
    _git(root, 'add', '--all')
    _git(root, 'commit', '-qm', 'Created synthetic fixture')


def _snapshot(root: Path) -> dict:
    """Capture origin content and controls, excluding shared worktree/ref additions."""
    entries = [p for p in root.rglob('*') if '.git' not in p.relative_to(root).parts]
    entries += [root / '.git' / n for n in ('HEAD', 'index', 'config')]
    return {
        p.relative_to(root).as_posix(): (
            p.lstat().st_ino,
            p.lstat().st_mode,
            p.lstat().st_mtime_ns,
            p.read_bytes() if p.is_file() else None,
        )
        for p in entries
        if p.exists()
    }


@pytest.fixture
def repositories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Build real temporary Git history and a synthetic encrypted backup."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path.resolve()
    origin, source, mirror, key, output = (root / n for n in ('origin', 'source', 'mirror', 'synthetic.key', 'review'))
    origin.mkdir()
    _git(origin, 'init', '-qb', 'main')
    for name, data in {
        'note.md': b'SYNTHETIC BASE\n',
        'base-only.md': b'SYNTHETIC BASE ONLY',
        'nested/base.bin': b'BASE\x00',
        '.gitignore': b'ignored.bin\n',
        '.obsidian/settings.json': b'{"synthetic":"base"}',
    }.items():
        p = origin / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    _commit(origin)
    source.mkdir()
    for name, data in {
        'note.md': b'SYNTHETIC BACKUP\r\n',
        'nested/new.bin': bytes(range(256)),
        'ignored.bin': b'SYNTHETIC IGNORED',
        '.obsidian/settings.json': b'{"synthetic":"backup"}',
    }.items():
        p = source / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    (source / 'nested/empty').mkdir()
    keys._generate_key(key)
    backup._publish_backup(backup._plan_fresh(source, mirror, key), non_interactive=True)
    return origin, source, mirror, key, output


def _plan(repositories, **options):
    origin, _, mirror, key, output = repositories
    return git_restore._plan_merge(origin, mirror, key, worktree=output, branch='synthetic-review', **options)


def _invoke(repositories, *options):
    origin, _, mirror, key, output = repositories
    return CliRunner().invoke(
        cli,
        [
            'unshroud',
            'merge',
            '--origin',
            str(origin),
            '--mirror',
            str(mirror),
            '--key',
            str(key),
            '--worktree',
            str(output),
            '--branch',
            'synthetic-review',
            '--non-interactive',
            *options,
        ],
    )


@pytest.mark.parametrize('preserve', [False, True])
def test_additive_uncommitted_overlay_and_original_preservation(repositories, preserve):
    origin, source, mirror, key, output = repositories
    before = _snapshot(origin)
    head, index = _git(origin, 'rev-parse', 'HEAD'), _git(origin, 'ls-files', '--stage', '-z')
    plan = _plan(repositories, preserve_config=preserve)
    result = git_restore._publish_merge(plan)
    assert _snapshot(origin) == before
    assert _git(origin, 'rev-parse', 'HEAD') == head == _git(output, 'rev-parse', 'HEAD')
    assert _git(output, 'ls-files', '--stage', '-z') == index
    assert _git(output, 'diff', '--cached') == b''
    assert _git(output, 'symbolic-ref', '--short', 'HEAD') == b'obfuscidian/synthetic-review\n'
    assert (output / '.git').is_file()
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert (output / '.gitignore').read_bytes() == (origin / '.gitignore').read_bytes()
    assert (output / 'base-only.md').read_bytes() == (origin / 'base-only.md').read_bytes()
    assert (output / 'nested/base.bin').read_bytes() == (origin / 'nested/base.bin').read_bytes()
    assert (output / 'nested/empty').is_dir()
    for name in ('note.md', 'nested/new.bin', 'ignored.bin'):
        assert (output / name).read_bytes() == (source / name).read_bytes()
        assert stat.S_IMODE((output / name).stat().st_mode) == 0o600
    assert (output / 'nested/empty').stat().st_mtime_ns == (source / 'nested/empty').stat().st_mtime_ns
    assert (output / '.obsidian/settings.json').read_bytes() == (origin if preserve else source).joinpath(
        '.obsidian/settings.json'
    ).read_bytes()
    assert result.ignored == ('ignored.bin',)
    assert not result.retained
    assert not list(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
    assert b' M note.md' in _git(output, 'status', '--porcelain')


def test_cli_manual_review_privacy_and_ignored_files(repositories):
    result = _invoke(repositories)
    assert result.exit_code == 0, result.output
    assert 'unstaged and uncommitted' in result.output
    assert 'before they can be merged' in result.output
    assert 'manual review: 1' in result.output
    assert 'git add -f' in result.output
    assert str(repositories[0].parent) not in result.output
    assert 'ignored.bin' not in result.output


def test_dry_run_creates_no_plaintext_refs_worktrees_or_locks(repositories):
    origin, _, _, _, output = repositories
    before = _snapshot(origin)
    refs, worktrees = _git(origin, 'show-ref'), _git(origin, 'worktree', 'list', '--porcelain')
    children = set(output.parent.iterdir())
    result = _invoke(repositories, '--dry-run')
    assert result.exit_code == 0, result.output
    assert 'no plaintext' in result.output
    assert _snapshot(origin) == before
    assert _git(origin, 'show-ref') == refs
    assert _git(origin, 'worktree', 'list', '--porcelain') == worktrees
    assert set(output.parent.iterdir()) == children


@pytest.mark.parametrize('dirty', ['tracked', 'staged', 'untracked', 'ignored', 'empty-directory'])
def test_dirty_origin_refused_read_only(repositories, dirty):
    origin, _, _, _, output = repositories
    if dirty in ('tracked', 'staged'):
        (origin / 'note.md').write_bytes(b'SYNTHETIC USER EDIT')
        if dirty == 'staged':
            _git(origin, 'add', 'note.md')
    elif dirty == 'empty-directory':
        (origin / 'untracked-empty').mkdir()
    else:
        (origin / ('ignored.bin' if dirty == 'ignored' else 'untracked.md')).write_bytes(b'SYNTHETIC USER DATA')
    before = _snapshot(origin)
    result = _invoke(repositories)
    assert result.exit_code == 1, result.output
    assert _snapshot(origin) == before and not output.exists()


@pytest.mark.parametrize('pending', const.GIT_PENDING_NAMES)
def test_pending_git_operations_refused(repositories, pending):
    origin = repositories[0]
    (origin / '.git' / pending).write_bytes(b'SYNTHETIC PENDING')
    result = _invoke(repositories)
    assert result.exit_code == 1 and not repositories[-1].exists()


@pytest.mark.parametrize(
    'option,value',
    [
        ('--base-branch', 'missing'),
        ('--base-branch', 'HEAD'),
        ('--base-branch', '../main'),
        ('--base-branch', '-main'),
        ('--branch', '../unsafe'),
        ('--branch', 'bad..suffix'),
        ('--branch', 'obfuscidian/full'),
        ('--branch', ''),
        ('--branch', 'bad@{name'),
    ],
)
def test_invalid_base_and_branch_refused(repositories, option, value):
    result = _invoke(repositories, option, value)
    assert result.exit_code == 2, result.output
    assert not repositories[-1].exists()


def test_custom_base_with_different_origin_head_and_explicit_gitdir(repositories):
    origin, _, _, _, output = repositories
    _git(origin, 'checkout', '-qb', 'alternate')
    (origin / 'alternate-only.md').write_bytes(b'SYNTHETIC ALTERNATE')
    _commit(origin)
    alternate = _git(origin, 'rev-parse', 'HEAD')
    _git(origin, 'checkout', '-q', 'main')
    result = _invoke(repositories, '--base-branch', 'alternate', '--gitdir', str(origin / '.git'), '--verbose')
    assert result.exit_code == 0, result.output
    assert _git(output, 'rev-parse', 'HEAD') == alternate
    assert (output / 'alternate-only.md').read_bytes() == b'SYNTHETIC ALTERNATE'
    assert 'Manual command' in result.output and 'Ignored review entry' in result.output
    assert _git(origin, 'symbolic-ref', '--short', 'HEAD') == b'main\n'


@pytest.mark.parametrize(
    'failure',
    [
        'no-git',
        'not-repository',
        'bare',
        'no-commit',
        'subdirectory',
        'wrong-gitdir',
        'existing-output',
        'missing-parent',
        'origin-overlap',
        'mirror-overlap',
        'symlink-output',
    ],
)
def test_environment_and_output_validation_before_writes(repositories, tmp_path, monkeypatch, failure):
    origin, _, mirror, key, output = repositories
    opts = {}
    if failure == 'no-git':
        monkeypatch.setattr(git_restore.shutil, 'which', lambda _: None)
    elif failure in ('not-repository', 'bare', 'no-commit'):
        origin = tmp_path.resolve() / 'other'
        origin.mkdir()
        if failure != 'not-repository':
            _git(origin, 'init', '-q', *(['--bare'] if failure == 'bare' else []))
    elif failure == 'subdirectory':
        origin = origin / 'nested'
    elif failure == 'wrong-gitdir':
        opts['gitdir'] = tmp_path.resolve()
    elif failure == 'existing-output':
        output.mkdir()
        (output / 'user-data').write_bytes(b'SYNTHETIC KEEP')
    elif failure == 'missing-parent':
        output = output / 'absent'
    elif failure == 'origin-overlap':
        output = origin / 'review'
    elif failure == 'mirror-overlap':
        output = mirror / 'review'
    elif failure == 'symlink-output':
        output.symlink_to(origin, target_is_directory=True)
    with pytest.raises((_ConfigurationError, _OperationalError)):
        git_restore._plan_merge(origin, mirror, key, worktree=output, branch='synthetic', **opts)
    if failure == 'existing-output':
        assert (output / 'user-data').read_bytes() == b'SYNTHETIC KEEP'


@pytest.mark.parametrize('suffix', ['synthetic-review', 'synthetic-review/child', 'synthetic'])
def test_branch_collision_never_reset_or_deleted(repositories, suffix):
    origin = repositories[0]
    existing = 'obfuscidian/synthetic-review' if suffix != 'synthetic' else 'obfuscidian/synthetic/child'
    _git(origin, 'branch', existing)
    refs = _git(origin, 'show-ref')
    with pytest.raises((_ConfigurationError, _OperationalError)):
        git_restore._publish_merge(
            git_restore._plan_merge(
                origin,
                repositories[2],
                repositories[3],
                worktree=repositories[4],
                branch=suffix,
            )
        )
    assert _git(origin, 'show-ref') == refs and not repositories[4].exists()


@pytest.mark.parametrize('conflict', ['file-to-directory', 'directory-to-file', 'case', 'symlink', 'submodule', 'nested-git'])
def test_unsafe_base_layout_and_overlay_conflicts(repositories, conflict):
    origin = repositories[0]
    if conflict == 'file-to-directory':
        (origin / 'nested/base.bin').unlink()
        (origin / 'nested').rmdir()
        (origin / 'nested').write_bytes(b'SYNTHETIC FILE')
    elif conflict == 'directory-to-file':
        (origin / 'note.md').unlink()
        (origin / 'note.md').mkdir()
        (origin / 'note.md/base').write_bytes(b'SYNTHETIC FILE')
    elif conflict == 'case':
        _git(origin, 'mv', 'note.md', 'temporary-case-name')
        _git(origin, 'mv', 'temporary-case-name', 'NOTE.md')
    elif conflict == 'symlink':
        (origin / 'link').symlink_to('note.md')
    elif conflict == 'submodule':
        (origin / '.gitmodules').write_bytes(b'SYNTHETIC MODULE CONTROL')
    else:
        (origin / 'nested/.git').mkdir()
        (origin / 'nested/.git/user-data').write_bytes(b'SYNTHETIC KEEP')
        with pytest.raises(_ConfigurationError):
            _plan(repositories)
        return
    _commit(origin)
    with pytest.raises((_ConfigurationError, _OperationalError)):
        _plan(repositories)
    assert not repositories[4].exists()


def test_hook_filter_and_ambient_git_configuration_cannot_execute(repositories, monkeypatch):
    origin, _, _, _, output = repositories
    marker = origin.parent / 'must-not-run'
    hook = origin / '.git/hooks/post-checkout'
    hook.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
    hook.chmod(0o700)
    for name in ('reference-transaction', 'post-index-change'):
        (hook.parent / name).write_bytes(hook.read_bytes())
        (hook.parent / name).chmod(0o700)
    (origin / '.gitattributes').write_bytes(b'*.md filter=synthetic\n')
    _commit(origin)
    for selector in ('clean', 'smudge', 'process'):
        _git(origin, 'config', 'filter.synthetic.' + selector, 'touch "' + str(marker) + '"')
    _git(origin, 'config', 'filter.synthetic.required', 'true')
    _git(origin, 'config', 'core.fsmonitor', 'touch "' + str(marker) + '"')
    monkeypatch.setenv('GIT_DIR', '/SYNTHETIC-NONEXISTENT')
    monkeypatch.setenv('GIT_WORK_TREE', '/SYNTHETIC-NONEXISTENT')
    monkeypatch.setenv('GIT_INDEX_FILE', '/SYNTHETIC-NONEXISTENT')
    monkeypatch.setenv('GIT_CONFIG_COUNT', '1')
    monkeypatch.setenv('GIT_CONFIG_KEY_0', 'core.hooksPath')
    monkeypatch.setenv('GIT_CONFIG_VALUE_0', str(hook.parent))
    result = _invoke(repositories)
    assert result.exit_code == 0, result.output
    assert not marker.exists() and (output / 'note.md').read_bytes() == repositories[1].joinpath('note.md').read_bytes()


@pytest.mark.parametrize('phase', ['stage', 'branch', 'worktree', 'index', 'publication', 'after-publication'])
def test_failures_preserve_origin_and_conservatively_clean_owned_git(repositories, monkeypatch, phase):
    origin, _, _, _, output = repositories
    plan = _plan(repositories)
    before = _snapshot(origin)
    original_git, original_move = git_restore._git, tx._move
    fired = False

    def fail_git(executable, root, *args, **kw):
        nonlocal fired
        match = (
            (phase == 'branch' and args[0] == 'update-ref')
            or (phase == 'worktree' and args[:2] == ('worktree', 'add'))
            or (phase == 'index' and args[0] == 'read-tree')
            or (phase == 'after-publication' and args[:3] == ('ls-files', '--others', '--ignored'))
        )
        if match and not fired:
            fired = True
            raise _OperationalError('SYNTHETIC FAILURE')
        return original_git(executable, root, *args, **kw)

    def fail_move(source, destination, expected):
        nonlocal fired
        if phase == 'publication' and destination.parent == output and destination.name != '.gitignore' and not fired:
            fired = True
            raise OSError('SYNTHETIC PUBLICATION FAILURE')
        return original_move(source, destination, expected)

    monkeypatch.setattr(git_restore, '_git', fail_git)
    monkeypatch.setattr(tx, '_move', fail_move)
    if phase == 'stage':

        def fail_stage(*args):
            (args[1] / 'unknown-user-data').write_bytes(b'SYNTHETIC KEEP')
            raise OSError('SYNTHETIC STAGE FAILURE')

        monkeypatch.setattr(git_restore, '_stage_overlay', fail_stage)
    with pytest.raises(git_restore._MergeFailure) as caught:
        git_restore._publish_merge(plan)
    assert _snapshot(origin) == before
    if phase != 'index':
        assert not output.exists()
        assert b'obfuscidian/synthetic-review' not in _git(origin, 'show-ref')
    else:
        assert output.exists() and output in caught.value.retained
    if phase == 'stage':
        retained = list(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
        assert retained and retained[0] in caught.value.retained
        assert (retained[0] / 'unknown-user-data').read_bytes() == b'SYNTHETIC KEEP'


@pytest.mark.parametrize('edit', ['working-tree', 'index', 'branch', 'git-control', 'ignored', 'stage'])
def test_cleanup_preserves_later_user_edits(repositories, monkeypatch, edit):
    origin, _, _, _, output = repositories
    plan = _plan(repositories)
    original = git_restore._git
    fired = False

    def mutate_then_fail(executable, root, *args, **kw):
        nonlocal fired
        if args[:3] == ('ls-files', '--others', '--ignored') and not fired:
            fired = True
            if edit in ('working-tree', 'ignored'):
                (output / ('ignored.bin' if edit == 'ignored' else 'note.md')).write_bytes(b'SYNTHETIC LATER USER EDIT')
            elif edit == 'index':
                _git(output, 'add', 'note.md')
            elif edit == 'branch':
                _git(output, 'add', '--all')
                _git(output, 'commit', '-qm', 'Created synthetic later user commit')
            elif edit == 'git-control':
                (output / '.gitignore').write_bytes(b'SYNTHETIC LATER USER CONTROL')
            else:
                stage = next(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
                (stage / 'user-data').write_bytes(b'SYNTHETIC STAGING USER DATA')
            raise _OperationalError('SYNTHETIC FAILURE AFTER USER EDIT')
        return original(executable, root, *args, **kw)

    monkeypatch.setattr(git_restore, '_git', mutate_then_fail)
    with pytest.raises(git_restore._MergeFailure) as caught:
        git_restore._publish_merge(plan)
    if edit == 'stage':
        assert not output.exists()
        stage = next(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
        assert (stage / 'user-data').read_bytes() == b'SYNTHETIC STAGING USER DATA'
        assert stage in caught.value.retained
    else:
        assert output.exists() and output in caught.value.retained
        assert b'obfuscidian/synthetic-review' in _git(origin, 'show-ref')
        if edit in ('working-tree', 'ignored'):
            assert (output / ('ignored.bin' if edit == 'ignored' else 'note.md')).read_bytes() == b'SYNTHETIC LATER USER EDIT'


@pytest.mark.parametrize('change', ['origin', 'index', 'base', 'mirror', 'key', 'output'])
def test_changed_plan_fails_before_branch_creation(repositories, change):
    origin, _, mirror, key, output = repositories
    plan = _plan(repositories)
    if change == 'origin':
        (origin / 'note.md').write_bytes(b'SYNTHETIC CHANGE')
    elif change == 'index':
        (origin / 'note.md').write_bytes(b'SYNTHETIC CHANGE')
        _git(origin, 'add', 'note.md')
    elif change == 'base':
        _git(origin, 'checkout', '-qb', 'alternate')
        (origin / 'other').write_bytes(b'SYNTHETIC CHANGE')
        _commit(origin)
        _git(origin, 'branch', '-f', 'main', 'HEAD')
    elif change == 'mirror':
        next((mirror / '.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC CORRUPTION')
    elif change == 'key':
        key.write_bytes(b'SYNTHETIC CHANGED KEY')
    else:
        output.mkdir()
        (output / 'user-data').write_bytes(b'SYNTHETIC KEEP')
    with pytest.raises((_ConfigurationError, _OperationalError)):
        git_restore._publish_merge(plan)
    assert b'obfuscidian/synthetic-review' not in _git(origin, 'show-ref')


@pytest.mark.parametrize('corruption', ['key', 'manifest', 'object'])
def test_integrity_failure_creates_no_git_or_plaintext_artifacts(repositories, corruption):
    origin, _, mirror, key, output = repositories
    if corruption == 'key':
        key.unlink()
        keys._generate_key(key)
    else:
        path = (
            mirror / '.obfuscidian/manifest.obf'
            if corruption == 'manifest'
            else next((mirror / '.obfuscidian/objects').iterdir())
        )
        path.write_bytes(b'SYNTHETIC CORRUPTION')
    children, refs = set(output.parent.iterdir()), _git(origin, 'show-ref')
    result = _invoke(repositories)
    assert result.exit_code == 1, result.output
    assert set(output.parent.iterdir()) == children and _git(origin, 'show-ref') == refs


def test_merge_recover_is_explicitly_refused(repositories):
    result = _invoke(repositories, '--recover', '--yes')
    assert result.exit_code == 2 and 'manual' in result.output
    assert not repositories[4].exists()


def test_default_timestamp_branch_and_sibling_output(repositories):
    origin, _, mirror, key, _ = repositories
    plan = git_restore._plan_merge(origin, mirror, key)
    assert plan.branch.startswith('obfuscidian/restore-')
    assert plan.output.parent == origin.parent and plan.output.name.startswith('origin-restore-')
    result = git_restore._publish_merge(plan)
    assert result.output.exists()
    with pytest.raises(_ConfigurationError):
        git_restore._plan_merge(origin, mirror, key, worktree=plan.output, branch='other')


@pytest.mark.parametrize('present', [False, True])
def test_preserve_config_absence_and_base_only_settings(repositories, present):
    origin, _, _, _, output = repositories
    (origin / '.obsidian/settings.json').unlink()
    if present:
        (origin / '.obsidian/base-only.json').write_bytes(b'SYNTHETIC BASE CONFIG')
    else:
        (origin / '.obsidian').rmdir()
    _commit(origin)
    result = _invoke(repositories, '--preserve-config')
    assert result.exit_code == 0, result.output
    assert not (output / '.obsidian/settings.json').exists()
    assert (output / '.obsidian').exists() == present
    if present:
        assert (output / '.obsidian/base-only.json').read_bytes() == b'SYNTHETIC BASE CONFIG'


def test_gitlink_base_rejected_without_fetch_or_submodule_execution(repositories):
    origin = repositories[0]
    _git(
        origin, 'update-index', '--add', '--cacheinfo', '160000,' + _git(origin, 'rev-parse', 'HEAD').decode().strip() + ',module'
    )
    _git(origin, 'commit', '-qm', 'Created synthetic gitlink')
    with pytest.raises(_ConfigurationError):
        _plan(repositories)
    assert not repositories[4].exists()


def test_linked_origin_git_metadata_file_supported(repositories):
    origin, _, mirror, key, output = repositories
    linked = origin.parent / 'linked-origin'
    _git(origin, 'worktree', 'add', '-qb', 'linked-fixture', str(linked))
    control = (linked / '.git').read_bytes()
    head, index = _git(linked, 'rev-parse', 'HEAD'), _git(linked, 'ls-files', '--stage', '-z')
    directory = Path(_git(linked, 'rev-parse', '--absolute-git-dir').decode().strip())
    result = git_restore._publish_merge(
        git_restore._plan_merge(
            linked,
            mirror,
            key,
            gitdir=directory,
            worktree=output,
            branch='linked-restore',
        )
    )
    assert result.output == output and (linked / '.git').read_bytes() == control
    assert _git(linked, 'rev-parse', 'HEAD') == head and _git(linked, 'ls-files', '--stage', '-z') == index


def test_wrong_explicit_gitdir_never_redirects_to_another_repository(repositories):
    origin = repositories[0]
    other = origin.parent / 'other-repo'
    other.mkdir()
    _git(other, 'init', '-qb', 'main')
    (other / 'synthetic').write_bytes(b'SYNTHETIC')
    _commit(other)
    result = _invoke(repositories, '--gitdir', str(other / '.git'))
    assert result.exit_code == 2 and not repositories[4].exists()


def test_low_space_and_selected_key_alias_fail_read_only(repositories, monkeypatch):
    monkeypatch.setattr(git_restore.shutil, 'disk_usage', lambda _: type('Space', (), {'free': 0})())
    result = _invoke(repositories)
    assert result.exit_code == 1 and not repositories[4].exists()


def test_selected_key_hardlink_in_origin_refused(repositories):
    origin, _, _, key, _ = repositories
    os.link(key, origin / 'synthetic-key-alias')
    _commit(origin)
    result = _invoke(repositories)
    assert result.exit_code == 2 and not repositories[4].exists()


def test_staging_source_change_prevents_any_branch_creation(repositories, monkeypatch):
    plan = _plan(repositories)
    original = git_restore._stage_overlay

    def changed(plan, workspace, unsupported):
        result = original(plan, workspace, unsupported)
        (plan.origin / 'note.md').write_bytes(b'SYNTHETIC CONCURRENT ORIGIN EDIT')
        return result

    monkeypatch.setattr(git_restore, '_stage_overlay', changed)
    with pytest.raises(git_restore._MergeFailure):
        git_restore._publish_merge(plan)
    assert not repositories[4].exists()
    assert (repositories[0] / 'note.md').read_bytes() == b'SYNTHETIC CONCURRENT ORIGIN EDIT'
    assert b'obfuscidian/synthetic-review' not in _git(repositories[0], 'show-ref')


def test_cleanup_failure_after_success_reports_private_retention(repositories, monkeypatch):
    original = tx._remove_captured

    def retain(path, captured):
        if path.name.startswith(const.GIT_STAGE_PREFIX):
            (path / 'later-user-data').write_bytes(b'SYNTHETIC USER DATA')
            raise _OperationalError('SYNTHETIC REFUSAL')
        return original(path, captured)

    monkeypatch.setattr(tx, '_remove_captured', retain)
    result = git_restore._publish_merge(_plan(repositories))
    assert repositories[4].exists()
    assert result.retained and 'sensitive plaintext retained' in result.warnings[-1]
    assert (result.retained[-1] / 'later-user-data').read_bytes() == b'SYNTHETIC USER DATA'


@pytest.mark.parametrize('phase', ['stage', 'publication'])
def test_interrupt_has_no_success_claim_and_preserves_origin(repositories, monkeypatch, phase):
    before = _snapshot(repositories[0])
    if phase == 'stage':

        def interrupt(*args):
            raise KeyboardInterrupt

        monkeypatch.setattr(git_restore, '_stage_overlay', interrupt)
    else:
        original = tx._move
        fired = False

        def interrupt(source, destination, expected):
            nonlocal fired
            if destination.parent == repositories[4] and destination.name != '.gitignore' and not fired:
                fired = True
                raise KeyboardInterrupt
            return original(source, destination, expected)

        monkeypatch.setattr(tx, '_move', interrupt)
    result = _invoke(repositories)
    assert result.exit_code == 130, result.output
    assert 'interrupted' in result.output and 'published' not in result.output
    assert _snapshot(repositories[0]) == before
    assert not repositories[4].exists()


def test_manual_paths_are_quoted_and_terminal_controls_escaped(repositories):
    origin, _, mirror, key, output = repositories
    strange = origin.parent / "review space's; touch SYNTHETIC\n"
    result = _invoke(repositories, '--worktree', str(strange), '--branch', 'review/with-space-path', '--verbose')
    assert result.exit_code == 0, result.output
    assert strange.exists() and '\\n' in result.output
    assert not (origin.parent / 'SYNTHETIC').exists()
    command = next(line.split(': ', 1)[1] for line in result.output.splitlines() if line.startswith('Manual command'))
    assert shlex.split(ast.literal_eval(command)) == ['git', '-C', str(strange), 'status', '--ignored']


def test_filename_trailing_newline_is_preserved_in_git_base(repositories):
    origin = repositories[0]
    (origin / 'synthetic-newline\n').write_bytes(b'SYNTHETIC NAME')
    _commit(origin)
    result = _invoke(repositories)
    assert result.exit_code == 0, result.output
    assert (repositories[4] / 'synthetic-newline\n').read_bytes() == b'SYNTHETIC NAME'


def test_origin_executable_mode_changes_are_dirty(repositories):
    (repositories[0] / 'note.md').chmod(0o755)
    result = _invoke(repositories)
    assert result.exit_code == 1 and not repositories[4].exists()


@pytest.mark.parametrize('phase', ['branch-created', 'worktree-created'])
def test_git_failure_after_partial_creation_retains_uncertain_artifacts(repositories, monkeypatch, phase):
    plan = _plan(repositories)
    original = git_restore._git
    fired = False

    def fail_after_creation(executable, root, *args, **kw):
        nonlocal fired
        value = original(executable, root, *args, **kw)
        selected = args[0] == 'update-ref' if phase == 'branch-created' else args[:2] == ('worktree', 'add')
        if selected and not fired:
            fired = True
            raise _OperationalError('SYNTHETIC FAILURE AFTER MUTATION')
        return value

    monkeypatch.setattr(git_restore, '_git', fail_after_creation)
    with pytest.raises(git_restore._MergeFailure) as caught:
        git_restore._publish_merge(plan)
    assert 'retained' in str(caught.value)
    assert b'obfuscidian/synthetic-review' in _git(repositories[0], 'show-ref')
    assert repositories[4].exists() == (phase == 'worktree-created')


def test_git_configuration_change_after_preflight_is_refused(repositories):
    plan = _plan(repositories)
    _git(repositories[0], 'config', 'synthetic.changed', 'true')
    with pytest.raises(_OperationalError, match='configuration changed'):
        git_restore._publish_merge(plan)
    assert not repositories[4].exists()


def test_worktree_configuration_extension_does_not_change_origin(repositories):
    _git(repositories[0], 'config', 'extensions.worktreeConfig', 'true')
    before = _snapshot(repositories[0])
    result = _invoke(repositories)
    assert result.exit_code == 0, result.output
    assert _snapshot(repositories[0]) == before


def test_mirror_pending_ownership_is_refused_read_only(repositories):
    plan = _plan(repositories)
    source_plan = tx._plan_transaction(
        repositories[1],
        repositories[2],
        mirror=True,
        fernet=plan.reconstruction.fernet,
        target_rules=plan.reconstruction.transaction.target_rules,
    )
    source_plan.lock.write_bytes(b'SYNTHETIC PENDING OWNERSHIP')
    result = _invoke(repositories)
    assert result.exit_code == 1 and not repositories[4].exists()
    assert source_plan.lock.read_bytes() == b'SYNTHETIC PENDING OWNERSHIP'


def test_base_only_executable_flag_is_preserved_without_execution(repositories):
    origin = repositories[0]
    (origin / 'synthetic-script').write_bytes(b'SYNTHETIC NOT EXECUTABLE CONTENT')
    (origin / 'synthetic-script').chmod(0o700)
    _commit(origin)
    result = _invoke(repositories)
    assert result.exit_code == 0, result.output
    assert stat.S_IMODE((repositories[4] / 'synthetic-script').stat().st_mode) == 0o700
    assert _git(repositories[4], 'diff', '--', 'synthetic-script') == b''


def test_user_edit_between_staging_validation_and_branch_creation_is_retained(repositories, monkeypatch):
    original = git_restore._stage_overlay

    def edit_after_validation(plan, workspace, unsupported):
        result = original(plan, workspace, unsupported)
        (result[0] / 'later-user-file').write_bytes(b'SYNTHETIC LATER STAGE USER EDIT')
        return result

    monkeypatch.setattr(git_restore, '_stage_overlay', edit_after_validation)
    with pytest.raises(git_restore._MergeFailure) as caught:
        git_restore._publish_merge(_plan(repositories))
    assert not repositories[4].exists()
    assert b'obfuscidian/synthetic-review' not in _git(repositories[0], 'show-ref')
    retained = next(repositories[4].parent.glob(const.GIT_STAGE_PREFIX + '*'))
    assert (retained / 'overlay/later-user-file').read_bytes() == b'SYNTHETIC LATER STAGE USER EDIT'
    assert retained in caught.value.retained


def test_output_cannot_enter_external_gitdir_through_case_alias(repositories):
    origin, _, mirror, key, _ = repositories
    external = origin.parent / 'synthetic-external-git'
    _git(origin, 'init', '--separate-git-dir', str(external))
    alias = external.with_name(external.name.upper())
    with pytest.raises(_ConfigurationError):
        git_restore._plan_merge(origin, mirror, key, worktree=alias / 'review', branch='alias-test')
    assert not (external / 'review').exists()


@pytest.mark.parametrize('setting', ['extensions.partialClone', 'remote.synthetic.promisor'])
def test_partial_promisor_repository_refused_before_object_resolution(repositories, monkeypatch, setting):
    origin = repositories[0]
    _git(origin, 'config', setting, 'synthetic' if setting.startswith('extensions') else 'true')
    original = git_restore._git

    def no_object_reads(executable, root, *args, **kw):
        assert args[:3] != ('rev-parse', '--verify', 'HEAD^{commit}')
        assert args[0] not in ('ls-tree', 'cat-file')
        return original(executable, root, *args, **kw)

    monkeypatch.setattr(git_restore, '_git', no_object_reads)
    with pytest.raises(_ConfigurationError, match='partial/promisor'):
        _plan(repositories)
    assert not repositories[4].exists()


def test_unsupported_timestamp_preservation_warns_and_preserves_required_bytes(repositories, monkeypatch):
    plan = _plan(repositories)

    def unavailable(*args, **kwargs):
        raise OSError('SYNTHETIC FILESYSTEM TIMESTAMP LIMIT')

    monkeypatch.setattr(git_restore.restore.os, 'utime', unavailable)
    result = git_restore._publish_merge(plan)
    assert 'Some modification times could not be preserved' in result.warnings[-1]
    assert (repositories[4] / 'nested/new.bin').read_bytes() == bytes(range(256))
    assert (repositories[4] / 'nested/empty').is_dir()

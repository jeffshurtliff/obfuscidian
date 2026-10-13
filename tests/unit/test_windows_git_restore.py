# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_git_restore
:Synopsis:          Portable Git policy refusal and injected private lifecycle regression
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import os
import struct
from types import SimpleNamespace

import pytest

from obfuscidian import _windows_git_restore as win
from obfuscidian import constants as const
from obfuscidian import git_restore as git
from obfuscidian._windows_native import _NativeSafetyError, _private_acl
from tests.integration.test_merge_restore import _git, _plan, _snapshot, repositories
from tests.unit.test_windows_transactions import _ModelGuard, _security, model

SID = b'\x01\x01\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00'  # Synthetic parser SID only.


@pytest.mark.parametrize('directory', [False, True])
@pytest.mark.parametrize('inherited', [False, True])
def test_git_owner_policy_and_transaction_policy_remain_separate(directory, inherited):
    security = _security(directory)
    if inherited:
        acl = bytearray.fromhex(security['acl'])
        acl[9] |= 16
        security = {**security, 'acl': acl.hex(), 'protected': False}
    win._git_acl(security, SID, directory=directory)
    if inherited:
        with pytest.raises(_NativeSafetyError):
            _private_acl(bytes.fromhex(security['acl']), SID, directory=directory)


@pytest.mark.parametrize('change', ['owner', 'extra', 'null', 'explicit', 'deny', 'inherit-only', 'partial', 'foreign-grant'])
def test_unsafe_git_security_is_refused(change):
    security = _security()
    data = bytearray.fromhex(security['acl'])
    data[9] = 16
    security['protected'] = False
    if change == 'owner':
        security['owner'] = (SID[:-1] + b'\x01').hex()
    elif change == 'extra':
        data.extend(data[8:])
        struct.pack_into('<H', data, 2, len(data))
        struct.pack_into('<H', data, 4, 2)
    elif change == 'null':
        data = bytearray()
    elif change == 'explicit':
        data[9] = 0
    elif change == 'deny':
        data[8] = 1
    elif change == 'inherit-only':
        data[9] |= 8
    elif change == 'partial':
        struct.pack_into('<I', data, 12, 1)
    else:
        data[-1] ^= 1
    security['acl'] = data.hex()
    with pytest.raises(_NativeSafetyError):
        win._git_acl(security, SID, directory=False)


@pytest.fixture
def injected(tmp_path, monkeypatch):
    """Use real local Git with injected native I/O; this is never Windows proof."""
    if os.name != 'posix':
        pytest.skip('Supplementary POSIX Git with injected Windows I/O; native Git tests are separate.')
    repository_root, model_root = tmp_path / 'repositories', tmp_path / 'model'
    repository_root.mkdir()
    model_root.mkdir()
    locations = repositories.__wrapped__(repository_root, monkeypatch)
    model.__wrapped__(model_root, monkeypatch)
    monkeypatch.setattr(win, '_Guard', _ModelGuard)
    monkeypatch.setattr(win, 'os', SimpleNamespace(name='nt'))

    def record(handle):
        return win.files._record(handle)

    def timestamp(path, mtime_ns, unsupported, relative):
        os.utime(path, ns=(mtime_ns, mtime_ns))

    monkeypatch.setattr(win, '_git_record', record)
    monkeypatch.setattr(win, '_timestamp', timestamp)
    return locations


@pytest.mark.parametrize('preserve', [False, True])
def test_injected_git_lifecycle_preserves_bytes_index_origin_and_retained_evidence(injected, preserve):
    origin, source, _, _, output = injected
    before = _snapshot(origin)
    index = _git(origin, 'ls-files', '--stage', '-z')
    result = win._publish_merge(_plan(injected, preserve_config=preserve))
    assert _snapshot(origin) == before
    assert _git(output, 'ls-files', '--stage', '-z') == index
    assert _git(output, 'diff', '--cached') == b''
    for name in ('note.md', 'nested/new.bin', 'ignored.bin'):
        assert (output / name).read_bytes() == (source / name).read_bytes()
    assert (output / 'nested/empty').is_dir()
    assert (output / '.obsidian/settings.json').read_bytes() == (origin if preserve else source).joinpath(
        '.obsidian/settings.json'
    ).read_bytes()
    assert result.ignored == ('ignored.bin',)
    assert len(result.retained) == 1 and result.retained[0].is_dir()
    assert not list(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))


@pytest.mark.parametrize('boundary', ['branch-created', 'private-root-created', 'index-ready', 'published'])
def test_injected_ordinary_failure_removes_only_proven_git_artifacts(injected, monkeypatch, boundary):
    before = _snapshot(injected[0])

    def fail(label):
        if label == boundary:
            raise OSError('SYNTHETIC FAILURE')

    monkeypatch.setattr(win, '_boundary', fail)
    with pytest.raises(git._MergeFailure, match='cleaned safely'):
        win._publish_merge(_plan(injected))
    assert _snapshot(injected[0]) == before
    assert not injected[4].exists()
    assert b'obfuscidian/synthetic-review' not in _git(injected[0], 'show-ref')


@pytest.mark.parametrize('edit', ['payload', 'ignored', 'index', 'ref', 'control', 'admin', 'directory-time', 'reconstruction'])
def test_injected_cleanup_preserves_user_edits(injected, monkeypatch, edit):
    origin, _, _, _, output = injected

    def fail(label):
        if label == 'published':
            if edit in {'payload', 'ignored', 'control'}:
                (output / {'payload': 'note.md', 'ignored': 'ignored.bin', 'control': '.gitignore'}[edit]).write_bytes(
                    b'USER EDIT'
                )
            elif edit == 'index':
                _git(output, 'add', 'note.md')
            elif edit == 'ref':
                _git(output, 'symbolic-ref', 'HEAD', 'refs/heads/main')
            elif edit == 'admin':
                (origin / '.git/worktrees' / output.name / 'HEAD').write_bytes(b'USER EDIT')
            elif edit == 'directory-time':
                os.utime(output / 'nested', ns=(1_500_000_000_000_000_000, 1_500_000_000_000_000_000))
            else:
                stage = next(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
                (stage / 'user-edit').write_bytes(b'USER EDIT')
            raise OSError('SYNTHETIC FAILURE')

    monkeypatch.setattr(win, '_boundary', fail)
    with pytest.raises(git._MergeFailure) as caught:
        win._publish_merge(_plan(injected))
    if edit == 'reconstruction':
        assert any((p / 'user-edit').exists() for p in caught.value.retained)
    else:
        assert output.exists() and output in caught.value.retained


def test_injected_preview_and_late_collisions_do_not_overwrite(injected, monkeypatch):
    origin, _, _, _, output = injected
    plan = _plan(injected)
    before = _snapshot(origin)
    assert win._publish_merge(plan, dry_run=True) is None
    assert _snapshot(origin) == before and not output.exists()

    def collision(label):
        if label == 'before-branch':
            _git(origin, 'branch', 'obfuscidian/synthetic-review')

    monkeypatch.setattr(win, '_boundary', collision)
    with pytest.raises(git._MergeFailure):
        win._publish_merge(plan)
    assert _git(origin, 'rev-parse', 'refs/heads/obfuscidian/synthetic-review') == plan.head
    assert not output.exists()


def test_injected_directory_creation_failure_retains_uncertain_private_artifact(injected, monkeypatch):
    original = win.files._mkdir

    def uncertain(parent, name):
        result = original(parent, name)
        if name.startswith(const.GIT_STAGE_PREFIX):
            raise OSError('SYNTHETIC POST-CREATION FAILURE')
        return result

    monkeypatch.setattr(win.files, '_mkdir', uncertain)
    before = _snapshot(injected[0])
    with pytest.raises(git._MergeFailure) as caught:
        win._publish_merge(_plan(injected))
    assert len(caught.value.retained) == 1
    assert caught.value.retained[0].is_dir() and not list(caught.value.retained[0].iterdir())
    assert _snapshot(injected[0]) == before and not injected[4].exists()
    assert b'obfuscidian/synthetic-review' not in _git(injected[0], 'show-ref')

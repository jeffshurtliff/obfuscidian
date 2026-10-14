# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_windows_git_restore
:Synopsis:          Synthetic real Git for Windows private merge lifecycle and retention tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import ctypes
import os
import queue
import shlex
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian import _windows_files as files
from obfuscidian import _windows_git_restore as win
from obfuscidian import backup, git_restore, keys
from obfuscidian import constants as const
from obfuscidian._windows_native import _Guard, _NativeSafetyError
from obfuscidian.cli import cli
from tests._windows_support import _failure_details, _io_path, _terminate_worker
from tests.integration.test_merge_restore import _commit, _git
from tests.integration.test_windows_native import _set_descriptor

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Actual Git for Windows/native filesystem proof required.')


def _object_attribute_masks(root: Path) -> str:
    """Enumerate extended fixture paths while retaining ordinary native bindings."""
    enumeration = _io_path(root)
    masks = set()
    for path in enumeration.rglob('*'):
        if path.is_file():
            # Extended spelling belongs only to observational Python I/O.
            # Native guards must receive the original ordinary drive root.
            logical = root / path.relative_to(enumeration)
            with files._entry(logical.parent, logical.name, False) as handle:
                masks.add(handle._identity().attributes)
    return ','.join(f'0x{mask:08x}' for mask in sorted(masks))


@pytest.fixture
def repositories(tmp_path, monkeypatch, record_property):
    """Require real unelevated Git for Windows and private synthetic NTFS roots."""
    assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Use an existing unelevated token.'
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    parent = tmp_path.resolve()
    with _Guard(parent):
        pass
    files._mkdir(parent, 'spaced synthetic paths')
    parent /= 'spaced synthetic paths'
    origin, source, mirror, key, output = (
        parent / n for n in ('origin repo', 'source', 'mirror', 'synthetic.key', 'review tree')
    )
    files._mkdir(parent, origin.name)
    files._mkdir(origin, '.git')
    _git(origin, 'init', '-qb', 'main')
    version = _git(origin, '--version').decode().strip()
    assert '.windows.' in version, 'Actual Git for Windows is mandatory.'
    record_property('git_version', version)
    _git(origin, 'config', 'core.autocrlf', 'false')
    _git(origin, 'config', 'core.filemode', 'false')
    for name, data in {
        'note.md': b'SYNTHETIC BASE\r\n',
        'base-only.bin': b'BASE\x00\xff',
        '.gitignore': b'ignored.bin\n',
    }.items():
        files._write(origin, name, data)
    files._mkdir(origin, '.obsidian')
    files._write(origin / '.obsidian', 'settings.json', b'{"synthetic":"base"}')
    _commit(origin)
    _git(origin, 'update-index', '--chmod=+x', 'base-only.bin')
    _git(origin, 'commit', '-qm', 'Recorded synthetic executable Git mode')
    record_property('git_object_attribute_masks', _object_attribute_masks(origin / '.git' / 'objects'))
    files._mkdir(parent, source.name)
    files._write(source, 'note.md', b'SYNTHETIC BACKUP\r\n\x00\xff')
    files._write(source, 'ignored.bin', bytes(range(256)))
    files._mkdir(source, 'new folder')
    files._write(source / 'new folder', 'binary data.bin', bytes(range(256)) + b'\r\n')
    files._mkdir(source / 'new folder', 'empty')
    files._mkdir(source, '.obsidian')
    files._write(source / '.obsidian', 'settings.json', b'{"synthetic":"backup"}')
    keys._generate_key(key)
    backup._publish_windows_backup(backup._plan_fresh(source, mirror, key))
    return origin, source, mirror, key, output


def _plan(repositories, **options):
    origin, _, mirror, key, output = repositories
    return win._plan_merge(origin, mirror, key, worktree=output, branch='synthetic-review', **options)


def _origin_state(origin):
    tree = win._git_tree(origin, excluded={'.git'})
    for name in ('HEAD', 'index', 'config'):
        path = origin / '.git' / name
        with files._entry(path.parent, path.name, False) as handle:
            tree['.git/' + name] = win._git_record(handle)
    return tree


def test_real_native_readonly_git_objects_keep_exact_attributes_and_payload_refusal(repositories, record_property):
    plan = _plan(repositories)
    before = win._administration(plan)
    objects = {name: record for name, record in before[plan.common].items() if name.startswith('objects/')}
    readonly = {name: record for name, record in objects.items() if record['attributes'] & const.WINDOWS_ATTRIBUTE_READONLY}
    record_property('readonly_git_object_count', len(readonly))
    assert readonly, 'Actual Git-created read-only objects are mandatory for this regression.'
    for name, record in readonly.items():
        assert not record['id'][2]
        path = plan.common / name
        with files._entry(path.parent, path.name, False) as handle:
            assert win._git_record(handle, _readonly=True) == record
            with pytest.raises(_NativeSafetyError, match='Unsupported Windows Git attributes'):
                win._git_record(handle)
            with pytest.raises(_NativeSafetyError, match='Unsupported baseline Windows attributes'):
                files._record(handle)
    assert win._administration(plan) == before
    assert not repositories[-1].exists()


@pytest.mark.parametrize('preserve', [False, True])
def test_real_native_git_overlay_privacy_binary_index_and_spaced_paths(repositories, preserve, monkeypatch, record_property):
    origin, source, _, _, output = repositories
    before = _origin_state(origin)
    index, head = _git(origin, 'ls-files', '--stage', '-z'), _git(origin, 'rev-parse', 'HEAD')
    observed = []

    def observe(label):
        if label == 'worktree-created':
            with files._entry(output, const.GIT_METADATA, False) as handle:
                observed.append(handle._identity().attributes)
                record_property('worktree_git_control_attributes', f'0x{observed[-1]:08x}')

    monkeypatch.setattr(win, '_boundary', observe)
    try:
        result = win._publish_merge(_plan(repositories, preserve_config=preserve))
    except git_restore._MergeFailure as error:
        pytest.fail(_failure_details(error), pytrace=False)
    assert observed and observed[0] & const.WINDOWS_ATTRIBUTE_HIDDEN
    with files._entry(output, const.GIT_METADATA, False) as handle:
        record = win._git_record(handle, _hidden_control=True)
        assert record['attributes'] == observed[0]
        with pytest.raises(_NativeSafetyError, match='Unsupported baseline Windows attributes'):
            files._record(handle)
    assert _origin_state(origin) == before
    assert _git(output, 'rev-parse', 'HEAD') == head
    assert _git(output, 'ls-files', '--stage', '-z') == index
    assert b'100755 ' in index and _git(output, 'diff', '--cached') == b''
    assert _git(output, 'symbolic-ref', '--short', 'HEAD') == b'obfuscidian/synthetic-review\n'
    for name in ('note.md', 'ignored.bin', 'new folder/binary data.bin'):
        assert (output / name).read_bytes() == (source / name).read_bytes()
    assert (output / 'base-only.bin').read_bytes() == b'BASE\x00\xff'
    assert (output / 'new folder/empty').is_dir()
    assert (output / '.obsidian/settings.json').read_bytes() == (origin if preserve else source).joinpath(
        '.obsidian/settings.json'
    ).read_bytes()
    assert result.ignored == ('ignored.bin',)
    assert b' M note.md' in _git(output, 'status', '--porcelain')
    assert len(result.retained) == 1 and result.retained[0].is_dir()
    assert not list(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
    win._git_tree(output)
    win._administration(_plan_for_audit(repositories))
    files._capture(result.retained[0], private=True)
    with files._entry(output, '.git', False) as handle:
        security = files._security(handle, baseline=False)
        assert not security['protected'], 'The fixture must exercise actual inherited Git control ACLs.'
        with pytest.raises(_NativeSafetyError):
            handle._private()  # Production transaction-control policy is unchanged.


def _plan_for_audit(repositories):
    """Supply existing read-only control locations after the branch was created."""
    from types import SimpleNamespace

    return SimpleNamespace(common=repositories[0] / '.git', gitdir=repositories[0] / '.git')


@pytest.mark.parametrize('collision', ['branch', 'branch-parent', 'output', 'late-branch', 'late-output'])
def test_real_native_git_collisions_preserve_existing_data(repositories, monkeypatch, collision):
    origin, _, _, _, output = repositories
    if collision == 'branch':
        _git(origin, 'branch', 'obfuscidian/synthetic-review')
    elif collision == 'branch-parent':
        _git(origin, 'branch', 'obfuscidian')
    elif collision == 'output':
        output.mkdir()
        (output / 'keep.bin').write_bytes(b'SYNTHETIC COLLISION')
    if collision.startswith('late'):
        plan = _plan(repositories)

        def collide(label):
            if label == 'before-branch':
                if collision == 'late-branch':
                    _git(origin, 'branch', 'obfuscidian/synthetic-review')
                else:
                    output.mkdir()
                    (output / 'keep.bin').write_bytes(b'SYNTHETIC COLLISION')

        monkeypatch.setattr(win, '_boundary', collide)
        with pytest.raises(git_restore._MergeFailure):
            win._publish_merge(plan)
    else:
        with pytest.raises((_NativeSafetyError, git_restore._ConfigurationError)):
            _plan(repositories)
    if 'output' in collision:
        assert (output / 'keep.bin').read_bytes() == b'SYNTHETIC COLLISION'
    if collision.endswith('branch'):
        assert _git(origin, 'rev-parse', 'refs/heads/obfuscidian/synthetic-review') == _git(origin, 'rev-parse', 'HEAD')


@pytest.mark.parametrize('boundary', ['branch-created', 'private-root-created', 'index-ready', 'published'])
def test_real_native_git_ordinary_failures_cleanup_only_unchanged_artifacts(repositories, monkeypatch, boundary):
    before = _origin_state(repositories[0])
    reached = []

    def fail(label):
        if label == boundary:
            reached.append(label)
            raise OSError('SYNTHETIC ORDINARY FAILURE')

    monkeypatch.setattr(win, '_boundary', fail)
    with pytest.raises(git_restore._MergeFailure, match='cleaned safely'):
        win._publish_merge(_plan(repositories))
    assert reached == [boundary]
    assert _origin_state(repositories[0]) == before
    assert not repositories[4].exists()
    assert b'obfuscidian/synthetic-review' not in _git(repositories[0], 'show-ref')


@pytest.mark.parametrize(
    'edit', ['payload', 'ignored', 'index', 'branch', 'control', 'admin', 'directory-time', 'reconstruction']
)
def test_real_native_git_user_edits_and_private_artifacts_retained(repositories, monkeypatch, edit):
    origin, _, _, _, output = repositories
    plan = _plan(repositories)
    reached = []

    def mutate(label):
        if label != 'published':
            return
        reached.append(label)
        if edit in {'payload', 'ignored', 'control'}:
            name = {'payload': 'note.md', 'ignored': 'ignored.bin', 'control': '.gitignore'}[edit]
            (output / name).write_bytes(b'SYNTHETIC USER EDIT')
        elif edit == 'index':
            _git(output, 'add', 'note.md')
        elif edit == 'branch':
            _git(output, 'add', '--all')
            _git(output, 'commit', '-qm', 'Created synthetic user branch edit')
        elif edit == 'admin':
            admin = next((origin / '.git/worktrees').iterdir())
            (admin / 'HEAD').write_bytes(b'SYNTHETIC USER EDIT')
        elif edit == 'directory-time':
            os.utime(output / 'new folder', ns=(1_500_000_000_000_000_000, 1_500_000_000_000_000_000))
        else:
            stage = next(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
            files._write(stage, 'user-edit.bin', b'SYNTHETIC KEEP')
        raise OSError('SYNTHETIC FAILURE AFTER EDIT')

    monkeypatch.setattr(win, '_boundary', mutate)
    with pytest.raises(git_restore._MergeFailure) as caught:
        win._publish_merge(plan)
    assert reached == ['published'], _failure_details(caught.value)
    if edit == 'reconstruction':
        assert any((p / 'user-edit.bin').exists() for p in caught.value.retained)
    else:
        assert output in caught.value.retained and output.exists()
    for root in caught.value.retained:
        if root != output:
            files._capture(root, private=True)


def test_real_native_git_sharing_denial_retains_worktree(repositories, monkeypatch):
    output = repositories[4]
    handles = []
    reached = []

    def deny(label):
        if label == 'published':
            reached.append(label)
            # A real deny-delete read handle must prevent Git's worktree cleanup.
            guard = _Guard(output)
            guard.__enter__()
            handles.append(guard)
            leaf = guard.api._open_relative(guard.handles[-1], 'note.md', directory=False)
            leaf.parent = guard
            handles.append(leaf)
            raise OSError('SYNTHETIC FAILURE WITH REAL SHARING DENIAL')

    monkeypatch.setattr(win, '_boundary', deny)
    try:
        with pytest.raises(git_restore._MergeFailure) as caught:
            win._publish_merge(_plan(repositories))
        assert reached == ['published'], _failure_details(caught.value)
        assert output in caught.value.retained
        assert (output / 'note.md').read_bytes().startswith(b'SYNTHETIC BACKUP')
    finally:
        for handle in reversed(handles):
            handle.__exit__()


def test_real_native_proposal_sharing_denial_retains_transaction_evidence(repositories, monkeypatch):
    origin, _, _, _, output = repositories
    before = _origin_state(origin)
    handles = []
    reached = []

    def deny(label):
        if label == 'ready':
            reached.append(label)
            workspace = next(
                p for p in output.parent.glob(const.TRANSACTION_PREFIX + '*') if p.is_dir() and (p / 'stage/note.md').exists()
            )
            guard = _Guard(workspace / 'stage')
            guard.__enter__()
            handles.append(guard)
            leaf = guard.api._open_relative(guard.handles[-1], 'note.md', directory=False)
            leaf.parent = guard
            handles.append(leaf)
            # No exception injection: the actual deny-delete handle must stop
            # the forthcoming native proposal rename acquisition.

    monkeypatch.setattr(win.windows, '_boundary', deny)
    try:
        with pytest.raises(git_restore._MergeFailure) as caught:
            win._publish_merge(_plan(repositories))
        assert reached == ['ready'], _failure_details(caught.value)
        assert _origin_state(origin) == before
        assert any((p / 'stage/note.md').exists() for p in caught.value.retained if p.is_dir())
    finally:
        for handle in reversed(handles):
            handle.__exit__()


def test_real_native_unsafe_git_permissions_refused_without_repair(repositories):
    origin, _, _, _, output = repositories
    plan = _plan(repositories)
    config = origin / '.git/config'
    original = config.read_bytes()
    with _Guard(origin / '.git') as guard:
        _, owner = guard.api._owner()
        _set_descriptor(guard.api, config, f'O:{owner}D:P(A;;FA;;;{owner})(A;;FR;;;WD)')
    with files._entry(config.parent, config.name, False) as handle:
        unsafe = files._security(handle, baseline=False)
        identity = files._id(handle)
    with pytest.raises(_NativeSafetyError):
        win._publish_merge(plan)
    with files._entry(config.parent, config.name, False) as handle:
        assert files._id(handle) == identity and files._security(handle, baseline=False) == unsafe
        assert handle._read(const.MAX_ENCRYPTED_BYTES) == original
    assert not output.exists()
    assert b'obfuscidian/synthetic-review' not in _git(origin, 'show-ref')


def test_real_native_git_hooks_filters_and_ambient_selectors_do_not_execute(repositories, monkeypatch):
    origin, _, _, _, output = repositories
    marker = origin.parent / 'must not run'
    hook = origin / '.git/hooks/post-checkout'
    hook.write_text('#!/bin/sh\ntouch ' + shlex.quote(marker.as_posix()) + '\n', encoding='utf-8')
    for name in ('reference-transaction', 'post-index-change'):
        (hook.parent / name).write_bytes(hook.read_bytes())
    files._write(origin, '.gitattributes', b'*.md filter=synthetic\n')
    _commit(origin)
    for selector in ('clean', 'smudge', 'process'):
        _git(origin, 'config', 'filter.synthetic.' + selector, 'touch ' + shlex.quote(marker.as_posix()))
    _git(origin, 'config', 'filter.synthetic.required', 'true')
    monkeypatch.setenv('GIT_DIR', 'SYNTHETIC-NONEXISTENT')
    monkeypatch.setenv('GIT_WORK_TREE', 'SYNTHETIC-NONEXISTENT')
    win._publish_merge(_plan(repositories))
    assert not marker.exists() and (output / 'note.md').read_bytes().startswith(b'SYNTHETIC BACKUP')


def test_real_native_inherited_git_control_kernel_denial_with_positive_control(repositories, record_property):
    """Prove inherited Git control denial through native relative kernel opens.

    Open the synthetic root before impersonation so a parent's traverse denial
    cannot masquerade as denial of the leaf. The matching permissive leaf must
    open under the same restricted token/rights. No parent ACL is changed, which
    could otherwise propagate grants into the inherited Git control.
    """
    output = repositories[4]
    win._publish_merge(_plan(repositories))
    with files._entry(output, '.git', False) as handle:
        before = win._git_record(handle, _hidden_control=True)
    record_property('inherited_git_control_attributes', f'0x{before["attributes"]:08x}')
    assert not before['security']['protected'], 'Actual inherited Git control policy is mandatory.'
    with _Guard(output) as guard:
        api, ptr = guard.api, ctypes.c_void_p
        wt = api.wt
        phandle = ctypes.POINTER(wt.HANDLE)

        class _SidAndAttributes(ctypes.Structure):
            _fields_ = [('sid', ptr), ('attributes', wt.DWORD)]

        api._bind(api.advapi, 'ConvertStringSidToSidW', wt.BOOL, [wt.LPCWSTR, ctypes.POINTER(ptr)])
        api._bind(
            api.advapi,
            'CreateRestrictedToken',
            wt.BOOL,
            [wt.HANDLE, wt.DWORD, wt.DWORD, ptr, wt.DWORD, ptr, wt.DWORD, ptr, phandle],
        )
        api._bind(api.advapi, 'DuplicateToken', wt.BOOL, [wt.HANDLE, ctypes.c_int, phandle])
        api._bind(api.advapi, 'ImpersonateLoggedOnUser', wt.BOOL, [wt.HANDLE])
        api._bind(api.advapi, 'RevertToSelf', wt.BOOL, [])
        process_token, restricted, impersonation = wt.HANDLE(), wt.HANDLE(), wt.HANDLE()
        everyone = ptr()
        files._write(output, 'positive-control.bin', b'SYNTHETIC POSITIVE')
        _, owner = api._owner()
        _set_descriptor(api, output / 'positive-control.bin', f'O:{owner}D:P(A;;FA;;;{owner})(A;;GR;;;WD)')
        try:
            api._check(api.advapi.OpenProcessToken(api.kernel.GetCurrentProcess(), 0xA, ctypes.byref(process_token)))
            api._check(api.advapi.ConvertStringSidToSidW('S-1-1-0', ctypes.byref(everyone)))
            restricting = _SidAndAttributes(everyone, 0)
            api._check(
                api.advapi.CreateRestrictedToken(
                    process_token, 1, 0, None, 0, None, 1, ctypes.byref(restricting), ctypes.byref(restricted)
                )
            )
            api._check(api.advapi.DuplicateToken(restricted, 2, ctypes.byref(impersonation)))
            api._check(api.advapi.ImpersonateLoggedOnUser(impersonation))
            try:
                with pytest.raises(_NativeSafetyError, match='0xC0000022'):
                    with api._open_relative(guard.handles[-1], '.git', directory=False):
                        pytest.fail('Restricted token opened inherited private Git control.')
                record_property('restricted_git_control_denied', True)
                with api._open_relative(guard.handles[-1], 'positive-control.bin', directory=False) as positive:
                    assert positive._read(100) == b'SYNTHETIC POSITIVE'
                record_property('restricted_positive_control_opened', True)
            finally:
                api._check(api.advapi.RevertToSelf())
        finally:
            for token in (impersonation, restricted, process_token):
                if token.value:
                    api._check(api.kernel.CloseHandle(token))
            if everyone.value:
                api._check(api.kernel.LocalFree(everyone) is None)
    with files._entry(output, '.git', False) as handle:
        assert win._git_record(handle, _hidden_control=True) == before
    record_property('inherited_git_control_preserved_exactly', True)


def test_real_native_git_preview_and_production_cli_refusal(repositories):
    origin, _, mirror, key, output = repositories
    # Let unchanged production read-only planning reach the existing write gate;
    # executable Git-mode coverage belongs to the private lifecycle case above.
    _git(origin, 'update-index', '--chmod=-x', 'base-only.bin')
    _git(origin, 'commit', '-qm', 'Selected ordinary synthetic mode for CLI gate proof')
    plan = _plan(repositories)
    root = _io_path(origin.parent)
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert win._publish_merge(plan, dry_run=True) is None
    result = CliRunner().invoke(
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
        ],
    )
    assert result.exit_code != 0 and not output.exists()
    assert 'native Windows support is deferred' in result.output
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()} == before


WORKER = r"""
import os, sys
from pathlib import Path
from obfuscidian import _windows_git_restore as win
origin, mirror, key, output = map(Path, sys.argv[1:5])
boundary = sys.argv[5]
def observe(label):
    if label == boundary:
        print('SYNTHETIC READY', os.getpid(), flush=True)
        sys.stdin.readline()
win._boundary = observe
try:
    win._publish_merge(win._plan_merge(origin, mirror, key, worktree=output, branch='synthetic-review'))
except BaseException as error:
    from tests._windows_support import _failure_details
    # Never return a raw traceback, paths or arbitrary exception text to JUnit.
    detail = _failure_details(error).replace('\n', ' | ')
    print('SYNTHETIC FAILURE', detail, flush=True)
    raise SystemExit(1) from None
"""


@pytest.mark.parametrize('boundary', ['branch-created', 'private-root-created', 'worktree-added', 'index-ready', 'published'])
def test_real_native_git_worker_death_retains_manual_inspection_state(repositories, boundary):
    origin, _, mirror, key, output = repositories
    before = _origin_state(origin)
    process = subprocess.Popen(
        [sys.executable, '-c', WORKER, *(str(p) for p in (origin, mirror, key, output)), boundary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ready = queue.Queue()
    thread = threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True)
    thread.start()
    try:
        message = ready.get(timeout=90)
        if message.startswith(b'SYNTHETIC FAILURE '):
            pytest.fail(message.decode().strip(), pytrace=False)
        _terminate_worker(process, message, b'SYNTHETIC READY')
        process.communicate(timeout=15)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=15)
        thread.join(timeout=1)
    assert _origin_state(origin) == before
    assert _git(origin, 'rev-parse', 'refs/heads/obfuscidian/synthetic-review') == _git(origin, 'rev-parse', 'HEAD')
    retained = list(output.parent.glob(const.GIT_STAGE_PREFIX + '*'))
    assert retained
    for root in retained:
        files._capture(root, private=True)
    if output.exists():
        win._git_tree(output)
    if boundary in {'worktree-added', 'index-ready', 'published'}:
        assert any(root == output for root, _ in git_restore._worktrees('git', origin))
    with pytest.raises(git_restore._ConfigurationError):
        _plan(repositories)  # Collision requires manual inspection, never automatic recovery.

# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_verify
:Synopsis:          Synthetic verify CLI integrity, privacy, and no-write boundaries
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import builtins
import hashlib
import importlib
import io
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import manifest, verification
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from obfuscidian.errors import _OperationalError
from obfuscidian.paths import _TargetRules

cli_module = importlib.import_module('obfuscidian.cli')
FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/v1'


@pytest.fixture
def mirror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Fernet]:
    """Use frozen public synthetic data and keep configuration entirely temporary."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path.resolve())
    monkeypatch.setenv('HOME', str(tmp_path.resolve()))
    monkeypatch.setenv('USERPROFILE', str(tmp_path.resolve()))
    root = tmp_path.resolve() / 'synthetic-mirror'
    shutil.copytree(FIXTURE / 'mirror', root)
    key = root.parent / 'obfuscidian-synthetic.key'
    key.write_bytes((FIXTURE / 'synthetic-fernet-key.txt').read_bytes().strip())
    key.chmod(0o600)
    (root / '.git').mkdir()
    (root / '.git/sentinel').write_bytes(b'SYNTHETIC GIT CONTROL')
    (root / '.gitignore').write_bytes(b'SYNTHETIC GIT IGNORE')
    return root, key, Fernet(key.read_bytes())


def _snapshot(root: Path) -> dict:
    """Record the entire temporary tree except OS read-induced access times."""
    result = {}
    for path in (root, *sorted(root.rglob('*'))):
        info = path.lstat()
        digest = None
        if stat.S_ISREG(info.st_mode):
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        result[path.relative_to(root).as_posix()] = (
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            digest,
        )
    return result


def _args(root: Path, key: Path, *options: str) -> list[str]:
    """Supply absolute paths to sequential CliRunner invocations."""
    return ['verify', '--mirror', str(root), '--key', str(key), '--non-interactive', *options]


def _assert_no_writes(root: Path, arguments: list[str], monkeypatch: pytest.MonkeyPatch, *, input: str = ''):
    """Reject application write attempts as well as comparing final tree state.

    This also detects attempts later undone or caught by the command. Instrument
    opens, direct descriptor writes and filesystem mutations across all paths.
    Snapshotting happens outside the guarded invocation; stdout is permitted.
    """
    before = _snapshot(root)
    attempted = []

    def reject(*args, **kwargs):
        attempted.append('mutation')
        raise AssertionError('Verification attempted an application write.')

    original_open, original_io_open, original_os_open = builtins.open, io.open, os.open

    def guard_open(file, mode='r', *args, **kwargs):
        if any(flag in mode for flag in 'wax+'):
            return reject()
        return original_open(file, mode, *args, **kwargs)

    def guard_io_open(file, mode='r', *args, **kwargs):
        if any(flag in mode for flag in 'wax+'):
            return reject()
        return original_io_open(file, mode, *args, **kwargs)

    def guard_os_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            return reject()
        return original_os_open(path, flags, *args, **kwargs)

    with monkeypatch.context() as guarded:
        guarded.setattr(builtins, 'open', guard_open)
        guarded.setattr(io, 'open', guard_io_open)
        guarded.setattr(os, 'open', guard_os_open)
        for name in (
            'mkdir',
            'makedirs',
            'remove',
            'unlink',
            'rmdir',
            'rename',
            'replace',
            'chmod',
            'utime',
            'write',
            'truncate',
            'ftruncate',
            'symlink',
            'link',
        ):
            guarded.setattr(os, name, reject)
        guarded.setattr(subprocess, 'Popen', reject)
        result = CliRunner().invoke(cli, arguments, input=input)
    assert attempted == []
    assert _snapshot(root) == before
    return result


@pytest.mark.parametrize('verbose', [False, True])
def test_complete_valid_mirror_counts_and_privacy(mirror, monkeypatch, verbose):
    """Authenticate all mixed binary/hidden/empty records and preserve Git controls."""
    root, key, fernet = mirror
    expected = manifest._verify_mirror(root, fernet)
    result = _assert_no_writes(root.parent, _args(root, key, *(['--verbose'] if verbose else [])), monkeypatch)
    assert result.exit_code == 0, result.output
    assert '5 files, 4 directories' in result.output
    assert f'{expected.plaintext_bytes} plaintext bytes, {expected.encrypted_bytes} encrypted bytes' in result.output
    assert 'Best-effort' in result.output and 'access times' in result.output
    for private in (str(root), str(key), key.read_text(), 'SYNTHETIC HIDDEN', expected.manifest.files[0].plaintext_sha256):
        assert private not in result.output
    for record in expected.manifest.files:
        assert (repr(record.path) in result.output) == verbose


@pytest.mark.parametrize(
    'case',
    [
        'wrong-key',
        'manifest-tampered',
        'manifest-truncated',
        'object-tampered',
        'object-truncated',
        'object-empty',
        'last-object',
        'missing-object',
        'unexpected-object',
        'swapped',
        'unknown-version',
        'malformed',
        'duplicate-key',
        'unsafe-path',
        'missing-manifest',
        'missing-objects',
        'missing-managed',
        'missing-mirror',
        'unknown-root',
        'unknown-managed',
        'plaintext-hash',
        'plaintext-size',
        'object-authentication',
        'oversize-manifest',
        'oversize-object',
    ],
)
@pytest.mark.parametrize('verbose', [False, True])
def test_failed_mirrors_never_write_or_disclose_partial_names(mirror, monkeypatch, case, verbose):
    """Fail closed on complete-format failures through the actual public command."""
    root, key, fernet = mirror
    target = root / '.obfuscidian/manifest.obf'
    mapping = json.loads(fernet.decrypt(target.read_bytes()))
    objects = root / '.obfuscidian/objects'
    opened_oversize = []
    first, second = [objects / (entry['object_id'] + '.obf') for entry in mapping['files'][:2]]
    if case == 'wrong-key':
        key.write_bytes(Fernet.generate_key())
    elif case in {'manifest-tampered', 'manifest-truncated', 'object-tampered', 'object-truncated', 'object-empty'}:
        path = target if case.startswith('manifest') else first
        data = path.read_bytes()
        path.write_bytes(b'' if case.endswith('empty') else data[:-8] if case.endswith('truncated') else b'!' + data[1:])
    elif case == 'missing-object':
        first.unlink()
    elif case == 'last-object':
        (objects / (mapping['files'][-1]['object_id'] + '.obf')).write_bytes(b'CORRUPT')
    elif case == 'unexpected-object':
        (objects / ('f' * 32 + '.obf')).write_bytes(first.read_bytes())
    elif case == 'swapped':
        a, b = first.read_bytes(), second.read_bytes()
        assert len(a) == len(b)
        first.write_bytes(b)
        second.write_bytes(a)
    elif case in {'unknown-version', 'unsafe-path', 'plaintext-hash', 'plaintext-size', 'object-authentication'}:
        if case == 'unknown-version':
            mapping['format_version'] = 99
        elif case == 'unsafe-path':
            mapping['files'][0]['path'] = '../SYNTHETIC PRIVATE'
        elif case == 'plaintext-hash':
            mapping['files'][0]['plaintext_sha256'] = '0' * 64
        elif case == 'plaintext-size':
            mapping['files'][0]['size'] += 1
        else:
            first.write_bytes(Fernet(Fernet.generate_key()).encrypt(b'SYNTHETIC PRIVATE'))
            mapping['files'][0]['ciphertext_sha256'] = hashlib.sha256(first.read_bytes()).hexdigest()
        target.write_bytes(fernet.encrypt(json.dumps(mapping).encode()))
    elif case in {'malformed', 'duplicate-key'}:
        target.write_bytes(fernet.encrypt(b'{"format_version":1,"format_version":1}' if case == 'duplicate-key' else b'\xff'))
    elif case.startswith('missing-'):
        path = {'missing-manifest': target, 'missing-objects': objects, 'missing-managed': target.parent, 'missing-mirror': root}[
            case
        ]
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    elif case.startswith('unknown-'):
        (root / ('unknown' if case == 'unknown-root' else '.obfuscidian/unknown')).write_bytes(b'SYNTHETIC PRIVATE')
    else:
        path = target if case == 'oversize-manifest' else first
        with path.open('wb') as stream:
            stream.truncate(const.MAX_ENCRYPTED_BYTES + 1)
        original = os.open

        def never_open_oversize(name, *args, **kwargs):
            if str(name) in {str(path), path.name}:
                opened_oversize.append(name)
                raise AssertionError('Oversize token was opened.')
            return original(name, *args, **kwargs)

        monkeypatch.setattr(os, 'open', never_open_oversize)
    result = _assert_no_writes(root.parent, _args(root, key, *(['--verbose'] if verbose else [])), monkeypatch)
    assert opened_oversize == []
    assert result.exit_code == (2 if case in {'unknown-root', 'unknown-managed'} else 1), result.output
    assert 'Verified file:' not in result.output and 'Verified complete' not in result.output
    for private in (str(root), str(key), key.read_text(), 'café', 'SYNTHETIC PRIVATE', '.hidden'):
        assert private not in result.output


@pytest.mark.parametrize('location', ['parent', 'ancestor'])
@pytest.mark.parametrize('kind', ['malformed', 'directory', 'broken-link'])
@pytest.mark.parametrize('missing', [False, True])
def test_pending_ownership_is_not_recovered(mirror, monkeypatch, location, kind, missing):
    """Ownership markers of every type block even valid or temporarily absent mirrors."""
    root, key, _ = mirror
    scope = root.parent
    nested = scope / 'nested'
    nested.mkdir()
    root.rename(nested / root.name)
    root = nested / root.name
    name = tx._lock_name(root, _TargetRules(case_sensitive=False, normalization='NFC'))
    marker = (root.parent if location == 'parent' else scope) / name
    if kind == 'malformed':
        marker.write_bytes(b'SYNTHETIC PRIVATE BROKEN RECORD')
    elif kind == 'directory':
        marker.mkdir()
    else:
        try:
            marker.symlink_to(scope / 'absent')
        except OSError:
            pytest.skip('Host cannot create a synthetic symlink.')
    if missing:
        shutil.rmtree(root)
    result = _assert_no_writes(scope, _args(root, key), monkeypatch)
    assert result.exit_code == 1, result.output
    assert 'pending transaction' in result.output and 'separately' in result.output
    assert str(marker) not in result.output and 'SYNTHETIC PRIVATE' not in result.output


def test_retained_completed_workspace_does_not_block(mirror, monkeypatch):
    """Preserve unrelated historic rollback directories without interpreting them."""
    root, key, _ = mirror
    workspace = root.parent / (const.TRANSACTION_PREFIX + 'a' * 32)
    workspace.mkdir()
    (workspace / 'journal.json').write_bytes(b'SYNTHETIC PRIVATE RETAINED')
    result = _assert_no_writes(root.parent, _args(root, key), monkeypatch)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    'option',
    [
        '--yes',
        '--recover',
        '--dry-run',
        '--force',
        '--repair',
        '--write',
        '--log-file',
        '--log-paths',
        '--origin',
        '--exclude',
        '--worktree',
        '--gitdir',
        '--preserve-config',
        '--branch',
        '--base-branch',
    ],
)
def test_write_log_recovery_and_exclusion_options_are_rejected(mirror, monkeypatch, option):
    """Unknown options fail before validation, logging, recovery or destination creation."""
    root, key, _ = mirror
    result = _assert_no_writes(root.parent, _args(root, key, option), monkeypatch)
    assert result.exit_code == 2
    assert 'No such option' in result.output


@pytest.mark.parametrize('selector', ['environment', 'alias', 'relative', 'home', 'override'])
def test_mirror_and_key_resolution_ignores_origin(mirror, monkeypatch, selector):
    """Honor CLI/env precedence without requiring, resolving or inspecting an origin."""
    root, key, _ = mirror
    monkeypatch.setenv(const.ENV_ORIGIN, '')
    arguments = ['verify', '--non-interactive']
    if selector == 'environment':
        monkeypatch.setenv(const.ENV_MIRROR, str(root))
        monkeypatch.setenv(const.ENV_KEY_PATH, str(key))
    elif selector == 'alias':
        arguments += ['--mirror', str(root), '--alias', 'synthetic', '--keydir', str(key.parent)]
        monkeypatch.setenv(const.ENV_KEY_PATH, '')
    elif selector in {'relative', 'home'}:
        prefix = '~/' if selector == 'home' else './'
        arguments += ['--mirror', prefix + root.name, '--key', prefix + key.name]
    else:
        monkeypatch.setenv(const.ENV_MIRROR, '')
        monkeypatch.setenv(const.ENV_KEY_PATH, '')
        arguments = _args(root, key)
    result = _assert_no_writes(root.parent, arguments, monkeypatch)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize('case', ['absent-mirror', 'absent-key', 'empty-mirror', 'empty-key', 'conflict', 'inside-key'])
def test_configuration_failures_and_no_fallback(mirror, monkeypatch, case):
    """Invalid or absent selectors fail with usage status and never regenerate keys."""
    root, key, _ = mirror
    args = _args(root, key)
    if case == 'absent-mirror':
        args = ['verify', '--key', str(key), '--non-interactive']
    elif case == 'absent-key':
        args = ['verify', '--mirror', str(root), '--non-interactive']
    elif case == 'empty-mirror':
        args[2] = ''
    elif case == 'empty-key':
        args[4] = ''
    elif case == 'conflict':
        args += ['--alias', 'synthetic']
    else:
        inside = root / 'obfuscidian-inside.key'
        inside.write_bytes(key.read_bytes())
        args[4] = str(inside)
    result = _assert_no_writes(root.parent, args, monkeypatch, input='synthetic\n')
    assert result.exit_code == 2, result.output
    assert 'Key alias:' not in result.output and 'Mirror vault:' not in result.output


@pytest.mark.parametrize('case', ['success', 'eof', 'invalid', 'non-interactive'])
def test_terminal_only_mirror_and_alias_prompts(mirror, monkeypatch, case):
    """Prompt only for missing selectors on a terminal; explicit opt-out still wins."""
    root, key, _ = mirror
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    result = _assert_no_writes(
        root.parent,
        ['verify'] + (['--non-interactive'] if case == 'non-interactive' else []),
        monkeypatch,
        input='' if case == 'eof' else f'{root}\n{"bad/alias" if case == "invalid" else "synthetic"}\n',
    )
    assert result.exit_code == {'success': 0, 'eof': 1, 'invalid': 2, 'non-interactive': 2}[case], result.output
    assert key.read_text() not in result.output


@pytest.mark.parametrize('failure', [PermissionError, MemoryError, KeyboardInterrupt])
def test_failure_exit_categories_are_redacted(mirror, monkeypatch, failure):
    """Operational failures and interrupts never expose original exception details."""
    root, key, _ = mirror

    def fail(*args, **kwargs):
        raise failure('SYNTHETIC PRIVATE')

    monkeypatch.setattr(manifest, '_verify_mirror', fail)
    result = _assert_no_writes(root.parent, _args(root, key, '--verbose'), monkeypatch)
    assert result.exit_code == (130 if failure is KeyboardInterrupt else 1)
    assert 'SYNTHETIC PRIVATE' not in result.output and 'Verified complete' not in result.output


def test_ownership_appearing_during_validation_blocks_success(mirror, monkeypatch):
    """Reinspect pending ownership after full authentication without recovery calls."""
    root, key, _ = mirror
    original = verification._reject_pending
    calls = []

    def pending_after_validation(path):
        calls.append(path)
        if len(calls) == 1:
            return original(path)
        raise _OperationalError('Mirror has pending transaction ownership.')

    monkeypatch.setattr(verification, '_reject_pending', pending_after_validation)
    result = _assert_no_writes(root.parent, _args(root, key), monkeypatch)
    assert len(calls) == 2 and result.exit_code == 1
    assert 'Verified complete' not in result.output


def test_help_is_read_only(mirror, monkeypatch):
    """Explain the implemented command, read-only restrictions and privacy limits."""
    root, _, _ = mirror
    result = _assert_no_writes(root.parent, ['verify', '--help'], monkeypatch)
    assert result.exit_code == 0
    for word in (
        '--mirror',
        '--key',
        '--alias',
        '--keydir',
        '--non-interactive',
        '--verbose',
        'every',
        'access times',
        'pending',
    ):
        assert word in result.output
    assert ':param' not in result.output and 'versionadded' not in result.output


def test_empty_snapshot_and_read_only_permissions(mirror, monkeypatch):
    """No writable access, space estimates or write plan is needed."""
    root, key, fernet = mirror
    target = root / '.obfuscidian/manifest.obf'
    mapping = json.loads(fernet.decrypt(target.read_bytes()))
    mapping['files'], mapping['directories'] = [], []
    for path in (root / '.obfuscidian/objects').iterdir():
        path.unlink()
    target.write_bytes(fernet.encrypt(json.dumps(mapping).encode()))
    if os.name == 'posix':
        for path in (root, *root.rglob('*'), key):
            path.chmod(0o555 if path.is_dir() else 0o400)
    monkeypatch.setattr(tx, '_plan_transaction', lambda *args, **kwargs: pytest.fail('Verification planned a write.'))
    monkeypatch.setattr(shutil, 'disk_usage', lambda *args, **kwargs: pytest.fail('Verification required staging space.'))
    try:
        result = _assert_no_writes(root.parent, _args(root, key), monkeypatch)
        assert result.exit_code == 0, result.output
        assert '0 files, 0 directories, 0 plaintext bytes' in result.output
    finally:
        if os.name == 'posix':
            for path in (root, *root.rglob('*'), key):
                path.chmod(0o700 if path.is_dir() else 0o600)


@pytest.mark.skipif(os.name == 'nt', reason='Windows rejects control characters in filenames.')
def test_verbose_authenticated_names_escape_terminal_controls(mirror, monkeypatch):
    """Print only opted-in relative names, escaping newline and terminal sequences."""
    root, key, fernet = mirror
    target = root / '.obfuscidian/manifest.obf'
    mapping = json.loads(fernet.decrypt(target.read_bytes()))
    mapping['files'][0]['path'] = 'SYNTHETIC\x1b\nNAME'
    target.write_bytes(fernet.encrypt(json.dumps(mapping).encode()))
    normal = _assert_no_writes(root.parent, _args(root, key), monkeypatch)
    verbose = _assert_no_writes(root.parent, _args(root, key, '--verbose'), monkeypatch)
    assert normal.exit_code == verbose.exit_code == 0
    assert 'SYNTHETIC' not in normal.output
    assert '\\x1b\\nNAME' in verbose.output and '\x1b' not in verbose.output


@pytest.mark.parametrize('which', ['mirror', 'manifest', 'object', 'key'])
def test_unsafe_links_fail_without_writes(mirror, monkeypatch, which):
    """Reject linked inputs without following or modifying their target data."""
    root, key, _ = mirror
    target = {
        'mirror': root,
        'manifest': root / '.obfuscidian/manifest.obf',
        'object': next((root / '.obfuscidian/objects').iterdir()),
        'key': key,
    }[which]
    saved = root.parent / 'saved'
    target.rename(saved)
    try:
        target.symlink_to(saved, target_is_directory=saved.is_dir())
    except OSError:
        pytest.skip('Host cannot create a synthetic symlink.')
    result = _assert_no_writes(root.parent, _args(root, key), monkeypatch)
    assert result.exit_code == 2, result.output
    assert str(saved) not in result.output


def test_missing_selected_key_never_uses_valid_environment_fallback(mirror, monkeypatch):
    """Missing selected keys fail instead of being regenerated or silently replaced."""
    root, key, _ = mirror
    monkeypatch.setenv(const.ENV_KEY_PATH, str(key))
    result = _assert_no_writes(root.parent, _args(root, key.parent / 'absent.key'), monkeypatch)
    assert result.exit_code == 2
    assert 'never generates a replacement' in result.output

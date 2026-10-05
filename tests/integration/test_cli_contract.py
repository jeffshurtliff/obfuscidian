# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_cli_contract
:Synopsis:          Synthetic command-wide privacy, logging and automation contracts
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import importlib
import json
import os
import stat

import pytest
from click.testing import CliRunner

from obfuscidian import backup, keys, output, restore, verification
from obfuscidian import constants as const
from obfuscidian.cli import cli

cli_module = importlib.import_module('obfuscidian.cli')
NAME = 'SYNTHETIC_PRIVATE_NAME-\x1b\n\u202e.md'
CONTENT = b'SYNTHETIC_PRIVATE_CONTENT\r\n\x00\xff'


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Isolate selectors and use a private log directory outside all fixture vaults."""
    for variable in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(variable, raising=False)
    root = tmp_path.resolve()
    monkeypatch.chdir(root)
    origin = root / 'SYNTHETIC_PRIVATE_ORIGIN'
    origin.mkdir()
    name = NAME if os.name == 'posix' else 'SYNTHETIC_PRIVATE_NAME.md'
    (origin / name).write_bytes(CONTENT)
    (origin / 'empty').mkdir()
    key = root / 'SYNTHETIC_PRIVATE_KEY.key'
    keys._generate_key(key)
    logs = root / 'logs'
    logs.mkdir()
    return origin, root / 'mirror', key, logs, name


def _backup(workspace, mode='fresh'):
    origin, mirror, key, _, _ = workspace
    return ['shroud', mode, '--origin', str(origin), '--mirror', str(mirror), '--key', str(key), '--non-interactive']


def _snapshot(root):
    """Observe bytes, namespace, mode and write-related times, excluding read access times."""
    return {
        str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None, p.stat().st_mode, p.stat().st_mtime_ns)
        for p in (root, *root.rglob('*'))
    }


def _records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def _private(workspace, text, *, names=True):
    """Reject paths, material and content independently on each captured stream/log."""
    origin, mirror, key, logs, name = workspace
    for path in (origin, mirror, key, logs):
        assert str(path) not in text
    assert key.read_text() not in text
    assert CONTENT.decode('latin1') not in text
    assert 'SYNTHETIC_PRIVATE_CONTENT' not in text
    if names:
        assert name not in text and 'SYNTHETIC_PRIVATE_NAME' not in text
    assert '\x1b' not in text and '\u202e' not in text


@pytest.mark.parametrize('command', [[], ['keygen'], ['shroud'], ['unshroud'], ['verify']])
@pytest.mark.parametrize('width', [40, 100])
def test_help_is_discoverable_and_read_only(workspace, command, width):
    before = _snapshot(workspace[0].parent)
    result = CliRunner().invoke(cli, [*command, '--help'], terminal_width=width)
    assert result.exit_code == 0
    assert ':param' not in result.stdout and 'versionadded' not in result.stdout
    if command and command != ['verify']:
        assert '--log-file' in result.stdout and '--log-paths' in result.stdout
    if command in (['shroud'], ['unshroud']):
        assert '{fresh|merge}' in result.stdout
    assert _snapshot(workspace[0].parent) == before


@pytest.mark.parametrize(
    'arguments',
    [
        ['SYNTHETIC_PRIVATE_NAME-\x1b'],
        ['--SYNTHETIC_PRIVATE_NAME'],
        ['shroud', 'SYNTHETIC_PRIVATE_NAME-\x1b'],
        ['unshroud', 'SYNTHETIC_PRIVATE_NAME'],
        ['keygen', '--SYNTHETIC_PRIVATE_NAME'],
        ['verify', '--mirror'],
        ['shroud', 'fresh', 'SYNTHETIC_PRIVATE_NAME-\x1b'],
    ],
)
def test_parser_never_echoes_private_values(workspace, arguments):
    before = _snapshot(workspace[0].parent)
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == 2
    assert 'SYNTHETIC_PRIVATE_NAME' not in result.stdout + result.stderr
    assert '\x1b' not in result.stdout + result.stderr
    assert 'help' in result.stderr.lower()
    assert _snapshot(workspace[0].parent) == before


@pytest.mark.parametrize('command', ['keygen', 'shroud', 'unshroud', 'verify'])
def test_unsupported_logging_combinations_are_no_write(workspace, command):
    _, mirror, key, logs, _ = workspace
    args = {
        'keygen': ['keygen', '--alias', 'synthetic', '--dir', str(logs)],
        'shroud': _backup(workspace),
        'unshroud': ['unshroud', 'fresh'],
        'verify': ['verify', '--mirror', str(mirror), '--key', str(key)],
    }[command]
    before = _snapshot(workspace[0].parent)
    for options in (['--log-paths'], ['--log-file', str(logs / 'events.jsonl'), '--dry-run']):
        result = CliRunner().invoke(cli, args + options)
        assert result.exit_code == 2
        assert _snapshot(workspace[0].parent) == before


@pytest.mark.skipif(os.name != 'posix', reason='Native backup mutation is deferred to Thread 12.')
@pytest.mark.parametrize('verbose,log_paths', [(False, False), (True, False), (False, True), (True, True)])
def test_terminal_and_log_disclosure_are_independent(workspace, verbose, log_paths):
    log = workspace[3] / 'events.jsonl'
    arguments = _backup(workspace) + ['--log-file', str(log)]
    if verbose:
        arguments += ['--verbose']
    if log_paths:
        arguments += ['--log-paths']
    before = _snapshot(workspace[0])
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == 0, result.output
    assert 'Progress:' in result.stdout and '\r' not in result.stdout
    if verbose:
        assert repr(workspace[4]) in result.stdout
    else:
        _private(workspace, result.stdout)
    _private(workspace, result.stderr)
    data = log.read_text()
    _private(workspace, data, names=not log_paths)
    assert ('SYNTHETIC_PRIVATE_NAME' in data) == log_paths
    assert _records(log)[-1] == {'command': 'shroud fresh', 'event': 'completed', 'exit_code': 0}
    assert any(record['event'] == 'inventory' for record in _records(log))
    assert stat.S_IMODE(log.stat().st_mode) == 0o600
    assert _snapshot(workspace[0]) == before


@pytest.mark.skipif(os.name != 'posix', reason='Native backup/restore mutation is deferred to Thread 12.')
def test_noop_append_restore_verify_and_read_only_modes(workspace):
    origin, mirror, key, logs, name = workspace
    log = logs / 'events.jsonl'
    first = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log)])
    assert first.exit_code == 0, first.output
    before = _snapshot(mirror)
    prior_log = log.read_bytes()
    noop = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log)])
    assert noop.exit_code == 0 and 'no-op' in noop.stdout
    assert log.read_bytes().startswith(prior_log)
    assert any(r['event'] == 'no-op' for r in _records(log))
    assert _snapshot(mirror) == before
    restored = origin.parent / 'restored'
    args = ['unshroud', 'fresh', '--origin', str(restored), '--mirror', str(mirror), '--key', str(key), '--non-interactive']
    preview = CliRunner().invoke(cli, args + ['--dry-run'])
    assert preview.exit_code == 0 and not restored.exists()
    restore_log = logs / 'restore.jsonl'
    restored_result = CliRunner().invoke(cli, args + ['--log-file', str(restore_log), '--log-paths'])
    assert restored_result.exit_code == 0, restored_result.output
    assert (restored / name).read_bytes() == CONTENT
    _private(workspace, restored_result.stdout)
    assert 'SYNTHETIC_PRIVATE_NAME' in restore_log.read_text()
    assert str(restored) not in restore_log.read_text()
    stable = _snapshot(origin.parent)
    for command in (
        _backup(workspace) + ['--dry-run', '--verbose'],
        ['verify', '--mirror', str(mirror), '--key', str(key), '--non-interactive', '--verbose'],
    ):
        result = CliRunner().invoke(cli, command)
        assert result.exit_code == 0, result.output
        assert _snapshot(origin.parent) == stable


@pytest.mark.parametrize(
    'location',
    [
        'origin',
        'mirror',
        'key',
        'missing-parent',
        'git',
        'stage',
        'rollback',
        'symlink',
        'hardlink',
        'public-existing',
        'directory',
        'parent-link',
    ],
)
def test_unsafe_log_locations_fail_before_mutation(workspace, location):
    origin, mirror, key, logs, _ = workspace
    if location == 'origin':
        log = origin / 'events.jsonl'
    elif location == 'mirror':
        mirror.mkdir()
        log = mirror / 'events.jsonl'
    elif location == 'key':
        log = key
    elif location == 'missing-parent':
        log = logs / 'absent/events.jsonl'
    elif location == 'git':
        (logs / '.git').mkdir()
        log = logs / 'events.jsonl'
    elif location in {'stage', 'rollback'}:
        directory = logs / (
            const.GIT_STAGE_PREFIX + 'synthetic' if location == 'stage' else const.TRANSACTION_PREFIX + 'synthetic'
        )
        directory.mkdir()
        log = directory / 'events.jsonl'
    elif location == 'symlink':
        log = logs / 'link'
        log.symlink_to(key)
    elif location == 'parent-link':
        linked = origin.parent / 'linked'
        linked.symlink_to(logs, target_is_directory=True)
        log = linked / 'events.jsonl'
    elif location == 'hardlink':
        log = logs / 'alias'
        os.link(key, log)
    elif location == 'public-existing':
        log = logs / 'events.jsonl'
        log.write_bytes(b'SYNTHETIC EXISTING LOG\n')
        log.chmod(0o644)
    else:
        log = logs
    before = _snapshot(origin.parent)
    result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log)])
    assert result.exit_code == 2, result.output
    assert _snapshot(origin.parent) == before
    _private(workspace, result.stdout)
    _private(workspace, result.stderr)


@pytest.mark.parametrize('failure', ['permission', 'open', 'parent-change', 'existing-change'])
def test_log_access_and_identity_fail_before_key_creation(workspace, monkeypatch, failure):
    origin, _, _, logs, _ = workspace
    log = logs / 'events.jsonl'
    if failure == 'existing-change':
        log.write_text('SYNTHETIC PRIOR LOG\n')
        log.chmod(0o600)
    if failure == 'permission':
        monkeypatch.setattr(output.os, 'access', lambda *args: False)
    else:
        original = output._Output._open

        def changed(self):
            if failure == 'open':
                raise PermissionError('SYNTHETIC_PRIVATE_CONTENT')
            if failure == 'parent-change':
                logs.rename(logs.with_name('previous'))
                logs.mkdir()
            else:
                log.rename(log.with_name('previous.jsonl'))
                log.write_text('SYNTHETIC USER REPLACEMENT\n')
                log.chmod(0o600)
            return original(self)

        monkeypatch.setattr(output._Output, '_open', changed)
    result = CliRunner().invoke(
        cli, ['keygen', '--alias', 'new', '--dir', str(origin.parent), '--non-interactive', '--log-file', str(log)]
    )
    assert result.exit_code == 1, result.output
    assert not (origin.parent / 'obfuscidian-new.key').exists()
    assert 'SYNTHETIC_PRIVATE_CONTENT' not in result.stdout + result.stderr


@pytest.mark.parametrize('command', ['keygen', 'shroud', 'unshroud', 'verify'])
@pytest.mark.parametrize('exception,code', [(KeyboardInterrupt, 130), (PermissionError, 1), (RuntimeError, 1)])
def test_exit_categories_and_unexpected_errors_are_private(workspace, monkeypatch, command, exception, code):
    origin, mirror, key, logs, _ = workspace
    targets = {
        'keygen': (keys, '_generate_key'),
        'shroud': (backup, '_plan_fresh'),
        'unshroud': (restore, '_plan_restore'),
        'verify': (verification, '_verify_backup'),
    }

    def fail(*args, **kwargs):
        raise exception('SYNTHETIC_PRIVATE_CONTENT ' + str(origin))

    monkeypatch.setattr(*targets[command], fail)
    arguments = {
        'keygen': ['keygen', '--alias', 'new', '--dir', str(logs), '--non-interactive'],
        'shroud': _backup(workspace),
        'unshroud': [
            'unshroud',
            'fresh',
            '--origin',
            str(origin.parent / 'restored'),
            '--mirror',
            str(mirror),
            '--key',
            str(key),
            '--non-interactive',
        ],
        'verify': ['verify', '--mirror', str(mirror), '--key', str(key), '--non-interactive'],
    }[command]
    before = _snapshot(origin.parent)
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == code, result.output
    assert 'Traceback' not in result.stdout + result.stderr
    _private(workspace, result.stdout)
    _private(workspace, result.stderr)
    assert 'snapshot published' not in result.stdout
    assert _snapshot(origin.parent) == before


@pytest.mark.skipif(os.name != 'posix', reason='Native mutation is deferred to Thread 12.')
@pytest.mark.parametrize('response', ['n\n', '', 'y\n'])
def test_confirmation_refusal_eof_and_success(workspace, monkeypatch, response):
    assert CliRunner().invoke(cli, _backup(workspace)).exit_code == 0
    (workspace[0] / workspace[4]).write_bytes(b'SYNTHETIC UPDATE')
    arguments = _backup(workspace)[:-1]
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    before = _snapshot(workspace[1])
    result = CliRunner().invoke(cli, arguments, input=response)
    assert result.exit_code == (0 if response == 'y\n' else 1), result.output
    if response != 'y\n':
        assert _snapshot(workspace[1]) == before
        assert 'snapshot published' not in result.stdout


@pytest.mark.skipif(os.name != 'posix', reason='Native backup mutation is deferred to Thread 12.')
def test_failed_and_interrupted_publication_logs_only_exit_category(workspace, monkeypatch):
    log = workspace[3] / 'failure.jsonl'
    for exception, code in ((RuntimeError, 1), (KeyboardInterrupt, 130)):

        def fail(*args, failure=exception, **kwargs):
            raise failure('SYNTHETIC_PRIVATE_CONTENT')

        monkeypatch.setattr(backup, '_publish_backup', fail)
        result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log), '--verbose'])
        assert result.exit_code == code
        assert _records(log)[-1]['event'] == 'failed'
        assert _records(log)[-1]['exit_code'] == code
        _private(workspace, log.read_text())
        assert 'snapshot published' not in result.stdout


@pytest.mark.skipif(os.name != 'posix', reason='Native backup mutation is deferred to Thread 12.')
def test_logging_write_failure_never_reports_success(workspace, monkeypatch):
    original = output._Output._record

    def fail(self, event, **fields):
        if event == 'completed':
            raise OSError('SYNTHETIC_PRIVATE_CONTENT')
        return original(self, event, **fields)

    monkeypatch.setattr(output._Output, '_record', fail)
    result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(workspace[3] / 'events.jsonl')])
    assert result.exit_code == 1
    assert 'No success is reported' in result.stderr
    _private(workspace, result.stderr)
    # Publication may have completed; the failure must not undo a successful data operation.
    assert workspace[1].is_dir()


@pytest.mark.parametrize('value', ['', '\x00', 'missing-parent/events.jsonl'])
def test_invalid_log_path_is_a_private_usage_error(workspace, value):
    result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', value])
    assert result.exit_code == 2, result.output
    assert 'Traceback' not in result.stderr
    assert not (workspace[3] / 'events.jsonl').exists()


@pytest.mark.skipif(os.name != 'posix', reason='POSIX FIFO fixture.')
def test_special_log_is_rejected_without_blocking(workspace):
    log = workspace[3] / 'pipe'
    os.mkfifo(log, 0o600)
    result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log)])
    assert result.exit_code == 2
    assert not workspace[1].exists()


@pytest.mark.skipif(os.name != 'posix', reason='Native backup publication is deferred to Thread 12.')
def test_changed_open_log_preserves_replacement_and_refuses_publication(workspace, monkeypatch):
    log = workspace[3] / 'events.jsonl'
    old = log.with_name('retained.jsonl')
    original = output._Output._record

    def replace(self, event, **fields):
        if event == 'inventory':
            log.rename(old)
            log.write_bytes(b'SYNTHETIC USER LOG REPLACEMENT\n')
            log.chmod(0o600)
        return original(self, event, **fields)

    monkeypatch.setattr(output._Output, '_record', replace)
    result = CliRunner().invoke(cli, _backup(workspace) + ['--log-file', str(log)])
    assert result.exit_code == 1
    assert not workspace[1].exists()
    assert log.read_bytes() == b'SYNTHETIC USER LOG REPLACEMENT\n'
    assert 'completed' not in old.read_text()


@pytest.mark.parametrize('logging', [False, True])
def test_keygen_logging_is_optional_and_never_ignores_bad_log_custody(workspace, monkeypatch, logging):
    origin, _, _, logs, _ = workspace
    monkeypatch.setenv(const.ENV_ORIGIN, '')
    args = ['keygen', '--alias', 'new', '--dir', str(logs), '--non-interactive']
    if logging:
        args += ['--log-file', str(logs / 'events.jsonl')]
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == (2 if logging else 0), result.output
    assert (logs / 'obfuscidian-new.key').exists() != logging
    assert not (logs / 'events.jsonl').exists()


def test_interrupt_during_argument_handling_exits_130(workspace, monkeypatch):
    """Interrupts outside the callback still share the approved exit category."""

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module._PrivateCommand, 'parse_args', interrupt)
    result = CliRunner().invoke(cli, ['keygen', '--alias', 'synthetic'])
    assert result.exit_code == 130
    assert 'interrupted' in result.stderr
    assert list(workspace[3].iterdir()) == []


@pytest.mark.parametrize('failure', [OSError, KeyboardInterrupt])
def test_log_close_failure_has_a_failure_exit(workspace, monkeypatch, failure):
    original = output._Output._close

    def fail(self):
        original(self)
        raise failure('SYNTHETIC_PRIVATE_CONTENT')

    monkeypatch.setattr(output._Output, '_close', fail)
    result = CliRunner().invoke(
        cli,
        [
            'keygen',
            '--alias',
            'synthetic',
            '--dir',
            str(workspace[3]),
            '--non-interactive',
            '--log-file',
            str(workspace[3] / 'events.jsonl'),
        ],
    )
    assert result.exit_code == (130 if failure is KeyboardInterrupt else 1)
    assert 'SYNTHETIC_PRIVATE_CONTENT' not in result.stderr


def test_interrupt_during_log_write_keeps_original_exit(workspace, monkeypatch):
    def interrupt(self, event, **fields):
        raise KeyboardInterrupt

    monkeypatch.setattr(output._Output, '_record', interrupt)
    result = CliRunner().invoke(
        cli,
        [
            'keygen',
            '--alias',
            'synthetic',
            '--dir',
            str(workspace[3]),
            '--non-interactive',
            '--log-file',
            str(workspace[3] / 'events.jsonl'),
        ],
    )
    assert result.exit_code == 130, result.output
    assert not (workspace[3] / 'obfuscidian-synthetic.key').exists()


def test_git_ownership_appearing_after_log_preflight_blocks_key_creation(workspace, monkeypatch):
    logs = workspace[3]
    original = output._Output._open

    def changed(self):
        (logs / '.git').mkdir()
        return original(self)

    monkeypatch.setattr(output._Output, '_open', changed)
    result = CliRunner().invoke(
        cli, ['keygen', '--alias', 'synthetic', '--dir', str(logs), '--non-interactive', '--log-file', str(logs / 'events.jsonl')]
    )
    assert result.exit_code == 2, result.output
    assert not (logs / 'obfuscidian-synthetic.key').exists()
    assert not (logs / 'events.jsonl').exists()

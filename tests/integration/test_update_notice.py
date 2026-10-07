# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_update_notice
:Synopsis:          Advisory logging, preservation and installed console/module parity
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     07 Oct 2026
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest
from click.testing import CliRunner

from obfuscidian import constants as const
from obfuscidian import keys, updates
from obfuscidian.cli import cli


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Enable a fake stable-release response with isolated keys, vaults and logs."""
    monkeypatch.delenv(const.ENV_SUPPRESS_UPDATE_NOTICE, raising=False)
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(updates, 'version', lambda name: '1.0.0')
    monkeypatch.setattr(updates, '_fetch_releases', lambda: {'releases': {'1.1.0': [{'yanked': False}]}})
    root = tmp_path.resolve()
    monkeypatch.chdir(root)
    (root / 'keys').mkdir()
    (root / 'logs').mkdir()
    return root


@pytest.mark.parametrize('suppressed', [False, True])
def test_keygen_logs_notice_only_after_safe_open(workspace, monkeypatch, suppressed):
    if suppressed:
        monkeypatch.setenv(const.ENV_SUPPRESS_UPDATE_NOTICE, 'true')
    log = workspace / 'logs/keygen.jsonl'
    result = CliRunner().invoke(
        cli, ['keygen', '--alias', 'demo', '--dir', str(workspace / 'keys'), '--non-interactive', '--log-file', str(log)]
    )
    assert result.exit_code == 0, result.output
    records = [json.loads(line) for line in log.read_text().splitlines()]
    notices = [record for record in records if record['event'] == 'update_notice']
    assert len(notices) == (0 if suppressed else 1)
    assert ('A newer version' in result.stderr) is (not suppressed)
    if not suppressed:
        assert notices[0]['message'] + '\n' == result.stderr
        assert records[0]['event'] == 'started' and records[1] == notices[0]
    material = (workspace / 'keys/obfuscidian-demo.key').read_text()
    assert material not in log.read_text() and material not in result.output
    assert str(workspace) not in log.read_text() and str(workspace) not in result.output


@pytest.mark.parametrize('case', ['preflight', 'dry-run', 'read-only', 'unsafe-log'])
def test_notice_cannot_open_logs_or_destinations_during_refusal(workspace, case):
    log = workspace / 'logs/advisory.jsonl'
    if case == 'read-only':
        arguments = ['verify', '--mirror', str(workspace / 'missing'), '--key', str(workspace / 'missing.key')]
    elif case == 'unsafe-log':
        arguments = ['keygen', '--alias', 'demo', '--dir', str(workspace / 'keys'), '--log-file', str(workspace / 'absent/log')]
    else:
        arguments = ['keygen', '--alias', 'demo', '--dir', str(workspace / ('missing' if case == 'preflight' else 'keys'))]
        if case == 'dry-run':
            arguments += ['--dry-run']
        else:
            arguments += ['--log-file', str(log)]
    before = set(workspace.rglob('*'))
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == {'dry-run': 0, 'read-only': 1, 'preflight': 2, 'unsafe-log': 2}[case]
    assert 'A newer version' in result.stderr
    assert set(workspace.rglob('*')) == before
    assert not log.exists()


def test_unavailable_check_neither_logs_nor_changes_success(workspace, monkeypatch):
    def failed():
        raise OSError('SYNTHETIC_PRIVATE_NETWORK_FAILURE')

    monkeypatch.setattr(updates, '_fetch_releases', failed)
    log = workspace / 'logs/keygen.jsonl'
    result = CliRunner().invoke(cli, ['keygen', '--alias', 'demo', '--dir', str(workspace / 'keys'), '--log-file', str(log)])
    assert result.exit_code == 0, result.output
    assert result.stderr == ''
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any(record['event'] == 'update_notice' for record in records)
    assert 'SYNTHETIC_PRIVATE_NETWORK_FAILURE' not in result.output + log.read_text()


@pytest.mark.skipif(os.name == 'nt', reason='Native Windows vault mutation remains intentionally unavailable')
def test_verify_and_backup_dry_run_preserve_bytes_and_write_times(workspace):
    vault = workspace / 'vault'
    vault.mkdir()
    (vault / 'note.md').write_bytes(b'SYNTHETIC\r\n\x00\xff')
    key = workspace / 'keys/demo.key'
    keys._generate_key(key)
    mirror = workspace / 'mirror'
    runner = CliRunner()
    backup_args = ['shroud', 'fresh', '--origin', str(vault), '--mirror', str(mirror), '--key', str(key), '--non-interactive']
    assert runner.invoke(cli, backup_args).exit_code == 0

    def snapshot():
        return {str(p): (p.read_bytes() if p.is_file() else None, p.stat().st_mtime_ns) for p in workspace.rglob('*')}

    before = snapshot()
    for arguments in (
        [*backup_args, '--dry-run'],
        ['verify', '--mirror', str(mirror), '--key', str(key), '--non-interactive'],
        ['unshroud', 'fresh', '--mirror', str(mirror), '--origin', str(workspace / 'restored'), '--key', str(key), '--dry-run'],
    ):
        result = runner.invoke(cli, arguments)
        assert result.exit_code == 0, result.output
        assert result.stderr.count('A newer version') == 1
        assert snapshot() == before
    log = workspace / 'logs/noop.jsonl'
    result = runner.invoke(cli, [*backup_args, '--log-file', str(log)])
    assert result.exit_code == 0 and '(no-op)' in result.output
    assert sum(json.loads(line)['event'] == 'update_notice' for line in log.read_text().splitlines()) == 1


def test_console_and_module_entry_points_share_mocked_notice(tmp_path):
    """Use installed entry-point code with fake PyPI in child processes outside the checkout."""
    script = """
import sys
from importlib.metadata import distribution
from obfuscidian import updates
updates._fetch_releases = lambda: {'releases': {'99.0.0': [{'yanked': False}]}}
entry_mode = sys.argv[1]
sys.argv = ['obfuscidian', '--version']
if entry_mode == 'console':
    entry = next(e for e in distribution('obfuscidian').entry_points if e.group == 'console_scripts' and e.name == 'obfuscidian')
    entry.load()()
else:
    import runpy
    runpy.run_module('obfuscidian', run_name='__main__')
"""
    environment = dict(os.environ)
    environment.pop(const.ENV_SUPPRESS_UPDATE_NOTICE, None)
    results = []
    for entry in ('console', 'module'):
        result = subprocess.run(  # nosec B603: fixed interpreter/script and synthetic response, no live network.
            [sys.executable, '-c', script, entry],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stderr.count('(v99.0.0)') == 1
        assert 'A newer version' not in result.stdout
        results.append((result.stdout, result.stderr))
    assert results[0] == results[1]
    assert list(tmp_path.iterdir()) == []

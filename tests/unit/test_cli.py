# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_cli
:Synopsis:          Verify keygen help, prompts, privacy, and no-mutation behavior
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

import importlib
import io
import os
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import config, keys
from obfuscidian import constants as const
from obfuscidian.cli import cli
from obfuscidian.errors import _OperationalError

cli_module = importlib.import_module('obfuscidian.cli')


@pytest.fixture(autouse=True)
def isolated_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove ambient selectors and keep every potential key inside temporary paths."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('HOME', str(tmp_path.resolve()))
    monkeypatch.setenv('USERPROFILE', str(tmp_path.resolve()))
    monkeypatch.chdir(tmp_path.resolve())


@pytest.mark.parametrize('arguments', [[], ['--help']])
def test_help_describes_current_commands(arguments: list[str], tmp_path: Path) -> None:
    """Expose implemented keygen/fresh backup and keep later commands gated."""
    result = CliRunner().invoke(cli, arguments, prog_name='obfuscidian')
    assert result.exit_code == (2 if not arguments else 0)
    assert 'Usage: obfuscidian [OPTIONS]' in result.output
    assert '--help' in result.output and '--version' in result.output
    assert 'planned' in result.output and 'unavailable' in result.output
    assert 'keygen' in result.output and 'shroud' in result.output
    assert ':returns:' not in result.output and 'versionchanged' not in result.output
    assert list(tmp_path.iterdir()) == []


def test_version_names_product(tmp_path: Path) -> None:
    """Use installed metadata and the product name even under CliRunner."""
    result = CliRunner().invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert result.output == f'obfuscidian, version {version("obfuscidian")}\n'
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('command', ['command', 'unshroud', 'verify'])
def test_unavailable_commands_fail(command: str, tmp_path: Path) -> None:
    """Refuse template and later-thread commands without side effects."""
    result = CliRunner().invoke(cli, [command])
    assert result.exit_code == 2
    assert f"No such command '{command}'" in result.output
    assert list(tmp_path.iterdir()) == []


def test_keygen_help_is_read_only(tmp_path: Path) -> None:
    """Explain aliases, precedence, permissions, custody, and dry run in help."""
    result = CliRunner().invoke(cli, ['keygen', '--help'])
    assert result.exit_code == 0
    for text in ('--alias', '--dir', '--non-interactive', '--dry-run', '--verbose', '0600', 'offline', 'never overwrite'):
        assert text in result.output
    assert ':param' not in result.output and 'versionadded' not in result.output
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('dry_run', [False, True])
def test_missing_alias_fails_without_terminal_prompt(tmp_path: Path, dry_run: bool) -> None:
    """Redirected input never causes prompts, even if it contains a usable alias."""
    args = ['keygen'] + (['--dry-run'] if dry_run else [])
    result = CliRunner().invoke(cli, args, input='synthetic\n')
    assert result.exit_code == 2
    assert 'requires --alias' in result.output
    assert 'Key alias:' not in result.output
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('dry_run', [False, True])
def test_noninteractive_never_prompts_even_on_terminal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dry_run: bool) -> None:
    """Explicit non-interactive mode must still require an explicit alias."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    args = ['keygen', '--non-interactive'] + (['--dry-run'] if dry_run else [])
    result = CliRunner().invoke(cli, args, input='synthetic\n')
    assert result.exit_code == 2
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('response', ['prompt\n', '\n'])
def test_interactive_alias_and_timestamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: str) -> None:
    """Allow empty prompt input as a local-time timestamp, but never overwrite it."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)

    class FrozenDateTime:
        @staticmethod
        def now():
            return datetime(2026, 10, 3, 14, 15, 16)

    monkeypatch.setattr(config, 'datetime', FrozenDateTime)
    alias = 'prompt' if response.strip() else '20261003-141516'
    result = CliRunner().invoke(cli, ['keygen'], input=response)
    assert result.exit_code == 0, result.output
    path = tmp_path.resolve() / f'obfuscidian-{alias}.key'
    assert path.exists()
    assert str(path) in result.output
    material = path.read_bytes()
    assert material.decode() not in result.output
    second = CliRunner().invoke(cli, ['keygen'], input=response)
    assert second.exit_code == 2
    assert path.read_bytes() == material
    assert material.decode() not in second.output


@pytest.mark.parametrize('response', ['', 'bad/alias\n', '\x04'])
def test_prompt_failure_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: str) -> None:
    """Treat EOF as an operational failure and invalid prompted aliases as usage errors."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    result = CliRunner().invoke(cli, ['keygen'], input=response)
    assert result.exit_code == (1 if response == '' else 2)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('selector', ['cli', 'environment'])
@pytest.mark.parametrize('alias', ['', 'bad/alias', 'a' * 65])
def test_explicit_invalid_alias_never_reprompts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selector: str, alias: str
) -> None:
    """Prompt only for an absent alias, not an invalid selected one."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    arguments = ['keygen']
    if selector == 'cli':
        arguments += ['--alias', alias]
        monkeypatch.setenv(const.ENV_KEY_ALIAS, 'valid')
    else:
        monkeypatch.setenv(const.ENV_KEY_ALIAS, alias)
    result = CliRunner().invoke(cli, arguments, input='valid\n')
    assert result.exit_code == 2
    assert 'Key alias (' not in result.output
    assert list(tmp_path.iterdir()) == []


def test_environment_generation_and_cli_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use environment aliases/dirs and ignore KEY_PATH for generation output."""
    environment_dir = tmp_path.resolve() / 'environment'
    environment_dir.mkdir()
    monkeypatch.setenv(const.ENV_KEY_ALIAS, 'environment')
    monkeypatch.setenv(const.ENV_KEY_DIR, str(environment_dir))
    monkeypatch.setenv(const.ENV_KEY_PATH, str(tmp_path / 'ignored.key'))
    first = CliRunner().invoke(cli, ['keygen', '--non-interactive'])
    assert first.exit_code == 0
    assert (environment_dir / 'obfuscidian-environment.key').exists()
    second = CliRunner().invoke(cli, ['keygen', '--alias', 'cli', '--dir', str(tmp_path.resolve()), '--non-interactive'])
    assert second.exit_code == 0
    assert (tmp_path / 'obfuscidian-cli.key').exists()
    assert not (tmp_path / 'ignored.key').exists()
    assert str(tmp_path) not in first.output + second.output


@pytest.mark.parametrize('style', ['relative', 'home', 'absolute'])
def test_paths_with_spaces_and_quotes(tmp_path: Path, style: str) -> None:
    """Use literal quoted/spaced filenames passed as already shell-parsed arguments."""
    directory = tmp_path.resolve() / "keys with 'quotes'"
    directory.mkdir()
    supplied = {'relative': directory.name, 'home': f'~/{directory.name}', 'absolute': str(directory)}[style]
    result = CliRunner().invoke(cli, ['keygen', '--alias', 'synthetic', '--dir', supplied, '--non-interactive'])
    assert result.exit_code == 0, result.output
    path = directory / 'obfuscidian-synthetic.key'
    assert path.read_bytes().decode() not in result.output
    assert str(directory) not in result.output
    cipher, _ = keys._load_key(path)
    assert cipher.decrypt(cipher.encrypt(b'SYNTHETIC')) == b'SYNTHETIC'


@pytest.mark.parametrize('dry_run', [False, True])
def test_existing_key_and_missing_parent_fail(tmp_path: Path, dry_run: bool) -> None:
    """Preserve existing bytes and never create missing directories."""
    path = tmp_path / 'obfuscidian-existing.key'
    original = Fernet.generate_key()
    path.write_bytes(original)
    args = ['keygen', '--alias', 'existing', '--non-interactive'] + (['--dry-run'] if dry_run else [])
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 2
    assert path.read_bytes() == original
    assert original.decode() not in result.output
    missing = CliRunner().invoke(cli, args + ['--dir', str(tmp_path / 'missing')])
    assert missing.exit_code == 2
    assert not (tmp_path / 'missing').exists()


@pytest.mark.parametrize('interactive', [False, True])
def test_dry_run_has_no_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interactive: bool) -> None:
    """Validate an absent target without creating any files, including logs."""
    if interactive:
        monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)
    args = ['keygen', '--dry-run'] + ([] if interactive else ['--alias', 'synthetic', '--non-interactive'])
    result = CliRunner().invoke(cli, args, input='synthetic\n')
    assert result.exit_code == 0, result.output
    assert 'no key or files created' in result.output
    assert list(tmp_path.iterdir()) == []


def test_verbose_path_is_escaped(tmp_path: Path) -> None:
    """Only explicit verbose output may disclose unattended paths; escape controls."""
    directory = tmp_path.resolve() / 'SYNTHETIC\x1b\nPATH'
    if os.name == 'nt':
        pytest.skip('Windows filenames cannot contain these control characters.')
    directory.mkdir()
    args = ['keygen', '--alias', 'synthetic', '--dir', str(directory), '--non-interactive', '--dry-run']
    normal = CliRunner().invoke(cli, args)
    verbose = CliRunner().invoke(cli, args + ['--verbose'])
    assert normal.exit_code == verbose.exit_code == 0
    assert 'SYNTHETIC' not in normal.output
    assert '\\x1b\\nPATH' in verbose.output
    assert '\x1b' not in verbose.output
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize('option', ['--yes', '--recover', '--force', '--key', '--keydir', '--log-file', '--log-paths'])
def test_unsupported_keygen_options_fail(option: str, tmp_path: Path) -> None:
    """No option may bypass no-overwrite or silently enable deferred behavior."""
    result = CliRunner().invoke(cli, ['keygen', '--alias', 'synthetic', option])
    assert result.exit_code == 2
    assert list(tmp_path.iterdir()) == []


def test_operational_failure_and_interrupt_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose operational and interrupt exit categories without claiming success."""

    def fail(*args, **kwargs):
        raise _OperationalError('Cannot create the key; existing keys were preserved.')

    monkeypatch.setattr(keys, '_generate_key', fail)
    failure = CliRunner().invoke(cli, ['keygen', '--alias', 'synthetic', '--non-interactive'])
    assert failure.exit_code == 1

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(keys, '_generate_key', interrupt)
    interrupted = CliRunner().invoke(cli, ['keygen', '--alias', 'synthetic', '--non-interactive'])
    assert interrupted.exit_code == 130
    assert 'interrupted' in interrupted.stderr
    assert list(tmp_path.iterdir()) == []


def test_keyboard_interrupt_during_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Distinguish a real prompt interrupt from EOF; both leave no files."""
    monkeypatch.setattr(cli_module, '_is_interactive', lambda non_interactive: not non_interactive)

    class InterruptedInput(io.BytesIO):
        def read1(self, size: int = -1) -> bytes:
            raise KeyboardInterrupt

    result = CliRunner().invoke(cli, ['keygen'], input=InterruptedInput())
    assert result.exit_code == 130
    assert 'interrupted' in result.stderr
    assert list(tmp_path.iterdir()) == []

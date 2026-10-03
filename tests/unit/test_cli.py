# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_cli
:Synopsis:          Verify the foundation CLI contract
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from importlib.metadata import version
from pathlib import Path

import pytest
from click.testing import CliRunner

from obfuscidian.cli import cli


@pytest.mark.parametrize('arguments', [[], ['--help']])
def test_help_describes_foundation(arguments: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offer useful help without exposing an unimplemented command."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, arguments, prog_name='obfuscidian')
    assert result.exit_code == (2 if not arguments else 0)
    assert 'Usage: obfuscidian [OPTIONS]' in result.output
    assert '--help' in result.output
    assert '--version' in result.output
    assert 'planned and unavailable' in result.output
    assert 'Commands:' not in result.output
    assert ':returns:' not in result.output
    assert 'versionchanged' not in result.output
    assert list(tmp_path.iterdir()) == []


def test_version_names_product(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use installed metadata and the product name even under CliRunner."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert result.output == f'obfuscidian, version {version("obfuscidian")}\n'
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('command', ['command', 'keygen', 'shroud', 'unshroud', 'verify'])
def test_unavailable_commands_fail(command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse template and future commands without side effects."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, [command])
    assert result.exit_code == 2
    assert f"No such command '{command}'" in result.output
    assert list(tmp_path.iterdir()) == []

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.tests.test_obfuscidian
:Synopsis:          The primary pytest module for obfuscidian
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     30 Sep 2026
"""

from click.testing import CliRunner
from obfuscidian.cli import cli


def test_version():
    runner = CliRunner()
    # TODO: Replace the deprecated isolated_filesystem() function
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")

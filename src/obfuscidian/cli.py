# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.cli
:Synopsis:          The foundation CLI for Obfuscidian
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     03 Oct 2026
"""

import click


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(package_name='obfuscidian', prog_name='obfuscidian')
def cli() -> None:
    """Show help and version information for Obfuscidian.

    Obfuscidian will create encrypted Obsidian vault backups. Key generation,
    backup, restore, and verification commands are planned and unavailable.

    \f

    :returns: No value; Click renders help or version information.

    .. versionadded:: 1.0.0
       Removed the template command and identified the product in version output.
    """

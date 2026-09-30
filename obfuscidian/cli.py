# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.cli
:Synopsis:          The primary CLI module for obfuscidian
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     30 Sep 2026
"""

import click


@click.group()
@click.version_option()
def cli():
    """Obfuscate and encrypt your Obsidian vault to create secure and private backups."""


@cli.command(name="command")
@click.argument(
    "example"
)
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def first_command(example, option):
    """Command description goes here"""
    click.echo("Here is some output")

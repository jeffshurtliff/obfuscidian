# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.cli
:Synopsis:          Configuration and secure key generation CLI for Obfuscidian
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     03 Oct 2026
"""

import sys

import click

from obfuscidian import config, keys
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(package_name='obfuscidian', prog_name='obfuscidian')
def cli() -> None:
    """Generate keys for encrypted Obsidian vault backups.

    Keygen is available. Backup, restore, and verification commands are planned
    and unavailable.

    \f

    .. versionadded:: 1.0.0

    :returns: No value; Click dispatches commands or renders help/version.
    """


def _is_interactive(non_interactive: bool) -> bool:
    """Permit prompts and handoff paths only with terminal input and no opt-out."""
    return not non_interactive and sys.stdin.isatty()


def _prompt_alias(*, generation: bool) -> str:
    """Ask for an absent selector, never a replacement for an invalid selector."""
    label = 'Key alias (empty selects local-time YYYYMMDD-HHmmss)' if generation else 'Key alias'
    try:
        return click.prompt(label, default='', show_default=False, type=str)
    except click.Abort as error:
        if isinstance(error.__context__, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        raise _OperationalError('Alias input ended; no key was created or changed.') from None


@cli.command()
@click.option('--alias', type=str, help='ASCII letters, digits, or hyphens (1–64); CLI overrides OBFUSCIDIAN_KEY_ALIAS.')
@click.option('--dir', 'directory', type=str, help='Existing key directory; CLI overrides OBFUSCIDIAN_KEY_DIR, then home.')
@click.option('--non-interactive', is_flag=True, help='Never prompt; require an explicit CLI or environment alias.')
@click.option(
    '--dry-run', is_flag=True, help='Validate the target read-only; generate no key and create no files or directories.'
)
@click.option('--verbose', is_flag=True, help='Show the escaped output path even when unattended; never show key bytes.')
def keygen(alias: str | None, directory: str | None, non_interactive: bool, dry_run: bool, verbose: bool) -> None:
    """Create obfuscidian-ALIAS.key exclusively; never overwrite an existing entry.

    With terminal input, an absent alias prompts; empty input chooses local-time
    YYYYMMDD-HHmmss. Explicit empty aliases are invalid. OBFUSCIDIAN_KEY_PATH
    never selects a generation filename. Expand ~ and resolve relative paths
    from the current directory; shell variables are not interpolated.

    POSIX keys use mode 0600. Windows keys use a protected owner-only DACL where
    supported; privileged access and filesystem ACL limitations still apply.
    Keep keys outside both vaults and cloud repositories, with a separate offline
    backup. A lost key prevents decryption; no reset or recovery bypass exists.

    No force, --yes, --recover, or logging options are available. Unattended
    paths are redacted unless --verbose is selected. Dry run performs the same
    target/collision checks without generating random key material or writing.

    \f

    .. versionadded:: 1.0.0

    :param alias: Explicit generation alias, if supplied.
    :param directory: Existing output directory, if supplied.
    :param non_interactive: Disable all prompts and implicit path disclosure.
    :param dry_run: Validate without creating a key.
    :param verbose: Permit escaped handoff path display.
    :returns: No value; prints the result and custody guidance.
    :raises click.UsageError: Invalid, missing, or unsafe configuration.
    :raises click.ClickException: Operational I/O or input failure.
    """
    interactive = _is_interactive(non_interactive)
    try:
        path = config._resolve_generation_path(
            alias=alias,
            directory=directory,
            alias_prompt=(lambda: _prompt_alias(generation=True)) if interactive else None,
        )
        warnings = keys._generate_key(path, dry_run=dry_run)
    except _ConfigurationError as error:
        raise click.UsageError(str(error)) from None
    except _OperationalError as error:
        raise click.ClickException(str(error)) from None
    except KeyboardInterrupt:
        click.echo('Key generation interrupted; no existing key was changed.', err=True)
        raise click.exceptions.Exit(130) from None
    for warning in warnings:
        click.echo(f'Warning: {warning}', err=True)
    message = (
        'Dry run: key target validated; no key or files created.'
        if dry_run
        else 'Key created securely; existing keys were preserved.'
    )
    click.echo(message)
    if interactive or verbose:
        click.echo(f'Key target: {str(path)!r}')
    click.echo(const.CUSTODY_GUIDANCE)

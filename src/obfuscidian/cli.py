# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.cli
:Synopsis:          Secure keys, encrypted backups, and read-only verification CLI
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
import sys

import click

from obfuscidian import backup, config, keys, verification
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.transactions import _TransactionResult


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(package_name='obfuscidian', prog_name='obfuscidian')
def cli() -> None:
    """Generate keys, back up Obsidian vaults, and verify encrypted mirrors.

    Keygen, shroud fresh/merge, and read-only verify are available. Restore
    commands and optional logging are planned and unavailable.

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


def _prompt_backup(label: str, *, confirmation: bool = False) -> str | bool:
    """Handle EOF and keyboard interrupts in terminal-owned backup prompts."""
    try:
        return click.confirm(label, default=False) if confirmation else click.prompt(label, type=str)
    except click.Abort as error:
        if isinstance(error.__context__, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        raise _OperationalError('Input ended; no backup transaction was started.') from None


def _show_retained(result: _TransactionResult, *, show_paths: bool) -> None:
    """Report retained encrypted recovery data and durability warnings deliberately."""
    for warning in result.warnings:
        click.echo(f'Warning: {warning}', err=True)
    if not result.retained:
        click.echo('Temporary merge recovery data removed after verified publication.')
        return
    click.echo('Encrypted recovery data retained outside the mirror and Git worktrees; no automatic pruning.')
    if show_paths:
        click.echo(f'Recovery workspace: {str(result.workspace)!r}')
        click.echo(f'Rollback location: {str(result.rollback)!r}')


@cli.command()
@click.argument('mode', type=click.Choice(['fresh', 'merge']))
@click.option('--origin', type=str, help='Existing source vault; CLI overrides OBFUSCIDIAN_ORIGIN_VAULT.')
@click.option('--mirror', type=str, help='Encrypted destination; CLI overrides OBFUSCIDIAN_MIRROR_VAULT.')
@click.option('--key', type=str, help='Existing external key; overrides environment selectors; conflicts with --alias/--keydir.')
@click.option('--alias', type=str, help='Key alias; CLI overrides environment key selectors.')
@click.option('--keydir', type=str, help='Alias directory; CLI overrides OBFUSCIDIAN_KEY_DIR, then home.')
@click.option(
    '--exclude', multiple=True, help='Case-sensitive relative component glob; ** spans components; trailing / prunes dirs.'
)
@click.option('--non-interactive', is_flag=True, help='Never prompt; does not imply --yes.')
@click.option('--yes', is_flag=True, help='Consent to replacement/recovery only; never bypass safety or key checks.')
@click.option('--dry-run', is_flag=True, help='Read-only inventory, authentication and space estimate; create no artifacts.')
@click.option(
    '--recover',
    is_flag=True,
    help='Explicitly recover a pending transaction, then retry the selected mode; conflicts with --dry-run.',
)
@click.option(
    '--verbose', is_flag=True, help='Show escaped relative names and private rollback locations; never key bytes/content.'
)
def shroud(
    mode: str,
    origin: str | None,
    mirror: str | None,
    key: str | None,
    alias: str | None,
    keydir: str | None,
    exclude: tuple[str, ...],
    non_interactive: bool,
    yes: bool,
    dry_run: bool,
    recover: bool,
    verbose: bool,
) -> None:
    """Back up current files with fresh replacement or additive merge retention.

    Fresh removes stale and excluded old entries from the new snapshot. Preserve
    origin bytes and mirror root .git/.gitignore in place. Merge retains absent
    and excluded old paths: deleted notes can return during a later restore.
    Renames add a new path and retain the old one. Type conflicts require fresh.
    Reuse authenticated unchanged ciphertext; fresh retains external rollback,
    while successful merge cleans only its own proven temporary recovery data.
    Pause editors/sync during backup and recovery.

    Confirm replacement of existing contents or removal of old files/directories
    in fresh, or existing file content in merge, after preflight. Metadata-only
    updates and additions need no replacement prompt. Unattended replacement/recovery requires --yes. A no-op
    changes no files, timestamps or snapshot IDs and creates no write artifacts.
    Dry run never prompts for replacement or repairs pending transactions.

    Mandatory exclusions: .git components, .gitignore and obfuscidian-*.key files
    at every depth. Other secrets require explicit exclusions. Patterns cannot
    contain absolute paths, .. or backslashes; no negation/re-inclusion exists.
    Selected keys must remain outside both vaults. A wrong key or corrupt mirror
    fails before replacement; no automatic rekeying or key generation exists.

    Restore and optional logging are planned and unavailable; use verify for read-only integrity checks.
    Native Windows mutation fails closed pending platform hardening; read-only dry runs are available.

    \f

    .. versionadded:: 1.0.0

    :param mode: Required fresh or additive merge mode.
    :param origin: Explicit source or environment fallback.
    :param mirror: Explicit destination or environment fallback.
    :param key: Explicit selected key path.
    :param alias: Explicit key alias.
    :param keydir: Alias lookup directory.
    :param exclude: Repeated portable relative exclusion patterns.
    :param non_interactive: Disable all prompts and implicit path disclosure.
    :param yes: Explicit replacement and recovery consent.
    :param dry_run: Validate read-only without creating artifacts.
    :param recover: Restore pending previous state before retrying the operation.
    :param verbose: Permit escaped relative names and private handoff locations.
    :returns: No value; prints counts and a truthful result.
    :raises click.UsageError: Missing, unsafe or conflicting configuration.
    :raises click.ClickException: Integrity, consent or operational failure.
    """
    interactive = _is_interactive(non_interactive)
    try:
        if recover and dry_run:
            raise _ConfigurationError('--recover cannot be combined with --dry-run.')
        source, destination = config._resolve_vault_paths(origin=origin, mirror=mirror)
        if interactive:
            if source is None:
                source = config._expand_path(_prompt_backup('Origin vault'), '--origin')
            if destination is None:
                destination = config._expand_path(_prompt_backup('Mirror vault'), '--mirror')
        if source is None or destination is None:
            raise _ConfigurationError('Select --origin and --mirror or their OBFUSCIDIAN_ORIGIN_VAULT/MIRROR_VAULT variables.')
        selected_key = config._resolve_key_path(
            key=key,
            alias=alias,
            keydir=keydir,
            alias_prompt=(lambda: _prompt_alias(generation=False)) if interactive else None,
        )
        if recover:
            recovered = backup._recover_backup(
                source,
                destination,
                selected_key,
                yes=yes,
                non_interactive=not interactive,
                prompt=(lambda: _prompt_backup('Recover the previous complete snapshot before retrying?', confirmation=True))
                if interactive
                else None,
                exclusions=exclude,
            )
            click.echo(f'Previous state recovered; replanning {mode} backup.')
            _show_retained(recovered, show_paths=interactive or verbose)
        planner = backup._plan_merge if mode == 'merge' else backup._plan_fresh
        plan = planner(source, destination, selected_key, exclusions=exclude)
        for warning in plan.warnings:
            click.echo(f'Warning: {warning}', err=True)
        click.echo(
            f'{mode.capitalize()} inventory: {plan.source.file_count} files, {plan.source.directory_count} directories, '
            f'{plan.source.plaintext_bytes} plaintext bytes; {plan.source.excluded_entries} excluded entries.'
        )
        if mode == 'merge':
            counts = plan.changes
            click.echo(
                f'Merge files: {counts.new} new, {counts.changed} changed, {counts.metadata_only} metadata-only, '
                f'{counts.unchanged} unchanged, {counts.retained} retained absent/excluded.'
            )
            click.echo('Merge retains historic paths; deleted or renamed notes can return during restore.')
        if verbose:
            for entry in plan.source.entries:
                click.echo(f'Included {entry.kind}: {entry.path!r}')
        result = backup._publish_backup(
            plan,
            yes=yes,
            non_interactive=not interactive,
            prompt=(
                lambda: _prompt_backup(
                    'Replace existing file contents?'
                    if mode == 'merge'
                    else 'Replace existing contents or remove stale entries and retain rollback?',
                    confirmation=True,
                )
            )
            if interactive
            else None,
            dry_run=dry_run,
        )
        if dry_run:
            click.echo(
                f'Dry run: {plan.transaction.required_bytes} staged bytes estimated; no files or transaction artifacts created.'
            )
        elif plan.no_op:
            click.echo(f'{mode.capitalize()} backup unchanged (no-op); no files or transaction artifacts created.')
        else:
            click.echo(
                f'{mode.capitalize()} encrypted snapshot published; origin preserved. '
                'Git controls preserved; no Git operations performed.'
            )
            if plan.previous is not None and mode == 'fresh':
                click.echo('Previous complete encrypted snapshot retained for rollback.')
            _show_retained(result, show_paths=interactive or verbose)
    except _ConfigurationError as error:
        raise click.UsageError(str(error)) from None
    except _OperationalError as error:
        raise click.ClickException(f'{error} Origin data was not modified by Obfuscidian.') from None
    except (OSError, MemoryError):
        raise click.ClickException(
            'Backup could not complete; origin preserved. Inspect pending recovery before retrying.'
        ) from None
    except KeyboardInterrupt:
        click.echo(
            'Backup interrupted; origin preserved. Retained transaction artifacts may require --recover before retrying.',
            err=True,
        )
        raise click.exceptions.Exit(130) from None


@cli.command()
@click.option('--mirror', type=str, help='Existing encrypted mirror; CLI overrides OBFUSCIDIAN_MIRROR_VAULT.')
@click.option('--key', type=str, help='Existing external key; overrides environment selectors; conflicts with --alias/--keydir.')
@click.option('--alias', type=str, help='Key alias; CLI overrides environment key selectors.')
@click.option('--keydir', type=str, help='Alias directory; CLI overrides OBFUSCIDIAN_KEY_DIR, then home.')
@click.option('--non-interactive', is_flag=True, help='Never prompt; require mirror and key selectors from CLI/environment.')
@click.option('--verbose', is_flag=True, help='Show escaped authenticated relative names after complete validation.')
def verify(
    mirror: str | None,
    key: str | None,
    alias: str | None,
    keydir: str | None,
    non_interactive: bool,
    verbose: bool,
) -> None:
    """Validate the manifest and every encrypted object without application writes.

    Report counts only by default; --verbose permits escaped relative names
    after the entire snapshot passes. Never print key bytes, hashes or content.
    No origin vault is required, and no exclusions apply. Expand ~ and resolve
    relative paths from the current directory. Prompt for absent mirror/alias
    selectors only with terminal input; invalid selectors never fall back.

    Missing, corrupt, unsupported or pending snapshots fail without repair.
    Inspect pending recovery separately using the backup recovery procedure.
    No --yes, --recover, --dry-run, write, restore or logging options exist.
    Create no paths, locks, worktrees, rollback copies, logs or metadata.

    Validation is a best-effort observation, not an atomic snapshot or security
    certification. OS reads may change access times. A valid historic snapshot
    can pass; this does not prove freshness or target-platform restorability.

    \f

    .. versionadded:: 1.0.0

    :param mirror: Explicit mirror or environment fallback.
    :param key: Explicit selected key path.
    :param alias: Explicit key alias.
    :param keydir: Alias lookup directory.
    :param non_interactive: Disable all prompts.
    :param verbose: Permit escaped authenticated relative names.
    :returns: No value; prints complete validated counts on success.
    :raises click.UsageError: Missing, invalid, unsafe or conflicting configuration.
    :raises click.ClickException: Incomplete, corrupt, pending or unreadable backup.
    """
    interactive = _is_interactive(non_interactive)
    try:
        value = mirror if mirror is not None else os.environ.get(const.ENV_MIRROR)
        if value is None and interactive:
            try:
                value = click.prompt('Mirror vault', type=str)
            except click.Abort as error:
                if isinstance(error.__context__, KeyboardInterrupt):
                    raise KeyboardInterrupt from None
                raise _OperationalError('Mirror input ended; verification did not complete.') from None
        if value is None:
            raise _ConfigurationError('Select --mirror or OBFUSCIDIAN_MIRROR_VAULT.')
        destination = config._expand_path(value, '--mirror')
        selected_key = config._resolve_key_path(
            key=key,
            alias=alias,
            keydir=keydir,
            alias_prompt=(lambda: _prompt_alias(generation=False)) if interactive else None,
        )
        result, warnings = verification._verify_backup(destination, selected_key)
        for warning in warnings:
            click.echo(f'Warning: {warning}', err=True)
        click.echo(
            f'Verified complete v1 mirror: {result.file_count} files, {result.directory_count} directories, '
            f'{result.plaintext_bytes} plaintext bytes, {result.encrypted_bytes} encrypted bytes.'
        )
        if verbose:
            for record in result.manifest.directories:
                click.echo(f'Verified directory: {record.path!r}')
            for record in result.manifest.files:
                click.echo(f'Verified file: {record.path!r}')
        click.echo('Best-effort read-only observation; no application writes performed. OS reads may update access times.')
    except _ConfigurationError as error:
        raise click.UsageError(str(error)) from None
    except _OperationalError as error:
        raise click.ClickException(f'{error} Backup was not modified.') from None
    except (OSError, MemoryError):
        raise click.ClickException(
            'Verification could not complete; check access, memory and other writers. Backup was not modified.'
        ) from None
    except KeyboardInterrupt:
        click.echo('Verification interrupted; no application writes performed.', err=True)
        raise click.exceptions.Exit(130) from None

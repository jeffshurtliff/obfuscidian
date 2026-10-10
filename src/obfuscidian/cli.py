# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.cli
:Synopsis:          Secure keys, encrypted backups, fresh/Git restore and read-only verification CLI
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import os
import shlex
import sys
from functools import wraps
from pathlib import Path

import click

from obfuscidian import backup, config, git_restore, keys, output, restore, updates, verification
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.transactions import _TransactionError, _TransactionResult


class _PrivateCommand(click.Command):
    """Reject malformed arguments without echoing arbitrary private input."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        try:
            return super().parse_args(ctx, args)
        except click.UsageError as error:
            _parser_error(error, ctx)


def _parser_error(error: click.UsageError, ctx: click.Context) -> None:
    """Render usage failures without arbitrary option values, names or positional inputs."""
    if isinstance(error, click.exceptions.NoArgsIsHelpError):
        raise error
    if isinstance(error, click.BadParameter) and error.param is not None:
        label = error.param.opts[0] if error.param.opts else error.param.name
        message = f'Invalid or missing {label}; see --help for allowed values.'
    elif isinstance(error, click.NoSuchOption):
        message = 'No such option; see --help for supported options.'
    else:
        message = 'Unsupported or incomplete arguments; see --help for required mode and supported options.'
    raise click.UsageError(message, ctx) from None


class _PrivateGroup(click.Group):
    """Keep parsing and entry-point failures private, with one product name."""

    command_class = _PrivateCommand

    def make_context(self, info_name: str | None, args: list[str], parent: click.Context | None = None, **extra) -> click.Context:
        """Check once at the root, including eager help/version, but never during completion."""
        notice = None
        if parent is None and not extra.get('resilient_parsing', self.context_settings.get('resilient_parsing', False)):
            notice = updates._notice()
            if notice is not None:
                click.echo(notice, err=True)
        context = super().make_context(info_name, args, parent, **extra)
        if parent is None:
            context.meta['update_notice'] = notice
        return context

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        try:
            return super().parse_args(ctx, args)
        except click.UsageError as error:
            _parser_error(error, ctx)

    def resolve_command(self, ctx: click.Context, args: list[str]):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            raise click.UsageError('Unknown command; choose keygen, shroud, unshroud or verify (see --help).', ctx) from None

    def main(self, *args, **kwargs):
        kwargs.setdefault('prog_name', 'obfuscidian')
        # Application expansion is explicit and identical for console/module on Windows.
        kwargs.setdefault('windows_expand_args', False)
        standalone = kwargs.pop('standalone_mode', True)
        try:
            result = super().main(*args, standalone_mode=False, **kwargs)
        except click.Abort as error:
            interrupted = isinstance(error.__context__, KeyboardInterrupt)
            code = 130 if interrupted else 1
            click.echo(
                'Operation interrupted; inspect retained recovery before retrying.'
                if interrupted
                else 'Input ended; no successful operation is reported.',
                err=True,
            )
            if standalone:
                raise SystemExit(code) from None
            return code
        except click.ClickException as error:
            if not standalone:
                raise
            error.show()
            raise SystemExit(error.exit_code) from None
        except Exception:
            # Entry-point failures outside a command must not produce a raw traceback.
            error = click.ClickException('Operation could not complete; inspect its state before retrying.')
            if not standalone:
                raise error from None
            error.show()
            raise SystemExit(1) from None
        if standalone:
            raise SystemExit(result if isinstance(result, int) else 0)
        return result


def _operation(*, logging: bool = True):
    """Apply one invocation's logging policy and suppress unexpected exception payloads."""

    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            log_file = kwargs.pop('log_file', None)
            log_paths = kwargs.pop('log_paths', False)
            if log_file is not None and kwargs.get('dry_run'):
                raise click.UsageError('--log-file cannot be combined with --dry-run; dry runs never write logs.')
            if log_paths and log_file is None:
                raise click.UsageError('--log-paths requires --log-file.')
            command = function.__name__ + (f' {kwargs["mode"]}' if 'mode' in kwargs else '')
            current = output._Output(command, None, log_paths)
            current.update_notice = click.get_current_context().meta.get('update_notice')
            click.get_current_context().meta['output'] = current
            try:
                if log_file is not None:
                    current.log = config._expand_path(log_file, '--log-file')
                function(*args, **kwargs)
                current._record('completed', exit_code=0)
                if current.log is not None:
                    click.echo('Requested private operational log recorded; handoff locations remain redacted in logs.')
            except (Exception, KeyboardInterrupt) as error:
                code = (
                    error.exit_code
                    if isinstance(error, (click.ClickException, click.exceptions.Exit))
                    else (130 if isinstance(error, KeyboardInterrupt) else 2 if isinstance(error, _ConfigurationError) else 1)
                )
                try:
                    current._record('failed', exit_code=code)
                except (_ConfigurationError, _OperationalError, OSError, KeyboardInterrupt):
                    click.echo('Warning: log recording failed; inspect operation and recovery state before retrying.', err=True)
                if isinstance(error, (click.ClickException, click.exceptions.Exit)):
                    raise
                if isinstance(error, _ConfigurationError):
                    raise click.UsageError(str(error)) from None
                if isinstance(error, KeyboardInterrupt):
                    click.echo('Operation interrupted; inspect retained recovery before retrying.', err=True)
                    raise click.exceptions.Exit(130) from None
                if isinstance(error, _OperationalError):
                    raise click.ClickException(str(error)) from None
                raise click.ClickException(
                    'Operation could not complete; inspect its state and retained recovery before retrying. '
                    'No success is reported.'
                ) from None
            finally:
                failed = sys.exc_info()[0] is not None
                try:
                    current._close()
                except KeyboardInterrupt:
                    click.echo('Log close interrupted; inspect operation state before retrying.', err=True)
                    raise click.exceptions.Exit(130) from None
                except OSError:
                    if not failed:
                        raise click.ClickException('Private log close failed; inspect operation state before retrying.') from None
                    click.echo('Warning: private log close failed; inspect operation state before retrying.', err=True)

        if logging:
            run = click.option(
                '--log-paths',
                is_flag=True,
                help='Permit escaped relative names in the log; requires --log-file. Never absolute paths.',
            )(run)
            run = click.option(
                '--log-file',
                type=str,
                help='Private JSON lines log outside vaults/Git/recovery trees; existing parent; no dry run.',
            )(run)
        return run

    return decorate


@click.group(cls=_PrivateGroup, invoke_without_command=True, no_args_is_help=True)
@click.version_option(package_name='obfuscidian', prog_name='obfuscidian')
def cli() -> None:
    """Generate keys, back up and restore vaults, and verify encrypted mirrors.

    Keygen, shroud fresh/merge, unshroud fresh/merge, and read-only verify are available.
    Write commands support private --log-file records and explicit --log-paths.
    PyPI update notices use stderr; OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE=true disables checks.
    Operation options follow the command; shroud/unshroud require fresh or merge.
    Exit codes: 0 success/dry run/no-op; 1 failure/refusal; 2 usage; 130 interrupt.

    \f

    .. versionadded:: 1.0.0

    .. versionchanged:: 2.0.0
       Update checks use a packaged CA bundle unless SSL_CERT_FILE or SSL_CERT_DIR
       explicitly supplies custom trust.

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
@_operation()
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

    No force, --yes or --recover is available. Logs require an explicit --log-file. Unattended
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
        protected = ()
        if output._current().log is not None:
            protected = tuple(
                config._expand_path(value, 'vault')
                for name in (const.ENV_ORIGIN, const.ENV_MIRROR)
                if (value := os.environ.get(name)) is not None
            )
        output._prepare(protected=protected, key=path)
        output._phase('Validating key target.')
        if not dry_run:
            if output._current().log is not None:
                keys._generate_key(path, dry_run=True)
            output._start()
            output._phase('Creating key exclusively.')
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
        raise _OperationalError('Input ended; no publication or recovery was started.') from None


def _show_retained(result: _TransactionResult, *, show_paths: bool) -> None:
    """Report retained recovery data and its sensitivity with deliberate path disclosure."""
    for warning in result.warnings:
        click.echo(f'Warning: {warning}', err=True)
    if not result.retained:
        click.echo('Temporary merge recovery data removed after verified publication.')
        return
    if result.plaintext:
        click.echo('Plaintext recovery data is sensitive; retained outside vaults and Git worktrees. No automatic pruning.')
    else:
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
@_operation()
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
    updates and additions need no replacement prompt. Unattended replacement/recovery
    requires --yes. A no-op preserves vault files, timestamps and snapshot IDs,
    creating no transaction artifacts; an explicit log may record it. Dry run
    never prompts for replacement or repairs pending transactions.

    Mandatory exclusions: .git components, .gitignore and obfuscidian-*.key files
    at every depth. Other secrets require explicit exclusions. Patterns cannot
    contain absolute paths, .. or backslashes; no negation/re-inclusion exists.
    Selected keys must remain outside both vaults. A wrong key or corrupt mirror
    fails before replacement; no automatic rekeying or key generation exists.

    Use unshroud fresh to restore, or verify for read-only integrity checks.
    Optional --log-file records are redacted; --log-paths permits only relative names.
    Native Windows mutation fails closed pending platform hardening; read-only
    dry runs are available.

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
        output._prepare(protected=(source, destination), key=selected_key)
        output._phase(f'Planning {mode} backup and authenticating any existing snapshot.')
        if recover:
            output._start()
            output._phase('Recovering the previous encrypted state before retrying.')
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
        if not recover and not dry_run:
            output._start()
        output._counts(
            files=plan.source.file_count, directories=plan.source.directory_count, plaintext_bytes=plan.source.plaintext_bytes
        )
        for entry in plan.source.entries:
            output._relative(f'Included {entry.kind}', entry.path, verbose=verbose)
        output._phase('Checking publication consent and stability.' if not dry_run else 'Rechecking read-only proposal.')
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
            click.echo(f'{mode.capitalize()} backup unchanged (no-op); no vault files or transaction artifacts created.')
            if output._current() is not None:
                output._current()._record('no-op')
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
@_operation(logging=False)
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
        output._phase('Authenticating the complete encrypted snapshot.')
        result, warnings = verification._verify_backup(destination, selected_key)
        for warning in warnings:
            click.echo(f'Warning: {warning}', err=True)
        click.echo(
            f'Verified complete v1 mirror: {result.file_count} files, {result.directory_count} directories, '
            f'{result.plaintext_bytes} plaintext bytes, {result.encrypted_bytes} encrypted bytes.'
        )
        for record in result.manifest.directories:
            output._relative('Verified directory', record.path, verbose=verbose)
        for record in result.manifest.files:
            output._relative('Verified file', record.path, verbose=verbose)
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


@cli.command()
@click.argument('mode', type=click.Choice(['fresh', 'merge']))
@click.option('--origin', type=str, help='Fresh destination or merge origin repository; overrides OBFUSCIDIAN_ORIGIN_VAULT.')
@click.option('--mirror', type=str, help='Existing encrypted source; CLI overrides OBFUSCIDIAN_MIRROR_VAULT.')
@click.option('--key', type=str, help='Existing external key; conflicts with --alias/--keydir.')
@click.option('--alias', type=str, help='Key alias; CLI overrides environment key selectors.')
@click.option('--keydir', type=str, help='Alias directory; CLI overrides OBFUSCIDIAN_KEY_DIR, then home.')
@click.option('--preserve-config', is_flag=True, help='Leave root .obsidian in place, including its absence.')
@click.option('--gitdir', type=str, help='Merge only: exact Git directory belonging to origin.')
@click.option('--worktree', type=str, help='Merge only: new restore output with existing parent; default timestamped sibling.')
@click.option('--branch', type=str, help='Merge only: new suffix under obfuscidian/; default timestamped restore suffix.')
@click.option('--base-branch', type=str, help='Merge only: existing local base branch; default main.')
@click.option('--non-interactive', is_flag=True, help='Never prompt; does not imply --yes.')
@click.option('--yes', is_flag=True, help='Consent to plaintext replacement and explicit recovery; safety checks still apply.')
@click.option('--dry-run', is_flag=True, help='Verify and plan read-only; create no plaintext, directories or locks.')
@click.option('--recover', is_flag=True, help='Explicitly recover old plaintext before replanning and retrying fresh restore.')
@click.option('--verbose', is_flag=True, help='Show escaped authenticated relative names and sensitive recovery locations.')
@_operation()
def unshroud(
    mode: str,
    origin: str | None,
    mirror: str | None,
    key: str | None,
    alias: str | None,
    keydir: str | None,
    preserve_config: bool,
    gitdir: str | None,
    worktree: str | None,
    branch: str | None,
    base_branch: str | None,
    non_interactive: bool,
    yes: bool,
    dry_run: bool,
    recover: bool,
    verbose: bool,
) -> None:
    """Restore a verified fresh snapshot or additive uncommitted Git worktree.

    MIRROR is the encrypted source and ORIGIN is the plaintext destination.
    Authenticate every object and validate target names before staging plaintext.
    Replace old payload after consent; preserve root .git/.gitignore in place.
    --preserve-config leaves root .obsidian unchanged, including its absence.
    Other old files, including excluded files, move to external plaintext rollback.
    Nested repositories and unsafe destinations are refused. A merge backup can
    restore stale/deleted notes. Only the destination's final component may be absent.

    Dry run never creates plaintext, destinations, locks or recovery artifacts.
    --recover conflicts with --dry-run. Non-interactive replacement/recovery
    requires --yes. Terminal output redacts paths unless interactive or verbose.
    Timestamp limitations produce warnings; exact bytes and structure are required.
    Merge requires a clean committed origin and local base (default main). It
    restores an additive overlay in a new obfuscidian/ branch and separate worktree,
    retaining base-only files and leaving all restored differences uncommitted.
    Ignored origin data is refused. --gitdir/--worktree/--branch/--base-branch are
    merge-only. Merge --recover is unavailable: retain uncertain artifacts for
    manual inspection. No commit, merge, fetch or push is automatic.
    Optional --log-file records are redacted; --log-paths permits relative names. Native Windows writes fail
    closed pending platform hardening; read-only dry runs remain available.

    \f

    .. versionadded:: 1.0.0

    :param mode: Required fresh replacement or additive Git merge restore.
    :param origin: Explicit plaintext destination or environment fallback.
    :param mirror: Explicit encrypted source or environment fallback.
    :param key: Explicit external selected key path.
    :param alias: Explicit key alias.
    :param keydir: Alias lookup directory.
    :param preserve_config: Preserve destination or merge-base Obsidian configuration.
    :param gitdir: Merge-only Git administration directory belonging to origin.
    :param worktree: Merge-only new output directory.
    :param branch: Merge-only new suffix under obfuscidian/.
    :param base_branch: Merge-only existing local branch, default main.
    :param non_interactive: Disable prompts and implicit path disclosure.
    :param yes: Explicit replacement/recovery consent.
    :param dry_run: Verify and plan without application writes.
    :param recover: Recover the proven previous state before retrying.
    :param verbose: Permit escaped names and private recovery locations.
    :returns: No value; reports verified counts, publication and retention.
    :raises click.UsageError: Invalid, missing, conflicting or unsafe configuration.
    :raises click.ClickException: Integrity, consent, I/O, publication or recovery failure.
    """
    interactive = _is_interactive(non_interactive)
    try:
        if recover and dry_run:
            raise _ConfigurationError('--recover cannot be combined with --dry-run.')
        if mode == 'fresh' and any(value is not None for value in (gitdir, worktree, branch, base_branch)):
            raise _ConfigurationError('--gitdir, --worktree, --branch and --base-branch require merge mode.')
        if mode == 'merge' and recover:
            raise _ConfigurationError('Merge --recover is unavailable; inspect retained worktree and private staging manually.')
        destination, source = config._resolve_vault_paths(origin=origin, mirror=mirror)
        if interactive:
            if destination is None:
                destination = config._expand_path(_prompt_backup('Origin destination'), '--origin')
            if source is None:
                source = config._expand_path(_prompt_backup('Mirror source'), '--mirror')
        if source is None or destination is None:
            raise _ConfigurationError('Select --origin and --mirror or their OBFUSCIDIAN_ORIGIN_VAULT/MIRROR_VAULT variables.')
        selected_key = config._resolve_key_path(
            key=key,
            alias=alias,
            keydir=keydir,
            alias_prompt=(lambda: _prompt_alias(generation=False)) if interactive else None,
        )
        protected = (destination, source)
        if worktree is not None:
            protected += (config._expand_path(worktree, '--worktree'),)
        output._prepare(protected=protected, key=selected_key)
        output._phase(f'Planning {mode} restore and authenticating all objects.')
        if mode == 'merge':
            _unshroud_merge(
                destination,
                source,
                selected_key,
                gitdir=gitdir,
                worktree=worktree,
                branch=branch,
                base_branch=base_branch,
                preserve_config=preserve_config,
                dry_run=dry_run,
                show_paths=interactive or verbose,
                verbose=verbose,
            )
            return
        if recover:
            output._start()
            output._phase('Recovering the previous plaintext state before retrying.')
            recovered = restore._recover_restore(
                destination,
                source,
                selected_key,
                preserve_config=preserve_config,
                yes=yes,
                non_interactive=not interactive,
                prompt=(lambda: _prompt_backup('Recover the previous plaintext state before retrying?', confirmation=True))
                if interactive
                else None,
            )
            click.echo('Previous state recovered; replanning fresh restore.')
            _show_retained(recovered, show_paths=interactive or verbose)
        plan = restore._plan_restore(destination, source, selected_key, preserve_config=preserve_config)
        for warning in plan.warnings:
            click.echo(f'Warning: {warning}', err=True)
        click.echo(
            f'Completely verified snapshot; restoring {len(plan.files)} files, {len(plan.directories)} directories, '
            f'{sum(r.size for r in plan.files)} plaintext bytes.'
        )
        if preserve_config:
            click.echo('Root Obsidian configuration preserved; backup configuration is verified and skipped.')
        if not recover and not dry_run:
            output._start()
        output._counts(files=len(plan.files), directories=len(plan.directories), plaintext_bytes=sum(r.size for r in plan.files))
        for record in (*plan.directories, *plan.files):
            output._relative('Restore entry', record.path, verbose=verbose)
        output._phase('Checking publication consent and stability.' if not dry_run else 'Rechecking read-only proposal.')
        result = restore._publish_restore(
            plan,
            yes=yes,
            non_interactive=not interactive,
            dry_run=dry_run,
            prompt=(
                lambda: _prompt_backup('Replace existing plaintext contents and retain sensitive rollback?', confirmation=True)
            )
            if interactive
            else None,
        )
        if dry_run:
            click.echo(
                f'Dry run: {plan.transaction.required_bytes} staged bytes estimated; no files or transaction artifacts created.'
            )
        else:
            click.echo(
                'Fresh plaintext snapshot published; encrypted mirror and root Git controls preserved. '
                'No Git operations performed.'
            )
            _show_retained(result, show_paths=interactive or verbose)
    except _ConfigurationError as error:
        raise click.UsageError(str(error)) from None
    except _OperationalError as error:
        if isinstance(error, git_restore._MergeFailure):
            click.echo('Retained artifacts may contain sensitive plaintext; review before retrying.', err=True)
            if interactive or verbose:
                click.echo(f'Restore branch: {error.branch!r}; worktree: {str(error.output)!r}', err=True)
                for location in error.retained:
                    click.echo(f'Retained sensitive location: {str(location)!r}', err=True)
        if isinstance(error, _TransactionError):
            raise click.ClickException(f'{error} Retained restore artifacts contain sensitive plaintext.') from None
        raise click.ClickException(str(error)) from None
    except (OSError, MemoryError):
        raise click.ClickException('Restore could not complete; inspect pending recovery before retrying.') from None
    except KeyboardInterrupt:
        click.echo(
            'Merge restore interrupted; inspect retained worktree/private staging manually before retrying.'
            if mode == 'merge'
            else 'Restore interrupted; retained sensitive plaintext artifacts may require --recover before retrying.',
            err=True,
        )
        raise click.exceptions.Exit(130) from None


def _unshroud_merge(
    origin: Path,
    mirror: Path,
    key: Path,
    *,
    gitdir: str | None,
    worktree: str | None,
    branch: str | None,
    base_branch: str | None,
    preserve_config: bool,
    dry_run: bool,
    show_paths: bool,
    verbose: bool,
) -> None:
    """Render a completely validated additive worktree and manual next steps."""
    plan = git_restore._plan_merge(
        origin,
        mirror,
        key,
        gitdir=config._expand_path(gitdir, '--gitdir') if gitdir is not None else None,
        worktree=config._expand_path(worktree, '--worktree') if worktree is not None else None,
        branch=branch,
        base_branch=base_branch if base_branch is not None else 'main',
        preserve_config=preserve_config,
    )
    for warning in plan.reconstruction.warnings:
        click.echo(f'Warning: {warning}', err=True)
    click.echo(
        f'Completely verified merge snapshot: {len(plan.reconstruction.files)} files, '
        f'{len(plan.reconstruction.directories)} directories, '
        f'{sum(r.size for r in plan.reconstruction.files)} plaintext bytes.'
    )
    output._prepare(protected=(origin, mirror, plan.output, plan.gitdir, plan.common), key=key)
    if not dry_run:
        output._start()
    output._counts(
        files=len(plan.reconstruction.files),
        directories=len(plan.reconstruction.directories),
        plaintext_bytes=sum(r.size for r in plan.reconstruction.files),
    )
    for record in (*plan.reconstruction.directories, *plan.reconstruction.files):
        output._relative('Restore entry', record.path, verbose=verbose)
    output._phase('Preparing isolated uncommitted restore.' if not dry_run else 'Rechecking read-only Git proposal.')
    result = git_restore._publish_merge(plan, dry_run=dry_run)
    if dry_run:
        click.echo('Dry run: no plaintext, branch, worktree, locks or recovery artifacts created.')
        return
    click.echo('Additive restore published in a separate worktree; base-only files remain. This is not an exact snapshot.')
    click.echo('Original checkout preserved. Restored differences are unstaged and uncommitted; no restore commit created.')
    click.echo('Review and commit the restored differences before they can be merged. No automatic commit, merge, fetch or push.')
    if preserve_config:
        click.echo('Base Obsidian settings preserved, including their absence; backup settings verified and skipped.')
    click.echo(
        f'Ignored restored/base files requiring manual review: {len(result.ignored)}. '
        'Inspect git status --ignored; selected ignored files may require git add -f.'
    )
    for relative in result.ignored:
        output._relative('Ignored review entry', relative, verbose=verbose)
    if show_paths:
        click.echo(f'Restore branch: {result.branch!r}; worktree: {str(result.output)!r}')
        review = shlex.quote(str(result.output))
        original = shlex.quote(str(origin))
        # POSIX shell instructions are shown escaped to avoid terminal control characters.
        for command in (
            f'git -C {review} status --ignored',
            f'git -C {review} diff --no-ext-diff --no-textconv',
            f'git -C {review} add -- <reviewed-paths>',
            f'git -C {review} commit',
            f'git -C {original} merge -- {shlex.quote(result.branch)}',
        ):
            click.echo(f'Manual command (POSIX shell): {command!r}')
        click.echo('The last merge command is only for later, after committing and reviewing the original checkout.')
    else:
        click.echo('Use --verbose to disclose branch/worktree locations and quoted manual commands.')
    for warning in result.warnings:
        click.echo(f'Warning: {warning}', err=True)
    if result.retained:
        click.echo('Sensitive private plaintext artifacts retained; inspect before manual removal.', err=True)
        if show_paths:
            for location in result.retained:
                click.echo(f'Retained sensitive location: {str(location)!r}', err=True)

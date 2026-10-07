# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.output
:Synopsis:          Private operational logs and deliberate CLI path disclosure
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     07 Oct 2026
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import click

from obfuscidian import constants as const
from obfuscidian import paths
from obfuscidian.errors import _ConfigurationError, _OperationalError


class _Output:
    """Keep operational records separate from terminal-only handoff locations.

    :param command: Fixed command/mode name, never an arbitrary CLI value.
    :param log: Expanded explicit log filename, or None.
    :param log_paths: Explicit consent for relative names in the log.
    """

    def __init__(self, command: str, log: Path | None, log_paths: bool) -> None:
        self.command = command
        self.log = log
        self.log_paths = log_paths
        self.parent: paths._PathState | None = None
        self.existing: paths._PathState | None = None
        self.descriptor: int | None = None
        self.identity: tuple[int, int] | None = None
        self.update_notice: str | None = None

    def _prepare(self, *, protected: tuple[Path, ...], key: Path) -> None:
        """Validate log custody and permissions read-only, before any application write."""
        if self.log is None:
            return
        log = self.log
        if log == key or any(log == root or log.is_relative_to(root) for root in protected):
            raise _ConfigurationError('Log must remain outside keys, both vaults and restore worktrees.')
        if any(part.startswith((const.TRANSACTION_PREFIX, const.GIT_STAGE_PREFIX)) for part in log.parts):
            raise _ConfigurationError('Log cannot be stored in staging or rollback trees.')
        self.parent = paths._inspect_path(log.parent)
        self._check_git_custody()
        if os.name == 'nt':
            from obfuscidian._windows import _check_private_directory

            try:
                _check_private_directory(log.parent)
            except OSError:
                raise _OperationalError('Private Windows logs require accessible persistent ACL storage.') from None
        try:
            info = log.lstat()
        except FileNotFoundError:
            self.existing = None
        except OSError:
            raise _OperationalError('Cannot inspect the log; check access permissions.') from None
        else:
            if paths._is_link(info) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise _ConfigurationError('Log must be a regular file without links, junctions or hard-link aliases.')
            if os.name == 'posix' and stat.S_IMODE(info.st_mode) & 0o077:
                raise _ConfigurationError('Existing log must have private permissions (0600 or stricter); no chmod is automatic.')
            if os.name == 'nt':
                raise _ConfigurationError('Appending existing Windows logs awaits ACL validation; select a new private log.')
            self.existing = paths._inspect_path(log, kind='file')
        if not os.access(log.parent, os.W_OK | os.X_OK) or (self.existing is not None and not os.access(log, os.W_OK)):
            raise _OperationalError('Log location is not writable/searchable; no operation was started.')

    def _check_git_custody(self) -> None:
        """Refuse newly appeared Git ownership as well as pre-existing repositories."""
        # A vault may live in an outer repository. Logs must also stay out of that repository.
        for parent in (self.log.parent, *self.log.parent.parents):
            try:
                (parent / const.GIT_METADATA).lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise _OperationalError('Cannot validate log custody; check directory access.') from None
            raise _ConfigurationError('Log must remain outside Git repositories and worktrees.')

    def _open(self) -> None:
        """Create a private log or append to the inspected file through an anchored parent."""
        if self.log is None:
            return
        if self.parent is None:
            raise _OperationalError('Log custody was not validated; no operation was started.')
        self._check_git_custody()
        descriptor = None
        try:
            with paths._directory_handle(self.parent) as handle:
                if self.existing is not None:
                    paths._recheck_path(self.existing, content=True)
                    flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
                    descriptor = os.open(self.log.name, flags, dir_fd=handle)
                elif os.name == 'nt':
                    from obfuscidian._windows import _create_private_key

                    descriptor = _create_private_key(self.log)
                else:
                    descriptor = os.open(
                        self.log.name,
                        os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        const.LOG_MODE,
                        dir_fd=handle,
                    )
                info = os.fstat(descriptor)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise _OperationalError('Log identity changed; no operation was started.')
                if self.existing is not None and not self.existing.components[-1][1]._same_object(info):
                    raise _OperationalError('Log identity changed; no operation was started.')
                if os.name == 'posix' and stat.S_IMODE(info.st_mode) & 0o077:
                    raise _OperationalError('Log permissions changed; no operation was started.')
                self.identity = (info.st_dev, info.st_ino)
                self.descriptor = descriptor
                descriptor = None
            self._record('started')
            if self.update_notice is not None:
                self._record('update_notice', message=self.update_notice)
        except OSError:
            raise _OperationalError('Cannot open the private log; no operation was started.') from None
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _record(self, event: str, **fields: str | int) -> None:
        """Write only deliberately supplied operational fields, never captured streams/errors."""
        if self.descriptor is None:
            return
        try:
            self._check_git_custody()
            paths._recheck_path(self.parent)
            info = self.log.lstat()
            opened = os.fstat(self.descriptor)
            if (
                paths._is_link(info)
                or info.st_nlink != 1
                or opened.st_nlink != 1
                or (info.st_dev, info.st_ino) != self.identity
                or (os.name == 'posix' and stat.S_IMODE(info.st_mode) & 0o077)
            ):
                raise _OperationalError('Log changed; operation may be incomplete. Inspect retained recovery before retrying.')
            data = memoryview(
                (json.dumps({'command': self.command, 'event': event, **fields}, ensure_ascii=True) + '\n').encode()
            )
            while data:
                written = os.write(self.descriptor, data)
                if written == 0:
                    raise OSError('No log write progress')
                data = data[written:]
            os.fsync(self.descriptor)
        except OSError:
            raise _OperationalError(
                'Operational logging failed; the data operation may have completed. Inspect its state before retrying.'
            ) from None

    def _close(self) -> None:
        """Close the private descriptor even after a failed write or interrupted operation."""
        if self.descriptor is not None:
            descriptor, self.descriptor = self.descriptor, None
            os.close(descriptor)


def _current() -> _Output | None:
    """Find this invocation's output policy without shared mutable global state."""
    context = click.get_current_context(silent=True)
    return context.meta.get('output') if context is not None else None


def _prepare(*, protected: tuple[Path, ...], key: Path) -> None:
    """Validate custody before planning; opening remains a separate write boundary."""
    current = _current()
    if current is not None:
        current._prepare(protected=protected, key=key)


def _start() -> None:
    """Establish optional logging after read-only preflight and before mutation."""
    current = _current()
    if current is not None:
        current._open()


def _phase(message: str) -> None:
    """Render static progress on all streams without animation or control sequences."""
    click.echo(f'Progress: {message}')
    current = _current()
    if current is not None:
        current._record('progress', phase=message)


def _counts(*, files: int, directories: int, plaintext_bytes: int) -> None:
    """Record only validated aggregate inventory values."""
    current = _current()
    if current is not None:
        current._record('inventory', files=files, directories=directories, plaintext_bytes=plaintext_bytes)


def _relative(label: str, value: str, *, verbose: bool) -> None:
    """Disclose escaped relative names independently to terminal and explicitly opted-in logs."""
    if verbose:
        click.echo(f'{label}: {repr(value)}')
    current = _current()
    if current is not None and current.log_paths:
        current._record('path', kind=label, relative=value)

# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_keys
:Synopsis:          Verify synthetic key loading, exclusive creation, and failures
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from cryptography.fernet import Fernet, InvalidToken

from obfuscidian import config, keys
from obfuscidian.errors import _ConfigurationError, _OperationalError


@pytest.fixture
def key_path(tmp_path: Path) -> Path:
    """Use canonical temporary paths so system-level aliases do not mask links."""
    return tmp_path.resolve() / 'obfuscidian-synthetic.key'


def test_generate_load_round_trip_and_no_overwrite(key_path: Path) -> None:
    """Authenticate synthetic binary bytes and preserve a colliding existing key."""
    keys._generate_key(key_path)
    original = key_path.read_bytes()
    before = key_path.stat()
    cipher, warnings = keys._load_key(key_path)
    payload = bytes(range(256)) + b'\0\xffSYNTHETIC'
    token = cipher.encrypt(payload)
    assert cipher.decrypt(token) == payload
    with pytest.raises(InvalidToken):
        Fernet(Fernet.generate_key()).decrypt(token)
    for dry_run in (False, True):
        with pytest.raises(_ConfigurationError, match='never overwritten'):
            keys._generate_key(key_path, dry_run=dry_run)
    assert key_path.read_bytes() == original
    assert key_path.stat().st_mtime_ns == before.st_mtime_ns
    if os.name == 'posix':
        assert stat.S_IMODE(before.st_mode) == 0o600
        assert warnings == ()


@pytest.mark.parametrize('ending', [b'', b'\n', b'\r\n'])
def test_external_key_line_endings(key_path: Path, ending: bytes) -> None:
    """Accept the complete canonical key with at most one conventional line ending."""
    material = Fernet.generate_key()
    key_path.write_bytes(material + ending)
    cipher, _ = keys._load_key(key_path)
    assert cipher.decrypt(Fernet(material).encrypt(b'SYNTHETIC')) == b'SYNTHETIC'


@pytest.mark.parametrize('kind', ['empty', 'short', 'long', 'extra', 'space', 'double-newline', 'nonascii', 'noncanonical'])
def test_invalid_full_keys_are_rejected_without_mutation(key_path: Path, kind: str) -> None:
    """Do not ignore trailing data or regenerate malformed key material."""
    valid = Fernet.generate_key()
    data = {
        'empty': b'',
        'short': valid[:-1],
        'long': b'X' * 10000,
        'extra': valid + b'junk',
        'space': b' ' + valid,
        'double-newline': valid + b'\n\n',
        'nonascii': b'\xff' * 44,
        'noncanonical': valid[:-2] + b'!=',
    }[kind]
    key_path.write_bytes(data)
    before = key_path.stat()
    with pytest.raises(_ConfigurationError, match='valid Fernet') as failure:
        keys._load_key(key_path)
    if data:
        assert data.decode('ascii', errors='replace') not in str(failure.value)
    assert str(key_path) not in str(failure.value)
    assert key_path.read_bytes() == data
    assert key_path.stat().st_mtime_ns == before.st_mtime_ns


def test_missing_selected_key_has_no_environment_fallback(key_path: Path) -> None:
    """An explicit missing key fails even when an environment alias could work."""
    selected = config._resolve_key_path(
        key=str(key_path), environ={'OBFUSCIDIAN_KEY_ALIAS': 'fallback', 'OBFUSCIDIAN_KEY_DIR': str(key_path.parent)}
    )
    with pytest.raises(_ConfigurationError, match='never generates'):
        keys._load_key(selected)
    assert list(key_path.parent.iterdir()) == []


def test_dry_run_does_not_generate_random_material(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read-only validation cannot generate or write a key."""

    def forbidden() -> bytes:
        pytest.fail('A dry run must not generate key material.')

    monkeypatch.setattr(Fernet, 'generate_key', forbidden)
    assert keys._generate_key(key_path, dry_run=True) == ()
    assert list(key_path.parent.iterdir()) == []


@pytest.mark.parametrize('operation', ['generate', 'load'])
def test_missing_parent_and_directory_target_refused(key_path: Path, operation: str) -> None:
    """Do not create parents or treat a directory as a key file."""
    function = keys._generate_key if operation == 'generate' else keys._load_key
    with pytest.raises(_ConfigurationError):
        function(key_path.parent / 'missing' / key_path.name)
    with pytest.raises(_ConfigurationError):
        function(key_path.parent)
    assert list(key_path.parent.iterdir()) == []


@pytest.mark.parametrize('link_kind', ['file', 'dangling', 'directory', 'ancestor'])
def test_links_are_refused_without_touching_referents(key_path: Path, link_kind: str) -> None:
    """Refuse selected links and links in the parent chain."""
    target = key_path.parent / 'referent'
    if link_kind in ('directory', 'ancestor'):
        target.mkdir()
    else:
        target.write_bytes(b'SYNTHETIC EXISTING DATA')
    try:
        if link_kind in ('directory', 'ancestor'):
            linked = key_path.parent / 'linked'
            linked.symlink_to(target, target_is_directory=True)
            path = linked / key_path.name
            if link_kind == 'ancestor':
                path = linked / '..' / key_path.name
        else:
            key_path.symlink_to(target if link_kind == 'file' else target.with_name('absent'))
            path = key_path
    except OSError:
        pytest.skip('This platform/user cannot create symlinks.')
    for operation in (keys._generate_key, keys._load_key):
        with pytest.raises(_ConfigurationError):
            operation(path)
    if target.is_file():
        assert target.read_bytes() == b'SYNTHETIC EXISTING DATA'
    else:
        assert list(target.iterdir()) == []


@pytest.mark.skipif(os.name != 'posix', reason='FIFO and POSIX mode semantics.')
def test_fifo_refused_without_blocking(key_path: Path) -> None:
    """Refuse special files before attempting a read."""
    os.mkfifo(key_path)
    for operation in (keys._generate_key, keys._load_key):
        with pytest.raises(_ConfigurationError):
            operation(key_path)
    assert stat.S_ISFIFO(key_path.lstat().st_mode)


@pytest.mark.skipif(os.name != 'posix', reason='POSIX permission assessment.')
def test_insecure_permissions_warn_without_chmod(key_path: Path) -> None:
    """Assess permissions, but preserve existing key bytes and mode."""
    key_path.write_bytes(Fernet.generate_key())
    key_path.chmod(0o644)
    before = key_path.read_bytes()
    _, warnings = keys._load_key(key_path)
    assert len(warnings) == 1 and '0600' in warnings[0]
    assert key_path.read_bytes() == before
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o644


@pytest.mark.skipif(os.name != 'posix', reason='POSIX descriptor-based secure creation.')
def test_create_permission_error_preserves_existing_sibling(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Translate access failures without disclosing paths or modifying other keys."""
    existing = key_path.with_name('existing.key')
    existing.write_bytes(Fernet.generate_key())
    before = existing.read_bytes()
    original_open = os.open

    def deny_create(path, flags, *args, **kwargs):
        if flags & os.O_CREAT:
            raise PermissionError('SYNTHETIC PRIVATE PATH must not be displayed')
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', deny_create)
    with pytest.raises(_OperationalError) as failure:
        keys._generate_key(key_path)
    assert 'SYNTHETIC PRIVATE' not in str(failure.value)
    assert not key_path.exists()
    assert existing.read_bytes() == before


@pytest.mark.parametrize('failure_kind', ['write', 'fsync', 'interrupt'])
def test_failed_creation_cleans_only_owned_key(key_path: Path, monkeypatch: pytest.MonkeyPatch, failure_kind: str) -> None:
    """Remove an incomplete new key after partial I/O or interruption."""
    existing = key_path.with_name('existing.key')
    existing.write_bytes(b'SYNTHETIC EXISTING KEY')
    original_write = os.write

    def partial_then_fail(descriptor: int, data) -> int:
        original_write(descriptor, data[:3])
        if failure_kind == 'interrupt':
            raise KeyboardInterrupt
        raise OSError('SYNTHETIC PRIVATE ERROR')

    def fail_sync(descriptor: int) -> None:
        raise OSError('SYNTHETIC PRIVATE ERROR')

    monkeypatch.setattr(
        os, 'fsync' if failure_kind == 'fsync' else 'write', fail_sync if failure_kind == 'fsync' else partial_then_fail
    )
    expected = KeyboardInterrupt if failure_kind == 'interrupt' else _OperationalError
    with pytest.raises(expected):
        keys._generate_key(key_path)
    assert not key_path.exists()
    assert existing.read_bytes() == b'SYNTHETIC EXISTING KEY'


@pytest.mark.skipif(os.name != 'posix', reason='POSIX atomic O_EXCL race injection.')
def test_creation_race_preserves_winning_key(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Enforce no-overwrite at open, even when the preflight target was absent."""
    original_open = os.open
    winner = Fernet.generate_key()

    def racing_open(path, flags, *args, **kwargs):
        if flags & os.O_CREAT:
            key_path.write_bytes(winner)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', racing_open)
    with pytest.raises(_ConfigurationError, match='never overwritten'):
        keys._generate_key(key_path)
    assert key_path.read_bytes() == winner


def test_loading_permission_error_is_redacted(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Never replace an unreadable key or echo an OS exception's private path."""
    keys._generate_key(key_path)
    material = key_path.read_bytes()
    original_open = os.open

    def deny_read(path, flags, *args, **kwargs):
        if not flags & getattr(os, 'O_DIRECTORY', 0):
            raise PermissionError(material.decode() + str(key_path))
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', deny_read)
    with pytest.raises(_OperationalError) as failure:
        keys._load_key(key_path)
    assert material.decode() not in str(failure.value)
    assert str(key_path) not in str(failure.value)
    assert key_path.read_bytes() == material


@pytest.mark.skipif(os.name != 'posix', reason='POSIX protected directory identity checks.')
def test_parent_substitution_is_refused(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse a changed directory identity between inspection and open."""
    directory = key_path.parent / 'keys'
    directory.mkdir()
    selected = directory / key_path.name
    moved = directory.with_name('moved')
    original_inspect = keys._inspect

    def replace_parent(path: Path, *, creating: bool):
        identities = original_inspect(path, creating=creating)
        directory.rename(moved)
        directory.mkdir()
        return identities

    monkeypatch.setattr(keys, '_inspect', replace_parent)
    with pytest.raises(_ConfigurationError, match='changed'):
        keys._generate_key(selected)
    assert list(directory.iterdir()) == list(moved.iterdir()) == []


@pytest.mark.skipif(os.name != 'posix' or os.getuid() == 0, reason='Requires an unprivileged POSIX permission model.')
def test_actual_permission_denial_and_dry_run(key_path: Path) -> None:
    """Reject read-only output directories and unreadable existing keys."""
    directory = key_path.parent / 'private'
    directory.mkdir()
    selected = directory / key_path.name
    directory.chmod(0o500)
    try:
        for dry_run in (True, False):
            with pytest.raises(_OperationalError):
                keys._generate_key(selected, dry_run=dry_run)
        assert list(directory.iterdir()) == []
    finally:
        directory.chmod(0o700)
    keys._generate_key(selected)
    before = selected.read_bytes()
    selected.chmod(0o000)
    try:
        with pytest.raises(_OperationalError):
            keys._load_key(selected)
    finally:
        selected.chmod(0o600)
    assert selected.read_bytes() == before


@pytest.mark.skipif(os.name != 'posix', reason='POSIX descriptor failure injection.')
def test_failed_cleanup_reports_retained_entry(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep uncertain partial data and give recovery guidance when cleanup fails."""

    def fail_sync(descriptor: int) -> None:
        raise OSError('SYNTHETIC fsync failure')

    def deny_unlink(*args, **kwargs) -> None:
        raise PermissionError('SYNTHETIC unlink failure')

    monkeypatch.setattr(os, 'fsync', fail_sync)
    monkeypatch.setattr(os, 'unlink', deny_unlink)
    with pytest.raises(_OperationalError, match='incomplete key may remain') as failure:
        keys._generate_key(key_path)
    assert key_path.is_file()
    assert key_path.read_bytes().decode() not in str(failure.value)


@pytest.mark.skipif(os.name != 'posix', reason='POSIX creation/identity race injection.')
def test_replacement_after_write_failure_is_preserved(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Cleanup must never remove a competing replacement key."""
    replacement = Fernet.generate_key()
    saved = key_path.with_name('failed-entry.key')

    def replace_then_fail(descriptor: int) -> None:
        key_path.rename(saved)
        key_path.write_bytes(replacement)
        raise OSError('SYNTHETIC fsync failure')

    monkeypatch.setattr(os, 'fsync', replace_then_fail)
    with pytest.raises(_OperationalError, match='target changed'):
        keys._generate_key(key_path)
    assert key_path.read_bytes() == replacement
    assert saved.is_file()


@pytest.mark.skipif(os.name != 'posix', reason='POSIX secure permission setup failure injection.')
def test_permission_setup_failure_removes_new_entry(key_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not leave a newly created key if restrictive mode setup fails."""

    def deny_chmod(*args, **kwargs) -> None:
        raise PermissionError('SYNTHETIC mode failure')

    monkeypatch.setattr(os, 'fchmod', deny_chmod)
    with pytest.raises(_OperationalError):
        keys._generate_key(key_path)
    assert not key_path.exists()

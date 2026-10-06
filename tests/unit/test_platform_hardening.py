# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_platform_hardening
:Synopsis:          Portable path, resource and descriptor failure boundaries
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from obfuscidian import _windows, backup, crypto, git_restore, inventory, keys, manifest, output, paths, restore, transactions
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError, _OperationalError


@pytest.mark.parametrize('relative', ['//server/share/a', 'C:', 'C:note', 'C:/note', '\\server\\share', '\\?\\C:\\note'])
def test_drive_and_unc_names_never_become_relative_payloads(relative: str) -> None:
    """Reject all serialized drive/UNC spellings on every host."""
    for windows in (False, True):
        with pytest.raises(_ConfigurationError):
            paths._validate_relative_path(relative, windows=windows)


@pytest.mark.parametrize(
    'name', ['CON.txt', 'NUL .txt', 'LPT¹.log', 'COM²', 'AUX', 'note:stream', 'folder./note', 'folder /note']
)
def test_windows_device_stream_and_lossy_names(name: str) -> None:
    """Refuse device names, streams and stripped components without normalization."""
    with pytest.raises(_ConfigurationError):
        paths._validate_relative_path(name, windows=True)


@pytest.mark.parametrize('normalization', ['NFC', 'NFD'])
@pytest.mark.parametrize('names', [('CAFÉ/a', 'cafe\u0301/b'), ('Folder/a', 'folder/b')])
def test_ambiguous_ancestor_names_are_refused(tmp_path: Path, normalization: str, names: tuple[str, str]) -> None:
    """Case/Unicode ambiguity in a parent cannot overwrite another subtree."""
    with pytest.raises(_ConfigurationError, match='collide'):
        paths._validate_target_paths(names, paths._TargetRules(False, normalization), destination=tmp_path.resolve())
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('windows,units', [(False, 4), (True, 2)])
def test_multibyte_path_limit_at_exact_boundary(tmp_path: Path, windows: bool, units: int) -> None:
    """Enforce full target and component limits in bytes or UTF-16 code units."""
    target = tmp_path.resolve() / 'absent'
    full = str(target / '😀')
    limit = len(full.encode('utf-16-le')) // 2 if windows else len(full.encode('utf-8'))
    rules = paths._TargetRules(False, windows=windows, component_limit=units, path_limit=limit)
    paths._validate_target_paths(['😀'], rules, destination=target)
    with pytest.raises(_ConfigurationError):
        paths._validate_target_paths(['😀x'], rules, destination=target)
    assert not target.exists()


@pytest.mark.parametrize('size', [1022, 1023, 1024])
def test_bounded_actual_cipher_boundary(monkeypatch: pytest.MonkeyPatch, size: int) -> None:
    """Exercise an actual token at a reduced cap, avoiding a 50 MiB allocation."""
    monkeypatch.setattr(const, 'MAX_ENCRYPTED_BYTES', inventory._fernet_size(1023))
    cipher = Fernet(Fernet.generate_key())
    data = b'x' * size
    if size <= 1023:
        token = crypto._encrypt_bytes(data, cipher)
        assert crypto._decrypt_bytes(token, cipher) == data
        assert len(token) <= const.MAX_ENCRYPTED_BYTES
    else:
        with pytest.raises((_ConfigurationError, manifest._FormatError)):
            crypto._encrypt_bytes(data, cipher)


@pytest.mark.parametrize('reader', ['key', 'source', 'mirror'])
@pytest.mark.parametrize('failure', [MemoryError, OSError])
def test_stream_allocation_failure_closes_owned_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reader: str, failure: type[Exception]
) -> None:
    """Resource failures return no bytes and do not leak the opened file handle."""
    root = tmp_path.resolve()
    file = root / 'synthetic.bin'
    file.write_bytes(Fernet.generate_key() if reader == 'key' else b'SYNTHETIC\r\n\x1a\xff')
    observed = inventory._scan_inventory(root)
    state = paths._inspect_path(file, kind='file')
    descriptors = []
    original_open, original_fdopen = os.open, os.fdopen

    def opened(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if str(path) in {file.name, str(file)}:
            descriptors.append(descriptor)
        return descriptor

    def fail(descriptor, *args, **kwargs):
        if descriptor in descriptors:
            raise failure('SYNTHETIC PRIVATE ERROR')
        return original_fdopen(descriptor, *args, **kwargs)

    monkeypatch.setattr(os, 'open', opened)
    monkeypatch.setattr(os, 'fdopen', fail)
    with pytest.raises(_OperationalError) as error:
        if reader == 'key':
            keys._load_key(file)
        elif reader == 'source':
            inventory._read_file(observed, observed.entries[0])
        else:
            manifest._read_token(state)
    assert 'SYNTHETIC PRIVATE ERROR' not in str(error.value)
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


def test_path_based_capture_uses_absolute_binary_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The non-dir-fd observation path reads the intended bytes outside the cwd."""
    file = tmp_path.resolve() / 'synthetic.bin'
    file.write_bytes(bytes(range(256)) + b'\r\n\x1a')

    @contextmanager
    def path_based(state):
        paths._recheck_path(state)
        yield None
        paths._recheck_path(state)

    monkeypatch.setattr(transactions, '_directory_handle', path_based)
    import hashlib

    captured = transactions._capture(file)
    assert captured['digest'] == hashlib.sha256(file.read_bytes()).hexdigest()
    assert captured['size'] == 259


def test_private_windows_creation_refuses_unassessable_acl_before_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every private Windows file caller checks persistent ACLs before creation."""
    target = tmp_path.resolve() / 'events.jsonl'

    def unavailable(parent: Path) -> None:
        assert parent == target.parent
        raise OSError('SYNTHETIC ACL FAILURE')

    monkeypatch.setattr(_windows, '_check_private_directory', unavailable)
    with pytest.raises(OSError):
        _windows._create_private_key(target)
    monkeypatch.setattr(output, 'os', SimpleNamespace(name='nt'))
    with pytest.raises(_OperationalError, match='persistent ACL'):
        output._Output('synthetic', target, False)._prepare(protected=(), key=target.with_suffix('.key'))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(os.name != 'posix', reason='Shared backup/restore staging is POSIX-only.')
@pytest.mark.parametrize('failure', [OSError, MemoryError])
def test_failed_staged_stream_allocation_closes_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: type[Exception]
) -> None:
    """Shared staging failures retain the partial entry but release its file handle."""
    opened = []
    original = os.open

    def track(path, *args, **kwargs):
        descriptor = original(path, *args, **kwargs)
        if str(path) == 'synthetic.bin':
            opened.append(descriptor)
        return descriptor

    def fail(*args, **kwargs):
        raise failure('SYNTHETIC STREAM FAILURE')

    monkeypatch.setattr(os, 'open', track)
    monkeypatch.setattr(os, 'fdopen', fail)
    with pytest.raises(_OperationalError if failure is OSError else failure):
        backup._write_token(tmp_path.resolve(), 'synthetic.bin', b'SYNTHETIC')
    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])
    assert (tmp_path / 'synthetic.bin').read_bytes() == b''


@pytest.mark.skipif(os.name != 'posix', reason='Git overlay copying is guarded by the POSIX mutation boundary.')
def test_git_overlay_allocation_failure_closes_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failure creating the Git overlay stream releases its source descriptor."""
    root = tmp_path.resolve()
    source, target = root / 'source', root / 'target'
    source.mkdir()
    target.mkdir()
    (source / 'synthetic.bin').write_bytes(b'SYNTHETIC')
    captured = transactions._capture(source)
    original = os.fdopen
    descriptors = []

    def failed(descriptor, mode, *args, **kwargs):
        if kwargs.get('closefd') is not False:
            descriptors.append(descriptor)
            raise MemoryError('SYNTHETIC STREAM FAILURE')
        return original(descriptor, mode, *args, **kwargs)

    monkeypatch.setattr(os, 'fdopen', failed)
    with pytest.raises(MemoryError):
        git_restore._copy_tree(source, target, captured, set())
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
    assert list(target.iterdir()) == []
    assert (source / 'synthetic.bin').read_bytes() == b'SYNTHETIC'


@pytest.mark.skipif(os.name != 'posix', reason='Timestamp application belongs to existing POSIX restore staging.')
def test_unavailable_timestamp_preserves_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unsupported timestamps are recorded while exact bytes remain mandatory."""
    file = tmp_path.resolve() / 'synthetic.bin'
    file.write_bytes(b'SYNTHETIC\r\n\x00\xff')
    before = file.read_bytes()
    unsupported = set()

    def fail(*args, **kwargs):
        raise OSError('SYNTHETIC UNSUPPORTED TIME')

    monkeypatch.setattr(os, 'utime', fail)
    restore._set_time(file, 0, unsupported, 'synthetic.bin')
    assert unsupported == {'synthetic.bin'}
    assert file.read_bytes() == before

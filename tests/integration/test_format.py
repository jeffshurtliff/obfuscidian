# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_format
:Synopsis:          Immutable v1 compatibility and complete read-only hostile mirror tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from dataclasses import replace
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import manifest as fmt
from obfuscidian.cli import cli
from obfuscidian.crypto import _new_id, _sha256
from obfuscidian.errors import _ConfigurationError, _FormatError, _OperationalError
from obfuscidian.inventory import _read_file, _scan_inventory, _verify_inventory
from obfuscidian.paths import _TargetRules

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/v1'
# Pin artifacts independently of the fixture's checksum file. Never regenerate in tests.
OBJECT_PREFIX = 'mirror/.obfuscidian/objects/'
PINNED_HASHES = {
    'mirror/.obfuscidian/manifest.obf': 'fc7dd9e02eee9d5c583579b3ba70332db40c0efb5c9b0e2de70ef91771ddbb38',
    f'{OBJECT_PREFIX}00000000000000000000000000000001.obf': 'bf8bd9188682e7daea53164afcac075c80f1bda296ead084c2fb799ee13cb2c7',
    f'{OBJECT_PREFIX}00000000000000000000000000000002.obf': 'afaf563e49a380b6b9a9cee3c653d70bba8aced215beb65aed52ff85f89dd7a8',
    f'{OBJECT_PREFIX}00000000000000000000000000000003.obf': '5ff0af7e59bf05830ed790a1a56b09572d5fabde6f9b52d9a7288364d76c8001',
    f'{OBJECT_PREFIX}00000000000000000000000000000004.obf': '9be8839082f11775a4c5ffe4e90fb0e045ee52a66031847bd15ed982fb689a19',
    f'{OBJECT_PREFIX}00000000000000000000000000000005.obf': 'fbc8a84e84ff07141132e880273b7de75366d0ca0157e52e465925ed6529bf2c',
    'synthetic-fernet-key.txt': '7d3a1c8c0fb3f26a4cb1cd78f37751d39dd8d37addb78103d8a346d010eeccdc',
}
CONTENTS = {
    '.hidden': b'SYNTHETIC HIDDEN\n',
    '.obsidian/settings.json': b'{"synthetic": true}\r\n',
    'attachments/all-bytes.bin': bytes(range(256)),
    'notes/café-日本語.md': '# SYNTHETIC café 日本語\r\n'.encode(),
    'zero.bin': b'',
}


@pytest.fixture
def mirror(tmp_path: Path) -> tuple[Path, Fernet]:
    """Copy only immutable public synthetic bytes into an isolated temporary mirror."""
    root = tmp_path.resolve() / 'synthetic-mirror'
    shutil.copytree(FIXTURE / 'mirror', root)
    return root, Fernet((FIXTURE / 'synthetic-fernet-key.txt').read_bytes().strip())


def _snapshot(root: Path) -> dict:
    """Compare content/identity/times while allowing access-time effects of reads."""
    result = {}
    for path in (root, *root.rglob('*')):
        info = path.lstat()
        digest = _sha256(path.read_bytes()) if stat.S_ISREG(info.st_mode) else None
        result[path.relative_to(root).as_posix()] = (
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            digest,
        )
    return result


def _raw_manifest(mirror: Path, fernet: Fernet) -> dict:
    """Authenticate fixture metadata independently for test-only mutations."""
    return json.loads(fernet.decrypt((mirror / '.obfuscidian/manifest.obf').read_bytes()))


def _replace_manifest(mirror: Path, fernet: Fernet, mapping: dict) -> None:
    """Write an authenticated adversarial manifest only in a temporary test copy."""
    (mirror / '.obfuscidian/manifest.obf').write_bytes(fernet.encrypt(json.dumps(mapping).encode()))


def _object(mirror: Path, mapping: dict, index: int = 0) -> Path:
    """Locate a synthetic fixture object by its already known test ID."""
    return mirror / '.obfuscidian/objects' / (mapping['files'][index]['object_id'] + '.obf')


def _assert_failure_read_only(mirror: Path, fernet: Fernet, capsys: pytest.CaptureFixture[str], **kwargs: object) -> None:
    """Assert failure preserves the complete temporary parent and emits no private data."""
    before = _snapshot(mirror.parent)
    with pytest.raises((_ConfigurationError, _OperationalError)) as error:
        fmt._verify_mirror(mirror, fernet, **kwargs)
    assert _snapshot(mirror.parent) == before
    assert str(mirror) not in str(error.value)
    assert 'café' not in str(error.value)
    assert 'SYNTHETIC PRIVATE' not in str(error.value)
    output = capsys.readouterr()
    assert output.out == output.err == ''


def test_fixture_bytes_are_pinned() -> None:
    """Fixture tokens and public key cannot change as a side effect of refactoring."""
    assert json.loads((FIXTURE / 'SHA256SUMS.json').read_text()) == PINNED_HASHES
    actual = {name: hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() for name in PINNED_HASHES}
    assert actual == PINNED_HASHES
    assert {path.relative_to(FIXTURE / 'mirror').as_posix() for path in (FIXTURE / 'mirror').rglob('*') if path.is_file()} == {
        name.removeprefix('mirror/') for name in PINNED_HASHES if name.startswith('mirror/')
    }


def test_frozen_fixture_exact_reconstruction_and_reuse(mirror: tuple[Path, Fernet], capsys: pytest.CaptureFixture[str]) -> None:
    """Verify all historic bytes, signed times, empty directories, and exact token reuse."""
    root, fernet = mirror
    (root / '.git').mkdir()
    (root / '.git/synthetic-control').write_bytes(b'SYNTHETIC GIT CONTROL')
    (root / '.gitignore').write_bytes(b'SYNTHETIC GIT CONFIG\n')
    before = _snapshot(root.parent)
    verified = fmt._verify_mirror(root, fernet)
    assert (verified.file_count, verified.directory_count, verified.plaintext_bytes) == (5, 4, sum(map(len, CONTENTS.values())))
    assert verified.encrypted_bytes == sum(path.stat().st_size for path in (root / '.obfuscidian').rglob('*.obf'))
    assert verified.manifest.vault_id == 'a' * 32
    assert verified.manifest.snapshot_id == 'b' * 32
    assert verified.manifest.created_at == '1970-01-01T00:00:00Z'
    assert {record.path for record in verified.manifest.directories} == {'.obsidian', 'attachments', 'empty', 'notes'}
    assert all(record.mtime_ns == -1 for record in verified.manifest.directories)
    reconstructed = {record.path: fmt._read_validated_file(verified, record, fernet) for record in verified.manifest.files}
    assert reconstructed == CONTENTS
    for index, record in enumerate(verified.manifest.files, 1):
        assert record.mtime_ns == -index
        original = (root / '.obfuscidian/objects' / f'{record.object_id}.obf').read_bytes()
        assert fmt._reuse_object(verified, record, CONTENTS[record.path], fernet) == original
        assert fernet.extract_timestamp(original) == 0
        changed = replace(record, mtime_ns=123)
        updated = replace(verified.manifest, files=tuple(changed if item == record else item for item in verified.manifest.files))
        assert fmt._decrypt_manifest(fmt._encrypt_manifest(updated, fernet), fernet).files[index - 1] == changed
    assert _snapshot(root.parent) == before
    assert str(root) not in repr(verified)
    assert 'café' not in repr(verified)
    assert capsys.readouterr().out == ''


def test_mixed_vault_encode_and_reconstruct(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Thread 03 inventory feeds v1 and reconstructs exact mixed content synthetically."""
    source = tmp_path.resolve() / 'synthetic-source'
    source.mkdir()
    for path in ('.obsidian', 'attachments', 'empty', 'notes'):
        (source / path).mkdir()
    for path, data in CONTENTS.items():
        (source / path).write_bytes(data)
    before = _snapshot(source)
    inventory = _scan_inventory(source)
    fernet = Fernet(Fernet.generate_key())
    root = tmp_path.resolve() / 'temporary-encoded-mirror'
    objects = root / '.obfuscidian/objects'
    objects.mkdir(parents=True)
    files, directories, reserved = [], [], set()
    for entry in inventory.entries:
        if entry.kind == 'directory':
            directories.append(fmt._DirectoryRecord(entry.path, entry.mtime_ns))
        else:
            identifier = _new_id(reserved)
            reserved.add(identifier)
            record, token = fmt._encode_file(entry.path, _read_file(inventory, entry), entry.mtime_ns, identifier, fernet)
            files.append(record)
            (objects / f'{identifier}.obf').write_bytes(token)
    manifest = fmt._Manifest(1, _new_id(), _new_id(), '2026-10-04T01:02:03Z', tuple(directories), tuple(files))
    (root / '.obfuscidian/manifest.obf').write_bytes(fmt._encrypt_manifest(manifest, fernet))
    _verify_inventory(inventory)
    assert _snapshot(source) == before
    verified = fmt._verify_mirror(root, fernet)
    before_validation = _snapshot(tmp_path)
    output = {record.path: fmt._read_validated_file(verified, record, fernet) for record in verified.manifest.files}
    assert output == CONTENTS
    assert _snapshot(tmp_path) == before_validation
    # Test-only reconstruction occurs after complete validation, not through a CLI write command.
    restored = tmp_path / 'synthetic-reconstructed'
    restored.mkdir()
    for record in verified.manifest.directories:
        (restored / record.path).mkdir()
    for record in verified.manifest.files:
        (restored / record.path).write_bytes(output[record.path])
    assert {
        path.relative_to(restored).as_posix(): path.read_bytes() for path in restored.rglob('*') if path.is_file()
    } == CONTENTS
    assert (restored / 'empty').is_dir()
    assert _snapshot(source) == before
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize(
    'case',
    [
        'wrong-key',
        'manifest-changed',
        'manifest-truncated',
        'object-changed',
        'object-truncated',
        'object-empty',
        'missing-object',
        'unexpected-object',
        'swapped-tokens',
        'same-plaintext-new-token',
        'wrong-object-key',
        'plaintext-hash',
        'plaintext-size',
        'ciphertext-hash',
        'unsupported-version',
        'unsafe-path',
        'manifest-missing',
        'objects-missing',
        'managed-missing',
        'unknown-root',
        'unknown-managed',
        'nested-object',
    ],
)
def test_complete_failures_before_destination_writes(
    mirror: tuple[Path, Fernet],
    case: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Integrity/layout/path failures preserve existing and absent destination trees."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    path = _object(root, mapping)
    destination = root.parent / 'existing-destination'
    destination.mkdir()
    (destination / 'SYNTHETIC PRIVATE SENTINEL').write_bytes(b'SYNTHETIC PRIVATE CONTENT')
    if case == 'wrong-key':
        fernet = Fernet(Fernet.generate_key())
    elif case.startswith('manifest-') and case in {'manifest-changed', 'manifest-truncated'}:
        target = root / '.obfuscidian/manifest.obf'
        token = target.read_bytes()
        target.write_bytes(token[:40] + b'!' + token[41:] if case.endswith('changed') else token[:-8])
    elif case in {'object-changed', 'object-truncated', 'object-empty'}:
        token = path.read_bytes()
        path.write_bytes(
            token[:40] + b'!' + token[41:] if case.endswith('changed') else token[:-8] if case.endswith('truncated') else b''
        )
    elif case == 'missing-object':
        path.unlink()
    elif case == 'unexpected-object':
        (path.parent / ('f' * 32 + '.obf')).write_bytes(fernet.encrypt(b'SYNTHETIC'))
    elif case == 'swapped-tokens':
        other = _object(root, mapping, 1)
        first, second = path.read_bytes(), other.read_bytes()
        assert len(first) == len(second), 'Substitution must fail even for equal-length valid tokens.'
        path.write_bytes(second)
        other.write_bytes(first)
    elif case in {'same-plaintext-new-token', 'wrong-object-key'}:
        key = fernet if case == 'same-plaintext-new-token' else Fernet(Fernet.generate_key())
        path.write_bytes(key.encrypt(CONTENTS[mapping['files'][0]['path']]))
        if case == 'wrong-object-key':
            mapping['files'][0]['ciphertext_sha256'] = _sha256(path.read_bytes())
            _replace_manifest(root, fernet, mapping)
    elif case in {'plaintext-hash', 'plaintext-size', 'ciphertext-hash', 'unsupported-version', 'unsafe-path'}:
        if case == 'unsupported-version':
            mapping['format_version'] = 999
        elif case == 'unsafe-path':
            mapping['files'][0]['path'] = '../SYNTHETIC PRIVATE SENTINEL'
        elif case == 'plaintext-size':
            mapping['files'][0]['size'] += 1
        else:
            mapping['files'][0]['plaintext_sha256' if case == 'plaintext-hash' else 'ciphertext_sha256'] = '0' * 64
        _replace_manifest(root, fernet, mapping)
    elif case == 'manifest-missing':
        (root / '.obfuscidian/manifest.obf').unlink()
    elif case == 'objects-missing':
        shutil.rmtree(root / '.obfuscidian/objects')
    elif case == 'managed-missing':
        shutil.rmtree(root / '.obfuscidian')
    elif case == 'unknown-root':
        (root / 'SYNTHETIC PRIVATE').write_bytes(b'')
    elif case == 'unknown-managed':
        (root / '.obfuscidian/SYNTHETIC PRIVATE').write_bytes(b'')
    else:
        (path.parent / ('f' * 32 + '.obf')).mkdir()
    _assert_failure_read_only(root, fernet, capsys)
    assert not (root.parent / 'absent-destination').exists()


@pytest.mark.parametrize(
    'raw',
    [
        b'{',
        b'{"format_version":1,"format_version":1}',
        b'\xff',
        b'{"files":[{"path":"a","path":"b"}]}',
        b'[' * 10000 + b']' * 10000,
    ],
)
def test_authenticated_hostile_json(mirror: tuple[Path, Fernet], raw: bytes, capsys: pytest.CaptureFixture[str]) -> None:
    """Even authenticated malformed/deep metadata cannot cause destination writes."""
    root, fernet = mirror
    (root / '.obfuscidian/manifest.obf').write_bytes(fernet.encrypt(raw))
    _assert_failure_read_only(root, fernet, capsys)


def test_wrong_manifest_key_is_never_parsed(mirror: tuple[Path, Fernet], monkeypatch: pytest.MonkeyPatch) -> None:
    """No unauthenticated manifest plaintext reaches the schema parser."""
    root, _ = mirror

    def forbidden(*args: object) -> None:
        pytest.fail('Parser must not run before authentication succeeds.')

    monkeypatch.setattr(fmt, '_parse_manifest', forbidden)
    with pytest.raises(_FormatError, match='authentication'):
        fmt._verify_mirror(root, Fernet(Fernet.generate_key()))


@pytest.mark.parametrize('location', ['root', 'managed', 'objects', 'manifest', 'object', 'git'])
def test_links_rejected_without_writes(
    mirror: tuple[Path, Fernet],
    location: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reject links in mirror controls, managed data, and location ancestors."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    targets = {
        'root': root,
        'managed': root / '.obfuscidian',
        'objects': root / '.obfuscidian/objects',
        'manifest': root / '.obfuscidian/manifest.obf',
        'object': _object(root, mapping),
        'git': root / '.git',
    }
    path = targets[location]
    saved = root.parent / 'synthetic-link-target'
    if location == 'git':
        saved.mkdir()
    else:
        path.rename(saved)
    try:
        path.symlink_to(saved, target_is_directory=saved.is_dir())
    except OSError:
        pytest.skip('Host cannot create this synthetic symlink.')
    _assert_failure_read_only(root, fernet, capsys)


@pytest.mark.skipif(not hasattr(os, 'mkfifo'), reason='Host lacks POSIX FIFO creation.')
def test_special_object_rejected(mirror: tuple[Path, Fernet], capsys: pytest.CaptureFixture[str]) -> None:
    """A FIFO is rejected by type inspection rather than blocking on open."""
    root, fernet = mirror
    path = _object(root, _raw_manifest(root, fernet))
    path.unlink()
    os.mkfifo(path)
    _assert_failure_read_only(root, fernet, capsys)


@pytest.mark.parametrize('which', ['manifest', 'object'])
def test_oversized_sparse_token_not_read(
    mirror: tuple[Path, Fernet],
    which: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Oversize stat length fails before file allocation/decryption."""
    root, fernet = mirror
    target = root / '.obfuscidian/manifest.obf' if which == 'manifest' else _object(root, _raw_manifest(root, fernet))
    with target.open('wb') as stream:
        stream.truncate(const.MAX_ENCRYPTED_BYTES + 1)
    original = fmt.os.open

    def bounded_open(path: object, *args: object, **kwargs: object) -> int:
        assert str(path) not in {str(target), target.name}, 'Oversized token must never be opened.'
        return original(path, *args, **kwargs)

    monkeypatch.setattr(fmt.os, 'open', bounded_open)
    _assert_failure_read_only(root, fernet, capsys)


@pytest.mark.parametrize('case', ['case', 'unicode', 'windows', 'component-length', 'path-length', 'ancestor-case'])
def test_explicit_hostile_target_rules(
    mirror: tuple[Path, Fernet],
    case: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Target-specific collisions/limits fail without probing or creating the target."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    rules = _TargetRules(case_sensitive=True)
    if case == 'case':
        mapping['files'][0]['path'] = 'ZERO.BIN'
        rules = _TargetRules(case_sensitive=False)
    elif case == 'unicode':
        mapping['files'][0]['path'] = 'notes/cafe\u0301-日本語.md'
        rules = _TargetRules(case_sensitive=True, normalization='NFC')
    elif case == 'ancestor-case':
        mapping['directories'].append({'path': 'Notes', 'mtime_ns': 0})
        mapping['files'][0]['path'] = 'Notes/x'
        rules = _TargetRules(case_sensitive=False)
    elif case == 'windows':
        mapping['files'][0]['path'] = 'CON.txt'
        rules = _TargetRules(case_sensitive=True, windows=True)
    elif case == 'component-length':
        rules = _TargetRules(case_sensitive=True, component_limit=5)
    else:
        rules = _TargetRules(case_sensitive=True, path_limit=1)
    _replace_manifest(root, fernet, mapping)
    destination = root.parent / 'absent-target'
    _assert_failure_read_only(root, fernet, capsys, target_rules=rules, destination=destination)
    assert not destination.exists()


def test_empty_snapshot_with_empty_objects(mirror: tuple[Path, Fernet]) -> None:
    """A complete empty snapshot still requires the objects directory."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    mapping['files'] = []
    mapping['directories'] = []
    for path in (root / '.obfuscidian/objects').iterdir():
        path.unlink()
    _replace_manifest(root, fernet, mapping)
    verified = fmt._verify_mirror(root, fernet)
    assert verified.file_count == verified.directory_count == verified.plaintext_bytes == 0


@pytest.mark.parametrize(
    'case', ['changed-proposal', 'forged-record', 'stale-token', 'stale-manifest', 'extra-object', 'wrong-key']
)
def test_reuse_revalidates_and_requires_unchanged_content(mirror: tuple[Path, Fernet], case: str) -> None:
    """Reuse cannot authorize changed data, foreign records, or a stale observation."""
    root, fernet = mirror
    result = fmt._verify_mirror(root, fernet)
    record = result.manifest.files[0]
    data = CONTENTS[record.path]
    if case == 'changed-proposal':
        data += b'SYNTHETIC CHANGE'
    elif case == 'forged-record':
        record = replace(record, mtime_ns=0)
    elif case == 'stale-token':
        (root / '.obfuscidian/objects' / f'{record.object_id}.obf').write_bytes(fernet.encrypt(data))
    elif case == 'stale-manifest':
        (root / '.obfuscidian/manifest.obf').write_bytes(fmt._encrypt_manifest(result.manifest, fernet))
    elif case == 'extra-object':
        (root / '.obfuscidian/objects' / ('f' * 32 + '.obf')).write_bytes(fernet.encrypt(b'SYNTHETIC'))
    else:
        fernet = Fernet(Fernet.generate_key())
    before = _snapshot(root.parent)
    with pytest.raises(_OperationalError):
        fmt._reuse_object(result, record, data, fernet)
    assert _snapshot(root.parent) == before


def test_changed_content_keeps_id_and_gets_new_ciphertext(mirror: tuple[Path, Fernet]) -> None:
    """Same-path changes preserve the opaque ID and bind new exact binary bytes."""
    root, fernet = mirror
    old = fmt._verify_mirror(root, fernet).manifest.files[0]
    new, token = fmt._encode_file(old.path, b'SYNTHETIC CHANGED CONTENT', old.mtime_ns, old.object_id, fernet)
    assert new.object_id == old.object_id
    assert new.ciphertext_sha256 != old.ciphertext_sha256
    assert fmt._decode_file(new, token, fernet) == b'SYNTHETIC CHANGED CONTENT'
    with pytest.raises(_FormatError):
        fmt._decode_file(old, token, fernet)


@pytest.mark.parametrize('when', ['first', 'last'])
@pytest.mark.parametrize('change', ['content', 'missing', 'unexpected'])
def test_change_during_complete_validation(
    mirror: tuple[Path, Fernet],
    when: str,
    change: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Late changes cannot make earlier objects or a changed namespace silently pass."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    original = fmt._decode_file
    calls = 0

    def changing(record: fmt._FileRecord, token: bytes, key: Fernet) -> bytes:
        nonlocal calls
        data = original(record, token, key)
        calls += 1
        if calls == (1 if when == 'first' else len(mapping['files'])):
            path = _object(root, mapping)
            if change == 'content':
                path.write_bytes(fernet.encrypt(b'SYNTHETIC CHANGE'))
            elif change == 'missing':
                path.unlink()
            else:
                (path.parent / ('f' * 32 + '.obf')).write_bytes(fernet.encrypt(b'SYNTHETIC EXTRA'))
        return data

    monkeypatch.setattr(fmt, '_decode_file', changing)
    with pytest.raises(_OperationalError):
        fmt._verify_mirror(root, fernet)
    assert not (root.parent / 'destination').exists()


@pytest.mark.parametrize('failure', [PermissionError, MemoryError])
def test_read_failures_are_redacted(
    mirror: tuple[Path, Fernet],
    failure: type[Exception],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No successful partial mirror is returned for access/allocation failure."""
    root, fernet = mirror
    original = fmt.os.open

    def fail(path: object, *args: object, **kwargs: object) -> int:
        if str(path).endswith('.obf'):
            raise failure('SYNTHETIC PRIVATE PATH')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(fmt.os, 'open', fail)
    _assert_failure_read_only(root, fernet, capsys)


def test_read_identity_replacement_during_open(mirror: tuple[Path, Fernet], monkeypatch: pytest.MonkeyPatch) -> None:
    """Opening a replaced regular inode after inspection aborts before accepting bytes."""
    root, fernet = mirror
    target = _object(root, _raw_manifest(root, fernet))
    original = fmt.os.open

    def replacing(path: object, *args: object, **kwargs: object) -> int:
        if str(path) in {target.name, str(target)}:
            replacement = target.with_suffix('.replacement')
            replacement.write_bytes(target.read_bytes())
            replacement.replace(target)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(fmt.os, 'open', replacing)
    with pytest.raises(_OperationalError, match='identity changed'):
        fmt._verify_mirror(root, fernet)


def test_unrelated_sibling_changes_do_not_invalidate(mirror: tuple[Path, Fernet], monkeypatch: pytest.MonkeyPatch) -> None:
    """Reading remains usable when unrelated sibling entries are created."""
    root, fernet = mirror
    original = fmt._decode_file
    counter = 0

    def changing(record: fmt._FileRecord, token: bytes, key: Fernet) -> bytes:
        nonlocal counter
        counter += 1
        (root.parent / f'synthetic-sibling-{counter}').write_bytes(b'SYNTHETIC')
        return original(record, token, key)

    monkeypatch.setattr(fmt, '_decode_file', changing)
    assert fmt._verify_mirror(root, fernet).file_count == 5


def test_no_new_cli_commands_or_output_leaks(mirror: tuple[Path, Fernet]) -> None:
    """Only implemented commands are exposed; incomplete selections leak no format paths."""
    root, _ = mirror
    runner = CliRunner()
    help_result = runner.invoke(cli, ['--help'])
    assert help_result.exit_code == 0
    assert set(cli.commands) == {'keygen', 'shroud', 'verify'}
    before = _snapshot(root.parent)
    for command in ('shroud', 'unshroud'):
        result = runner.invoke(cli, [command, '--mirror', str(root)])
        assert result.exit_code == 2
        assert str(root) not in result.output
        assert 'café' not in result.output
    assert _snapshot(root.parent) == before


@pytest.mark.parametrize('change', ['content', 'replace', 'memory'])
def test_change_or_failure_during_token_read(
    mirror: tuple[Path, Fernet],
    change: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mid-read identity/content/allocation failures return no accepted payload."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    target = _object(root, mapping)
    original = fmt.os.fdopen

    class ChangingReader:
        """Wrap a test stream to inject a change after the actual bounded read."""

        def __init__(self, source: object) -> None:
            self.source = source

        def __enter__(self) -> ChangingReader:
            self.source.__enter__()
            return self

        def __exit__(self, *args: object) -> None:
            self.source.__exit__(*args)

        def fileno(self) -> int:
            return self.source.fileno()

        def read(self, size: int) -> bytes:
            before = os.fstat(self.fileno())
            data = self.source.read(size)
            if before.st_ino == target.stat().st_ino:
                if change == 'memory':
                    raise MemoryError('SYNTHETIC PRIVATE CONTENT')
                if change == 'content':
                    target.write_bytes(fernet.encrypt(b'SYNTHETIC CHANGE'))
                else:
                    replacement = target.with_suffix('.replacement')
                    replacement.write_bytes(data)
                    replacement.replace(target)
            return data

    monkeypatch.setattr(fmt.os, 'fdopen', lambda *args, **kwargs: ChangingReader(original(*args, **kwargs)))
    with pytest.raises(_OperationalError) as error:
        fmt._verify_mirror(root, fernet)
    assert 'SYNTHETIC PRIVATE' not in str(error.value)
    assert not (root.parent / 'destination').exists()


def test_stream_construction_failure_closes_descriptor(mirror: tuple[Path, Fernet], monkeypatch: pytest.MonkeyPatch) -> None:
    """An allocation failure between open and stream ownership cannot leak a handle."""
    root, fernet = mirror
    descriptors = []

    def fail(descriptor: int, *args: object) -> None:
        descriptors.append(descriptor)
        raise MemoryError('SYNTHETIC PRIVATE CONTENT')

    monkeypatch.setattr(fmt.os, 'fdopen', fail)
    with pytest.raises(_OperationalError):
        fmt._verify_mirror(root, fernet)
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


@pytest.mark.skipif(os.name == 'nt', reason='Windows cannot represent control characters in file names.')
def test_posix_control_and_quote_names_round_trip(mirror: tuple[Path, Fernet]) -> None:
    """Valid control/quote characters are preserved and never emitted implicitly."""
    root, fernet = mirror
    mapping = _raw_manifest(root, fernet)
    name = 'notes/SYNTHETIC\n\t\x1b[31m".md'
    mapping['files'][0]['path'] = name
    _replace_manifest(root, fernet, mapping)
    result = fmt._verify_mirror(root, fernet)
    record = next(record for record in result.manifest.files if record.path == name)
    assert fmt._read_validated_file(result, record, fernet) == CONTENTS['.hidden']
    assert name not in repr(result)


def test_validated_file_read_rejects_late_different_object(mirror: tuple[Path, Fernet]) -> None:
    """A valid prior result cannot expose an object replaced after verification."""
    root, fernet = mirror
    result = fmt._verify_mirror(root, fernet)
    record = result.manifest.files[0]
    (root / '.obfuscidian/objects' / f'{record.object_id}.obf').write_bytes(fernet.encrypt(b'SYNTHETIC SUBSTITUTION'))
    with pytest.raises(_OperationalError):
        fmt._read_validated_file(result, record, fernet)

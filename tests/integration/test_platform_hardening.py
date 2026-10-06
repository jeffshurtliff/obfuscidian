# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_platform_hardening
:Synopsis:          Bounded host-native inventory, Git preflight and refusal coverage
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import backup, git_restore, inventory, keys, manifest, output, transactions
from obfuscidian import constants as const
from obfuscidian.cli import cli
from obfuscidian.errors import _ConfigurationError, _OperationalError

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/v1'


def _snapshot(root: Path) -> dict:
    """Observe exact bytes and write-related metadata, excluding access times."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes() if path.is_file() else None, path.stat().st_mtime_ns)
        for path in (root, *root.rglob('*'))
    }


@pytest.fixture
def vaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Reconstruct only public synthetic fixture bytes without backup mutation."""
    for name in (const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR, const.ENV_ORIGIN, const.ENV_MIRROR):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path.resolve()
    source, mirror, key = root / 'source', root / 'mirror', root / 'synthetic.key'
    shutil.copytree(FIXTURE / 'mirror', mirror)
    key.write_bytes((FIXTURE / 'synthetic-fernet-key.txt').read_bytes().strip())
    key.chmod(0o600)
    cipher = Fernet(key.read_bytes())
    checked = manifest._verify_mirror(mirror, cipher)
    source.mkdir()
    for record in checked.manifest.directories:
        (source / record.path).mkdir(parents=True, exist_ok=True)
    for record in checked.manifest.files:
        file = source / record.path
        file.write_bytes(manifest._read_validated_file(checked, record, cipher))
        os.utime(file, ns=(record.mtime_ns, record.mtime_ns))
    for record in reversed(checked.manifest.directories):
        os.utime(source / record.path, ns=(record.mtime_ns, record.mtime_ns))
    # The frozen format fixture has negative nanosecond timestamps.
    # Match this synthetic mirror to timestamps the host actually represents.
    current = replace(
        checked.manifest,
        files=tuple(replace(record, mtime_ns=(source / record.path).stat().st_mtime_ns) for record in checked.manifest.files),
        directories=tuple(
            replace(record, mtime_ns=(source / record.path).stat().st_mtime_ns) for record in checked.manifest.directories
        ),
    )
    (mirror / const.MANAGED_DIRECTORY / const.MANIFEST_FILENAME).write_bytes(manifest._encrypt_manifest(current, cipher))
    return source, mirror, key


def test_large_metadata_inventory_and_bounded_binary_read(tmp_path: Path) -> None:
    """Inventory a thousand small records and read one bounded binary attachment."""
    root = tmp_path.resolve()
    for index in range(1000):
        (root / f'file-{index:04}.bin').write_bytes(b'x')
    binary = bytes(range(256)) * 4096 + b'\r\n\x1a'
    (root / 'attachment.bin').write_bytes(binary)
    before = _snapshot(root)
    observed = inventory._scan_inventory(root)
    assert observed.file_count == 1001
    assert observed.plaintext_bytes == len(binary) + 1000
    assert tuple(entry.path for entry in observed.entries) == tuple(sorted(entry.path for entry in observed.entries))
    entry = next(item for item in observed.entries if item.path == 'attachment.bin')
    assert inventory._read_file(observed, entry) == binary
    inventory._verify_inventory(observed)
    estimate = inventory._estimate_resources(
        observed, manifest_plaintext_bytes=300000, retained_bytes=123, rollback_copy_bytes=456
    )
    assert (
        estimate.required_free_bytes
        == 1000 * inventory._fernet_size(1) + inventory._fernet_size(len(binary)) + inventory._fernet_size(300000) + 579
    )
    assert _snapshot(root) == before


@pytest.mark.parametrize('free_delta', [-1, 0, 1])
def test_space_estimate_boundary_has_no_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, free_delta: int) -> None:
    """Exact payload space is accepted without pretending to reserve disk allocation."""
    root = tmp_path.resolve()
    estimate = inventory._ResourceEstimate(100, 200, 300, 400)
    monkeypatch.setattr(shutil, 'disk_usage', lambda _: SimpleNamespace(free=1000 + free_delta))
    before = _snapshot(root)
    if free_delta < 0:
        with pytest.raises(_OperationalError, match='space'):
            inventory._check_space(root, estimate)
    else:
        inventory._check_space(root, estimate)
    assert _snapshot(root) == before


@pytest.mark.parametrize('mode', ['fresh', 'merge'])
def test_existing_snapshot_noop_is_artifact_free_on_host(vaults, mode: str) -> None:
    """A matching encrypted snapshot preserves tokens/times without ownership or staging."""
    source, mirror, key = vaults
    before = _snapshot(source.parent)
    result = CliRunner().invoke(
        cli, ['shroud', mode, '--origin', str(source), '--mirror', str(mirror), '--key', str(key), '--non-interactive']
    )
    assert result.exit_code == 0, result.output
    assert 'no-op' in result.stdout
    assert _snapshot(source.parent) == before


def _git(root: Path, *arguments: str) -> bytes:
    """Create/read synthetic local Git history with conversions and hooks disabled."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    return subprocess.run(
        [
            'git',
            '-c',
            'core.hooksPath=' + os.devnull,
            '-c',
            'core.autocrlf=false',
            '-c',
            'core.fsmonitor=false',
            '-c',
            'gc.auto=0',
            '-c',
            'maintenance.auto=false',
            '-c',
            'user.name=Synthetic Tester',
            '-c',
            'user.email=synthetic@example.invalid',
            '-C',
            str(root),
            *arguments,
        ],
        env=environment,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout


@pytest.mark.parametrize('base', ['main', 'missing'])
def test_native_git_merge_preflight_is_read_only(vaults, base: str) -> None:
    """Validate local Git capabilities and byte-preserving base observation on every OS."""
    source, mirror, key = vaults
    repository = source.parent / 'repository with spaces'
    repository.mkdir()
    _git(repository, 'init', '-qb', 'main')
    data = bytes(range(256)) + b'\r\n\x1a'
    (repository / 'base.bin').write_bytes(data)
    _git(repository, 'add', '--all')
    _git(repository, 'commit', '-qm', 'Created synthetic platform fixture')
    review = repository.parent / 'review with spaces'
    before = _snapshot(source.parent)
    if base == 'missing':
        with pytest.raises(_ConfigurationError, match='existing local'):
            git_restore._plan_merge(repository, mirror, key, worktree=review, branch='synthetic', base_branch=base)
    else:
        plan = git_restore._plan_merge(repository, mirror, key, worktree=review, branch='synthetic', base_branch=base)
        assert git_restore._publish_merge(plan, dry_run=True) is None
        if os.name == 'nt':
            with pytest.raises(_ConfigurationError, match='POSIX'):
                git_restore._publish_merge(plan)
        entry = next(item for item in plan.base_files if item.path == 'base.bin')
        assert git_restore._blob(plan, entry) == data
    assert _snapshot(source.parent) == before
    assert not review.exists()


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows write-refusal and ACL boundaries.')
@pytest.mark.parametrize('command,mode', [('shroud', 'fresh'), ('shroud', 'merge'), ('unshroud', 'fresh')])
def test_native_windows_mutation_refuses_before_artifacts(vaults, command: str, mode: str) -> None:
    """Actual Windows write attempts fail without locks, workspaces or payload changes."""
    source, mirror, key = vaults
    if command == 'shroud':
        (source / 'new.bin').write_bytes(b'SYNTHETIC NEW')
    else:
        source = source.parent / 'absent-restore'
    before = _snapshot(mirror.parent)
    result = CliRunner().invoke(
        cli, [command, mode, '--origin', str(source), '--mirror', str(mirror), '--key', str(key), '--non-interactive', '--yes']
    )
    assert result.exit_code != 0
    assert 'Traceback' not in result.output
    assert _snapshot(mirror.parent) == before
    destination = mirror if command == 'shroud' else source
    lock = destination.parent / transactions._lock_name(destination, backup._mirror_rules(destination.parent))
    lock.write_bytes(b'SYNTHETIC PENDING OWNERSHIP')
    before = _snapshot(mirror.parent)
    recovery = CliRunner().invoke(
        cli,
        [
            command,
            mode,
            '--origin',
            str(source),
            '--mirror',
            str(mirror),
            '--key',
            str(key),
            '--non-interactive',
            '--yes',
            '--recover',
        ],
    )
    assert recovery.exit_code != 0
    assert 'Traceback' not in recovery.output
    assert _snapshot(mirror.parent) == before
    assert lock.read_bytes() == b'SYNTHETIC PENDING OWNERSHIP'


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows log creation/append custody.')
def test_native_windows_private_log_and_existing_append_refusal(tmp_path: Path) -> None:
    """Write a new protected log, then preserve it when an existing append is refused."""
    root = tmp_path.resolve()
    key = root / 'synthetic.key'
    keys._generate_key(key)
    log = root / 'events.jsonl'
    policy = output._Output('synthetic', log, False)
    policy._prepare(protected=(), key=key)
    try:
        policy._open()
        policy._record('complete', files=1)
    finally:
        policy._close()
    original = log.read_bytes()
    assert b'complete' in original and key.read_bytes() not in original
    with pytest.raises(_ConfigurationError, match='ACL validation'):
        output._Output('synthetic', log, False)._prepare(protected=(), key=key)
    assert log.read_bytes() == original


@pytest.mark.skipif(os.name != 'nt', reason='Requires native Windows junction creation.')
def test_junction_inventory_refuses_without_following(tmp_path: Path) -> None:
    """A native directory junction cannot silently include external data."""
    root = tmp_path.resolve()
    source, external = root / 'source', root / 'external'
    source.mkdir()
    external.mkdir()
    sentinel = external / 'synthetic.bin'
    sentinel.write_bytes(b'SYNTHETIC EXTERNAL DATA')
    digest = hashlib.sha256(sentinel.read_bytes()).digest()
    junction = source / 'junction'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(external)], capture_output=True, timeout=30)
    assert result.returncode == 0, 'Native CI must provide junction fixture capability.'
    try:
        with pytest.raises(_ConfigurationError, match='junctions'):
            inventory._scan_inventory(source)
        assert hashlib.sha256(sentinel.read_bytes()).digest() == digest
    finally:
        junction.rmdir()

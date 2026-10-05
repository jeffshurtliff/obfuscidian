# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_transactions
:Synopsis:          Synthetic publication fault boundaries and process recovery
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.cli import cli
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.paths import _TargetRules

pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Transaction writes fail closed pending native platform hardening.')
FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/v1'
OLD = {'same.bin': b'SYNTHETIC OLD\x00\xff', 'old-dir/note.md': b'SYNTHETIC OLD\r\n', 'old-dir/empty': None}
NEW = {'same.bin': bytes(range(256)), 'new-dir/note.md': b'SYNTHETIC NEW\r\n', 'new-dir/empty': None}
RULES = _TargetRules(case_sensitive=True)


def _write(root: Path, files: dict = NEW) -> None:
    """Populate synthetic payload with exact bytes and an empty directory."""
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            path.mkdir()
        else:
            path.write_bytes(data)


def _snapshot(root: Path) -> dict:
    """Independently snapshot synthetic bytes, names, identities and non-access times."""
    result = {}
    for path in (root, *root.rglob('*')):
        info = path.lstat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if stat.S_ISREG(info.st_mode) else None
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


def _bytes(root: Path) -> dict:
    """Observe payload bytes and empty directories, ignoring protected Git controls."""
    result = {}
    if not root.exists():
        return result
    for path in root.rglob('*'):
        if '.git' in path.relative_to(root).parts or path.name == '.gitignore':
            continue
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
        elif not any(path.iterdir()):
            result[path.relative_to(root).as_posix()] = None
    return result


def _verify(stage: Path) -> None:
    """Require the complete staged proposal before publication."""
    assert _bytes(stage) == NEW


@pytest.fixture
def locations(tmp_path: Path) -> tuple[Path, Path]:
    """Create an isolated origin and a synthetic destination inside an actual Git repo."""
    root = tmp_path.resolve()
    source = root / 'source'
    source.mkdir()
    (source / 'sentinel').write_bytes(b'SYNTHETIC ORIGIN')
    repository = root / 'repository'
    repository.mkdir()
    subprocess.run(['git', 'init', '-q', str(repository)], check=True, capture_output=True)
    destination = repository / 'destination'
    destination.mkdir()
    _write(destination, OLD)
    return source, destination


def _plan(source: Path, destination: Path, **kwargs: object) -> tx._TransactionPlan:
    """Use explicit synthetic target rules for all calls."""
    return tx._plan_transaction(source, destination, target_rules=RULES, **kwargs)


def _run(plan: tx._TransactionPlan, **kwargs: object) -> tx._TransactionResult:
    """Execute only internal synthetic publication."""
    return tx._execute_transaction(plan, _write, _verify, yes=True, **kwargs)


def _assert_previous_or_blocked(source: Path, destination: Path, plan: tx._TransactionPlan) -> None:
    """A failure either restores exact previous bytes or retains exclusive pending state."""
    if plan.lock.exists():
        with pytest.raises(_OperationalError, match='pending'):
            _plan(source, destination)
        # Every old file remains somewhere in the destination or private recovery tree.
        found = [path.read_bytes() for path in plan.workspace_parent.rglob('*') if path.is_file() and '.git' not in path.parts]
        for data in OLD.values():
            if data is not None:
                assert data in found
    else:
        assert _bytes(destination) == OLD
    assert (source / 'sentinel').read_bytes() == b'SYNTHETIC ORIGIN'


def test_fresh_success_retains_private_rollback_outside_git(locations: tuple[Path, Path]) -> None:
    """Preserve source, all old bytes, empty dirs and Git inode/content during fresh success."""
    source, destination = locations
    repository = destination.parent
    git_before = tx._capture(repository / '.git', git_control=True)
    git_bytes = {p.relative_to(repository / '.git'): p.read_bytes() for p in (repository / '.git').rglob('*') if p.is_file()}
    plan = _plan(source, destination, required_bytes=4096)
    result = _run(plan)
    assert _bytes(destination) == NEW
    assert _bytes(result.rollback) == OLD
    assert result.plaintext
    assert not result.workspace.is_relative_to(repository)
    assert not result.workspace.is_relative_to(source)
    assert result.workspace.stat().st_dev == destination.stat().st_dev
    assert stat.S_IMODE(result.workspace.stat().st_mode) == 0o700
    assert stat.S_IMODE((result.workspace / const.TRANSACTION_JOURNAL).stat().st_mode) == 0o600
    assert not plan.lock.exists()
    assert tx._capture(repository / '.git', git_control=True) == git_before
    assert git_bytes == {
        p.relative_to(repository / '.git'): p.read_bytes() for p in (repository / '.git').rglob('*') if p.is_file()
    }
    assert (source / 'sentinel').read_bytes() == b'SYNTHETIC ORIGIN'


@pytest.mark.parametrize('control', ['directory', 'file'])
def test_root_git_controls_and_preserved_config(locations: tuple[Path, Path], control: str) -> None:
    """Root Git directory/file, gitignore and requested settings retain identities and hashes."""
    source, destination = locations
    if control == 'directory':
        subprocess.run(['git', 'init', '-q', str(destination)], check=True, capture_output=True)
    else:
        metadata = destination.parent / '.git'
        (destination / '.git').write_text(f'gitdir: {metadata}\n')
    (destination / '.gitignore').write_bytes(b'SYNTHETIC IGNORE\r\n')
    (destination / '.obsidian').mkdir()
    (destination / '.obsidian/settings.json').write_bytes(b'{"synthetic":true}')
    plan = _plan(source, destination, preserve_config=True)
    protected = plan.protected
    result = _run(plan)
    assert tx._observe(destination, True) == (tx._observe(destination, True)[0], protected)
    assert '.git' not in {p.name for p in result.rollback.iterdir()}
    assert '.obsidian' not in {p.name for p in result.rollback.iterdir()}


def test_missing_destination_and_empty_payload(locations: tuple[Path, Path]) -> None:
    """Only a missing final component is created; empty proposals retain all previous content."""
    source, existing = locations
    destination = existing.parent / 'new'
    result = _run(_plan(source, destination))
    assert _bytes(destination) == NEW
    assert _bytes(result.rollback) == {}
    result = tx._execute_transaction(_plan(source, existing), lambda p: None, lambda p: None, yes=True)
    assert _bytes(existing) == {}
    assert _bytes(result.rollback) == OLD


def test_dry_run_creates_nothing_and_never_builds_or_prompts(locations: tuple[Path, Path]) -> None:
    """Dry runs inspect only; callback, lock, journal, stage, rollback and paths remain absent."""
    source, destination = locations
    plan = _plan(source, destination)
    before = _snapshot(plan.workspace_parent)

    def forbidden(*args: object) -> None:
        pytest.fail('Dry run cannot invoke a write or prompt callback.')

    tx._execute_transaction(plan, forbidden, forbidden, dry_run=True, prompt=forbidden)
    assert _snapshot(plan.workspace_parent) == before
    assert not plan.lock.exists()
    destination = destination.parent / 'missing'
    plan = _plan(source, destination)
    tx._execute_transaction(plan, forbidden, forbidden, dry_run=True)
    assert not destination.exists()


@pytest.mark.parametrize('failure', [PermissionError, MemoryError, KeyboardInterrupt])
def test_failed_builder_or_validation_preserves_payload(locations: tuple[Path, Path], failure: type[BaseException]) -> None:
    """Incomplete staged writes never authorize destination modification."""
    source, destination = locations
    plan = _plan(source, destination)

    def broken(stage: Path) -> None:
        (stage / 'partial').write_bytes(b'SYNTHETIC PARTIAL')
        raise failure('SYNTHETIC PRIVATE')

    with pytest.raises((tx._TransactionError, KeyboardInterrupt)) as error:
        tx._execute_transaction(plan, broken, _verify, yes=True)
    assert 'SYNTHETIC PRIVATE' not in str(error.value) if isinstance(error.value, tx._TransactionError) else True
    _assert_previous_or_blocked(source, destination, plan)


@pytest.mark.parametrize('boundary,index', [('checkpoint', i) for i in range(1, 14)] + [('move', i) for i in range(1, 5)])
def test_every_checkpoint_and_rename_failure(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    index: int,
    boundary: str,
) -> None:
    """Inject before and after each durable checkpoint/rename; preserve full old state or block."""
    source, destination = locations
    plan = _plan(source, destination)
    original = getattr(tx, '_' + boundary)
    calls = 0

    def broken(*args: object) -> None:
        nonlocal calls
        calls += 1
        if calls == index:
            raise OSError(errno.ENOSPC, 'SYNTHETIC PRIVATE')
        original(*args)

    monkeypatch.setattr(tx, '_' + boundary, broken)
    try:
        _run(plan)
    except tx._TransactionError as error:
        assert 'SYNTHETIC PRIVATE' not in str(error)
        _assert_previous_or_blocked(source, destination, plan)
    else:
        assert calls < index
        assert _bytes(destination) == NEW


@pytest.mark.parametrize('index', range(1, 5))
def test_failure_after_rename(locations: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, index: int) -> None:
    """A rename completed before an exception must be inferred from durable identities."""
    source, destination = locations
    plan = _plan(source, destination)
    original = tx._move
    calls = 0

    def broken(*args: object) -> None:
        nonlocal calls
        calls += 1
        original(*args)
        if calls == index:
            raise PermissionError('SYNTHETIC PRIVATE')

    monkeypatch.setattr(tx, '_move', broken)
    with pytest.raises(tx._TransactionError):
        _run(plan)
    _assert_previous_or_blocked(source, destination, plan)


@pytest.mark.parametrize('boundary', ['fsync', 'write', 'mkdir', 'open', 'replace', 'rename', 'unlink'])
@pytest.mark.parametrize('index', [1, 2, 3, 5, 10, 20, 30, 40])
def test_io_failure_boundaries(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    index: int,
) -> None:
    """Inject disk/access errors across control creation, writes, fsync, replace, rename and release."""
    source, destination = locations
    plan = _plan(source, destination)
    original = getattr(tx.os, boundary)
    calls = 0

    def broken(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == index:
            raise OSError(errno.ENOSPC, 'SYNTHETIC PRIVATE')
        return original(*args, **kwargs)

    monkeypatch.setattr(tx.os, boundary, broken)
    try:
        _run(plan)
    except _OperationalError as error:
        assert 'SYNTHETIC PRIVATE' not in str(error)
        _assert_previous_or_blocked(source, destination, plan)
    else:
        assert calls < index
        assert _bytes(destination) == NEW


def _leave_pending(plan: tx._TransactionPlan, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail after first old rename and block automatic rollback, retaining durable recovery state."""
    original = tx._move
    calls = 0

    def broken(*args: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            original(*args)
        raise PermissionError('SYNTHETIC PRIVATE')

    with monkeypatch.context() as patch:
        patch.setattr(tx, '_move', broken)
        with pytest.raises(tx._TransactionError) as error:
            _run(plan)
        assert error.value.recovery_required
    assert plan.lock.exists()


def test_rollback_failure_then_explicit_recovery(locations: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Failed inverse publication blocks writes until deliberate verified recovery restores all old bytes."""
    source, destination = locations
    plan = _plan(source, destination)
    _leave_pending(plan, monkeypatch)
    with pytest.raises(_OperationalError, match='pending'):
        _plan(source, destination)
    pending = _plan(source, destination, allow_pending=True)
    before = _snapshot(plan.workspace_parent)
    with pytest.raises(_OperationalError, match='confirmation'):
        tx._recover_transaction(pending, non_interactive=True)
    assert _snapshot(plan.workspace_parent) == before
    result = tx._recover_transaction(pending, yes=True, non_interactive=True)
    assert _bytes(destination) == OLD
    assert not pending.lock.exists()
    assert _bytes(result.workspace / const.TRANSACTION_STAGE) == NEW
    assert (result.workspace / const.TRANSACTION_JOURNAL).exists()


@pytest.mark.parametrize(
    'change', ['destination-content', 'unexpected', 'rollback', 'stage', 'gitignore', 'journal', 'root', 'container']
)
def test_uncertain_user_artifacts_preserved_without_recovery_writes(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    """User changes anywhere in publication/recovery state prevent inverse mutation or cleanup."""
    source, destination = locations
    (destination / '.gitignore').write_bytes(b'SYNTHETIC IGNORE')
    plan = _plan(source, destination)
    _leave_pending(plan, monkeypatch)
    record = json.loads(plan.lock.read_bytes())
    workspace = plan.workspace_parent / (const.TRANSACTION_PREFIX + record['id'])
    if change == 'destination-content':
        (destination / 'same.bin').write_bytes(b'SYNTHETIC USER CHANGE')
    elif change == 'unexpected':
        (destination / 'user').write_bytes(b'SYNTHETIC USER CHANGE')
    elif change in {'rollback', 'stage'}:
        container = workspace / change
        next(p for p in container.rglob('*') if p.is_file()).write_bytes(b'SYNTHETIC USER CHANGE')
    elif change == 'gitignore':
        (destination / '.gitignore').write_bytes(b'SYNTHETIC USER CHANGE')
    elif change == 'journal':
        (workspace / const.TRANSACTION_JOURNAL).write_bytes(b'{"broken":true}')
    else:
        path = destination if change == 'root' else workspace / const.TRANSACTION_STAGE
        path.rename(path.with_name(path.name + '-saved'))
        path.mkdir()
    pending = _plan(source, destination, allow_pending=True)
    before = _snapshot(plan.workspace_parent)
    with pytest.raises(tx._TransactionError) as error:
        tx._recover_transaction(pending, yes=True)
    assert error.value.recovery_required
    assert _snapshot(plan.workspace_parent) == before
    assert plan.lock.exists()


@pytest.mark.parametrize('case', ['nested-git', 'symlink', 'special', 'changed', 'new-entry', 'staged-git', 'bad-verify'])
def test_unsafe_or_changed_destination_and_proposal(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    """Reject unsafe payloads, changes and incomplete validation without losing user data."""
    source, destination = locations
    if case == 'nested-git':
        (destination / 'old-dir/.git').mkdir()
        with pytest.raises(_ConfigurationError, match='nested'):
            _plan(source, destination)
        return
    if case == 'symlink':
        (destination / 'link').symlink_to(source)
        with pytest.raises(_ConfigurationError):
            _plan(source, destination)
        return
    if case == 'special':
        os.mkfifo(destination / 'fifo')
        with pytest.raises(_ConfigurationError):
            _plan(source, destination)
        return
    plan = _plan(source, destination)

    def build(stage: Path) -> None:
        _write(stage)
        if case == 'changed':
            (destination / 'same.bin').write_bytes(b'SYNTHETIC USER CHANGE')
        elif case == 'new-entry':
            (destination / 'user').write_bytes(b'SYNTHETIC USER CHANGE')
        elif case == 'staged-git':
            (stage / '.git').mkdir()

    def verify(stage: Path) -> None:
        if case == 'bad-verify':
            raise _OperationalError('Synthetic proposal rejected.')
        _verify(stage)

    with pytest.raises(tx._TransactionError):
        tx._execute_transaction(plan, build, verify, yes=True)
    if case == 'changed':
        assert (destination / 'same.bin').read_bytes() == b'SYNTHETIC USER CHANGE'
    elif case == 'new-entry':
        assert (destination / 'user').read_bytes() == b'SYNTHETIC USER CHANGE'
    else:
        assert _bytes(destination) == OLD


@pytest.mark.parametrize(
    'case', ['source-overlap', 'destination-overlap', 'missing-parent', 'space', 'permissions', 'cross-device']
)
def test_read_only_preflight_failures(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    """Unsafe locations or unavailable resources fail before any transaction artifacts."""
    source, destination = locations
    before = _snapshot(source.parent)
    if case == 'source-overlap':
        destination = source / 'nested'
    elif case == 'destination-overlap':
        source = destination / 'old-dir'
    elif case == 'missing-parent':
        destination = destination / 'missing/final'
    elif case == 'space':
        monkeypatch.setattr(tx.shutil, 'disk_usage', lambda p: shutil._ntuple_diskusage(0, 0, 0))
    elif case == 'permissions':
        monkeypatch.setattr(tx.os, 'access', lambda *a: False)
    else:
        monkeypatch.setattr(tx, '_select_parent', lambda s, d: Path('/'))
        # A deterministic substitute device observation avoids depending on mounted volumes.
        original = Path.stat

        def altered(path: Path, *args: object, **kwargs: object) -> os.stat_result:
            result = original(path, *args, **kwargs)
            if path == destination:
                values = list(result)
                values[2] += 1
                return os.stat_result(values)
            return result

        monkeypatch.setattr(Path, 'stat', altered)
    with pytest.raises((_ConfigurationError, _OperationalError)):
        _plan(source, destination)
    if case != 'cross-device':
        assert _snapshot(locations[0].parent) == before


def test_mirror_managed_tree_authentication_and_publication(tmp_path: Path) -> None:
    """Mirror publication validates both complete trees and moves only the managed unit."""
    root = tmp_path.resolve()
    source = root / 'source'
    shutil.copytree(FIXTURE / 'mirror', source)
    destination = root / 'destination'
    shutil.copytree(source, destination)
    subprocess.run(['git', 'init', '-q', str(destination)], check=True, capture_output=True)
    key = Fernet((FIXTURE / 'synthetic-fernet-key.txt').read_bytes().strip())
    before_git = tx._capture(destination / '.git', git_control=True)
    plan = _plan(source, destination, mirror=True, fernet=key)

    def build(stage: Path) -> None:
        shutil.copytree(source / '.obfuscidian', stage / '.obfuscidian')

    result = tx._execute_transaction(plan, build, lambda stage: None, yes=True)
    assert not result.plaintext
    assert tx._capture(destination / '.git', git_control=True) == before_git
    assert _bytes(destination) == _bytes(source)
    tx._verify_mirror(result.rollback, key)
    unmanaged = root / 'unmanaged'
    unmanaged.mkdir()
    (unmanaged / 'sentinel').write_bytes(b'SYNTHETIC')
    with pytest.raises(_ConfigurationError, match='Unmanaged'):
        _plan(source, unmanaged, mirror=True, fernet=key)
    corrupt = _plan(source, destination, mirror=True, fernet=key)

    def bad_build(stage: Path) -> None:
        build(stage)
        (stage / '.obfuscidian/manifest.obf').write_bytes(b'SYNTHETIC INVALID')

    with pytest.raises(tx._TransactionError):
        tx._execute_transaction(corrupt, bad_build, lambda stage: None, yes=True)
    tx._verify_mirror(destination, key)


WORKER = """
import os, sys
from pathlib import Path
from obfuscidian import transactions as tx
from obfuscidian.paths import _TargetRules
source, destination = map(Path, sys.argv[1:3])
plan = tx._plan_transaction(source, destination, target_rules=_TargetRules(case_sensitive=True))
original = tx._move
count = 0
def move(*args):
    global count
    count += 1
    original(*args)
    if count == int(sys.argv[3]):
        os._exit(73)
tx._move = move
def build(stage):
    (stage / 'same.bin').write_bytes(bytes(range(256)))
    (stage / 'new-dir').mkdir()
    (stage / 'new-dir/note.md').write_bytes(b'SYNTHETIC NEW\\r\\n')
    (stage / 'new-dir/empty').mkdir()
tx._execute_transaction(plan, build, lambda p: None, yes=True)
"""


@pytest.mark.parametrize('boundary', range(1, 5))
def test_terminated_process_recovery_at_every_payload_move(locations: tuple[Path, Path], boundary: int) -> None:
    """SIG-like immediate process death releases OS ownership but retains durable recovery state."""
    source, destination = locations
    result = subprocess.run([sys.executable, '-c', WORKER, str(source), str(destination), str(boundary)], capture_output=True)
    assert result.returncode == 73, result.stderr.decode()
    pending = _plan(source, destination, allow_pending=True)
    assert pending.lock.exists()
    before = _snapshot(source.parent)
    with pytest.raises(_OperationalError, match='pending'):
        _plan(source, destination)
    assert _snapshot(source.parent) == before
    tx._recover_transaction(pending, yes=True)
    assert _bytes(destination) == OLD
    assert not pending.lock.exists()


def test_competing_live_process_refuses_ownership_and_recovery(locations: tuple[Path, Path], tmp_path: Path) -> None:
    """A live writer owns OS lock; another process cannot publish or recover its artifacts."""
    source, destination = locations
    ready = tmp_path / 'ready'
    worker = (
        WORKER[: WORKER.index('original = tx._move')]
        + """
import time
def build(stage):
    Path(sys.argv[3]).write_text('ready')
    time.sleep(30)
tx._execute_transaction(plan, build, lambda p: None, yes=True)
"""
    )
    process = subprocess.Popen(
        [sys.executable, '-c', worker, str(source), str(destination), str(ready)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        import time

        deadline = time.monotonic() + 5
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists()
        with pytest.raises(_OperationalError, match='pending'):
            _plan(source, destination)
        pending = _plan(source, destination, allow_pending=True)
        before = _snapshot(source.parent)
        with pytest.raises(tx._TransactionError):
            tx._recover_transaction(pending, yes=True)
        assert _snapshot(source.parent) == before
    finally:
        process.kill()
        process.communicate(timeout=5)
    pending = _plan(source, destination, allow_pending=True)
    tx._recover_transaction(pending, yes=True)
    assert _bytes(destination) == OLD


def test_no_public_partial_write_commands() -> None:
    """Expose complete backup, fresh restore and verification; standalone recovery stays gated."""
    assert set(cli.commands) == {'keygen', 'shroud', 'unshroud', 'verify'}
    runner = CliRunner()
    for name in ('unshroud', 'recover'):
        result = runner.invoke(cli, [name])
        assert result.exit_code == 2
    assert runner.invoke(cli, ['shroud', 'merge']).exit_code == 2


@pytest.mark.parametrize('boundary', ['fsync', 'write', 'mkdir', 'replace', 'rename', 'unlink', 'write-open'])
def test_all_observed_mutation_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    """Enumerate every mutation on a successful run, then fail each observed boundary in isolation."""

    def setup(index: int) -> tuple[Path, Path, tx._TransactionPlan]:
        root = tmp_path.resolve() / str(index)
        root.mkdir()
        source, destination = root / 'source', root / 'destination'
        source.mkdir()
        (source / 'sentinel').write_bytes(b'SYNTHETIC ORIGIN')
        destination.mkdir()
        _write(destination, OLD)
        return source, destination, _plan(source, destination)

    source, destination, plan = setup(0)
    name = 'open' if boundary == 'write-open' else boundary
    original = getattr(tx.os, name)
    observed = 0

    def selected(args: tuple) -> bool:
        if boundary == 'mkdir' and Path(args[0]).is_absolute() and tx._entry_exists(Path(args[0])):
            return False
        return boundary != 'write-open' or bool(args[1] & (os.O_CREAT | os.O_WRONLY | os.O_RDWR))

    def trace(*args: object, **kwargs: object) -> object:
        nonlocal observed
        if selected(args):
            observed += 1
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(tx.os, name, trace)
        _run(plan)
    assert observed > 0
    for index in range(1, observed + 1):
        source, destination, plan = setup(index)
        calls = 0

        def broken(*args: object, _index: int = index, **kwargs: object) -> object:
            nonlocal calls
            if selected(args):
                calls += 1
                if calls == _index:
                    raise OSError(errno.ENOSPC, 'SYNTHETIC PRIVATE')
            return original(*args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(tx.os, name, broken)
            try:
                result = _run(plan)
            except _OperationalError:
                _assert_previous_or_blocked(source, destination, plan)
            else:
                # Only the fsync after completed unlink can return a success warning.
                assert boundary == 'fsync'
                assert result.warnings
                assert _bytes(destination) == NEW
                assert _bytes(result.rollback) == OLD
        assert calls >= index


@pytest.mark.parametrize('index', range(1, 14))
def test_failure_after_each_journal_checkpoint(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    index: int,
) -> None:
    """A completed checkpoint followed by failure is recovered using its durable state."""
    source, destination = locations
    plan = _plan(source, destination)
    original = tx._checkpoint
    calls = 0

    def broken(*args: object) -> None:
        nonlocal calls
        calls += 1
        original(*args)
        if calls == index:
            raise PermissionError('SYNTHETIC PRIVATE')

    monkeypatch.setattr(tx, '_checkpoint', broken)
    with pytest.raises(tx._TransactionError):
        _run(plan)
    _assert_previous_or_blocked(source, destination, plan)


@pytest.mark.parametrize('case', ['lock', 'journal'])
def test_short_control_write_never_authorizes_publication(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    """Short lock/journal writes retain ambiguous state and never touch destination payload."""
    source, destination = locations
    plan = _plan(source, destination)
    if case == 'lock':
        original = tx.os.write
        monkeypatch.setattr(tx.os, 'write', lambda fd, data: original(fd, data[:8]))
    else:
        original = tx.os.fdopen

        class ShortWriter:
            """Wrap only binary write streams to simulate a short durable record write."""

            def __init__(self, stream: object) -> None:
                self.stream = stream

            def __enter__(self) -> ShortWriter:
                self.stream.__enter__()
                return self

            def __exit__(self, *args: object) -> None:
                self.stream.__exit__(*args)

            def write(self, data: bytes) -> int:
                return self.stream.write(data[:8])

            def flush(self) -> None:
                self.stream.flush()

        def short(*args: object, **kwargs: object) -> object:
            stream = original(*args, **kwargs)
            return ShortWriter(stream) if args[1] == 'wb' else stream

        monkeypatch.setattr(tx.os, 'fdopen', short)
    with pytest.raises(tx._TransactionError) as error:
        _run(plan)
    assert error.value.recovery_required
    assert _bytes(destination) == OLD
    assert plan.lock.exists()


def test_missing_destination_failure_restores_absence(locations: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Recovery removes only this transaction's proven empty created root."""
    source, existing = locations
    destination = existing.parent / 'missing'
    plan = _plan(source, destination)
    original = tx._move
    calls = 0

    def broken(*args: object) -> None:
        nonlocal calls
        calls += 1
        original(*args)
        if calls == 1:
            raise PermissionError('SYNTHETIC PRIVATE')

    monkeypatch.setattr(tx, '_move', broken)
    with pytest.raises(tx._TransactionError) as error:
        _run(plan)
    assert not error.value.recovery_required
    assert not destination.exists()
    assert not plan.lock.exists()


def test_pending_lock_discovered_when_git_boundary_changes(locations: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """A new enclosing Git marker cannot hide ownership at its previously selected ancestor."""
    source, destination = locations
    plan = _plan(source, destination)
    _leave_pending(plan, monkeypatch)
    (source.parent / '.git').mkdir()
    with pytest.raises(_OperationalError, match='pending'):
        _plan(source, destination)
    pending = _plan(source, destination, allow_pending=True)
    assert pending.lock == plan.lock
    before = _snapshot(source.parent)
    with pytest.raises(tx._TransactionError):
        tx._recover_transaction(pending, yes=True)
    assert _snapshot(source.parent) == before


def test_ancestor_replacement_preserves_uncertain_artifacts(
    locations: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Moving an enclosing directory and recreating its name cannot authorize recovery."""
    source, destination = locations
    plan = _plan(source, destination)
    _leave_pending(plan, monkeypatch)
    repository = destination.parent
    saved = repository.with_name('saved-repository')
    repository.rename(saved)
    repository.mkdir()
    # Move the original destination into the replacement ancestor: same leaf, new ancestor identity.
    (saved / destination.name).rename(destination)
    pending = _plan(source, destination, allow_pending=True)
    before = _snapshot(source.parent)
    with pytest.raises(tx._TransactionError):
        tx._recover_transaction(pending, yes=True)
    assert _snapshot(source.parent) == before


@pytest.mark.parametrize('index', range(1, 14))
@pytest.mark.parametrize('when', ['before', 'after'])
def test_process_death_at_every_journal_checkpoint(locations: tuple[Path, Path], index: int, when: str) -> None:
    """Immediate death at every WAL boundary either recovers old bytes or leaves uncertain state untouched."""
    source, destination = locations
    worker = WORKER.replace('original = tx._move', 'original = tx._checkpoint').replace(
        'def move(*args):', 'def checkpoint(*args):'
    )
    worker = worker.replace('tx._move = move', 'tx._checkpoint = checkpoint')
    if when == 'before':
        worker = worker.replace(
            '    original(*args)\n    if count == int(sys.argv[3]):\n        os._exit(73)',
            '    if count == int(sys.argv[3]):\n        os._exit(73)\n    original(*args)',
        )
    result = subprocess.run([sys.executable, '-c', worker, str(source), str(destination), str(index)], capture_output=True)
    assert result.returncode == 73, result.stderr.decode()
    pending = _plan(source, destination, allow_pending=True)
    assert pending.lock.exists()
    before = _snapshot(source.parent)
    try:
        tx._recover_transaction(pending, yes=True)
    except tx._TransactionError:
        assert _snapshot(source.parent) == before
        assert pending.lock.exists()
    else:
        assert not pending.lock.exists()
        assert _bytes(destination) == OLD


@pytest.mark.parametrize('index', range(1, 5))
@pytest.mark.parametrize('when', ['before', 'after'])
def test_recovery_interrupt_can_be_retried_without_data_loss(
    locations: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    index: int,
    when: str,
) -> None:
    """Every inverse move can fail or interrupt and still retain both old and proposed bytes for retry."""
    source, destination = locations
    plan = _plan(source, destination)
    original_move = tx._move
    original_release = tx._release_lock
    published = False

    def release(*args: object) -> None:
        nonlocal published
        published = True
        raise PermissionError('SYNTHETIC PRIVATE')

    def refuse_rollback(*args: object) -> None:
        if published:
            raise PermissionError('SYNTHETIC PRIVATE')
        original_move(*args)

    with monkeypatch.context() as patch:
        patch.setattr(tx, '_release_lock', release)
        patch.setattr(tx, '_move', refuse_rollback)
        with pytest.raises(tx._TransactionError):
            _run(plan)
    assert _bytes(destination) == NEW
    pending = _plan(source, destination, allow_pending=True)
    calls = 0

    def interrupted(*args: object) -> None:
        nonlocal calls
        calls += 1
        if when == 'before' and calls == index:
            raise KeyboardInterrupt()
        original_move(*args)
        if when == 'after' and calls == index:
            raise KeyboardInterrupt()

    with monkeypatch.context() as patch:
        patch.setattr(tx, '_move', interrupted)
        with pytest.raises(KeyboardInterrupt):
            tx._recover_transaction(pending, yes=True)
    assert pending.lock.exists()
    monkeypatch.setattr(tx, '_release_lock', original_release)
    tx._recover_transaction(_plan(source, destination, allow_pending=True), yes=True)
    assert _bytes(destination) == OLD
    assert not pending.lock.exists()


@pytest.mark.parametrize('change', ['file', 'root', 'content'])
def test_staged_identity_changes_abort_before_publication(
    locations: tuple[Path, Path],
    change: str,
) -> None:
    """A verifier cannot authorize a linked staged file/root even after building valid bytes."""
    source, destination = locations
    plan = _plan(source, destination)

    def verify(stage: Path) -> None:
        _verify(stage)
        if change == 'content':
            (stage / 'same.bin').write_bytes(b'SYNTHETIC CHANGE AFTER VALIDATION')
            return
        target = stage if change == 'root' else stage / 'same.bin'
        saved = target.with_name(target.name + '-saved')
        target.rename(saved)
        target.symlink_to(saved, target_is_directory=change == 'root')

    with pytest.raises(tx._TransactionError):
        tx._execute_transaction(plan, _write, verify, yes=True)
    assert _bytes(destination) == OLD


def test_target_collision_precedes_destination_mutation(locations: tuple[Path, Path]) -> None:
    """Stage and preserved controls are checked together under actual target comparison rules."""
    source, destination = locations
    (destination / '.gitignore').write_bytes(b'SYNTHETIC IGNORE')
    plan = tx._plan_transaction(source, destination, target_rules=_TargetRules(case_sensitive=False))

    def build(stage: Path) -> None:
        (stage / '.GITIGNORE').write_bytes(b'SYNTHETIC')

    with pytest.raises(tx._TransactionError):
        tx._execute_transaction(plan, build, lambda p: None, yes=True)
    assert _bytes(destination) == OLD

# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_packaging
:Synopsis:          Build, inspect, and install package artifacts offline
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tomllib
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def artifacts(pytestconfig: pytest.Config, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Use explicit candidates or build a synthetic source copy without network access."""
    candidate_dir = pytestconfig.getoption('--artifact-dir')
    if candidate_dir is None:
        root = Path(__file__).resolve().parents[2]
        source = tmp_path_factory.mktemp('package-source')
        for name in ('pyproject.toml', 'poetry.lock', 'README.md', 'LICENSE'):
            shutil.copy2(root / name, source / name)
        shutil.copytree(root / 'src', source / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (source / 'docs').mkdir()
        for name in (
            'CHANGELOG.md',
            'CONFIGURATION.md',
            'INVENTORY.md',
            'FORMAT.md',
            'TRANSACTIONS.md',
            'BACKUP.md',
            'VERIFY.md',
            'RESTORE.md',
        ):
            shutil.copy2(root / 'docs' / name, source / 'docs' / name)
        # Deliberately seed obvious synthetic private/scratch content, never real vault data.
        for name in (
            'local/private.txt',
            '.env',
            'scratch.txt',
            'src/obfuscidian/probe.key',
            'src/obfuscidian/scratch.txt',
            'src/obfuscidian/__pycache__/probe.pyc',
        ):
            sentinel = source / name
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text('SYNTHETIC PACKAGING EXCLUSION PROBE')
        candidate_dir = tmp_path_factory.mktemp('artifacts')
        _run(
            [
                sys.executable,
                '-c',
                'from poetry.core.masonry.api import build_sdist, build_wheel; '
                'import sys; build_sdist(sys.argv[1]); build_wheel(sys.argv[1])',
                str(candidate_dir),
            ],
            source,
        )
    candidate_dir = candidate_dir.resolve(strict=True)
    wheels = list(candidate_dir.glob('*.whl'))
    sdists = list(candidate_dir.glob('*.tar.gz'))
    assert len(wheels) == len(sdists) == 1, 'Use exactly one fresh wheel and sdist.'
    return wheels[0], sdists[0]


def _run(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess outside the checkout with no source-path overrides."""
    environment = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONHOME', 'OBFUSCIDIAN_KEY_PATH', 'OBFUSCIDIAN_KEY_ALIAS', 'OBFUSCIDIAN_KEY_DIR'):
        environment.pop(name, None)
    result = subprocess.run(arguments, cwd=cwd, env=environment, capture_output=True, text=True, check=False, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def _assert_metadata(data: bytes) -> None:
    """Check installation and license metadata retained by both build formats."""
    metadata = BytesParser().parsebytes(data)
    assert metadata['Name'] == 'obfuscidian'
    assert metadata['Version'] == '1.0.0.dev0'
    assert metadata['Requires-Python'] == '>=3.12'
    assert metadata['License-Expression'] == 'Apache-2.0'
    assert metadata.get_all('License-File') == ['LICENSE']
    assert set(metadata.get_all('Requires-Dist')) == {'click (>=8.5.0)', 'cryptography (>=50.0.2)'}


def test_artifact_contents(artifacts: tuple[Path, Path]) -> None:
    """Allow only package files and explicit distribution metadata/documentation."""
    wheel, sdist = artifacts
    modules = {
        '__init__.py',
        '__main__.py',
        'cli.py',
        'config.py',
        'constants.py',
        'errors.py',
        'keys.py',
        '_windows.py',
        'inventory.py',
        'paths.py',
        'crypto.py',
        'manifest.py',
        'transactions.py',
        'backup.py',
        'verification.py',
        'restore.py',
        'git_restore.py',
    }
    with zipfile.ZipFile(wheel) as archive:
        prefix = 'obfuscidian-1.0.0.dev0.dist-info/'
        assert set(archive.namelist()) == {f'obfuscidian/{name}' for name in modules} | {
            prefix + name for name in ('METADATA', 'WHEEL', 'entry_points.txt', 'RECORD', 'licenses/LICENSE')
        }
        _assert_metadata(archive.read(prefix + 'METADATA'))
        entry_points = configparser.ConfigParser()
        entry_points.read_string(archive.read(prefix + 'entry_points.txt').decode())
        assert entry_points['console_scripts']['obfuscidian'] == 'obfuscidian.cli:cli'
        assert archive.read(prefix + 'licenses/LICENSE').startswith(b'                                 Apache License')
    with tarfile.open(sdist, 'r:gz') as archive:
        prefix = 'obfuscidian-1.0.0.dev0/'
        names = {member.name for member in archive.getmembers() if member.isfile()}
        assert names == {prefix + f'src/obfuscidian/{name}' for name in modules} | {
            prefix + name
            for name in (
                'pyproject.toml',
                'poetry.lock',
                'README.md',
                'LICENSE',
                'PKG-INFO',
                'docs/CHANGELOG.md',
                'docs/CONFIGURATION.md',
                'docs/INVENTORY.md',
                'docs/FORMAT.md',
                'docs/TRANSACTIONS.md',
                'docs/BACKUP.md',
                'docs/VERIFY.md',
                'docs/RESTORE.md',
            )
        }
        metadata_file = archive.extractfile(prefix + 'PKG-INFO')
        assert metadata_file is not None
        _assert_metadata(metadata_file.read())


@pytest.mark.parametrize('artifact_index', [0, 1], ids=['wheel', 'sdist'])
def test_installation_entry_points(
    artifacts: tuple[Path, Path], artifact_index: int, tmp_path: Path, pytestconfig: pytest.Config
) -> None:
    """Install each artifact and compare console/module behavior outside its source tree.

    The default offline suite shares already installed dependencies. Supplying
    --wheelhouse uses a fresh environment with independently installed dependencies.
    """
    wheelhouse = pytestconfig.getoption('--wheelhouse')
    environment = tmp_path / 'environment'
    venv.EnvBuilder(with_pip=True).create(environment)
    scripts = environment / ('Scripts' if os.name == 'nt' else 'bin')
    python = scripts / ('python.exe' if os.name == 'nt' else 'python')
    console = scripts / ('obfuscidian.exe' if os.name == 'nt' else 'obfuscidian')
    outside = tmp_path / 'outside'
    outside.mkdir()
    if wheelhouse is None:
        # A nested venv cannot inherit the parent venv's dependencies through system_site_packages.
        # Share its installed dependency directory explicitly, without processing its editable .pth files.
        site_directory = _run([str(python), '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], outside)
        (Path(site_directory.stdout.strip()) / 'test-dependencies.pth').write_text(sysconfig.get_path('purelib') + '\n')
    else:
        project = tomllib.loads((Path(__file__).resolve().parents[2] / 'pyproject.toml').read_text())
        dependencies = project['project']['dependencies'] + project['build-system']['requires']
        _run(
            [
                str(python),
                '-m',
                'pip',
                'install',
                '--no-index',
                '--find-links',
                str(wheelhouse.resolve(strict=True)),
                *dependencies,
            ],
            outside,
        )
    _run(
        [str(python), '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-build-isolation', str(artifacts[artifact_index])],
        outside,
    )
    installed = _run([str(python), '-c', 'import obfuscidian; print(obfuscidian.__file__)'], outside)
    assert Path(installed.stdout.strip()).is_relative_to(environment)
    # Import installed format modules outside the checkout and read the frozen
    # synthetic fixture without creating any vault command or destination.
    fixture = Path(__file__).resolve().parents[1] / 'fixtures/v1'
    format_check = _run(
        [
            str(python),
            '-c',
            'import sys; from pathlib import Path; from cryptography.fernet import Fernet; '
            'from obfuscidian import manifest; '
            'assert Path(manifest.__file__).is_relative_to(Path(sys.prefix)); '
            'root=Path(sys.argv[1]); key=Fernet((root/"synthetic-fernet-key.txt").read_bytes().strip()); '
            'result=manifest._verify_mirror(root/"mirror", key); '
            'assert manifest._read_validated_file(result, result.manifest.files[-1], key)==b""; '
            'print(result.file_count, result.directory_count)',
            str(fixture),
        ],
        outside,
    )
    assert format_check.stdout == '5 4\n'
    assert format_check.stderr == ''
    # Public verify parity is available even where native backup mutation is gated.
    verify_mirror = (tmp_path / 'synthetic-verification-mirror').resolve()
    shutil.copytree(fixture / 'mirror', verify_mirror)
    verify_key = tmp_path.resolve() / 'synthetic-verification.key'
    verify_key.write_bytes((fixture / 'synthetic-fernet-key.txt').read_bytes().strip())
    verify_key.chmod(0o600)
    before_verify = {
        path.relative_to(verify_mirror): (path.read_bytes() if path.is_file() else None, path.stat().st_mtime_ns)
        for path in (verify_mirror, *verify_mirror.rglob('*'))
    }
    for arguments in (
        ['verify', '--help'],
        ['verify', '--mirror', str(verify_mirror), '--key', str(verify_key), '--non-interactive'],
    ):
        console_result = _run([str(console), *arguments], outside)
        module_result = _run([str(python), '-m', 'obfuscidian', *arguments], outside)
        assert console_result.stdout == module_result.stdout
        assert console_result.stderr == module_result.stderr == ''
        if '--help' not in arguments:
            assert '5 files, 4 directories' in console_result.stdout
            assert str(verify_mirror) not in console_result.stdout
            assert verify_key.read_text() not in console_result.stdout
    assert {
        path.relative_to(verify_mirror): (path.read_bytes() if path.is_file() else None, path.stat().st_mtime_ns)
        for path in (verify_mirror, *verify_mirror.rglob('*'))
    } == before_verify
    for option in ('--help', '--version'):
        console_result = _run([str(console), option], outside)
        module_result = _run([str(python), '-m', 'obfuscidian', option], outside)
        assert console_result.stdout == module_result.stdout
        assert console_result.stderr == module_result.stderr == ''
        if option == '--version':
            assert console_result.stdout == 'obfuscidian, version 1.0.0.dev0\n'
        else:
            assert 'Usage: obfuscidian [OPTIONS]' in console_result.stdout
            assert 'planned' in console_result.stdout and 'unavailable' in console_result.stdout
            assert (
                'Commands:' in console_result.stdout and 'keygen' in console_result.stdout and 'shroud' in console_result.stdout
            )
    key_directory = (tmp_path / 'synthetic-keys').resolve()
    key_directory.mkdir()
    for arguments in (
        ['keygen', '--help'],
        ['keygen', '--alias', 'dry-run', '--dir', str(key_directory), '--non-interactive', '--dry-run'],
    ):
        console_result = _run([str(console), *arguments], outside)
        module_result = _run([str(python), '-m', 'obfuscidian', *arguments], outside)
        assert console_result.stdout == module_result.stdout
        assert console_result.stderr == module_result.stderr == ''
        assert list(key_directory.iterdir()) == []
    for entry_point, alias in (([str(console)], 'console'), ([str(python), '-m', 'obfuscidian'], 'module')):
        result = _run([*entry_point, 'keygen', '--alias', alias, '--dir', str(key_directory), '--non-interactive'], outside)
        key = key_directory / f'obfuscidian-{alias}.key'
        assert key.exists()
        assert key.read_bytes().decode() not in result.stdout + result.stderr
        assert str(key_directory) not in result.stdout + result.stderr
    origin = (tmp_path / 'synthetic-origin').resolve()
    origin.mkdir()
    (origin / 'note.md').write_bytes(b'SYNTHETIC INSTALLED NOTE\r\n')
    (origin / 'attachment.bin').write_bytes(bytes(range(256)))
    (origin / 'empty').mkdir()
    key = key_directory / 'obfuscidian-console.key'
    for entry_point, name in (([str(console)], 'console'), ([str(python), '-m', 'obfuscidian'], 'module')):
        mirror = (tmp_path / f'synthetic-{name}-mirror').resolve()
        arguments = ['shroud', 'fresh', '--origin', str(origin), '--mirror', str(mirror), '--key', str(key), '--non-interactive']
        _run([*entry_point, 'shroud', '--help'], outside)
        preview = _run([*entry_point, *arguments, '--dry-run'], outside)
        assert 'Dry run:' in preview.stdout and not mirror.exists()
        if os.name == 'posix':
            published = _run([*entry_point, *arguments], outside)
            assert 'snapshot published' in published.stdout
            unchanged = _run([*entry_point, *arguments], outside)
            assert 'no-op' in unchanged.stdout
            validation = _run(
                [
                    str(python),
                    '-c',
                    'import sys; from pathlib import Path; from obfuscidian import manifest, keys; '
                    'cipher,_=keys._load_key(Path(sys.argv[2])); '
                    'checked=manifest._verify_mirror(Path(sys.argv[1]),cipher); '
                    'assert checked.file_count==2 and checked.directory_count==1; '
                    'assert {r.path:manifest._read_validated_file(checked,r,cipher) for r in checked.manifest.files}'
                    '=={"note.md":b"SYNTHETIC INSTALLED NOTE\\r\\n","attachment.bin":bytes(range(256))}',
                    str(mirror),
                    str(key),
                ],
                outside,
            )
            assert validation.stdout == validation.stderr == ''
            assert str(origin) not in published.stdout + unchanged.stdout
            # Installed merge retains an old renamed path with exact ciphertext.
            old_tokens = {path.name: path.read_bytes() for path in (mirror / '.obfuscidian/objects').iterdir()}
            (origin / 'note.md').rename(origin / 'renamed.md')
            merge_arguments = list(arguments)
            merge_arguments[1] = 'merge'
            merged = _run([*entry_point, *merge_arguments], outside)
            assert 'snapshot published' in merged.stdout and 'recovery data removed' in merged.stdout
            assert 'deleted or renamed notes can return' in merged.stdout
            for name, token in old_tokens.items():
                assert (mirror / '.obfuscidian/objects' / name).read_bytes() == token
            stable = {
                path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (mirror / '.obfuscidian').rglob('*.obf')
            }
            noop = _run([*entry_point, *merge_arguments], outside)
            assert 'no-op' in noop.stdout
            assert {
                path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (mirror / '.obfuscidian').rglob('*.obf')
            } == stable
            _run(
                [
                    str(python),
                    '-c',
                    'import sys; from pathlib import Path; from obfuscidian import manifest,keys; '
                    'cipher,_=keys._load_key(Path(sys.argv[2])); checked=manifest._verify_mirror(Path(sys.argv[1]),cipher); '
                    'payload={r.path:manifest._read_validated_file(checked,r,cipher) for r in checked.manifest.files}; '
                    'assert set(payload)=={"note.md","renamed.md","attachment.bin"}; '
                    'assert payload["note.md"]==payload["renamed.md"]==b"SYNTHETIC INSTALLED NOTE\\r\\n"',
                    str(mirror),
                    str(key),
                ],
                outside,
            )
            # Both installed entry points reconstruct merge-retained history and binary bytes.
            restored = (tmp_path / f'{mirror.name}-restored').resolve()
            restore_arguments = [
                'unshroud',
                'fresh',
                '--origin',
                str(restored),
                '--mirror',
                str(mirror),
                '--key',
                str(key),
                '--non-interactive',
            ]
            _run([*entry_point, 'unshroud', '--help'], outside)
            preview = _run([*entry_point, *restore_arguments, '--dry-run'], outside)
            assert 'Dry run:' in preview.stdout and not restored.exists()
            restored_result = _run([*entry_point, *restore_arguments], outside)
            assert 'Plaintext recovery data is sensitive' in restored_result.stdout
            assert str(restored) not in restored_result.stdout
            assert (restored / 'note.md').read_bytes() == (restored / 'renamed.md').read_bytes()
            assert (restored / 'note.md').read_bytes() == b'SYNTHETIC INSTALLED NOTE\r\n'
            assert (restored / 'attachment.bin').read_bytes() == bytes(range(256))
            assert (restored / 'empty').is_dir()
            review_origin = (tmp_path / f'{mirror.name}-git-origin').resolve()
            review_origin.mkdir()

            # Real Git fixtures remain temporary; no global/system hooks or config.
            def fixture_git(*args: str, repository: Path = review_origin) -> str:
                environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
                environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
                command = subprocess.run(
                    [
                        'git',
                        '-c',
                        'core.hooksPath=' + os.devnull,
                        '-c',
                        'core.fsmonitor=false',
                        '-c',
                        'user.name=Synthetic Tester',
                        '-c',
                        'user.email=synthetic@example.invalid',
                        '-C',
                        str(repository),
                        *args,
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                return command.stdout

            fixture_git('init', '-qb', 'main')
            (review_origin / 'base-only.md').write_bytes(b'SYNTHETIC INSTALLED BASE')
            fixture_git('add', '--all')
            fixture_git('commit', '-qm', 'Created synthetic installed fixture')
            original_head = fixture_git('rev-parse', 'HEAD')
            original_index = (review_origin / '.git/index').read_bytes()
            review = (tmp_path / f'{mirror.name}-review').resolve()
            merge_arguments = [
                'unshroud',
                'merge',
                '--origin',
                str(review_origin),
                '--mirror',
                str(mirror),
                '--key',
                str(key),
                '--worktree',
                str(review),
                '--branch',
                'installed-review',
                '--non-interactive',
            ]
            preview = _run([*entry_point, *merge_arguments, '--dry-run'], outside)
            assert 'Dry run:' in preview.stdout and not review.exists()
            merged = _run([*entry_point, *merge_arguments], outside)
            assert 'unstaged and uncommitted' in merged.stdout and str(review) not in merged.stdout
            assert (review / 'note.md').read_bytes() == b'SYNTHETIC INSTALLED NOTE\r\n'
            assert (review / 'attachment.bin').read_bytes() == bytes(range(256))
            assert (review / 'base-only.md').read_bytes() == b'SYNTHETIC INSTALLED BASE'
            assert (review / '.git').is_file()
            assert fixture_git('rev-parse', 'HEAD') == original_head
            assert fixture_git('rev-parse', 'obfuscidian/installed-review') == original_head
            assert (review_origin / '.git/index').read_bytes() == original_index
            (origin / 'renamed.md').rename(origin / 'note.md')
        assert (origin / 'note.md').read_bytes() == b'SYNTHETIC INSTALLED NOTE\r\n'
    if wheelhouse is not None:
        _run([str(python), '-m', 'pip', 'check'], outside)
    assert list(outside.iterdir()) == []

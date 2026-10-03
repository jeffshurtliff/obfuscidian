# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_packaging
:Synopsis:          Build, inspect, and install foundation artifacts offline
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
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
        shutil.copy2(root / 'docs/CHANGELOG.md', source / 'docs/CHANGELOG.md')
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
    for name in ('PYTHONPATH', 'PYTHONHOME'):
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
    modules = {'__init__.py', '__main__.py', 'cli.py'}
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
            prefix + name for name in ('pyproject.toml', 'poetry.lock', 'README.md', 'LICENSE', 'PKG-INFO', 'docs/CHANGELOG.md')
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
    for option in ('--help', '--version'):
        console_result = _run([str(console), option], outside)
        module_result = _run([str(python), '-m', 'obfuscidian', option], outside)
        assert console_result.stdout == module_result.stdout
        assert console_result.stderr == module_result.stderr == ''
        if option == '--version':
            assert console_result.stdout == 'obfuscidian, version 1.0.0.dev0\n'
        else:
            assert 'Usage: obfuscidian [OPTIONS]' in console_result.stdout
            assert 'planned and unavailable' in console_result.stdout
            assert 'Commands:' not in console_result.stdout
    if wheelhouse is not None:
        _run([str(python), '-m', 'pip', 'check'], outside)
    assert list(outside.iterdir()) == []

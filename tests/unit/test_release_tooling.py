# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_release_tooling
:Synopsis:          Verify stable publication gates against synthetic Git repositories
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     09 Oct 2026
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location('check_release', _ROOT / '.github/scripts/check_release.py')
assert _SPEC is not None and _SPEC.loader is not None
_GUARD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GUARD)


@pytest.mark.parametrize(
    'value', ['v1.0.0', '1.0', '01.0.0', '1.0.0.dev0', '1.0.0rc1', '1.0.0.post1', '1.0.0+local', '--all', '']
)
def test_release_tag_refuses_nonstable_or_ambiguous_input(value: str) -> None:
    """Untrusted dispatch input cannot become an arbitrary Git revision or flag."""
    with pytest.raises(ValueError):
        _GUARD._stable_version(value)


@pytest.fixture
def release_repository(tmp_path: Path):
    """Create only a synthetic offline repository with an annotated stable tag."""
    environment = {name: value for name, value in os.environ.items() if not name.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)

    def git(*arguments: str) -> str:
        return subprocess.run(
            [
                'git',
                '-C',
                str(tmp_path),
                '-c',
                'core.hooksPath=' + os.devnull,
                '-c',
                'commit.gpgsign=false',
                '-c',
                'tag.gpgsign=false',
                '-c',
                'user.name=Synthetic Tester',
                '-c',
                'user.email=synthetic@example.invalid',
                *arguments,
            ],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git('init', '-b', 'main')
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="obfuscidian"\nversion="1.0.0"\n')
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/CHANGELOG.md').write_text('## [Unreleased]\n\n## [1.0.0] - 2026-10-08\n')
    git('add', '.')
    git('commit', '-m', 'Created synthetic stable source')
    git('update-ref', 'refs/remotes/origin/main', 'HEAD')
    git('tag', '-a', '1.0.0', '-m', 'Synthetic stable tag')
    return tmp_path, git


def test_release_guard_accepts_matching_annotated_tag_without_writes(release_repository) -> None:
    """Valid release selection preserves the checkout, branch and tag references."""
    root, git = release_repository
    refs = git('show-ref')
    status = git('status', '--porcelain')
    assert _GUARD._check_release('1.0.0', root) == git('rev-parse', 'HEAD')
    assert git('show-ref') == refs
    assert git('status', '--porcelain') == status == ''


@pytest.mark.parametrize('failure', ['lightweight', 'version', 'changelog', 'off-main'])
def test_release_guard_refuses_invalid_release_state(release_repository, failure: str) -> None:
    """Publication cannot select mismatched metadata, missing notes or off-main code."""
    root, git = release_repository
    git('tag', '-d', '1.0.0')
    if failure == 'lightweight':
        git('tag', '1.0.0')
    else:
        if failure == 'version':
            (root / 'pyproject.toml').write_text('[project]\nname="obfuscidian"\nversion="1.0.1"\n')
        elif failure == 'changelog':
            (root / 'docs/CHANGELOG.md').write_text('## [Unreleased]\n')
        else:
            (root / 'synthetic.txt').write_text('SYNTHETIC OFF-MAIN COMMIT')
        git('add', '.')
        git('commit', '-m', 'Created synthetic refusal state')
        if failure != 'off-main':
            git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        git('tag', '-a', '1.0.0', '-m', 'Synthetic invalid tag')
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        _GUARD._check_release('1.0.0', root)


def test_release_workflow_denies_cache_access_including_reusable_tests() -> None:
    """Release execution cannot read or poison caches, even without explicit cache actions."""
    workflow = yaml.load((_ROOT / '.github/workflows/publish.yml').read_text(), Loader=yaml.BaseLoader)
    assert workflow['cache-mode'] == 'none'
    for job in workflow['jobs'].values():
        assert job.get('cache-mode', workflow['cache-mode']) == 'none'
        if 'uses' in job:
            called = yaml.load((_ROOT / job['uses']).read_text(), Loader=yaml.BaseLoader)
            # GitHub propagates the caller's explicit limit; a broader request fails validation.
            assert called.get('cache-mode', 'none') == 'none'
            for called_job in called['jobs'].values():
                assert called_job.get('cache-mode', called.get('cache-mode', 'none')) == 'none'


def test_upload_workflow_requires_manual_opt_in_and_all_validation() -> None:
    """Release events cannot upload, and dispatch must cross validation/approval gates."""
    workflow = yaml.load((_ROOT / '.github/workflows/publish.yml').read_text(), Loader=yaml.BaseLoader)
    assert set(workflow['on']) == {'workflow_dispatch'}
    inputs = workflow['on']['workflow_dispatch']['inputs']
    assert inputs['publish']['type'] == 'boolean' and inputs['publish']['default'] == 'false'
    jobs = workflow['jobs']
    assert jobs['preflight']['if'] == "github.ref == 'refs/heads/main'"
    assert jobs['tests']['needs'] == 'preflight'
    assert jobs['tests']['uses'] == './.github/workflows/test.yml'
    assert jobs['tests']['with']['release_ref'] == '${{ needs.preflight.outputs.commit }}'
    assert jobs['build']['needs'] == ['preflight', 'tests']
    checkout = jobs['build']['steps'][0]
    assert checkout['with']['ref'] == '${{ needs.preflight.outputs.commit }}'
    commands = '\n'.join(step.get('run', '') for step in jobs['build']['steps'])
    assert 'sphinx-build -W' in commands and 'check_docs.py' in commands
    assert 'check_artifacts.py --output-dir dist --expected-version' in commands
    upload = jobs['publish']
    assert upload['if'] == 'inputs.publish == true' and upload['needs'] == 'build'
    assert upload['environment'] == 'release'
    assert upload['permissions']['id-token'] == 'write'
    assert 'id-token' not in workflow['permissions']
    for name, job in jobs.items():
        if name != 'publish':
            assert 'id-token' not in job.get('permissions', {})
    test_workflow = yaml.load((_ROOT / '.github/workflows/test.yml').read_text(), Loader=yaml.BaseLoader)
    assert 'workflow_call' in test_workflow['on']
    matrix = test_workflow['jobs']['test']['strategy']['matrix']
    assert matrix['os'] == ['ubuntu-latest', 'macos-latest', 'windows-latest']
    assert matrix['python-version'] == ['3.12', '3.13', '3.14']


@pytest.mark.parametrize('failure', ['nonempty', 'symlink', 'wrong-version'])
def test_candidate_helper_refuses_unsafe_output_before_build(tmp_path: Path, failure: str) -> None:
    """Candidate validation cannot overwrite existing files or build mismatched versions."""
    output = tmp_path / 'candidate'
    sentinel = tmp_path / 'sentinel'
    sentinel.write_bytes(b'SYNTHETIC PRESERVATION PROBE')
    expected_version = '1.0.0'
    if failure == 'nonempty':
        output.mkdir()
        (output / 'sentinel').write_bytes(sentinel.read_bytes())
    elif failure == 'symlink':
        try:
            output.symlink_to(tmp_path, target_is_directory=True)
        except OSError:
            pytest.skip('Host cannot create a synthetic directory symlink.')
    else:
        expected_version = '9.0.0'
    result = subprocess.run(
        [
            sys.executable,
            str(_ROOT / '.github/scripts/check_artifacts.py'),
            '--output-dir',
            str(output),
            '--expected-version',
            expected_version,
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert sentinel.read_bytes() == b'SYNTHETIC PRESERVATION PROBE'
    assert 'Building obfuscidian' not in result.stdout
    if failure == 'nonempty':
        assert list(output.iterdir()) == [output / 'sentinel']
        assert (output / 'sentinel').read_bytes() == sentinel.read_bytes()
    elif failure == 'symlink':
        assert output.is_symlink()
    else:
        assert not output.exists()

# -*- coding: utf-8 -*-
"""
:Module:            check_artifacts
:Synopsis:          Validate fresh isolated artifacts with portable temporary paths
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     08 Oct 2026
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path

from packaging.requirements import Requirement


def main() -> None:
    """Build and test exactly one fresh wheel/sdist in independent environments."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--output-dir', type=Path, help='Retain validated candidates in a new or empty directory.')
    parser.add_argument('--expected-version', help='Require this exact stable project version.')
    options = parser.parse_args()
    poetry = shutil.which('poetry')
    if poetry is None:
        raise RuntimeError('Poetry must be available on PATH.')
    project = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    if options.expected_version is not None:
        from packaging.version import Version

        expected = Version(options.expected_version)
        if (
            str(expected) != options.expected_version
            or expected.is_prerelease
            or expected.is_postrelease
            or expected.local is not None
            or project['project']['version'] != options.expected_version
        ):
            raise ValueError('Expected version must match exact stable project metadata.')
    requirements = project['project']['dependencies'] + project['build-system']['requires']
    pinned = [f'{Requirement(item).name}=={version(Requirement(item).name)}' for item in requirements]
    with ExitStack() as stack:
        if options.output_dir is None:
            candidate = stack.enter_context(tempfile.TemporaryDirectory(prefix='obfuscidian-artifacts-'))
        else:
            if options.output_dir.is_symlink():
                raise ValueError('Candidate directory must not be a symbolic link.')
            options.output_dir.mkdir(parents=True, exist_ok=True)
            if any(options.output_dir.iterdir()):
                raise ValueError('Candidate directory must be empty; existing artifacts are never overwritten.')
            candidate = str(options.output_dir.resolve())
        with tempfile.TemporaryDirectory(prefix='obfuscidian-wheelhouse-') as wheelhouse:
            subprocess.run([poetry, 'build', '--output', candidate], check=True)
            artifacts = sorted(str(path) for path in Path(candidate).iterdir())
            subprocess.run([sys.executable, '-m', 'twine', 'check', '--strict', *artifacts], check=True)
            subprocess.run(
                [sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--dest', wheelhouse, *pinned], check=True
            )
            subprocess.run(
                [
                    sys.executable,
                    '-m',
                    'pytest',
                    '-q',
                    '-ra',
                    'tests/integration/test_packaging.py',
                    '--artifact-dir',
                    candidate,
                    '--wheelhouse',
                    wheelhouse,
                ],
                check=True,
            )

        checksum_lines = []
        for artifact in artifacts:
            with Path(artifact).open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            checksum_lines.append(f'{digest}  {Path(artifact).name}\n')
        checksums = ''.join(checksum_lines)
        Path(candidate, 'SHA256SUMS').write_text(checksums, encoding='ascii')
        print(checksums, end='')


if __name__ == '__main__':
    main()

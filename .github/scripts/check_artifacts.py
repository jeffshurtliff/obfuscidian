# -*- coding: utf-8 -*-
"""
:Module:            check_artifacts
:Synopsis:          Validate fresh isolated artifacts with portable temporary paths
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import tomllib
from importlib.metadata import version
from pathlib import Path

from packaging.requirements import Requirement


def main() -> None:
    """Build and test exactly one fresh wheel/sdist in independent environments."""
    poetry = shutil.which('poetry')
    if poetry is None:
        raise RuntimeError('Poetry must be available on PATH.')
    project = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    requirements = project['project']['dependencies'] + project['build-system']['requires']
    pinned = [f'{Requirement(item).name}=={version(Requirement(item).name)}' for item in requirements]
    with tempfile.TemporaryDirectory(prefix='obfuscidian-artifacts-') as candidate:
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


if __name__ == '__main__':
    main()

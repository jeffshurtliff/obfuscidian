# -*- coding: utf-8 -*-
"""
:Module:            check_release
:Synopsis:          Refuse mismatched or nonstable release tags before workflow validation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     08 Oct 2026
"""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from pathlib import Path

from packaging.version import Version


def _stable_version(value: str) -> str:
    """Require a canonical bare three-component stable version.

    :param value: Requested release tag.
    :returns: Validated version, safe to use as a Git revision.
    :raises ValueError: The value is not an exact stable release tag.
    """
    if re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', value) is None or str(Version(value)) != value:
        raise ValueError('Use an exact bare stable version such as 1.0.0.')
    return value


def _check_release(value: str, repository: Path) -> str:
    """Require an annotated tag on main with matching metadata and release notes.

    :param value: Requested stable release tag.
    :param repository: Checkout containing the fetched tag and origin/main.
    :returns: Exact release commit SHA.
    :raises ValueError: Tag type, ancestry, version or changelog disagrees.
    :raises subprocess.CalledProcessError: Required Git objects are unavailable.
    """
    tag = _stable_version(value)

    def git(*arguments: str) -> str:
        return subprocess.run(
            ['git', '-C', str(repository), *arguments], check=True, capture_output=True, text=True, timeout=30
        ).stdout.strip()

    reference = f'refs/tags/{tag}'
    if git('cat-file', '-t', reference) != 'tag':
        raise ValueError('Release tag must be annotated.')
    commit = git('rev-parse', f'{reference}^{{commit}}')
    git('merge-base', '--is-ancestor', commit, 'refs/remotes/origin/main')
    metadata = tomllib.loads(git('show', f'{commit}:pyproject.toml'))['project']
    if metadata['name'] != 'obfuscidian' or metadata['version'] != tag:
        raise ValueError('Tag and package metadata must agree.')
    changelog = git('show', f'{commit}:docs/CHANGELOG.md')
    if re.search(rf'^## \[{re.escape(tag)}\] - \d{{4}}-\d{{2}}-\d{{2}}$', changelog, re.MULTILINE) is None:
        raise ValueError('Changelog must contain the dated release section.')
    return commit


def main() -> None:
    """Validate the dispatch inputs without publishing or changing Git state."""
    commit = _check_release(os.environ['RELEASE_VERSION'], Path.cwd())
    print(commit)


if __name__ == '__main__':
    main()

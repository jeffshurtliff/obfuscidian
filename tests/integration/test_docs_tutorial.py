# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_docs_tutorial
:Synopsis:          Executes public beginner examples and the synthetic restore rehearsal
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     07 Oct 2026
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _example_blocks(page: str) -> list[str]:
    """Read executable shell blocks from a checked-in documentation page."""
    root = Path(__file__).resolve().parents[2]
    content = (root / 'docs' / page).read_text(encoding='utf-8')
    return re.findall(r'^```(?:bash|sh)\n(.*?)^```$', content, flags=re.MULTILINE | re.DOTALL)


def _example_environment(tmp_path: Path) -> dict[str, str]:
    """Use the installed CLI with isolated home, Git configuration and temporary files."""
    environment = {name: value for name, value in os.environ.items() if not name.startswith(('OBFUSCIDIAN_', 'GIT_', 'PYTHON'))}
    environment['OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE'] = '1'
    environment['PATH'] = os.pathsep.join((str(Path(sys.executable).parent), environment.get('PATH', '')))
    environment['TMPDIR'] = str(tmp_path)
    environment['HOME'] = str(tmp_path)
    environment['GIT_CONFIG_NOSYSTEM'] = '1'
    environment['GIT_CONFIG_GLOBAL'] = os.devnull
    return environment


def _run_examples(blocks: list[str], workspace: Path, environment: dict[str, str]) -> None:
    """Execute documented commands in order and stop on the first failure."""
    assert blocks, 'Expected at least one executable example.'
    result = subprocess.run(  # nosec B603: checked-in commands, synthetic temporary workspace, no external data.
        [shutil.which('bash') or '/bin/bash', '-c', 'set -eu\n' + '\n'.join(blocks)],
        cwd=workspace,
        env=environment,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(os.name == 'nt', reason='The documented POSIX mutation examples are unsupported on native Windows.')
def test_beginner_quickstart_and_fresh_restore(tmp_path: Path) -> None:
    """Run the beginner path and independently check the original and restored note."""
    environment = _example_environment(tmp_path)
    _run_examples(_example_blocks('getting-started/quickstart.md'), tmp_path, environment)
    demos = [path for path in tmp_path.iterdir() if (path / 'vault').is_dir()]
    assert len(demos) == 1
    demo = demos[0]
    _run_examples(_example_blocks('getting-started/creating-a-backup.md'), demo, environment)
    _run_examples(_example_blocks('getting-started/fresh-restore.md'), demo, environment)
    expected = b'# Hello\n\nThis is a practice note.\n'
    for name in ('vault', 'restored', 'restored-again'):
        assert (demo / name / 'Hello.md').read_bytes() == expected
        assert {p.name for p in (demo / name).iterdir()} == {'Hello.md'}
    assert (demo / 'keys/obfuscidian-demo.key').is_file()
    assert (demo / 'mirror/.obfuscidian/manifest.obf').is_file()
    assert not list(demo.glob('.obfuscidian-lock-*'))


@pytest.mark.skipif(os.name == 'nt', reason='The documented POSIX Git restore is unsupported on native Windows.')
def test_beginner_git_merge_restore(tmp_path: Path) -> None:
    """Prove the documented merge overlays backup bytes, retains base-only files and leaves Git changes uncommitted."""
    environment = _example_environment(tmp_path)
    _run_examples(_example_blocks('getting-started/quickstart.md'), tmp_path, environment)
    demo = next(path for path in tmp_path.iterdir() if (path / 'vault').is_dir())
    vault = demo / 'vault'
    base_note = b'This synthetic version is committed in Git.\n'
    base_only = b'This synthetic note is not in the backup.\n'
    (vault / 'Hello.md').write_bytes(base_note)
    (vault / 'Base-only.md').write_bytes(base_only)

    def git(*args: str) -> str:
        """Run Git only against the isolated synthetic repository."""
        result = subprocess.run(  # nosec B603 B607: fixed Git executable, argument list, synthetic repository.
            ['git', '-C', str(vault), *args], env=environment, capture_output=True, text=True, timeout=30, check=True
        )
        return result.stdout.strip()

    git('init', '--initial-branch=main', '--template=')
    git('config', 'user.name', 'Synthetic Docs Example')
    git('config', 'user.email', 'docs@example.invalid')
    git('config', 'commit.gpgsign', 'false')
    git('config', 'core.autocrlf', 'false')
    git('add', '--', 'Hello.md', 'Base-only.md')
    git('commit', '-m', 'Created synthetic docs fixture')
    before = git('rev-parse', 'HEAD')
    merge = _example_blocks('getting-started/merge-restore.md')
    _run_examples(merge[:1], demo, environment)
    assert not (demo / 'vault-review').exists()
    assert git('branch', '--list', 'obfuscidian/review') == ''
    _run_examples(merge[1:], demo, environment)
    review = demo / 'vault-review'
    assert (review / 'Hello.md').read_bytes() == b'# Hello\n\nThis is a practice note.\n'
    assert (review / 'Base-only.md').read_bytes() == base_only
    assert (vault / 'Hello.md').read_bytes() == base_note
    assert (vault / 'Base-only.md').read_bytes() == base_only
    assert git('rev-parse', 'HEAD') == before
    assert git('rev-parse', 'obfuscidian/review') == before
    assert git('status', '--porcelain') == ''
    _run_examples(
        [
            'test -z "$(git -C ./vault-review diff --cached --name-only)"',
            'test "$(git -C ./vault-review diff --name-only)" = Hello.md',
        ],
        demo,
        environment,
    )


@pytest.mark.skipif(os.name == 'nt', reason='The documented POSIX mutation tutorial is unsupported on native Windows.')
def test_public_restore_tutorial(tmp_path: Path) -> None:
    """Run the documented commands and independently verify their synthetic output."""
    root = Path(__file__).resolve().parents[2]
    tutorial = (root / 'docs/guides/restore-rehearsal.md').read_text(encoding='utf-8')
    blocks = re.findall(r'^```bash\n(.*?)^```$', tutorial, flags=re.MULTILINE | re.DOTALL)
    assert len(blocks) == 1, 'The tutorial must have one complete executable rehearsal.'
    environment = _example_environment(tmp_path)
    result = subprocess.run(  # nosec B603: checked-in tutorial, synthetic temporary workspace, no external data.
        [shutil.which('bash') or '/bin/bash', '-c', blocks[0]],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Synthetic restore verified: 6 files' in result.stdout
    demos = [path for path in tmp_path.iterdir() if (path / 'vault').is_dir()]
    assert len(demos) == 1
    demo = demos[0]
    expected = {
        'notes/Welcome.md': b'# Demo\n\nSynthetic restore rehearsal.\n',
        'notes/caf\u00e9.md': b'Fake Unicode note.\n',
        'attachments/sample.bin': bytes(range(256)) * 4,
        '.hidden': b'fake hidden data\n',
        '.obsidian/app.json': b'{"fakeDemoSetting": true}\n',
        'zero.txt': b'',
    }
    for directory in ('vault', 'restored'):
        vault = demo / directory
        actual = {path.relative_to(vault).as_posix(): path.read_bytes() for path in vault.rglob('*') if path.is_file()}
        assert actual == expected
        assert {path.relative_to(vault).as_posix() for path in vault.rglob('*') if path.is_dir()} == {
            'notes',
            'attachments',
            '.obsidian',
            'empty',
        }
    assert (demo / 'keys/obfuscidian-demo.key').is_file()
    assert (demo / 'mirror/.obfuscidian/manifest.obf').is_file()
    assert not list(demo.glob('.obfuscidian-lock-*'))
    # Fresh success retains transaction containers even without a previous payload.
    for transaction in demo.glob('.obfuscidian-transaction-*'):
        assert not list((transaction / 'rollback').iterdir())

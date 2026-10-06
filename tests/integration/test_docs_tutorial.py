# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_docs_tutorial
:Synopsis:          Executes the public synthetic restore rehearsal verbatim
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     06 Oct 2026
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name == 'nt', reason='The documented POSIX mutation tutorial is unsupported on native Windows.')
def test_public_restore_tutorial(tmp_path: Path) -> None:
    """Run the documented commands and independently verify their synthetic output."""
    root = Path(__file__).resolve().parents[2]
    tutorial = (root / 'docs/getting-started/tutorial.md').read_text(encoding='utf-8')
    blocks = re.findall(r'^```bash\n(.*?)^```$', tutorial, flags=re.MULTILINE | re.DOTALL)
    assert len(blocks) == 1, 'The tutorial must have one complete executable rehearsal.'
    environment = {name: value for name, value in os.environ.items() if not name.startswith(('OBFUSCIDIAN_', 'GIT_', 'PYTHON'))}
    environment['PATH'] = os.pathsep.join((str(Path(sys.executable).parent), environment.get('PATH', '')))
    environment['TMPDIR'] = str(tmp_path)
    environment['HOME'] = str(tmp_path)
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

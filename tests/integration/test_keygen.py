# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_keygen
:Synopsis:          Verify exclusive keygen across real competing CLI processes
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from obfuscidian import constants as const
from obfuscidian import keys


def test_competing_keygen_processes(tmp_path: Path) -> None:
    """One process wins a collision; the other fails without corrupting its key."""
    directory = tmp_path.resolve()
    environment = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONHOME', const.ENV_KEY_PATH, const.ENV_KEY_ALIAS, const.ENV_KEY_DIR):
        environment.pop(name, None)
    arguments = [
        sys.executable,
        '-m',
        'obfuscidian',
        'keygen',
        '--alias',
        'synthetic',
        '--dir',
        str(directory),
        '--non-interactive',
    ]
    processes = []
    try:
        for _ in range(2):
            processes.append(
                subprocess.Popen(arguments, cwd=directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            )
        outputs = [process.communicate(timeout=30) for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert sorted(process.returncode for process in processes) == [0, 2]
    path = directory / 'obfuscidian-synthetic.key'
    material = path.read_bytes()
    cipher, _ = keys._load_key(path)
    assert cipher.decrypt(cipher.encrypt(b'SYNTHETIC')) == b'SYNTHETIC'
    for stdout, stderr in outputs:
        assert material not in stdout + stderr
        assert str(directory).encode() not in stdout + stderr
    result = subprocess.run(arguments, cwd=directory, env=environment, capture_output=True, check=False, timeout=30)
    assert result.returncode == 2
    assert path.read_bytes() == material
    assert list(directory.iterdir()) == [path]

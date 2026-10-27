# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_lifecycle_tooling
:Synopsis:          Check interpreter probe refusal and Windows shell file execution
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     12 Oct 2026
"""

from __future__ import annotations

import ctypes
import json
import platform
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_HELPER = _ROOT / '.github/scripts/check_windows_lifecycle.ps1'


def _probe_source() -> str:
    """Read the exact embedded probe that the maintainer helper saves as a file."""
    return _HELPER.read_text(encoding='utf-8').split("$Probe = @'\n", 1)[1].split("\n'@", 1)[0]


@pytest.fixture
def injected_windows(monkeypatch):
    """Supply synthetic interpreter/token responses without changing a native token."""
    monkeypatch.setattr(sys, 'implementation', SimpleNamespace(name='cpython'))
    monkeypatch.setattr(sys, 'version_info', (3, 13, 14))
    monkeypatch.setattr(sys, 'argv', ['synthetic-probe.py', '13'])
    monkeypatch.setattr(sys, 'executable', 'C:/synthetic/PythonSoftwareFoundation.Python.3.13/python.exe')
    monkeypatch.setattr(platform, 'python_implementation', lambda: 'CPython')
    monkeypatch.setattr(platform, 'python_version', lambda: '3.13.14')
    monkeypatch.setattr(platform, 'machine', lambda: 'AMD64')
    monkeypatch.setattr(struct, 'calcsize', lambda _: 8)
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: 0)), raising=False)


def test_probe_reports_complete_injected_metadata(injected_windows, capsys) -> None:
    """The full probe emits one complete metadata line for an injected eligible host."""
    exec(compile(_probe_source(), 'synthetic-probe.py', 'exec'), {})
    output = capsys.readouterr()
    assert output.err == ''
    assert len(output.out.splitlines()) == 1
    assert json.loads(output.out) == {
        'implementation': 'CPython',
        'version': '3.13.14',
        'architecture': 'AMD64',
        'bits': 64,
        'store_package_path_detected': True,
        'elevated': False,
    }


@pytest.mark.parametrize('failure', ['implementation', 'minor', 'architecture', 'bits', 'elevated'])
def test_probe_refuses_ineligible_injected_host(injected_windows, monkeypatch, capsys, failure) -> None:
    """An ineligible injected host cannot produce successful qualification metadata."""
    if failure == 'implementation':
        monkeypatch.setattr(sys, 'implementation', SimpleNamespace(name='pypy'))
    elif failure == 'minor':
        monkeypatch.setattr(sys, 'version_info', (3, 14, 6))
    elif failure == 'architecture':
        monkeypatch.setattr(platform, 'machine', lambda: 'ARM64')
    elif failure == 'bits':
        monkeypatch.setattr(struct, 'calcsize', lambda _: 4)
    else:
        monkeypatch.setattr(ctypes.windll.shell32, 'IsUserAnAdmin', lambda: 1)
    with pytest.raises(AssertionError):
        exec(compile(_probe_source(), 'synthetic-probe.py', 'exec'), {})
    assert capsys.readouterr().out == ''


@pytest.mark.skipif(sys.platform != 'win32', reason='Requires the real Windows shell used by Poetry execution.')
@pytest.mark.parametrize('line_ending', ['\n', '\r\n'])
def test_complete_probe_file_through_windows_shell(tmp_path: Path, line_ending: str) -> None:
    """A BOM-bearing file with a spaced path emits full metadata through the native shell."""
    probe = tmp_path / 'synthetic interpreter probe.py'
    probe.write_bytes(_probe_source().replace('\n', line_ending).encode('utf-8-sig'))
    # Match Poetry's Windows execution path; only owned synthetic script data is run.
    result = subprocess.run(
        [sys.executable, str(probe), str(sys.version_info.minor)],
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    assert len(result.stdout.splitlines()) == 1
    metadata = json.loads(result.stdout)
    assert metadata['version'] == platform.python_version()
    assert metadata['implementation'] == 'CPython'
    assert metadata['architecture'].upper() == 'AMD64'
    assert metadata['bits'] == 64
    assert metadata['elevated'] is False

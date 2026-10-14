# -*- coding: utf-8 -*-
"""
:Module:            record_qualification_environment
:Synopsis:          Record path-free candidate and host observations without qualifying support
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


def _git(*arguments: str) -> str:
    """Read local Git state through literal arguments."""
    return subprocess.run(['git', *arguments], check=True, capture_output=True, text=True, timeout=30).stdout.strip()


def _main() -> None:
    """Write a new observation report; success is not a matrix/native qualification result."""
    parser = argparse.ArgumentParser(description=_main.__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    assert Path.cwd().resolve() == root, 'Run from the reviewed repository root.'
    commit = _git('rev-parse', 'HEAD')
    expected = os.environ.get('OBFUSCIDIAN_QUALIFICATION_REF')
    if expected:
        assert commit == _git('rev-parse', '--verify', '--end-of-options', expected + '^{commit}'), 'Wrong candidate commit.'
    sources = _git('ls-files', '-z').split('\0')
    hashes = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources if name and (root / name).is_file()
    }
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    report = {
        'base_commit': commit,
        'tracked_source_digest': digest,
        'tracked_source_sha256': hashes,
        'dirty': bool(_git('status', '--porcelain=v1')),
        'os': platform.system(),
        'os_release': platform.release(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'python': platform.python_version(),
        'implementation': platform.python_implementation(),
        'bits': struct.calcsize('P') * 8,
        'git': _git('--version'),
        'scope': 'environment observations; no qualification claim',
    }
    if sys.platform == 'win32':
        report['elevated'] = bool(ctypes.windll.shell32.IsUserAnAdmin())
        # Import source-test helpers only for observation. Do not create a fixture,
        # activate privileges, change owners or mutate application dispatch.
        sys.path.insert(0, str(root))
        from obfuscidian import _windows_native as native
        from tests._windows_owner import _owner_candidate

        try:
            report['assignable_owner_group_available'] = _owner_candidate(native._Api()) is not None
            with native._Guard(Path(tempfile.gettempdir())):
                report['temporary_storage'] = 'guard-verified local fixed NTFS with persistent ACLs'
        except (OSError, AssertionError) as error:
            report['native_setup_error_type'] = type(error).__name__
            report['temporary_storage'] = 'unqualified; inspect private native test setup evidence'
        report['store_package_path_detected'] = 'PythonSoftwareFoundation.Python.' in getattr(sys, '_base_executable', '')
    else:
        report['temporary_storage_flags'] = os.statvfs(tempfile.gettempdir()).f_flag
    with options.output.open('x', encoding='utf-8') as destination:
        json.dump(report, destination, indent=2, sort_keys=True)
        destination.write('\n')


if __name__ == '__main__':
    _main()

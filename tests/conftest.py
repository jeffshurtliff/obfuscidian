# -*- coding: utf-8 -*-
"""
:Module:            tests.conftest
:Synopsis:          Configure optional fully isolated artifact validation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     07 Oct 2026
"""

from __future__ import annotations

from pathlib import Path

import pytest

from obfuscidian import constants as const


@pytest.fixture(autouse=True)
def suppress_live_update_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep ordinary commands and child processes offline; notifier tests opt into mocks."""
    monkeypatch.setenv(const.ENV_SUPPRESS_UPDATE_NOTICE, '1')


def pytest_addoption(parser: pytest.Parser) -> None:
    """Accept fresh artifacts and an offline dependency wheelhouse."""
    parser.addoption('--artifact-dir', type=Path, help='Directory containing exactly one fresh wheel and sdist.')
    parser.addoption('--wheelhouse', type=Path, help='Offline dependency wheels for fully isolated installation tests.')

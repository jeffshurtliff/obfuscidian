# -*- coding: utf-8 -*-
"""
:Module:            tests.conftest
:Synopsis:          Configure optional fully isolated artifact validation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Accept fresh artifacts and an offline dependency wheelhouse."""
    parser.addoption('--artifact-dir', type=Path, help='Directory containing exactly one fresh wheel and sdist.')
    parser.addoption('--wheelhouse', type=Path, help='Offline dependency wheels for fully isolated installation tests.')

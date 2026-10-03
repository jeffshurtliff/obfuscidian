# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.errors
:Synopsis:          Internal redacted configuration and operational errors
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""


class _ConfigurationError(Exception):
    """Reject missing, ambiguous, or unsafe configuration without path disclosure."""


class _OperationalError(Exception):
    """Report an I/O failure without including private paths or key contents."""

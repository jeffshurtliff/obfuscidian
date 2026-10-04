# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.errors
:Synopsis:          Internal redacted configuration and operational errors
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""


class _ConfigurationError(Exception):
    """Reject missing, ambiguous, or unsafe configuration without path disclosure."""


class _OperationalError(Exception):
    """Report an I/O failure without including private paths or key contents."""


class _FormatError(_OperationalError):
    """Reject invalid, incomplete, or unauthenticated backups without payload disclosure."""

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.verification
:Synopsis:          Internal read-only verification and pending ownership inspection
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

from pathlib import Path

from obfuscidian import keys, manifest, paths, transactions
from obfuscidian.errors import _ConfigurationError, _FormatError, _OperationalError


def _reject_pending(mirror: Path) -> None:
    """Inspect canonical ownership markers in every ancestor without opening them.

    Backup uses conservative case-folded NFC lock naming on every platform.
    Length/restore rules are irrelevant to computing that same ownership name.
    Any marker type, including a broken link or malformed record, blocks success.
    Retained workspaces without ownership markers are not pending transactions.
    """
    name = transactions._lock_name(mirror, paths._TargetRules(case_sensitive=False, normalization='NFC'))
    if any(transactions._entry_exists(parent / name) for parent in mirror.parents):
        raise _OperationalError(
            'Mirror has pending transaction ownership; inspect the documented backup recovery procedure separately. '
            'Verification does not recover or remove artifacts.'
        )


def _verify_backup(mirror: Path, key: Path) -> tuple[manifest._VerifiedMirror, tuple[str, ...]]:
    """Authenticate a complete mirror without requiring writable paths or an origin.

    Inspect ownership before and after validation, using the publication lock
    convention without acquiring a lock or reading private recovery records.
    Complete validation is still a best-effort observation under concurrent use.

    :param mirror: Absolute mirror path with safe existing ancestors.
    :param key: Selected external key path; never generated or replaced.
    :returns: Completely validated metadata and redacted key-permission warnings.
    :raises _ConfigurationError: Unsafe paths or a key inside the mirror.
    :raises _FormatError: Missing, incomplete, unsupported or corrupt backup data.
    :raises _OperationalError: Pending ownership, changing state or I/O failure.
    """
    root = paths._inspect_path(mirror, allow_missing=True)
    if key == mirror or key.is_relative_to(mirror):
        raise _ConfigurationError('Select a key outside the encrypted mirror.')
    _reject_pending(mirror)
    if not root.exists:
        raise _FormatError('Mirror is missing; select an existing complete backup. Verification creates no destination.')
    fernet, warnings = keys._load_key(key)
    try:
        result = manifest._verify_mirror(mirror, fernet)
    except _FormatError as error:
        raise _FormatError(
            f'{error} Check the selected key, complete manifest/object set and supported reader version; '
            'use a known-good complete snapshot if data is damaged.'
        ) from None
    paths._recheck_path(root, content=True)
    _reject_pending(mirror)
    return result, warnings

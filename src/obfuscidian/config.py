# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.config
:Synopsis:          Internal CLI and environment configuration resolution
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     08 Oct 2026
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError


def _validate_alias(alias: str) -> str:
    """Validate an explicitly supplied alias without modifying it."""
    if re.fullmatch(const.ALIAS_PATTERN, alias, flags=re.ASCII) is None:
        raise _ConfigurationError(f'Alias must contain 1–{const.ALIAS_MAX_LENGTH} ASCII letters, digits, or hyphens.')
    return alias


def _expand_path(value: str | Path, label: str) -> Path:
    """Expand home and cwd, retaining link components for later safety checks.

    Arbitrary shell variables are literal. This is resolution only, not vault
    preflight; consumers must validate filesystem types and retain identities.
    """
    if not str(value) or '\0' in str(value):
        raise _ConfigurationError(f'{label} must be a nonempty valid path.')
    try:
        return Path(value).expanduser().absolute()
    except (OSError, RuntimeError, ValueError):
        raise _ConfigurationError(f'{label} could not be resolved.') from None


def _alias_path(alias: str, directory: str | Path | None) -> Path:
    """Build a selected key path without inspecting or creating it."""
    _validate_alias(alias)
    base = _expand_path(directory if directory is not None else '~', 'Key directory')
    return base / f'{const.KEY_PREFIX}{alias}{const.KEY_SUFFIX}'


def _resolve_key_path(
    *,
    key: str | None = None,
    alias: str | None = None,
    keydir: str | None = None,
    environ: Mapping[str, str] | None = None,
    alias_prompt: Callable[[], str] | None = None,
) -> Path:
    """Resolve loading selectors by the approved precedence/conflict matrix.

    The prompt callback is supplied only by an interactive CLI. Missing or
    invalid selected files are handled by the loader and never trigger fallback.
    """
    env = os.environ if environ is None else environ
    if key is not None:
        if alias is not None or keydir is not None:
            raise _ConfigurationError('--key cannot be combined with --alias or --keydir.')
        return _expand_path(key, '--key')
    directory = keydir if keydir is not None else env.get(const.ENV_KEY_DIR)
    if alias is not None:
        return _alias_path(alias, directory)
    if const.ENV_KEY_PATH in env:
        if keydir is not None:
            raise _ConfigurationError('--keydir is ambiguous with OBFUSCIDIAN_KEY_PATH; select --alias or --key explicitly.')
        return _expand_path(env[const.ENV_KEY_PATH], const.ENV_KEY_PATH)
    selected_alias = env.get(const.ENV_KEY_ALIAS)
    if selected_alias is None:
        if alias_prompt is None:
            raise _ConfigurationError('Select a key with --key, --alias, or OBFUSCIDIAN_KEY_PATH/KEY_ALIAS.')
        selected_alias = alias_prompt()
    return _alias_path(selected_alias, directory)


def _resolve_generation_path(
    *,
    alias: str | None = None,
    directory: str | None = None,
    environ: Mapping[str, str] | None = None,
    alias_prompt: Callable[[], str] | None = None,
) -> Path:
    """Resolve keygen alias/directory; environment KEY_PATH is never an output."""
    env = os.environ if environ is None else environ
    selected_alias = alias if alias is not None else env.get(const.ENV_KEY_ALIAS)
    if selected_alias is None:
        if alias_prompt is None:
            raise _ConfigurationError('Keygen requires --alias or OBFUSCIDIAN_KEY_ALIAS without an interactive terminal.')
        selected_alias = alias_prompt()
        if selected_alias == '':
            selected_alias = datetime.now().strftime(const.TIMESTAMP_FORMAT)
    selected_dir = directory if directory is not None else env.get(const.ENV_KEY_DIR)
    return _alias_path(selected_alias, selected_dir)


def _resolve_vault_paths(
    *, origin: str | None = None, mirror: str | None = None, environ: Mapping[str, str] | None = None
) -> tuple[Path | None, Path | None]:
    """Resolve optional vault paths separately from inventory and path preflight."""
    env = os.environ if environ is None else environ
    origin_value = origin if origin is not None else env.get(const.ENV_ORIGIN)
    mirror_value = mirror if mirror is not None else env.get(const.ENV_MIRROR)
    return (
        _expand_path(origin_value, '--origin') if origin_value is not None else None,
        _expand_path(mirror_value, '--mirror') if mirror_value is not None else None,
    )

# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.updates
:Synopsis:          Best-effort stable-release notices without application filesystem writes
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import json
import os
import ssl
from importlib.metadata import version

import certifi
import urllib3
from packaging.version import InvalidVersion, Version

from obfuscidian import constants as const


def _tls_context() -> ssl.SSLContext:
    """Require verified TLS using a packaged bundle or explicit custom trust.

    SSL_CERT_FILE and SSL_CERT_DIR replace bundled trust when either is set.
    Empty settings are rejected, and failed custom trust never falls back to
    the bundle or default certificate discovery. Paths are used as supplied.

    :returns: A context requiring certificate and hostname verification.
    :raises ValueError: An explicit trust location is empty.
    :raises OSError: A certificate file cannot be read or parsed.
    """
    ca_file = os.environ.get(const.ENV_SSL_CERT_FILE)
    ca_directory = os.environ.get(const.ENV_SSL_CERT_DIR)
    if ca_file == '' or ca_directory == '':
        raise ValueError('Empty update certificate trust setting')
    if ca_file is None and ca_directory is None:
        ca_file = certifi.where()
    return ssl.create_default_context(cafile=ca_file, capath=ca_directory)


def _fetch_releases() -> object:
    """Read bounded JSON over verified HTTPS, without redirects, retries or a cache.

    Certificate trust comes from the packaged CA bundle unless explicitly
    replaced with SSL_CERT_FILE and/or SSL_CERT_DIR.

    :returns: Decoded PyPI project metadata; no response text is emitted.
    :raises Exception: Network, decoding or response validation failure.
    """
    with urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ssl_context=_tls_context()) as pool:
        response = pool.request(
            'GET',
            const.UPDATE_API_URL,
            headers={'Accept': 'application/json', 'Accept-Encoding': 'identity'},
            timeout=urllib3.Timeout(connect=const.UPDATE_CONNECT_TIMEOUT, read=const.UPDATE_READ_TIMEOUT),
            retries=False,
            redirect=False,
            preload_content=False,
        )
        try:
            if response.status != 200:
                raise ValueError('Update lookup unavailable')
            data = response.read(const.UPDATE_RESPONSE_BYTES + 1, decode_content=False)
            if len(data) > const.UPDATE_RESPONSE_BYTES:
                raise ValueError('Update metadata exceeds limit')
            return json.loads(data)
        finally:
            response.close()


def _latest_stable(payload: object) -> Version | None:
    """Select the highest PEP 440 stable release with at least one non-yanked file.

    :param payload: Decoded PyPI project JSON, including its releases mapping.
    :returns: Latest published stable version, or None when none is eligible.
    :raises ValueError: The API response lacks the required release mapping.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get('releases'), dict):
        raise ValueError('Invalid update metadata')
    latest = None
    for name, files in payload['releases'].items():
        if not isinstance(name, str) or len(name) > const.UPDATE_VERSION_LENGTH:
            continue
        try:
            candidate = Version(name)
        except InvalidVersion:
            continue
        if candidate.is_prerelease or candidate.is_devrelease or candidate.local is not None:
            continue
        if not isinstance(files, list) or not any(isinstance(file, dict) and file.get('yanked') is False for file in files):
            continue
        if latest is None or candidate > latest:
            latest = candidate
    return latest


def _notice() -> str | None:
    """Return an advisory without exposing network errors or changing command success.

    Suppression skips metadata and network access entirely. No application file,
    vault, key, path, installed version or command argument is sent to PyPI.

    :returns: Newer-release notice, or None for suppression, unavailable checks or no update.
    """
    if os.environ.get(const.ENV_SUPPRESS_UPDATE_NOTICE, '').strip().lower() in {'true', '1'}:
        return None
    try:
        installed = Version(version('obfuscidian'))
        latest = _latest_stable(_fetch_releases())
        if latest is not None and latest > installed:
            return (
                f'A newer version of obfuscidian (v{latest}) is available. '
                f'Visit {const.UPDATE_INSTRUCTIONS_URL} for update instructions.'
            )
    except Exception:
        # Optional discovery must not block backup/restore or disclose exception payloads.
        return None
    return None

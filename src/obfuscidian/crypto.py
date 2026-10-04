# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.crypto
:Synopsis:          Internal bounded standard Fernet byte operations
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Collection

from cryptography.fernet import Fernet, InvalidToken

from obfuscidian import constants as const
from obfuscidian.errors import _FormatError, _OperationalError
from obfuscidian.inventory import _fernet_size


def _new_id(reserved: Collection[str] = ()) -> str:
    """Generate a secure opaque identifier, retrying reserved collisions before I/O.

    :param reserved: All identifiers already assigned in the caller's namespace.
    :returns: An unreserved 32-character lowercase hexadecimal identifier.
    :raises _OperationalError: Secure randomness is unavailable.
    """
    try:
        while True:
            identifier = secrets.token_hex(const.ID_RANDOM_BYTES)
            if identifier not in reserved:
                return identifier
    except (OSError, MemoryError):
        raise _OperationalError('Cannot generate a secure backup identifier.') from None


def _sha256(data: bytes) -> str:
    """Return a full SHA-256 digest for authenticated manifest binding."""
    return hashlib.sha256(data).hexdigest()


def _check_token_size(size: int) -> None:
    """Reject empty or oversized tokens before decryption or file allocation."""
    if type(size) is not int or not 0 < size <= const.MAX_ENCRYPTED_BYTES:
        raise _FormatError('Encrypted objects and manifests require nonempty tokens within the 50 MiB v1 limit.')


def _encrypt_bytes(data: bytes, fernet: Fernet) -> bytes:
    """Encrypt complete binary bytes using the standard bounded Fernet recipe.

    :param data: Original binary payload, without content normalization.
    :param fernet: The selected mirror's single validated key context.
    :returns: A complete standard encoded token including padding.
    :raises _FormatError: The input type or projected token length is invalid.
    :raises _OperationalError: Allocation or encryption fails.
    """
    if not isinstance(data, bytes):
        raise _FormatError('Encryption requires binary bytes.')
    _check_token_size(_fernet_size(len(data)))
    try:
        token = fernet.encrypt(data)
        _check_token_size(len(token))
        return token
    except (MemoryError, OSError, OverflowError):
        raise _OperationalError('Cannot encrypt the complete payload; no partial result is accepted.') from None


def _decrypt_bytes(token: bytes, fernet: Fernet) -> bytes:
    """Authenticate and decrypt one bounded archival token without a TTL.

    :param token: Complete standard encoded Fernet bytes.
    :param fernet: The selected mirror's single validated key context.
    :returns: Authenticated plaintext only after Fernet succeeds.
    :raises _FormatError: The token is invalid, oversize, or uses another key.
    :raises _OperationalError: Allocation or cryptographic I/O fails.
    """
    if not isinstance(token, bytes):
        raise _FormatError('Decryption requires binary token bytes.')
    _check_token_size(len(token))
    try:
        return fernet.decrypt(token)
    except InvalidToken:
        raise _FormatError('Backup authentication failed; check the selected key and backup integrity.') from None
    except (MemoryError, OSError, OverflowError):
        raise _OperationalError('Cannot decrypt the complete payload; no partial result is accepted.') from None

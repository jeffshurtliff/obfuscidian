# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_crypto
:Synopsis:          Standard Fernet compatibility, archival, bounds, and failure tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import re

import pytest
from cryptography.fernet import Fernet

from obfuscidian import constants as const
from obfuscidian import crypto
from obfuscidian.errors import _FormatError, _OperationalError
from obfuscidian.inventory import _fernet_size


@pytest.mark.parametrize('size', [0, 1, 2, 3, 14, 15, 16, 17, 30, 31, 32, 33, 47, 48, 49, 255, 256, 257])
def test_standard_fernet_bytes_and_estimates(size: int) -> None:
    """Cross-decrypt with the upstream recipe at padding/Base64 boundaries."""
    fernet = Fernet(Fernet.generate_key())
    data = bytes(index % 256 for index in range(size))
    token = crypto._encrypt_bytes(data, fernet)
    assert len(token) == _fernet_size(size)
    assert len(token) % 4 == 0
    assert fernet.decrypt(token) == data
    assert crypto._decrypt_bytes(fernet.encrypt(data), fernet) == data
    assert crypto._decrypt_bytes(fernet.encrypt_at_time(data, 0), fernet) == data


def test_ids_use_secure_randomness_and_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reserved collision is retried without writes or content-derived names."""
    reserved = {'a' * 32}
    values = iter(['a' * 32, 'b' * 32])
    requested = []

    def synthetic_random(size: int) -> str:
        requested.append(size)
        return next(values)

    monkeypatch.setattr(crypto.secrets, 'token_hex', synthetic_random)
    assert crypto._new_id(reserved) == 'b' * 32
    assert requested == [16, 16]
    assert reserved == {'a' * 32}
    monkeypatch.undo()
    identifiers = {crypto._new_id() for _ in range(100)}
    assert len(identifiers) == 100
    assert all(re.fullmatch(const.ID_PATTERN, identifier) for identifier in identifiers)


def test_bounds_before_crypto(monkeypatch: pytest.MonkeyPatch) -> None:
    """At-cap valid tokens pass; above-cap data fails before crypto allocation."""
    fernet = Fernet(Fernet.generate_key())
    token = fernet.encrypt(b'')
    monkeypatch.setattr(const, 'MAX_ENCRYPTED_BYTES', len(token))
    assert len(crypto._encrypt_bytes(b'', fernet)) == len(token)
    assert crypto._decrypt_bytes(token, fernet) == b''
    with pytest.raises(_FormatError):
        crypto._decrypt_bytes(token + b'x', fernet)
    with pytest.raises(_FormatError):
        crypto._encrypt_bytes(bytes(16), fernet)
    crypto._check_token_size(len(token))
    for bad in (-1, 0, True, len(token) + 1):
        with pytest.raises(_FormatError):
            crypto._check_token_size(bad)


@pytest.mark.parametrize('data', ['', bytearray(b'content'), None])
def test_binary_types_required(data: object) -> None:
    """Text and mutable buffers cannot silently change the encoded contract."""
    fernet = Fernet(Fernet.generate_key())
    with pytest.raises(_FormatError):
        crypto._encrypt_bytes(data, fernet)
    with pytest.raises(_FormatError):
        crypto._decrypt_bytes(data, fernet)


@pytest.mark.parametrize('mutation', ['wrong-key', 'changed', 'truncated', 'garbage', 'empty'])
def test_authentication_failures_are_redacted(mutation: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid tokens expose no content, key, or partial plaintext."""
    fernet = Fernet(Fernet.generate_key())
    data = b'SYNTHETIC SECRET SENTINEL'
    token = fernet.encrypt(data)
    if mutation == 'wrong-key':
        fernet = Fernet(Fernet.generate_key())
    elif mutation == 'changed':
        token = token[:40] + (b'A' if token[40:41] != b'A' else b'B') + token[41:]
    elif mutation == 'truncated':
        token = token[:-8]
    elif mutation == 'garbage':
        token = b'SYNTHETIC INVALID TOKEN'
    else:
        token = b''
    with pytest.raises(_FormatError) as error:
        crypto._decrypt_bytes(token, fernet)
    assert data.decode() not in str(error.value)
    assert repr(token) not in str(error.value)
    output = capsys.readouterr()
    assert output.out == output.err == ''


@pytest.mark.parametrize('operation', ['encrypt', 'decrypt', 'random'])
@pytest.mark.parametrize('failure', [MemoryError, OSError])
def test_allocation_and_random_failures(monkeypatch: pytest.MonkeyPatch, operation: str, failure: type[Exception]) -> None:
    """Required operations cannot return a successful partial result."""
    fernet = Fernet(Fernet.generate_key())
    token = fernet.encrypt(b'SYNTHETIC')

    def fail(*args: object) -> None:
        raise failure('SYNTHETIC PRIVATE PATH')

    if operation == 'random':
        monkeypatch.setattr(crypto.secrets, 'token_hex', fail)
        call = crypto._new_id
    else:
        monkeypatch.setattr(fernet, operation, fail)

        def call() -> bytes:
            return getattr(crypto, f'_{operation}_bytes')(b'SYNTHETIC' if operation == 'encrypt' else token, fernet)

    with pytest.raises(_OperationalError) as error:
        call()
    assert 'SYNTHETIC PRIVATE PATH' not in str(error.value)

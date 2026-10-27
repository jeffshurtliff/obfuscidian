# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_v1_exchange_tooling
:Synopsis:          Exercise generated exchange bytes and refusal before output creation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from tests import _v1_exchange as exchange


@pytest.fixture
def generated(tmp_path):
    """Generate a new synthetic key and ciphertext, never reuse the frozen v1 fixture."""
    source_id = hashlib.sha256(Path(exchange.__file__).read_bytes()).hexdigest()
    report = exchange._export(tmp_path / 'producer', source_id)
    assert report['files'] == 3 and report['directories'] == 2
    return tmp_path / 'producer/bundle'


def test_generated_v1_local_exchange_preserves_bytes_and_empty_directories(generated, tmp_path, record_property):
    """A same-host rehearsal is successful but cannot claim cross-platform exchange."""
    report = exchange._import(generated, tmp_path / 'consumer')
    assert report['producer'] == report['consumer'] == sys.platform
    assert report['cross_platform'] is False
    assert report['exact_bytes_and_directories'] and report['source_unchanged']
    record_property('exchange_evidence', 'same-platform rehearsal; no two-host exchange')


@pytest.mark.parametrize('damage', ['ciphertext', 'marker', 'extra-entry'])
def test_exchange_damage_refused_before_output_creation(generated, tmp_path, damage):
    """Altered transfer or non-synthetic setup cannot create a destination."""
    if damage == 'ciphertext':
        next((generated / 'mirror/.obfuscidian/objects').iterdir()).write_bytes(b'SYNTHETIC TRANSFER CORRUPTION')
    elif damage == 'marker':
        metadata = json.loads((generated / 'exchange.json').read_text())
        metadata['marker'] = 'UNREVIEWED INPUT'
        (generated / 'exchange.json').write_text(json.dumps(metadata))
    else:
        (generated / 'unknown').write_bytes(b'SYNTHETIC UNKNOWN')
    destination = tmp_path / 'must-stay-absent'
    with pytest.raises(AssertionError):
        exchange._import(generated, destination)
    assert not destination.exists()


def test_exchange_never_overwrites_existing_output(generated, tmp_path):
    """Keep a previously generated exchange and key byte-for-byte unchanged."""
    before = exchange._tree(generated)
    with pytest.raises(AssertionError, match='new disposable'):
        exchange._export(tmp_path / 'producer', 'a' * 40)
    assert exchange._tree(generated) == before

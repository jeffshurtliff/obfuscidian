# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_transactions
:Synopsis:          Consent, read-only preflight, private control and naming contracts
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     04 Oct 2026
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from obfuscidian import constants as const
from obfuscidian import transactions as tx
from obfuscidian.errors import _ConfigurationError, _OperationalError
from obfuscidian.paths import _TargetRules


@pytest.mark.parametrize(
    'yes,non_interactive,answer,accepted',
    [
        (True, True, False, True),
        (True, False, False, True),
        (False, True, True, False),
        (False, False, True, True),
        (False, False, False, False),
        (False, False, 1, False),
    ],
)
def test_explicit_consent_never_inferred(yes: bool, non_interactive: bool, answer: object, accepted: bool) -> None:
    """Consent is exact affirmative, and unattended execution never prompts."""
    calls = []

    def prompt() -> bool:
        calls.append(True)
        return answer

    if accepted:
        tx._confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    else:
        with pytest.raises(_OperationalError):
            tx._confirm_action(yes=yes, non_interactive=non_interactive, prompt=prompt)
    assert bool(calls) == (not yes and not non_interactive)


def test_eof_consent_and_no_prompt() -> None:
    """Unavailable terminal consent produces no affirmative authorization."""

    def eof() -> bool:
        raise EOFError('SYNTHETIC PRIVATE')

    with pytest.raises(_OperationalError, match='unavailable') as error:
        tx._confirm_action(yes=False, non_interactive=False, prompt=eof)
    assert 'SYNTHETIC PRIVATE' not in str(error.value)
    with pytest.raises(_OperationalError, match='confirmation'):
        tx._confirm_action(yes=False, non_interactive=False)


def test_target_comparison_rules_lock_aliases(tmp_path: Path) -> None:
    """Equivalent target names share ownership; case-sensitive distinct names do not."""
    insensitive = _TargetRules(case_sensitive=False, normalization='NFC')
    assert tx._lock_name(tmp_path / 'CAFÉ', insensitive) == tx._lock_name(tmp_path / 'cafe\u0301', insensitive)
    sensitive = _TargetRules(case_sensitive=True)
    assert tx._lock_name(tmp_path / 'A', sensitive) != tx._lock_name(tmp_path / 'a', sensitive)


@pytest.mark.parametrize('required', [-1, True, 0.5])
def test_invalid_estimates_without_artifacts(tmp_path: Path, required: object) -> None:
    """Resource estimates are nonnegative integer byte counts with no implicit coercion."""
    root = tmp_path.resolve()
    source = root / 'source'
    source.mkdir()
    with pytest.raises(_ConfigurationError, match='estimates'):
        tx._plan_transaction(source, root / 'destination', required_bytes=required, target_rules=_TargetRules(True))
    assert {p.name for p in root.iterdir()} == {'source'}


def test_actual_target_rules_required(tmp_path: Path) -> None:
    """A caller must supply target behavior before any preflight observation authorizes writes."""
    with pytest.raises(_ConfigurationError, match='naming rules'):
        tx._plan_transaction(tmp_path, tmp_path / 'target')


@pytest.mark.skipif(os.name != 'posix', reason='Private POSIX metadata and ownership tests.')
@pytest.mark.parametrize('case', ['duplicate', 'oversize', 'world-readable', 'link', 'hardlink'])
def test_private_journal_reader_rejects_unsafe_metadata(tmp_path: Path, case: str) -> None:
    """Malformed/bounded/linked/public recovery records never authorize mutation."""
    root = tmp_path.resolve()
    record = root / 'record'
    record.write_bytes(b'{"synthetic":1,"synthetic":2}' if case == 'duplicate' else b'{"synthetic":1}')
    record.chmod(0o600)
    if case == 'world-readable':
        record.chmod(0o644)
    elif case == 'link':
        original = root / 'original'
        record.rename(original)
        record.symlink_to(original)
    elif case == 'hardlink':
        os.link(record, root / 'alias')
    limit = 1 if case == 'oversize' else 100
    with pytest.raises((_OperationalError, _ConfigurationError, ValueError)):
        tx._read_private_json(record, limit)
    assert record.exists()


def test_no_native_write_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Platforms without the implemented ownership/privacy primitives refuse writes."""
    root = tmp_path.resolve()
    source = root / 'source'
    source.mkdir()
    plan = tx._plan_transaction(source, root / 'destination', target_rules=_TargetRules(True))
    monkeypatch.setattr(tx.os, 'name', 'nt')
    with pytest.raises(_ConfigurationError, match='POSIX'):
        tx._lock_descriptor(plan, recovery=False)
    assert not plan.lock.exists()


@pytest.mark.skipif(os.name != 'posix', reason='POSIX no-follow/private directory test.')
def test_checkpoint_refuses_replaced_workspace(tmp_path: Path) -> None:
    """Journal replacement must not write into a user-replaced workspace inode."""
    root = tmp_path.resolve()
    workspace = root / 'workspace'
    workspace.mkdir(mode=0o700)
    journal = {'workspace_identity': tx._identity(workspace.lstat())}
    workspace.rename(root / 'saved')
    workspace.mkdir(mode=0o700)
    with pytest.raises(_OperationalError, match='identity changed'):
        tx._checkpoint(workspace, journal)
    assert list(workspace.iterdir()) == []


@pytest.mark.skipif(os.name != 'posix', reason='POSIX private JSON output test.')
def test_journal_excludes_source_plaintext_and_key(tmp_path: Path) -> None:
    """Private control metadata serializes only journal state, never encryption context."""
    workspace = tmp_path.resolve() / 'workspace'
    workspace.mkdir(mode=0o700)
    journal = {'workspace_identity': tx._identity(workspace.lstat()), 'phase': 'synthetic'}
    tx._checkpoint(workspace, journal)
    assert json.loads((workspace / const.TRANSACTION_JOURNAL).read_bytes()) == journal

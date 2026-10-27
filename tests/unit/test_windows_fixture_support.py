# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_windows_fixture_support
:Synopsis:          Long-path fixture regression and injected actual-worker termination checks
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from obfuscidian import transactions as tx
from obfuscidian._windows_native import _NativeSafetyError
from tests import _windows_support as support


def test_suppressed_backend_context_reports_locations_without_private_arguments():
    """A from-None failure retains code context without exposing traceback filenames."""
    namespace = {'__name__': 'obfuscidian.synthetic', 'FileNotFoundError': FileNotFoundError}
    source = "def fail():\n    raise FileNotFoundError(2, 'SYNTHETIC SECRET', 'C:/private-fixture/secret.bin')\n"
    exec(compile(source, 'C:/private-fixture/private-code.py', 'exec'), namespace)
    try:
        try:
            namespace['fail']()
        except FileNotFoundError:
            raise tx._TransactionError(recovery_required=True) from None
    except tx._TransactionError as error:
        assert error.__suppress_context__
        details = support._failure_details(error)
    assert '_TransactionError' in details
    assert 'FileNotFoundError: obfuscidian.synthetic.fail:2' in details
    for private in ('SYNTHETIC SECRET', 'C:/', 'secret.bin', 'private-code.py'):
        assert private not in details


def test_failure_context_cycle_is_bounded_without_reporting_arguments():
    first, second = ValueError('SYNTHETIC FIRST'), OSError('SYNTHETIC SECOND')
    first.__context__, second.__context__ = second, first
    details = support._failure_details(first)
    assert details.count('ValueError') == 1 and details.count('OSError') == 1
    assert 'SYNTHETIC FIRST' not in details and 'SYNTHETIC SECOND' not in details


def test_git_attribute_status_requires_the_complete_numeric_template():
    error = _NativeSafetyError('Unsupported Windows Git attributes refused (0x00000022).')
    assert '[Git attributes 0x00000022]' in support._failure_details(error)
    error = _NativeSafetyError('Unsupported Windows Git attributes refused (0x00000022). C:/private/secret.bin')
    details = support._failure_details(error)
    assert '0x00000022' not in details and 'C:/' not in details and 'secret.bin' not in details


@pytest.mark.parametrize('code', ['WinError 32', 'NTSTATUS 0xC0000043, I/O 0xC0000043'])
def test_numeric_native_status_uses_only_complete_loader_template(code):
    error = _NativeSafetyError(f'Native Windows call refused ({code}); preserve pending artifacts.')
    assert '[' + code + ']' in support._failure_details(error)
    error = _NativeSafetyError(f'Native Windows call refused ({code}); preserve pending artifacts. C:/private/secret.bin')
    details = support._failure_details(error)
    assert code not in details and 'C:/' not in details and 'secret.bin' not in details


@pytest.mark.parametrize('message', [b'READY', b'OTHER 123', b'READY -1', b'READY 0', b'READY 123 extra', b'READY 4294967296'])
def test_worker_readiness_refuses_missing_or_invalid_pid(message):
    with pytest.raises(AssertionError):
        support._worker_pid(message, b'READY')


def test_worker_pid_and_bounded_launcher_ancestry():
    assert support._worker_pid(b'SYNTHETIC READY 123\r\n', b'SYNTHETIC READY') == 123
    assert support._descendant(123, 123, {})
    assert support._descendant(123, 120, {123: 122, 122: 120})
    assert not support._descendant(123, 120, {123: 122})
    assert not support._descendant(123, 120, {123: 122, 122: 123})
    assert not support._descendant(123, 100, {pid: pid - 1 for pid in range(101, 124)})


@pytest.mark.parametrize('failure', [None, 'foreign-worker', 'terminate', 'wait', 'exit-code', 'closed-input'])
def test_injected_worker_wait_precedes_launcher_wait_and_input_release(monkeypatch, failure):
    """Injected kernel responses test ordering/refusal; they are not actual process proof."""
    events = []
    stream = SimpleNamespace(closed=False)

    def wait(timeout):
        assert not stream.closed
        events.append('launcher-wait')
        process.returncode = 97

    process = SimpleNamespace(pid=100, stdin=stream, poll=lambda: None, wait=wait, returncode=None)

    def acquire(access, inherit, pid):
        assert (access, inherit, pid) == (0x00101001, False, 101)
        events.append('acquire')
        return 999

    def terminate(handle, code):
        assert handle == 999 and code == 97 and not stream.closed
        events.append('terminate')
        return failure != 'terminate'

    def death(handle, timeout):
        assert handle == 999 and timeout == 20_000 and not stream.closed
        events.append('worker-wait')
        return 258 if failure == 'wait' else 0

    def exit_code(handle, pointer):
        assert handle == 999
        events.append('worker-status')
        pointer._obj.value = 0 if failure == 'exit-code' else 97
        if failure == 'closed-input':
            stream.closed = True
        return True

    def close(handle):
        assert handle == 999
        events.append('close')
        return True

    api = SimpleNamespace(
        OpenProcess=acquire,
        TerminateProcess=terminate,
        WaitForSingleObject=death,
        GetExitCodeProcess=exit_code,
        CloseHandle=close,
    )
    monkeypatch.setattr(support, 'os', SimpleNamespace(name='nt', getpid=lambda: 200))
    monkeypatch.setattr(support, '_process_api', lambda: api)
    monkeypatch.setattr(support, '_parents', lambda _: {101: 300 if failure == 'foreign-worker' else 100})
    if failure is None:
        support._terminate_worker(process, b'READY 101')
        assert events == ['acquire', 'terminate', 'worker-wait', 'worker-status', 'close', 'launcher-wait']
    else:
        with pytest.raises(AssertionError):
            support._terminate_worker(process, b'READY 101')
        assert events[-1] == 'close'
        assert 'launcher-wait' not in events
        if failure == 'foreign-worker':
            assert 'terminate' not in events


@pytest.mark.skipif(os.name != 'nt', reason='Actual Windows long-path fixture I/O required.')
def test_actual_long_checkpoint_fixture_read_tamper_remove_without_policy_change(tmp_path):
    """Use the existing internal DOS conversion only for synthetic test inspection."""
    root = tmp_path.resolve() / ('synthetic-' + 'a' * 100)
    observed = support._io_path(root)
    observed.mkdir()
    logical = root / ('checkpoint-' + 'b' * 140 + '.json')
    assert len(str(logical)) > 260
    path = support._io_path(logical)
    path.write_bytes(b'SYNTHETIC KEEP\x00\xff')
    snapshot = {str(p.relative_to(observed)): p.read_bytes() for p in observed.rglob('*')}
    assert snapshot == {logical.name: b'SYNTHETIC KEEP\x00\xff'}
    path.write_bytes(b'SYNTHETIC CORRUPTION')
    assert path.read_bytes() == b'SYNTHETIC CORRUPTION'
    path.unlink()
    assert list(observed.iterdir()) == []

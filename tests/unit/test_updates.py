# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_updates
:Synopsis:          Offline stable-release selection, bounded requests and suppression
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     07 Oct 2026
"""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError

import pytest
import urllib3
from click.testing import CliRunner

from obfuscidian import constants as const
from obfuscidian import updates
from obfuscidian.cli import cli


@pytest.fixture
def enabled(monkeypatch):
    """Opt into a deterministic fake update endpoint, never a live HTTP request."""
    monkeypatch.delenv(const.ENV_SUPPRESS_UPDATE_NOTICE, raising=False)
    monkeypatch.setattr(updates, 'version', lambda name: '1.0.0')
    monkeypatch.setattr(updates, '_fetch_releases', lambda: {'releases': {'1.1.0': [{'yanked': False}]}})


@pytest.mark.parametrize('value', ['true', '1', 'TRUE', 'True', ' true ', '\t1\n'])
def test_suppression_skips_network_and_metadata(monkeypatch, value):
    """Explicit suppression avoids even metadata access and all output."""
    monkeypatch.setenv(const.ENV_SUPPRESS_UPDATE_NOTICE, value)

    def forbidden(*args, **kwargs):
        pytest.fail('Suppressed notices must not inspect metadata or request PyPI')

    monkeypatch.setattr(updates, '_fetch_releases', forbidden)
    monkeypatch.setattr(updates, 'version', forbidden)
    assert updates._notice() is None


@pytest.mark.parametrize('value', ['', 'false', '0', 'yes', '2'])
def test_other_environment_values_leave_check_enabled(enabled, monkeypatch, value):
    """Only the documented true/1 values suppress checks."""
    monkeypatch.setenv(const.ENV_SUPPRESS_UPDATE_NOTICE, value)
    assert '(v1.1.0)' in updates._notice()


@pytest.mark.parametrize(
    ('installed', 'available', 'notify'),
    [
        ('1.0.0', '1.1.0', True),
        ('1.9.0', '1.10.0', True),
        ('1.0.0.dev0', '1.0.0', True),
        ('1.1.0rc1', '1.1.0', True),
        ('1.0.0', '1.0.0.post1', True),
        ('1.0.0', '1!1.0.0', True),
        ('1.1', '1.1.0', False),
        ('1.2.0', '1.1.0', False),
        ('2.0.0.dev0', '1.1.0', False),
        ('1.1.0+local', '1.1.0', False),
    ],
)
def test_pep440_comparison(enabled, monkeypatch, installed, available, notify):
    """Use semantic PEP 440 ordering, including development and post releases."""
    monkeypatch.setattr(updates, 'version', lambda name: installed)
    monkeypatch.setattr(updates, '_fetch_releases', lambda: {'releases': {available: [{'yanked': False}]}})
    notice = updates._notice()
    if notify:
        assert notice == (
            f'A newer version of obfuscidian (v{available}) is available. '
            f'Visit {const.UPDATE_INSTRUCTIONS_URL} for update instructions.'
        )
    else:
        assert notice is None


def test_choose_stable_uploaded_non_yanked_release():
    """Ignore pre/dev/local, yanked/deleted, malformed and unsafe version records."""
    payload = {
        'info': {'version': '99.0rc1'},
        'releases': {
            '1.9.0': [{'yanked': False}],
            'v1.10.0': [{'yanked': True}, {'yanked': False}],
            '99.0rc1': [{'yanked': False}],
            '99.0a1': [{'yanked': False}],
            '99.0b1': [{'yanked': False}],
            '99.0.dev1': [{'yanked': False}],
            '99.0+local': [{'yanked': False}],
            '99.0': [{'yanked': True}],
            '98.0': [],
            '97.0': [{'yanked': 'false'}],
            '96.0': [{'yanked': 0}],
            '95.0': [{}],
            '94.0': None,
            '93.0': [None],
            'invalid\x1b\nSYNTHETIC_PRIVATE_VALUE': [{'yanked': False}],
            '9' * (const.UPDATE_VERSION_LENGTH + 1): [{'yanked': False}],
            92: [{'yanked': False}],
        },
    }
    assert str(updates._latest_stable(payload)) == '1.10.0'


@pytest.mark.parametrize('payload', [None, [], {}, {'releases': None}, {'releases': []}])
def test_bad_api_schema_fails_silently(enabled, monkeypatch, payload):
    """An unavailable or malformed check cannot claim an update or break a command."""
    monkeypatch.setattr(updates, '_fetch_releases', lambda: payload)
    assert updates._notice() is None


@pytest.mark.parametrize('payload', [{'releases': {}}, {'releases': {'2.0rc1': [{'yanked': False}]}}])
def test_no_stable_release_has_no_notice(enabled, monkeypatch, payload):
    monkeypatch.setattr(updates, '_fetch_releases', lambda: payload)
    assert updates._notice() is None


@pytest.mark.parametrize('error', [OSError, urllib3.exceptions.HTTPError, ValueError, MemoryError, PackageNotFoundError])
def test_failed_check_preserves_help_and_privacy(enabled, monkeypatch, error):
    def failed():
        raise error('SYNTHETIC_PRIVATE_NETWORK_DETAIL')

    monkeypatch.setattr(updates, '_fetch_releases', failed)
    result = CliRunner().invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert result.stderr == ''
    assert 'SYNTHETIC_PRIVATE_NETWORK_DETAIL' not in result.output


def test_invalid_installed_version_skips_network(enabled, monkeypatch):
    monkeypatch.setattr(updates, 'version', lambda name: 'invalid-private-value')
    monkeypatch.setattr(updates, '_fetch_releases', lambda: pytest.fail('Invalid metadata must skip the request'))
    assert updates._notice() is None


@pytest.fixture
def fake_pool(monkeypatch):
    """Capture the HTTPS request and response cleanup without any network access."""

    class Response:
        status = 200
        body = b'{"releases": {}}'
        closed = False
        reads = []

        def read(self, size, **kwargs):
            self.reads.append((size, kwargs))
            return self.body[:size]

        def close(self):
            self.closed = True

    class Pool:
        def __init__(self, **kwargs):
            self.options = kwargs
            self.response = Response()
            self.cleared = False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.cleared = True

        def request(self, *args, **kwargs):
            self.request_args = args
            self.request_options = kwargs
            return self.response

    pool = Pool(cert_reqs='CERT_REQUIRED')
    monkeypatch.setattr(urllib3, 'PoolManager', lambda **kwargs: setattr(pool, 'options', kwargs) or pool)
    return pool


def test_request_is_private_bounded_and_verified(fake_pool):
    assert updates._fetch_releases() == {'releases': {}}
    assert fake_pool.options == {'cert_reqs': 'CERT_REQUIRED'}
    assert fake_pool.request_args == ('GET', const.UPDATE_API_URL)
    options = fake_pool.request_options
    assert options['retries'] is False and options['redirect'] is False and options['preload_content'] is False
    assert options['headers'] == {'Accept': 'application/json', 'Accept-Encoding': 'identity'}
    assert options['timeout'].connect_timeout == const.UPDATE_CONNECT_TIMEOUT
    assert options['timeout'].read_timeout == const.UPDATE_READ_TIMEOUT
    assert fake_pool.response.reads == [(const.UPDATE_RESPONSE_BYTES + 1, {'decode_content': False})]
    assert fake_pool.response.closed and fake_pool.cleared


@pytest.mark.parametrize('status', [301, 404, 429, 500])
def test_http_errors_close_without_reading(fake_pool, status):
    fake_pool.response.status = status
    with pytest.raises(ValueError):
        updates._fetch_releases()
    assert fake_pool.response.reads == []
    assert fake_pool.response.closed and fake_pool.cleared


@pytest.mark.parametrize('body', [b'not JSON', b'\xff', b'{}' + b' ' * const.UPDATE_RESPONSE_BYTES])
def test_bad_or_oversized_json_closes_response(fake_pool, body):
    fake_pool.response.body = body
    with pytest.raises((ValueError, UnicodeError)):
        updates._fetch_releases()
    assert fake_pool.response.closed and fake_pool.cleared


def test_exact_response_limit_is_accepted(fake_pool):
    body = json.dumps({'releases': {}}).encode()
    fake_pool.response.body = body + b' ' * (const.UPDATE_RESPONSE_BYTES - len(body))
    assert updates._fetch_releases() == {'releases': {}}
    assert fake_pool.response.closed and fake_pool.cleared


def test_read_failure_closes_response(fake_pool, monkeypatch):
    def failed(*args, **kwargs):
        raise urllib3.exceptions.ReadTimeoutError(None, None, 'synthetic')

    monkeypatch.setattr(fake_pool.response, 'read', failed)
    with pytest.raises(urllib3.exceptions.ReadTimeoutError):
        updates._fetch_releases()
    assert fake_pool.response.closed and fake_pool.cleared


@pytest.mark.parametrize('error', [urllib3.exceptions.SSLError, urllib3.exceptions.NewConnectionError])
def test_tls_or_connection_failure_clears_pool(fake_pool, monkeypatch, error):
    def failed(*args, **kwargs):
        raise error(None, 'synthetic') if error is urllib3.exceptions.NewConnectionError else error('synthetic')

    monkeypatch.setattr(fake_pool, 'request', failed)
    with pytest.raises(error):
        updates._fetch_releases()
    assert fake_pool.cleared


@pytest.mark.parametrize('arguments', [['--help'], ['--version'], ['keygen', '--help'], ['shroud', '--help'], ['verify']])
def test_notice_once_on_stderr_and_no_files(enabled, monkeypatch, tmp_path, arguments):
    calls = []

    def fetch():
        calls.append(True)
        return {'releases': {'1.1.0': [{'yanked': False}]}}

    monkeypatch.setattr(updates, '_fetch_releases', fetch)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == (2 if arguments == ['verify'] else 0)
    assert result.stderr.count('A newer version') == 1
    assert 'A newer version' not in result.stdout
    assert len(calls) == 1
    assert list(tmp_path.iterdir()) == []


def test_completion_never_checks(enabled, monkeypatch):
    monkeypatch.setattr(updates, '_fetch_releases', lambda: pytest.fail('Completion must remain offline'))
    with cli.make_context('obfuscidian', [], resilient_parsing=True) as context:
        assert context.meta['update_notice'] is None


def test_invocations_do_not_reuse_old_notice(enabled, monkeypatch):
    first = CliRunner().invoke(cli, ['--version'])
    assert 'A newer version' in first.stderr
    monkeypatch.setenv(const.ENV_SUPPRESS_UPDATE_NOTICE, '1')
    second = CliRunner().invoke(cli, ['--version'])
    assert second.stderr == ''
    assert second.stdout == first.stdout

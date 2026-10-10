# -*- coding: utf-8 -*-
"""
:Module:            tests.integration.test_update_tls
:Synopsis:          Offline update checks against synthetic loopback TLS certificates
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     10 Oct 2026
"""

from __future__ import annotations

import ipaddress
import json
import ssl
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import certifi
import pytest
import urllib3
from click.testing import CliRunner
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from obfuscidian import constants as const
from obfuscidian import updates
from obfuscidian.cli import cli


@pytest.fixture
def tls_endpoint(tmp_path, monkeypatch, request):
    """Serve only synthetic metadata on loopback; create ephemeral test-only keys."""
    for name in ('SSL_CERT_FILE', 'SSL_CERT_DIR', const.ENV_SUPPRESS_UPDATE_NOTICE):
        monkeypatch.delenv(name, raising=False)
    # Model a Python installation with no usable default CA discovery, on every OS.
    monkeypatch.setattr(ssl.SSLContext, 'load_default_certs', lambda *args, **kwargs: None)
    now = datetime.now(UTC)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Synthetic update test CA')])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    ca_file = tmp_path / 'synthetic-ca.pem'
    ca_file.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    hostname = (
        x509.DNSName('wrong.example.invalid')
        if getattr(request, 'param', None) == 'wrong-hostname'
        else x509.IPAddress(ipaddress.ip_address('127.0.0.1'))
    )
    leaf = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Synthetic update endpoint')]))
        .issuer_name(ca_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(True, False, False, False, False, False, False, False, False), critical=True)
        .add_extension(x509.SubjectAlternativeName([hostname]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    leaf_file = tmp_path / 'synthetic-server.pem'
    leaf_file.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
    key_file = tmp_path / 'synthetic-server.key'
    key_file.write_bytes(
        leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    payload = {'releases': {'99.0.0': [{'yanked': False}]}}
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(leaf_file, key_file)
    with HTTPServer(('127.0.0.1', 0), Handler) as server:
        server.socket = server_context.wrap_socket(server.socket, server_side=True)
        monkeypatch.setattr(const, 'UPDATE_API_URL', f'https://127.0.0.1:{server.server_port}/metadata')
        worker = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        worker.start()
        try:
            yield ca_file, payload, requests
        finally:
            server.shutdown()
            worker.join(timeout=5)
            assert not worker.is_alive()


def test_bundled_ca_works_without_default_roots(tls_endpoint, monkeypatch):
    """A supplied bundle authenticates HTTPS even when default trust discovery is empty."""
    ca_file, payload, requests = tls_endpoint
    # Stand in for certifi's real public-root bundle using a test-only private CA.
    monkeypatch.setattr(certifi, 'where', lambda: str(ca_file))
    assert updates._fetch_releases() == payload
    assert requests == ['/metadata']


def test_explicit_ca_file_works_without_default_roots(tls_endpoint, monkeypatch):
    ca_file, payload, requests = tls_endpoint
    monkeypatch.setenv('SSL_CERT_FILE', str(ca_file))
    assert updates._fetch_releases() == payload
    assert requests == ['/metadata']


def test_explicit_hashed_ca_directory_works(tls_endpoint, monkeypatch, tmp_path):
    ca_file, payload, requests = tls_endpoint
    directory = tmp_path / 'synthetic-hashed-ca-directory'
    directory.mkdir()
    # OpenSSL subject hash of the fixed synthetic CA name above. A regular copy
    # works on Windows too, without symlinks or an openssl executable dependency.
    (directory / 'd42bc0ff.0').write_bytes(ca_file.read_bytes())
    monkeypatch.setenv('SSL_CERT_DIR', str(directory))
    assert updates._fetch_releases() == payload
    assert requests == ['/metadata']


def test_combined_ca_file_and_directory_work(tls_endpoint, monkeypatch, tmp_path):
    ca_file, payload, requests = tls_endpoint
    directory = tmp_path / 'empty-synthetic-ca-directory'
    directory.mkdir()
    monkeypatch.setenv('SSL_CERT_FILE', str(ca_file))
    monkeypatch.setenv('SSL_CERT_DIR', str(directory))
    assert updates._fetch_releases() == payload
    assert requests == ['/metadata']


@pytest.mark.parametrize('setting', ['missing-file', 'invalid-file', 'empty-file-setting', 'empty-directory'])
def test_failed_custom_trust_does_not_fall_back(tls_endpoint, monkeypatch, tmp_path, setting):
    """Even an otherwise trusted endpoint cannot bypass an explicit failed override."""
    ca_file, _, requests = tls_endpoint
    monkeypatch.setattr(certifi, 'where', lambda: str(ca_file))
    custom = tmp_path / 'synthetic-custom-trust'
    if setting == 'invalid-file':
        custom.write_text('not a certificate')
    elif setting == 'empty-directory':
        custom.mkdir()
    if setting == 'empty-directory':
        monkeypatch.setenv('SSL_CERT_DIR', str(custom))
    else:
        monkeypatch.setenv('SSL_CERT_FILE', '' if setting == 'empty-file-setting' else str(custom))
    assert updates._notice() is None
    assert requests == []


def test_untrusted_certificate_is_rejected(tls_endpoint):
    """The packaged public roots must not trust the ephemeral synthetic test CA."""
    _, _, requests = tls_endpoint
    with pytest.raises(urllib3.exceptions.SSLError):
        updates._fetch_releases()
    assert requests == []
    assert updates._notice() is None
    assert requests == []


@pytest.mark.parametrize('tls_endpoint', ['wrong-hostname'], indirect=True)
def test_wrong_hostname_is_rejected(tls_endpoint, monkeypatch):
    ca_file, _, requests = tls_endpoint
    monkeypatch.setenv('SSL_CERT_FILE', str(ca_file))
    with pytest.raises(urllib3.exceptions.SSLError):
        updates._fetch_releases()
    assert requests == []
    assert updates._notice() is None
    assert requests == []


@pytest.mark.parametrize('arguments', [['--help'], ['--version'], ['keygen', '--help'], ['verify']])
def test_verified_notice_preserves_command_behavior(tls_endpoint, monkeypatch, arguments):
    ca_file, _, requests = tls_endpoint
    monkeypatch.setenv('SSL_CERT_FILE', str(ca_file))
    result = CliRunner().invoke(cli, arguments)
    assert result.exit_code == (2 if arguments == ['verify'] else 0)
    if arguments == ['verify']:
        assert result.stderr.count('A newer version') == 1
    else:
        assert result.stderr == (
            'A newer version of obfuscidian (v99.0.0) is available. '
            f'Visit {const.UPDATE_INSTRUCTIONS_URL} for update instructions.\n'
        )
    assert 'A newer version' not in result.stdout
    assert requests == ['/metadata']

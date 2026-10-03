# Obfuscidian

[![Tests](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml/badge.svg)](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jeffshurtliff/obfuscidian/blob/main/LICENSE)

Obfuscidian is a Python CLI being developed to create encrypted Obsidian vault
backups. The current foundation provides help and version information only.
Key generation, backup, restore, and verification are planned and unavailable.
This repository does not yet claim a published package or completed platform validation.

## Project status

Thread 01 — Project foundation — is complete, reviewed, and merged into
`origin/main`; [issue #1](https://github.com/jeffshurtliff/obfuscidian/issues/1)
is closed. The foundation includes Poetry/src packaging, developer tooling,
help/version entry points, installation tests, and Linux CI configuration.

Thread 02 — Configuration and keys — is next and has not started. Follow the
[approved roadmap](dev/IMPLEMENTATION_PLAN.md#thread-02--configuration-and-keys)
for its scope; key generation and vault operations remain unavailable.

## Installation from source

Python 3.12 or newer is required. From a checkout, install with pip in a virtual
environment (activate it using the command appropriate for your shell):

```sh
python -m venv .venv
python -m pip install .
```

## Usage

```sh
obfuscidian --help
obfuscidian --version
python -m obfuscidian --help
python -m obfuscidian --version
```

Both entry points offer the same CLI behavior. No vault operations are available yet.

## Development

Use Poetry 2.2 or newer, below 3.0. Runtime dependencies are declared in
`pyproject.toml`; developer tools use its `dev` group, and `poetry.lock` records
resolved dependencies. cryptography is included for the approved Fernet design;
no encryption behavior is implemented in this foundation.

```sh
poetry install --with dev
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run coverage run -m pytest -q
poetry run coverage report
poetry run bandit -r src/obfuscidian
poetry build
```

The normal suite is offline. It builds artifacts from a temporary synthetic
source copy, checks their contents, and installs each outside the checkout with
already available dependencies. Fully isolated installation validation uses
fresh artifacts and a dependency wheelhouse; see the
[contributor guide](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md#fresh-artifact-validation).
Linux CI runs the foundation checks on Python 3.12–3.14. Broader OS hardening
belongs to Thread 12; Sphinx documentation tooling belongs to Thread 13.

See the [changelog](docs/CHANGELOG.md),
[contributor guide](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md), and
[approved roadmap](https://github.com/jeffshurtliff/obfuscidian/blob/main/dev/IMPLEMENTATION_PLAN.md).

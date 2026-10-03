# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Secure `keygen` with CLI/environment resolution, terminal-only alias prompts, non-interactive operation, and read-only dry runs.
- Exclusive mode-0600 POSIX key creation and protected owner-only Windows DACL creation on ACL-capable volumes.
- Internal configuration/key-loading helpers with selector conflicts, full bounded Fernet key validation, and permission warnings.
- Synthetic precedence, alias, prompt/EOF, collision, permission, failure-cleanup, concurrent-process, and installed-keygen tests.
- Key custody, path resolution, output privacy, and platform-limit documentation.

- Reproducible Poetry developer tooling with pytest, coverage, Ruff, Bandit, and Twine.
- Offline package-content and installation tests, with an option for fully isolated wheelhouse installs.
- Linux CI for Python 3.12, 3.13, and 3.14, including fresh wheel/sdist validation.

### Changed

- Clarified that docstring version history starts after 1.0.0, with one bare initial-release directive on public CLI callables.
- Migrated packaging to Poetry/poetry-core and `src/obfuscidian/`, retaining version `1.0.0.dev0` and both CLI entry points.
- Raised the minimum Python version to 3.12.
- Made `pyproject.toml` authoritative for Click and cryptography dependencies, with a Poetry-generated lockfile.
- Identified Obfuscidian consistently in version output; help now exposes keygen and keeps vault operations marked planned.

### Removed

- The template `command` subcommand and manually maintained `requirements.txt`.

[Unreleased]: https://github.com/jeffshurtliff/obfuscidian/compare/main...HEAD

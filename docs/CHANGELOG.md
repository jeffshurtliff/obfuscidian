# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Reproducible Poetry developer tooling with pytest, coverage, Ruff, Bandit, and Twine.
- Offline package-content and installation tests, with an option for fully isolated wheelhouse installs.
- Linux CI for Python 3.12, 3.13, and 3.14, including fresh wheel/sdist validation.

### Changed

- Migrated packaging to Poetry/poetry-core and `src/obfuscidian/`, retaining version `1.0.0.dev0` and both CLI entry points.
- Raised the minimum Python version to 3.12.
- Made `pyproject.toml` authoritative for Click and cryptography dependencies, with a Poetry-generated lockfile.
- Identified Obfuscidian consistently in version output and described the current help/version-only foundation.

### Removed

- The template `command` subcommand and manually maintained `requirements.txt`.

[Unreleased]: https://github.com/jeffshurtliff/obfuscidian/compare/main...HEAD

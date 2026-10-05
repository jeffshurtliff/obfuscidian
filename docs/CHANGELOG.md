# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- End-to-end `shroud fresh` with CLI/environment selection, complete read-only preflight and selected-key mirror authentication.
- Current-inventory encrypted snapshots, validated ciphertext reuse, stale removal, and retained external encrypted rollback.
- Replacement/recovery consent, artifact-free no-op/dry-run behavior, explicit recovery/retry, and escaped private handoff output.
- Mixed-vault, source-change, wrong-key/corruption, safety/resource, failure, process-death and installed-entry fresh-backup tests.
- Fresh backup guide and synchronized help/roadmap/status; merge backup, restore and verification commands remain planned.

- Internal private same-filesystem staging, exclusive POSIX ownership, durable bounded journal, and checked payload publication.
- Retained fresh rollback outside Git worktrees, protected Git/settings controls, and conservative explicit recovery with shared consent.
- Synthetic mutation-boundary, process-death, competing-writer, interrupted recovery, privacy, and user-change preservation tests.
- Transaction integration and durability/platform-limit documentation, initially without public vault write commands.

- Internal frozen v1 UTF-8 manifest schema, canonical serialization, secure opaque IDs, and bounded standard Fernet byte codecs.
- Complete read-only mirror authentication with encrypted hash/size binding, safe token reads, state rechecks, and validated reuse.
- Immutable synthetic compatibility artifacts and adversarial substitution, hostile JSON/path, size, race, and preservation tests.
- V1 format, key custody, target constraints, and threat-limit documentation, initially without vault commands.

- Internal deterministic read-only vault inventory with binary/hidden/config/empty-directory inclusion and typed identity records.
- Mandatory exclusions and portable case-sensitive component globs with pruning and encountered-entry totals.
- Read-only path/target safety, selected-key custody, mirror namespace checks, stable binary reads, and final inventory comparison.
- Exact bounded Fernet estimates, actual-manifest accounting hooks, and staging/rollback payload/free-space checks.
- Synthetic preservation, exclusion, permission, unsafe-path, size-boundary, and changing-source tests; internal inventory documentation.

- Secure `keygen` with CLI/environment resolution, terminal-only alias prompts, non-interactive operation, and read-only dry runs.
- Exclusive mode-0600 POSIX key creation and protected owner-only Windows DACL creation on ACL-capable volumes.
- Internal configuration/key-loading helpers with selector conflicts, full bounded Fernet key validation, and permission warnings.
- Synthetic precedence, alias, prompt/EOF, collision, permission, failure-cleanup, concurrent-process, and installed-keygen tests.
- Key custody, path resolution, output privacy, and platform-limit documentation.

- Reproducible Poetry developer tooling with pytest, coverage, Ruff, Bandit, and Twine.
- Offline package-content and installation tests, with an option for fully isolated wheelhouse installs.
- Linux CI for Python 3.12, 3.13, and 3.14, including fresh wheel/sdist validation.

### Changed

- Added a final source prepublication callback and selected-key authentication before mirror recovery inverse moves.
- Clarified that docstring version history starts after 1.0.0, with one bare initial-release directive on public CLI callables.
- Migrated packaging to Poetry/poetry-core and `src/obfuscidian/`, retaining version `1.0.0.dev0` and both CLI entry points.
- Raised the minimum Python version to 3.12.
- Made `pyproject.toml` authoritative for Click and cryptography dependencies, with a Poetry-generated lockfile.
- Identified Obfuscidian consistently in version output; help now exposes keygen and keeps vault operations marked planned.

### Removed

- The template `command` subcommand and manually maintained `requirements.txt`.

[Unreleased]: https://github.com/jeffshurtliff/obfuscidian/compare/main...HEAD

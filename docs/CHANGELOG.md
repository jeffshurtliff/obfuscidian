# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Thread 13 documentation accepted by the maintainer and completed on `main` at
  `c4bda3c`, with passing nine-job Linux/macOS/Windows CI on Python 3.12–3.14;
  issue #13 closed as completed. Documentation hosting/publication remains separate.

- Reorganized Getting Started into nine beginner topics with short examples and
  task cards; moved detailed installation and restore rehearsal into User Guides.
- Removed development-thread references from Sphinx pages except this changelog,
  and updated documentation links, source-package includes and artifact validation.

### Added

- Locked `sphinx-favicon` documentation dependency and extension activation for
  the configured browser and Apple touch icons, including Read the Docs builds.

- Read the Docs v2 configuration using Ubuntu 24.04, Python 3.12 and the locked Poetry docs group,
  with HTML builds that fail on Sphinx warnings; no duplicate requirements list or publication.

- Thread 13 optional locked Sphinx/reST/MyST documentation with the PyData theme, dark default,
  proportional web logo, violet/cyan accents and reader-selectable light mode.
- Installation/CLI navigation, an executable synthetic backup/verify/restore tutorial, security policy,
  threat-model/troubleshooting/cleanup guides and contributor/documentation maintenance guidance.
- Exact tutorial integration rehearsal and offline rendered HTML link/asset/fragment checks.

- Thread 12 nine-job Linux/macOS/Windows CI for Python 3.12–3.14, portable fresh-artifact validation and retained test/coverage evidence.
- Focused native/platform path, Git preflight, no-op, resource, descriptor failure, termination and recovery coverage.
- Platform validation guide distinguishing local results, hosted CI and intentional Windows write/append refusal.
- Thread 12 completed after maintainer review/merge and a passing nine-job Linux/macOS/Windows Python 3.12–3.14 matrix.

- Thread 11 shared CLI contract: static phase progress, private JSON lines logs, and independent terminal/log path disclosure.
- Optional `--log-file`/`--log-paths` on write commands with custody, permissions, link and identity validation before mutation.
- Privacy/UX tests for streams, logs, malformed arguments, control-character names, no-ops, recovery and exit categories.
- Installed console/module command/help/error/logging parity and shared CLI guidance; Thread 11 reviewed/merged,
  with green Linux CI and issue #11 completed.

- `unshroud merge` with clean-origin (including ignored data), local base/ref, Git-directory and new-output validation.
- Private authenticated additive reconstruction before isolated branch/worktree creation; restored differences remain uncommitted.
- Raw base-blob reconstruction, hook/filter/config isolation, protected Git controls and optional base-settings preservation.
- Ignored-file/manual review guidance, no-write dry runs and conservative cleanup that preserves user edits and uncertain artifacts.
- Offline temporary-repository round trips, ref/path/corruption/dirty-state checks, fault/interrupt and cleanup-preservation tests.
- Extended restore guide and roadmap evidence for completed Thread 10; later threads remain not started.

- `unshroud fresh` with complete mirror authentication and conservative target checks before private plaintext staging.
- Exact binary/hidden/empty-directory reconstruction, supported times, protected Git controls and optional settings preservation.
- Journaled fresh publication with sensitive external plaintext rollback, consent, no-write dry run and verified-source recovery/retry.
- Synthetic round-trip, corruption, safety, source/stage-change, fault, interrupt and process-death tests plus installed entry checks.
- Fresh restore guide, subsequently extended by Thread 10 with Git merge restore.

- Read-only `verify` with mirror/key resolution, complete v1 manifest/object validation, counts and escaped opt-in relative names.
- Pending-ownership inspection without recovery and rejection of write, exclusion, recovery, restore and logging options.
- Synthetic corrupt/valid/privacy/no-write verification tests, installed console/module parity, and verification documentation.

- Additive `shroud merge` with old/current union, stale/excluded file and directory retention, and new-path rename semantics.
- Stable object IDs and exact ciphertext reuse, metadata-only updates, content-only consent and artifact-free merge no-ops.
- Early type-conflict refusal with fresh-mode guidance; authenticated retained-byte reads prove historic content remains reconstructible.
- Synthetic incremental, corruption, conflict, preservation, cleanup, source-change, failure and process-recovery tests.
- Merge help/guide explaining that deleted notes can return during restore; later commands remain unavailable.

- End-to-end `shroud fresh` with CLI/environment selection, complete read-only preflight and selected-key mirror authentication.
- Current-inventory encrypted snapshots, validated ciphertext reuse, stale removal, and retained external encrypted rollback.
- Replacement/recovery consent, artifact-free no-op/dry-run behavior, explicit recovery/retry, and escaped private handoff output.
- Mixed-vault, source-change, wrong-key/corruption, safety/resource, failure, process-death and installed-entry fresh-backup tests.
- Fresh backup guide and synchronized help/roadmap/status, initially without merge, restore or verification commands.

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

### Fixed

- Stale planned-command wording and README installation/platform claims; synchronized current user and contributor guidance.

- Open-file replacement tests accept safe directory-guard sharing refusal, verify descriptor cleanup and preserve source bytes.
- Same-size changed-source fixtures set a distinct modification time explicitly, avoiding timing-dependent Windows failures.
- Windows source/token reads and transaction hashing compare creation time across APIs while retaining raw descriptor change checks.
- Case-alias overlap tests accept the earlier Windows lexical overlap refusal without changing production path validation.
- Inventory and mirror traversal use full no-follow entry metadata, preventing false Windows identity-change errors.
- Interactive keygen tests match escaped Windows paths without relaxing output privacy.
- Repository text checks out with LF on Windows as required by Ruff; compatibility fixtures retain exact bytes.
- Read-only destination capture uses absolute binary reads when directory handles are unavailable.
- Source/key/staging/Git copy stream allocation failures release opened descriptors; key-load memory failures remain redacted.
- All Windows private-file creators require persistent ACL capability, including new operational logs before mutation.

### Changed

- Redacted parser misuse and unexpected exception payloads while preserving useful help and exit-code categories.
- Dry runs reject explicit logging and verification remains read-only; verbose handoff locations never enter operational logs.

- Shared fresh/merge planning, staging and recovery reuse the existing v1 validators and transaction primitives.
- Successful merge cleans only its own proven temporary recovery workspace; uncertain data stays retained with a warning.

- Added a final source prepublication callback and selected-key authentication before mirror recovery inverse moves.
- Clarified that docstring version history starts after 1.0.0, with one bare initial-release directive on public CLI callables.
- Migrated packaging to Poetry/poetry-core and `src/obfuscidian/`, retaining version `1.0.0.dev0` and both CLI entry points.
- Raised the minimum Python version to 3.12.
- Made `pyproject.toml` authoritative for Click and cryptography dependencies, with a Poetry-generated lockfile.
- Identified Obfuscidian consistently in version output; help now exposes keygen and keeps vault operations marked planned.

### Removed

- The template `command` subcommand and manually maintained `requirements.txt`.

[Unreleased]: https://github.com/jeffshurtliff/obfuscidian/compare/main...HEAD

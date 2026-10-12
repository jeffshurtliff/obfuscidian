# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Package versions and encrypted backup-format versions are separate contracts.

## [Unreleased]

### Added

- Python 3.14 Windows lifecycle validation wrapper for #27, reusing the shared
  interpreter, safety and diagnostic checks with a separate default report
  directory. Native execution remains pending.

- Private Windows copy-based transaction, fresh/merge backup, fresh restore and
  explicit recovery candidate for [#27](https://github.com/jeffshurtliff/obfuscidian/issues/27),
  with bounded ownership/checkpoint binding, independently verified saved and
  inverse copies, copy-inclusive estimates and synthetic lifecycle/termination
  fixtures. Production Windows CLI mutation/recovery and existing-log append
  remain refused; actual native lifecycle execution and qualification are pending.

- Maintainer safety design and staged implementation plan for native Windows
  backup, restore and recovery in 2.0.0 (issue
  [#17](https://github.com/jeffshurtliff/obfuscidian/issues/17)). Windows write
  support remains planned pending implementation and native validation.

- Internal Windows safety primitives and synthetic native qualification tests
  (issue [#26](https://github.com/jeffshurtliff/obfuscidian/issues/26)): explicit
  private DACLs, guarded handles/full identities, bounded I/O, lifetime ownership,
  no-clobber rename, checked disposition and timestamps, with bounded immutable
  checkpoint generations that retain earlier records. Native qualification
  retains an outstanding real ownership-transition proof; CLI mutation gates
  and existing-log append refusal remain in place. Added a maintainer Windows qualification procedure and interruption
  fixtures without starting transaction integration.

- Supplementary owner-validation tests for #26 using injected metadata and a
  Windows-created in-memory descriptor, with distinct evidence properties and
  unchanged filesystem owner/ACL checks. The mandatory real owner-transition
  test remains intact; these supplements do not establish that native proof.

### Changed

- Accepted the #26 implementation handoff with the maintainer-approved limited
  real ownership-transition proof deferral to #29. Internal #27 development may
  proceed with Windows CLI mutation/recovery gates retained; the proof remains
  mandatory before write enabling or qualified 2.0.0 Windows support claims.

- Windows primitive qualification guidance includes Microsoft Store Python
  selection without a required `py` launcher, explicit interpreter checks and
  script-file execution. Recorded r3 native diagnostic evidence retains the
  outstanding real ownership-transition proof and CLI mutation gates (#26).

### Fixed

- Windows lifecycle validation installs locked runtime/development requirements
  without the unused optional Sphinx group, keeping documentation installation
  failures separate from native pytest diagnostics. Documentation-build
  qualification remains a separate check (#27).

- Windows lifecycle interpreter validation executes its multiline probe as a
  file, avoiding Windows shell handling of multiline `poetry run python -c`
  arguments. Missing/invalid metadata is refused before patch comparison; genuine
  mismatches report both versions. Native verification remains pending (#27).

- Python 3.14 qualification wrapper loads its shared helper as a script block
  when invoked from source text, preserving repository discovery and validation
  without a nested `.ps1` invocation or execution-policy setting changes (#27).

- Revised internal Windows acquisition/publication to use retained native root
  handles after the first qualification run exposed insufficient pathname
  guarding. Added numeric native diagnostics and conversion-race fixtures;
  corrected unsafe-ACL preservation and CLI-gate test expectations. Revised
  native cases passed on the supplied host, while required real ownership proof
  remains outstanding before Windows write enabling; its deadline is deferred
  to #29 under the approved gated development handoff (issue #26).

- PyPI update checks use a runtime CA bundle when default Python certificate
  discovery is unavailable (issue [#24](https://github.com/jeffshurtliff/obfuscidian/issues/24)).
  Explicit `SSL_CERT_FILE`/`SSL_CERT_DIR` settings replace bundled trust;
  certificate and hostname verification remain required, and failed checks
  continue to skip the notice silently.

### Removed

### Security

## [1.0.1] - 2026-10-10

Maintenance release with packaging checks, release-workflow hardening and
updated documentation presentation. CLI behavior, runtime dependencies,
supported platforms and encrypted backup-format v1 are unchanged.

### Added

- Social preview image assets for the documentation.

### Changed

- Package metadata now links to stable documentation, the source repository and
  the rendered changelog; the README includes a PyPI version badge.
- Documentation uses a custom copyright footer with adjusted alignment.

### Fixed

- Packaging checks now derive expected artifact metadata, archive paths and CLI
  version output from `pyproject.toml`, allowing development and release version
  changes without stale version assertions failing CI.

### Security

- Denied GitHub Actions cache reads and writes throughout the guarded release
  workflow, including reusable tests, to mitigate the cache-poisoning risk
  reported in code-scanning alerts #1–3 (issue [#22](https://github.com/jeffshurtliff/obfuscidian/issues/22)).

## [1.0.0] - 2026-10-08

First stable release of the Obfuscidian CLI for individually encrypted Obsidian
vault backups. Requires Python 3.12+; CI covers Python 3.12–3.14 on Linux, macOS
and Windows. Backup-format v1 uses standard whole-file Fernet encryption with
an encrypted manifest and a 50 MiB cap per encrypted object or manifest.

### Added

- Exclusive private key creation, CLI/environment key selection and external key
  custody. Keys are never overwritten, printed or automatically regenerated.
- Fresh and additive merge backups with exact note/attachment byte preservation,
  empty directories, exclusions, resource checks and unchanged-backup no-ops.
  Additive backups retain deleted, renamed and excluded historical entries.
- Complete read-only verification of authenticated manifests and every required
  object, with namespace, path, size and metadata validation.
- Fresh restore with explicit replacement consent, rollback retention and optional
  settings preservation; additive Git restore into a separate branch/worktree
  with restored changes left uncommitted for manual review.
- Dry-run previews, non-interactive operation, explicit recovery, consistent exit
  codes, redacted output and optional private operational logs.
- Best-effort stable-version notices from PyPI and opt-out through
  `OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE`. Checks never install updates or write a cache.
- Sphinx documentation, beginner task guides, a synthetic restore rehearsal,
  pipx/pip installation and update instructions, scheduling examples, security
  reporting guidance and a maintainer release runbook.

### Changed

- Poetry/poetry-core packaging with a `src/` layout, locked development/docs tools,
  stable metadata and both console and `python -m obfuscidian` entry points.
- Release delivery uses fresh inspected artifacts and manual Twine uploads by
  default. GitHub release creation/publication does not initiate a PyPI upload.

### Fixed

- Cross-platform filesystem identity checks, portable artifact validation,
  Windows timestamp comparisons, descriptor cleanup and documentation navigation.

### Removed

- The template subcommand and duplicate runtime requirements file.

### Security

- Authenticated validation precedes destination mutation; unsafe overlap,
  traversal, links/junctions, special files and target name collisions are refused.
- Source identity/content rechecks, private staging, journaled publication and
  conservative recovery retain uncertain data rather than silently discarding it.
- Source vaults remain read-only during backup. Git metadata and original Git
  branches remain protected; Obfuscidian never commits, merges or pushes vault data.
- Linux/macOS support vault writes. Native Windows supports protected key creation,
  verification and read-only planning; vault mutation/recovery and existing-log
  append fail closed. Filesystem observations are best effort, not atomic
  snapshots or universal power-loss guarantees. Restore rollback contains
  sensitive plaintext and needs deliberate custody and cleanup.

[Unreleased]: https://github.com/jeffshurtliff/obfuscidian/compare/1.0.1...HEAD
[1.0.1]: https://github.com/jeffshurtliff/obfuscidian/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/jeffshurtliff/obfuscidian/releases/tag/1.0.0

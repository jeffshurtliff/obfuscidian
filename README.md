# Obfuscidian

[![Tests](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml/badge.svg)](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jeffshurtliff/obfuscidian/blob/main/LICENSE)

Obfuscidian is a Python CLI being developed to create encrypted Obsidian vault
backups. The current CLI provides help, version information, secure key
generation, `shroud fresh|merge`, read-only `verify`, and `unshroud fresh|merge`.
Git merge restore is available; optional logging remains planned and unavailable.
This repository does not yet claim a published package or completed platform validation.

## Project status

Thread 01 — Project foundation — is complete, reviewed, and merged into
`origin/main`; [issue #1](https://github.com/jeffshurtliff/obfuscidian/issues/1)
is closed. The foundation includes Poetry/src packaging, developer tooling,
help/version entry points, installation tests, and Linux CI configuration.

Thread 02 — Configuration and keys — is complete, reviewed, and merged into
`origin/main`; [issue #2](https://github.com/jeffshurtliff/obfuscidian/issues/2)
is closed. It adds configuration resolution, secure `keygen`, and internal key
loading. Linux CI passed on Python 3.12–3.14 for the merged implementation.

Thread 03 — Vault inventory and path preflight — is complete, reviewed, and
merged into `origin/main`; [issue #3](https://github.com/jeffshurtliff/obfuscidian/issues/3)
is closed. It adds internal read-only inventory, exclusion/path checks, stable
binary reads, and resource estimates. Linux CI passed on Python 3.12–3.14. See
the [inventory/preflight guide](docs/INVENTORY.md) and the
[approved roadmap](dev/IMPLEMENTATION_PLAN.md#thread-03--vault-inventory-and-path-preflight)
for its scope and validation evidence.

Thread 04 — Encrypted backup format — is complete, reviewed, and merged into
`origin/main`; [issue #4](https://github.com/jeffshurtliff/obfuscidian/issues/4)
is closed. It adds internal v1 codecs, complete read-only validation, and
synthetic compatibility fixtures; see [the format guide](docs/FORMAT.md).
Linux CI passed on Python 3.12–3.14 for Thread 04.

Thread 05 — Safe publication and recovery — is complete, reviewed, and
merged/pushed into `origin/main`; [issue #5](https://github.com/jeffshurtliff/obfuscidian/issues/5)
is closed. Linux CI passed on Python 3.12–3.14. See the
[transaction guide](docs/TRANSACTIONS.md) and
[roadmap completion record](dev/IMPLEMENTATION_PLAN.md#tracking-and-handoff-record)
for retained rollback, conservative recovery, validation, and platform limits.

Thread 06 — Fresh backup — is complete, reviewed, and merged/pushed into
`origin/main`; [issue #6](https://github.com/jeffshurtliff/obfuscidian/issues/6)
is closed. Linux CI passed on Python 3.12–3.14; see the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-06--fresh-backup-completion-record-5-october-2026).
See the [fresh backup guide](docs/BACKUP.md) for preservation, consent, no-op,
dry-run and recovery behavior. 

Thread 07 — Merge backup — is complete, reviewed, and merged/pushed into
`origin/main`; [issue #7](https://github.com/jeffshurtliff/obfuscidian/issues/7)
is closed. Linux CI passed on Python 3.12–3.14; see the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-07--merge-backup-completion-record-5-october-2026).

Thread 08 — Read-only verification — is complete, reviewed, and merged/pushed
into `origin/main`; [issue #8](https://github.com/jeffshurtliff/obfuscidian/issues/8)
is closed as completed. Linux CI passed on Python 3.12–3.14; see the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-08--read-only-verification-completion-record-5-october-2026).
See [verification](docs/VERIFY.md) for behavior and limits.

Thread 09 — Fresh restore — is complete, reviewed and merged/pushed into
`origin/main`; [issue #9](https://github.com/jeffshurtliff/obfuscidian/issues/9)
is closed as completed. Linux CI passed on Python 3.12/3.13. Python 3.14 was
canceled before execution due to hosted runner availability; the maintainer
accepted that validation gap for closure. See [fresh restore](docs/RESTORE.md)
and the [completion record](dev/IMPLEMENTATION_PLAN.md#thread-09--fresh-restore-completion-record-5-october-2026).

Thread 10 — Git merge restore — is complete, reviewed and merged/pushed into
`origin/main`; [issue #10](https://github.com/jeffshurtliff/obfuscidian/issues/10)
is closed as completed. Linux CI passed on Python 3.12–3.14. See
[merge restore](docs/RESTORE.md#additive-git-merge-restore) and the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-10--git-merge-restore-completion-record-5-october-2026).

Thread 11 remains **not started**. Broader OS validation is deferred to Thread 12;
native Windows mutation fails closed.

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

Both entry points offer the same CLI behavior.
Use an existing private key directory outside both vaults and cloud repositories:

```sh
obfuscidian keygen --alias primary --dir ./keys --non-interactive --dry-run
obfuscidian keygen --alias primary --dir ./keys --non-interactive
```

Keys are created exclusively; collisions never overwrite. POSIX keys use mode
`0600`; Windows uses a protected owner-only DACL on ACL-capable volumes, with
platform validation pending. Keep a separate offline key backup. Unattended
paths are redacted unless `--verbose` is selected. See
[configuration, precedence, permissions, and custody](docs/CONFIGURATION.md).

With an existing key and vault, preview and then publish a fresh snapshot:

```sh
obfuscidian shroud fresh --help
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --dry-run
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --non-interactive --yes
```

Fresh excludes deleted or newly excluded old entries from the new snapshot,
retaining the complete old encrypted snapshot outside the mirror and Git
worktrees. Source data and root mirror Git controls stay in place. Replacing
existing contents or removing old paths requires confirmation; metadata-only
updates, additions and no-ops do not. A no-op or dry run creates no write
artifacts. Pause editing and sync during writes; see [backup safety and explicit
recovery](docs/BACKUP.md). No Git operations run automatically.

For additive retention, use `shroud merge` with the same options. It keeps
deleted, renamed and excluded old paths, so **deleted notes can return during
restore**. Existing-path edits keep their IDs; unchanged or metadata-only files
keep exact ciphertext. Only existing content replacements need consent; supply
`--yes` for unattended replacements. Merge refuses file/directory type conflicts
with guidance to use fresh. A successful merge cleans only its own proven
temporary recovery data, preserving earlier fresh rollback copies.

Verify every manifest/object without creating logs, locks or recovery artifacts:

```sh
obfuscidian verify --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --non-interactive
```

Verification never repairs or mutates a backup. Counts are shown only after
complete validation; `--verbose` permits escaped authenticated relative names.
Pending ownership requires separate recovery inspection. See [verification
selection, exit codes and limits](docs/VERIFY.md).

Fresh restore reads the encrypted mirror and replaces the plaintext origin after
complete verification. Keep the key outside both locations:

```sh
obfuscidian unshroud fresh --mirror ./encrypted-mirror --origin ./restored-vault \
  --key ./keys/obfuscidian-primary.key --non-interactive --dry-run
```

Use `--yes` for unattended replacement and `--preserve-config` to leave root
`.obsidian` in place. Root Git controls remain in place; old payload is retained
externally as **sensitive plaintext rollback**. See [fresh restore](docs/RESTORE.md)
for confirmation, recovery, metadata and filesystem limits. Additive Git merge
restore uses a separate uncommitted review worktree:

```sh
obfuscidian unshroud merge --origin ./vault --mirror ./encrypted-mirror \
  --key ./keys/obfuscidian-primary.key --base-branch main --branch review \
  --worktree ./vault-review --non-interactive --verbose
```

The origin must be clean, including ignored/untracked data. Base-only files remain;
review ignored files and commit selected changes manually before any merge. See
[merge restore](docs/RESTORE.md#additive-git-merge-restore) for validation and failure cleanup.

## Development

Use Poetry 2.2 or newer, below 3.0. Runtime dependencies are declared in
`pyproject.toml`; developer tools use its `dev` group, and `poetry.lock` records
resolved dependencies. cryptography is included for the approved Fernet design;
key creation/loading and internal v1 byte codecs use its standard Fernet recipe.
Fresh and merge backup use those codecs and existing private transaction
primitives; read-only verification uses the complete v1 validator. Restore
orchestration reuses authenticated validators and journaled publication; Git
merge restore initializes only the new worktree index to its base.

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

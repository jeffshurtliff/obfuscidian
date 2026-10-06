
<img src="docs/_static/obfuscidian-logo-horizontal-web.png" style="max-height: 160px;" alt="Obfuscidian Logo">

# Obfuscidian

[![Tests](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml/badge.svg)](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jeffshurtliff/obfuscidian/blob/main/LICENSE)

Obfuscidian is a Python CLI for encrypted Obsidian vault backups. It stores
individual Fernet-encrypted files and an encrypted path manifest in a separate
mirror, then authenticates and restores the complete snapshot. Notes and binary
attachments retain their exact bytes. The CLI is the supported public interface.

## Status and supported environments

Initial version `1.0.0.dev0` is in development; no PyPI release or hosted docs
publication is claimed. Threads 01–12 are reviewed and merged, including a
passing Linux/macOS/Windows CI matrix on Python 3.12–3.14. Linux/macOS backup and
restore writes are implemented. Native Windows supports key creation,
verification and read-only planning; vault mutation/recovery and existing-log
append still fail closed. See [platform validation](docs/PLATFORMS.md).

Thread 13 documentation is implemented locally, pending maintainer review.
Thread 14 release preparation remains not started.

## Install from source

Python 3.12+ is required. From the repository root in a POSIX shell:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
obfuscidian --help
```

For pipx, run `pipx install --python python3.12 .` from the checkout.
See [installation](docs/getting-started/installation.md) for Windows PowerShell,
local wheel and developer setup. Both `obfuscidian` and `python -m obfuscidian`
offer the same behavior.

## First backup and restore

Follow the [complete synthetic rehearsal](docs/getting-started/tutorial.md)
before using a real vault. It creates a private key outside both vaults,
previews and writes a fresh backup, verifies every object, restores to a new
location and compares all bytes and directories.

For existing synthetic locations and their external key:

```sh
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
obfuscidian verify --mirror ./mirror --key ./keys/obfuscidian-demo.key --non-interactive
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
```

The mirror must exist for verify and restore. Replace `--dry-run` with an intended
write only after review. `--non-interactive` never supplies replacement consent;
`--yes` does, without bypassing validation. Pause editing and sync during writes.

Keep a separate offline key backup: key loss prevents decryption, with no recovery
bypass. `shroud merge` retains deleted/renamed/excluded historical entries, so
those notes can return on restore. Fresh replacement retains previous payloads
outside the vault and Git; **restore rollback contains sensitive plaintext**.
Verification and dry runs create no application files or logs. Git merge restore
creates a separate review branch/worktree with differences left uncommitted;
Obfuscidian never stages, commits, merges or pushes them.

## Documentation

- [Configuration and key custody](docs/CONFIGURATION.md)
- [Fresh/additive backup](docs/BACKUP.md), [verification](docs/VERIFY.md) and [restore](docs/RESTORE.md)
- [Command reference](docs/reference/cli.md) and [output/privacy/logging](docs/CLI.md)
- [Security and limits](docs/SECURITY.md), [private reporting policy](SECURITY.md) and [troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributor guide](CONTRIBUTING.md), [changelog](docs/CHANGELOG.md) and [approved roadmap](dev/IMPLEMENTATION_PLAN.md)

Build the local Sphinx/reST/MyST site with the PyData theme (dark by default,
with a reader-selectable light mode):

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
```

Open `docs/_build/html/index.html`. See [documentation maintenance](docs/maintainers/documentation.md)
for tutorial tests, rendered/accessibility review and optional external link checks.
This build does not publish or configure hosting.

## Development

Use Poetry 2.2 or newer, below 3.0. Runtime dependencies have one authoritative
list in `pyproject.toml`; `poetry.lock` records developer and optional docs tools.
The normal pytest suite is offline and uses only synthetic temporary fixtures.

```sh
poetry install --with dev
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run bandit -r src/obfuscidian
poetry build
```

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before changing
code. Keep work within the requested thread and leave changes reviewable.
Git history and publication actions require separate maintainer authorization.
The project is licensed under [Apache-2.0](LICENSE).

---

_This utility is considered unofficial and is in no way endorsed or supported by [Obsidian](https://obsidian.md/terms)._

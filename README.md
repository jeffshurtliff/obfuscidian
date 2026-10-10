
<img src="https://raw.githubusercontent.com/jeffshurtliff/obfuscidian/1.0.1/docs/_static/obfuscidian-logo-horizontal-web.png"
     style="max-height: 160px;"
     alt="Obfuscidian Logo">

# Obfuscidian

[![PyPI Version](https://img.shields.io/pypi/v/obfuscidian)](https://pypi.org/project/obfuscidian/)
[![Tests](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml/badge.svg)](https://github.com/jeffshurtliff/obfuscidian/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jeffshurtliff/obfuscidian/blob/main/LICENSE)

Obfuscidian is a Python CLI for encrypted Obsidian vault backups. It stores
individual Fernet-encrypted files and an encrypted path manifest in a separate
mirror, then authenticates and restores the complete snapshot. Notes and binary
attachments retain their exact bytes. The CLI is the supported public interface.

## Version and supported environments

Obfuscidian 1.0.1 is a stable maintenance release and requires Python 3.12 or newer.
The tested matrix covers Linux, macOS and Windows on Python 3.12–3.14.
Linux/macOS support backup and restore writes. Native Windows supports key
creation, verification and read-only planning; vault mutation/recovery and
existing-log append fail closed. See [supported environments](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/PLATFORMS.md).

## Install

Python 3.12+ is required. For use directly from Bash, zsh or PowerShell without
activating an environment, **pipx is recommended**. With
[pipx installed](https://pipx.pypa.io/latest/how-to/install-pipx.html), run
in a POSIX shell:

```sh
python3.12 --version
pipx ensurepath
pipx install --python python3.12 obfuscidian
```

Reopen your terminal after PATH setup, then run `obfuscidian --version` and
`obfuscidian --help` from any folder. pipx manages an isolated Python environment
internally; you do not activate it. See [installation](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/guides/installation.md)
for pipx prerequisites, PowerShell commands, **pip `--user` installation outside
a venv**, local wheels and developer setup. For unattended use, follow
[scheduled jobs and automation](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/guides/installation.md#scheduled-jobs-and-automation).

Alternatively, install into a venv:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install obfuscidian
obfuscidian --help
```

`python -m obfuscidian` offers the same behavior when that Python interpreter
contains the package; your primary Python may not contain a pipx installation.

## Update to a newer stable version

Keep the CLI current to receive features, fixes and security patches. Update
the installation you actually run:

| Installation | Update command |
| --- | --- |
| pipx, originally installed from PyPI | `pipx upgrade obfuscidian` |
| pipx, switching a source/wheel install to PyPI | `pipx runpip obfuscidian install --upgrade obfuscidian` |
| pip user install, outside a venv | `python3 -m pip install --user --upgrade obfuscidian` |
| Activated venv | `python -m pip install --upgrade obfuscidian` |

Use the original installation's Python; in PowerShell a user install may use
`py -3.12 -m pip install --user --upgrade obfuscidian`. Afterward, run
`obfuscidian --version` in your usual shell and check the exact executable used
by scheduled jobs. pipx needs no activation. A source/wheel pipx install normally
retains its original source for `pipx upgrade`; use `runpip` again for subsequent
PyPI updates, or follow the local-source instructions in
[Updating Obfuscidian](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/getting-started/updating.md).

The CLI checks PyPI for newer stable versions and displays an advisory on stderr,
also recording it when an optional private operational log opens. Set
`OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE=true` or `1` to disable the request and notice.
Checks never install updates. Subscribe to repository releases through GitHub
**Watch → Custom → Releases** and read the [changelog](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/CHANGELOG.md).
The notice links to [update instructions](https://bit.ly/updating-obfuscidian).
The [update guide](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/getting-started/updating.md) covers all installation
methods, failed checks and competing PATH entries.

## First backup and restore

New to command-line backups? Start with [What is Obfuscidian?](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/getting-started/what-is-obfuscidian.md)
and the [Quickstart](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/getting-started/quickstart.md). The beginner pages introduce keys,
backup choices and restore steps one topic at a time.

Follow the [complete synthetic rehearsal](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/guides/restore-rehearsal.md)
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

- [Configuration and key custody](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/CONFIGURATION.md)
- [Fresh/additive backup](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/BACKUP.md), [verification](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/VERIFY.md) and [restore](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/RESTORE.md)
- [Command reference](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/reference/cli.md) and [output/privacy/logging](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/CLI.md)
- [Security and limits](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/SECURITY.md), [private reporting policy](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/SECURITY.md) and [troubleshooting](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/TROUBLESHOOTING.md)
- [Contributor guide](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/CONTRIBUTING.md) and [changelog](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/CHANGELOG.md)

Build the local Sphinx/reST/MyST site with the PyData theme (dark by default,
with a reader-selectable light mode):

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
```

Open `docs/_build/html/index.html`. See [documentation maintenance](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/docs/maintainers/documentation.md)
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

Read [AGENTS.md](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/AGENTS.md) and [CONTRIBUTING.md](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/CONTRIBUTING.md) before changing
code. Keep work within the requested task and leave changes reviewable.
Git history and publication actions require separate maintainer authorization.
The project is licensed under [Apache-2.0](https://github.com/jeffshurtliff/obfuscidian/blob/1.0.1/LICENSE).

---

_This utility is considered unofficial and is in no way endorsed or supported by [Obsidian](https://obsidian.md/terms)._

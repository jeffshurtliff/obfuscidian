# Installation and supported environments

Obfuscidian requires Python 3.12 or newer. The tested matrix is Linux, macOS
and Windows on Python 3.12–3.14. This initial development version has no claimed
PyPI publication; install from a source checkout or a locally built artifact.

Linux/macOS implement backup and restore writes. Native Windows implements
help/configuration, private key creation, verification and read-only planning;
vault mutation/recovery and existing-log append still fail closed. A passing
Windows CI job does not enable those writes. See [platform validation](../PLATFORMS.md).
Obsidian does not have to be running; no plugins are executed.

## pip from a checkout

From the repository root, use an isolated environment. POSIX shell:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
obfuscidian --version
```

Windows PowerShell, using a Python 3.12+ interpreter:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\obfuscidian.exe --help
```

The explicit executable paths avoid requiring PowerShell activation-policy changes.
pip resolves runtime dependencies from `pyproject.toml`; docs tooling is optional.
For a local wheel, substitute its actual path for `.` in the install command.

## pipx from a checkout

With pipx already installed and configured on your PATH, run from the repository
root with Python 3.12+:

```sh
pipx install --python python3.12 .
obfuscidian --help
```

PowerShell equivalent, when `python` resolves to a supported interpreter:

```powershell
pipx install --python python .
obfuscidian --help
```

pipx provides an isolated CLI environment. These examples install the checkout;
they do not depend on a package-index release.

## Developers

Use Poetry 2.2 or newer, below 3.0. See [contributing](../maintainers/contributing.md)
for the locked development/docs setup. The [synthetic tutorial](tutorial.md)
expects `python` and `obfuscidian` to be available from the selected environment.

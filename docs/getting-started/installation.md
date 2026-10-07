# Installation steps

Obfuscidian currently installs from its source code. You need **Python 3.12
or newer**. Backup and restore writes work on Linux and macOS; native Windows
supports key creation, verification and previews only.

If Python is missing or older, get a supported version from
[Python downloads](https://www.python.org/downloads/), then reopen your terminal.
The tested Python versions are 3.12–3.14.

## 1. Get the source code

Download the source ZIP from the
[Obfuscidian repository](https://github.com/jeffshurtliff/obfuscidian) using
**Code → Download ZIP**, then extract it. Alternatively, use an existing clone.
Open a terminal in the extracted folder containing `pyproject.toml`.

## 2. Choose an installation method

| Method | Choose this when… |
| --- | --- |
| **pipx (recommended)** | You want `obfuscidian` in your usual shell without activation, including for scheduled jobs. |
| **pip `--user`** | You want it installed outside a venv, in your primary Python's user packages. |
| **venv** | You prefer a separate environment that you activate before using the CLI. |

pipx keeps dependencies in an environment it manages internally. You never need
to activate that environment. A pip `--user` install shares dependencies with
other user packages and is available only where the Python installation permits
it. Follow the [detailed user-install instructions](../guides/installation.md#user-installation-outside-a-venv)
for that alternative and its PATH setup.

### Recommended: pipx without activation

First [install pipx](../guides/installation.md#pipx-without-activation-recommended)
if it is not already available. On Linux/macOS, using an installed Python 3.12:

```sh
python3.12 --version
pipx ensurepath
pipx install --python python3.12 .
```

In Windows PowerShell, select the installed Python 3.12 using the Python launcher:

```powershell
py -3.12 --version
$Python = py -3.12 -c "import sys; print(sys.executable)"
pipx ensurepath
pipx install --python "$Python" .
```

You may select an installed newer supported Python instead. See the detailed
guide if the launcher or versioned interpreter command is unavailable.
`pipx ensurepath` updates PATH configuration so your shell can find the CLI.
**Reopen your terminal**, then run from any folder:

```sh
obfuscidian --version
obfuscidian --help
```

These two commands also work in PowerShell. No activation or return to the
source folder is needed after installation.

### Alternative: a venv

A virtual environment keeps Obfuscidian's Python packages separate from your
other applications. On Linux/macOS, check `python3 --version` reports Python
3.12 or newer, then run from the source folder:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
obfuscidian --version
```

In a **new terminal**, return to this source folder and run
`. .venv/bin/activate` before using `obfuscidian`. Your vault can be in a
different folder. For the PowerShell venv equivalent, local wheels or contributor
setup, follow [Installation and supported environments](../guides/installation.md).
The current source install does not require a published package on PyPI.

## Scheduled jobs

Once the CLI works in your shell, use the
[automation guidance](../guides/installation.md#scheduled-jobs-and-automation)
before setting up cron, Task Scheduler or a Git hook. Scheduled jobs may have
a different PATH, working directory and environment from your terminal.

**Next:** run the [Quickstart](quickstart.md), or learn
[Using the Obfuscidian CLI](using-the-cli.md) first.

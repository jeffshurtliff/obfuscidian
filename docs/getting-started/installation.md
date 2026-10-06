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

## 2. Install in a separate Python environment

A virtual environment keeps Obfuscidian's Python packages separate from your
other applications. On Linux/macOS, run:

```sh
python3 --version
```

Check that this reports Python 3.12 or newer before continuing:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
obfuscidian --version
```

The final command should print Obfuscidian's version.

In a **new terminal**, return to this source folder and run
`. .venv/bin/activate` before using `obfuscidian`. Leave that terminal open while
you follow the tutorials; your vault can be in a different folder.

## Windows and other installation choices

For Windows PowerShell, pipx, local packages or contributor setup, follow
[Installation and supported environments](../guides/installation.md).
The current source install does not require a published package on PyPI.

**Next:** run the [Quickstart](quickstart.md), or learn
[Using the Obfuscidian CLI](using-the-cli.md) first.

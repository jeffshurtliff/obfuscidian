# Installation and supported environments

Obfuscidian requires Python 3.12 or newer. The tested matrix is Linux, macOS
and Windows on Python 3.12–3.14. This initial development version has no claimed
PyPI publication; install from a source checkout or a locally built artifact.
Run installation commands from the folder containing `pyproject.toml`.

Linux/macOS implement backup and restore writes. Native Windows implements
help/configuration, private key creation, verification and read-only planning;
vault mutation/recovery and existing-log append still fail closed. A passing
Windows CI job does not enable those writes. See [platform validation](../PLATFORMS.md).
Obsidian does not have to be running; no plugins are executed.

## Choose a method

- **pipx (recommended):** exposes `obfuscidian` to your primary shell without
  activation, while keeping its dependencies in a managed isolated environment.
- **pip `--user`:** installs outside a venv into your selected Python's user
  packages. It shares dependencies with other user-installed applications.
- **venv:** keeps a project-local isolated environment; activate it or use the
  full path to its executable. Activation is not required for scheduled jobs
  that call that executable directly.

All three methods install the same CLI. They do not change platform capabilities.
pip resolves runtime dependencies from `pyproject.toml`; docs tooling is optional.
For a local wheel, substitute its actual path for `.` in the install command.

## pipx without activation (recommended)

Install pipx using the [pipx installation instructions](https://github.com/pypa/pipx#install-pipx)
for your operating system. Package-manager installations are available for
Linux/macOS; Windows can use a supported Python installation. If pipx was installed
with pip and its command is not on PATH yet, use that interpreter's
`python -m pipx ensurepath` (or `py -3.12 -m pipx ensurepath`), then reopen the
terminal. This requires pipx to be installed in that particular interpreter.

On Linux/macOS, select an installed Python 3.12+ explicitly. This example uses 3.12:

```sh
python3.12 --version
pipx ensurepath
pipx install --python python3.12 .
```

If your supported interpreter is named `python3` instead, check
`python3 --version` and substitute `python3` for `python3.12`. An absolute path
to a supported Python executable can also be supplied to `--python`.

Windows PowerShell with the Python launcher:

```powershell
py -3.12 --version
$Python = py -3.12 -c "import sys; print(sys.executable)"
pipx ensurepath
pipx install --python "$Python" .
```

If `py` is unavailable, check `python --version` is 3.12+ and set
`$Python = python -c "import sys; print(sys.executable)"` instead.
Select the same interpreter for both the check and installation.

`pipx ensurepath` may update shell/PATH configuration. **Reopen your terminal**
after it finishes. From any folder in Bash or zsh:

```sh
command -v obfuscidian
obfuscidian --version
obfuscidian --help
```

PowerShell:

```powershell
Get-Command obfuscidian -CommandType Application | Select-Object -ExpandProperty Source
obfuscidian --version
obfuscidian --help
```

pipx manages an isolated environment internally; these commands do not activate
it. Discover the installed executable rather than assuming a fixed bin directory.
The installation is normally available to the account that installed it, not
every user on the machine. These examples install the checkout, without relying
on an Obfuscidian package-index release.

## User installation outside a venv

Use pip `--user` with a user-owned Python installation that permits user
packages. Open a terminal without an active venv, or run `deactivate` if you
previously activated one. Check the selected interpreter reports Python 3.12+
and that `sys.prefix == sys.base_prefix` reports `True`:

```sh
python3 --version
python3 -c "import sys; print(sys.prefix == sys.base_prefix)"
python3 -m pip install --user .
USER_SCRIPTS=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts', sysconfig.get_preferred_scheme('user')))")
export PATH="$USER_SCRIPTS:$PATH"
command -v obfuscidian
obfuscidian --version
```

`USER_SCRIPTS` comes from the same interpreter used for installation, so it
accounts for different Linux/macOS Python layouts. The `export` affects only
this shell. To make it persistent, run `printf '%s\n' "$USER_SCRIPTS"` and add
`export PATH="/the/printed/scripts/directory:$PATH"` to your `~/.zshrc` for zsh,
or `~/.bashrc` for interactive Bash. Replace the placeholder with the printed
directory; ensure your Bash login configuration loads `~/.bashrc` if needed.
Reopen the terminal and repeat the discovery/version checks.

Windows PowerShell, using Python 3.12 selected by the launcher:

```powershell
py -3.12 --version
py -3.12 -c "import sys; print(sys.prefix == sys.base_prefix)"
py -3.12 -m pip install --user .
$UserScripts = py -3.12 -c "import sysconfig; print(sysconfig.get_path('scripts', sysconfig.get_preferred_scheme('user')))"
$env:Path = "$UserScripts;$env:Path"
Get-Command obfuscidian -CommandType Application | Select-Object -ExpandProperty Source
obfuscidian --version
```

The PATH assignment affects only the current PowerShell session. To persist the
scripts directory for this account while preserving existing user PATH entries:

```powershell
$UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($UserScripts -notin ($UserPath -split ';')) {
    [Environment]::SetEnvironmentVariable('Path', "$UserScripts;$UserPath", 'User')
}
```

Reopen PowerShell afterward. Use the same supported interpreter throughout;
substitute another installed version, or `python`, consistently if necessary.

Some OS/package-manager Python installations reject even `--user` with an
`externally-managed-environment` error. Follow that provider's instructions,
use pipx, or select a suitable user-owned Python instead. Do not override the
protection with `sudo pip` or `--break-system-packages`. See
[PyPA's externally managed environments guidance](https://packaging.python.org/en/latest/specifications/externally-managed-environments/)
and [pip user installs](https://pip.pypa.io/en/stable/user_guide/#user-installs).

## pip in a venv

From the repository root, POSIX shell:

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
In a new POSIX terminal, activate the venv again or invoke its executable by
absolute path. Both `obfuscidian` and `python -m obfuscidian` offer equivalent
behavior **when that interpreter contains the package**. Your primary Python
may not contain a pipx-installed package; use the exposed `obfuscidian` executable.

## Scheduled jobs and automation

First confirm the CLI works in your shell. A scheduler or Git hook may use a
different PATH, working directory, execution account and environment. Do not
depend on interactive shell startup files, aliases, venv activation or previously
exported `OBFUSCIDIAN_*` variables. Use the discovered **absolute executable path**
and explicit absolute vault, mirror and key paths, quoted when they contain spaces.
Run as the installation account with access to those paths; keep the existing
private key outside both vaults. Never put key contents in a command or task.

### POSIX cron example

The following paths are synthetic placeholders. Replace every path with your
chosen executable and locations. The source, key and mirror parent must already
exist. Rehearse with [fake data](restore-rehearsal.md) before scheduling real work.
Preview a current-inventory backup manually on Linux/macOS:

```sh
"/home/demo/.local/bin/obfuscidian" shroud fresh \
  --origin "/srv/demo/vault" --mirror "/srv/demo/mirror" \
  --key "/srv/demo/keys/obfuscidian-demo.key" --non-interactive --dry-run
```

An illustrative user crontab entry runs at 02:00 each day in the scheduler's
timezone. Keep the command on one line; this example does not register a job:

```text
0 2 * * * "/home/demo/.local/bin/obfuscidian" shroud fresh --origin "/srv/demo/vault" --mirror "/srv/demo/mirror" --key "/srv/demo/keys/obfuscidian-demo.key" --non-interactive --yes
```

`--non-interactive` prevents prompts; **`--yes` explicitly consents to replacing
existing backup content**. It does not bypass safety checks. Fresh backups
retain previous encrypted snapshots outside the mirror without automatic pruning;
plan storage and review retained copies. If choosing additive `shroud merge`,
understand that deleted/renamed/excluded historical entries remain and can return
on restore. See [backup modes and consent](../BACKUP.md).

Cron commonly runs `/bin/sh`, even when your interactive shell is zsh. Use
portable command syntax and account for cron's special handling of `%` in
commands; see the [crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html).

### PowerShell and Task Scheduler example

Native Windows supports verification, not backup/restore writes. With an
existing compatible mirror and its external key, discover the executable and
test a read-only command using synthetic placeholder locations:

```powershell
$Obfuscidian = (Get-Command obfuscidian -CommandType Application -ErrorAction Stop).Source
$Obfuscidian
& $Obfuscidian verify --mirror 'C:\Demo\mirror' --key 'C:\Demo\keys\obfuscidian-demo.key' --non-interactive
$Result = $LASTEXITCODE
Write-Output "Obfuscidian exit code: $Result"
```

For a Task Scheduler **Start a program** action, use:

| Field | Value |
| --- | --- |
| Program/script | The full `obfuscidian.exe` path printed by `$Obfuscidian`; browse/select that executable. |
| Add arguments | `verify --mirror "C:\Demo\mirror" --key "C:\Demo\keys\obfuscidian-demo.key" --non-interactive` |
| Start in | An existing folder such as `C:\Demo`, without surrounding quotes. |

Replace the synthetic paths and use the account that installed the CLI and can
read the mirror/key. The task invokes the executable directly, so PowerShell
activation or profile loading is unnecessary. See
[Microsoft's task action guidance](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskaction)
for executable, arguments and working-directory fields. No task is created by
these instructions. A PowerShell wrapper should finish with `exit $Result` to
propagate the captured CLI status to its caller.

### Failures and operational choices

- Check the process status: `0` means success; `1` means operational/integrity
  failure; `2` means configuration/path/usage failure; `130` means keyboard
  interruption. Capture `$?` immediately in a POSIX shell or `$LASTEXITCODE` in
  PowerShell. Stop dependent actions after failure rather than reporting success.
- Arrange one run at a time, and pause editing/sync/other writers during writes.
  Existing transaction checks do not replace scheduling coordination. Test with
  the intended task account, permissions and environment before enabling a job.
- Inspect pending state after failure before retrying. Do not add automatic
  `--recover` or regenerate a missing key. Follow [troubleshooting](../TROUBLESHOOTING.md).
- Choose private output handling appropriate to your scheduler. For write
  commands, see [optional private logs](../CLI.md#optional-private-logs); their
  parent must exist outside vaults and Git repositories. `verify` rejects
  `--log-file`, and dry runs never create application logs.
- Git fetch/commit/push, cross-device transfer and hook setup remain user-managed.
  Installing a shell command does not synchronize devices or make unattended
  restores safe. See [restore guidance](../RESTORE.md) before planning one.

## Updating an existing installation

See [Updating Obfuscidian](../getting-started/updating.md) for stable-release
upgrades, source/wheel updates, pipx source metadata, version checks, release
notifications and disabling the online advisory. Update the same installation
used by your shell or scheduler.

## Installation troubleshooting

| Symptom | Check or action |
| --- | --- |
| `obfuscidian` is not found | Reopen the terminal after PATH changes. For pipx, rerun `pipx ensurepath`; for `--user`, derive the scripts directory from the installation interpreter. |
| The wrong version runs | Use `type -a obfuscidian` in Bash/zsh or `Get-Command obfuscidian -All` in PowerShell. Check competing PATH entries and an active venv; select the intended executable explicitly. |
| `python -m obfuscidian` fails after pipx installation | Use the exposed `obfuscidian` command. Module invocation needs the Python interpreter that contains the package. |
| pip refuses a user install | Leave the venv, check that user packages are permitted, and follow externally managed environment guidance above. |
| Installation works but the job fails | Check its execution account, absolute executable/data paths, permissions and environment; inspect the CLI exit code and stderr. |

## Developers

Use Poetry 2.2 or newer, below 3.0. See [contributing](../maintainers/contributing.md)
for the locked development/docs setup. The [synthetic tutorial](restore-rehearsal.md)
expects `python` and `obfuscidian` to be available; with pipx, `python` is a
separately selected supported interpreter, not necessarily the CLI's interpreter.

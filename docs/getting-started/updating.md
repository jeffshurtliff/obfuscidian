# Updating Obfuscidian

Use the latest stable version to receive new features, bug fixes and security
patches. An older CLI keeps its old code even after a fix is published. Updating
Obfuscidian is a separate step from updating Python or Obsidian.

This project is currently `1.0.0.dev0`, installed from source. **The PyPI commands
below apply once the first stable release is published.** Until then, use the
[source or wheel instructions](#source-or-local-wheel-installations). No published
package or hosted documentation is assumed by this page.

## 1. Check the version and installation you use

Run in the same shell or execution account that normally runs your backups:

```sh
obfuscidian --version
```

In Bash or zsh, find all matching commands:

```sh
type -a obfuscidian
```

In PowerShell:

```powershell
Get-Command obfuscidian -All -CommandType Application | Select-Object -ExpandProperty Source
```

For pipx, `pipx list` identifies the managed installation. For pip, use the
**same Python interpreter used to install the CLI** and run
`python -m pip show obfuscidian` (substitute `python3` or `py -3.12` as appropriate).
Your primary Python may not contain an application installed through pipx.

Check [GitHub releases](https://github.com/jeffshurtliff/obfuscidian/releases)
and the [changelog](../CHANGELOG.md) for the stable version and any upgrade
instructions. On the repository page, choose **Watch → Custom → Releases** to
receive GitHub release notifications according to your account's notification
settings. This also helps when the CLI's online check is disabled or unavailable.

## 2. Update using your installation method

Finish any running backup, restore or scheduled job before updating. Retain your
external key and its offline backup; a CLI update never calls for a new key.
Check release notes for Python requirements and compatibility changes first.

These commands request a stable PyPI package. Do not add `--pre` or enable
`PIP_PRE` if you want stable releases only. An installer may choose an older
compatible version when your Python is too old for the latest release; check
the reported version afterward.

### pipx: available in your main shell

For an installation originally made from PyPI:

```sh
pipx upgrade obfuscidian
obfuscidian --version
```

The same commands work in PowerShell. No environment activation is needed.
pipx updates the environment it manages; running `python -m pip install` in
your main shell would update a different Python installation.

**If you installed from a source folder or local wheel**, pipx normally retains
that original source for upgrades. To deliberately switch that installation to
stable PyPI releases after publication, run:

```sh
pipx runpip obfuscidian install --upgrade obfuscidian
obfuscidian --version
```

Use the same `runpip` command for subsequent PyPI upgrades of that installation;
this explicitly selects the package index rather than relying on pipx's stored
installation source. To continue using local releases instead, follow
[source or local wheel installations](#source-or-local-wheel-installations).

### pip `--user`: outside a venv

Open a shell without an active venv. Select the Python interpreter used for the
original user installation. For Linux/macOS with `python3`:

```sh
python3 -m pip install --user --upgrade obfuscidian
python3 -m obfuscidian --version
obfuscidian --version
```

In PowerShell, for an installation made with the Python 3.12 launcher selector:

```powershell
py -3.12 -m pip install --user --upgrade obfuscidian
py -3.12 -m obfuscidian --version
obfuscidian --version
```

Use your original supported interpreter if it differs from these examples.
User packages share dependencies with other user-installed tools. If Python
refuses changes to an externally managed environment, follow the
[installation guidance](../guides/installation.md#user-installation-outside-a-venv)
and use pipx or a venv. Do not use `sudo pip` or `--break-system-packages` to
bypass the protection.

### venv: update inside the environment

In Bash or zsh, from the folder containing your `.venv`:

```sh
. .venv/bin/activate
python -m pip install --upgrade obfuscidian
python -m obfuscidian --version
obfuscidian --version
```

In PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade obfuscidian
python -m obfuscidian --version
obfuscidian --version
```

For another environment name or location, use its activation script. Activation
is optional if you call that environment's Python by its full path. Update
each environment independently, including an environment used only by a job.

### Source or local wheel installations

Obtain the intended reviewed source or wheel from the project's maintainer or
release, and read its upgrade notes. From that source folder, install again into
the same environment. These examples use `.` for source; replace it with the
actual wheel filename for a wheel:

| Installation | Command |
| --- | --- |
| pipx | `pipx runpip obfuscidian install --upgrade .` |
| pip user packages, Linux/macOS | `python3 -m pip install --user --upgrade .` |
| pip user packages, PowerShell | `py -3.12 -m pip install --user --upgrade .` |
| Activated venv | `python -m pip install --upgrade .` |

Changing files in a non-editable source checkout does not update an installed
CLI. If the source still has the **same package version**, pip may retain the
old installation; use `--force-reinstall` with the intended local source/wheel
to replace it explicitly. Contributors using Poetry should follow
[developer setup](../guides/installation.md#developers) and the checked-out
revision's lockfile instead of upgrading the project through pip.

## 3. Confirm that your shell and jobs run the updated copy

Run `obfuscidian --version` again and compare it with the intended stable release.
If the old version still runs, repeat the command-discovery checks in step 1.
An active venv, another Python's user scripts, shell alias or earlier PATH entry
can take priority over the copy you updated. Select the intended executable by
its full path; reopen the terminal if it retains an old command location.

For cron, Task Scheduler, hooks or another execution account, check the version
using the **exact executable configured in the job**, under that account. An
updated interactive shell does not prove the job uses the same installation.
See [scheduled jobs](../guides/installation.md#scheduled-jobs-and-automation).

Before resuming writes, follow any release-specific steps and preview with
`--dry-run`. [Verification](../VERIFY.md) checks an existing encrypted mirror;
it does not certify that the installed CLI is free of vulnerabilities.

## Update availability notices

Each CLI invocation, including help/version and read-only commands, makes a
best-effort HTTPS request to the [PyPI JSON API](https://docs.pypi.org/api/json/).
It compares the installed version with the highest stable release having an
available, non-yanked file. Development, alpha, beta and release-candidate
versions are excluded. When a newer stable release exists, stderr shows:

```text
A newer version of obfuscidian (v1.1.0) is available. Visit https://bit.ly/updating-obfuscidian for update instructions.
```

The notice links to [these update instructions](https://bit.ly/updating-obfuscidian).
It never downloads or installs a release.

If the lookup fails, the CLI silently skips the notice and commands still run
with their normal exit status. Absence of a newer-version notice is
not proof that your version is current or safe; check release announcements too.

Requests use short connection/read timeouts, no retries or redirects, and a
bounded response. They send no vault content, keys, paths, command arguments or
installed-version value; PyPI can observe ordinary network connection metadata
such as your IP address. No update cache or other application file is created.
Shell completion skips the check. The notice is recorded as an `update_notice`
JSON event only when a requested operational log opens after safe preflight.
Failed preflight, help/version, verification and dry runs never create a log.

### Suppress the check and notice

Set `OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE` to `true` or `1` to skip the request,
terminal notice and log event entirely. Values are case-insensitive and surrounding
whitespace is ignored; other values do not suppress it.

For the current Bash/zsh session:

```sh
export OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE=true
```

For the current PowerShell session:

```powershell
$env:OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE = 'true'
```

To re-enable checks, use `unset OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE` in Bash/zsh
or `Remove-Item Env:OBFUSCIDIAN_SUPPRESS_UPDATE_NOTICE` in PowerShell. For
persistent suppression, set it in your shell startup configuration or the job's
execution environment. Suppression does not update the CLI; continue checking
stable releases and security fixes yourself.

# Using the Obfuscidian CLI

A **CLI** is a command-line interface: you type a command in a terminal, press
Enter, and read the result. Obfuscidian's commands work on folders you choose.

## Find help

After [installation](installation.md), try:

```sh
obfuscidian --help
obfuscidian shroud fresh --help
```

Help lists the available commands and their options. `python -m obfuscidian`
also works in the same Python environment.

| Command | Purpose |
| --- | --- |
| `keygen` | Create a new private key file |
| `shroud fresh` | Back up the vault's current included files |
| `shroud merge` | Update a backup while keeping its older entries |
| `verify` | Check the entire encrypted backup without changing it |
| `unshroud fresh` | Restore the backup to a readable folder |
| `unshroud merge` | Restore into a separate Git branch and review folder |

## Read a command

```sh
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --dry-run
```

Here, `--origin` chooses your readable vault, `--mirror` chooses the encrypted
backup folder, and `--key` chooses the secret file. `./vault` means a folder
named `vault` inside the terminal's current folder. Real paths can be different;
put paths containing spaces in quotes, such as `--origin "/path/My Vault"`.

In Linux/macOS examples, a backslash at the end of a line continues the same
command on the next line. Copy the whole block, without adding a prompt like `$`.

## Preview before writing

Use `--dry-run` on backup and restore commands to check the plan first.
Read the result before running the command again without it. `verify` is
already read-only and does not accept `--dry-run`.

`--non-interactive` disables questions; it does not approve replacement.
`--yes` explicitly approves replacement or recovery after validation. The
beginner examples use new destinations so you can practice without replacing
existing notes. If a command fails, stop and read its guidance.

**Next:** [Set up your private key](private-key.md).
For all options and exit codes, see the [CLI reference](../reference/cli.md).

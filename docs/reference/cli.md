# Command reference

`obfuscidian` and `python -m obfuscidian` are equivalent. Options belong after
the operation; `fresh` and `merge` are positional modes, not subcommands.

| Command | Purpose | Important options |
| --- | --- | --- |
| `obfuscidian --help` / `--version` | Discover commands / installed version | Global options only |
| `keygen` | Exclusively create a private key | `--alias`, `--dir`, `--dry-run` |
| `shroud fresh` | Snapshot current included inventory | `--origin`, `--mirror`, key selection, repeatable `--exclude` |
| `shroud merge` | Add/update paths, retaining stale entries | Same backup options; exclusions do not remove historic entries |
| `verify` | Authenticate all manifest records and objects | `--mirror`, key selection; always read-only |
| `unshroud fresh` | Restore a complete snapshot | `--origin`, `--mirror`, key selection, `--preserve-config` |
| `unshroud merge` | Restore additive union to a separate Git worktree | Fresh restore options plus `--base-branch`, `--branch`, `--worktree`, optional `--gitdir` |

```sh
obfuscidian --help
obfuscidian keygen --help
obfuscidian shroud --help
obfuscidian verify --help
obfuscidian unshroud --help
```

Vault commands select `--key FILE`, or `--alias NAME` with optional
`--keydir DIR`. Explicit invalid selections fail; no replacement key is generated.
See [configuration](../CONFIGURATION.md) for the complete precedence table.

All commands support `--non-interactive` and `--verbose`. Write commands support
`--dry-run`, private `--log-file` and explicit `--log-paths` where applicable.
Backup and fresh restore support `--recover` and `--yes`. Merge restore accepts
`--yes` but needs no destructive consent for a new review output; it has no
automated recovery. Keygen and verification reject `--yes`/`--recover`.
Verification has no `--dry-run`, exclusion or logging options. Restore has no
`--exclude`. See [output, prompts and exit codes](../CLI.md).

Native Windows writes/recovery remain refused; help, keygen, verification and
read-only planning are available. Consult [platform validation](../PLATFORMS.md).

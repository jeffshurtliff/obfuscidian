# Troubleshooting and recovery

Start with `obfuscidian COMMAND --help` and [exit codes](CLI.md). A failure is
never partial success. Default diagnostics redact paths; choose `--verbose`
only in a private terminal when you need escaped handoff locations. Do not paste
verbose output, logs, keys or real vault names into public issues.

| Symptom | Next action |
| --- | --- |
| Missing/invalid selector (exit 2) | Check explicit options and `OBFUSCIDIAN_*` precedence; invalid explicit values never fall back. |
| Missing key or authentication failure | Locate the original private key/offline copy; never generate a new key to decrypt an old snapshot. Preserve the failing mirror for inspection. |
| Replacement refused unattended | Preview first, then supply `--yes` only for an intended replacement. `--non-interactive` supplies no consent. |
| Unsafe path, link or collision | Choose separate real directories and supported target names; do not rename/normalize encrypted records or bypass checks. |
| Oversized file/manifest or insufficient space | Review the 50 MiB token cap and staged/rollback estimates. Exclusions do not purge old merge records. |
| Native Windows mutation or log append refusal | Use supported read-only commands; vault writes/recovery and existing-log append remain unimplemented. |
| Dirty Git origin or existing review output | Review tracked, untracked and ignored data; use a clean origin and new branch/worktree names after inspecting any retained output. |
| Logging failed after publication | Inspect destination and retained recovery state before retrying; data may already be complete although the command failed. |

## Pending transaction ownership

Stop other writers and inspect reported retained locations privately.
`verify` and dry runs report pending ownership without repairing it. Never
delete a lock because it is old; a live owner, malformed journal, changed payload
or unexpected user data must remain blocked.

Backup and fresh restore support explicit `--recover` only for a proven pending
transaction. It restores the verified previous state and then replans the
requested operation. It conflicts with `--dry-run`; unattended recovery requires
`--yes`. With synthetic placeholder paths:

```sh
obfuscidian unshroud fresh --origin ./restored-vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --recover --non-interactive --yes --verbose
```

Use this only after inspecting an actual pending restore, on a supported write
platform. Recovery refusal preserves uncertain content for manual investigation.
Git merge restore has **no automated `--recover`**: inspect the new worktree,
branch and private staging/journal manually before retrying. No branch pruning,
stage, commit, push or merge is automatic. See [restore](RESTORE.md).

## Retained plaintext and cleanup

Successful fresh restore keeps the previous plaintext payload in a private
`.obfuscidian-transaction-*` container outside both vaults and enclosing Git
worktrees. Failed reconstruction can leave `.obfuscidian-git-stage-*` or other
private staging. These are sensitive even though the mirror is encrypted.
There is no automatic fresh rollback pruning or public prune command.

Before manually removing a known successful rollback, verify the current mirror,
compare restored files and keep an independent backup. Confirm the exact location
from the private handoff, that no transaction is pending, and that it contains
only the old payload you intend to discard. Keep its key while an encrypted copy
is still needed. Retain changed/unknown artifacts; never recursively delete all
matching siblings or remove active ownership. Ordinary deletion is not a promise
of secure erasure on SSDs, snapshots, cloud sync or retained Git history.

## Git review

The separate merge worktree contains an additive union: base-only and historical
backup files remain. Inspect ignored data with `git status --ignored`; selected
ignored files may require manual `git add -f`. Restored differences are left
uncommitted. Review and commit selected changes before any later manual merge.
See [manual review steps](RESTORE.md#manual-review-and-ignored-data). Never use
real vaults or cloud repositories to reproduce a suspected problem publicly;
build a small fake fixture and use [private security reporting](SECURITY.md#report-a-concern-privately).

# Fresh and additive encrypted backup

`shroud fresh` backs up the current included inventory; Thread 07 adds
`shroud merge` for additive history retention. Thread 08 exposes
[read-only verification](VERIFY.md). [Fresh restore](RESTORE.md) is available; optional file logging remains planned. 
The internal [v1 validator](FORMAT.md) authenticates produced snapshots; 
it is not a supported Python library API.
No Git commands, commits, pushes, merges or worktrees are created by backup.
Threads 06–07 are reviewed and merged/pushed into `origin/main`, with issues
#6–#7 closed and green Linux CI on Python 3.12–3.14. See the
[Thread 07 completion record](../dev/IMPLEMENTATION_PLAN.md#thread-07--merge-backup-completion-record-5-october-2026)
for validation and platform limits. Thread 08 is complete, reviewed and
merged/pushed, with issue #8 closed and Linux Python 3.12–3.14 CI passing; see
[verification](VERIFY.md) and its
[completion record](../dev/IMPLEMENTATION_PLAN.md#thread-08--read-only-verification-completion-record-5-october-2026).
Thread 09 is complete, reviewed and merged/pushed; see
[fresh restore](RESTORE.md) for the accepted Python 3.14 CI gap. Thread 10 is implemented locally for review; see
[additive Git merge restore](RESTORE.md#additive-git-merge-restore). Thread 11 remains **not started**.

## Usage and selection

Use an existing key outside both vaults. The source directory and destination
parent must already exist; only the final mirror component may be absent.
Pause Obsidian editing, sync and other writers during backup or recovery.

```sh
obfuscidian shroud --help
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --dry-run
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --non-interactive --yes
python -m obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --alias primary --keydir ./keys --exclude '**/*.tmp' --dry-run
obfuscidian shroud merge --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --dry-run
obfuscidian shroud merge --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --non-interactive
```

Vault CLI options override `OBFUSCIDIAN_ORIGIN_VAULT` and
`OBFUSCIDIAN_MIRROR_VAULT`, including when the explicit value is invalid.
An absent vault path or key alias can prompt only with terminal input and
without `--non-interactive`. Key precedence, custody and alias rules follow
[configuration](CONFIGURATION.md). Explicit invalid selections never fall back
to another key or vault. The operation never generates or overwrites a key.

## Snapshot and preservation

The included inventory covers regular files as exact bytes, hidden files,
`.obsidian`, nested paths, binary attachments, zero-byte files and empty
directories. [Mandatory exclusions and component globs](INVENTORY.md) apply
before encryption. `.git` components, `.gitignore` files and
`obfuscidian-*.key` files are always excluded at every depth. Other secrets
must be kept outside the vault or explicitly excluded.

Fresh describes **only the current included inventory**. Deleted and newly
excluded old entries disappear from the new snapshot. The complete previous
snapshot remains in a private rollback directory outside the mirror and
enclosing Git worktrees, with no automatic pruning. Keep that encrypted copy
and its key until you decide it can be removed. The rollback directory contains
the managed `.obfuscidian` tree and can be authenticated as a complete mirror.

Merge is the **union of the old snapshot and current included paths**. It
initializes a new mirror safely, adds new paths, and updates existing paths.
Deleted files, newly excluded files, old renamed paths and absent/excluded
empty directories remain backed up with their previous metadata and ciphertext.
An exclusion prevents current reads/updates; it does not purge historic data.
Renaming `note.md` to `renamed.md` adds a new ID/token while retaining `note.md`.
**Deleted or renamed notes can return during a later restore**, because the
manifest still describes them. [Fresh restore](RESTORE.md) reconstructs these historic bytes.
Use fresh for a current-inventory snapshot that omits stale paths. Fresh does
not erase retained rollback copies or Git history.

A current file at an old directory path, or a current directory at an old file
path, conflicts with retention. Merge refuses before writes and explains that
`shroud fresh` is required for that exact-state transition. Excluding the entire
new conflicting entry prunes it and retains the old entry without a transition.

After successful merge publication, cleanup removes only that operation's
proven temporary staging, rollback and journal data. Older fresh rollback copies
and failed/recovered workspaces are never pruned. Unknown names, links, changed
bytes/identities, or cleanup I/O failure leave remaining artifacts with a warning;
the complete published snapshot remains in place. A failed final directory
flush warns that removed artifacts might reappear after restart, without claiming
absent data is still retained. Cleanup is best effort and
may be partial; failures do not reverse an already successful publication.

The source is read-only: backup never rewrites content, names, permissions or
timestamps. Ordinary filesystem reads may update access times. Root mirror
`.git` files/directories and `.gitignore` remain at their original identities.
Unknown mirror entries, links/junctions, special files, overlap, selected-key
aliases in either vault and missing parents cause refusal; `--yes` cannot
bypass these checks. No Git controls are initialized when absent.

An existing snapshot must authenticate completely with the selected key,
including every object. Corruption, missing/extra objects, substitution,
unsupported formats and wrong keys stop work before staging. The format and
Fernet recipe are unchanged. Unchanged file content keeps its object ID and
exact validated ciphertext. Metadata-only changes update the manifest. Changed
content at an existing path keeps its ID with a new token; new paths receive
secure random IDs. Renames are new paths, without inferred rename matching.
Mirror lineage is retained; each logical update gets a new snapshot ID and
encrypted UTC timestamp.

## Consent, dry run and no-op

Read-only preflight precedes replacement consent and all transaction writes.
Fresh replacement of existing file content or removal of old files/directories
needs affirmative terminal confirmation or `--yes`. Merge needs confirmation
only when existing file **content** changes; retention itself needs no consent.
Metadata-only updates, additions and initial backups into empty/new mirrors do not need that destructive prompt.
`--non-interactive` never implies consent. Redirected input never triggers
prompts. Decline or EOF returns failure without starting a transaction.

Dry run authenticates the existing mirror, inventories and hashes stable source
files, serializes bounded proposal metadata and estimates ciphertext allocation
and free space, including retained stale object tokens. It never encrypts,
creates IDs, repairs pending ownership, or writes destinations, staging, locks, journals, rollback copies or logs. It needs
no replacement consent and rejects `--recover`. Estimates do not reserve space
or guarantee that a later write will succeed.

A no-op compares the complete proposed logical records: included paths for fresh,
and old/current union for merge, with sizes, plaintext hashes and file/directory
modification times. Deletion or exclusion alone can be a merge no-op if the
retained union and included directory metadata are unchanged. It leaves tokens,
manifest, snapshot ID and timestamp unchanged, creates no randomness or write artifacts, and does not prompt.
Source and mirror identities/content marks are rechecked even for no-ops.

## Publication, failure and recovery

Backup reads one bounded source file at a time in preflight, then re-reads it
for staging and validates its planned hash. The source is fully re-inventoried
after reading and immediately before publication. The entire staged snapshot
passes authenticated v1 validation. Each object and the manifest obey the
50 MiB encrypted limit; oversized input is an error rather than silently skipped.
Required free space accounts for complete staged ciphertext and the transaction
metadata reserve. Retained old allocation is moved rather than charged as a
second copied payload.

Publication uses existing [private transaction primitives](TRANSACTIONS.md).
It replaces only `.obfuscidian` through checked, journaled same-filesystem
renames. Detected source/destination changes abort. A normal failure attempts
to restore the previous complete state; uncertain artifacts remain retained
with ownership blocking subsequent writes. Multi-step replacement can briefly
leave the managed tree absent; it never publishes a partially populated tree.
Readers must respect pending ownership rather than assuming concurrent access
is an atomic snapshot.

Explicit recovery restores the proven previous complete state before replanning
the requested backup. Non-interactive recovery requires `--yes`:

```sh
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --recover --non-interactive --yes
```

Recovery authenticates complete old/proposed mirror payloads with the selected
key before inverse moves. It refuses live ownership, malformed journals,
changed/missing bytes or identities and unexpected user data. Incomplete staging
that never received publication authorization stays retained. Recovery does not
delete uncertain content or remove locks based on age. `--recover` requires an
actual pending transaction; it is not a force-overwrite switch. Dry run reports
pending ownership as failure without repairing it.

Normal output reports mode, file/directory/exclusion counts, plaintext bytes and
the result; merge also counts new, changed, metadata-only, unchanged and retained
files. Warnings/errors on stderr. Names and private locations stay
redacted unattended; `--verbose` permits escaped relative names and retained
workspace/rollback locations. Terminal users receive private handoff locations.
Keys and file contents never appear in output. Exit codes are `0` for success,
dry run or no-op; `1` for operational/integrity/consent/recovery failure; `2`
for configuration/usage errors; and `130` for interruption after attempted
recovery. Failures cannot report successful publication.

## Limits and deferred work

Mutation currently requires POSIX transaction facilities. Native Windows writes
fail closed pending Thread 12; read-only dry runs remain available. Filesystem
limits are read without writing a probe. Backup creates only fixed lowercase
ASCII managed names and hexadecimal IDs, whose comparisons agree across case
policies. Conservative case/Unicode lock comparison also serializes destination
aliases; original names remain unchanged inside the encrypted manifest.
Restore must establish the actual target's full naming rules in its own thread.

Identity/hash rechecks are best effort, not an atomic source snapshot or a
guarantee against hostile same-authority writers. Local synthetic process-death
tests do not establish power-loss, network/cloud-filesystem or supported-platform
guarantees. Hosted CI must be reported separately. Public verification is
available through Thread 08. Restore Threads 09–10 and optional logging/CLI
polish Thread 11 remain planned. Sphinx remains Thread 13.

# Fresh plaintext restore

Thread 09 adds `unshroud fresh`. The encrypted mirror is the source; the origin
is the plaintext destination. Git merge restore remains planned for Thread 10.
These changes are locally implemented and awaiting maintainer review; hosted CI
and broader supported-platform validation have not run for this increment.

## Usage

Keep the selected key outside both locations. The mirror must be a complete
existing backup. The destination parent must exist; only the final destination
component may be absent. Pause editors, Obsidian sync and other writers.

```sh
obfuscidian unshroud fresh --mirror ./encrypted-mirror --origin ./restored-vault \
  --key ./keys/obfuscidian-primary.key --non-interactive --dry-run
obfuscidian unshroud fresh --mirror ./encrypted-mirror --origin ./restored-vault \
  --key ./keys/obfuscidian-primary.key --non-interactive --yes
```

`--origin` and `--mirror` override `OBFUSCIDIAN_ORIGIN_VAULT` and
`OBFUSCIDIAN_MIRROR_VAULT`. Key selection follows [configuration](CONFIGURATION.md):
`--key`, or `--alias` with optional `--keydir`, then environment selectors.
Explicit invalid selections fail without fallback or key generation. Missing
selectors can prompt only with terminal input; redirected input never prompts.

## Complete validation and preservation

The command authenticates the entire manifest and every required object,
checking ciphertext/plaintext bindings, schema, exact object namespace and
relative paths before staging any plaintext. Configuration records are fully
verified even when `--preserve-config` will skip them. A wrong key, missing or
corrupt object, unsupported version, unsafe name or pending source ownership
fails before destination changes and transaction artifacts.

Restore reconstructs exact binary bytes, hidden files, zero-byte files, Unicode
names, relative structure and empty directories in private staging. It preserves
supported file/directory modification times, applying directory times after
children. Unsupported or truncated times produce a redacted warning. Ownership,
ACLs, extended attributes and original executable modes are not restored.
New POSIX plaintext files use mode `0600`, directories `0700`.

Root `.git` (file or directory) and `.gitignore` remain in place with their
identities unchanged. `--preserve-config` also leaves root `.obsidian` in place,
including its absence; authenticated backup configuration is then skipped.
Without this option, old settings move to rollback and backup settings are
restored. No Obsidian plugins or Git commands are executed. Nested repositories,
Git metadata aliases, links, junctions, special files, selected-key hard links,
overlap and unsafe destinations are refused.

Other existing files, including files excluded during backup, move to rollback.
Fresh restore reproduces the selected snapshot, so a `shroud merge` snapshot
can reintroduce deleted, renamed or subsequently excluded historic files.
There is no selective restore exclusion option.

Target names are checked with a conservative case-folded NFC comparison,
including on case-sensitive filesystems, and actual filesystem component/path
length limits. Protected-control aliases are refused. Ambiguous names fail
without renaming or normalization; valid distinct case/Unicode names on some
filesystems can therefore be refused. More precise filesystem rules belong to
Thread 12. Staging-prefix length checks also precede plaintext creation.

## Consent, dry run and rollback

Replacing an existing payload requires consent after read-only preflight and
before staging. `--yes` supplies replacement/recovery consent; it never bypasses
validation. `--non-interactive` does not imply `--yes`. A new, empty or
protected-controls-only destination needs no destructive confirmation.
Refusal or EOF writes nothing. Dry run needs no destructive consent and creates
no destination, locks, staging, rollback, journals, logs or Git state.

Successful fresh restore retains the previous payload in a private rollback
container outside both vaults and all enclosing Git worktrees, on the same
filesystem. **Restore rollback and failed staging contain sensitive plaintext.**
There is no automatic pruning. The terminal explains this sensitivity; paths
are shown only interactively or with explicit `--verbose`, using escaped text.
Keep recovery data private and review it before removing it manually. New and
empty destinations also retain a recovery workspace, with an empty rollback.

Before publication, the entire staged namespace, file sizes/hashes and supported
times are compared with the authenticated proposal. Source/key observations,
ownership and destination content/identities are rechecked. Publication uses
[the existing journaled transaction](TRANSACTIONS.md); root protected controls
are never moved. Normal failure attempts conservative rollback. An interrupt
exits with status 130; required content failure never reports success.

## Explicit recovery and limits

A terminated process or incomplete rollback leaves ownership markers that block
writes and dry runs. Recovery verifies the complete selected encrypted source
before any inverse destination moves. Use the same configuration-preservation
choice as the interrupted operation:

```sh
obfuscidian unshroud fresh --mirror ./encrypted-mirror --origin ./restored-vault \
  --key ./keys/obfuscidian-primary.key --recover --yes --non-interactive
```

Recovery restores the proven previous complete state, retains artifacts, then
replans and retries fresh restore. Non-interactive recovery requires `--yes`;
`--recover` conflicts with `--dry-run`. Changed, unknown or uncertain recovery
artifacts are retained and block recovery. Do not remove a lock based on age.
If the mirror or key is damaged, make them verifiable before retrying recovery.

Checks are best-effort observations, not an atomic snapshot. Exclusive ownership
coordinates Obfuscidian processes, not unrelated writers. Multi-entry publication
is journaled and recoverable under tested failures; it is not universally atomic
or a guarantee against power loss. Native Windows mutation fails closed pending
Thread 12; read-only preflight/dry runs remain available. No Git merge restore,
branch/worktree creation, commit, push, release or optional logging is included.

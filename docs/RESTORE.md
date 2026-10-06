# Plaintext restore

`unshroud fresh` reconstructs a complete authenticated snapshot into the plaintext
origin. `unshroud merge` reconstructs an additive union with a local Git base in
a separate uncommitted review worktree. The encrypted mirror stays read-only.

Rehearse into an absent destination with the
[synthetic tutorial](guides/restore-rehearsal.md) before replacing real data.
Existing plaintext moves to sensitive private rollback during fresh replacement.
[Platform validation](PLATFORMS.md) records the passing OS/Python matrix and
intentional Windows mutation/recovery refusal.

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
filesystems can therefore be refused. More precise filesystem capability
detection remains future work; the current policy retains conservative
comparison. Staging-prefix length checks also
precede plaintext creation.

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
or a guarantee against power loss. Native Windows mutation still fails closed pending
native publication/ACL support; read-only preflight/dry runs remain available.
Fresh mode performs no Git operations. Optional private logging follows the [CLI contract](CLI.md).


## Additive Git merge restore

`unshroud merge` restores into a new local `obfuscidian/` branch and separate
worktree. It retains base-only files and directories, overlays backup files with
exact bytes, and leaves all differences unstaged and uncommitted. It is an
additive review result, not an exact backup snapshot. The original checkout,
branch and index stay unchanged; only the requested new shared branch/worktree
metadata is added. No restore commit, origin checkout switch, stash, reset,
fetch, merge, remote or push is performed.

```sh
obfuscidian unshroud merge --origin ./vault --mirror ./encrypted-mirror \
  --key ./keys/obfuscidian-primary.key --base-branch main --branch review \
  --worktree ./vault-review --non-interactive --dry-run
obfuscidian unshroud merge --origin ./vault --mirror ./encrypted-mirror \
  --key ./keys/obfuscidian-primary.key --base-branch main --branch review \
  --worktree ./vault-review --non-interactive --verbose
```

### Origin, base, branch and output checks

Git must be on PATH. Origin must be the worktree root of an existing local
non-bare repository with a commit. Linked origin worktrees with a legitimate
root `.git` file are supported. `--gitdir`, if selected, must match the exact
Git administration directory discovered for that origin; it cannot redirect
operations into a different repository.

The index must match HEAD, and tracked files must match raw committed bytes
and executable status. All untracked and ignored vault entries are refused;
even untracked empty directories are conservatively refused. Pending merge,
rebase, cherry-pick, revert, bisect, sequencer or index-lock state blocks the
operation. Links, special files, nested Git controls and submodule layouts are
unsupported. Partial/promisor clones are refused before object resolution to
prevent implicit fetching. Pause all writers during restore.

`--base-branch` names an existing local committed branch, default `main`.
Tags, remote branches and implicit `master` fallback are not selected.
`--branch` is a suffix under mandatory `obfuscidian/`; its default is
`restore-YYYYMMDD-HHmmss`. Complete refs are validated with Git, and existing
branches, ref namespace conflicts and timestamp collisions are refused.
No branch is reset.

`--worktree` selects a new absent output whose parent already exists. Without
it, output is a sibling named `<origin-name>-restore-YYYYMMDD-HHmmss`. The
parent must be outside Git worktrees. Output cannot overlap origin, mirror,
key, Git administration or registered worktrees. Source/key custody, actual
length limits and conservative case/Unicode collisions are checked before
writes. File/directory conflicts between base and backup are refused with
fresh-mode guidance. Git options are merge-only and rejected by fresh mode.

### Staging, Git isolation and settings

Every encrypted object is authenticated before plaintext staging. The entire
additive union is reconstructed privately and checked before creating any
branch/worktree. The chosen base is read as raw Git blobs, without checkout
filters or attribute conversion. The new worktree is created with
`--no-checkout`; only its index is initialized to the committed base with
`read-tree`. Journaled publication installs the verified union and preserves
the new `.git` file and the base root `.gitignore`.

`--preserve-config` keeps base `.obsidian` content unchanged, including its
absence; backup settings are still authenticated. Without it, settings are
additive too: backup settings overwrite matching base settings and base-only
settings remain. Git does not track empty directories, although restore
reconstructs them on disk. Files and directories use private POSIX permissions;
backup executable modes, ACLs and other extended metadata are not imported.
The executable flag of base-only Git blobs is retained with owner-only access.
Supported backup modification times are preserved; limitations warn.

Git subprocesses use argument lists, suppress raw Git diagnostics and ignore
inherited Git selectors and global/system configuration. External hooks and
fsmonitor are disabled; no checkout, status or diff conversion executes
repository filters. Lazy fetching and automatic maintenance are disabled.
Repository configuration and original HEAD/index/content are rechecked.
Repositories whose checked-out bytes differ because of line-ending conversion
or filters are conservatively refused. Base blobs also use the bounded
plaintext reconstruction limit derived from the existing v1 object cap; no
unbounded base-file allocation is attempted.

### Manual review and ignored data

Completion reports ignored untracked files as a review count. Interactive or
`--verbose` output discloses escaped worktree/branch locations and quoted POSIX
shell guidance; `--verbose` additionally lists ignored relative paths. Review
all changed, untracked and ignored content before staging selected paths.
Manual commands in terminal output are represented as escaped strings to
avoid terminal control characters; remove the representation quoting before
executing them. For ordinary paths, the workflow is:

```sh
git -C ./vault-review status --ignored
git -C ./vault-review diff --no-ext-diff --no-textconv
git -C ./vault-review add -- reviewed-note.md
# Only after explicit review of the ignored file:
git -C ./vault-review add -f -- ignored-attachment.bin
git -C ./vault-review commit
# Later, after reviewing the original checkout and the restore commit:
git -C ./vault merge -- obfuscidian/review
```

**Uncommitted differences cannot be merged.** These steps are manual;
Obfuscidian never stages restored differences, commits or merges them. Git
may apply the user's configured filters when the user subsequently runs their
own review/staging commands; restored bytes are the raw validated bytes.
Merge mode creates a new review output, so destructive confirmation is not
needed; `--yes` does not bypass any validation. Dry run creates no plaintext,
branch, worktree, lock or journal.

### Failure cleanup and retained artifacts

Normal failure attempts cleanup only of the operation's newly created branch
and worktree. Cleanup compares output identity, complete content including
ignored data, protected controls, index, branch commit, registration, original
state and pending transaction ownership. Changed, unknown or partially created
artifacts are retained with guidance. The branch is removed only if it still
points at the captured base and no worktree is using it. No other worktree or
branch is removed or pruned. Interrupts exit 130 and do not claim success.

Known unchanged private reconstruction staging is removed after success or
failure. Failed incomplete staging and journaled transaction recovery data
remain **sensitive plaintext**. A cleanup warning after successful publication
does not undo the result. Use interactive/verbose failure locations and inspect
private `.obfuscidian-git-stage-*` and `.obfuscidian-transaction-*` siblings
outside all worktrees. Do not delete unknown contents or locks based on age.

After process termination, incomplete creation or user edits, inspect the
retained worktree, branch and private journal/staging manually. Existing output,
branch collisions and pending ownership refuse a retry. Merge mode does not
provide automated `--recover`; that option remains for fresh-mode journal
recovery. Retain uncertain artifacts and make an explicit manual recovery
decision before retrying with new names. Journaled publication attempts
rollback to the new worktree's prior state under tested ordinary failures;
it does not guarantee atomic Git/filesystem publication or power-loss recovery.
Native Windows writes remain fail-closed pending native publication/ACL
implementation. Synthetic temporary-repository tests and the
Linux/macOS/Windows Python 3.12–3.14 matrix passed with these retained limits;
see [platform validation](PLATFORMS.md). Universal filesystem, cloud-sync and
power-loss guarantees are not established by that matrix.

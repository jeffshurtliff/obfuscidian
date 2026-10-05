# Internal publication and recovery

Thread 05 implements internal transaction primitives in `transactions.py`.
These are orchestration building blocks, not a supported Python API. The CLI
exposes [`shroud fresh|merge` and `--recover`](BACKUP.md), plus
[read-only verification](VERIFY.md) that inspects ownership without recovery.
Restore command wiring remains planned.
The encrypted [v1 format](FORMAT.md) is unchanged.

## Preflight and ownership

`_plan_transaction` observes locations without creating anything. It rejects
roots, overlap, missing parents, links/junctions, special files, nested repository
payloads, unsafe Git controls, unmanaged mirrors, inadequate access, and inadequate
estimated free space. The caller must provide actual target naming rules and a
staging estimate. The estimate includes staged bytes and any caller-owned copies;
rename-based rollback retains existing allocation. A separate metadata reserve
is checked too. This is a preflight estimate, not a disk reservation or a quota;
actual writes can still fail. Large journals fail at a bounded 16 MiB limit.

The closest suitable existing ancestor outside the source, destination, and
all enclosing Git worktrees is selected on the destination filesystem. Git
markers are inspected without executing Git or reading its metadata. The private
transaction directory is a uniquely named child there. Parent identities are
rechecked; no missing ancestor is created. Sources remain read-only in these
primitives. Callers must inventory/recheck source content and keep keys outside
both vaults using existing path/key helpers.

Destination names are hashed using the caller's target comparison rules to
choose an ownership filename. All destination ancestors are checked for existing
ownership, including when an enclosing Git marker changes the preferred staging
location. No timestamp or PID makes a retained lock safe to delete. Ordinary
execution refuses any retained ownership file. Explicit recovery must obtain the
nonblocking OS lifetime lock; a live competing writer keeps ownership.

Mutation currently requires POSIX `flock`, anchored no-follow directory handles,
mode-0600 ownership/journals, and mode-0700 workspaces. Native Windows mutation
fails closed before creating artifacts; Windows locking, owner-only directory
ACLs, and broader filesystem hardening remain Thread 12. Read-only observation
and consent helpers do not create artifacts. Linux hosted validation and native
Windows execution must be reported separately from local macOS tests.

## Stage, validate, publish

Execution accepts trusted internal builder and verifier callbacks. These are
never loaded from vault/plugin content. The builder receives a private empty
stage. The verifier must validate the complete proposal; a restore caller must
also authenticate and validate every required encrypted source object before
calling the transaction primitive. Mirror execution additionally invokes the
complete v1 validator on the staged mirror and on the previous managed mirror.
An optional trusted prepublication callback rechecks the caller's complete source
inventory immediately before destination changes; backup uses it for both fresh and merge.
Mirror stages may contain only the managed `.obfuscidian` tree. All staged names
and preserved controls are checked together under actual target rules.

Full tree observations record identities, file sizes/modification times and
SHA-256 hashes, and complete recursive namespaces. Links, special files and
nested `.git` entries are rejected. Files are read in bounded blocks using
no-follow handles with identity/content rechecks. Root `.git` directories are
identity-only controls: their contents are never traversed by transactions.
Root `.git` files and `.gitignore` are also left in place; file content is
rechecked. A requested root `.obsidian` directory is protected for restore.
Stages cannot supply protected controls.

Staged files and directories are flushed before publication. The private JSON
journal records the original destination, protected controls, complete proposed
payload and rename-stable identities. The original observation digest is also
bound in the separately held ownership record. Each checkpoint uses an exclusive
mode-0600 temporary file, full write, file flush/fsync, replacement of the journal,
and directory fsync. Complete observations are persisted before any payload
rename and checkpointed around each move. A partially created destination root
whose identity was never recorded is uncertain and remains blocked.

Mirror publication moves `.obfuscidian` as one managed unit. Restore publication
moves top-level payload entries using checked same-filesystem renames. Root Git
controls and preserved settings remain at their original identities. Destination
namespace/content is rechecked around each move. Existing old payload is moved
to the private rollback directory; the proposal then moves into place. No source
file is encrypted in place, and no Git commit, push, merge, branch or worktree
operation is performed by these primitives.

## Retention, failure, and explicit recovery

Fresh success retains the entire previous managed payload outside the repository.
Restore rollback contains **plaintext and is sensitive**. Private results provide
locations and a plaintext flag for deliberate caller reporting; diagnostics never
emit paths, original names, key bytes, or content. There is no automatic retention
pruning. These primitives conservatively retain recovery directories/journals
and proposed data after failures too. Thread 07 adds internal successful-merge
cleanup: only the current operation's complete recorded workspace is eligible,
after durable publication and ownership release. It verifies the published
payload, terminal journal, container identities, complete namespaces and rollback
hashes, then rechecks each entry through anchored no-follow handles before
removal. Older workspaces and uncertain/modified data remain retained. Partial
cleanup or I/O failure produces a redacted warning without undoing publication.
If ownership-removal durability is unconfirmed, cleanup is skipped and rollback
remains available. Cleanup is best effort against same-authority writers;
there is no general retention-pruning command.

A normal failure attempts conservative recovery from the durable journal, rather
than trusting the last in-memory step. Interrupts attempt the same recovery and
then propagate. If rollback cannot complete, ownership remains and subsequent
writes are blocked. `_TransactionError.recovery_required` distinguishes blocked
recovery from a restored old payload; both outcomes are failures. The original
exception is kept as Python context while the displayed error is redacted.

Explicit recovery obtains exclusive OS ownership and validates bounded private
records, transaction ID, modes/owner, recorded ancestor/root/container identities,
original-observation digest, protected controls, and complete old/new payload
locations. Every old and proposed entry must occur exactly once in its allowed
location with matching hashes and identities. All these checks precede inverse
payload writes. Mirror recovery also authenticates complete old/proposed snapshots
with the selected key before inverse moves. Unexpected, missing, replaced or edited payloads prevent recovery;
no uncertain/user-modified data is deleted. Unfinished staging that never
received publication authorization is retained, and ownership is released only
if the original destination is unchanged.

Recovery returns published proposal entries to staging and restores old entries
from rollback. Every inverse rename is checked and journaled; interruption can
be retried. It removes only an empty destination root whose creation identity is
proven and whose original state was absent. All proposed bytes remain retained.
Ownership is removed only after the previous complete payload is demonstrably
restored and the terminal journal is durable. Malformed/incomplete ownership or
a missing initial journal cannot be guessed safe: all artifacts stay blocked
for deliberate maintainer inspection.

Consent is shared through `_confirm_action`: explicit yes is sufficient;
non-interactive mode cannot prompt or imply yes. Caller-provided prompts must be
terminal-aware and return the literal boolean `True`. Dry runs recheck observations
and pending ownership without invoking builders, verifiers or prompts, and create
no paths, locks, journals, logs, staging or rollback copies. Read-only validation
never recovers transactions.

## Guarantees and limits

Tests inject failure before/after every journal checkpoint and payload rename,
at every observed control write/open, directory creation, fsync, journal replace
and ownership removal, plus short writes, disk/access failures, rollback failure,
interrupts, process termination and competing processes. Tests use synthetic bytes
and temporary Git metadata, never real vaults or cloud access.

Multi-step publication is not universally atomic. It relies on local filesystem
rename/locking/fsync semantics; network filesystems and power-loss behavior need
separate validation. After durable payload publication and a durable terminal
journal, ownership unlink is the completion point. If the subsequent directory
fsync fails, the internal result carries a warning: lock removal durability is
unconfirmed, so ownership may reappear and require recovery after restart. The
complete new payload and retained old payload remain available.

Identity/hash rechecks detect ordinary changes on a best-effort basis. Locks
coordinate cooperating Obfuscidian processes, not unrelated editors or a hostile
process running with the same filesystem authority. Users should pause editing
and sync during writes/recovery. Root Git contents are preserved but not monitored
for internal Git activity. A journal and ownership record are local recovery
metadata, not independently authenticated backup-format data; an attacker able
to rewrite all private controls can falsify them. These primitives promise
conservative preservation/refusal, not guaranteed recovery or immunity to power
loss. Future orchestration must surface private locations, plaintext sensitivity,
durability warnings, and retained recovery requirements explicitly.

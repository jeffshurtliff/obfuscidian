# Obfuscidian implementation roadmap

**Approved planning baseline:** 3 October 2026

**Status:** Thread 01 complete, reviewed, and merged into `origin/main`.
Thread 02 — Configuration and keys — is complete, reviewed, and merged into
`origin/main`; issue #2 is closed and Linux CI passed on Python 3.12–3.14.
Thread 03 — Vault inventory and path preflight — is complete, reviewed, and
merged into `origin/main`; issue #3 is closed and Linux CI passed on Python
3.12–3.14. Thread 04 — Encrypted backup format — is complete, reviewed, and
merged into `origin/main`; issue #4 is closed and Linux CI passed on Python
3.12–3.14. Thread 05 — Safe publication and recovery — is complete, reviewed,
and merged/pushed into `origin/main`; issue #5 is closed and Linux CI passed on
Python 3.12–3.14. Thread 06 — Fresh backup — is complete, reviewed, and
merged/pushed into `origin/main`; issue #6 is closed and Linux CI passed on
Python 3.12–3.14. Thread 07 — Merge backup — is complete, reviewed, and
merged/pushed into `origin/main`; issue #7 is closed and Linux CI passed on
Python 3.12–3.14. Thread 08 — Read-only verification — is complete, reviewed,
and merged/pushed into `origin/main`; issue #8 is closed as completed and Linux
CI passed on Python 3.12–3.14. Thread 09 is complete, reviewed and merged/pushed
into `origin/main`; issue #9 is closed as completed. Linux CI passed on Python
3.12/3.13; Python 3.14 was canceled before execution due to runner availability,
a validation gap explicitly accepted by the maintainer for closure. Thread 10
is complete, reviewed and merged/pushed into `origin/main`; issue #10 is closed
as completed and Linux CI passed on Python 3.12–3.14.
Thread 11 is complete, reviewed and merged/pushed into `origin/main`; issue #11
is closed as completed and Linux CI passed on Python 3.12–3.14. Thread 12 is
complete, reviewed and merged/pushed into `origin/main`; issue #12 is closed
as completed. All nine Linux/macOS/Windows jobs passed on Python 3.12–3.14.
See the Thread 12 completion record below for evidence and retained limitations.
Threads 13–14 remain not started. See the Thread 11 completion record below. See the Thread 10
completion record below and Thread 09 completion record for evidence and limits.

**Intended first stable release:** `1.0.0` (current metadata: `1.0.0.dev0`).

**Codex model selection — maintainer confirmed 4 October 2026:** Use
`GPT-6.1 Sol` for all Obfuscidian project threads performed by Codex unless
the maintainer explicitly states otherwise. This is the maintainer-confirmed
model selection, not an inference from an app name or earlier headers. For
Python files changed by Codex, use
`Jeff Shurtliff (via GPT-6.1 Sol)` in `Last Modified`, retain `Created By`, and
update `Modified Date` to the current local date. An explicit model override
supersedes this default for the affected thread; do not update unrelated headers.

This is the authoritative implementation plan for the Python/Click Obfuscidian
CLI. [PLANS.md](PLANS.md) is the preserved original design brief; this roadmap
supersedes conflicting details there. [Root AGENTS.md](../AGENTS.md) governs all
agent participation. Future tool-specific companion instructions remain
secondary. Do not treat a task, CLI example, or validation command in this file
as implemented functionality.

## 1. Purpose, baseline, and decisions

Obfuscidian will make encrypted, reversible backups of Obsidian vaults suitable
for a user-managed private Git mirror. It will protect file contents and original
names while maintaining individual encrypted files, avoiding a monolithic
archive. Backup reads the origin without modifying it. Restore writes only to an
explicitly selected destination or a separate local Git restore worktree.

### Repository baseline

| Area | Observed state before implementation |
| --- | --- |
| Template | Simon Willison's `simonw/click-app` cookiecutter framework |
| Package | Root `obfuscidian/`; setuptools backend; version `1.0.0.dev0`; Python `>=3.10` |
| Entry points | `obfuscidian = obfuscidian.cli:cli` and `python -m obfuscidian` |
| CLI | Click group, version option, and placeholder `command` subcommand |
| Dependencies | `pyproject.toml` declares only Click; `requirements.txt` separately declares Click and cryptography floors |
| Tests | One template version test using deprecated `CliRunner.isolated_filesystem()` |
| CI | Linux-only tests for Python 3.10–3.14; docs/planning paths ignored |
| Publication | Template workflow publishes to PyPI when a GitHub release is created |
| Missing tooling | No Poetry lockfile, Ruff configuration, Sphinx project, contribution guide, or production encryption modules |
| Private material | `local/` is ignored; `local/vendor_docs/` was absent at review |

The planning review could not execute the baseline tests because the active
Python environment lacked pytest; it also lacked Click. No dependencies were
installed and no application tests passed as part of that review. Future agents
must establish and report their actual environment rather than inherit this
observation as a permanent condition.

### Confirmed maintainer choices

| Decision | Approved choice |
| --- | --- |
| Backup layout | Stable opaque file identifiers plus an encrypted path/metadata manifest |
| Git merge restore | Separate worktree and restore branch; restored changes remain uncommitted |
| Python tooling | Poetry, `src/` layout, Python 3.12+; initial validation on 3.12–3.14 |
| Default contents | All vault files, including attachments, hidden files, and `.obsidian`, subject to mandatory exclusions |
| Fresh replacement safety | Complete staging, confirmation or `--yes`, and retained local rollback copy |
| Large files | Bounded whole-file Fernet in v1; chunking deferred |
| Merge history | Retain backed-up files deleted or renamed in the origin |
| Git baseline | Require a clean origin checkout; default base branch `main` |
| Output privacy | Counts normally; relative paths only with explicit terminal/log options |

### Changes from the original brief

- A symmetric **secret key**, not an asymmetric private key, protects backups.
  Fernet uses AES-128-CBC and HMAC-SHA256 authentication; its 32-byte encoded key
  is not a selectable AES-256 encryption setting.
- Base64 alone offers no secrecy. Do not Base64-encode names and then use Fernet
  tokens as filenames: randomized tokens destabilize incremental backups, and
  their expansion can exceed filesystem component limits.
- Names and directory structure live in the encrypted manifest. Physical mirror
  folders do not reproduce the source hierarchy. No inside-out source renaming
  is needed, and no backup operation renames or overwrites origin files.
- Fresh operations stage and validate first. They do not delete existing data
  before encryption/decryption succeeds. Unmanaged mirror content causes refusal.
- Merge restore creates a separate worktree rather than switching the live vault.
  `--worktree` means the new restore output location, not an arbitrary override
  of the origin Git working tree. `--base-branch` makes the restore base explicit.
- Relative key paths resolve from the current working directory, not implicitly
  from the home directory. Alias-only lookup still defaults to the home directory.
- Explicitly invalid configuration fails without falling back or prompting for
  a different key. Alias prompting is reserved for an absent key selector.
- Normal output omits paths. Error diagnostics should identify actionable options
  and counts without leaking vault names into unattended logs.

### Treatment of the concept scripts

| Reference | Useful concept | Production limitations |
| --- | --- | --- |
| [example-file-name-obfuscation-concept.py](example-file-name-obfuscation-concept.py) | Reversible URL-safe Base64 and padding | Encoding is not encryption; name encoding is superseded by manifest-based names |
| [example-encrypt-base64-to-base64.py](example-encrypt-base64-to-base64.py) | Fernet byte inputs, tokens, and decryption | Extra name Base64 is unnecessary; each encryption generates a fresh token |
| [example-encrypt-decrypt-concept.py](example-encrypt-decrypt-concept.py) | Key generation and basic file encryption | Encrypts in place, only handles two extensions, can overwrite a key, and catches errors while continuing |

Keep these scripts as historical concept references unless a later task requests
changes. Never run the in-place example against actual vaults or copy its unsafe
behavior into the application.

## 2. Architecture, data contract, and security

### Target package boundaries

Thread 01 moves the package to `src/obfuscidian/` without changing entry-point
names. Subsequent threads add focused modules as needed:

- `cli.py`: Click commands, prompts, help, and rendering; `__main__.py`: module entry point.
- `config.py`, `keys.py`, `constants.py`, `errors.py`: option resolution, secure key I/O,
  shared limits/names, and typed operational errors.
- `inventory.py`, `paths.py`: deterministic traversal, exclusions, identity and path safety.
- `crypto.py`, `manifest.py`: Fernet operations, backup schema, integrity, and compatibility.
- `transactions.py`, `backup.py`, `restore.py`, `git_restore.py`: staging/recovery,
  backup/restore orchestration, and isolated Git workflow.

These are internal boundaries; the CLI is the initial public interface. Avoid a
large orchestration module, custom crypto, or a general-purpose framework.
Shared constants are centralized and imported as `const` where appropriate.

### V1 mirror format

```text
mirror/
  .git/                     # or a legitimate root Git metadata file; never encrypted
  .gitignore                # existing mirror configuration; never replaced
  .obfuscidian/
    manifest.obf            # Fernet-encrypted UTF-8 JSON manifest
    objects/
      <opaque-id>.obf        # one complete Fernet token per included file
```

The dedicated `.obfuscidian/` subtree is application-managed. Outside it, only
root `.git` and `.gitignore` are allowed during v1 mirror publication. Unknown
root files or unknown managed-tree entries cause refusal with guidance to move
them outside the mirror; `--yes` cannot override this validation. Future support
for additional mirror control files belongs in a separately approved task.

Thread 04 specifies this schema in the [v1 format guide](../docs/FORMAT.md)
and freezes it with synthetic compatibility fixtures before backup commands
use it:

| Manifest field | Contract |
| --- | --- |
| `format_version` | Integer `1`; reject unknown versions |
| `vault_id` | Random identifier for the mirror lineage; preserve across updates |
| `snapshot_id` | Random identifier for this logical publication; unchanged on a no-op |
| `created_at` | UTC publication timestamp inside the encrypted manifest |
| `directories` | Records of normalized relative paths and integer modification times in nanoseconds; include empty directories |
| `files` | Records containing `path`, `object_id`, `size`, `mtime_ns`, `plaintext_sha256`, and `ciphertext_sha256` |

Use forward slashes in manifest relative paths and lossless UTF-8 names; do not
store absolute source paths, usernames, keys, plaintext hashes, or file listings
outside the encrypted manifest. Sort records deterministically. Object IDs are
32 lowercase hexadecimal characters generated from secure randomness; handle
collisions by regenerating before any write. Object filenames contain only the
ID and `.obf`; Fernet tokens keep their standard encoding and padding. Modification
times are signed integer nanoseconds so pre-epoch timestamps are not rejected
solely for being negative; validate target filesystem representability on restore.

Validate schema types, bounds, duplicate JSON keys, duplicate paths/IDs, file vs
directory conflicts, missing parent records, unsafe components, and referenced
objects. Verify each object's ciphertext hash, Fernet authentication, plaintext
size, and plaintext hash. Hashes stored in the authenticated encrypted manifest
bind a path to its intended object; independently valid tokens must not be
interchangeable. Reject unexpected object files in v1 rather than restoring them.

There is no token TTL for archival backups. A lost manifest prevents path
recovery; it must be backed up with the objects. A lost key prevents decryption;
there is no reset or recovery bypass. Do not mix keys within a mirror. An
existing mirror must authenticate with the selected key before it is updated,
including fresh mode; rekeying is deferred.

For unchanged content, retain both object ID and exact ciphertext. Metadata-only
changes update the manifest without re-encrypting the object. Changed files at
the same path keep their ID but receive a new token in staging. Renames are new
paths; v1 does not infer renames by content equality. Thus merge can retain both
the stale old path and the new path. Reuse ciphertext only after validating its
old manifest/object integrity. No-op detection compares logical records and
does not generate a new timestamp, snapshot ID, manifest, lock, or rollback copy.
It also does not create or append optional log files; report a no-op through
terminal output only. Delay log creation until a write operation is necessary.

### Resource and restore contract

- The v1 encrypted size cap is `50 * 1024 * 1024` bytes for every object and the
  manifest. No command-line bypass is planned. An exactly-at-cap valid token is
  allowed; a larger token fails before destination publication.
- Account for Fernet overhead before allocation/writing: for `n` plaintext bytes,
  padded AES content is `16 * (floor(n / 16) + 1)` bytes; the encoded token size
  is `4 * ceil((57 + padded_content) / 3)` bytes. Test the estimate against real
  tokens at block/Base64 boundaries. Check actual serialized manifest size too.
- Process one file at a time and bound token reads before decryption; memory
  usage can still be several times one file's size. Catch allocation/I/O failures
  without publishing partial output. Do not silently omit oversize attachments.
- Restore exact file bytes, names, relative structure, and empty directories.
  Preserve file/directory modification times where supported, setting directory
  times after child writes. Unsupported timestamp preservation is a reported
  warning; required content failure is an error.
- Do not promise original ownership, ACLs, extended attributes, executable modes,
  or full cross-platform metadata fidelity. Create plaintext output with
  restrictive permissions where supported rather than importing unsafe modes.
- Reject paths unrepresentable on the target filesystem, including case or
  normalization collisions, Windows reserved components, and length limits.
  Do not silently rename, truncate, or normalize restored names. Validation
  considers the actual target platform; a valid source name may be unrestorable
  on another platform and must be reported before destination changes.

### Transaction and preservation requirements

Before writes, resolve paths and validate permissions, identity, overlap, keys,
limits, existing format, pending transactions, and sufficient staging/rollback
space. Reject same paths, either-direction nesting, roots as replacement targets,
and sources/destinations reached through symlinks or junctions. Inspect links
without following them. Non-excluded symlinks, junctions, and special files in
vault content cause errors; mandatory excluded Git metadata is never traversed.

Require an existing source directory. A new destination may have only its final
component missing; parents must exist. Inventory included entries in a defined,
case-sensitive ascending relative-path order, independent of locale. Read files
as bytes, capture identity/size/time before and after reading, and re-inventory
before publication to detect additions, deletions, or changes. Abort on detected
changes. This is best-effort detection, not a filesystem-wide atomic snapshot;
users should pause editing, Obsidian sync, and other writers during operations.

Use private same-filesystem staging and rollback locations outside both source
and destination. Default to uniquely named siblings of the destination; if the
destination is itself a Git worktree or inside a repository, choose an ancestor
location outside all relevant Git worktrees on the same filesystem. Refuse if a
safe writable location cannot be established; never place plaintext staging,
rollback data, logs, or journals where a routine mirror commit can include them.

Transactions must have exclusive destination ownership, recorded filesystem
identities, and a private durable journal. Revalidate identity/content before
publication; locking prevents competing Obfuscidian processes, not unrelated
editors. After staging, verify the entire proposed result. Replace the managed
mirror tree as a unit with recoverable rename steps. Restore publication also
uses staged data and journaled replacement of managed destination entries while
leaving root Git metadata in place. Do not claim multi-step replacement is
universally atomic or immune to power loss.

Fresh replacement retains the previous destination payload as a rollback copy
outside the destination after success. Preserve root `.git` and `.gitignore`
in place; with `--preserve-config`, leave root `.obsidian` in place too. Protect
nested `.git` metadata and refuse a replacement that would remove a nested
repository rather than silently deleting it. Other old fresh-restore content
belongs in the rollback copy. Report rollback locations interactively with an
explicit explanation that restore rollback data is plaintext and sensitive.
No automatic retention pruning is included. Merge retains previous state until
publication succeeds, then may remove only its own temporary recovery data.

On normal failures, roll back to the previous complete state when possible. On
process termination or incomplete recovery, refuse subsequent writes, identify
the pending transaction, and offer explicit recovery through `--recover` on the
same write command. Recovery conservatively restores the previous complete
state before retrying the requested operation; it must not delete uncertain or
user-modified artifacts. Non-interactive recovery requires `--yes`. Verification
and dry run report pending transactions but never recover them. Keep journals
and rollback copies until recovery is demonstrably complete. Never silently
remove stale locks merely because their timestamp is old.

### Threat model and limits

Fernet protects the secrecy and authenticity of stored content with the key;
the manifest protects original names and hierarchy. Base64 is only encoding.
Fernet timestamps are visible, and whole-file encryption requires data in
memory. These are properties of the chosen recipe, not bugs fixed by padding
stripping or another Base64 layer. See the [Fernet reference](https://cryptography.io/en/50.0.2/fernet/).

An observer can still learn encrypted sizes, object counts, token times, and
change patterns. Encryption does not protect an unlocked endpoint, a stolen
key, deletion of the backup, or replay of an older valid backup. There is no
trusted external freshness anchor in v1. Integrity verification must not claim
to detect rollback of a complete valid historic snapshot.

Private repository status is the user's responsibility. Obfuscidian does not
commit, push, inspect remote privacy, or interpret mirror `.gitignore` settings.
The user must ensure all managed backup files are tracked together. Git history
can grow rapidly with encrypted binary changes; individual-file encryption does
not remove repository limits. GitHub currently warns above 50 MiB and blocks
regular Git files above 100 MiB; the chosen cap avoids that warning boundary.
Other providers can impose stricter limits. See [GitHub's size guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

Include key custody and separate offline key backup guidance. Never save the key
in either vault or its cloud repository. Changing a key later cannot revoke
access to old Git history encrypted under the former key.

## 3. CLI and workflow contract

### Commands and option placement

Global options are `--help` and `--version`. Operation options belong after the
subcommand; `fresh`/`merge` is one required positional choice rather than another
Click subgroup. Preserve these environment variables:

| Variable | Meaning |
| --- | --- |
| `OBFUSCIDIAN_KEY_PATH` | Complete key filename/path |
| `OBFUSCIDIAN_KEY_ALIAS` | Alias for `obfuscidian-ALIAS.key` |
| `OBFUSCIDIAN_KEY_DIR` | Alias lookup directory; defaults to home |
| `OBFUSCIDIAN_ORIGIN_VAULT` | Plaintext backup source or fresh restore destination; repository for merge restore |
| `OBFUSCIDIAN_MIRROR_VAULT` | Encrypted backup destination or restore/verification source |

| Command | Planned options |
| --- | --- |
| `keygen` | `--alias`, `--dir`, `--non-interactive`, `--dry-run`, output/logging options |
| `shroud fresh\|merge` | `--origin`, `--mirror`, key options, repeatable `--exclude`, shared write/output options |
| `unshroud fresh\|merge` | `--origin`, `--mirror`, key options, `--preserve-config`, shared write/output options |
| `unshroud merge` only | `--gitdir`, `--worktree`, `--branch`, `--base-branch` |
| `verify` | `--mirror`, key options, `--non-interactive`, terminal output options; always read-only |

Key options are `--key`, `--alias`, and `--keydir`. Shared write options for
shroud/unshroud are `--non-interactive`, `--yes`, `--dry-run`, and `--recover`.
Keygen has no `--yes` or `--recover`; it cannot overwrite a key. Output options
are `--verbose`, `--log-file`, and `--log-paths` where
writes are permitted. Reject options unsupported by a command/mode instead of
silently ignoring them; reject `--recover` with `--dry-run`.

Dry run performs read-only configuration, inventory, integrity, and space
estimation; it writes no keys, destinations, locks, logs, staging, rollback, or
Git state. It cannot guarantee later source stability or successful allocation.
Reject `--log-file` with dry run and on `verify` to preserve their read-only
contract. `--log-paths` requires `--log-file`. Missing information in a dry run
can prompt interactively; it must fail in non-interactive mode.

### Key and path resolution

1. CLI `--key` selects a path and ignores environment key selectors. Reject
   simultaneous CLI `--alias` or `--keydir`.
2. CLI `--alias` selects alias lookup and ignores environment `KEY_PATH`/`KEY_ALIAS`.
   Use CLI `--keydir`, then environment `KEY_DIR`, then home for its directory.
3. Without a CLI selector, environment `KEY_PATH` wins over environment alias.
   A CLI `--keydir` with environment `KEY_PATH` is ambiguous and must fail; with
   an environment alias it overrides the environment directory. A directory
   without any alias/path may accompany an interactive alias prompt.
4. With no path or alias, prompt for an alias only in an interactive terminal;
   otherwise fail. Missing/invalid explicitly selected key files always fail
   without trying a different key. Loading never generates a replacement key.

CLI vault paths override their environment equivalents even when invalid. Expand
`~` using the home directory and resolve relative paths from the current working
directory. Shell variable substitution belongs to the shell; the application
does not interpolate arbitrary `$NAME` or `%NAME%` strings in supplied paths.
Retain protected path identities for later rechecks, not just string comparisons.

For keygen, resolve alias from CLI then environment alias; resolve directory
from CLI `--dir`, environment `KEY_DIR`, then home. Environment `KEY_PATH` does
not determine a generation output filename. Alias characters are ASCII letters,
digits, and hyphens, with length capped at 64. When no alias exists, interactive
input can be empty to select local-time `YYYYMMDD-HHmmss`; non-interactive mode
requires an explicit alias. Explicit empty aliases are invalid.

Key output directories must already exist. Create `obfuscidian-ALIAS.key`
exclusively, with mode `0600` on POSIX and the strongest practical local access
restriction available on Windows; document Windows ACL limitations. Never
overwrite a collision, including a timestamp collision. Validate the full
Fernet key without printing it; warn about insecure permissions when they can
be assessed. Do not add a force-overwrite option.

### Inclusion and mode semantics

Scan all file types as bytes. Mandatory exclusions cannot be overridden:
`.git` components (directory or Git metadata file), `.gitignore` files, and
`obfuscidian-*.key` files at any depth. Selected key paths inside either vault
are invalid even though generated filenames would otherwise be excluded.
Other secrets cannot be reliably identified by filename; document user
responsibility and explicit exclusions. Do not parse Markdown, rewrite links,
load Obsidian plugins, or require `.obsidian` to exist for a vault to be valid.

`--exclude` operates on original relative paths before obfuscation. Use a
documented, case-sensitive component glob: `*` and `?` match inside one
component, bracket classes match one character, and a standalone `**` component
matches zero or more components. No negation/re-inclusion is supported. A
trailing slash matches directories and prunes their descendants. Reject
absolute patterns, `..`, and backslashes; forward slashes make patterns portable.
Examples: `'.obsidian/'`, `'attachments/**'`, `'**/*.tmp'`, and `'**/.DS_Store'`.
Report exclusion counts. V1 restore has no selective `--exclude` option.

| Operation | Data semantics and confirmation |
| --- | --- |
| `shroud fresh` | Current included inventory only; reuse validated unchanged objects where possible; replace previous managed snapshot after confirmation when it changes existing data; retain old snapshot outside mirror |
| `shroud merge` | Union old manifest with current included paths; update matches, add new paths, retain absent/excluded old paths; confirm when replacing existing file contents; a new mirror can be initialized |
| `unshroud fresh` | Reconstruct complete snapshot; replace existing destination payload after confirmation; preserve root Git controls and optionally `.obsidian`; retain old destination outside it |
| `unshroud merge` | Overlay backup files onto a separate Git worktree from the chosen base; retain base-only files; require clean origin and leave all changes uncommitted |

Fresh snapshots omit excluded entries; excluded existing plaintext destination
files are not automatically preserved, except root Git controls and the explicit
configuration preservation option. Merge exclusion does not purge historic data.
Fresh or merge stale-file behavior must be visible in help/examples so users
understand when deleted notes can reappear. A metadata-only change counts as a
logical update but does not require a content-overwrite confirmation.

Confirmations occur after read-only preflight and before staging/mutation. A
non-terminal input stream does not trigger interactive prompts. `--yes` waives
only the stated replacement/recovery prompt; it never bypasses safety checks or
overwrites a key. User refusal exits without mutation. New empty destinations
need no destructive confirmation; read-only dry runs never need `--yes`.

### Git merge restore details

Require Git on PATH and an existing local non-bare origin repository with at
least one commit. Default discovery requires the origin to be its worktree root.
`--gitdir` permits an explicitly selected Git directory only after it is
validated as belonging to that origin; it is not a second output path. Refuse
unsupported submodule/nested-repository layouts and overlapping output locations.

Require a clean origin index and working tree and no untracked vault files;
also detect ignored user vault files rather than treating ordinary Git status
as sufficient. Refuse pending merge/rebase operations. Resolve `--base-branch`
to an existing local branch, default `main`; do not infer `master`, fetch, reset,
stash, initialize a repository, or silently switch bases.

Default branch suffix: `restore-YYYYMMDD-HHmmss`; `--branch` supplies a suffix
under the mandatory `obfuscidian/` prefix. Validate the complete branch using
`git check-ref-format --branch`, not a simplistic allowed-character regex.
Refuse an existing branch or timestamp collision; never reset it.

`--worktree` selects a new, non-existing restore directory with an existing
parent. Without it, choose a sibling of the origin named
`<origin-name>-restore-YYYYMMDD-HHmmss`. Validate and stage all backup contents
before creating the branch/worktree. Preserve the new worktree's `.git` metadata
file and base `.gitignore`. `--preserve-config` leaves the base branch's
`.obsidian` contents unchanged; absent base configuration remains absent.

Print the branch/worktree location and manual `git status`, `git add`, `git commit`,
and later merge guidance using correctly quoted paths. Warn that restored files
ignored by the base `.gitignore` need explicit review and may need `git add -f`;
never stage them automatically. Report that base-only files remain and the
result is an additive restore, not an exact backup snapshot. Changes are not
mergeable until the user commits them. Never open plaintext remotes or push.

On failure, clean up only branch/worktree artifacts created by that operation
and only when they contain no user changes; otherwise retain them and provide
recovery guidance. Leave the original checkout, branch, index, and Git controls
unchanged. Actual Git integration tests use temporary repositories with
synthetic commits and disabled external hooks/configuration.

### Output, logging, and exit codes

- Normal output includes operation/mode, counts, byte totals, progress, and
  summaries; it omits plaintext relative paths. Use stderr for warnings/errors.
- `--verbose` permits relative paths in terminal output. Never print key bytes
  or file contents, even at debug level. Sanitize terminal control characters in
  names; path detail must not reach logs by accident through exception strings.
- `--log-file` writes optional redacted operational records outside both vaults,
  Git worktrees, staging, and rollback trees. Require an existing parent, refuse
  links, create restrictive permissions, and validate before mutation. Appending
  to an explicit existing regular log file is allowed. `--log-paths` explicitly
  permits relative paths in that log; absolute identifying paths stay redacted.
- Keygen output paths and completed restore/worktree/rollback locations are
  intentional interactive handoff exceptions to counts-only progress. Redact
  them in unattended output unless verbose was explicitly selected; private
  recovery records retain actionable locations without putting them in Git.
- An explicitly requested operational log may record a no-op; vault bytes/times
  and transaction artifacts remain unchanged. Dry run and verify never write logs.
- Suppress animated progress when output is redirected. Escape display values;
  failure summaries state what was preserved and whether recovery is needed.

| Exit code | Meaning |
| --- | --- |
| `0` | Successful operation, verification, dry run, or no-op |
| `1` | Operational/integrity/I/O failure, declined confirmation, or incomplete recovery |
| `2` | Usage/configuration failure (missing/invalid option, unsafe path, unsupported combination) |
| `130` | Keyboard interrupt after attempted cleanup/recovery |

Interruption and partial failure never count as success. If rollback fails, keep
the original error and report recovery requirements without sensitive payloads.

### Examples and remaining planned commands

The key directory exists already; paths and aliases below are placeholders.
Keygen, `shroud fresh|merge`, and read-only `verify` are implemented locally.
`unshroud fresh` and `unshroud merge` are implemented, reviewed and merged/pushed.

```sh
obfuscidian keygen --alias primary --dir ./keys --non-interactive
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --dry-run
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --yes
obfuscidian shroud merge --origin ./vault --mirror ./vault-encrypted --alias primary --exclude '**/*.tmp'
obfuscidian verify --mirror ./vault-encrypted --alias primary --non-interactive
obfuscidian unshroud fresh --origin ./restored-vault --mirror ./vault-encrypted --alias primary --preserve-config --yes
obfuscidian unshroud merge --origin ./vault --mirror ./vault-encrypted --alias primary --base-branch main --worktree ./vault-review
```

The alias examples assume a separately generated key in the home directory;
the first three examples select their explicit `./keys` file. PowerShell/cmd
activation and environment-variable examples belong in the later usage docs.
Both installed console and module entry points must offer identical behavior.

## 4. Implementation threads

All fourteen threads initially started **not started**; the index below records current status. 
Each is a bounded implementation request, not permission to perform the entire roadmap. No 
commits, publication, or PRs are implied. Update status only after acceptance criteria are met.

### Common thread contract

- Inspect root agent/contributor instructions and the dependency threads first.
- Read the linked GitHub issue and dependency issues before implementation.
  Keep that issue updated with a start comment, verified checklist progress,
  meaningful blockers/decisions, and a public-safe handoff. Routine updates
  to the existing issue are part of authorized work on that thread; follow
  [AGENTS.md issue-update guidance](../AGENTS.md#roadmap-issue-updates).
  Synchronize issue evidence with the index, thread status, and handoff record.
  Leave partial work and pending maintainer review open; close only after
  acceptance criteria are met and completion is approved or closure requested.
  If GitHub access fails, record the unsent update here and report the limitation.
- Implement the listed subtasks, tests, help, and any documentation necessary
  to describe that increment. Do not expose an unsafe half-implemented command.
- Follow the centralized contracts above; a necessary deviation is a maintainer
  decision to record before dependent implementation, not an undocumented guess.
- Once tooling exists, run `poetry check --lock --strict`,
  `poetry run ruff check .`, `poetry run ruff format --check .`,
  `poetry run pytest -q`, and `git diff --check`. Add the thread-specific checks
  below. Do not claim commands ran when dependencies are absent.
- Update the changelog after Thread 01 establishes it. Keep docs/examples marked
  planned until their commands work. End with deliverables, evidence, limitations,
  Git status, and the next eligible thread. Leave changes uncommitted.

### Thread index and dependencies

| ID | Increment | Dependencies | GitHub issue | Status |
| --- | --- | --- | --- | --- |
| 01 | Project foundation | None | [#1](https://github.com/jeffshurtliff/obfuscidian/issues/1) | Complete |
| 02 | Configuration and keys | 01 | [#2](https://github.com/jeffshurtliff/obfuscidian/issues/2) | Complete |
| 03 | Vault inventory and path preflight | 02 | [#3](https://github.com/jeffshurtliff/obfuscidian/issues/3) | Complete |
| 04 | Encrypted backup format | 03 | [#4](https://github.com/jeffshurtliff/obfuscidian/issues/4) | Complete |
| 05 | Safe publication and recovery | 04 | [#5](https://github.com/jeffshurtliff/obfuscidian/issues/5) | Complete |
| 06 | Fresh backup | 05 | [#6](https://github.com/jeffshurtliff/obfuscidian/issues/6) | Complete |
| 07 | Merge backup | 06 | [#7](https://github.com/jeffshurtliff/obfuscidian/issues/7) | Complete |
| 08 | Read-only verification | 04; may precede 05–07 | [#8](https://github.com/jeffshurtliff/obfuscidian/issues/8) | Complete |
| 09 | Fresh restore | 05, 07, 08 | [#9](https://github.com/jeffshurtliff/obfuscidian/issues/9) | Complete; 3.14 CI gap accepted |
| 10 | Git merge restore | 09 | [#10](https://github.com/jeffshurtliff/obfuscidian/issues/10) | Complete; reviewed/merged; Linux CI passed |
| 11 | CLI polish | 10 | [#11](https://github.com/jeffshurtliff/obfuscidian/issues/11) | Complete; reviewed/merged; Linux CI passed |
| 12 | Cross-platform hardening | 11 | [#12](https://github.com/jeffshurtliff/obfuscidian/issues/12) | Complete; reviewed/merged; nine-job OS/Python matrix passed |
| 13 | Documentation and contribution guidance | 12; incremental docs accompany earlier threads | [#13](https://github.com/jeffshurtliff/obfuscidian/issues/13) | Not started |
| 14 | Release preparation | 13 | [#14](https://github.com/jeffshurtliff/obfuscidian/issues/14) | Not started |

All fourteen issues are assigned to `jeffshurtliff` and belong to the
[v1.0.0 milestone](https://github.com/jeffshurtliff/obfuscidian/milestone/1).
Issue numbers are tracking identifiers; creating them does not start or
complete implementation. Existing repository labels categorize each thread.

The thread-specific subtasks and handoff prompts follow below.

### Thread 01 — Project foundation

**GitHub issue:** [#1](https://github.com/jeffshurtliff/obfuscidian/issues/1)

**Goal/deliverable:** An installable Poetry/src-layout package with reproducible
developer tooling and passing entry-point tests; no backup functionality yet.

**Depends on:** None.

**Status:** Complete. Maintainer reviewed, committed, and merged the foundation
into `origin/main`; issue #1 is closed as completed.

Local acceptance evidence is recorded in the initial handoff below, followed by
the maintainer-approved completion record. Thread 02 status and evidence follow below.

1. Migrate packaging to Poetry/poetry-core while retaining PEP 621 metadata,
   static `1.0.0.dev0`, license, console entry point, and module invocation.
   Move the package to `src/obfuscidian/`; change Python minimum to 3.12 and
   initially test 3.12–3.14. Generate the lock through Poetry.
2. Make `pyproject.toml` authoritative. Carry forward reviewed runtime floors
   `click>=8.5.0` and `cryptography>=50.0.2` or newer justified floors. Remove the
   manually maintained `requirements.txt` and update its references. Establish
   `dev` tools for pytest, coverage, Ruff, Bandit, and Twine, with docs tools
   deferred to Thread 13. Configure the agreed Ruff style.
3. Remove the placeholder command; retain useful help/version behavior. Move
   tests into `tests/unit/` and `tests/integration/`, use absolute `tmp_path`
   fixtures, and verify the product name in version output. Establish
   `docs/CHANGELOG.md` with `[Unreleased]` and update development instructions.
4. Update the test workflow for Poetry on Linux/Python 3.12–3.14, keeping broader
   OS coverage for Thread 12. Inspect packaging inclusion rules so the sdist and
   wheel include required package/license metadata and exclude private/scratch
   content. Do not activate or trigger the publication workflow.

**Acceptance/demo:** A clean developer install runs `obfuscidian --help`,
`obfuscidian --version`, and `python -m obfuscidian --help`; no placeholder
command remains. Both package artifacts work outside the checkout and contain
no `local/` material. Record what is already automated versus deferred.

**Validation:** Common checks; `poetry build`; strict Twine checks of just the
new candidate wheel/sdist; install each in separate temporary environments with
dependencies and run console/module help/version there. Check the changelog and
README links. Do not use an old accumulated `dist/` directory as validation.

**Copy-ready prompt:**

> Read AGENTS.md and dev/IMPLEMENTATION_PLAN.md. Implement only Thread 01 and its
> four subtasks, following the approved foundation and packaging contracts. Add
> installation/entry-point tests, validate fresh wheel and sdist artifacts, and
> update the roadmap status with actual evidence. Do not implement keygen or
> backup features, commit, create a PR, or publish. Leave changes for review.

### Thread 02 — Configuration and keys

**GitHub issue:** [#2](https://github.com/jeffshurtliff/obfuscidian/issues/2)

**Goal/deliverable:** Safe working `keygen` and reusable configuration/key
resolution, without a functional vault write command.
**Depends on:** 01. **Status:** Complete. Maintainer reviewed, committed, and
merged the implementation into `origin/main`; issue #2 is closed as completed.
Linux CI passed on Python 3.12–3.14. Local acceptance evidence, platform limits,
and the completion record are preserved in the handoff below. Thread 03 is
also complete following maintainer review and merge.

1. Add shared constants, operational/configuration errors, and independent key
   and path resolution helpers. Implement the documented CLI/environment matrix
   and explicit-invalid-value refusal; use controlled test environments.
2. Add keygen alias/directory validation, local timestamp prompt default,
   exclusive secure key creation, valid key loading, and clear custody guidance.
   Implement keygen dry run and non-interactive behavior without key disclosure.
3. Reject selector conflicts, missing parents, link targets, and existing key
   files. Assess POSIX permissions and document Windows access limitations;
   preserve existing key bytes on every failure.
4. Add Click command/help and tests for prompts, EOF, alias edge cases, quoted
   relative/home paths, environment precedence, invalid keys, collisions,
   permission failures, and no-mutation dry runs.

**Acceptance/demo:** Generate a synthetic key in a temporary existing directory,
load it for an in-memory authenticated round trip, and prove a second generation
cannot overwrite it. No key bytes appear in captured output or errors.

**Validation:** Common checks; targeted config/key unit and CLI tests; POSIX
permission assertions guarded by platform; a manual dry run that creates no file.

**Copy-ready prompt:**

> Read the project instructions and roadmap; confirm Thread 01 is complete.
> Implement only Thread 02: configuration resolution and secure keygen/loading.
> Follow the precedence, alias, permission, and no-overwrite contracts; test
> prompts and non-interactive/dry-run behavior with temporary synthetic keys.
> Update status and help, report checks, and leave changes uncommitted.

### Thread 03 — Vault inventory and path preflight

**GitHub issue:** [#3](https://github.com/jeffshurtliff/obfuscidian/issues/3)

**Goal/deliverable:** A deterministic, read-only inventory usable by backup and
restore planning, with exclusion and filesystem safety tests.
**Depends on:** 02. **Status:** Complete. Maintainer reviewed, committed, and
merged the implementation into `origin/main`; issue #3 is closed as completed.
Linux CI passed on Python 3.12–3.14. See the handoff and completion records for
executed validation and platform limits.

1. Add typed inventory records for included relative files/directories, sizes,
   times, and filesystem identities; include empty directories and all binary
   types. Reject unsupported links/special files without traversing them.
2. Implement mandatory exclusions and the component-glob contract; prune
   excluded directories before descending. Include target/path checks for
   roots, overlaps, keys inside vaults, missing parents, and unmanaged mirrors.
3. Add Fernet size estimation, manifest-bound accounting hooks, staging space
   estimation, file read stability checks, and post-read inventory comparison.
4. Add representative synthetic fixtures for Unicode, hidden/config files,
   binary and zero-byte files, names with control characters, exclusions,
   nesting, junction/symlink cases, and source changes during scanning.

**Acceptance/demo:** Inventory a fixture vault twice with identical sorted
results and no writes; show included/excluded totals. Abort on overlap, a
non-excluded link, oversize content, or a detected inventory change.

**Validation:** Common checks; targeted inventory/path tests; compare filesystem
trees and file hashes before/after read-only inventory; platform-specific cases
must explicitly skip only where the host cannot create the fixture.

**Copy-ready prompt:**

> Implement only Thread 03 after checking its dependencies. Build deterministic
> read-only inventory, approved exclusion matching, size estimation, and path
> safety helpers. Use synthetic fixtures to prove source preservation, empty
> directory/binary inclusion, and failure on unsafe or changing paths. Do not
> expose backup writing yet. Update the roadmap and leave work uncommitted.

### Thread 04 — Encrypted backup format

**GitHub issue:** [#4](https://github.com/jeffshurtliff/obfuscidian/issues/4)

**Goal/deliverable:** A frozen v1 format with in-memory/file-helper round trips
and compatibility fixtures, ready for orchestration.
**Depends on:** 03. **Status:** Complete. Maintainer reviewed, committed, and
merged/pushed the implementation into `origin/main`; issue #4 is closed as
completed. All four subtasks and acceptance criteria are met. Linux CI passed
on Python 3.12–3.14. See the handoff and completion records for validation and
platform limits.

1. Implement the schema and managed layout in Section 2, bounded parsing,
   canonical sorting, validation of paths/IDs/types, and format-version errors.
   Introduce format-version constants independent of the package version.
2. Implement full-byte Fernet object/manifest encryption and decryption, ID
   generation, archival decryption without TTL, and encrypted hash binding.
   Confirm ciphertext estimation at empty/block/Base64 boundary sizes.
3. Implement reusable complete-mirror verification and validated object reuse.
   It reads only, checks every reference and unexpected object, and returns
   structured results suitable for both CLI verification and safe restoration.
4. Add immutable synthetic v1 compatibility fixtures and adversarial tests:
   wrong key, changed tokens, missing/truncated objects, token swaps, malformed
   JSON, duplicate IDs/paths/keys, traversal/absolute paths, and unknown versions.
   Keep only clearly synthetic fixture keys; never copy a real backup.

**Acceptance/demo:** Encode a small mixed-content vault into temporary v1
objects/manifest and reconstruct its full content exactly. Every tested
authentication/path/format failure occurs before a destination write.

**Validation:** Common checks; compatibility and crypto tests;
`poetry run bandit -r src/obfuscidian`; review that neither names nor plaintext
hashes are exposed outside the encrypted manifest.

**Copy-ready prompt:**

> Implement only Thread 04, using the approved v1 schema, limits, and flat opaque
> object layout. Add complete read-only validation and synthetic compatibility
> fixtures, including object substitution and hostile path tests. Document the
> format and threat limits; do not improvise crypto or expose write commands.
> Record validation and status, and leave changes uncommitted.

### Thread 05 — Safe publication and recovery

**GitHub issue:** [#5](https://github.com/jeffshurtliff/obfuscidian/issues/5)

**Goal/deliverable:** Tested transaction primitives that preserve the previous
complete destination during errors; public vault write commands remain gated.
**Depends on:** 04. **Status:** Complete. The maintainer reviewed, committed,
and merged/pushed the implementation into `origin/main`; issue #5 is closed as
completed. All four subtasks and acceptance criteria are met. Linux CI passed
on Python 3.12–3.14. See the handoff/completion records and
[transaction guide](../docs/TRANSACTIONS.md) for evidence and platform limits.
Thread 06 is complete; see its later completion record for merge/CI evidence.

1. Implement safe same-filesystem staging/rollback location selection outside
   vaults and Git worktrees, permission/space preflight, exclusive ownership,
   identity rechecks, and private durable journal lifecycle.
2. Add mirror managed-tree publication and restore payload replacement without
   moving root Git metadata. Retain successful fresh rollback copies and refuse
   unmanaged mirrors, nested repositories, or unexpected destination changes.
3. Implement conservative recovery of incomplete transactions and shared
   confirmation/non-interactive handling. Never infer that an old lock is safe
   to delete; verify ownership and transaction state before explicit recovery.
4. Inject failures at every journal/rename/write boundary, including inability
   to roll back. Test a competing process, interrupt, disk-full/permission error,
   changed destination, preserved `.git` file/directory and `.gitignore`, and
   rollback confidentiality/location. Use process isolation where needed.

**Acceptance/demo:** A failed synthetic replacement either restores the previous
complete payload or leaves a clearly blocked, recoverable state with its data
retained. Fresh success keeps the old payload outside the repository. A dry run
creates no transaction artifacts. Document limits of crash/power-loss guarantees.

**Validation:** Common checks; transaction fault-injection/integration tests;
filesystem identity/hash assertions for protected data; interrupted-process
recovery tests. No real vault or cloud access.

**Copy-ready prompt:**

> Implement only Thread 05 after format validation is available. Build staging,
> lock/journal, publication, retained fresh rollback, and explicit recovery
> primitives. Exercise every failure boundary with synthetic destinations and
> temporary Git metadata; preserve uncertain/user-modified artifacts. Do not
> expose unsafe partial write commands. Leave changes uncommitted with evidence.

### Thread 06 — Fresh backup

**GitHub issue:** [#6](https://github.com/jeffshurtliff/obfuscidian/issues/6)

**Goal/deliverable:** Working `shroud fresh` using validated format and transactions.
**Depends on:** 05. **Status:** Complete. The maintainer reviewed, committed,
and merged/pushed the implementation into `origin/main`; issue #6 is closed as
completed. All four subtasks and acceptance criteria are met. Linux CI passed
on Python 3.12–3.14. See the Thread 06 completion record and
[fresh backup guide](../docs/BACKUP.md) for evidence, CLI behavior and platform
limits. Threads 07–08 are complete; see their completion records. Thread 09 is
complete; see its completion record below for the accepted Python 3.14 CI gap.

1. Wire CLI options into read-only preflight, complete origin inventory,
   selected-key validation, existing-mirror authentication, and confirmation.
2. Stage individual encrypted objects and manifest; reuse unchanged validated
   ciphertext when possible and validate the entire proposed snapshot.
3. Publish only the managed tree, remove stale entries from the new logical
   snapshot, retain the previous snapshot externally, and implement dry run,
   no-op handling, interruption, and explicit recovery.
4. Add end-to-end mixed binary/nested-vault tests for first backup, replacement,
   stale cleanup, unsafe/unmanaged destinations, wrong keys, detected source
   changes, refused prompts, non-interactive replacement, and size limits.

**Acceptance/demo:** A nested fixture produces a complete authenticated mirror
without changing source bytes or Git controls. Fresh excludes stale data, and
failure never exposes an incomplete published snapshot. A no-op creates no
changed files or retained-copy artifacts.

**Validation:** Common checks; fresh-backup integration/CLI tests; console and
module examples with temporary paths; verify the produced mirror through the
shared validator (or the `verify` command if Thread 08 is complete).

**Copy-ready prompt:**

> Implement only Thread 06: end-to-end shroud fresh using existing format and
> transaction primitives. Test mixed vaults, stale removal, retained rollback,
> confirmations, no-op and dry-run behavior, wrong keys, and failure recovery.
> Preserve origin data and Git controls. Update help/roadmap and leave changes
> uncommitted; do not implement merge backup or restore in this thread.

### Thread 07 — Merge backup

**GitHub issue:** [#7](https://github.com/jeffshurtliff/obfuscidian/issues/7)

**Goal/deliverable:** Working additive incremental `shroud merge` with predictable
history retention and minimal ciphertext churn.
**Depends on:** 06. **Status:** Complete. The maintainer reviewed, committed,
and merged/pushed the implementation into `origin/main`; issue #7 is closed as
completed. All four subtasks and acceptance criteria are met. Linux CI passed
on Python 3.12–3.14. See the [completion record](#thread-07--merge-backup-completion-record-5-october-2026)
and [backup guide](../docs/BACKUP.md) for evidence, behavior and platform limits.
Thread 08 is complete; see its completion record. Thread 09 is complete;
see its completion record below for the accepted Python 3.14 CI gap.

1. Validate the old mirror, union old/current logical paths, and classify new,
   changed, metadata-only, unchanged, and retained stale entries. Initialize
   a new mirror safely when no previous snapshot exists.
2. Reuse IDs and ciphertext according to the format contract; preserve old
   absent/excluded entries and corresponding empty directories. Reject a stale
   file/directory type conflict rather than silently deleting a retained entry;
   explain that fresh mode is required for that exact-state transition.
3. Apply confirmation only to existing content replacement; stage/verify and
   publish transactionally. Detect no-op before creating any write artifacts;
   clean only the operation's temporary recovery data after successful merge.
4. Test repeated backup, add/edit/delete/rename, changed exclusion rules,
   metadata-only changes, stale path type conflicts, corrupted old ciphertext,
   and explicit-invalid-key behavior. Confirm that retained stale paths restore.

**Acceptance/demo:** After a delete/rename, merge retains old entries while
fresh removes them. Unchanged tokens are byte-identical. A completely unchanged
merge leaves the mirror, snapshot ID, and filesystem modification times intact.

**Validation:** Common checks; incremental integration tests; compare sorted
mirror hashes and mtimes across no-op runs; verify old/new snapshot integrity.

**Copy-ready prompt:**

> Implement only Thread 07: additive shroud merge with stable IDs/ciphertext,
> stale-entry retention, metadata-only updates, and no-write no-op detection.
> Reuse existing transactions and validators. Test delete/rename/exclusion and
> type-conflict behavior; document that deleted notes can return during restore.
> Update status with evidence and leave changes uncommitted.

### Thread 08 — Read-only verification

**GitHub issue:** [#8](https://github.com/jeffshurtliff/obfuscidian/issues/8)

**Goal/deliverable:** Public `verify` command using complete backup validation.
**Depends on:** 04; may run before 05–07. **Status:** Complete. The maintainer
reviewed, committed and merged/pushed the implementation into `origin/main`;
issue #8 is closed as completed. All four subtasks and acceptance criteria
are met. Linux CI passed on Python 3.12–3.14. See
[verification](../docs/VERIFY.md) and the
[completion record](#thread-08--read-only-verification-completion-record-5-october-2026)
for evidence and limits. Thread 09 is complete; see its completion record for
the accepted Python 3.14 CI gap.

1. Add `verify` with mirror/key resolution, non-interactive behavior, counts,
   controlled verbose diagnostics, help, and integrity failure exit status.
2. Verify the manifest and every object regardless of exclusions; detect
   unexpected files and pending transactions without attempting repair.
3. Reject write/log/recovery options and guarantee no destination creation,
   locks, rewritten metadata, or retained artifacts. Treat missing mirror data
   and unknown format versions as failures with useful remediation.
4. Test valid, missing, tampered, swapped, oversized, malformed, pending, and
   wrong-key mirrors. Assert output privacy and stable exit categories.

**Acceptance/demo:** Verification reports a valid synthetic mirror, identifies
corruption without printing content, and makes no writes on success or failure.
Filesystem access times may be changed by the OS on reads; that is not an
application write or a claim that every filesystem attribute remains frozen.

**Validation:** Common checks; validator/verify CLI tests; snapshot filesystem
content, file lists, mtimes, and transaction artifacts before/after invocation.

**Copy-ready prompt:**

> Implement only Thread 08 after Thread 04 is complete. Expose read-only verify
> through Click using complete manifest/object validation. Test corrupt and
> valid mirrors, privacy, pending transactions, and zero application writes;
> reject log/recovery/write options. Do not repair or mutate backups. Update
> help/status and leave changes uncommitted.

### Thread 09 — Fresh restore

**GitHub issue:** [#9](https://github.com/jeffshurtliff/obfuscidian/issues/9)

**Goal/deliverable:** Working `unshroud fresh` with complete authentication before
destination mutation and retained destination rollback.
**Depends on:** 05, 07, 08. **Status:** Complete; reviewed and merged/pushed into `origin/main`.

All four subtasks and acceptance criteria are met; issue #9 is closed as completed
under explicit maintainer authorization. Linux CI passed on Python 3.12/3.13.
Python 3.14 was canceled before running any steps because no hosted runner acquired
the job; the maintainer accepted that validation gap for closure. See
[fresh restore](../docs/RESTORE.md) and the
[completion record](#thread-09--fresh-restore-completion-record-5-october-2026)
for commit alignment, job evidence and platform limits. Thread 10 is now
complete, reviewed and merged/pushed with Linux CI passing on Python 3.12–3.14;
Thread 11 is also complete with green Linux CI; Thread 12 is complete with the
nine-job Linux/macOS/Windows matrix passing on Python 3.12–3.14. Threads 13–14 remain not started.

1. Resolve restore direction correctly: mirror is source; origin is destination.
   Validate every manifest/object and target name before staging plaintext.
2. Reconstruct bytes, paths, empty directories, and supported modification times
   in private staging. Implement `.obsidian` preservation and root Git controls;
   refuse nested-repository destruction and unsafe destination shapes.
3. Integrate dry run, confirmation, non-interactive rules, safe publication,
   retained plaintext rollback, interrupt handling, and conservative recovery.
4. Add round trips for fresh/merge backups and fixtures with settings/binary
   files. Test existing destinations, failed keys/tokens, collisions, missing
   parents, path traversal, timestamp limits, excluded historic entries,
   preserved settings, and failure before/during publication.

**Acceptance/demo:** Restoring a mixed backup reproduces exact bytes and included
structure; a merge backup also reproduces its retained stale notes. A corrupt
backup leaves existing destination payload untouched. Fresh success retains
the old payload externally and explains its plaintext sensitivity.

**Validation:** Common checks; fresh-restore integration tests; hash/tree
comparisons excluding protected controls/configuration; inspect private staging
and rollback locations and their platform-appropriate permissions.

**Copy-ready prompt:**

> Implement only Thread 09: safe unshroud fresh, using complete verification
> before destination changes. Restore binary bytes and empty folders, preserve
> protected Git/configuration state, retain plaintext rollback, and test failure,
> confirmation, and dry-run paths. Do not add Git merge restore yet. Record
> checks/status and leave changes uncommitted for review.

### Thread 10 — Git merge restore

**GitHub issue:** [#10](https://github.com/jeffshurtliff/obfuscidian/issues/10)

**Goal/deliverable:** Working `unshroud merge` with a separate review worktree;
original checkout and restored changes remain under user control.
**Depends on:** 09. **Status:** Complete, reviewed and merged/pushed into
`origin/main`; issue #10 is closed as completed. Linux CI passed on Python
3.12–3.14. See the
[completion record](#thread-10--git-merge-restore-completion-record-5-october-2026)
for commit alignment, acceptance evidence and platform limits.

1. Validate Git availability, origin repository/root, clean tracked/untracked
   and ignored vault data, local base branch, explicit Git directory, branch
   suffix, output parent, overlap, and absence of pending Git operations.
2. Stage authenticated restore data first, then create the new restore branch
   and worktree. Overlay onto the chosen committed base while retaining
   base-only files and protecting `.git`, `.gitignore`, and optional settings.
3. Leave the index/restored content uncommitted; report ignored restored paths
   as review concerns and provide manual review/commit/merge instructions.
   Never switch, stage, stash, reset, commit, fetch, or push the origin/mirror.
4. Test temporary Git repositories with synthetic commits: default/custom base,
   branch collisions, metadata files, ignored/untracked files, dirty origin,
   missing Git/base, hooks/config isolation, existing output, and creation/write
   failures. Cleanup must preserve any later user edits.

**Acceptance/demo:** Origin branch/index/tree are unchanged; the new worktree
contains an additive overlay with uncommitted differences and documented manual
next steps. The command never claims those differences can merge before commit.

**Validation:** Common checks; offline real-Git integration tests; compare
origin HEAD/index/content before/after; inspect new branch/worktree/status and
verify no restore commit was created.

**Copy-ready prompt:**

> Implement only Thread 10: unshroud merge in a separate Git worktree, with a
> clean origin and explicit base/branch/output validation. Keep restored data
> uncommitted, preserve the original checkout, and report ignored files/manual
> review steps. Test using temporary repositories only, including safe cleanup
> after failure. Do not commit, push, or publish; update roadmap evidence.

### Thread 11 — CLI polish

**GitHub issue:** [#11](https://github.com/jeffshurtliff/obfuscidian/issues/11)

**Goal/deliverable:** Consistent user-facing help, errors, progress, privacy, and
automation behavior across the completed commands.
**Depends on:** 10. **Status:** Complete, reviewed and merged/pushed into
`origin/main`; issue #11 is closed as completed. Linux CI passed on Python
3.12–3.14. See the
[completion record](#thread-11--cli-polish-completion-record-5-october-2026)
for commit alignment, acceptance evidence and platform limits.
Thread 12 is complete with the nine-job Linux/macOS/Windows matrix passing on
Python 3.12–3.14. Threads 13–14 remain not started.

1. Audit options/help at group and subcommand levels, required modes, precedence,
   incompatible options, defaults, and exit-code mapping; ensure console/module
   parity and useful misuse messages.
2. Complete normal/verbose progress, redirected-output behavior, redacted
   optional logging, safe path rendering, and explicit `--log-paths` handling.
   Validate log locations and never expose secrets through tracebacks/messages.
3. Harmonize confirmation, EOF/non-terminal input, `--non-interactive`, `--yes`,
   dry runs, recovery, and KeyboardInterrupt behavior. Ensure actual partial
   failure and unsupported combinations never produce success status.
4. Add CLI contract tests with realistic temporary workflows and synthetic
   sensitive markers/control-character filenames; test both streams, logs,
   no-op output, unavailable permissions, and each exit category.

**Acceptance/demo:** A user can discover backup/verify/restore through help,
run an unattended confirmed workflow, and understand exactly what to review.
Default output/logs contain no plaintext paths, keys, or contents; explicit
handoff-location exceptions follow the documented interactive policy.

**Validation:** Common checks; CLI/logging tests; run all planned examples in a
synthetic workspace with correct key locations; manually inspect redirected
output and help formatting at narrow and normal terminal widths.

**Copy-ready prompt:**

> Implement only Thread 11. Audit and finish the approved CLI contract across
> commands: help, progress, redacted logs, explicit path detail, prompts,
> non-interactive/dry-run/recovery behavior, and exit codes. Add privacy/UX
> contract tests and verify console/module parity using synthetic fixtures.
> Preserve existing data semantics and leave changes uncommitted.

### Thread 12 — Cross-platform hardening

**GitHub issue:** [#12](https://github.com/jeffshurtliff/obfuscidian/issues/12)

**Goal/deliverable:** Evidence for the supported OS/Python matrix and robust
boundary/failure handling, without new product features.
**Depends on:** 11. **Status:** Complete; reviewed and merged/pushed into
`origin/main`. All four subtasks and acceptance criteria are met, with the
documented native Windows mutation/recovery and existing-log append refusals
retained. Issue #12 is closed as completed under explicit maintainer
authorization. All nine Linux/macOS/Windows jobs passed on Python 3.12–3.14
at `dc56009`; see the
[completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026).
Threads 13–14 remain **not started**; the maintainer explicitly excluded Thread 13.

1. Expand CI to Windows, macOS, and Linux across Python 3.12, 3.13, and 3.14.
   Use Poetry/lock-aware installs; run unit and offline local-Git integration
   suites. Platform-only skips must be narrow and explained.
2. Run read-only Ruff/Bandit checks, report coverage, and fix relevant failures.
   Test case/Unicode collisions, reserved names, roots/drives, path limits,
   junctions/symlinks, permissions, metadata support, and shell differences.
3. Add size-boundary, large-inventory, space estimation, concurrency, interruption,
   and transaction recovery checks. Use mocks for impractical allocation/disk
   failures plus bounded actual files; do not allocate gigabytes in routine CI.
4. Assess source/destination race protections and no-op behavior across hosts.
   Record what was validated locally, by remote CI, or remains unverified;
   do not treat adding a matrix as proof that all jobs passed.

**Acceptance/demo:** Supported matrix passes where authorized CI execution is
available, with documented narrowly scoped limitations. No lossy restore or
unsafe path workaround is introduced to make platform tests pass.

**Validation:** Common checks; security scan; targeted boundary tests; actual
matrix results. Remote pushes/PRs still require separate authorization, so a
local-only handoff reports unexecuted hosted validation explicitly.

**Thread 09 discovery for future work:** Refine read-only target filesystem
comparison/capability detection. Fresh restore currently rejects ambiguous
case-folded/NFC names conservatively even when a case-sensitive filesystem
could preserve them distinctly. Broaden native Windows destination observation
and mutation validation without weakening the fail-closed write boundary.

**Thread 11 discovery for future work:** Validate private append permissions and
ownership for existing Windows operational logs. Thread 11 creates new logs
using the established keygen protected DACL helper but refuses existing Windows
log appends until their file ACL can be checked. Exercise this boundary in the
broader matrix without relaxing private log custody. Thread 12 retains existing-log
append refusal pending native file ownership/DACL validation.

**Copy-ready prompt:**

> Implement only Thread 12: cross-platform CI and hardening of existing behavior
> for Python 3.12–3.14 on Windows/macOS/Linux. Add focused platform, resource,
> interruption, and recovery coverage; report actual validation versus pending
> CI. Do not weaken safety or add deferred features. Do not push or create a PR
> without authorization; leave changes reviewable and uncommitted.

### Thread 13 — Documentation and contribution guidance

**GitHub issue:** [#13](https://github.com/jeffshurtliff/obfuscidian/issues/13)

**Goal/deliverable:** Coherent, buildable user/contributor/security documentation
that describes completed behavior rather than the template.
**Depends on:** 12 for completion; earlier threads add incremental help/docs.
**Status:** Not started.

1. Add Poetry `docs` dependencies and Sphinx/reST/MyST with `pydata_sphinx_theme`.
   Adapt the structure of SalesPyForce/PyDPlus: overview/getting started, CLI
   reference, backup/restore/configuration guides, security/limits, troubleshooting,
   changelog, and maintainer material. Avoid unrelated copied extensions/content.
2. Document installation through pip/pipx, supported environments, POSIX and
   Windows command/environment examples, key custody, first backup/verification,
   dry run, merge stale entries, and a complete restore rehearsal.
3. Document format compatibility, output privacy, file caps, non-interactive
   confirmation, pending recovery, retained plaintext rollback cleanup, ignored
   Git files, worktree/manual commit/merge, and honest threat-model limitations.
4. Create CONTRIBUTING.md and public-safe security reporting guidance; describe
   setup, Ruff/docstrings/headers, meaningful tests, branch/issue/PR policy,
   docs/version/changelog standards, and release authorization. Synchronize
   AGENTS.md with actual tooling without requiring absent issue templates or
   inventing existing hosting/reporting configuration. Fix template README links.

**Acceptance/demo:** A new user can follow a synthetic backup/verify/restore
walkthrough without relying on implementation internals. Sphinx builds without
warnings, links resolve, and examples use only fake data and supported commands.
No claim of PyPI publication, remote privacy validation, or guaranteed recovery
appears before it is supported.

**Validation:** Common checks; `poetry install --with dev,docs`;
`poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html`;
local link checks; execute examples against temporary fixtures and inspect the
rendered key usage/security/restore pages. Check Markdown/reST literal syntax.

**Copy-ready prompt:**

> Implement only Thread 13. Build Sphinx/reST/MyST docs using the PyData theme,
> update user guides/README/changelog, and create contributor/security guidance
> consistent with AGENTS.md and completed functionality. Use public-safe
> examples, test a full synthetic restore tutorial, and validate a strict docs
> build and rendered pages. Do not publish docs or create tool companion files
> unless separately requested. Leave changes uncommitted.

### Thread 14 — Release preparation

**GitHub issue:** [#14](https://github.com/jeffshurtliff/obfuscidian/issues/14)

**Goal/deliverable:** A reviewable release candidate, validated artifacts,
maintainer runbook, and safe publication workflow proposal; no publication.
**Depends on:** 13. **Status:** Not started.

1. Review approved package/version/changelog and compatibility policy. Prepare
   only the requested release-version edits; stable promotion requires a
   separately explicit request. Recheck dependency security floors and current
   build/publishing guidance using official sources.
2. Build one fresh wheel and sdist in an isolated candidate directory. Run strict
   Twine validation, inspect metadata/archive contents, and install each with
   dependencies outside the checkout. Test console/module invocation and a
   synthetic backup/verify/restore using the installed package.
3. Replace template publication assumptions with a reviewed Poetry-compatible
   workflow: full required checks, protected release environment, trusted
   publishing, explicit stable-release selection, tag/version agreement, and
   artifact inspection. Do not trigger it, configure external credentials or
   environments, or create a GitHub release during preparation.
4. Write a maintainer runbook for candidate checks, review, exact-commit builds,
   docs/changelog/version consistency, authorized tag/release/publication order,
   and failure recovery. Enumerate every external/history-changing step requiring
   separate authorization and the controls not yet configured externally.

**Acceptance/demo:** Candidate artifacts contain exactly the intended package,
license, and metadata; no secrets/private data/generated clutter; installation
works independently of the checkout. All executed checks pass, and unexecuted
hosted checks remain explicit blockers to publication readiness.

**Validation:** Full available common/security/docs checks; strict Twine checks
of exact candidate files; archive inspection, checksums, dependency-aware wheel
and sdist smoke tests, and installed synthetic round trip. Verify release trigger
behavior without creating tags/releases or uploading anything.

**Copy-ready prompt:**

> Implement only Thread 14 release preparation. Inspect actual tooling and
> release state, validate fresh candidate artifacts and an installed synthetic
> round trip, prepare the maintainer runbook and safe publication workflow, and
> report all external prerequisites. Do not promote versions unless requested,
> stage/commit/push, create PRs/tags/releases, configure publishing, or upload
> packages. Leave the proposed changes and evidence for maintainer review.

## 5. Acceptance, tracking, and deferred work

### V1 acceptance matrix

| Area | Required scenarios |
| --- | --- |
| Functional | Mixed vault bytes/names/empty folders round trip; all commands and both entry points work |
| Incremental | Stable IDs/tokens; metadata-only updates; unchanged mirror has no writes; stale entries retain/remove according to mode |
| Configuration | Every CLI/environment precedence and conflict case; keygen cannot overwrite; non-interactive never prompts |
| Integrity | Wrong key, manifest/object tampering, substitution, missing/truncated/unexpected files, size caps, format versions |
| Filesystem | Roots, nesting/overlap, missing parents, symlinks/junctions, special files, traversal, case/Unicode/name-length collisions |
| Preservation | Origin remains read-only during backup; Git controls preserved; fresh rollback retained; settings preservation honored |
| Transactions | Failure at each phase, competing operations, detected changes, space/permission problems, interrupt, pending recovery |
| Git | Clean repository/base/branch/output checks; isolated worktree; no origin changes or automatic commit; ignored-file review |
| Privacy/UX | Counts normally, explicit path detail, redacted logs, escaped filenames, useful error/exit behavior |
| Delivery | Supported platform/Python checks, strict docs, clean wheel/sdist, installed round trip, no accidental publication |

Use invariant-driven tests that show data preservation and detect real failures,
not tests that simply mirror private implementation. The CLI suite uses process
isolation for parallel execution; Click's test runner swaps interpreter-global
streams and must not run concurrently in threads. Use `tmp_path` instead of
the deprecated isolated-filesystem helper. See [Click testing guidance](https://click.palletsprojects.com/en/stable/testing/).

### Tracking and handoff record

Each completed or partial thread updates its status and appends a short record
here. Record the date, scope, commands actually run and outcomes, unresolved
limitations, and next eligible thread. Do not add credentials, user vault paths,
real content, or private runtime details. Keep the task index and per-thread
status consistent. 

Thread 01 is complete following maintainer review and merge;

Thread 02 is complete following maintainer review, merge, and successful Linux
CI. Thread 03 is complete following maintainer review, merge, and successful
Linux CI; issue #3 is closed.

Thread 04 is complete following maintainer review, merge/push, and successful
Linux CI; issue #4 is closed. 

Thread 05 is complete following maintainer review, commit, merge/push, and
successful Linux CI on Python 3.12–3.14; issue #5 is closed as completed.

Thread 06 is complete following maintainer review, commit, merge/push, and
successful Linux CI on Python 3.12–3.14; issue #6 is closed as completed.

Thread 07 is complete following maintainer review, commit, merge/push, and
successful Linux CI on Python 3.12–3.14; issue #7 is closed as completed.

Thread 08 is complete following maintainer review, commit, merge/push and
successful Linux CI on Python 3.12–3.14; issue #8 is closed as completed. See
its completion record below. Thread 09 is complete following maintainer review,
commit and merge/push, with issue #9 closed as completed. Linux Python 3.12/3.13
CI passed; the maintainer accepted the runner-unavailable Python 3.14 cancellation
for closure. See its completion record below. Thread 10 is complete following
maintainer review, commit and merge/push, with issue #10 closed as completed and
Linux CI passing on Python 3.12–3.14. See its completion record below.
Thread 11 is complete following maintainer review, merge/push and successful
Linux CI on Python 3.12–3.14; issue #11 is closed as completed. See its
completion record below. Thread 12 is complete following maintainer review,
merge/push and the passing nine-job Linux/macOS/Windows Python 3.12–3.14 matrix;
issue #12 is closed as completed. See its completion record below.
Threads 13–14 remain not started.
Earlier handoff records describe the state at that time; later completion
records supersede their pending-review and Git-status statements.
The linked GitHub issues hold public progress discussion and verified
checklists; this roadmap remains authoritative for approved scope and
dependencies. Do not silently resolve conflicting scope or acceptance
criteria: record the maintainer decision in both places before proceeding.

**Planning-document handoff:** This task creates the roadmap and root agent
instructions and adds only a notice to the original brief. It does not implement
any application thread, migrate packaging, modify examples, or run a release.
Review these documents first; Thread 01 is the next implementation task.

**Documentation validation:** The fourteen thread blocks each have dependencies,
bounded subtasks, acceptance/demo criteria, validation guidance, and a handoff
prompt. All nine confirmed maintainer choices are recorded. Local links and
Markdown code fences were checked; whitespace checks include the two new,
untracked documents. The original brief is byte-for-byte preserved after removing
the inserted notice. Only the three authorized Markdown files changed; no
application tests were rerun for this documentation-only task and no changes
were staged or committed.

**Contributor-guidance preparation — 3 October 2026:** By direct maintainer
request, added root `CONTRIBUTING.md` and all sixteen SalesPyForce issue-template
categories, adapted for Obfuscidian's CLI, privacy, and release authorization.
The guide distinguishes current setuptools/Python 3.10+ setup from planned
Poetry/src/Python 3.12+ tooling. Root AGENTS.md now points to the existing guide.
This supplies preparatory contributor/security reporting guidance for Thread 13,
not its complete documentation deliverable. Thread 13 remains not started;
Threads 01–12, Sphinx tooling, user guides, and the release runbook are still
pending. Thread 01 remains the next eligible implementation thread. No GitHub
labels, private reporting configuration, issues, or publication settings were
created or changed. Validation passed: all sixteen YAML frontmatter blocks
parsed with Ruby Psych; source filename parity, eleven local Markdown links,
code-fence balance, LF/final newlines, whitespace, private-path/key-marker
scans, and source/diff review. `git diff --check` passed, with new untracked
files checked separately. Application tests and Sphinx builds were not run for
this documentation-only task; no dependencies were installed. Changes remain
uncommitted and unstaged; no application or workflow files changed.

**GitHub roadmap tracking — 3 October 2026:** Reviewed latest local and
GitHub commit `e513c793084aacc6792de8769ddc452b20280e69`, including the sixteen
issue templates and contributor/agent/roadmap guidance. Created issues #1–#14,
one per implementation thread, with all fifty-six roadmap subtasks, dependency
links, acceptance criteria, validation requirements, and public-safe handoff
checklists. All are assigned to `jeffshurtliff`, associated with milestone 1
(`v1.0.0`), and labeled using existing Obfuscidian labels, including `maintainer`
and `codex`. Thread 13 records the existing contributor-guidance preparation;
Thread 14 tracks preparation only and preserves separate release authorization
checkpoints. Added issue links to the index and each thread, and agent guidance
for progress, blockers, checklist evidence, handoff, and review before closure.
Verified live issue metadata and bodies against the prepared requests, along
with local link/consistency/privacy/whitespace checks and `git diff --check`.
Only AGENTS.md and this roadmap changed locally; changes remain unstaged and
uncommitted. No application tests or Sphinx builds were run for this tracking
and documentation task. All implementation threads remain not started;
Thread 01 / issue #1 is next. No labels, milestone settings, workflows, releases,
or publication configuration were changed.

**Thread 01 foundation handoff — 3 October 2026:** Implemented only the four
foundation subtasks on the existing `chore/1-thread-01-project-foundation` branch,
which started clean at the same commit as `main`. Issue #1 has no dependencies;
its live scope matched the roadmap. No keygen, backup, restore, verification,
cryptography behavior, or backup-format implementation was added.

- Packaging now uses PEP 621, static `1.0.0.dev0`, Python `>=3.12`, and
  Poetry/poetry-core with `src/obfuscidian/`. Apache-2.0 license metadata and both
  entry-point names are retained. Poetry 2.4.2 generated `poetry.lock` through
  `poetry add --group dev --lock`; no lockfile edits were made by hand.
- `pyproject.toml` is the sole runtime declaration, retaining `click>=8.5.0` and
  `cryptography>=50.0.2`. cryptography is reserved for the approved later Fernet
  implementation. Removed `requirements.txt`. Added pytest, coverage, Ruff,
  Bandit, Twine, and poetry-core to `dev`; the backend is needed for offline
  artifact builds in tests. Its developer marker excludes Python 4, matching
  upstream metadata without changing the approved package minimum. Docs tooling
  remains deferred. Ruff uses the approved style; UP009 is excluded specifically
  to retain the required module encoding header, and historical `dev/` scripts
  are outside application/test lint scope.
- Removed the template command; help states that later commands are unavailable.
  Console/module help and version output agree, with the product name in version
  output. reST return/version directives remain in the docstring and are hidden
  from Click help. Added `tests/unit/`, `tests/integration/`, `docs/CHANGELOG.md`,
  and current README/contributor/agent development guidance.
- Linux CI now targets Python 3.12–3.14 with Poetry lock checks, Ruff, pytest,
  coverage, Bandit, fresh builds, strict Twine checks, and wheelhouse-backed
  installation tests. The release publication workflow was not changed or
  triggered; its old template assumptions remain for Thread 14 to replace.

**Executed local validation:** macOS ARM64 with Poetry 2.4.2 and Python 3.12.7,
3.13.15, and 3.14.7. `poetry install --with dev --no-interaction`,
`poetry check --lock --strict`, `poetry run ruff check .`,
`poetry run ruff format --check .`, `poetry run pytest -q`, and
`poetry run bandit -r src/obfuscidian` passed on all three interpreters. Each
normal offline suite passed **11 tests**; Bandit reported no issues. Python
3.13/3.14 used separate temporary source copies and environments. Console/module
help/version were also executed directly from the Python 3.12 developer install.
`poetry run coverage run -m pytest -q` and `poetry run coverage report` passed
on Python 3.12, reporting 44% in-process application coverage; this does not
measure the separate installed entry-point subprocesses, and no coverage
threshold is established.

`poetry build --output <fresh-candidate-directory>` created exactly
`obfuscidian-1.0.0.dev0-py3-none-any.whl` and `obfuscidian-1.0.0.dev0.tar.gz`.
`poetry run twine check --strict <candidate-wheel> <candidate-sdist>` passed.
Archive allowlists verified package modules, entry-point/dependency/Python/license
metadata, and absence of private/scratch/generated content. The sdist additionally
contains the lockfile and changelog. Normal tests seed synthetic private/key/cache/
scratch sentinels in a temporary source copy and verify their exclusion.

After downloading top-level dependencies pinned to the installed environment,
fully isolated offline installation checks passed on Python 3.12–3.14 using
`poetry run pytest -q tests/integration/test_packaging.py --artifact-dir
<fresh-candidate-directory> --wheelhouse <dependency-wheelhouse>`. Each artifact
was installed with dependencies in its own fresh virtual environment, with no
system site packages or source-path override. Tests verified the imported module
resides in that environment, matched console/module help/version outside the
checkout, and ran `pip check`. The default suite explicitly shares installed
development dependencies; it does not claim that stronger isolation mode.

Candidate SHA-256 values:

- Wheel: `2b73895bd85c31303ffc6ed2ce55000addcf696fa2f37305d75f0bd32500cf37`
- Sdist: `84fae88a152c7e306c585c880a98fc1eb07ba143b6501344af97a7196a5c62ee`

README/changelog and other modified guidance passed local link, code-fence,
line-ending, and diff checks; test workflow YAML and embedded shell syntax were
validated. Source/diff and proposed-file privacy review found no private data.
Issue #1 receives the matching checklist/handoff update and remains open for
maintainer review. Local changes are unstaged and uncommitted; no branch, commit,
PR, tag, release, deployment, or publication was created by this task.

**Remaining/deferred:** All Thread 01 local acceptance criteria are met. Hosted
Linux CI has not run; Windows validation and broader OS hardening belong to
Thread 12, strict Sphinx builds to Thread 13, and publication workflow replacement
to Thread 14. No real-vault/cloud tests were run. Thread 02 is the next eligible
implementation increment after maintainer review of this foundation; it was not
started. Issue closure requires the maintainer's review/decision.

**Thread 01 completion — 3 October 2026:** The maintainer reviewed the
foundation, committed it as
[`1b7432f`](https://github.com/jeffshurtliff/obfuscidian/commit/1b7432f), and merged
it into `origin/main` as
[`8c9e2c8`](https://github.com/jeffshurtliff/obfuscidian/commit/8c9e2c8).
The live GitHub `main` commit matches local `HEAD`, `main`, and `origin/main`.
At the maintainer's explicit request, issue #1 is closed as completed and its
review/closure checklist item is checked. Thread 01 is complete; Thread 02 —
Configuration and keys — is the next increment and remains not started.
The maintainer explicitly directed that Thread 02 not begin during this update.

This follow-up changes only this roadmap and `README.md` to reflect completion
and next-thread status. The earlier implementation/artifact evidence remains
in the initial handoff; no new application tests, artifact builds, or hosted
CI/platform checks were run for this documentation-only update. Local links,
status consistency, Markdown fences, privacy/whitespace, and `git diff --check`
passed. These status edits remain unstaged and uncommitted; no implementation,
commit, PR, publication, or Thread 02 work was performed in this follow-up.

**Thread 02 handoff — 3 October 2026:** Implemented only configuration and
keys on the pre-existing `feature/2-thread-02-config-and-keys` branch, initially
clean and matching `main`/`origin/main` at `0d0b909`. Thread 01 is confirmed
complete from actual code/packaging, closed issue #1 and its maintainer review
record, the successful hosted Test run for foundation merge `8c9e2c8`, and
this task's passing lock check and 11 baseline tests.

- Added internal [configuration resolution](../src/obfuscidian/config.py),
  [shared constants](../src/obfuscidian/constants.py),
  [redacted errors](../src/obfuscidian/errors.py), and
  [key I/O](../src/obfuscidian/keys.py). Implemented CLI/environment selector
  precedence and conflicts, explicit-invalid-value refusal, cwd/home expansion,
  literal shell variables, and independent optional vault-path resolution.
  Vault inventory, overlap, and key-in-vault preflight remain Thread 03 work.
- Added [keygen](../src/obfuscidian/cli.py) with exclusive creation, ASCII aliases,
  local timestamp prompt defaults, terminal-only prompts, EOF/interrupt handling,
  non-interactive operation, read-only dry runs, and controlled path output.
  POSIX uses mode 0600 and no-follow directory handles with identity rechecks.
  [Windows creation](../src/obfuscidian/_windows.py) applies an owner-only
  protected DACL at creation and refuses volumes without persistent ACLs;
  native runtime validation is pending. Failed writes clean only the owned new
  entry; changed targets/failed cleanup are preserved and reported for inspection.
- Loading reads a bounded complete canonical Fernet key, optionally with one
  LF/CRLF ending; invalid/missing selected keys never trigger fallback or key
  generation. Permission warnings do not chmod or rewrite existing keys.
  Synthetic authenticated binary round trips, wrong-key rejection, collisions,
  genuine and injected permission failures, race/cleanup failure preservation,
  and output privacy satisfy all local acceptance criteria.
- Updated README, contributor/agent current-status notes, changelog,
  [configuration/custody guide](../docs/CONFIGURATION.md), and installed help.
  The configuration guide is included in the sdist; package/dependency versions
  and the lockfile are unchanged. Keygen exposes only its implemented options;
  logging remains deferred to Thread 11 and unsupported options are rejected.
  No vault write/restore/verify command or backup-format behavior was added.

**Executed validation:** Poetry 2.4.2 on macOS ARM64; Python 3.12.7 in the
checkout and Python 3.13.15/3.14.7 in temporary public-safe source copies.
Lock checks, Ruff lint/format, pytest, and Bandit passed for all three:
**121 passed, 1 skipped** each. The skip requires native Windows ACL APIs.
Temporary Poetry installs initially failed due to sandbox network restrictions;
retrying the same locked installs with authorized network access succeeded.
No dependencies or lock entries were changed. Final Python 3.12 coverage
run/report passed, reporting 76% in-process coverage, including unexecuted
Windows code. Installed entry-point subprocesses are separately tested and
not included in that measurement.

Fresh `poetry build --output <fresh-candidate-directory>` and strict Twine checks
passed for exactly one new wheel and sdist. Updated offline archive allowlists
and default installation tests pass within the normal suite. Fully isolated
wheelhouse-backed wheel/sdist installation tests passed on Python 3.12
(**3 passed**), checking imports outside the checkout, console/module help and
version, keygen help/dry run/creation, output privacy, and `pip check`.
A direct manual synthetic dry run through both developer entry points created
no files. Local Markdown links/fences, LF/whitespace, proposed-file privacy,
source/diff inspection, and `git diff --check` passed.

**Tracking/remaining:** Issue #2 receives matching start, progress, handoff,
and verified checklist updates and remains open for maintainer review. All
Thread 02 local acceptance criteria are met; native Windows/ACL behavior and
hosted CI for these uncommitted changes remain unexecuted. Broader OS validation
belongs to Thread 12; Sphinx tooling/build to Thread 13; logging completion to
Thread 11. No real keys, vaults, or cloud backups were used. Thread 03 is next
following review; Threads 03–14 were not started.

All proposed changes are unstaged and uncommitted on the existing Thread 02
branch. No branch, staging, commit, push, PR, merge, tag, release, or publication
was performed, and no workflow was edited or triggered.

**Thread 02 documentation follow-up — 3 October 2026:** At the maintainer's
request, clarified AGENTS.md and CONTRIBUTING.md: summarized `versionadded` and
`versionchanged` history is required only for releases after 1.0.0. Public
initial-release CLI callables retain/include one bare `.. versionadded:: 1.0.0`
below `\f` and above their Sphinx field lists, without change summaries.
The current CLI docstrings already matched the maintainer's convention and
were preserved. Updated the changelog and issue #2 with this decision. Verified
directive count/order using AST docstring inspection, guidance consistency,
Markdown fences/local links, and `git diff --check`. No application behavior
changed; application tests and artifact/platform checks were not rerun for this
documentation-only follow-up. Changes remain unstaged and uncommitted; issue #2
remains open, and no Git history or publication action was performed.

**Thread 02 completion — 3 October 2026:** The maintainer reviewed and
accepted Thread 02, committed it as
[`472a6ac`](https://github.com/jeffshurtliff/obfuscidian/commit/472a6ac), and merged
and pushed it into `origin/main` as
[`26a5929`](https://github.com/jeffshurtliff/obfuscidian/commit/26a5929).
Verified that live GitHub `main` matches local `HEAD`, `main`, and `origin/main`.
The [hosted Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37157742622)
completed successfully for that merge, including the Linux/Python 3.12, 3.13,
and 3.14 jobs. At the maintainer's explicit request, issue #2 is closed as
completed and its review/closure checklist item is checked. The earlier handoff
records retain their evidence and historical Git/review status; this completion
record supersedes their pending-review and unexecuted-hosted-CI statements.
Native Windows ACL validation and broader OS hardening remain Thread 12 work.

Updated README.md, CONTRIBUTING.md, AGENTS.md, and this roadmap to reflect
completion and the next step. Thread 03 — Vault inventory and path preflight —
is next and remains not started; the maintainer explicitly prohibited beginning
it during this update. This documentation-only follow-up verifies local links,
Markdown fences, status consistency, privacy/whitespace, and `git diff --check`;
it does not rerun application tests, builds, or platform checks. The status edits
remain unstaged and uncommitted on `main`. No application changes, Thread 03
work, staging, commit, push, branch, PR, or publication was performed by this
follow-up.

**Thread 03 handoff — 3 October 2026:** Implemented only deterministic read-only
inventory and path preflight on the pre-existing
`feature/3-thread-03-vault-inv-and-path-preflight` branch. It began clean and
matched local/live `main` and `origin/main` at `f48a5c5`. Dependencies were
verified from actual configuration/key/packaging code, closed issues #1/#2 with
maintainer review records, today's **121 passed, 1 skipped** baseline, and the
successful [Thread 02 merge Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37157742622)
for Linux/Python 3.12–3.14. The GitHub connector returned 404; authenticated
GitHub CLI access succeeded and was used for issue tracking.

- Added internal [inventory](../src/obfuscidian/inventory.py) and
  [path preflight](../src/obfuscidian/paths.py), using shared
  [limits/names](../src/obfuscidian/constants.py). Typed immutable records include
  relative names, file sizes, signed nanosecond times, and filesystem identities.
  Metadata-only scanning includes empty directories, all regular binary/hidden/
  config files, and vaults without `.obsidian`. All included records are sorted
  case-sensitively, independent of locale. No vault command is exposed.
- Mandatory Git/key exclusions and validated component globs prune before
  descent; excluded totals count encountered entries rather than unseen
  descendants. Git metadata is never traversed. The representative fixture
  inventories twice as **6 files, 5 directories, 7 excluded entries**, with
  identical source names/types/identities/modes/mtime/ctime and SHA-256 file
  hashes after scanning and stable binary reads. Access time is intentionally
  omitted because filesystem reads may update it.
- Preflight rejects roots, missing source/parents, links/junctions/special files,
  same/nested locations by spelling or identity, selected keys inside vaults and
  encountered file aliases, and unmanaged mirror names/types. Mirror inspection
  validates namespace only; authenticated format/completeness checks remain
  Thread 04, and Git-control legitimacy/publication remain later work.
- Stable reads are bounded binary I/O, with POSIX no-follow anchored handles,
  identity/size/mode/time comparisons, and post-read inventory rechecks. Synthetic
  changes during enumeration and reads, additions/deletions/renames/replacements,
  permission/allocation failures, and unsafe substitutions fail without accepting
  partial results. Unrelated sibling changes do not invalidate source inventory.
- Exact Fernet estimates agree with real tokens at empty/block/Base64 boundaries;
  objects and actual serialized-manifest accounting hooks enforce the 50 MiB cap.
  Staging hooks explicitly account for retained ciphertext and additional rollback
  copies, with read-only access/free-space checks. Safe staging-location selection,
  filesystem allocation/journal overhead, authentication, and writes remain later
  threads; no resource helper creates or reserves paths.
- Target helpers validate relative syntax, Windows reserved names, explicit
  case/Unicode comparison, ancestor-prefix collisions, and component/full-path
  bounds without renaming or filesystem probes. Native target comparison/length
  policy validation remains Thread 12; callers must supply actual filesystem rules.
- Added [unit inventory tests](../tests/unit/test_inventory.py),
  [unit path tests](../tests/unit/test_paths.py), and
  [synthetic integration scenarios](../tests/integration/test_inventory.py).
  Updated package archive allowlists and included the
  [inventory guide](../docs/INVENTORY.md) in the sdist. README, agent/contributor
  current-status notes, and changelog now describe this increment. Versions,
  runtime dependencies, lockfile, CLI, and workflows are unchanged.

**Executed validation:** Poetry 2.4.2 / Python 3.12.7 on macOS ARM64:

- `poetry check --lock --strict`, Ruff lint/format checks, full offline pytest
  through `poetry run coverage run -m pytest -q`, coverage reporting, and Bandit
  all passed: **258 passed, 2 skipped**. The skips require native Windows ACL
  APIs and native junction creation. Targeted inventory/path/integration tests
  passed separately: **137 passed, 1 skipped** (native junction).
- Coverage is **88%** overall; new inventory/path modules report **95%/97%**.
  Native Windows code remains unexecuted locally; installed CLI subprocesses
  are separately verified rather than included in this in-process measurement.
- Fresh `poetry build --output <fresh-candidate-directory>` produced exactly
  one wheel and sdist; strict Twine checks passed for both. Default offline
  archive/installation tests passed in the full suite. The same freshly built
  candidate artifacts passed an explicit `--artifact-dir` package-content and
  separate wheel/sdist installation run: **3 passed**, using available developer
  dependencies outside the checkout. Fully isolated wheelhouse-backed installs
  were not rerun because runtime dependencies/entry points were unchanged.
- Proposed-file local Markdown links/fences, LF, private absolute-path exclusion,
  Python AST/model/date headers, read-only mutation-call inspection, source/diff
  review, and `git diff --check` passed. The normal suite uses synthetic fixtures
  only; no source preservation claim comes from a real vault.

Python 3.13/3.14, hosted Linux CI for these uncommitted changes, native Windows
execution, broader OS validation, and Sphinx builds were not run. The verified
Linux/Python 3.12–3.14 result above belongs to the merged Thread 02 dependency,
not this change. Sphinx tooling/build remains Thread 13.

**Tracking/remaining:** Issue #3 receives matching start/progress/checklist/handoff
updates and stays open for maintainer review. All Thread 03 local acceptance
criteria are met; no remaining local blockers. Detection is best effort rather
than an atomic filesystem snapshot. Native Windows race/ACL/junction validation,
filesystem-specific comparison/length policy validation, and broader supported-OS
hardening remain Thread 12. Thread 04 — Encrypted backup format — is next after
review; Threads 04–14 were not implemented. No real vaults, keys, or cloud tests
were used, and no backup-writing/restore/verify command or format serializer was
exposed.

All proposed changes remain **unstaged and uncommitted** on the existing Thread 03
branch. No branch creation, staging, commit, push, PR, merge, tag, release,
publication, or workflow change/trigger was performed. Issue #3 remains open;
maintainer approval is still required for completion/closure.

**Thread 03 completion — 3 October 2026:** The maintainer confirmed review,
commit, merge/push, and completion, and explicitly requested closure of issue #3.
The implementation commit
[`982dae8`](https://github.com/jeffshurtliff/obfuscidian/commit/982dae8) is merged
into `origin/main` as
[`33c19fb`](https://github.com/jeffshurtliff/obfuscidian/commit/33c19fb).
Verified live GitHub `main` matches local `HEAD`, `main`, and `origin/main` at
[`51be612`](https://github.com/jeffshurtliff/obfuscidian/commit/51be612), which
contains that merge and subsequent maintainer changes. The
[Thread 03 merge Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37163121904)
and [current-main Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37164444283)
completed successfully, with all Linux/Python 3.12, 3.13, and 3.14 jobs passing.
Issue #3 is closed as completed and its maintainer-review/closure checklist item
is checked. All four subtasks and acceptance criteria are complete.

The earlier handoff retains its historical local-test, pending-review, Git,
and unexecuted-hosted-CI evidence; this completion record supersedes those
status statements. Native Windows runtime checks, filesystem-specific target
comparison/length policy validation, and broader OS hardening remain Thread 12.
Backup, restore, and verification commands remain unavailable.

Updated README.md, CONTRIBUTING.md, AGENTS.md, and this roadmap to reflect
completion and the next step. Thread 04 — Encrypted backup format — is next and
remains not started; the maintainer explicitly prohibited beginning it during
this follow-up. This documentation-only update checks local links, Markdown
fences/LF, status consistency, privacy, scope, and `git diff --check`. It does
not rerun application tests, artifact builds, or platform tests; existing hosted
CI results were verified without triggering a workflow. These four documentation
edits remain unstaged and uncommitted on `main`. No application or Thread 04
work, staging, commit, push, branch, PR, or publication was performed.

**Thread 04 handoff — 4 October 2026:** Implemented only the approved v1
format increment on the pre-existing `main` checkout, initially clean at
`a0d25b9`. Dependency readiness was verified from actual inventory/path/resource,
configuration/key, and packaging code, the closed issue #3 completion/merge/CI
record, and today's **258 passed, 2 skipped** baseline. The GitHub connector
returned 404; authenticated GitHub CLI access succeeded for issue tracking.

- Added internal [Fernet byte helpers](../src/obfuscidian/crypto.py) and
  [v1 manifest/complete validation](../src/obfuscidian/manifest.py), separate
  from the unchanged Click layer. Shared [format constants](../src/obfuscidian/constants.py)
  are independent of the unchanged package version `1.0.0.dev0`. No custom
  cryptography, new dependency, lockfile change, TTL, or vault command was added.
- Froze exact schema fields, compact canonical UTF-8 JSON, path sorting,
  32-lowercase-hex lineage/snapshot/object identifiers, UTC calendar timestamps,
  signed nanosecond times, and full SHA-256 bindings in the
  [format guide](../docs/FORMAT.md) and
  [immutable synthetic fixture](../tests/fixtures/v1/README.md). Parsing checks
  the 50 MiB encrypted limit, bounded plaintext/depth, duplicate JSON keys,
  exact types/fields, versions, unsafe paths, mandatory exclusions, duplicate
  IDs/paths, file/directory conflicts, and every required parent directory.
  Writers check actual serialized bytes and projected standard token length.
- Complete read-only validation requires the managed manifest/objects layout
  and exact object set. Every object passes ciphertext hash, Fernet
  authentication, plaintext size, and plaintext hash checks. Objects are read
  one at a time using bounded stable I/O; no aggregate payload is retained.
  Structured metadata is returned only after all objects and final namespace/
  identity checks pass. Validated reads/reuse repeat state and object checks.
  Unchanged content retains exact ciphertext and ID; metadata-only changes can
  reuse that token. Changed same-path content keeps its ID with a new token.
- [Unit crypto tests](../tests/unit/test_crypto.py),
  [unit schema tests](../tests/unit/test_manifest.py), and
  [synthetic integration tests](../tests/integration/test_format.py) prove exact
  mixed-byte reconstruction and source/mirror preservation. The fixed fixture
  contains **5 files and 4 directories**, including all 256 byte values, CRLF,
  Unicode, hidden/config content, zero bytes, and an empty directory. Its
  timestamp-zero tokens decrypt without a TTL; independent pinned artifact
  hashes prevent silent fixture replacement. Tests mutate temporary copies only.
- Tests reject equal-length valid token swaps, identical-plaintext re-encryption,
  wrong manifest/object keys, changed/truncated/missing/unexpected objects,
  incorrect bound size/hashes, hostile authenticated JSON/paths, target case/
  Unicode/Windows/length conflicts, links/special files, oversize sparse tokens,
  changed identities/content during open/read/complete verification, stale reuse,
  and access/allocation failures. Stream-construction failure closes the opened
  descriptor. Unrelated sibling changes do not invalidate the mirror. Existing
  and absent synthetic destinations remain unchanged; helpers emit no output.
- Updated README, contributor/agent current status, changelog, and sdist guide
  inclusion. Archive allowlists include the two modules and format guide, while
  excluding test keys/fixtures/private/generated material. Installed wheel and
  sdist imports validate the frozen fixture outside the checkout.

**Executed validation:** Poetry 2.4.2 / Python 3.12.7 on macOS ARM64:

- `poetry check --lock --strict`, `poetry run ruff check .`,
  `poetry run ruff format --check .`, full offline pytest via
  `poetry run coverage run -m pytest -q`, coverage reporting, and
  `poetry run bandit -r src/obfuscidian` passed: **454 passed, 2 skipped**.
  Skips require native Windows ACL APIs and junction creation. Overall coverage
  is **90%**, with **100% crypto / 95% manifest**; installed subprocess checks
  are verified separately. The new format tests account for 196 passing cases.
- Fresh `poetry build --output <fresh-candidate-directory>` built exactly one
  wheel and sdist, and strict Twine checks passed for both. The same candidates
  passed explicit archive/content and separate wheel/sdist installation checks:
  **3 passed**, using available developer dependencies outside the checkout.
  Fully isolated wheelhouse installs were not repeated; dependencies/entry
  points are unchanged. Default offline packaging checks also passed in the
  full suite.
- Proposed-file Markdown links/fences, LF/whitespace, AST/model/date headers,
  privacy and mirror artifact inspection, read-only mutation-call inspection,
  scope/source/diff review, and `git diff --check` passed. No real vault, real
  key, cloud service, release, or publication was used.

**Tracking/remaining:** All four subtasks and Thread 04 local acceptance criteria
are met. Issue #4 has start, progress, verified checklist, and handoff updates
and stays open for maintainer review. These local changes have not run hosted
Linux CI, Python 3.13/3.14, native Windows execution, broader OS validation,
or Sphinx. The dependency's recorded Linux matrix is not evidence for this
change. Windows/target-filesystem hardening remains Thread 12; docs tooling
remains Thread 13. No local acceptance blockers remain.

Validation is a best-effort read-only observation, not an atomic snapshot or
security certification. It cannot detect replay of a complete valid historic
snapshot; the key holder can forge valid data. Visible encrypted sizes/counts,
token times, and change patterns remain threat limits. The token cap is not a
total-vault resource quota. Root Git controls are inspected only for names/types,
not authenticated or interpreted. Actual target naming rules must be provided
by callers; timestamp representability belongs to restore. All publication,
locking/recovery, snapshot/no-op orchestration, Git operations, and vault commands
remain later work. Thread 05 — Safe publication and recovery — is the next
sequential thread after review; Thread 08 may separately precede it as approved
in the dependency index. Neither was started.

All 24 proposed files remain **unstaged and uncommitted on `main`**. No branch
creation, staging, commit, push, PR, merge, tag, release, publication, or workflow
edit/trigger occurred. New deliverables are local and will become available
remotely only through the maintainer's separately authorized Git workflow.

**Thread 04 completion — 4 October 2026:** The maintainer confirmed review,
commit, merge/push, and acceptance of Thread 04 and explicitly requested closure
of issue #4. The implementation commit
[`caf62b1`](https://github.com/jeffshurtliff/obfuscidian/commit/caf62b14c566e411605de00ab4c4ef74244c67d7)
is merged into `origin/main` as
[`9729772`](https://github.com/jeffshurtliff/obfuscidian/commit/9729772acf554fcb5504f1b9acba9b2af0b1b4a5).
Verified live GitHub `main` matches local `HEAD`, `main`, and `origin/main` at
that merge. The [Thread 04 merge Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37217437014)
completed successfully, including all Linux/Python 3.12, 3.13, and 3.14 jobs
and their style/security, offline-test/coverage, and fresh-artifact steps.
Issue #4 is closed as completed and its maintainer-review/closure checklist
item is checked. All four subtasks and acceptance criteria are complete.

The earlier handoff retains its historical local validation, pending-review,
uncommitted Git status, and unexecuted-hosted-CI evidence. This completion record
supersedes those status statements. Native Windows execution, target-filesystem
hardening, and broader supported-OS validation remain Thread 12 work; Sphinx
tooling remains Thread 13. Vault backup, restore, and verification commands
remain unavailable.

Updated README.md, CONTRIBUTING.md, AGENTS.md, and the roadmap's current status,
index, thread section, and completion record. Thread 05 — Safe publication and
recovery — is next sequentially and remains **not started**; the maintainer
explicitly prohibited beginning it during this follow-up. Threads 05–14 remain
not started. This documentation-only update verifies local Markdown links,
fences/LF, privacy, status consistency, four-file scope, and `git diff --check`.
Existing hosted CI was verified without triggering a workflow; application
tests, builds, and additional platform checks were not rerun. These four edits
remain **unstaged and uncommitted on `main`** for the maintainer to handle.
No application/Thread 05 work, staging, commit, push, branch, PR, merge, tag,
release, publication, or workflow change/trigger was performed by this follow-up.

**Thread 05 local handoff — 4 October 2026:** Implemented only safe publication
and recovery primitives. The runtime behavior is implemented locally; the thread
is not formally complete, merged, or closed. The maintainer confirmed
`GPT-6.1 Sol`; all five pending headers now use that attribution. Maintainer
review remains pending.

**Deliverables:**

- `src/obfuscidian/transactions.py`: read-only preflight/target rules, safe
  same-filesystem workspace selection outside vaults/enclosing Git markers,
  resource/access checks, exclusive POSIX OS ownership, bounded private
  write-ahead journals, complete proposal checks, and checked publication.
- Mirror publication replaces the `.obfuscidian` unit. Restore primitives leave
  root `.git` file/directory and `.gitignore` in place and optionally preserve
  root `.obsidian`. Nested repositories, unsafe payloads, target collisions,
  unmanaged mirrors, and unexpected changes are refused.
- Fresh success retains old payload outside Git. Durable observations/hash
  binding and conservative explicit recovery restore previous complete payloads
  without deleting uncertain/user-modified data. Interrupted recovery can be
  retried. Only a proven empty transaction-created root may be removed.
- Shared consent does not infer yes from non-interactive mode. Dry-run execution
  invokes no builder/verifier/prompt and creates no paths or transaction artifacts.
- `tests/unit/test_transactions.py` and
  `tests/integration/test_transactions.py`: 197 targeted cases, including
  synthetic byte/empty-directory preservation, temporary Git controls, every
  observed mutation boundary, short writes, before/after journal and rename
  failure, process death, competing live ownership, rollback failure,
  recovery interruption/retry, changed data/ancestors/containers, and privacy.
- [Transaction guide](../docs/TRANSACTIONS.md), unchanged-format integration
  notes, status/changelog synchronization, sdist documentation allowlist and
  artifact-content tests. No public vault command, new dependency, lockfile or
  crypto/backup-format change, or later-thread implementation was introduced.

**Dependency evidence:** Thread 04 code and closed issue #4 were checked,
including its maintainer review/merge and Linux/Python 3.12–3.14 evidence.
The targeted format baseline passed 162 cases. GitHub connector reads returned
404; authenticated CLI issue access works. Issue #5 has start/progress comments.

**Validation:** Poetry 2.4.2 / Python 3.12.7 / macOS ARM64. Full offline suite
passed 651 tests with 2 native Windows skips; targeted transaction tests passed
197. Strict Poetry lock, Ruff lint/format, Bandit, diff whitespace, Python
AST/date, local Markdown links/fences, LF/privacy/scope checks passed. Fresh
wheel/sdist, strict Twine and separate offline artifact-content/installed-entry
checks passed (3 cases), repeated against fresh final candidates after the last
safety edits. Coverage is 90% overall and 89% for `transactions.py`. Developer
dependencies were used for installation checks; fully isolated wheelhouse
installs were not repeated. The attribution follow-up checked all five updated
headers against the maintainer-confirmed `GPT-6.1 Sol` selection, verified
unchanged executable Python ASTs, and passed Ruff lint/format and diff whitespace
checks. Runtime tests and packaging were not rerun for the header/documentation-only
follow-up; the results above belong to the implementation validation.

**Limits/remaining:** Native Windows mutation intentionally fails closed until
Thread 12 adds locking/private-directory ACL support. Hosted Linux CI,
Python 3.13/3.14, Windows execution, network/cloud filesystems, and actual
power-loss validation were not run. Sphinx tooling remains Thread 13. No real
vault/key/cloud access occurred. Private rollback for restore contains plaintext;
there is no retention pruning. Callback orchestration must authenticate complete
restore source objects, estimate staged allocation, and recheck source inventory.
These primitives detect filesystem changes best effort, coordinate cooperating
writers, and do not guarantee power-loss recovery. An unconfirmed fsync after
terminal ownership unlink returns an explicit durability warning; the complete
new payload and retained old data remain available. Uncertain early ownership
or an unrecorded created-root identity remains blocked for deliberate inspection.

**Tracking/Git:** Issue #5 remains open for maintainer review. Generating-model
attribution is resolved by the maintainer's explicit confirmation of
`GPT-6.1 Sol`; future Codex threads use the model-selection default above unless
explicitly overridden. The 14 proposed files are unstaged/uncommitted on
the pre-existing `feature/5-thread-05-safe-pub-and-recovery` branch at `c71d16c`.
No branch creation, stage, commit, push, PR, merge, tag, release, publication or
workflow change/trigger occurred. Thread 06 — Fresh backup — is next sequentially
and **not started**; Threads 06–14 remain unimplemented. Thread 08 may separately
proceed under the approved dependency graph, but was not started here.

**Thread 05 completion — 4 October 2026:** The maintainer confirmed review,
commit, merge/push, and green CI, and explicitly requested closure of issue #5.
The implementation is complete; all four subtasks and acceptance criteria are
met. Earlier local handoff records describe the state at that time; this
completion record supersedes their pending-review, platform-CI, and Git-status
statements while retaining the documented safety limitations.

**Verified remote/Git evidence:** Implementation commit
[`4a0c1d4`](https://github.com/jeffshurtliff/obfuscidian/commit/4a0c1d409d3b5dad7641619df2975833518db00c)
is included in merge commit
[`dbec601`](https://github.com/jeffshurtliff/obfuscidian/commit/dbec6013b233a1a3e543a056fe20f7f65f6450db).
The live GitHub `refs/heads/main`, local `HEAD`/`main`, and `origin/main` all
match `dbec6013b233a1a3e543a056fe20f7f65f6450db`. The checkout was clean on
`main` before this documentation-only follow-up. No separate feature-commit
workflow run was returned; the successful merge run validates the exact pushed
implementation and is the closure evidence.

**Verified hosted validation:** The
[Thread 05 merge Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37236920352)
completed successfully for all three Linux jobs: Python 3.12, 3.13, and 3.14.
Each job passed locked installation/strict Poetry checks, Ruff lint/format,
Bandit, the full offline suite (**651 passed, 2 skipped**), coverage reporting
(**90% overall**), fresh wheel/sdist builds, strict Twine checks, and fully
isolated wheelhouse artifact installation/content checks (**3 passed** per job).
The two skips require native Windows ACL APIs and junction creation. These
hosted results supplement the earlier local macOS/Python 3.12 evidence.

**Limits and remaining work:** Native Windows transaction mutation still fails
closed pending Thread 12 ownership/private-directory ACL support. Broader OS,
network/cloud filesystem, actual power-loss, and strict Sphinx validation remain
unexecuted/deferred as documented. No real vault/key/cloud access occurred.
Publication remains multi-step, recovery conservative, and plaintext restore
rollback sensitive; source authentication/inventory orchestration remains the
responsibility of later callers. No public vault command is exposed.

**Tracking/handoff:** Issue #5 is closed as completed with its maintainer
review/closure checklist checked and the verified merge/CI evidence recorded.
README, AGENTS, CONTRIBUTING, and this roadmap's summary/index/thread section
are synchronized. Documentation link/fence, consistency, privacy, scope, and
`git diff --check` validation passed for this follow-up. Runtime tests, builds,
and platform tests were not rerun because only documentation changed.

Thread 06 — Fresh backup — is next sequentially and remains **not started**;
Threads 06–14 remain not started. The maintainer explicitly excluded Thread 06
from this request. No application, test, dependency, workflow, or later-thread
work was performed. The four completion-document edits remain **unstaged and
uncommitted on `main`** for the maintainer to handle. No branch creation, stage,
commit, push, PR, merge, tag, release, publication, or workflow change/trigger
was performed by this follow-up.

#### Thread 06 — Fresh backup implementation handoff (4 October 2026)

**Status:** Implemented locally; all four requested subtasks and the synthetic
acceptance/demo are met. Pending maintainer review; issue #6 remains open.
Thread 07 is next sequentially and **not started**; Threads 07–14 remain
unimplemented. This record supersedes earlier statements that Thread 06 had
not started, without altering those historical handoffs.

**Dependency readiness and issue tracking:** Read the root agent/contributor
guides, Thread 06 requirements and dependency contracts. Actual Thread 02–05
code is present on clean `main` baseline `2e61010`; issues #2–#5 are closed.
Issue #5 records reviewed/merged transaction implementation and Linux/Python
3.12–3.14 CI. A targeted dependency run passed **373 tests**. The GitHub
connector returned 404; authenticated `gh` reads/start/checklist/handoff updates
work. No local result is attributed to hosted CI.

**Deliverables:**

- [Internal fresh orchestration](../src/obfuscidian/backup.py): external selected
  key custody, CLI/environment path preflight, complete stable inventory,
  complete old-mirror authentication, one-file-at-a-time hashing and re-reading,
  exact bounded manifest/ciphertext estimates, consent requirements and no-op
  comparison before write artifacts. Placeholder metadata has the final
  serialized widths; no-op/dry run generate no IDs/tokens/timestamps.
- [CLI](../src/obfuscidian/cli.py): `shroud fresh` only, repeated exclusions,
  terminal-only missing-value/replacement prompts, explicit `--yes`,
  `--non-interactive`, `--dry-run`, `--recover` and escaped `--verbose` output.
  Counts/default output redact names and private locations. Public CLI docs
  retain the required bare initial-release directive. Optional logging remains
  Thread 11; unsupported options and later modes are rejected.
- Complete authenticated staging reuses validated unchanged ciphertext, keeps
  changed-path object IDs and lineage, assigns secure IDs to new paths, and
  publishes only the managed tree. Fresh removes absent/newly excluded records
  from the proposed snapshot. All previous encrypted data remains in external
  private rollback; origin content and root Git controls remain preserved.
- [Transactions](../src/obfuscidian/transactions.py): minimal orchestration
  integration adds a final source re-inventory callback before destination
  changes and selected-key authentication of complete mirror payloads before
  recovery inverse moves. V1 schema, cryptographic recipe and journal version
  are unchanged; no restore command or merge implementation was added.
- [Synthetic fresh integration tests](../tests/integration/test_fresh_backup.py),
  [installed artifact checks](../tests/integration/test_packaging.py), updated
  prior CLI-boundary assertions, [fresh backup guide](../docs/BACKUP.md),
  changelog and synchronized current status/help. The sdist includes the new
  guide; runtime dependencies, lockfile, version and CI/workflows are unchanged.

**Executed validation:** Poetry **2.4.2**, Python **3.12.7**, local macOS ARM64.

- Fresh integration suite: **68 passed**. Mixed hidden/config/nested Unicode,
  binary and zero-byte files, empty directories, mandatory/explicit exclusions,
  first backup into empty/absent mirrors, stale purge, exact unchanged token/ID
  reuse, metadata updates, lineage and independently authenticated rollback.
- Preservation assertions cover source bytes/identities/permissions/non-access
  timestamps and root Git file/directory/ignore controls. No Git execution is
  permitted in the backup test. No-op/dry run compare entire temporary tree
  observations and forbid randomness/staging/ownership/consent calls.
- Tests cover wrong keys, corrupt/unsupported/incomplete/extra-object mirrors,
  unsafe/unmanaged/link/overlap/key-alias/missing-parent locations, encrypted
  size/manifest/space limits, declined/EOF/unattended consent, source edits/adds/
  deletes/replaced parents and late source changes after the ready checkpoint.
- Stage/write/allocation/validation/rename/interrupt failures preserve the old
  complete snapshot. Blocked rollback gates writes/dry run; consented recovery
  restores previous state before retrying, refusing wrong keys and edited
  retained bytes. Real subprocess termination at ready, old-moved and new-moved
  boundaries exercises end-to-end CLI recovery. Existing transaction tests
  retain their broader deterministic fault-boundary and process coverage.
- Full `poetry run coverage run -m pytest -q`: **718 passed, 2 skipped**;
  `poetry run coverage report`: **90% overall**, **94% backup**, **92% CLI**.
  Both skips require native Windows ACL/junction APIs. The earlier plain pytest
  run exposed two obsolete command-boundary assertions; those were corrected
  and the final coverage run passed in full.
- `poetry check --lock --strict`, `poetry run ruff check .`,
  `poetry run ruff format --check .`, `poetry run bandit -r src/obfuscidian`,
  and `git diff --check` passed.
- Fresh `poetry build --output` wheel/sdist and strict Twine checks passed.
  Explicit final-candidate packaging checks passed **3 cases**: content allowlist
  and separate wheel/sdist installs outside the checkout, console/module help,
  synthetic fresh dry run/publication/no-op and shared-validator byte checks.
  These use available developer dependencies; fully isolated wheelhouse mode
  was not rerun. Direct console/module fresh help also passed.
- Proposed-file headers/dates, Python AST, Markdown links/anchors/fences, LF,
  privacy, scope and final diff checks passed. Model headers use the recorded
  maintainer-confirmed `GPT-6.1 Sol` default, with `04 Oct 2026` dates.

**Limits and remaining work:** No implementation acceptance blocker remains;
maintainer review and any separately authorized Git workflow are pending.
Native Windows mutation fails closed pending Thread 12; no native Windows run,
Python 3.13/3.14 run or hosted Linux CI for these uncommitted changes is claimed.
Network/cloud filesystems, power-loss behavior, hostile same-authority writers
and real vault tests were not exercised. Rechecks are best effort and multi-step
renames are not universally atomic. Private recovery data is retained without
pruning; uncertain/user-modified artifacts remain blocked rather than deleted.
Fresh managed names use fixed lowercase ASCII/hex; conservative case/Unicode
ownership comparison serializes aliases without writable probes and reads POSIX
limits from the destination filesystem. Actual restore naming policies remain
for later restore/platform work. Sphinx is deferred to Thread 13. Merge backup,
restore, public verification and optional logging remain unavailable.

**Git handoff:** **19 files** are changed/new, unstaged and uncommitted on
`codex/feature/6-shroud-fresh`, based on `main` at `2e61010`. No stage, commit,
push, PR, merge, tag, release, publication or workflow trigger occurred. Only
temporary synthetic vaults, generated test keys and Git metadata were used;
no private local reference content or real vault/key/cloud data was inspected.
The new branch is the only Git setup mutation. Issue #6 stays open for review.

#### Thread 06 — Fresh backup completion record (5 October 2026)

**Maintainer decision:** The maintainer confirmed that the changes were reviewed,
committed, merged, pushed and green in CI, explicitly requested closure of issue
#6, and prohibited beginning Thread 07. All four subtasks and acceptance criteria
are met; no Thread 06 acceptance blocker remains. Earlier implementation/handoff
records are historical; this record supersedes their pending-review, local-only
validation and uncommitted-implementation statements.

**Verified implementation and remote state:** Implementation commit `6d3bf28`
is included in pushed `main` merge
[`fea9217`](https://github.com/jeffshurtliff/obfuscidian/commit/fea92170736e16038b87d6c391b517c752f28e24).
Local `HEAD`/`main`, `origin/main` and the live remote `main` ref all matched
`fea92170736e16038b87d6c391b517c752f28e24` before this documentation-only update.
The checkout was clean on `main`; no Git history operation was needed.

**Hosted validation:** The
[merged-commit Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37315634336)
completed successfully on Linux/Python **3.12, 3.13 and 3.14** for that exact
merge SHA. Each job reported **718 passed, 2 skipped**, **90% overall coverage**,
and **3 passing fully isolated wheelhouse artifact checks**. Strict Poetry lock
checks, Ruff lint/format, Bandit, fresh wheel/sdist builds and strict Twine
validation also passed. The skips require native Windows ACL/junction APIs;
Linux results do not establish native Windows validation.

**Merged deliverables:**

- [Fresh orchestration](../src/obfuscidian/backup.py) and
  [CLI](../src/obfuscidian/cli.py): `shroud fresh` with stable binary reads,
  complete mirror authentication, ciphertext reuse, stale removal, retained
  external encrypted rollback, consent, no-write no-op/dry-run behavior, and
  explicit recovery/retry. Origin and Git controls stay preserved.
- [Transaction integration](../src/obfuscidian/transactions.py),
  [fresh integration tests](../tests/integration/test_fresh_backup.py),
  [installed-artifact tests](../tests/integration/test_packaging.py), and
  [backup guide](../docs/BACKUP.md). The format, runtime dependencies, package
  version and CI/workflow configuration remain unchanged by this follow-up.

**Tracking and documentation handoff:** Issue #6 is closed as completed with
the maintainer review/closure checkbox checked and merge/CI evidence recorded.
README, AGENTS, CONTRIBUTING, the backup guide, and this roadmap's summary,
index and per-thread status are synchronized. Local Markdown links/anchors/
fences, current-status consistency, privacy, LF, scope and `git diff --check`
passed. Runtime tests/builds were not rerun because only documentation changed;
the hosted results above were inspected directly.

**Limits and next work:** Native Windows mutation fails closed until Thread 12;
broader OS/network/cloud and actual power-loss validation remain deferred.
Change detection is best effort, and multi-step publication is not universally
atomic or guaranteed recovery. Sphinx remains Thread 13. No real vault/key/cloud
tests or supported-platform/security certification are claimed.
Thread 07 — Merge backup — is next sequentially and **not started**; Threads
07–14 remain not started. No later-thread implementation was performed.

**Current Git status:** These **five documentation edits remain unstaged and
uncommitted on `main`** for maintainer review. No application, tests, dependency,
format or workflow files were changed. No branch creation, staging, commit,
push, PR, merge, tag, release, publication or workflow trigger occurred during
this closure follow-up.

### Thread 07 — Merge backup handoff: 5 October 2026

This historical implementation handoff is superseded for current status by the
[completion record](#thread-07--merge-backup-completion-record-5-october-2026) below.

**Status:** Implemented locally and validated; pending maintainer review.
All four subtasks and acceptance/demo are met with synthetic fixtures. Issue #7
remains open; changes are unstaged/uncommitted on the existing
`feature/7-thread-07-merge-backup` branch at baseline `387a121`. Thread 08 is next
and **not started**; Threads 08–14 remain unimplemented. Hosted CI has not run
for these edits.

**Deliverables and behavior:**

- [Backup orchestration](../src/obfuscidian/backup.py) shares fresh/merge preflight,
  planning, staging and recovery. Merge authenticates the whole old snapshot,
  unions current included paths with old files/directories, classifies new,
  changed, metadata-only, unchanged and retained files, and accounts for retained
  ciphertext in complete staging-space estimates. New mirrors initialize safely.
- [CLI](../src/obfuscidian/cli.py) exposes `shroud fresh|merge`. Existing-path edits
  preserve IDs, unchanged/metadata-only content preserves exact ciphertext, and
  renames get new IDs while retaining the old path. Absent/excluded files and empty
  directories keep their records. Type/ancestor conflicts fail before artifacts
  with guidance to use fresh. Only content replacement prompts in merge.
- [Transactions](../src/obfuscidian/transactions.py) reuse complete staging,
  validation, publication and recovery. Successful merge removes only its own
  proven temporary workspace after publication/ownership release. Older fresh
  rollback and failed/recovered workspaces stay retained. Changed/unknown/link
  artifacts and malformed journals refuse cleanup with redacted warnings;
  cleanup failures never reverse a completed publication. A failed final flush
  reports durability uncertainty and actual retention, not nonexistent rollback.
- [Merge integration tests](../tests/integration/test_merge_backup.py) exercise
  first/repeated/add/edit/delete/rename/exclusion/re-inclusion, empty current
  inventories, metadata updates, stable IDs/tokens, consent, type conflicts,
  retained-object corruption, explicit invalid keys, resource limits, source
  changes, failures, process death and explicit recovery. Sorted complete tree
  observations compare bytes, identities, permissions, mtimes/ctimes and namespaces
  across no-ops; randomness/encryption/time/ownership/staging/consent calls are
  prohibited. Read-induced access times are excluded.
- [Installed-entry tests](../tests/integration/test_packaging.py) exercise console
  and module merge, rename retention, exact old ciphertext, no-op mtimes and
  authenticated retained-byte reconstruction outside the checkout. The
  [backup guide](../docs/BACKUP.md), help, changelog, README and status/reference
  guides explain that **deleted notes can return during restore**. Restore and
  public verification remain unavailable; reconstructibility is proved through
  existing authenticated readers, without starting a restore thread.

**Executed validation:** Poetry 2.4.2, Python 3.12.7, local macOS ARM64.
Dependency fresh/transaction tests passed **265** cases before implementation;
expanded backup/transaction validation passed **340** cases. The final full
`poetry run pytest -q` passed **797 tests, 2 native Windows skips**; this includes
**79 merge cases**. Strict Poetry lock check, Ruff lint/format, Bandit (no issues),
console/module help, fresh wheel/sdist builds and strict Twine passed. Final
candidate package checks passed **3** cases, including separate wheel/sdist
installs, archive boundaries and installed merge workflows. These installs use
available developer dependencies; fully isolated wheelhouse mode was not rerun.
Final local links/anchors/fences, Python AST/model/date headers, privacy/LF/scope,
Git status and `git diff --check` passed.

**Limits and remaining work:** Maintainer review and any separately authorized
Git workflow remain. No implementation acceptance blocker remains. Native Windows
mutation still fails closed pending Thread 12; native Windows, Python 3.13/3.14
and hosted Linux CI were not run for these edits. Real vault/key/cloud access,
network/cloud filesystems, actual power loss and Sphinx (Thread 13) were not
validated. Rechecks/cleanup are best effort against same-authority writers,
not an atomic source snapshot or a universal recovery guarantee. Format version,
Fernet recipe, dependencies, lockfile, package version and workflows are unchanged.

**Git/issue handoff:** Fifteen changed/new files remain unstaged/uncommitted.
No branch change, staging, commit, push, PR, merge, tag, release, publication or
workflow trigger occurred. Issue #7's status and verified checklist were updated,
and its [final handoff](https://github.com/jeffshurtliff/obfuscidian/issues/7#issuecomment-5997774038)
was posted through authenticated CLI access (the connector returned 404). The
issue remains open; maintainer review/closure stays pending.
Earlier completion records below/above describe their own historical scopes and
are superseded by this record for current Thread 07 status.

### Thread 07 — Merge backup completion record: 5 October 2026

The maintainer confirmed review, commit, merge/push and green CI, and explicitly
requested issue #7 closure. All four subtasks and acceptance criteria are met;
no Thread 07 acceptance blocker remains.

Implementation commit [`8171898`](https://github.com/jeffshurtliff/obfuscidian/commit/8171898e63a2f84cd90b79da860de2dc982872b9)
is included in pushed main merge
[`e0086e8`](https://github.com/jeffshurtliff/obfuscidian/commit/e0086e841750d639bd897d9a3eb0ab7d032518a0).
Local HEAD/main, origin/main and the live remote main ref match that exact merge
SHA. The checkout was clean before this documentation-only completion update.

The [merged-commit Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37336476695)
passed on Linux/Python 3.12, 3.13 and 3.14. Each job reported **797 passed,
2 native Windows skips**, **90% overall coverage** (**96% backup**, **94% CLI**),
and **3 passing fully isolated wheelhouse artifact checks**, plus successful
strict Poetry lock checks, Ruff lint/format, Bandit, fresh wheel/sdist builds and
strict Twine. CI metadata and actual job logs were inspected directly; these
results apply to the pushed merge, not merely the earlier local proposal.

Merged deliverables include [backup orchestration](https://github.com/jeffshurtliff/obfuscidian/blob/e0086e841750d639bd897d9a3eb0ab7d032518a0/src/obfuscidian/backup.py),
[CLI](https://github.com/jeffshurtliff/obfuscidian/blob/e0086e841750d639bd897d9a3eb0ab7d032518a0/src/obfuscidian/cli.py),
[transactions](https://github.com/jeffshurtliff/obfuscidian/blob/e0086e841750d639bd897d9a3eb0ab7d032518a0/src/obfuscidian/transactions.py),
[synthetic merge tests](https://github.com/jeffshurtliff/obfuscidian/blob/e0086e841750d639bd897d9a3eb0ab7d032518a0/tests/integration/test_merge_backup.py),
and [backup guide](https://github.com/jeffshurtliff/obfuscidian/blob/e0086e841750d639bd897d9a3eb0ab7d032518a0/docs/BACKUP.md).
Earlier handoff records/comments remain historical; this completion evidence
supersedes their pending-review, local-only CI and uncommitted-implementation
statements.

Issue #7 is closed as completed under the maintainer's explicit request, with
its [completion evidence](https://github.com/jeffshurtliff/obfuscidian/issues/7#issuecomment-5998332979)
and review/closure checkbox synchronized. The roadmap
summary, index, Thread 07 status and completion record, README, AGENTS,
CONTRIBUTING and backup guide now reflect reviewed/merged completion.

Local links/anchors/fences, current-status consistency, privacy/LF/scope and
`git diff --check` passed for this documentation-only follow-up. Runtime tests
and builds were not rerun locally; hosted merged-commit evidence was verified.
Native Windows mutation remains deferred/fails closed until Thread 12; broader
OS/network/cloud filesystems, actual power loss and Sphinx retain their documented
limits. Linux CI does not establish native Windows validation or universal
recovery guarantees. No real vault/key/cloud access was performed.

**Thread 08 — Read-only verification — remains not started**; Threads 08–14
remain unimplemented. No application, test, dependency, format or workflow file
was changed during this closure follow-up.

**Current Git status:** These **five documentation edits remain unstaged and
uncommitted on `main`** for maintainer review. No branch creation, staging,
commit, push, PR, merge, tag, release, publication or workflow trigger occurred
during this follow-up. The implementation's commit/merge/push were performed
by the maintainer before this request.

### Deferred capabilities

- Thread 12: validate minimum Git capabilities and broader platforms for isolated
  worktree plumbing, raw-byte/conversion constraints and local object availability.
  Merge retained-artifact recovery after process death is manual; automated
  Git ownership recovery needs a separately approved durable recovery design.

- Password-derived keys and keychain integration: require a separately reviewed
  KDF/storage/recovery design; do not treat a password as a Fernet key.
- Automated key rotation/rekeying and multiple-key support: include format and
  Git-history implications. Old keys still decrypt historic backups; rotation
  cannot revoke copies already obtained.
- Chunked authenticated encryption: needs a versioned format authenticating
  ordering, completeness, and final length before large-attachment support.
- Git LFS, configurable larger-file caps, remote privacy/configuration checks,
  Git-host integration, automatic commit/push/merge, and repository pruning.
- Scheduling/watch mode, sync conflict handling, Obsidian plugins, GUI features,
  remote/cloud transfers, and profile/configuration files beyond environment/CLI.
- Advanced ownership/ACL/xattr preservation, link handling, automatic rename
  detection, selective restore, additional mirror control files, and rollback
  retention/pruning automation.
- Independent cryptographic/security review before broad production use;
  scanners and test coverage do not amount to a security certification.

Add newly discovered tasks here or to an explicitly scoped future thread rather
than expanding the current implementation request. Bugs required to satisfy a
thread's acceptance criteria stay in that thread; unrelated enhancements do not.

### Reference sources

These informed the planning review; recheck release-sensitive details during the
relevant implementation thread instead of pinning assumptions indefinitely.

- [Click stable documentation](https://click.palletsprojects.com/en/stable/),
  [options](https://click.palletsprojects.com/en/stable/options/), and
  [testing](https://click.palletsprojects.com/en/stable/testing/).
- [Fernet recipe, cryptography 50.0.2](https://cryptography.io/en/50.0.2/fernet/).
- [Git worktree](https://git-scm.com/docs/git-worktree) and
  [branch validation](https://git-scm.com/docs/git-check-ref-format).
- [GitHub large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
- [Poetry project metadata](https://python-poetry.org/docs/pyproject/).
- [click-app template](https://github.com/simonw/click-app).
- [SalesPyForce agent guide](https://github.com/jeffshurtliff/salespyforce/blob/master/AGENTS.md)
  and [PyDPlus agent guide](https://github.com/jeffshurtliff/pydplus/blob/main/AGENTS.md):
  their local working copies were inspected for agent conventions and docs style.

### Thread 08 — Read-only verification handoff (5 October 2026)

This historical handoff records the pre-review state. The completion record
below supersedes its pending-review, local-only CI and uncommitted-implementation
statements.

**Status:** Implemented and locally validated; pending maintainer review.
All four Thread 08 subtasks and local acceptance criteria are met. Issue #8
remains open. Changes are unstaged/uncommitted on the pre-existing
`feature/8-thread-08-read-only-verification` branch at baseline `ef7ce2b`.
Thread 09 is the next sequential thread and **not started**; Threads 09–14
remain planned. No Git history, publication or workflow action occurred.

**Dependency readiness:** Actual Thread 04 codec/validator/fixture code is
present. Its closed issue #4 records maintainer approval, merge/push and green
Linux Python 3.12–3.14 CI. The initial crypto/manifest/format suite passed
**196 tests** before implementation. The GitHub connector returned 404;
authenticated CLI access read issues #8/#4 and posted the issue #8 start update.

**Local proposed deliverables:**

- [Click verify/help](../src/obfuscidian/cli.py) and the internal
  [verification adapter](../src/obfuscidian/verification.py), using the existing
  complete v1 validator without format or cryptography changes.
- [Synthetic verify integration tests](../tests/integration/test_verify.py),
  updated command-availability tests and
  [wheel/sdist entry-point checks](../tests/integration/test_packaging.py).
- [Verification guide](../docs/VERIFY.md), synchronized README/agent/contributor
  status and related guides, [changelog](../docs/CHANGELOG.md), and an explicit
  sdist documentation inclusion. Runtime dependencies, lockfile, package
  version, mutation helpers and backup behavior remain unchanged.

**Behavior and acceptance evidence:** CLI/environment mirror and key selection
reuse existing key precedence/conflict rules, with prompts only for absent
selectors on terminal input. Origin configuration is ignored; keys inside the
mirror are rejected. Complete validation authenticates the manifest before
parsing and checks schema/path safety, exact object namespace, every token's
ciphertext binding, authentication, plaintext size/hash and final state.
Counts appear only on complete success. Opt-in verbose relative names are
escaped and appear only after every object passes; no keys, hashes, content or
absolute mirror/key paths appear in normal/verbose results or errors.

Canonical ownership markers are inspected in all mirror ancestors before and
after validation, without opening private journals or acquiring ownership.
Malformed/directory/broken-link markers and missing pending payloads fail
without recovery; retained completed workspaces without ownership remain
untouched. Write, repair, recovery, dry-run, consent, logging, exclusion and
restore options are rejected. Exit categories are `0` success, `1` incomplete/
integrity/pending/I/O failure, `2` usage/configuration, and `130` interruption.
Missing data and unknown versions include redacted remediation guidance.

The new verify suite covers valid mixed-content and empty mirrors, the last
object as well as earlier objects, wrong keys, manifest/object tampering and
truncation, malformed/duplicate JSON, unsafe names/links, missing/unexpected
data, equal-length swaps, binding/authentication failures and sparse oversize
tokens rejected before open. It also covers selector precedence/conflicts,
missing selected keys without fallback/regeneration, terminal/EOF behavior,
permissions/allocation/interruption failures, escaped terminal controls and
pending ownership at multiple ancestor levels. Read-only permission tests prove
no writable location or staging-space estimate is required.

Every guarded CLI case compares the entire temporary tree's namespace,
bytes/digests, identities, permissions, sizes, mtimes and ctimes before/after.
Instrumentation additionally rejects write-mode opens, descriptor writes,
filesystem mutation and subprocess execution across all paths, recording even
caught or transient attempts. Success, failure, help, options and interruption
make no application writes. OS read-induced access times are intentionally
excluded. Installed console/module verification has matching help/results and
preserves mirror bytes/file lists/mtimes for both wheel and sdist.

**Executed validation:** Poetry 2.4.2 / Python 3.12.7 / macOS ARM64.

- `poetry check --lock --strict`, `poetry run ruff check .`, and
  `poetry run ruff format --check .` passed.
- Final `poetry run coverage run -m pytest -q` passed **903 tests, 2 skipped**;
  the skips require native Windows ACL APIs and junction creation. Full-suite
  wheel/sdist content and separate installed console/module checks passed using
  available developer dependencies outside the checkout. An earlier full run
  identified two stale command-availability expectations; those were updated
  and the final full run passed. The final focused run passed **109 tests**,
  including **107 verify cases** and those two expectations.
- `poetry run coverage report`: **91% overall, 100% verification adapter**.
  Installed subprocess execution is outside these coverage totals.
- `poetry run bandit -r src/obfuscidian`: no issues. Fresh `poetry build`
  wheel/sdist candidates and `poetry run twine check --strict` passed.
- Proposed-file local Markdown links/anchors/fences, Python AST/model/date
  headers, identifying-path checks, source/no-write/scope/diff review and
  `git diff --check` passed. No private fixtures or real vault/key data were used.

**Limitations/unexecuted checks:** Hosted Linux CI, Python 3.13/3.14, native
Windows and broader OS tests, real vault/cloud tests, and Sphinx (Thread 13)
were not run. Fully isolated wheelhouse installs were not repeated; default
offline installed-artifact checks used available developer dependencies.
Verification is a best-effort observation, not an atomic snapshot, certification,
freshness proof or target-platform restorability check. It detects existing
and observed pending ownership but does not lock against later writers. OS reads
may change access times; valid historic snapshots and key-holder-forged data
can pass. Root Git controls are checked for allowed names/types only.

**Tracking/Git handoff:** Issue #8's implementation and executed-progress
checklists are updated, and a public-safe handoff is posted; maintainer
review/closure remains unchecked. All **20 proposed files** remain local,
unstaged/uncommitted. New/updated code and docs will become remotely available
only through a separately authorized Git workflow. No local acceptance blocker
remains; maintainer review and hosted validation are outstanding. Thread 09
was not started.


### Thread 08 — Read-only verification completion record (5 October 2026)

The maintainer confirmed merge/push into `origin/main`, green CI and acceptance
of Thread 08, and explicitly requested issue #8 closure. All four subtasks and
acceptance criteria are complete; issue #8 is closed as completed and its
maintainer-review/closure checkbox is checked. The
[issue completion evidence](https://github.com/jeffshurtliff/obfuscidian/issues/8#issuecomment-6000104604)
records the verified merge and CI results.

**Verified Git evidence:** Implementation commit
[`9c232a5`](https://github.com/jeffshurtliff/obfuscidian/commit/9c232a5)
and annotation follow-up
[`26e8dec`](https://github.com/jeffshurtliff/obfuscidian/commit/26e8dec)
were merged through
[`ce3cf78`](https://github.com/jeffshurtliff/obfuscidian/commit/ce3cf78e29803e175ab0303627cf144fb21ac056).
The subsequent style correction
[`3d3425b`](https://github.com/jeffshurtliff/obfuscidian/commit/3d3425b6a10e529b1e608fe93b4fb2d883db3a16)
is the exact CI-verified commit. Local `HEAD`, `main` and `origin/main` and the
live GitHub `main` commit all matched
`3d3425b6a10e529b1e608fe93b4fb2d883db3a16` at verification. The implementation
and annotation commits are ancestors of that head; the checkout was clean
before these documentation-only completion edits.

**Hosted validation:** GitHub Actions
[Test run 37349183494](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37349183494)
completed successfully on the exact head above. All Linux Python **3.12, 3.13
and 3.14** jobs passed, each reporting **903 tests passed, 2 skipped**, plus
**3 fully isolated wheel/sdist artifact checks passed**. Logs confirm strict
Poetry lock checks, Ruff lint/format, Bandit with no issues, coverage reporting,
fresh wheel/sdist builds, strict Twine validation, dependency wheelhouse
creation and installed-artifact validation. The two main-suite skips require
native Windows ACL APIs and junction creation. These results establish hosted
Linux validation separately from the earlier macOS local handoff.

**Merged deliverables:**
[Click verify/help](https://github.com/jeffshurtliff/obfuscidian/blob/3d3425b6a10e529b1e608fe93b4fb2d883db3a16/src/obfuscidian/cli.py),
[read-only verification adapter](https://github.com/jeffshurtliff/obfuscidian/blob/3d3425b6a10e529b1e608fe93b4fb2d883db3a16/src/obfuscidian/verification.py),
[synthetic verify tests](https://github.com/jeffshurtliff/obfuscidian/blob/3d3425b6a10e529b1e608fe93b4fb2d883db3a16/tests/integration/test_verify.py),
[installed-entry checks](https://github.com/jeffshurtliff/obfuscidian/blob/3d3425b6a10e529b1e608fe93b4fb2d883db3a16/tests/integration/test_packaging.py)
and [verification guide](https://github.com/jeffshurtliff/obfuscidian/blob/3d3425b6a10e529b1e608fe93b4fb2d883db3a16/docs/VERIFY.md).
The existing complete v1 validator authenticates all manifest/object data;
verification detects pending ownership without repair and rejects write/log/
recovery/exclusion options. Synthetic tests cover valid/corrupt/privacy cases
and zero application writes. Earlier handoff records/comments remain historical;
this completion record supersedes their pending-review, local-only CI and
uncommitted-implementation statements.

The roadmap summary, index, Thread 08 status and completion record, README,
AGENTS, CONTRIBUTING, backup guide and verification guide now reflect reviewed/
merged completion and issue closure. Local links/anchors/fences, status
consistency, privacy/LF/scope checks and `git diff --check` passed for this
follow-up. Runtime tests and builds were not rerun locally; hosted merged-commit
results and logs were verified. No application, test, dependency, format or
workflow file was changed for closure.

Native Windows mutation remains deferred/fails closed until Thread 12. Broader
OS/network/cloud filesystems, actual power loss and Sphinx retain their documented
limits. Linux CI does not establish native Windows validation or security
certification. Verification remains a best-effort observation, with possible
OS access-time changes on reads. No real vault/key/cloud access was performed.

**Thread 09 — Fresh restore — remains not started**; Threads 09–14 remain
planned. No work on Thread 09 was initiated or delegated.

**Current Git status:** These **six documentation edits remain unstaged and
uncommitted on `main`** for maintainer review. No branch creation, staging,
commit, push, PR, merge, tag, release, publication or workflow trigger occurred
during this follow-up. The implementation's commit/merge/push were performed
by the maintainer before this request.

### Thread 09 — Fresh restore implementation handoff (5 October 2026)

**Status:** Implemented locally; all four requested subtasks and the synthetic
acceptance/demo are met. Awaiting maintainer review. Issue #9 remains open;
Thread 10 — Git merge restore — remains **not started**. No later command,
worktree creation, Git history, release or publication action was implemented.

**Dependency and scope evidence:** Read root `AGENTS.md`, `CONTRIBUTING.md`,
this roadmap and live issues #9, #5, #7 and #8. Dependency issues are closed with
implementation/validation evidence. Inspected complete mirror authentication,
backup retention, no-follow path checks and transaction fault/recovery behavior.
Baseline HEAD, main and origin/main all matched `1a49473` before work; the
existing branch was clean. Used maintainer-requested `GPT-6.1 Sol` attribution
and `05 Oct 2026` on changed Python headers.

**Deliverables and acceptance:**

- [Restore orchestration](../src/obfuscidian/restore.py): read-only direction and
  key-custody preflight, complete manifest/object authentication (including
  skipped settings), target/control alias checks, allocation/space estimates,
  selected-key hard-link refusal and encrypted source ownership checks before
  plaintext staging. Actual component/path length constraints include staging.
- [CLI](../src/obfuscidian/cli.py): only `unshroud fresh`, existing CLI/environment
  key/path precedence, terminal-only prompts, explicit replacement/recovery
  consent, no-write dry run, escaped opt-in names and sensitive rollback paths.
  Source authentication precedes recovery; recovery restores proven old state
  before replanning/retrying. Failure/interrupt output never claims success.
- [Path preflight](../src/obfuscidian/paths.py) supports restore direction without
  relaxing backup safety. Private same-filesystem staging reconstructs exact
  binary bytes, hidden/zero-byte files, relative structure and empty folders.
  Supported times are checked after reconstruction; directory times are set
  after children, and unsupported timestamps produce a redacted warning.
- Existing [transactions](../src/obfuscidian/transactions.py) publish only the
  fully compared staged namespace/hash/size/time proposal. Root `.git` and
  `.gitignore` stay in place; `--preserve-config` preserves `.obsidian`, including
  its absence. Other old files, including historically excluded files, move to
  externally retained sensitive plaintext rollback. Nested repositories, control
  aliases, links/junctions, special files and unsafe target shapes are refused.
- [Synthetic integration tests](../tests/integration/test_fresh_restore.py):
  fresh and merge-backup round trips (including retained stale/excluded data),
  bytes/empty trees/times, root Git file/directory/absence, settings preservation,
  rollback location/modes, corruption/substitution/wrong keys, hostile schema and
  target names, overlap/key aliases, resource failures, consent/refusal/EOF,
  dry-run observations, changed source/key/destination/staging, failed writes,
  allocation/verification/rename failures, interrupts, process death, pending
  ownership, conservative recovery and user-modified artifact preservation.
- [Packaging tests](../tests/integration/test_packaging.py) include the new
  module/guide and exercise console/module dry-run and real fresh restore from
  merge backups outside the checkout. [Fresh restore guide](../docs/RESTORE.md),
  README, related guides, contributor/agent status and changelog are synchronized.

**Executed checks:**

- `poetry check --lock --strict`: passed; no dependencies or lockfile changes.
- `poetry run ruff check .` and `poetry run ruff format --check .`: passed.
- `poetry run coverage run -m pytest -q`: **996 passed, 2 native Windows skips**
  on local macOS/Python 3.12.7. This executes the full pytest suite with coverage.
- `poetry run coverage report`: **91% total**, **95% restore orchestration**.
- `poetry run pytest -q tests/integration/test_fresh_restore.py`: **94 passed**.
- `poetry run bandit -r src/obfuscidian`: passed, no findings.
- `poetry build --output <fresh-candidate>`: new wheel and sdist built; strict
  Twine validation passed for exactly those artifacts.
- Packaging tests against that candidate with an existing offline Python 3.12
  wheelhouse: **3 passed**, including separately isolated wheel/sdist installs,
  console/module restore, content boundaries and `pip check`. The full suite
  separately exercised the development-dependency installation mode.
- Local Markdown links/anchors/fences, LF/header attribution, status consistency,
  privacy/scope, diff whitespace and final Git status checked.

**Limits and next work:** No real vault/cloud operation, hosted CI, local
Python 3.13/3.14 matrix, native Windows mutation, universal filesystem/power-loss
validation, or Sphinx build was performed. Mutation remains POSIX-only and
fails closed on native Windows. Timestamp fidelity varies by filesystem;
ownership/ACLs/xattrs/executable modes are not imported. Target comparisons use
conservative case-folded NFC checks, which can refuse distinct valid names on
case-sensitive filesystems; precise capability detection is recorded for
Thread 12. Source stability and crash recovery remain best-effort under the
existing transaction threat model, not atomicity or power-loss guarantees.

**Git and issue handoff:** All changes remain unstaged/uncommitted on
`feature/9-thread-09-fresh-restore` at baseline `1a49473`; no stage, commit, push,
PR, merge, tag, release or publication action was performed. Start and final
handoff/checklist updates are posted to issue #9. Maintainer review/closure and
separately authorized Git/hosted validation remain outstanding. The next eligible
implementation is Thread 10 after review/acceptance of Thread 09; it is not started.

### Thread 09 — Fresh restore completion record (5 October 2026)

**Maintainer decision and status:** The maintainer reviewed, committed, merged
and pushed Thread 09, accepted the successful Python 3.12/3.13 CI results despite
the runner-unavailable Python 3.14 cancellation, and explicitly requested closure
of issue #9. All four subtasks and the acceptance/demo are met. Thread 09 is
**complete**; issue #9 is closed as completed. This is a thread acceptance decision,
not a claim that the full Python matrix passed or that 3.14 support was removed.

**Commit and remote evidence:** Implementation commit
[`a6c401d`](https://github.com/jeffshurtliff/obfuscidian/commit/a6c401d) is included
in pushed main merge
[`2caadac`](https://github.com/jeffshurtliff/obfuscidian/commit/2caadac390752a60f1bf19945ac62799f4f61f7f).
Local HEAD/main, origin/main and the live remote main ref all matched that exact
merge when checked. The checkout was clean before this documentation follow-up.
Earlier handoff records retain their historical local/uncommitted status; this
completion record supersedes their pending review, publication and CI statements.

**Hosted validation:** The
[merge Test run, attempt 2](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37365231237/attempts/2)
reports overall `failure` because the Python 3.14 job was canceled before any
steps ran. Individual job results are:

| Linux job | Verified result |
| --- | --- |
| [Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37365231237/job/111956779377) | Success; 996 tests passed, 2 native Windows skips; 91% coverage; 3 isolated artifact checks passed |
| [Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37365231237/job/111956819401) | Success; 996 tests passed, 2 native Windows skips; 91% coverage; 3 isolated artifact checks passed |
| [Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37365231237/job/111956778032) | Canceled; zero steps executed; hosted runner never acquired the job |

Both successful jobs also passed strict Poetry lock/metadata validation, Ruff
lint/format, Bandit, fresh wheel/sdist builds and strict Twine validation.
GitHub's cancellation annotation states that the job was not acquired by a
hosted runner after multiple attempts. Python 3.14 validation remains unavailable
for this merge; the maintainer explicitly accepted that gap for issue closure.
No CI retry, workflow/support-matrix change or replacement runtime test was
performed by this follow-up.

**Documentation-only closure checks and Git status:** Updated the roadmap index,
Thread 09 status/completion record, README, agent/contributor status and related
backup/restore/verification/inventory guides. Checked local Markdown links,
anchors/fences, status consistency, privacy, LF, diff whitespace and final Git
status. Application files, tests, dependencies and workflows were not changed;
application tests, builds and Sphinx were not rerun for these documentation edits.
The follow-up documentation changes remain unstaged/uncommitted on `main`; no
stage, commit, push, PR, merge, tag, release or publication action was performed
by the agent. Broader platform, timestamp/filesystem and power-loss limits remain
as documented in [fresh restore](../docs/RESTORE.md).

**Next thread:** Thread 10 — Git merge restore — remains **not started**,
explicitly excluded by the maintainer. No implementation or delegation of
Thread 10 was initiated. All later threads remain planned.

### Thread 10 — Git merge restore implementation handoff (5 October 2026)

**Scope/status:** Implemented only Thread 10 and its necessary CLI, tests and
public-safe documentation. All four thread subtasks and the synthetic acceptance
demo are met locally; maintainer review remains pending and issue #10 stays open.
Thread 11 — CLI polish — is **not started**. No later command, logging,
cross-platform hardening, release or publication capability was implemented.

**Dependency and baseline evidence:** Thread 09 implementation and its accepted
completion record are present at clean baseline `4507563` on the existing
`feature/10-thread-10-git-merge-restore` branch. Read issue #10 and dependency
issue #9; the latter is closed and records the maintainer-accepted Python 3.14
runner gap. Existing fresh reconstruction, format verification and journaled
transaction helpers were reused. No private `local/` content, real keys or
vaults were inspected; `local/vendor_docs/` is absent.

**Deliverables and acceptance evidence:**

- [Git orchestration](../src/obfuscidian/git_restore.py) requires a committed
  non-bare worktree root, an index matching HEAD, raw committed tracked bytes
  and executable flags, and no untracked/ignored entries or pending Git state.
  It validates exact optional Git administration, local base branch, mandatory
  `obfuscidian/` suffix, namespace/timestamp collisions, absent output/existing
  parent, overlap/identity aliases, keys, target names/types and staging space.
  Partial/promisor clones are refused before object resolution.
- Complete mirror authentication precedes private reconstruction. The complete
  additive union is checked before branch/worktree creation. Raw base blobs
  avoid checkout filters; the new worktree uses `--no-checkout` and `read-tree`
  only to initialize its index to the committed base. Journaled publication
  preserves the new `.git` file and base `.gitignore`; base-only content remains.
  Settings are additive by default; `--preserve-config` retains base settings,
  including absence. Required binary bytes, empty directories and supported
  times are preserved; unsupported times warn. Base-only executable flags use
  restrictive owner-only permissions without executing their contents.
- [CLI](../src/obfuscidian/cli.py) exposes `unshroud merge` and rejects merge
  options in fresh mode. Dry run creates no plaintext, refs, worktrees, locks or
  journals. Restored differences remain unstaged/uncommitted, with ignored-file
  review counts, opt-in escaped locations/names and quoted manual status,
  add/commit and later merge guidance. It explicitly says changes cannot merge
  until committed. Original checkout/HEAD/index/controls stay unchanged;
  only the requested shared branch/worktree metadata is added.
- Git subprocesses use argument lists, suppress raw diagnostics, ignore ambient
  Git selectors/global/system configuration, disable hooks/fsmonitor/automatic
  maintenance/lazy fetching and avoid status/diff/checkout attribute conversion.
  Original observations and configuration are rechecked at mutation boundaries.
- Ordinary failure removes only proven unchanged owned branch/worktree artifacts.
  Unknown partial creation, pending recovery, modified index/branch/controls,
  ignored files, user edits and changed private staging are retained. In
  particular, cleanup snapshots remain bound to verified contents, rather than
  accepting later staging edits as owned. Private journaled recovery data is
  retained after failed publication; it is sensitive plaintext. Interrupts exit
  130 without claiming success.
- [Temporary Git tests](../tests/integration/test_merge_restore.py) cover these
  behaviors offline with synthetic commits and generated test keys. Independent
  before/after comparisons prove original content/controls/index/HEAD unchanged,
  base-only retention, no restore commit, uncommitted differences and ignored
  review. Tests include custom/default bases, linked origins, Git metadata files,
  ref/path conflicts, wrong keys/corruption, dirty/ignored/untracked data,
  hooks/filters/config isolation, resource/timestamp limits, staged/source changes,
  failures before/after partial creation, publication failure, interrupts and
  later user edits. Existing command-gating tests were updated for the new mode.
- [Artifact checks](../tests/integration/test_packaging.py) include the new module
  and run both installed console/module merge restores in separate temporary
  repositories, including read-only dry runs and origin/index/commit preservation.
  [Restore guide](../docs/RESTORE.md#additive-git-merge-restore), README, changelog,
  related guides, agent/contributor status, roadmap index and this handoff are
  synchronized. Changed Python headers use `GPT-6.1 Sol` and `05 Oct 2026`.

**Validation actually executed:** Local macOS, Python 3.12.7 and Git 2.55.0.

- Strict Poetry lock/metadata validation, Ruff lint and formatting passed.
- Final full suite with coverage: **1092 passed, 2 native Windows skips**. Coverage: **91% total and 91% Git restore orchestration**.
- Thread 10 temporary-repository suite: **97 passed**.
- Bandit: no findings, with two local documented subprocess suppressions for
  resolved Git argument-list plumbing without a shell or checkout helpers.
- Fresh wheel/sdist build and strict Twine checks passed. Offline isolated
  wheelhouse packaging checks: **3 passed**; both artifacts include console
  and module merge restore smoke tests and `pip check`. The full suite separately
  exercises development-dependency installs.
- Markdown links/anchors/fences, changed headers/LF, privacy/scope, diff whitespace
  and final Git/status checks passed, including review of new untracked files.

**Limits and remaining work:** Hosted CI, local Python 3.13/3.14, native Windows
mutation, broader OS/filesystem validation, universal power-loss behavior and
Sphinx builds were not executed. Native Windows mutation remains fail-closed
pending Thread 12; docs tooling remains Thread 13. Git worktree/ref creation and
filesystem publication are not universally atomic. Incomplete creation or
process death is retained for manual review; merge `--recover` is explicitly
refused. Raw-byte checks conservatively refuse checkout conversions/filters,
non-UTF-8 names and case/normalization ambiguity; base blobs use the bounded
plaintext reconstruction limit. Advanced filesystem metadata is not imported.
Exclusive journal ownership coordinates Obfuscidian processes, not other
writers. Future Git capability/platform and durable Git ownership recovery work
is recorded in deferred capabilities. Maintainer review, separately authorized
Git history/publication and hosted validation remain outstanding.

**Issue synchronization and Git status:** The connector could read issues but
returned HTTP 403 on the start comment; authenticated CLI access successfully
posted that update. The final public-safe handoff and verified checklist/status update were posted
with the CLI and read back successfully; the issue remains open and its labels,
assignee and milestone are unchanged. See the
[handoff comment](https://github.com/jeffshurtliff/obfuscidian/issues/10#issuecomment-6002981556). All 16 proposed files remain **unstaged and
uncommitted** on the pre-existing `feature/10-thread-10-git-merge-restore` branch
at `4507563`. No development branch/worktree creation, stage, commit, push, PR,
merge, tag, release or publication was performed. Git commits/staging/worktrees
were created only inside explicitly authorized synthetic temporary fixtures.
Next eligible implementation is Thread 11 after review/acceptance; it is not
started.

### Thread 10 — Git merge restore completion record (5 October 2026)

**Maintainer decision and status:** The maintainer reviewed, committed, merged
and pushed Thread 10, reported all three CI jobs green, and explicitly requested
closure of issue #10. All four subtasks and the acceptance/demo are met.
Thread 10 is **complete**; issue #10 is closed as completed. The implementation
handoff above retains its historical local/uncommitted state; this completion
record supersedes its pending review, Git publication and hosted CI statements.

**Commit and remote evidence:** Implementation commit
[`8e41e30`](https://github.com/jeffshurtliff/obfuscidian/commit/8e41e30619ffb3eabde8a4146f88e2b97053c9d8)
is an ancestor of pushed main merge
[`f448b2c`](https://github.com/jeffshurtliff/obfuscidian/commit/f448b2c61211ac4e02414b992f31f82e39cde4f5).
Local HEAD/main, origin/main and the live remote main ref all matched that exact
merge when checked. The checkout was clean before this documentation follow-up.

**Acceptance evidence:** The merged implementation and synthetic tests establish
clean-origin/base/branch/output validation, authenticated additive restoration
into a separate worktree, unchanged origin HEAD/index/content, uncommitted
restored differences, ignored-file reporting and manual review/commit/merge
guidance. Failure cleanup removes only proven unchanged owned artifacts and
retains uncertain artifacts or later user edits. The implementation handoff
links the deliverables and records the 97 temporary-repository cases; no real
vault or cloud tests were used.

**Hosted validation:** The
[merged-commit Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37385531508)
completed successfully on the exact merge SHA. All three Linux jobs passed:

| Linux job | Verified result |
| --- | --- |
| [Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37385531508/job/112017748843) | Success; 1092 tests passed, 2 native Windows skips; 90% total coverage; 3 isolated artifact checks passed |
| [Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37385531508/job/112017748409) | Success; 1092 tests passed, 2 native Windows skips; 90% total coverage; 3 isolated artifact checks passed |
| [Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37385531508/job/112017748751) | Success; 1092 tests passed, 2 native Windows skips; 90% total coverage; 3 isolated artifact checks passed |

Each job also passed strict Poetry lock/metadata validation, Ruff lint/format,
Bandit, fresh wheel/sdist builds and strict Twine checks. Git restore coverage
was 91% in each hosted job; the historical 91% total coverage was a local result,
not the hosted total. No workflow retry or support-matrix change was performed
by this follow-up.

**Documentation-only closure checks and Git status:** Updated the roadmap index,
Thread 10 status/completion record, README, agent/contributor status, changelog
wording and related backup/restore/verification guides. Checked local Markdown
links, anchors/fences, status consistency, privacy, LF, diff whitespace and final
Git status. No
application files, tests, dependencies or workflows changed. Application tests,
builds and Sphinx were not rerun for these documentation edits; hosted results
above were read from the completed run and its logs. The documentation follow-up
remains unstaged/uncommitted on `main`; no stage, commit, push, PR, merge, tag,
release or publication action was performed by the agent. The existing issue
body/checklist and a
[completion comment](https://github.com/jeffshurtliff/obfuscidian/issues/10#issuecomment-6005075868)
were updated; closure was read back as `closed` with reason `completed`, and
the exact body, labels, assignee and milestone were verified unchanged except
for the requested completion update.

**Limits and next thread:** Native Windows mutation remains fail-closed pending
Thread 12; broader platform/filesystem and universal power-loss validation remain
unestablished. Incomplete Git creation/process death and uncertain recovery data
require manual review; merge `--recover` remains refused. Existing deferred
Git capability and durable ownership recovery work stays in the roadmap.
Thread 11 — CLI polish — is **not started**, explicitly excluded by the
maintainer. No implementation or delegation of Thread 11 was initiated.
Threads 11–14 remain planned.

### Thread 11 — CLI polish implementation handoff (5 October 2026)

**Historical handoff:** The completion record below supersedes this record
for review, Git status and hosted CI availability.

**Status:** Implemented locally, pending maintainer review. All four requested
subtasks and the local acceptance/demo are met; issue #11 remains open for the
review/closure decision. Thread 10 code, temporary Git/installed-artifact tests
and its accepted merged Linux CI evidence were inspected before work. Actual
Thread 11 synthetic runs additionally exercised the dependency behavior.

**Deliverables and audit:**

- [CLI](../src/obfuscidian/cli.py): required modes, command option placement,
  selector precedence, supported combinations and helpful misuse diagnostics;
  static phase progress; terminal-only interactive/verbose handoff exceptions;
  prompt refusal/EOF, non-terminal input, non-interactive/consent separation,
  read-only dry run/verification and recovery behavior; consistent exit codes
  `0`/`1`/`2`/`130`, including interrupts outside callbacks and logging failures.
- [Private output/logging](../src/obfuscidian/output.py) and
  [constants](../src/obfuscidian/constants.py): private JSON lines operational
  records from deliberately supplied fields, never captured streams/prompts or
  exception text. `--verbose` cannot add log names; `--log-paths` explicitly
  permits relative names and never absolute handoff locations, content or keys.
  Log custody, parent/file identity, permissions and link/special/hard-link
  refusal precede mutation. Git ownership is rechecked before opening/records.
  Existing private POSIX logs append; default logging remains disabled.
- [Shared CLI contract tests](../tests/integration/test_cli_contract.py): 71
  synthetic privacy/UX checks, including both streams, control-character names,
  independent terminal/log disclosure, safe/no-op/read-only behavior, refused
  or changed log locations, permissions, interrupts and each exit category.
  Existing [CLI unit tests](../tests/unit/test_cli.py) match the completed help.
  Backup/restore recovery log regressions and Git merge log/handoff tests are in
  their existing integration suites; all fixtures remain temporary and synthetic.
- [Installed-artifact parity](../tests/integration/test_packaging.py): wheel and
  sdist content allowlists, each command's help, version, parser/operational/
  interrupt exits, dry runs, redacted logs and byte-preserving backup/restore/Git
  workflows outside the checkout. Restored differences remain uncommitted.
- [Shared CLI guide](../docs/CLI.md), configuration/backup/restore/verify guides,
  README, contributor/agent status and [changelog](../docs/CHANGELOG.md) are
  synchronized. `pyproject.toml` includes the CLI guide in the sdist; runtime
  dependencies, lockfile, cryptography and v1 format/data semantics are unchanged.

**Checks actually executed:**

- `poetry check --lock --strict`, `poetry run ruff check .`,
  `poetry run ruff format --check .` and `poetry run bandit -r src/obfuscidian`
  passed. Bandit found no issues; the two existing documented Git subprocess
  suppressions remain unchanged.
- Final `poetry run coverage run -m pytest -q`: **1165 passed, 2 native Windows
  skips** on local macOS/Python 3.12.7. `poetry run coverage report`: **90% total**,
  **89% CLI**, **86% output/logging**. These are local results, not hosted matrix
  evidence. A separate targeted run of all 71 shared CLI tests also passed.
- Fresh `poetry build --output <temporary-candidate>` and strict Twine validation
  of exactly that wheel/sdist passed. `test_packaging.py` using the fresh artifacts
  and an existing compatible dependency wheelhouse: **3 passed**, with isolated
  installs and `pip check`. The normal suite separately tested offline installs
  with explicitly shared development dependencies.
- All seven roadmap command examples plus the optional logging example ran with
  exit `0` in a temporary synthetic workspace, with correct external key/log
  custody and a clean committed synthetic Git origin. Redirected output was
  private/static; restored binary/note bytes matched. Help was manually inspected
  at 40 and 100 columns and covered by width tests.
- Local Markdown links/anchors/fences, LF/privacy, required Python headers,
  `git diff --check`, full proposed diff/new-file inspection and scope/status
  checks passed. No real vault/cloud/key tests ran.

**Limits and next work:** Hosted CI and broader supported-platform validation
were not executed or triggered. Sphinx tooling/build remains Thread 13. Windows
vault mutation remains fail-closed; new Windows logs reuse the established keygen
DACL helper, while existing Windows log appends await file ACL validation in
Thread 12. Filesystem identity observations remain best effort against concurrent
writers. A logging failure after data publication returns failure but may leave a
complete publication; inspect state/recovery before retrying. An explicitly
requested no-op log may be created/appended, while vault bytes/times and all
transaction artifacts remain unchanged. Private plaintext recovery artifacts
remain sensitive. No implementation acceptance blocker remains; maintainer
review/closure and any later hosted validation remain pending. Next eligible
implementation is Thread 12 after acceptance; **Thread 12 is not started**.

**Git and issue tracking:** All **20 proposed files are unstaged/uncommitted on
`main`**; no staging, development commit, push, PR, merge, tag, release or
publication occurred. Temporary fixture commits/worktrees served only offline
integration checks. Issue #11 start/progress/checklists/handoff were synchronized
through the authenticated GitHub CLI after the connector's comment endpoint
returned permission-denied; labels, assignee, milestone and open state are
unchanged. Historical handoffs describe their original state and are not claims
that later threads remain unimplemented today.

### Thread 11 — CLI polish completion record (5 October 2026)

The maintainer confirmed successful review/merge and explicitly requested closure
of issue #11, with Thread 12 excluded. All four subtasks and acceptance/demo are
met. This record supersedes the historical implementation handoff's pending-review,
uncommitted-implementation and unavailable-hosted-CI statements.

**Commit alignment:** Implementation commit
[`c6e7a15`](https://github.com/jeffshurtliff/obfuscidian/commit/c6e7a1577da95663cd2902773d77719d41a00089)
is present on pushed `main`. Local HEAD/main, `origin/main` and the live remote
main ref matched this exact commit; the checkout was clean before this
completion-documentation follow-up. No Git history or workflow action was taken.

**Hosted CI inspected:** The exact-commit
[Test run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37390743274)
completed successfully. All three Linux jobs passed **1165 tests with 2 native
Windows skips**, **90% total coverage**, **89% CLI coverage**, **86% output/logging
coverage** and **3 isolated fresh-artifact checks**:

- [Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37390743274/job/112034951899)
- [Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37390743274/job/112034952170)
- [Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37390743274/job/112034952058)

Each job also passed strict Poetry lock/metadata validation, Ruff lint/format,
Bandit, fresh wheel/sdist builds and strict Twine checks. Counts were verified
from hosted logs, separately from the original local validation. No new run was
triggered. Installed-artifact tests cover console/module help, version, all exit
categories, optional logs, synthetic byte-preserving workflows and `pip check`.

**Merged deliverables:**
[CLI](https://github.com/jeffshurtliff/obfuscidian/blob/c6e7a1577da95663cd2902773d77719d41a00089/src/obfuscidian/cli.py),
[private output/logging](https://github.com/jeffshurtliff/obfuscidian/blob/c6e7a1577da95663cd2902773d77719d41a00089/src/obfuscidian/output.py),
[privacy/UX tests](https://github.com/jeffshurtliff/obfuscidian/blob/c6e7a1577da95663cd2902773d77719d41a00089/tests/integration/test_cli_contract.py),
[installed-artifact tests](https://github.com/jeffshurtliff/obfuscidian/blob/c6e7a1577da95663cd2902773d77719d41a00089/tests/integration/test_packaging.py)
and [CLI contract](https://github.com/jeffshurtliff/obfuscidian/blob/c6e7a1577da95663cd2902773d77719d41a00089/docs/CLI.md).
The verified contract includes static private progress, independently selected
terminal/log names, safe log custody/permissions/identity checks, unchanged data
semantics, prompts/consent/recovery, no-write dry runs/verification and truthful
exit codes. Default logs omit paths/content/keys; explicit relative-name logging
never captures absolute handoff locations, prompts or exception payloads.

**Completion-documentation checks:** Current roadmap index/thread status/tracking
summary, README, agent/contributor status, CLI/backup/restore/verification guides
and changelog are synchronized. Local Markdown links/anchors/fences, privacy/LF,
consistency, scope and `git diff --check` passed. These **nine documentation files
remain unstaged/uncommitted on `main`**; this new closure wording is not yet pushed.
No application files, tests, dependencies or workflows changed. Application
checks/builds were not rerun for this documentation-only task; completed hosted
results were inspected instead. Sphinx remains unavailable until Thread 13.

**Limits and next work:** Native Windows vault mutation and existing Windows log
append remain fail-closed pending Thread 12. Broader platform/filesystem and
universal power-loss validation remain outstanding; identity checks are best
effort against concurrent writers. Sensitive plaintext recovery and logging
failure after completed publication still require the documented state review.
These documented limits do not block accepted Thread 11 completion. No remaining
Thread 11 acceptance criterion or dependency blocker remains.

Issue #11 is closed as **completed** under explicit maintainer authorization;
labels, assignee and milestone are unchanged. **Thread 12 remains not started**
and was explicitly excluded: no Thread 12 implementation or delegation was
initiated. Threads 12–14 remain planned. No staging, commit, push, PR, merge, tag,
release or publication action occurred during this closure task.


### Thread 12 — Cross-platform hardening handoff (5 October 2026)

**Historical record:** The [completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026)
supersedes pending review, Git status and hosted acceptance below.

**Status:** Local implementation complete for the requested bounded CI/hardening
scope; issue #12 remains open for maintainer review and hosted matrix acceptance.
The nine new jobs have not been executed. Windows publication/recovery and
existing-log append remain deliberately fail-closed. This record supersedes
historical statements that Thread 12 was not started. Threads 13–14 remain
**not started**; no later feature or release/publication work was initiated.

**Dependency readiness:** Thread 11 implementation/CLI/private logging and its
completion record were read against the checkout. Issue #11 is closed as
completed. The live accepted Test run `37390743274` was inspected: successful
Linux/Python 3.12–3.14 jobs at implementation commit
`c6e7a1577da95663cd2902773d77719d41a00089`. These dependency results do not
validate this uncommitted Thread 12 change. Baseline local macOS/Python 3.12.7
suite: **1165 passed, 2 native Windows skips**.

**Deliverables:**

- [Test workflow](../.github/workflows/test.yml): Linux/macOS/Windows × Python
  3.12/3.13/3.14, unchanged locked Poetry installs, offline suites, read-only
  style/security checks, coverage, fresh artifacts, per-job XML evidence and
  bounded job duration. No matrix exclusion or whole-suite skip was added.
- [Portable artifact helper](../.github/scripts/check_artifacts.py): native
  temporary paths, argument-list subprocesses, wheel/sdist/Twine and separate
  offline installs after downloading a temporary dependency wheelhouse.
- [Unit hardening tests](../tests/unit/test_platform_hardening.py),
  [native platform tests](../tests/integration/test_platform_hardening.py) and
  [transaction resource/termination tests](../tests/integration/test_platform_transactions.py).
  Coverage includes Windows names/drives/streams, case/Unicode ancestor collisions,
  multibyte path boundaries, bounded encryption, 1001-file inventory, binary
  preservation, exact space estimates, allocation failures and descriptor cleanup,
  no-op preservation, real local Git preflight/absent refs, metadata limitations,
  staged disk-full/quota/I/O faults and native POSIX termination after rename.
- Read-only transaction capture now uses absolute binary file paths when no
  directory handle is available; inspected identity/content rechecks remain.
  Key/source/staged-write/Git-copy stream allocation failures close descriptors.
  Windows private-file creation and log preflight require persistent ACL capability.
  Native Windows tests cover key DACLs, junction refusal, all existing write-mode
  refusals, recovery refusal, new logs and existing-log append refusal.
- Installed command tests account for Windows launcher scripts, permission
  warnings and deliberate append refusal. Symlink privilege skips are narrow;
  existing Windows log-change tests stop at the earlier explicit ACL boundary.
  Open-file sharing denial is treated as safe read failure, never successful data.
- [Platform guide](../docs/PLATFORMS.md), current status/docs, changelog and sdist
  guide inclusion describe the limits and separate validation from configuration.

**Validation actually executed:**

| Environment | Full offline suite | Scope |
| --- | --- | --- |
| Local macOS arm64 / Python 3.12.7 | 1213 passed, 7 skipped | Coverage run; 91% overall |
| Local macOS arm64 / Python 3.13.15 | 1213 passed, 7 skipped | Temporary source copy; unchanged locked Poetry environment |
| Local macOS arm64 / Python 3.14.7 | 1213 passed, 7 skipped | Temporary source copy; unchanged locked Poetry environment |
| Hosted Linux/macOS/Windows × Python 3.12–3.14 | Not run | Uncommitted/unpushed change; acceptance pending |

Seven local skips are native Windows-only cases: existing junction/key DACL,
three new mutation/recovery cases, new-log/append refusal and inventory junction
refusal. No native Windows success is inferred from portable mocks. Python
3.13/3.14 copies were isolated from the development environment. Initial sandboxed
dependency installs could not access PyPI; unchanged locked installs succeeded
with approved network access. Earlier test expectation/fixture errors were fixed;
passing reruns supersede those failures. Synthetic Git fixtures disable automatic
maintenance to prevent asynchronous fixture changes.

Strict Poetry metadata/lock, Ruff lint/format and Bandit passed (no Bandit issues;
two unchanged documented Git-subprocess suppressions). Fresh wheel/sdist build,
strict Twine and **3 fully isolated artifact tests** passed using the portable
helper; final guide/include changes also passed this isolated check.
Final targeted reruns: **71 passed, 5 native Windows skips** on Python 3.12;
updated platform/inventory/packaging tests: **34 passed, 5 native Windows skips**
on each Python 3.13/3.14 environment after portability refinements.
Local Git **2.55.0** exercised the required plumbing/worktree-preflight capability;
older Git versions are unverified. Documentation/link/anchor, privacy/header/LF,
workflow structure, scope and whitespace checks passed across all **26 proposed
files**. An actionlint executable was unavailable; YAML/matrix/evidence structure
was checked locally, while GitHub workflow/runtime acceptance remains pending.
No Sphinx build was run: its tooling remains Thread 13. No real vault/cloud/key
or privileged filesystem test was performed.

**Safety assessment and remaining acceptance:** Existing process-death/checkpoint,
competing-writer, changed-source/destination, interrupted-recovery, protected-Git,
no-write verification/dry-run and no-op coverage still runs on POSIX hosts.
Windows read-only observation lacks anchored directory handles; identity checks
are best effort. Native Windows private directory ACLs, locks, publication and
recovery primitives, and existing-log ownership/DACL validation remain unimplemented;
these writes stay blocked. Conservative filesystem comparison remains unchanged;
no probe, lossy name/content workaround, weakened validation, format/dependency
change or deferred capability was added. Native Windows/Linux runs, the new hosted
matrix and maintainer acceptance remain pending; CI configuration alone is not
platform certification. See the platform guide for narrowly scoped skip reasons.

**Git/issue handoff:** All **21 modified tracked files and 5 new files** are unstaged/uncommitted on the existing maintainer
branch `ci/12-thread-12-cross-platform-hardening`, based on `main`. No branch,
commit, staging, push, PR, merge, tag, release or publication action was taken.
Only temporary synthetic Git fixture history was created by tests. Issue #12
received start/progress updates through authenticated GitHub CLI after the
connector refused comment access; its final body/checklists/handoff are synchronized
without changing labels, assignee, milestone or open state. The next roadmap
thread is Thread 13 only after Thread 12 acceptance; it has not started.

### Thread 12 — Windows CI follow-up (6 October 2026)

**Historical record:** The [completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026)
supersedes pending review, Git status and hosted acceptance below.

**Status:** The maintainer reviewed, committed and merged the initial Thread 12
implementation at `7e5cfd9`. The correction below remains uncommitted for review;
issue #12 remains open and full matrix acceptance is pending. This follow-up
supersedes the earlier pre-merge/pending-CI status, preserving its historical
local validation record. Threads 13–14 remain **not started**.

**Hosted evidence:** [Test run `37470636499`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37470636499)
at that merge passed all six Linux/macOS × Python 3.12–3.14 jobs, including
style/security, offline tests, coverage and fresh artifacts. All three Windows
jobs failed at Ruff formatting. Lint passed in the inspected Python 3.12 job;
Bandit, tests, coverage and builds were not reached there. The artifact warning
reflects missing test/coverage reports after the earlier failure.

**Cause and correction:** A temporary clone with `core.autocrlf=true` reproduced
the exact **49 files would be reformatted, 24 already formatted** failure.
Ruff requires LF, but Git checked text out with CRLF, including Python code blocks
in Markdown issue templates. New [`.gitattributes`](../.gitattributes) uses
`text=auto eol=lf` for detected text and `-text` for `tests/fixtures/**` to retain
byte-exact compatibility inputs. Application code, format, dependencies, CI
checks and fail-closed Windows boundaries are unchanged.

**Validation:** Fresh checkouts in the disposable clone with `core.autocrlf=true`,
`false` and `input` each passed Ruff formatting: **73 files already formatted**,
with no CRLF Python files. All **9 existing fixture files** matched their original
bytes in every checkout; synthetic mixed-ending ASCII ciphertext and binary
probes also survived unchanged. An initial attempt to refresh existing clone
files left Git's normalized worktree cache intact; the successful regression
removed disposable tracked files first to exercise a genuinely fresh checkout.
Only the disposable clone's index was changed; this development checkout was
never staged. Strict Poetry metadata/lock, Ruff lint/format, Bandit (no issues)
and **71 format integration tests** passed on local macOS/Python 3.12.7. The full
offline suite also passed: **1213 passed, 7 native Windows skips**. All unchanged
tracked files matched the original bytes in the corrected disposable checkout;
its Ruff lint passed too. Changed-file LF, local documentation links/anchor,
privacy/scope and `git diff --check` passed.

**Pending/handoff:** Native Windows reruns on Python 3.12–3.14 are pending the
maintainer's review, commit, merge and push. Local Git conversion regression
does not establish native Windows runtime or packaging success. No Windows
safety check was weakened. No fresh artifact build, alternative local Python
suite or Sphinx build was needed for this checkout-policy-only correction.
Changes are limited to `.gitattributes`, changelog, platform guide and roadmap,
unstaged/uncommitted on `ci/12-thread-12-fix-windows-ci-failures`; no commit,
push or PR was performed. Issue #12 records the investigation and follow-up.
Thread 13 is eligible only after Thread 12 acceptance and has not started.

### Thread 12 — Windows identity follow-up (6 October 2026)

**Historical record:** The [completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026)
supersedes pending review, Git status and hosted acceptance below.

**Status:** The maintainer reviewed and merged the LF checkout correction at
`65af1dd`. [Test run `37473104440`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37473104440)
passed all six Linux/macOS × Python 3.12–3.14 jobs. All three Windows jobs passed
style/security, then failed offline tests with **69 failed, 581 passed, 563 skipped,
7 errors** each. Failed test coverage/evidence was retained; fresh artifact
validation was skipped. Logs for all three Windows jobs were reviewed; the
[Python 3.12 job](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37473104440/job/112301445798)
provides representative traceback evidence. This new correction remains
uncommitted for review; issue #12 remains open and full matrix acceptance is pending.

**Cause and correction:** Windows `DirEntry.stat()` supplies zero device/inode
values, unlike full `os.stat()`/`lstat()`. Cached scan metadata was recorded as
identity in inventory and mirror namespace traversal, producing false failures
when later full metadata was checked. [Inventory](../src/obfuscidian/inventory.py)
and [mirror path traversal](../src/obfuscidian/paths.py) now use fresh full
`os.stat(..., follow_symlinks=False)` entry metadata. POSIX calls remain anchored
to inspected directory handles; fallback calls use absolute child paths. Every
existing identity, type, link/reparse, content, parent and pre/post-read comparison
remains in place. No zero-identity wildcard or comparison relaxation was added.
Two CLI failures were test expectations for raw Windows separators; the
[interactive keygen tests](../tests/unit/test_cli.py) now assert the existing
escaped `repr` output. Production output/privacy behavior is unchanged.

**Regression coverage:** [Synthetic scan identity tests](../tests/integration/test_scanned_identity.py)
model incomplete cached enumeration metadata with both native and unanchored
traversal. They exercise stable nested inventory/binary reads, full mirror
authentication, selected-key hard-link refusal before exclusion pruning,
source edit/replacement rejection, same-byte token replacement rejection and
no-follow symlink refusal with external-target preservation. The regression
reproduced false identity/inventory-change errors before the fix; all **16 cases**
passed afterward. Symlink/hard-link capability skips remain narrow; no broad
Windows skip or expected-failure marker was introduced.

**Validation actually executed:**

| Environment/check | Result |
| --- | --- |
| Local macOS arm64 / Python 3.12.7 full offline suite | 1229 passed, 7 native Windows skips |
| New scan regression and CLI unit tests, Python 3.12.7 | 52 passed |
| Focused inventory/path/format/verify/CLI/regression suite, Python 3.13.15 | 367 passed, 1 native Windows junction skip |
| Same focused suite, Python 3.14.7 | 367 passed, 1 native Windows junction skip |
| Strict Poetry metadata/lock, Ruff lint/format, Bandit | Passed; no Bandit issues |
| Fresh wheel/sdist build and strict Twine | Passed |
| Changed-file header/date/LF, documentation links/anchors, privacy/scope, diff whitespace | Passed |
| Native Windows runtime/artifact checks with this correction | Pending maintainer commit/merge/push and hosted rerun |

The alternative Python checks imported the current checkout's corrected source,
using the existing isolated locked environments. Full Python 3.13/3.14 suites,
new coverage measurement, separate wheelhouse-isolated artifact installs and
Sphinx were not rerun; the full Python 3.12 suite includes offline wheel/sdist
installation tests. No real vault/key/cloud or privileged filesystem test was used.
Python headers use `Jeff Shurtliff (via GPT-6.1 Sol)` and `06 Oct 2026` only on
changed/new Python files.

**Git/issue handoff:** Exactly **6 modified tracked files and 1 new regression
module** remain unstaged/uncommitted on the existing maintainer branch
`ci/12-thread-12-fix-windows-filesysem-id-change-ci-failures`, at `65af1dd`.
No development-checkout staging, commit, push, PR, merge or release action was
performed; the full suite uses temporary synthetic Git fixture history only. Issue #12
records the investigation, actual hosted/local evidence and pending acceptance.
Windows mutation/recovery and existing-log append still fail closed; format,
dependencies and the nine-job matrix are unchanged. Threads 13–14 remain
**not started**; Thread 13 becomes eligible only after Thread 12 acceptance.

### Thread 12 — Windows descriptor follow-up (6 October 2026)

**Historical record:** The [completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026)
supersedes pending review, Git status and hosted acceptance below.

**Status/evidence:** The maintainer merged the scan-identity correction at
`fd6472f`. [Run `37493585740`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37493585740)
passed all six Linux/macOS jobs and Windows style/security. Windows offline
results were **32 failed / 634 passed** on Python 3.12, **34 failed / 632 passed**
on Python 3.13, and **32 failed / 634 passed** on Python 3.14, with **563 skipped
and 7 setup errors** on each. Logs for all three failed jobs were reviewed;
the [3.12 traceback](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37493585740/job/112372301308)
shows fixture setup reaching `_read_token()` and refusing descriptor metadata.
Test/coverage evidence was retained; fresh artifact validation was skipped.
This correction remains local/uncommitted and issue #12 remains open.

**Cause and correction:** Supported Windows Python can return creation time in
path `st_ctime_ns` but change time in descriptor `st_ctime_ns`, as documented in
[CPython issue #157671](https://github.com/python/cpython/issues/157671).
A new private [fingerprint matcher](../src/obfuscidian/paths.py) permits only an
exact descriptor `st_birthtime_ns` bridge when full metadata equality fails on
Windows. Device/inode, full mode, size and modification time must all match;
missing/malformed creation metadata cannot justify a mismatch. Exact metadata
matches remain accepted on all hosts, with no POSIX creation-time fallback.
[Source reads](../src/obfuscidian/inventory.py),
[token reads](../src/obfuscidian/manifest.py) and
[transaction hashing](../src/obfuscidian/transactions.py) use the same matcher.
Each also compares raw descriptor metadata before/after reading, retaining the
independent change-time check, and rechecks the path. No timestamp is dropped
from same-API comparisons and no identity, type, link, parent, length or content
validation is bypassed. Windows mutation/recovery/append refusals are unchanged.

The case-alias overlap test now accepts the earlier lexical overlap diagnostic
on Windows while continuing to require refusal. The existing cached-enumeration
fixture models absent directory handles without changing timestamp semantics,
so it remains a focused test of scan identities rather than a fake OS globally.

**Regression and validation actually executed:**

- New [descriptor metadata regression](../tests/integration/test_opened_metadata.py):
  **35 cases** covering stable source/token/hash reads, change-time-only drift,
  creation-time/device/inode/mode/size/mtime drift, missing/malformed creation
  metadata, and exact/POSIX comparison behavior. The three stable-reader cases
  reproduced the original failures before the fix and passed after it.
- New/existing scan regression plus path unit suite: **94 passed, 1 native Windows
  junction skip** on local macOS/Python 3.12.7.
- Full local macOS/Python 3.12.7 suite: **1264 passed, 7 native Windows skips**,
  including offline wheel/sdist installation tests and existing interruption,
  recovery, changing-path, no-op and refusal coverage.
- Focused descriptor/scan/format/inventory/verify/platform/path suites on each
  Python **3.13.15 and 3.14.7**: **374 passed, 6 native Windows skips** each;
  existing isolated locked environments imported the current corrected source.
- Strict Poetry metadata/lock, Ruff lint/format, Bandit (no issues), fresh wheel/
  sdist builds and strict Twine passed. Header/model/date/LF, documentation
  links/anchors, privacy/scope and `git diff --check` passed.

**Pending/handoff:** Native Windows runtime/artifact reruns remain pending the
maintainer's review, commit/merge/push and CI execution. Synthetic Windows
metadata on macOS does not establish hosted Windows success. Full alternative
Python suites, new coverage measurement, separate wheelhouse-isolated installs
and Sphinx were not rerun. No real vault/key/cloud or privileged filesystem test
was performed. Format, dependencies and the nine-job matrix are unchanged; no
new broad skip, expected failure or deferred product feature was added.
Exactly **9 modified tracked files and 1 new regression module** remain
unstaged/uncommitted on the existing maintainer branch
`ci/12-thread-12-fix-windows-offline-test-failures`, at `fd6472f`. No development
index, commit, push, PR, merge or release action was taken; only temporary
synthetic Git fixture history was used by tests. Issue #12 records this follow-up.
Changed Python headers use `Jeff Shurtliff (via GPT-6.1 Sol)` and `06 Oct 2026`.
Threads 13–14 remain **not started**; Thread 13 requires Thread 12 acceptance.

### Thread 12 — Windows test follow-up (6 October 2026)

**Historical record:** The [completion record](#thread-12--cross-platform-hardening-completion-record-6-october-2026)
supersedes pending review, Git status and hosted acceptance below.

**Status/evidence:** The maintainer merged the descriptor correction at
`187cffc`. [Run `37517678167`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37517678167)
passed all six Linux/macOS jobs. All three Windows jobs passed style/security,
then failed offline tests. Python 3.12 and 3.13 each reported **1 failed,
707 passed, 563 skipped**; Python 3.14 reported **2 failed, 706 passed, 563 skipped**.
Logs for all three Windows jobs were inspected. Coverage and test evidence
were retained; Windows fresh artifact validation was skipped.

**Cause and corrections:** In
[the inventory race test](../tests/integration/test_inventory.py), Windows
refuses replacement of an open file. The directory context translates the
sharing denial into the existing safe directory-access error, which the
test's message pattern excluded. The assertion now accepts that refusal,
still requires the second file-stat injection to be reached, and verifies
that the descriptor is closed. A new deterministic sharing-denial case runs
on every host, checks the exact directory-guard diagnostic, and proves both
original and attempted replacement retain their synthetic bytes. Replaying
the old message pattern against this case reproduced the assertion mismatch.
No read payload is accepted after the error.

The additional Python 3.14 failure is in
[the incomplete-cache edit fixture](../tests/integration/test_scanned_identity.py):
a same-size immediate rewrite cannot assume an observable timestamp change.
The fixture now explicitly sets modification time one second beyond its
recorded value, asserts that difference, and still requires read refusal.
This tests a deterministic metadata change under the existing best-effort
observation contract; it does not claim an atomic filesystem snapshot.
Production code, safety checks, format, dependencies and matrix are unchanged.
No skip or expected-failure marker was added.

**Validation actually executed on local macOS:**

- Full offline suite on Python **3.12.7**: **1265 passed, 7 native Windows skips**,
  including offline package installations and existing interruption/recovery tests.
- The two changed integration modules on each Python **3.12.7, 3.13.15 and
  3.14.7**: **40 passed** each. Alternative interpreters used existing locked
  environments and imported the current workspace source.
- Strict Poetry metadata/lock, Ruff lint/format (**75 files already formatted**)
  and Bandit (**no issues**) passed.
- Changed headers use `Jeff Shurtliff (via GPT-6.1 Sol)`, `06 Oct 2026`.
  Header/LF, documentation links/anchor, public-safe scope, diff whitespace
  and unchanged development index were checked.

**Handoff/pending:** Exactly **5 modified tracked files** remain
unstaged/uncommitted on the existing maintainer branch
`ci/12-thread-12-fix-windows-failed-assertion`, at `187cffc`.
No commit, merge, push, PR or release action was taken. Native Windows reruns
remain pending maintainer review and the next hosted run; local injected
sharing denial is not native Windows validation. Full alternative-Python
suites, a separate fresh-build/Twine run, new coverage measurement,
wheelhouse-isolated installs and Sphinx were not rerun for these test-only
corrections. No real vault/key/cloud or privileged filesystem test was used.
The changelog and platform guide record the correction; issue #12 remains open
for review and full matrix acceptance. Windows mutation/recovery and existing-log
append still fail closed. Threads 13–14 remain **not started**; Thread 13
becomes eligible only after Thread 12 acceptance.

### Thread 12 — Cross-platform hardening completion record (6 October 2026)

**Maintainer decision and alignment:** The maintainer confirmed successful CI
and explicitly authorized closing issue #12, with Thread 13 excluded.
The final test correction commit `1b69441` is merged in
[`dc56009a580c55f5544c271457d3305064277dbd`](https://github.com/jeffshurtliff/obfuscidian/commit/dc56009a580c55f5544c271457d3305064277dbd).
Local `HEAD`, `main`, cached `origin/main`, live remote `refs/heads/main`
and the successful push-triggered Test run all match that full SHA.
The checkout was clean before this documentation-only closure update.
All four Thread 12 subtasks and acceptance criteria are met with the documented
platform limitations retained. Issue #12 is closed as completed under that
authorization; its labels, assignee, milestone and existing discussion are preserved.

**Hosted validation inspected:** [Test run `37519004246`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246)
completed successfully. All nine job records and logs were read. Each job
passed locked Poetry installation/checks, Ruff lint/format, Bandit, offline
tests, coverage reporting, fresh wheel/sdist and installed-artifact validation,
and test/coverage evidence retention.

| Hosted job | Offline tests passed / skipped | Reported coverage | Fresh artifact validation |
| --- | --- | --- | --- |
| [macos-latest / Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199910) | 1265 / 7 | 91% | Passed |
| [macos-latest / Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199731) | 1265 / 7 | 91% | Passed |
| [macos-latest / Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199974) | 1265 / 7 | 91% | Passed |
| [ubuntu-latest / Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459200017) | 1265 / 7 | 91% | Passed |
| [ubuntu-latest / Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199988) | 1265 / 7 | 91% | Passed |
| [ubuntu-latest / Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459200032) | 1265 / 7 | 91% | Passed |
| [windows-latest / Python 3.12](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199938) | 709 / 563 | 66% | Passed |
| [windows-latest / Python 3.13](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459199899) | 709 / 563 | 66% | Passed |
| [windows-latest / Python 3.14](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246/job/112459200037) | 709 / 563 | 66% | Passed |

Windows skips are the documented POSIX mutation/private-mode/anchoring/FIFO
cases and Windows filename restrictions; Windows instead exercises native
key ACLs, links/junctions, read-only/no-op behavior and write/append refusal.
The POSIX skips cover native Windows APIs. Passing jobs do not prove skipped
behavior or universal filesystem support. The platform guide records the exact
boundaries; no broad skip or unsafe write workaround was introduced.

**Delivered behavior:** The [nine-job workflow](../.github/workflows/test.yml)
and [portable artifact validator](../.github/scripts/check_artifacts.py)
exercise the locked package on each of the nine OS/Python combinations. Focused
platform/resource/concurrency/interruption/recovery tests use synthetic data.
The merged follow-ups enforce LF checkout while preserving fixture bytes,
obtain full no-follow scan identities, reconcile Windows path/descriptor
creation-time semantics while retaining raw before/after checks, and make
sharing-denial and edit fixtures deterministic. The initial handoff and four
Windows follow-ups above retain their historical evidence; this completion
record supersedes their pending-review, Git-status and hosted-acceptance claims.

**Retained limitations and future work:** Native Windows vault mutation,
publication/recovery, private directory ACL/locking support and existing-log
ownership/DACL validation remain unimplemented and fail closed. The maintainer
accepted completion of the bounded Thread 12 hardening/validation scope with
these documented refusals. Best-effort filesystem observation is not an atomic
snapshot or universal crash/power-loss guarantee; target comparison remains
conservative. Any further runtime capability needs a separate maintainer request.
Thread 13 is the next roadmap dependency, but **has not started** and was
explicitly prohibited in this request. Thread 14 is also not started.

**Closure-only checks and Git status:** Documentation link/anchor, status
consistency, scope/privacy, LF and diff-whitespace checks were performed.
No application/test/workflow/dependency/version changes were made, and no new
local test, build, coverage, real-vault or privileged filesystem run was needed
for this documentation-only update. Sphinx remains unconfigured Thread 13 work.
The status documents and this completion record are local, unstaged/uncommitted
on `main` at `dc56009`; they are not yet published. No stage, commit, merge,
push, PR, tag, release or publication action was performed. The already-merged
implementation and hosted results are separate from these uncommitted docs.

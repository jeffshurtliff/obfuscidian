# Obfuscidian implementation roadmap

**Approved planning baseline:** 3 October 2026

**Status:** Thread 01 complete, reviewed, and merged into `origin/main`.
Thread 02 — Configuration and keys — is implemented and locally validated; maintainer review is pending.
Threads 03–14 remain not started.

**Intended first stable release:** `1.0.0` (current metadata: `1.0.0.dev0`).

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

Specify the following schema in Thread 04 and freeze it with compatibility
fixtures before backup commands use it:

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

### Planned examples (after the relevant threads are implemented)

The key directory exists already; paths and aliases below are placeholders.

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
| 02 | Configuration and keys | 01 | [#2](https://github.com/jeffshurtliff/obfuscidian/issues/2) | Local criteria met; review pending |
| 03 | Vault inventory and path preflight | 02 | [#3](https://github.com/jeffshurtliff/obfuscidian/issues/3) | Not started |
| 04 | Encrypted backup format | 03 | [#4](https://github.com/jeffshurtliff/obfuscidian/issues/4) | Not started |
| 05 | Safe publication and recovery | 04 | [#5](https://github.com/jeffshurtliff/obfuscidian/issues/5) | Not started |
| 06 | Fresh backup | 05 | [#6](https://github.com/jeffshurtliff/obfuscidian/issues/6) | Not started |
| 07 | Merge backup | 06 | [#7](https://github.com/jeffshurtliff/obfuscidian/issues/7) | Not started |
| 08 | Read-only verification | 04; may precede 05–07 | [#8](https://github.com/jeffshurtliff/obfuscidian/issues/8) | Not started |
| 09 | Fresh restore | 05, 07, 08 | [#9](https://github.com/jeffshurtliff/obfuscidian/issues/9) | Not started |
| 10 | Git merge restore | 09 | [#10](https://github.com/jeffshurtliff/obfuscidian/issues/10) | Not started |
| 11 | CLI polish | 10 | [#11](https://github.com/jeffshurtliff/obfuscidian/issues/11) | Not started |
| 12 | Cross-platform hardening | 11 | [#12](https://github.com/jeffshurtliff/obfuscidian/issues/12) | Not started |
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
**Depends on:** 01. **Status:** Implemented and locally validated; maintainer review pending.

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
**Depends on:** 02. **Status:** Not started.

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
**Depends on:** 03. **Status:** Not started.

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
**Depends on:** 04. **Status:** Not started.

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
**Depends on:** 05. **Status:** Not started.

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
**Depends on:** 06. **Status:** Not started.

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
**Depends on:** 04; may run before 05–07. **Status:** Not started.

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
**Depends on:** 05, 07, 08. **Status:** Not started.

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
**Depends on:** 09. **Status:** Not started.

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
**Depends on:** 10. **Status:** Not started.

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
**Depends on:** 11. **Status:** Not started.

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
status consistent. Thread 01 is complete following maintainer review and merge;
Thread 02 is implemented and locally validated with review pending. Threads 03–14
remain not started; Thread 03 is next after review.
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

### Deferred capabilities

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

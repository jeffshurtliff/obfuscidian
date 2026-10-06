# CLI output, privacy and automation

Thread 11 completes the shared CLI contract and is reviewed and merged/pushed
into `origin/main`; issue #11 is closed as completed. Linux CI passed on Python
3.12–3.14; see the
[completion record](../dev/IMPLEMENTATION_PLAN.md#thread-11--cli-polish-completion-record-5-october-2026).
Thread 12 remains **not started**.

Backup and restore semantics remain those in the [backup](BACKUP.md),
[restore](RESTORE.md), [verification](VERIFY.md) and
[configuration](CONFIGURATION.md) guides. Native Windows vault mutation remains
fail-closed; broader platform hardening is Thread 12.

## Discovery and option placement

`obfuscidian` and `python -m obfuscidian` have equivalent help, output and exit
behavior. Global options are `--help` and `--version`. Operation options follow
the command. `shroud` and `unshroud` require the positional mode `fresh` or
`merge`, rather than a second command group. Use `COMMAND --help` to discover
options, precedence, mandatory exclusions and retention behavior.

Normal output reports static phases, counts, bytes and final results.
Warnings and errors use stderr. Static progress remains readable in redirected
output and never uses animation or cursor control. Long file processing happens
within a phase; there is no per-file animation or completion percentage.

Default unattended output omits original names and absolute paths. `--verbose`
permits escaped relative names and actionable handoff locations in terminal
output. Keygen targets, completed restore/worktree locations and private rollback
locations may also be shown with interactive terminal input. Key bytes, file
contents, hashes and raw exception/traceback payloads are never printed.
Control characters, including newlines, escape and bidirectional controls, are
escaped; ordinary printable Unicode names remain readable. Parser misuse
messages identify supported options or required arguments without echoing the
invalid value or arbitrary unknown command/option name.

## Optional private logs

`keygen`, `shroud` and `unshroud` accept `--log-file FILE`. The existing parent
must be outside both vaults, all Git repositories/worktrees, staging and rollback
trees. The log cannot be the selected key, a link, junction, hard-link alias,
directory or other special file. Parent components must be real directories.
Locations and permissions are validated before mutation, and identities are
rechecked at opening and each record. No directories are created for logging.

New POSIX logs use `0600`. Existing private regular logs may be appended;
logs with group/other permissions are refused without automatically changing
their permissions. Windows new logs use the keygen protected owner-only DACL
on ACL-capable volumes; appending existing Windows logs is refused pending
file ACL validation in Thread 12. This does not claim broader Windows support.

Logs contain UTF-8 JSON lines: fixed command/mode, phase events, inventory
counts/bytes, completion/failure exit category and no-op events. They do not
capture stdout/stderr, prompts, absolute handoff locations or exception text.
`--verbose` alone cannot add paths to logs. `--log-paths` requires `--log-file`
and explicitly permits escaped relative names, including ignored restore names.
It still cannot include key bytes, content or absolute paths. Those names may
be sensitive; store the explicitly requested log privately.

Log opening or writing failure returns failure, never success. A logging failure
after publication may leave a complete data operation; inspect its state and
retained recovery before retrying. Records before log opening, failed read-only
preflight and parser failures do not create logs. No-op backup preserves vault
bytes/times and creates no transaction artifacts; an explicitly requested log
may still be created/appended to record that no-op.

```sh
obfuscidian shroud fresh --origin ./vault --mirror ./vault-encrypted \
  --key ./keys/obfuscidian-primary.key --non-interactive --yes \
  --log-file ./private-logs/backup.jsonl
```

The key and log parents already exist outside both vaults and Git repositories.
Logs are optional; no log is created without an explicit filename.

## Prompts, read-only modes and recovery

Prompts require terminal input and no `--non-interactive`. Piped input never
supplies implicit interactive answers. Missing selectors fail unattended;
explicit invalid selectors never fall back or regenerate keys. `--yes` waives
only replacement/recovery consent and cannot bypass preflight, integrity,
key-custody or path checks. Refusal and EOF fail before publication.

Dry runs may prompt for absent selectors interactively, but never for destructive
consent. They create no keys, vault paths, logs, locks, staging, rollback,
branches or worktrees. `--log-file` is rejected with `--dry-run`, and `verify`
rejects both logging options because it is always read-only.

`--recover` conflicts with `--dry-run`. Backup and fresh restore recovery
require an actual proven pending transaction and explicit consent, then replan
the operation. Merge restore recovery remains unavailable: inspect uncertain
worktree/private plaintext artifacts manually. Keygen and verify reject
`--yes`/`--recover`; keygen never overwrites a collision. Merge-only Git options
are refused in fresh restore, and restore has no `--exclude`.

Git merge restore leaves the original checkout intact and restored differences
unstaged/uncommitted in a separate worktree. Review ignored files explicitly;
selected ignored paths may require `git add -f`. Commit selected changes manually
before any later merge. Interactive or verbose handoff supplies escaped quoted
POSIX manual commands; no stage, commit, merge, fetch or push runs automatically.

| Exit | Meaning |
| --- | --- |
| `0` | Successful command, complete verification, dry run or no-op |
| `1` | Operational/integrity/I/O/logging failure, refused consent, EOF or incomplete recovery |
| `2` | Missing/invalid configuration, unsafe path, unsupported option/combination or absent mode |
| `130` | Keyboard interrupt after the operation's conservative cleanup/recovery attempt |

Failure and interruption do not report partial publication as success. Retained
plaintext artifacts remain sensitive; inspect the reported recovery state before
retrying. Filesystem observations remain best effort, rather than atomic
snapshots or a guarantee against hostile concurrent writers.

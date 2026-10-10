# Native Windows safety design for 2.0.0

**Status:** Design delivered for review; no Windows write operation is enabled by
this document. **Date:** 10 October 2026. **Parent:** [#17](https://github.com/jeffshurtliff/obfuscidian/issues/17).
Package metadata already targets `2.0.0.dev0`; the intended stable version is
`2.0.0`. Package version and encrypted backup-format version remain separate.

This is the first, documentation-only increment of the Windows port. It defines
the implementation contract, required native proofs and handoff boundaries.
Subsequent implementation must resolve the named proof gates before enabling
an operation. A design, mocked API test or passing job that skips writes does
not establish native Windows support.

## Delivery sequence

| Thread | Issue | Deliverable | Dependency |
| --- | --- | --- | --- |
| 1 | [#25](https://github.com/jeffshurtliff/obfuscidian/issues/25) | This safety contract, implementation map and validation plan | Current baseline and #12 evidence |
| 2 | [#26](https://github.com/jeffshurtliff/obfuscidian/issues/26) | Native ACL, handle, ownership and publication primitives with native tests | Reviewed #25 design |
| 3 | [#27](https://github.com/jeffshurtliff/obfuscidian/issues/27) | Fresh/merge backup, fresh restore and explicit recovery | Proven #26 primitives |
| 4 | [#28](https://github.com/jeffshurtliff/obfuscidian/issues/28) | Git merge restore and ordinary-failure cleanup | Complete #27 lifecycle |
| 5 | [#29](https://github.com/jeffshurtliff/obfuscidian/issues/29) | Native matrix, exchanged v1 backups, installed artifacts and support docs | Complete #27 and #28 implementations |

All five issues are actual sub-issues of #17. Complete only the requested thread.
Native testing belongs in each implementation thread; thread 5 audits and
completes evidence rather than postponing safety testing until the end.

Leave changes uncommitted for maintainer review. A successor must verify the
reviewed predecessor changes are present in its checkout; an issue checkbox
does not supply those changes. Git history, pushes, PRs, releases and issue
closure retain the authorization rules in the root contributor guidance.

## Baseline review

The reviewed baseline is commit `8126a7666187f85f484913c18477a28ac1f6478d`.
Local `HEAD`, `main` and `origin/main` agreed during this review. This is local
ref evidence, not a new hosted CI result. The existing maintainer branch is
`feature/17-add-safe-native-windows-support` and began clean.

| Area | Current implementation | Windows port requirement |
| --- | --- | --- |
| `paths.py` | `_directory_handle` anchors POSIX components; Windows yields `None` after path rechecks | Separate write guards with native handles; never interpret `None` as a write capability |
| `_windows.py` | `_create_private_key` uses protected `OWNER RIGHTS` DACL, `CREATE_NEW`, exclusive sharing and persistent-ACL checks | Reuse suitable declarations; add directory creation, real owner checks and handle-based existing-artifact ACL validation |
| `transactions.py` | `_lock_descriptor` refuses non-POSIX; checkpoints/moves/cleanup use `dir_fd`, `flock`, modes and `fsync` | Native ownership, checkpoint, publication, cleanup and recovery backend |
| `backup.py` | `_write_token` and `_build_backup` use no-follow exclusive POSIX files/directories | Private binary staged writes through the backend |
| `restore.py` | `_build_restore` and `_set_time` use directory-relative creation/timestamps | Private reconstruction and checked handle timestamps |
| `git_restore.py` | `_publish_merge` refuses non-POSIX; `_stage_overlay`/`_copy_tree` use modes and directory-relative writes | Private worktree before Git writes, native copy/publication and checked cleanup |
| `output.py` | New Windows logs use the private creator; existing-log append refuses Windows | Preserve this separate append boundary |
| Tests/artifacts | Common mutation suites have POSIX module skips; installed write smoke tests have a POSIX gate | Execute native success/failure/recovery tests and installed write smoke cases |
| CI | Nine Linux/macOS/Windows jobs, Python 3.12–3.14 | Retain all jobs and report exact native test/skip evidence |

The [#12 completion](https://github.com/jeffshurtliff/obfuscidian/issues/12)
established the supported read-only/refusal boundaries, not a Windows write
backend. The current [platform](../PLATFORMS.md), [transaction](../TRANSACTIONS.md)
and [threat-model](../SECURITY.md) documentation agrees with the code.
The historical `dev/IMPLEMENTATION_PLAN.md` remains a v1 implementation record;
this document does not rewrite its historical acceptance evidence.
No `local/vendor_docs/` directory was available for this review.

## Scope and invariants

Implement the existing CLI's fresh/merge encrypted backups, fresh restore,
supported explicit interrupted-operation recovery and Git merge restore.
Retain standard whole-file Fernet, v1 manifest/object layout, 50 MiB token cap,
no expiry for archival decrypts, key isolation and exact primary-stream bytes.
No Python library API, CLI switch, dependency or format migration is introduced
by this design.

Sources remain read-only. Authenticate and validate all required restore
objects and paths before destination writes. Preserve root `.git`, `.gitignore`
and requested `.obsidian` controls; reject nested repositories and ambiguous
names. `--non-interactive` does not imply `--yes`. Consent never authorizes an
unsafe filesystem operation. Verification, dry runs and matching backup no-ops
must not create paths, probes, ownership records, logs or worktrees.

Keep [#18](https://github.com/jeffshurtliff/obfuscidian/issues/18) rollback pruning,
[#19](https://github.com/jeffshurtliff/obfuscidian/issues/19) naming capability
refinement, Python 3.15, existing-log append, privilege elevation and new Git
recovery semantics outside this port. Continue the current conservative naming
rules; namespace aliases must not bypass overlap or destination ownership.

## Eligible environments

Initial qualification targets ordinary unelevated, 64-bit CPython 3.12–3.14
on Windows 11 and Windows Server 2022 or newer, on local NTFS storage. These are
qualification targets, not a claim that all those systems have been tested.
Record the exact runner image/build and architecture in native handoffs; the
`windows-latest` label alone is not an OS support certificate. Additional
architectures and older Windows releases need their own evidence.

For every writable destination, private workspace, rollback area and Git output,
require all of the following before creating an artifact:

1. An opened, inspected ancestor chain without reparse points or device paths;
   absolute canonical locations and existing parents; stable nonzero handle
   identities and agreement with the inspected namespace.
2. Local fixed storage, persistent ACL support and no read-only volume flag,
   assessed against the actual opened location. Use volume identity as well as
   capability flags. The NTFS name is an initial qualification restriction,
   never sufficient evidence of safety by itself.
3. Destination and transaction workspace on the same opened volume. There is no
   cross-volume copy/delete fallback for a publication rename.
4. Ordinary rights to create private objects, query ownership/DACLs, read
   existing payload, perform the required checked deletes/renames and restore
   supported baseline access controls. Reject a missing right; never request
   elevation, enable backup/restore privileges or repair user permissions.
5. Current resource estimates, journal limits, supported names and safe absence
   of pending ownership. `os.access`, mode bits and free space are observations,
   not guarantees that a later write will succeed.

Reject remote/UNC and mapped network paths, removable-class volumes, FAT/exFAT,
ReFS until qualified, unknown volume capabilities, mount/reparse paths and
cloud placeholder/reparse entries for mutation. Read-only operations retain
their existing contracts. `DRIVE_FIXED` does not prove a device is non-removable
USB hardware; removal/disconnection remains an I/O failure with retained
evidence, not a supported durability promise. A fully hydrated local sync folder
cannot always be identified reliably: pause sync/editing and document concurrent
sync actors outside the atomicity guarantee. Do not claim complete provider
detection from attributes.

Capability inspection is read-only and uncached; reacquire/revalidate guards
when execution starts. Creation itself must enforce privacy and exclusivity.
Do not create a probe merely to decide whether preview or verification can run.

Microsoft documents drive classes separately from USB removal policy in
[GetDriveTypeW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdrivetypew).
Prefer [GetVolumeInformationByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew)
for handle-bound volume flags. API availability and returned identities are
required native proof gates in #26.

## Private objects and access-control validation

Use explicit security attributes on `CreateFileW(CREATE_NEW)` and
`CreateDirectoryW`, with non-inheritable handles. The protected DACL grants
full access only to the current effective user SID; validate that the owner is
that SID. Do not use a group owner or accept an arbitrary owner merely because
an `OWNER RIGHTS` ACE exists. Keep the existing key/log helper contract stable;
transaction helpers may use an explicit SID descriptor without altering keys.

Each sensitive file and directory must have its own validated protection.
For recovery/control artifacts, inspect the opened handle's owner, DACL presence,
protection flag and parsed ACEs using `GetSecurityInfo`. Reject a null/absent
DACL, inherited or additional grants, unsupported ACE forms, unexpected owner,
reparse point, nonregular type, multiple file links or invalid bounds. Do not
accept an SDDL substring, `chmod`, Windows mode bits or a private parent as
equivalent validation. Require the precise descriptor policy implemented by
the creator; do not silently tighten a reused unsafe artifact.

Files created by trusted external Git may inherit the explicit owner-only
directory grants. Their validator must distinguish this known inheritance
policy from the protected explicit policy for journals/locks: inspect every
effective grant and its owner, prove no nonowner access, and bind that proof to
the handle. Adding a permissive inheritance exception to the control validator
is not acceptable.

These rules protect against ordinary other users. Administrators, backup
operators, already-authorized open handles, the current user's malicious
processes and compromised endpoints remain outside the privacy guarantee.
No new privilege activation is needed for owner/DACL checks. Avoid SACL reads
or repairs requiring privileged access.

Microsoft's [file security guidance](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)
states that moving an object does not assign a new default descriptor and that
parent ACLs do not govern a child's access. Therefore a private rollback parent
does not prove the privacy of preexisting children. Creation and inspection APIs
are documented in [CreateDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createdirectoryw)
and [GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo).

## Handle guards, identity and publication

Keep native mutation guards distinct from best-effort read-only traversal.
Acquire directory components from the trusted root outward, opening each with
`FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT`. Query the opened
attributes/type and compare volume/file IDs before accessing a child. Retain
ancestor handles through the operation. Directory guards must deny delete
sharing and establish that in-place reparse conversion is prevented; denying
write sharing is the candidate policy to test. Check already-open incompatible
handles and preserve data on sharing violations.

An absolute path assembled from inspected strings is insufficient without
these live guards. `FILE_FLAG_OPEN_REPARSE_POINT` affects the opened component;
it does not independently protect every intermediate component. If the pinned
chain cannot prevent substitution or reparse conversion on a qualified system,
leave writes refused and revise the backend design. Do not replace it with
`lstat`/write/`lstat` and call that anchoring.

Open the mutation leaf once with the required rights, deny write/delete sharing
to competing opens, and perform the action on that validated handle. A rename
handle itself needs `DELETE`; avoid opening conflicting duplicate guards on
the same leaf. Reject multiple links for files that will be replaced or removed.
Existing mapped writers and same-user adversaries remain a documented residual
limit; recheck bytes and namespace as well as IDs.

Use handle-derived volume serial plus full file ID, object kind, attributes,
size, timestamps and content digest as appropriate. Do not truncate the file ID
or assume `DirEntry.stat()` is a native write identity. Preserve the existing
read-only Python creation/change-time bridge; it must not become a wildcard
identity or suppress changed-content comparisons. Bind alternate path spellings
to the same destination ownership; reject aliases that cannot be canonicalized
and checked safely, including unresolved short-name/drive aliases.

For publication, prefer `SetFileInformationByHandle(FileRenameInfo)` on the
validated source, with `ReplaceIfExists = FALSE`, a single validated target
component and a held target-directory guard. Verify the target handle-relative
resolution on the supported API/OS combinations; if using a full target path,
retain the entire target chain. Postcheck moved identity, bytes and DACL.
Never use overwrite flags for payload publication, reboot-delayed moves or
cross-volume fallbacks. Close file read/flush handles before their required
rename, retaining the appropriate rename handle and directory guards.

Journal replacement is a separate narrowly authorized overwrite of the exact
held journal identity. Validate an existing journal before replacement and keep
the flushed new candidate when replacement is uncertain. Checked cleanup uses
handle disposition on proven entries, children before directories, and refuses
unknown children; no broad `rmtree` fallback.

The relevant contracts are [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info),
[FILE_RENAME_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info)
and [FILE_DISPOSITION_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_disposition_info).
These API choices are a proposed implementation, conditional on native tests,
not evidence that the sharing combinations already work together.

## Ownership, checkpoints and durability

Ordinary execution creates a private lock with `CREATE_NEW` and no read/write/
delete sharing. Its open, non-inheritable handle is the OS lifetime ownership
token. An existing lock always blocks ordinary writes, regardless of age/PID.
Recovery opens that same existing entry exclusively, validates its owner/DACL/
identity and retains the handle through all mutations. Read its bounded record
through the held handle; reopening by pathname would conflict with exclusive
sharing. Only an exact held identity can be marked for deletion, and only after
terminal state is written. Closing completes release; a denied delete or
uncertain close leaves pending ownership and an accurate warning/failure.
Do not use delete-on-close at acquisition: process death must retain the record.

Exclusive sharing is the proposed ownership mechanism; adding `LockFileEx` is
not required merely to imitate `flock`. It cannot replace the retained-record
and identity protocol. #26 must prove both exclusion while alive and acquisition
after abrupt termination, including a competing recovery process.

Use bounded complete binary writes, stream flush and `FlushFileBuffers` on
write-capable handles for ownership, journal candidates and staged payload.
Checkpoint intent before every destructive boundary and checkpoint observed
completion afterward. Any flush error prevents a success claim. Keep the
current 4 KiB lock and 16 MiB journal bounds; reject an oversized Windows record
before destructive work rather than increasing limits incidentally.

There is no assumed portable Windows directory equivalent to the current
POSIX `fsync` protocol. This design promises tested process-interruption recovery
while the OS/storage remain functioning, not universal power-loss durability.
Do not swallow a required file-flush error or flush a whole volume with elevation.
If journal replacement/namespace persistence cannot be established after an OS
crash, retain artifacts and refuse uncertain recovery. Hardware caches, filter
drivers and disconnected storage can invalidate a stronger guarantee.

[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
requires a write-capable file handle and documents the privileged whole-volume
case. These are not grounds for assuming directory flush behavior.

## Private rollback copies and Windows recovery state

Use verified private copies of replaced Windows payload before destructive
publication. Do not move permissive old plaintext into rollback or recursively
change the original destination's DACL. This preserves the source read-only
contract and avoids a partially tightened destination after failure. Apply
the same Windows copy protocol to replaced encrypted payload for one coherent
native lifecycle; Linux/macOS retain their rename-based rollback protocol.

Private copies receive new file IDs. Consequently the existing POSIX journal's
one-identity inverse-move model cannot simply be reused. Introduce a distinct
internal Windows recovery schema/backend discriminator, retaining the POSIX
version-1 reader unchanged. This changes local recovery metadata, not the v1
encrypted backup format. Unknown schemas/platforms fail closed. Do not try to
recover a foreign-platform journal using current path spellings or ACL guesses.

Record bounded, validated metadata for original identities/content, private
rollback-copy identities/content, proposal identities/content, parent/root/
container identities, owner SID, baseline access controls, protected controls,
transaction ID, operation kind and per-entry intent/completion. Bind the
baseline to the separately held ownership record and retain duplicate-field,
type, version, bounds and namespace validation. Treat recovery JSON as untrusted
input; derive workspace paths from validated IDs/held parents and allowlists,
never arbitrary journal paths. Validate nesting/resource limits before writes.

Baseline owner/DACL and supported attributes must be observable and restorable
without elevation before replacement begins. Refuse unsupported ownership,
unrestorable access controls, additional named streams or metadata whose loss
would make inverse restoration unsafe. Do not silently delete an alternate
stream while claiming the original is recoverable. The backup format still
preserves primary-stream content rather than serving as an NTFS metadata archive.

Recover the previous logical namespace, bytes, supported timestamps and baseline
access controls; recreated replaced files can have new IDs. The existing root
and protected controls must retain their identities. This Windows-specific
identity limit must appear in user recovery documentation before enabling writes.
Original files that have not been removed keep their recorded original identity.

| State/boundary | Required evidence before next mutation | Interruption/refusal behavior |
| --- | --- | --- |
| Lock acquired; workspace not yet recorded/created | Complete bounded ownership record, private held parent | Incomplete record or uncertain workspace retained; no age-based deletion |
| Preparing proposal/copies | Private creation, full source/destination observation; no original removal | Preserve incomplete artifacts; original payload stays intact |
| Ready | Complete verified/flushed proposal and complete private rollback copies; checked old ACL/metadata | No destructive work until every old entry is demonstrably recoverable |
| Removing each original entry | Full baseline recheck, per-descendant identity/content check, durable intent | Infer absence only from a valid intent and matching saved copy; foreign/changed entries preserved |
| Publishing each proposal entry | Target absent, validated stage handle and intent, old copies intact | Locate exact proposal in stage or destination; reject duplicates/substitution |
| Published | Complete destination proof, protected controls unchanged, terminal checkpoint | Release exact held ownership; preserve private rollback by existing retention policy |
| Recovering | Prove all old/proposed/partial entries and private copies before first inverse write | Resumable inverse intent; retain proposed data and immutable old copies |
| Recovered | Previous logical tree/access controls verified; created empty root removed only if owned | Terminal checkpoint then ownership release; retain protected recovery artifacts |
| Unknown/missing/corrupt/edited state | No authoritative complete proof | Refuse inverse mutation and cleanup; preserve evidence |

Deletion can interrupt within a directory. Record descendant removal intents
and prove surviving original children, authorized absences and the complete
immutable copy. A top-level flag alone cannot justify restoring over a partial
tree. During inverse reconstruction, use separate private recovery staging,
journal its new identities before publication and never overwrite a survivor
or consume the only saved copy. Restore baseline DACLs only at their intended
destination locations, with checkpointed intent and verified inheritance
effects; saved/recovery staging must remain private throughout. If that ACL
finalization is interrupted, resume only when the exact expected intermediate
state can be proven. A mismatched descriptor is not permission to repair it.

Ordinary errors attempt the same conservative inverse protocol as explicit
recovery. Changed ownership, unexpected files, ambiguous copies, missing control
metadata and uncertain root creation block automatic rollback. Report retained
plaintext and required action with the existing output privacy rules. A
checkpoint failure after publication must not turn incomplete work into success.

Update estimates to include the full old payload copy, proposal, metadata reserve
and any inverse reconstruction copy that may be required concurrently. Check
actual free space again at execution/recovery; no disk reservation is claimed.
Retain bounded metadata and avoid unbounded reads of a tampered saved size.
No automatic pruning is added; existing merge cleanup may remove only this
proven completed workspace and must never delete edited/unknown artifacts.

## Git merge restore

Reconstruct/verify the additive union privately before creating a branch or
worktree. Precreate an owner-only empty output directory under held safe
parents, then use real `git worktree add --no-checkout` against it. Test this
behavior with Git for Windows; do not rely on protecting the directory after
Git has written there. Require a verified inheritable owner-only policy for
Git-created data/control descendants. The common Git metadata locations must
also permit protected new administrative artifacts without changing existing
user permissions; otherwise refuse before branch creation.

Preserve compare-and-create refs, selected base, original HEAD/index/config,
protected controls, safe subprocess argument lists, disabled hooks/filters and
the existing uncommitted manual-review outcome. No automatic vault commit,
push or merge. Windows executable bits are Git metadata rather than a reason
to translate `chmod` blindly; preserve the base index mode and documented byte
contract, and report unsupported filesystem timestamps accurately.

Ordinary-failure cleanup may remove only the proven unchanged new worktree/ref;
retain user edits, changed indices, unknown branch ownership and incomplete
transactions. Abrupt death can retain Git refs/worktree administration before
the common transaction exists: manual inspection remains required under the
existing Git contract. This port does not add a Git ownership journal or a new
Git recovery CLI. Common transaction recovery evidence must not be advertised
as full automatic recovery of Git side effects.

## Implementation map and native proof gates

Keep platform APIs private. Extend `_windows.py` or add narrowly scoped private
Windows modules where size warrants; do not invent a public library interface.
Use context-managed native handles with explicit transfer to/from CRT descriptors,
precise `ctypes` signatures/layouts and error/cleanup checks. Put shared Windows
flags/limits in `constants.py`. Preserve pure JSON/namespace/crypto validation
where possible, while isolating POSIX and Windows mutation state explicitly.

| Work | Concrete locations | Required proof before enabling callers |
| --- | --- | --- |
| Capability, guard and identity helpers | `_windows.py`, `constants.py`, `paths.py` internal integration | Native volume/ACL/ID checks, guarded create, directory substitution and in-place reparse refusal |
| Private files/directories and metadata reads | `_windows.py`; `transactions._read_private_json` backend | Actual owner/DACL checks on opened artifacts; malformed/unsafe grants refused without repairs |
| Ownership/checkpoint/move/delete/flush | `transactions._lock_descriptor`, `_release_lock`, `_checkpoint`, `_move`, `_sync_tree`, `_remove_captured` | Competing processes, abrupt death/reacquisition, no-clobber rename and sharing failures |
| Windows recovery lifecycle | `_execute_transaction`, `_recover_owned`, `_recover_transaction`, `_cleanup_published` backend | Private copy/partial-delete/inverse ACL states, modified artifacts, namespace and all interruption points |
| Backup builder/resource planning | `backup._write_token`, `_build_backup`, `_plan_backup` | Binary bytes, authenticated ciphertext reuse, fresh/merge/no-op and copy-inclusive estimates |
| Restore builder/timestamps/planning | `restore._build_restore`, `_set_time`, `_plan_restore` | Full authentication before mutation, bytes, metadata limitations and protected controls |
| Git reconstruction/output/cleanup | `git_restore._copy_tree`, `_stage_overlay`, `_publish_merge`, `_cleanup_git` | Native Git worktree privacy from creation, preserved origin/index and retained uncertainty |
| Installed support/evidence | `test_packaging.py`, `check_artifacts.py`, `.github/workflows/test.yml`, operation docs | Installed native round trips/recovery/Git and exact-commit matrix evidence |

Thread 2 must leave CLI mutation gates intact. Thread 3 may enable only complete
common backup/restore/recovery operations. Thread 4 may enable Git merge only
after its own evidence. Thread 5 must not describe unrun native checks as passing.
Existing-log append remains refused in every thread. Any failed proof leaves
the affected operation refused; retain partial status in #17.

The implementation must resolve these concrete gates with actual native tests:

- Guard sharing compatibility for reading/copying, creating children, timestamps,
  directory rename and handle disposition; guard close ordering without an
  unprotected mutation gap; prevention of in-place reparse conversion.
- Handle-relative rename target resolution and variable-length structure layout
  across supported Python/Windows builds; full file IDs and alias ownership.
- Journal replacement while guarding its identity and handling sharing denial;
  held-lock reads, terminal deletion and process-death retention.
- Windows copy journal reconciliation after partial original-directory deletion
  and partial inverse reconstruction, including interrupted DACL finalization.
- Git's use of a precreated private root and inherited descendant/admin DACLs
  without retroactively changing origin permissions.

Record tested API choices and failures in the design/issue handoff. Changing the
privacy, preservation or supported-operation contract requires a maintainer
decision, not an undocumented fallback.

## Validation plan

Use generated test keys, temporary vaults and temporary repositories only.
Native fixtures must assert eligible storage; mandatory eligible-runner cases
fail if setup is unavailable instead of silently skipping the feature suite.
Native APIs skip narrowly on POSIX; truly POSIX mode/FIFO/anchored-operation
tests can remain POSIX-specific. Move general behavior cases out of existing
POSIX-only module skips as each Windows operation becomes complete.

| Evidence | Required cases | Main suite locations |
| --- | --- | --- |
| Private enforcement | Explicit/inherited/extra/null DACL, changed owner, file/directory/control/rollback privacy, unsupported ACL storage | `test_windows_keys.py`; new native Windows primitive tests |
| Real access denial | Kernel access attempts with an available restricted token lacking owner access, plus descriptor/AccessCheck evidence | New native Windows ACL integration tests |
| Lifetime ownership | Two writers/recovery processes, collision preservation, noninherited handles, terminate owner then recover | `test_transactions.py`, `test_platform_transactions.py` |
| Native namespace protection | Junction/symlink/reparse, ancestor/leaf substitution, hard links, short/drive aliases, late target and unknown child | `test_platform_hardening.py`, native guard tests |
| Common CLI success | Fresh/merge backup, no-op, fresh restore/new/existing target, binary/CRLF/empty dirs, protected controls | Fresh/merge backup and fresh restore suites |
| Interruption | Ownership write, first journal, ready copies, root creation, descendant delete, proposal rename, ACL finalization, terminal release; recovery interrupted again | Native child-process transaction/recovery integration tests |
| Failures/privacy | Disk-full/I/O/short writes, sharing denial, permission failure, changed copies/DACL/journal, missing/corrupt state, bounded malformed metadata | Transaction and platform suites |
| Authentication/naming | Wrong keys, substituted/missing/corrupt objects, unsupported formats/limits, traversal/case/Unicode/reserved/stream collisions | Existing format/path/verify suites plus native restore cases |
| No-write/consent | Verify/dry run/no-op snapshots of namespace/content, no logs/locks/probes; unattended consent and redacted output | CLI/platform/backup/verify suites |
| Git | Real native Git round trip, branch/output collisions, base modes, ignored files, preserved HEAD/index/config, ordinary cleanup and user-edit retention | `test_merge_restore.py` |
| Format compatibility | POSIX fixture on Windows, newly generated Windows backup on Linux/macOS, newly generated POSIX backup on Windows | Format suite and controlled cross-job artifact exchange |
| Installed artifacts | Isolated fresh wheel/sdist CLI backup/verify/restore/recovery/Git smoke on Windows | `test_packaging.py`, artifact helper |

`AccessCheck` alone evaluates a descriptor; it does not prove a real file open
was denied. Combine parsed descriptors, restricted-token access attempts and
the kernel-enforced file API in native tests. Do not create accounts, request
elevation or substitute an administrator bypass for the owner-only test. A
missing required enforcement fixture is an explicit qualification blocker.
Microsoft documents the token/descriptor role in
[AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck).

Windows subprocess coordination must use bounded portable pipes/events/threads,
not POSIX `select` on pipe descriptors, `fork` or a negative-signal exit-code
assumption. Use deterministic readiness markers immediately at the chosen
boundary, then terminate the real child and assert retained bytes/controls and
the supported next action. Do not run concurrent `CliRunner` invocations in one
interpreter. Mocks for disk-full/API failures supplement native success and
termination tests; monkeypatching `os.name` is never native proof.

Cross-job compatibility exchange must use only generated, clearly labeled
synthetic encrypted data and test keys in short-lived CI artifacts. Restore
all bytes and required directories in both directions. Preserve existing v1
fixture checksums. Report exact runner/storage/Git versions, test names/counts,
skips and commit SHA. All nine matrix jobs must pass on the approved
implementation commit before #17 can claim full qualification.

Run Poetry lock/style/tests/coverage/Bandit/build/Twine and isolated artifact
checks proportionate to implementation, plus strict Sphinx and rendered-doc
checks. Local macOS results do not establish Windows runtime behavior. Hosted
execution depends on separately authorized Git publication; pending CI stays
pending. #17 remains open for incomplete criteria or maintainer review.

## Documentation and next-thread handoff

When operations are actually enabled, update `PLATFORMS.md`, `TRANSACTIONS.md`,
`SECURITY.md`, backup/restore/CLI/recovery guides and the Unreleased changelog.
Use `2.0.0` public behavior directives where required, preserving existing
directives. Keep remaining unsupported operations and durability limits clear.
Headers on changed Python files use `Jeff Shurtliff (via GPT-6.1 Sol)` and the
current local date; this design increment changes no Python headers.

For the next chat, use this request after making the reviewed design available
in that checkout:

> Review Issue #17 and implement only #26: native Windows safety primitives for
> Obfuscidian 2.0.0. Read root AGENTS.md, CONTRIBUTING.md and
> docs/maintainers/windows-safety-design.md, plus #25's handoff. Resolve and test
> the documented native API proof gates; keep CLI mutation gates and existing-log
> append refusal intact. Use synthetic offline fixtures, update #17/#26 as work
> progresses and distinguish local checks from native Windows CI. Use GPT-6.1 Sol
> in changed Python headers. Leave changes uncommitted; do not start #27 or publish.


## Thread 2 local implementation handoff

Thread 2 / #26 adds `src/obfuscidian/_windows_native.py`, isolated from the CLI,
key/new-log helper and POSIX transaction backend. The module is internal;
its presence does not qualify Windows write support or complete #17. No
transaction lifecycle, recovery schema, backup/restore builder or Git integration
has started. Existing-log append remains refused.

Implemented foundations:

- Lazy 64-bit native loader with explicit pointer-width-safe Win32 signatures,
  noninherited context-managed handles and redacted safety failures. There is no
  CRT descriptor transfer: binary I/O stays on the owned Win32 handle throughout.
- Read-only guarded ancestor acquisition, normalized handle namespace checks,
  fixed local NTFS/persistent-ACL/read-only-volume checks and full 128-bit file
  IDs plus volume identity. Reparse/offline/EFS objects, non-disk kinds, multiple
  file links and unresolved short/drive/UNC/device aliases are refused.
- Explicit effective-user owner SID and protected private DACL at file/directory
  creation; existing artifacts require the same owner, protection and complete
  exact ACE policy on their opened descriptor. No repair or inheritance exception
  is introduced. The directory policy has OI/CI grants; controls require explicit
  protected grants. The external Git inherited-policy validator belongs to #28.
- Exclusive `CREATE_NEW` or existing ownership acquisition with no sharing;
  bounded reads use the held handle. Process death retains the record. Explicit
  release requires matching bounded terminal bytes supplied by a future
  schema-validating transaction backend; disposition/close failures are errors.
- Bounded binary writes with short-write completion, checked truncation and
  `FlushFileBuffers`; held-handle timestamps with explicit 100 ns precision;
  no-clobber `FileRenameInfo` publication retaining source/target parents and
  the source handle. File publication rechecks full IDs, primary-stream digest
  and private ACL. Directory-tree/content reconciliation remains a lifecycle
  responsibility; the primitive does not establish descendant ownership.
- Exact held-identity disposition without recursive traversal or an overwrite/
  copy-delete fallback. A nonempty directory is preserved by kernel refusal.
  New checkpoints are bounded, exclusive, private and flushed.

API choices reviewed against the official references above. Publication uses
`RootDirectory = NULL` and a full DOS target path under the complete retained
target guard chain, with a DWORD-sized initial union and UTF-16 byte length in
the variable-size rename structure. Relative-target resolution is therefore
not assumed. Native file and directory rename/sharing tests must prove this
combination before any caller is enabled.

### Unresolved proof gates

**Exact existing-journal replacement is deliberately refused.** A deny-delete
handle pins the old journal but also prevents an ordinary overwrite rename.
Closing it to overwrite by path would lose the exact-identity guard; relaxing
sharing without an atomic destination identity comparison would permit target
substitution. `_checkpoint(previous=...)` refuses before creating/writing a
candidate. A future design must resolve this within #26 before journal integration,
for example by reviewing a bounded immutable-generation protocol with retained
old generations; no such recovery-schema change is implemented here.

**Native guard/privacy/ownership evidence remains pending.** Denying ordinary
write/delete sharing alone does not prove in-place reparse prevention: Microsoft
explicitly distinguishes attribute access in
[CreateFileW sharing semantics](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
The native junction test includes a successful unelevated positive conversion
and an actual `FSCTL_SET_REPARSE_POINT` attempt using an attribute handle acquired
before the guard. If this succeeds, the guard design is insufficient and must
be revised before integration. Directory creation's create-then-open boundary
also needs native qualification; failed acquisition retains the uncertain empty
artifact without pathname cleanup. No path-only fallback is authorized.

The native suite is `tests/integration/test_windows_native.py`. It requires
eligible storage and mandatory fixture setup rather than skipping failed setup
on Windows. Cases cover created/reused DACLs, null/extra/inherited/unsupported
ACE/OWNER RIGHTS rejection, restricted-token `AccessCheck` plus a real denied
kernel open and permissive positive control, full file/directory publication,
late-target preservation, hard links, junctions, sharing/substitution, bounded
I/O/timestamps/disposition, real terminated-owner retention and reacquisition,
explicit terminal release and injected short-write/flush failures. Native
process coordination uses a bounded thread/queue/pipe protocol. Restricted-token
fixture failure is a qualification blocker; it is not replaced by descriptor
inspection alone.

Still required within #26: native execution and repair on the supported Windows
builds/Python versions; an actual changed-owner fixture (OWNER RIGHTS rejection
is an unsafe grant test, not changed-owner evidence); drive/short-name alias and
unsupported-volume qualification; directory create/acquisition failure and
process-interruption evidence; complete journal replacement protocol/proof.
POSIX parser/failure tests are supplementary and do not discharge these gates.
No runtime OS-build support claim is made by the 64-bit loader.

### Validation and scope

Local macOS / Python 3.12.7 results:

- New scoped tests: 45 passed, 16 native Windows cases skipped.
- Full coverage run: 1,404 passed, 23 skipped, 14 TLS fixture setup errors because
  the sandbox refused an ephemeral loopback socket. A permitted loopback rerun
  with coverage append passed all 14 affected tests; this is separate retry
  evidence, not a claim that the initial invocation passed. Aggregate: 1,418
  passing tests, 23 platform skips. Coverage report: 82% overall, 21% for the
  new native module; unexecuted Win32 branches remain unqualified.
- Strict Poetry lock, Ruff lint/format, Bandit, fresh wheel/sdist build and strict
  Twine checks passed. Default offline packaging tests use available development
  dependencies through an explicit path; no downloaded wheelhouse isolation or
  native installed-write smoke qualification is claimed.
- Strict fresh Sphinx and rendered local references passed (36 HTML pages).
  External URL availability was not checked by the rendered-reference script.
- Diff/whitespace, changed-header, public-safe path/privacy and scope checks
  passed. The packaging module allowlist now includes the new private module;
  the initial suite's allowlist failure was corrected before the coverage rerun.

Exact results are also recorded in the #26 issue handoff.
Native cases skip narrowly on POSIX because Win32 enforcement cannot execute
there. Windows/hosted matrix results, runner/storage/build/Git versions and
exact-commit evidence are unavailable until separately authorized publication
and actual native execution. No real vaults, keys, accounts or elevated privileges
were used. No dependency, package version, encrypted format or public interface
changed. Changed Python headers use `Jeff Shurtliff (via GPT-6.1 Sol)` and
`10 Oct 2026`.

Leave #26 and #17 open for these gates and maintainer review. The next request
must finish #26's remaining proof before authorizing #27; this handoff is not
permission to begin a successor. All changes remain unstaged and uncommitted.

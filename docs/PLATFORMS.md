# Supported environments and platform validation

Backup and restore writes are implemented on Linux and macOS. Native Windows
supports key creation, authenticated verification and read-only planning;
vault mutation/recovery and existing-log append are refused. The table below
distinguishes tested behavior from unavailable writes.

Microsoft Store CPython is included in the Windows compatibility target for
the supported Python versions. A separate `py` launcher or traditional
installer is not required; select the actual interpreter with `python` (or its
versioned executable) and validate the version. The maintainer's Store-based
CPython 3.13.14/AMD64/64-bit virtualenv returned 907 passes, one unavailable
ownership-fixture failure and 596 platform skips in the #26 r3 diagnostic run;
it did not produce passing native qualification. See the
[primitive validation record](maintainers/windows-primitive-validation.md)
for the precise candidate, 12 October interpreter metadata follow-up and
remaining proof gaps. Store-specific path
redirection still requires the same storage, identity and ACL checks; Windows
backup/restore mutation and existing-log append remain refused.

The maintainer accepted #26's implementation handoff on 12 October 2026 with
actual ownership-transition proof deferred to #29. This permits internal
lifecycle development with production Windows CLI gates retained; the deferred
proof remains mandatory before Windows writes are enabled or 2.0.0 Windows
support is described as qualified. It does not change current supported behavior.

The [private #27 lifecycle candidate](maintainers/windows-lifecycle-validation.md)
adds synthetic backup/restore/recovery fixtures with production gates retained.
Its portable injected model checks are distinct from actual native Windows
evidence: retry4 confirms replacement restore and retry5 passes the six corrected
metadata interruption cases. The maintainer accepted that private handoff for
#28. The [private #28 Git lifecycle candidate](maintainers/windows-git-validation.md)
adds protected reconstruction/worktree handling and native fixtures. Its first
Git for Windows runs provide 30 passing retry3 cases and a separate successful
retry4 kernel-denial/positive-control proof. The maintainer accepted the private
#28 handoff; it is not a passing full-suite/matrix or supported-write claim.
Historical failed full-suite totals,
mandatory owner proof and unexecuted qualification remain explicit in those
records. No new support claim follows from these private candidates.

## Validation evidence

All nine Linux/macOS/Windows CI jobs passed on Python 3.12–3.14 in
[Test run `37519004246`](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37519004246)
at `dc56009`. Each job passed style/security, offline tests/coverage and fresh
artifact validation. Linux/macOS passed **1265 tests with 7 native Windows skips**
per job; Windows passed **709 tests with 563 platform skips** per job.
Reported coverage was 91% on Linux/macOS and 66% on Windows; skipped mutation
behavior is not validated by those figures. These are the recorded results for
that commit, rather than a claim about every later change.

Repository `.gitattributes` keeps detected text at LF, matching Ruff, even with
Windows `core.autocrlf=true`. This includes Python code blocks in Markdown.
Compatibility inputs under `tests/fixtures/` bypass line-ending conversion so
their exact bytes remain intact. These checkout rules apply to this repository;
backup/restore still preserves vault bytes independently of Git text conversion.

## Existing platform boundaries

| Behavior | Linux/macOS | Windows |
| --- | --- | --- |
| Help, configuration, authenticated verification | Implemented | Implemented; native matrix passed |
| Key creation | Exclusive private POSIX file | Exclusive protected owner-only DACL; persistent ACL storage required |
| Inventory and read-only backup/restore/Git planning | Anchored no-follow directory reads | Absolute binary reads with component and pre/post identity checks |
| Matching fresh/merge backup no-op | No locks, staging or token replacement | Same read-only contract; native matrix passed |
| Fresh/merge backup and fresh/Git merge restore mutation | POSIX ownership/private staging/recovery | Production CLI fails closed; private implementation/evidence does not establish qualified write support |
| New operational log | Private POSIX file | Protected owner-only DACL; ACL capability checked before creation |
| Existing operational log append | Requires private mode and stable identity | Refused pending file ownership/DACL validation |

The Windows refusal boundaries are intentional limitations, not successful
write validation. No chmod, unsafe rename, lossy restore, privilege elevation or
format change bypasses these boundaries. Existing-log appends remain blocked
even when a prior Obfuscidian invocation created the log.

Scanned entries use fresh `os.stat(..., follow_symlinks=False)` metadata because
Windows `DirEntry.stat()` omits device/inode identities. POSIX scans retain
directory-handle anchoring; Windows uses absolute paths with component and
pre/post identity/content rechecks. Windows read-only observation rejects
inspected junctions/reparse points and checks opened file identity and metadata.
Supported Windows Python versions can expose creation time in path `ctime` and
change time in descriptor `ctime` ([CPython issue #157671](https://github.com/python/cpython/issues/157671)).
When exact metadata comparison fails, only an exact descriptor `st_birthtime_ns`
match can bridge that distinction; identity, type/mode, size and modification
time must still match. Raw descriptor metadata, including change time, is also
compared before/after reading, and path metadata is rechecked. POSIX change-time
semantics and Windows mutation/append refusals are unchanged.
Windows traversal still lacks POSIX directory anchoring;
identity observation is best effort, not an atomic snapshot against hostile
concurrent writers. POSIX checks also do not provide a universal power-loss or
concurrent-writer guarantee. Use separate, trusted vault/key/log locations.

## Names, metadata and resources

Target preflight conservatively rejects case-folded and Unicode-equivalent
names, ambiguous ancestor names, reserved Windows devices/streams, drive/root
paths and names that exceed the target component/full-path limits. It does not
create a writable probe, rename data or normalize Markdown/attachments to make
a restore succeed. Refining read-only filesystem capability detection remains
future work under an explicit maintainer request.

Fernet objects/manifests retain the 50 MiB v1 cap. Tests exercise the real cap
using bounded/sparse files and a reduced test-only token cap for actual
encryption boundaries. A 1,001-file inventory and approximately 1 MiB binary
attachment exercise actual traversal and byte preservation without gigabytes
of allocation. Estimates account for staged objects, manifest, retained bytes
and requested rollback copies; allocation/journal reserves remain conservative
estimates, not disk reservations. Tests simulate disk-full, quota, I/O and
allocation failures. Unsupported timestamps are reported without relaxing
byte/namespace verification.

## CI and evidence

The nine jobs install unchanged locked dependencies with Poetry and run Ruff,
format checks, Bandit, the offline suite/coverage, and fresh wheel/sdist checks.
The artifact helper uses native Python temporary paths and subprocess argument
lists, including on Windows; it downloads a temporary dependency wheelhouse
before independent offline artifact installs. It does not publish packages.
CI retains pytest XML and coverage XML per OS/Python job, including failed runs
when those files are available. `pytest -ra` reports exact skip reasons.

POSIX mutation/recovery suites are skipped on Windows because those operations
fail closed. Windows instead exercises native key DACLs, junction refusal,
write refusal, new-log creation and existing-log append refusal. POSIX FIFO,
mode and anchored-write tests require those primitives; native Windows tests
are skipped on POSIX. Symlink tests skip only when a host cannot create the
fixture; denied Windows symlink privilege is distinct from junction support.
No whole-suite skip or test-success assertion replaces unsupported writes.

Offline Git preflight uses real temporary repositories, paths with spaces,
raw binary blobs and absent-ref failure. Fixtures disable configuration,
hooks, line conversions and automatic maintenance. The installed local Git
capabilities are recorded in the handoff; other Git versions remain unverified.
Existing process-death, competing-writer and interrupted-recovery tests run on
Linux/macOS; added native termination after a payload rename proves explicit
recovery with protected controls and original bytes retained.

# Platform hardening and validation

Thread 12 configures Linux, macOS and Windows CI on Python 3.12, 3.13 and 3.14.
A configured job is not a passing result. Initial local validation is recorded in the
[Thread 12 handoff](../dev/IMPLEMENTATION_PLAN.md#thread-12--cross-platform-hardening-handoff-5-october-2026).
The [Windows CI follow-up](../dev/IMPLEMENTATION_PLAN.md#thread-12--windows-ci-follow-up-6-october-2026)
records the first hosted run: all Linux/macOS jobs passed; all Windows jobs
stopped at Ruff formatting before tests/builds. Hosted acceptance remains pending.

Repository `.gitattributes` keeps detected text at LF, matching Ruff, even with
Windows `core.autocrlf=true`. This includes Python code blocks in Markdown.
Compatibility inputs under `tests/fixtures/` bypass line-ending conversion so
their exact bytes remain intact. These checkout rules apply to this repository;
backup/restore still preserves vault bytes independently of Git text conversion.

Thread 13 documentation tooling and Thread 14 release preparation are not started.

## Existing platform boundaries

| Behavior | Linux/macOS | Windows |
| --- | --- | --- |
| Help, configuration, authenticated verification | Implemented | Implemented; native matrix pending |
| Key creation | Exclusive private POSIX file | Exclusive protected owner-only DACL; persistent ACL storage required |
| Inventory and read-only backup/restore/Git planning | Anchored no-follow directory reads | Absolute binary reads with component and pre/post identity checks |
| Matching fresh/merge backup no-op | No locks, staging or token replacement | Same read-only contract; native matrix pending |
| Fresh/merge backup and fresh/Git merge restore mutation | POSIX ownership/private staging/recovery | Fails closed; private directory ACL and publication/recovery primitives remain unimplemented |
| New operational log | Private POSIX file | Protected owner-only DACL; ACL capability checked before creation |
| Existing operational log append | Requires private mode and stable identity | Refused pending file ownership/DACL validation |

The Windows refusal boundaries are intentional limitations, not successful
write validation. No chmod, unsafe rename, lossy restore, privilege elevation or
format change bypasses these boundaries. Existing-log appends remain blocked
even when a prior Obfuscidian invocation created the log.

Windows read-only observation rejects inspected junctions/reparse points and
checks opened file identity and metadata. It has no POSIX directory anchoring;
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

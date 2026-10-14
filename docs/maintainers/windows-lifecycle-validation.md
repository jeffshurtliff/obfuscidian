# Private Windows lifecycle handoff — #27

**Date:** 13 October 2026. **Target:** 2.0.0. **Status:** #27 private implementation
and scoped native evidence ready for maintainer review on the existing
`feature/17-add-safe-native-windows-support` branch. Retry4 confirms replacement
restore; retry5 passes all six corrected metadata interruption cases. The full
retry4 suite remains a failed diagnostic with the deferred owner-fixture failure.
Production Windows CLI mutation/recovery
and existing-log append remain refused. No qualified support claim is made.

The clean starting checkout contained reviewed #26 continuation `2316457` and
predecessor `36be5e0`. No checkout reset or branch change was performed. The
[approved limited deferral](windows-safety-design.md)
accepts #26's implementation handoff while retaining actual ownership-transition
proof as a mandatory #29 gate. The original real-owner fixture and production
owner/DACL validators are unchanged.

## Deliverables and private entry points

- `_windows_files.py`: independently private binary creation, native bounded
  capture, supported baseline descriptors/metadata, verified copy reconstruction,
  exact baseline deletion, no-clobber moves and destination-only DACL finalization.
- `_windows_transactions.py`: separate `windows-copy-1` local recovery schema,
  held exclusive ownership, immutable checkpoint generations, ownership cursor
  binding, descendant removal intents, proposal publication, explicit inverse
  reconstruction and ordinary-error recovery through the same protocol.
- `backup._publish_windows_backup` and `restore._publish_windows_restore` are
  private test/orchestration entry points. Shared builders reuse the existing
  Fernet/v1 codec and authentication. They are not a supported Python API or a
  CLI bypass. Production dispatch still uses the unchanged POSIX locking gate.
- `transactions._plan_transaction` includes both saved and inverse copy costs
  in Windows read-only resource estimates. Execution recalculates current native
  costs and rechecks space before ownership/publication; recovery checks inverse
  space. Estimates include allocation reserves and metadata; they reserve no disk.
- Portable injected model/schema tests and native synthetic lifecycle tests;
  the [PowerShell helper](../../.github/scripts/check_windows_lifecycle.ps1)
  selects and verifies Store or explicit CPython, captures private evidence and
  keeps the original real-owner fixture selected during diagnostic regression.

These changes introduce no dependency, CLI/public interface or encrypted-format
change. The existing CLI docstrings receive only the 2.0.0 directive for the changed
Windows read-only byte estimate; no write-support directive is added.
The POSIX backend and version-1 POSIX journal reader remain in place. No Git
merge restore integration, append, pruning or naming refinement was implemented.
Private Windows merge backups conservatively retain their completed workspace;
this candidate does not perform rollback pruning or broaden cleanup authority.

## Recovery proof and supported baseline envelope

Before removal, every old payload entry has a complete flushed private copy,
with independent native identity and exact byte digest. Saved entries use opaque
slots derived from the validated baseline; journals cannot redirect writes to
arbitrary saved paths. Original, saved, proposal and inverse IDs remain distinct.
All files stay protected while staged or retained. Recovery never consumes the
only saved copy and never overwrites a survivor or unexpected target.

Each destructive removal/publication has an intent checkpoint and an observed
completion checkpoint. Directory descendants are removed before their parent;
partial removal permits only recorded absences and unchanged surviving IDs,
bytes, supported attributes and descriptors. Directory write times may change
with authorized child progress; exact supported times are restored before the
terminal previous-tree proof. Recreated removed entries acquire new native IDs;
surviving originals, roots and protected controls retain their identities.

The held ownership record independently binds the baseline, effective owner,
full ownership/parent/source/root ancestor identities, operation/options and
latest generation/digest. A checkpoint append first records its expected next
payload. Recovery accepts an interrupted cursor completion only when the exact
published next frame, predecessor and all retained artifacts agree. A valid
older immutable chain alone is insufficient: truncating the latest generation
is refused. A partial candidate, missing control, ambiguous root creation,
foreign artifact or mismatched namespace/descriptor blocks inverse work and
preserves evidence. No age/PID cleanup or broad recursive deletion exists.

Inverse work first authenticates saved and proposed encrypted layouts for backup
recovery. It constructs separate private reconstruction slots, checkpoints their
new IDs, moves only authorized missing entries, then finalizes baseline DACLs
at intended destination locations after children are complete. Interrupted moves
and finalization accept only the recorded private/baseline states. Incomplete
inverse-copy preparation remains retained/refused; it is not silently rebuilt or
cleaned. Completed reconstruction still retains the immutable saved copies.

This candidate explicitly refuses unrestorable baselines: owner must be the
current effective user; payload DACLs must be protected, contain only supported
explicit allow ACEs and retain an explicit full owner grant. Nonowner allow grants
can be restored exactly; private copies continue to require #26's stricter exact
owner-only policy. Inherited/unprotected, deny/object/unsupported ACE forms,
named streams, unsupported attributes, links/reparse points and oversized files
are refused before ownership/payload removal rather than repaired. Payloads are
bounded to 256 entries, 32 components deep and the existing per-file read limit.
The complete worst-case checkpoint history must fit the existing count/aggregate
budget before any original deletion. Unsupported ordinary inherited payloads
remain a limitation of this candidate, not an advertised general Windows restore
capability. Root/control descriptors are observed and compared without rewriting.

The production owner/DACL refusal policy is not relaxed. Baseline-specific
original deletion/finalization is confined to the private lifecycle. Administrators
and malicious same-user actors remain outside the documented privacy guarantee.
There is no universal power-loss durability or directory-flush claim.

## Actual evidence and unexecuted gates

New local evidence is recorded below. Portable injected
filesystem responses exercise orchestration/schema logic, not Win32 sharing,
DACL enforcement, native IDs or process termination. Native fixtures skip narrowly
on POSIX; on Windows eligible setup is mandatory and failures stay visible.
Native child tests use `sys.executable`, bounded pipe/thread coordination,
readiness at the selected boundary and a reported actual worker PID. The repaired
harness verifies spawned ancestry, holds the worker process handle, terminates
and waits for that worker before closing stdin or reacquiring filesystem handles.
The retry3 native run exercised this repaired harness successfully. The cases cover
original descendant deletion, top-level proposal publication, root creation,
inverse publication/ACL states and terminal ownership release. Unbound root and
incomplete inverse construction are expected conservative refusal cases.

The predecessor r3 record is unchanged: **907 passed, 1 unavailable real-owner
fixture failure, 596 skipped**, exit 1; owner supplements **3 passed**, exit 0.
The host was Windows 11 Home build 26200, unelevated, Microsoft Store CPython
**3.13.14 / AMD64 / 64-bit**. This is prior #26 evidence, not a #27 run or a passing
qualification result. The injected owner supplement does not discharge the real
filesystem ownership-transition requirement. Raw reports remain private.

## Local validation — 12 October 2026

Executed on macOS (Darwin), ARM64 CPython **3.12.7**, Poetry **2.4.2**:

| Check | Actual result |
| --- | --- |
| Final full synthetic offline suite | **1479 passed, 109 platform skips**, exit 0; includes existing isolated artifact tests |
| Portable injected lifecycle/schema model | **29 passed**; not native Windows proof |
| New native lifecycle collection | **55 cases collected**, all skipped on POSIX; not executed natively |
| CLI unit/native selection after docstring directives | **36 passed, 55 native skips** |
| Ruff lint and format | Passed; 116 Python files already formatted |
| Poetry strict lock, Bandit, fresh wheel/sdist and Twine | Passed; no Bandit findings; dependencies/lock unchanged |
| Strict fresh Sphinx and rendered references | Passed; **38 HTML pages**, local references/assets only |
| Scope, headers, LF/whitespace, literal private paths and Git diff | Passed; 19 scoped files, all unstaged/uncommitted |

The sandbox initially blocked 14 existing TLS loopback fixtures; the full run
above used authorized local loopback access. The package archive allowlist was
extended for the two new private modules. Initial builder callback failures were
fixed and their four existing regressions passed before the final full run.
CLI executable AST, production locking and owner-validator ASTs match the
starting commit; the original real-owner fixture, append/Git implementations and
dependency files have no diff. Public directives describe only the changed
Windows read-only estimate, never write enabling.

At this initial implementation handoff, no native #27 run, PowerShell execution/syntax validation, Linux run, hosted CI,
real-vault/key test or exchanged Windows/POSIX artifact qualification was executed.
The PowerShell helper is source-reviewed but must be executed on the eligible
host. New local green checks cannot clear those operation/platform gates.

Git handoff: **13 modified tracked files and 6 new files**, all unstaged and
uncommitted at `2316457cb4b838aaf8087b0ab6c545642ebf5dfb`, on the unchanged
`feature/17-add-safe-native-windows-support` branch. #17/#27 tracking updates
were synchronized through authenticated `gh` after the connector returned
integration 403. Issues stay open. No stage, commit, reset, branch creation,
push, merge, PR, closure, publication or next-thread implementation occurred.

## Exact native commands

Use an existing unelevated Windows PowerShell session, eligible local NTFS and a
reviewed source snapshot containing these unstaged files. From the repository
root, select the actual desired Store interpreter through `python`, or replace
`python` with an explicit installed executable. No `py` launcher is required.

```powershell
& .\.github\scripts\check_windows_lifecycle.ps1 -Python python -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-27-reports"
```

For the Store-installed CPython 3.14 testing host, use the
[3.14 wrapper](../../.github/scripts/check_windows_lifecycle-314.ps1):

```powershell
& .\.github\scripts\check_windows_lifecycle-314.ps1 -Python python -ReportDirectory "$env:TEMP\obfuscidian-27-reports-314"
```

For the maintainer's source-text invocation on the testing host where `.ps1`
execution is disabled, run this from the repository root:

```powershell
$lifecycleScriptPath = (Resolve-Path '.\.github\scripts\check_windows_lifecycle-314.ps1').Path
$lifecycleScriptDirectory = Split-Path -Parent $lifecycleScriptPath
$lifecycleSource = Get-Content -LiteralPath $lifecycleScriptPath -Raw
$lifecycleBlock = [ScriptBlock]::Create($lifecycleSource.Replace('$PSScriptRoot', '$lifecycleScriptDirectory'))
& $lifecycleBlock -Python python -ReportDirectory "$env:TEMP\obfuscidian-27-reports-314"
```

The wrapper loads only the adjacent shared helper as a script block, binding its
script directory explicitly so repository discovery remains correct. No nested
`.ps1` invocation or execution-policy setting change is performed. Both files must
come from the reviewed source snapshot. The helper's checks and selected tests
remain unchanged.

This selects minor version 3.14 and reuses the shared helper, including both test
runs and the unchanged real-owner fixture. The actual patch version (for example,
3.14.6) is recorded and compared with the Poetry interpreter. It does not require
the `py` launcher. Both helper files are included in source hash evidence. The
separate report directory keeps this run distinct from the earlier 3.13 evidence.
The wrapper has been source-reviewed locally; actual PowerShell/native execution
remains pending and must be reported separately.

For another target under qualification, use `-ExpectedMinor 12` or `14` with the
shared helper and matching explicit executable. The helper rejects the wrong implementation/minor version,
architecture or elevated token, verifies the Poetry interpreter's actual patch
version, validates the existing lock and runs the private native suite plus full
diagnostic suite. It records OS/build/Git, source-file SHA-256s, interpreter
metadata, exit codes, JUnit and text reports outside the checkout. It neither
changes machine policy nor dispatches hosted CI. No execution-policy setting or
machine-wide adjustment is performed by either invocation method.

The helper installs locked runtime/development requirements with
`poetry install --with dev --without docs --no-interaction`. Its selected and full
pytest runs do not import Sphinx or build documentation. Optional documentation
dependencies and strict documentation builds remain separate qualification
checks; this helper does not establish documentation-build success.

Keep native reports and machine paths private. Return sanitized OS/build/storage,
actual Python version/architecture/Store detection, candidate source hashes,
commands/exits, individual failure names, counts and narrow skips. Distinguish
real native successes, injected responses and missing fixtures. The known real
owner fixture remains selected: an unavailable fixture is a failure, not a skip,
xfail or passing qualification. Do not enable writes in response to a green subset.

### Interpreter preflight repair — 12 October 2026

The supplied 3.13 transcript reached the patch-comparison error before any
lifecycle tests ran. Direct and Poetry one-line probes both reported CPython
3.13.14 with exit 0 and one captured JSON line; Poetry was 2.5.1. The requested
report directory held direct metadata but no Poetry metadata. This does not
establish a genuine patch mismatch or any native lifecycle result.

The likely cause is the multiline `-c` probe crossing
[Poetry 2.5.1's Windows shell launch](https://github.com/python-poetry/poetry/blob/2.5.1/src/poetry/utils/env/base_env.py).
The helper now saves the complete probe as `interpreter-probe.py` outside
the checkout and executes that file with both interpreters. It requires one
nonempty JSON line and a nonempty version before comparison, saves both reports,
prints both versions and retains the exact patch check. A Windows regression
exercises file execution through the shell with a spaced path and UTF-8 BOM;
portable injected cases check the probe's success/refusal behavior. These checks
remain distinct from actual Windows execution, which still requires a rerun.
The 3.14 wrapper delegates to the repaired shared helper as before. No environment
removal, dependency change, policy change or production gate relaxation is needed.

New local checks for this repair: **35 passed, 2 Windows-only skips** across the
tooling and transaction model tests; Ruff lint/format, strict Sphinx and rendered
references passed. The six tooling passes use injected interpreter/token
responses; the two real Windows shell cases were not executed here. PowerShell,
native lifecycle execution and hosted CI remain unexecuted for this repair.

### Documentation dependency installation refusal — 12 October 2026

The next supplied attempt stopped during locked dependency installation with
`FileNotFoundError` for a `sphinxcontrib-serializinghtml` 2.0.0 locale file. This
occurred before the Poetry probe and lifecycle tests, so it does not verify the
interpreter repair or provide a native lifecycle result. The complete missing
path and traceback were not supplied; a path-length, cache or installer cause
has not been established. No machine policy or environment deletion is needed
for the bounded helper change.

The helper previously installed the optional docs group even though it never
ran Sphinx. It now explicitly excludes that group while retaining locked runtime
and development requirements, strict lock validation and every existing pytest
selection. The docs group and lockfile remain unchanged. The supplied host must
rerun the helper; strict documentation build and broader native qualification
remain separate gates.

### First #27 native diagnostic and fixture repairs — 12 October 2026

The supplied retry2 transcript and JUnit reports establish execution of both
helper suites at candidate `0a68ace`. All **33 recorded source hashes** match the
local candidate. Direct and Poetry metadata both report **Microsoft Store CPython
3.13.14 / AMD64 / 64-bit**, unelevated, on **Windows 11 Home build 26200**;
Git is 2.55.0.windows.5. Interpreter preflight, development dependency installation
and strict lock validation completed. This run did not build documentation.

| Suite | Actual result |
| --- | --- |
| Selected qualification | **101 passed, 38 failed, no skips/errors**, exit 1; 139 cases |
| Full diagnostic | **962 passed, 38 failed, 596 skipped, no errors**, exit 1; 1596 cases |
| Private native lifecycle module | **38 passed, 17 failed**, no skips |
| Native checkpoint module | **16 passed, 1 failed**, no skips |
| Native primitive module | **28 passed, 2 failed**, no skips; includes the unchanged unavailable real-owner fixture |
| Injected transaction model | **11 passed, 18 failed**; never native API proof |
| Interpreter tooling | **8 passed**: six injected checks and two actual Windows shell-file cases |

Native modules also include injected faults/responses around real filesystem
operations. Their module totals do not turn those supplements into uninjected
proof, clear failed cases or establish complete native qualification.

The helper ran to completion, but neither suite passed. Seventeen lifecycle
failures encounter plain pathname I/O while inspecting/tampering with retained
long checkpoint paths. The injected model also uses ordinary pathname creation,
read/write/stat and removal for these long controls; its original exceptions are
masked by the lifecycle's conservative error. That is a likely fixture cause,
awaiting native confirmation. The two additional primitive/checkpoint failures
observe sharing denial during post-termination reacquisition; the failing
checkpoint boundary differs between the selected and full runs. No production
sharing refusal is relaxed to make these tests pass.

Fixture-only repairs use the existing internal DOS long-path conversion for
inspection, model I/O and deliberate corruption, preserving ordinary logical
bindings and production checkpoint names. A regression exercises actual long
fixture creation, binary reads, corruption and deletion without a policy change.
Native transaction, checkpoint and ownership children now report `os.getpid()`;
the parent validates spawned ancestry and verifies actual worker death and exit
status before releasing stdin. Windows venv executables are
[CPython redirectors](https://github.com/python/cpython/blob/v3.13.14/PC/venvlauncher.c).
The launcher uses a kill-on-close job but waits only for its launched child;
waiting for launcher termination alone does not explicitly await that worker.
[Microsoft documents asynchronous process termination](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess),
requiring a wait on the actual process. The previous child-test passes therefore
need repetition with the repaired death verification before accepting boundary
proof. This is a harness correction, not evidence of a Store production defect.

The repaired helper selects the new fixture regressions and hashes their shared
test support module. Production code, real-owner assertions, owner/DACL validators,
CLI mutation/recovery and existing-log append gates are unchanged. The known
owner-fixture failure remains selected and mandatory for #29; the earlier #26 r3
record remains **907 passed, 1 failed, 596 skipped**, with three owner supplements
passed. A new native run, other hosts/interpreters, hosted CI and broader artifact
qualification remain pending. Raw supplied reports and identifying paths are private.

Local fixture-repair checks on macOS ARM64 CPython 3.12.7 / Poetry 2.4.2:
**48 passed, 105 Windows-only skips** in the scoped selection. The new worker
ordering/refusal responses are injected; actual long-path I/O and worker APIs
were skipped here. Ruff lint/format, strict Sphinx and local reference checks
across **38 HTML pages** passed. PowerShell is unavailable locally. Source,
dependency/lock and real-owner fixture AST comparisons confirm those boundaries
are unchanged; reviewed #26 continuation `2316457` remains an ancestor of HEAD.
All ten scoped repair files remain unstaged/uncommitted on the requested branch.
Full local regression: **1498 passed, 112 platform skips**, exit 0, with authorized
loopback access. The preceding sandboxed attempt returned **1484 passed,
112 skipped, 14 localhost TLS fixture setup errors**, exit 1; it is not relabeled
as passing. Neither local run executes the new Windows APIs or hosted CI.

### Retry3 native evidence and replacement-restore diagnostic — 12 October 2026

The supplied retry3 transcript and JUnit reports correspond to the maintainer's
commit `4bc1b1a`; all **35 source-file hashes** match that commit. The archive's
SHA-256 is `5759996a3538cb69bb691566c29a697e79ba658853be3a89d89848f6df8aa73d`.
Direct and Poetry probes again report **Store CPython 3.13.14 / AMD64 / 64-bit**,
unelevated, on **Windows 11 Home build 26200**, Git 2.55.0.windows.5.
Strict lock/interpreter preflight completed. Both suites still exit 1.

| Suite | Actual retry3 result |
| --- | --- |
| Selected qualification | **151 passed, 2 failed, no skips/errors**; 153 cases |
| Full diagnostic | **1012 passed, 2 failed, 596 skipped, no errors**; 1610 cases |
| Private lifecycle module | **54 passed, 1 failed**, no skips |
| Native checkpoint module | **17 passed**, no failures/skips |
| Native primitive module | **29 passed, 1 failed**, no skips; failure is the unchanged unavailable real-owner fixture |
| Injected transaction model | **29 passed**; not native API proof |
| Interpreter tooling | **8 passed**: six injected checks and two Windows shell-file cases |
| Fixture support | **14 passed**: thirteen portable/injected checks and one actual Windows long-path I/O regression |

The repaired child harness passed all **28 lifecycle interruption cases**:
13 forward boundaries, 11 inverse boundaries, two created-root cases, broader
DACL finalization and inverse-root removal. The four primitive checkpoint
termination cases and exclusive owner-death/reacquisition also passed with actual
worker termination/wait verification. Boundary/fault selection is injected;
filesystem operations and child termination are native. Changed-artifact,
authentication, namespace, sharing, baseline-DACL recovery and four production
CLI refusal cases passed. Other fault-response supplements remain explicitly
injected evidence. This is scoped evidence on one host/interpreter, not qualified
Windows 2.0.0 support or hosted CI.

The remaining lifecycle case is
`test_private_native_backup_fresh_merge_noop_and_restore_roundtrip`. It now
passes fresh backup, no-op merge without writes, changed merge retaining historic
content, fresh binary restore, replacement confirmation refusal and confirmed
fresh backup replacement. It fails at the final **confirmed replacement of an
already restored plaintext destination**. The transaction reports that retained
artifacts require explicit recovery. The reports suppress its underlying
exception; its exact cause and retained-state integrity cannot be established
from these attachments. This failure is **not** covered by the owner-proof
deferral and remains a #27 blocker. No production metadata, reconciliation,
owner/DACL or sharing policy is changed on an unverified diagnosis.

A test-only diagnostic now inspects the suppressed in-memory exception context
and prints exception types plus Obfuscidian function names/line numbers and
numeric API codes matching the native loader's exact path-free templates. It
excludes arbitrary messages, traceback filenames, locals and filesystem contents; handles
bounded/cyclic chains. The failing test invokes it only after unexpected
replacement failure. Production exception handling, API and CLI behavior remain
unchanged. These new diagnostics are absent from the supplied retry3 candidate
and need one targeted native execution after maintainer review/commit/sync:

```powershell
New-Item -ItemType Directory -Force -Path "$env:TEMP\obfuscidian-27-replacement-diagnostic" | Out-Null
& poetry run python -m pytest -q -ra tests/integration/test_windows_lifecycle.py::test_private_native_backup_fresh_merge_noop_and_restore_roundtrip "--junitxml=$env:TEMP\obfuscidian-27-replacement-diagnostic\replacement.xml" *> "$env:TEMP\obfuscidian-27-replacement-diagnostic\replacement.txt"
Write-Output "Replacement diagnostic exit: $LASTEXITCODE"
```

Run from the repository root in the already validated 3.13 Poetry environment.
This diagnostic subset intentionally targets the single unresolved lifecycle
case; it is not a qualification suite or a replacement for the unchanged full
helper/owner test. Return its two private reports and identify the tested commit.
After diagnosis/repair, repeat the full helper into a fresh report directory.

New local diagnostic checks on macOS ARM64 CPython 3.12.7 / Poetry 2.4.2:
**52 passed, 105 Windows-only skips** in the scoped selection; four added
cases verify suppressed context visibility, output privacy/bounds and numeric-code filtering.
Ruff lint/format, strict Sphinx and local reference checks across **38 HTML pages**
passed; whitespace, scope, privacy and current Python headers were checked.
These are synthetic local checks, not native reproduction of the failure.
The earlier full local result **1498 passed/112 skipped** predates these four
tests; it is not claimed as a rerun. No new full native suite or hosted CI was
executed here. All diagnostic/evidence updates remain unstaged/uncommitted on
the same branch. #28/#29 implementation is unstarted; the original #26 r3 result
and mandatory deferred owner proof remain unchanged.

### Targeted diagnostic and publication metadata candidate — 12 October 2026

The supplied targeted PowerShell transcript shows the maintainer pulling
diagnostic commit `8a0fcfe` and running the single replacement roundtrip test:
**1 failed in 18.93 seconds**. Its filtered context locates the underlying
`_NativeSafetyError` in `_execute:849` → `_reconcile:498`, after publication.
That check requires each proposal group to exist exactly once, at its recorded
stage or destination location, with complete matching records. The transcript
does not identify which field differs. It contains no new interpreter metadata,
source-hash manifest or JUnit report; retry3's host metadata remains earlier
evidence. This is actual native failure evidence, not a passing rerun.

Creation-time tunneling is a plausible cause, rather than a confirmed diagnosis
from that trace. [Microsoft documents](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/fltkernel/nf-fltkernel-fltgettunneledname)
that a delete followed by a same-name rename can reuse cached creation time.
An injected model reproduces that effect and causes the prior `_move`
implementation to fail. This controlled counterexample does not establish that
the supplied Windows failure was caused by tunneling.

The candidate repair checks the complete private proposal before its own rename
and keeps its native handle held through the subsequent observation and metadata
verification. Only creation-time drift from that operation may be restored to
the already recorded value, after identity, type, size, digest, write time,
attributes and exact owner/DACL all match. Any other drift is refused before
metadata rewriting. The final record must match completely. The same private
move serves forward publication, returning proposals and inverse reconstruction.
Recovery record matching, original real-owner assertions and native owner/DACL
validators remain unchanged; no checkpoint-only authorization is introduced.

Metadata I/O failure or termination before correction can leave an uncertain
creation time. Explicit recovery still refuses that mismatch and retains all
artifacts and ownership. It does not retrospectively normalize unexplained
changes. Six new native child-process cases target both sides of metadata
verification during forward publication, proposal return and inverse
reconstruction. Each records `actual_creation_time_tunnel_observed`: a host that
does not produce cache drift does not establish that particular native proof.
Exact states must recover; uncertain states must refuse without inverse writes.
The native cases have not yet executed for this repair.

Eight added injected regressions cover exact forward/inverse records and binary
saved-copy preservation, metadata failure retention and refusal of six kinds
of non-creation drift before any metadata rewrite. Local scoped checks on macOS
ARM64 CPython 3.12.7 / Poetry 2.4.2: **60 passed, 111 Windows-only skips**.
The controlled prior-implementation comparison returned its expected **1 failed**;
the current injected transaction model returned **37 passed**. These are
supplementary local evidence, not native qualification. Final full local
regression: **1510 passed, 118 platform skips**, exit 0, with loopback access
for synthetic localhost TLS fixtures. Ruff lint/format (119 files), Bandit,
strict Poetry lock validation, strict Sphinx and local references across
**38 HTML pages** passed. Diff, header, scope and privacy checks passed.
Windows execution, PowerShell and hosted CI were not executed locally.

After maintainer review/commit/sync, run the existing helper from the repository
root on the original unelevated Store Python 3.13 machine; no new wrapper is
needed:

```powershell
& .\.github\scripts\check_windows_lifecycle.ps1 -Python python -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-27-reports-313-retry4"
```

Return the private reports and tested commit. The helper retains the mandatory
owner fixture in both suites. On the same unavailable token, its known failure
remains expected and must be reported; all other failures need investigation.
No policy, naming, dependency, public interface or production CLI gate change
is included. Hosted CI, other interpreters/hosts and native repair confirmation
remain unexecuted. Six repair/source/test/document files remain unstaged and
uncommitted on the existing branch; no agent Git delivery was performed.

### Retry4 native evidence and protected-control fixture correction — 12 October 2026

The supplied retry4 archive has SHA-256
`3ba25117be0bd07072fc92268c0afecbfa9f077a98001e2ce9c505471775f95f`.
All **35 recorded source-file hashes** match maintainer commit `33e8aab`.
Direct and Poetry reports agree on **Microsoft Store CPython 3.13.14 / AMD64 /
64-bit**, unelevated, on **Windows 11 Home build 26200**, Git 2.55.0.windows.5.
Both helper suites executed; no separate PowerShell transcript was supplied.
The archive records both exits as 1. Reports, host names and identifying paths
remain private; only sanitized evidence is recorded here.

| Suite | Actual retry4 result |
| --- | --- |
| Selected qualification | **166 passed, 5 failed, no skips/errors**; 171 cases, exit 1 |
| Full diagnostic | **1027 passed, 5 failed, 596 skipped, no errors**; 1628 cases, exit 1 |
| Private lifecycle module | **57 passed, 4 failed**, no skips |
| Native checkpoint module | **17 passed**, no failures/skips |
| Native primitive module | **29 passed, 1 failed**, no skips; unchanged unavailable real-owner fixture |
| Injected transaction model | **37 passed**; not native API proof |
| Interpreter tooling | **8 passed**: six injected checks and two Windows shell-file cases |
| Fixture support | **18 passed**: seventeen portable/injected checks and one Windows long-path I/O case |

The previously failing private backup/restore roundtrip now **passes in both
suites**, including confirmed replacement of previously restored plaintext.
This supplies native success evidence for the private metadata-preservation
candidate on this host, without proving the exact field that caused retry3's
failure. Existing lifecycle successes, the original 28 actual-worker lifecycle
interruption cases and production CLI refusal cases also pass. The eight new
transaction regressions remain injected evidence. Native modules retain their
injected fault/descriptor supplements; passing module totals do not turn those
supplements into uninjected filesystem proof or qualified platform support.

Two new proposal-return metadata interruption cases pass, with
`actual_creation_time_tunnel_observed=False` in both suites. They prove actual
worker termination and subsequent recovery for the exact observed state, not
recovery from a real creation-time drift. The four forward/reconstruction cases
also reach verified child termination, then fail before recording observations
or attempting recovery: their test inspection calls `_capture` on a destination
containing protected root `.git`, without passing the transaction's exclusions.
The production reader correctly refuses it as a nested control. These four
failures are fixture errors and remain failed evidence; they are not covered by
the owner deferral or relabeled as successful recovery proof.

The test-only correction passes `_protected_names(plan.preserve_config)` to its
payload observation. It leaves the whole-tree before/after/retention snapshots
inclusive of protected controls and retains every metadata and recovery assertion.
No production reader, transaction, recovery, owner/DACL or CLI check changes.
The real-owner test still fails with `assignable_owner_group_available=False`
before reassignment; actual changed-owner proof remains mandatory in #29.
Four source/document files remain unstaged/uncommitted on the existing branch;
HEAD is `33e8aab`, and reviewed continuation `2316457` remains an ancestor.

New local checks for this test-only correction: **60 passed, 111 Windows-only
skips** in the scoped selection. Ruff lint/format (119 files), strict Sphinx,
local references across **38 rendered HTML pages**, diff/privacy/scope and Python
header checks passed. No full runtime rerun was needed for the inspection-only
change; the earlier **1510 passed/118 skipped** result remains earlier evidence.
PowerShell and the corrected native cases have not executed locally.

After maintainer review/commit/sync, rerun only the six metadata-boundary cases
from the repository root in the already validated 3.13 Poetry environment:

```powershell
$metadataReports = "$env:TEMP\obfuscidian-27-metadata-retry5"
New-Item -ItemType Directory -Force -Path $metadataReports | Out-Null
git rev-parse HEAD | Set-Content -Encoding UTF8 (Join-Path $metadataReports 'candidate-commit.txt')
Get-FileHash -Algorithm SHA256 '.\tests\integration\test_windows_lifecycle.py' | Select-Object Hash | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $metadataReports 'test-source-sha256.json')
& poetry run python -m pytest -q -ra tests/integration/test_windows_lifecycle.py::test_actual_same_name_publication_death_at_metadata_boundary "--junitxml=$metadataReports\metadata.xml" *> "$metadataReports\metadata.txt"
Write-Output "Metadata interruption exit: $LASTEXITCODE"
Compress-Archive -Path "$metadataReports\*" -DestinationPath "$metadataReports.zip"
```

Return that private ZIP. This diagnostic subset does not clear the owner gate,
replace a full qualification run or claim the unchanged owner fixture passes;
retry4's complete results and failure counts remain recorded above. A full
repeat is warranted if these results expose a production change or further
failure; unchanged native cases need not be repeated to diagnose this fixture.
Other hosts/interpreters, exchanged artifacts and hosted CI remain unexecuted.

### Retry5 metadata evidence and #27 review handoff — 13 October 2026

The supplied targeted archive has SHA-256
`ec8fc8253112a0bac23f5a23a6dc21b544e127736dac37f178b6548c6e31ab16`.
Its recorded candidate is `cbd30bb5a1b56d1c8c2281587a3549f1a6fc078e`.
The recorded lifecycle-test SHA-256,
`2e7cebd7e5d70c937373afef0af714132e673817094e32041279966156466797`,
matches that commit and the current checkout. Comparison with `33e8aab` confirms
production source, dependencies and the real-owner test are unchanged; only
protected-control test inspection and the accompanying docs changed.
The archive contains no new interpreter/host probes, full source manifest or
saved shell exit code. Retry4's Windows 11 Home build 26200 / unelevated Store
CPython 3.13.14 / AMD64 / 64-bit metadata is earlier evidence, not newly measured
metadata for this subset. Raw host-identifying output remains private.

**Actual targeted result: 6 passed, 0 failures/errors/skips, 6 warnings**, in
69.59 seconds. The warnings concern `record_property` with JUnit `xunit2`;
the parsed XML still contains every named case and its observation property.
No code/configuration change was made to suppress those warnings.

| Actual worker-termination case | Creation-time drift observed | Verified result |
| --- | --- | --- |
| Forward, before metadata verification | Yes | Recovery refused; all artifacts and ownership retained without inverse writes |
| Forward, after metadata verification | No | Explicit recovery restored the original binary tree and released ownership |
| Proposal return, before metadata verification | No | Explicit recovery restored the original tree |
| Proposal return, after metadata verification | No | Explicit recovery restored the original tree |
| Inverse reconstruction, before metadata verification | Yes | Recovery refused; all artifacts and ownership retained without inverse writes |
| Inverse reconstruction, after metadata verification | No | Explicit recovery completed the original tree |

These are real native filesystem operations and verified actual child-process
terminations; boundary selection uses the private synthetic observation hook.
The two before-correction cases establish actual creation-time drift and strict
preservation/refusal on this fixture. The four exact-state cases establish
resumable recovery. Proposal-return cases did not produce drift and are not
claimed as proof for a drifted proposal return. This does not guarantee recovery
after arbitrary metadata interruption or prove the exact original retry3 cause.

Together with retry4's replacement roundtrip, original 28 lifecycle termination
cases, sharing/DACL/namespace refusals, authentication/retention checks and
production CLI refusal cases, this closes the identified #27 implementation and
fixture follow-ups on the supplied host. The private lifecycle and scoped native
handoff are ready for maintainer review; no additional #27 code repair is
identified. Full-suite totals are not recomputed or relabeled: retry4 remains
**166 passed/5 failed** selected and **1027 passed/5 failed/596 skipped** full,
both exit 1. Retry5 is a separate six-case success. The original real-owner
fixture remains unchanged and unavailable; #26 r3 remains **907 passed/1 failed/
596 skipped**, with three passing owner supplements.

This review changes only three documentation files. Strict Sphinx, local
references across **38 rendered HTML pages**, consistency/privacy and diff checks passed;
no new local runtime, PowerShell or hosted execution is claimed. The earlier
local full **1510 passed/118 skipped** and scoped **60 passed/111 Windows-only
skips** remain earlier validation. Changes stay unstaged/uncommitted on the
requested branch, HEAD `cbd30bb`; reviewed #26 continuation `2316457` is present.
#17/#27 stay open pending maintainer review, with #28/#29 implementation unstarted.

## Current successor boundary — 13 October 2026

The maintainer accepted this private #27 handoff for the separately authorized
#28 continuation. The [private Windows Git candidate](windows-git-validation.md)
implements only that lifecycle. Retry3 passes 30 native Git cases and targeted
retry4 passes the corrected inherited-control kernel-denial/positive-control
proof. The maintainer accepted the private #28 handoff, with all
production gates retained. Historical unstarted statements above record their
original handoff dates; they are superseded by this continuation status.

## Remaining qualification and scope

- Maintainer acceptance of the bounded private #27 lifecycle and its
  native/injected evidence permits the #28 continuation. No further native
  rerun is needed for the resolved fixture on unchanged code. Additional failures
  or implementation changes must be investigated and retested before acceptance.
- #29 must clear the deferred actual changed-owner refusal proof and applicable
  exact-commit OS/Python matrix, exchanged synthetic v1 backups and installed
  wheel/sdist qualification. No account creation, privilege activation or injected
  substitute is authorized. Hosted CI and exchanged artifacts were not run here.
- #28 Git merge restore has 30 native retry3 passes and a separate successful
  retry4 kernel proof. Its bounded private handoff is accepted by the maintainer.
  Historical failed full-suite totals remain unchanged. #29 now has authorized
  [qualification preparation](windows-qualification.md), with actual owner
  proof and external execution still pending.
  No Windows write enabling or qualified 2.0.0 claim precedes these required gates.
- #17/#27 remain open pending review/qualification. Source changes remain
  unstaged/uncommitted; no push, merge, PR, release or publication was performed.

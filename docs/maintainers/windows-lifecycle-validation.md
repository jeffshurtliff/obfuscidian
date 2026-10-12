# Private Windows lifecycle handoff — #27

**Date:** 12 October 2026. **Target:** 2.0.0. **Status:** implementation candidate
on the existing `feature/17-add-safe-native-windows-support` branch, pending
review and actual native execution. Production Windows CLI mutation/recovery
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
Native child tests use `sys.executable`, portable bounded pipe/thread coordination,
readiness at the selected boundary and actual process termination. They cover
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

No native #27 run, PowerShell execution/syntax validation, Linux run, hosted CI,
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

Keep native reports and machine paths private. Return sanitized OS/build/storage,
actual Python version/architecture/Store detection, candidate source hashes,
commands/exits, individual failure names, counts and narrow skips. Distinguish
real native successes, injected responses and missing fixtures. The known real
owner fixture remains selected: an unavailable fixture is a failure, not a skip,
xfail or passing qualification. Do not enable writes in response to a green subset.

## Remaining qualification and scope

- Execute/review the #27 native suite, including actual sharing/DACL/namespace,
  metadata/stream APIs, every real child boundary and broader baseline finalization.
  Any failure must retain affected production gates and be fixed/retested within
  the authorized thread before claiming native lifecycle proof.
- #29 must clear the deferred actual changed-owner refusal proof and applicable
  exact-commit OS/Python matrix, exchanged synthetic v1 backups and installed
  wheel/sdist qualification. No account creation, privilege activation or injected
  substitute is authorized. Hosted CI and exchanged artifacts were not run here.
- #28 Git merge restore remains unstarted. #29 implementation remains unstarted.
  No Windows write enabling or qualified 2.0.0 claim precedes these required gates.
- #17/#27 remain open pending review/qualification. Source changes remain
  unstaged/uncommitted; no push, merge, PR, release or publication was performed.

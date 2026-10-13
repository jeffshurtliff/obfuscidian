# Private Windows Git merge restore handoff — #28

**Date:** 13 October 2026. **Target:** 2.0.0. **Status:** private implementation
candidate; the first actual Git for Windows run failed. The administration
attribute correction below needs a native rerun. Production Windows
CLI mutation/recovery and existing-log append remain refused. This is neither
qualified Windows support nor a supported Python library API.

Work stays on `feature/17-add-safe-native-windows-support`, starting at `4c38cce`.
Reviewed #26 continuation `2316457` and #27 implementation through `cbd30bb`
are ancestors. The lifecycle test SHA-256 matches the retry5 record:
`2e7cebd7e5d70c937373afef0af714132e673817094e32041279966156466797`.
The subsequent `4c38cce` commit changes only the accepted evidence documentation.
No reset or branch change occurred. The maintainer accepted #27's private handoff
for this continuation. Read the [safety design](windows-safety-design.md),
[primitive evidence](windows-primitive-validation.md) and
[lifecycle evidence](windows-lifecycle-validation.md) with `AGENTS.md` and
`CONTRIBUTING.md` before continuing.

## Implementation and preservation

`src/obfuscidian/_windows_git_restore.py` contains the private Windows planner,
reconstruction, copy, publication and ordinary-failure cleanup. It reuses #27's
authenticated builders, binary-copy primitives and private transaction lifecycle.
The shared Git planner gains a private file-mode selection argument, defaulting
to its prior behavior. Only the private Windows planner selects byte validation
with executable modes preserved in the base Git index. The supported CLI planner,
POSIX publisher and all production gates keep their previous behavior.

- Authenticate and reconstruct the complete additive union before creating refs
  or a worktree. Independently private files/directories protect reconstruction,
  proposal and retained transaction evidence. Copying preserves primary-stream
  binary/CRLF bytes and supported creation/write times; precision differences
  produce a redacted warning. No `chmod` translation is used for Git modes.
- Audit the existing shared Git administration and its writable parent policies
  before side effects. Require an explicitly protected full-owner root, then
  inspect every descendant's owner, complete DACL, full native ID, regular type,
  supported attributes, stream envelope and bounded content. Refuse unsafe
  existing permissions without tightening or repairing them.
- Create an explicitly protected empty review root before trusted Git writes
  `.git` or administration. Hold common/root-parent/worktree guards across Git
  calls, then audit the generated controls. Git descendants may have exactly one
  inherited effective full-owner ACE, with OI/CI on directories. This separate
  validator does not relax production transaction/control owner/DACL checks.
  [Microsoft inheritance guidance](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces)
  explains why a permission change on an inheritable parent can affect descendants;
  this implementation performs no such repair.
- Create the branch with compare-and-create `update-ref`, use
  `worktree add --no-checkout`, and initialize only the new worktree's base index
  with `read-tree`. Raw blob reads and the existing isolated Git runner avoid
  checkout/filter/hook execution. Preserve origin bytes, HEAD/index/config,
  protected controls and source authentication across publication. Base
  `.gitignore` stays protected; ignored restored files are reported for review.
  Restored differences stay unstaged and uncommitted.
- On ordinary failure, compare full native worktree/control/administration
  snapshots including exact directory write times after owned publication, source/origin observations, branch value and registration before
  Git removes an owned worktree/ref. Remove a precreated empty root only when its
  exact identity, policy and absence of registration remain proven. Changed
  indices, refs, controls, user edits or sharing failures retain uncertainty.
  Reconstruction cleanup uses checked native descendant deletion after a
  complete exact snapshot; incomplete/edited reconstruction stays retained.
- Completed common Windows transaction workspaces remain retained under #27's
  existing policy. Newly observed failed transaction directories/ownership are
  reported for inspection, without granting cleanup authority. No rollback
  pruning or broad recursive deletion is added.

The private candidate deliberately has a narrow envelope: explicitly protected
owner-only origin and Git administration roots, exact owner-only explicit or
inherited Git descendants, eligible local NTFS, supported attributes/no named
streams, and existing per-file bounds. Read-only regular administration files
are observed without repair; payloads/directories keep the original attribute
envelope. Each audited Git tree includes its root
in the 256-entry/32-depth bound. Ordinary permissive repositories, larger Git
administration trees, unsupported descriptors or uncertain sharing are refused.
This is a candidate limitation, not a general Windows repository support claim.
Linked/external administration also needs independently eligible protected roots.

## Git interruption and cleanup limits

The [Git worktree contract](https://git-scm.com/docs/git-worktree) is still managed
through trusted Git plumbing. There is no new Git ownership journal, recovery
command, automatic commit/push/merge or whole-repository recovery guarantee.
Abrupt death may retain the new branch, an empty private root, partial worktree
registration, reconstruction or a private common transaction before handoff.
Retain and manually inspect these artifacts before retrying. Common transaction
recovery does not prove or automatically repair Git side effects.

Ordinary `git worktree remove --force` can itself fail or partially remove known
owned content when sharing changes. The original vault and independently private
evidence remain available; cleanup does not claim an intact review worktree after
such failure. A failed remove never proceeds to branch deletion. Namespace
guards are released for proven Git removal, followed by Git's checked ref deletion.
Malicious same-user writers and privileged actors remain outside the privacy
guarantee; no universal OS/power-loss durability is claimed.

## Tests and evidence classes

`tests/unit/test_windows_git_restore.py` separates exact ACL parser/refusal cases
from real local POSIX Git with injected Windows filesystem/descriptor responses.
Those injected cases test orchestration, byte/index preservation, safe cleanup,
edited artifacts, previews and late collisions. They are supplementary evidence,
never Win32 identity/DACL/sharing proof. Their fixture skips narrowly on Windows.

`tests/integration/test_windows_git_restore.py` supplies mandatory eligible native
fixtures, with no skips on Windows. Cases require actual Git for Windows,
unelevated native APIs and synthetic data only. They cover spaced paths, binary
bytes, settings preservation, executable base index modes, ignored files, existing
and late branch/output collisions, ordinary failures, user edits, unsafe admin
DACL refusal, hooks/filters/ambient selectors, real proposal/cleanup sharing
denial and inherited-control kernel denial with a matching restricted-token
positive control. No parent ACL is changed for that kernel test, avoiding
propagation into the inherited private leaf.

Five child cases terminate and wait for the actual Python worker at branch,
private-root, worktree-add, index-ready and published boundaries. Boundary
selection and ordinary fault exceptions are injected; filesystem/Git operations,
native sharing and worker death are real when executed. Death asserts retention
and manual inspection, not new Git recovery. Raw reports must stay private.

The mandatory real filesystem owner-transition test, production owner/DACL
validators, POSIX backend, CLI write/recovery gates, existing-log append refusal,
Fernet/v1 format and dependency/lock files remain unchanged. No accounts,
privileges, real vaults/keys or machine policy changes are used.

## Historical evidence and remaining gates

Preserve these exact earlier results; do not recompute a passing full-suite total
from the separate retry5 subset:

| Earlier invocation | Recorded result |
| --- | --- |
| #26 r3 owner supplements | 3 passed; injected owner supplement remains supplementary |
| #26 r3 full diagnostic | 907 passed / 1 failed / 596 skipped, exit 1 |
| #27 retry4 selected | 166 passed / 5 failed, exit 1 |
| #27 retry4 full diagnostic | 1027 passed / 5 failed / 596 skipped, exit 1 |
| #27 retry5 targeted metadata | 6 passed, no failures/errors/skips; 6 JUnit warnings |

Retry4 confirms replacement restore. Retry5 independently passes all six
corrected metadata interruption cases, including actual before-correction drift
with refusal/preservation; proposal-return cases observed no drift. Retry5's test
hash matches the checkout; host/interpreter probes and full-source evidence are
earlier retry4 evidence, not newly measured in that subset. The recorded host was
Windows 11 Home build 26200, unelevated Store CPython 3.13.14/AMD64/64-bit with
Git 2.55.0.windows.5. Historical failed totals and injected/fixture qualifications
remain visible in the predecessor documents.

The **12 October 2026 limited ownership-proof deferral remains mandatory #29
qualification**. Its unavailable `assignable_owner_group_available=False`
fixture is unchanged, not hidden with deselection, skip, xfail or injection.
Actual owner transition, positive setup, production refusal and unchanged full
native identity, bytes and exact protected DACL remain required before Windows
write enabling or qualified support. This supersedes #28's earlier enabling item.

The first actual #28 native/helper execution is recorded below; it failed and
does not validate the correction. Other Windows hosts/interpreters,
exact-commit nine-job hosted CI, exchanged synthetic v1
artifacts and installed wheel/sdist Windows write qualification remain unexecuted.
Native #28 failures/repairs belong to this thread before its acceptance; #29
implementation has not started. Native fixture absence is a failure, never a
qualification pass. Do not repeat the unchanged known owner fixture merely to
seek a passing total.

## Actual local validation — 13 October 2026

Executed on macOS ARM64 CPython 3.12.7 / Poetry 2.4.2:

- Full synthetic offline suite with permitted localhost TLS fixtures:
  **1538 passed / 148 platform skips**, exit 0. This includes existing isolated
  packaging tests using available development dependencies.
- The earlier sandboxed full attempt returned **1522 passed / 146 skipped /
  14 localhost TLS fixture setup errors**, exit 1. It predates the final added
  native kernel-denial case and is not relabeled as passing.
- Final dedicated #28 selection: **28 passed / 30 native Windows skips**, exit 0.
  The passing cases include injected lifecycle checks and exact ACL parser/refusals.
- Earlier scoped Git/POSIX/common-model selection: **162 passed / 25 native
  skips**, exit 0. The native module gained four further cases afterward; this
  earlier result is not presented as a run of those added cases.
- Strict Poetry lock, Ruff lint/format and Bandit passed, with no security findings.
  Fresh wheel/sdist, strict Twine and three installed-candidate packaging checks
  passed using available development dependencies, without downloaded-wheelhouse
  or native installed-write qualification. Strict fresh Sphinx and local rendered
  references passed across 39 HTML pages; external URLs were not checked by that
  reference script. Scope/privacy/AST/header/LF checks and the empty index passed.
  Python headers use the repository's maintainer-confirmed GPT-6.1 Sol identifier
  and 13 Oct 2026. POSIX publication, production gates, owner/DACL validators,
  real-owner assertions and dependency/lock files retain their original behavior.

This initial local handoff predates the supplied Windows reports below.
Actual native Windows/Git/PowerShell execution and hosted CI were unexecuted here.
Local success does not clear the deferred owner proof or native Git proof. All
changes were unstaged/uncommitted on the requested branch; no push, PR, merge,
issue closure or publication occurred.

## Supplied native run and administration correction — 13 October 2026

The maintainer supplied private reports for local continuation
`04633b775218f50064b5323cd7a4bd54cf4e6d18`. All **42 source SHA-256 entries**
match that checkout, including the helper, production modules, native fixtures,
dependencies and lifecycle test. Archive SHA-256:
`df2f10e2e94fc4592086404c99337a651f4c9846dfced10078f62f8bab2817cb`.
Raw reports, hostname and identifying paths remain private.

The new helper/probes measured Windows 11 Home build 26200, Git
2.55.0.windows.5 and unelevated Store CPython 3.13.14/AMD64/64-bit. Direct and
Poetry interpreter metadata agree. The helper ran natively; this establishes
execution of its reporting path, not successful qualification or independent
PowerShell parser/static validation. The archive does not report Poetry or
PowerShell versions.

| Invocation | Passed | Failed | Skipped | Errors | Exit |
| --- | --- | --- | --- | --- | --- |
| Scoped #28 plus mandatory real-owner fixture | 17 | 26 | 16 | 0 | 1 |
| Full diagnostic | 1048 | 26 | 612 | 0 | 1 |

The scoped passes comprise 12 portable ACL-policy cases and five actual native
cases: existing branch, branch-parent and output collisions; unsafe administration
DACL refusal without repair; preview and production CLI refusal. Sixteen POSIX
Git cases with injected Windows I/O skip on this Windows host. The full diagnostic
has the same 26 failing test names and includes **61 passing native #27 lifecycle
cases**. These are new results, not replacements for retry4's failed totals or
retry5's separate six-case pass.

Twenty native #28 cases stop at `Unsupported Windows Git attributes refused`
during the initial administration audit, before reconstruction/ref/worktree side
effects. Five child cases return no readiness marker, so no selected worker death
was exercised. Their reports omit the child error; the same early audit refusal
is the leading explanation, not independently proven child evidence. The remaining
failure is the unchanged real-owner fixture with
`assignable_owner_group_available=False`, still mandatory #29 qualification.

The matching [Git object writer](https://github.com/git-for-windows/git/blob/v2.55.0.windows.5/object-file.c#L613)
creates loose objects with mode `0444`, and its
[Windows implementation](https://github.com/git-for-windows/git/blob/v2.55.0.windows.5/compat/mingw.c#L918)
uses the [Windows C runtime permission mode](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/open-wopen?view=msvc-170).
Read-only loose objects are the leading cause;
the original reports do not contain a rejected numeric mask or object name.

The follow-up permits the read-only attribute **only for regular files during
audited Git administration observation**. No attribute is cleared or normalized:
the exact bit remains part of identity/content/security/metadata snapshots and
cleanup comparisons. Directories, origin/restored payloads, other unsupported
attributes, streams, types, owner/DACL checks and production baseline validators
keep their prior refusal. Git alone manages any administration removal; there is
no new attribute repair, payload write capability or cleanup fallback.

Added six portable injected observation regressions for exact read-only capture,
unchanged production refusal, other unsupported attributes and attribute changes
during reads. Added one mandatory real Git-created read-only-object regression
checking exact retained attributes and both payload refusals, plus numeric object
attribute-mask properties in the native fixture. Worker failures now report
sanitized native safety messages or exception types instead of an empty readiness
marker. These additions are diagnostics/tests, not native success evidence.

The revised candidate needs a **fresh native helper run**, preserving the above
failed reports. Use a new directory such as `obfuscidian-28-reports-313-retry1`
with either invocation below. Keep all scoped #28 cases and the unchanged owner
fixture selected. The known owner gap may still fail the scoped/full commands;
each #28 failure must be repaired or explicitly resolved before acceptance.
No #29 work or production write enabling is authorized by this correction.

The maintainer's continuation commit is the starting point for these repairs;
new edits remain unstaged/uncommitted on the same requested branch. The agent
performed no Git history, remote delivery, issue closure or publication action.

New macOS ARM64 CPython 3.12.7 / Poetry 2.4.2 validation of the correction:
**1544 passed / 149 platform skips** in the full synthetic suite, exit 0,
including permitted localhost TLS fixtures; dedicated #28 selection
**34 passed / 31 native skips**, exit 0. Six new passing tests inject native
observations, while the new actual read-only-object regression is skipped here.
Strict Poetry lock, Ruff lint/format (123 files), Bandit (no findings), strict
fresh Sphinx and local reference checks across 39 HTML pages passed. External
URLs were not requested by the reference checker. Full regression includes the
existing isolated packaging checks using available development dependencies;
no new installed Windows write qualification or hosted CI was executed.
Diff/privacy/header/LF, empty-index and production/POSIX/real-owner/dependency
preservation checks passed; existing constants retain their values. Nine files
are modified, all unstaged/uncommitted at `04633b7`; no reset or branch change.

## Exact native validation procedure

Use a reviewed source snapshot containing the new uncommitted files, or the
maintainer's separately authorized local continuation commit. On an existing
unelevated Windows host, keep the checkout and disposable test storage on
eligible local NTFS. No push or machine policy change is needed. From repository
root, use the installed Store alias or explicit executable:

```powershell
& .\.github\scripts\check_windows_git_restore.ps1 -Python python -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-28-reports-313"
```

Where existing `.ps1` execution is disabled, use the reviewed source-text method:

```powershell
$gitScriptPath = (Resolve-Path '.\.github\scripts\check_windows_git_restore.ps1').Path
$gitScriptDirectory = Split-Path -Parent $gitScriptPath
$gitSource = Get-Content -LiteralPath $gitScriptPath -Raw
$gitBlock = [ScriptBlock]::Create($gitSource.Replace('$PSScriptRoot', '$gitScriptDirectory'))
& $gitBlock -Python python -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-28-reports-313"
```

Choose 12 or 14 only for an available installed target, using a distinct report
directory. The helper reuses the reviewed #27 file-based interpreter probe and
locked dev-only installation pattern, validates exact direct/Poetry patch version,
AMD64/64-bit and elevation, then records OS/build/Git, source/dependency hashes,
base commit, JUnit/text reports and both exit codes outside the checkout. With
uncommitted work the base commit alone does not identify the candidate; preserve
the source hashes too. It runs scoped #28 tests **plus the unchanged real-owner
fixture**, then full diagnostic regression with that fixture still selected.
It does not dispatch hosted CI or invoke production mutation through a bypass.

The known unavailable owner fixture can still fail both invocations. Report all
other failures independently and repair/retest them; do not relabel those runs
as passing qualification. Return private reports with source identity, actual
environment, test names/counts/skips, injected observations and fixture gaps.
Poetry/documentation/package checks and native installed writes remain distinct.
All issues stay open pending their scoped review/qualification.

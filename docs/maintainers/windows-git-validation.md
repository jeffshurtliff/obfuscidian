# Private Windows Git merge restore handoff — #28

**Date:** 13 October 2026. **Target:** 2.0.0. **Status:** private implementation
handoff ready for maintainer review: retry3 passes 30 native Git cases and
retry4 separately passes the corrected kernel-denial case. No scoped repair
remains identified. The unchanged owner-fixture failure remains mandatory #29. Production Windows
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
are observed without repair, as is the hidden bit on the root regular `.git`
control; payloads/directories keep the original attribute
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

At this initial correction handoff, the candidate needed a **fresh native helper run**, preserving the above
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

## Retry1 setup evidence and fixture correction — 13 October 2026

The supplied retry1 archive identifies maintainer continuation
`849a3e2e503b27a18c924e5a6869f186d14b38da`. All **42 source SHA-256 entries**
match that checkout. Archive SHA-256:
`01c6f4324e01807e0acdf205664a011783dec2c9b92a901b78d246e8ad2325a0`.
Fresh probes again measure Windows 11 Home build 26200, Git 2.55.0.windows.5
and unelevated Store CPython 3.13.14/AMD64/64-bit, with matching direct/Poetry
metadata. Poetry/PowerShell versions remain absent. Raw reports stay private.

| Retry1 invocation | Passed | Failed | Skipped | Setup errors | Exit |
| --- | --- | --- | --- | --- | --- |
| Scoped #28 plus mandatory real-owner fixture | 18 | 1 | 16 | 31 | 1 |
| Full diagnostic | 1049 | 1 | 612 | 31 | 1 |

All **31 native #28 cases fail setup**, in the object-attribute diagnostic added
for retry1. `_io_path` provides extended spelling for Python enumeration; passing
that enumerated parent directly into `files._entry` incorrectly crosses the
native guard's ordinary-drive-path boundary. The guard correctly refuses it.
Git fixture initialization reached synthetic commits, but no #28 test body,
object-attribute-mask property, native administration correction or selected
worker termination was exercised. Retry1 provides no confirmation of the
read-only attribute hypothesis and does not resolve initial #28 failures.

The 18 scoped passes are 12 portable ACL-policy cases and six injected attribute
observation regressions. Sixteen POSIX Git/injected-I/O cases skip on Windows.
Full diagnostic again includes **61 passing native #27 lifecycle cases** and the
unchanged mandatory owner-transition failure,
`assignable_owner_group_available=False`. Setup errors, injected responses and
that #29 fixture gap remain distinct. Preserve all earlier failed totals and
retry5's separate six-case pass; none is relabeled by retry1.

The repair changes **tests only**: retain extended spelling for observational
enumeration, then rebuild each native entry from the original ordinary root and
its enumerated relative path. The portable regression injects a distinct
enumeration spelling and checks that native calls retain the complete original
spaced Windows drive root, relative object names and deduplicated numeric masks.
It is not native path/Git proof. Production code, the strict path guard,
read-only administration handling, owner/DACL validators, real-owner assertions,
CLI mutation/recovery/log-append gates, POSIX behavior, v1 format and dependencies
are byte-identical to `849a3e2`. No filesystem naming refinement, #29 work,
account/privilege/policy change or new recovery command is added.

**Next #28 gate:** execute the revised fixture and unchanged administration
correction with the existing native helper, using a fresh directory such as
`obfuscidian-28-reports-313-retry2` and preserving both supplied archives. Keep
all 31 native #28 cases and the unchanged owner fixture selected. The known
owner gap may still fail commands; every #28 setup error/failure must be resolved
with actual native evidence before acceptance. #29 owner proof, applicable
host/storage/interpreter coverage, exact-commit hosted matrix, exchanged v1 and
installed wheel/sdist write qualification remain mandatory. Both issues stay
open; no Windows support or write enabling follows from this fixture repair.

New local macOS ARM64 CPython 3.12.7 / Poetry 2.4.2 checks for this test-only
repair: full synthetic suite **1545 passed / 149 platform skips**, exit 0, with
permitted localhost TLS; dedicated #28 **35 passed / 31 native skips**, exit 0.
The added spelling regression passes using injected enumeration/native entry
responses. Ruff lint/format (123 files), strict Poetry lock, strict fresh Sphinx
and local references across 39 HTML pages passed; external URLs were not
requested. Full regression includes existing isolated packaging checks with
available development dependencies. No native Windows rerun, hosted CI or new
installed Windows write qualification ran here. Source byte preservation,
ancestry, diff/privacy/header/LF and empty-index checks passed. Seven follow-up
files are modified, all unstaged/uncommitted at `849a3e2` on the requested branch;
the maintainer's commits are preserved. No agent Git history, remote delivery,
issue closure or publication action occurred.

## Retry2 native evidence and root-control candidate — 13 October 2026

All **42 recorded source hashes** in the supplied retry2 archive match maintainer
continuation `f0395ea0382689a0fb5058a91cc81e37be8f024f`. Archive SHA-256:
`ee84f2d68923018bd6ef8b15612b21ae1269e04c95fb72762b52016288144a85`.
Fresh probes measure Windows 11 Home build 26200, Git 2.55.0.windows.5 and
unelevated Store CPython 3.13.14/AMD64/64-bit; direct/Poetry metadata agree.
Poetry/PowerShell versions remain absent. Raw reports stay private.

| Retry2 invocation | Passed | Failed | Skipped | Errors | Exit |
| --- | --- | --- | --- | --- | --- |
| Scoped #28 plus mandatory real-owner fixture | 38 | 13 | 16 | 0 | 1 |
| Full diagnostic | 1069 | 13 | 612 | 0 | 1 |

Native object masks measure **`0x00000021`**, and the mandatory read-only-object
case proves exact observation of **nine Git-created read-only objects**, plus
unchanged payload/default policy refusal. Retry1's setup correction works. Other
bounded native passes cover five collisions, early branch/private-root ordinary
cleanup, unsafe administration DACL refusal without repair, preview/production
CLI refusal and actual termination at branch-created/private-root-created.

The native #28 module reports **19 passed / 12 failed**. Seven of those reported
passes are user-edit retention cases lacking an assertion that the selected
`published` boundary executed. They can pass on an unrelated early retained
failure; they are **not accepted as actual published user-edit proof**. The
other 12 passing cases above provide bounded native evidence. Keep the original
pytest totals intact rather than silently subtracting these fixture gaps.
Scoped unit results are 19 portable/injected passes and 16 POSIX Git/model skips.
Full diagnostic again has 61 passing native #27 lifecycle cases; its failed test
names match the scoped invocation.

The 12 #28 failures cover both successful-overlay variants; index-ready/published
ordinary cleanup; reconstruction-edit retention; actual worktree/proposal sharing;
hooks/filters/ambient selectors; inherited-control kernel denial; and the three
later worker boundaries. The successful path stops before `worktree-added`,
but the outer failure previously lost its underlying context. No successful
published lifecycle, later termination, sharing or restricted-token enforcement
proof is accepted from these failures. The remaining ordinary failure is the
unchanged real-owner fixture, `assignable_owner_group_available=False`, still
mandatory #29 under the 12 October deferral.

The matching [Git Windows implementation](https://github.com/git-for-windows/git/blob/v2.55.0.windows.5/compat/mingw.c#L700)
marks a newly created `.git` file hidden under its default `dotGitOnly` policy;
see [Git configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehideDotFiles).
This is a leading explanation for the post-worktree refusal, **not a measured
rejected control mask or confirmed cause** in retry2.

The private correction permits observation of the hidden bit **only on the
top-level regular `.git` control**, preserving it exactly without clearing,
repairing or normalizing attributes. Hidden administration files, nested `.git`
files, payloads, directories and other unsupported bits retain refusal. Read-only
administration policy remains separate. Full native identity/content/metadata,
streams and exact owner/DACL checks remain in force. All production owner/DACL,
CLI mutation/recovery/log-append gates and the real-owner test are unchanged.

Added a pre-audit `worktree-created` diagnostic observation and actual control-mask
property in the successful native fixtures; this hook does not assert a successful
audit or add a worker-death/recovery guarantee. The private failure wrapper keeps
its original exception context in memory while suppressing normal presentation.
The test helper reports only code locations and fully matched numeric native/API
or Git-attribute templates. Worker failures use that filtered chain, never raw
arguments or paths. Portable regressions verify suppression/privacy and exact
root-only hidden observation/refusal.

Native ordinary failure, user-edit and sharing tests now assert that their
selected boundary actually executed. An earlier unrelated failure can no longer
qualify a published-edit/sharing case. Prior seven reported passes remain recorded
as fixture-limited evidence rather than being relabeled.

**Next #28 gate:** run the revised source with the existing helper in a fresh
`obfuscidian-28-reports-313-retry3` directory, preserving all supplied failed
archives. Inspect measured control masks and filtered failure locations; keep all
native #28 cases and the unchanged owner fixture selected. Resolve every scoped
failure and fixture gap with actual native evidence before acceptance. #29 real
owner transition/positive setup/production refusal/full preservation, applicable
host/storage/interpreter coverage, exact-commit hosted matrix, exchanged v1 and
installed wheel/sdist write qualification remain mandatory. No #29, new recovery,
append, pruning, naming refinement, dependency/format change or support claim.

New macOS ARM64 CPython 3.12.7 / Poetry 2.4.2 checks: full synthetic suite
**1552 passed / 149 platform skips**, exit 0, with permitted localhost TLS;
dedicated #28 **41 passed / 31 native skips**, exit 0; Git/diagnostic-helper
selection **59 passed / 32 skips**, exit 0. New observation/diagnostic passes
use injected responses and do not qualify native writes. Ruff lint/format
(123 files), strict Poetry lock, Bandit (no findings), strict fresh Sphinx and
local references across 39 HTML pages passed; external URLs were not requested.
Full regression includes existing isolated packaging checks using available
development dependencies. No revised native/helper execution, hosted CI,
exchanged artifacts or new installed Windows write qualification ran here.
Production/POSIX/owner/real-owner/gate/dependency byte preservation, unchanged
existing constants, private-helper scope, privacy/header/LF, diff and empty-index
checks passed. Eleven files are modified, all unstaged/uncommitted on the
requested branch at `f0395ea`; the maintainer's continuation commits remain.
No agent reset/branch change/stage/commit/push/PR/merge/closure/publication.

## Retry3 native lifecycle evidence and final fixture correction — 13 October 2026

All **42 source hashes** in the supplied retry3 archive match maintainer
continuation `e22b1c2c0caeec4db30e0fd065f9f2f43b4deb1c`. Archive SHA-256:
`719465915100b4106f1209c34413ffefdabb9390b4f86f5c6c4834e6926ce5a7`.
Fresh probes measure Windows 11 Home build 26200 / Git 2.55.0.windows.5 /
unelevated Store CPython 3.13.14 AMD64/64-bit; direct/Poetry metadata agree.
Poetry/PowerShell versions remain absent. Raw reports stay private.

| Retry3 invocation | Passed | Failed | Skipped | Errors | Exit |
| --- | --- | --- | --- | --- | --- |
| Scoped #28 plus mandatory real-owner fixture | 54 | 2 | 17 | 0 | 1 |
| Full diagnostic | 1086 | 2 | 613 | 0 | 1 |

Actual native #28 results are **30 passed / 1 failed**. The unit selection has
24 portable/injected passes and 17 POSIX Git/model skips. Full diagnostic again
has 61 native #27 lifecycle passes and the same two failed test names.

Root `.git` controls now measure **`0x00000022`** in both successful overlay
variants, confirming hidden-control handling rather than the earlier inference.
Read-only objects measure `0x21` and nine actual objects pass their regression.
Native passes cover binary/CRLF preservation, spaced paths, index modes,
ignored files/config preservation, uncommitted restored differences, origin and
protected controls, collisions, ordinary cleanup, all eight selected user edits,
real proposal/worktree sharing denial, artifact retention, hooks/filters/ambient
selectors and all five actual worker termination boundaries. Strengthened
boundary assertions pass; retry2's seven user-edit fixture gaps are resolved
by this new evidence, without relabeling their earlier results.

The remaining #28 test successfully publishes but fails its direct pre-kernel
control observation: it calls `_git_record` without `_hidden_control=True` on
the root hidden `.git` file. Restricted-token setup, denied leaf open and matching
positive-control open are **not executed** in this failed case. The test-only
repair selects the existing control policy for both before/after observations,
requires an actual inherited descriptor, and records numeric control attributes,
kernel-denial/positive-open and exact-preservation properties when reached.
The actual kernel enforcement/positive-control proof still needs a native rerun.

The other failure is the unchanged real-owner fixture,
`assignable_owner_group_available=False`. It remains mandatory #29 under the
12 October limited deferral. No ownership reassignment proof follows from the
restricted-token test. Keep earlier #26/#27/#28 failed totals and retry5's
separate six-case pass; do not calculate a new passing full total from a subset.

All application modules, production owner/DACL and CLI mutation/recovery/log
append gates, real-owner assertions, shared helper, native validation script,
POSIX behavior, public interface, v1 format and dependencies remain byte-identical
to `e22b1c2`. Only the kernel-denial test function changes within its Python module;
the other 30 native cases and repository fixture are unchanged. No #29 work,
account/privilege/policy change, new recovery, append, pruning or naming refinement.

**Next #28 gate:** a targeted native rerun of the corrected kernel test is
sufficient for this test-only repair. It does not select the unchanged owner
fixture, does not discharge its recorded failure, and must not be described as
a full-suite pass or #29 qualification. Preserve the full failed reports. Use
the targeted procedure below with fresh `obfuscidian-28-reports-313-retry4`
storage and source/host/interpreter evidence; the existing full helper remains
available for a separately chosen diagnostic rerun. #29 ownership/positive setup/
production refusal/full preservation, applicable storage/host/interpreter,
exact-commit hosted matrix, exchanged v1 and installed wheel/sdist write
qualification remain required. #17/#28 stay open pending this proof and review.

New local checks: Git/diagnostic-helper selection **59 passed / 32 platform skips**,
exit 0; Ruff lint/format (123 files) pass. Native kernel execution is skipped on
macOS. The earlier full local **1552 passed / 149 skips** belongs to the preceding
candidate, not a new full run of this test-only correction.
Strict Poetry lock, strict fresh Sphinx/local references (39 HTML pages; external
URLs not requested), AST/function and application/real-owner/helper/dependency
byte preservation, diff/privacy/header/LF and empty-index checks pass. No new
full runtime suite, native PowerShell/kernel run, hosted CI, exchanged artifacts
or installed Windows write qualification executed here. Six files are modified,
all unstaged/uncommitted at `e22b1c2` on the requested branch; maintainer commits
remain preserved. No agent reset/branch change/stage/commit/push/PR/merge/closure/
publication occurred.

## Retry4 targeted kernel proof and scoped #28 handoff — 13 October 2026

All **42 source hashes** in the supplied targeted archive match maintainer
continuation `395454bf37c41e8b6a8ab976ade0da292f1b092c`. Archive SHA-256:
`7ed5c87617921269d66aec14835991b1b03e5bb27065b1d1b99e856f45e38d77`.
The targeted procedure freshly records Windows 11 Home build 26200, Git
2.55.0.windows.5, Poetry **2.5.1**, PowerShell **5.1.26100.9444** and unelevated
Store CPython **3.13.14 / AMD64 / 64-bit**. Direct/Poetry interpreter probes
agree. Raw reports, identifying paths and hostnames remain private.

The corrected kernel-denial case reports **1 passed / 0 failures / 0 errors /
0 skips**, exit **0**, in **23.339 seconds**. It records:

- Actual Git object attributes `0x00000021` and inherited root `.git` attributes
  `0x00000022`, with an actual inherited descriptor required by the assertion.
- `restricted_git_control_denied=True`: a native relative leaf open beneath
  the pre-opened root refuses the inherited private `.git` control with the
  expected access-denied status. Parent traverse denial cannot substitute for
  the leaf proof because the matching positive control must open.
- `restricted_positive_control_opened=True`: the same restricted token/rights
  opens and reads the deliberately permissive synthetic leaf. No parent ACL
  repair/propagation is performed.
- `inherited_git_control_preserved_exactly=True`: the complete before/after
  control record, including full native identity, bytes/digest, creation/write
  times, exact attributes and exact owner/DACL, remains equal after reversion.

All application modules, shared helper, native full-validation script, real-owner
test and dependency files are byte-identical to retry3's `e22b1c2`. AST comparison
confirms only the corrected kernel test function differs; the repository fixture
and other **30 passing native cases are unchanged**. Reviewed #26 continuation
`2316457` and #27 through `cbd30bb` remain ancestors; the lifecycle-test hash still
matches retry5's `2e7cebd7e5d70c937373afef0af714132e673817094e32041279966156466797`.

The private #28 implementation and bounded native handoff are **ready for
maintainer review**. All 31 native cases have passing scoped evidence across
retry3 and the separate retry4 subset on this recorded eligible host. This is
not a single 31-case invocation or a passing full-suite/matrix claim. The
previously remaining kernel fixture is resolved; no additional scoped #28 repair
is identified. Source/authentication, protected plaintext/Git controls, bytes,
uncommitted differences, collisions, conservative cleanup, sharing/user edits,
retained artifacts and five worker-death limits remain covered as described above.

Preserve retry3 **54 passed / 2 failed / 17 skipped** scoped and **1086 passed /
2 failed / 613 skipped** full, both exit 1, plus all earlier failed totals.
Retry4 contains **no full diagnostic** and **does not select the real-owner
fixture**. Its previous `assignable_owner_group_available=False` failure is
unchanged and remains mandatory #29 under the 12 October limited deferral.
Restricted-token/kernel proof does not prove filesystem ownership transition.
Do not recompute a new full total from the separate successful subset.

**Remaining boundary:** maintainer review/acceptance of this scoped #28 handoff.
The separately authorized successor would be #29; it has not started. Actual
filesystem owner transition with positive setup, production refusal and unchanged
full native identity/bytes/exact protected DACL; applicable storage/host/interpreter
coverage; exact-commit nine-job hosted CI; exchanged synthetic v1 artifacts;
installed wheel/sdist Windows write qualification and final support documentation
remain mandatory before enabling writes or claiming qualified Windows support.
All production CLI mutation/recovery/log-append gates and owner/DACL validators
remain unchanged. No public bypass/API, new recovery, append, pruning, naming
refinement, account/privilege activation/policy change or format/dependency change.

This review changes documentation/changelog only. New strict fresh Sphinx/local
reference, consistency/privacy/scope, diff and empty-index checks are recorded
with the handoff. No new local runtime tests, hosted CI, artifact exchange or
installed Windows writes were run during this review. Earlier local full
1552 passed/149 skipped and Git/diagnostic 59 passed/32 skipped remain earlier
evidence. Five documents remain unstaged/uncommitted at `395454b` on the requested
branch; maintainer commits preserved. No agent reset/branch change/stage/commit/
push/PR/merge/issue closure/publication. #17/#28 remain open pending review and
qualification, with no production Windows write enabling.

## Exact native validation procedure

### Targeted remaining kernel proof after retry3

This procedure produced the successful retry4 proof above. No repeat of the
unchanged corrected case is required for the resolved fixture; preserve these
commands as the reviewed historical procedure, using fresh storage for any
separately chosen rerun.

From the revised repository root on the existing unelevated Windows host, using
the same installed 3.13 environment, run this source text in PowerShell. It
changes no execution policy, accounts or privileges. Fresh output stays outside
the checkout. This procedure is source-reviewed here; actual Windows execution
of the corrected case remains pending. Return the directory as a private archive.

```powershell
$KernelRepository = (Resolve-Path '.').Path
$KernelReports = [IO.Path]::GetFullPath((Join-Path $env:TEMP 'obfuscidian-28-reports-313-retry4'))
if (Test-Path -LiteralPath $KernelReports) { throw 'Preserve earlier reports; use a fresh directory.' }
if ($KernelReports.StartsWith($KernelRepository + [IO.Path]::DirectorySeparatorChar,
                              [StringComparison]::OrdinalIgnoreCase) -or $KernelReports -eq $KernelRepository) {
    throw 'Keep raw reports outside the checkout.'
}
New-Item -ItemType Directory -Path $KernelReports | Out-Null
$KernelProbe = @'
import ctypes, json, platform, struct, sys
assert sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 13)
assert platform.machine().upper() == 'AMD64' and struct.calcsize('P') == 8
assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Use an existing unelevated token'
print(json.dumps({'implementation': platform.python_implementation(), 'version': platform.python_version(),
                 'architecture': platform.machine(), 'bits': struct.calcsize('P') * 8,
                 'store_package_path_detected': 'PythonSoftwareFoundation.Python.' in sys.executable,
                 'elevated': False}))
'@
$KernelProbePath = Join-Path $KernelReports 'interpreter-probe.py'
$KernelProbe | Set-Content -Encoding UTF8 -LiteralPath $KernelProbePath
$KernelDirectProbe = @(& python $KernelProbePath)
if ($LASTEXITCODE -ne 0 -or $KernelDirectProbe.Count -ne 1) { throw 'Direct interpreter/token probe failed.' }
$KernelDirectProbe | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'selected-interpreter.json')
$KernelPoetryProbe = @(& poetry run python $KernelProbePath)
if ($LASTEXITCODE -ne 0 -or $KernelPoetryProbe.Count -ne 1) { throw 'Poetry interpreter/token probe failed.' }
$KernelPoetryProbe | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'poetry-interpreter.json')
$KernelDirect = Get-Content -Raw (Join-Path $KernelReports 'selected-interpreter.json') | ConvertFrom-Json
$KernelPoetry = Get-Content -Raw (Join-Path $KernelReports 'poetry-interpreter.json') | ConvertFrom-Json
if ($KernelDirect.version -ne $KernelPoetry.version) { throw 'Direct and Poetry interpreters differ.' }
$KernelOS = Get-CimInstance Win32_OperatingSystem
@{ os = $KernelOS.Caption; build = $KernelOS.BuildNumber; git = (& git --version);
   powershell = $PSVersionTable.PSVersion.ToString(); poetry = ((& poetry --version) -join ' ') } |
    ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'host-summary.json')
$KernelSources = @(Get-ChildItem 'src/obfuscidian' -Filter '*.py' -File)
$KernelSources += Get-ChildItem 'tests/unit' -Filter 'test_windows*.py' -File
$KernelSources += Get-ChildItem 'tests/integration' -Filter 'test_windows*.py' -File
$KernelSources += Get-Item 'tests/_windows_support.py', 'tests/integration/test_merge_restore.py', `
    'tests/integration/test_packaging.py', 'tests/conftest.py', 'pyproject.toml', 'poetry.lock', `
    '.github/scripts/check_windows_git_restore.ps1'
$KernelSources | Sort-Object FullName | ForEach-Object {
    $KernelRelative = $_.FullName.Substring($KernelRepository.Length + 1).Replace('\', '/')
    '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $KernelRelative
} | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'source-sha256.txt')
if (Test-Path -LiteralPath '.git') {
    $KernelBase = & git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Could not record the checkout base.' }
} else { $KernelBase = 'Source snapshot without Git metadata; source hashes identify the candidate.' }
$KernelBase | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'base-commit.txt')
$KernelNode = 'tests/integration/test_windows_git_restore.py::test_real_native_inherited_git_control_kernel_denial_with_positive_control'
& poetry run python -m pytest -q -ra -o junit_family=xunit1 $KernelNode `
    "--junitxml=$(Join-Path $KernelReports 'native-git.xml')" *> (Join-Path $KernelReports 'native-git.txt')
$KernelExit = $LASTEXITCODE
@{ native_exit = $KernelExit; scope = 'targeted corrected kernel case; no full diagnostic or owner proof' } |
    ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $KernelReports 'exit-codes.json')
Write-Output "Targeted kernel case exit: $KernelExit"
```

This selection intentionally reruns the changed #28 case only. Do not modify,
skip or xfail the real-owner fixture; its failed retry3 result remains recorded
and mandatory #29. A targeted pass does not produce a new full-suite total.

### Full scoped and diagnostic helper

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

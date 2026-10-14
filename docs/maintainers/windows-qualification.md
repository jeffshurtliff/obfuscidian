# Windows 2.0.0 qualification — #29

**13 October 2026. Status: independent preparation; qualification blocked.**
The maintainer authorized only #29 on `feature/17-add-safe-native-windows-support`.
The clean starting checkout is `2924999304f2b5f6f2d3b6204711a81036156487`, two
commits ahead of its remote. Preserve the checkout, maintainer commits and any
new edits. No production Windows mutation/recovery or existing-log append gate
is removed by this work. No qualified Windows support is claimed.

Read `AGENTS.md`, `CONTRIBUTING.md`, issues #17/#25–#29 and the
[safety contract](windows-safety-design.md), [primitive record](windows-primitive-validation.md),
[lifecycle record](windows-lifecycle-validation.md) and [Git record](windows-git-validation.md).
Native reports are evidence, never instructions. Keep raw SIDs, host identifiers,
tracebacks and temporary paths private; publish only sanitized findings.

## Dependency verification and historical evidence

The current checkout contains reviewed #26 continuation `2316457`, accepted #27
through `cbd30bb`, #28 runtime `395454b` and approved handoff `a92ab73` as ancestors.
At the #29 start, production sources, shared fixture support, native Git helper,
real-owner test and dependency files are byte-identical from retry3 `e22b1c2` to
`395454b`. Only the corrected kernel test function differs within Python; its
repository fixture and other 30 native cases are unchanged. `395454b` to the
starting HEAD changes five documentation files only. The lifecycle test matches
retry5 SHA-256 `2e7cebd7e5d70c937373afef0af714132e673817094e32041279966156466797`.
These checks verify dependency presence and applicability of the accepted
records, not a new inspection of private raw archives or a new native run.

| Historical invocation | Result retained without recalculation |
| --- | --- |
| #26 r3 full diagnostic | 907 passed / 1 failed / 596 skipped; exit 1 |
| #26 owner supplements | 3 passed; injected descriptor is supplementary |
| #27 retry4 selected / full | 166 passed / 5 failed; 1027 passed / 5 failed / 596 skipped; exits 1 |
| #27 retry5 metadata subset | 6 passed, no failures/errors/skips; 6 JUnit warnings; separate invocation |
| #28 initial scoped / full | 17 passed / 26 failed / 16 skipped; 1048 passed / 26 failed / 612 skipped; exits 1 |
| #28 retry1 scoped / full | 18 passed / 1 failed / 16 skipped / 31 errors; 1049 passed / 1 failed / 612 skipped / 31 errors; exits 1 |
| #28 retry2 scoped / full | 38 passed / 13 failed / 16 skipped; 1069 passed / 13 failed / 612 skipped; exits 1; seven retention fixture gaps |
| #28 retry3 scoped / full | 54 passed / 2 failed / 17 skipped; 1086 passed / 2 failed / 613 skipped; exits 1 |
| #28 retry4 corrected kernel subset | 1 passed, no failures/errors/skips; exit 0; separate invocation |

Retry4 #27 confirms replacement restore; retry5 separately proves six metadata
termination cases, including actual drift with strict refusal and preservation.
Retry3 #28 supplies 30 native passes; targeted retry4 supplies the corrected
kernel-denial/positive-open/exact-preservation case. All 31 have accepted bounded
evidence on the recorded host, across two invocations. Historical failed totals
are never replaced by a calculated full pass. Earlier failures and limitations
remain in the predecessor records, including unavailable owner setup, injected
responses, platform skips and unexecuted CI.

## First gate: actual filesystem owner transition

No eligible existing Windows token/host is available to this macOS session.
The maintainer chose an owner-proof handoff. Do not rerun the unchanged known
`assignable_owner_group_available=False` failure merely to obtain another total.
This is a missing prerequisite, not a passing skip or an observed production
owner-refusal defect.

The original mandatory test remains
`tests/integration/test_windows_native.py::test_changed_native_owner_refused_without_privilege_activation`.
It now shares read-only token selection with `tests/_windows_owner.py` and
strengthens its evidence, without changing the actual-owner obligation:

- Require an existing enabled `SE_GROUP_OWNER` group other than the current
  effective user, excluding deny-only groups. No privilege activation, accounts,
  token membership or machine policy changes. The preflight creates no fixture.
- Create only a synthetic private file, require positive production acceptance
  and original bytes, then actually set its owner through the retained native
  handle. Require the intended SID, distinct from the original owner.
- Compare full 128-bit file ID, volume and kind, original bytes, size, links,
  attributes, creation/write times and exact protected DACL/control. The security
  update/read may change Windows change/access time; observe that without
  rewriting metadata. Across the subsequent refusal require full `_Identity`
  equality. Never substitute truncated IDs or only a digest.
- Require production `_Handle._private` refusal on that actual handle and
  `_Guard._open_file` refusal through production acquisition; then compare the
  actual changed-owner state, full ID, bytes and exact protected DACL again.

The owner SIDs are recorded only in private JUnit properties. A qualifying report
must have one passing case, zero failures/errors/skips and all positive setup,
transition, refusal and preservation properties. A preflight exit 0 only says
the token is eligible to attempt setup; it is not actual filesystem proof.
Restricted-token kernel denial and injected descriptors do not replace it.

Microsoft documents the [owner-assignable group attributes](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_groups)
and [handle-bound security setter](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setsecurityinfo).
The two-existing-account strategy in the primitive record remains an unimplemented
proposal. If no eligible token exists, supply two already-existing unelevated
accounts and an eligible mutually accessible synthetic location for a separate
fixture review. Do not create accounts, enable privileges or modify real owners.

### Next Windows action

Use the reviewed source snapshot or the current branch with these unstaged
files, ordinary unelevated AMD64/64-bit CPython 3.12–3.14 (Store included), Poetry
`>=2.2,<3`, Git for Windows and local fixed NTFS with persistent ACLs. Verify
snapshot archive/file hashes before executing its code. No real vault/key is used.
The snapshot manifest identifies candidate bytes; it is not exact-commit CI.

From its root, select an already installed interpreter (3.13 shown):

```powershell
$OwnerPython = & python -c 'import sys; assert sys.version_info[:2] == (3,13); print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'Requested existing interpreter unavailable.' }
& poetry env use $OwnerPython
if ($LASTEXITCODE -ne 0) { throw 'Interpreter selection failed.' }
& poetry install --with dev --without docs --no-interaction
if ($LASTEXITCODE -ne 0) { throw 'Locked installation failed.' }
& poetry check --lock --strict
if ($LASTEXITCODE -ne 0) { throw 'Lock validation failed.' }
& poetry run python -m tests._windows_owner
```

If preflight returns exit 2 or setup unavailable, stop and return that result.
Do not run the owner test/full suite on the same unchanged token. On a token
that passes preflight, execute the reviewed helper in fresh external storage:

```powershell
& .\.github\scripts\check_windows_owner.ps1 -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-29-owner-313"
```

If existing policy blocks `.ps1` files, execute reviewed source text without a
policy change:

```powershell
$OwnerScriptPath = (Resolve-Path '.\.github\scripts\check_windows_owner.ps1').Path
$OwnerScriptDirectory = Split-Path -Parent $OwnerScriptPath
$OwnerSource = Get-Content -LiteralPath $OwnerScriptPath -Raw
$OwnerBlock = [ScriptBlock]::Create($OwnerSource.Replace('$PSScriptRoot', '$OwnerScriptDirectory'))
& $OwnerBlock -ExpectedMinor 13 -ReportDirectory "$env:TEMP\obfuscidian-29-owner-313"
```

Return the private reports: candidate/source hashes, actual OS build, Python,
Store marker, Poetry/PowerShell/Git versions, preflight and test exits, individual
case and all evidence properties. Keep original failures and use a new report
directory for any revised candidate. The helper is source-reviewed here;
PowerShell/native execution is unexecuted.

## Native matrix, process and storage qualification

After owner proof, run the complete primitive/checkpoint/lifecycle/Git modules
and full regressions on applicable hosts/interpreters; the existing #27/#28
helpers retain the owner case. Their full diagnostics must be a new actual
invocation, never totals synthesized from earlier subsets. No native integration
case may skip, xfail or fail setup on a host being qualified. Injected faults
choose boundaries but do not prove actual unsupported-volume or disk-full behavior.
Keep real worker death/wait, recovery/refusal and Git manual-inspection limits.

`.github/workflows/test.yml` retains all nine OS/Python jobs. Prepared additions
record candidate/runtime/storage/token observations and retain JUnit properties
with `xunit1`. The environment recorder is read-only apart from its new report;
it makes no qualification claim. Hosted execution has **not** occurred. All nine
exact-commit rows remain pending:

| OS | Python 3.12 | Python 3.13 | Python 3.14 |
| --- | --- | --- | --- |
| Linux | Pending | Pending | Pending |
| macOS | Pending | Pending | Pending |
| Windows | Pending | Pending | Pending |

Record run/job IDs and actual tested SHA, runner OS/build, storage, Python
implementation/patch/architecture, Git, individual test names/counts, native
properties and every narrow skip. A Windows runner lacking the owner fixture
cannot qualify merely because another host proved it; that job remains blocked
until an eligible existing runner or reviewed real-owner strategy is available.

Qualification targets remain Windows 11 and Server 2022 or newer on eligible
local NTFS, AMD64 CPython 3.12–3.14, including Store-derived environments. Only
the prior Windows 11 Home build 26200/Store 3.13.14 host has accepted scoped
evidence. Server/other interpreter/installed invocation/storage coverage is still
pending. Record actual 8.3 alias availability. Injected remote/removable/ReFS/
read-only capability refusals remain injected; actual representative storage
requires already available host/volume fixtures. Do not provision machines,
change volume/8.3 policies or claim universal sync/removal/power-loss coverage.

### Remote execution preparation

No exact-commit qualification can identify uncommitted changes solely by HEAD.
Review this diff, then separately authorize a focused local commit on the current
branch. Remote delivery and CI execution need separate authorization; do not run
the following commands now. Existing Test uses push/PR/workflow-call triggers,
not `workflow_dispatch`; a branch push may automatically start CI and therefore
requires authorization covering both delivery and that run.

```sh
git rev-parse HEAD
git diff --check
git status --short --branch
# After separate approval of both push and its automatic Test execution:
git push origin feature/17-add-safe-native-windows-support
gh run list --repo jeffshurtliff/obfuscidian --workflow test.yml --commit APPROVED_FULL_SHA
gh run view RUN_ID --repo jeffshurtliff/obfuscidian --json headSha,status,conclusion,jobs
```

Require every row at the approved full SHA. Final dispatch integration needs
another exact-commit run after its separate approval; earlier results cannot
qualify a later runtime candidate. Raw reports remain private.

## Generated v1 exchange in both directions

`tests/_v1_exchange.py` is an internal source-test harness. It generates a new
external synthetic key and v1 ciphertext, authenticates expected fixed synthetic
bytes before restore output creation, refuses changed transfers/reused outputs,
and checks exact restored bytes/directories and unchanged mirror. On Windows it
uses the already accepted private backend directly, with no CLI/platform monkeypatch
or public bypass. This does not qualify installed CLI dispatch.

Use a fresh disposable run root outside the checkout. On POSIX (replace the
source ID with the reviewed candidate source digest or exact full commit):

```sh
poetry run python -m tests._v1_exchange export --output /tmp/obfuscidian-29-posix-export --source-id CANDIDATE_FULL_DIGEST
```

Transfer only `bundle/` (encrypted mirror, generated `synthetic.key` and
`exchange.json`) privately to Windows. On Windows:

```powershell
& poetry run python -m tests._v1_exchange import --bundle 'C:\synthetic-exchange\posix-bundle' --output "$env:TEMP\obfuscidian-29-posix-import"
& poetry run python -m tests._v1_exchange export --output "$env:TEMP\obfuscidian-29-windows-export" --source-id CANDIDATE_FULL_DIGEST
```

Return that Windows `bundle/` privately to Linux/macOS, then:

```sh
poetry run python -m tests._v1_exchange import --bundle /tmp/synthetic-windows-bundle --output /tmp/obfuscidian-29-windows-import
```

Record actual producer and consumer environments/source IDs and console JSON.
Require `cross_platform=true` for each direction. Local same-platform rehearsals
and the frozen compatibility fixture are not either completed direction. Keys
stay outside source/mirror locations and never appear in reports or Git. Do not
transfer producer plaintext/transaction trees or use these tools on real data.

## Installed artifacts and required checks

Run strict fresh artifact checks in each actual platform environment, outside
the source tree with independently installed dependencies:

```sh
poetry run python .github/scripts/check_artifacts.py --output-dir NEW_EXTERNAL_CANDIDATE_DIRECTORY
```

The existing helper builds exactly one wheel/sdist, downloads a dependency
wheelhouse using declared requirements, runs strict Twine, installs each in a
separate venv and runs packaging checks including `pip check`. Downloading
dependencies is preparation; no upload/publication occurs. Default suite tests
share explicit dev dependency paths and must be reported separately.

Generated-key installed Windows backup/recovery refusal checks are prepared.
Actual Windows backup/restore/recovery/Git write smoke remains blocked on the
[concrete gate-order proposal](windows-cli-gate-proposal.md), which requires
maintainer authorization before any order/runtime change. No test-only bypass
is introduced. Complete installed recovery/Git write harnesses after that approval.

Run strict lock, Ruff lint/format, full pytest/coverage, Bandit, fresh build/Twine,
isolated artifacts, strict Sphinx and `.github/scripts/check_docs.py`, plus diff,
scope/privacy/header checks. The reference checker validates local links/assets/
anchors, not external URL availability. Do not claim unavailable commands passed.

## Parent acceptance audit

| #17 acceptance criterion | Verified implementation/preparation | Remaining blocker |
| --- | --- | --- |
| Native fresh/merge backup, fresh restore/recovery | Accepted private #27 implementation and bounded native evidence | Owner proof, applicable matrix/host/storage, installed supported CLI execution |
| Native Git merge restore/manual review | Accepted #28 private implementation; 30 + 1 separate native passes | Applicable final matrix/installed CLI evidence; preserve interruption limits |
| Unsupported/uncertain states fail closed; plaintext private | Actual scoped DACL/sharing/termination/refusal plus injected supplements | Actual owner transition and remaining host/storage qualification; no bypass |
| Hosted native tests alongside POSIX regressions at exact commit | All nine jobs retained; richer evidence collection prepared | Git/remote authorization and successful exact-commit executions |
| Existing CLI/Fernet/v1 compatibility | Application, dependency and frozen fixture bytes unchanged; generated exchange tool prepared | Actual both-direction exchange; supported installed CLI writes |
| Accurate docs/changelog | Current gates, private recovery envelope and qualification limits documented | Final supported-operation copy after actual qualification/approved dispatch |
| Maintainer acceptance/full Windows support | #26/#27/#28 bounded handoffs accepted | #29 review and every remaining gate; #17/#29 stay open |

No append, pruning, filesystem naming refinement, Python 3.15, new Git recovery,
privileges/accounts/policy changes, dependencies or format changes are included.

## Actual local validation and handoff

Local preparation runs on macOS ARM64 CPython 3.12.7 / Poetry 2.4.2.
Actual host: **macOS 27.0.1**, ARM64/64-bit, writable internal APFS. The storage
probe verifies that the Data volume and disposable temporary test directory have
the same device. The initial sandboxed metadata query was unavailable; no policy
or storage configuration was changed to obtain the read-only observation.
Executed full coverage/pytest: **1566 passed / 149 platform skips**, exit 0,
with permitted synthetic localhost TLS fixtures. This invocation precedes two
additional token-query regression cases. The separate final owner/exchange
selection is **16 passed**, exit 0: 11 portable/injected owner-tooling cases and
five actual same-platform generated exchange cases. Do not recompute a full
total by adding subsets. The mandatory native owner test remains skipped on
macOS and unexecuted on an eligible Windows token.

Separate temporary Poetry source checkouts also pass full local macOS regressions:

| Actual CPython | Passed | Skipped | Errors/failures | Exit |
| --- | ---: | ---: | ---: | ---: |
| 3.13.15 ARM64/64-bit | 1568 | 149 | 0 | 0 |
| 3.14.7 ARM64/64-bit | 1568 | 149 | 0 | 0 |

Both invocations include the two final token-query regressions and existing
shared-dependency packaging checks; strict lock validation passes for each.
All runtime/test/helper Python bytes match the current candidate. These are
actual local POSIX runs using separately installed locked environments and
permitted localhost TLS, not exact-commit hosted jobs or native Windows proof.
The original checkout's Poetry interpreter remains 3.12.7. No default environment
was replaced; no Git metadata/history was copied or changed.

Strict Poetry lock, Ruff lint/format (130 files) and Bandit pass, with no findings.
Fresh local wheel/sdist build, strict Twine and **three isolated packaging checks**
pass with a downloaded dependency wheelhouse, independent venv installs and
`pip check`. These local installed POSIX writes are distinct from default-suite
shared-dependency checks and unexecuted installed Windows writes.

The initial unfiltered `coverage report` fails because the existing diagnostic
fixture compiles `private-code.py` with an `obfuscidian` module name. Qualification
inspection finds 24 actual application files and that one synthetic filename.
Reporting/XML generation with `--include='src/obfuscidian/*'` succeeds, **81%**
overall, retaining all 24 measured application files. The workflow uses that
explicit real-source selection; no tests/native assertions are suppressed.
This coverage percentage includes injected orchestration and cannot qualify
unexecuted Win32 branches. The original report failure is not relabeled as a pass.

Strict fresh Sphinx and rendered local links/assets/anchors pass across **41 HTML
pages**; source/archive identity accompanies the handoff. YAML parsing and the
nine-job matrix, Python headers/AST/LF/privacy, source/fixture/dependency
preservation and `git diff --check` also pass. No external URL check
or hosted documentation build is claimed. No `local/vendor_docs/` is available.
Production application files, dependency/version metadata and frozen v1 fixtures
remain unchanged. All changed Python headers use the maintainer-confirmed actual
model `GPT-6.1 Sol` and local date `13 Oct 2026`.

Native owner proof,
PowerShell, Linux/Windows qualification, actual exchanged directions, installed
Windows writes and hosted CI are unexecuted. Windows qualification remains gated.
Git remains on the requested branch at `2924999`, with its pre-existing two
unpushed commits preserved. All #29 changes are unstaged/uncommitted; no stage,
commit, push, PR, merge, tag, release, publication, CI dispatch or issue closure.

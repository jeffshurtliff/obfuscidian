# Plan: practical AMD64 Windows qualification — #17 / #29

**16 October 2026. Selected direction: existing physical AMD64 laptop. Planning
and handoff only; Windows write support is not qualified or enabled.**

## Decision and evidence

The maintainer prioritizes broadly useful Windows support and personal encrypted
vault backups, without maintaining a custom cryptography artifact. The selected
next environment is the previously used physical Windows laptop. The maintainer
reports running this read-only command there:

```powershell
Get-CimInstance Win32_Processor | Select-Object Architecture, AddressWidth
```

Reported result: **Architecture = 9; AddressWidth = 64**. This is new
maintainer-reported platform evidence, not a fresh agent-observed Python, token,
storage or application qualification. It supersedes earlier statements that no
AMD64 machine was available. Do not repeat this unchanged CPU check merely to
restart a chat. Verify the other prerequisites in A1 below.

Earlier records identify Windows 11 Home build 26200 / Store CPython 3.13.14
AMD64 and accepted bounded lifecycle/Git results. Those are historical inputs;
current OS revision, interpreter, dependencies, storage and accounts are unknown.
The previously unavailable owner-group fixture does not establish unsuitable
hardware. A two-standard-account fixture may provide the alternative, but account
availability and any setup need review. Do not rerun the known failing group
fixture on an unchanged token.

The accepted ARM64 fix04 result remains **1 passed in 215.27s**, only for its
recorded Windows 11 Home/build 26300/fixed NTFS/native ARM64 CPython 3.13.16
combination. Preserve the VM, snapshot, reports, original approval flags and
all earlier failures. Its reviewed fixture is reusable engineering work; its
pass does not discharge AMD64 owner proof. No ARM rerun is required for this pivot.

## First usable Windows target — proposal for explicit review

The architecture choice is decided; the detailed release scope and changed
acceptance order are **not yet approved**. A2 must resolve them before execution.

| Dimension | Proposed first target |
| --- | --- |
| Environment | One measured Windows 11 x64 laptop, native 64-bit CPython 3.13, eligible local fixed NTFS; freeze exact versions after A1 |
| Supported writes | Fresh encrypted backup into an absent mirror; fresh restore into an absent destination; explicit recovery bound to those eligible operations |
| Existing behavior | Private key creation, authenticated verification and no-write planning retain their contracts |
| Deferred writes | Existing-mirror updates/replacement, merge backup, destination replacement, Git merge restore/publication and existing-log append remain refused |
| Git workflow | User manually commits/pushes the complete encrypted mirror; Obfuscidian backup performs no Git publication |
| Repeated backups | Initially use new dated snapshot destinations; assess storage/retention and repository layout before promising a convenient recurring workflow |
| Other environments | ARM64, emulation, Server and other Python/storage combinations remain unqualified until separately evidenced |

This narrower target may support an initial personal-use candidate and later
release. It does not complete the original broad #17 criteria automatically.
Retain authenticated decryption, exact bytes, private plaintext, source
preservation, conservative refusal, interruption/recovery and consent guarantees.
Reduce supported features/environments rather than skipping safety assertions.
Unsupported operations need explicit tested refusal; unexplained failures still
require triage. Preserve POSIX behavior, CLI syntax, Fernet/v1 and canonical
dependencies. No new public bypass or incidental Python 3.15 work.

For the personal-use goal, upload only the encrypted mirror. Keep plaintext and
keys outside its Git repository and keep independent key/backup copies. Object
sizes/counts/change patterns remain observable; endpoint/key compromise and
backup deletion are outside encryption's protection. See [security limits](../SECURITY.md).

## Existing issue ownership and future issues

All seven issues were read and remain open at this handoff. This planning change
does not edit their bodies/checklists, close issues, change relationships or create
new issues. The next authorized chat should post a public-safe direction update
on #17/#29 and a parked-work note on #30; preserve historical evidence below it.

| Issue | Continue using it for | Closure / follow-up policy |
| --- | --- | --- |
| [#17](https://github.com/jeffshurtliff/obfuscidian/issues/17) | Parent Windows roadmap, release-scope decision and acceptance audit | Keep open. A limited candidate does not close it; either finish broad scope later or explicitly approve rescoping and transfer every deferred requirement to linked follow-ups before closure |
| [#25](https://github.com/jeffshurtliff/obfuscidian/issues/25) | Existing safety/capability design; reference accepted deliverables | Do not redo design solely because chats changed. Scoped closure requires evidence review and maintainer authorization; qualification gaps remain in #29 |
| [#26](https://github.com/jeffshurtliff/obfuscidian/issues/26) | Existing native primitives; link any genuine primitive defect here | Preserve limited-deferral history. AMD64 owner proof is executed/tracked under #29; do not relabel ARM proof as AMD64 or restart #26 wholesale |
| [#27](https://github.com/jeffshurtliff/obfuscidian/issues/27) | Accepted private backup/restore/recovery implementation; focused defects if found | Private handoff acceptance remains distinct from installed CLI support; carry remaining qualification in #29 |
| [#28](https://github.com/jeffshurtliff/obfuscidian/issues/28) | Accepted private Git implementation and its bounded evidence | Preserve 30 + 1 separate native results and failed full totals. Public Git restore may be deferred without deleting its implementation or claiming it qualified |
| [#29](https://github.com/jeffshurtliff/obfuscidian/issues/29) | Active AMD64 readiness, owner proof, native qualification, CLI acceptance, matrix and support documentation | Reuse across A1–A8; a new chat does not require a new issue. Update current status to separate parked ARM blockers from unverified AMD64 readiness. No completed criterion from metadata alone |
| [#30](https://github.com/jeffshurtliff/obfuscidian/issues/30) | Preserved ARM64 cryptography/build provenance investigation | Park, leave open, retain metadata mismatch and 18.10.4 discovery evidence. It is not a prerequisite for the selected AMD64 route if the canonical locked wheel audit passes; do not claim it solved |

No new issue is needed for A1. After scope review, create new linked issues only
for independent defects, separately owned CI work or explicit deferred feature
acceptance—not one per chat. Create a release-tracking issue before actual 2.0.0
release preparation if none exists then. Verify live issues first; never invent
numbers or silently retarget/close #17/#29. Leave #18 rollback pruning, #19 naming
detection and unrelated features outside this plan.

## Chat-sized tasks and approval boundaries

Run tasks sequentially. Each row is a natural fresh-chat boundary, not an
authorization to execute all rows. A chat ends with its deliverable, evidence,
Git status and next eligible task. Split a row further if a defect or approval
decision makes its continuation substantial; do not continue into a later row
merely because the earlier one passed.

| Chat | Task and dependencies | Concrete output / exit check | Execution boundary |
| --- | --- | --- | --- |
| **A1 — next** | Read-only laptop readiness and canonical binary-route audit | Current environment/readiness report; exact known/unknown inputs; scope/setup decision packet; next prompt | Submitting the [saved kickoff](windows-amd64-next-chat.md) authorizes A1 only |
| **A2** | Review first-release scope, owner-account setup and validation order; consumes A1 | Reviewed operation/environment matrix, deferred requirements, exact setup/install commands, resource/permission boundaries and proposed revised #17/#29/CLI prerequisites | Proposal only until maintainer explicitly approves the concrete scope and required setup |
| **A3** | Execute only approved laptop preparation; consumes A2 decisions | Isolated native AMD64 runtime/dev environment, verified canonical binary inputs, dependency/import checks and private paths; no source fallback | Separate approval for named account creation, installations, source transfer and environment writes; none follows from A1 |
| **A4** | Prepare/review then execute real AMD64 owner proof; consumes verified A3 environment | One actual original mandatory owner case with all positive setup, transition/refusal/identity/bytes/exact-DACL evidence and fresh source manifest | Separate approval of synthetic fixture/runner/paths and execution; preserve ARM result and every failed attempt |
| **A5** | Private native qualification and Windows/POSIX exchange; consumes accepted A4 and approved scope | Applicable primitives/checkpoints/lifecycle/DACL/termination tests, full diagnostic totals, two generated exchange directions and release-scope evidence audit | Separately approved synthetic execution; no public dispatch enabling |
| **A6** | Integrate only approved Windows CLI routes and test installed artifacts; consumes A5 acceptance and explicit revised gate-order approval | Focused runtime/tests/docs diff; fresh wheel and sdist; real console/module write/recovery checks outside checkout; excluded operations refuse | Separate implementation/build/install/test approval; no test-only public bypass or automatic support claim |
| **A7** | Repeatable CI and final exact-candidate regression evidence; consumes A6 | Reviewed ordinary-user Windows test strategy plus passing required candidate checks, or precise remaining blockers | Prepare runner/workflow changes for review; remote execution, accounts/policy and Git delivery require their own explicit scope |
| **A8** | User documentation and readiness/personal-use review; consumes A7 evidence | Accurate support matrix, limitations, manual encrypted-Git workflow, synthetic rehearsal and go/no-go handoff | Real vault copies, keys, cloud upload or personal-data rehearsal require separate explicit authorization; do not start with the only copy |
| **A9** | Stable-release preparation and separately approved publication; consumes accepted A8 | Approved release scope, stable metadata/docs, final archives/checksums/installed checks, exact-commit CI and release handoff | Follow [release runbook](releasing.md); merge/tag/upload/publication/closure are separate consequential actions, not included in planning |

### A1: what to inspect, and what not to do

Read root instructions, #17/#25–#30, this plan, [qualification](windows-qualification.md),
[owner fixture](windows-owner-vm.md), [CLI gate proposal](windows-cli-gate-proposal.md),
the existing lifecycle/Git validation records, canonical `pyproject.toml` and
`poetry.lock`, and the existing runner scripts. Read the [ARM acquisition packet](windows-arm64-cryptography-acquisition-packet.md)
only to preserve its handoff and understand why that work is parked.

Use **one ordinary PowerShell command at a time**, wait for pasted output, and
assume no surviving variables/session state. Begin with fresh current-session
token/elevation facts before any guest executable probe. No credential collection,
automatic UTM/terminal typing, broad account enumeration or unrelated private-file
search. The maintainer supplies only task-relevant account availability; keep
raw identities/paths private and public summaries sanitized.

Measure current OS edition/full build, actual selected Python implementation,
version/bitness and process/native machine via `IsWow64Process2`, relevant Git/
Poetry versions, prospective fixed-NTFS test location/free space and ordinary
account/owner-fixture availability. Native AMD64 Python requires native machine
`0x8664`, process machine `0x0000`, 64-bit pointers; the CPU result alone proves
none of these interpreter/token/storage properties. Missing tools stay missing.
Existing Store Python is eligible for assessment; do not replace it by assumption.

Audit official package **metadata only** against the actual target and unchanged
lock: all applicable runtime/dev/build entries, compatible non-yanked wheels,
Python constraints and matching locked hashes. The ARM 36/37 count is not an
AMD64 audit. Published AMD64 cryptography wheels are a promising route, not a
complete environment installation. No wheel/source/crate/installer payload
downloads, package installation/imports of candidates or build-backend execution
in A1. Read-only interpreter/system metadata probes are permitted.

Return a pass/conditional/blocked readiness table with precise reasons, proposed
isolated paths and the minimum setup needed. An unavailable second account
means propose a concrete setup for review, not reject the hardware or repeat the
old group-fixture failure. Do not create accounts, change policy/privileges or
ACLs, write synthetic guest fixtures, install tools, run tests, dispatch CI or
change canonical dependencies. No ARM work resumes.

### A2–A9: important implementation and acceptance details

- A2 must settle whether this is a personal-use engineering candidate, a beta or
  the first stable 2.0.0 Windows scope. Explicitly review the former nine-job,
  broad-environment and full-operation criteria and the installed-command gate
  order. Do not reinterpret a smaller matrix as the old all-nine success. Keep
  historical failed jobs and repository required checks; any replacement must be
  approved, runnable and documented. #17/#29 stay open unless explicitly rescoped.
- A3 uses the canonical Poetry input and authenticated upstream AMD64 wheels.
  Confirm the complete target-specific closure before execution; enforce no
  implicit source-build fallback. An absent compatible wheel stops that route.
  Do not install a compiler, downgrade dependencies, hand-edit the lock or
  preinstall an untracked binary to force resolution. Preserve old environments
  and laptop source changes; source transfer must identify exact candidate bytes.
- A4 reviews `tests/_windows_owner_vm.py`, the original test node in
  `tests/integration/test_windows_native.py` and
  `.github/scripts/check_windows_owner_vm.ps1` before physical-host reuse.
  Check VM-specific names/paths and both ordinary sessions explicitly; do not
  blindly execute saved VM commands. Retain all mandatory assertions, account
  barriers and fresh report/source manifests; maintainers enter passwords directly.
- A5 tests refused/tampered/permission/sharing states and real worker termination,
  not only happy-path round trips. Keep the full suite's actual totals; classify
  out-of-scope failures and narrow skips without deselecting mandatory safety
  cases to manufacture a pass. Full diagnostics must use the reviewed explicit
  owner-fixture mode and account coordination; a separately accepted owner subset
  does not turn a fixture-blocked full run into a pass. Reuse #27/#28 evidence only for matching source
  and its original environment limits. Do not require Git restore support merely
  to manually commit a completed encrypted backup.
- A6 updates `windows-cli-gate-proposal.md` before implementation to match the
  approved smaller scope. Test eligible architecture/Python/storage dispatch and
  refusal for excluded operations. Preserve POSIX paths and low-level backend
  boundaries. Both fresh wheel and sdist need real installed console/module
  tests; calling private functions is insufficient. No user-facing unsafe switch.
- A7 cannot use the existing elevated hosted Windows run as ordinary-user proof.
  A local laptop is sufficient for interactive native evidence; a reviewed
  disposable x64 VM/runner can later automate it. Avoid making a family machine
  a general public-PR self-hosted runner. Server VM results do not automatically
  qualify Windows 11. Record local, hosted, injected, skipped and unexecuted
  evidence separately at the final candidate identity.
- A8/A9 retain exact-byte restores, wrong-key/corruption refusal, no-write previews,
  key custody and clear interruption/storage limits. No universal power-loss or
  privileged-actor protection claim. Release preparation is distinct from use of
  real data and from GitHub/PyPI publication; use the runbook's separate checkpoints.

## Preservation, handoff and fallback

The host handoff is on `feature/17-add-safe-native-windows-support`, HEAD/cached
origin/live remote **e54875bfc4c2aee1d55633be622de940a2d1883f** when checked on
16 October. The older `e0cadc3dd7132edbcc01266f07992bb1943fdce3` is historical
Stage 1. Verify actual state on continuation; never reset, replace the checkout,
start from main or discard subsequent work. Git authorization was completed and
does not carry forward. The laptop checkout's current identity is unknown.

Preserve the five pre-existing Phase A changes: acquisition packet/catalogue,
acquisition-plan, maintainer index and changelog. This handoff adds this plan,
the next-chat prompt and additive qualification/navigation/changelog notes.
Everything remains unstaged/uncommitted unless separately authorized. Update
Python headers only on Python files actually changed, using
`Jeff Shurtliff (via GPT-6.1 Sol)` and the current local date; none changes here.

If A1 establishes a genuine laptop blocker, propose the smallest remedy first.
If unsuitable or unavailable, review a disposable x64 VM on an x64 host or a
Windows x64 cloud VM with ordinary test accounts and eligible NTFS. No purchase,
cloud resource, VM, runner registration or account setup is authorized by this
fallback. Preserve all ARM evidence and keep that custom-build route parked.

Each chat handoff must include exact source/candidate identity, delivered files,
executed versus unexecuted checks, issue status/unsent updates, raw-report privacy,
remaining decisions and Git/index status. Planning/docs checks do not establish
native success. Windows mutation/recovery and existing-log append remain gated
until their specifically approved implementation and acceptance milestones pass.

## Validation of this planning handoff

Executed: live issue/status and host Git/ref reads; fresh strict Sphinx; local
references across **50 rendered HTML pages**; both new pages rendered; acquisition
catalogue download/source equality; additive preservation of existing docs and
byte-for-byte preservation of the ARM acquisition plan, packet and catalogue;
source-link/fence/LF/privacy/scope/diff checks; unchanged application/tests/CI/
dependency files and empty-index verification. The requested project-memory
extension note was saved separately without editing the historical memory registry.

Unexecuted: fresh laptop readiness probes beyond the maintainer's CPU result,
payload acquisition, account/tool/environment setup, owner/native/application
tests, builds, real-vault rehearsal, CI, Windows enabling and release actions.
GitHub issues were read but not changed by this planning-only task. At handoff
the four tracked documentation changes and four new documentation/catalogue
files remain unstaged/uncommitted, including the preserved Phase A work; HEAD
remains the proposal checkpoint above. Recheck actual status in the next chat.

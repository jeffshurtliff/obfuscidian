# Plan: narrowly scoped native ARM64 Windows beta qualification — #29

**16 October 2026. Status: ARM64-only qualification scope and non-installing dependency audit approved; binary provisioning blocked.**

The maintainer approved only the bounded ARM qualification target and metadata
audit, while explicitly keeping production Windows operations gated and AMD64
unqualified. This does not authorize later phases, compiler/toolchain installation,
custom wheels, dependency changes, dispatch/order integration or publication.
The approved scope is a qualification target, not a support claim or completed
criterion. The original broader #17/#29 criteria remain outstanding.

The requested [cryptography build/provenance proposal](windows-arm64-cryptography-provenance-plan.md)
is tracked separately in [#30](https://github.com/jeffshurtliff/obfuscidian/issues/30),
a sibling of #29 under #17. Its read-only builder inventory and input-pin
preparation stage has delivered a [blocked feasibility report](windows-arm64-cryptography-stage1.md)
and incomplete input manifest; no usable authorized existing builder was
established. Later stages remain unapproved. Issue #29 stays open and blocked for
this ARM64 track, retaining
native suites, matrix, exchange and installed-command qualification. The split
does not change its broader criteria or close the original qualification effort.
The artifact proposal uses unchanged 50.0.2 source, a reviewed
builder/input manifest, reproducible outputs, native acceptance and an explicit
dependency-origin policy. No compiler, build, private wheel or dependency change
is approved; builder availability and exact toolchain pins remain open.

## Executed non-installing dependency audit — 16 October

The maintainer's ordinary-session pip diagnostics identify native ARM64 CPython
3.13.16 and 45 compatible wheel tags. The subsequent official PyPI JSON query
for cryptography 50.0.2 returned **zero Windows ARM64 wheels**. The diagnostics
were inspected as observations, not parsed by automation or treated as new
`IsWow64Process2` proof; the earlier native machine/process evidence is separate.

A host-side metadata audit then evaluated the unchanged lockfile's main/dev
markers for Windows ARM64 CPython 3.13.16, including the locked build backend.
Of 39 main/dev entries, existing Linux-only markers exclude `jeepney` and
`secretstorage`; **37 entries apply**. Official release metadata lists at least
one compatible non-yanked wheel with a matching locked SHA-256 and Python version
constraint for **36 packages**. **Cryptography 50.0.2 is the sole missing compatible
locked binary.** These are release-metadata compatibility results, not downloaded
artifact validation, successful resolution/imports or installation passes.

The audit models tags with the installed packaging library; its 45-tag set agrees
with the observed native pip tag list. The lock SHA-256 remains
`b63c1714fcf641742a10be8cf46b4d641ea0329217a86835379d4105515e10fb`.
Private reports retain names, versions, official metadata URLs, compatible wheel
names, published/locked hashes and target markers. The first host metadata fetch
failed TLS trust validation for all 37 entries; that failed report is preserved.
The corrected fetch used the already installed trusted CA bundle with certificate
verification retained, and all 37 metadata requests completed. No package
artifacts were downloaded, installed or built, no guest application tests ran,
and no dependencies, environments or machine settings were changed.

**Stop here:** the unchanged locked set has no complete official binary route
for this target. No further PowerShell installation/source-build command follows
from the audit authorization. A viable dependency/build/artifact-provenance route
requires a separate concrete proposal and approval. Full ARM qualification,
installed writes and beta acceptance remain blocked; accepted fix04 owner
evidence and every earlier failed total are unchanged.

## Approved qualification target and remaining decisions

The maintainer has only the existing ARM64 UTM VM available. The recorded fix04
actual-owner evidence is already accepted for its precise combination. The
approved target is a separate ARM64 qualification track for a synthetic-data lab beta, with AMD64
explicitly unqualified and the broader #17/#29 completion criteria still open.
All production Windows operations stay gated throughout preparation and private
testing. The scoped envelope/matrix target below is approved for qualification;
this does not approve dispatch integration, broader criterion completion,
toolchain installation, dependency changes, remote CI or beta publication.

| Dimension | Proposed first beta envelope |
| --- | --- |
| Guest | Recorded Windows 11 Home build 26300, UTM 4.7.5 (118), QEMU ARM `virt-10.0`; measure full revision/channel and virtualization mode before freezing the candidate |
| Interpreter | Native ARM64, GIL-enabled CPython 3.13.16, 64 bits; per-user installer and isolated environments |
| Architecture proof | `IsWow64Process2`: native `0xAA64`, process `0x0000`; no emulated Python or architecture-string substitution |
| Storage | Internal fixed NTFS with persistent ACLs, validated by production opened-handle guards; no shared/synced/network/removable paths |
| Payload/permissions | Existing native owner/protected-DACL, ordinary-file/stream, identity, entry/depth/size and resource bounds remain mandatory; no repair or relaxed validation |
| Accounts/data | Existing two standard test accounts, no elevation or privilege activation; generated keys and disposable synthetic data only |
| Proposed writes | Fresh backup into an absent mirror; fresh restore into an absent destination; existing explicit transaction recovery restricted to those eligible operations |
| Excluded writes | Merge backup, existing-mirror replacement, destination replacement, Git restore/publication and existing-log append |
| Existing read-only behavior | Key creation, authenticated verification and planning retain their existing contracts; previews/verification create no application artifacts |
| Other targets | AMD64, emulated AMD64 Python, Server, Store Python, other Python versions, guest builds and physical ARM hosts remain unqualified for this beta |

The official [Python 3.13.16 release](https://www.python.org/downloads/release/python-31316/)
labels its Windows ARM64 installer experimental. Any eventual lab-beta wording
must disclose that upstream status and this single-VM evidence limit; it cannot
claim general Windows support. An OS/Python/dependency update requires a new
recorded candidate and review of the affected evidence, not automatic eligibility.

## Scoped qualification target approved; broader criteria remain open

| Existing target or requirement | Proposed ARM-only treatment | What remains required |
| --- | --- | --- |
| Native AMD64 Windows eligibility | Add a separate native ARM64 row for the exact envelope above | AMD64 remains unqualified; existing AMD64 probes/assertions and historical results remain intact |
| Windows 11 / Server and Python 3.12–3.14, including Store | Qualify only the recorded Windows 11 Home / traditional per-user native ARM64 CPython 3.13.16 combination | No Server/Store/other-version support claim or completed broad-platform checkbox |
| Successful nine-job Linux/macOS/Windows matrix | Propose an ARM-beta evidence set of all six Linux/macOS Python 3.12–3.14 jobs plus a separately recorded full native ARM64 3.13.16 run and ARM installed artifacts at the same approved commit | Existing three AMD64 Windows jobs retain actual outcomes and stay unqualified; they are not ARM evidence. The original all-nine-success criterion remains unmet for #17/#29 |
| Full Windows operation envelope | First beta offers only the absent-destination operations and bound recovery above | All other Windows writes continue to refuse; full private backend diagnostics remain selected and reported |
| Installed CLI write checks before production dispatch is integrated | Retain the separate gate-order decision, with its prerequisites explicitly adapted to this ARM-beta evidence set only if approved | No supported CLI writes until separate dispatch/order approval; actual installed console/module acceptance is still mandatory afterward |

The approved ARM-only matrix target is a scope revision, not a passing
reinterpretation of the old matrix; its execution remains unapproved. No tests, workflows
or required checks are disabled to manufacture success. Preserve the three
elevated AMD64 job failures and their setup errors/skips. Any new unexplained
failure, including outside the proposed envelope, requires review. Repository
protection rules still apply; this plan grants no bypass. A narrow lab beta would
not complete or authorize closure of the broad #17/#29 qualification effort.

## Phase 1: establish a complete, reproducible ARM toolchain

**Goal:** a runnable application and full test environment in ordinary sessions.
**Authorization:** scope and non-installing audit only; the executed audit above
stops at missing binary provisioning. Later tasks are not authorized by that audit.

1. Audit the unchanged `poetry.lock`, runtime/build/dev requirements and official
   release file metadata for CPython 3.13 on Windows ARM64. Record wheel names,
   compatible tags, hashes and provenance privately. This metadata/download-only
   audit must forbid source builds; it installs nothing and executes no build
   backend. Use the [pip binary-only download controls](https://pip.pypa.io/en/stable/cli/pip_download/)
   when later verifying a fresh disposable wheelhouse in the guest.
2. Treat cryptography as a current blocker. The
   [50.0.2 release file list](https://pypi.org/project/cryptography/50.0.2/#files)
   has no `win_arm64` wheel at review; the two guest source builds failed without
   `link.exe` and remain failures. Its
   [Windows build documentation](https://cryptography.io/en/50.0.2/installation/#building-cryptography-on-windows)
   requires a compatible native build toolchain, OpenSSL and Rust. A missing
   linker is not established to be the only missing prerequisite.
3. Stop if the unchanged locked dependency set has no compatible, trusted native
   binary route. The present constraints do not authorize a compiler install,
   third-party wheel, manual copied package or dependency downgrade/upgrade.
   A future upstream compatible artifact, a separately approved reproducible
   build/wheel-provenance plan using the same dependency versions, or an explicit
   dependency revision with regenerated lock and compatibility/security evidence
   would need its own concrete review. None is assumed available or approved.
   A privately built wheel absent from the lock's artifact hashes also requires
   explicit provenance/lock-policy review; matching a version string does not
   authorize forcing it into the environment or editing the lock by hand.
4. After a viable route is approved, verify all dependency imports, strict lock,
   selected Poetry interpreter, `pip check`, and actual native machine/process
   codes in fresh per-user environments. Do not overwrite the partial owner-test
   environment or its reports. Record a per-user Git for Windows tool/version
   for the full private Git tests; native versus emulated Git is an explicit
   observation, with any emulated tool requiring separate scope review.

**Exit evidence:** complete reproducible runtime/build/dev installations without
administrator elevation, hashes/tool versions, no implicit source-build fallback, and
successful application imports plus dependency checks. An owner-only environment
does not pass. Until then, the entire path remains blocked at Phase 1.

## Phase 2: review ARM-specific test tooling, then execute private qualification

**Locations:** `.github/scripts/check_windows_lifecycle.ps1`,
`.github/scripts/check_windows_git_restore.ps1`, the separate owner-VM runner,
`tests/_windows_owner_vm.py`, `tests/_windows_support.py` and relevant tooling tests.

1. Prepare a separately reviewed ARM runner or explicit architecture mode using
   actual machine/process APIs. Preserve the AMD64 default requirement. Check
   pointer widths, handle sharing, token membership including filtered-admin
   cases, process-worker ancestry and safe synthetic paths. Add meaningful
   portable regressions for wrong/unknown architectures, emulation, selected
   interpreter mismatch and unavailable prerequisites. Do not weaken production.
2. Keep the original mandatory owner node in scoped and complete diagnostics,
   using the explicit two-account fixture and visible manual barrier. Do not
   redirect interactive input to a hidden log, deselect, skip or xfail that node.
   Preserve accepted fix04 evidence; a later full-candidate run is separately
   identified, with fresh reports and all mandatory assertions retained.
3. Execute actual primitive/checkpoint, DACL enforcement, lifecycle, metadata,
   process-termination and private Git success/failure suites, then full pytest
   diagnostics on the native ARM interpreter. Include #27 retry5's six metadata
   boundaries and #28's kernel-denial positive control; earlier AMD64 bounded
   passes are not ARM execution. Retain unexpected states and raw reports.

**Exit evidence:** individual native results, all required owner properties,
complete scoped/full totals and narrow platform skips, source hashes, exits and
actual toolchain/storage observations. Any unexecuted safety case stays a gap.
Injected models remain supplementary. No power-loss or general Git recovery
guarantee follows from worker termination or ordinary cleanup tests.

## Phase 3: compatibility and exact-candidate evidence before dispatch review

**Locations:** `tests/_v1_exchange.py`, `tests/integration/test_packaging.py`,
`.github/scripts/check_artifacts.py`, `.github/workflows/test.yml` and the evidence record.

1. Exchange newly generated synthetic v1 backups in both ARM-Windows/macOS
   directions, using private backend qualification tooling while production
   Windows dispatch stays refused. Verify primary bytes, empty directories,
   layout authentication and unchanged sources/mirrors; keep generated keys
   outside source/destination trees and all raw exchange material private.
2. Build fresh wheel/sdist and qualify both in independent native ARM per-user
   installations outside the checkout with the approved wheelhouse. Validate
   metadata, help/version, keygen, authenticated read-only commands, consent and
   all currently required Windows write/append refusals. These remain installed
   refusal checks, not installed write qualification.
3. Run lock/Ruff/Bandit/docs/local references and all local regression checks.
   After separately authorized Git delivery/remote execution, collect all six
   POSIX matrix passes plus full ARM evidence at the same approved exact commit.
   Preserve actual legacy Windows outcomes separately. A local source manifest
   is valid preparation provenance but does not satisfy exact-commit CI.

**Exit evidence:** two actual exchange directions, native ARM artifact installs,
complete private qualification and the explicitly approved matrix evidence set.
No remote execution is dispatched by this plan.

## Phase 4: separate dispatch/order approval, then installed write qualification

**Prerequisite:** Phases 1–3 passed and maintainer review of both the scoped matrix
revision and [installed CLI gate-order proposal](windows-cli-gate-proposal.md).
This later approval is distinct from accepting the owner case or this plan.

1. Before requesting implementation approval, prepare the exact dispatch diff
   and negative tests for the proposed first-beta envelope. Planned call sites
   are `backup._publish_backup` / `_recover_backup`,
   `restore._publish_restore` / `_recover_restore` and existing CLI dispatch.
   Require proof that the destination was absent and that recovery's bound
   operation/options match an eligible first-beta transaction. If current
   metadata cannot establish that restriction, stop for design review; do not
   guess, adopt unknown state or add an incidental public API/bypass switch.
2. Only after explicit authorization, implement the reviewed local routing and
   retain refusal for merge/replacement/Git/append, excluded environments and
   uncertain states. Preserve POSIX, CLI syntax/consent, Fernet/v1, dependencies,
   exact owner/DACL/identity checks and retained rollback semantics.
3. Build/install both fresh artifacts again and execute actual console **and**
   module entry points outside the checkout: new-mirror backup, absent-target
   restore, worker interruption and bound explicit recovery before retry,
   sensitive-state reporting, output privacy, no-write previews and every
   excluded-operation refusal. Inspect actual output/control/retained plaintext
   DACLs. Keep each application's execution unelevated.

**Exit evidence:** both independently installed artifact forms pass real command
success/failure/recovery tests on the exact ARM envelope, with unchanged excluded
operation refusals and POSIX regressions. No installed private-function or
injected dispatch substitutes for these commands. Failures block beta acceptance;
they do not authorize retries on unknown retained state.

## Phase 5: final acceptance and public-safe lab-beta handoff

Repeat required checks at the final approved exact commit after any implementation
changes. Audit every criterion and publish no claim until separately authorized.
Prepare accurate platform, CLI, transaction, recovery, getting-started, threat
model and changelog wording for the actual qualified envelope and excluded modes.
Explicitly retain single-VM/experimental-interpreter, same-user/privileged-actor,
retained-copy, existing Git interruption and OS/power-loss limitations.

Deliver a public-safe pass/fail/skipped/unexecuted ledger, private report inventory,
source/artifact identities and an accurate unstaged/uncommitted status. Keep
#17/#29 open for broader Windows work. Enabling production operations, staging,
commit/push/PR/merge, remote CI, release/publication and issue closure each still
require their separately applicable approval. This session performs none of them.

## Stop conditions and evidence preservation

The currently demonstrated increment is the accepted fix04 owner case only.
No ARM full dependency installation, full private suite, exchanged backup or
installed Windows write pass is inferred. Preserve all three earlier failed
owner totals, both failed dependency builds, predecessor failures and separate
retry5/kernel-control evidence. Do not repair or delete uncertain synthetic data.
Missing binaries, privileges, eligibility or evidence stop the affected phase.
No account creation, policy change, real data or credential collection is allowed.
If dispatch work later fails, keep it unqualified and retain evidence; any return
to gated routing must be a focused reviewed edit preserving all unrelated work,
never a reset or blanket checkout. The current production gates are unchanged.

**Next decision:** review the separate [dependency/build/provenance proposal](windows-arm64-cryptography-provenance-plan.md)
for the cryptography blocker. Its recommended first stage is read-only builder
feasibility and input-pin preparation, with no demonstrated builder yet. The approved non-installing audit is complete;
it authorizes no compiler, custom wheel, dependency revision or native application
test. Production Windows operations remain gated and AMD64 unqualified.

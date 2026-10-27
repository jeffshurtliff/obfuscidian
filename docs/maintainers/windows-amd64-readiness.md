# AMD64 laptop readiness and A2 decision packet — #17 / #29

**17 October 2026. A1 complete: read-only readiness and official dependency
metadata audit. Conditional go for A2 review only; no setup or native qualification.**

The selected physical laptop is a viable candidate for the proposed Windows
work. Its measured native AMD64 interpreter and canonical package metadata do
not show the ARM64 cryptography binary blocker. Two dedicated owner-fixture
accounts are absent, and installation, owner proof, application qualification,
matrix and installed-command acceptance remain outstanding. Native AMD64 support
is **unqualified**. The smaller first scope and revised prerequisites are still
proposals, not approved replacements for the broad #17/#29 criteria.

Read this report with the [continuation plan](windows-amd64-continuation-plan.md),
[qualification history](windows-qualification.md), [owner protocol](windows-owner-vm.md)
and [unchanged CLI gate-order proposal](windows-cli-gate-proposal.md).
The [next-chat prompt](windows-amd64-next-chat.md) now starts A2 review only.

## Source identity and evidence boundaries

Both host and laptop report branch `feature/17-add-safe-native-windows-support`,
HEAD/cached origin/live remote **64dcff07f1ad456fd0aa38f775c6bcf9a4c8f592**.
This newer continuation preserves the prior `e54875b` checkpoint; neither checkout
was reset or replaced. Initial host and laptop tree/index are clean, with zero
laptop untracked entries. The laptop was inspected through maintainer-entered
read-only Git commands with optional locks and filesystem-monitor invocation
disabled; no fetch or ref update was performed. No Git delivery is authorized.

The host independently reads these unchanged inputs; the laptop's pasted
read-only hashes match exactly:

| Input | SHA-256 |
| --- | --- |
| `pyproject.toml` | `1e66448aad2e0c5925d827afd85333791ac3635d885516a0fbcb5619d6f85fe5` |
| `poetry.lock` | `b63c1714fcf641742a10be8cf46b4d641ea0329217a86835379d4105515e10fb` |

Laptop observations below are maintainer-executed/pasted results, not agent
computer-use execution or independently transferred raw-report verification.
They establish current-session readiness facts, not an exact future installed
candidate. A3/A4 must bind actual source bytes, including checkout line endings,
to a fresh manifest and recheck each account's process/token/storage. No private
paths, usernames, account SIDs, raw inventories, keys or vault contents belong
in this report or public issues.

## Current readiness table

| Area | Result | Measured facts and exact remaining gap |
| --- | --- | --- |
| CPU observation | Pass for candidate selection | Maintainer's earlier `Architecture=9`, `AddressWidth=64` retained; unchanged CPU command was not repeated |
| OS/session | Pass for A1 | Windows 11 Home / Core, 25H2, **26200.9711**; PowerShell **5.1.26100.9711**; no other Windows build or Server qualification follows |
| Current token | Pass for A1 | Effective administrator **False**, integrity **Medium**, Administrators SID absent; this is not either future designated fixture session |
| Interpreter | Pass for A1 | Current-account PSF Store package **3.13.3824.0**, X64, status OK; actual **CPython 3.13.14**, 64-bit pointers, process `0x0000`, native `0x8664`, `win-amd64`, GIL-disabled build False |
| Executable identity | Resolved | `QueryFullProcessImageNameW` reports the exact selected package `python3.13.exe`; `sys.executable` reports the Store `python.exe` alias. Use the verified explicit package executable for later probes, rechecking it each session |
| Git / Poetry | Pass for A1 | Actual `git --version`: **2.55.0.windows.5**; Poetry **2.5.1** with plugins/cache disabled for version read; existing Poetry project environment/dependency completeness was not inspected or assumed |
| Source checkout | Pass for A1 | Host and laptop refs agree at `64dcff0`; laptop tree/index/untracked counts zero; canonical input hashes match. Preserve it and every subsequent local change |
| Proposed storage | Conditional | Both proposed parents report NTFS, drive type **3 / Fixed**, persistent ACLs True, read-only-volume False; observed healthy volume, **350,088,290,304 free bytes** at final probe (about 326 GiB). Earlier space observation was slightly higher; neither reserves space |
| Proposed namespace | Conditional | Per-account proposed private root absent; Public Documents exists; checked ancestors report zero reparse points. Persistent-ACL flags/metadata observations do not prove production opened-volume/namespace/DACL checks, actual create permission, sync exclusion or enforcement |
| Owner accounts | Blocked for owner execution | Maintainer confirms **ObfOwnerA and ObfOwnerB are absent on the laptop**, present only in the ARM VM. No named-account lookup repetition or broad enumeration needed; both future standard sessions and runtimes need separate setup approval |
| Canonical binary route | Metadata pass | **37/37** runtime/dev/build entries; **59/59** including optional docs; exact selected-wheel sidecars and target dependency constraints checked. No package payload acquired, installed or imported |
| AMD64 real-owner proof | Unexecuted | Original mandatory test, positive setup, actual distinct owner transition, both production refusals, full identity/bytes/exact protected DACL and private source-bound reports still required |
| Native application / release | Unqualified | Applicable private suites, both generated v1 exchange directions, approved matrix, installed wheel/sdist console/module writes/recovery and final scope/support decisions remain pending |

## Complete canonical binary-route result

Download the [AMD64 metadata catalogue](windows-amd64-binary-audit.json) for every
selected package/version/wheel, compatible locked alternatives, official URLs,
published wheel hashes, matching lock declarations, selected sidecar hashes,
Python constraints, target markers/tags and active dependency edges.
This catalogue is metadata evidence, not a payload acquisition queue, installed
environment, second runtime lock or permission to install.

| Independently evaluated profile | Applicable packages | Compatible non-yanked locked wheels / verified sidecars | Selected payload sizes declared by metadata |
| --- | ---: | ---: | ---: |
| Runtime (`main`) | 7 | 7 / 7 | 4,586,459 bytes |
| Runtime + dev + project build backend | 37 | 37 / 37 | 20,210,192 bytes |
| Runtime + dev + optional docs + build backend | 59 | 59 / 59 | 43,067,295 bytes |

Counts are nested, not additive. Optional docs adds 22 packages to the 37-package
development profile. Of 61 locked packages, Linux-only `jeepney` and
`secretstorage` are excluded by the actual target's markers. Build requirement
`poetry-core>=2.2.0,<3.0.0` is satisfied by locked **2.5.0** and counted once.
This audits the project's backend, not installation of Poetry CLI 2.5.1 or its
separate bootstrap environment in a new account. No package extras are requested.

All applicable roots and selected-wheel `Requires-Dist` edges satisfy the
unchanged locked versions and target markers, with **zero missing dependencies
or incompatible constraints** in all three profiles. Native/platform wheels
include CFFI, charset-normalizer, coverage, cryptography, MarkupSafe (docs), nh3,
PyYAML and Ruff; the catalogue includes every universal wheel as well.

Cryptography's selected official binary is
`cryptography-50.0.2-cp311-abi3-win_amd64.whl`, declared SHA-256
`7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c`.
It is compatible with measured standard CPython 3.13.14 and matches the lock.
An older-baseline `cp39-abi3-win_amd64` wheel is another compatible locked choice;
the audit selects the higher-ranked `cp311-abi3` sidecar. No private cryptography
build or new artifact-origin policy is indicated by this AMD64 metadata result.
The [official release metadata](https://pypi.org/pypi/cryptography/50.0.2/json)
remains distinct from downloaded wheel-byte verification.

### Method, receipts and practical limits

The measured marker environment is recorded in the catalogue, including
`implementation_name=cpython`, `platform_machine=AMD64`,
`platform_python_implementation=CPython`, `sys_platform=win32`,
`python_full_version=3.13.14`, Windows release `11` and version `10.0.26200`.
Existing host packaging **26.3** models the **45** standard CPython 3.13 AMD64
tags using explicit target inputs, without using host macOS tags or importing a
laptop/candidate package. This is a fresh AMD64 evaluation; the ARM 36/37 audit
does not supply any result here.

TLS-verified requests used official PyPI release JSON, the official Simple JSON
API and only the selected wheel's separately served `.whl.metadata` text.
For each package, require compatible wheel tags, package/file Python constraints,
non-yanked status and identical release/index/locked wheel SHA-256 declarations.
The selected sidecar's **actual metadata bytes** match its index-declared digest,
Name/Version/Python constraints; dependency checks use that exact sidecar.
All **177 metadata response receipts** were retained in fresh private host
temporary storage; the public catalogue records URLs/hashes and receipt-set
identity, with no host location map. No artifact-body digest, RECORD/PE content,
signature/attestation, install/import result or source-build success is claimed.
Alternative wheels' own sidecars were not individually audited. A later binary
acquisition must select the reviewed exact rows or re-audit a different choice.

The initial metadata parser incorrectly rejected all `Dynamic` headers in
prebuilt wheel metadata, leaving 22 assertion errors and an incomplete first
report. The [PyPA core metadata specification](https://packaging.python.org/en/latest/specifications/core-metadata/#dynamic-multiple-use)
defines those fields as informational outside source distributions. The final
audit reprocessed all 177 preserved responses offline, using the exact selected
wheel's declared fields and retaining the initial report unchanged. No additional
payload request, package-version substitution or compatibility check waiver was
used. Metadata success still requires later acquired-byte/hash verification,
binary-only installation and actual application evidence.

## Proposed isolated paths and minimum setup — review only

These are environment-variable templates; keep the private mapping on the laptop.
Only the current account's top-level private-root absence and existing fixture
parent were observed. Future accounts' profiles, every child path, source access,
ACLs, volume identities and usable/free space remain unverified. Refuse existing
task locations rather than replacing or cleaning them.

| Purpose | Proposed location / handling |
| --- | --- |
| Existing laptop checkout | Keep its current private location and branch; do not pull/reset/copy over it as a setup shortcut |
| Per-account runtime/tools | `%LOCALAPPDATA%\Obf29Amd64\Python313` if separately approved provisioning is necessary; isolated Poetry tools under `%LOCALAPPDATA%\Obf29Amd64\tools` |
| Account A project environment | `%LOCALAPPDATA%\Obf29Amd64\envs\candidate-01`; no reuse of the historical development environment or cross-account private environment |
| A/B private evidence and temporary work | Each account's `%LOCALAPPDATA%\Obf29Amd64\reports\attempt-01` and `work\attempt-01`; new attempts retain all earlier folders |
| Shared reviewed public source | `%PUBLIC%\Documents\obfuscidian-29-amd64-candidate-01`, with a manifest and only public source; do not transfer private `local/`, credentials, keys or real vaults |
| Owner fixture | **Directly** beneath `%PUBLIC%\Documents`, named `obfuscidian-owner29-<32 lowercase hex digits>` by the reviewed harness; do not nest it under an invented work root |
| Binary inputs | Fresh separately approved wheel storage outside the checkout and fixtures; only exact reviewed upstream files with lock-hash verification, no source fallback |

The existing reviewed helper requires the exact local names **ObfOwnerA** and
**ObfOwnerB**. The current standard account cannot stand in for A without an
explicitly reviewed harness change. Recommend two dedicated local **standard**
test accounts to reuse the unchanged reviewed protocol. A trusted administrator
would create only those accounts after separate approval; the maintainer enters
every password directly. The present standard session cannot be assumed to
have account-creation rights. No administrator test session, privilege activation,
machine policy, real-data ACL change or cleanup authority follows.

Account A needs verified native CPython 3.13, Poetry and the locked development
environment. B needs its own verified native CPython and the shared reviewed
source; the peer uses isolated stdlib/private source and needs no Poetry or full
application dependency installation. The current account's Store registration
and tools do **not** establish access/registration in A or B. A2 must settle
whether the existing exact Store package can be used in each ordinary account,
or propose a pinned official per-user native x64 PSF interpreter. Freeze exact
version, artifact metadata/checksum, executable and rights before any A3 install;
if the actual target version changes, refresh the relevant marker/tag audit.
No new Python/Poetry installer/bootstrap artifact has been accepted by A1.

For future preparation, require binary-only project consumption of the canonical
lock, fresh per-user environments and source manifests, no compiler/backend
fallback, and no PATH/launcher/long-path-policy changes. Any missing tool stays
missing until specifically approved; A2 must include the exact bootstrap closure
and commands rather than treating the project audit as a Poetry installer audit.
An absent compatible wheel or changed source/metadata stops that preparation.
Before later tests, parse the reviewed scripts under the actual PowerShell and
recheck production guards; do not run the existing install-and-test helpers in A1.

Concrete runner gaps for A2 review: the existing lifecycle/Git helpers install
dependencies and select the original owner case without `--owner-vm-two-account`,
so running them unchanged would return to the known unavailable group strategy.
The two-account owner runner supplies that explicit option but calls the VM
environment script, which includes the unchanged CPU query, and labels its
report scope as one VM case. Review a bounded physical-host procedure/runner
proposal before any later execution: preserve the mandatory test/assertions,
use the verified A/B executables, avoid the unchanged CPU/group retry and report
physical AMD64 evidence accurately. This identifies future tooling work; no
helper, fixture, test option, scope flag or source file is changed by A1.

## Concrete A2 decision packet and order

**Recommend A2 next, with review/proposals only. A2 does not execute setup or
tests.** These decisions are deliberately unresolved for explicit maintainer review:

| Decision | Concrete recommendation / required disposition |
| --- | --- |
| Candidate purpose | Begin with a synthetic-data engineering candidate on the measured Windows 11 Home / native AMD64 / standard CPython 3.13 envelope. Decide separately whether/when to target public beta or stable 2.0.0; no current support claim |
| First operations | Absent-mirror fresh encrypted backup; authenticated verify/no-write planning; absent-destination fresh restore; recovery bound to eligible interrupted new-destination operations. Manual commit/push of the complete encrypted mirror only |
| Deferred requirements | Explicitly map existing-mirror updates/replacement, merge backup, destination replacement, public Git merge restore, other hosts/Python/storage rows to retained #17/#29 requirements or later approved linked follow-ups. Existing-log append remains refused. Open/close nothing during A1 |
| Accounts and rights | Review two dedicated standard accounts with exact helper names; identify whether an authorized administrator is available. If not, retain the blocker and propose a controlled x64 alternative; do not reject this hardware solely for missing accounts |
| Per-account setup | Freeze runtime choice in A/B, isolated locations, source access, per-account process/token checks and Poetry bootstrap closure. Produce exact commands with explicit acquisition/install/write boundaries for separate A3 approval; no current installation completeness claim |
| Validation matrix | Separate the proposed first local Windows 11 / CPython 3.13 row from original Windows 11/Server, 3.12–3.14 and all-nine-job obligations. Keep six POSIX rows and historical three elevated Windows failures visible. Review a runnable ordinary-user Windows strategy; no public-PR runner on the family laptop or silent matrix reduction |
| Gate order | Review a concrete revision of `windows-cli-gate-proposal.md` before implementation: actual AMD64 owner proof and applicable private safety/lifecycle/DACL/termination/exchange evidence precede approved local dispatch; installed console/module wheel/sdist writes follow that integration; final approved exact-candidate regression/CI and support acceptance remain later gates. Original prerequisites remain in force until a replacement is explicitly approved |
| Source and execution | Preserve current checkouts; use separately reviewed public snapshot bytes/manifest for the two-account lab. Review VM-named helper assumptions for physical-host reuse, actual A/B executables and interactive barriers, fresh reports and failure retention. No source transfer, fixture or test execution yet |

Bound recovery must reject unrelated operation modes/retained states rather than
enable the entire private backend accidentally. No installed private-function
call, environment switch, skip, injected response or setup-only pass substitutes
for actual console/module behavior and the original owner safety assertions.
Preserve source bytes, authentication, private plaintext, exact-byte restores,
confirmation/refusal behavior and retention of uncertain recovery states.

After A2 decisions are reviewed, A3 is separately approved preparation only.
A4 then separately reviews/executes the **actual AMD64** owner case. A5–A9 retain
their individual native/exchange, integration/artifact, CI, documentation/use and
release boundaries in the continuation plan. Do not jump from this metadata pass
to a write command, personal-data rehearsal, installed test or publication.

### What the maintainer needs to do next

1. Review this report and the proposed first operation/environment scope.
2. Start A2 using the saved prompt; decide the candidate purpose, deferred scope,
   matrix/gate-order treatment, runtime/account plan and exact allowed setup.
3. For that review, state whether a trusted administrator can later create the
   two standard accounts. **Do not create them, install anything, change policy,
   run the owner helper or send passwords now.**
4. After the concrete A2 packet is accepted, authorize only the named A3 actions.
   Actual account switching and the source-bound owner transition occur later in
   separately approved A4; keep A signed in while B performs the exact peer step.

## Preserved evidence, checks and stopping point

#17 stays parent, #29 active qualification; #25–#28 are reviewed implementation
history, not work to restart. Start/direction and meaningful progress comments
were posted on #17/#29; a parked-work note was posted on #30. Handoff comments
record final checks without editing historical bodies/checklists or changing
labels, milestones, relationships or issue state. No issue is opened or closed.

#30's ARM acquisition/custom-build track is **parked, not solved or deleted**.
Keep its Microsoft mismatch and 18.10.4 discovery, VM/frozen snapshot, private
reports, original flags, historical failures and accepted fix04 **1 passed in
215.27s** unchanged. That pass belongs only to its recorded ARM environment.
No ARM proof rerun occurred or is needed for this A1 pivot.

Executed A1 checks: read root guidance, live #17/#25–#30 and relevant handoffs,
canonical inputs and existing runner/fixture source; read-only host/laptop
Git/ref/hash comparisons; the ordered maintainer-entered token, OS, interpreter,
version, storage and account-availability observations; fresh official AMD64
metadata/sidecar/closure audit; documentation validation recorded in the final
handoff below. Raw reports remain private; public records contain sanitized facts.

Preserve probe failures accurately: initial host network reads failed before
successful read-only live verification; host default Python lacked packaging,
so the existing project environment's packaging was used without installing it.
The first laptop Python `-c` command failed parsing because of PowerShell 5.1
argument quoting; stdin delivery succeeded. A subsequent alias-file hash probe
failed with invalid-argument before returning its comparison; the successful
native process-image query resolved executable identity. Neither failure is an
Obfuscidian application result. The metadata-parser correction is documented
above with the incomplete report preserved. No failed invocation is relabeled.

Unexecuted: account/privilege/policy/ACL changes, package/tool payload acquisition,
environment creation or installation, source/backend builds, source transfer,
fixture writes, tests (including owner/native/application/packaging), exchanged
v1 artifacts, CI dispatch, real-vault/key access, Windows dispatch/gate enabling,
Git delivery and release/publication. POSIX behavior, CLI syntax/gate order,
Fernet/v1, canonical inputs and existing-log append refusal remain unchanged.
Stop for maintainer review before A2 execution or any setup/test work.

### Final documentation validation and Git handoff

Executed on the existing host environment, without installing dependencies:

- Fresh strict Sphinx (`-W --keep-going -E -a -b html`) passed without warnings.
- Local rendered links/assets/anchors passed across **51 HTML pages**; external
  URL availability was not checked by that checker.
- All five readiness tables, key findings and the A2 prompt rendered; the
  downloadable 59-package JSON catalogue is byte-identical to its source.
- Catalogue/lock/digest/count/evidence-flag, receipt and selected dependency
  checks passed; source links, fences, LF, privacy, scope and diff checks passed.
- Runtime/tests/CI/dependency files, historical ARM acquisition inputs/packet,
  owner/primitive/lifecycle/Git records and the CLI gate proposal remain unchanged.
  Required predecessor commits are ancestors; no historical evidence was deleted.

Host HEAD/cached origin remain `64dcff07f1ad456fd0aa38f775c6bcf9a4c8f592`.
Five tracked documentation files are modified and two documentation/catalogue
files are new, all **unstaged/uncommitted**; the index is empty. The laptop was
clean when measured and receives no file writes from this work. These local
documentation changes have not been transferred there. Host live-ref comparison
and public-safe #17/#29 handoff comments accompany the final response; no Git
delivery, issue-state change or further qualification work is authorized.

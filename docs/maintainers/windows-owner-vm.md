# Two-account Windows VM owner proof — #29

**16 October 2026. Status: fix04 owner evidence accepted only for the recorded native ARM64 combination.**

The maintainer explicitly accepted the owner-proof evidence for Windows 11 Home
build 26300 / internal fixed NTFS / native ARM64 CPython 3.13.16 only. Production
Windows operations remain gated. This accepts the bounded evidence recorded
below; it does not qualify AMD64, broader ARM support or any production operation.
For the original AMD64 target, the next qualification step requires an eligible
native AMD64 environment and existing unelevated owner fixture. The maintainer
now confirms only the ARM64 VM is available and requests a separate
[ARM64-only beta qualification proposal](windows-arm64-beta-qualification-plan.md).
The maintainer approved its bounded ARM qualification scope and non-installing
audit only. The audit finds compatible locked wheel metadata for 36 of 37
applicable packages, with cryptography 50.0.2 blocking the complete binary route.
AMD64 remains unqualified and production operations stay gated. No additional accounts,
privileges, machine-policy changes or dependency changes are authorized.

The maintainer has provisioned two distinct standard test accounts in a disposable
Windows 11 VM and authorized a synthetic two-account fixture. This supersedes
the earlier account-availability blocker only for that VM. Account provisioning
is complete before this workflow; it grants no authority to create accounts,
activate privileges, change policy or modify real data. Passwords are entered
directly by the maintainer and never accepted by a harness.

The preserved checkout starts at `d4bca46` on
`feature/17-add-safe-native-windows-support`. Accepted #26 continuation `2316457`,
#27 through `cbd30bb`, and #28 runtime `395454b` / handoff `a92ab73` are ancestors.
The lifecycle test still matches retry5 SHA-256
`2e7cebd7e5d70c937373afef0af714132e673817094e32041279966156466797`.
All application and dependency files match `395454b`. This verifies the
applicability of accepted records; it does not inspect old private reports or
create new native evidence. Retain every historical failed total in the
[qualification record](windows-qualification.md), including retry5's separate
six-case metadata pass and #28's separate targeted kernel pass.

## Current executed owner evidence — fix04

The maintainer executed the reviewed original mandatory test, with the explicit
two-account fixture, in ordinary sessions on Windows 11 Home build 26300,
internal fixed NTFS and native ARM64 CPython 3.13.16. Both account preflights
reported 64 bits, native machine `0xAA64`, process machine `0x0000`, no elevation
and no Administrators membership. This is native ARM64 evidence, not native
AMD64 or an AMD64 process under emulation. UTM hardware acceleration and the
guest release channel remain unverified.

**Result: 1 passed in 215.27s (0:03:35)**. The runner validated the mandatory
properties. The maintainer supplied the terminal result and a read-only summary
of the saved attempt-04 JUnit/status reports: one case, zero failure/error/skip,
preflight and owner exits zero, `owner_test_executed=true` and
`evidence_validated=true`. These are maintainer-executed results; the agent has
not independently inspected a transferred raw report archive.

The saved summary confirms positive production acceptance and guarded open, an
actual distinct-account filesystem owner transition, exact original DACL
restoration through retained custody, production handle-bound and guarded-open
owner refusals, full native identity across both refusals, original bytes and
the exact protected DACL. The separate verification read changed access time;
that observation is recorded explicitly and does not relax the complete identity
comparison around either production refusal. Both accounts remained standard;
no privileges, policy, production checks or timestamps were changed.

The executed 176-file fix04 snapshot is identified by manifest SHA-256
`f4a3c85268e2461e735fbe8572ced8036913ff3f43b69e3dffa7708360f8a5d7`,
source-list digest `23ef679b36e56df3ec1bf187d9a17e80435095c8739f4d17f20ef18da1973d30`
(SHA-256 of manifest-order UTF-8 `sha256  path\n` lines), and mandatory test SHA-256
`8ea86d46c1c6be3fe49b3d090e95849c37a0df83fabe3752c48b367901cbce23`.
The snapshot includes uncommitted work based on `d4bca46`; it is not an exact
committed candidate. Subsequent documentation records this result without
relabeling the frozen snapshot or regenerating its manifest.

Preserve private A/B attempt-04 reports, the original failed attempts and their
synthetic artifacts. The runner deliberately records
`qualification_scope_approved=false` and scope
`one VM owner case; no matrix or production qualification`. Actual owner evidence
was awaiting acceptance when these reports were generated. The separate
16 October maintainer decision below accepts only this recorded ARM combination.
Preserve the reports and frozen source unchanged; their original approval flag
is historical, not a reason to rewrite or rerun successful evidence. No broader
Windows qualification follows.

## Environment verification before testing

The live guest About page reports a **64-bit operating system, ARM-based
processor**, corroborated by the maintainer's actual CIM architecture code `12`,
with 4 GB RAM and 64 GB virtual storage. UTM About confirms **4.7.5 (118)**;
its library identifies **ARM64/aarch64**, QEMU 10.0 ARM `virt-10.0`.
Hardware acceleration versus full emulation remains unverified. The supplied screenshot
reports Windows 11 Home, version 26H2, build 26300.9457; that build has not yet
been independently remeasured by the API probe. Python/process architecture,
account membership and production fixture-volume capabilities still require
verification. The maintainer's actual `Get-Volume` output reports NTFS, Fixed,
and 33,357,565,952 free bytes. Command discovery reports Git and Poetry absent;
`python --version` returns the Store-installation-alias message and `py` is
unrecognized: no working Python interpreter had been found at initial handoff.
The provisioning continuation below supersedes those initial tool observations.
These observations
do not replace the production opened-volume guard. Do not infer the release channel or
support eligibility from the displayed version alone.

The computer-use connection can inspect the guest, but command input dropped
characters in the initial attempts. Malformed input was cleared without executing
it; no owner test or owner/ACL change ran. A final persistent-clipboard trial
also failed to insert a harmless marker. Execution is handed to the maintainer
using direct guest paste. A successful keystroke tool response is not proof
that a command executed correctly.

### Maintainer-executed provisioning continuation — 15 October

Account A installed checksum-verified CPython 3.13.16 ARM64 per-user without an
administrator prompt, launcher, persistent PATH change or long-path policy
change. It created an isolated per-user Poetry 2.5.1 environment and selected
a project virtualenv. A session-only Python PATH prefix was required before
Poetry's environment selection; its initial Store-alias failure is preserved
as a setup failure. The maintainer reported successful locked development
installation and strict lock validation. The first module probe could not import
the project; an explicit `poetry install --only-root --no-interaction` completed
successfully and resolved that import failure. These are provisioning results,
not installed-artifact qualification.

The three PowerShell helpers passed the actual guest parser. The read-only
PowerShell readiness probe ran successfully: Windows 11 Home `10.0.26300`,
native machine `0xAA64`, process `0x0000`, 64-bit PowerShell `5.1.26100.9457`,
no elevation or Administrators membership, approved test account, fixed NTFS.
The standalone actual Python probe independently reported 64 bits, process
`0x0000`, native machine `0xAA64`. The displayed full OS revision/channel and
UTM acceleration remain separately unestablished.

The subsequent A account probe failed before any fixture or ACL mutation:
the test harness passed the entire 68-byte SID buffer capacity to the exact
production SID parser. [LookupAccountNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lookupaccountnamew)
does not guarantee replacing that capacity with the actual length on success.
The corrected test-only resolver first calls `IsValidSid`, then `GetLengthSid`,
requires the result within the allocated buffer, and retains the unchanged exact
production SID parser. Portable regressions cover both reported-capacity
behaviors, both account names, invalid SIDs and out-of-bounds lengths. The native
probe failure remains a failure; corrected native execution is pending.

A fresh `fix01` source archive/candidate preserves the first archive, candidate
and virtualenv. Do not overwrite the old source or retry its uncorrected helper.
Record the new archive and manifest hashes with new private execution reports.
Account B provisioning/probes and actual owner proof remain unexecuted.

### First native ARM64 owner attempt and synchronous-open correction

Subsequent maintainer execution completed both designated standard-account
preflights on native ARM64 CPython 3.13.16, 64 bits, process `0x0000` / native
`0xAA64`, build 26300. Their four source hashes matched the reviewed `fix01`
archive. B's fresh private preflight reports were prepared. A collected the exact
original owner node: **1 test collected**, without execution at that stage.

Two actual locked development installs in A then failed building
`cryptography==50.0.2`: the lock and published release have no Windows ARM64
wheel, and source compilation could not find `link.exe`. The build backend
reported user-cache Rust/toolchain activity during those failed attempts;
preserve those artifacts and do not retry unchanged builds or install compilers.
The environment is partial. Earlier reported install success and successful
root-only project installation do not establish complete application dependency
or artifact qualification. The owner case imports stdlib/private native helpers
and pytest; its bounded execution does not waive the broader installation gate.

The actual original owner node under `fix01` failed: **1 failed in 0.14s**,
with `NTSTATUS 0xC000000D` / I/O `0x00000000` while acquiring A's retained leaf
handle. Source/control-flow review shows it created a fresh synthetic directory
and `KEEP` file but did not reach temporary B-grant installation or any owner
setter. Preserve the new fixture and A's `obfuscidian-29-owner-a-01` reports;
no cleanup, owner transition or preservation success is inferred from failure.

The test opener requested synchronous I/O without an explicit `SYNCHRONIZE`
access bit. The [NtCreateFile contract](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
requires that bit. The `fix02` correction adds it at the private test-helper call
only; production already requests it explicitly and remains unchanged. Injected
call-contract regressions exercise the real opener for A and B, including pinned
relative roots/names, full-width handles, exact options and compatible sharing.
The regression failed for A before the correction and passed afterward; this
is portable contract evidence, not corrected native owner proof. New selected
local checks: **52 passed, 30 native Windows tests skipped**. Keep the earlier
50/30 and 43/30 targeted results and initial 1600/149 full result separate.

Apply only a reviewed checksummed source continuation with a preserved backup;
do not recreate environments, overwrite failed reports or edit the fixture.
The new helper/source manifest must be recorded with fresh A/B reports before
another native attempt. Corrected native execution, B's owner transition and
the full actual-owner safety proof remain pending. All production gates and
architecture/matrix/artifact criteria remain unchanged.

### Second native ARM64 attempt and exact descriptor-control continuation

After a UTM RPC/startup hang, stopping the VM and restarting UTM restored guest
startup. Windows completed a startup update and both accounts signed in again.
The maintainer verified the preserved source/report presence, the original
manifest and fix02 updater checksums, then completed the reviewed source-only
update with its preserved original-source backup. Both fresh account preflights
matched the fix02 hashes, CPython 3.13.16, process `0x0000` / native `0xAA64`,
64 bits and build 26300. No full revision/channel or acceleration claim follows.

The second original owner-node attempt **failed: 1 failed in 0.12s**. It passed
the retained leaf open, positive production private/guarded-open checks and
original byte read. `SetSecurityInfo` returned success for the temporary directory
DACL, but exact descriptor readback failed; cleanup also refused that unrecognized
state. The leaf grant and B owner setter were never reached. Keep both failed
fixtures and each attempt's private reports; never reuse or repair them.

A subsequent read-only directory observation found protected control `0x9004`
and one full-access inheritable ACE on the earlier fixture, versus protected
control `0x9404` and the intended two-ACE mask/flag shape on the second fixture.
The difference is `SE_DACL_AUTO_INHERITED` (`0x0400`). That shape summary is not
raw DACL-byte equality, an owner-transition result or final preservation proof.
Microsoft documents that [SetSecurityInfo imposes the current inheritance model](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces)
and can set this bit. It cannot serve as an assumed exact-control round trip.

The reviewed fix03 candidate changes only the private fixture DACL setter to
[NtSetSecurityObject](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntsetsecurityobject),
with a validated bounded self-relative descriptor containing the exact requested
protected control and original ACL bytes. It selects only `DACL_SECURITY_INFORMATION`
on the retained full-width handle, without owner/group/SACL writes, privileges,
path-based repair or inheritance propagation. Each caller explicitly passes the
original control; supported protected `0x9004` and `0x9404` states remain distinct.
All existing exact readbacks and unknown-state refusal/retention remain unchanged.
B's owner setter and all production code are unchanged. No control bit is masked
out, no changed baseline is adopted, and no earlier failed fixture is repaired.

Portable call-contract, validation/refusal and custody/cleanup checks passed
**64 tests, with 30 native Windows tests skipped**. These are injected/portable
tests, not proof that the corrected setter round-trips on Windows. Fix03 native
execution and actual owner proof remain pending. Transfer only the reviewed
checksummed source continuation, preserve its backup, and use new A/B reports.

### Third native ARM64 attempt: actual transition, then observation-time failure

The maintainer verified and applied fix03, then both standard-account preflights
matched its reviewed helper hash and unchanged production sources. A reached the
interactive handoff; B's exact-identity peer command completed with exit zero,
`peer_owner_setter_completed=true`, native ARM64 CPython 3.13.16 / build 26300,
and matching source hashes. A then accepted the requested `OWNER-CHANGED` input.
The long case duration includes the manual session-switch/input wait; it does
not establish prolonged computation or an input error.

The third original-node execution **failed: 1 failed in 11280.55s (3:08:00)**.
The supplied traceback shows that the actual distinct-owner transition, exact
original DACL/control restoration, bytes, full object identity and both production
owner refusals passed their assertions. The first complete `_Identity` comparison
after the refusals also passed. A subsequent test byte-verification read returned
`KEEP`, but the following complete identity comparison failed with only `accessed`
different; the other nine fields were identical. Neither the supplied trace nor
the peer success makes the complete case a pass. Final evidence properties and
runner validation were not reached. Keep this failure separate from the two
earlier setup failures and preserve all three fixtures/report sets.

Windows [documents that reads can update last-access time](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfiletime).
The verification read between the two strict identity comparisons is a plausible
observer effect, not yet a separately isolated causal experiment. Do not classify
this as a production owner-acceptance defect or silently ignore the timestamp.
Read-only JUnit/property inspection and review of the measurement boundary are
next. No timestamp rewrite, weakened identity check, fixture reuse or automatic
permission repair is authorized by this failure. Full native owner proof remains
unmet; ARM acceptance and all production qualification gates remain unchanged.

The maintainer's saved JUnit/status summary independently records positive
guarded-open/setup, exact original DACL restoration and actual transition as
`True`, with preflight exit 0, owner exit 1, execution true, validation false and
scope approval false. The final full-identity property is absent because the
case failed before it was recorded. Preserve that distinction.

### Reviewed fix04 measurement boundary — preparation record before execution

The fix04 candidate keeps the original mandatory node, every original assertion
expression, the same actual two-account owner change and all production checks.
It places both original complete-identity equality checks after the production
refusals and descriptor readback, before the subsequent verification read. A
third complete snapshot equality explicitly includes access/change time. The
matching full before/after identities and exact protected DACL are recorded for
that production-refusal interval; no identity field is omitted or normalized.

The real byte verification still executes afterward on the same retained handle.
The test requires original bytes, complete file ID/volume/kind and every other
metadata field to remain unchanged during that separate read. Its resulting full
identity and whether access time changed are recorded separately, rather than
claiming the observer read is part of the production refusal. There is no time
setter, per-handle time suppression, machine-policy change, adopted identity
baseline or permission repair. Both owner-refusal and final byte/DACL assertions
must pass before the mandatory success properties are emitted. The original
outside-custody byte check remains too. This is a test measurement correction,
not a production exception or a waiver of complete identity across refusals.

Portable regressions execute the actual mandatory test function with an explicit
injected observation model. They reproduce the old post-read access mismatch,
then check that every one of the ten identity fields changed during either
refusal still fails, that changed bytes fail, and that all nine non-access
identity fields changed during the verification read fail. The selected result
is **95 passed / 30 native Windows skipped**, distinct from prior 64/30, 52/30,
50/30 and 43/30 local selections and all three actual failed Windows attempts.
These models neither execute a native owner transition nor replace that proof.

Transfer fix04 only with its checked full manifest and backup-first source
updater. Preserve all old reports/fixtures and use fresh A/B `-04` reports. The
VM helper's four probe hashes are unchanged; the changed mandatory test and
regression module are additionally bound by the full 176-file manifest and
runner source report. This preparation record preceded the passing execution
recorded above; ARM acceptance and the remaining qualification criteria are still
pending. Earlier pending statements in the chronological preparation history
describe their respective candidates, not the current fix04 result.

In **each** account, open PowerShell normally. For an initial read-only check:

```powershell
Get-CimInstance Win32_Processor | Select-Object Architecture
Get-Volume -DriveLetter C | Select-Object FileSystem,DriveType,SizeRemaining
Get-Command python,py,git,poetry -ErrorAction SilentlyContinue | Select-Object Name
```

After transferring the reviewed source onto internal guest storage, run the
[read-only VM probe](../../.github/scripts/get_windows_vm_environment.ps1)
from the candidate root. Where the existing policy permits scripts:

```powershell
& .\.github\scripts\get_windows_vm_environment.ps1
```

If scripts are blocked, use reviewed source text without changing policy:

```powershell
$VmProbe = Get-Content -LiteralPath '.\.github\scripts\get_windows_vm_environment.ps1' -Raw
& ([ScriptBlock]::Create($VmProbe))
```

Keep output private. This probe records `IsWow64Process2` native/process machine
codes, CIM processor architecture, build, current token administrator observations,
storage observations and command availability. It does not create a fixture,
establish production storage eligibility, determine UTM's host-side backend,
or qualify Python. Run the same native/process probe inside the selected Python
process before testing; the PowerShell process result cannot establish Python's
architecture. Require a standard account and unelevated token in both sessions.

Microsoft documents the separate native/process outputs of
[IsWow64Process2](https://learn.microsoft.com/en-us/windows/win32/api/wow64apiset/nf-wow64apiset-iswow64process2).
An emulated AMD64 process on an ARM64 guest remains ARM Windows evidence.

## Implemented fixture protocol for review

`tests/_windows_owner_vm.py` implements the following source-test protocol.
Portable tests cover architecture/path refusal, restricted grant masks,
pointer-width-safe DACL setter binding, filtered-admin rejection, isolated peer
bootstrap and injected interruption/grant restoration. These are portable or
injected tests; only actual Windows execution can establish native behavior.

Retain the original mandatory test node and every safety assertion:
`tests/integration/test_windows_native.py::test_changed_native_owner_refused_without_privilege_activation`.
Its existing group strategy remains available. The two-account strategy must be
an explicit synthetic test arrangement, never a production bypass or a passing
setup-only report.

1. Account A verifies its expected local identity, Account B's distinct local
   SID, both ordinary-token requirements, supported CPython and actual native/
   process architectures. Guard the proposed parent on internal fixed NTFS,
   with persistent ACLs and the complete production ancestor/namespace checks.
   Create a fresh uniquely named fixture only; refuse preexisting/reparse/aliased
   storage. Do not inspect or change unrelated Public/profile content.
2. Create the synthetic file through production private creation. Write fixed
   binary bytes, close the creation handle, and reacquire an A-owned retained
   handle with read, read-control and **WRITE_DAC** rights and compatible sharing.
   Require positive `_Handle._private()` and guarded-open acceptance before
   granting B any rights. Record original full `_Identity`, bytes, owner SID,
   complete descriptor control and exact protected DACL bytes.
3. On that new fixture only, grant B parent traverse/attribute/read-control
   access and leaf ownership/attribute/read-control access. Grant no file-data
   write, delete or DACL-write access to B. Preserve A's complete original grant;
   use explicit protected, noninheriting grants. Record this intentional setup
   state separately from the later refusal state. Never change a profile,
   system directory or existing parent DACL.
4. Keep A's process, native file handle and ancestor guards alive. **Switch user**
   to B rather than signing A out. B opens only the designated file with the
   reviewed minimum rights, validates the expected full volume/file identity,
   current A owner and exact temporary ACL, then calls handle-bound
   `SetSecurityInfo(OWNER_SECURITY_INFORMATION)` to take ownership as B itself.
   Assert the actual owner is now B, identities/bytes remain protected as
   applicable, and the setter did not change the temporary DACL. Close B's
   handle and exit successfully before resuming A. No credential API, privileged
   token, general ownership tool or arbitrary target path is accepted.
5. Switch back to A. Observe the actual B owner through A's retained handle.
   Restore the saved **exact original protected DACL** through that already-held
   WRITE_DAC handle, without restoring the owner or reopening for repair.
   Confirm full volume/128-bit file identity, kind, size, links, attributes,
   creation/write times and original bytes. Windows change/access times may
   change during intentional security setup; observe them without rewriting.
6. Capture the complete changed-owner baseline after setup. Require production
   handle-bound owner refusal and production `_Guard._open_file` refusal for
   the changed owner. Require full `_Identity` equality across refusal,
   unchanged original bytes, B owner, descriptor control and exact original
   protected DACL. Setup failure, access denial before the positive control,
   SID mismatch, sharing failure or absent B participation is a failure.
7. Record private source identity/hashes, actual environments, commands, exits,
   individual results and all positive/transition/refusal/preservation properties.
   Restore temporary grants using retained custody on failure where proven safe;
   retain uncertain synthetic artifacts and report failure. Do not recursively
   delete, repair unknown data or claim a pass after cleanup fails.

[SetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setsecurityinfo)
operates on the supplied handle. The design deliberately obtains A's DACL-write
rights before the transition; it does not assume an A reopen can repair a B-owned
file. The original owner-only DACL is the refusal baseline, not the temporary
two-account grant. No SACL query or privilege activation is needed.

The explicit pytest option is `--owner-vm-two-account`. Without it, the original
group strategy and unavailable-fixture failure remain selected. Neither strategy
skips or xfails the actual-owner obligation. The group preflight now additionally
requires actual native AMD64 machine/process evidence; an emulated process's
`platform.machine()` string cannot satisfy it. The VM helper records ARM results
as diagnostic evidence with acceptance pending. All production sources remain
unchanged. Current-chat model selection was verified as `GPT-6.1 Sol` from
the current turn metadata and confirmed directly by the maintainer before Python
headers were edited, using the local date 15 October 2026.

## Exact per-account execution handoff

**Reusable execution procedure; fix04 has passed as recorded above.** Review source changes before any new execution.
No signature/ABI/sharing behavior is claimed from portable tests. Never run the
old group-only helper expecting these accounts to pass its group preflight.

Transfer the reviewed source snapshot into a fresh directory on internal guest
NTFS, accessible for source reads in both accounts, for example
`C:\Users\Public\Documents\obfuscidian-29-candidate-fix01`. Copy only public candidate
source and its manifest; no host `local/`, Git credentials, real vaults or keys.
Verify the source archive SHA-256 against the handoff **before** executing it.
The candidate snapshot includes uncommitted changes; its source manifest and
file hashes, rather than base commit alone, identify what was tested.

Before invoking the helpers, parse the reviewed PowerShell scripts with the
actual guest PowerShell. This check creates no owner fixture:

```powershell
foreach ($VmScript in @('get_windows_vm_environment.ps1', 'check_windows_owner.ps1', 'check_windows_owner_vm.ps1')) {
    $VmTokens = $null
    $VmParseErrors = $null
    [void][Management.Automation.Language.Parser]::ParseFile(
        (Join-Path (Get-Location) ('.github/scripts/' + $VmScript)), [ref]$VmTokens, [ref]$VmParseErrors)
    if ($VmParseErrors.Count) { $VmParseErrors; throw 'PowerShell syntax check failed; do not execute.' }
}
```

Account A needs a supported 64-bit CPython, Poetry `>=2.2,<3`, and the
locked dev environment. Account B needs an existing supported 64-bit CPython;
the peer entry point runs with `-I -S`, loads this reviewed source explicitly,
and needs neither A's private virtualenv nor B's own Poetry/dependency install.
If tools are missing, stop and provision only the required user-level tooling
from official sources; never elevate a test or alter machine policy to proceed.
The actual interpreter/guest combination is established by each probe, not an
installer name or the availability of an application alias. Prefer native ARM64
Python deliberately for this ARM guest; emulated AMD64 remains a separate result.
If a native interpreter must be provisioned, Python.org currently provides
[CPython 3.13.16](https://www.python.org/downloads/release/python-31316/), including
an ARM64 installer explicitly marked **Experimental**. Treat that as an additional
toolchain limitation for these diagnostics. Use a just-for-me installation in
each account, retaining ordinary user rights; leave the all-users launcher,
machine PATH and long-path policy unchanged. Review installer terms directly.
The [Python installer documentation](https://docs.python.org/3.13/using/windows.html#installing-without-ui)
documents `InstallAllUsers=0`, `Include_launcher=0`, `PrependPath=0` and user-owned
target directories. No installer has been executed by this preparation.

For this currently interpreter-free VM, run the following in **each account's
ordinary PowerShell**, using direct paste. It downloads the official ARM64
installer, checks the published checksum, and opens its interactive UI. The
maintainer reviews and accepts the installer terms directly. Keep installation
per-user, the launcher unchecked and PATH unchanged; do not enable the optional
long-path policy or approve an elevation request. Stop if those choices cannot
be preserved. This is provisioning, not owner-test evidence.

```powershell
$OwnerPythonRoot = Join-Path $env:LOCALAPPDATA 'ObfuscidianOwner29\Python313'
$OwnerInstaller = Join-Path $env:TEMP 'obfuscidian-owner29-python-3.13.16-arm64.exe'
if ((Test-Path -LiteralPath $OwnerPythonRoot) -or (Test-Path -LiteralPath $OwnerInstaller)) {
    throw 'Review existing tooling or select fresh storage; do not overwrite it.'
}
Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.13.16/python-3.13.16-arm64.exe' -OutFile $OwnerInstaller
if ((Get-FileHash -LiteralPath $OwnerInstaller -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    '696e2226062c6ec3622c13f143d28336a856968518e49cb4f4c62513215a4f5d') {
    throw 'Installer checksum mismatch; do not execute.'
}
& $OwnerInstaller InstallAllUsers=0 Include_launcher=0 PrependPath=0 "TargetDir=$OwnerPythonRoot"
```

After the UI finishes successfully, in that same account's PowerShell:

```powershell
$OwnerPython = Join-Path $OwnerPythonRoot 'python.exe'
& $OwnerPython --version
if ($LASTEXITCODE -ne 0) { throw 'Interpreter provisioning failed.' }
$env:PATH = $OwnerPythonRoot + ';' + $env:PATH
```

That last assignment affects **only this PowerShell session and its children**,
so the exact printed `python` peer command uses the deliberate interpreter rather
than the Store alias. It changes no persistent user or machine PATH. In a new
session, set the same two path variables explicitly and repeat the version check
and session-only PATH assignment. The Python runtime probe still verifies the
actual native/process machine codes before any fixture mutation.

In **Account A**, ordinary PowerShell, from the fresh candidate root:

```powershell
Set-Location 'C:\Users\Public\Documents\obfuscidian-29-candidate-fix01'
$OwnerPython = & python -c 'import sys; assert sys.version_info[:2] == (3,13); print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'Select an existing supported interpreter first.' }
if ($env:VIRTUAL_ENV) { throw 'Use a fresh ordinary PowerShell without an activated environment.' }
$OwnerPoetry = Join-Path $env:LOCALAPPDATA 'obfuscidian-owner29-tools-01\Scripts\poetry.exe'
if (-not (Test-Path -LiteralPath $OwnerPoetry)) {
    $OwnerToolRoot = Join-Path $env:LOCALAPPDATA 'obfuscidian-owner29-tools-01'
    if (Test-Path -LiteralPath $OwnerToolRoot) { throw 'Choose fresh tool storage; do not overwrite an environment.' }
    & $OwnerPython -m venv $OwnerToolRoot
    if ($LASTEXITCODE -ne 0) { throw 'User-level tool environment creation failed.' }
    & (Join-Path $OwnerToolRoot 'Scripts\python.exe') -m pip install 'poetry>=2.2,<3'
    if ($LASTEXITCODE -ne 0) { throw 'Isolated Poetry installation failed.' }
    $OwnerPoetry = Join-Path $OwnerToolRoot 'Scripts\poetry.exe'
}
& $OwnerPoetry --version
& $OwnerPoetry env use $OwnerPython
if ($LASTEXITCODE -ne 0) { throw 'Interpreter selection failed.' }
& $OwnerPoetry install --with dev --without docs --no-interaction
if ($LASTEXITCODE -ne 0) { throw 'Locked development installation failed.' }
& $OwnerPoetry install --only-root --no-interaction
if ($LASTEXITCODE -ne 0) { throw 'Current project installation failed.' }
& $OwnerPoetry check --lock --strict
if ($LASTEXITCODE -ne 0) { throw 'Lock check failed.' }
& $OwnerPoetry run python -m tests._windows_owner_vm probe --account ObfOwnerA
if ($LASTEXITCODE -ne 0) { throw 'A preflight failed; do not run the owner test.' }
```

Use 12 or 14 consistently only when that supported interpreter was deliberately
selected. No dependency/version/lock change is authorized. A resolved `python`
command may be a Store installation alias rather than a usable interpreter;
stop if the command opens an installation prompt or fails. The optional Poetry
setup uses the documented [isolated installation](https://python-poetry.org/docs/#installing-manually)
approach in new user-owned storage, without activation, administrator rights,
machine/PATH policy changes or a project dependency/lock change. Git is optional
for this owner-only source snapshot; its absence remains a later Git qualification
prerequisite rather than a fabricated version result.

Before starting A's held test, **switch user** to B and prepare B's ordinary
PowerShell. In **Account B**:

```powershell
Set-Location 'C:\Users\Public\Documents\obfuscidian-29-candidate-fix01'
& python -I -S tests/_windows_owner_vm.py probe --account ObfOwnerB
if ($LASTEXITCODE -ne 0) { throw 'B preflight failed; do not start A or change ownership.' }
$PeerReports = Join-Path $env:TEMP 'obfuscidian-29-owner-b-01'
if (Test-Path -LiteralPath $PeerReports) { throw 'Choose a fresh B report directory.' }
New-Item -ItemType Directory -Path $PeerReports | Out-Null
& python -I -S tests/_windows_owner_vm.py probe --account ObfOwnerB |
    Tee-Object -FilePath (Join-Path $PeerReports 'account-b-preflight.json')
if ($LASTEXITCODE -ne 0) { throw 'B preflight failed.' }
```

Keep B's source-hash/runtime output private. It must match A's source hashes.
If using an explicit interpreter instead of `python`, use that same executable
for B's probe and peer command. B does not import an installed Obfuscidian build.

Switch back to **A**, retaining both sessions. Run the reviewed helper through
source text if the existing script policy blocks `.ps1` files:

```powershell
$VmOwnerPath = (Resolve-Path '.github/scripts/check_windows_owner_vm.ps1').Path
$VmOwnerDirectory = Split-Path -Parent $VmOwnerPath
$VmOwnerSource = Get-Content -LiteralPath $VmOwnerPath -Raw
$VmOwnerBlock = [ScriptBlock]::Create($VmOwnerSource.Replace('$PSScriptRoot', '$VmOwnerDirectory'))
& $VmOwnerBlock -ExpectedMinor 13 -Poetry $OwnerPoetry -ReportDirectory (Join-Path $env:TEMP 'obfuscidian-29-owner-a-01')
```

The test prints an exact B command containing the newly generated fixture path,
full volume ID and complete 128-bit file ID. Keep A's process and session alive.
Switch user to B, paste that **exact printed command** and append:

```powershell
| Tee-Object -FilePath (Join-Path $PeerReports 'peer-transition.json')
```

Put the pipe on the same command line. Immediately afterward, in B:

```powershell
$PeerExit = $LASTEXITCODE
@{ peer_exit = $PeerExit } | ConvertTo-Json |
    Set-Content -Encoding UTF8 (Join-Path $PeerReports 'peer-exit.json')
if ($PeerExit -ne 0) { throw 'B failed; retain reports and return to A without claiming success.' }
```

Only after B exits successfully, switch back to A and type `OWNER-CHANGED` at
the test's barrier. That marker is not a credential. A independently verifies
the real owner, restores the exact DACL through its retained handle, and runs
the shared production refusal/preservation assertions. Do not sign A out,
restart/suspend the VM, manually change owners, use `takeown`/`icacls`, or repeat
a failed run without reviewing the cause. On interruption, A attempts to restore
only recognized temporary grants using retained handles; an unexpected owner,
DACL or descriptor-control state is preserved and fails the fixture. It retains synthetic evidence
and never restores the owner or deletes uncertain artifacts. An abnormal A
termination can leave temporary fixture grants; report that state for review.

Return A and B reports privately. Require exactly the original passing owner
node with zero failure/error/skip/xfail, both actual distinct owner SIDs, positive
setup, guarded acceptance, retained-DACL restoration, both production owner
refusals, full before/after identity and exact original protected DACL/bytes.
Validate the helper's exit and JUnit properties; a peer setter or preflight pass
alone is insufficient. Any combination outside the bounded accepted fix04 result
still needs its own evidence and acceptance. Preserve both report directories and
every earlier failed total.

## Architecture acceptance-scope proposal

**Bounded owner-evidence scope accepted 16 October 2026; broader eligibility remains unchanged.**

| Environment | Evidence classification | Proposed use |
| --- | --- | --- |
| Native AMD64 guest / AMD64 CPython | Native AMD64 | Existing architecture target, subject to all other gates |
| ARM64 guest / native ARM64 CPython | Native ARM64 Windows | Fix04 owner evidence accepted only for its recorded combination; no broader support |
| ARM64 guest / emulated AMD64 CPython | AMD64 process emulation on ARM64 Windows | Separate compatibility diagnostic; never relabel as native AMD64 |
| Unknown native machine or conflicting probes | Unestablished | Stop before owner/ACL mutation |

Accepted decision: accept the passing fix04 fixture as evidence of the actual-owner
safety obligation **only on its recorded Windows 11 Home build 26300 / fixed NTFS /
native ARM64 CPython 3.13.16 combination**,
while retaining native AMD64 host/interpreter, storage, matrix and artifact
requirements for an AMD64 beta. Broader ARM support would require its own native
primitive/lifecycle/Git/interruption, Python and installed-artifact qualification.
This bounded evidence acceptance grants no such support.

Do not silently relax the existing AMD64 helper assertion or treat
`platform.machine()` as guest identification. A reviewed diagnostic runner may
label ARM evidence explicitly; the accepted fix04 scope does not authorize other
combinations. Existing hosted Windows failures remain failed.

## Remaining qualification sequence

**ARM-only target approved for qualification 16 October:** because no native AMD64 environment
is available, review the [separate narrowly scoped lab-beta path](windows-arm64-beta-qualification-plan.md).
Its scope and metadata-only audit are approved, with a 36/37 compatible locked
binary result and cryptography blocking provisioning. Later execution, dependency
changes and dispatch remain unapproved. It does not complete the original AMD64
sequence below or enable writes.

The independent preparation is ready for review: source-bound owner tooling,
generated-v1 exchange tooling, installed refusal checks, CI evidence collection,
the parent acceptance audit and the concrete
[installed CLI gate-order proposal](windows-cli-gate-proposal.md) are prepared.
The current owner pass does not authorize their gated production steps.

1. The bounded fix04 ARM owner-evidence decision above is accepted. The next
   executable gate is to identify an eligible native AMD64 Windows environment
   with an existing unelevated owner fixture, verify the actual guest/process,
   token, internal fixed NTFS and locked tooling, then execute the mandatory
   actual-owner case there. Do not create accounts or repeat known unavailable
   group setup. The accepted ARM case does not fill that target's matrix rows.
2. Complete the existing eligible native AMD64 host/storage/Python rows and full
   private primitive/checkpoint/lifecycle/Git/DACL/termination suites. Retain the
   Windows 11 / Server 2022-or-newer, local fixed persistent-ACL NTFS and 64-bit
   CPython 3.12–3.14 criteria, including Store interpreters where applicable;
   any narrower host or interpreter criteria need a separate proposal/approval.
   Preserve #27 retry5's six metadata cases and #28's 30 plus one separate passes
   as bounded evidence, rather than successful full diagnostic totals.
3. Execute both generated synthetic v1 exchange directions with the recorded
   candidate identity and verify bytes/layout without copying real data. Obtain
   the required nine-job exact-commit evidence only after separately authorized
   Git delivery and remote execution; existing elevated Windows failures stay
   failed. This session authorizes neither action.
4. Review the gate-order proposal after its prerequisites. Only separate
   authorization may move installed CLI write acceptance after scoped local
   production dispatch integration. Then qualify fresh wheel and sdist installs,
   outside the checkout, through actual console/module backup, restore,
   recovery and Git operations, including failures and interruptions. An installed
   private-function call or unchanged refusal smoke is not installed-write proof.
5. Repeat all required final checks at the exact approved commit. Review a
   narrowly scoped AMD64 Windows beta proposal covering fresh/merge backup,
   fresh restore, existing recovery and additive Git worktree restore only on
   qualified combinations. Public support copy and enabling each operation need
   separate acceptance. No beta support is claimed now.

ARM beta support is not proposed for enabling: the per-user ARM64 interpreter is
marked experimental, two locked development installs failed building cryptography
without the MSVC linker, and complete application/artifact qualification is absent.
Do not install compilers, change dependencies or substitute an emulated process
to hide that limitation. Broader ARM eligibility needs its own complete proposal
and qualification. The installed CLI gate-order decision remains unapproved.

Until those gates pass and the maintainer approves the concrete enabling/support
proposal, production Windows mutation/recovery remains refused. Existing-log
append refusal, POSIX behavior, CLI syntax, dependencies, Fernet/v1, retained
rollback and existing Git interruption/power-loss limits remain unchanged.
No CI dispatch, stage, commit, push, merge, PR, closure, release or publication is
part of this VM preparation.

## Review and local validation handoff

The initial candidate's local macOS ARM64 / CPython 3.12.7 suite passed **1,600 tests, with
149 skipped**. The focused owner-tooling/native-node selection passed **43,
with 30 native Windows tests skipped**. Portable and injected harness checks
exercise refusal and cleanup boundaries; neither result proves a filesystem
owner transition. Earlier intermediate local totals are not added to these.
Poetry lock validation, Ruff lint/format and production Bandit passed. Strict
Sphinx passed, and rendered local references passed across 42 HTML pages;
external URLs were not requested by that checker. A fresh standalone package
build/installation was not run. After the test-only SID lookup correction,
targeted checks passed **50 tests, with 30 native Windows tests skipped**;
this is portable/injected regression evidence, not corrected native execution
or a new full-suite total. After the subsequent synchronous-open correction,
targeted checks passed **52 tests, with 30 native Windows tests skipped**.

Source review checked retained handle sharing and pointer widths, exact original
descriptor control/DACL restoration, bounded token parsing, filtered-admin
refusal, UUID-only target confinement, unknown-state preservation, and mandatory
production acceptance/refusal assertions. All 14 distinct original owner-test
assertion expressions remain, with additional full-identity/evidence checks.
This is source review with portable regression coverage. The fourth actual
Windows owner invocation passed after the three distinct failures above.

The three separate failed native ARM64 owner attempts are recorded above. No installed
Windows write/recovery test, exchanged-v1 test, new Windows matrix or hosted CI
run was executed. The second attempt's unexpected directory-grant state remains
retained. The third attempt performed B's actual owner transition and passed both
production owner-refusal assertions, but failed the later identity comparison
after a verification read; it is not a complete passing owner case. The fourth
case independently passed and its saved evidence summary is recorded above.
No privilege activation, account creation, credential collection or policy change
occurred. Both account fix04 preflights passed with matching source hashes.
The build/channel and UTM acceleration questions remain private-environment
qualification work. The bounded ARM owner evidence is now accepted; native AMD64
qualification remains outstanding. Preserve raw reports privately for detailed
review; #17/#29 remain open and production remains gated.

After fix04, the complete local macOS ARM64 / CPython 3.12.7 regression run passed
**1,652 tests, with 149 skipped**, in 141.55s. This replaces no historical total;
the platform-specific skips remain unexecuted native evidence. Fresh lock
validation, repository-wide Ruff lint/format and production Bandit passed.
Strict fresh Sphinx passed after correcting two heading-level warnings in the
first post-proof documentation build; rendered local references passed across
42 HTML pages. External URL availability was not checked.
A fresh local wheel and sdist passed strict Twine checks and **three isolated
packaging tests**, including independent installations outside the checkout.
This is macOS packaging evidence, not an installed Windows write result. No
artifact was uploaded or published. The later documentation handoff is distinct
from the frozen, executed fix04 VM snapshot.

At the post-proof handoff, the preserved branch/HEAD was `feature/17-add-safe-native-windows-support` /
`d4bca46`; 10 tracked files were modified and five new files were untracked,
all then unstaged/uncommitted. No production, dependency or workflow file changed.

**16 October commit checkpoint:** the maintainer subsequently authorized staging,
committing and pushing the accumulated owner-proof and qualification/provenance
handoffs on this same branch, with references to #17/#29/#30. The frozen guest
snapshot and original reports retain their historical base and file identities;
they are not new exact-commit qualification results. A successor must inspect
the actual current HEAD and status rather than restore the old base or assume
the earlier uncommitted inventory still applies. Read-only #30 Stage 1 remains
the next authorized task; production Windows operations remain gated and AMD64
unqualified.

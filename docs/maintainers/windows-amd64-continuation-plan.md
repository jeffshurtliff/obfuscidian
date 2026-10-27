# Plan: practical AMD64 Windows qualification — #17 / #29

**17 October A3 execution checkpoint:** the maintainer accepted bounded A3.0–A3.5
preparation only. The [current checkpoint](windows-amd64-next-chat.md)
records the preserved newer host commit, exact 190-file source freeze, completed
two-account creation/configuration checks, A's ordinary Medium token and current
storage/DACL observations. A3 stops before runtime acquisition or task-directory
writes because the proposed Public Documents source parent fails permission
review. The maintainer conditionally accepted a fresh source sibling beneath A's
Local AppData; freshness, ancestor permissions and B access remain unverified.
This is not measured storage acceptance. No existing-parent permission repair,
tooling change, A4 execution, gate-order adoption, dispatch or support claim follows.
The dated A2/A1 text below remains historical and does not undo this bounded
authorization or turn incomplete preparation into qualification.

(amd64-a2-review)=
## A2 review proposal — 17 October 2026

**Delivered for concrete maintainer review; nothing in this section is execution
approval. Stop before A3 preparation and A4 owner execution.** This section takes
precedence over the dated planning/navigation below only as a new **proposal**.
The original #17/#29 criteria and CLI prerequisites remain in force until an
explicit revision is approved. Windows mutation/recovery and existing-log append
are still refused. POSIX, CLI syntax, Fernet/v1 and canonical dependencies are unchanged.

**Runtime-selection follow-up:** the maintainer selected **CPython 3.13.16 for
both ObfOwnerA and ObfOwnerB**. The proposed acquisition is the official PSF
per-user x64 installer pinned below. The [revision 2 catalogue](windows-amd64-a2-inputs-r2.json)
re-evaluates runtime, bootstrap and all project metadata for that exact patch;
the [3.13.14 A2 catalogue](windows-amd64-a2-inputs.json) and A1 evidence remain
unchanged historical records. This follow-up began with the three existing A2
tracked-document changes and original new catalogue preserved; the host refs
remain `9c2dd1b`. The [saved A3 kickoff](windows-amd64-next-chat.md) is ready
for a future chat after this proposal's documentation checks. No further A2
metadata task is needed; administrator availability, private paths, source
archive/manifest and acquired-byte trust checks are explicit A3 prerequisites,
not facts invented here. The current request approves no A3 setup or A4 work.

The original A2 starting tree/index were clean on
`feature/17-add-safe-native-windows-support`, HEAD/cached origin/read-only live
remote **9c2dd1b30b1fc9d5d975c65a9d4d0d10da8798fe**. Its A1 commit preserves
`64dcff07f1ad456fd0aa38f775c6bcf9a4c8f592`; #26 `2316457`, #27 `cbd30bb`,
and #28 `395454b` / `a92ab73` are ancestors. The laptop's clean tree/index and
`64dcff0` refs are **A1 measurements, not newly checked in A2**. Do not pull,
reset, replace or write over that checkout. Future source transfer uses a
separate fresh public-source snapshot, never that checkout as a destination.

Read A1's [readiness report](windows-amd64-readiness.md) and complete
[binary audit](windows-amd64-binary-audit.json) as measured evidence. A2 reads
live #17/#25–#30 and their discussions: #17 remains parent, #29 active/open,
#25–#28 implementation history. Their dated issue-body ARM/unavailable-AMD64
summaries are historical alongside the newer A1 comments. No body/checklist,
state, label, milestone or relationship is changed here. #30 acquisition/custom
building stays parked, including its unresolved Microsoft metadata pair.
Preserve the original ARM VM/frozen fix04 sources, reports, flags, failures and
**1 passed in 215.27s**; that is ARM-only owner evidence, never AMD64 evidence.

### Candidate purpose and operation/environment/refusal matrix

**Recommend a private synthetic-data engineering candidate first.** It would
establish whether the measured physical laptop can safely use a small native
Windows path. It authorizes no real-vault rehearsal or public distribution.
Personal engineering acceptance is not beta/stable support or #17 completion.
A later beta needs an explicitly accepted envelope, repeatable ordinary-user
evidence, installed artifacts, documentation and release authorization. Stable
2.0.0 additionally needs the approved final candidate gates, all outstanding
broad criteria or an explicit audited rescope, and the release runbook. Do not
infer Windows maturity from the unchanged project Production/Stable classifier.

| Operation | Proposed first candidate | Required refusal/preservation evidence |
| --- | --- | --- |
| `shroud fresh`, mirror absent | Eligible only after A4/A5 evidence and separate A6 integration approval | Recheck target absence and opened parent/volume at publication; refuse a late target, pending transaction, overlap or unsafe source; never replace an existing mirror |
| `verify`, no-write plans/previews | Retain current authenticated read-only contracts; proposal adds no storage write probe | Namespace/content snapshots prove no destination, log, lock, journal, rollback or worktree creation, including refusal paths |
| `unshroud fresh`, destination absent | Eligible after complete source authentication and the same A6 approval | Refuse every existing destination, including an empty directory; wrong key/corruption/missing objects/path collisions fail before output creation |
| Explicit recovery | Only a positively identified interrupted **eligible new-destination** operation | Bind operation kind, original target-absent baseline, source/key/plan, ownership, exact control chain, volume/identities and complete artifact reconciliation; uncertainty retains evidence and refuses inverse writes |
| Key/new-log creation | Existing exclusive private creation contract | No overwrite/key replacement; existing-log append stays refused; verification/previews still create no logs |
| Existing-mirror fresh replacement/update, merge/no-op write workflow; existing-destination replacement | Deferred; proposed Windows dispatch must refuse before workspace/lock/log mutation | Empty targets, `--yes`, non-interactive mode and no-op planning do not authorize deferred mutation; read-only planning retains its current contract |
| Git merge restore/worktree/publication | Deferred public Windows route; preserve private #28 implementation/history | No automatic branch/worktree/Git side effects from refused CLI routes; no new Git recovery semantics |
| Manual encrypted-mirror Git publication | Maintainer action after a completed, verified backup; outside application dispatch | Publish only the complete encrypted mirror after pending-state checks; keys/plaintext/reports/transaction workspaces stay outside its repository; no Git action in A2–A4 |

Bound recovery is an implementation requirement to review, **not an assertion
that current journals already prove initial absence**. If existing authenticated
control metadata cannot distinguish that baseline, refuse recovery and stop for
a reviewed internal-schema/compatibility design; never infer eligibility from a
currently missing target or a directory name. Preserve the POSIX v1 journal
reader and encrypted v1 format. Test interrupted recovery again, altered copies,
foreign owners/DACLs, unknown controls and competing recovery processes.

| Environment | Proposed disposition | Evidence boundary |
| --- | --- | --- |
| Windows 11 Home 25H2 / 26200.9711 observed in A1; proposed ordinary native AMD64 standard-GIL PSF CPython 3.13.16 in A/B; internal fixed NTFS | First synthetic candidate only; selected patch is not yet installed or observed | A1 measured the current Store **3.13.14** account, Medium token, administrator false/Administrators SID absent, native `0x8664` / process `0x0000`, PowerShell 5.1.26100.9711, Git 2.55.0.windows.5, Poetry 2.5.1. A/B and PSF 3.13.16 have not been measured |
| Every destination/workspace/control path | Opened native guard chain, persistent ACLs, non-read-only local fixed NTFS; same-volume publication; actual ordinary create/rename/delete/flush rights and private DACL enforcement | A1's writable-NTFS flags and about 326 GiB free are metadata, not storage/permission qualification or reserved capacity; no ancestor/parent ACL repair |
| Other Windows builds/editions; Server 2022+; CPython 3.12/3.14, other 3.13 patches; direct Store-derived invocation | Separate qualification rows, deferred for first candidate | Historical Store 3.13.14 subsets remain scoped evidence; PSF success would not newly qualify Store A/B access or all Store locations |
| ARM64/emulation/32-bit/free-threaded/unknown native process | Excluded from proposed AMD64 write dispatch | Test architecture/patch/operation eligibility explicitly; preserve ARM evidence without extending it |
| UNC/mapped network, removable-class, FAT/exFAT/ReFS, reparse/alias/unknown capabilities, unsafe or uncertain controls | Writes/recovery refused | Preserve existing read-only contracts; injected capability tests do not establish real unsupported-volume behavior. Fixed drive class alone proves neither nonremovable hardware nor sync exclusion |
| Linux/macOS | Existing behavior preserved | Final exact-candidate regression remains required; Windows scope reduction cannot waive POSIX regressions |

Repeated backup proposal: use a new dated absent mirror each time; document
copy-inclusive capacity, retained sensitive workspaces and manual retention.
No automatic pruning or incremental-Git convenience is promised. Encryption
does not hide object sizes/counts/change patterns or protect against endpoint/key
compromise or deletion; retain independent key/backup copies. Real data and cloud
publication need later authorization.

### Every broad acceptance obligation remains owned

| Original requirement | First-candidate treatment / retained owner |
| --- | --- |
| Actual AMD64 filesystem owner transition, positive setup, production refusals, full native identity/bytes/exact protected DACL | Mandatory A4 under #29; no substitute, skip, xfail or unchanged group retry |
| Native guards, substitution/reparse/link/alias safety, exclusive ownership, checkpoint bounds, actual kernel DACL enforcement, worker termination and conservative lifecycle/recovery | Mandatory applicable A5 proof before A6; shared safety cannot be deferred because the first operations are smaller |
| Fresh and merge backup, no-op/additive updates, replacement restore, existing-target recovery | Only absent-target fresh paths proposed now; retain existing-target/merge/replacement acceptance in #17/#29. No broad item marked done |
| Real Git restore, private worktrees/admin controls, index modes, branch collisions, ordinary cleanup, user edits/sharing and five worker-death/manual-inspection boundaries | #28 accepted private history remains intact; public/installed Git operation and final-source regression still owed under #17/#29; manual encrypted Git does not discharge it |
| Other Windows 11/Server builds, native 3.12–3.14, Store distribution, actual storage/8.3/refusal fixtures | Retain individual #29 rows and fixture limitations; one laptop/PSF patch cannot qualify them. No storage-policy or machine provisioning in this task |
| Generated v1 exchange Windows → POSIX and POSIX → Windows | Mandatory both directions at A5; generate independently on each source host, verify/restore exact bytes/directories on receiver with private synthetic key custody and unchanged input checks. Same-host five-pass tests or old fixed fixtures are insufficient |
| Installed wheel/sdist console **and** module write/recovery acceptance | Mandatory A6 after integration, using each fresh artifact independently outside checkout, isolated wheelhouse, import-location and `pip check` evidence; deferred merge/replacement/Git installed acceptance stays #29 |
| All nine exact-commit Linux/macOS/Windows × 3.12–3.14 jobs | Retain broad #29 criterion. Proposed engineering interim evidence is explicitly smaller, not its replacement. Final A7 needs the approved exact-candidate strategy; beta/stable rescope, if wanted, needs a recorded separate decision |
| Lock/style/security/coverage, fresh build/Twine, docs/reference validation, compatibility and public support guidance | Final exact-candidate A7/A8 gates; historical/local results are not current Windows acceptance. Retain power-loss/Git-interruption/log-append limits and consent/privacy guarantees |
| Full parent acceptance, merge/release/publication/issue closure | #17/#29 remain open. Future explicit rescope must map every deferred item to retained requirements or approved linked follow-ups before closure; open no issue or release in A2 |

Historical results remain in [qualification](windows-qualification.md),
[primitives](windows-primitive-validation.md), [lifecycle](windows-lifecycle-validation.md)
and [Git](windows-git-validation.md). In particular, r3 **907/1/596** and #27
retry4 **166/5** selected / **1027/5/596** full remain failed; retry5's six passes
are separate. #28 retry3 **54/2/17** scoped / **1086/2/613** full remain failed;
its separate corrected one-case pass plus 30 earlier native passes are bounded
private evidence, not a computed passing full suite. Preserve earlier failures
and all ARM source-install/setup/observation failures as well.

### Proposed gate-order revision and ordinary-user runner strategy

The [explicit CLI proposal revision](windows-cli-gate-proposal.md#a2-amd64-revision-proposal)
separates private qualification before dispatch from installed acceptance after
integration and final regression/CI/support acceptance. It proposes moving the
**final** all-nine-job gate later, not deleting it. Approving a proposal here
does not itself approve A6 dispatch or A7 remote execution.

1. **A3:** approved preparation only; accepted inputs/source identities and
   independent A/B ordinary sessions. No fixture/test runner invocation.
2. **A4:** separately approved original mandatory AMD64 owner node; accept only
   fresh complete positive/transition/refusal/preservation evidence.
3. **A5:** applicable private primitives/checkpoints/lifecycle/DACL/actual worker
   termination, full diagnostic with explicit two-account coordination, POSIX
   regressions and both generated v1 exchanges. Retain all counts/failures/skips;
   relevant native setup failures block the affected scope. Review shared Git
   safety dependencies; excluded public Git remains refused.
4. **Evidence review, then separate A6 implementation approval:** integrate only
   eligible absent-target operations and positively bound recovery. No public
   bypass. Keep current gates until that approval and preceding proof.
5. **A6 installed acceptance:** fresh wheel and sdist, each console/module,
   actual new-destination writes, verify/previews, consent, wrong-key/tamper
   refusals, opened-output/control/plaintext DACL checks, real worker death and
   production recovery, excluded-operation and existing-log append refusal.
6. **A7/A8:** approved final exact source/commit/artifact regression, CI and
   support gates, then explicit candidate-purpose decision. A source repair or
   routing change requires affected proof to be refreshed at the final identity.
   A9 release preparation/publication remains separate.

Live read of existing [run 38571560642](https://github.com/jeffshurtliff/obfuscidian/actions/runs/38571560642)
still shows **six POSIX successes, three Windows failures**. Its Windows Server
2025 elevated-token results at `7a7250e` remain failed: each records
**1098 passed / 3 failed / 31 errors / 585 skipped**; isolated artifact step
skipped. A2 does not reinterpret elevation or rerun those jobs.

For the initial local row, use maintainer-operated A/B interactive sessions on
the physical laptop, with actual native process/token/opened-storage facts and
private reports. It is **not a public-PR self-hosted runner**. For automation,
review later a dedicated disposable x64 Windows runner with preprovisioned
standard accounts, pinned image/interpreters, eligible NTFS, bounded source
allowlist, no secrets and trusted exact-source jobs only. An elevated controller
may provision a disposable machine only with separate approval; the test child
must actually have a standard Medium token with no Administrators SID. Verify
that token inside the tested Python; dropping a shell label or using a filtered
administrator token is insufficient. Keep provisioning separate from tests.

The interactive owner barrier cannot become unattended CI by omitting B or
stdin. A later reviewed controller must coordinate two independent ordinary
sessions, exact peer identity/source and retained A custody with bounded waits,
or keep that row blocked. No password injection, privilege enabling, automatic
logon or policy workaround is proposed. Preserve current required checks; any
workflow/check replacement needs its own review. A Server runner does not replace
Windows 11 evidence, and a laptop 3.13 pass cannot replace three Windows jobs.

### Frozen proposed tooling inputs, with metadata evidence only

Use the [revision 2 A2 input catalogue](windows-amd64-a2-inputs-r2.json). It is an immutable
review input, **not a second project lock** or acquisition authority. Versions
and exact official URLs/hashes for all **44** bootstrap wheels are enumerated;
their declared total is **14,214,048 bytes**, before installation/caches.
The closure is Poetry **2.5.1** plus pip **26.2.1**, for standard CPython
3.13.16/native AMD64 Windows. Selected wheel tags, non-yanked status, release/
Simple hash agreement, exact sidecar hashes and all active dependencies/extras
were freshly checked for 3.13.16. There are **311 metadata receipts**: 310 GET
bodies and one installer HEAD with zero body bytes read; zero payload bodies/imports.
The 44 exact package versions/wheels from revision 1 remain compatible; their
sidecar bytes are unchanged and every active constraint/extra was re-evaluated
for 3.13.16. No unrelated bootstrap upgrade or moving “latest” resolution.

Both A and B: propose **official PSF full per-user CPython 3.13.16 x64**, standard
GIL, separate private roots. Installer:
`https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe`, published
SHA-256 `fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b`.
[Official release metadata](https://www.python.org/downloads/release/python-31316/)
lists 28.5 MB (rounded), checksum and signature references; an official HEAD
declares **29,935,584 bytes**, reading zero executable-body bytes. Neither that
length declaration nor the checksum establishes acquired-byte integrity,
Authenticode trust, account access, installation or native execution. The
runtime version decision is settled; any later target change needs a fresh audit.

Existing Store use remains valid historical evidence, not rejected as defective:
A1 binds the current account's package process image (3.13.3824.0 package /
CPython 3.13.14) while `sys.executable` is an alias. It establishes no registration
or executable access in A/B. This proposal now pins separate PSF 3.13.16 runtimes;
do not substitute the Store alias or change the working Store account. A later
Store route would require a new per-account registration/access/process-image
review. No Store registration/acquisition or alias disabling is approved.

For the selected patch/distribution change, A2 freshly rechecked **all 59 exact A1
wheels** (including optional docs) through release/Simple/selected sidecar
metadata: freshly modelled **45** standard CPython 3.13 AMD64 tags are unchanged,
but `implementation_version` and `python_full_version` are now **3.13.16**.
Re-evaluated all 61 lock entries' Python/group markers, exact selected wheels'
Python constraints, every applicable project/build root and all active dependency
edges/extras. The resulting profiles are **7/37/59**, with no dependency gaps;
Linux-only `jeepney`/`secretstorage` remain excluded. All selected wheel hashes,
sizes and non-yanked status agree, and all selected sidecar bytes match A1.
These are new 3.13.16 metadata results, not reused 3.13.14 closure claims or
installation/native qualification. Preserve
the original A1 catalogue and its first incomplete metadata-parser report.

Poetry bootstrap uses the [officially documented isolated manual venv method](https://python-poetry.org/docs/#installation),
with exact wheels in a separate tools environment. **No
`install.python-poetry.org` script is selected or acquired**, so no moving script
hash or unaudited installer dependency resolution is hidden in the proposal.
The PSF runtime's bundled `venv`/`ensurepip` is the initial bootstrap; replace its
pip with the pinned wheel before installing the other tools offline. B needs
only its own stdlib runtime/shared public source, no Poetry/project dependencies.
Keep project backend poetry-core 2.5.0 and the entire canonical lock unchanged.

### Exact proposed A3 actions and commands — do not execute in A2

Each numbered boundary needs explicit named approval before execution. Run one
reviewed PowerShell command/block at a time and wait for its result; reconstruct
session-local variables in each account/new session. Do not automatically paste
or run a saved install-and-test helper. Report raw paths/identities privately.

**A3.0 — maintainer decisions and source freeze.** Confirm administrator
availability, purpose and permission/write limits below; the runtime pin is now
PSF CPython 3.13.16 in both accounts. Snapshot the reviewed existing source for
A3 preparation. If a later tooling change is proposed, review its diff and freeze
a new snapshot separately before A4; A3 does not authorize that repair. Freeze exact host
candidate/dirty diff plus a sorted manifest of every public source file's relative
path, byte length and SHA-256, including `src`, tests/support/conftest, relevant
PowerShell/Python scripts, canonical inputs and required packaging docs. Record
archive and manifest SHA-256 separately; reject duplicates, absolute/traversal/
case-colliding paths, links, undeclared files and byte/line-ending changes on
extraction. Include A2 catalogues as review inputs; exclude `.git`, `local`,
environments/caches/reports, credentials, real keys/vaults and generated outputs.
Record original mandatory node/helper/native/constant hashes explicitly. A/B
verify identical complete manifests, not just the four helper-reported hashes.

No archive/manifest for a future candidate exists yet: `APPROVED_*` values below
are deliberate review inputs to fill from that future freeze, never invented
pins. Stop if they remain unresolved. This source-snapshot preparation/transfer
is itself A3 work requiring approval; do not overwrite the laptop checkout.

**A3.1 — trusted administrator creates only the two absent local accounts.**
Use a separate administrator session; the maintainer enters passwords directly
at the OS prompt. No transcript/screen capture/password paste to this chat.
Check only the exact names; if either exists, stop and review rather than modify
it. These commands are for the administrator, never the current standard user:

```powershell
Get-LocalUser -Name ObfOwnerA,ObfOwnerB -ErrorAction SilentlyContinue
# Only after confirming both absent and approving account creation:
net.exe user ObfOwnerA * /add /passwordreq:yes
if ($LASTEXITCODE -ne 0) { throw 'Account A creation failed; stop.' }
net.exe user ObfOwnerB * /add /passwordreq:yes
if ($LASTEXITCODE -ne 0) { throw 'Account B creation failed; preserve partial setup.' }
net.exe user ObfOwnerA
net.exe user ObfOwnerB
```

Verify each is enabled and only an ordinary local Users member, with no
Administrators membership; use localized group SIDs if necessary. Do not add
groups/rights, activate privileges, reset existing passwords or remove an
unexpected membership automatically. A provisioning mistake stops for review.
Sign out of the administrator session before ordinary setup. First sign-in
creates each profile; do not substitute the current account for A or rename the
reviewed helper's exact ObfOwnerA/ObfOwnerB identities.

**A3.2 — each account's ordinary PowerShell: fresh private storage and runtime.**
Before writing, recheck the actual selected account/token and approved root's
ancestor chain/volume metadata and DACL. Require Medium, effective administrator
false and Administrators SID absent; inspect only task-relevant identities.
No unchanged CIM CPU or assignable-owner-group query. Refuse sync/reparse/alias/
unexpected storage and existing roots. A1 free space is not a reservation.
Budget initially **5 GiB per account** for preparation, plus **10 GiB** shared
source/wheel inputs; recheck actual space before later synthetic lifecycle work
with copy-inclusive estimates. Stop rather than delete old data to meet a budget.

```powershell
$A3ExpectedAccount = 'ObfOwnerA' # Use ObfOwnerB in B's ordinary session.
$A3Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$A3Principal = [Security.Principal.WindowsPrincipal]::new($A3Identity)
if ($A3Identity.Name -ine "$env:COMPUTERNAME\$A3ExpectedAccount" -or
    $A3Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or
    @($A3Identity.Groups | Where-Object Value -eq 'S-1-5-32-544').Count -ne 0) { throw 'Ordinary designated account required.' }
whoami.exe /groups /fo csv
# Privately verify Medium integrity before proceeding; do not paste raw identity/group output.
$A3Root = Join-Path $env:LOCALAPPDATA 'Obf29Amd64\attempt-01'
if (Test-Path -LiteralPath $A3Root) { throw 'Choose reviewed fresh storage; preserve existing data.' }
New-Item -ItemType Directory -Path $A3Root | Out-Null
foreach ($A3Child in @('inputs','reports','work','envs','cache','config','data')) {
    New-Item -ItemType Directory -Path (Join-Path $A3Root $A3Child) | Out-Null
}
$A3PythonRoot = Join-Path $A3Root 'Python313'
$A3Installer = Join-Path $A3Root 'inputs\python-3.13.16-amd64.exe'
Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe' -OutFile $A3Installer
if ((Get-FileHash -LiteralPath $A3Installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    'fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b' -or
    (Get-Item -LiteralPath $A3Installer).Length -ne 29935584) { throw 'Installer hash/length mismatch.' }
Get-AuthenticodeSignature -LiteralPath $A3Installer
```

Acquisition stops here for private hash/actual-length/signature review. Require
valid Authenticode and expected Python Software Foundation publisher; a checksum
alone does not validate signer identity. If validation is unavailable/invalid or
the metadata differs, retain the file and stop, never bypass trust. After named
installer execution approval and direct license review, use interactive UI:

```powershell
$A3Install = Start-Process -FilePath $A3Installer -Wait -PassThru -ArgumentList @(
    'InstallAllUsers=0','Include_launcher=0','InstallLauncherAllUsers=0',
    'PrependPath=0','AppendPath=0','AssociateFiles=0','Shortcuts=0',
    'Include_test=0','Include_doc=0','Include_tcltk=0','Include_debug=0',
    'Include_symbols=0','Include_freethreaded=0','Include_pip=1',
    ('TargetDir="' + $A3PythonRoot + '"'))
if ($A3Install.ExitCode -ne 0) { throw 'Installer did not finish successfully; do not retry or reboot automatically.' }
$A3Python = Join-Path $A3PythonRoot 'python.exe'
```

The following proposed read-only probe uses stdin to avoid A1's PowerShell 5.1
`-c` quoting failure. Set the expected account to **ObfOwnerB in B's session**;
never reuse A's private executable/path. It queries only the actual current
process/token, without CPU/group-fixture queries, source imports or writes:

```powershell
$A3ExpectedAccount = 'ObfOwnerA'
$A3Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($A3Identity.Name -ine "$env:COMPUTERNAME\$A3ExpectedAccount" -or
    @($A3Identity.Groups | Where-Object Value -eq 'S-1-5-32-544').Count -ne 0) {
    throw 'Wrong local account or Administrators SID present.'
}
@'
import ctypes as c
from ctypes import wintypes as w
import hashlib, json, struct, sys, sysconfig
assert sys.implementation.name == 'cpython' and sys.version_info[:3] == (3, 13, 16)
assert struct.calcsize('P') == 8 and not sysconfig.get_config_var('Py_GIL_DISABLED')
k = c.WinDLL('kernel32', use_last_error=True)
a = c.WinDLL('advapi32', use_last_error=True)
k.GetCurrentProcess.argtypes, k.GetCurrentProcess.restype = [], w.HANDLE
k.IsWow64Process2.argtypes = [w.HANDLE, c.POINTER(w.WORD), c.POINTER(w.WORD)]
k.IsWow64Process2.restype = w.BOOL
k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
k.QueryFullProcessImageNameW.restype = w.BOOL
k.CloseHandle.argtypes, k.CloseHandle.restype = [w.HANDLE], w.BOOL
a.OpenProcessToken.argtypes, a.OpenProcessToken.restype = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL
a.GetTokenInformation.argtypes = [w.HANDLE, w.DWORD, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
a.GetTokenInformation.restype = w.BOOL
process, native = w.WORD(), w.WORD()
handle = k.GetCurrentProcess()
assert k.IsWow64Process2(handle, c.byref(process), c.byref(native))
assert (process.value, native.value) == (0, 0x8664)
image, length = c.create_unicode_buffer(32768), w.DWORD(32768)
assert k.QueryFullProcessImageNameW(handle, 0, image, c.byref(length))
token, needed = w.HANDLE(), w.DWORD()
assert a.OpenProcessToken(handle, 8, c.byref(token))  # TOKEN_QUERY only
try:
    elevated = w.DWORD()
    assert a.GetTokenInformation(token, 20, c.byref(elevated), c.sizeof(elevated), c.byref(needed))
    assert elevated.value == 0
    a.GetTokenInformation(token, 25, None, 0, c.byref(needed))
    assert 8 <= needed.value <= 65536
    storage = c.create_string_buffer(needed.value)
    assert a.GetTokenInformation(token, 25, storage, len(storage), c.byref(needed))
    start = c.addressof(storage)
    sid = c.c_void_p.from_buffer(storage).value
    assert sid is not None and start <= sid <= start + len(storage) - 8
    revision, count = c.string_at(sid, 2)
    assert revision == 1 and 1 <= count <= 15 and sid + 8 + 4 * count <= start + len(storage)
    assert c.string_at(sid + 2, 6) == b'\x00\x00\x00\x00\x00\x10'
    integrity = int.from_bytes(c.string_at(sid + 8 + 4 * (count - 1), 4), 'little')
    assert integrity == 0x2000  # Medium, not Medium Plus/high/system
finally:
    assert k.CloseHandle(token)
with open(image.value, 'rb') as stream:
    image_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
print(json.dumps({'python': sys.version, 'image': image.value, 'image_sha256': image_hash,
    'process': process.value, 'native': native.value, 'elevated': False, 'integrity': 'Medium'}))
'@ | & $A3Python -I -B -
if ($LASTEXITCODE -ne 0) { throw 'Actual runtime/token/image probe failed.' }
```

Inspect selected executable Authenticode privately too. Never infer success
from partial stdout or a different PowerShell process's architecture. Refuse elevation,
machine prerequisites, restart, automatic update, launcher/PATH/association or
long-path-policy changes. The per-user installer may write its own HKCU
registration and temporary files; approve that specific scope, no machine policy.

**A3.3 — shared public source, separate from private work.** After source-freeze
review, A copies only the approved archive/input catalogues to a fresh approved
location; verify archive/manifest hash before extraction. Proposed source root:

```powershell
$A3Source = Join-Path $env:PUBLIC 'Documents\obfuscidian-29-amd64-candidate-01'
$A3Archive = Join-Path $A3Root 'inputs\approved-public-source.zip'
if (Test-Path -LiteralPath $A3Source) { throw 'Existing source destination; stop.' }
if ((Get-FileHash -LiteralPath $A3Archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    'APPROVED_ARCHIVE_SHA256') { throw 'Unaccepted source archive.' }
Expand-Archive -LiteralPath $A3Archive -DestinationPath $A3Source
```

Review archive member safety before extraction, using a bounded ZIP central
directory listing; `Expand-Archive` alone is not that review. Immediately verify
all extracted bytes/names against the accepted manifest. A must own source;
propose **only this newly created source tree** gets explicit A full-control /
B read-execute inheritable grants, with inheritance removed on the new root.
After separately approving that ACL change, in A's ordinary session:

```powershell
$A3AccountA = "$env:COMPUTERNAME\ObfOwnerA"
$A3AccountB = "$env:COMPUTERNAME\ObfOwnerB"
& icacls.exe $A3Source /inheritance:r /grant:r "${A3AccountA}:(OI)(CI)F" "${A3AccountB}:(OI)(CI)RX"
if ($LASTEXITCODE -ne 0) { throw 'New source-root access setup failed; stop.' }
```

Verify root/descendant DACLs and B read access/absence of write rights privately;
an exit zero alone is insufficient. Shared source is public, not a report/key
store. No parent/Public/profile/existing-source ACL change, recursive repair,
ownership takeover or grant to Everyone/Users is proposed. Hold source immutable
during A4/A5 and rehash in both sessions before execution; A's ability to edit
is not a claim against a malicious source owner. Tests/caches/coverage/reports
belong in A's approved private roots; B peer remains isolated stdlib-only.

**A3.4 — A's separate Poetry bootstrap, acquisition then offline install.**
Obtain the reviewed A2 catalogue from approved source transfer and verify its
separately recorded SHA-256 before trusting URLs/filenames. Refuse unknown
schema/count, non-HTTPS/nonofficial URLs, unsafe filename components and any
existing output. These commands consume only the exact reviewed 44 wheel rows:

```powershell
$A3PinsPath = Join-Path $A3Source 'docs\maintainers\windows-amd64-a2-inputs-r2.json'
if ((Get-FileHash -LiteralPath $A3PinsPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne
    '896c514996b6dedae97778272efa126b5bd9d6410e877b7fe63eda54aec5b7a3') { throw 'Unaccepted A2 catalogue bytes.' }
$A3Pins = Get-Content -Raw -LiteralPath $A3PinsPath | ConvertFrom-Json
if ($A3Pins.bootstrap.package_count -ne 44 -or @($A3Pins.bootstrap.packages).Count -ne 44) { throw 'Unexpected bootstrap closure.' }
$A3Tools = Join-Path $A3Root 'tools\poetry-2.5.1'
$A3ToolWheels = Join-Path $A3Root 'inputs\poetry-wheels'
if ((Test-Path -LiteralPath $A3Tools) -or (Test-Path -LiteralPath $A3ToolWheels)) { throw 'Bootstrap storage must be fresh.' }
New-Item -ItemType Directory -Path $A3ToolWheels | Out-Null
foreach ($A3Wheel in $A3Pins.bootstrap.packages) {
    if ($A3Wheel.filename -ne [IO.Path]::GetFileName($A3Wheel.filename) -or
        $A3Wheel.filename -notmatch '^[A-Za-z0-9_.+!-]+\.whl$' -or
        $A3Wheel.url -notmatch '^https://files\.pythonhosted\.org/packages/' -or
        $A3Wheel.sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Unaccepted bootstrap input.' }
    $A3File = Join-Path $A3ToolWheels $A3Wheel.filename
    if (Test-Path -LiteralPath $A3File) { throw 'Do not overwrite an acquired file.' }
    Invoke-WebRequest -UseBasicParsing -Uri $A3Wheel.url -OutFile $A3File
    if ((Get-Item -LiteralPath $A3File).Length -ne $A3Wheel.size -or
        (Get-FileHash -LiteralPath $A3File -Algorithm SHA256).Hash.ToLowerInvariant() -ne $A3Wheel.sha256) {
        throw 'Bootstrap payload differs from reviewed metadata; retain and stop.'
    }
}
```

Pause for acquired-file hash/length/namespace review, no payload import. After
the separate tooling-install boundary is approved:

```powershell
& $A3Python -I -m venv $A3Tools
if ($LASTEXITCODE -ne 0) { throw 'Tools venv creation failed.' }
$A3ToolPython = Join-Path $A3Tools 'Scripts\python.exe'
$A3PipRow = @($A3Pins.bootstrap.packages | Where-Object name -eq 'pip')
if ($A3PipRow.Count -ne 1 -or $A3PipRow[0].version -ne '26.2.1') { throw 'Pinned pip missing.' }
& $A3ToolPython -I -m pip --isolated install --no-index --no-deps --only-binary=:all: (Join-Path $A3ToolWheels $A3PipRow[0].filename)
if ($LASTEXITCODE -ne 0) { throw 'Pinned pip bootstrap failed.' }
$A3WheelPaths = @($A3Pins.bootstrap.packages | Where-Object name -ne 'pip' | ForEach-Object { Join-Path $A3ToolWheels $_.filename })
& $A3ToolPython -I -m pip --isolated install --no-index --no-deps --only-binary=:all: @A3WheelPaths
if ($LASTEXITCODE -ne 0) { throw 'Offline Poetry bootstrap failed.' }
& $A3ToolPython -I -m pip --isolated check
if ($LASTEXITCODE -ne 0) { throw 'Poetry tooling closure check failed.' }
$A3Poetry = Join-Path $A3Tools 'Scripts\poetry.exe'
& $A3Poetry --no-plugins --no-cache --version
if ($LASTEXITCODE -ne 0) { throw 'Poetry unavailable.' }
```

Record installed tooling names/versions against all rows and native executable
identity. Do not run `poetry self update`, pip upgrade/resolution, pipx or a
moving bootstrap script. No tooling dependency becomes a project dependency.

**A3.5 — A's canonical project environment; no tests.** From accepted source,
use session-only isolation, not persistent config or PATH mutation:

```powershell
if ($env:VIRTUAL_ENV) { throw 'Start a fresh ordinary PowerShell.' }
$env:PATH = $A3PythonRoot + ';' + $env:PATH
$env:POETRY_CONFIG_DIR = Join-Path $A3Root 'config'
$env:POETRY_DATA_DIR = Join-Path $A3Root 'data'
$env:POETRY_CACHE_DIR = Join-Path $A3Root 'cache'
$env:POETRY_VIRTUALENVS_PATH = Join-Path $A3Root 'envs'
$env:POETRY_VIRTUALENVS_IN_PROJECT = 'false'
$env:POETRY_INSTALLER_ONLY_BINARY = ':all:'
$env:POETRY_INSTALLER_NO_BINARY = ':none:'
$env:POETRY_INSTALLER_RE_RESOLVE = 'false'
$env:POETRY_KEYRING_ENABLED = 'false'
$env:VIRTUALENV_NO_PERIODIC_UPDATE = '1'
$env:VIRTUALENV_NO_DOWNLOAD = '1'
$env:VIRTUALENV_APP_DATA = Join-Path $A3Root 'cache\virtualenv'
$env:PYTHONDONTWRITEBYTECODE = '1'
Set-Location $A3Source
& $A3Poetry --no-plugins --no-cache check --lock --strict
if ($LASTEXITCODE -ne 0) { throw 'Canonical input validation failed.' }
& $A3Poetry --no-plugins --no-cache env use $A3Python
if ($LASTEXITCODE -ne 0) { throw 'Exact interpreter selection failed.' }
& $A3Poetry --no-plugins --no-cache install --with dev --without docs --no-root --dry-run
if ($LASTEXITCODE -ne 0) { throw 'Locked binary installation plan failed.' }
```

Review the plan/37-package profile and input hashes before authorizing the next
command. Per [Poetry configuration](https://python-poetry.org/docs/configuration/),
`:all:` disallows dependency source builds, and re-resolve false consumes locked
markers. A dry run does not verify downloaded bytes or promise a wheel choice.
If planned/actual artifact selection differs from revision 2's exact project rows,
refresh that wheel's official metadata before accepting/continuing the install;
do not silently adopt a compatible alternative or resolve a different version.
Poetry's installer is **not an offline `--find-links` wheelhouse consumer**:
this proposed project step explicitly permits only official locked binary
acquisition, with a fresh private cache and retained private install log.
Virtualenv's pinned bundled seed wheels may be used, but automatic seed-wheel
updates/downloads are disabled and its app-data cache stays under this attempt.
It does not install project dependencies by an independently maintained pip list.

```powershell
& $A3Poetry --no-plugins --no-cache -vv install --with dev --without docs --no-root --no-interaction *> (Join-Path $A3Root 'reports\project-install.txt')
if ($LASTEXITCODE -ne 0) { throw 'Locked binary install failed; retain partial environment.' }
& $A3Poetry --no-plugins --no-cache check --lock --strict
if ($LASTEXITCODE -ne 0) { throw 'Canonical lock validation failed.' }
& $A3Poetry --no-plugins --no-cache run python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Project dependency closure failed.' }
```

Inspect actual installed distributions/artifact origins/hashes and unchanged
canonical inputs before any candidate import. Do not accept a source fallback,
preinstalled custom binary or build toolchain. Missing binaries stop the route;
retain the partial environment. Once specifically approved, install only the
reviewed project root (`install --only-root --no-interaction`) and perform a
bounded module/import-location/version check. That invokes trusted project
backend/root installation and must be named in A3 approval; it is not wheel/sdist
installed-command qualification. No package build/test runner follows it.
Docs packages are not needed on the laptop; optional docs remain metadata-only.

Exact final preparation commands, only after dependency/source review and
explicit project-root backend/import approval:

```powershell
& $A3Poetry --no-plugins --no-cache install --only-root --no-interaction
if ($LASTEXITCODE -ne 0) { throw 'Reviewed project-root installation failed.' }
@'
import importlib.metadata, json, pathlib, sys
import obfuscidian
root = pathlib.Path.cwd().resolve()
assert pathlib.Path(obfuscidian.__file__).resolve() == root / 'src/obfuscidian/__init__.py'
assert importlib.metadata.version('obfuscidian') == '2.0.0.dev0'
print(json.dumps({'version': importlib.metadata.version('obfuscidian'), 'python': sys.version,
    'scope': 'source-root preparation only; no installed-artifact acceptance'}))
'@ | & $A3Poetry --no-plugins --no-cache run python -I -B -
if ($LASTEXITCODE -ne 0) { throw 'Project import identity check failed.' }
```

B reconstructs its own private runtime variables and records the same source
manifest and executable/native-token facts, with no Poetry/dev install. Before
later A4, set B's **session-only** PATH to its own selected PSF runtime so the
printed `python -I -S tests/_windows_owner_vm.py peer ...` selects B's interpreter.
Record command resolution/process image; never point B at A's private venv.

### Physical-host owner runner review and bounded future tooling work

Do not execute or edit these helpers/tests in A2. Their reviewed future diff
belongs to a separately authorized tooling task before A4, with fresh source
identity and proportionate regression/parser checks then:

| Current gap / source | Bounded future proposal and acceptance |
| --- | --- |
| `.github/scripts/check_windows_owner_vm.ps1` invokes `get_windows_vm_environment.ps1`, which repeats `Win32_Processor` | Add a reviewed physical-host observation path that omits the unchanged CPU query, retaining actual OS/PowerShell/process/token/opened-storage observations. Do not dynamically strip lines from old scripts or rerun the old group-only helper |
| Owner runner accepts only expected minor and relies on Poetry-selected `python` | Bind explicit A interpreter, expected full 3.13.16/native AMD64/GIL state and accepted complete source manifest before fixture creation; B independently verifies its own executable and same source. Retain no-optimized-Python and filtered-admin rejection |
| VM-only report/property text | Add accurate new scope `one physical AMD64 owner case; no matrix or production qualification`; record physical host and observed OS/runtime separately from fixture strategy. Keep `qualification_scope_approved=false` until an actual acceptance decision; never rewrite ARM reports/flags. Review future neutral strategy wording without relabeling past evidence |
| Lifecycle/Git helpers install dependencies, omit explicit owner option, redirect stdin and in lifecycle may reuse report directory | Separate preparation from execution; require existing accepted environment, fresh external reports/basetemp, explicit `--owner-vm-two-account`, `-s`, xunit1 properties and visible interactive peer instructions in **both selected and full runs**. No automatic install, CPU/group retry or report overwrite; stop if coordination is unavailable |
| Source/report coverage | Verify complete allowlisted manifest before helper/probe execution in both accounts, record base plus actual bytes/dirty state; exclude and redirect caches/reports/coverage. PowerShell parser check is not source authentication or test success |

Keep the original mandatory node
`tests/integration/test_windows_native.py::test_changed_native_owner_refused_without_privilege_activation`
and **all assertions**. Existing `--owner-vm-two-account` spelling can remain
internal. A4 must hold A's native/ancestor/WRITE_DAC custody while switching
users without signing A out; B validates exact UUID fixture directly beneath
Public Documents, source hashes, expected A owner, full volume/file identity and
temporary DACL, uses only its reviewed ownership grant, closes and exits before
A resumes. A restores the exact original protected DACL through retained
custody, never repairs by path/reopen, restores owner or normalizes timestamps.
Resume A only after B's peer completion/exit zero and the exact `OWNER-CHANGED`
barrier; session switching is manual and passwords never enter a harness/report.

Validate exactly one original case, zero failure/error/skip, actual distinct
owners and every positive setup/guarded-open/transition/retained-DACL/production
handle and guarded refusal/full native identity/original bytes/exact protected
DACL property. Keep fix04's separation between the complete refusal interval
and subsequent verification-read access-time observation. Setup failure or
missing B participation is failure. On interruption restore only known temporary
grants through retained custody where proven safe; retain uncertain fixtures and
private reports, never delete/repair/reuse them. Every attempt gets new A/B report
and work directories, exits and source manifests. A3 performs none of this.

### Approval limits, maintainer actions and stop conditions

Required review decisions: accept engineering-only purpose and the operation/
environment/refusal/deferred map; retain the now-selected CPython 3.13.16 pin
and proposed PSF per-user x64 acquisition; identify the trusted administrator;
approve each account-creation/per-user acquisition/installer/tooling/root-backend/
source-transfer/new-source-ACL boundary explicitly; approve or revise the proposed
gate order and later ordinary-user runner design. Review the future tooling diff
before transfer/test approval. A2 deliverable acceptance alone executes nothing.

The saved next-chat prompt supplies bounded A3.0–A3.5 authorization only if the
maintainer later submits it. This current runtime-refresh request supplies none.
That future authorization names the exact accepted input
catalogue/source hashes and paths, two standard accounts, per-user PSF registration/
temporary files, exact bootstrap wheels and canonical binary acquisition, bounded
project-root backend/import checks and new-source-only ACL grants. Reports stay
private. There is **no** existing-data ACL/owner repair, privilege/policy change,
machine install/PATH/launcher change, fixture/test/build execution, helper run,
CI/VM/cloud resource, real data, Git delivery or publication authority. A4 needs
a later separate synthetic fixture/runner/path/execution approval after A3 review.

Stop on missing administrator/accounts/ordinary session, any elevation or
Administrators SID, wrong interpreter/native machine/GIL/patch, unknown source or
manifest/input/hash/signer/metadata mismatch, existing task paths, unsafe ancestors/
DACL/storage or inadequate capacity, source build/backend fallback, network/auth
failure, changed canonical lock, unreviewed wheel choice, incomplete bootstrap,
unavailable peer/session barrier or any failed safety property. Preserve partial
setup/reports and propose the smallest remedy for review; no cleanup/retry,
source/cryptography substitution or criterion waiver. No approval can be inferred
from elapsed time or a passing earlier stage.

### Initial A2 validation and handoff — 3.13.14 history

A2's deliverable is this proposal, its explicit CLI gate revision and metadata input catalogue,
with public-safe #17/#29 comments and an Unreleased note. No Python, PowerShell,
tests, workflows, canonical dependency files or historical ARM/owner/lifecycle/Git
records are changed. Raw metadata receipts stay private in fresh host temporary
storage. Early metadata attempts encountered host default-Python missing packaging,
sandbox DNS/TLS-CA failures, an unpublished tentative pip pin, historical malformed
Requires-Python metadata and HTML checksum line wrapping; the final metadata-only
pass uses existing host tooling/TLS verification, rejects unusable candidates and
parses publisher markup. Earlier receipts remain retained; no payload or native
application failure is inferred from these preparation failures.

Executed: strict fresh Sphinx without warnings after repairing the new
cross-reference; local references across **51 rendered HTML pages**; seven plan
tables and byte-identical downloadable A2 catalogue; all 334 retained metadata
receipt hashes/lengths, 44 bootstrap wheel tags/Python/extras/dependency closure,
all 59 exact project sidecar refresh rows, canonical input/catalogue hashes;
proposal Python snippets parsed as AST only; LF/fences/privacy/scope/ancestry/diff
and empty-index checks. Every one of the 188 initial tracked files was compared:
only this plan, the CLI gate proposal and changelog changed; the A2 JSON is new.
Dated predecessor content is preserved byte-for-byte as each proposal's suffix.

Unexecuted: PowerShell parser (not available locally), any proposed Windows
command, installer/wheel acquisition/import, accounts/ACLs/privileges/policy,
environments/installations/source transfer, owner/native/application tests,
package/backend builds, exchanges/installed qualification, VMs/cloud/CI,
external URL linkcheck and Git delivery/publication. Existing host doc tooling
alone was used; no dependency installation. Three tracked docs plus one new JSON
remain **unstaged/uncommitted**, index empty, host refs unchanged at `9c2dd1b`.
The laptop was not rechecked or written. Public-safe #17/#29 progress/handoff
comments record this limited result; both issues remain open. **Stop for
maintainer review; A3 and A4 have not started.**

### CPython 3.13.16 follow-up validation and A3 handoff

The earlier A2 validation above describes revision 1 and its original four-file
handoff. This runtime-only follow-up preserves that catalogue byte-for-byte,
along with A1's measured 3.13.14 evidence and all ARM/owner/lifecycle/Git records.
The new revision 2 explicitly supersedes the original catalogue by filename,
target and SHA-256; its current digest is
`896c514996b6dedae97778272efa126b5bd9d6410e877b7fe63eda54aec5b7a3`.
All proposed installer names/URL/hash/length, exact-version assertions, selected
target markers and future owner-runner expectations now use **3.13.16**.

The [new-chat prompt](windows-amd64-next-chat.md) is an A3-only authorization
template for later maintainer submission. It includes A3.0–A3.5 and the existing
source/trust/permission review checkpoints; it never authorizes A4, helper/source
repairs, dispatch/CI/support decisions or Git delivery. Administrator availability,
private path mapping and future source archive/manifest are still unestablished
execution prerequisites. The present request remains proposal-only.

Current documentation and metadata validation results are reported in the final
handoff and public-safe #17/#29 comments. No proposed Windows command, acquisition,
setup, package import, helper, fixture, test or package/backend build ran. Native
AMD64 remains unqualified; A3/A4 have not started. All changes remain
unstaged/uncommitted on the preserved checkout at `9c2dd1b`, with an empty index.

The dated A1 and original planning records below are preserved as history.

---

**17 October A1 handoff:** read-only laptop readiness and a fresh complete
canonical AMD64 metadata audit are delivered in the [A1 report and A2 decision
packet](windows-amd64-readiness.md). Native Store CPython 3.13.14/AMD64 and current
standard-token/storage/tool observations are recorded; all 37 runtime/dev/build
packages (59 including optional docs) have compatible locked wheel metadata.
Both owner accounts are absent; no setup, payload acquisition or tests occurred.
Host and laptop refs agree at `64dcff0`, preserving the older checkpoint below.
**Next: A2 proposal/review only**, using the [updated prompt](windows-amd64-next-chat.md).
All detailed scope/matrix/prerequisite decisions remain unapproved and native
AMD64 support remains unqualified. Historical 16 October planning follows.

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
| **A1 — delivered** | Read-only laptop readiness and canonical binary-route audit | [Readiness report/A2 packet](windows-amd64-readiness.md), complete metadata catalogue and next prompt; no native qualification | A1 authorization stops at its handoff; no setup/tests |
| **A2 — next** | Review first-release scope, owner-account setup and validation order; consumes A1 | Reviewed operation/environment matrix, deferred requirements, exact setup/install commands, resource/permission boundaries and proposed revised #17/#29/CLI prerequisites | [Saved A2 prompt](windows-amd64-next-chat.md) authorizes proposal preparation only; concrete scope and setup require maintainer review |
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

# Native Windows primitive validation (#26)

This procedure qualifies the internal safety primitives and immutable checkpoint
store on synthetic temporary data. It does not enable Windows backup, restore,
recovery or existing-log append. #26's implementation handoff is accepted under
the **12 October 2026 approved ownership-proof deferral to #29**. Internal #27
development may begin in a new chat with production CLI gates retained; #27 has
not started here. Read
[the safety design](windows-safety-design.md), `AGENTS.md`, `CONTRIBUTING.md` and
the #26 handoff first.

## Candidate and environment

Use the exact reviewed source candidate, including uncommitted continuation
files. The initial maintainer commit is
`36be5e0847d93fd46a20d61d79cd0b95a4dac643`; that commit alone omits this
continuation. Copy a clean synthetic validation snapshot to the Windows machine;
no push, merge or real vault is needed. The supplied snapshot contains tracked
project sources plus the explicitly scoped continuation files, with no `.git`,
private `local/`, environment files or real keys. Its manifest records the base
commit and each source file's SHA-256. A snapshot run is candidate evidence, not
an exact-commit hosted CI result.

Use ordinary **unelevated** PowerShell, native 64-bit CPython and Poetry
`>=2.2,<3.0`. Initial qualification targets are Windows 11 and Windows Server
2022 or newer, Python 3.12–3.14, on local fixed NTFS with persistent ACLs. Record
which actual OS builds, architectures and interpreters were tested. A result on
one host/interpreter does not qualify the unexecuted combinations. Keep the
candidate and pytest temporary directory on eligible local NTFS; avoid mapped,
SUBST, network, removable and synchronized/reparse locations. Native fixture
setup failures must remain failures, rather than skips.

For a supplied archive, first compare its SHA-256 with the accompanying checksum,
extract it and change to the directory containing `pyproject.toml`. Then verify
all source hashes **before** installing dependencies:

```powershell
$manifest = Get-Content -LiteralPath candidate-manifest.json -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
    $actual = (Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $file.sha256) { throw "Candidate source checksum mismatch." }
}
$manifest.base_commit
$manifest.source_digest
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
"Elevated administrator: $($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
$PSVersionTable.PSVersion
git --version
poetry --version
```

The manifest deliberately contains no machine paths or identity information.
These commands only inspect the candidate. Ordinary dependency installation
below may download packages; the tests themselves use isolated synthetic data
and temporary local TLS servers, with update notices suppressed by the test
configuration.

## Run the tests

Select each available supported interpreter explicitly. This example uses 3.12;
repeat with 3.13 and 3.14, giving each interpreter distinct output filenames.
Stop and report a failed command rather than continuing toward a passing claim.
For a repaired candidate, use a new extraction folder and distinct report names
(for example `qualification-results-r2/native-python313.xml`); preserve the
first candidate and its failure evidence. Do not reuse an existing `--basetemp`.

If dependency installation hits deep cache-path failures, a short session-local
virtualenv root may help. Set `POETRY_VIRTUALENVS_PATH` to a dedicated short local
directory and `POETRY_VIRTUALENVS_IN_PROJECT=false` before selecting the
interpreter again. This does not change the application or prove the cause of an
installation failure. Do not change machine-wide long-path policy or delete an
existing environment to force installation. The first supplied run installed
successfully after choosing a shorter virtualenv location; its native failures
were separate.

```powershell
$pythonPath = python -c "import sys; assert sys.version_info[:2] == (3, 12); print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw "Requested interpreter unavailable." }
poetry env use $pythonPath
if ($LASTEXITCODE -ne 0) { throw "Interpreter selection failed." }
poetry install --with dev,docs
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
poetry check --lock --strict
if ($LASTEXITCODE -ne 0) { throw "Lock validation failed." }
$interpreterInfo = poetry run python -c "import json, platform, struct, sys; assert sys.version_info[:2] == (3, 12) and sys.platform == 'win32' and struct.calcsize('P') == 8; print(json.dumps({'version': platform.python_version(), 'architecture': platform.machine(), 'bits': struct.calcsize('P') * 8, 'implementation': platform.python_implementation()}))"
if ($LASTEXITCODE -ne 0) { throw "Native 64-bit interpreter required." }
$interpreterInfo
New-Item -ItemType Directory -Force qualification-results | Out-Null
poetry run pytest -q -ra -o junit_family=xunit1 --junitxml=qualification-results/native-python312.xml tests/unit/test_windows_native.py tests/unit/test_windows_checkpoints.py tests/unit/test_windows_keys.py tests/integration/test_windows_native.py tests/integration/test_windows_checkpoints.py 2>&1 | Tee-Object qualification-results/native-python312.txt
if ($LASTEXITCODE -ne 0) { throw "Native primitive qualification failed; retain results." }
poetry run coverage run -m pytest -q -ra -o junit_family=xunit1 --junitxml=qualification-results/full-python312.xml 2>&1 | Tee-Object qualification-results/full-python312.txt
if ($LASTEXITCODE -ne 0) { throw "Full regression suite failed; retain results." }
poetry run coverage report
```

### Microsoft Store Python and script execution

Microsoft Store CPython is included in the Windows compatibility target; a
separate traditional installer or `py` launcher is not required. The commands
above use `python` and validate its version before selecting the actual
executable for Poetry. For Python 3.13, change both `(3, 12)` assertions to
`(3, 13)` and use distinct `python313` report names. A versioned executable such
as `python3.13.exe` or an explicit executable path may also select the intended
interpreter. `python -3.13` is not a replacement for `py -3.13`.

Python's [Store package documentation](https://docs.python.org/3.13/using/windows.html#the-microsoft-store-package)
describes command aliases, virtual environments and app-specific filesystem
redirection. Storage/identity/ACL eligibility remains subject to the same native
checks; installation origin does not bypass them. A passing virtualenv run based
on Store Python does not prove every direct Store invocation or redirected
location safe for future mutation.

If multiline paste is unreliable, save the commands as a `.ps1` file and invoke
it with `&` and its quoted path from an ordinary unelevated PowerShell session.
No machine-wide execution-policy change is part of this procedure. Capture
interpreter metadata into a variable before displaying/saving it, as above:
the returned r3 transcript omitted the directly displayed version/architecture
stdout despite recording the later test results.

If the default temporary directory is ineligible, use pytest's `--basetemp` with
a **new dedicated disposable** directory on eligible local NTFS. Pytest clears
that directory; never point it at the checkout or any existing data. Do not
change volume security, enable privileges or elevate to force a fixture to pass.

No case in the two native integration modules may be skipped on a supported
Windows test host. POSIX transaction tests in the full suite intentionally skip
while Windows CLI mutation remains gated; distinguish those skips from primitive
qualification. Portable mocks test argument/framing/failure logic and supplement
the native cases; they cannot prove Win32 enforcement.

## Interpret the evidence

- Restricted-token tests require both a permissive positive control and actual
  kernel denial on the private file/directory, alongside `AccessCheck`. No real
  account is created and no privileges are activated.
- The changed-owner fixture uses an already enabled, owner-assignable group in
  the process token. A token without such a group produces an explicit fixture
  failure. Return that failure for a safe test-strategy revision; do not elevate,
  create accounts or convert it into a skip.
- The junction fixtures require working attribute-only positive conversions.
  They then deliberately convert a guarded directory before an operation or at
  the native file-open, directory-create and rename boundaries. Operations must
  refuse without writing through the new link. Directory attribute conversion
  itself is possible; denial of ordinary path rename is insufficient proof.
  Test-only removal of the fixture's reparse attribute reveals retained original
  entries; production never repairs a changed root or cleans it by pathname.
- The isolated drive-alias fixture creates and removes an unused per-session
  DOS mapping; it never replaces an existing drive. The short-name testcase's
  JUnit property `actual_short_alias_available` records whether this host exposed
  an actual 8.3 alias. `False` means syntax refusal only; do not change system 8.3
  policy to make the test pass.
- Unsupported-volume cases inject failure/flags into actual handle inspection.
  They prove fail-closed handling of those responses, not behavior on an actual
  ReFS, remote, removable or read-only volume. Record this limitation explicitly.
- Checkpoint interruption tests really terminate native children and reacquire
  retained ownership. Injected callbacks select partial-write, flushed-candidate,
  completed-publication and directory-create/acquisition boundaries. These are
  primitive retention proofs; transaction recovery is future #27 work.
- The native CLI checks must still refuse mutation and existing-log append.
  A primitive success is not permission to remove those gates.

Return the candidate source digest, actual OS/build/architecture, Python and Git
versions, command exit codes, test counts/skips and the native/full JUnit reports.
Keep raw reports private: failure traces may contain machine usernames and
temporary paths. Public issue summaries must redact those paths and must not
include key contents, even temporary test keys. Include the short-name property
and identify mandatory fixture failures separately from behavior failures.

## First candidate evidence and required rerun

The maintainer supplied reports for source digest
`8ae01c4e381eb3b7b4c9df7db0096325e16ca57b6d3470049031d6583adadffd`:
Windows 11 Home 10.0.26200/build 26200, AMD64 CPython 3.13.14, Poetry 2.5.1 and
Git 2.55.0.windows.5, on reported fixed local NTFS. Selected suites returned exit
1: **90 passed, 20 failed, 1 POSIX-only skip**. Native integration contributed
**23 passes, 20 failures and no skips**. The actual short-alias property was true.
Source-file hash verification and strict lock validation succeeded; archive
checksum, PowerShell version and elevation were not independently recorded.
Full regression/coverage did not run after the selected-suite failure.

The original guard allowed in-place conversion. Rename failures stopped most
checkpoint scenarios at their first publication, so those scenarios were not
proved. A changed-owner fixture lacked an assignable owner group. An object-ACE
preservation assertion lost read access after installing its unsafe descriptor;
another test expected exit 2 where the existing transaction gate returns exit 1.
These fixture/assertion failures do not authorize weakening production checks.

The repaired candidate uses native retained-root acquisition/publication,
creation-time directory handles and numeric native diagnostics. It also retains
a fully shared preexisting reader for unsafe-ACL byte-preservation assertions,
corrects gate exit expectations and captures child startup diagnostics. Local
argument/layout tests supplement the replacement API combination; only a native
rerun can qualify it. The changed-owner fixture remains mandatory and may still
fail on the same token. Report it separately; a suitable existing host/token or
an explicitly reviewed alternate test strategy is still needed for that proof.
No Microsoft Store Python or interpreter-version defect has been established.

## Repaired candidate evidence — 11 October 2026

The supplied r2 transcript and JUnit report identify source digest
`eec6f6890b9171e60dc24939941077ca3cb1c9072979352ebc3718d96c1be8e9` on
Windows 11 Home build 26200, native AMD64 CPython 3.13.14, PowerShell
5.1.26100.9444, Poetry 2.5.1 and Git 2.55.0.windows.5. The recorded elevated
administrator check was false. Source-file hash verification, installation,
strict lock validation and the interpreter check completed successfully.
Archive checksum verification was not recorded. The separate web handoff has
a transcription error in its digest; the terminal digest matches the supplied
r2 candidate. Keep the raw host-identifying evidence private.

Selected-suite exit code 1: **120 passed, 1 failed, 1 skipped**. Module counts:

| Module | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit native primitives | 54 | 0 | 1 (POSIX loader refusal) |
| Unit immutable checkpoints | 20 | 0 | 0 |
| Unit Windows key helper | 1 | 0 | 0 |
| Native primitive integration | 28 | 1 | 0 |
| Native checkpoint integration | 17 | 0 | 0 |

The **45 passing native integration cases** include the repaired conversion,
publication, private-directory, ACL preservation and checkpoint interruption
cases, plus retained CLI gates. The actual 8.3 alias property was true. Injected
volume responses remain injected evidence. These results qualify the executed
cases on this candidate/host/interpreter, not a passing entire qualification,
other Windows/Python combinations, transaction integration or hosted CI.

The sole failure again occurred before owner reassignment: the token had no
enabled, assignable alternate owner group. It is a mandatory fixture prerequisite
failure, with no observed production owner-refusal failure. Full regression and
coverage did not run. Repeating the same fixture on the unchanged token will
not supply the missing evidence. Preserve its failure and finish that proof
using an eligible existing token or a reviewed fixture strategy; do not remove
the assertion or turn it into a skip.

One possible strategy uses two **existing unelevated** accounts and only a
synthetic fixture: its creator records the original native identity/owner and
bytes, grants the second account ownership rights on that fixture, and the
second account takes ownership as itself. Restore the fixture's protected DACL
to the creator's exact grant, then the creator verifies the unchanged full ID,
bytes and DACL and requires the production owner check to refuse the new owner.
This retains actual owner-transition proof, without accounts or privilege
activation being added: Microsoft's [ownership-rights explanation](https://devblogs.microsoft.com/oldnewthing/20050818-09/?p=34533/)
distinguishes taking ownership as oneself with `WRITE_OWNER` from assigning it
to somebody else. It requires a mutually accessible eligible synthetic
location and a reviewed fixture implementation; it is a proposal, not executed
evidence or permission to change any real artifact's owner/ACL.

## Single-account supplementary checks — 11 October 2026

The maintainer confirmed that no second existing account is available. The
two-account proposal therefore cannot supply proof on the available machine.
The original owner-transition test and its mandatory failure remain intact;
its JUnit property `assignable_owner_group_available` now records fixture
availability on future runs. No privilege, account or ACL workaround is added.

Additional tests exercise the production owner validator without changing a
filesystem owner: portable injected-metadata cases cover acceptance, foreign
owner refusal and descriptor release. A supplementary Windows test creates a
real private synthetic file and checks its actual descriptor, then injects a
Windows-created in-memory foreign-owner descriptor into one `GetSecurityInfo`
response. All other descriptor parsing, token lookup, I/O and release calls use
actual Windows APIs. Its positive checks before/after verify the original
identity, bytes and owner/DACL remain unchanged. The descriptor is never
installed, and no file-owner or ACL setter is used.

This is **injected response evidence**, not kernel ownership reassignment or
an adequate substitute for the mandatory proof without a maintainer decision.
The JUnit property `owner_evidence` records
`injected-native-descriptor;kernel-owner-unchanged`. See Microsoft's
[descriptor operations](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptor-operations)
for the distinction between constructing an in-memory descriptor and retrieving
the descriptor of a held filesystem object.

Local macOS/Python 3.12 supplementary validation returned **77 passed, 48
platform skips** across the five selected suites. Ruff lint/format, diff checks
and strict Sphinx with the 37-page documentation check passed. The new Windows
case has not executed here; the full suite was not rerun for these test/document
additions. Production source is unchanged from the r2 candidate.

Use a fresh supplementary candidate extraction and retain r2 unchanged. Select
and validate Python 3.13/install dependencies using the earlier procedure,
then run only the new cases first. There is no need to rerun the whole selected
suite just to reproduce the known unavailable fixture:

```powershell
New-Item -ItemType Directory -Force qualification-results-r3 | Out-Null
poetry run pytest -q -ra -o junit_family=xunit1 --junitxml=qualification-results-r3/owner-supplement-python313.xml tests/unit/test_windows_native.py::test_descriptor_owner_validation_and_release_with_injected_metadata tests/integration/test_windows_native.py::test_injected_native_owner_descriptor_refused_without_file_changes 2>&1 | Tee-Object qualification-results-r3/owner-supplement-python313.txt
$supplementExit = $LASTEXITCODE
"Owner supplement exit code: $supplementExit"
if ($supplementExit -ne 0) { throw "Supplementary checks failed; retain results." }
poetry run coverage run -m pytest -q -ra -o junit_family=xunit1 --junitxml=qualification-results-r3/full-python313.xml 2>&1 | Tee-Object qualification-results-r3/full-python313.txt
$regressionExit = $LASTEXITCODE
"Full diagnostic regression exit code: $regressionExit"
poetry run coverage report 2>&1 | Tee-Object qualification-results-r3/coverage-python313.txt
```

The full invocation is **diagnostic regression**, with the original mandatory
owner-transition case still selected. On the unchanged token it is expected
to retain that one failure. Report every failure and skip, including any new
failure; neither a successful supplement nor absence of other failures makes
the full invocation or qualification pass. No test is deselected, skipped,
xfail-marked or weakened to hide the unavailable prerequisite. These commands
collect additional regression evidence while #26 remains incomplete. Keep raw
reports private and report the actual exit codes.

## R3 diagnostic evidence — 11 October 2026

Reviewed the supplied script, transcript and JUnit reports for source digest
`c0d477a6e2afc03b2de5e3076644a244a67163b3229d982de8d5dbd743a7c241`.
The transcript records archive SHA-256
`57c1e73b38d5124987d3c1a6f9dcd386f03dbd8c40343dba05a0224a9239b579`
and successful verification of every source file. The script changed interpreter
selection to `python -c ...`; it did not change tests or assertions. The
maintainer identifies the installation as Microsoft Store Python. Poetry
created a Python 3.13 virtualenv and the script's native 64-bit Windows check
completed without aborting. The transcript records Windows 11 Home build 26200,
64-bit OS, elevation false, PowerShell 5.1.26100.9444, Poetry 2.5.1 and Git
2.55.0.windows.5. Exact Python patch-version and architecture stdout were not
retained in this r3 transcript; r2 independently recorded AMD64 CPython 3.13.14.
Do not treat the earlier metadata as newly measured in r3.

The metadata-only follow-up returned on **12 October 2026** closes that reporting
gap for the existing r3 environment: **CPython 3.13.14, AMD64, 64-bit**, with
`store_package_path_detected=true`. The helper checks the existing Poetry
environment rather than installing dependencies or rerunning tests. The Store
package-path marker corroborates the maintainer's installation report; it does
not qualify untested invocation modes or filesystem locations. This is later
interpreter evidence, not a replacement test run. The supplied JSON uses the
UTF-16 encoding produced by Windows PowerShell; it contains no machine paths or
identity data, and the raw file remains private.

| Invocation | Passed | Failed | Skipped | Exit |
| --- | ---: | ---: | ---: | ---: |
| Supplementary owner checks | 3 | 0 | 0 | 0 |
| Full diagnostic regression | 907 | 1 | 596 | 1 |

The full XML has 1,504 cases and no errors. The sole failure is the original
owner-transition fixture, with `assignable_owner_group_available=False`, before
any owner reassignment. No additional production failure was observed. Native
primitive integration returned 29 passes/1 failure/0 skips; checkpoint
integration returned 17 passes/0 failures/0 skips. Of those 46 integration
passes, one is the newly passing injected-descriptor supplement and 45 are the
other native cases. The property
`owner_evidence=injected-native-descriptor;kernel-owner-unchanged` remains
explicitly supplementary. Actual 8.3 alias availability was true; injected
capability responses still do not qualify actual unsupported volumes.

The full run also passed all three installed-artifact packaging cases, using
development-environment dependencies rather than an isolated downloaded
wheelhouse. It exercised the retained CLI mutation/recovery and existing-log
append refusals. Skips cover gated mutation/recovery, POSIX semantics and
unavailable symlink fixtures; they do not validate Windows writes. Coverage
report exit was 0: 70% overall, 86% native wrapper and 91% immutable checkpoint
store. Coverage from this failing run is execution evidence, not qualification
success. Hosted CI and other Windows/Python combinations remain unexecuted.

No production repair or repeat of this unchanged diagnostic run is justified
by these results. Full diagnostic regression is now collected; actual ownership
transition proof remains a required blocker. An eligible existing host/token,
reviewed real-owner fixture or explicit maintainer revision of that proof
requirement is still needed. The current single account cannot supply it using
the proposed fixtures. Production source and mandatory assertions remain
unchanged, CLI gates remain intact, #26 stays incomplete and #27 has not started.

## Approved handoff and successor boundary — 12 October 2026

The maintainer approved the limited deferral described in the
[current safety design](windows-safety-design.md). #26's implementation handoff
is accepted and ready for internal #27 development, with actual ownership
transition proof carried to #29 as a mandatory qualification gate. Earlier
historical statements that this fixture blocks #27 are superseded by that
decision. No test result is relabeled and the real-owner test remains unchanged.

#27 must retain production Windows CLI mutation/recovery and existing-log
append refusals. Test synthetic lifecycle writes through private backend tests;
do not add an end-user bypass or expose an unsupported library API. #29 must
obtain actual owner-transition refusal with positive fixture and unchanged
native identity, bytes and exact protected DACL, plus the applicable native
operation/matrix/artifact evidence, before enabling Windows writes or claiming
qualified 2.0.0 support. Unavailable fixtures still fail; no skip, xfail,
privilege activation or account creation is approved.

No further unchanged r3 test run is needed for this handoff. The full diagnostic
run still has one failed fixture; portable/injected cases do not discharge the
deferred proof. All issues remain open and Git/release actions retain their
separate authorization requirements.

## Historical qualification and Windows-chat procedure

The maintainer can return results to the existing #26 chat for review and fixes.
Do not mark #26 complete or begin #27 solely because local macOS checks or
portable mocks passed. Review native results against the selected qualification
targets and document any remaining host/interpreter/fixture gaps. Hosted CI is
separate evidence and is unavailable for this unpushed candidate. Issue closure,
commits, push and merge each still require maintainer authorization.

If validation is continued in a separate Windows chat, use this prompt:

> Continue only Obfuscidian #26 for 2.0.0 from the exact source candidate supplied
> by the preceding #26 chat. Read AGENTS.md, CONTRIBUTING.md,
> docs/maintainers/windows-safety-design.md,
> docs/maintainers/windows-primitive-validation.md, #17, #26 and #25's handoff.
> Verify the candidate manifest and identify the actual native Windows build,
> architecture and Python version. Run the documented synthetic primitive and
> regression tests unelevated, repair #26 failures and retain all CLI mutation/
> recovery gates and existing-log append refusal. Distinguish genuine native
> enforcement and process-death results from portable mocks, injected volume
> responses, unavailable fixtures and unexecuted hosted matrix jobs. Do not use
> real vaults/keys, create accounts, activate privileges, weaken ACLs or start
> #27. Update #17/#26 accurately, use GPT-6.1 Sol in changed Python headers, and
> leave changes uncommitted with no push/merge. Report remaining qualification
> gaps and apply the approved 12 October ownership-proof deferral: #26 may hand
> off to gated internal #27 development, while actual proof remains mandatory
> in #29 before enabling Windows writes or claiming qualified support.

## #27 kickoff prompt

Use the following in a new chat after committing the reviewed #26 continuation
locally. Verify that the new chat uses the current branch and includes that
commit; `36be5e0` alone omits the continuation and approved deferral.

```text
Implement only Obfuscidian #27 for 2.0.0 in the current local branch
feature/17-add-safe-native-windows-support. Verify that the reviewed #26
continuation commit is present; do not reset the checkout or start from main.
Read AGENTS.md, CONTRIBUTING.md, docs/maintainers/windows-safety-design.md,
docs/maintainers/windows-primitive-validation.md, #17, #26, #27, #29 and #25's
handoff. Inspect the actual code and evidence rather than relying on issue state.

Apply the maintainer-approved 12 October 2026 limited deferral: #26's
implementation handoff is accepted, while real filesystem ownership-transition
proof remains a mandatory #29 gate. Keep the real-owner test and production
owner/DACL checks unchanged. Keep production Windows CLI mutation/recovery
gates and existing-log append refusal intact throughout #27; this instruction
supersedes #27's earlier instruction to enable common operations. Do not add a
user-facing bypass or expose an unsupported library API. No Windows write
enabling or qualified 2.0.0 support claim before the deferred proof and
applicable native qualification gates are satisfied.

Implement the private Windows transaction, fresh/merge backup, fresh restore
and explicit recovery lifecycles, retaining the POSIX backend and journal
reader. Use verified private rollback copies before removing original data;
retain distinct original/copy/proposal identities, a bounded Windows recovery
schema, full ownership/checkpoint binding and copy-inclusive resource estimates.
Reconcile retained artifacts and expected progress before inverse writes;
preserve changed, incomplete or uncertain artifacts. Do not treat the immutable
checkpoint store alone as proof of an intact latest transaction state.

Test synthetic native success, no-op/confirmation/no-write behavior, binary
preservation, tampering/corruption/wrong keys, DACL/sharing/namespace refusal,
I/O failures and genuine child-process termination/recovery at each destructive
boundary. Exercise Windows lifecycle writes through private backend tests,
retaining production CLI refusal tests. Microsoft Store CPython is part of the
compatibility target: use python or an explicit executable, validate the actual
version/architecture and provide exact PowerShell commands or a .ps1 helper.
The #26 r3 evidence is Windows 11 Home build 26200, unelevated, Store-based
CPython 3.13.14/AMD64/64-bit: owner supplements 3 passed; full diagnostic suite
907 passed, 1 unavailable owner-fixture failure, 596 skipped. Do not relabel that
run as passing or hide the known fixture failure.

Distinguish new local checks, actual native Windows evidence, injected responses,
fixture gaps and unexecuted hosted CI. Update #17/#27, relevant docs/changelog
and public behavior directives only where behavior actually changes. Use
Jeff Shurtliff (via GPT-6.1 Sol) and the current local date in changed Python
headers. Keep the CLI/public interface, Fernet/v1 backup format and dependencies
unchanged unless an additional maintainer decision is required.

Do not start #28/#29 implementation, Git merge restore integration, existing-log
append, rollback pruning or filesystem naming refinements. Do not use real
vaults/keys, create accounts, activate privileges or change machine-wide policy.
Leave changes unstaged/uncommitted; do not push, merge, open a PR, close issues
or publish. Finish with a precise #27 handoff and remaining qualification gates.
```

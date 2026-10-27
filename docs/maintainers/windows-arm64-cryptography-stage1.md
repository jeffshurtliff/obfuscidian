# ARM64 cryptography Stage 1 inventory and feasibility — #30

**16 October 2026. Result: bounded read-only inventory complete; build feasibility blocked.**

No usable authorized existing builder was established. The current guest has
an authenticated native ARM64 Python runtime and some development inputs, but
no verified compiler/linker/SDK, Rust/Cargo toolchain, OpenSSL build inputs or
complete cryptography build environment. Missing or unverified inputs remain
blockers; this finding does not authorize their acquisition or installation.

This is the Stage 1 deliverable for [#30](https://github.com/jeffshurtliff/obfuscidian/issues/30),
a sibling of #29 under #17. The [provenance plan](windows-arm64-cryptography-provenance-plan.md)
continues to govern later stages. #29 remains open and blocked for its selected
ARM64 track, retains #28, and owns application qualification. No broader #29
execution, production enabling, beta/support claim or AMD64 qualification follows.

## Manifest and evidence classes

Download the [input-pin preparation manifest](windows-arm64-cryptography-input-pins.json).
It is an inventory and review artifact, **not a frozen build manifest**, an
executable recipe, a replacement lockfile or a second runtime dependency list.
Null pins and explicit gaps must remain unresolved until supported by evidence.

The manifest distinguishes:

- Current host repository hashes and canonical lock declarations.
- Maintainer-executed guest observations returned privately in this chat.
- Earlier source/audit evidence carried forward from the committed handoff.
- Proposed inputs and missing or unverified candidates.

The agent reviewed supplied outputs; it did not independently run commands in
the VM or acquire copies of the guest binaries. Raw account identifiers, paths,
environment configuration and inventories remain private. Sanitized observations
below do not copy SIDs, hostnames, profile paths, cache identifiers or fixture IDs.
Private cache/build artifacts were neither searched broadly nor removed.

## Preserved source and environment identities

At inventory start, `feature/17-add-safe-native-windows-support` was clean at
`d067d81340811d3b21319c670a4f6624e0d7e3b3`. Local HEAD, the cached remote ref and
a read-only live remote query agreed. No fetch/ref update, reset, replacement
checkout, staging, commit, push, merge or PR occurred.

| Canonical input | SHA-256, verified on the host during Stage 1 |
| --- | --- |
| `pyproject.toml` | `1e66448aad2e0c5925d827afd85333791ac3635d885516a0fbcb5619d6f85fe5` |
| `poetry.lock` | `b63c1714fcf641742a10be8cf46b4d641ea0329217a86835379d4105515e10fb` |

The current guest reports edition `Core`, display version `26H2`, build
**26300.9711**. This is a fresh registry observation, not a rerun of accepted
owner proof or new exact-commit application qualification. The frozen fix04
snapshot, its original identities/report flags and all historical failures stay
unchanged. Do not relabel it as this host commit or current OS revision. No
comparison establishing that the guest snapshot matches this host commit was
performed. Its accepted **1 passed in 215.27s** remains bounded to the recorded
owner-proof combination; this inventory does not extend that acceptance.

Only Account A's current session was rechecked for this inventory: `whoami /all`
shows medium integrity, no Administrators group and no listed take-ownership or
restore privilege. Account B's current token/session was not rechecked; no B
execution was needed or inferred. Existing two-account historical evidence is
preserved, not remeasured. No privilege, account, policy or persistent environment
change occurred.

## Builder inventory and ordinary-user feasibility

| Component | Read-only observation | Version, architecture, provenance and feasibility |
| --- | --- | --- |
| Native CPython | Explicit existing per-user interpreter executed with `-I -S -B`; no site packages or bytecode writes | CPython 3.13.16, 64 bits, GIL enabled, `Py_GIL_DISABLED=0`, SOABI `cp313-win_arm64`; `IsWow64Process2` process `0x0000`, native `0xAA64`. Execution and selected file reads work under the current ordinary token |
| Python runtime files | `python.exe`, `python313.dll`, `python3.dll` hashed and inspected without loading candidate code | All PE machine fields are `0xAA64`; all three report version 3.13.16 and valid PSF Authenticode signatures |
| Python development files | `python313.lib`, `Python.h`, `patchlevel.h` and `LICENSE.txt` present and hashed | All 1,660 parsed import-library machine records are `0xAA64`; two remaining members are linker indexes. Selected inputs are readable; the complete headers/libs tree is not frozen or authenticated by these spot checks |
| Original Python installer | Retained installer hashed and signature checked, without execution | SHA-256 matches the current official release page; valid PSF Authenticode. No Sigstore/GPG verification or installer payload-to-installed-tree comparison was performed |
| C/C++ compiler/linker | `cl`, `link`, `clang-cl`, `lld-link` absent from current PATH; checked standard Visual Studio 2022/18 roots and installer locator absent | No exact tool version, host architecture, ARM64 target libraries, vendor provenance/license or ordinary-user build usability established. Python's `MSC v.1944` build string does not establish a local compiler |
| Windows SDK | `rc`, `mt` absent from PATH; both checked Windows Kits 10 roots absent | Targeted registry reads returned no readable result, conflating absence/access failure; SDK variables unset. No SDK/version/hash/license established |
| Rust/Cargo | `rustc`, `cargo`, `rustup` absent from PATH; standard current-user Cargo bin and Rust toolchain roots absent; relevant variables unset | No installed toolchain release, host/target standard libraries, checksums or vendor provenance established. Earlier failed-build cache activity remains historical, uninspected and untrusted as a build input; no rustup proxy was invoked |
| OpenSSL | `openssl` absent from PATH; two checked standard roots absent; selected OpenSSL variables unset | No usable ARM64 development input set established. Python's bundled SSL implementation is not an accepted substitute for the proposed cryptography OpenSSL build input |
| Auxiliary tools | Perl, nmake, NASM, CMake, Ninja, Git and vswhere absent from PATH; checked Strawberry Perl executable absent | Exact versions, architectures, origins/licenses and ordinary-user usability unresolved. The recipe must determine applicable ARM64 make/assembler requirements; no x86 assembly recipe or CMake/Ninja requirement is assumed |
| Python build backend | Maturin and setuptools metadata absent from all checked environments | No exact versions, authenticated wheels, complete transitive backend requirements or executable/backend usability established |
| Python tooling/dependencies | Tooling environment and two task-specific Poetry cached environments inspected through stdlib metadata, without importing packages | See the version/metadata observations below; installed metadata is not an authenticated wheel or execution result |
| Other builder | None identified with authorized access | No other machine or remote CI was inventoried, provisioned or dispatched |

Negative results are bounded to current PATH, the explicitly checked standard
locations, selected variables, targeted registry entries and task environments.
They do not prove machine-wide absence. No recursive profile search, credential
discovery, unrelated private-file inspection or full environment dump occurred.
No vendor installation inventory exists from which to accept compiler/SDK terms.
[Microsoft's permissions documentation](https://learn.microsoft.com/en-us/visualstudio/ide/user-permissions-and-visual-studio?view=visualstudio)
requires administrator permissions for initial Visual Studio installation;
Stage 1 neither establishes a per-user provisioning route nor approves one.

## Python input and licensing observations

The [official 3.13.16 release page](https://www.python.org/downloads/release/python-31316/)
publishes the retained installer's digest
`696e2226062c6ec3622c13f143d28336a856968518e49cb4f4c62513215a4f5d`
and labels its ARM64 installer **Experimental**. The installed license file was
hashed, not legally audited. The [Python license documentation](https://docs.python.org/3.13/license.html)
records PSF and incorporated third-party terms; retain/review applicable notices
before any later redistribution. An installer hash/signature does not establish
that every installed file is unchanged or authorize another installation.

| Environment inspected | Selected observed versions and declared license metadata |
| --- | --- |
| Base Python | pip 26.2.1 (MIT); other selected build packages absent |
| Per-user Poetry tools | Poetry 2.5.1 (MIT), poetry-core 2.5.0 (MIT), pip 26.2.1 (MIT), packaging 26.3 (Apache-2.0 OR BSD-2-Clause) |
| Both task-specific cached environments | CFFI 2.1.1 (MIT-0), pycparser 3.0 (BSD-3-Clause), packaging 26.3, pip 26.2.1, poetry-core 2.5.0, pytest 9.1.1 (MIT); both configurations reference CPython 3.13.16 with system site packages disabled |

Both cached environments lack metadata for cryptography, matching vectors,
maturin, puccinialin and setuptools. The snapshot-local `.venv` is absent; this
does not imply the cached environments are absent. No Poetry project association
or completeness claim was inferred. Declared licenses are metadata observations,
not independent license compliance, wheel provenance or installed-payload audits.
Both cached environments show CFFI depending on pycparser for non-PyPy.

The initial base/tool-environment metadata hashes cover decoded/re-encoded text.
Later cached-environment hashes cover raw `METADATA` bytes; the manifest labels
these separately. Neither kind is a wheel digest or a complete installed payload
pin. No package imports, `pip check`, dependency resolution or backend execution
were used to turn metadata presence into a runtime claim.

## Verified declarations versus unresolved build pins

| Input | Prepared identity | Remaining acceptance gap |
| --- | --- | --- |
| cryptography source | Unchanged official 50.0.2 sdist; current lock declares SHA-256 `7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5` | Earlier in-memory source/PyPI/hash comparison is carried forward from the committed proposal; source bytes were not reacquired here. No new signature/attestation verification or unchanged extracted tree exists |
| Python ABI/runtime | Native GIL-enabled CPython 3.13.16, runtime/selected development hashes and retained installer identity | Complete development/runtime inventory and payload provenance binding still needed for a frozen builder |
| CFFI / pycparser | Versions 2.1.1 / 3.0 observed; compatible wheel declarations/digests copied from the unchanged lock | No wheel bytes acquired/hashed or native CFFI payload/RECORD/import verification performed |
| Maturin / setuptools | Earlier source review records maturin `>=1.14.1,<2`, applicable CFFI and setuptools exclusions | Exact selected releases, hashes, transitive requirements, provenance and licenses unresolved; constraint bounds are not pins |
| Rust / Cargo / crates | Upstream Rust MSRV 1.83.0 and locked Cargo resolution; recorded PyO3 0.29.2, openssl 0.10.81, openssl-sys 0.9.117 | Exact toolchain, full upstream Cargo.lock digest/checksums and all offline crate inputs unresolved; these three recorded crate versions are not a complete Cargo manifest |
| Compiler / SDK | None selected or verified | Exact compatible authenticated licensed host/ARM64-target input set unavailable |
| OpenSSL | Conditional 4.0.3 baseline retained; upstream source catalogue lists it and Apache-2.0 terms | Source hash/signature/trust-anchor verification, fresh advisory review, ARM64 configuration/flags, source bytes and final linked-library hashes unresolved. No advisory clearance inferred |
| Auxiliary tools | None selected or verified | Exact applicable Perl/make/assembler and any other recipe inputs, versions, hashes, provenance/licensing unresolved |
| Upstream tests/vectors | Matching 50.0.2 required; absent from checked environments | Exact matching archives, complete test dependencies, hashes/licenses and reviewed offline execution plan unresolved |

The [upstream Windows build guidance](https://cryptography.io/en/50.0.2/installation/#building-cryptography-on-windows)
requires compatible native tools, OpenSSL and Rust. It does not establish a
working ARM64 builder here. No older wheel, downgrade, crypto-code patch,
algorithm change or substitute dependency is selected. Any private 50.0.2 wheel
would have a new origin/hash and is not authenticated by the current canonical
lock merely because its version matches.

## Executed checks and limits

Executed guest checks were maintainer-pasted, read-only commands, one at a time:
current account/token; PATH discovery; explicit standard-path presence; isolated
stdlib Python ABI/native-machine observation; selected file hashes/Authenticode;
selected distribution metadata; targeted variables/registry and task-cache
environment discovery; static PE/COFF inspection; current OS registry and retained
installer checks. No owner fixture, application command or qualification suite ran.

Host checks passed using the existing environment, without installing tools:

- Canonical input hashes, unchanged HEAD, empty Git index and documentation-only
  scope: five tracked edits and two new public files; private observations ignored.
- JSON parsing, 23 typed digest formats, four canonical artifact/version/hash
  declarations, 13 explicitly unresolved input groups, and equality of the
  rendered downloadable manifest with its source bytes.
- Strict fresh `sphinx-build -W --keep-going -E -a -b html docs docs/_build/html`.
- `.github/scripts/check_docs.py docs/_build/html`: local links/assets/anchors
  across **45 HTML pages**, with no external requests by that checker.
- LF/privacy/scope inspection and `git diff --check`.

The initial ad hoc manifest checks stopped on two checker assumptions: an
expected group count and descriptive fields whose names included `sha256`.
Correcting that validation logic, without changing input evidence, produced the
successful result above. No prior test/CI result is promoted to a Stage 1 pass.
Official references were reviewed selectively; a complete external link check,
OpenSSL advisory review and input signature-chain audit were not executed.

Unexecuted: compiler/backend execution, compilation, installations, package
imports/tests, complete native upstream/application suites, rebuild comparison,
candidate wheel inspection/acceptance, either v1 exchange direction, installed
CLI qualification and hosted CI. No source archive, toolchain or test materials
were acquired; browsing official documentation is separate from input acquisition.
The prior 36/37 metadata audit and both failed source installs remain historical;
their reports/caches were not changed, retried or used as trusted builder pins.

## Stop and next review boundary

Stage 1 stops with a **blocked feasibility finding and incomplete pin preparation**.
There is no executable build command or installation recommendation in this
handoff. If an existing suitable builder is later identified, its identity and
access need a concrete scoped review before further inventory. Otherwise a
separate acquisition/provisioning proposal is required; no such action is
approved as an automatic next step. A complete authenticated input set and
licensed ordinary-user builder must precede any separately approved build.

Later acquisition/build, artifact acceptance, installation and dependency-origin
experiments each require their own concrete approval. #30 remains open; #29 is
still blocked and owns application qualification. POSIX behavior, CLI syntax,
Fernet/v1, canonical dependencies, CLI gate order and existing-log append refusal
are unchanged. Production Windows mutation/recovery remains gated; AMD64 is
unqualified. No waiver, public API, pruning, naming refinement, Python 3.15 or
new Git recovery command is introduced; existing Git interruption/power-loss
limits remain. All Stage 1 documentation changes are unstaged/uncommitted on the
preserved branch; no issue closure, release or publication is authorized.

# ARM64 builder acquisition approval packet — #30 Phase A

**16 October 2026. Phase A delivered for review. Full Phase B is blocked; no acquisition approved.**

This is the concrete follow-up to the
[acquisition/provisioning proposal](windows-arm64-cryptography-acquisition-plan.md),
using proposal checkpoint `e54875bfc4c2aee1d55633be622de940a2d1883f` on
`feature/17-add-safe-native-windows-support`. At entry the working tree/index
were clean; HEAD, cached origin ref and live GitHub branch ref matched that
checkpoint. The shell remote query failed DNS; the GitHub connector supplied
the successful read-only live-ref check. Historical Stage 1 checkpoint
`e0cadc3dd7132edbcc01266f07992bb1943fdce3` and its report/manifest remain unchanged.
Prior Git authorization is complete; this packet remains uncommitted.

Download the [revision 1 metadata catalogue](windows-arm64-cryptography-acquisition-inputs-r1.json)
for exact stable artifact URLs, filenames, sizes, full expected SHA-256 values,
declared licenses, dependency declarations and metadata-response receipts.
This is an acquisition proposal, **not a frozen input manifest, runtime lockfile,
accepted builder or executable download queue**. All proposed tool/source/package
artifact-body acquisition and hash-verification fields remain false.

## Review outcome and decisions

The preferred route remains a full independent disposable native ARM64 UTM copy.
Preserve the original owner-proof VM, frozen fix04 snapshot, failed attempts,
reports and caches. No guest command was necessary or requested in Phase A.

Microsoft's current [Windows release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information)
lists 26H2 / 26300.9711 on the General Availability Channel. That resolves the
published release classification of the last Stage 1 registry observation;
it does not remeasure the guest, prove its enrollment/channel, exclude S mode,
verify UTM acceleration or extend accepted fix04 evidence. Copy eligibility
still needs the later ordinary-session checks before tool execution.

| Decision | Concrete proposal / unresolved requirement |
| --- | --- |
| Microsoft integrity | **Hold all Microsoft payload acquisition/layout execution.** Resolve the channel/catalog mismatch below; authenticate and freeze the installer engine and complete required ARM64 package closure first |
| Download-only subset | If separately approved, acquire only the explicitly selected non-Microsoft rows in revision 1 into fresh host storage, verify them and statically inspect archives; no installation, import or backend execution |
| Assembler | Add native ARM64 LLVM **23.1.3** as `clang-cl` assembler for the proposed OpenSSL ARM target; keep MSVC as C compiler/linker. Review this added tool explicitly |
| Auxiliary emulation | Approve or reject Strawberry Perl **5.42.3.1 x64**, for Perl scripts only. It is not native ARM64 Perl; no bundled GCC/OpenSSL enters tool/library lookup |
| Windows/tool rights | Confirm rights for the separate Windows instance and applicable Build Tools compilation/development/testing terms. No entitlement or license acceptance is assumed |
| Resources and identity | Approve the private source/copy identity and paths, four vCPUs, 8 GiB RAM, a proposed 128 GiB copy disk, and the budgets below, subject to actual capacity. No resize or copy is authorized |
| Layout execution host | Approve an explicit ordering change: host-only download phase B1; separately approved copy creation C1; then approved B2 layout generation inside that copy; C2 installation follows later review. Never generate a layout in the original guest |
| Later execution | Archive receipts and static review precede C/D; complete inputs and a reviewed ordinary-user recipe precede Stage 2. No build or #29 execution follows from this packet |

The proposed non-Microsoft selection is **58 payloads totaling 1,294,896,218
bytes**, using release-declared sizes and Rust HEAD sizes. This includes the
conditional Perl archive and LLVM assembler, 32 crate archives and 15 upstream
test wheels. It excludes Microsoft payloads, a Python installer reacquisition,
metadata sidecars and any additional inputs discovered during static review.
This count measures proposed transfers, not files acquired. A partial acquisition
could produce receipts; it cannot clear the Microsoft/builder/input-freeze blockers.

## Microsoft: exact candidate, failed catalog binding

The [fixed-version release history](https://learn.microsoft.com/en-us/visualstudio/releases/2022/release-history)
lists **17.14.42**, released 13 October, build **17.14.37806.7**. Its exact
Build Tools bootstrapper URL and HEAD-only size **4,474,848 bytes** are in revision 1.
No executable body was read. A digest-looking URL segment is not an independently
published checksum: the accepted bootstrapper SHA-256 remains **unknown**.
Before any execution, require its recorded complete SHA-256 and valid Microsoft
Authenticode publisher, chain and timestamp under an explicitly reviewed trust policy.
The bootstrapper's own PE/process architecture remains unverified.

The moving `aka.ms/vs/17/release/channel` endpoint was used **only to discover
metadata**. It resolved to a version-specific Microsoft `.chman` URL reporting
17.14.42; revision 1 records that URL and the observed channel-body hash. Its
signature has not been verified. Do not use the moving alias for acquisition or
silently accept a different release.

| Referenced `VisualStudio.vsman` | Channel declaration | Received metadata bytes |
| --- | --- | --- |
| Size | 30,443,686 | 17,954,770 |
| SHA-256 | `a871a5ff41acebbe5037455fd6f51fcd4907b47d8f3c9860871ea0b222a2fd45` | `99dda859c4ae3c446eb25620d1a6237bb135d95d14d55cd1d30a15340bb39d80` |

One explicit `Accept-Encoding: identity` recheck returned the same length/hash,
HTTP 200 and no Content-Encoding. Both responses are retained privately. The
cause is unestablished. Do not repair/reformat the response, adopt the observed
digest as the expected pin, assert publisher compromise, or execute a bootstrapper
to work around the discrepancy. No catalog signature or payload is accepted.

### Read-only discrepancy investigation — 16 October follow-up

The maintainer authorized further official-metadata investigation only. **The
mismatch reproduces; no authoritative corrected pair or root cause was established.**
The catalogue's appended `microsoft.metadata_investigation` preserves six probe
receipts and their evidence limits; original declarations and response bodies
remain unchanged. No executable, package or source payload was requested.

| Probe | Result |
| --- | --- |
| Direct fixed `.chman` GET, identity/no-cache | 91,688 bytes; SHA-256 `4f0f290bb4d58a061a49a2fa893357a8c9e7e2b49fc91873f533ab8f791e4fa0`; byte-identical to the original channel |
| Current channel alias GET, identity/no-cache | Resolves to that same fixed channel URL; byte-identical body and unchanged catalog size/hash declaration |
| Referenced fixed `.vsman` HEAD | HTTP 200; Content-Length **17,954,770**, matching GET rather than the channel's **30,443,686** declaration; no body read |
| Referenced fixed `.vsman` GET, identity/no-cache | HTTP 200; same **17,954,770 bytes / `99dda859…`** as both saved original responses |
| Same catalog path with a diagnostic query | Same complete body/hash and Content-Length; no Content-Encoding or Content-Range; still reports cache hits |
| Existing host curl, raw HTTP/1.1, identity/no-cache | HTTP 200; same complete body/hash and length; no Content-Encoding or Content-Range. No automatic decompression or redirect followed |

The direct channel and catalog both report **17.14.42+37806.7**. These observations
find no moving-channel rollover or wrong-release selection. Parsing succeeds on
the complete received JSON, and independent byte hashing precedes parsing; JSON
serialization is not used as a substitute for the published file digest. HEAD
and GET agree, so the smaller file is not merely a short read relative to its
reported HTTP length. No gzip/content-encoding or partial-response explanation
was observed. These checks do not prove that every upstream delivery layer is
correct or rule out a transformed/stale response with internally consistent headers.

All six probes report `X-Cache: HIT, HIT`, including the diagnostic query and
requests carrying no-cache headers. Those request headers did **not** establish
an uncached origin response. Python and curl used the same host/network route;
two clients do not establish independent-network or origin evidence. The same
ETag on catalog responses is an opaque validator, not an accepted SHA-256. No
conclusion about which publishing/CDN/intermediary layer caused this discrepancy
is justified. No proxy/DNS/network/security configuration was changed to investigate.

Embedded signature fields remain **unverified**. Their presence, release label,
HTTPS delivery and an ETag do not replace the channel-declared file hash. No
supported normalization rule or publisher-issued replacement size/hash was
established. Microsoft-hosted support discussion was not treated as authoritative
release metadata. The documented [minimal-layout profile repair](https://learn.microsoft.com/en-us/troubleshoot/developer/visualstudio/installation/error-test-deploy-minimal-layout)
concerns an existing installation/profile; its applicability to this direct
metadata inconsistency is unestablished, so no profile/cache repair was attempted.

**Acquisition hold is unchanged.** A later review needs a publisher-corrected
channel/catalog pair whose exact bytes satisfy its declaration and whose trust
checks pass, or an explicitly reviewed different official release candidate.
Do not substitute a release, repeat unchanged probes indefinitely, fetch a
bootstrapper to investigate, run layout verification, alter declared digests or
contact upstream without separate authorization. Compiler/SDK closure, engine
pins and all B/C/D/build approvals remain unresolved. This follow-up changes no
artifact acquisition/verification flag to true.

### Supported fixed-release alternatives — 16 October metadata check

**No consistent pair was found in the additional releases checked.** This is a
bounded finding, not a claim that every archived release has been tested. The
appended `microsoft.alternative_release_checks` catalogue record contains exact
fixed bootstrapper/channel/catalog URLs, declared/observed hashes and private
metadata receipt identities. **17.14.42 remains the original proposed selection**;
no alternative was adopted and the acquisition hold remains.

Microsoft's [2022 support policy](https://learn.microsoft.com/en-us/visualstudio/releases/2022/servicing-vs2022)
requires the latest servicing release on Current. The 17.12 LTSC ended in July
2026; an older fixed bootstrapper's availability does not establish a supported
alternative. For 2026, the current [fixed release history](https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history)
and Stable channel both identify **18.11.0**, released 13 October, full build
**18.11.12306.390**. The [2026 support policy](https://learn.microsoft.com/en-us/visualstudio/releases/2026/servicing-vs)
covers the latest Stable release; its [release rhythm](https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-rhythm)
places 2026 LTSC availability in November 2026. No older 2026 LTSC is assumed
available or supported on this check's date. Component/toolset lifecycle rules
are separate; checking a new product release does not select a new compiler.

| Fixed release checked | Official catalog declaration | Received catalog | Result |
| --- | --- | --- | --- |
| **18.11.0** / build **18.11.12306.390** | **31,254,503 bytes**, SHA-256 `db509503…` | **18,403,028 bytes**, SHA-256 `8feeff26…` | Size/hash mismatch; no replacement accepted |
| **16.11.60** / build **16.11.37627.13**, legacy comparator | **19,253,644 bytes**, SHA-256 `fb642c3f…` | **11,154,648 bytes**, SHA-256 `406969c3…` | Size/hash mismatch; also outside the native ARM64 host route |

Full SHA-256 pairs, preserving the original declarations:

- **18.11.0:** declared
  `db509503e199e75b45c99fc473dd01de6b5a8f2bfe85a4eda8c0bb2b49fb2b80`;
  received `8feeff2606390c54ea2943f2d7cec739cc7360322b3c161ab1ef5028664a2a98`.
- **16.11.60:** declared
  `fb642c3f891b70947e0152275e1722ffb3cca7e8700eea0f0fa0f3a7645584cc`;
  received `406969c30f4eb8bf0075a0850e339340ac83942705b76269156bb5b70f01b631`.

Each direct fixed channel matches its corresponding discovery-channel body;
each received catalog parses and reports the same semantic version as its
channel. HTTP Content-Length agrees with the received body, and these catalog
GETs report no Content-Encoding or Content-Range. For **18.11.0**, a separate
HEAD also reports **18,403,028** and existing raw HTTP/1.1 curl receives exactly
the same bytes as Python. These remain same-host/network observations; they do
not establish an uncached origin response, independent-network corroboration,
publisher fault or a signature-verified correction. Metadata signatures remain
unverified. No alternate body digest replaces a declared pin.

The [2019 servicing policy](https://learn.microsoft.com/en-us/visualstudio/releases/2019/servicing-vs2019)
keeps its 16.11 baseline in support through April 2029. The retrieved
[2019 release history](https://learn.microsoft.com/en-us/visualstudio/releases/2019/history)
and channel both report **16.11.60**; that is the measured legacy comparator,
not an assumption about another version. Microsoft's [ARM host documentation](https://learn.microsoft.com/en-us/visualstudio/install/visual-studio-on-arm-devices?view=visualstudio)
identifies 2022 **17.4** as the first native ARM64-host release. Supported legacy
product status therefore does not supply this proposal's required native
compiler/linker host, and no emulated legacy toolchain is proposed. Still older
legacy products were not catalog-tested for this native ARM64 route.

**18.10.4 remains untested.** The 2026 history lists it as a 13 October servicing
release, build **12306.391**. Its exact fixed Build Tools link was recorded; a
HEAD-only request returns HTTP 200 / **5,694,384 bytes**, with no channel/catalog
reference in the response headers. The official metadata inspected did not
resolve its fixed pair. No executable body was read to inspect embedded data,
and no channel URL/hash was guessed. Availability in the history is not treated
as proof of supported-pair consistency, or as permission to replace 17.14.42.

### Fixed 18.10.4 metadata follow-up — 16 October

**Still unresolved after targeted discovery; no integrity result for this pair.**
The earlier “untested” observation above and its receipts remain historical.
Re-reading the [official release history](https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history)
confirms **18.10.4**, **13 October 2026**, table build **12306.391** and this
[fixed Build Tools bootstrapper URL](https://download.visualstudio.microsoft.com/download/pr/2c69ffd0-d38e-457c-9c18-020fe133868c/f4ad61ca6e875e784d3e3e7412c6115d2c471220575ac1c908fa23fffc736761/vs_BuildTools.exe).
That link is recorded only: its executable body remains unread, and the hash-like
URL segment is not accepted as a verified bootstrapper digest. The prior HEAD
observation remains HTTP 200 / **5,694,384 bytes**, zero body bytes read and no
manifest reference in its headers. A full fixed-manifest build number, direct
channel/catalog URLs and declared catalog size/hash remain **unknown**.

| Metadata-only discovery checked | Observation and limit |
| --- | --- |
| Release history and [release notes](https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes) | Confirm the servicing release; no fixed `.chman` / `.vsman` reference found in the inspected pages |
| Microsoft public [channel index](https://aka.ms/vs/channels) | Six entries; Stable is **18.11.0**, build **18.11.12306.390**, URI `https://aka.ms/vs/18/stable/channel`; no **18.10.4** reference. This is not a complete historical archive |
| One inferred versioned alias, `https://aka.ms/vs/stable.18.10/channel`, HEAD only | HTTP **302** to Bing; redirect not followed, zero body bytes read; no manifest resolved |
| Microsoft Update Catalog search for `Visual Studio 2026 18.10.4` | One **Visual Studio 2026 Security Update (18.10.4)** entry dated **13 October**, ID `a27c8988-7811-43f2-9069-93717f5d9dba`, listed **103,365,464 bytes**; no fixed manifest reference in that search response. Details/download dialog and update payload were not requested |

The alias probe was an **inference** from Microsoft's [command-parameter example](https://learn.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=visualstudio)
using `stable.18.0/channel`; Microsoft did not publish the exact **18.10** alias
in the inspected documentation. It was tried twice, first stopping at a redirect
guard error and then retaining the explicit redirect trace. Neither request read
a response body. No additional alias permutations or synthesized fixed hash paths
were tried. The public channel index resolves to a Microsoft CDN JSON document:
**49,962 bytes**, observed SHA-256
`b7138d6e11c5affbc22472d07b8f8164c323b99672234b6e3308d0873b47eddd`.
This is a metadata receipt, not an authenticated release pin.

The [2026 servicing policy](https://learn.microsoft.com/en-us/visualstudio/releases/2026/servicing-vs)
also describes servicing updates to the last monthly update. The existence of
18.11.0 therefore does not by itself establish that 18.10.4 is unsupported.
Conversely, a release-history row or administrator-update listing does not
establish this fixed pair's consistency, native toolset closure or builder
eligibility. The update's listed size is not the bootstrapper, layout or catalog
size. No current-channel manifest or other release is substituted.

**Required to clear this discovery gap:** a publisher-referenced direct fixed
18.10.4 channel and its declared catalog URL/size/hash, matching release identity,
received-byte integrity and applicable authentication. No fixed-pair bytes were
retrieved, so this follow-up establishes neither a match nor another mismatch;
metadata signatures, bootstrapper authenticity and ARM64 compiler/SDK closure
remain unverified. The bounded search does not prove that an official pair cannot
be found elsewhere. Preserve 17.14.42 and all earlier mismatch evidence; retain
the acquisition hold and stop for review without payload acquisition or Phase B.

The attempted 2026 system-requirements documentation URL returned 404. No guest
eligibility, licensing, installed tool identity, compiler/SDK closure or exact
engine acceptance is inferred from this alternative search. Read-only metadata
research stops here; payload acquisition, bootstrapper/layout execution and
Phase B remain unapproved.

The original 17.14.42 catalog response's static contents suggest the following,
**without authenticating them**:

- Requested ARM64 selector: `Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64`;
  its `HostARM64.TargetARM64` tool package reports **14.44.35229**.
- SDK selector: `Microsoft.VisualStudio.Component.Windows11SDK.26100`, component
  **17.14.37011.9**, display title **10.0.26100.7705**; its bundle package is
  **10.0.26100.15** with **229 payload declarations**. These are different metadata
  version fields, not an observed installed SDK patch or accepted payload closure.
- The C++ workload has required MSBuild/core/redist dependencies. The ARM selector
  also references other host/target and ARM64EC packages. `--arch arm64` does not
  justify manually deleting required dependencies or claiming an ARM64-only file set.
- The catalog's Clang component has a neutral package declaration; this does
  not prove native ARM64 `clang-cl`. The separate LLVM candidate below addresses
  the proposed assembler input without accepting that unverified component.

An accepted closure must enumerate exact package identities/versions/conditions,
English resources, every payload URL/size/hash/signer, ARM64 CRT/UCRT and SDK
headers/import libraries, native `cl`/`link`/`nmake` and required setup/engine
prerequisites. Resolve conditional dependencies with the vendor's authenticated
catalog/layout rules; a naive dependency walk is not an installer resolver.
Revision 1 deliberately leaves the accepted closure, byte total and engine pin null.

### Proposed fixed-version layout commands — blocked, not executed

These are concrete review templates for **B2 in the separately approved copy**,
after resolving integrity, licensing, host identity, engine/closure and budget.
The paths are task-only examples; the private location map supplies the proposed
mapping. Check absence/ACLs first. These are not commands for the original VM.

```powershell
& 'C:\Obf30\B-20261016-01\inputs\vs_BuildTools.exe' --layout 'C:\Obf30\B-20261016-01\vs-layout' --lang en-US --arch arm64 --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64 --add Microsoft.VisualStudio.Component.Windows11SDK.26100 --quiet --wait --norestart
```

Separate proposed layout verification, after generation and receipt inspection:

```powershell
& 'C:\Obf30\B-20261016-01\inputs\vs_BuildTools.exe' --layout 'C:\Obf30\B-20261016-01\vs-layout' --verify --wait
```

Microsoft documents [layout controls](https://learn.microsoft.com/en-us/visualstudio/install/create-an-offline-installation-of-visual-studio?view=vs-2022)
and [parameter semantics](https://learn.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022).
No `--includeRecommended`, `--includeOptional`, `--fix`, `--clean` or installer
command is proposed. `--keepLayoutVersion` controls modification of an existing
layout; it does not pin a new layout's installer engine. Post-April-2023
bootstrappers obtain the latest installer by default even for a fixed product.
The engine therefore needs a separate exact approved identity before these
templates become executable. `--wait` exposes the exit; it does not prove success.

Layout generation executes vendor code and downloads packages. It writes the
layout's packages, channel/catalog/response files, certificates, setup material
and logs, and may use TEMP and installer/shared caches outside the layout.
Verification may also write logs. No claim of an ordinary-user or contained
layout process is established. Its required token, cache/TEMP locations,
prerequisites, network endpoints and all outside-layout writes must be reviewed
before B2. No UAC approval, privilege activation, certificate/policy change,
installation or automatic repair is implicit. Preserve failures and stop.

## Native tools, source and authentication

| Input | Exact selection and evidence | Remaining acceptance |
| --- | --- | --- |
| Rust | **1.99.1**, **2026-10-15**, `aarch64-pc-windows-msvc`; separate `rustc`, `cargo`, `rust-std` `.tar.xz` inputs | Acquire/archive-verify in B; review native Windows extraction/user-tree placement and notices. No rustup, proxy, auto-bootstrap or added Unix shell |
| OpenSSL | **4.0.3**, official source **55,235,667 bytes**, SHA-256 `325b5c806167c13b40b1ffeadfe0248197c00eccc4cf123ec1e28d2d2fd216d9` | Source digest/signature, full notices and version-matched recipe review in B; compilation and linked-library hashes later |
| LLVM assembler | **23.1.3**, `clang+llvm-23.1.3-aarch64-pc-windows-msvc.tar.xz`, **763,913,356 bytes**, exact fixed release asset and digest in revision 1 | Added candidate needs explicit review; verify provenance/signature and native PE payloads, required DLLs and notices before execution |
| Python | Preserve copied **3.13.16 ARM64**, GIL-enabled, `cp313-win_arm64`; retained PSF installer identity from Stage 1 | No installer reacquisition selected. Full installed runtime/headers/libs tree and installer-to-tree binding remain incomplete; D must recheck exact executable/native machine values |
| Perl | **5.42.3.1**, portable x64 ZIP, **304,765,269 bytes**, official release JSON digest | Explicit auxiliary-only emulation decision, archive safety/native-payload inventory and bundled licenses; no signature verification claimed |

The Rust manifest body SHA-256 is
`fb152be80975c194aa5fc684b2aec3a6e14e2b855efe2faa4e5f8ae6e590f463`.
Its separately retrieved published checksum matches. Existing host `gpgv`
successfully verifies the manifest's detached signature with official release
key **108F66205EAEB0AAA8DD5E1C85AB96E6FA1BE5FE**, retrieved from the
[Rust distribution key URL](https://static.rust-lang.org/rust-key.gpg.ascii)
linked by the [official installation guidance](https://forge.rust-lang.org/infra/other-installation-methods.html).
Verification used an isolated temporary keyring, without importing into the
user's keyring. This authenticates **metadata only**. Component checksum sidecars
agree with the manifest; no component archive signature or artifact bytes were
verified. The selected MSVC target has no MinGW component requirement; no other
host/target distribution or rustup bootstrap is selected.

OpenSSL's [source catalogue](https://openssl-library.org/source/) and official
release-asset API agree on the source digest. Its detached-signature issuer packet
identifies subkey **C46ED3F2CBEFDA1FDAADA44264ED7B1DCCE71CB2**, present under published
primary key **B146647E45A7B33947AB226B2A2C87D161692D40**. This is a packet/key
association, **not signature verification over absent source bytes**. Preserve
both keys/signature/checksum receipts; verify against the acquired archive in B.

The versioned [4.0.3 Windows notes](https://github.com/openssl/openssl/blob/openssl-4.0.3/NOTES-WINDOWS.md)
identify **`VC-WIN64-CLANGASM-ARM`** for MSVC C compilation with ARM64 assembly
through `clang-cl`. Their generic NASM/x86 steps do not establish an ARM64 recipe.
Propose the assembly-capable target; do not silently choose the other ARM target
or `no-asm`. [Versioned Perl notes](https://github.com/openssl/openssl/blob/openssl-4.0.3/NOTES-PERL.md)
require Perl >=5.10, Text::Template (a fallback is included in source), and
test modules including Test::More >=0.96. Review their actual bundled versions
and the complete source recipe in B; no CPAN/network fallback is approved.
The upstream notes' administrator quick-start does not authorize elevated builds:
ordinary-token usability and a user-owned prefix remain acceptance requirements.
Static OpenSSL/static CRT choices, environment/search paths, full nmake/OpenSSL
tests and reproducibility flags need the separate Stage 2 recipe review.

The OpenSSL catalogue lists 4.0 support through **14 May 2027**. The current
[advisory catalogue](https://openssl-library.org/news/vulnerabilities/) was read;
for example, CVE-2026-35189 lists affected 4.0 releases before 4.0.3. This is a
scoped metadata observation, not blanket security clearance. Refresh applicable
advisories/support for every selected component before input freeze; a new
finding stops review rather than authorizing a silent version substitution.

LLVM's fixed release metadata and parsed attestation subject agree on the archive
digest. The statement names `llvm/llvm-project`, tag `llvmorg-23.1.3` and
`.github/workflows/release-tasks.yml`; neither its Sigstore verification material
nor detached signature has been cryptographically verified. Candidate tags and
filenames are not native PE evidence. No ARM64 tool executes in Phase A.

## Python build, crate and upstream test closure

Build selections are **maturin 1.15.0 native ARM64**, **setuptools 84.0.0**,
unchanged **CFFI 2.1.1 CPython 3.13 ARM64** and **pycparser 3.0**. Their selected
release metadata satisfies Python 3.13.16 and the upstream backend constraints;
the CFFI/pycparser file declarations match the unchanged canonical lock. With
no extras selected, metadata adds no Python packages beyond CFFI's pycparser
dependency on this CPython. Do not request maturin's Zig/patchelf or setuptools
extras. Wheel contents, RECORD, bundled notices and executable architecture
remain uninspected until B.

Parsed PyPI publish statements for maturin, the cryptography sdist and matching
vectors bind the selected filenames/digests and record the publisher repositories
and workflows in revision 1. These are **parsed, unverified attestations**; no
Sigstore certificate/transparency verification or artifact comparison is claimed.
The selected setuptools/CFFI/pycparser provenance endpoints returned 404; retain
that missing-evidence distinction. Do not install a verifier or manufacture
equivalent provenance in Phase A. The approved B trust policy must specify the
existing verifier/trust roots or preserve an authentication blocker.

The tag manifest selects unmodified cryptography **50.0.2**, maturin backend,
Rust MSRV **1.83.0**, locked Cargo resolution and the recorded setuptools exclusions.
The release tag resolves to commit **4dda5c7fe4ae71b8925f2551910a0ef959df9c7a**.
GitHub reports tag verification **false / `bad_cert`**; a resolved tag is not a
verified release signature. Keep that separate from the sdist's PyPI attestation.

The upstream **root `Cargo.lock`** metadata SHA-256 is
`98778208027ce05bfff0db88c290f28355eb20e685f0c728775359fb91a1a4c4`.
Its Git blob hash matches the official tree declaration. It contains **32 registry
packages and eight workspace packages, with no git dependencies**. All 32 crates'
official API checksum declarations match the lock; all report non-yanked versions.
Revision 1 enumerates every fixed `.crate` URL, expected SHA-256, size and declared
license: **4,141,222 bytes** total. The eight workspace manifests were read at the
resolved commit; their path dependencies remain within that source workspace.

No crate body was downloaded and no Cargo command ran. In B, compare the acquired
sdist's lock, workspace manifests and metadata with these declarations before
acceptance. Safely inspect/extract the exact archives, retain package checksums
and generate a file-checksummed offline directory source map without executing
Cargo or build scripts. Later frozen/offline Cargo execution needs a separately
reviewed `source.crates-io` replacement configuration and no network. Target-
inapplicable lock entries are retained in the acquisition inventory; they are
not claimed executed. Review included notices, including self_cell's Apache/GPL
alternative, target-lexicon's LLVM exception and unicode-ident's combined notice.

The base upstream `test` group requires matching vectors, pytest, benchmark/cov/
xdist plugins, pretend and certifi. The proposed metadata closure is:

| Role | Exact candidate versions |
| --- | --- |
| Matching vectors | `cryptography_vectors==50.0.2` universal wheel; **56,362,804 bytes**, SHA-256 `51641f03a3eb4edbe9fb68e3a3574d25f86aa502d06391fffa886330d02778a0` |
| Test runner/plugins | pytest **9.1.1**, pytest-benchmark **5.3.0**, pytest-cov **7.1.0**, pytest-xdist **3.8.0**, pretend **1.0.9** |
| Required transitives | py-cpuinfo2 **10.1.1**, execnet **2.1.2**, coverage **7.16.2** (CPython 3.13 ARM64 wheel), pluggy **1.6.0**, iniconfig **2.3.0**, packaging **26.3**, pygments **2.21.0**, colorama **0.4.6**, certifi **2026.7.22** |

All **15 selected wheel** filenames/URLs/hashes/licenses are in revision 1. A
local metadata-only marker/version check for native CPython 3.13.16 Windows
finds no missing dependency edge or violated selected constraint, including the
inherited `coverage[toml]` extra. Existing canonical versions are reused where
present; new plugin/transitive versions are isolated test candidates, not project
dependency changes. No optional plugin, docs, random-order or SSH extra is selected.

The tag tree declares **117 Python test files** and upstream sdist inclusion
metadata includes tests while excluding external vectors. This does not inspect
the acquired sdist or prove complete fixture/import requirements. B must verify
that source/tests/vectors and any extra fixture/test inputs are complete. Missing
optional/backend-specific requirements or an ARM64 binary stop the affected
acceptance; do not waive tests or fetch more packages implicitly. No upstream
test or candidate import has run. The application qualification environment and
Git installation remain separately owned by #29.

## Locations, network, resource and license boundaries

The ignored private task folder contains a proposed location map and retained
metadata responses/receipts. Proposed host acquisition/copy paths were checked
absent without creating them. The exact original UTM bundle/disks, source/copy
separation, host capacity and guest path absence remain unverified decisions;
no broad host scan or guest inventory was performed. Public records use location
labels and synthetic guest paths only.

Use **HOST_INPUTS** for host-only B1, **BUILDER_INPUTS** for verified transfers,
**VS_LAYOUT** for B2, and distinct **BUILDER_WORK**, **BUILDER_REPORTS** and
**VS_INSTALL** locations inside the copy. Refuse existing task paths, links,
unexpected ACLs, shared/synced/network/removable storage, overwrite and cache reuse.
Copies inherit old material: preserve it but exclude old Python/Rust/Poetry/build
caches from every input/search path. No original-guest configuration changes.

Proposed hard review ceilings are **2 GiB for selected non-Microsoft bodies**,
**20 GiB for the eventual Microsoft layout**, and **256 MiB for metadata/sidecars**.
These are approval limits, not measured layout requirements or installer-enforced
quotas. Microsoft closure/engine sizes are unresolved, so B2 cannot yet demonstrate
compliance. Any expansion requires a revised packet. Allow no automatic retries,
updates, repair, pruning or alternate mirrors. Reserve space for original plus
full independent VM copy, host inputs, copy-local inputs/layout/tool installations,
two later clean build trees, retained output/evidence and at least **20 GiB guest
headroom**. The 128 GiB disk is a proposal; actual usage/copy cost and host RAM/CPU
capacity must be checked before C1, and guest free space before B2/C2.

Acquisition network scope is TLS-verified HTTPS to the exact rows in revision 1:
`files.pythonhosted.org`, `static.crates.io`, `static.rust-lang.org`,
`download.visualstudio.microsoft.com`, and the specified publisher GitHub release
paths, whose currently observed asset redirect host is
`release-assets.githubusercontent.com`. Metadata uses the recorded official
PyPI/crates/GitHub/vendor documentation endpoints. Allow at most three redirects,
validate **each** hop's HTTPS scheme and approved host/publisher release origin
before reading a body, and never persist signed redirect query tokens publicly.
No arbitrary GitHub repository, index/mirror, CPAN, rustup, package manager or
upstream contact is included. Unknown installer/PKI endpoints require review;
do not disable revocation/TLS checks to fit an incomplete network list.

For a direct, nonredirecting B1 row, the reviewed command shape is:

```sh
# FUTURE B1 ONLY. HOST_INPUTS must already be approved, fresh and private.
# Do not follow redirects here: a non-200 response stops for per-hop review.
curl --fail --proto '=https' --max-filesize 9713795 --output "$HOST_INPUTS/maturin-1.15.0-py3-none-win_arm64.whl" --write-out '%{http_code}\n' 'https://files.pythonhosted.org/packages/8b/10/15d4314edf130955edf2dc237aa393a8a7c10f2b9b57b89fa2f61f915659/maturin-1.15.0-py3-none-win_arm64.whl'
shasum -a 256 "$HOST_INPUTS/maturin-1.15.0-py3-none-win_arm64.whl"
```

Expected result is HTTP 200, exactly **9,713,795 bytes** and
`c7dc0c66c78d3debdd9c5aa807e861fbcbf07f3505d34b125df74c03986b0f48`.
No command in this packet was executed. For every other row, materialize its
literal reviewed URL, fresh exclusive destination and size/hash controls before
the B run; do not treat the catalogue as permission for a generic resolver.
The downloader must refuse existing destinations and enforce aggregate/per-file
limits; this template alone does not implement exclusive creation or a budget.
Retain/quarantine unexpected bytes, including redirect/error bodies, without
importing/executing them. No Microsoft download/layout command is ready now.

The [Build Tools license](https://visualstudio.microsoft.com/license-terms/vs2022-ga-diagnosticbuildtools/)
embeds a Microsoft license document, retained as documentation in the private
metadata set. Its SHA-256 is
`2f66b86a00e8d9833789897ce23d05a4a2dbea370cf39c8c1098dbc17d0e7bdc`.
The terms describe Visual Studio product rights and a separate exception to
compile/build qualifying open-source C++ dependencies; that exception restricts
development/testing of those dependencies. Maintainer review must establish
which rights cover the planned OpenSSL/cryptography work and tests. Do not assert
that the exception or Community eligibility automatically covers all activities.
Windows instance rights remain a separate decision. This packet accepts no terms.

Retain exact Python/PSF and incorporated licenses; Rust's MIT/Apache alternatives
and third-party notices; LLVM's Apache/LLVM-exception and bundled notices;
OpenSSL Apache-2.0 and incorporated notices; Python wheel license files and
Strawberry's Perl and bundled third-party terms. Declared labels are not an
included-notice audit or redistribution approval. No tools or private binary
publication is proposed.

## Executed checks, gaps and stop

Phase A executed read-only official documentation/catalog/checksum/attestation/
license research, HEAD-only artifact-size requests, metadata hashes/parsing,
Rust manifest checksum/signature verification, crate declaration comparisons,
tag/Cargo blob comparison, and Python marker/version/lock-declaration checks.
Metadata was retained privately. Initial default Python TLS trust failed;
the already installed Poetry environment's CA bundle succeeded with verification
enabled. Defuddle and selected direct documentation requests failed; official
web-reader fallbacks supplied cryptography/UTM documentation. Initial guessed
upstream manifest paths returned 404; the official tree resolved root Cargo.lock.
No failed request is reported as a verified input. A compressed documentation
response and binary PGP sidecar required format-aware inspection, not UTF-8 text.

Local validation passed: fresh strict Sphinx; local links/assets/anchors across
**48 rendered HTML pages**; JSON and typed digest/evidence-flag checks; exact
candidate counts/sizes; the 32-crate declaration comparisons; 15-wheel marker/
version closure and canonical source/CFFI/pycparser artifact declarations;
source links/fences, LF/privacy/scope and whitespace checks; unchanged Stage 1,
saved prompt, runtime/tests/CI/dependency bytes; and empty-index verification.
The initial ad hoc digest validator wrongly treated descriptive semantics text
as a digest; its type/path selection was corrected and the final check passed
without changing input evidence. Rendered catalogue download equality was also
checked. No new application/native suite or package build was warranted for
these five documentation/catalogue changes.

The subsequent discrepancy investigation adds six official metadata-only probes,
raw-response equality/length/hash and release/declaration checks, plus receipt
and preserved-starting-file checks. Fresh strict Sphinx and local references
across the same **48 HTML pages**, rendered catalogue equality, privacy/LF/scope
and diff checks passed after this follow-up. The pre-existing navigation edit
and historical Stage 1/runtime/test/dependency files are preserved. No guest or
independent-network checks, metadata signature verification or Phase B occurred.

The later alternative-release check adds 17 successful metadata requests and one
documentation 404: support/release/architecture documents, channel/catalog reads,
an 18.11.0 catalog HEAD/raw-curl comparison and an 18.10.4 bootstrapper HEAD with
zero body bytes. Both tested alternative catalog pairs fail their declared
size/hash comparisons. Fresh strict Sphinx, local references across **48 HTML
pages**, catalogue download equality, metadata receipts, prior-content
preservation, privacy/LF/scope and diff checks passed. No original observation
or candidate pin was replaced, and no payload or later-phase action occurred.

The targeted 18.10.4 follow-up adds seven successful documentation/index/search
metadata or HEAD requests, plus two alias HEAD attempts stopped at a redirect
guard (the second records the 302 destination). Prior response/receipt bytes and
all previous catalogue fields are preserved. No fixed 18.10.4 channel/catalog
body was resolved or integrity-tested. Fresh strict Sphinx, local references,
rendered JSON equality, receipt hashes, preservation, privacy/LF/scope and diff
checks were repeated for this documentation-only addition. No application suite,
package build, guest command or native qualification was run.

No tool/source/package payload bodies, VM copy/boot/provisioning, installer/layout,
Configure/backend/Cargo/compiler, candidate installation/import, native/upstream/
application test, accepted fix04 rerun, dependency/lock change or CI dispatch
occurred. Existing host tools only parsed/verified metadata; no tool was installed.

**Stop for maintainer review.** Full B remains blocked by Microsoft integrity,
exact closure/engine, rights/resources and layout-host approval. Source-byte,
archive/signature/attestation, full Python tree, complete test/notice and offline
provisioning checks remain later work. No incomplete input is frozen or accepted.
#30 stays open; #29 remains blocked for its selected ARM64 track and retains
application/#28 qualification obligations. Accepted fix04 **1 passed in 215.27s**,
original report flags and every historical failure are unchanged. Production
Windows mutation/recovery and existing-log append stay gated; AMD64 remains
unqualified. POSIX, CLI syntax/gate order, canonical dependencies, Fernet/v1 and
existing Git interruption/power-loss limits are preserved. No staging, commit,
push, PR, merge, closure, release or publication is authorized by this packet.
At handoff the three navigation/proposal/changelog edits and two new packet/
catalogue files are unstaged/uncommitted; the index is empty and HEAD remains
`e54875bfc4c2aee1d55633be622de940a2d1883f`. Private task evidence is ignored.

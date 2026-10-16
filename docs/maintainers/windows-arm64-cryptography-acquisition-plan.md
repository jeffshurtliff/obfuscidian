# Plan: ARM64 builder acquisition and provisioning — #30

**16 October 2026. Status: proposal only; no acquisition or provisioning approved.**

The maintainer requested this proposal after authorizing delivery of Stage 1.
The seven Stage 1 files were committed and pushed as
`e0cadc3dd7132edbcc01266f07992bb1943fdce3`,
**Recorded ARM64 builder inventory and input pins (#30)**. HEAD, the cached
origin ref and a live remote query matched; the tree was clean at that checkpoint.
This proposal and its navigation/changelog edits were prepared afterward. The
maintainer subsequently authorized staging, committing and pushing all five
proposal files. Verify that delivery checkpoint and current Git status from the
continuation handoff; preserve any later local changes. Git delivery does not
authorize any acquisition/provisioning/build operation.

## Recommendation and decision

Use a **separate disposable native ARM64 Windows UTM builder copy**, with
maintainer-performed administrator setup confined to that copy. The maintainer
selected this route **for the proposal only**. Preserve the original owner-proof
guest, accepted fix04 snapshot, raw reports and failed-build caches. Never install
tools into its Account A/B environments or restore it to an older baseline.

The output sought here is a licensed, input-pinned builder usable by an ordinary
account, plus an authenticated offline input set for **unchanged cryptography
50.0.2**. Provisioning does not create an accepted wheel. OpenSSL compilation,
cryptography compilation, candidate installation and #29 application qualification
remain later approvals under the [provenance plan](windows-arm64-cryptography-provenance-plan.md).

The [Stage 1 inventory](windows-arm64-cryptography-stage1.md) and
[preparation manifest](windows-arm64-cryptography-input-pins.json) remain historical
evidence, not a complete frozen builder manifest. Retain their bytes and create a
new revisioned acquisition/build-input record rather than replacing their unknown
pins with guessed values. Current guest build **26300.9711** is an inventory
observation, not an extension of accepted fix04 or exact-commit qualification.

## Approval boundaries and outputs

| Phase | Proposed action and reviewable output | Authority needed before execution |
| --- | --- | --- |
| A — next chat | Read-only metadata and exact-candidate selection; prepare the acquisition request, resource/license decisions and private location map | Submitting the bounded continuation prompt authorizes A only; no tool payload downloads or VM changes |
| B — acquisition | Download only approved inputs; create and verify a fixed-version Microsoft offline layout; inspect source/wheel/crate archives statically; produce receipts and the installation packet | Separate approval of A's concrete URLs, versions, trust checks, paths, network scope and bootstrapper/layout commands; layout generation executes vendor code even though it is not installation |
| C — builder provisioning | Create the separate VM copy; install the accepted compiler/SDK and provision isolated user build tools from B's verified inputs | Separate approval of clone identity, resources, licensing, administrator actions, installer options and exact commands |
| D — readiness and input freeze | Ordinary-token version/path/architecture checks, file inventories and full manifest review; no compilation | Included only if C's approval explicitly covers these executable checks and environment writes |
| Later Stage 2+ | Compile OpenSSL and cryptography, reproducibility, static/native acceptance, candidate installs and origin policy | Separate concrete approvals; none is included in A–D by implication |

If a required phase cannot establish its exit evidence, report that blocker and
stop the affected work. Do not use a phase name to expand its approval. No remote
CI, external builder access, spending, new accounts or policy/security-setting
changes are proposed for automatic execution.

## Builder specification and preservation

1. **Source and copy:** after approval, the maintainer identifies the original
   UTM entry and confirms no owner-proof process is still active. Record its
   private source identity and reports before a normal shutdown; do not rerun
   proof. UTM documents a [copy action](https://docs.getutm.app/basics/actions/)
   that includes the VM's data. Make a full independent copy, not another library
   reference to the same writable disk. Verify distinct bundles and writable
   backing files; never resize, overwrite or delete the original. Do not scan
   unrelated host storage to find a guest.
2. **License and resources:** the maintainer must confirm Windows rights for a
   separate builder instance and review Microsoft tool terms. No entitlement,
   activation workaround or paid purchase is assumed. Proposed budget: four
   virtual CPUs, 8 GiB RAM and a 128 GiB builder disk, subject to actual host capacity
   and approval. These are engineering allocations, not vendor minima or an
   instruction to resize now. Measure layout size, guest free space and host
   capacity for an independent VM copy plus layout, two later clean build trees
   and retained evidence; approve actual paths/size limits before writes.
3. **OS suitability:** record copy OS edition, full revision/channel and UTM
   configuration. Verify compatibility with the selected tool versions and
   exclude S mode or unsupported/pre-release configurations. If the current
   copy cannot meet vendor requirements, stop and propose an explicitly licensed
   supported ARM64 guest separately; no OS upgrade/reinstall is authorized here.
4. **Accounts:** reuse the copied existing setup administrator for approved
   installation only, with the maintainer entering credentials directly. Reuse
   an existing copied standard account for readiness and all later builds/tests.
   Do not create users, demote/promote accounts, enable privileges or weaken UAC,
   Defender, execution policy, ACLs or TLS validation. No password collection.
5. **Isolation:** use fresh task-specific directories and an isolated Python
   build environment in the copy; do not reuse copied Poetry/build/Rust caches.
   Preserve them without importing from them. Keep public source inputs separate
   from private reports and installer receipts. Resolve concrete private paths
   in A; public documents use labels such as `BUILDER_INPUTS` and `BUILDER_WORK`.
   Disable no security controls to make an installer or tool run.
6. **Offline use:** acquisition is the declared network phase. Provisioning and
   later compilation must use the verified offline set, with implicit downloads
   disabled. Disconnecting the builder's network for later offline work needs
   its explicit UTM action recorded in C's approval. Do not change the original
   guest's network, shared folders, tools or account state.

## Concrete candidate inputs

These are proposed exact release candidates or component selectors, **not
verified installed tools or accepted artifact bytes**. Recheck vendor availability,
support and relevant advisories when freezing inputs. A changed release requires
a new recorded candidate and review; never substitute a moving channel silently.

| Input | Proposed candidate and acquisition source | Acceptance before provisioning/use |
| --- | --- | --- |
| Microsoft C/C++ Build Tools | Visual Studio 2022 **17.14.42**, installer build **17.14.37806.7**, from the **fixed-version Build Tools** link in the [release history](https://learn.microsoft.com/en-us/visualstudio/releases/2022/release-history) | Record exact redirected Microsoft URL, bootstrapper SHA-256/signature chain and fixed channel/catalog identities; a page entry is not package authentication |
| Compiler/SDK selectors | `Microsoft.VisualStudio.Workload.VCTools`, `Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64`, `Microsoft.VisualStudio.Component.Windows11SDK.26100`, plus only their required dependency closure | Resolve exact package versions/digests, native ARM64 host compiler/linker/nmake and ARM64 CRT/UCRT/SDK headers/import libs from the selected catalog; selectors alone do not freeze patch versions |
| Rust/Cargo | **1.99.1**, native host and target `aarch64-pc-windows-msvc`, minimal distribution, from the [official release](https://blog.rust-lang.org/2026/10/15/Rust-1.99.1/) and versioned distribution manifests | Record dated manifest, per-component archives/hashes, release authentication/trust anchors and bundled licenses. No floating `stable`, auto-update or automatic Visual Studio bootstrap |
| CPython ABI | Existing verified **3.13.16 ARM64**, GIL-enabled, using the retained PSF-signed installer identity from Stage 1 | In the builder copy verify the explicit runtime, all required include/libs/runtime files, actual native/process machine values and full selected-tree hashes. Do not reinstall in the original guest or assume the copied tree is authenticated by version alone |
| OpenSSL | **4.0.3** official source, detached signature and checksum, through the [official catalogue](https://openssl-library.org/source/) | Verify source digest, release signer/trust anchor, applicable notices/support/advisories and version-matched Windows recipe; source bytes acquired only in B, compilation remains later Stage 2 |
| Maturin | **1.15.0**, `maturin-1.15.0-py3-none-win_arm64.whl`, [official PyPI release](https://pypi.org/project/maturin/1.15.0/) | Verify archive hash, attestation identity/digest where available, METADATA/WHEEL/RECORD and ARM64 executable payload; select no extras or source fallback |
| Setuptools | **84.0.0**, `setuptools-84.0.0-py3-none-any.whl`, [official PyPI release](https://pypi.org/project/setuptools/84.0.0/) | Satisfies the recorded exclusions; authenticate full wheel and metadata/transitive requirements, retain MIT notices. Not installed or backend-executed here |
| CFFI / pycparser | **2.1.1 / 3.0** and exact compatible wheel declarations in unchanged `poetry.lock` | Reacquire only approved official wheel bytes in B; compare canonical hashes and inspect RECORD/native ARM64 payload. Installed metadata from Stage 1 is not a wheel receipt |
| Perl — conditional auxiliary exception | Strawberry Perl **5.42.3.1**, portable x64 package listed in its [official release metadata](https://strawberryperl.com/releases.json) | This is **x64 host emulation for a build-script tool**, not native Perl or AMD64 qualification. Requires an explicit auxiliary-only emulation decision; otherwise Perl stays blocked. Freeze package contents/licenses and prevent bundled GCC/OpenSSL from entering the compiler/library search path |
| Make / assembler | Native MSVC `nmake` from the selected toolset; exact ARM64 assembler/LLVM requirement determined from authenticated OpenSSL 4.0.3 notes/configuration | Do not infer an ARM64 recipe from generic NASM/x86 examples. If LLVM/another assembler is needed, add its exact native host package to the packet before acquisition; do not disable assembly/algorithms or switch compilers opportunistically |
| Rust crates | The **unchanged upstream cryptography 50.0.2 Cargo.lock**, including every registry/git/path dependency | Static parse first; freeze lock hash, full crate URLs/checksums/licenses, referenced source revisions and offline source map. No Cargo resolution, update, vendoring command or build-script execution in A/B |
| Upstream tests/vectors | Matching **cryptography 50.0.2** source/tests/vectors and their complete test-only dependency closure | Determine exact source contents/fixture requirements statically, pin official archives/wheels and notice files; no extras auto-resolution, source fallback, unreviewed test execution or network during later tests |

The [component directory](https://learn.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools?view=vs-2022)
supplies selectors, not the package closure for every installer release. Confirm
`Hostarm64/arm64` executables and ARM64 libraries in the actual selected layout.
Do not request the Visual Studio Python workload; Python is independently
provided. The [ARM64 tooling documentation](https://learn.microsoft.com/en-us/visualstudio/install/visual-studio-on-arm-devices?view=visualstudio)
describes native C++ support; it is not proof of this cryptography build working.

The Rust candidate is above cryptography's recorded 1.83.0 MSRV; that alone does
not establish source compatibility or reproducibility. Prefer a fixed complete
Rust distribution over an unpinned rustup bootstrap. If rustup is selected for
installation, its own exact version/hash/host architecture and no-auto-bootstrap
behavior must first enter B's packet. Cargo/rustc/version probes execute tools
and therefore belong to D after approval, not this proposal.

### Published candidate digests, not acquired-byte verification

| Candidate file | SHA-256 read from official metadata on 16 October |
| --- | --- |
| `maturin-1.15.0-py3-none-win_arm64.whl` | `c7dc0c66c78d3debdd9c5aa807e861fbcbf07f3505d34b125df74c03986b0f48` |
| `setuptools-84.0.0-py3-none-any.whl` | `51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670` |
| `strawberry-perl-5.42.3.1-64bit-portable.zip` | `6a081a811781c30aca51dbc036afd93092af91e3297901f02c17043795a10690` |

These three values are proposed expected hashes only. No archives were downloaded
or verified against them. Maturin's PyPI page reports Trusted Publishing and
attestation material; setuptools reports no Trusted Publishing for this upload.
Record that distinction rather than inventing equivalent release authentication.
The [Rust Windows target documentation](https://doc.rust-lang.org/stable/rustc/platform-support/windows-msvc.html)
distinguishes host tooling from target support. Perl's official metadata reports
`MSWin32-x64-multi-thread`; a compatible tag/name is not PE validation.

## Phase A — prepare the acquisition approval packet

**Inputs:** this proposal, Stage 1 records, current branch and primary vendor metadata.
**Output:** a reviewable request; no installation, payload acquisition or VM mutation.

1. Verify branch/status/HEAD and preserve all new local edits. Record the pushed
   checkpoint separately from the proposal delivery checkpoint. Read #17/#29/#30 and
   the existing plans; do not resume #29. Start with a fresh read-only account/token
   check if any guest observation is needed; do not reuse shell variables.
2. Resolve builder-copy identity and confirm source/copy separation, licensing,
   existing administrator/standard accounts and resource budget as **decisions**,
   without copying, booting a new copy, resizing disks or changing configuration.
3. Capture exact primary release metadata/URLs, support/advisory status, terms,
   proposed architectures and initial trust anchors. Fetch/save documentation,
   catalogs/checksums/attestation metadata only. No `.exe`, `.msi`, wheel, crate,
   toolchain or source archive payload downloads in A. A required binary metadata
   inspection must be proposed as B work instead of executed implicitly.
4. Resolve source review gaps: the exact OpenSSL 4.0.3 Windows notes and checksum
   and Rust 1.99.1 distribution metadata were not retrievable through this turn's
   web reader. Retry through official read-only metadata endpoints; if still
   unavailable, keep unknown hashes/recipe requirements explicit. Moving OpenSSL
   `master` notes are context only, never a version-matched build recipe.
5. Prepare B's exact download and Microsoft layout commands, network origin list,
   download limits, new private output paths, expected hashes/signers and abort
   behavior. Separate bootstrapper download/verification from its later execution.
   Document any bootstrapper digest available only after acquisition and the
   vendor-signature/catalog trust check required before executing it.
6. Ask the maintainer to approve that concrete B packet, including any proposed
   Perl-only x64 emulation. Stop; elapsed time or selecting the builder-copy
   preference does not approve downloads, cloning or administrator setup.

**Validation:** selected official metadata supports each proposed release/file;
digest formats and constraints check; no unknown pin is labeled verified; original
VM and repository runtime/dependency files unchanged. Report missing metadata.

## Phase B — acquire inputs and produce the installation packet

**Prerequisite:** explicit approval of A's packet. Work in new private task-only storage.

1. Download approved inputs with TLS verification and fixed filenames/URLs.
   Reject redirects outside reviewed vendor/publisher hosts, yanked/mismatched
   files, unknown extras and overwrite/reuse of prior attempt directories.
   Record URL, size, SHA-256, published digest, signature/attestation status,
   publisher/trust anchor, license/notice identity and host/target architecture.
2. Verify the approved Microsoft bootstrapper before execution. After separate
   approval of its exact command, generate only the specified fixed-version
   offline layout with the component closure and English resources; do not
   install while making the layout. Use Microsoft's documented
   [offline layout and validation controls](https://learn.microsoft.com/en-us/visualstudio/install/create-an-offline-installation-of-visual-studio?view=vs-2022).
   Preserve bootstrapper/channel/catalog manifests, catalog signatures and all
   package digests. Do not use evergreen shortcuts or unbounded recommended/
   optional workloads. Reject an unexpected version or dependency expansion.
3. Inspect sources/wheels/crates without executing code, importing modules,
   resolving packages or running setup/build hooks. Check safe archive paths;
   hash the original archives and version-matched build metadata. Enumerate the
   complete Cargo.lock and test-input closure, including any nonregistry inputs.
   Preserve cryptography source and Cargo.lock exactly. Pin all backend and test
   transitive inputs; a missing wheel or crate stops acquisition acceptance.
4. Produce a revisioned input receipt, signed-catalog/package validation log,
   private location map, source/test/license inventory and `.vsconfig`/component
   closure for review. The SDK selector's exact patch, toolset executable versions,
   Rust component hashes, Perl exception and assembler choice must now be concrete.
5. Present C's reviewed commands and expected writes: clone operation, copy-only
   resource changes, compiler/SDK installation, required installer prerequisites,
   isolated user-tool provisioning, network limits and any reboot. Stop for approval.

**Validation:** acquired bytes match accepted hashes/trust evidence; Microsoft
layout verifies; sources/locks are unchanged; no tools installed and no build
backend/Configure/Cargo command executed. Layout generation is recorded vendor
tool execution and cannot be described as a read-only action.

## Phase C — provision only the approved builder copy

**Prerequisite:** reviewed B outputs and explicit clone/installation approval.

1. The maintainer creates/identifies the full independent copy, applies only
   approved copy-specific resource changes, verifies original source preservation
   and accepts applicable Windows/tool terms. No automated credential entry.
2. From the existing copy's setup administrator, install only the accepted offline
   MSVC/SDK layout with network fallback disabled (`--noWeb` as documented), the
   reviewed component closure, a new copy-local install path and no automatic
   reboot. Stop on unexpected prerequisites, elevation beyond the approved setup,
   system-policy requests or changed versions; do not install more components ad hoc.
3. Return to the existing standard account. Verify medium integrity/no admin
   membership before provisioning isolated user tools. Use fresh task-specific
   Rust/tool/Python directories; retain the existing base interpreter and Poetry
   environments. Install only accepted wheel/tool payloads, offline and hash
   checked, with no dependency/source fallback and no global index/config changes.
   Installing build-tool wheels is part of this future C approval, not a change
   to canonical Obfuscidian dependencies or permission to run their backends.
4. Use session-local compiler/SDK/tool search paths with explicit native ARM64
   host/target selection. Exclude Strawberry's bundled compiler, libraries and
   unrelated copied caches. If approved Perl-only x64 emulation is needed, record
   it explicitly; no emulated Python/compiler/linker/Rust substitute is accepted.
   No OpenSSL or cryptography compilation, `Configure`, Cargo build or backend run.

**Validation:** install exits/components/versions match B; original VM untouched;
fresh build-tool environment and selected inputs recorded; no application install
or dependency/lock modification. Stop and retain failed provisioning evidence.

## Phase D — ordinary-user readiness and freeze, then stop

Run only explicitly approved version/identity commands against verified installed
tools: Python stdlib/native-machine checks; compiler/linker/nmake/SDK version
reporting; explicit native Rust/Cargo version reporting; approved Perl version;
and package metadata/static payload checks. Do not run a compiler smoke, OpenSSL
Configure, backend hooks, test suites or candidate imports under a readiness label.
Use the selected executables directly; prevent Rust proxy downloads/auto-updates.

Record PE machines, exact versions, SDK include/lib/bin identities, Python ABI and
full selected headers/libs hashes, tools/licenses, current ordinary token, copy
OS/storage and installer receipts. Prepare an immutable full input manifest and
ordinary-user builder description, binding source/Cargo.lock/crates/backend/test
inputs and accepted auxiliary emulation. No missing or unverified input may be
represented as frozen. Report the remaining OpenSSL source-to-library gap: library
hashes exist only after a separately approved build and are not invented here.

**Exit:** reviewed provisioned builder plus complete pre-build inputs, or explicit
blocked result. Next comes a separate Stage 2 recipe/build approval: OpenSSL flags,
static linkage/runtime choices, offline frozen Cargo/backend invocation and two
clean reproducibility runs. A provisioned builder is not an accepted artifact,
native application qualification or canonical private-wheel consumption policy.

## Licensing, risks and failure handling

The [Build Tools license](https://visualstudio.microsoft.com/license-terms/vs2022-ga-diagnosticbuildtools/)
and [Microsoft licensing guidance](https://www.microsoft.com/licensing/guidance/Visual-Studio)
must be reviewed for this open-source dependency build and any retained or
redistributed tools. No Community edition eligibility, Windows VM entitlement,
license acceptance or zero-cost provisioning is asserted by this proposal.
Rust/compiler bundles, Perl's bundled third-party tools, OpenSSL and Python
require their exact included notices recorded; metadata license labels alone
are insufficient for a complete redistributed provenance bundle.

Native compiler/Rust/Python targets do not make Perl native. Offline Visual Studio
layout creation executes a downloader, installation can introduce prerequisites,
and an SDK family/component ID can select a different patch later. Preserve
fixed catalogs and receipts, and refuse changes rather than normalizing them.
Do not treat upstream MSRV, a valid signature or a compatible filename as a
successful build/test. No fresh OpenSSL advisory clearance is claimed here.

On failure, stop and retain logs/quarantine mismatched inputs. Do not repair the
original VM, purge old caches, change dependency versions or use a private wheel
already satisfied by version. Preserve the copy until evidence review; deletion
or reverting it requires a specific later maintainer action, never deletion of
the source guest. No automatic cleanup/pruning or rollback of unknown state.

## Current execution and handoff

Executed in this proposal turn: authorized Stage 1 staging/commit/push, read-only
live remote-tip verification, official metadata/document research and local
documentation/consistency/privacy/diff validation. No VM copy, payload acquisition,
installation, source/backend execution, compilation, dependency change or remote
CI dispatch occurred. The existing Test workflow ignores `docs/**`; no hosted
CI success is inferred from this documentation-only push.

Strict fresh Sphinx and rendered local links/assets/anchors across **47 HTML
pages** passed. Candidate digest-format, continuation-prompt boundary,
privacy/LF/scope, unchanged Stage 1/runtime/dependency bytes, empty index and
diff checks passed. Package/native tests, installer/layout execution and full
external link/advisory/signature verification were not performed. The proposed
payload hashes above remain metadata observations, not acquired-byte checks.

Use the [next-chat prompt](windows-arm64-cryptography-next-chat.md) to start
**Phase A only**. It does not grant B–D or Stage 2 approval. #30 remains open;
#29 stays blocked for the selected ARM64 track, retaining #28 and application
qualification. Production Windows mutation/recovery and existing-log append
remain gated; AMD64 unqualified. Preserve POSIX, CLI syntax/gate order,
Fernet/v1, canonical dependencies and existing Git interruption/power-loss limits.

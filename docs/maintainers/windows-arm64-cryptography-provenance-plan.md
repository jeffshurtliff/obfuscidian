# Plan: trusted native ARM64 cryptography artifact — #30

**16 October 2026. Status: Stage 1 bounded read-only inventory delivered; build feasibility blocked.**

The [Stage 1 report](windows-arm64-cryptography-stage1.md) and
[input-pin preparation manifest](windows-arm64-cryptography-input-pins.json)
record current guest observations and unresolved inputs. No usable authorized
existing builder was established; the manifest is incomplete and not approved
for build execution. No acquisition, installation or later stage follows from
this blocked finding. The approval/handoff history below is preserved.

[Issue #30](https://github.com/jeffshurtliff/obfuscidian/issues/30) owns this
artifact work as a child of #17 and sibling of #29. Issue #29 remains open and
blocked for its selected ARM64 track; application qualification stays there.
The existing #28 dependency and original broad criteria remain intact. No
compiler, build, candidate installation, dependency-origin change or production
enabling approval follows from the split. Stage 1 continued in a separate chat
on the existing branch, preserving all commits and any subsequent local work.
The maintainer separately authorized committing and pushing the accumulated
#17/#29/#30 handoffs on 16 October. Verify the actual current branch HEAD and
status at continuation; the old owner snapshot base is historical evidence,
not an instruction to reset. This Git authorization does not authorize any
build or later qualification stage.

## Decision and current feasibility

Prepare a controlled, same-version private build of **unmodified cryptography
50.0.2** as the conditional engineering route. It must pass the provenance,
rebuild, native execution and dependency-origin gates below before use in further
qualification. Prefer an authenticated upstream ARM64 artifact if upstream resumes
publication, but no such artifact is available or promised. Do not downgrade,
patch cryptographic code or change algorithms, Fernet/v1, public APIs or runtime
dependency versions to get a build through.

This route is **not currently executable under the established environment**.
The only available guest lacks the linker, and a complete licensed builder,
Windows SDK, Rust and OpenSSL input set has not been established. Standard
Visual Studio/MSVC provisioning is not a demonstrated per-user solution:
[Microsoft requires administrator permissions for initial Visual Studio installation](https://learn.microsoft.com/en-us/visualstudio/ide/user-permissions-and-visual-studio?view=visualstudio).
No elevation, new accounts, policy changes or compiler installation is proposed
for the two existing standard test sessions. No external builder, credentials,
spending, machine provisioning or remote CI is authorized by this document.

The approved Stage 1 task is **read-only build-feasibility and input-pin
preparation only**: inventory already present tools, identify a suitable
pre-provisioned builder if one exists, and finish the immutable input manifest.
Use known task-relevant locations, with no broad private-file or credential
discovery. If no builder exists, report that blocker and leave unresolved pins
explicit; do not substitute an installer command or invent authenticated inputs.
Approval to evaluate feasibility does not approve compilation or installation.

## Evidence reviewed for this proposal

- The prior non-installing audit finds compatible locked wheel metadata for
  36 of 37 applicable packages; cryptography 50.0.2 is the sole missing native
  binary. Both earlier failed source installs remain failed and preserved.
- Upstream [46.0.4 removed Windows ARM64 wheel support](https://cryptography.io/en/50.0.2/changelog/#v46-0-4).
  Its [removal decision](https://github.com/pyca/cryptography/pull/14216) cites
  problems maintaining the ARM64 CI image and removes building/testing. This
  does not prove a custom build impossible, but upstream ARM64 build/test
  coverage must not be assumed. Maintaining this private artifact becomes an
  explicit project responsibility.
- The official 50.0.2 sdist was read in memory and its complete SHA-256 compared
  with both current PyPI metadata and the unchanged project lock:
  `7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5`.
  Only static TOML/archive inspection occurred; no archive was extracted or
  source/build backend executed. Comparing hashes is not signature verification.
- Its build backend is maturin; requirements include maturin `>=1.14.1,<2`,
  CFFI `>=2.0.0` for this CPython, and setuptools excluding 74.0.0, 74.1.0,
  74.1.1 and 74.1.2.
  Cargo specifies Rust `1.83.0` minimum and `locked=true` in maturin configuration.
  The actual upstream Cargo lock pins PyO3 0.29.2, openssl 0.10.81 and
  openssl-sys 0.9.117. Constraint lower bounds are not the complete pinned build
  environment; do not resolve them afresh at build time.
- The [50.0.2 wheel baseline](https://cryptography.io/en/50.0.2/changelog/#v50-0-2)
  uses OpenSSL 4.0.3. Propose that same statically linked OpenSSL baseline,
  subject to exact source/signature verification and a fresh supported-release
  and advisory review at input freeze. The [official source catalogue](https://openssl-library.org/source/)
  lists the source/checksum/signature and release trust anchors. Those signatures
  have not been verified in this turn.

## Routes and selection

| Route | Use and boundary |
| --- | --- |
| Upstream resumes a compatible authenticated 50.0.2 ARM64 wheel | Preferred input if it appears; verify identity, tags, attestation/hash and regenerated Poetry artifact metadata before acceptance. Its existence is not assumed |
| Controlled private build of unchanged 50.0.2 | Recommended conditional engineering route; same runtime versions, new artifact origin/hash, full obligations below; builder and origin-policy blockers unresolved |
| A later maintained upstream release with an official ARM64 wheel | Would require a separate dependency revision, regenerated lock and compatibility/security review; not selected or approved |
| Old ARM64 wheel or anonymous third-party binary | Rejected for this proposal. Earlier wheels do not satisfy `cryptography>=50.0.2` or the current source/provenance baseline |

Source hash, wheel RECORD, a successful build and a publisher identity each
answer different questions. None alone establishes a trusted or qualified
runtime. Do not reuse upstream source attestations to claim upstream signed or
endorsed our private output; [PyPI attestations bind a particular file digest](https://docs.pypi.org/attestations/).

## Stage 1: builder feasibility and immutable input manifest

**Output:** a reviewable manifest and builder description; no compilation.

1. Under the Stage 1 approval, perform read-only inventory of already installed
   compiler/linker/SDK, Rust/Cargo, Python, build backend and OpenSSL inputs.
   Record versions, executable hashes, architecture, licensing/provenance and
   whether they are usable without elevation. Existing cache contents from the
   failed build are evidence to preserve, not automatically trusted tools.
2. Prefer an already provisioned native Windows ARM64 builder. A separately
   approved Windows cross-builder may target ARM64 if its full target ABI,
   Python development files, libraries and host/target identities are recorded.
   Cross-compilation is not native runtime validation or AMD64 qualification.
   No builder is presently identified; do not provision one or dispatch CI.
3. Freeze exact versions and authenticated hashes for every input below before
   seeking any build approval. No floating stable channel, unbounded build
   isolation download, package-manager bootstrap or dependency auto-update.

| Input | Required pin and acceptance evidence |
| --- | --- |
| cryptography source | Official 50.0.2 sdist and SHA-256 above; release publisher/provenance verification where available; unchanged source tree and Cargo lock |
| Python ABI | Native ARM64 GIL-enabled CPython 3.13.16 development/runtime inputs, installer provenance/hash, actual process machine evidence; no free-threaded or emulated substitute |
| C/C++ linker and Windows SDK | Exact compatible MSVC/SDK component versions and vendor-authenticated package or existing installation identity; supported ARM64 target libraries; licensing and no-elevation feasibility |
| Rust/Cargo | Exact mutually compatible toolchain release, compiler/standard-library target and vendor authentication; satisfy source MSRV, use upstream Cargo lock and verified crate checksums |
| OpenSSL | Candidate 4.0.3 source, verified published SHA-256 and signature/trust anchor, full build flags and linked-library hashes; reject newly unsupported/vulnerable input at freeze |
| OpenSSL build tools | Exact upstream-required Perl, make/assembler and auxiliary-tool versions and authenticated inputs for the chosen Windows ARM64 recipe; no automatic tool acquisition |
| Python build tools | Exact maturin, setuptools, CFFI 2.1.1 and pycparser 3.0 plus applicable transitive build requirements; satisfy upstream constraints and verify official wheel hashes |
| Upstream test material | Matching cryptography tests/vectors and any additional test-only packages, separately pinned and hashed; no unreviewed test code or network fetch during execution |

Compiler/SDK, exact Rust release, maturin/setuptools pins and OpenSSL signature
verification are **open inputs**, not filled by the old failed-build log. Building
is blocked until the completed manifest and builder are reviewed. Build/test-only
materials do not become Obfuscidian runtime requirements or a maintained second
runtime dependency list. Raw host paths, account IDs and logs stay private; no
credentials or full environment dumps enter reports.

## Stage 2: reproducible controlled build — separate approval required

**Input:** accepted Stage 1 manifest and a specifically authorized builder.
**Output:** quarantined unsigned candidate wheel, two build records and provenance.

1. Verify all acquired materials before build execution, with TLS/signature
   validation retained. Use a fresh synthetic build workspace without vaults,
   keys, credentials, repository secrets or the existing account test reports.
   Only the acquisition step may fetch declared inputs; compilation is offline.
2. Build unchanged source using the approved PEP 517 backend and exact tools.
   Preserve upstream Cargo.lock and locked resolution, with offline crate access
   and checksum validation; [Cargo frozen mode](https://doc.rust-lang.org/cargo/commands/cargo-build.html#manifest-options)
   combines locked/offline behavior. The concrete backend invocation must be
   reviewed rather than assuming every maturin/backend flag is interchangeable.
   Fail on any missing crate, tool, Python build dependency or target input.
3. Statically link the approved ARM64 OpenSSL build, following the reviewed
   upstream Windows build contract. Capture compiler/linker commands, flags,
   feature choices, exact build dependencies and imported runtime DLLs. Do not
   patch crypto code, disable security checks or remove algorithms to compile.
4. Build twice from fresh, separately initialized workspaces with the same
   pinned inputs and reviewed deterministic environment. Require identical
   unsigned wheel SHA-256. If hashes differ, preserve both outputs, compare
   archive/PE payloads and stop for a reviewed reproducibility correction.
   Do not silently strip, retag, resign or normalize binaries to call them equal.
   Repeated builds on one builder establish reproducibility, not independence
   from a compromised builder; seek a second trusted builder when available.
5. Preserve exact backend-produced filename/version/tags. Mark the private
   origin and SHA-256 in the provenance record; never rename an AMD64/macOS/old
   wheel or advertise a broader ABI/version than it actually implements.

The provenance bundle must bind source and all input digests, builder identity,
host/target architectures, recipe identity, commands/flags, both output hashes,
linked OpenSSL identity, file inventory/licenses, test results and review status.
Sign or attest the private output using a separately approved existing identity
where available; the consumer must verify that identity and output digest.
No signing key, password, account or external publication is created here.
Missing provenance or unequal rebuilds leave the candidate unaccepted.

## Stage 3: static and native artifact acceptance — separate approval required

**Output:** an accepted engineering artifact only, not an application beta.

- Inspect without import first: wheel filename/WHEEL/METADATA compatibility with
  the native 3.13.16 tag set, package identity/version, RECORD digests, expected
  contents, licenses and a complete inventory of executable/native payloads.
  All shipped PE extension/DLL machine fields must be ARM64 `0xAA64`; enumerate
  runtime imports and reject undeclared libraries or dependence on build paths.
  A compatible filename alone does not establish the PE architecture.
- Verify the authenticated manifest and selected artifact hash again after
  transfer. Use a fresh per-user native environment on internal guest NTFS with
  original standard accounts, no elevation, no source checkout on import paths
  and no source-build fallback. Preserve the existing owner-proof environment.
- Execute the full applicable matching upstream test suite for the enabled
  backend, recording every failure and skipped case rather than selecting only
  successful algorithms. Test
  cryptography imports, actual linked OpenSSL identity, generated-key Fernet
  round trips, existing synthetic v1 decode, wrong-key rejection, token tampering,
  byte preservation and both generated Windows/POSIX exchange directions before
  any beta acceptance. Do not claim that a Fernet smoke replaces upstream tests
  or that old AMD64 results validate this wheel.
- Record native `IsWow64Process2` evidence, installed module location, dependency
  versions, `pip check`, payload hashes, application/format test results and
  zero production dispatch changes. If a test needs a new dependency, package
  version, privilege or unavailable fixture, record the gap and seek review.

No code is imported from the candidate until static/provenance review and
execution approval. ABI-compatible tags do not qualify other Python versions,
other OS builds, AMD64, emulation or physical ARM machines.

## Stage 4: dependency-origin and packaging policy — separate approval required

The canonical `poetry.lock` currently authenticates the upstream sdist and
published wheels; it does **not** contain the new private wheel hash. Neither
preinstalling the same version nor a later successful `poetry check --lock`
turns that artifact into a canonical locked dependency. Do not install it over
the current environment, hand-edit the lock, disable hash checks or pretend an
unchanged version implies an unchanged dependency source.

Propose a disposable qualification-project copy derived from the canonical
`pyproject.toml`/`poetry.lock`, outside the checkout. Only after origin-policy
approval, explicitly bind cryptography 50.0.2 to the reviewed immutable artifact
or an approved explicit package source and let Poetry regenerate the derived
qualification lock. Require a complete diff: all 37 applicable package versions
and all unrelated origins stay unchanged; only the approved artifact/source
binding changes. Preserve both lock hashes and label the derived lock as an
engineering qualification candidate, not the canonical project's passing lock.
No second hand-maintained runtime requirements list is introduced.

The source mechanism itself needs a small reviewed experiment: either a local
private wheel binding in the disposable copy or a maintainer-approved immutable
explicit package source. Do not configure a global/supplemental catch-all index
or deploy an artifact server now. [Poetry source constraints](https://python-poetry.org/docs/repositories/)
do not propagate into installed package metadata, so ordinary pip installation
would not inherit this private source. No private absolute path or credential may
leak into distributed Obfuscidian metadata. Build release-candidate packages
from approved canonical metadata, not a temporary local-path experiment.

For a later lab-beta handoff, propose an immutable reviewed wheelhouse and a
generated per-platform hash manifest derived from the one approved Poetry input
and candidate artifact identity. [Pip hash enforcement and binary-only mode](https://pip.pypa.io/en/stable/topics/secure-installs/)
must apply to the complete dependency set, with network/source fallback disabled.
This manifest is a generated transport/verification artifact, not another
maintained dependency list. Both wheel and sdist installed-command acceptance
must use that same selected artifact and prove its origin rather than merely
finding an already satisfied version.

Current `.github/scripts/check_artifacts.py` downloads binary dependencies from
the configured index, and `tests/integration/test_packaging.py` accepts an offline
wheelhouse but does not enforce this new per-file provenance policy. A future
reviewed change must select only the accepted wheelhouse/manifest, reject unknown
or mismatched files and retain the original default behavior. No packaging tool,
dependency metadata, lockfile or workflow is changed by this proposal. If an
approved canonical dependency-origin policy cannot be established, the artifact
may remain engineering evidence but cannot support a reproducible distributed beta.

## Stop conditions, maintenance and the next approval boundary

No verified builder, incomplete pins, failed signatures, source changes, new
runtime versions, unapproved transitive inputs, non-ARM native payload, unknown
DLL lookup, unequal rebuilds, failed tests or unresolved source/lock policy stop
the affected stage. Keep raw outputs and all earlier failures; do not clear
caches or repair/delete uncertain fixtures as part of this work.

Private artifact maintenance requires a named maintainer decision for ownership,
future advisory checks, rebuild/revalidation and secure retention/revocation.
If cryptography, OpenSSL, compiler, Python ABI or build inputs change, freeze a
new artifact identity and requalify affected evidence. A trusted source and hash
do not provide a guarantee that native crypto code has no vulnerabilities.

**Authorization boundary: Stage 1 read-only feasibility/inventory and input-pin
preparation only.** The bounded inventory has now delivered the linked report
and incomplete manifest with a blocked builder finding. Stage 1 stops here;
missing inputs do not authorize installation or another execution stage.
No compiler install, build, custom wheel install,
dependency/source/lock change, upstream contact, account creation, policy change,
remote CI, stage/commit/push/PR/merge or publication follows from it. Later stages
need separately scoped approval of their concrete artifacts and commands. There
is no guest build command to run yet. The accepted owner proof remains intact;
production Windows mutation/recovery and append remain gated; AMD64 unqualified.

## Validation of this proposal

For the subsequent Stage 1 inventory and validation evidence, see the
[executed report](windows-arm64-cryptography-stage1.md). The paragraph below
describes the preceding proposal preparation, not a new source/build execution.

The preceding proposal preparation performed official-document research and
hash-verified in-memory source inspection only, then documentation/privacy/diff
checks. The issue split and handoff add no builder inventory or guest execution.
No compiler is installed, source executed, wheel built, dependency changed or
native application test run.
Keep the [approved ARM-only qualification target](windows-arm64-beta-qualification-plan.md)
and broad #17/#29 obligations separate from this dependency proposal.

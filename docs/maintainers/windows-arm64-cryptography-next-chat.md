# Next-chat prompt: #30 acquisition approval preparation

**16 October 2026. Phase A only; no payload acquisition or provisioning.**

The [acquisition/provisioning proposal](windows-arm64-cryptography-acquisition-plan.md)
is ready for review. Submitting the prompt below authorizes its read-only Phase A
and preparation of a concrete Phase B approval packet. It does not approve
downloads of tool/source/package payloads, cloning or installation. The maintainer
authorized a separate commit/push of the five proposal files after the Stage 1
checkpoint. Use the resulting proposal commit from the continuation handoff and
verify actual status; preserve any subsequent local changes.

```text
Continue only Obfuscidian #30, Phase A of the ARM64 builder acquisition/provisioning proposal.
Use the existing Obfuscidian checkout and preserve its commits and every local change.
Do not reset, start from main, replace the checkout or discard work.

Expected branch: feature/17-add-safe-native-windows-support
Pushed Stage 1 checkpoint: e0cadc3dd7132edbcc01266f07992bb1943fdce3
Commit: Recorded ARM64 builder inventory and input pins (#30)
Proposal checkpoint: use the resulting commit supplied in the continuation handoff.
Expected handoff: all five proposal files committed/pushed and the working tree clean.
Verify actual HEAD, status, index and remote before proceeding. Prior Git authorization
is completed and does not authorize further staging, commit, push, PR or merge.

Read AGENTS.md, CONTRIBUTING.md, issues #17/#29/#30, and:
- docs/maintainers/windows-arm64-cryptography-acquisition-plan.md
- docs/maintainers/windows-arm64-cryptography-stage1.md
- docs/maintainers/windows-arm64-cryptography-input-pins.json
- docs/maintainers/windows-arm64-cryptography-provenance-plan.md
- docs/maintainers/windows-arm64-beta-qualification-plan.md
- docs/maintainers/windows-qualification.md
- docs/maintainers/windows-owner-vm.md

I authorize read-only Phase A metadata research and acquisition-approval preparation only.
The preferred proposed route is a separate disposable native ARM64 UTM builder copy.
This preference does not authorize creating it or performing administrator setup.
Preserve the original owner-proof VM, frozen fix04 snapshot, reports and caches.

Prepare a concrete Phase B acquisition packet: exact official URLs/redirect hosts,
versions, architecture, expected hashes or explicit missing hashes, authentication
and license checks, download/resource limits, fresh private paths, Microsoft
fixed-version offline-layout commands and their writes, and stop conditions.
Distinguish published metadata from verified artifact bytes and complete frozen pins.
Review the proposed VS Build Tools 17.14.42/ARM64 components, Rust 1.99.1,
CPython 3.13.16, OpenSSL 4.0.3, maturin 1.15.0, setuptools 84.0.0 and unchanged
locked CFFI/pycparser inputs. Resolve the exact SDK/toolset package closure,
Rust/crate/test-input metadata and OpenSSL 4.0.3 recipe/trust gaps. No moving latest
channel, silent version substitution, source fallback or hand-edited lock.

Strawberry Perl 5.42.3.1 is an x64 auxiliary-only candidate, not native ARM64 Perl.
Seek an explicit later decision for that emulation exception or retain the blocker.
Keep the compiler/linker/Rust/Python native ARM64; do not qualify AMD64 by emulation.

Only documentation/catalog/checksum/attestation metadata requests are allowed now.
Do not acquire executable/MSI/wheel/crate/toolchain/source-archive payloads, run a
Microsoft layout bootstrapper, clone/provision machines, install tools, invoke
Configure/build backends/Cargo, compile, install/import candidate binaries or tests,
change canonical dependencies/lockfiles, accounts, privileges or machine policy.
No spending, upstream contact, external builder access, remote CI, issue closure,
release/publication or Windows enabling. Do not resume broader #29 execution.

The last observed original guest was Core/26H2/build 26300.9711. Accepted fix04's
1 passed in 215.27s remains only its recorded Windows 11 Home/build 26300/internal
fixed NTFS/native ARM64 CPython 3.13.16 owner evidence. Preserve original flags and
historical failures; do not rerun it because chats or commits changed. The 36/37
dependency audit is metadata only, and both earlier source installs remain failed.

You may read local/windows-vm-owner-setup.md and the task-specific private summary
local/windows-arm64-cryptography-stage1-2026-10-16/observations.json, plus reports
I provide. No unrelated private content, credentials, .env or real keys.
If a guest check is necessary, begin with a fresh read-only account/token check,
use verified explicit interpreter paths, and give ONE ordinary PowerShell command
at a time, waiting for my pasted output. Do not type commands automatically in UTM.
No prior PowerShell variables or sessions may be assumed. I enter credentials directly.

Keep #30/#17 updates public-safe; update #29 only for relevant dependency status.
Preserve POSIX behavior, CLI syntax/gate order, Fernet/v1, canonical dependencies,
existing-log append refusal and Git interruption/power-loss limits. Production
Windows mutation/recovery stays gated; AMD64 stays unqualified. No new API,
pruning, naming refinements, Python 3.15 or new Git recovery command.
For any Python files actually changed, use Jeff Shurtliff (via GPT-6.1 Sol)
and the current local date in headers; no Python change is expected for Phase A.

Deliver the acquisition approval packet, unresolved pins and licensing/resource
decisions, executed/unexecuted checks and accurate Git status, then stop for my
review. Do not proceed to B/C/D or Stage 2 without a new explicit approval.
```

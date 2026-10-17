# Next-chat prompt: AMD64 laptop readiness — #17 / #29

**16 October 2026. A1 only: read-only readiness and decision-packet preparation.**

The maintainer selected the existing physical AMD64 laptop for the next Windows
work. The [continuation plan](windows-amd64-continuation-plan.md) divides the
remaining work into chat-sized tasks A1–A9. Submitting this prompt authorizes
only A1 and its public-safe tracking/documentation updates. It does not approve
setup, test execution, Windows dispatch integration or release scope changes.

```text
Continue only Obfuscidian #17/#29, task A1 in
docs/maintainers/windows-amd64-continuation-plan.md.

Use the existing checkout and preserve every commit and local change. Expected
host branch: feature/17-add-safe-native-windows-support. Last verified host HEAD,
cached origin and live remote: e54875bfc4c2aee1d55633be622de940a2d1883f.
Verify actual current HEAD/tree/index/remote read-only; the laptop checkout's
current identity is unknown. Do not reset, replace the checkout, start from main,
stage, commit, push, open a PR, merge, tag, close issues or publish.

Read AGENTS.md, CONTRIBUTING.md, live issues #17/#25-#30, and:
- docs/maintainers/windows-amd64-continuation-plan.md
- docs/maintainers/windows-amd64-next-chat.md
- docs/maintainers/windows-qualification.md
- docs/maintainers/windows-owner-vm.md
- docs/maintainers/windows-primitive-validation.md
- docs/maintainers/windows-lifecycle-validation.md
- docs/maintainers/windows-git-validation.md
- docs/maintainers/windows-cli-gate-proposal.md
- docs/maintainers/windows-arm64-cryptography-acquisition-packet.md
- pyproject.toml, poetry.lock and the relevant existing Windows runner scripts.

My priority is practical Windows use and broadly useful support, without owning
a custom cryptography artifact. I selected the previously used physical laptop.
I ran Get-CimInstance Win32_Processor | Select-Object Architecture, AddressWidth
there and report Architecture=9, AddressWidth=64. Do not repeat that unchanged
CPU check. This is not proof of the current Python process, token, storage,
complete dependencies or application qualification.

Authorize A1 only: read-only current-session token/elevation, OS/build,
interpreter/native process identity, relevant Git/Poetry and proposed fixed-NTFS
storage/free-space checks; obtain task-relevant account/fixture availability
without broad enumeration; audit official package metadata for the complete
actual AMD64 target against the unchanged canonical lock. Candidate payloads
must not be downloaded or imported. Do not assume the ARM 36/37 audit applies.

Give ONE ordinary PowerShell command at a time and wait for my pasted output.
Begin with the current session's token/elevation check; assume no surviving
variables or previous shell state. Use an explicitly verified interpreter for
later probes. Keep raw identities/paths/inventories private. Do not collect
credentials, inspect .env/real keys/vaults, search unrelated private files or type
automatically in the laptop/UTM. I enter any passwords myself.

The historical laptop owner-group fixture was unavailable. Do not repeat that
unchanged failing setup. Assess whether the reviewed two-standard-account
strategy can be prepared there; missing accounts require a concrete proposal,
not creation now. Accepted ARM64 fix04 (1 passed in 215.27s) remains only its
recorded ARM environment's owner evidence. Preserve the VM, frozen snapshot,
reports, saved flags and historical failures; do not rerun ARM proof. Actual
AMD64 owner proof still needs its own later approved execution.

Keep #17 as parent and #29 as active qualification. Use #25-#28 as implementation
history, not work to restart. Post concise public-safe direction/start/handoff
updates on #17/#29 and a parked ARM-track note on #30; preserve discussion and
old evidence. Open/close no issues or change labels/milestones/relationships in A1.
#30's ARM64 custom-build/acquisition work is parked, not solved or deleted.

Return a current readiness table, exact gaps, proposed isolated paths/setup,
complete metadata-only binary-route result and a concrete A2 decision packet.
The proposed first Windows scope is absent-destination fresh backup, verify,
absent-destination fresh restore and bound recovery, with manual encrypted-mirror
Git publication. Detailed scope/matrix/gate-order changes need explicit review;
do not silently declare broad #17/#29 criteria complete or waived.

No account/privilege/policy/ACL changes, package/tool acquisition or installation,
environment creation, source builds/backends, VM/cloud provisioning, fixture
writes, tests, CI dispatch, dependency/lock changes or Windows gate enabling.
Preserve POSIX behavior, CLI syntax/gate order, Fernet/v1 and existing-log append
refusal. Native AMD64 support remains unqualified until later evidence passes.
For any Python files actually changed, use Jeff Shurtliff (via GPT-6.1 Sol)
and the current local date in headers; no Python change is expected in A1.

Update the handoff docs, run proportionate available documentation checks,
report executed/unexecuted checks and accurate Git/index status, and stop for
my review before A2 execution or any setup/test work.
```

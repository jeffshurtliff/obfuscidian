# Windows installed CLI gate-order proposal — #29

**16 October scope/audit approval:** the ARM-only qualification target and
non-installing dependency audit are approved. The audit is blocked at missing
cryptography 50.0.2 Windows ARM64 binaries. This approval does not authorize this
gate-order proposal, native application tests, production dispatch or dependencies.
All production Windows operations remain gated; AMD64 stays unqualified.

**16 October ARM-only alternative:** the
[lab-beta qualification plan](windows-arm64-beta-qualification-plan.md) proposes
a narrower operation/environment/matrix envelope. Adopting it would require an
explicit prerequisites revision before a separate dispatch/order approval. The
original broad proposal below is not silently applied to that narrower track;
no order or production routing change is authorized by preparing the plan.

**16 October decision:** the maintainer accepts owner-proof evidence only for the
recorded native ARM64 fix04 combination. This does not approve this CLI gate-order
proposal, satisfy native AMD64 qualification or enable production Windows
operations. All prerequisites and production gates below remain retained.

**15 October continuation:** the original mandatory two-account owner case passed
on native ARM64 Windows / CPython 3.13.16: **1 passed in 215.27s**, with all mandatory
properties validated. See the [executed fixture and architecture
proposal](windows-owner-vm.md). Two earlier actual attempts failed during setup;
the third failed only at the later verification-read identity comparison. Those
failures remain separate. Fix04 preserves every identity field across both
production refusals and records observer-read effects separately. Acceptance of
this ARM evidence is still unapproved; native AMD64 and all other applicable
qualification remain outstanding. No prerequisite, dispatch/order decision or
production gate below is waived or changed.

**13 October 2026. Status: proposal only; no authorization or runtime change.**

**14 October fallback:** both available maintainer computers lack the current
owner-group fixture. Production Windows write qualification remains deferred;
the [fallback record](windows-qualification.md)
retains actual owner proof as a prerequisite. The existing hosted run has six
passing POSIX jobs and three failed elevated Windows jobs. No prerequisite is
waived and no installed CLI dispatch/order change is authorized here. The
maintainer also confirms no second existing account on either computer and
explicitly directs that Windows remain gated. The two-existing-account
real-owner alternative is therefore unavailable and remains unimplemented;
injected evidence cannot replace actual proof.

The supported CLI still reaches POSIX transaction locking for backup, fresh
restore and recovery; Git publication has a separate POSIX gate. Installed
Windows write smoke tests cannot pass with those gates retained. Testing private
functions from an installed package would establish backend execution, but would
not qualify the actual console/module CLI. A flag, environment switch, injected
dispatch or test-only bypass would not resolve this requirement.

The maintainer must approve the following order before implementation. Approval
would authorize only the scoped local dispatch change after its prerequisites;
it would not authorize commits, push, CI execution, publication or a support claim.

1. Obtain actual real-owner proof with positive setup, production refusal and
   unchanged full native identity, bytes and exact protected DACL. Complete
   applicable private lifecycle/Git/DACL/termination, host/storage and nine-job
   exact-commit evidence, plus both generated v1 exchange directions.
2. Review that evidence and approve moving the **installed CLI write acceptance
   gate** after local production dispatch integration. Leave all current gates
   intact until step 1 and that authorization are satisfied.
3. Implement the concrete routing below, with no public bypass. Build fresh
   wheel/sdist from the reviewed candidate, install each with an isolated
   dependency wheelhouse, and run actual console and module commands outside
   the checkout. Any failure retains an unqualified local candidate and blocks
   release/support claims; do not compensate with injected calls or skips.
4. After separately approved Git history/remote execution, repeat the full
   nine-job matrix and installed write checks at the final exact commit,
   including strict docs/security/build checks. Only then consider the public
   support documentation and parent acceptance decision.

## Concrete dispatch changes for review

| Current call site | Proposed Windows routing | POSIX route |
| --- | --- | --- |
| `backup._publish_backup` | Delegate to `_publish_windows_backup` with the same plan, consent, prompt and read-only arguments | Existing implementation |
| `backup._recover_backup`, after custody/inventory/key/plan validation | Call `_windows_transactions._recover` with the verified plan and existing consent arguments | Existing `_recover_transaction` |
| `restore._publish_restore` | Delegate to `_publish_windows_restore` with the same validated plan/options | Existing implementation |
| `restore._recover_restore`, after complete source authentication/recheck | Call `_windows_transactions._recover` on the validated transaction plan | Existing `_recover_transaction` |
| `cli._unshroud_merge` | Select `_windows_git_restore._plan_merge` and `_publish_merge` together | Existing Git planner/publisher |

The Git planner selection is necessary for Windows index-mode handling. Do not
route the shared planner unconditionally back to the Windows planner: the private
Windows planner already calls the shared planner, so that would recurse. Keep
the low-level POSIX `_lock_descriptor` refusal as a backend boundary. Keep
`output.py` existing-log append refusal unchanged. The Windows backup result
retains its completed copy workspace; review CLI reporting against that behavior
rather than adopting POSIX merge cleanup claims. Keep constructors/helpers
private and preserve CLI syntax, consent, Fernet/v1 and dependencies.

## Installed-command acceptance required after approval

Extend `tests/integration/test_packaging.py`, using an independently installed
wheel and sdist and offline wheelhouse, for both console and module entry points:

- Generated external key, fresh/changed merge/no-op backup, byte-exact fresh and
  confirmed replacement restore, sensitive retained-state reporting, no-write
  verify/previews, consent refusal and default output privacy.
- Real worker termination of an installed command at a reviewed synthetic
  transaction boundary, then actual `--recover --non-interactive --yes` before
  retry. Boundary selection may use a child harness; the recovery command must
  use ordinary production dispatch. Preserve uncertainty/refusal cases.
- Real Git for Windows with the eligible protected root/administration policy
  established at fixture creation. Preserve origin HEAD/index/config, executable
  base index modes, ignored files and uncommitted restored differences. No new
  Git recovery command or automatic commit/push/merge.
- Actual opened-handle DACL inspection of installed command outputs, journals,
  ownership and retained plaintext, plus exact existing-log append refusal.

The current packaging extension checks generated-key installed Windows
fresh/merge/recovery **refusal** and absence of application artifacts. Its Windows
branch is unexecuted here. Existing POSIX smoke and read-only/help/keygen checks
remain available. These are partial preparation, not installed Windows writes.
The complete installed recovery/Git write harness remains blocked on the approved
order and routing; it must be implemented and executed in step 3.

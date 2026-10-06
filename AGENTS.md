# Agent instructions for Obfuscidian

This is the canonical, tool-independent guide for Codex, Claude Code, Gemini,
and other AI agents working in this repository. Guidance that applies to multiple
tools belongs here. Future `CLAUDE.md` and `GEMINI.md` files are thin, secondary
supplements for their respective tools; they must point here and must not
contradict this file. Do not create those companions unless requested.

Direct maintainer instructions define the authorized task. Read this file,
[the implementation roadmap](dev/IMPLEMENTATION_PLAN.md), and root
[`CONTRIBUTING.md`](CONTRIBUTING.md) before changing anything.
`CONTRIBUTING.md` owns the detailed contributor workflow; this file owns
agent participation and summarizes the day-to-day standards. If instructions
conflict and the conflict cannot be resolved from the maintainer's request, ask.

## Project and scope

Obfuscidian is a cross-platform Python CLI built with Click. It will back up
Obsidian vaults as individually encrypted files with an encrypted path manifest,
and restore those backups safely. The origin vault and encrypted mirror are
separate locations. Git hosting and publication remain user-managed.

- Implement only the requested roadmap thread and its necessary subtasks.
- Read that thread's dependencies and acceptance criteria before starting.
- Do not implement later threads, widen the scope, or perform unrelated cleanup.
- Record newly discovered work in the roadmap for a future thread. Ask before
  changing approved behavior, public interfaces, or the backup format.
- A roadmap is a target, not evidence that a feature has already been built.
  Verify the actual code, configuration, and tooling before using them.
- Preserve user changes. Keep work localized, reviewable, and uncommitted unless
  the maintainer explicitly authorizes committing.

## Roadmap issue updates

Each implementation thread has a dedicated GitHub issue linked in the roadmap's
thread index and its individual thread section. When the maintainer requests
work on a thread, keeping that existing issue updated is part of the authorized
task; routine progress comments and checklist edits do not require renewed
permission. Issue tracking does not authorize implementing other threads or
performing Git history, release, or publication actions.

- Before starting, read the linked issue and its dependency issues alongside
  the current roadmap. Check actual code and validation evidence; an issue's
  existence or closed state alone does not establish that a dependency works.
- Post a concise start comment describing the requested scope and dependency
  readiness. Update the existing issue rather than creating duplicate tracking.
- Record meaningful progress, verified checklist completion, blockers, and
  maintainer decisions. Keep the roadmap index, thread status, and handoff
  record consistent with the issue; preserve existing discussion and user edits.
- At handoff, post deliverables/file links, checks actually run and results,
  skipped checks, remaining acceptance criteria, blockers, next eligible work,
  and accurate Git status. Do not report uncommitted local work as merged or
  unexecuted hosted CI as passing.
- Leave the issue open for partial work, unmet acceptance criteria, or pending
  maintainer review. Close it only after acceptance criteria are met and the
  maintainer has approved completion or explicitly requested closure. Do not
  change its assignee, milestone, or labels without a relevant maintainer request.
- Use only public-safe planning and synthetic examples. Never post real keys,
  vault content, credentials, identifying local paths, or sensitive security
  details. Follow private reporting guidance for suspected vulnerabilities.
- If GitHub access is unavailable, record the unsent update in the roadmap's
  handoff record and report the limitation. Do not claim the issue was updated;
  synchronize the existing issue when access becomes available.

## Current environment versus planned environment

Thread 01 establishes Poetry/poetry-core, `src/obfuscidian/`, Python `>=3.12`,
locked developer tooling, and help/version-only CLI behavior. Runtime requirements
are authoritative in `pyproject.toml`; there is no second requirements list.

Thread 02 adds configuration/key resolution, secure keygen, and internal key
loading; it is complete, reviewed, and merged into `origin/main`, with issue #2
closed and Linux CI passing on Python 3.12–3.14. 

Thread 03 — Vault inventory and path preflight — is complete, reviewed, and
merged into `origin/main`; issue #3 is closed and Linux CI passed on Python
3.12–3.14. It adds internal read-only helpers; no vault command is exposed.

Thread 04 — Encrypted backup format — is complete, reviewed, and merged into
`origin/main`; issue #4 is closed and Linux CI passed on Python 3.12–3.14.
Internal codecs and complete read-only validation are documented in
[the format guide](docs/FORMAT.md).

Thread 05 — Safe publication and recovery — is complete, reviewed, and
merged/pushed into `origin/main`; issue #5 is closed and Linux CI passed on
Python 3.12–3.14. See [the transaction guide](docs/TRANSACTIONS.md) and roadmap
completion record for evidence and platform limits.

Thread 06 — Fresh backup — is complete, reviewed, and merged/pushed into
`origin/main`; issue #6 is closed and Linux CI passed on Python 3.12–3.14.
See [fresh backup](docs/BACKUP.md) and the roadmap completion record for
validation and platform limits. `shroud fresh` and additive `shroud merge` are
available; `verify` performs complete read-only validation. Fresh and additive
Git merge restore are available; Thread 11 adds optional private operational
logging.

Thread 07 — Merge backup — is complete, reviewed, and merged/pushed into
`origin/main`; issue #7 is closed and Linux CI passed on Python 3.12–3.14.
See the backup guide and roadmap completion record for evidence and limits.

Thread 08 — Read-only verification — is complete, reviewed, and merged/pushed
into `origin/main`; issue #8 is closed as completed. Linux CI passed on Python
3.12–3.14. See [verification](docs/VERIFY.md) and the roadmap completion record
for evidence and limits.

Thread 09 — Fresh restore — is complete, reviewed and merged/pushed into
`origin/main`; issue #9 is closed as completed. Linux CI passed on Python
3.12/3.13; Python 3.14 was canceled before execution because no hosted runner
acquired the job. The maintainer accepted that validation gap for closure; see
[fresh restore](docs/RESTORE.md) and the roadmap completion record. 

Thread 10 — Git merge restore — is complete, reviewed and merged/pushed into
`origin/main`; issue #10 is closed as completed. Linux CI passed on Python
3.12–3.14. See [merge restore](docs/RESTORE.md#additive-git-merge-restore) and the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-10--git-merge-restore-completion-record-5-october-2026).

Thread 11 — CLI polish — is complete, reviewed and merged/pushed into
`origin/main`; issue #11 is closed as completed. Linux CI passed on Python
3.12–3.14. See [the CLI contract](docs/CLI.md) and the
[completion record](dev/IMPLEMENTATION_PLAN.md#thread-11--cli-polish-completion-record-5-october-2026).

Thread 12 is complete, reviewed and merged/pushed into `origin/main`; issue #12
is closed as completed. Linux/macOS/Windows CI passed on Python 3.12–3.14.
Native Windows mutation/recovery and existing-log append still fail closed.
See [platform validation](docs/PLATFORMS.md). Threads 13–14 remain not started.

Use Poetry 2.2 or newer, below 3.0, for development, dependencies, and packaging.
CI targets Linux/macOS/Windows on Python 3.12, 3.13, and 3.14; Thread 12 records
the passing matrix and retained platform limits. Local results alone do not prove hosted validation.
Package metadata and the CI matrix are the operational source of truth; do not
silently change support requirements.

```sh
poetry install --with dev
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run bandit -r src/obfuscidian
poetry build
```

After Thread 13 adds the docs tooling:

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
```

Use Poetry commands to add dependencies and regenerate `poetry.lock`; never edit
the lockfile by hand. Justify additional runtime dependencies. Do not introduce
a second manually maintained runtime dependency list. Generated package
metadata, build output, caches, coverage reports, and rendered docs are not
source files and must not be hand-edited or committed accidentally.

## Coding standards

- Follow PEP 8; prefer explicit, focused functions and clarity over abstraction.
- Use type hints, especially at module boundaries, compatible with the supported
  minimum Python version. Use `from __future__ import annotations` where useful.
- Keep the Click layer thin. Separate option/prompt handling from key loading,
  traversal, cryptography, format validation, transactions, and Git operations.
- Centralize shared constants in `constants.py`; group related values logically
  and import this module as `const` where appropriate. Do not invent classes
  merely to hold unrelated constants.
- Use `pathlib` and safe binary I/O; do not normalize Markdown text or attachment
  bytes during backup/restore. Use subprocess argument lists, never shell
  interpolation, for Git calls. Do not execute vault or plugin content.
- Target Ruff formatting: 130-character lines, single-quoted ordinary strings,
  triple-double-quoted docstrings, spaces for indentation, LF endings. Wrap
  instead of broadly suppressing lint. Any unavoidable line-length exception
  must be local and explained.
- Do not reformat unrelated files or hand-copy template code without checking
  its assumptions and safety implications.

## Docstrings and module headers

Follow PEP 257. Use a concise summary ending with a period, then a blank line
before detail. Describe observable purpose, inputs, outputs, exceptions, and
important usage limitations. Use Sphinx/reST field lists (`:param name:`,
`:returns:`, `:raises ExceptionType:`); do not repeat clear signature types.
Document constructors on the class rather than duplicating full parameter
documentation in both the class and `__init__`.

Version-history directives are required only for releases after `1.0.0`: new
public callables/classes/exceptions need `.. versionadded:: X.Y.Z`, and public
behavior or signature changes need `.. versionchanged:: X.Y.Z`. During initial
`1.0.0` development, do not maintain summarized docstring changes or add
`.. versionchanged:: 1.0.0`; it will be the first released version.

The initial-release exception is `src/obfuscidian/cli.py`: retain the existing
`.. versionadded:: 1.0.0` lines and include this single, bare directive on each
additional public CLI callable introduced for the first release. Place it below
the `\f` line and above the Sphinx field list (`:param`, `:returns:`, `:raises`),
without a summarized change description. Other initial-release public
callables/classes/exceptions do not require version directives.

For later releases, preserve earlier directives. In CLI docstrings, keep version
directives below `\f` and above the field list; elsewhere, place new directives
after the field list. Use the intended stable
release version derived from `pyproject.toml` without development/prerelease
suffixes (`1.0.0.dev0` means `1.0.0`). Private helpers and internal refactors do
not receive public version directives. The CLI is the initial public contract;
do not expose an unsupported Python library API incidentally.

New Python modules and tests use the existing header convention:

```python
# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.module_name
:Synopsis:          Describes the module's purpose
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via <actual-model-identifier>)
:Modified Date:     DD Mon YYYY
"""
```

On Python files actually changed, preserve `Created By`, update `Last Modified`
to `Jeff Shurtliff (via <actual-model-identifier>)`, and update `Modified Date`
using the current local date and existing format. Replace the angle-bracket
placeholder with the model actually used for that file. A sample identifier is
not a pinned model version. Do not infer an exact model from an app/tool name;
if the model identifier is unavailable and a header needs updating, ask the
maintainer. Update no unrelated headers. Supplemental tool instructions may
clarify verified identifiers but must not hard-code a stale model.

## Security, privacy, and data preservation

- Never expose real key contents, real vault content, credentials, or identifying
  local paths in code, docs, logs, tests, issues, commits, or tracked artifacts.
  Use synthetic content, temporary generated test keys, and obvious placeholders.
  Fixed compatibility-fixture keys are permitted only when clearly labeled as
  synthetic and never used for real data; never print even test keys in CLI logs.
- `dev/` is tracked/public-safe planning material. `local/` is ignored private
  material, not a source of fixtures to copy into Git. Relevant safe reference
  documentation under `local/vendor_docs/` may be read when present; other
  private local content requires explicit authorization. Do not inspect `.env`
  or real key files to discover credentials or test availability.
- Keep encryption keys outside origin and mirror locations. Use exclusive key
  creation; never overwrite, print, or automatically regenerate a missing key.
- Use standard Fernet authenticated encryption, not Base64 as security or a
  custom cryptographic primitive. Justify cryptographic changes and test their
  compatibility and failure behavior.
- Preserve backup-format version compatibility. Validate all manifest paths and
  all required objects before modifying a restore destination. Do not expose
  unauthenticated plaintext or silently skip failed files and report success.
- Reject overlap, traversal, links/junctions, special files, unsafe destinations,
  and target name collisions. Recheck filesystem identities during publication.
- Source data stays read-only during backup. Never encrypt in place. Preserve
  Git metadata, retain required rollback copies, and implement failure recovery
  before exposing destructive modes. `--non-interactive` is not `--yes`.
- Verification and dry runs must not modify vaults, create destination paths,
  locks, worktrees, rollback copies, or log files.
- Never run Git commit/push/merge operations automatically in user vaults or
  mirrors. A merge restore may create its explicitly requested local branch and
  worktree; restored content must remain uncommitted for manual review.
- No cryptographic changes or backup-format changes without security reasoning,
  targeted tests, documentation, and any required maintainer decision.
- Report suspected vulnerabilities privately when supported; do not publish
  secrets or sensitive exploit details in a public issue.

## Tests and validation

Use pytest, with `tests/unit/` and `tests/integration/`.
Behavior changes require meaningful tests; fixes require regression tests. Use
`tmp_path`, temporary vaults, and temporary Git repositories. Tests must be
deterministic, isolated, and offline. Local synthetic integration tests run in
the normal suite; real vault/cloud tests require separate explicit authorization.

Do not execute any `dev/example-*.py` against real vaults. In particular,
`example-encrypt-decrypt-concept.py` modifies files in place, can overwrite a key,
and catches errors while continuing; it is a concept reference, not production
code or a safe migration tool.

Test binary byte preservation, wrong keys, corruption, object substitution,
missing files, unsupported formats, path safety, permission failures, source
changes, interrupted writes, rollback, confirmations, no-op backups, and output
privacy as relevant to the requested thread. CLI tests use Click's `CliRunner`
and absolute temporary paths; never run concurrent `CliRunner` invocations in
threads within one interpreter.

Run checks proportionate to the task. Documentation-only work needs link,
consistency, privacy, and diff checks; it does not justify installing dependencies
or modifying application files. Report missing tooling or skipped checks
accurately. Do not claim passing tests from a failed or unexecuted command.

## Documentation and changelog

Keep the roadmap's status and decisions accurate. Update user-facing docs and
docstrings for public behavior changes, and `docs/CHANGELOG.md` under
`[Unreleased]`. Use Keep a Changelog categories.
Internal refactors, tooling, CI, and dependency maintenance belong in the
changelog rather than public usage explanations or public version directives.

Use single backticks in Markdown/MyST; reST-style double backticks are appropriate
in `.rst` files and reST docstrings. Keep examples minimal, public, executable,
and privacy-safe. Target Sphinx + reST + MyST and `pydata_sphinx_theme`, following
the organization of SalesPyForce/PyDPlus without importing their private content
or unrelated domain-specific rules. Document future features as planned until
they work. Do not claim publication or supported-platform validation prematurely.

## Git and release authorization

- Never stage, commit, push, open a PR, merge, tag, create a release, or publish
  unless the maintainer has explicitly authorized that action. Authorization for
  one action does not authorize the others. Preparing a release is not publishing.
- Base project branches on `main`; do not commit directly to `main`. Codex-created
  branches use `codex/<type>/<description>` (for example, `codex/docs/agent-guide`).
  Include a real issue number when provided; do not invent one or create an issue
  merely to satisfy naming conventions. Other agents follow the contributor
  branch policy when it exists.
- When commits are authorized, keep them focused, use past-tense messages, and
  mention the filename for a single-file commit. Reference applicable issue
  numbers. Authorized PRs follow actual templates and labels; include `codex`
  for Codex-created PRs when configured, and report unavailable conventions.
- Do not activate release/publication automation as a side effect. The current
  template workflow publishes on a GitHub release event; Thread 14 must replace
  its assumptions before release use. Do not trigger it during preparation.

## End-of-thread handoff

Before returning work, inspect the diff and status, run relevant available
checks, verify that scope is unchanged, and ensure no secrets or private files
entered the proposed change. Include:

1. What changed and why, with links to the relevant files.
2. Acceptance criteria met and checks actually executed, including limitations.
3. Remaining work, dependency blockers, and the next appropriate roadmap thread.
4. Accurate Git status and whether changes remain uncommitted.

Update thread status in the roadmap only when its acceptance criteria are met;
record partial work explicitly. A handoff must not turn a planned feature or a
skipped platform test into a completed claim.

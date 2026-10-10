# Agent instructions for Obfuscidian

This is the canonical, tool-independent guide for Codex, Claude Code, Gemini,
and other AI agents working in this repository. Guidance that applies to multiple
tools belongs here. Future `CLAUDE.md` and `GEMINI.md` files are thin, secondary
supplements for their respective tools; they must point here and must not
contradict this file. Do not create those companions unless requested.

Direct maintainer instructions define the authorized task. Read this file and
root [CONTRIBUTING.md](CONTRIBUTING.md) before changing anything.
`CONTRIBUTING.md` owns the detailed contributor workflow; this file owns agent
participation and summarizes the day-to-day standards. If instructions conflict
and the maintainer's request does not resolve them, ask.

## Project and scope

Obfuscidian is a Python/Click CLI for individually encrypted Obsidian vault
backups with an encrypted path manifest and safe restores. The origin vault and
encrypted mirror are separate locations. The CLI is the supported public
interface; Git hosting and publication remain user-managed.

- Implement only the requested task and its necessary subtasks. Review its
  dependencies and acceptance criteria against actual code and validation.
- Do not widen scope or perform unrelated cleanup. Record unrelated discoveries
  in the existing issue or handoff for future work.
- Ask before changing approved behavior, public interfaces or the backup format.
- Preserve user changes. Keep work localized, reviewable and uncommitted unless
  the maintainer explicitly authorizes committing.

## Issue updates

When the maintainer requests implementation work tied to an existing issue,
keeping that issue updated is part of the authorized task. Routine progress
comments and verified checklist edits do not need renewed permission. Issue
tracking does not authorize Git history, release or publication actions.

- Read the linked issue and its dependencies; verify actual implementation and
  validation evidence rather than relying on issue state alone.
- Post concise public-safe start, meaningful progress and handoff updates.
  Preserve discussion and user edits; do not change assignees, labels or
  milestones without a relevant maintainer request.
- Report deliverables, executed/skipped checks, limitations and accurate Git
  status. Never describe uncommitted work as merged or unexecuted CI as passing.
- Leave issues open for partial work or pending review. Close only after
  acceptance criteria are met and the maintainer approves completion or requests
  closure.
- If GitHub is unavailable, record the unsent update in the handoff and report
  the limitation; synchronize it when access becomes available.

## Environment and checks

Obfuscidian 1.0.1 uses Poetry/poetry-core, `src/obfuscidian/` and Python `>=3.12`.
Runtime requirements in `pyproject.toml` and the CI matrix are authoritative.
CI targets Linux/macOS/Windows on Python 3.12, 3.13 and 3.14. Linux/macOS support
vault writes; native Windows mutation/recovery and existing-log append fail
closed. See [supported environments](docs/PLATFORMS.md). Local checks do not
establish hosted CI or publication success.

Use Poetry 2.2 or newer, below 3.0:

```sh
poetry install --with dev,docs
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run bandit -r src/obfuscidian
poetry build
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
```

Use Poetry to manage dependencies and regenerate `poetry.lock`; never edit the
lockfile by hand or maintain a second runtime dependency list. Justify additional
runtime dependencies. Generated package metadata, builds, caches, coverage and
rendered docs are ignored outputs, not source files. See the
[release runbook](docs/maintainers/releasing.md) for candidate validation and
separately authorized publication.

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

For releases after `1.0.0`, new public callables/classes/exceptions need
`.. versionadded:: X.Y.Z`; public behavior or signature changes need
`.. versionchanged:: X.Y.Z`. Preserve existing directives, including the bare
`.. versionadded:: 1.0.0` on public CLI callables. Initial-release callables
outside the CLI do not need retroactive directives.

In CLI docstrings, place directives below `\f` and above the Sphinx field list;
elsewhere, place new directives after the field list. Use the intended stable
version from `pyproject.toml`, without prerelease suffixes. Private helpers and
internal refactors receive no public directives. Do not expose an unsupported
Python library API incidentally.

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
- Historical planning material is public-safe. `local/` is ignored private
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

Do not execute historical concept scripts against real vaults. They can modify
files in place, overwrite keys and continue after errors; they are references,
not production code or safe migration tools.

Test binary byte preservation, wrong keys, corruption, object substitution,
missing files, unsupported formats, path safety, permission failures, source
changes, interrupted writes, rollback, confirmations, no-op backups, and output
privacy as relevant to the requested task. CLI tests use Click's `CliRunner`
and absolute temporary paths; never run concurrent `CliRunner` invocations in
threads within one interpreter.

Run checks proportionate to the task. Documentation-only work needs link,
consistency, privacy, and diff checks; it does not justify installing dependencies
or modifying application files. Report missing tooling or skipped checks
accurately. Do not claim passing tests from a failed or unexecuted command.

## Documentation and changelog

Keep issue status and maintainer decisions accurate. Update user-facing docs and
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
- Follow [the release runbook](docs/maintainers/releasing.md). Publication is
  manual through Twine by default; the optional guarded workflow requires
  separate authorization and external controls. Never dispatch it during
  preparation or activate publication as a side effect.

## Handoff

Before returning work, inspect the diff and status, run relevant available
checks, verify that scope is unchanged, and ensure no secrets or private files
entered the proposed change. Include:

1. What changed and why, with links to the relevant files.
2. Acceptance criteria met and checks actually executed, including limitations.
3. Remaining work, dependency blockers and appropriate follow-up tasks.
4. Accurate Git status and whether changes remain uncommitted.

Update issue status only when its acceptance criteria are met; record partial
work explicitly. A handoff must not turn a planned feature or a
skipped platform test into a completed claim.

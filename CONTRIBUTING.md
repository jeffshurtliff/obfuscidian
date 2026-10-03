# Contributing to Obfuscidian

Contributions are welcome. Obfuscidian is a Python/Click CLI being developed to
back up Obsidian vaults as individually encrypted files with an encrypted path
manifest and restore them safely. Data preservation, privacy, clear CLI behavior,
and meaningful tests guide contributions.

Read [AGENTS.md](AGENTS.md) and the
[implementation roadmap](dev/IMPLEMENTATION_PLAN.md) before starting. This guide
owns the contributor workflow; AGENTS.md is the canonical agent guide, and the
roadmap defines approved behavior, dependencies, and acceptance criteria. Direct
maintainer instructions define the authorized task. Resolve conflicts with the
maintainer before changing approved behavior, public interfaces, or the backup
format.

## Current project status

Application implementation has not started. The repository currently has a
root-level `obfuscidian/` package, setuptools packaging, Python `>=3.10`, a Click
placeholder command, and one template test. Backup, restore, verification, and
key generation are planned functionality.

Thread 01 will introduce Poetry, the `src/` layout, Python 3.12+, Ruff, developer
tools, `tests/unit/`, `tests/integration/`, and `docs/CHANGELOG.md`. Thread 12 will
expand validation to Windows, macOS, and Linux for Python 3.12–3.14. Thread 13
will introduce Sphinx/reST/MyST and `pydata_sphinx_theme`. These are targets,
not claims of completed tooling or supported-platform validation. Recheck actual
package metadata, workflows, and roadmap evidence as implementation advances.

## Development workflow

1. Choose a bounded roadmap thread or a maintainer-approved task. Read its
   dependencies and acceptance criteria; do not implement later threads or
   unrelated cleanup as a side effect.
2. Search existing issues before filing a new one. Use the appropriate template
   below and reference a real issue when one exists. A direct maintainer request
   or roadmap task may proceed without creating an issue solely for naming.
3. Base the work on `main` and use the branch conventions below. Preserve
   existing user changes; never commit directly to `main`.
4. Make focused changes and add meaningful tests for behavior changes and
   regression tests for fixes. Keep the Click layer thin.
5. Update relevant docs, docstrings, and the changelog once it exists. Keep
   unimplemented capabilities clearly marked as planned.
6. Run available checks proportionate to the task, inspect the diff and Git
   status, and report executed checks, skipped checks, and remaining blockers.
7. Submit work for review through the authorized workflow. Agents leave changes
   uncommitted by default; Git history and publication actions require the
   separate permissions described below.

Record unrelated discoveries in the roadmap for a future thread. Update a
thread's status only when its acceptance criteria are met; record partial work
explicitly rather than marking a full thread complete.

## Issues and branch naming

Use [the issue templates](.github/ISSUE_TEMPLATE) for public reports and requests.
Maintainer templates capture approved implementation work. All issue templates,
including those named "Maintainer," create public issues; they are not private
reporting channels.

| Type | Public template | Maintainer template | Title prefix | Labels | Branch type |
| --- | --- | --- | --- | --- | --- |
| Feature | Feature Request | Maintainer Feature | `[FEATURE]` | `enhancement` | `feature` |
| Bug | Bug Report | Maintainer Bug | `[BUG]` | `bug` | `fix` |
| Refactor | Refactor Request | Maintainer Refactor | `[REFACTOR]` | `refactor` | `refactor` |
| Maintenance | None | Maintainer Chore | `[CHORE]` | `chore` | `chore` |
| Documentation | Docs Request | Maintainer Docs | `[DOCS]` | `documentation` | `docs` |
| Tests | Test Request | Maintainer Test | `[TEST]` | `testing` | `test` |
| CI | CI Request | Maintainer CI | `[CI]` | `ci` | `ci` |
| Security | Security Report (sanitized only) | Maintainer Security (sanitized only) | `[SECURITY]` | `security` | `security` |
| Release | None | Maintainer Release | `[CHORE]` | `chore` | `chore` |

Maintainer templates also request `maintainer`. Template labels express intended
categorization; this change does not create or verify labels on GitHub. Use
configured labels and report unavailable conventions. Codex-created PRs include
`codex` when configured.

Branches use `<type>/<issue-number>-<description>` when an issue is provided,
or `<type>/<description>` otherwise. Codex branches add the `codex/` prefix:

```text
fix/42-reject-unsafe-paths
docs/contributor-guide
codex/fix/42-reject-unsafe-paths
codex/docs/contributor-guide
```

Use a real issue number; never invent one. Features change user-visible
capabilities; fixes correct defects; refactors preserve behavior; chores cover
dependencies, metadata, and tooling. Documentation and test branches cover work
limited to those areas. A fix and its regression test belong together. CI covers
pipeline mechanics; security covers risk reduction. Release preparation is a
chore with its own [maintainer template](.github/ISSUE_TEMPLATE/maintainer-release.md).
An issue checklist does not grant Git or release authorization.

## Developer setup and checks

### Current setuptools setup

From the repository root, create a virtual environment:

```sh
python -m venv .venv
```

Activate it for your shell:

| Shell | Activation |
| --- | --- |
| POSIX shell | `source .venv/bin/activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |

Then install and check the current scaffold:

```sh
python -m pip install -e '.[test]'
python -m pytest -q
python -m obfuscidian --help
```

`pyproject.toml` and `requirements.txt` currently disagree about runtime
dependencies. Use the package's declared test extra for this setup; Thread 01
will reconcile dependencies and remove the second manually maintained list.
Do not mistake successful help/version checks for working backup functionality.

### After Thread 01 is complete

Use these commands only after the corresponding tooling and configuration exist:

```sh
poetry install --with dev
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run bandit -r src/obfuscidian
poetry build
```

Use Poetry to add dependencies and regenerate `poetry.lock`; never edit the
lockfile by hand. Justify new runtime dependencies and maintain one authoritative
runtime dependency declaration. Generated package metadata, builds, caches,
coverage reports, and rendered docs are not hand-edited source files.

After Thread 13 adds docs tooling:

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
```

Run `git diff --check` and inspect new, untracked files as well. Documentation-only
work needs link, consistency, privacy, and whitespace checks; it does not require
installing dependencies or changing application code. Report missing tools and
unexecuted checks accurately. Current CI tests only on Linux and ignores several
documentation paths; it does not enforce all planned checks.

## Code standards

- Follow PEP 8; favor explicit, focused functions and clarity over abstraction.
- Use type hints at module boundaries, compatible with the supported minimum
  Python version; use `from __future__ import annotations` where useful.
- Separate Click option/prompt handling from key I/O, traversal, cryptography,
  format validation, transactions, and Git operations.
- Centralize shared constants in `constants.py`, grouped logically, and import
  that module as `const` where appropriate. Avoid classes holding unrelated constants.
- Use `pathlib`, binary I/O, and subprocess argument lists. Preserve exact note
  and attachment bytes; do not execute vault or plugin content.
- Target Ruff formatting: 130-character lines, single-quoted ordinary strings,
  triple-double-quoted docstrings, space indentation, and LF endings. Wrap long
  lines; unavoidable exceptions must be local and explained. Do not broadly
  suppress lint or reformat unrelated files.

### Docstrings and module headers

Follow PEP 257 with a concise summary ending in a period and a blank line before
details. Describe purpose, inputs, outputs, exceptions, and important limitations
using Sphinx/reST fields (`:param name:`, `:returns:`, `:raises ExceptionType:`).
Do not repeat clear signature types. Document constructors on the class rather
than duplicating parameter documentation in `__init__`.

New public callables, classes, and exceptions need `.. versionadded:: X.Y.Z`;
public behavior or signature changes need `.. versionchanged:: X.Y.Z`. Preserve
earlier directives and put new ones after the field list. Derive the intended
stable release version from `pyproject.toml` without development/prerelease
suffixes: `1.0.0.dev0` means `1.0.0`. Private helpers and internal refactors receive
no public version directives. The CLI is the initial public contract; do not
incidentally expose an unsupported Python library API.

New Python modules and tests use this header convention:

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

On Python files actually changed by an agent, preserve `Created By`, update
`Last Modified` to Jeff Shurtliff with the actual generating model in parentheses,
and update `Modified Date` using the current local date and existing format.
The placeholder is not a pinned model. Do not infer an exact model from an app
name; ask the maintainer if the identifier is unavailable and a header needs
updating. Do not update unrelated headers.

## Testing requirements

Behavior changes require meaningful tests; fixes require regression tests. Use
pytest, deterministic offline fixtures, `tmp_path`, temporary vaults, temporary
generated keys, and temporary Git repositories. Thread 01 establishes
`tests/unit/` and `tests/integration/`. Local synthetic integration tests belong
in the normal suite; real vault/cloud tests require separate explicit authorization.

As relevant to the task, cover byte preservation, wrong keys, corruption, object
substitution, missing files, unsupported formats, unsafe paths, collisions,
permissions, source changes, interrupted writes, rollback, confirmations, no-op
backups, and output privacy. Test observable invariants and failure behavior,
not copies of private implementation logic. No coverage percentage threshold
is currently established for this repository.

CLI tests use Click's `CliRunner` with absolute temporary paths. Do not run
concurrent `CliRunner` invocations in threads within one interpreter; use process
isolation when parallelism is needed. Platform skips must be narrow and explained.
Report local results separately from actual hosted matrix results.

Do not execute `dev/example-*.py` against real vaults. In particular,
`example-encrypt-decrypt-concept.py` encrypts in place, can overwrite a key,
and catches errors while continuing. These scripts are historical concepts,
not production code or migration tools.

## Security and data preservation

Use synthetic content and placeholder paths in code, tests, docs, issues, and
logs. Never include real key contents, credentials, vault content, or identifying
local paths in tracked artifacts. Clearly labeled synthetic compatibility keys
are permitted only as fixtures and must never protect real data or appear in
CLI output. `dev/` is public-safe planning material; `local/` is ignored private
material, not a fixture source. Relevant safe docs in `local/vendor_docs/` may
be read if present; other private material requires explicit authorization.
Do not inspect `.env` or real keys to discover credentials or test availability.

Implement the approved roadmap safety contracts:

- Keep keys outside origin and mirror locations. Create them exclusively;
  never overwrite, print, or automatically regenerate a missing key.
- Use standard Fernet authenticated encryption. Base64 is encoding, not security.
  Cryptographic or backup-format changes require security reasoning, targeted
  tests, documentation, and any required maintainer decision.
- Authenticate and validate all manifest paths and required objects before
  modifying a restore destination. Reject overlap, traversal, links/junctions,
  special files, unsafe destinations, and collisions; recheck identities at publication.
- Keep backup sources read-only. Preserve Git metadata and required rollback
  copies; implement failure recovery before exposing destructive modes.
  `--non-interactive` does not imply `--yes` or bypass safety checks.
- Verification and dry runs must not create paths, locks, worktrees, rollback
  copies, logs, or other application writes.
- Never automatically commit, push, or merge in user vaults or mirrors. An
  explicitly requested merge restore may create its separate branch/worktree,
  with restored changes left uncommitted for manual review.

Document threat-model limits honestly. Do not claim guaranteed recovery,
security certification, remote privacy validation, or publication without evidence.

### Security reporting

For suspected vulnerabilities, use GitHub's Security tab **Report a vulnerability**
if private reporting is enabled. Availability is not assumed. If unavailable,
contact the maintainer privately at the public maintainer email in
`pyproject.toml`; start with a sanitized summary and agree on a secure channel
before sharing sensitive details. Never send real keys, credentials, or vault data.

The public Security Report and Maintainer Security templates are for sanitized
hardening suggestions and non-sensitive tracking only. Do not publish exploit
payloads, detailed attack instructions, sensitive environment data, or secrets
in public issues, even when private reporting is unavailable. Refer to private
coordination without copying its sensitive contents into public tracking.

## Documentation, versions, and changelog

Describe observable CLI behavior, supported options, errors, and limitations.
Keep examples minimal, executable, and synthetic; mark future commands as
planned until implemented. Internal refactors, tooling, CI, and dependency
maintenance belong in the changelog rather than public usage explanations or
public version directives.

Once Thread 01 establishes `docs/CHANGELOG.md`, add entries under `[Unreleased]`
using Keep a Changelog categories. Preserve version compatibility; public
interface and backup-format changes require maintainer review. Package version
and backup-format version are separate contracts. Version promotion requires
an explicit request; do not bump versions incidentally.

Use single backticks for Markdown/MyST inline code. Double backticks belong in
`.rst` files and reST docstrings. Thread 13 will establish the Sphinx/reST/MyST
docs organization and PyData theme. Do not copy private content or unrelated
extensions from reference projects. Check local links and examples without
claiming a strict Sphinx build before its tooling exists.

## Commits, pull requests, and releases

Agents must not stage, commit, push, open a PR, merge, tag, create a release, or
publish without explicit maintainer authorization for each action. Authorization
for one does not authorize the others. Human contributors submit focused work
for maintainer review; direct maintainer instructions govern agent participation.

When commits are authorized, use past-tense messages, mention the filename for
a single-file commit, and reference applicable issue numbers, for example:
`Updated CONTRIBUTING.md with developer setup guidance (#42)`.

PR descriptions explain the problem, resulting behavior, scope, actual
validation, and material limitations. Reference a real issue when applicable,
use the appropriate branch type and configured labels, and follow any PR
template that exists at submission time. There is currently no PR template;
issue templates are not PR templates. Include tests and docs as appropriate,
and require relevant available CI checks before merge. Do not present unexecuted
hosted checks as passing or require nonexistent checks.

Release preparation belongs to Thread 14 after Thread 13. Use the Maintainer
Release template to record facts, validation, blockers, and separate authorization
checkpoints. Do not assume a release runbook, tag convention, external publishing
configuration, or PyPI publication exists. The current template workflow publishes
on a GitHub release event; Thread 14 must replace its assumptions before use.
Never trigger it or activate publication automation as a preparation side effect.

## Handoff checklist

Before returning work, inspect the diff and status and verify scope and privacy.
Report what changed with file links, acceptance criteria met, checks actually
executed, limitations, remaining work, dependency blockers, and the next eligible
roadmap thread. Update roadmap evidence for completed or partial work without
overstating completion. State the accurate Git status and whether changes remain
uncommitted.

This guide and the issue templates were adapted from the public
[SalesPyForce contributor guide](https://github.com/jeffshurtliff/salespyforce/blob/2cbc66bc4fee815e27b748990222c97c1fe0222e/CONTRIBUTING.md)
and [issue templates](https://github.com/jeffshurtliff/salespyforce/tree/2cbc66bc4fee815e27b748990222c97c1fe0222e/.github/ISSUE_TEMPLATE),
with Obfuscidian's approved roadmap and agent instructions controlling project-specific behavior.

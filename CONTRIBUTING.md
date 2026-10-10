# Contributing to Obfuscidian

Contributions are welcome. Obfuscidian is a Python/Click CLI for individually
encrypted Obsidian vault backups and safe restores. Data preservation, privacy,
clear CLI behavior and meaningful tests guide contributions.

Read [AGENTS.md](AGENTS.md) before starting. This guide owns contributor policy;
AGENTS.md is the canonical agent guide. Direct maintainer instructions define
authorized scope. Resolve conflicts with the maintainer before changing approved
behavior, public interfaces or the backup format.

## Supported environment

Obfuscidian 1.0.1 requires Python 3.12+. CI covers Linux/macOS/Windows on Python
3.12–3.14. Linux/macOS implement backup and restore writes. Native Windows
supports private key creation, verification and read-only planning; mutation,
recovery and existing-log append fail closed. See [supported environments](docs/PLATFORMS.md).

Poetry manages locked development tools and the optional Sphinx/reST/MyST docs
group. The Read the Docs configuration uses those locked tools; see
[documentation maintenance](docs/maintainers/documentation.md). Runtime
requirements and the CI matrix are the operational source of truth.

## Development workflow

1. Choose a bounded maintainer-approved task. Read its dependencies and
   acceptance criteria; avoid unrelated cleanup or capabilities.
2. Search existing issues before filing a new one. Use the appropriate template
   below and reference a real issue when one exists. A direct maintainer request
   may proceed without creating an issue solely for naming.
3. Base the work on `main` and use the branch conventions below. Preserve
   existing user changes; never commit directly to `main`.
4. Make focused changes and add meaningful tests for behavior changes and
   regression tests for fixes. Keep the Click layer thin.
5. Update relevant docs, docstrings, and the changelog. Keep
   unimplemented capabilities clearly marked as planned.
6. Run available checks proportionate to the task, inspect the diff and Git
   status, and report executed checks, skipped checks, and remaining blockers.
7. Submit work for review through the authorized workflow. Agents leave changes
   uncommitted by default; Git history and publication actions require the
   separate permissions described below.

Record unrelated discoveries in the existing issue or handoff for future work.
Update status only when acceptance criteria are met; record partial work explicitly.

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

### Poetry setup

Install Poetry 2.2 or newer, below 3.0, and Python 3.12+. From the repository root:

```sh
poetry install --with dev
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest -q
poetry run coverage run -m pytest -q
poetry run coverage report
poetry run bandit -r src/obfuscidian
poetry build
```

Poetry manages the development environment; a separate activation step is not
required. Choose an interpreter explicitly with `poetry env use python3.12`
(or the appropriate executable path). Validate help/version, keygen and fresh/merge
backup, read-only verification and fresh restore with synthetic vaults.

### Fresh artifact validation

Build in a newly created temporary candidate directory, then run strict Twine
validation against exactly its wheel and sdist. The following example is for a
POSIX shell; use equivalent temporary directories in PowerShell/cmd.

```sh
CANDIDATE=$(mktemp -d)
WHEELHOUSE=$(mktemp -d)
poetry build --output "$CANDIDATE"
poetry run twine check --strict "$CANDIDATE"/*
```

Populate the wheelhouse before running the offline tests. This command reads
the authoritative runtime/build requirements and pins their top-level versions
to the installed Poetry environment; it downloads dependencies without uploading:

```sh
poetry run python - "$WHEELHOUSE" <<'PYTHON'
import subprocess
import sys
import tomllib
from importlib.metadata import version
from packaging.requirements import Requirement

with open('pyproject.toml', 'rb') as source:
    project = tomllib.load(source)
requirements = project['project']['dependencies'] + project['build-system']['requires']
pinned = [f'{Requirement(item).name}=={version(Requirement(item).name)}' for item in requirements]
subprocess.run([
    sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
    '--dest', sys.argv[1], *pinned,
], check=True)
PYTHON
poetry run pytest -q tests/integration/test_packaging.py --artifact-dir "$CANDIDATE" --wheelhouse "$WHEELHOUSE"
```

Each artifact is installed in its own temporary virtual environment, without
system site packages, using dependencies from the wheelhouse. Tests run console
and module help/version outside the checkout, verify the import location, and
run `pip check`. The default offline suite uses available development dependencies
through an explicit dependency path instead; report these two validation modes
distinctly.
Do not validate old artifacts accumulated in `dist/`. The sdist includes the
lockfile and changelog; wheel content is limited to application and distribution
metadata. Docs build tooling uses the optional `docs` group.

Use Poetry to add dependencies and regenerate `poetry.lock`; never edit the
lockfile by hand. Justify new runtime dependencies and maintain one authoritative
runtime dependency declaration. Generated package metadata, builds, caches,
coverage reports, and rendered docs are not hand-edited source files.

Documentation setup and strict local checks:

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
poetry run pytest -q tests/integration/test_docs_tutorial.py
```

Run `git diff --check` and inspect new, untracked files as well. Documentation-only
work needs link, consistency, privacy, and whitespace checks; it does not require
installing dependencies or changing application code. Report missing tools and
unexecuted checks accurately. The CI runs Poetry checks, Ruff,
pytest/coverage, Bandit, and fresh artifact validation on Linux/macOS/Windows
and Python 3.12–3.14. It ignores several documentation paths; release validation
also runs strict Sphinx and rendered-reference checks. Configured CI does not
establish hosted success.

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

For releases after `1.0.0`, new public callables/classes/exceptions need
`.. versionadded:: X.Y.Z`; public behavior or signature changes need
`.. versionchanged:: X.Y.Z`. Preserve earlier directives, including the bare
initial-release directive on public CLI callables. Other initial-release
callables do not need retroactive directives.

In CLI docstrings, place version directives below `\f` and above field lists;
elsewhere, add them after field lists. Use the intended stable version from
`pyproject.toml` without prerelease suffixes. Private refactors receive no public
directives. The CLI is the supported public interface; do not expose an
unsupported Python library API incidentally.

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
generated keys, and temporary Git repositories. Tests live in
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

Do not execute historical concept scripts against real vaults. They can modify
files in place, overwrite keys and continue after errors; they are references,
not production code or migration tools.

## Security and data preservation

Use synthetic content and placeholder paths in code, tests, docs, issues, and
logs. Never include real key contents, credentials, vault content, or identifying
local paths in tracked artifacts. Clearly labeled synthetic compatibility keys
are permitted only as fixtures and must never protect real data or appear in
CLI output. Historical planning material is public-safe; `local/` is ignored private
material, not a fixture source. Relevant safe docs in `local/vendor_docs/` may
be read if present; other private material requires explicit authorization.
Do not inspect `.env` or real keys to discover credentials or test availability.

Preserve these safety contracts:

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

See [SECURITY.md](SECURITY.md) and [the threat-model guide](docs/SECURITY.md).

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

Add entries to `docs/CHANGELOG.md` under `[Unreleased]`
using Keep a Changelog categories. Preserve version compatibility; public
interface and backup-format changes require maintainer review. Package version
and backup-format version are separate contracts. Version promotion requires
an explicit request; do not bump versions incidentally.

Use single backticks for Markdown/MyST inline code. Double backticks belong in
`.rst` files and reST docstrings. Sphinx/reST/MyST docs use the PyData theme
with a dark default and reader-selectable light mode. Do not copy private content or unrelated
extensions from reference projects. Check local links and examples without
claiming unexecuted validation. See [docs maintenance](docs/maintainers/documentation.md).

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

Follow [the maintainer release runbook](docs/maintainers/releasing.md) for version
promotion, fresh candidate validation, exact-commit builds, bare annotated tags,
GitHub drafts, manual Twine uploads and post-release verification. The optional
manual publication workflow requires separate authorization and configured
external protections; GitHub release events never initiate uploads.

## Handoff checklist

Before returning work, inspect the diff and status and verify scope and privacy.
Report what changed with file links, acceptance criteria met, checks actually
executed, limitations, remaining work, dependency blockers, and the next eligible
task. Update issue evidence for completed or partial work without
overstating completion. State the accurate Git status and whether changes remain
uncommitted.

This guide and the issue templates were adapted from the public
[SalesPyForce contributor guide](https://github.com/jeffshurtliff/salespyforce/blob/2cbc66bc4fee815e27b748990222c97c1fe0222e/CONTRIBUTING.md)
and [issue templates](https://github.com/jeffshurtliff/salespyforce/tree/2cbc66bc4fee815e27b748990222c97c1fe0222e/.github/ISSUE_TEMPLATE),
with Obfuscidian's agent instructions controlling project-specific behavior.

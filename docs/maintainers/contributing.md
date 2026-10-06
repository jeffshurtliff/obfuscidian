# Contributing

The repository's [CONTRIBUTING.md](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md)
owns detailed contributor policy; [AGENTS.md](https://github.com/jeffshurtliff/obfuscidian/blob/main/AGENTS.md)
is the canonical guide for every agent. Read both and the approved roadmap before
changing code. Direct maintainer instructions define authorized scope.

## Setup and checks

Use Python 3.12+ and Poetry 2.2 or newer, below 3.0:

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
git diff --check
```

Use Poetry to manage dependencies and regenerate `poetry.lock`; never edit it
manually or add a second runtime dependency list. Generated docs/builds/caches
are ignored artifacts. The docs group is optional and contains no runtime tools.

## Code, docs and tests

Follow PEP 8, focused typed functions, a thin Click layer and shared constants.
Use pathlib and binary I/O, preserving exact bytes. Git subprocesses use argument
lists. Ruff uses 130 columns, single-quoted ordinary strings, triple-double-quoted
docstrings, spaces and LF. PEP 257 docstrings use Sphinx field lists for parameters,
returns, exceptions and material limitations.

New Python modules/tests use the repository header convention. Preserve
`Created By`; on changed files update `Last Modified` to
`Jeff Shurtliff (via <actual-model-identifier>)` and `Modified Date` to the local
date as `DD Mon YYYY`. Use the actual generating model, not a pinned sample.

During initial `1.0.0` development, public version directives are not required
except for the existing CLI exception: each public CLI callable includes one
bare `.. versionadded:: 1.0.0` below `\f` and before its field list. Later releases
require version-added/changed directives for public changes while preserving
earlier ones. Private refactors get no public version directives.

Use deterministic offline pytest fixtures in `tests/unit/` and
`tests/integration/`, temporary vaults/repos and synthetic keys. Behavior changes
need meaningful tests; fixes need regression tests. No concurrent CliRunner calls
in interpreter threads. Real vault/cloud tests need separate authorization.
Do not run historical `dev/example-*.py` against real data.

Update user docs for observable behavior and `docs/CHANGELOG.md` under Unreleased
with Keep a Changelog categories. Package and format versions are separate;
do not bump either incidentally. Use single backticks in Markdown/MyST and double
backticks in reST. See [documentation maintenance](documentation.md).

## Issues, review and authorization

Use the existing roadmap issue and actual repository issue templates. Base
branches on `main`; Codex uses `codex/<type>/<issue-number>-<description>` when a
real issue exists. Do not invent an issue just for naming. Preserve user edits
and keep work focused. Post public-safe start/progress/handoff evidence for the
requested task. Leave its issue open pending maintainer review/closure.

Stage, commit, push, PR, merge, tag, release and publication each need explicit
maintainer authorization. Authorized commits use past tense, a filename for a
single-file change, and the applicable issue number. PRs explain the resulting
behavior, checks and limits, following any actual template and configured labels
(including `codex` for Codex work). No PR template is currently configured.

Do not trigger the template release workflow. Release preparation remains
a separate task. A handoff states actual Git status,
executed/skipped checks, blockers and next eligible work. Never equate local
results with hosted CI, publication or guaranteed recovery. Handle suspected
vulnerabilities through [private reporting](../SECURITY.md#report-a-concern-privately).

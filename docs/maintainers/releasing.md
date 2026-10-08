# Preparing and publishing a stable release

This is the maintainer runbook for Obfuscidian. The distribution and import
package are `obfuscidian`; the supported public interface is the CLI. Poetry
uses static `[project].version` in `pyproject.toml`. Stable tags are bare,
annotated versions such as `1.0.0`, and the primary branch is `main`.

## Authorization and release order

Preparation authorizes local version/docs edits, synthetic checks, fresh builds
and artifact inspection. Staging, committing, merging, pushing, tagging,
GitHub draft creation, uploads and GitHub publication need explicit maintainer
instructions. An existing authorization remains valid within its stated phase;
never treat a request to prepare as permission to publish.

For 1.0.0, the maintainer chose three checkpoints:

1. Prepare stable metadata, release notes, documentation, runbook and workflow;
   validate locally, then pause with changes uncommitted for review.
2. After approval, commit the release branch, merge into `main` and push. Wait
   for the nine CI jobs on the exact merged commit. Build fresh distributions
   from that clean commit, create/push the annotated `1.0.0` tag and create the
   GitHub draft titled `obfuscidian 1.0.0` with archives and checksums attached.
   Pause while the maintainer uploads those exact files using Twine.
3. After confirmed PyPI upload, verify version, hashes and clean installation;
   publish the existing GitHub draft and close the release issue. Verify stable
   documentation or report its outstanding external setup.

The adjustment to the merge/tag order is deliberate: wait for exact-commit CI
before exposing the public tag. Preparation archives are review candidates;
rebuild from the final clean merged commit for publication. PyPI and GitHub
must use the same unchanged archives. GitHub release events do not upload to
PyPI. Do not dispatch the optional upload workflow after a manual Twine upload.

## Preflight facts and compatibility

Record the target version/date, existing release issue, branch, exact source SHA,
previous reachable stable tag (none for the first release), required checks and
publication method. Use a real issue number; preserve an existing maintainer
branch. New Codex branches use `codex/chore/<issue>-prepare-<version>-release`.

```sh
poetry --version
poetry version --short
git status --short --branch
git remote -v
git log -5 --oneline
git tag --merged main
git ls-remote --tags origin refs/tags/1.0.0
```

For 1.0.0, the release date is `2026-10-08`. Check the version-specific
[PyPI JSON endpoint](https://pypi.org/pypi/obfuscidian/1.0.0/json): HTTP 404 means
unused; HTTP 200 means the version exists and cannot be reused. Network or
permission failures are unresolved checks, not evidence of availability.

Review public [dependency advisories](https://github.com/advisories), official
[cryptography release notes](https://cryptography.io/en/latest/changelog/) and
[urllib3 release notes](https://urllib3.readthedocs.io/en/stable/changelog.html).
Compare dependency floors and locked versions; do not refresh the lock merely
for a version promotion. No audit proves the absence of unknown vulnerabilities.

Retain backup-format v1 compatibility, the 50 MiB encrypted-token cap, exact byte
preservation and documented [platform limits](../PLATFORMS.md). Linux/macOS
support vault writes; native Windows mutation/recovery and existing-log append
remain refused in 1.0.0. A stable classifier does not expand platform capabilities.

## Prepare source and documentation

```sh
poetry version 1.0.0
poetry check --lock --strict
```

Set the Production/Stable classifier for a stable release. Move Unreleased
entries into `## [1.0.0] - 2026-10-08`, retain an empty category skeleton and
update comparison links using the bare tag. For the initial release, link the
version heading to its release page instead of inventing a previous tag.

Review README, security/contributor/agent guidance, Sphinx pages, packaged docs,
CLI version output and packaging expectations. Historical planning artifacts
remain in the repository and are excluded from distributions. Documentation
reads metadata from `pyproject.toml`; never hand-edit generated metadata or docs.

```sh
poetry install --with dev,docs --no-interaction
poetry check --lock --strict
poetry run ruff check .
poetry run ruff format --check .
poetry run coverage run -m pytest -q -ra
poetry run coverage report
poetry run bandit -r src/obfuscidian
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
git diff --check
```

The ordinary suite is offline with temporary synthetic vaults/repositories/keys.
Real vault or cloud tests need separate authorization. Report platform skips,
unexecuted hosted CI and optional external linkcheck separately. Rendered review
must confirm stable version, usable navigation and honest platform guidance.

## Validate fresh candidates

From the repository root, choose a new candidate directory:

```sh
RELEASE_DIST_DIR=$(mktemp -d)
poetry run python .github/scripts/check_artifacts.py \
  --output-dir "$RELEASE_DIST_DIR" --expected-version 1.0.0
```

The helper refuses a nonempty output directory. It builds exactly one wheel and
sdist with Poetry, runs strict Twine checks, downloads a temporary dependency
wheelhouse with top-level runtime/build versions pinned to the installed Poetry
environment and transitives resolved by pip, and runs the packaging suite.
Each artifact is installed in a separate fresh venv outside the checkout,
without system packages or editable-path overrides. Checks cover exact archive
allowlists, metadata/license/classifier, both entry points, `pip check`, the
frozen synthetic v1 fixture and installed backup/verify/restore/Git round trips
where the platform permits writes. SHA-256 hashes are written to `SHA256SUMS`.
The helper requires network access to populate the dependency wheelhouse;
subsequent installation/tests use it offline. It uploads nothing.

Also install the wheel with `--no-deps` into another temporary venv and assert
`importlib.metadata.version('obfuscidian') == '1.0.0'`; this is a metadata-only
check, separate from dependency-aware functional validation. Inspect the full
diff, archive contents, README rendering and candidate hashes before review.
Any failed check blocks release readiness; do not weaken checks to proceed.

## Approved merge, exact-commit build and GitHub draft

Stage only reviewed files. Use a focused past-tense message referencing the
release issue, such as `Prepared obfuscidian 1.0.0 release (#14)`. When the
maintainer authorizes a local merge, synchronize `main`, merge without rewriting
history and push `origin/main`. A PR is a separate action when requested.

Wait for the Test workflow to pass all Linux/macOS/Windows × Python 3.12–3.14
jobs on the exact merged SHA. Verify local `main`, `origin/main` and GitHub agree.
Build fresh archives from that clean commit in a new output directory using the
candidate command above. Retain the commit SHA, validation evidence and hashes
in the release issue. Never upload pre-merge candidates.

Only after those checks and the applicable approval:

```sh
git tag -a 1.0.0 -m "obfuscidian 1.0.0"
git push origin refs/tags/1.0.0
gh release create 1.0.0 --repo jeffshurtliff/obfuscidian --verify-tag \
  --draft --title "obfuscidian 1.0.0" --notes-file "$RELEASE_NOTES_FILE" \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0-py3-none-any.whl" \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0.tar.gz" \
  "$RELEASE_DIST_DIR/SHA256SUMS"
```

`RELEASE_NOTES_FILE` is a reviewed public-safe Markdown file, summarizing the
release and its Windows limits, with a full-changelog link at tag `1.0.0`.
Confirm the tag peels to the verified main SHA and the release is still a draft,
not a prerelease. Creating a draft is a review checkpoint, not publication.

## Maintainer Twine upload and verification

Run strict checks on exactly the intended wheel and source archive:

```sh
poetry run twine check --strict \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0-py3-none-any.whl" \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0.tar.gz"
poetry run twine upload --repository pypi \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0-py3-none-any.whl" \
  "$RELEASE_DIST_DIR/obfuscidian-1.0.0.tar.gz"
```

Enter credentials through Twine's prompt or the maintainer's existing secure
configuration. Never include tokens in commands, logs or tracked files. The
checksum file is a GitHub asset, not a PyPI distribution. Do not use
`--skip-existing` to hide a conflicting or partial upload. An optional TestPyPI
rehearsal needs separate authorization and does not reserve a production version.

Compare PyPI filenames and SHA-256 values with the local `SHA256SUMS`. In a new
venv outside the checkout, install `obfuscidian==1.0.0` from PyPI, run `pip check`,
both help/version entry points and a synthetic round trip on a supported write
platform. After verified upload and authorization, publish the existing draft:

```sh
gh release edit 1.0.0 --repo jeffshurtliff/obfuscidian --draft=false --latest
```

Verify the public title/tag/assets, stable status, PyPI metadata and hashes,
record remaining limitations, then close the existing release issue when its
acceptance criteria and maintainer closure instruction are satisfied.

## Optional guarded trusted publishing

`.github/workflows/publish.yml` is manual-dispatch-only. Dispatch from `main`
with an existing stable tag. Validation requires an annotated tag on main,
matching package metadata and dated changelog, the full reusable nine-job test
matrix, strict docs checks, inspected/installed fresh artifacts and checksums.
Tests and builds use the resolved commit SHA from preflight instead of resolving
the tag again.
`publish` defaults to false; only an explicitly authorized true selection reaches
the upload job, which alone has `id-token: write`.

Before any upload dispatch, the maintainer must separately configure/verify:

- GitHub environment `release` with required reviewers, self-review restrictions
  where available, and deployment branch policy limited to `main`.
- PyPI trusted publisher for repository `jeffshurtliff/obfuscidian`, workflow
  `publish.yml`, environment `release`, following
  [PyPI trusted publishing guidance](https://docs.pypi.org/trusted-publishers/using-a-publisher/).
- Repository/tag protections, workflow permissions and project-name ownership.
- A single selected upload method and evidence that the version is still unused.

These external controls are prerequisites, not configured by preparation code.
The 1.0.0 procedure uses manual Twine, so no workflow dispatch, environment or
publisher configuration is required for that upload. Never dispatch an upload
for a version already uploaded manually. Workflow code review/local tests do not
establish a successful hosted run or correctly configured external protections.

## Failure recovery and later work

Before pushing a tag, fix the reviewed branch, rerun affected checks and rebuild
from the corrected merged commit. Do not silently move a public tag. After any
public tag or draft exists, record the failure and decide whether a new patch
version is safer before changing externally visible state.

For a partial PyPI upload, identify the accepted unchanged files and compare
hashes. Upload only a validated missing file from the same candidate set; do not
rebuild accepted filenames. Incorrect published artifacts need a new release;
PyPI deletion does not make a filename reusable. After publication, never
reuse, overwrite or retag that version; consider an authorized yank/advisory.

Verify the Read the Docs `stable` build resolves to the new tag, and `latest`
remains coherent. Account/repository connection and version activation are
external actions; report unavailable verification explicitly. See
[documentation maintenance](documentation.md). Keep the dated source changelog
and release evidence distinct from the time GitHub/PyPI actually publish.

Choose the next development version in separate work after publication; do not
guess or bump it during this release. Candidate follow-ups include native Windows
write/recovery support, filesystem capability detection, durable Git recovery
ownership and bounded cleanup/retention of rollback snapshots. Each needs its
own reviewed design, meaningful tests and explicit scope.

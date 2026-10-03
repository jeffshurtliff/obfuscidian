---
name: Maintainer Release
about: Internal tracking for preparing an Obfuscidian stable release and separately authorized publication
title: "[CHORE] Prepare Obfuscidian <version> stable release"
labels: maintainer, chore
assignees: []
---

This template creates a public issue. Use synthetic examples and placeholder paths;
never include real keys, vault content, credentials, or identifying local paths.

## Release Summary

Prepare a reviewable release candidate. Stable-version promotion and publication
require separate, explicit maintainer instructions.

- Current version (from): `X.Y.Z.devN`
- Target stable version (to): `X.Y.Z`
- Target release date, if agreed: `YYYY-MM-DD`

Follow [Thread 14 of the implementation roadmap](https://github.com/jeffshurtliff/obfuscidian/blob/main/dev/IMPLEMENTATION_PLAN.md#thread-14--release-preparation),
[AGENTS.md](https://github.com/jeffshurtliff/obfuscidian/blob/main/AGENTS.md), and
[CONTRIBUTING.md](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md).
Thread 14 depends on Thread 13 and will establish the maintainer release runbook
and reviewed publication workflow. Do not assume those deliverables exist.

---

## Motivation

Why is this release being prepared now? Link completed roadmap work, relevant
issues, and pull requests. Identify any remaining release blockers.

---

## Release Facts to Confirm

Resolve values from actual metadata, code, and validation; do not guess.

- Distribution name: `obfuscidian`
- Primary branch: `main`
- Previous stable tag, if any:
- Proposed target tag and tag convention (requires maintainer decision):
- Release branch: `chore/<issue-number>-prepare-<version>-release`;
  Codex uses `codex/chore/<issue-number>-prepare-<version>-release`
- Next development version, if separately requested:
- Supported Python versions and dependency floors: current `pyproject.toml` and CI
- Backup-format compatibility and release-specific security considerations:
- External publishing prerequisites still unconfigured or unverified:

---

## Change Set Since Last Stable Tag

Summarize features, fixes, security work, breaking changes, dependency changes,
and Python support changes. For the first release, describe the initial scope
without inventing a previous stable tag.

---

## Authorization Checkpoints

An issue or preparation request does not grant any of these permissions. Record
explicit maintainer authorization for each action separately:

- [ ] Promote the development version to the requested stable version
- [ ] Stage changes
- [ ] Commit changes
- [ ] Push the release branch
- [ ] Open the preparation pull request
- [ ] Merge the preparation pull request
- [ ] Create a release tag
- [ ] Push the release tag
- [ ] Upload distributions to TestPyPI (optional rehearsal)
- [ ] Upload distributions to production PyPI
- [ ] Create a GitHub Release
- [ ] Publish a GitHub Release
- [ ] Configure or activate external publication automation

The current template workflow publishes on a GitHub release event. Do not create
a release or trigger that workflow during preparation. Thread 14 must replace
its assumptions before release use. Coordinate publication methods so one
authorized action does not accidentally start a second upload.

---

## Checklist

Preparation (local and reviewable):

- [ ] Thread 13 prerequisites completed; scope and version confirmed
- [ ] Work based on `main`; existing user changes preserved
- [ ] Version edits limited to explicitly requested changes; lock regenerated through Poetry if needed
- [ ] Changelog, docs, version metadata, and compatibility policy reviewed
- [ ] Available Poetry lock, Ruff lint/format, pytest, Bandit, strict Sphinx, and whitespace checks pass
- [ ] One fresh wheel and sdist built in an isolated candidate directory
- [ ] Strict Twine checks, archive contents, metadata, and checksums verified
- [ ] Each artifact installed with dependencies outside the checkout
- [ ] Installed console/module help and synthetic backup/verify/restore round trip verified
- [ ] No keys, real vault data, private files, or generated clutter in candidate archives
- [ ] Maintainer runbook and safe publication workflow proposal reviewed
- [ ] Unexecuted hosted checks and external prerequisites reported explicitly

Publication (only through the separately authorized, reviewed procedure):

- [ ] Required CI and release checks pass for the exact release commit
- [ ] Tag, version, changelog, and verified artifacts agree
- [ ] Authorized distribution upload completed and clean installation verified
- [ ] Authorized GitHub Release completed with verified artifacts
- [ ] Documentation publication verified if separately authorized
- [ ] Next development cycle handled as separate work if requested

---

## Done When

State whether this issue covers preparation only or separately authorized
publication. Preparation is complete when candidate artifacts and the runbook
are validated and remaining external blockers are explicit. Publication is
complete only after the authorized steps are verified; do not close a
publication milestone on the strength of local preparation alone.

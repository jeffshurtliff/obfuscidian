# Performing an additive or merge restore

Use this when your vault already uses Git and you want to review restored
files alongside a committed version. If Git is new to you, start with
[a fresh restore to a new folder](fresh-restore.md).

An additive restore keeps files from the selected Git version and overlays
files from the backup. Where both have the same filename, the backup's contents
win. This is a review workspace, not an automatic text merge of note contents.

## Before you start

On Linux/macOS, you need Git, a complete backup, its key, and a vault whose root
is an existing Git repository with a commit. Commit or safely move any pending
changes yourself first: untracked and ignored files, including empty folders,
prevent this operation. Pause editing and sync.

The example assumes an existing local branch called `main`. Choose a new branch
suffix and a new review folder outside existing Git worktrees. The review
folder's parent must exist. See the [detailed Git requirements](../RESTORE.md#origin-base-branch-and-output-checks)
if any of these checks fail; do not delete notes just to make the check pass.

## 1. Preview the review workspace

```bash
obfuscidian unshroud merge --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --base-branch main --branch review \
  --worktree ./vault-review --non-interactive --dry-run
```

Here, `--origin` is your existing Git vault. `--worktree` is a separate working
folder linked to that repository. `--branch review` names a new branch
`obfuscidian/review`. The preview creates none of these.

## 2. Restore into it

```bash
obfuscidian unshroud merge --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --base-branch main --branch review \
  --worktree ./vault-review --non-interactive --verbose
```

The original checkout stays as it was. Restored differences in `vault-review`
are left unstaged and uncommitted. `--verbose` shows the review location and
can display filenames, so keep that output private.

## 3. Review before accepting changes

```sh
git -C ./vault-review status --ignored
git -C ./vault-review diff --no-ext-diff --no-textconv
```

Inspect new and ignored files as well as tracked changes. Obfuscidian does not
stage, commit, merge or push. You must review and commit selected changes
manually before they can be merged back into your working vault.

See [manual review and ignored data](../RESTORE.md#manual-review-and-ignored-data)
for that Git workflow and safe handling of failures. For an exact copy of the
saved snapshot, use [fresh restore](fresh-restore.md).

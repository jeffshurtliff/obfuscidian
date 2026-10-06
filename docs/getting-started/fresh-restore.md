# Performing a fresh restore

“Unshroud” turns the encrypted backup into readable files using its original
key. For your first restore, choose a **new folder**, leaving your working
vault alone. These Linux/macOS examples continue the [Quickstart](quickstart.md).
The commands below use `restored-again`, so they also work after that exercise.
Choose another new name if you have already created this folder.

## 1. Preview a restore to a new folder

```bash
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored-again \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
```

During a restore, `--origin` names the **readable destination**. Its parent
folder must exist. The command checks the complete backup before restoring;
the preview creates no destination or readable copies.

## 2. Restore the files

```bash
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored-again \
  --key ./keys/obfuscidian-demo.key --non-interactive
```

Open the restored notes and attachments. For the Quickstart note, compare it:

```bash
cmp vault/Hello.md restored-again/Hello.md
```

No output from a successful `cmp` means the two files have identical bytes.
After checking the result, you can open the restored folder as an Obsidian vault.

## Before replacing an existing vault

A fresh restore replaces the existing readable files with the saved snapshot.
Files absent from the backup do not remain in the restored vault. Pause editing
and sync, preview first, and read the [full restore guide](../RESTORE.md).

Obfuscidian retains the previous files in a separate rollback folder. Those
files are **readable, sensitive plaintext**; protect them and review them before
cleanup. There is no automatic cleanup of older rollback copies.
`--non-interactive` does not approve replacement; explicit consent is required.

Older notes retained by `shroud merge` are part of the saved snapshot and can
return in a fresh restore. A failed restore needs the guidance in
[Troubleshooting](../TROUBLESHOOTING.md), rather than deleting recovery files.

**Next:** read [additive or merge restore](merge-restore.md) if you use Git.

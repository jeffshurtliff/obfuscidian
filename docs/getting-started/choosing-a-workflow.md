# Deciding how you'll use Obfuscidian

Start with a **fresh backup** and a restore into a **new folder**. This is the
simplest way to learn and check that your backup works before using real notes.

## Choose a backup style

| Your goal | Choose | What happens to deleted notes? |
| --- | --- | --- |
| Keep a snapshot of the vault's current included files | `shroud fresh` | Removed from the new snapshot; previous backup copies may remain |
| Keep older backup entries while adding or updating notes | `shroud merge` | Retained in the backup, so they can return during restore |

“Fresh” does not mean every unchanged file is encrypted again. Obfuscidian can
reuse unchanged encrypted data. “Merge” is additive: exclusions and renames do
not remove previously backed-up entries.

## Choose a restore style

| Your goal | Choose | What you need |
| --- | --- | --- |
| Recreate the saved snapshot as readable files | `unshroud fresh` | A separate destination folder; use a new one for practice |
| Combine backup files with an existing Git version for review | `unshroud merge` | A clean, committed Git vault and comfort reviewing changes in Git |

These choices are independent. Either restore style can read a backup made
with either backup style. A backup that retained older notes can restore them,
even when you choose a fresh restore.

## Decide where to keep the backup

Obfuscidian creates an encrypted folder on your filesystem. Copying it to
another device or managing it in a private Git repository is a separate step
you control. Keep the entire `.obfuscidian` folder together; it contains both
the encrypted file data and the information needed to restore their names.
Keep the key separately, with an offline copy.

Before using real notes, pause Obsidian editing and sync during backup or
restore, and practice a complete restore. These write examples need Linux or
macOS; see [platform limits](../PLATFORMS.md).

**Next:** [Create a shrouded backup](creating-a-backup.md).

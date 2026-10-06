# Creating a shrouded backup

“Shroud” means making an encrypted copy of your vault. Your original files stay
readable and unchanged. These Linux/macOS examples continue the
[Quickstart](quickstart.md), using `vault`, `mirror` and the existing demo key.

## 1. Preview a fresh backup

Pause Obsidian editing and sync if you are using a real vault. Choose a separate
mirror folder; its parent folder must already exist. Keep the key outside both.

```bash
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
```

Read the planned counts and any warnings. A preview does not create the mirror
or change an existing backup.

## 2. Create it

```bash
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key
```

The command can ask for consent if it will replace existing backup data.
Approve only after checking the locations and preview. If nothing has changed,
a matching backup can finish without rewriting data.

The mirror contains a `.obfuscidian` folder with encrypted data and a file
called `manifest.obf`, which records the original names in encrypted form.
Keep this complete folder together. Normal notes, attachments, hidden files,
Obsidian settings and empty folders are included; Git controls and
`obfuscidian-*.key` files are always excluded. Keep other secrets out of the vault.

## 3. Check the result

```bash
obfuscidian verify --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive
```

Successful verification checks the whole backup. A practice restore checks
that you can also recreate and read your notes.

For an additive backup, choose `shroud merge` after
[reviewing how it retains older entries](choosing-a-workflow.md).
See the [backup guide](../BACKUP.md) for exclusions, replacement consent,
retained previous backups and recovery.

**Next:** [Perform a fresh restore](fresh-restore.md).

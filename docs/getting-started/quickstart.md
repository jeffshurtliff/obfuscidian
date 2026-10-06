# Quickstart

Make a backup of one fake note, check it, and restore it to a new folder.
You will leave your real vault untouched.

## Before you begin

[Install Obfuscidian](installation.md), then open a terminal on Linux or macOS.
Keep the same terminal open for all four steps. These commands use a temporary
practice folder; native Windows does not support the backup/restore writes.

## 1. Create a practice vault and key

The first commands make a private temporary folder and move your terminal into
it. The remaining commands create a fake note and its key in separate folders.

```bash
umask 077
DEMO_DIR=$(mktemp -d "${TMPDIR:-/tmp}/obfuscidian-demo.XXXXXX")
cd "$DEMO_DIR"
mkdir vault keys
printf '# Hello\n\nThis is a practice note.\n' > vault/Hello.md
obfuscidian keygen --alias demo --dir ./keys --non-interactive
```

The key is saved as `keys/obfuscidian-demo.key`. Keep the file private;
you do not need to open it or copy its contents into a command.

## 2. Preview, then create the backup

```bash
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive
```

`--dry-run` checks the plan without writing anything. The second command creates
`mirror`, your encrypted backup. Your note in `vault` stays readable and unchanged.

## 3. Check the backup

```bash
obfuscidian verify --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive
```

Continue after successful verification. If any command reports an error, stop
and use [Troubleshooting](../TROUBLESHOOTING.md) before trying the next step.

## 4. Restore and compare

```bash
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored \
  --key ./keys/obfuscidian-demo.key --non-interactive
cmp vault/Hello.md restored/Hello.md
```

If `cmp` prints nothing and finishes successfully, the restored note has exactly
the original bytes. You can also open `restored/Hello.md` in a text editor.

Keep the key until you finish experimenting. This practice folder contains
only fake data. For a rehearsal covering attachments, settings and empty
folders, use [Rehearse a complete backup and restore](../guides/restore-rehearsal.md).

**Next:** learn [how to use the CLI](using-the-cli.md).

# Setting up your private key

Your key is a secret file, rather than a password you type. You need the **same
key** to create, check and restore a backup. Losing it means losing access to
that backup; Obfuscidian cannot reset it.

## 1. Choose a private folder

Keep the key outside your vault, encrypted backup, Git repositories and
cloud-synced folders. Keep a separate offline copy somewhere you control.
Anyone who obtains the key and backup can read your notes.

For this Linux/macOS practice example, work in the temporary folder from the
[Quickstart](quickstart.md). If you already generated its demo key, reuse it
and skip the creation commands below.

## 2. Generate a key once

```bash
mkdir -m 700 -p ./keys
obfuscidian keygen --alias demo --dir ./keys --non-interactive
```

`demo` is a label (an **alias**), not a password. This command writes
`keys/obfuscidian-demo.key` without displaying the secret. It refuses to overwrite
an existing key. Choose a new alias when you intend to create a separate key;
a new key will not unlock an older backup.

## 3. Select the file when running commands

Pass its filename, not its contents:

```sh
obfuscidian verify --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive
```

This check needs the backup created in the Quickstart. The same `--key` option
works for backup and restore.

For a real vault, choose your private key location first and quote paths with
spaces. Do not keep its only copy on the same device as the backup.
See [Configuration and key custody](../CONFIGURATION.md) for Windows key
creation, permissions, aliases and environment variables.

**Next:** [Decide how you'll use Obfuscidian](choosing-a-workflow.md).

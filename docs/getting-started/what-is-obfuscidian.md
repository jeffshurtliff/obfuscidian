# What is Obfuscidian?

Obfuscidian makes an encrypted backup of your Obsidian vault. Your notes and
attachments stay where they are; a separate folder holds their encrypted copies.
You can check the backup and turn it back into readable files when you need it.

You use Obfuscidian by typing commands in a terminal. It works with the vault's
files directly, so you do not need an Obsidian plugin.

## Three things to know

- **Vault (origin):** the folder containing your readable notes and attachments.
- **Shrouded backup (mirror):** a separate folder containing encrypted files.
  The original filenames and folder structure are encrypted too.
- **Private key:** a small secret file that lets Obfuscidian encrypt and restore
  your backup. Keep it outside both folders and keep a separate offline copy.

The basic flow is:

```text
Your vault → shroud → Encrypted backup → unshroud → Readable vault
                         ↑
                       verify
```

`verify` checks that the whole backup can be authenticated with your key.
A practice restore also lets you check that your notes come back as expected.

## Is it right for my vault?

Backup and restore writes currently work on Linux and macOS. On native Windows,
you can create a key, verify an existing backup and preview operations; writing
or recovering vaults is refused in 1.0.0. See [supported environments](../PLATFORMS.md).

Encryption protects the backed-up contents and names. Someone who has your key
can read the backup, and someone viewing the encrypted folder can still see
file counts, encrypted sizes and changes. Obfuscidian does not upload or sync
backups; storing them elsewhere is your choice.

**Next:** try the [Quickstart](quickstart.md) with one fake note.

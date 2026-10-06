# Rehearse a complete backup and restore

Run this with **synthetic data only** on Linux/macOS, in a POSIX shell such as
bash or zsh, after [installation](installation.md). It creates a fresh temporary
workspace outside Git. The key, source, mirror and restore destination are
separate siblings. No real vault, cloud service or Git hosting is used.

The commands form one complete rehearsal. Keep the same shell open so `DEMO_DIR`
remains available. `python` and `obfuscidian` must be on PATH (developers can use
`poetry run bash` first). The keygen parent is created privately; its generated
key is never displayed. The source contains Markdown, Unicode, a binary
attachment, hidden/settings files, a zero-byte file and an empty directory.

```bash
set -eu
umask 077
DEMO_DIR=$(mktemp -d "${TMPDIR:-/tmp}/obfuscidian-demo.XXXXXX")
export DEMO_DIR
cd "$DEMO_DIR"
python - <<'PYTHON'
from pathlib import Path

Path('keys').mkdir(mode=0o700)
vault = Path('vault')
for name in ('notes', 'attachments', '.obsidian', 'empty'):
    (vault / name).mkdir(parents=True, mode=0o700)
(vault / 'notes' / 'Welcome.md').write_bytes(b'# Demo\n\nSynthetic restore rehearsal.\n')
(vault / 'notes' / 'caf\u00e9.md').write_bytes('Fake Unicode note.\n'.encode('utf-8'))
(vault / 'attachments' / 'sample.bin').write_bytes(bytes(range(256)) * 4)
(vault / '.hidden').write_bytes(b'fake hidden data\n')
(vault / '.obsidian' / 'app.json').write_bytes(b'{"fakeDemoSetting": true}\n')
(vault / 'zero.txt').touch()
PYTHON
obfuscidian keygen --alias demo --dir ./keys --non-interactive --dry-run
test ! -e ./keys/obfuscidian-demo.key
obfuscidian keygen --alias demo --dir ./keys --non-interactive
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
test ! -e ./mirror
obfuscidian shroud fresh --origin ./vault --mirror ./mirror \
  --key ./keys/obfuscidian-demo.key --non-interactive
obfuscidian verify --mirror ./mirror --key ./keys/obfuscidian-demo.key --non-interactive
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored \
  --key ./keys/obfuscidian-demo.key --non-interactive --dry-run
test ! -e ./restored
obfuscidian unshroud fresh --mirror ./mirror --origin ./restored \
  --key ./keys/obfuscidian-demo.key --non-interactive
python - <<'PYTHON'
from pathlib import Path

source = Path('vault')
restored = Path('restored')
source_names = {p.relative_to(source) for p in source.rglob('*')}
restored_names = {p.relative_to(restored) for p in restored.rglob('*')}
assert source_names == restored_names, 'Restored names differ'
for name in source_names:
    original = source / name
    copy = restored / name
    assert original.is_dir() == copy.is_dir(), 'Restored type differs'
    if original.is_file():
        assert original.read_bytes() == copy.read_bytes(), 'Restored bytes differ'
assert (restored / 'empty').is_dir()
print('Synthetic restore verified: 6 files, matching bytes and complete directory structure.')
PYTHON
```

Every command must exit successfully; the last line confirms exact content and
structure. Dry runs create neither key nor vault destination. This restore goes
to an absent destination, so no replacement consent or old plaintext rollback
is needed. Fresh success can retain private terminal journals and empty
stage/rollback containers even for these new destinations; that does not mean
a transaction is pending. Read-only verification validates every encrypted record/object.

Keep `DEMO_DIR` for inspection, then remove **only this disposable demo directory**
through your file manager when finished. It contains a synthetic key and plaintext.
Do not copy that cleanup approach to unknown recovery directories or real vaults.

## Rehearse with your own data later

Make an independent backup and keep a separate offline copy of the real key.
Pause editing/sync, preview a backup, write it, verify it, then restore into a
new sibling destination and compare before relying on it. Keep the real key
outside vaults and cloud repositories. Never test first by overwriting your
only origin. Existing destination replacement requires `--yes` unattended;
`--non-interactive` supplies no consent.

`shroud merge` retains deleted, renamed and newly excluded old paths: a later
restore can bring those notes back. `shroud fresh` omits stale entries in the
new snapshot but does not erase Git history or earlier rollback copies. See
[backup](../BACKUP.md) and [restore](../RESTORE.md).

Fresh replacement of an existing plaintext destination retains the previous
payload outside the vault and Git as **sensitive plaintext rollback**. Keep it
until the new restore has been checked; follow [cleanup guidance](../TROUBLESHOOTING.md#retained-plaintext-and-cleanup).

## Windows read-only rehearsal commands

The complete write tutorial above is for Linux/macOS. On native Windows, use
PowerShell with an existing complete mirror made on a supported write platform
and its key stored privately outside both locations. These placeholder paths
must be replaced with separate existing directories; `restored` may be absent.

```powershell
$env:OBFUSCIDIAN_MIRROR_VAULT = 'C:\Demo\mirror'
$env:OBFUSCIDIAN_KEY_PATH = 'C:\Demo\keys\obfuscidian-demo.key'
obfuscidian verify --non-interactive
obfuscidian unshroud fresh --origin 'C:\Demo\restored' --non-interactive --dry-run
Remove-Item Env:OBFUSCIDIAN_MIRROR_VAULT
Remove-Item Env:OBFUSCIDIAN_KEY_PATH
```

No Windows mutation is implied. See [configuration](../CONFIGURATION.md) for
POSIX environment examples and [platform boundaries](../PLATFORMS.md).

# Configuration and keys

`keygen` creates private key files; configuration selects the key and vault locations.
[Backup](BACKUP.md) and [read-only verification](VERIFY.md) use these helpers;
[fresh restore](RESTORE.md) also uses them. The helpers are
internal implementation boundaries; the CLI is the supported public interface.
No vault data is read or written by keygen.

## Generate a key

Use an **existing private directory outside both vaults and their cloud
repositories**. The directory in this example already exists:

```sh
obfuscidian keygen --alias primary --dir ./keys --non-interactive --dry-run
obfuscidian keygen --alias primary --dir ./keys --non-interactive
python -m obfuscidian keygen --help
```

This creates `obfuscidian-primary.key` exclusively. An existing file, directory,
link, or dangling link at that name is a collision. A second generation fails
and preserves the original key. There is no force-overwrite option, `--yes`,
or automatic replacement of a missing or invalid key. Keygen does not use
`OBFUSCIDIAN_KEY_PATH` to choose an output filename.

An alias contains 1–64 ASCII letters, digits, or hyphens. Underscores, dots,
spaces, Unicode characters, and path separators are invalid. CLI `--alias`
overrides `OBFUSCIDIAN_KEY_ALIAS`. CLI `--dir` overrides
`OBFUSCIDIAN_KEY_DIR`; otherwise the directory defaults to home. Explicit empty
or invalid values fail instead of falling back to another value.

When no alias is selected and standard input is a terminal, keygen prompts.
Empty **prompt input** selects local-time `YYYYMMDD-HHmmss`; explicit empty
CLI/environment aliases are invalid. A timestamp collision also fails without
overwriting. EOF exits with an operational error and no key creation.
Redirected input and `--non-interactive` never prompt; both require an explicit
CLI or environment alias. Dry run can prompt under the same terminal rules.

`--dry-run` checks alias, directory, target absence, protected path identities,
and directory write/search access without generating a key or creating keys,
directories, logs, or other application files. On Windows it also checks volume
ACL capability. These read-only checks do not guarantee that a later write will
succeed or that the directory will remain unchanged.

## Paths and loading precedence

Paths expand `~` using home and resolve relative to the current working
directory. Shell variables such as `$NAME` or `%NAME%` are literal within the
application; perform substitution in your shell if desired. Quote paths with
spaces using your shell's quoting syntax. Key directories must already exist;
key paths and every parent component must be free of symlinks/junctions.
Key loading rejects special files and missing files without fallback.

The following precedence applies to `shroud`, `verify` and `unshroud` with
`--key`, `--alias` and `--keydir`:

| Selection | Result |
| --- | --- |
| CLI `--key` | Select that path; ignore environment key selectors; reject CLI `--alias` or `--keydir` |
| CLI `--alias` | Select that alias; ignore environment `KEY_PATH` and `KEY_ALIAS`; directory is CLI `--keydir`, then environment `KEY_DIR`, then home |
| No CLI selector; environment `KEY_PATH` present | Select that path even if invalid; reject CLI `--keydir` as ambiguous |
| No CLI selector/path; environment `KEY_ALIAS` present | Select that alias; CLI `--keydir` overrides environment `KEY_DIR`, then home |
| No selector | Prompt for an alias only with terminal input; a directory-only setting can accompany that prompt; otherwise fail |

All environment key variable names have the prefix `OBFUSCIDIAN_`, for example
`OBFUSCIDIAN_KEY_PATH`. An invalid explicitly selected key is an error and never
causes another selector or generated replacement to be tried. A loading prompt
requires a valid nonempty alias; the timestamp default belongs only to keygen.

The loader validates the complete canonical URL-safe Fernet key. It accepts the
44-byte key with no line ending, one LF, or one CRLF; extra content, whitespace,
malformed encoding, and truncation are errors. Reads are bounded and key bytes
are never included in errors. It returns permission warnings without changing
existing key bytes or permissions.

CLI origin/mirror paths also override `OBFUSCIDIAN_ORIGIN_VAULT` and
`OBFUSCIDIAN_MIRROR_VAULT`, even when invalid. The resolver expands these paths
without creating or inspecting vaults. Vault commands then reject overlap, key placement inside either vault and
unsafe inventory paths before any write.

## Permissions and custody

POSIX key creation uses mode `0600`, exclusive no-follow creation, and protected
directory handles with identity rechecks. Loading warns if group/other access
is allowed or ownership differs from the current user. It does not silently
chmod an existing key. Ordinary write failures remove only the operation's own
new key entry; a changed target or cleanup failure is retained and reported for
inspection. Existing keys are never deleted or overwritten. A process kill or
power loss can leave an incomplete new entry; inspect it before retrying.

Windows creation uses `CREATE_NEW` with a protected owner-only DACL at creation,
and refuses volumes without persistent ACL support. Default file ownership
follows the Windows token's ownership policy. Privileged administrators/backup
operators can still have access, and ACL enforcement depends on the filesystem
and host policy. POSIX `0600` is not a Windows ACL guarantee. Loading warns that
an existing Windows key's ACL has not been assessed; use a private directory
and review access permissions. Parent identity checks on Windows are best effort;
POSIX descriptor-relative protections are unavailable there. The native CI matrix
validated Windows key creation/loading and refusal behavior across Python 3.12–3.14;
see [platform validation](PLATFORMS.md). Existing-key ACL assessment remains absent.

A Fernet key is a symmetric secret: anyone with it can read and forge backups.
Keep a separate offline key backup. Losing the key prevents decryption; there
is no reset or recovery bypass. Do not save it in a vault or encrypted mirror,
and do not share or paste its contents. See the
[Fernet custody reference](https://cryptography.io/en/50.0.2/fernet/).

## Output and exit codes

Keygen never prints key bytes or file contents. Interactive terminal use shows
an escaped output path for handoff. Unattended output redacts paths unless
`--verbose` is selected; even verbose paths escape terminal control characters.
Custody guidance appears after successful generation or dry run.

Exit codes are `0` for success/dry run, `1` for operational/I/O/EOF failures,
`2` for usage/configuration errors (including collisions), and `130` for a
keyboard interrupt after cleanup is attempted. Failed cleanup reports that an
incomplete entry may remain rather than reporting success.

Keygen currently supports `--alias`, `--dir`, `--non-interactive`, `--dry-run`,
and `--verbose`, plus optional `--log-file`/`--log-paths`. Logs are private and
redacted by default; key target locations never enter them. `--log-file` is
rejected with dry run, and `--log-paths` requires an explicit log file. See the
[shared CLI contract](CLI.md). `--recover` and
`--yes` do not apply to keygen.

## Environment examples

Set paths to separate existing synthetic locations. POSIX shell:

```sh
export OBFUSCIDIAN_MIRROR_VAULT='./mirror'
export OBFUSCIDIAN_KEY_PATH='./keys/obfuscidian-demo.key'
obfuscidian verify --non-interactive
unset OBFUSCIDIAN_MIRROR_VAULT OBFUSCIDIAN_KEY_PATH
```

Windows PowerShell:

```powershell
$env:OBFUSCIDIAN_MIRROR_VAULT = 'C:\Demo\mirror'
$env:OBFUSCIDIAN_KEY_PATH = 'C:\Demo\keys\obfuscidian-demo.key'
obfuscidian verify --non-interactive
Remove-Item Env:OBFUSCIDIAN_MIRROR_VAULT
Remove-Item Env:OBFUSCIDIAN_KEY_PATH
```

These examples verify a pre-existing complete mirror. Alias selection can use
`OBFUSCIDIAN_KEY_ALIAS` and `OBFUSCIDIAN_KEY_DIR` instead; do not set
`KEY_PATH` when you intend alias selection. `OBFUSCIDIAN_ORIGIN_VAULT` selects
the source for backup and plaintext destination for restore. No environment
variable contains the key bytes. Windows mutation remains refused. Start with
the [complete synthetic rehearsal](guides/restore-rehearsal.md).

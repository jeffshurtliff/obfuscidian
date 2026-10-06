# Read-only verification

Thread 08 exposes `obfuscidian verify` through the same console and module
entry points. It uses the complete [v1 validator](FORMAT.md), without changing
the backup format or requiring an origin vault. [Fresh restore](RESTORE.md) also uses complete validation.

```sh
obfuscidian verify --help
obfuscidian verify --mirror ./vault-encrypted --key ./keys/obfuscidian-primary.key --non-interactive
python -m obfuscidian verify --mirror ./vault-encrypted --alias primary --keydir ./keys --non-interactive
```

Use an existing mirror and its existing external key. The CLI mirror overrides
`OBFUSCIDIAN_MIRROR_VAULT`. Key selection follows the existing
[precedence/conflict rules](CONFIGURATION.md#paths-and-loading-precedence).
`--key` conflicts with `--alias` or `--keydir`. Paths expand `~` and resolve from
the current directory; explicit invalid selectors never fall back or prompt for
replacements. With terminal input, absent mirror and key-alias selectors prompt.
`--non-interactive` or redirected input disables prompts. Origin configuration
is ignored. A selected key inside the mirror is rejected.

Verification authenticates the manifest before parsing, checks the complete
schema and safe relative paths, requires the exact object set, and checks
every object's ciphertext binding, Fernet authentication, plaintext size and
plaintext binding. It processes one object at a time and rechecks identities,
content and namespace before accepting the result. The 50 MiB encoded-token
cap applies to both manifest and objects; there is no bypass or token TTL.
All recorded objects are checked, including hidden/configuration files and
historic files retained by merge. No exclusion option exists.

Normal output reports complete file/directory counts and plaintext/encrypted
byte totals only after all checks pass. `--verbose` additionally displays
authenticated relative names using escaped representations, also only after
complete validation. Directory counts include empty directories and exclude
the implicit root. Encrypted totals include the manifest and all objects.
Neither mode prints absolute mirror/key paths, key bytes, hashes or content.
Warnings and errors go to stderr, with redacted remediation guidance.

Verification makes **no application writes** on success, failure or interrupt.
It creates no missing paths, logs, locks, worktrees, staging/rollback copies or
recovery metadata, and never repairs, removes or rewrites backup data. It needs
read access, not write access or staging space. `--yes`, `--recover`, `--dry-run`,
write/repair options, restore options, `--exclude`, `--log-file` and `--log-paths`
are rejected as usage errors. Verification is already read-only.

Pending transaction ownership blocks success before and after validation,
including when the managed payload is temporarily missing. Ownership marker
names use the existing conservative case/Unicode comparison. Any matching
marker in a mirror ancestor blocks verification, even if malformed or linked;
verification does not open private ownership/journal records or acquire a lock.
Retained completed workspaces without an ownership marker remain untouched and
do not block verification. Follow the [backup recovery procedure](BACKUP.md)
separately; `verify` never performs recovery.

Exit statuses are `0` for complete validation, `1` for integrity, incomplete
backup, pending ownership or operational failure, `2` for usage/configuration
errors (including unsafe location types or absent parents), and `130` for a
keyboard interrupt. An absent final mirror is an incomplete-backup failure;
no destination is created. Missing data and unknown versions require a complete
supported backup and a compatible reader; wrong keys cannot be reset or replaced
automatically. Use a known-good complete snapshot when data is damaged.

The result is a best-effort observation, not an atomic snapshot, security
certification, freshness proof or target-platform restorability guarantee.
Stop other writers for a more stable observation. OS reads may change access
times; these are not application writes. Valid historic snapshots can pass and
key holders can forge valid data. Root Git controls are checked for allowed
names/types, not authenticated as vault data. See the
[format threat limits](FORMAT.md#read-only-behavior-and-threat-limits).

Thread 08 is complete following maintainer review and merge/push into
`origin/main`; [issue #8](https://github.com/jeffshurtliff/obfuscidian/issues/8)
is closed as completed. The
[verified Linux CI run](https://github.com/jeffshurtliff/obfuscidian/actions/runs/37349183494)
passed on Python 3.12–3.14 at commit `3d3425b`, with 903 tests passed and two
native Windows skips in each job, plus three fully isolated artifact checks.
See the [completion record](../dev/IMPLEMENTATION_PLAN.md#thread-08--read-only-verification-completion-record-5-october-2026)
for commit alignment and validation evidence. Broader platform hardening remains
Thread 12; Linux CI does not establish native Windows or universal filesystem
validation. 

Thread 09 is complete, reviewed and merged/pushed; see
[fresh restore](RESTORE.md) for the accepted Python 3.14 CI gap. 

Thread 10 is complete, reviewed and merged/pushed, with issue #10 closed and
Linux CI passing on Python 3.12–3.14; see
[additive Git merge restore](RESTORE.md#additive-git-merge-restore). 

Thread 11 is complete, reviewed and merged/pushed, with issue #11 closed and
Linux CI passing on Python 3.12–3.14; see the [CLI contract](CLI.md).
Thread 12 remains **not started**.

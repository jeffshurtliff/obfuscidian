# Inventory and path preflight

Thread 03 adds internal read-only helpers now used by
[fresh and additive merge backup](BACKUP.md). The CLI exposes `keygen` and
`shroud fresh|merge`, and [read-only `verify`](VERIFY.md); [`unshroud fresh|merge`](RESTORE.md) is also available.
These helpers are implementation boundaries, not a supported Python library API.

## Included contents and deterministic totals

Inventory includes every regular file as bytes, including Markdown, attachments,
hidden files, `.obsidian`, zero-byte files, and all empty directories. Obsidian
configuration is optional. The source root is implicit rather than a directory
record. Names and bytes are preserved without parsing notes or executing plugins.
Included records use forward-slash relative names, with sizes, signed nanosecond
modification times, and filesystem identity/change indicators. Records are sorted
in ascending case-sensitive string order, independent of locale.

Mandatory exclusions cannot be overridden: `.git` components (directories or
metadata files), `.gitignore` files, and `obfuscidian-*.key` files at any depth.
Git metadata is never traversed. Other secrets cannot be reliably recognized by
filename; users must keep them outside the vault or explicitly exclude them.
The selected key must remain outside both vaults, including encountered hard-link
aliases even when their names would be excluded.

Exclusion matching operates on original relative paths before obfuscation:

| Pattern feature | Meaning |
| --- | --- |
| `*`, `?` | Match within exactly one component |
| `[abc]`, `[a-z]`, `[!a-z]` | Match one character within a component |
| Standalone `**` | Match zero or more complete components |
| Trailing `/` | Match only real directories and prune their descendants |

Patterns are case-sensitive and anchored at the source root. `*.tmp` matches
only root files; `**/*.tmp` also matches nested files. Examples include
`.obsidian/`, `attachments/**`, `**/*.tmp`, and `**/.DS_Store`.
Absolute/drive patterns, `..`, empty or `.` components, backslashes, null
characters, and leading negation/re-inclusion are rejected. An explicitly
excluded link is ignored without traversal; a directory-only pattern does not
turn a link into a safe directory.

Totals report included files, included directories, included plaintext bytes,
and **encountered excluded entries**. A pruned directory counts as one excluded
entry; its unseen descendants are neither scanned nor counted.

## Path and change safety

Preflight requires an existing source directory and existing key file. A new
mirror may have only its final component missing. It rejects roots, same paths,
either-direction nesting, overlap by filesystem identity, keys inside vaults,
linked components/junctions, and included special files. Missing destinations,
locks, logs, staging paths, and rollback copies are never created by these helpers.

Existing mirror namespace checks allow only root `.git`, `.gitignore`, and
`.obfuscidian`; the managed subtree allows `manifest.obf` and `objects/`, whose
files must use 32 lowercase hexadecimal characters plus `.obf`. Types and links
are checked, and unmanaged entries cause refusal. Git metadata contents and
manifest/object authentication/completeness are **not** validated here; format
validation belongs to Thread 04 and publication/transaction checks to Thread 05.
A legal namespace alone never authorizes modifying a mirror.

Stable reads accept only included regular file records and read one bounded
binary file at a time. POSIX traversal and file reads use no-follow directory
handles. Filesystem identity, type, size, mode, mtime, and ctime are rechecked
before/after reads. A final inventory comparison detects observed additions,
deletions, renames, replacements, metadata/content changes, and newly unsafe
entries. Unrelated sibling changes do not invalidate the source. Access time is
not compared because read access may update it; no helper sets timestamps,
permissions, or source content.

These checks provide best-effort change detection, not an atomic filesystem
snapshot. Pause editing, Obsidian sync, and other writers during backup, restore and recovery.
No implementation can promise to detect changes that leave all observed state
identical. Native Windows reads currently rely on pre/post-I/O path/identity
checks. Thread 12 passed the OS/Python matrix while retaining this observation
limit; stronger Windows race guarantees remain unimplemented. Errors contain
actionable generic diagnostics without private paths or source bytes, and
helpers print nothing.

Target name validation takes explicit filesystem rules for case sensitivity,
Unicode comparison, Windows restrictions, and component/full-path limits. It
rejects duplicate names, case/Unicode collisions (including ancestor prefixes),
unsafe serialized paths, Windows reserved names, and unrepresentable lengths;
it never renames or normalizes source data. POSIX control-character names and
lossless UTF-8 names are retained. Consumers must supply the actual target rules;
no writable filesystem probe or universal OS default is assumed. Thread 12
validated conservative comparison/length refusal across the matrix; precise
filesystem capability detection remains future work. See [platform validation](PLATFORMS.md).

## Resource accounting

Every encrypted object and manifest is capped at `50 * 1024 * 1024` bytes.
An exactly-at-cap encrypted length is allowed. Fernet estimates account for
AES padding, its fixed 57-byte overhead, and standard padded Base64 encoding:

```text
padded = 16 * (floor(plaintext_bytes / 16) + 1)
token_bytes = 4 * ceil((57 + padded) / 3)
```

Oversized included files are refused from metadata without reading/allocating
file contents. The resource helper requires the **actual serialized manifest
plaintext size**, provided by the v1 manifest serializer; it does not guess a complete
manifest from inventory counts. It also accepts explicit retained ciphertext
and additional rollback-copy bytes for transaction planning.

Staging totals include all included object tokens, the manifest token, and any
explicit retained ciphertext. Required free bytes add explicitly planned rollback
copies; already allocated destination data is not charged again. Read-only
free-space/access checks operate on an existing chosen parent without reserving
space. These are payload estimates: filesystem allocation, journals, metadata,
and later changes to available space are accounted for by transaction planning.
Thread 05 implements [safe staging and publication primitives](TRANSACTIONS.md).
Callers must still supply complete staging estimates, authenticate format data,
and recheck source inventory. Thread 06 supplies those checks for `shroud fresh`.

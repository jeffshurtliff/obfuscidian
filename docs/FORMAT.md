# V1 encrypted backup format

Thread 04 implements internal byte codecs and complete read-only validation.
Thread 05 adds [internal publication and recovery](TRANSACTIONS.md).
Threads 06–07 expose [fresh/additive merge backup and explicit recovery](BACKUP.md).
Thread 08 exposes [read-only verification](VERIFY.md); [fresh restore](RESTORE.md) uses the complete validator.
These helpers are internal
boundaries, not a supported Python library API.

## Managed layout

```text
mirror/
  .git/                       # optional root Git metadata; directory or file
  .gitignore                  # optional existing root Git configuration
  .obfuscidian/
    manifest.obf
    objects/
      <32-lowercase-hex-id>.obf
```

A complete mirror requires both the manifest and the objects directory, even
for an empty snapshot. Objects are flat: each included file has exactly one
opaque ID and one standard Fernet token. Empty directories live in the
manifest. Root Git controls are inspected for safe types but never traversed,
authenticated, interpreted, or modified by the format validator. Publication
preserves these controls in place; transaction preflight also recognizes
enclosing Git markers without interpreting Git contents.

Unknown root or managed entries, unexpected objects, missing objects,
links/junctions, and special files fail validation. No override is provided.
No source names, hierarchy, file listings, or plaintext hashes are written
outside the encrypted manifest. Tests use synthetic data only.

## Manifest schema

The decrypted manifest is strict UTF-8 JSON with exactly these fields. Format
version `1` is independent of the package version. Duplicate JSON member names,
non-finite numbers, unknown fields, incorrect types, and unsupported versions
are rejected. Booleans and floating-point values do not count as integers.

| Field | V1 representation |
| --- | --- |
| `format_version` | Integer `1` |
| `vault_id` | Random 32 lowercase hexadecimal characters, identifying the mirror lineage |
| `snapshot_id` | Random 32 lowercase hexadecimal characters, identifying a logical publication |
| `created_at` | Valid UTC calendar timestamp `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`; optional fraction has one through six digits |
| `directories` | Array of objects with exactly `path` and `mtime_ns` |
| `files` | Array of objects with exactly `path`, `object_id`, `size`, `mtime_ns`, `plaintext_sha256`, and `ciphertext_sha256` |

`path` is a nonempty, lossless UTF-8 relative name using forward slashes.
No root record is stored. Absolute/drive/UNC names, backslashes, NUL,
empty components, `.` and `..` are invalid. Paths are preserved byte-for-byte
in UTF-8: no case folding or Unicode normalization is applied to stored names.
Each non-root parent must have a directory record. Duplicate paths across
both arrays, file/directory conflicts, and duplicate object IDs fail.
Mandatory source exclusions also apply: no `.git` component, `.gitignore` file,
or `obfuscidian-*.key` file may appear in a manifest.

`object_id` is 32 lowercase hexadecimal characters. Both SHA-256 fields are
64 lowercase hexadecimal characters. `size` is the nonnegative integer length
of the original bytes, constrained by the encrypted object cap. `mtime_ns` is
a signed integer count of nanoseconds; pre-epoch values are accepted. Actual
target timestamp representability and timestamp preservation belong to restore.

Canonical serialization uses compact JSON, sorted member names, literal UTF-8
Unicode, and each record array sorted case-sensitively by path, independent of
locale. Readers accept different whitespace/member/record order and return
sorted immutable records. They reject a UTF-8 BOM and unpaired surrogates.
JSON structure is bounded to the schema's three container levels before parsing;
invalid/deeper structures cannot cause unbounded parser recursion.

## Encryption, binding, and limits

The implementation uses `cryptography.fernet.Fernet.encrypt` and `decrypt`
without a TTL. It preserves standard URL-safe Base64 encoding and padding.
Each object encrypts the complete original binary bytes. The manifest encrypts
the complete serialized JSON. No custom cipher, password derivation, chunking,
compression, additional Base64 layer, or key mixing is introduced.

Every token, including the manifest, is capped at **50 × 1024 × 1024 bytes**.
Exactly-at-cap valid tokens are accepted. Reads are bounded before decryption;
serialization checks actual JSON bytes and projected token length. For `n`
plaintext bytes, the exact standard token length is:

```text
padded = 16 * (floor(n / 16) + 1)
encoded = 4 * ceil((57 + padded) / 3)
```

The authenticated manifest binds each path to its exact token hash, plaintext
length, and plaintext hash. Complete verification checks all three plus Fernet
authentication for every required object. Swapping independently valid tokens,
including equal-length tokens, fails. Re-encrypting identical plaintext changes
the ciphertext hash and fails against the old record. Hashes are binding data
inside the authenticated manifest; they are not a replacement for Fernet.

Verification processes objects one at a time and returns structured metadata
only after every object passes. It retains no aggregate plaintext/ciphertext
payload. Reading content or reusing a token through a validated result rechecks
recorded filesystem state and repeats object validation. Results describe a
read-only observation, not a durable capability or an atomic snapshot. Readers
must recheck immediately before publication; Thread 05 implements the internal
transaction boundary described in the [transaction guide](TRANSACTIONS.md).

Unchanged content must keep its ID and exact validated token. Metadata-only
updates can use that token with a changed `mtime_ns`. Changed content at the
same path keeps its ID and needs a new token. Renames receive new IDs; no rename
inference or content deduplication is performed. Secure random ID generation
retries collisions against the caller's complete reserved set before any write.
The [backup commands](BACKUP.md) implement logical no-op planning and snapshot lifecycle orchestration.

Target path validation can use explicit case/Unicode/Windows/length rules and a
destination prefix without creating or inspecting a destination. Portable
syntax validation alone cannot establish that all names fit a particular
filesystem. Actual target rules are the caller's responsibility. Thread 12
passed the native OS/Python matrix with the limitations documented in [platform validation](PLATFORMS.md).

## Read-only behavior and threat limits

The validator creates no files, destinations, locks, logs, staging, worktrees,
or rollback copies. Safe reads use inspected identities, POSIX anchored
no-follow handles, bounded binary reads, and pre/post-read change checks. The
managed namespace is checked again after all objects. Detected replacement,
addition, deletion, or metadata/content changes abort; unrelated sibling changes
do not. Reads may update filesystem access times. Windows uses inspection and identity rechecks; Thread 12 tested native
read-only, key ACL and junction refusal behavior while retaining mutation limits.
See [platform validation](PLATFORMS.md).

Fernet authenticates before exposing plaintext, uses AES-128-CBC and
HMAC-SHA256, and exposes token timestamps. Whole-file encryption can use
several times one file's size in memory. See the
[cryptography 50.0.2 Fernet reference](https://cryptography.io/en/50.0.2/fernet/).
The per-token cap is not a total-memory, total-vault-size, or execution-time
quota. Untrusted authenticated metadata can still consume resources; allocation
and I/O failures are reported without a partial successful result.

Encryption conceals contents and original names, while observers can learn
object counts, encrypted sizes, token timestamps, and change patterns. It does
not protect an unlocked endpoint, a stolen key, deleted backups, or replay of a
complete older valid snapshot. V1 has no external freshness anchor; an old
valid snapshot passes verification. Anyone holding the key can forge a new
valid manifest and objects. Checks are not an independent security certification.

Keep the key outside both vaults and cloud repositories, with a separate offline
backup. Key loss prevents decryption; manifest loss prevents path recovery.
There is no recovery bypass. A later key change cannot revoke copies or Git
history encrypted under an old key. Remote repository privacy and tracking all
managed files together remain user responsibilities. See
[key custody](CONFIGURATION.md) and [inventory limits](INVENTORY.md).

## Compatibility fixtures

`tests/fixtures/v1/` freezes an encrypted synthetic mirror and a clearly labeled
public test key. The key must never protect real data. The companion README
records known synthetic contents and artifact hashes; tests verify those pinned
bytes before reading them. Tests copy the fixture into temporary locations for
adversarial mutations and never rewrite it or generate expected tokens at test
runtime. Fixtures are repository test material and are excluded from installed
package artifacts.

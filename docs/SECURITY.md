# Security, key custody and limits

Obfuscidian uses standard Fernet authenticated encryption for each file and the
path manifest. Authentication precedes plaintext use; complete validation and
target checks precede restore writes. This is a backup tool with documented
limits, not an independent security certification.

## What encryption protects

File contents, original names, relative paths and plaintext hashes live inside
authenticated encrypted records. The mirror uses opaque names. Anyone holding
the symmetric key can both read and forge valid backups. Keep it outside both
vaults and their Git/cloud repositories, with a separate offline backup.
Key loss prevents decryption; manifest loss prevents path recovery. There is no
reset, password recovery or bypass. See [key selection and permissions](CONFIGURATION.md).

## Observable information and endpoint limits

Observers can learn object counts, encrypted sizes, Fernet token timestamps and
change patterns. Encryption does not protect an unlocked endpoint, a stolen key,
deleted backups or the availability of storage. It does not stop replay of an
older complete valid snapshot: v1 has no external freshness anchor, and that
snapshot passes verification. A later key change cannot revoke copies or Git
history encrypted with the old key. Repository privacy and tracking the entire
managed tree together remain user responsibilities; no remote privacy test is claimed.

## Compatibility and resources

The frozen [v1 format](FORMAT.md) stores `.obfuscidian/manifest.obf` and a flat
`objects/` directory. Unknown versions and unexpected/missing objects fail
validation. Package version and backup format version are separate contracts.
Archival decryption uses no token expiry. Each encrypted file token and manifest
is capped at **50 MiB** (`50 * 1024 * 1024` bytes), including Fernet overhead;
the maximum plaintext file is therefore smaller. Oversized files fail rather
than being silently skipped. The cap is not a total-vault, memory or time quota.
Whole-file Fernet processing can use several times one file's size in memory.
Free-space estimates do not reserve disk space. See [inventory/resource accounting](INVENTORY.md).

## Preservation and recovery

Sources stay read-only during backup; normal reads can update access times.
Links/junctions, unsafe paths, overlaps, special files and target collisions are
refused. Rechecks are best-effort observation, not an atomic source snapshot or
protection against every hostile concurrent writer. Pause editing and sync.
Journaled replacement and tested ordinary failure recovery do not guarantee
universal power-loss, network filesystem or cloud-sync recovery.

Fresh restore retains replaced content as **sensitive plaintext rollback**;
failed staging and Git reconstruction may also retain plaintext. Nothing
automatically prunes successful fresh rollback. Keep uncertain artifacts and
locks until inspected; do not delete based on age. Follow
[recovery and cleanup](TROUBLESHOOTING.md) and [transaction limits](TRANSACTIONS.md).
Merge backups can resurrect deleted/excluded data on restore; fresh snapshots
do not erase earlier copies or Git history. Native Windows vault writes/recovery
and existing-log append still fail closed; see [platform validation](PLATFORMS.md).

## Output privacy

Unattended default output redacts paths. `--verbose` permits terminal names and
handoff locations; only explicit `--log-paths` permits relative names in private
logs. Neither prints keys or file contents. Logs are optional and their parents
must exist privately outside vaults, Git and recovery trees. Verification and
dry runs create no logs or other application files. Read [the CLI contract](CLI.md).

## Stay current with fixes

Use [Updating Obfuscidian](getting-started/updating.md) to install stable updates
in the environment your shell or jobs actually use. Watch repository releases
and read upgrade notes. The advisory PyPI check does not audit vulnerabilities
or guarantee that a version is safe; failed or suppressed checks cannot establish
that you are current. It sends no vault/key data and writes no cache; ordinary
connection metadata is visible to PyPI. Suppression also skips network access.

## Report a concern privately

Use GitHub **Security → Report a vulnerability** if enabled. If unavailable,
contact **jeff@shurt.us** privately with a sanitized summary and agree on a secure
channel. This is the public maintainer address in `pyproject.toml`. Do not send
real keys, credentials or vault data. Do not publish exploit details or sensitive
paths in public issues. No reporting configuration, released-version support
window or response deadline is assumed. The repository
{download}`security policy <../SECURITY.md>` and contributor guidance govern handling.
The policy is available locally with this documentation; no publication is assumed.

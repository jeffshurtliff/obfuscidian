# Immutable synthetic v1 compatibility fixture

This is a public test fixture, never a real backup. `synthetic-fernet-key.txt`
is deliberately public, deterministic test material and must never protect real
data. It is outside the fixture mirror. No test prints it.

The mirror was produced once with direct standard `cryptography` Fernet calls
and independently assembled v1 JSON, rather than the production codec. All
tokens have timestamp zero, proving archival reads impose no TTL. Do not
regenerate these bytes when refactoring the implementation. A format change
needs separate approval and a separately versioned fixture.

`SHA256SUMS.json` pins the exact key and six encrypted token artifacts. Tests
also contain literal pinned checksums so replacing both tokens and this list
cannot silently redefine compatibility. Tests mutate only temporary copies.

Known synthetic contents: `.hidden` contains `SYNTHETIC HIDDEN` plus LF;
`.obsidian/settings.json` contains `{"synthetic": true}` plus CRLF;
`attachments/all-bytes.bin` contains each byte from 0 to 255 in order;
`notes/café-日本語.md` contains `# SYNTHETIC café 日本語` plus CRLF in UTF-8;
`zero.bin` is empty. Directory records are `.obsidian`, `attachments`, `empty`,
and `notes`. Signed nanosecond times are -1 for directories and negative
one-based sorted file indices. Vault/snapshot IDs are 32 `a`/`b` characters,
respectively, and publication time is `1970-01-01T00:00:00Z`.

No plaintext manifest, plaintext hash list, source hierarchy, or test key lives
inside the mirror. The fixture is excluded from wheel/sdist artifacts.

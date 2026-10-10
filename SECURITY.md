# Security policy

Report suspected vulnerabilities in Obfuscidian 1.0.1 and the current source
privately. No fixed support window, independent security certification or
guaranteed recovery is claimed. Include the affected version in your report.

Use the repository's GitHub **Security → Report a vulnerability** action if
private reporting is enabled; its availability is not assumed. If unavailable,
contact the maintainer privately at **jeff@shurt.us**, the public maintainer
address in `pyproject.toml`. Start with a sanitized summary and agree on a secure
channel before sharing sensitive details. No response deadline is promised.

Never send real keys, credentials or vault data. Do not publish exploit payloads,
detailed attack instructions, sensitive environment information or identifying
local paths in issues. Public security issue templates are for sanitized,
non-sensitive hardening tracking only. Coordinate sensitive findings privately;
do not copy private details into public discussion.

For the threat model, key custody, resource limits and recovery boundaries, see
[the security guide](docs/SECURITY.md). Contributor handling is governed by
[CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).

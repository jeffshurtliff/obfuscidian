---
name: Security Report
about: Report a potential security concern in Obfuscidian (public fallback; sanitize details)
title: "[SECURITY] <short, sanitized summary>"
labels: security
assignees: ''

---

This template creates a public issue. Use synthetic examples and placeholder paths; never include
real keys, vault content, credentials, or identifying local paths. For suspected vulnerabilities,
follow the [security reporting
guidance](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md#security-reporting).

## Important: Public Issue Warning

This issue template creates a **public GitHub Issue**.

For real or suspected vulnerabilities, use **GitHub Private Vulnerability Reporting** (Security tab
-> **Report a vulnerability**) if enabled. If unavailable, contact the maintainer privately as
described in the contributor guide; availability is not assumed.

Use this public template only if:
- You are sharing a **sanitized, non-sensitive** security concern / hardening suggestion, and
- The report contains no sensitive vulnerability details, even if private reporting is unavailable

⚠️ Do **not** include secrets, proof-of-concept exploit payloads, private endpoints, real vault
content or identifying local paths, or step-by-step exploit instructions.

---

## Reporter Checklist

- [ ] I understand this issue will be public
- [ ] I have not included secrets or sensitive data
- [ ] I have sanitized logs, examples, and environment details
- [ ] This report is safe to discuss publicly at a high level

If any box cannot be checked, please use a private reporting channel instead.

---

## Security Concern Summary (Sanitized)

Provide a short, high-level description of the concern.

Examples:
- Potential input validation weakness
- Sensitive data may be logged under certain conditions
- Insecure default configuration or behavior

---

## Potential Impact (High Level)

Describe the possible impact without including exploit details.

Examples:
- Encryption-key or plaintext exposure risk
- Injection risk
- Privilege or access control weakness
- Data leakage in logs/errors

---

## Affected Versions / Components (if known)

- Obfuscidian version(s):
- Python version(s):
- Affected module(s) / functionality:
- Environment constraints:

---

## Reproduction Context (High Level Only)

Describe the general conditions under which the issue may occur.

Do **not** include:
- Secrets or tokens
- Full exploit payloads
- Detailed attack instructions
- Identifying local paths or real vault content

```text
High-level reproduction context (sanitized)
```

---

## Evidence / Logs (Redacted, Optional)

If helpful, include **sanitized** log excerpts or error messages.

```text
Paste redacted logs or messages here
```

---

## Suggested Mitigation / Hardening (Optional)

If you have ideas for a fix or mitigation, describe them at a high level.

Examples:
- Input sanitization/validation
- Redaction of sensitive fields in logs
- Safer defaults
- Additional permission checks

---

## Coordination Preference (Optional)

- [ ] I can provide additional details privately if a maintainer requests them
- [ ] I am willing to help validate a fix
- [ ] I prefer not to be contacted beyond issue updates

---

## Additional Context

Add any other context that may help triage this report safely.

---

## Acknowledgements

Thank you for taking the time to report security concerns responsibly.
Sanitized reports and private disclosures both help improve Obfuscidian safely.

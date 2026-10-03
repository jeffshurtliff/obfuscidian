---
name: Bug Report
about: Report a bug or unexpected behavior in Obfuscidian
title: "[BUG] <short, descriptive summary>"
labels: bug
assignees: ''

---

This template creates a public issue. Use synthetic examples and placeholder paths; never include
real keys, vault content, credentials, or identifying local paths. For suspected vulnerabilities,
follow the [security reporting
guidance](https://github.com/jeffshurtliff/obfuscidian/blob/main/CONTRIBUTING.md#security-reporting).

## Bug Description

Provide a clear and concise description of the bug.
What happened, and what did you expect to happen instead?

---

## Steps to Reproduce

Please provide **exact steps** so the issue can be reproduced reliably.

1. …
2. …
3. …

If applicable, include:
- Command and mode used
- Relevant options with placeholder paths
- Key selection method (path or alias; never include key contents)

---

## Expected Behavior

Describe what you expected to happen.

---

## Actual Behavior

Describe what actually happened, including any error messages or unexpected results.

---

## Code Sample (if applicable)

Please include a **minimal, reproducible example**.

```python
# Example code that triggers the issue
```

⚠️ **Do not include secrets** (encryption keys, credentials, vault content, identifying paths, etc.).

---

## Environment Details

Please complete the following information:

- **Obfuscidian version**:
- **Python version** (e.g. 3.12.7):
- **Operating system**:
- **Installation method**:
  - [ ] pip
  - [ ] Poetry
  - [ ] Other (please specify)
- **Virtual environment**:
  - [ ] venv
  - [ ] virtualenv
  - [ ] Conda
  - [ ] Poetry
  - [ ] Other (please specify)
  - [ ] None

---

## Traceback / Logs

If applicable, include the **sanitized traceback or relevant logs** below.

```text
Paste redacted traceback or logs here
```

---

## Security Considerations

- [ ] I have verified this issue does **not** expose credentials or sensitive data
- [ ] This issue is **not** a security vulnerability (if it is, please do **not** file a public issue)

If this may be security-related, please report it responsibly instead of filing a public issue.

---

## Additional Context

Add any other context that may help diagnose the problem:
- Workarounds you’ve tried
- Related issues or PRs
- Filesystem or Git setup (at a high level; sanitized)

---

## Acknowledgements

Thanks for taking the time to report this issue — detailed reports help make Obfuscidian better for everyone.

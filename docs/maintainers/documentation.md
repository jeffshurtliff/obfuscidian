# Maintain and validate documentation

Sphinx renders reST navigation and MyST Markdown guides with the PyData theme.
The organization follows the public SalesPyForce/PyDPlus pattern of getting
started, guides, reference and maintainer material; domain-specific extensions
and API documentation are not copied. The CLI remains the supported interface.
`docs/conf.py` reads the version from `pyproject.toml` without importing application
code or stale installed package metadata. No network inventory is required to build.

## Build locally

From the repository root:

```sh
poetry install --with dev,docs
poetry run sphinx-build -W --keep-going -E -a -b html docs docs/_build/html
poetry run python .github/scripts/check_docs.py docs/_build/html
poetry run pytest -q tests/integration/test_docs_tutorial.py
```

The strict fresh build treats warnings as failures, with nitpicky references
enabled. The local checker validates rendered links/assets and fragment targets;
it does not request external sites. Optional external validation is:

```sh
poetry run sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
```

Report unreachable external targets separately; do not suppress warnings merely
to claim a passing check. Open `docs/_build/html/index.html` locally or serve only
on loopback with `python -m http.server 8765 --bind 127.0.0.1 --directory docs/_build/html`.
No publishing or hosting configuration is introduced by this build.

## Rehearsal and rendered review

The integration test extracts and executes the tutorial's complete bash block in
a disposable temporary directory with synthetic data. It uses the installed CLI
and checks source preservation and restored bytes/structure independently.
Windows skips this mutation rehearsal explicitly; native write support remains
absent. Read-only Windows examples are documented separately.

Inspect the landing, configuration/key, security and restore pages in dark and
light modes, plus a narrow viewport. Check logo proportions, readable code,
tables, warnings, sidebar/search, keyboard focus, skip link and theme switcher.
Run an accessibility audit where available and report its limits; automated
results do not establish complete assistive-technology compliance.

## Branding and accessibility

Dark is the first-visit default, while PyData remembers a reader's selected mode.
The supplied horizontal PNG remains the source asset. A proportional 848 × 297
PNG provides a smaller web logo without changing the artwork/transparency.
Its dark backing keeps the luminous wordmark legible in both themes.
`docs/_static/custom.css` applies restrained violet/cyan accents to readable
surfaces while retaining semantic warning/error colors and accessible syntax
highlighting. Content links stay underlined; keyboard focus has a visible outline.
Verify at least WCAG AA text contrast (4.5:1 normal, 3:1 large) after palette changes.
See the [PyData theme documentation](https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/light-dark.html)
for mode configuration and [branding guidance](https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/branding.html).

Keep examples and evidence public-safe. Use supported commands and fake data;
mark future behavior as planned. Thread 14, external publishing, release automation
and tool-specific companion files require separate maintainer requests.

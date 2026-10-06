# -*- coding: utf-8 -*-
"""
:Module:            scripts.check_docs
:Synopsis:          Checks local links, assets and anchors in rendered documentation
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     06 Oct 2026
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PageParser(HTMLParser):
    """Collect local reference attributes and target identifiers from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.identifiers: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record identifiers and references on a rendered element."""
        attributes = dict(attrs)
        if identifier := attributes.get('id'):
            self.identifiers.add(identifier)
        if tag == 'a' and (name := attributes.get('name')):
            self.identifiers.add(name)
        for attribute in ('href', 'src'):
            if reference := attributes.get(attribute):
                self.references.append(reference)


def check_links(root: Path) -> list[str]:
    """Return broken local references within a rendered HTML tree.

    :param root: Existing Sphinx HTML output directory.
    :returns: Relative diagnostics; external URLs are not requested.
    """
    root = root.resolve()
    pages: dict[Path, PageParser] = {}
    for path in root.rglob('*.html'):
        # Theme assets include unrendered Jinja templates, not document pages.
        if '_static' in path.relative_to(root).parts:
            continue
        parser = PageParser()
        parser.feed(path.read_text(encoding='utf-8'))
        pages[path.resolve()] = parser
    failures: list[str] = []
    if not pages:
        return ['No rendered HTML pages found.']
    for page, parser in pages.items():
        for reference in parser.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            target = (root / path.lstrip('/') if path.startswith('/') else page.parent / path).resolve() if path else page
            if target.is_dir():
                target /= 'index.html'
            if not target.is_relative_to(root) or not target.is_file():
                failures.append(f'{page.relative_to(root)}: missing local target {reference}')
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].identifiers:
                failures.append(f'{page.relative_to(root)}: missing fragment {reference}')
    print(f'Checked local references across {len(pages)} rendered HTML pages; external URLs were not requested.')
    return failures


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python .github/scripts/check_docs.py HTML_DIRECTORY')
    errors = check_links(Path(sys.argv[1]).resolve())
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(bool(errors))

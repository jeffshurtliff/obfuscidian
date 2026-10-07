# -*- coding: utf-8 -*-
"""
:Module:            docs.conf
:Synopsis:          Configures the local Obfuscidian documentation build
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     06 Oct 2026
"""

import tomllib
from pathlib import Path

with (Path(__file__).resolve().parents[1] / 'pyproject.toml').open('rb') as metadata:
    package = tomllib.load(metadata)['project']

project = 'Obfuscidian'
author = 'Jeff Shurtliff'
copyright = '2026, Jeff Shurtliff'
release = package['version']
version = release
extensions = ['myst_parser', 'sphinx_favicon']
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
root_doc = 'index'
exclude_patterns = ['_build', '.DS_Store', 'Thumbs.db', 'desktop.ini']
nitpicky = True
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'fieldlist',
    'replacements',
    'strikethrough',
]
myst_heading_anchors = 6
myst_links_external_new_tab = True
html_theme = 'pydata_sphinx_theme'
html_title = f'{project} {release} Documentation'
html_static_path = ['_static']
html_css_files = ['custom.css']
html_logo = '_static/obfuscidian-logo-horizontal-web.png'
html_context = {'default_mode': 'dark'}
html_theme_options = {
    'logo': {'alt_text': 'Obfuscidian Documentation — Home'},
    'navbar_end': ['theme-switcher', 'navbar-icon-links'],
    'icon_links': [{'name': 'GitHub', 'url': 'https://github.com/jeffshurtliff/obfuscidian', 'icon': 'fa-brands fa-github'}],
    'show_prev_next': True,
    'navigation_depth': 2,
    'show_toc_level': 2,
}
html_show_sourcelink = True
html_copy_source = True
pygments_style = 'a11y-high-contrast-light'
pygments_dark_style = 'a11y-high-contrast-dark'
linkcheck_retries = 2
linkcheck_timeout = 15
favicons = [
    {'rel': 'icon', 'sizes': '16x16', 'href': 'obfuscidian-favicon-16x16.png'},
    {'rel': 'icon', 'sizes': '32x32', 'href': 'obfuscidian-favicon-32x32.png'},
    {'rel': 'apple-touch-icon', 'sizes': '180x180', 'href': 'obfuscidian-apple-touch-icon-180x180.png'},
]
htmlhelp_basename = 'obfuscidian'

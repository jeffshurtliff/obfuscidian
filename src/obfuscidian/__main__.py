# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.__main__
:Synopsis:          The ``__main__`` module for obfuscidian
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

from .cli import cli

if __name__ == '__main__':
    cli(prog_name='obfuscidian')

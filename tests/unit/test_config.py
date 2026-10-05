# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_config
:Synopsis:          Verify precedence, explicit invalid values, and path resolution
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff
:Modified Date:     05 Oct 2026
"""

from __future__ import annotations

from pathlib import Path

import pytest

from obfuscidian import config
from obfuscidian import constants as const
from obfuscidian.errors import _ConfigurationError


@pytest.mark.parametrize(
    ('options', 'environment', 'expected'),
    [
        ({'key': 'cli.key'}, {const.ENV_KEY_PATH: 'env.key', const.ENV_KEY_ALIAS: 'bad/alias', const.ENV_KEY_DIR: ''}, 'cli.key'),
        (
            {'alias': 'cli'},
            {const.ENV_KEY_PATH: '', const.ENV_KEY_ALIAS: 'bad/alias', const.ENV_KEY_DIR: 'env'},
            'env/obfuscidian-cli.key',
        ),
        ({'alias': 'cli', 'keydir': 'cli'}, {const.ENV_KEY_DIR: 'env'}, 'cli/obfuscidian-cli.key'),
        ({}, {const.ENV_KEY_PATH: 'env.key', const.ENV_KEY_ALIAS: 'bad/alias', const.ENV_KEY_DIR: ''}, 'env.key'),
        ({'keydir': 'cli'}, {const.ENV_KEY_ALIAS: 'env', const.ENV_KEY_DIR: 'env'}, 'cli/obfuscidian-env.key'),
        ({}, {const.ENV_KEY_ALIAS: 'env', const.ENV_KEY_DIR: 'env'}, 'env/obfuscidian-env.key'),
    ],
)
def test_key_precedence(options: dict, environment: dict, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Select exactly one source; ignored invalid selectors cannot affect it."""
    monkeypatch.chdir(tmp_path)
    assert config._resolve_key_path(**options, environ=environment) == tmp_path / expected


@pytest.mark.parametrize(
    ('options', 'environment'),
    [
        ({'key': 'a', 'alias': 'a'}, {}),
        ({'key': 'a', 'keydir': 'a'}, {}),
        ({'key': 'a', 'alias': 'a', 'keydir': 'a'}, {}),
        ({'keydir': 'a'}, {const.ENV_KEY_PATH: 'b', const.ENV_KEY_ALIAS: 'b'}),
        ({'key': ''}, {const.ENV_KEY_PATH: 'valid'}),
        ({'alias': ''}, {const.ENV_KEY_ALIAS: 'valid'}),
        ({'alias': 'bad/alias'}, {const.ENV_KEY_ALIAS: 'valid'}),
        ({}, {const.ENV_KEY_PATH: '', const.ENV_KEY_ALIAS: 'valid'}),
        ({}, {const.ENV_KEY_ALIAS: ''}),
        ({'alias': 'valid', 'keydir': ''}, {const.ENV_KEY_DIR: 'valid'}),
        ({'alias': 'valid'}, {const.ENV_KEY_DIR: ''}),
    ],
)
def test_invalid_key_selection_never_prompts_or_falls_back(options: dict, environment: dict) -> None:
    """Refuse explicit bad values without asking for a different selector."""

    def forbidden_prompt() -> str:
        pytest.fail('Explicit invalid configuration must not prompt.')

    with pytest.raises(_ConfigurationError):
        config._resolve_key_path(**options, environ=environment, alias_prompt=forbidden_prompt)


@pytest.mark.parametrize('alias', ['A-z-09', '-', 'a' * 64])
def test_valid_aliases(alias: str) -> None:
    """Allow only the documented ASCII alphabet, up to the boundary."""
    assert config._validate_alias(alias) == alias


@pytest.mark.parametrize('alias', ['', 'a' * 65, 'a_b', '../a', 'a.b', 'a/b', 'a\\b', 'a b', 'é', '０', 'a\n', '\x1b'])
def test_invalid_aliases(alias: str) -> None:
    """Reject traversal, whitespace, Unicode lookalikes, and control characters."""
    with pytest.raises(_ConfigurationError):
        config._validate_alias(alias)


def test_absent_loading_selector_requires_interactive_prompt(tmp_path: Path) -> None:
    """Allow a directory-only setting with a prompt, but never without it."""
    with pytest.raises(_ConfigurationError):
        config._resolve_key_path(keydir=str(tmp_path), environ={})
    assert config._resolve_key_path(keydir=str(tmp_path), environ={}, alias_prompt=lambda: 'prompt') == (
        tmp_path / 'obfuscidian-prompt.key'
    )
    with pytest.raises(_ConfigurationError):
        config._resolve_key_path(keydir=str(tmp_path), environ={}, alias_prompt=lambda: '')


def test_alias_home_and_literal_shell_variables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Expand home/cwd while leaving shell syntax literal and link checks possible."""
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('USERPROFILE', str(tmp_path))
    monkeypatch.setenv('SYNTHETIC_DIRECTORY', 'must-not-expand')
    monkeypatch.chdir(tmp_path)
    assert config._resolve_key_path(alias='home', environ={}) == tmp_path / 'obfuscidian-home.key'
    assert config._expand_path('~/keys with spaces', 'directory') == tmp_path / 'keys with spaces'
    assert config._expand_path('$SYNTHETIC_DIRECTORY/%SYNTHETIC_DIRECTORY%', 'directory') == (
        tmp_path / '$SYNTHETIC_DIRECTORY/%SYNTHETIC_DIRECTORY%'
    )
    assert config._expand_path('one/../two', 'directory') == tmp_path / 'one/../two'
    with pytest.raises(_ConfigurationError):
        config._expand_path('bad\0path', 'directory')


@pytest.mark.parametrize(
    ('options', 'environment', 'expected'),
    [
        (
            {'alias': 'cli', 'directory': 'cli'},
            {const.ENV_KEY_ALIAS: '', const.ENV_KEY_DIR: '', const.ENV_KEY_PATH: 'ignored.key'},
            'cli/obfuscidian-cli.key',
        ),
        ({'alias': 'cli'}, {const.ENV_KEY_ALIAS: 'env', const.ENV_KEY_DIR: 'env'}, 'env/obfuscidian-cli.key'),
        ({'directory': 'cli'}, {const.ENV_KEY_ALIAS: 'env', const.ENV_KEY_DIR: 'env'}, 'cli/obfuscidian-env.key'),
        (
            {},
            {const.ENV_KEY_ALIAS: 'env', const.ENV_KEY_DIR: 'env', const.ENV_KEY_PATH: 'ignored.key'},
            'env/obfuscidian-env.key',
        ),
    ],
)
def test_generation_precedence(
    options: dict, environment: dict, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ignore KEY_PATH for output, preserving alias/directory precedence."""
    monkeypatch.chdir(tmp_path)
    assert config._resolve_generation_path(**options, environ=environment) == tmp_path / expected


@pytest.mark.parametrize('environment', [{}, {const.ENV_KEY_PATH: 'ignored.key'}])
def test_key_path_cannot_supply_generation_alias(environment: dict) -> None:
    """Unattended generation always requires an explicit alias."""
    with pytest.raises(_ConfigurationError):
        config._resolve_generation_path(environ=environment)


@pytest.mark.parametrize('options', [{'alias': ''}, {'alias': 'valid', 'directory': ''}])
def test_explicit_empty_generation_values_do_not_fall_back(options: dict) -> None:
    """Do not replace explicit invalid values with valid environment values."""
    with pytest.raises(_ConfigurationError):
        config._resolve_generation_path(**options, environ={const.ENV_KEY_ALIAS: 'valid', const.ENV_KEY_DIR: 'valid'})


def test_vault_cli_paths_override_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve paths independently without validating or creating vaults."""
    monkeypatch.chdir(tmp_path)
    environment = {const.ENV_ORIGIN: 'env-origin', const.ENV_MIRROR: 'env-mirror'}
    assert config._resolve_vault_paths(origin='cli-origin', environ=environment) == (
        tmp_path / 'cli-origin',
        tmp_path / 'env-mirror',
    )
    assert config._resolve_vault_paths(mirror='cli-mirror', environ=environment) == (
        tmp_path / 'env-origin',
        tmp_path / 'cli-mirror',
    )
    assert config._resolve_vault_paths(environ={}) == (None, None)
    for option in ('origin', 'mirror'):
        with pytest.raises(_ConfigurationError):
            config._resolve_vault_paths(**{option: ''}, environ=environment)
    assert list(tmp_path.iterdir()) == []

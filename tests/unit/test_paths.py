# -*- coding: utf-8 -*-
"""
:Module:            tests.unit.test_paths
:Synopsis:          Read-only vault and target-path safety tests
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from obfuscidian import paths
from obfuscidian.errors import _ConfigurationError, _OperationalError


@pytest.fixture
def locations(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create separate synthetic origin, mirror, and external key locations."""
    root = tmp_path.resolve()
    origin, mirror, key = root / 'source', root / 'mirror', root / 'synthetic.key'
    origin.mkdir()
    key.write_bytes(b'SYNTHETIC PATH PREFLIGHT ONLY; NOT A REAL KEY')
    return origin, mirror, key


def test_new_mirror_is_not_created(locations: tuple[Path, Path, Path]) -> None:
    """Allow only the final component to be missing without mutation."""
    origin, mirror, key = locations
    state = paths._preflight_vault_paths(origin, mirror, key)
    state._recheck()
    assert not mirror.exists()
    assert str(origin) not in repr(state)
    with pytest.raises(_ConfigurationError, match='already exist'):
        paths._preflight_vault_paths(origin, mirror / 'missing-parent' / 'destination', key)
    with pytest.raises(_ConfigurationError):
        paths._preflight_vault_paths(origin / 'absent', mirror, key)


@pytest.mark.parametrize('scenario', ['same', 'child', 'parent', 'root-origin', 'root-mirror', 'key-origin', 'key-mirror'])
def test_overlap_roots_and_key_custody(locations: tuple[Path, Path, Path], scenario: str) -> None:
    """Refuse overlap in both directions, roots, and keys inside either vault."""
    origin, mirror, key = locations
    mirror.mkdir()
    if scenario == 'same':
        mirror = origin
    elif scenario == 'child':
        mirror = origin / 'new-mirror'
    elif scenario == 'parent':
        mirror = origin.parent
    elif scenario == 'root-origin':
        origin = Path(origin.anchor)
    elif scenario == 'root-mirror':
        mirror = Path(mirror.anchor)
    elif scenario == 'key-origin':
        key = origin / 'obfuscidian-synthetic.key'
        key.write_bytes(b'SYNTHETIC')
    elif scenario == 'key-mirror':
        key = mirror / 'obfuscidian-synthetic.key'
        key.write_bytes(b'SYNTHETIC')
    with pytest.raises(_ConfigurationError):
        paths._preflight_vault_paths(origin, mirror, key)


def test_location_replacement_and_appearance(locations: tuple[Path, Path, Path]) -> None:
    """Rechecks refuse newly appeared targets and replaced ancestors."""
    origin, mirror, key = locations
    state = paths._preflight_vault_paths(origin, mirror, key)
    mirror.mkdir()
    with pytest.raises(_OperationalError, match='appeared'):
        state._recheck()
    mirror.rmdir()
    origin.rename(origin.with_name('saved-source'))
    origin.mkdir()
    with pytest.raises(_OperationalError, match='identity'):
        state._recheck()


@pytest.mark.parametrize(
    'relative', ['/absolute', '../outside', 'a/../b', './a', 'a//b', 'a/', '', 'C:/x', 'C:x', 'a\\b', 'a\0b']
)
def test_relative_path_safety(relative: str) -> None:
    """Reject traversal and platform-ambiguous serialized names."""
    with pytest.raises(_ConfigurationError):
        paths._validate_relative_path(relative)


@pytest.mark.parametrize(
    'relative', ['CON', 'con.txt', 'aux', 'NUL.bin', 'COM1.md', 'LPT9', 'COM¹', 'a.', 'a ', 'a:b', 'a\nb', 'x/y?']
)
def test_windows_names(relative: str) -> None:
    """Reject unrepresentable Windows components without renaming them."""
    with pytest.raises(_ConfigurationError):
        paths._validate_relative_path(relative, windows=True)
    if relative != 'a:b':
        # These names remain valid POSIX data when the manifest syntax permits them.
        assert paths._validate_relative_path(relative)


def test_target_collisions_and_limits(tmp_path: Path) -> None:
    """Check explicit filesystem comparison rules, ancestors, and full lengths."""
    exact = paths._TargetRules(case_sensitive=True)
    paths._validate_target_paths(['a', 'A', 'café', 'cafe\u0301', 'control\nname'], exact)
    for names in (['a', 'A'], ['a/x', 'A/y']):
        with pytest.raises(_ConfigurationError, match='collide'):
            paths._validate_target_paths(names, paths._TargetRules(case_sensitive=False))
    with pytest.raises(_ConfigurationError, match='Unicode'):
        paths._validate_target_paths(['café', 'cafe\u0301'], paths._TargetRules(case_sensitive=True, normalization='NFD'))
    with pytest.raises(_ConfigurationError, match='duplicate'):
        paths._validate_target_paths(['a', 'a'], exact)
    paths._validate_target_paths(['é'], paths._TargetRules(case_sensitive=True, component_limit=2))
    with pytest.raises(_ConfigurationError, match='component'):
        paths._validate_target_paths(['éa'], paths._TargetRules(case_sensitive=True, component_limit=2))
    target = tmp_path.resolve() / 'new-target'
    limit = len(str(target / 'abc').encode('utf-8'))
    paths._validate_target_paths(['abc'], paths._TargetRules(case_sensitive=True, path_limit=limit), destination=target)
    with pytest.raises(_ConfigurationError, match='path exceeds'):
        paths._validate_target_paths(['abcd'], paths._TargetRules(case_sensitive=True, path_limit=limit), destination=target)
    # An astral character is two UTF-16 units on Windows, four bytes on POSIX.
    paths._validate_target_paths(['😀'], paths._TargetRules(case_sensitive=False, windows=True, component_limit=2))
    with pytest.raises(_ConfigurationError, match='component'):
        paths._validate_target_paths(['😀x'], paths._TargetRules(case_sensitive=False, windows=True, component_limit=2))
    assert not target.exists()


@pytest.mark.parametrize(
    'entry', ['README.txt', '.obfuscidian/unmanaged', '.obfuscidian/objects/bad.obf', '.obfuscidian/manifest.obf/child']
)
def test_unmanaged_mirror(locations: tuple[Path, Path, Path], entry: str) -> None:
    """Refuse unknown root/managed/object names and invalid entry types."""
    origin, mirror, key = locations
    path = mirror / entry
    path.parent.mkdir(parents=True)
    path.write_bytes(b'SYNTHETIC UNMANAGED CONTENT')
    with pytest.raises(_ConfigurationError):
        paths._preflight_vault_paths(origin, mirror, key)
    assert path.read_bytes() == b'SYNTHETIC UNMANAGED CONTENT'


@pytest.mark.parametrize('git_directory', [True, False])
def test_mirror_namespace_and_recheck(locations: tuple[Path, Path, Path], git_directory: bool) -> None:
    """Preserve root Git controls and inspect only supported managed names/types."""
    origin, mirror, key = locations
    objects = mirror / '.obfuscidian' / 'objects'
    objects.mkdir(parents=True)
    (mirror / '.gitignore').write_bytes(b'SYNTHETIC CONTROL')
    if git_directory:
        (mirror / '.git').mkdir()
        (mirror / '.git' / 'untouched').write_bytes(b'SYNTHETIC GIT METADATA')
    else:
        (mirror / '.git').write_bytes(b'gitdir: ../synthetic-control\n')
    manifest = mirror / '.obfuscidian' / 'manifest.obf'
    manifest.write_bytes(b'SYNTHETIC NAMESPACE FIXTURE; NOT AN AUTHENTICATED MANIFEST')
    (objects / ('a' * 32 + '.obf')).write_bytes(b'SYNTHETIC OBJECT')
    state = paths._preflight_vault_paths(origin, mirror, key)
    state._recheck()
    manifest.write_bytes(b'changed synthetic manifest')
    with pytest.raises(_OperationalError, match='changed'):
        state._recheck()


def test_parent_links_and_mirror_links(locations: tuple[Path, Path, Path]) -> None:
    """Refuse linked ancestors, final locations, keys, and managed entries."""
    origin, mirror, key = locations
    alias = origin.with_name('linked-source')
    try:
        alias.symlink_to(origin, target_is_directory=True)
    except OSError:
        pytest.skip('The host cannot create directory symlink fixtures.')
    for source, target, selected_key in ((alias, mirror, key), (origin, alias / 'nested', key), (origin, mirror, alias / 'key')):
        with pytest.raises(_ConfigurationError):
            paths._preflight_vault_paths(source, target, selected_key)
    mirror.mkdir()
    (mirror / '.git').symlink_to(origin, target_is_directory=True)
    with pytest.raises(_ConfigurationError, match='links'):
        paths._preflight_vault_paths(origin, mirror, key)


@pytest.mark.skipif(os.name != 'nt', reason='Native Windows junction creation requires cmd.exe.')
def test_native_junction(locations: tuple[Path, Path, Path]) -> None:
    """Reject an actual Windows junction without descending into its target."""
    origin, mirror, key = locations
    junction = origin.with_name('synthetic-junction')
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(origin)], capture_output=True, check=False)
    if result.returncode:
        pytest.skip('This Windows host cannot create a junction fixture.')
    try:
        with pytest.raises(_ConfigurationError, match='junctions'):
            paths._preflight_vault_paths(junction, mirror, key)
    finally:
        junction.rmdir()


def test_selected_key_alias_in_mirror(locations: tuple[Path, Path, Path]) -> None:
    """Keep an externally named selected key out of allowed mirror control files."""
    origin, mirror, key = locations
    mirror.mkdir()
    try:
        (mirror / '.gitignore').hardlink_to(key)
    except OSError:
        pytest.skip('The host cannot create hard-link fixtures.')
    with pytest.raises(_ConfigurationError, match='key'):
        paths._preflight_vault_paths(origin, mirror, key)


def test_case_alias_overlap(locations: tuple[Path, Path, Path]) -> None:
    """Detect overlap using identity on hosts where case aliases refer to one path."""
    origin, mirror, key = locations
    alias = origin.with_name(origin.name.upper())
    if not alias.exists():
        # Exact-case hosts can exercise the identity overlap through an existing parent.
        with pytest.raises(_ConfigurationError, match='overlap'):
            paths._preflight_vault_paths(origin, origin.parent, key)
        return
    with pytest.raises(_ConfigurationError, match='identity'):
        paths._preflight_vault_paths(origin, alias / 'new-mirror', key)


def test_invalid_target_rules_and_source_locations(locations: tuple[Path, Path, Path]) -> None:
    """Do not silently ignore invalid policies, missing prefixes, or traversal."""
    origin, mirror, key = locations
    for rules in (
        paths._TargetRules(case_sensitive=True, normalization='UNKNOWN'),
        paths._TargetRules(case_sensitive=True, component_limit=0),
        paths._TargetRules(case_sensitive=True, path_limit=True),
        paths._TargetRules(case_sensitive=True, path_limit=10),
    ):
        with pytest.raises(_ConfigurationError):
            paths._validate_target_paths(['safe'], rules)
    for source in (Path('relative'), origin / '..' / origin.name):
        with pytest.raises(_ConfigurationError, match='absolute paths'):
            paths._preflight_vault_paths(source, mirror, key)
    with pytest.raises(_ConfigurationError, match='UTF-8'):
        paths._validate_relative_path('synthetic-\udcff')

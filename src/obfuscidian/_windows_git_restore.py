# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian._windows_git_restore
:Synopsis:          Gated private Windows Git reconstruction and conservative manual-review lifecycle
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6.1 Sol)
:Modified Date:     13 Oct 2026
"""

from __future__ import annotations

import hashlib
import os
import secrets
from contextlib import ExitStack
from pathlib import Path

from obfuscidian import _windows_files as files
from obfuscidian import _windows_transactions as windows
from obfuscidian import constants as const
from obfuscidian import git_restore as git
from obfuscidian import manifest, restore, verification
from obfuscidian import transactions as tx
from obfuscidian._windows_native import _fail, _Guard, _Handle, _private_acl, _sid_bytes
from obfuscidian.errors import _ConfigurationError, _OperationalError


def _boundary(label: str) -> None:
    """Expose private synthetic fault/termination selection, never a CLI bypass."""


def _git_acl(security: dict, owner: bytes, *, directory: bool) -> None:
    """Validate exact owner-only Git inheritance separately from transaction controls.

    A protected explicit root anchors each inspected tree. Descendants may use
    exactly one inherited effective full-owner ACE, with OI|CI on directories.
    No foreign owner/grant, inherit-only, deny, extra ACE or unprotected explicit
    policy is accepted. This does not change the production private validator.
    """
    if security['owner'] != _sid_bytes(owner).hex():
        raise _fail('Unexpected Windows Git owner refused.')
    data = bytes.fromhex(security['acl'])
    if security['protected']:
        _private_acl(data, owner, directory=directory)
        return
    if not 16 <= len(data) <= const.WINDOWS_SECURITY_BYTES:
        raise _fail('Missing or unbounded Windows Git DACL.')
    # Strip only INHERITED_ACE for the isolated Git policy, then require the
    # existing exact one-grant parser. Explicit/unprotected grants stay refused.
    if data[9] != (19 if directory else 16):
        raise _fail('Unsupported Windows Git inheritance refused.')
    explicit = bytearray(data)
    explicit[9] &= ~16
    _private_acl(bytes(explicit), owner, directory=directory)


def _git_record(handle: _Handle) -> dict:
    """Capture a bounded Git-created entry through its pinned native handle."""
    before = handle._identity()
    if before.attributes & ~const.WINDOWS_SUPPORTED_ATTRIBUTES:
        raise _fail('Unsupported Windows Git attributes refused.')
    files._streams(handle)
    security = files._security(handle, baseline=False)
    _git_acl(security, handle.api._owner()[0], directory=before.directory)
    data = None if before.directory else handle._read(const.MAX_ENCRYPTED_BYTES)
    after = handle._recheck(before, metadata=False)
    if (before.size, before.created, before.written, before.changed, before.attributes) != (
        after.size,
        after.created,
        after.written,
        after.changed,
        after.attributes,
    ):
        raise _fail('Windows Git entry changed during observation.')
    if files._security(handle, baseline=False) != security:
        raise _fail('Windows Git security changed during observation.')
    return {
        'id': files._id(handle),
        'size': 0 if before.directory else before.size,
        'digest': None if data is None else hashlib.sha256(data).hexdigest(),
        'created': before.created,
        'written': before.written,
        'attributes': before.attributes,
        'security': security,
    }


def _git_tree(root: Path, *, excluded: set[str] = frozenset()) -> dict:
    """Audit every Git descendant beneath an explicit protected owner-only root."""
    with files._entry(root.parent, root.name, True, private=True) as handle:
        result = {'': _git_record(handle)}

    def visit(parent: Path, prefix: str, depth: int) -> None:
        if depth > const.WINDOWS_TRANSACTION_DEPTH:
            raise _fail('Windows Git namespace nesting exceeds its bound.')
        names = files._names(parent)
        for name in names:
            if not prefix and name in excluded:
                continue
            path, relative = parent / name, prefix + name
            with files._entry(parent, name, path.is_dir()) as handle:
                result[relative] = _git_record(handle)
                if result[relative]['id'][2]:
                    visit(path, relative + '/', depth + 1)
            if len(result) > const.WINDOWS_TRANSACTION_ENTRIES:
                raise _fail('Windows Git namespace exceeds its bound.')
        if files._names(parent) != names:
            raise _fail('Windows Git namespace changed during observation.')

    visit(root, '', 0)
    return result


def _administration(plan: git._MergePlan) -> dict:
    """Require privacy for all shared Git control parents before Git may write."""
    return {root: _git_tree(root) for root in {plan.common, plan.gitdir}}


def _plan_merge(origin: Path, mirror: Path, key: Path, **options) -> git._MergePlan:
    """Privately plan Windows bytes with executable modes retained in Git's index.

    Supported CLI planning keeps its current behavior. This Windows-only test
    entry point does not dispatch writes or relax namespace/authentication checks.
    """
    if os.name != 'nt':
        raise _ConfigurationError('Private native Windows Git planning requires Windows.')
    return git._plan_merge(origin, mirror, key, _check_file_modes=False, **options)


def _timestamp(path: Path, mtime_ns: int, unsupported: set[str], relative: str) -> None:
    """Preserve native supported times; report precision differences without names."""
    with files._entry(path.parent, path.name, path.is_dir(), private=True, writable=True) as handle:
        handle._set_time(mtime_ns)
        if (handle._identity().written - const.WINDOWS_FILETIME_EPOCH) * 100 != mtime_ns:
            unsupported.add(relative)


def _stage_overlay(plan: git._MergePlan, workspace: Path, unsupported: set[str]) -> tuple[Path, dict]:
    """Authenticate and reconstruct the additive union before Git side effects."""
    restored, overlay = workspace / 'backup', workspace / 'overlay'
    files._mkdir(workspace, restored.name)
    files._mkdir(workspace, overlay.name)
    restore._build_restore(
        plan.reconstruction, restored, unsupported, _writer=files._write, _directory=files._mkdir, _time=_timestamp
    )
    reconstructed = files._capture(restored, private=True)
    restore._verify_stage(plan.reconstruction, restored, unsupported)
    if files._capture(restored, private=True) != reconstructed:
        raise _fail('Windows reconstruction changed during validation.')
    incoming = {r.path: r for r in plan.reconstruction.files}
    for relative in sorted(
        set(plan.base_directories) | {r.path for r in plan.reconstruction.directories}, key=lambda n: (n.count('/'), n)
    ):
        path = overlay / relative
        files._mkdir(path.parent, path.name)
    expected = {}
    for entry in plan.base_files:
        if entry.path not in incoming:
            data = git._blob(plan, entry)
            path = overlay / entry.path
            files._write(path.parent, path.name, data)
            expected[entry.path] = (len(data), hashlib.sha256(data).hexdigest())
    for record in plan.reconstruction.files:
        data = manifest._read_validated_file(plan.reconstruction.snapshot, record, plan.reconstruction.fernet)
        path = overlay / record.path
        files._write(path.parent, path.name, data)
        _timestamp(path, record.mtime_ns, unsupported, record.path)
        expected[record.path] = (record.size, record.plaintext_sha256)
    for record in sorted(plan.reconstruction.directories, key=lambda r: (-r.path.count('/'), r.path)):
        _timestamp(overlay / record.path, record.mtime_ns, unsupported, record.path)
    captured = files._capture(overlay, private=True)
    namespace = set(expected) | set(plan.base_directories) | {r.path for r in plan.reconstruction.directories}
    if set(captured) != namespace or any((captured[n]['size'], captured[n]['digest']) != value for n, value in expected.items()):
        raise _fail('Windows additive union differs from its authenticated proposal.')
    git._recheck_origin(plan)
    return overlay, captured


def _copy_overlay(source: Path, stage: Path, captured: dict, *, exclude: set[str] = frozenset()) -> None:
    """Create independently private copies with exact supported bytes/metadata."""
    if files._capture(source, private=True) != captured:
        raise _fail('Windows additive staging changed; retain artifacts.')
    known = {n: r for n, r in captured.items() if n not in exclude}
    for name in sorted(known, key=lambda n: (n.count('/'), n)):
        files._copy(source / name, stage / name, captured[name])
    # Directory child creation updates times; finalize them after all copies.
    for name in sorted(known, key=lambda n: (-n.count('/'), n)):
        if captured[name]['id'][2]:
            with files._entry((stage / name).parent, (stage / name).name, True, private=True, writable=True) as handle:
                files._metadata(handle, captured[name])
    actual = files._capture(stage, private=True)
    if set(actual) != set(known) or any(not files._logical(actual[n], known[n]) for n in known):
        raise _fail('Windows publication staging differs from the additive union.')
    if files._capture(source, private=True) != captured:
        raise _fail('Windows additive staging changed during copying.')


def _private_snapshot(root: Path) -> tuple[dict, dict]:
    """Bind a reconstruction root and its complete independently private tree."""
    with files._entry(root.parent, root.name, True, private=True) as handle:
        record = files._record(handle, private=True)
    return record, files._capture(root, private=True)


def _remove_private(root: Path, expected: tuple[dict, dict]) -> None:
    """Delete only completely proven reconstruction, never transaction workspaces."""
    if _private_snapshot(root) != expected:
        raise _fail('Edited or incomplete Windows reconstruction retained.')
    root_record, tree = expected
    for name in sorted(tree, key=lambda n: (-n.count('/'), n)):
        path, record = root / name, tree[name]
        if record['id'][2]:
            with files._entry(path.parent, path.name, True, private=True) as handle:
                actual = files._record(handle, private=True)
            if actual != {**record, 'written': actual['written']}:
                raise _fail('Windows reconstruction directory changed during cleanup.')
            record = actual
        files._delete(path, record)
    with files._entry(root.parent, root.name, True, private=True) as handle:
        actual = files._record(handle, private=True)
    if actual != {**root_record, 'written': actual['written']}:
        raise _fail('Windows reconstruction root changed during cleanup.')
    files._delete(root, actual)


def _cleanup_git(
    plan: git._MergePlan, origin: dict, expected: dict | None, administration: dict | None, output_id: list | None
) -> bool:
    """Remove only exact owned Git artifacts, retaining any edits or uncertainty."""
    try:
        git._recheck_origin(plan, output_absent=False)
        if _git_tree(plan.origin, excluded={const.GIT_METADATA}) != origin:
            return False
        ref = 'refs/heads/' + plan.branch
        if git._text(git._git(plan.executable, plan.origin, 'rev-parse', '--verify', ref)) != plan.base_oid:
            return False
        if administration is None or _administration(plan) != administration:
            return False
        attached = [root for root, branch in git._worktrees(plan.executable, plan.origin) if branch == ref]
        if tx._entry_exists(plan.output):
            if expected is None or expected['']['id'] != output_id or _git_tree(plan.output) != expected:
                return False
            verification._reject_pending(plan.output)
            if attached == [plan.output]:
                if git._git(plan.executable, plan.output, 'symbolic-ref', 'HEAD') != (ref + '\n').encode():
                    return False
                # Git owns its administration/removal contract; no pathname
                # rmtree fallback or new recovery/pruning command is introduced.
                git._git(plan.executable, plan.origin, 'worktree', 'remove', '--force', str(plan.output))
            elif not attached and set(expected) == {''}:
                _remove_private(plan.output, _private_snapshot(plan.output))
            else:
                return False
        elif attached or any(root == plan.output for root, _ in git._worktrees(plan.executable, plan.origin)):
            return False
        elif output_id is not None:
            return False
        git._git(plan.executable, plan.origin, 'update-ref', '-d', ref, plan.base_oid)
        return True
    except (OSError, _ConfigurationError, _OperationalError, MemoryError):
        return False


def _publish_merge(plan: git._MergePlan, *, dry_run: bool = False) -> git._MergeResult | None:
    """Privately publish Windows Git differences without enabling CLI mutation.

    Only trusted Git plumbing writes shared administration. The empty worktree
    is protected before Git runs; all inherited controls are independently
    inspected. Ordinary failure may remove exact unchanged owned Git artifacts.
    Abrupt death can retain refs/registration/plaintext requiring manual review;
    this lifecycle adds no Git journal or recovery command. Completed common
    transaction workspaces remain retained under the existing Windows policy.
    """
    git._recheck_origin(plan)
    if dry_run:
        return None
    if os.name != 'nt':
        raise _ConfigurationError('Private native Windows Git publication requires Windows.')
    workspace = plan.reconstruction.transaction.workspace_parent / (const.GIT_STAGE_PREFIX + secrets.token_hex(16))
    expected_workspace = None
    output_id = expected = administration = None
    output_guard = None
    branch_attempted = created = False
    retained, warnings = [], []
    failure = outcome = None
    transaction = result = None
    transaction_names = frozenset()
    unsupported = set()
    # Retain native common/output-parent namespace guards across trusted Git
    # calls. Release the held worktree guard only for proven cleanup by Git,
    # which needs delete sharing. Same-user malicious writers are outside the model.
    with ExitStack() as stack:
        parents = {plan.common, plan.gitdir, plan.output.parent, workspace.parent}
        guards = [stack.enter_context(_Guard(parent)) for parent in parents]
        origin = _git_tree(plan.origin, excluded={const.GIT_METADATA})
        _administration(plan)

        def recheck():
            for guard in guards:
                guard._check()
            git._recheck_origin(plan, output_absent=output_id is None)
            if _git_tree(plan.origin, excluded={const.GIT_METADATA}) != origin:
                raise _fail('Windows origin identity/security/content changed.')
            _administration(plan)
            if output_id is not None:
                with files._entry(plan.output.parent, plan.output.name, True, private=True) as handle:
                    if files._id(handle) != output_id:
                        raise _fail('Windows review root identity changed.')

        try:
            files._mkdir(workspace.parent, workspace.name)
            overlay, captured = _stage_overlay(plan, workspace, unsupported)
            expected_workspace = _private_snapshot(workspace)
            recheck()
            _boundary('before-branch')
            branch_attempted = True
            git._git(
                plan.executable, plan.origin, 'update-ref', 'refs/heads/' + plan.branch, plan.base_oid, '0' * len(plan.base_oid)
            )
            created = True
            administration = _administration(plan)
            _boundary('branch-created')
            recheck()
            output_id = files._mkdir(plan.output.parent, plan.output.name)
            output_guard = stack.enter_context(_Guard(plan.output))
            guards.append(output_guard)
            expected = _git_tree(plan.output)
            _boundary('private-root-created')
            if files._names(plan.output):
                raise _fail('Windows worktree root is no longer empty.')
            recheck()
            git._git(plan.executable, plan.origin, 'worktree', 'add', '--no-checkout', str(plan.output), plan.branch)
            recheck()
            if files._names(plan.output) != [const.GIT_METADATA]:
                raise _fail('Windows Git created unexpected worktree entries.')
            # Audit both worktree controls and shared administration before
            # plaintext publication. No permission repair is performed.
            _git_tree(plan.output)
            _boundary('worktree-added')
            git._git(plan.executable, plan.output, 'read-tree', plan.base_oid)
            recheck()
            if const.GIT_IGNORE in captured:
                files._copy(overlay / const.GIT_IGNORE, plan.output / const.GIT_IGNORE, captured[const.GIT_IGNORE])
            expected = _git_tree(plan.output)
            administration = _administration(plan)
            _boundary('index-ready')
            transaction = tx._plan_transaction(
                plan.reconstruction.locations.mirror.path,
                plan.output,
                required_bytes=plan.reconstruction.transaction.required_bytes + sum(f.size for f in plan.base_files),
                target_rules=plan.reconstruction.transaction.target_rules,
            )
            proposed = None

            def build(stage):
                # The base .gitignore is installed as a protected control, so
                # the transaction proposal excludes it without consuming it.
                _copy_overlay(overlay, stage, captured, exclude={const.GIT_IGNORE})

            def verify(stage):
                nonlocal proposed
                actual = files._capture(stage, private=True)
                known = {n: r for n, r in captured.items() if n != const.GIT_IGNORE}
                if set(actual) != set(known) or any(not files._logical(actual[n], known[n]) for n in known):
                    raise _fail('Windows proposal differs from verified union.')
                proposed = actual
                recheck()
                if _git_tree(plan.output) != expected or _administration(plan) != administration:
                    raise _fail('Windows Git controls changed before publication.')

            transaction_names = frozenset(files._names(transaction.workspace_parent))
            result = windows._execute(transaction, build, verify, yes=True, prepublish=recheck)
            retained.append(result.workspace)
            # Do not capture an edited worktree as the cleanup baseline. Compare
            # exact recorded proposal IDs/bytes/metadata before adopting success.
            if files._capture(plan.output, protected=tx._protected_names(False), private=True) != proposed:
                expected = None
                raise _fail('Windows published proposal changed; retain worktree.')
            actual = _git_tree(plan.output)
            controls = {n: r for n, r in actual.items() if n in expected}
            # Only this root's child-publication write time is expected to
            # change. Freeze its new exact value after proving the proposal;
            # later directory metadata edits must also block cleanup.
            controls[''] = {**controls[''], 'written': expected['']['written']}
            if controls != expected or _administration(plan) != administration:
                expected = None
                raise _fail('Windows Git controls changed during publication.')
            expected = actual
            warnings.extend(result.warnings)
            _boundary('published')
            ignored = tuple(
                git._decode(p)
                for p in git._git(
                    plan.executable, plan.output, 'ls-files', '--others', '--ignored', '--exclude-standard', '-z'
                ).split(b'\0')
                if p
            )
            recheck()
            if _git_tree(plan.output) != expected or _administration(plan) != administration:
                raise _fail('Windows review artifacts changed before handoff.')
            if unsupported:
                warnings.append('Some modification times could not be preserved exactly.')
            outcome = ignored
        except BaseException as error:
            clean = not branch_attempted
            if created:
                try:
                    if output_guard is not None:
                        output_guard.__exit__()
                    clean = _cleanup_git(plan, origin, expected, administration, output_id)
                except OSError:
                    clean = False
            if tx._entry_exists(plan.output) and not clean:
                retained.append(plan.output)
            if isinstance(error, tx._TransactionError):
                warnings.append('Private transaction evidence retained; Git artifacts require manual inspection.')
            if transaction is not None and result is None:
                # Report newly observed evidence only; this grants no cleanup
                # authority and never interprets an incomplete journal as owned.
                try:
                    for name in files._names(transaction.workspace_parent):
                        suffix = name.removeprefix(const.TRANSACTION_PREFIX)
                        if (
                            name not in transaction_names
                            and name.startswith(const.TRANSACTION_PREFIX)
                            and len(suffix) == 32
                            and all(c in '0123456789abcdef' for c in suffix)
                        ):
                            retained.append(transaction.workspace_parent / name)
                    if tx._entry_exists(transaction.lock):
                        retained.append(transaction.lock)
                except OSError:
                    warnings.append('Transaction evidence enumeration incomplete; inspect the private workspace parent.')
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                error.add_note('Inspect retained private reconstruction, transaction and Git artifacts before retrying.')
                failure = error
            else:
                failure = 'Windows merge restore failed. ' + (
                    'Owned branch/worktree cleaned safely.'
                    if clean
                    else 'Git artifacts retained because ownership or data is uncertain.'
                )
        finally:
            try:
                if expected_workspace is None:
                    raise _fail('Incomplete Windows reconstruction retained.')
                _remove_private(workspace, expected_workspace)
            except (OSError, _ConfigurationError, _OperationalError, MemoryError):
                if tx._entry_exists(workspace):
                    retained.append(workspace)
    if isinstance(failure, BaseException):
        raise failure
    if failure is not None:
        raise git._MergeFailure(failure + (' ' + ' '.join(warnings) if warnings else ''), plan, tuple(retained)) from None
    if workspace in retained:
        warnings.append('Private reconstruction cleanup incomplete; sensitive plaintext retained.')
    warnings.append('Completed private Windows transaction evidence retained; inspect before manual cleanup.')
    return git._MergeResult(plan.output, plan.branch, outcome, tuple(warnings), tuple(retained))

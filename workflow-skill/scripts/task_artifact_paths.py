#!/usr/bin/env python3
"""Resolve ordinary task support inside the owning project's Cache."""

from __future__ import annotations

import hashlib
import argparse
import json
import plistlib
import os
import re
import stat
import sys
import shutil
import subprocess
import uuid
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Mapping
from xml.parsers.expat import ExpatError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_cache_cleanup
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


RUN_NAME_RE = re.compile(r"temp-(?P<task_key>[0-9a-f]{24})-(?P<run_id>[0-9a-f]{32})")


@contextmanager
def task_artifact_scope(project_root, task_id, *, borrowed_root=None):
    """Close an owned run and registration; a borrowed run stays caller-owned."""
    root = validate_task_directory(borrowed_root, project_root) if borrowed_root else resolve_task_artifact_root(project_root, task_id, create=True)
    if not root.is_dir():
        raise ValueError("borrowed task owner must already exist")
    failure = None
    try:
        yield root
    except BaseException as error:
        failure = error
        raise
    finally:
        if not borrowed_root:
            try:
                deadline = time.monotonic() + 5
                while True:
                    result = task_cache_cleanup.checkpoint(project_root, task_id, phase="finish", current_run=root, apply=True, budget_seconds=10, requested_only=True)
                    waiting = any(item.get("reason") == "active open files or working directory" for item in result["results"])
                    if result.get("requested_complete") or not waiting or time.monotonic() >= deadline:
                        break
                    time.sleep(.1)
                if not result.get("requested_complete"):
                    raise RuntimeError("Task owner cleanup pending: " + json.dumps(result, sort_keys=True))
            except Exception as cleanup_error:
                if failure is not None:
                    failure.add_note(str(cleanup_error))
                    print(str(cleanup_error), file=sys.stderr)
                else:
                    raise


def verify_cache_git(project_root: str | Path, path: str | Path) -> None:
    project = Path(project_root).resolve(strict=True)
    if not any((parent / ".git").exists() for parent in (project, *project.parents)):
        return
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git is required to verify Cache isolation")
    ignored = subprocess.run([git, "-C", str(project), "check-ignore", "-q", str(path)], capture_output=True, timeout=30, shell=False, **hidden_process_options())
    tracked = subprocess.run([git, "-C", str(project), "ls-files", "-z", "--", "Cache"], capture_output=True, timeout=30, shell=False, **hidden_process_options())
    if ignored.returncode != 0 or tracked.returncode != 0 or tracked.stdout:
        raise ValueError("project Cache must be ignored and contain no tracked files")


def _native_sticky_excluded(cache: Path) -> bool:
    """Read the native sticky exclusion marker without consulting backup mounts."""
    if sys.platform != "darwin":
        return False
    executable = shutil.which("xattr")
    if executable is None:
        return False
    original = cache.lstat()
    for ancestor in (cache, *cache.parents):
        _check_ancestors(ancestor)
        before = ancestor.lstat()
        result = task_cache_cleanup._run_command([executable, "-px", "com.apple.metadata:com_apple_backup_excludeItem", str(ancestor)], timeout=3)
        after, target = ancestor.lstat(), cache.lstat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or (target.st_dev, target.st_ino) != (original.st_dev, original.st_ino):
            raise ValueError("native exclusion directory identity changed")
        if result.returncode == 0 and not result.stderr.strip():
            try:
                marker = plistlib.loads(bytes.fromhex(result.stdout))
            except (ValueError, plistlib.InvalidFileException, ExpatError):
                return False
            if marker == "com.apple.backupd":
                return True
    return False


def _ensure_cache_backup_exclusion(cache: Path) -> None:
    """Verify macOS Cache exclusion before task payload or registry writes."""
    if sys.platform != "darwin":
        return
    _check_ancestors(cache)
    if _native_sticky_excluded(cache):
        return
    executable = shutil.which("tmutil")
    if executable is None:
        raise ValueError("Cache Time Machine exclusion cannot be verified: tmutil was not found on PATH")

    def is_excluded():
        _check_ancestors(cache)
        before = cache.lstat()
        observed = subprocess.run([executable, "isexcluded", "-X", str(cache)], capture_output=True, timeout=10, check=False, **hidden_process_options())
        if observed.returncode or observed.stderr.strip():
            raise ValueError(f"tmutil isexcluded exited {observed.returncode}: {observed.stderr.decode('utf-8', 'replace').strip()[:400]}")
        records = plistlib.loads(observed.stdout)
        if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict) or not isinstance(records[0].get("Path"), str) or type(records[0].get("IsExcluded")) not in (int, bool) or records[0]["IsExcluded"] not in (0, 1):
            raise ValueError("tmutil isexcluded returned an invalid exclusion plist")
        reported = _absolute_path(records[0].get("Path", ""), "tmutil Cache path")
        _check_ancestors(reported)
        _check_ancestors(cache)
        current, returned = cache.lstat(), reported.lstat()
        identities = {(item.st_dev, item.st_ino) for item in (before, current, returned)}
        if identities != {root_identity} or not stat.S_ISDIR(current.st_mode) or not stat.S_ISDIR(returned.st_mode):
            raise ValueError("tmutil exclusion did not identify the unchanged Cache directory")
        return bool(records[0]["IsExcluded"])

    try:
        _check_ancestors(cache)
        original = cache.lstat()
        root_identity = (original.st_dev, original.st_ino)
        if is_excluded():
            return
        _check_ancestors(cache)
        current = cache.lstat()
        if (current.st_dev, current.st_ino) != root_identity:
            raise ValueError("Cache directory changed before tmutil addexclusion")
        added = subprocess.run([executable, "addexclusion", str(cache)], capture_output=True, timeout=10, check=False, **hidden_process_options())
        if added.returncode or added.stderr.strip():
            raise ValueError(f"tmutil addexclusion exited {added.returncode}: {added.stderr.decode('utf-8', 'replace').strip()[:400]}")
        if not is_excluded():
            raise ValueError("tmutil still reports Cache included after addexclusion")
    except (OSError, subprocess.SubprocessError, ValueError, plistlib.InvalidFileException, ExpatError) as error:
        raise ValueError(f"Cache Time Machine exclusion could not be verified for {cache}: {error}") from error


def _absolute_path(value: str | Path, label: str) -> Path:
    text = os.fspath(value)
    if not text or text != text.strip() or any(ord(char) < 32 for char in text):
        raise ValueError(f"{label} must be a non-empty absolute path")
    if text.startswith("~") or any(token in text for token in ("%", "$")):
        raise ValueError(f"{label} contains an unexpanded environment or home token")
    path = Path(text)
    if not path.is_absolute() or any(part in {".", ".."} for part in text.replace("\\", "/").split("/")):
        raise ValueError(f"{label} must be absolute without dot or parent segments")
    if any((":" in part and part != path.anchor) or part.endswith((".", " ")) for part in path.parts):
        raise ValueError(f"{label} contains an unsafe path component")
    return path


def _check_ancestors(path: Path) -> None:
    for current in reversed((path, *path.parents)):
        try:
            observed = current.lstat()
        except FileNotFoundError:
            continue
        attributes = getattr(observed, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if stat.S_ISLNK(observed.st_mode) or (reparse and attributes & reparse):
            raise ValueError("task artifact paths must not traverse symlinks or reparse points")
        if not stat.S_ISDIR(observed.st_mode):
            raise ValueError("task artifact ancestor must be a directory")


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def legacy_artifact_base(*, environ: Mapping[str, str] | None = None) -> Path:
    """Locate the retired native task store for read/cleanup compatibility."""
    environment = os.environ if environ is None else environ
    match sys.platform:
        case "win32":
            return Path.home() / "YoFaAI" / "TaskArtifacts"
        case "darwin":
            return Path.home() / "Library" / "Application Support" / "YoFaAI" / "TaskArtifacts"
        case "linux":
            return Path(environment.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "YoFaAI" / "TaskArtifacts"
        case _:
            raise ValueError(f"unsupported task artifact host platform: {sys.platform}")


def _check_new_artifact_owner(project: Path, *, environ: Mapping[str, str] | None = None) -> None:
    legacy = legacy_artifact_base(environ=environ).resolve(strict=False)
    if _within(project, legacy) or (legacy.is_dir() and any(owner.samefile(legacy) for owner in (project, *project.parents))):
        raise ValueError("legacy task artifact stores are cleanup-only and cannot be project_root for new output; select the actual project or current workspace")


def _codex_component(path: Path) -> bool:
    return any(part.lower() in {".codex", ".agents", "codex-runtimes"} or part.lower().startswith("openai.codex_") for part in path.parts)


def validate_external_directory(
    directory: str | Path,
    project_root: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Validate without creating or following a link, including missing tails."""
    environment = os.environ if environ is None else environ
    path = _absolute_path(directory, "artifact directory")
    _check_ancestors(path)
    path = path.resolve(strict=False)
    _check_ancestors(path)
    project = Path(project_root).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise ValueError("project_root must be an existing directory")
    cache = project / "Cache"
    if _within(path, cache):
        return path
    raise ValueError("task artifacts must use the owning project's Cache directory")


def validate_task_directory(directory: str | Path, project_root: str | Path) -> Path:
    path = validate_external_directory(directory, project_root)
    cache = Path(project_root).expanduser().resolve(strict=True) / "Cache"
    relative = path.relative_to(cache)
    if not relative.parts or not relative.parts[0].startswith("temp-"):
        raise ValueError("task output must be inside a project Cache/temp-* directory")
    return path


def resolve_artifact_base(
    project_root: str | Path,
    *,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    environment = os.environ if environ is None else environ
    project = Path(project_root).expanduser().resolve(strict=True)
    cache = project / "Cache"
    selected = _absolute_path(artifact_root, "artifact directory") if artifact_root is not None else cache
    if selected != cache:
        raise ValueError("task artifacts must use the owning project's Cache directory")
    return validate_external_directory(selected, project, environ=environment)


def project_artifact_directory(
    project_root: str | Path,
    *,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    create: bool = False,
) -> Path:
    project = Path(project_root).expanduser().resolve(strict=True)
    path = resolve_artifact_base(project, artifact_root=artifact_root, environ=environ)
    validate_external_directory(path, project, environ=environ)
    if create:
        _check_new_artifact_owner(project, environ=environ)
        path.mkdir(parents=True, exist_ok=True)
        validate_external_directory(path, project, environ=environ)
        _ensure_cache_backup_exclusion(path)
    return path


def resolve_task_artifact_root(
    project_root: str | Path,
    task_id: str,
    *,
    run_id: str | None = None,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    create: bool = False,
) -> Path:
    """Allocate a fresh execution path; only an explicit run ID resolves it again."""
    if not isinstance(task_id, str) or not task_id.strip() or any(ord(char) < 32 for char in task_id):
        raise ValueError("task_id must be a non-empty identifier without control characters")
    task_key = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:24]
    if run_id is None:
        run_id = uuid.uuid4().hex
    if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("run_id must be a lowercase 32-character UUID hex value")
    path = project_artifact_directory(project_root, artifact_root=artifact_root, environ=environ) / f"temp-{task_key}-{run_id}"
    validate_external_directory(path, project_root, environ=environ)
    if create:
        _check_new_artifact_owner(Path(project_root).expanduser().resolve(strict=True), environ=environ)
        verify_cache_git(project_root, path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_cache_backup_exclusion(path.parent)
        try:
            checkpoint = task_cache_cleanup.checkpoint(project_root, task_id, artifact_root=path.parent, phase="start", current_run=path, apply=True, budget_seconds=5)
        except (OSError, ValueError) as error:
            checkpoint = {"bytes_deleted": 0, "results": [{"action": "pending", "reason": str(error)}]}
        actionable = [item for item in checkpoint["results"] if item["action"] in {"deleted", "pending"}]
        remote_review = checkpoint.get("remote_review", [])
        if actionable or remote_review:
            counts = {action: sum(item["action"] == action for item in actionable) for action in ("deleted", "pending")}
            print(json.dumps({"event": "task_cache_checkpoint", "bytes_deleted": checkpoint["bytes_deleted"], "result_counts": counts, "results": actionable[:5], "results_omitted": max(0, len(actionable) - 5), "remote_review_count": len(remote_review), "remote_review": remote_review[:5], "remote_review_omitted": max(0, len(remote_review) - 5)}, sort_keys=True), file=sys.stderr)
        path.mkdir(parents=True, exist_ok=False)
        validate_external_directory(path, project_root, environ=environ)
        try:
            task_cache_cleanup.register_run(project_root, task_id, path, artifact_root=path.parent)
        except (OSError, ValueError):
            path.rmdir()
            raise
    return path


def task_artifact_run_id(task_root: str | Path) -> str:
    match = RUN_NAME_RE.fullmatch(Path(task_root).name)
    if match is None:
        raise ValueError("task_root must identify one independent temp execution directory")
    return match["run_id"]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_run_inputs(project_root: str | Path, source_root: str | Path, destination_root: str | Path, relative_paths: list[str]) -> list[dict[str, str]]:
    """Copy only selected files into a new run, with independent byte readback."""
    source = validate_external_directory(source_root, project_root)
    destination = validate_external_directory(destination_root, project_root)
    if source == destination or source.parent != destination.parent:
        raise ValueError("continuation requires different execution directories for the same project")
    expected_parent = project_artifact_directory(project_root, artifact_root=destination.parent)
    if source.parent != expected_parent or not source.is_dir() or not destination.is_dir():
        raise ValueError("continuation roots must belong to the exact existing project artifact owner")
    task_artifact_run_id(destination)
    if RUN_NAME_RE.fullmatch(source.name) is None and re.fullmatch(r"t-[0-9a-f]{24}", source.name) is None:
        raise ValueError("source must be an exact current or legacy execution directory")
    if not relative_paths or len(relative_paths) != len(set(relative_paths)):
        raise ValueError("select a non-empty unique list of useful input files")
    selected = []
    for relative in relative_paths:
        if not isinstance(relative, str) or relative != relative.strip() or "\\" in relative or ":" in relative or any(ord(char) < 32 for char in relative) or relative.startswith("/") or any(part in {"", ".", ".."} for part in relative.split("/")):
            raise ValueError("input paths must be normalized relative file paths")
        original = source.joinpath(*relative.split("/"))
        target = destination.joinpath(*relative.split("/"))
        _check_ancestors(original.parent)
        _check_ancestors(target.parent)
        observed = original.lstat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1 or getattr(observed, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError("continuation inputs must be regular files without links or reparse points")
        if target.exists() or target.is_symlink():
            raise ValueError("continuation must not overwrite files in the new run")
        selected.append((relative, original, target, observed))
    receipts = []
    created = []
    created_directories = set()
    try:
        for relative, original, target, observed in selected:
            created_directories.update(directory for directory in (target.parent, *target.parent.parents) if directory != destination and destination in directory.parents and not directory.exists())
            target.parent.mkdir(parents=True, exist_ok=True)
            with original.open("rb") as reader, target.open("xb") as writer:
                identity = os.fstat(writer.fileno())
                created.append((target, identity.st_dev, identity.st_ino))
                shutil.copyfileobj(reader, writer)
            source_digest = _file_sha256(original)
            copied_digest = _file_sha256(target)
            current = original.lstat()
            if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns) != (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns) or source_digest != copied_digest:
                raise ValueError("continuation input changed or copied bytes failed verification; source preserved")
            receipts.append({"path": relative, "sha256": copied_digest})
    except (OSError, ValueError):
        for target, device, inode in reversed(created):
            if target.exists() and not target.is_symlink():
                observed = target.lstat()
                if (observed.st_dev, observed.st_ino) == (device, inode):
                    target.unlink()
        for directory in sorted(created_directories, key=lambda value: len(value.parts), reverse=True):
            if directory.is_dir() and not directory.is_symlink() and not any(directory.iterdir()):
                directory.rmdir()
        raise
    return receipts


def task_artifact_environment(
    task_root: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    create: bool = False,
) -> dict[str, str]:
    """Return a child environment whose temporary files stay in this exact root."""
    root = _absolute_path(task_root, "task_root")
    _check_ancestors(root)
    root = root.resolve(strict=False)
    environment = dict(os.environ if environ is None else environ)
    task_artifact_run_id(root)
    if not root.is_dir() or root.parent.name != "Cache":
        raise ValueError("temporary environment requires a project Cache/temp-* task root")
    codex_value = environment.get("CODEX_HOME")
    codex = _absolute_path(codex_value, "CODEX_HOME") if codex_value else Path.home() / ".codex"
    if _within(root, codex.resolve(strict=False)):
        raise ValueError("task temporary environment must remain outside Codex")
    temporary = root / "tmp"
    _check_ancestors(temporary)
    if create:
        _check_new_artifact_owner(root.parent.parent, environ=environment)
        _ensure_cache_backup_exclusion(root.parent)
        temporary.mkdir(parents=True, exist_ok=True)
        _check_ancestors(temporary)
    elif not temporary.is_dir():
        raise ValueError("create the exact task tmp directory before preparing a child environment")
    environment.update({name: str(temporary) for name in ("TMP", "TEMP", "TMPDIR")})
    return environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--run-id", help="Resolve one already allocated run; omit for a new execution")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--copy-from", type=Path)
    parser.add_argument("--input", action="append", default=[], help="Selected useful relative input file; repeat as needed")
    arguments = parser.parse_args()
    root = None
    created_root = None
    try:
        if bool(arguments.copy_from) != bool(arguments.input) or (arguments.copy_from and not arguments.create):
            raise ValueError("--copy-from and --input require a newly created execution directory")
        root = resolve_task_artifact_root(arguments.project_root, arguments.task_id, run_id=arguments.run_id, artifact_root=arguments.artifact_root, create=arguments.create)
        created_root = root if arguments.create else None
        copied = copy_run_inputs(arguments.project_root, arguments.copy_from, root, arguments.input) if arguments.copy_from else []
        environment = task_artifact_environment(root, create=True) if arguments.create else None
        print(json.dumps({"status": "complete", "task_root": str(root), "run_id": task_artifact_run_id(root), "copied_inputs": copied, "temporary_environment": {name: environment[name] for name in ("TMP", "TEMP", "TMPDIR")} if environment else None}, sort_keys=True))
        return 0
    except (OSError, ValueError) as error:
        cleanup = "not_created"
        cleanup_detail = None
        if created_root is not None:
            try:
                result = task_cache_cleanup.checkpoint(arguments.project_root, arguments.task_id, phase="finish", current_run=created_root, apply=True, requested_only=True)
                cleanup = "removed" if result.get("requested_complete") else "pending"
                if cleanup == "pending":
                    cleanup_detail = result["results"]
            except (OSError, ValueError, KeyError) as cleanup_error:
                cleanup = "pending"
                cleanup_detail = str(cleanup_error)
        print(json.dumps({"status": "error", "reason": str(error), "task_root": str(root) if root is not None else None, "run_id": task_artifact_run_id(root) if root is not None else None, "cleanup": cleanup, "cleanup_detail": cleanup_detail}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

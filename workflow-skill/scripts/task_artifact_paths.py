#!/usr/bin/env python3
"""Resolve ordinary task support outside projects and Codex-managed storage."""

from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import stat
import sys
import shutil
import uuid
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_cache_cleanup


RUN_NAME_RE = re.compile(r"temp-(?P<task_key>[0-9a-f]{24})-(?P<run_id>[0-9a-f]{32})")


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
    codex_value = environment.get("CODEX_HOME")
    codex = _absolute_path(codex_value, "CODEX_HOME") if codex_value else Path.home() / ".codex"
    for forbidden in (project, codex.resolve(strict=False), Path.home() / ".agents"):
        if _within(path, forbidden):
            raise ValueError("task artifacts must remain outside the project and Codex directories")
    if _codex_component(path):
        raise ValueError("task artifacts must remain outside Codex directories")
    if any((ancestor / ".git").exists() for ancestor in (path, *path.parents)):
        raise ValueError("task artifacts must remain outside every Git project")
    if path == Path(path.anchor) or path == Path.home():
        raise ValueError("an entire filesystem or home directory is not an artifact owner")
    return path


def resolve_artifact_base(
    project_root: str | Path,
    *,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    environment = os.environ if environ is None else environ
    selected = artifact_root if artifact_root is not None else environment.get("YOFA_TASK_ARTIFACT_ROOT")
    if selected is None:
        if os.name == "nt":
            # MSIX hosts can transparently redirect LOCALAPPDATA into Codex's
            # managed package storage. The home-owned directory stays external.
            selected = Path.home() / "YoFaAI" / "TaskArtifacts"
        elif sys.platform == "darwin":
            selected = Path.home() / "Library" / "Application Support" / "YoFaAI" / "TaskArtifacts"
        else:
            cache = environment.get("XDG_CACHE_HOME")
            selected = (_absolute_path(cache, "XDG_CACHE_HOME") if cache else Path.home() / ".cache") / "YoFaAI" / "TaskArtifacts"
    return validate_external_directory(selected, project_root, environ=environment)


def project_artifact_directory(
    project_root: str | Path,
    *,
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    create: bool = False,
) -> Path:
    project = Path(project_root).expanduser().resolve(strict=True)
    identity = hashlib.sha256(os.fsencode(os.path.normcase(str(project)))).hexdigest()[:16]
    path = resolve_artifact_base(project, artifact_root=artifact_root, environ=environ) / f"p-{identity}"
    validate_external_directory(path, project, environ=environ)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        validate_external_directory(path, project, environ=environ)
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
    path = project_artifact_directory(project_root, artifact_root=artifact_root, environ=environ, create=create) / f"temp-{task_key}-{run_id}"
    validate_external_directory(path, project_root, environ=environ)
    if create:
        try:
            checkpoint = task_cache_cleanup.checkpoint(project_root, task_id, artifact_root=path.parent.parent, phase="start", current_run=path, apply=True, budget_seconds=5)
        except (OSError, ValueError) as error:
            checkpoint = {"bytes_deleted": 0, "results": [{"action": "pending", "reason": str(error)}]}
        actionable = [item for item in checkpoint["results"] if item["action"] in {"deleted", "pending"}]
        if actionable:
            counts = {action: sum(item["action"] == action for item in actionable) for action in ("deleted", "pending")}
            print(json.dumps({"event": "task_cache_checkpoint", "bytes_deleted": checkpoint["bytes_deleted"], "result_counts": counts, "results": actionable[:5], "results_omitted": max(0, len(actionable) - 5)}, sort_keys=True), file=sys.stderr)
        path.mkdir(parents=True, exist_ok=False)
        validate_external_directory(path, project_root, environ=environ)
        try:
            task_cache_cleanup.register_run(project_root, task_id, path, artifact_root=path.parent.parent)
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
    expected_parent = project_artifact_directory(project_root, artifact_root=destination.parent.parent)
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
    if not root.is_dir() or not re.fullmatch(r"p-[0-9a-f]{16}", root.parent.name):
        raise ValueError("temporary environment requires a resolved external project/task root")
    codex_value = environment.get("CODEX_HOME")
    codex = _absolute_path(codex_value, "CODEX_HOME") if codex_value else Path.home() / ".codex"
    if _within(root, codex.resolve(strict=False)):
        raise ValueError("task temporary environment must remain outside Codex")
    if _codex_component(root) or any((ancestor / ".git").exists() for ancestor in (root, *root.parents)):
        raise ValueError("task temporary environment must remain outside projects and Codex")
    temporary = root / "tmp"
    _check_ancestors(temporary)
    if create:
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
        if created_root is not None:
            try:
                validate_external_directory(created_root, arguments.project_root)
                created_root.rmdir()
                cleanup = "removed"
            except (OSError, ValueError):
                cleanup = "pending"
        print(json.dumps({"status": "error", "reason": str(error), "task_root": str(root) if root is not None else None, "run_id": task_artifact_run_id(root) if root is not None else None, "cleanup": cleanup}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

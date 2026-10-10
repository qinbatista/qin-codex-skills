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
from pathlib import Path
from typing import Mapping


def _absolute_path(value: str | Path, label: str) -> Path:
    text = os.fspath(value)
    if not text or text != text.strip() or any(ord(char) < 32 for char in text):
        raise ValueError(f"{label} must be a non-empty absolute path")
    if any(token in text for token in ("%", "$", "~")):
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
    artifact_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    create: bool = False,
) -> Path:
    if not isinstance(task_id, str) or not task_id.strip() or any(ord(char) < 32 for char in task_id):
        raise ValueError("task_id must be a non-empty identifier without control characters")
    task_key = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:24]
    path = project_artifact_directory(project_root, artifact_root=artifact_root, environ=environ, create=create) / f"t-{task_key}"
    validate_external_directory(path, project_root, environ=environ)
    if create:
        path.mkdir(exist_ok=True)
        validate_external_directory(path, project_root, environ=environ)
    return path


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
    if not re.fullmatch(r"t-[0-9a-f]{24}", root.name) or not re.fullmatch(r"p-[0-9a-f]{16}", root.parent.name):
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
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--create", action="store_true")
    arguments = parser.parse_args()
    try:
        root = resolve_task_artifact_root(arguments.project_root, arguments.task_id, artifact_root=arguments.artifact_root, create=arguments.create)
        environment = task_artifact_environment(root, create=True) if arguments.create else None
        print(json.dumps({"status": "complete", "task_root": str(root), "temporary_environment": {name: environment[name] for name in ("TMP", "TEMP", "TMPDIR")} if environment else None}, sort_keys=True))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "error", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

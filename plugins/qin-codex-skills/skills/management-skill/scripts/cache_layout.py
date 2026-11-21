#!/usr/bin/env python3
"""Validate the two-category layout of project Cache directories."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional


SKIP_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "Build",
    "Builds",
    "Library",
    "Logs",
    "Obj",
    "Temp",
    "UserSettings",
    "__pycache__",
    "dist",
    "node_modules",
    "venv",
}


def classify_directory(name: str) -> Optional[str]:
    """Return the allowed category or None for a legacy/unknown directory."""

    if name.startswith("temp-") and len(name) > len("temp-"):
        return "temp"
    if name.startswith("remote-") and len(name) > len("remote-"):
        return "remote"
    return None


def discover_cache_roots(project_root: Path) -> list[Path]:
    """Find Cache roots without descending into a discovered Cache tree."""

    roots: list[Path] = []
    for current, directory_names, _ in os.walk(project_root, topdown=True):
        current_path = Path(current)
        directory_names[:] = sorted(
            directory_name
            for directory_name in directory_names
            if directory_name not in SKIP_DIRECTORY_NAMES
        )
        if current_path.name == "Cache":
            roots.append(current_path)
            directory_names[:] = []
    return sorted(roots)


def inspect_cache_root(cache_root: Path, project_root: Path | None = None) -> dict[str, object]:
    invalid: list[str] = []
    categories: dict[str, list[str]] = {"temp": [], "remote": []}
    for child in sorted(cache_root.iterdir(), key=lambda path: path.name):
        if not child.is_dir() or child.is_symlink():
            invalid.append(child.name)
            continue
        category = classify_directory(child.name)
        if category is None:
            invalid.append(child.name)
        else:
            categories[category].append(child.name)
    return {
        "path": cache_root.relative_to(project_root).as_posix() if project_root is not None else cache_root.name,
        "status": "pass" if not invalid else "fail",
        "invalid_entries": invalid,
        "categories": categories,
    }


def inspect_project(project_root: Path) -> dict[str, object]:
    resolved_root = project_root.expanduser().resolve()
    cache_roots = discover_cache_roots(resolved_root)
    reports = [inspect_cache_root(cache_root, resolved_root) for cache_root in cache_roots]
    invalid_roots = [report for report in reports if report["status"] != "pass"]
    return {
        "schema_version": 2,
        "project_root": ".",
        "status": "pass" if not invalid_roots else "fail",
        "cache_roots": reports,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check", help="validate discovered Cache roots")
    check_parser.add_argument("--project-root", type=Path, required=True)
    check_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    report = inspect_project(arguments.project_root)
    if arguments.as_json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        for cache_root in report["cache_roots"]:
            status = cache_root["status"]
            invalid = ", ".join(cache_root["invalid_entries"]) or "none"
            print(f"{status}: {cache_root['path']} invalid={invalid}")
        print(f"status: {report['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

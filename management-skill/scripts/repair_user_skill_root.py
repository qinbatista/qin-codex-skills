#!/usr/bin/env python3
"""Consolidate legacy user Skills with verified, recoverable copies."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import uuid
from contextlib import ExitStack
from pathlib import Path


def checked_path(path):
    path = Path(os.path.abspath(Path(path).expanduser()))
    for candidate in (path, *path.parents):
        try:
            observed = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(observed.st_mode) or getattr(observed, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"Refusing a symbolic link or junction: {candidate}")
    return path


def entry_exists(path):
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def tree_manifest(directory):
    directory = checked_path(directory)
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise ValueError(f"Expected a real Skill directory: {directory}")
    result = {}
    pending = [directory]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = checked_path(current / entry.name)
                observed = path.lstat()
                relative = path.relative_to(directory).as_posix()
                if stat.S_ISDIR(observed.st_mode):
                    result[relative] = {"kind": "directory"}
                    pending.append(path)
                elif stat.S_ISREG(observed.st_mode):
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    result[relative] = {"kind": "file", "size": observed.st_size, "sha256": digest.hexdigest()}
                else:
                    raise ValueError(f"Refusing a nonregular Skill entry: {path}")
    return result


def load_installer():
    path = Path(__file__).with_name("sync_global_skills.py")
    spec = importlib.util.spec_from_file_location("skill_root_repair_installer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def matches_installed_source(installer, source, target):
    tree_manifest(source)
    def manifest(root):
        return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in installer.included_files(root)}
    return (source / "SKILL.md").is_file() and manifest(source) == manifest(target)


def repair_skill(source, target, backups, installer, *, apply, authoritative_source=None, progress=None):
    original = tree_manifest(source)
    if original.get("SKILL.md", {}).get("kind") != "file":
        raise ValueError("The legacy Skill has no regular SKILL.md")
    observed = tree_manifest(target) if entry_exists(target) else None
    if observed is None:
        action = "copy_then_retire"
    elif observed == original:
        action = "retire_duplicate"
    elif authoritative_source is not None and matches_installed_source(installer, authoritative_source, target):
        action = "retire_superseded"
    else:
        return {"name": source.name, "status": "pending", "reason": "Different official and legacy Skill contents; neither copy was overwritten."}
    result = progress if progress is not None else {}
    result.update(name=source.name, status="planned", action=action)
    if not apply:
        return result
    identity = json.dumps({"source": str(source), "files": original}, sort_keys=True).encode("utf-8")
    backup = checked_path(backups / f"{source.name}-{hashlib.sha256(identity).hexdigest()[:24]}")
    result["backup"] = str(backup)
    backup.mkdir(parents=True, exist_ok=True)
    saved = backup / "copy"
    if not entry_exists(saved):
        staged_backup = backup / f".copy-{uuid.uuid4().hex}"
        result["staged_backup"] = str(staged_backup)
        shutil.copytree(source, staged_backup, symlinks=True)
        if tree_manifest(staged_backup) != original:
            raise ValueError(f"Backup verification failed; original preserved. Recovery directory: {backup}")
        os.rename(staged_backup, saved)
        result.pop("staged_backup")
    if tree_manifest(saved) != original or tree_manifest(source) != original:
        raise ValueError(f"Legacy or backup contents changed; original preserved. Recovery directory: {backup}")
    installer.write_atomic_json(backup / "manifest.json", {"schema_version": 1, "legacy": str(source), "official": str(target), "files": original})
    if observed is None:
        checked_path(target.parent).mkdir(parents=True, exist_ok=True)
        staged_target = target.parent.parent / f".skill-migration-{uuid.uuid4().hex}"
        result["staged_target"] = str(staged_target)
        shutil.copytree(saved, staged_target, symlinks=True)
        if tree_manifest(staged_target) != original or entry_exists(target):
            raise ValueError(f"Official target changed during migration; original preserved. Recovery directory: {backup}")
        os.rename(staged_target, target)
        result.pop("staged_target")
        observed = original
    if tree_manifest(target) != observed or tree_manifest(source) != original or tree_manifest(saved) != original:
        raise ValueError(f"Skill contents changed before retirement; original preserved. Recovery directory: {backup}")
    retired = backup / f"retired-{uuid.uuid4().hex}"
    result["retirement_target"] = str(retired)
    os.rename(source, retired)
    if tree_manifest(retired) != original:
        if not entry_exists(source):
            os.rename(retired, source)
        raise ValueError(f"Retired Skill verification failed. Recovery directory: {backup}")
    result.update(status="repaired", retired=str(retired))
    result.pop("retirement_target")
    return result


def repair_user_skill_root(*, legacy_root=None, official_root=None, backup_root=None, project_root=None, apply=False, source_dir=None, authoritative_names=()):
    legacy = Path(legacy_root) if legacy_root is not None else Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills"
    official = Path(official_root) if official_root is not None else Path.home() / ".agents" / "skills"
    result = {"status": "unchanged", "apply": apply, "legacy_root": str(legacy), "official_root": str(official), "entries": []}
    try:
        if project_root is not None:
            if legacy_root is not None or official_root is not None:
                raise ValueError("Use project_root or explicit Skill roots, not both")
            project = checked_path(project_root)
            if not project.is_dir():
                raise ValueError("The project root must be an existing directory")
            legacy, official = project / ".codex" / "skills", project / ".agents" / "skills"
            if backup_root is None:
                owner = hashlib.sha256(str(project).encode("utf-8")).hexdigest()[:12]
                backup_root = Path.home() / ".agents" / "skill-migration-backups" / f"project-{project.name}-{owner}"
        legacy, official = checked_path(legacy), checked_path(official)
        backups = checked_path(backup_root if backup_root is not None else official.parent / "skill-migration-backups")
        result.update(legacy_root=str(legacy), official_root=str(official), backup_root=str(backups))
        for first, second in ((legacy, official), (legacy, backups), (official, backups)):
            if first == second or first in second.parents or second in first.parents:
                raise ValueError("Legacy, official, and backup roots must be separate, nonnested directories")
        if not entry_exists(legacy):
            return result
        if not stat.S_ISDIR(legacy.lstat().st_mode):
            raise ValueError("The legacy Skill root is not a real directory")
        installer = load_installer()
        names = set(authoritative_names) & set(installer.PRIMARY_SKILL_ORDER)
        source_dir = checked_path(source_dir) if source_dir is not None else None
        with ExitStack() as locks:
            if apply:
                lock_roots = {root.parent: root for root in (legacy, official)}
                for root in sorted(lock_roots.values(), key=str):
                    locks.enter_context(installer.installation_lock(root))
            with os.scandir(legacy) as entries:
                candidates = sorted((entry.name for entry in entries), key=str.casefold)
            for name in candidates:
                source, target = legacy / name, official / name
                if name.startswith("."):
                    result["entries"].append({"name": name, "status": "preserved", "reason": "Hidden or bundled resource"})
                    continue
                progress = {"name": name}
                try:
                    checked_path(source)
                    if not stat.S_ISDIR(source.lstat().st_mode) or not entry_exists(source / "SKILL.md"):
                        result["entries"].append({"name": name, "status": "preserved", "reason": "Not a user Skill directory"})
                        continue
                    authority = source_dir / name if source_dir is not None and name in names else None
                    result["entries"].append(repair_skill(source, target, backups, installer, apply=apply, authoritative_source=authority, progress=progress))
                except (OSError, ValueError, RuntimeError) as error:
                    progress.update(status="pending", reason=f"{type(error).__name__}: {error}")
                    result["entries"].append(progress)
    except (OSError, ValueError, RuntimeError) as error:
        result.update(status="pending", reason=f"{type(error).__name__}: {error}")
        return result
    statuses = {entry["status"] for entry in result["entries"]}
    result["status"] = "pending" if "pending" in statuses else "repaired" if "repaired" in statuses else "planned" if "planned" in statuses else "unchanged"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "apply"))
    parser.add_argument("--legacy-root", type=Path)
    parser.add_argument("--official-root", type=Path)
    parser.add_argument("--backup-root", type=Path)
    parser.add_argument("--project-root", type=Path, help="Move only this project's .codex/skills to its .agents/skills; never install them globally.")
    parser.add_argument("--source-dir", type=Path, help="Authorize managed conflicts only when official files match this maintained source.")
    args = parser.parse_args(argv)
    names = load_installer().PRIMARY_SKILL_ORDER if args.source_dir is not None else ()
    result = repair_user_skill_root(legacy_root=args.legacy_root, official_root=args.official_root, backup_root=args.backup_root, project_root=args.project_root, apply=args.command == "apply", source_dir=args.source_dir, authoritative_names=names)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "pending" else 0


if __name__ == "__main__":
    raise SystemExit(main())

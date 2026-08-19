#!/usr/bin/env python3
"""Maintain safe, non-copying aliases from an Agents skills root to Codex."""

import argparse
import json
import re
from pathlib import Path


SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class SkillAliasError(ValueError):
    """Raised when an alias would overwrite or escape a managed skill root."""


def _skill_names(canonical_root, requested):
    if requested:
        names = list(dict.fromkeys(requested))
    else:
        names = sorted(path.name for path in canonical_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    if not names:
        raise SkillAliasError("no canonical Skills were selected")
    if any(SKILL_NAME_PATTERN.fullmatch(name) is None for name in names):
        raise SkillAliasError("skill names must be simple lowercase directory names")
    return names


def _inside(root, path):
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _canonical_skill(canonical_root, skill_name):
    source = canonical_root / skill_name
    if not source.is_dir() or not (source / "SKILL.md").is_file() or not _inside(canonical_root, source):
        raise SkillAliasError(f"canonical Skill is unavailable: {skill_name}")
    return source.resolve()


def _alias_state(target, source):
    if target.is_symlink():
        try:
            return "linked" if target.resolve() == source else "conflict"
        except OSError:
            return "conflict"
    return "absent" if not target.exists() else "conflict"


def apply_aliases(command, canonical_root, agents_root, skills=None, dry_run=False):
    canonical_root = Path(canonical_root).expanduser().resolve()
    agents_root = Path(agents_root).expanduser().resolve()
    if not canonical_root.is_dir():
        raise SkillAliasError("canonical skills root does not exist")
    names = _skill_names(canonical_root, skills)
    results = []
    for skill_name in names:
        source = _canonical_skill(canonical_root, skill_name)
        target = agents_root / skill_name
        state = _alias_state(target, source)
        if command in {"install", "upgrade"}:
            if state == "conflict":
                raise SkillAliasError(f"refusing to overwrite user Skill: {skill_name}")
            if state == "linked":
                action = "unchanged"
            else:
                action = "linked"
                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        target.symlink_to(source, target_is_directory=True)
                    except OSError as error:
                        raise SkillAliasError("unable to create a Skill symlink; no copy fallback is used") from error
            results.append({"skill": skill_name, "action": action})
            continue
        if command != "uninstall":
            raise SkillAliasError("command must be install, upgrade, or uninstall")
        if state == "absent":
            action = "unchanged"
        elif state == "conflict":
            raise SkillAliasError(f"refusing to remove a user-owned Skill: {skill_name}")
        else:
            action = "unlinked"
            if not dry_run:
                target.unlink()
        results.append({"skill": skill_name, "action": action})
    return {"status": "pass", "command": command, "alias_mode": "symlink", "results": results}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Create safe .agents Skill aliases without copying canonical content.")
    parser.add_argument("command", choices=("install", "upgrade", "uninstall"))
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--agents-root", type=Path, required=True)
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = apply_aliases(args.command, args.canonical_root, args.agents_root, args.skill, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

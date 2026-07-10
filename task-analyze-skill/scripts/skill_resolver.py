#!/usr/bin/env python3
"""Resolve global and canonical plugin-qualified skill IDs safely."""

import re
from pathlib import Path


SKILL_PART_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _valid_part(value):
    return isinstance(value, str) and bool(SKILL_PART_PATTERN.fullmatch(value))


def validate_skill_id(skill_id):
    if not isinstance(skill_id, str) or not skill_id:
        raise ValueError("skill id must be a non-empty string")
    parts = skill_id.split(":")
    if len(parts) == 1 and _valid_part(parts[0]):
        return parts
    if len(parts) == 2 and all(_valid_part(part) for part in parts):
        return parts
    raise ValueError("skill id must be a global skill or canonical plugin-qualified id")


def resolve_skill_path(skill_id, skills_root, plugins_cache_root=None):
    parts = validate_skill_id(skill_id)
    skills_root = Path(skills_root).resolve()
    if len(parts) == 1:
        skill_path = skills_root / parts[0] / "SKILL.md"
        resolved_skill_path = skill_path.resolve()
        try:
            resolved_skill_path.relative_to(skills_root)
        except ValueError:
            return None
        return resolved_skill_path if resolved_skill_path.is_file() else None

    plugin_id, skill_name = parts
    cache_root = Path(plugins_cache_root).resolve() if plugins_cache_root is not None else skills_root.parent / "plugins" / "cache"
    if not cache_root.is_dir():
        return None
    matches = sorted(cache_root.glob(f"*/{plugin_id}/*/skills/{skill_name}/SKILL.md"))
    safe_matches = []
    for match in matches:
        resolved_match = match.resolve()
        try:
            resolved_match.relative_to(cache_root)
        except ValueError:
            continue
        if resolved_match.is_file():
            safe_matches.append(resolved_match)
    return safe_matches[-1] if safe_matches else None

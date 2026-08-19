#!/usr/bin/env python3
"""Resolve global and canonical plugin-qualified skill IDs safely."""

import re
import os
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


def _plugin_skill_matches(skill_name, cache_root, plugin_id=None):
    if not cache_root.is_dir():
        return []
    pattern = f"*/{plugin_id}/*/skills/{skill_name}/SKILL.md" if plugin_id is not None else f"*/*/*/skills/{skill_name}/SKILL.md"
    matches = []
    for match in sorted(cache_root.glob(pattern)):
        resolved_match = match.resolve()
        try:
            relative_parts = resolved_match.relative_to(cache_root).parts
        except ValueError:
            continue
        if resolved_match.is_file() and len(relative_parts) >= 6:
            matches.append((relative_parts[1], resolved_match))
    return matches


def compatible_skill_roots(skills_root=None, agents_skills_root=None, environment=None):
    """Return canonical Codex and compatible Agents skill roots in precedence order."""
    values = environment if environment is not None else os.environ
    codex_home = Path(values.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    agents_home = Path(values.get("CODEX_AGENTS_HOME") or Path.home() / ".agents").expanduser()
    candidates = [skills_root or codex_home / "skills", agents_skills_root or agents_home / "skills"]
    roots = []
    for candidate in candidates:
        root = Path(candidate).expanduser().resolve()
        if root not in roots:
            roots.append(root)
    return tuple(roots)


def resolve_skill_path(skill_id, skills_root, plugins_cache_root=None, allowed_skill_roots=()):
    parts = validate_skill_id(skill_id)
    skills_root = Path(skills_root).resolve()
    if len(parts) == 1:
        skill_path = skills_root / parts[0] / "SKILL.md"
        resolved_skill_path = skill_path.resolve()
        allowed_roots = (skills_root, *[Path(root).expanduser().resolve() for root in allowed_skill_roots])
        def inside(root):
            try:
                resolved_skill_path.relative_to(root)
                return True
            except ValueError:
                return False
        if not any(inside(root) for root in allowed_roots):
            return None
        return resolved_skill_path if resolved_skill_path.is_file() else None

    plugin_id, skill_name = parts
    cache_root = Path(plugins_cache_root).resolve() if plugins_cache_root is not None else skills_root.parent / "plugins" / "cache"
    matches = [path for package, path in _plugin_skill_matches(skill_name, cache_root, plugin_id) if package == plugin_id]
    return matches[-1] if matches else None


def resolve_compatible_skill_path(skill_id, skills_root=None, agents_skills_root=None, plugins_cache_root=None, environment=None):
    """Resolve a skill through canonical Codex then Agents compatibility roots.

    Agents aliases may be directory symlinks into the canonical root.  They are
    accepted only when their resolved target stays under that canonical root.
    """
    roots = compatible_skill_roots(skills_root, agents_skills_root, environment)
    canonical_root = roots[0]
    for root in roots:
        path = resolve_skill_path(skill_id, root, plugins_cache_root, allowed_skill_roots=(canonical_root,))
        if path is not None:
            return path
    return None


def canonicalize_installed_skill_id(skill_id, skills_root, plugins_cache_root=None):
    parts = validate_skill_id(skill_id)
    skills_root = Path(skills_root).resolve()
    cache_root = Path(plugins_cache_root).resolve() if plugins_cache_root is not None else skills_root.parent / "plugins" / "cache"
    if len(parts) == 2:
        if resolve_skill_path(skill_id, skills_root, cache_root) is None:
            raise ValueError("canonical plugin skill is not installed")
        return skill_id
    global_path = resolve_skill_path(skill_id, skills_root, cache_root)
    if global_path is not None:
        return skill_id
    canonical_ids = sorted({f"{package}:{skill_id}" for package, _ in _plugin_skill_matches(skill_id, cache_root)})
    if not canonical_ids:
        raise ValueError("skill is not installed")
    if len(canonical_ids) != 1:
        raise ValueError("unqualified plugin skill is ambiguous")
    return canonical_ids[0]

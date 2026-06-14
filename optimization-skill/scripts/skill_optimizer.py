#!/usr/bin/env python3

from __future__ import annotations

import argparse
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_CANDIDATES = [
    (
        re.compile(r"\b(open|launch)\b.*\b(browser|chrome|safari|firefox)\b", re.IGNORECASE),
        "If this browser action is repeated and deterministic, move it into the target skill's own script.",
    ),
    (
        re.compile(r"\b(open|launch)\b.*\b(unity|editor|application|app)\b", re.IGNORECASE),
        "If this repeated app-launch step is stable, move it into the target skill's own script.",
    ),
    (
        re.compile(r"\b(window|file|edit|assets|gameobject|component|tools|help)\s*>\s*[\w &./-]+", re.IGNORECASE),
        "If this menu path is stable and repeated, script it inside the target skill instead of keeping it as long instructions.",
    ),
    (
        re.compile(r"\b(click|select|focus|activate)\b.*\b(tab|button|menu|window)\b", re.IGNORECASE),
        "If the target is static and permission-safe, move the repeated UI action into the target skill's own script.",
    ),
    (
        re.compile(r"\b(wait|poll|check|verify)\b.*\b(file|folder|window|tab|log|result|script)\b", re.IGNORECASE),
        "Move repeated deterministic checks into the target skill's own script so the skill does not spend tokens re-checking them.",
    ),
]

SECTION_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
COMMAND_PATH_PATTERN = re.compile(r"(?<!\w)(?:\./|\.\./|/|plugins/|scripts/)[^\s\"'`]+?\.(?:py|sh|applescript)\b")
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")


@dataclass
class ScriptCandidate:
    line_number: int
    line_text: str
    recommendation: str


@dataclass
class DuplicateInstruction:
    line_numbers: list[int]
    line_text: str


@dataclass
class AuditResult:
    skill_dir: Path
    skill_file: Path
    repo_root: Path
    name: str
    description: str
    headings: list[str]
    section_lengths: list[tuple[str, int]]
    local_links: list[Path]
    command_paths: list[Path]
    local_link_errors: list[str]
    command_path_errors: list[str]
    warnings: list[str]
    errors: list[str]
    script_candidates: list[ScriptCandidate]
    duplicate_instructions: list[DuplicateInstruction]
    peer_skills: list[str]


@dataclass
class SkillSummary:
    skill_dir: Path
    skill_file: Path
    name: str
    description: str
    headings: list[str]
    line_count: int


def parse_args() -> argparse.Namespace:
    _parser = argparse.ArgumentParser(description="Scan skills, check whether optimization is needed, and verify optimized skills.")
    _subparsers = _parser.add_subparsers(dest="command", required=True)
    _scan_parser = _subparsers.add_parser("scan")
    _scan_parser.add_argument("skills_root", help="Path to a skills root folder that contains skill directories.")
    for _name in ("audit", "verify"):
        _command_parser = _subparsers.add_parser(_name)
        _command_parser.add_argument("skill_path", help="Path to a skill directory or its SKILL.md file.")
    return _parser.parse_args()


def resolve_skill_dir(skill_path: str) -> Path:
    _path = Path(skill_path).expanduser().resolve()
    if _path.is_file():
        return _path.parent
    return _path


def resolve_skills_root(skills_root: str) -> Path:
    return Path(skills_root).expanduser().resolve()


def find_repo_root(start_path: Path) -> Path:
    for _path in [start_path, *start_path.parents]:
        if (_path / ".git").exists() or (_path / ".agents").exists():
            return _path
    return Path.cwd()


def collect_skills(skills_root: Path) -> list[SkillSummary]:
    _skills = []
    if not skills_root.exists():
        return _skills
    for _skill_file in sorted(skills_root.rglob("SKILL.md")):
        _text = _skill_file.read_text(encoding="utf-8")
        _frontmatter, _body = split_frontmatter(_text)
        _skills.append(
            SkillSummary(
                skill_dir=_skill_file.parent,
                skill_file=_skill_file,
                name=_frontmatter.get("name", _skill_file.parent.name),
                description=_frontmatter.get("description", ""),
                headings=[_heading for _, _heading in extract_headings(_body)],
                line_count=len(_text.splitlines()),
            )
        )
    return _skills


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    _end_index = text.find("\n---\n", 4)
    if _end_index == -1:
        return {}, text
    _frontmatter_block = text[4:_end_index]
    _body = text[_end_index + 5 :]
    _frontmatter = {}
    for _line in _frontmatter_block.splitlines():
        if ":" not in _line:
            continue
        _key, _value = _line.split(":", 1)
        _frontmatter[_key.strip()] = _value.strip().strip('"').strip("'")
    return _frontmatter, _body


def extract_headings(text: str) -> list[tuple[int, str]]:
    _headings = []
    for _line_number, _line in enumerate(text.splitlines(), start=1):
        _match = SECTION_HEADING_PATTERN.match(_line)
        if _match:
            _headings.append((_line_number, _match.group(2).strip()))
    return _headings


def extract_section_lengths(lines: list[str], headings: list[tuple[int, str]]) -> list[tuple[str, int]]:
    if not headings:
        return []
    _section_lengths = []
    for _index, (_line_number, _heading) in enumerate(headings):
        _next_line = headings[_index + 1][0] if _index + 1 < len(headings) else len(lines) + 1
        _section_lengths.append((_heading, _next_line - _line_number - 1))
    return _section_lengths


def resolve_reference(raw_path: str, skill_dir: Path, repo_root: Path) -> Path | None:
    _clean_path = raw_path.split("#", 1)[0].strip()
    if not _clean_path or re.match(r"^[a-z]+://", _clean_path):
        return None
    _path = Path(_clean_path).expanduser()
    if _path.is_absolute():
        return _path
    for _candidate in (skill_dir / _path, repo_root / _path):
        if _candidate.exists():
            return _candidate.resolve()
    return (skill_dir / _path).resolve()


def extract_local_links(text: str, skill_dir: Path, repo_root: Path) -> tuple[list[Path], list[str]]:
    _paths = []
    _errors = []
    for _match in LINK_PATTERN.finditer(text):
        _resolved_path = resolve_reference(_match.group(1), skill_dir, repo_root)
        if not _resolved_path:
            continue
        _paths.append(_resolved_path)
        if not _resolved_path.exists():
            _errors.append(f"Missing referenced file: {_match.group(1)}")
    return dedupe_paths(_paths), _errors


def extract_command_paths(text: str, skill_dir: Path, repo_root: Path) -> tuple[list[Path], list[str]]:
    _paths = []
    _errors = []
    for _match in COMMAND_PATH_PATTERN.finditer(text):
        _resolved_path = resolve_reference(_match.group(0), skill_dir, repo_root)
        if not _resolved_path:
            continue
        _paths.append(_resolved_path)
        if not _resolved_path.exists():
            _errors.append(f"Missing command path: {_match.group(0)}")
    return dedupe_paths(_paths), _errors


def dedupe_paths(paths: list[Path]) -> list[Path]:
    _seen = set()
    _deduped_paths = []
    for _path in paths:
        if _path in _seen:
            continue
        _seen.add(_path)
        _deduped_paths.append(_path)
    return _deduped_paths


def find_script_candidates(text: str) -> list[ScriptCandidate]:
    _candidates = []
    for _line_number, _line in enumerate(text.splitlines(), start=1):
        _stripped_line = _line.strip()
        if "skill_optimizer.py" in _stripped_line:
            continue
        if _stripped_line.startswith("- `audit`") or _stripped_line.startswith("- `verify`") or _stripped_line.startswith("- `scan`"):
            continue
        for _pattern, _recommendation in SCRIPT_CANDIDATES:
            if not _pattern.search(_stripped_line):
                continue
            _candidates.append(ScriptCandidate(_line_number, _stripped_line, _recommendation))
            break
    return _candidates


def normalize_instruction_text(text: str) -> str:
    _text = LIST_ITEM_PATTERN.sub("", text.strip().lower().replace("`", ""))
    _text = re.sub(r"\s+", " ", _text)
    _text = re.sub(r"[^\w ]+", "", _text)
    return _text.strip()


def find_duplicate_instructions(text: str) -> list[DuplicateInstruction]:
    _instruction_map = {}
    _inside_code_block = False
    for _line_number, _line in enumerate(text.splitlines(), start=1):
        if _line.strip().startswith("```"):
            _inside_code_block = not _inside_code_block
            continue
        if _inside_code_block or not LIST_ITEM_PATTERN.match(_line):
            continue
        _normalized_text = normalize_instruction_text(_line)
        if len(_normalized_text) < 24:
            continue
        _instruction_map.setdefault(_normalized_text, []).append((_line_number, _line.strip()))
    _duplicate_instructions = []
    for _entries in _instruction_map.values():
        if len(_entries) < 2:
            continue
        _duplicate_instructions.append(DuplicateInstruction(line_numbers=[_line_number for _line_number, _ in _entries], line_text=_entries[0][1]))
    return _duplicate_instructions


def build_warnings(skill_text: str, headings: list[str], section_lengths: list[tuple[str, int]], script_candidates: list[ScriptCandidate], duplicate_instructions: list[DuplicateInstruction], command_paths: list[Path]) -> list[str]:
    _warnings = []
    _line_count = len(skill_text.splitlines())
    if _line_count > 220:
        _warnings.append(f"SKILL.md is {_line_count} lines. Move details into scripts or references if it keeps growing.")
    if not any(_heading in headings for _heading in ("Trigger", "Scope")):
        _warnings.append("Add a short Trigger or Scope section so users can tell when the skill should be used.")
    if not any(_heading in headings for _heading in ("Workflow", "Required Workflow")):
        _warnings.append("Add a Workflow section so the skill has a predictable execution order.")
    if "Guardrails" not in headings:
        _warnings.append("Add a Guardrails section so optimization does not change the skill's behavior by accident.")
    if not any(_heading in headings for _heading in ("Examples", "Natural-Language Examples")):
        _warnings.append("Add examples so users can tell what the skill can do without reading the whole file.")
    for _heading, _length in section_lengths:
        if _length > 45:
            _warnings.append(f"Section `{_heading}` is {_length} lines. Consider moving repeated detail into scripts or references.")
    if duplicate_instructions:
        _warnings.append(f"{len(duplicate_instructions)} duplicate or overlapping instruction lines were found. Merge repeated requirements into one clearer rule.")
    if script_candidates and not command_paths:
        _warnings.append("The skill contains static step candidates but no script paths were referenced.")
    if command_paths and "Verification" not in headings:
        _warnings.append("The skill references helper commands but does not have a Verification section.")
    return _warnings


def audit_skill(skill_dir: Path) -> AuditResult:
    _skill_file = skill_dir / "SKILL.md"
    _repo_root = find_repo_root(skill_dir)
    _skills_root = skill_dir.parent
    _errors = []
    if not _skill_file.exists():
        return AuditResult(
            skill_dir=skill_dir,
            skill_file=_skill_file,
            repo_root=_repo_root,
            name="",
            description="",
            headings=[],
            section_lengths=[],
            local_links=[],
            command_paths=[],
            local_link_errors=[],
            command_path_errors=[],
            warnings=[],
            errors=[f"Missing SKILL.md at {_skill_file}"],
            script_candidates=[],
            duplicate_instructions=[],
            peer_skills=[],
        )
    _skill_text = _skill_file.read_text(encoding="utf-8")
    _frontmatter, _body = split_frontmatter(_skill_text)
    _name = _frontmatter.get("name", "")
    _description = _frontmatter.get("description", "")
    if not _name:
        _errors.append("Frontmatter is missing `name`.")
    if not _description:
        _errors.append("Frontmatter is missing `description`.")
    _heading_pairs = extract_headings(_body)
    _headings = [_heading for _, _heading in _heading_pairs]
    _section_lengths = extract_section_lengths(_body.splitlines(), _heading_pairs)
    _local_links, _local_link_errors = extract_local_links(_skill_text, skill_dir, _repo_root)
    _command_paths, _command_path_errors = extract_command_paths(_skill_text, skill_dir, _repo_root)
    _script_candidates = find_script_candidates(_skill_text)
    _duplicate_instructions = find_duplicate_instructions(_skill_text)
    _warnings = build_warnings(_skill_text, _headings, _section_lengths, _script_candidates, _duplicate_instructions, _command_paths)
    _peer_skills = [str(_skill.skill_dir.name) for _skill in collect_skills(_skills_root) if _skill.skill_dir != skill_dir]
    return AuditResult(
        skill_dir=skill_dir,
        skill_file=_skill_file,
        repo_root=_repo_root,
        name=_name,
        description=_description,
        headings=_headings,
        section_lengths=_section_lengths,
        local_links=_local_links,
        command_paths=_command_paths,
        local_link_errors=_local_link_errors,
        command_path_errors=_command_path_errors,
        warnings=_warnings,
        errors=_errors,
        script_candidates=_script_candidates,
        duplicate_instructions=_duplicate_instructions,
        peer_skills=_peer_skills,
    )


def validate_script(script_path: Path) -> list[str]:
    _errors = []
    if script_path.suffix == ".py":
        try:
            py_compile.compile(str(script_path), doraise=True)
        except py_compile.PyCompileError as _error:
            _errors.append(f"Python syntax check failed for {script_path}: {_error.msg}")
    elif script_path.suffix == ".sh":
        _result = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
        if _result.returncode != 0:
            _errors.append(f"Shell syntax check failed for {script_path}: {_result.stderr.strip() or _result.stdout.strip()}")
    elif script_path.suffix == ".applescript":
        _result = subprocess.run(["osacompile", "-o", "/tmp/skill_optimizer_compile.scpt", str(script_path)], capture_output=True, text=True)
        if _result.returncode != 0:
            _errors.append(f"AppleScript compile failed for {script_path}: {_result.stderr.strip() or _result.stdout.strip()}")
    return _errors


def verify_skill(audit_result: AuditResult) -> list[str]:
    _errors = list(audit_result.errors)
    _errors.extend(audit_result.local_link_errors)
    _errors.extend(audit_result.command_path_errors)
    for _script_dir in (audit_result.skill_dir / "scripts",):
        if not _script_dir.exists():
            continue
        for _script_path in sorted(_script_dir.rglob("*")):
            if _script_path.is_dir():
                continue
            if _script_path.suffix not in {".py", ".sh", ".applescript"}:
                continue
            _errors.extend(validate_script(_script_path))
    for _command_path in audit_result.command_paths:
        if _command_path.exists():
            _errors.extend(validate_script(_command_path))
    return dedupe_strings(_errors)


def dedupe_strings(values: list[str]) -> list[str]:
    _seen = set()
    _deduped = []
    for _value in values:
        if _value in _seen:
            continue
        _seen.add(_value)
        _deduped.append(_value)
    return _deduped


def format_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def print_report(audit_result: AuditResult) -> None:
    _optimization_reasons = [*audit_result.warnings]
    if audit_result.script_candidates:
        _optimization_reasons.append(f"{len(audit_result.script_candidates)} repeated deterministic step candidates were found.")
    if audit_result.duplicate_instructions:
        _optimization_reasons.append(f"{len(audit_result.duplicate_instructions)} duplicate instruction groups were found.")
    print("Skill")
    print(f"- file: {audit_result.skill_file}")
    print(f"- name: {audit_result.name or '[missing]'}")
    print(f"- description: {audit_result.description or '[missing]'}")
    print(f"- headings: {', '.join(audit_result.headings) if audit_result.headings else '[none]'}")
    print(f"- local references: {len(audit_result.local_links)}")
    print(f"- command paths: {len(audit_result.command_paths)}")
    print(f"- peer skills: {', '.join(audit_result.peer_skills) if audit_result.peer_skills else '[none]'}")
    print("")
    print("Optimization Check")
    print(f"- recommended: {'yes' if _optimization_reasons else 'no'}")
    if _optimization_reasons:
        for _reason in _optimization_reasons:
            print(f"- reason: {_reason}")
    else:
        print("- reason: no meaningful optimization issue was detected")
    print("")
    print("Suggested Summary")
    print(f"- Use for: {audit_result.description or 'Add a frontmatter description so the skill purpose is obvious.'}")
    if audit_result.command_paths:
        print(f"- Deterministic helpers: {', '.join(_path.name for _path in audit_result.command_paths)}")
    else:
        print("- Deterministic helpers: none referenced yet")
    if audit_result.script_candidates:
        print(f"- Static step candidates: {len(audit_result.script_candidates)}")
    else:
        print("- Static step candidates: none detected")
    if audit_result.duplicate_instructions:
        print(f"- Duplicate instruction groups: {len(audit_result.duplicate_instructions)}")
    else:
        print("- Duplicate instruction groups: none detected")
    if audit_result.warnings:
        print("")
        print("Warnings")
        for _warning in audit_result.warnings:
            print(f"- {_warning}")
    if audit_result.script_candidates:
        print("")
        print("Script Candidates")
        for _candidate in audit_result.script_candidates:
            print(f"- line {_candidate.line_number}: {_candidate.line_text}")
            print(f"  recommendation: {_candidate.recommendation}")
    if audit_result.duplicate_instructions:
        print("")
        print("Duplicate Instructions")
        for _duplicate_instruction in audit_result.duplicate_instructions:
            print(f"- lines {', '.join(str(_line_number) for _line_number in _duplicate_instruction.line_numbers)}: {_duplicate_instruction.line_text}")
    if audit_result.local_link_errors or audit_result.command_path_errors or audit_result.errors:
        print("")
        print("Errors")
        for _error in [*audit_result.errors, *audit_result.local_link_errors, *audit_result.command_path_errors]:
            print(f"- {_error}")


def print_skill_scan(skills: list[SkillSummary], skills_root: Path) -> int:
    print("Skills")
    print(f"- root: {skills_root}")
    print(f"- count: {len(skills)}")
    if not skills:
        print("")
        print("Errors")
        print("- No skills were found.")
        return 1
    print("")
    for _skill in skills:
        print(f"- {_skill.name}: {format_relative(_skill.skill_dir, skills_root)}")
        print(f"  description: {_skill.description or '[missing]'}")
        print(f"  headings: {', '.join(_skill.headings) if _skill.headings else '[none]'}")
        print(f"  lines: {_skill.line_count}")
    return 0


def main() -> int:
    _args = parse_args()
    if _args.command == "scan":
        _skills_root = resolve_skills_root(_args.skills_root)
        return print_skill_scan(collect_skills(_skills_root), _skills_root)
    _skill_dir = resolve_skill_dir(_args.skill_path)
    _audit_result = audit_skill(_skill_dir)
    print_report(_audit_result)
    if _args.command == "audit":
        return 1 if _audit_result.errors or _audit_result.local_link_errors or _audit_result.command_path_errors else 0
    _verification_errors = verify_skill(_audit_result)
    if _verification_errors:
        print("")
        print("Verification Failed")
        for _error in _verification_errors:
            print(f"- {_error}")
        return 1
    print("")
    print("Verification Passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

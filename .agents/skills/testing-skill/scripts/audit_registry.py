"""Check the project test registry against maintained test files."""

import argparse
import json
import re
from pathlib import Path, PurePosixPath


REGISTRY_RELATIVE_PATH = Path(".agents") / "skills" / "testing-skill" / "references" / "test-registry.json"
PROJECT_TESTS_RELATIVE_PATH = Path(".agents") / "skills" / "testing-skill" / "tests"
PURPOSE_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def discovered_tests(project_root):
    tests = set()
    for skill_dir in project_root.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
            tests.update(path.relative_to(project_root).as_posix() for path in (skill_dir / "tests").rglob("test_*.py"))
    tests.update(path.relative_to(project_root).as_posix() for path in (project_root / PROJECT_TESTS_RELATIVE_PATH).rglob("test_*.py"))
    return tests


def audit_registry(project_root, registry):
    issues = []
    skill_file = project_root / ".agents" / "skills" / "testing-skill" / "SKILL.md"
    try:
        skill_text = skill_file.read_text(encoding="utf-8")
    except OSError:
        issues.append("testing-skill/SKILL.md is missing or unreadable")
    else:
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", skill_text, re.DOTALL)
        names = re.findall(r"^name:\s*(\S+)\s*$", frontmatter.group(1), re.MULTILINE) if frontmatter else []
        if names != ["testing-skill"]:
            issues.append("testing-skill/SKILL.md requires frontmatter name: testing-skill")
    if not isinstance(registry, dict) or registry.get("schema_version") != 1 or not isinstance(registry.get("tests"), list):
        return issues + ["registry must contain schema_version 1 and a tests list"]

    paths = set()
    purposes = set()
    goals = set()
    for index, entry in enumerate(registry["tests"], start=1):
        if not isinstance(entry, dict):
            issues.append(f"entry {index}: expected an object")
            continue
        path_text = entry.get("path")
        purpose = entry.get("purpose")
        goal = entry.get("goal")
        level = entry.get("level")
        runner = entry.get("runner")
        owner = entry.get("owner")
        if not isinstance(path_text, str) or not path_text:
            issues.append(f"entry {index}: missing path")
            continue
        path = PurePosixPath(path_text)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != path_text or "\\" in path_text:
            issues.append(f"entry {index}: path must be a normalized repository-relative path: {path_text}")
            continue
        if path_text in paths:
            issues.append(f"duplicate path: {path_text}")
        paths.add(path_text)
        if not (project_root.joinpath(*path.parts)).is_file():
            issues.append(f"missing test file: {path_text}")
        if not isinstance(purpose, str) or not PURPOSE_PATTERN.fullmatch(purpose):
            issues.append(f"entry {index}: invalid purpose for {path_text}")
        elif purpose in purposes:
            issues.append(f"duplicate purpose: {purpose}")
        else:
            purposes.add(purpose)
        if not isinstance(goal, str) or not goal.strip():
            issues.append(f"entry {index}: missing goal for {path_text}")
        elif re.sub(r"\W+", " ", goal.casefold()).strip() in goals:
            issues.append(f"duplicate goal: {goal}")
        else:
            goals.add(re.sub(r"\W+", " ", goal.casefold()).strip())
        if type(level) is not int or level not in (1, 2, 3, 4):
            issues.append(f"entry {index}: invalid level for {path_text}")
        if not isinstance(runner, str) or not runner.strip():
            issues.append(f"entry {index}: missing runner for {path_text}")
        if not isinstance(owner, str) or not owner.strip():
            issues.append(f"entry {index}: missing owner for {path_text}")
        native_skill = len(path.parts) >= 3 and path.parts[1] == "tests" and (project_root / path.parts[0] / "SKILL.md").is_file()
        local_skill = tuple(path.parts[:4]) == (".agents", "skills", "testing-skill", "tests")
        if native_skill or local_skill:
            expected_owner = path.parts[0] if native_skill else "testing-skill"
            if owner != expected_owner or runner != "unittest":
                issues.append(f"entry {index}: Skill-owned test requires owner {expected_owner} and runner unittest: {path_text}")

    for path in sorted(discovered_tests(project_root) - paths):
        issues.append(f"unregistered test file: {path}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    try:
        registry = json.loads((project_root / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.exit(2, f"registry could not be read: {error}\n")
    issues = audit_registry(project_root, registry)
    if issues:
        parser.exit(1, "registry audit failed:\n" + "\n".join(f"- {issue}" for issue in issues) + "\n")
    print(f"registry audit passed: {len(registry['tests'])} test scripts, distinct purposes and goals")
    print(json.dumps({"checks": len(registry["tests"]), "status": "passed"}, separators=(",", ":")))


if __name__ == "__main__":
    main()

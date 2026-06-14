#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


SCENARIOS = {
    "text": {
        "expected_route": ["workflow-skill", "verify-skill"],
        "target_terms": ["content", "format"],
        "requires_code_order": False,
    },
    "code": {
        "expected_route": ["workflow-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["behavior", "input", "output"],
        "requires_code_order": True,
    },
    "python": {
        "expected_route": ["workflow-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["python", "runnable"],
        "requires_code_order": True,
    },
    "unity-csharp": {
        "expected_route": ["workflow-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["unity", "behavior"],
        "requires_code_order": True,
    },
    "prompt": {
        "expected_route": ["workflow-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["prompt", "output shape"],
        "requires_code_order": True,
    },
    "ui": {
        "expected_route": ["workflow-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["viewport", "visual"],
        "requires_code_order": True,
    },
    "image": {
        "expected_route": ["workflow-skill", "test-skill", "verify-skill"],
        "target_terms": ["image", "visual"],
        "requires_code_order": False,
    },
    "document-pdf": {
        "expected_route": ["workflow-skill", "test-skill", "verify-skill"],
        "target_terms": ["file path", "rendered"],
        "requires_code_order": False,
    },
    "skill-edit": {
        "expected_route": ["workflow-skill", "management-skill", "code-skill", "test-skill", "verify-skill", "management-skill"],
        "target_terms": ["frontmatter", "sync"],
        "requires_code_order": True,
    },
    "optimization": {
        "expected_route": ["workflow-skill", "optimization-skill", "code-skill", "test-skill", "verify-skill"],
        "target_terms": ["reusable", "script"],
        "requires_code_order": True,
    },
    "github-sync": {
        "expected_route": ["workflow-skill", "management-skill", "verify-skill"],
        "target_terms": ["public-safety", "hash"],
        "requires_code_order": False,
    },
    "codex-switch": {
        "expected_route": ["workflow-skill", "management-skill", "verify-skill"],
        "target_terms": ["privacy", "profile"],
        "requires_code_order": False,
    },
    "mixed": {
        "expected_route": ["workflow-skill", "relevant production skill(s)", "test-skill", "verify-skill"],
        "target_terms": ["per-artifact", "unresolved"],
        "requires_code_order": False,
    },
}


REQUIRED_SKILL_TEXT = [
    "Task slices",
    "Artifacts",
    "Pass targets",
    "Skill route",
    "Stop condition",
    "workflow-skill -> code-skill -> test-skill -> verify-skill -> goal check",
    "If any pass target is not met",
    "Do not stop because the method was attempted",
    "Input",
    "Used",
    "Output",
    "Why Pass",
]


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_frontmatter(skill_text):
    match = re.match(r"^---\n(.*?)\n---\n", skill_text, flags=re.DOTALL)
    if not match:
        raise ValueError("SKILL.md missing YAML frontmatter")
    fields = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            raise ValueError(f"invalid frontmatter line: {raw_line}")
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def parse_route_table(matrix_text):
    routes = {}
    for raw_line in matrix_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Scenario"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 5:
            continue
        scenario, use_when, goal_target, skill_route, evidence = parts[:5]
        routes[scenario] = {
            "use_when": use_when,
            "goal_target": goal_target,
            "route": [part.strip() for part in skill_route.split("->")],
            "evidence": evidence,
        }
    return routes


def ordered(route, ordered_items):
    indexes = []
    for item in ordered_items:
        if item not in route:
            return False
        indexes.append(route.index(item))
    return indexes == sorted(indexes)


def validate(skill_dir):
    skill_path = skill_dir / "SKILL.md"
    matrix_path = skill_dir / "references" / "routing-matrix.md"
    script_path = skill_dir / "scripts" / "validate_workflow_skill.py"
    for required_path in (skill_path, matrix_path, script_path):
        if not required_path.exists():
            raise ValueError(f"missing required file: {required_path}")

    skill_text = read_text(skill_path)
    matrix_text = read_text(matrix_path)
    metadata = parse_frontmatter(skill_text)
    if metadata.get("name") != "workflow-skill":
        raise ValueError("frontmatter name must be workflow-skill")
    if set(metadata) != {"name", "description"}:
        raise ValueError(f"frontmatter must only contain name and description, got {sorted(metadata)}")

    missing_text = [text for text in REQUIRED_SKILL_TEXT if text not in skill_text]
    if missing_text:
        raise ValueError("SKILL.md missing required workflow text: " + ", ".join(missing_text))

    routes = parse_route_table(matrix_text)
    results = []
    failures = []
    for scenario, expected in SCENARIOS.items():
        row = routes.get(scenario)
        if not row:
            failures.append(f"{scenario}: missing routing matrix row")
            continue
        route = row["route"]
        scenario_failures = []
        if route != expected["expected_route"]:
            scenario_failures.append(f"route {route} != expected {expected['expected_route']}")
        if route[0] != "workflow-skill":
            scenario_failures.append("route does not start with workflow-skill")
        if expected["requires_code_order"] and not ordered(route, ["code-skill", "test-skill", "verify-skill"]):
            scenario_failures.append("code/test/verify order is wrong")
        if "test-skill" in route and "verify-skill" in route and not ordered(route, ["test-skill", "verify-skill"]):
            scenario_failures.append("test-skill must run before verify-skill")
        lower_goal = row["goal_target"].lower()
        for target_term in expected["target_terms"]:
            if target_term not in lower_goal:
                scenario_failures.append(f"goal target missing term: {target_term}")
        if any(word in row["evidence"].strip().lower() for word in ("ok only", "pass only")):
            scenario_failures.append("evidence appears to allow bare status output")
        results.append({
            "scenario": scenario,
            "route": route,
            "goal_target": row["goal_target"],
            "evidence": row["evidence"],
            "status": "pass" if not scenario_failures else "fail",
            "failures": scenario_failures,
        })
        failures.extend(f"{scenario}: {failure}" for failure in scenario_failures)

    return {
        "skill_dir": str(skill_dir),
        "checked_files": [str(skill_path), str(matrix_path), str(script_path)],
        "scenario_count": len(SCENARIOS),
        "passed": len([result for result in results if result["status"] == "pass"]),
        "failed": len([result for result in results if result["status"] == "fail"]),
        "results": results,
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate workflow-skill routing and completion contract.")
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    result = validate(Path(args.skill_dir).resolve())
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"workflow-skill scenarios: {result['passed']}/{result['scenario_count']} passed")
    for item in result["results"]:
        print(f"- {item['scenario']}: {item['status']} -> {' -> '.join(item['route'])}")
    if result["failures"]:
        print("Failures:", file=sys.stderr)
        for failure in result["failures"]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

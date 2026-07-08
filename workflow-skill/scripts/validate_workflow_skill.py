#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


SCENARIOS = {
    "fast-path-simple": {
        "expected_route": ["workflow-skill"],
        "target_terms": ["direct action", "minimal local confirmation", "no formal verification"],
        "requires_code_order": False,
    },
    "text": {
        "expected_route": ["workflow-skill", "verify-skill"],
        "target_terms": ["content", "format"],
        "requires_code_order": False,
    },
    "code": {
        "expected_route": ["workflow-skill", "code-skill", "verify-skill"],
        "target_terms": ["behavior", "input", "output"],
        "requires_code_order": True,
    },
    "python": {
        "expected_route": ["workflow-skill", "code-skill", "verify-skill"],
        "target_terms": ["python", "runnable"],
        "requires_code_order": True,
    },
    "unity-csharp": {
        "expected_route": ["workflow-skill", "code-skill", "verify-skill"],
        "target_terms": ["unity", "behavior"],
        "requires_code_order": True,
    },
    "prompt": {
        "expected_route": ["workflow-skill", "verify-skill"],
        "target_terms": ["prompt", "general rules"],
        "requires_code_order": False,
    },
    "ui": {
        "expected_route": ["workflow-skill", "relevant production skill(s)", "verify-skill"],
        "target_terms": ["viewport", "visual"],
        "requires_code_order": False,
    },
    "image": {
        "expected_route": ["workflow-skill", "internal image-generation route when ChatGPT-in-Chrome generation is expected or useful", "relevant production skill(s)", "verify-skill"],
        "target_terms": ["image type", "transparency", "platform support"],
        "requires_code_order": False,
    },
    "document-pdf": {
        "expected_route": ["workflow-skill", "verify-skill"],
        "target_terms": ["file path", "rendered"],
        "requires_code_order": False,
    },
    "skill-edit": {
        "expected_route": ["workflow-skill", "management-skill", "code-skill", "verify-skill", "management-skill"],
        "target_terms": ["frontmatter", "sync"],
        "requires_code_order": True,
    },
    "optimization": {
        "expected_route": ["workflow-skill", "optimization-skill", "code-skill", "verify-skill"],
        "target_terms": ["reusable", "same-behavior"],
        "requires_code_order": True,
    },
    "management-github": {
        "expected_route": ["workflow-skill", "management-skill", "verify-skill"],
        "target_terms": ["public-safety", "hash"],
        "requires_code_order": False,
    },
    "management-profile": {
        "expected_route": ["workflow-skill", "management-skill", "verify-skill"],
        "target_terms": ["privacy", "profile"],
        "requires_code_order": False,
    },
    "mixed": {
        "expected_route": ["workflow-skill", "relevant production skill(s)", "verify-skill"],
        "target_terms": ["per-artifact", "unresolved"],
        "requires_code_order": False,
    },
}


REQUIRED_SKILL_TEXT = [
    "Always-First Rule",
    "Simple Task Fast Path",
    "do not route through `verify-skill`",
    "Do not append daily-log/wiki memory",
    "Post-Pass Non-Blocking Closeout",
    "After the user-facing task passes verification, return the result to the user immediately",
    "log/wiki/DailyLog/Obsidian/Markdown closeout drafting and file edits are Spark-default execution",
    "Newest/current user-selected reasoning models are reserved",
    "prompt/instruction authoring, updates, review, or optimization",
    "For standalone prompt/instruction work",
    "State the general rule once",
    "Other skills are executors",
    "Start Diagram Rule",
    "Before task action",
    "references/start-diagram-template.md",
    "compact direct-route diagram",
    "task-specific Mermaid start diagram",
    "Task slices",
    "Artifacts",
    "Pass targets",
    "Skill route",
    "Stop condition",
    "workflow-skill -> code-skill -> verify-skill -> goal check",
    "Optimization Gate",
    "repeated at least three times",
    "If any pass target is not met",
    "Do not stop because the method was attempted",
    "Input",
    "Used",
    "Output",
    "Why Pass",
]


TRACE_SCENARIOS = [
    "fast-path-simple",
    "text",
    "prompt",
    "code",
    "python",
    "skill-edit",
    "optimization",
    "management-github",
    "mixed",
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


def build_execution_trace(scenario, route):
    trace = [{
        "step": 1,
        "scenario": scenario,
        "skill": "workflow-skill",
        "role": "controller",
        "event": "start",
        "started_by": None,
    }]
    for skill in route[1:]:
        trace.append({
            "step": len(trace) + 1,
            "scenario": scenario,
            "skill": skill,
            "role": "executor",
            "event": "execute",
            "started_by": "workflow-skill",
        })
    return trace


def validate_execution_trace(trace):
    failures = []
    if not trace:
        return ["trace is empty"]
    first_event = trace[0]
    if first_event.get("skill") != "workflow-skill" or first_event.get("role") != "controller":
        failures.append("first event must be workflow-skill controller start")
    for event in trace[1:]:
        if event.get("skill") == "workflow-skill":
            continue
        if event.get("role") != "executor":
            failures.append(f"{event.get('skill')}: non-workflow skill must be an executor")
        if event.get("started_by") != "workflow-skill":
            failures.append(f"{event.get('skill')}: executor must be started by workflow-skill")
    return failures


def validate(skill_dir):
    skill_path = skill_dir / "SKILL.md"
    matrix_path = skill_dir / "references" / "routing-matrix.md"
    start_diagram_path = skill_dir / "references" / "start-diagram-template.md"
    image_generation_path = skill_dir / "references" / "image-generation.md"
    script_path = skill_dir / "scripts" / "validate_workflow_skill.py"
    for required_path in (skill_path, matrix_path, start_diagram_path, image_generation_path, script_path):
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
    start_diagram_text = read_text(start_diagram_path)
    for required_text in ("Lightweight Direct Route", "Explicit Workflow Route", "Skill Edit And Push Route", "Code Change Route"):
        if required_text not in start_diagram_text:
            raise ValueError(f"start diagram template missing required section: {required_text}")

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
        if expected["requires_code_order"] and not ordered(route, ["code-skill", "verify-skill"]):
            scenario_failures.append("code/verify order is wrong")
        if "test-skill" in route:
            scenario_failures.append("test-skill has been merged into verify-skill and must not appear in routes")
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

    trace_results = []
    for scenario in TRACE_SCENARIOS:
        row = routes.get(scenario)
        if not row:
            failures.append(f"{scenario}: missing route for execution trace")
            continue
        trace = build_execution_trace(scenario, row["route"])
        trace_failures = validate_execution_trace(trace)
        trace_results.append({
            "scenario": scenario,
            "status": "pass" if not trace_failures else "fail",
            "first_skill": trace[0]["skill"] if trace else "",
            "executors": [event["skill"] for event in trace[1:]],
            "trace": trace,
            "failures": trace_failures,
        })
        failures.extend(f"{scenario} trace: {failure}" for failure in trace_failures)

    return {
        "skill_dir": str(skill_dir),
        "checked_files": [str(skill_path), str(matrix_path), str(image_generation_path), str(script_path)],
        "scenario_count": len(SCENARIOS),
        "passed": len([result for result in results if result["status"] == "pass"]),
        "failed": len([result for result in results if result["status"] == "fail"]),
        "results": results,
        "trace_results": trace_results,
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
    print(f"workflow-skill execution traces: {len([item for item in result['trace_results'] if item['status'] == 'pass'])}/{len(result['trace_results'])} passed")
    for item in result["trace_results"]:
        print(f"- trace {item['scenario']}: {item['status']} -> first={item['first_skill']}; executors={', '.join(item['executors'])}")
    if result["failures"]:
        print("Failures:", file=sys.stderr)
        for failure in result["failures"]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

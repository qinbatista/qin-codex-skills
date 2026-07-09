#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


SCENARIOS = {
    "fast-path-simple": {
        "expected_route": ["workflow-skill"],
        "target_terms": ["direct action", "minimal local confirmation", "no formal verification", "mandatory comprehensive ending workflow subagent"],
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
    "Make the task-size decision before exploration",
    "change value(s)",
    "do not read project memory, scan unrelated files, run broad searches",
    "post-goal validation, verification, tests, documents, sync/status proof, and wiki/log closeout",
    "Simple Task Fast Path",
    "do not route through `verify-skill`",
    "do not read project memory, broad instructions, or unrelated files before the direct action",
    "smallest action-done confirmation",
    "Always delegate records, docs, Markdown/wiki/log updates, tests, verification, extended checks, or no-op closeout confirmation through `Ending Workflow` after the answer path is clear",
    "keep that ending pass task-local and related-information focused",
    "show the compact direct-route diagram and one-line model route before the direct action",
    "return the user-facing result immediately after the direct action and minimal confirmation",
    "Ending Workflow",
    "Ending Workflow Tool-Call Gate",
    "Ending Workflow delegated",
    "Ending Workflow blocked: no subagent tool",
    "The only allowed ending statuses",
    "Do not use `Ending Workflow deferred`, `Ending Workflow not needed`, or silent skip statuses",
    "must call the available subagent/delegation tool",
    "Ending Workflow Related Update Scope",
    "task-local, proportional, and document-related",
    "check the relevant log/history and directly related docs/wiki/Obsidian/Markdown pages",
    "update stale or missing related information",
    "Do not set fixed time limits in the skill",
    "Do not turn ending into broad testing, whole-repo archaeology, whole-vault scans, or unrelated cleanup",
    "Do not bundle previous tasks into the current `Ending Workflow`",
    "re-audit the whole project, or scan the whole vault/repo",
    "Related Closeout Inventory",
    "a no-op from the changed file alone is invalid",
    "No-op is allowed only after the worker reports the checked sources and a per-source reason",
    "No-op is forbidden for a user correction, repeated failure, global skill change, project contract, schema, mock API, fixture, public output shape, or API/documentation behavior change",
    "If the worker cannot inspect the related information",
    "Do not report no-op from the changed file alone",
    "Final response is allowed after the required background ending workers are dispatched",
    "hard pre-final gate",
    "A plan, queue note, intention, or written promise is not delegation",
    "Record every worker id, name, or tool-return handle immediately",
    "Do not wait for every ending worker to complete before final response",
    "report blocked closeout with remaining items",
    "checked sources and per-source reasons",
    "Let ending workers run in the background",
    "Every final response after task work must report visible background ending dispatch states for each worker",
    "Ending Workflow delegated: <worker-id-or-name> blocked",
    "A no-op final state must include a concise checked-source inventory summary",
    "a blocked state must include remaining items",
    "Do not send a final response with only an intended, planned, queued, or silent ending",
    "This applies no matter whether the task is fast-path simple, lightweight, or explicit workflow",
    "Main Goal Done Gate",
    "Ending Workflow Fan-Out",
    "Parallel Ending Workflow Dispatch",
    "same task-local `Ending Workflow` task",
    "post-goal validation, verification, local mini tests, real tests, docs, wiki, Obsidian, reports, or sync/status proof",
    "Use multiple purpose-specific Ending Workflow subagents when the task has distinct closeout purposes",
    "spawn independent ending workers in parallel before returning",
    "The user does not wait for every ending worker to finish unless they explicitly ask to wait",
    "Sequential one-by-one ending delegation is a workflow failure",
    "local mini test",
    "post-goal remote status/hash proof",
    "Any task after the major goal is done must be assigned here instead of done in the main task",
    "the main agent must not run post-goal validation",
    "For project-specific work, it must update the related project memory page",
    "Projects/<Project>/index.md",
    "When the main goal is done",
    "Main Goal Done Gate",
    "Ending Workflow Fan-Out",
    "If the `Ending Workflow` subagent later finds a real failure",
    "log/wiki/DailyLog/Obsidian/Markdown closeout drafting and file edits are Spark-default execution",
    "Workflow with models",
    "Hard model-route gate",
    "if no user-visible `Workflow with models` numbered list has been shown",
    "Each step label must include the model in parentheses",
    "best available workflow model",
    "best available verification model",
    "gpt-5.3-codex-spark",
    "Protected Spark fallback",
    "Model switch: Spark -> GPT-5.5 light",
    "gpt-5.5",
    "Spark is unreachable or limited",
    "The workflow creation, task decomposition, target-map writing, route selection, ambiguity/risk decisions, and final route judgment phases always use the best available workflow/reasoning model by default",
    "Verification judgment always uses the best available verification/reasoning model by default",
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
    "If an `Ending Workflow` local mini test, real test, or verification result fails",
    "If a lightweight or fast-path task starts expanding into broad verification",
    "If the model route was omitted or a Spark-required execution phase used the active reasoning model",
    "Do not stop because the method was attempted",
    "Input",
    "Used",
    "Output",
    "Why Pass",
]


REQUIRED_AGENT_TEXT = ["Ending Workflow Tool-Call Gate", "actually call one or more", "purpose-specific task-local Ending Workflow subagents", "record Ending Workflow delegated: <worker-id-or-name>", "Do not wait for every ending worker to complete before final response", "A plan, queue note, intention, or written promise is not delegation", "Ending Workflow blocked: no subagent tool", "Ending Workflow handles every post-goal item", "local mini test", "local real testing", "validation/verification", "post-goal remote", "Ending Workflow Fan-Out uses multiple purpose-specific Ending Workflow subagents", "Parallel Ending Workflow Dispatch", "spawn all independent Ending Workflow subagents in parallel before the final response", "Sequential one-by-one ending delegation is a workflow failure", "The user does not wait for all background subagents to finish", "Ending Workflow Related Update Scope is task-local, proportional, and document-related", "check the relevant log/history and directly related docs/wiki/Obsidian/Markdown pages", "update stale or missing related information", "Do not set fixed time limits in the skill", "Do not bundle previous tasks", "scan the whole repo", "scan the whole vault", "Related Closeout Inventory", "inspect related docs/wiki/Obsidian/Markdown/log sources", "no-op only with checked sources plus per-source reasons", "report blocked with checked sources and remaining items"]


REQUIRED_MATRIX_TEXT = ["Ending Workflow Tool-Call Gate", "dispatch evidence", "worker id/name", "purpose", "running status", "A plan, queue note, intention, or written promise is not delegation", "Main Goal Done Gate", "local mini tests", "validation/verification", "post-goal remote status/hash proof", "Ending Workflow Fan-Out", "purpose-specific Ending Workflow subagents", "Parallel Ending Workflow Dispatch", "parallel before the final response", "The user does not wait for all background subagents to finish", "Ending Workflow Related Update Scope is proportional and document-related", "check relevant log/history and directly related docs/wiki/Obsidian/Markdown pages", "update stale or missing related information", "Do not set fixed time limits in the skill", "Do not bundle previous tasks", "scan the whole repo", "scan the whole vault", "Related Closeout Inventory", "checked sources with per-source reasons"]


FORBIDDEN_SKILL_TEXT = ["Then decide and state the ending status: `Ending Workflow queued`, `Ending Workflow deferred`, or `Ending Workflow not needed`.", "If no background route is available and closeout is optional, defer it and say it was deferred instead of silently skipping it.", "state Ending Workflow queued, deferred, or not needed", "treat extended same-behavior checks as background unless", "A worker may inspect the closeout scope and report that no durable file updates are needed, but the worker must still be started", "scan the whole repo/vault by default", "Fast-path/simple tasks get a 60-120 second ending budget", "Explicit/comprehensive tasks normally get a 3-5 minute ending budget", "wait only within the `Ending Workflow Budget`", "keep the foreground mini verification in the main path", "real tests beyond that mini check", "real tests beyond the foreground mini verification", "The main task must not skip reasonable checking just because a comprehensive ending subagent exists", "waited completion/no-op/reopened status", "Wait for every ending worker to complete"]


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
    agent_yaml_path = skill_dir / "agents" / "openai.yaml"
    for required_path in (skill_path, matrix_path, start_diagram_path, image_generation_path, script_path, agent_yaml_path):
        if not required_path.exists():
            raise ValueError(f"missing required file: {required_path}")

    skill_text = read_text(skill_path)
    matrix_text = read_text(matrix_path)
    agent_text = read_text(agent_yaml_path)
    metadata = parse_frontmatter(skill_text)
    if metadata.get("name") != "workflow-skill":
        raise ValueError("frontmatter name must be workflow-skill")
    if set(metadata) != {"name", "description"}:
        raise ValueError(f"frontmatter must only contain name and description, got {sorted(metadata)}")

    missing_text = [text for text in REQUIRED_SKILL_TEXT if text not in skill_text]
    if missing_text:
        raise ValueError("SKILL.md missing required workflow text: " + ", ".join(missing_text))
    forbidden_text = [text for text in FORBIDDEN_SKILL_TEXT if text in skill_text]
    if forbidden_text:
        raise ValueError("SKILL.md contains forbidden weak ending-workflow text: " + ", ".join(forbidden_text))
    missing_agent_text = [text for text in REQUIRED_AGENT_TEXT if text not in agent_text]
    if missing_agent_text:
        raise ValueError("agents/openai.yaml missing required ending tool-call text: " + ", ".join(missing_agent_text))
    missing_matrix_text = [text for text in REQUIRED_MATRIX_TEXT if text not in matrix_text]
    if missing_matrix_text:
        raise ValueError("routing-matrix.md missing required ending tool-call text: " + ", ".join(missing_matrix_text))
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
        "checked_files": [str(skill_path), str(matrix_path), str(image_generation_path), str(script_path), str(agent_yaml_path)],
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

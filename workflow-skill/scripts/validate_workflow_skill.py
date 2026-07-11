#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

TASK_ANALYZE_SCRIPTS = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts"
sys.path.insert(0, str(TASK_ANALYZE_SCRIPTS))
from validate_graduated_routes import validate_fixture
from skill_resolver import resolve_skill_path

import importlib.util

try:
    from routing_policy import (
        EXECUTION_DOMAINS,
        expected_owner_skill,
        execution_domain_is_active,
        is_code_execution_domain,
        resolve_execution_domain,
        is_tiny_spark_profile,
        validate_execution_domain_registry,
    )
except ModuleNotFoundError:
    _routing_policy_spec = importlib.util.spec_from_file_location(
        "task_analyze_routing_policy", Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "routing_policy.py"
    )
    _routing_policy = importlib.util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    expected_owner_skill = _routing_policy.expected_owner_skill
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    is_tiny_spark_profile = _routing_policy.is_tiny_spark_profile
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry


EXPECTED_ROUTE_PREFIX = ["task-analyze-skill", "workflow-skill"]
DIRECT_TOOL_ROUTE_PREFIX = ["task-analyze-skill", "workflow-skill", "chrome:control-chrome"]
FRONTEND_ROUTE_PREFIX = ["task-analyze-skill", "workflow-skill", "build-web-apps:frontend-app-builder"]
REQUIRED_WORKFLOW = [
    "100%-trigger individual entry skill",
    "observable entry model and effort belong only to Task Analyze and route coordination",
    "model_routing_history.py record",
    "adaptive_model_runner.py",
    "it records after Mini and updates after Real",
    "same route-run ID",
    "Continue in the same task",
    "Do not wait for a lifecycle hook",
    "Easy task: concise text explanation",
    "Complex task: task-specific Mermaid",
    "Every active registry-owned code-domain node loads `code-skill`",
    "Mini Verify is the basic proportional result gate for every task",
    "show the main result immediately",
    "Ending Task starts after the main result",
    "Real Verify",
    "independent optimization verification",
    "must not silently inherit the entry selection",
    "workflow receives an explicit model and effort for every downstream node",
    "Runtime Receipt Gate",
]
REQUIRED_TEMPLATE = ["## Easy Task: Text Only", "## Complex Task: Mermaid", "current selected model | current selected effort", "Show main result now", "Dispatch Ending Task", "Real Verify", "Independent optimization verification", "Main Result always follows Mini Verify", "Ending Task always follows Main Result", "Workflow with models"]
REQUIRED_MATRIX = ["Every route begins with independent `task-analyze-skill`", "Easy tasks use concise text", "complex tasks use Mermaid", "Every active registry-owned code-domain node loads `code-skill`", "Mini Verify is the basic first-result gate", "Main Result precedes Ending Task", "background correctness failure"]
REQUIRED_CODE = ["task-analyze-skill", "locked", "code-skill", "Spark-low", "Mini Verify", "Ending Task", "Real Verify"]
REQUIRED_VERIFY = ["task-analyze-skill", "Mini Verify", "main result", "Ending Task", "Real Verify", "reopen"]
REQUIRED_OPTIMIZATION = ["task-analyze-skill", "Ending Task", "different", "verifier", "before/after"]
REQUIRED_ENTRY = [
    "resolve_entry_model.py",
    "selected entry model and effort run Task Analyze and route coordination only",
    "preserve its exact verified pair",
    "Never treat the entry pair as the workflow-wide model",
    "workflow-wide model",
]
REQUIRED_TINY = ["tiny_text", "tiny_code", "command_generation", "Spark-low"]
REQUIRED_ADAPTIVE = ["local/adaptive-routing/model_experience.json", "generalized privacy-filtered task summary", "result-producer attempt", "same attempt", "success_model", "failed_model", "raw prompts", "raw results", "model_experience.json"]
FORBIDDEN = ["internal Task Analyze", "not a sixth top-level skill", "Task Analyze itself uses `GPT-5.6-Sol`", "Task Analyze still runs on Sol", "correctness-affecting Real Verify stays before", "Real Verify always stays before Main Goal Done", "approved five", "five-folder boundary"]


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter")
    result = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def folded_prompt_length(text):
    match = re.search(r"^  default_prompt:\s*>-?\s*\n((?:    .*\n?)+)", text, flags=re.MULTILINE)
    if not match:
        return None
    return len(" ".join(line.strip() for line in match.group(1).splitlines()).strip())


def missing_terms(label, text, required):
    normalized = re.sub(r"\s+", " ", text).lower()
    return [f"{label} missing required contract: {term}" for term in required if re.sub(r"\s+", " ", term).lower() not in normalized]


def parse_routes(matrix_text):
    routes = {}
    for line in matrix_text.splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Scenario"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        routes[cells[0]] = [part.strip() for part in cells[2].split("->")]
    return routes


def can_show_main_result(requested_work_done, mini_passed):
    return bool(requested_work_done and mini_passed)


def _is_code_implementation(node):
    if node.get("purpose") in {"implement", "author-probe"}:
        return True
    if node.get("phase") != "result":
        return False
    try:
        execution_domain = resolve_execution_domain(
            owning_skill=node.get("skill"),
            task_family=node.get("task_family"),
            explicit_domain=node.get("execution_domain"),
            language=node.get("language"),
            purpose=node.get("purpose"),
        )
    except ValueError:
        return False
    return is_code_execution_domain(execution_domain)


def validate_trace(name, trace, skills_root=Path(__file__).resolve().parents[2]):
    failures = []
    try:
        validate_execution_domain_registry(skills_root)
    except ValueError as error:
        failures.append(f"execution-domain registry is invalid: {error}")
    ids = [node["id"] for node in trace]
    if not ids or ids[0] != "task-analyze":
        failures.append("Task Analyze is not first")
    for node in trace:
        if not node.get("model") or not node.get("effort"):
            failures.append(f"{node.get('id', '<unknown>')} lacks model/effort")
        if resolve_skill_path(node.get("skill"), skills_root) is None:
            failures.append(f"{node.get('id', '<unknown>')} names unavailable skill {node.get('skill')}")
    mini_index = ids.index("mini-verify") if "mini-verify" in ids else -1
    result_index = ids.index("main-result") if "main-result" in ids else -1
    ending_index = ids.index("ending-dispatch") if "ending-dispatch" in ids else -1
    if not (0 <= mini_index < result_index < ending_index):
        failures.append("expected Mini Verify < Main Result < Ending dispatch")
    for ending_id in ("real-verify", "optimization-verify", "records"):
        if ending_id in ids and ids.index(ending_id) <= result_index:
            failures.append(f"{ending_id} is not downstream of Main Result")
    for node in trace:
        explicit_domain = node.get("execution_domain")
        try:
            execution_domain = resolve_execution_domain(
                owning_skill=node.get("skill"),
                task_family=node.get("task_family"),
                explicit_domain=explicit_domain,
                language=node.get("language"),
                purpose=node.get("purpose"),
            )
        except ValueError:
            if explicit_domain:
                failures.append(f"{node['id']} uses unknown execution_domain {explicit_domain}")
            continue
        if not execution_domain_is_active(execution_domain):
            failures.append(f"{node['id']} execution_domain is non-active: {execution_domain}")
        if execution_domain not in EXECUTION_DOMAINS:
            failures.append(f"{node['id']} uses unknown execution_domain {execution_domain}")
            continue
        if not is_code_execution_domain(execution_domain):
            continue
        owner = expected_owner_skill(execution_domain)
        if owner is not None and node.get("skill") != owner:
            failures.append(f"{node['id']} bypasses code-skill")
        if node.get("model") == "gpt-5.3-codex-spark" and not is_tiny_spark_profile(node.get("task_family"), node.get("modality"), node.get("risk"), node.get("complexity"), node.get("ambiguity")):
            failures.append(f"{node['id']} Spark is valid only for low-risk easy low-ambiguity text tiny profiles")
    return {"name": name, "status": "pass" if not failures else "fail", "failures": failures}


def sample_traces():
    easy = [{"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill"}, {"id": "direct", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "mini-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "records", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}]
    complex_code = [{"id": "task-analyze", "model": "gpt-5.6-sol", "effort": "ultra", "skill": "task-analyze-skill"}, {"id": "audit", "model": "gpt-5.6-terra", "effort": "high", "skill": "workflow-skill"}, {"id": "implement", "model": "gpt-5.6-terra", "effort": "high", "skill": "code-skill", "language": "python", "purpose": "implement", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"}, {"id": "mini-verify", "model": "gpt-5.6-terra", "effort": "high", "skill": "verify-skill"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "medium", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "medium", "skill": "workflow-skill"}, {"id": "real-verify", "model": "gpt-5.6-terra", "effort": "high", "skill": "verify-skill"}, {"id": "optimization-verify", "model": "gpt-5.6-terra", "effort": "high", "skill": "verify-skill"}, {"id": "records", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}]
    terra_entry = [{"id": "task-analyze", "model": "gpt-5.6-terra", "effort": "medium", "skill": "task-analyze-skill"}, {"id": "direct", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "mini-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}]
    return {"easy-luna-entry": easy, "complex-sol-ultra-entry": complex_code, "easy-terra-entry": terra_entry}


def validate(skill_dir):
    global_root = skill_dir.parent
    paths = {
        "workflow": skill_dir / "SKILL.md",
        "agent": skill_dir / "agents" / "openai.yaml",
        "template": skill_dir / "references" / "start-diagram-template.md",
        "matrix": skill_dir / "references" / "routing-matrix.md",
        "code": global_root / "code-skill" / "SKILL.md",
        "verify": global_root / "verify-skill" / "SKILL.md",
        "optimization": global_root / "optimization-skill" / "SKILL.md",
        "task_analyze": global_root / "task-analyze-skill" / "SKILL.md",
        "task_analyze_entry_rule": global_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md",
        "task_analyze_selection": global_root / "task-analyze-skill" / "references" / "model-selection.md",
        "task_analyze_adaptive": global_root / "task-analyze-skill" / "references" / "adaptive-routing.md",
    }
    failures = []
    for label, path in paths.items():
        if not path.exists():
            failures.append(f"missing {label}: {path}")
    if failures:
        return {"failures": failures, "routes": [], "traces": []}
    texts = {label: read_text(path) for label, path in paths.items()}
    metadata = parse_frontmatter(texts["workflow"])
    if set(metadata) != {"name", "description"} or metadata.get("name") != "workflow-skill":
        failures.append("workflow frontmatter must contain only name=workflow-skill and description")
    if len(metadata.get("description", "")) > 1024:
        failures.append("workflow frontmatter description exceeds 1024 characters")
    prompt_length = folded_prompt_length(texts["agent"])
    if prompt_length is None or prompt_length > 1024:
        failures.append(f"workflow agent default_prompt invalid length: {prompt_length}")
    failures.extend(missing_terms("workflow", texts["workflow"], REQUIRED_WORKFLOW))
    failures.extend(missing_terms("template", texts["template"], REQUIRED_TEMPLATE))
    failures.extend(missing_terms("matrix", texts["matrix"], REQUIRED_MATRIX))
    failures.extend(missing_terms("code-skill", texts["code"], REQUIRED_CODE))
    failures.extend(missing_terms("verify-skill", texts["verify"], REQUIRED_VERIFY))
    failures.extend(missing_terms("optimization-skill", texts["optimization"], REQUIRED_OPTIMIZATION))
    failures.extend(missing_terms("task-analyze-entry-rule", texts["task_analyze_entry_rule"], REQUIRED_ENTRY))
    failures.extend(missing_terms("task-analyze-model-selection", texts["task_analyze_selection"], REQUIRED_TINY))
    failures.extend(missing_terms("task-analyze-adaptive", texts["task_analyze_adaptive"], REQUIRED_ADAPTIVE))
    live_text = "\n".join(texts.values())
    for forbidden in FORBIDDEN:
        if forbidden.lower() in live_text.lower():
            failures.append(f"live contract contains obsolete text: {forbidden}")
    for obsolete_path in (skill_dir / "references" / "model-capabilities.md", skill_dir / "references" / "major-task-model-manager.md", skill_dir / "scripts" / "sync_model_capabilities.py"):
        if obsolete_path.exists():
            failures.append(f"Task Analyze-owned file remains under workflow-skill: {obsolete_path}")
    routes = parse_routes(texts["matrix"])
    route_results = []
    for name, route in routes.items():
        expected_prefix = DIRECT_TOOL_ROUTE_PREFIX if name in {"open-chrome", "open-youtube", "search-cctv-on-youtube"} else FRONTEND_ROUTE_PREFIX if name == "design-youtube-like-website" else EXPECTED_ROUTE_PREFIX
        route_failures = [] if route[:len(expected_prefix)] == expected_prefix else [f"route must begin {expected_prefix}, got {route[:len(expected_prefix)]}"]
        if any(is_code_execution_domain(node.get("execution_domain")) for node in sample_traces().get(name, []) if node.get("execution_domain")) and "code-skill" not in route:
            route_failures.append("registered code-domain route bypasses code-skill")
        route_results.append({"name": name, "status": "pass" if not route_failures else "fail", "route": route, "failures": route_failures})
        failures.extend([f"route {name}: {failure}" for failure in route_failures])
    gate_results = [{"name": "done+mini", "observed": can_show_main_result(True, True), "expected": True}, {"name": "done+mini-fail", "observed": can_show_main_result(True, False), "expected": False}, {"name": "not-done+mini", "observed": can_show_main_result(False, True), "expected": False}]
    for result in gate_results:
        if result["observed"] != result["expected"]:
            failures.append(f"gate {result['name']} mismatch")
    trace_results = [validate_trace(name, trace, global_root) for name, trace in sample_traces().items()]
    for result in trace_results:
        failures.extend([f"trace {result['name']}: {failure}" for failure in result["failures"]])
    entry_models = {trace[0]["model"] for trace in sample_traces().values()}
    if len(entry_models) < 3:
        failures.append("entry-model regression samples do not prove arbitrary selected entry models")
    fixture_path = global_root / "task-analyze-skill" / "assets" / "graduated-route-fixtures.json"
    graduated_failures = validate_fixture(fixture_path, global_root, True)
    try:
        graduated_count = len(json.loads(fixture_path.read_text(encoding="utf-8")).get("scenarios", []))
    except (OSError, json.JSONDecodeError):
        graduated_count = 0
    graduated_results = [{"name": "graduated-raw-prompts", "status": "pass" if not graduated_failures else "fail", "failures": graduated_failures, "scenario_count": graduated_count}]
    failures.extend([f"graduated scenario: {failure}" for failure in graduated_failures])
    return {"skill_dir": str(skill_dir), "routes": route_results, "gates": gate_results, "traces": trace_results, "graduated": graduated_results, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description="Validate workflow execution after independent Task Analyze routing.")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.skill_dir.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for label in ("routes", "gates", "traces", "graduated"):
        items = result[label]
        passed = sum(1 for item in items if item.get("status", "pass" if item.get("observed") == item.get("expected") else "fail") == "pass")
        if label == "graduated":
            total = sum(item.get("scenario_count", 0) for item in items)
            print(f"workflow-skill {label}: {total if passed == len(items) else 0}/{total} passed")
        else:
            print(f"workflow-skill {label}: {passed}/{len(items)} passed")
    if result["failures"]:
        print("Failures:", file=sys.stderr)
        for failure in result["failures"]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

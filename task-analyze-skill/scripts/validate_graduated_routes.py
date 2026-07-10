#!/usr/bin/env python3
"""Portable static validation for the graduated raw-prompt routing fixture."""

import argparse
from copy import deepcopy
import importlib.util
import json
import tempfile
from pathlib import Path


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "assets" / "graduated-route-fixtures.json"
DIRECT_PROMPTS = ["Open Chrome", "Open Chrome and open YouTube", "Open Chrome, open YouTube, and search CCTV"]
COMPLEX_PROMPT = "Design a website like YouTube for me"
DIRECT_MINI_CONDITIONS = {"Open Chrome": "Chrome is open", "Open Chrome and open YouTube": "youtube.com is loaded", "Open Chrome, open YouTube, and search CCTV": "CCTV query and visible results are present"}
DIRECT_ROUTE = ["task-analyze-skill", "workflow-skill", "chrome:control-chrome"]
COMPLEX_ROUTE = ["task-analyze-skill", "workflow-skill", "build-web-apps:frontend-app-builder"]
REQUIRED_PAIRS = {"design": "gpt-5.6-sol|high", "implementation": "gpt-5.6-terra|high", "mini": "gpt-5.6-terra|medium", "ending_records": "gpt-5.6-luna|low", "ending_real": "gpt-5.6-terra|high"}
SUPPORTED_PAIRS = {"gpt-5.3-codex-spark|low", "gpt-5.3-codex-spark|medium", "gpt-5.3-codex-spark|high", "gpt-5.6-luna|low", "gpt-5.6-luna|medium", "gpt-5.6-luna|high", "gpt-5.6-terra|low", "gpt-5.6-terra|medium", "gpt-5.6-terra|high", "gpt-5.6-sol|low", "gpt-5.6-sol|medium", "gpt-5.6-sol|high", "gpt-5.6-sol|ultra"}
ENDING_CHECKS = ["responsive", "console", "navigation", "accessibility", "visual"]
DIRECT_ALLOWED_KEYS = {"prompt", "complexity", "route_type", "skill", "controller_skill", "route", "mini_condition", "timing_evidence"}
COMPLEX_ALLOWED_KEYS = {"prompt", "complexity", "route_type", "skill", "controller_skill", "route", "mini_condition", "timing_evidence", "dispatcher_plan", "static_pairs", "adaptive_result_producer", "controller_transitions", "ending_checks"}


def materialize_dispatcher_plan(plan_template, cache_dir, entry_model, entry_effort):
    plan = deepcopy(plan_template)
    plan["cache_dir"] = str(Path(cache_dir).expanduser().resolve())
    plan["entry"] = {"model": entry_model, "effort": entry_effort}
    return plan


def required_skill_ids(scenario):
    skill_ids = {scenario.get("skill"), scenario.get("controller_skill")}
    skill_ids.update(scenario.get("route", []))
    plan = scenario.get("dispatcher_plan")
    if isinstance(plan, dict):
        skill_ids.update(node.get("skill") for node in plan.get("nodes", []) if isinstance(node, dict))
    return sorted(skill_id for skill_id in skill_ids if isinstance(skill_id, str) and skill_id)


def _check_installed(skill_id, skills_root, failures):
    try:
        from skill_resolver import resolve_skill_path
    except ImportError:
        resolver_path = Path(__file__).with_name("skill_resolver.py")
        resolver_spec = importlib.util.spec_from_file_location("graduated_route_skill_resolver", resolver_path)
        resolver_module = importlib.util.module_from_spec(resolver_spec)
        resolver_spec.loader.exec_module(resolver_module)
        resolve_skill_path = resolver_module.resolve_skill_path
    if resolve_skill_path(skill_id, skills_root) is None:
        failures.append(f"skill is not installed: {skill_id}")


def _dispatcher_module():
    dispatcher_path = Path(__file__).with_name("task_route_dispatcher.py")
    dispatcher_spec = importlib.util.spec_from_file_location("graduated_route_dispatcher", dispatcher_path)
    dispatcher = importlib.util.module_from_spec(dispatcher_spec)
    dispatcher_spec.loader.exec_module(dispatcher)
    return dispatcher


def _validate_dispatcher_plan(scenario, skills_root, failures):
    plan = scenario.get("dispatcher_plan")
    if not isinstance(plan, dict):
        failures.append("website scenario dispatcher_plan must be an object")
        return
    dispatcher = _dispatcher_module()
    expected_nodes = ["design", "implementation", "mini", "ending-records", "ending-real"]
    expected_roles = {
        "design": ("result", "build-web-apps:frontend-app-builder", "gpt-5.6-sol", "high", [], "general"),
        "implementation": ("result", "build-web-apps:frontend-app-builder", "gpt-5.6-terra", "high", ["design"], "general"),
        "mini": ("mini", "verify-skill", "gpt-5.6-terra", "medium", ["implementation"], "general"),
        "ending-records": ("ending", "management-skill", "gpt-5.6-luna", "low", ["mini"], "general"),
        "ending-real": ("ending", "verify-skill", "gpt-5.6-terra", "high", ["mini"], "general"),
    }
    template_nodes = plan.get("nodes", [])
    if [node.get("id") for node in template_nodes if isinstance(node, dict)] != expected_nodes:
        failures.append("website dispatcher plan node topology is incorrect")
        return
    if plan.get("main_result_node") != "implementation" or plan.get("mini_verify_node") != "mini":
        failures.append("website dispatcher plan main and Mini nodes are incorrect")
    if scenario.get("adaptive_result_producer") != "implementation":
        failures.append("website dispatcher plan adaptive producer is incorrect")
    for node in template_nodes:
        expected = expected_roles[node["id"]]
        observed = (node.get("phase"), node.get("skill"), node.get("model"), node.get("effort"), node.get("dependencies"), node.get("execution_domain"))
        if observed != expected:
            failures.append(f"website dispatcher plan role is incorrect for {node['id']}")
        expected_pair = scenario["static_pairs"].get({"design": "design", "implementation": "implementation", "mini": "mini", "ending-records": "ending_records", "ending-real": "ending_real"}[node["id"]])
        if f"{node.get('model')}|{node.get('effort')}" != expected_pair:
            failures.append(f"website dispatcher plan pair is incorrect for {node['id']}")
    supported_pairs = sorted(f"{model}|{effort}" for model, efforts in dispatcher.MODEL_EFFORTS.items() for effort in efforts)
    with tempfile.TemporaryDirectory(prefix="graduated-route-plan-") as temporary:
        for pair in supported_pairs:
            entry_model, entry_effort = pair.split("|", 1)
            materialized = materialize_dispatcher_plan(plan, Path(temporary) / pair.replace("|", "-"), entry_model, entry_effort)
            plan_failures = dispatcher.validate_plan(materialized, entry_model, entry_effort, Path(temporary), skills_root)
            failures.extend([f"website dispatcher plan {pair}: {failure}" for failure in plan_failures])
            for template_node, materialized_node in zip(template_nodes, materialized["nodes"]):
                if (template_node.get("model"), template_node.get("effort")) != (materialized_node.get("model"), materialized_node.get("effort")):
                    failures.append(f"website dispatcher plan downstream pair inherited entry pair for {materialized_node['id']}")


def validate_fixture(path=FIXTURE_PATH, skills_root=None, require_installed=False):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"graduated fixture cannot be read: {error}"]
    failures = []
    scenarios = payload.get("scenarios") if isinstance(payload, dict) else None
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(scenarios, list) or len(scenarios) != 4:
        return ["graduated fixture must contain exactly four scenarios"]
    by_prompt = {scenario.get("prompt"): scenario for scenario in scenarios if isinstance(scenario, dict)}
    if set(by_prompt) != set(DIRECT_PROMPTS + [COMPLEX_PROMPT]):
        failures.append("graduated fixture raw prompts do not match the required set")
    if require_installed:
        resolved_root = Path(skills_root or Path(__file__).resolve().parents[2])
        for scenario in scenarios:
            for skill_id in required_skill_ids(scenario):
                _check_installed(skill_id, resolved_root, failures)
    for prompt in DIRECT_PROMPTS:
        scenario = by_prompt.get(prompt, {})
        if scenario.get("complexity") != "easy" or scenario.get("route_type") != "direct_tool" or scenario.get("skill") != "chrome:control-chrome":
            failures.append(f"{prompt}: must be an easy chrome direct_tool route")
        if scenario.get("controller_skill") != "workflow-skill":
            failures.append(f"{prompt}: controller skill must be workflow-skill")
        if scenario.get("route") != DIRECT_ROUTE:
            failures.append(f"{prompt}: route ordering must be {DIRECT_ROUTE}")
        if scenario.get("mini_condition") != DIRECT_MINI_CONDITIONS[prompt]:
            failures.append(f"{prompt}: Mini condition is incorrect")
        if scenario.get("timing_evidence") != "wall_clock_to_observable_stop":
            failures.append(f"{prompt}: timing evidence must be wall_clock_to_observable_stop")
        unknown_keys = set(scenario) - DIRECT_ALLOWED_KEYS
        if unknown_keys:
            failures.append(f"{prompt}: direct route leaks dispatch or model execution: {', '.join(sorted(unknown_keys))}")
    scenario = by_prompt.get(COMPLEX_PROMPT, {})
    if scenario.get("complexity") != "complex" or scenario.get("route_type") != "model_dispatch" or scenario.get("skill") != "build-web-apps:frontend-app-builder":
        failures.append("website scenario must be complex model_dispatch with canonical frontend skill")
    if scenario.get("controller_skill") != "workflow-skill":
        failures.append("website scenario controller skill must be workflow-skill")
    if scenario.get("route") != COMPLEX_ROUTE:
        failures.append(f"website scenario route ordering must be {COMPLEX_ROUTE}")
    if scenario.get("mini_condition") != "A rendered draft exists and core interaction paths render":
        failures.append("website scenario Mini condition must say a rendered draft exists and core interaction paths render")
    if scenario.get("timing_evidence") != "passing_runtime_receipts":
        failures.append("website scenario timing evidence is incorrect")
    unknown_keys = set(scenario) - COMPLEX_ALLOWED_KEYS
    if unknown_keys:
        failures.append("website scenario contains unknown execution fields: " + ", ".join(sorted(unknown_keys)))
    if scenario.get("static_pairs") != REQUIRED_PAIRS or any(pair not in SUPPORTED_PAIRS for pair in scenario.get("static_pairs", {}).values()):
        failures.append("website scenario static model/effort roles are incorrect or unsupported")
    if scenario.get("adaptive_result_producer") != "implementation":
        failures.append("website scenario adaptive producer must be the implementation receipt")
    if scenario.get("controller_transitions") != {"main_result_release": "observed_entry_coordinator", "ending_dispatch": "observed_entry_coordinator"}:
        failures.append("website scenario controller transitions must use the observed entry coordinator")
    if scenario.get("ending_checks") != ENDING_CHECKS:
        failures.append("website scenario Ending checks are incomplete")
    _validate_dispatcher_plan(scenario, Path(skills_root or Path(__file__).resolve().parents[2]), failures)
    return failures


def main():
    parser = argparse.ArgumentParser(description="Validate graduated raw-prompt routes.")
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--skills-root", type=Path)
    parser.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    failures = validate_fixture(args.fixture, args.skills_root, args.require_installed)
    print(f"graduated-route-fixtures: {0 if failures else 4}/4 passed")
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

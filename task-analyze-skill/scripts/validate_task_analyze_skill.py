#!/usr/bin/env python3
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


SYNC_PATH = Path(__file__).resolve().parent / "sync_model_capabilities.py"
SYNC_SPEC = importlib.util.spec_from_file_location("task_analyze_sync_model_capabilities", SYNC_PATH)
sync_model_capabilities = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(sync_model_capabilities)

try:
    from routing_policy import EXECUTION_DOMAINS, MODEL_EFFORTS, MODEL_EFFORT_ORDER, MODEL_ORDER
except ModuleNotFoundError:
    import importlib.util as _importlib_util

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = _importlib_util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = _importlib_util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    MODEL_EFFORTS = _routing_policy.MODEL_EFFORTS
    MODEL_EFFORT_ORDER = _routing_policy.MODEL_EFFORT_ORDER
    MODEL_ORDER = _routing_policy.MODEL_ORDER
REQUIRED_FILES = [
    ".gitignore",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/global-agents-entry-rule.md",
    "references/route-contract.md",
    "references/model-selection.md",
    "references/model-capabilities.md",
    "references/runtime-receipts.md",
    "references/adaptive-routing.md",
    "scripts/resolve_entry_model.py",
    "scripts/sync_model_capabilities.py",
    "scripts/model_execution_receipt.py",
    "scripts/model_routing_history.py",
    "scripts/task_route_dispatcher.py",
    "scripts/validate_task_analyze_skill.py",
]
REQUIRED_SKILL_TEXT = [
    "Use this skill first for every user task",
    "individual global skill",
    "hookless global entry mechanism",
    "nested cache/fixture `SKILL.md`",
    "entry can be any supported pair",
    "resolve_entry_model.py",
    "every downstream node uses its planned model and effort",
    "Easy",
    "concise text",
    "Complex",
    "Mermaid",
    "Python/C#/Unity C#",
    "Spark first",
    "Private Adaptive Routing",
    "trial exactly one lower effort on the same model",
    "Mini Verify",
    "show the main result immediately",
    "Ending Task",
    "scripts/model_execution_receipt.py",
    "task_route_dispatcher.py run-plan",
    "continue in the same task",
]
REQUIRED_ROUTE_TEXT = [
    "## Easy Task: Text Route",
    "Do not draw Mermaid for an easy task",
    "## Complex Task: Mermaid Route",
    "```mermaid",
    "Workflow with models",
    "Main Goal Done Gate",
    "Show main result now",
    "Dispatch background Ending Task",
    "Real Verify",
    "Independent optimization verification",
    "## Internal Plan",
    "never conversation output",
]
REQUIRED_SELECTION_TEXT = [
    "selected at task entry",
    "static model by the node's real work",
    "Spark first",
    "lowest supported effort that can reliably meet the stop condition",
    "Receipt-Backed Personal Learning",
    "one cheaper/faster rung",
    "Efficiency Guard",
    "No prior success",
    "tiny_text",
    "tiny_code",
    "command_generation",
    "Spark-low",
    "currently selected",
]
REQUIRED_RECEIPT_TEXT = [
    "requested model and effort",
    "resolved model and effort",
    "effective model",
    "model_reroute",
    "input, cached-input, output, reasoning-output, and total tokens",
    "whole-process elapsed time",
    "not a cryptographically signed backend attestation",
    "like-for-like",
    "workload_prompt_sha256",
]
REQUIRED_ADAPTIVE_TEXT = [
    "local/adaptive-routing/model_experience.json",
    "generalized privacy-filtered task summary",
    "success_model",
    "failed_model",
    "result-producer attempt",
    "After a receipt-matched verification pass",
    "correctness or quality failure",
    "Real Verify failure overrides",
    "Tokens are a usage proxy",
]
FORBIDDEN_TEXT = [
    "mandatory internal phase of `workflow-skill`",
    "not a sixth top-level skill",
    "Run Task Analyze with `GPT-5.6-Sol`",
    "Task Analyze still runs on Sol",
    "entry model always Sol",
    "correctness-affecting Real Verify stays before",
    "approved five",
    "user-level Codex hook",
    "trusted `Stop` hook",
    "TASK_ANALYZE_PLAN_JSON",
    "ends Task Analyze with the visible route and JSON handoff",
]


def read_text(path):
    return path.read_text(encoding="utf-8")


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("SKILL.md missing YAML frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def folded_prompt_length(text):
    match = re.search(r"^  default_prompt:\s*>-?\s*\n((?:    .*\n?)+)", text, flags=re.MULTILINE)
    if match:
        return len(" ".join(line.strip() for line in match.group(1).splitlines()).strip())
    quoted = re.search(r'^  default_prompt:\s*"(.*)"\s*$', text, flags=re.MULTILINE)
    return len(quoted.group(1)) if quoted else None


def missing_terms(label, text, required):
    normalized = normalize(text)
    return [f"{label} missing required contract: {term}" for term in required if normalize(term) not in normalized]


def installed_skills(skill_dir):
    return {path.name for path in skill_dir.parent.iterdir() if path.is_dir() and (path / "SKILL.md").exists()}




def _is_code_implementation(node):
    if node.get("purpose") in {"implement", "author-probe"}:
        return True
    language = node.get("language")
    execution_domain = node.get("execution_domain")
    return (
        language in {"python", "csharp", "unity_csharp"}
        or execution_domain in {"python", "csharp", "unity_csharp"}
    )


def validate_plan(plan, installed):
    failures = []
    nodes = plan.get("nodes", [])
    entry = nodes[0] if nodes else {}
    entry_model = entry.get("model")
    entry_effort = entry.get("effort")
    node_by_id = {node.get("id"): node for node in nodes}
    if not nodes or nodes[0].get("skill") != "task-analyze-skill":
        failures.append("Task Analyze must be the first node")
    if plan.get("complexity") == "easy" and plan.get("display") != "text":
        failures.append("easy plans must use text display")
    if plan.get("complexity") == "complex" and plan.get("display") != "mermaid":
        failures.append("complex plans must use Mermaid display")
    for index, node in enumerate(nodes):
        node_id = node.get("id", "<missing>")
        model = node.get("model")
        effort = node.get("effort")
        skill = node.get("skill")
        if model not in MODEL_EFFORTS or effort not in MODEL_EFFORTS.get(model, set()):
            failures.append(f"{node_id} has unsupported model/effort")
        if skill not in installed:
            failures.append(f"{node_id} names unavailable skill {skill}")
        for dependency in node.get("dependencies", []):
            if dependency not in node_by_id:
                failures.append(f"{node_id} has missing dependency {dependency}")
        execution_domain = node.get("execution_domain")
        if execution_domain and execution_domain not in EXECUTION_DOMAINS:
            failures.append(f"{node_id} uses unknown execution_domain: {execution_domain}")
        if _is_code_implementation(node) and skill != "code-skill":
            failures.append(f"{node_id} bypasses code-skill")
        if (
            _is_code_implementation(node)
            and model != "gpt-5.3-codex-spark"
            and not node.get("spark_exception_reason")
            and not node.get("fallback_reason")
        ):
            failures.append(f"{node_id} is not Spark-first and has no fallback reason")
        if index > 0 and model == entry_model and effort == entry_effort:
            failures.append(f"{node_id} reuses resolved entry model and effort")
    mini = node_by_id.get("mini-verify")
    main = node_by_id.get("main-result")
    ending = node_by_id.get("ending-dispatch")
    if not mini or not main or not ending:
        failures.append("plan must contain Mini Verify, Main Result, and Ending dispatch")
    else:
        if "mini-verify" not in main.get("dependencies", []):
            failures.append("Main Result must depend on Mini Verify")
        if "main-result" not in ending.get("dependencies", []):
            failures.append("Ending dispatch must depend on Main Result")
        if any(dependency in {"real-verify", "optimization-verify", "records"} for dependency in main.get("dependencies", [])):
            failures.append("Main Result must not depend on Ending Task work")
    for ending_id in ("real-verify", "optimization-verify", "records"):
        if ending_id in node_by_id and "ending-dispatch" not in node_by_id[ending_id].get("dependencies", []):
            failures.append(f"{ending_id} must depend on Ending dispatch")
    return failures


def _downstream_model(entry_model):
    index = MODEL_ORDER.index(entry_model)
    if index + 1 < len(MODEL_ORDER):
        return MODEL_ORDER[index + 1]
    return MODEL_ORDER[1]


def _downstream_effort(model):
    for effort in MODEL_EFFORT_ORDER:
        if effort in MODEL_EFFORTS[model]:
            return effort
    raise ValueError(f"model has no supported effort: {model}")


def sample_plans():
    ordered_models = list(MODEL_ORDER)
    plans = {}
    for model in ordered_models:
        for effort in MODEL_EFFORT_ORDER:
            if effort not in MODEL_EFFORTS[model]:
                continue
            downstream_model = _downstream_model(model)
            downstream_effort = _downstream_effort(downstream_model)
            if model == "gpt-5.6-sol" and effort == "ultra":
                plans[f"complex-{model}-{effort}"] = {
                    "complexity": "complex",
                    "display": "mermaid",
                    "nodes": [
                        {
                        "id": "task-analyze",
                        "skill": "task-analyze-skill",
                        "model": model,
                        "effort": effort,
                        "dependencies": [],
                        },
                        {"id": "audit", "skill": "workflow-skill", "model": "gpt-5.6-terra", "effort": "high", "dependencies": ["task-analyze"], "execution_domain": "general"},
                        {
                            "id": "implement",
                            "skill": "code-skill",
                            "model": "gpt-5.3-codex-spark",
                            "effort": "high",
                            "dependencies": ["audit"],
                            "execution_domain": "python",
                            "language": "python",
                            "purpose": "implement",
                        },
                        {"id": "mini-verify", "skill": "verify-skill", "model": "gpt-5.6-terra", "effort": "high", "dependencies": ["implement"], "execution_domain": "general"},
                        {"id": "main-result", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["mini-verify"], "execution_domain": "general"},
                        {"id": "ending-dispatch", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["main-result"], "execution_domain": "general"},
                        {"id": "real-verify", "skill": "verify-skill", "model": "gpt-5.6-terra", "effort": "high", "dependencies": ["ending-dispatch"], "execution_domain": "general"},
                        {"id": "optimization-verify", "skill": "verify-skill", "model": "gpt-5.6-terra", "effort": "high", "dependencies": ["ending-dispatch"], "execution_domain": "general"},
                        {"id": "records", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["ending-dispatch"], "execution_domain": "general"},
                    ],
                }
            else:
                plans[f"easy-{model}-{effort}"] = {
                    "complexity": "easy",
                    "display": "text",
                    "nodes": [
                        {"id": "task-analyze", "skill": "task-analyze-skill", "model": model, "effort": effort, "dependencies": []},
                        {
                            "id": "direct",
                            "skill": "workflow-skill",
                            "model": downstream_model,
                            "effort": downstream_effort,
                            "dependencies": ["task-analyze"],
                            "execution_domain": "general",
                        },
                        {"id": "mini-verify", "skill": "verify-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["direct"], "execution_domain": "general"},
                        {"id": "main-result", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["mini-verify"], "execution_domain": "general"},
                        {"id": "ending-dispatch", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["main-result"], "execution_domain": "general"},
                        {"id": "records", "skill": "workflow-skill", "model": downstream_model, "effort": downstream_effort, "dependencies": ["ending-dispatch"], "execution_domain": "general"},
                    ],
                }
    return plans


def validate(skill_dir, models_cache_path, global_agents_path=Path.home() / ".codex" / "AGENTS.md", global_skills_root=Path.home() / ".codex" / "skills", global_hooks_path=Path.home() / ".codex" / "hooks.json"):
    failures = []
    paths = {relative: skill_dir / relative for relative in REQUIRED_FILES}
    for relative, path in paths.items():
        if not path.exists():
            failures.append(f"missing required file: {relative}")
    if failures:
        return {"valid": False, "failures": failures, "plans": []}
    skill_text = read_text(paths["SKILL.md"])
    agent_text = read_text(paths["agents/openai.yaml"])
    route_text = read_text(paths["references/route-contract.md"])
    selection_text = read_text(paths["references/model-selection.md"])
    receipt_text = read_text(paths["references/runtime-receipts.md"])
    adaptive_text = read_text(paths["references/adaptive-routing.md"])
    entry_asset_text = read_text(paths["assets/global-agents-entry-rule.md"])
    metadata = parse_frontmatter(skill_text)
    if set(metadata) != {"name", "description"} or metadata.get("name") != "task-analyze-skill":
        failures.append("frontmatter must contain only name=task-analyze-skill and description")
    if len(metadata.get("description", "")) > 1024:
        failures.append("frontmatter description exceeds 1024 characters")
    prompt_length = folded_prompt_length(agent_text)
    if prompt_length is None or prompt_length > 1024:
        failures.append(f"agent default_prompt invalid length: {prompt_length}")
    failures.extend(missing_terms("SKILL.md", skill_text, REQUIRED_SKILL_TEXT))
    failures.extend(missing_terms("route-contract", route_text, REQUIRED_ROUTE_TEXT))
    failures.extend(missing_terms("model-selection", selection_text, REQUIRED_SELECTION_TEXT))
    failures.extend(missing_terms("runtime-receipts", receipt_text, REQUIRED_RECEIPT_TEXT))
    failures.extend(missing_terms("adaptive-routing", adaptive_text, REQUIRED_ADAPTIVE_TEXT))
    if "/local/" not in read_text(paths[".gitignore"]):
        failures.append("task-analyze-skill .gitignore must exclude /local/")
    for obsolete_path in (skill_dir / "assets" / "hooks.json", skill_dir / "scripts" / "task_entry_hook.py", skill_dir / "tests" / "test_task_entry_hook.py"):
        if obsolete_path.exists():
            failures.append(f"obsolete hook artifact remains: {obsolete_path.relative_to(skill_dir)}")
    live_text = "\n".join([skill_text, agent_text, route_text, selection_text, receipt_text])
    for forbidden in FORBIDDEN_TEXT:
        if normalize(forbidden) in normalize(live_text):
            failures.append(f"live contract contains obsolete text: {forbidden}")
    if not global_agents_path.exists():
        failures.append(f"always-loaded global AGENTS.md is missing: {global_agents_path}")
    else:
        global_agents_text = read_text(global_agents_path)
        failures.extend(
            missing_terms(
                "global AGENTS",
                global_agents_text,
                [
                    "Global Codex Task Entry Rule",
                    "100% task-start contract",
                    "hookless",
                    "exact visible shape",
                    "LOCKED_ROUTE_NODE",
                    "task_route_dispatcher.py run-plan",
                    "same task through `workflow-skill`",
                    "adaptive-routing",
                ],
            )
        )
    failures.extend(
        missing_terms(
            "global entry asset",
            entry_asset_text,
            [
                "hookless workflow",
                "100% task-start contract",
                "LOCKED_ROUTE_NODE",
                "same task through `workflow-skill`",
                "adaptive-routing history",
                "resolve_entry_model.py",
                "preserve its exact verified pair",
            ],
        )
    )
    if global_hooks_path.exists() and "task_entry_hook.py" in read_text(global_hooks_path):
        failures.append(f"obsolete Task Analyze lifecycle hook is still installed: {global_hooks_path}")
    nested_skill_files = [path for path in global_skills_root.rglob("SKILL.md") if ".system" not in path.relative_to(global_skills_root).parts and path.parent.parent != global_skills_root]
    if nested_skill_files:
        failures.append(f"loader-visible nested SKILL.md files remain under global skills: {len(nested_skill_files)}")
    capability_status = sync_model_capabilities.check_snapshot(models_cache_path.expanduser().resolve(), read_text(paths["references/model-capabilities.md"]))
    if not capability_status["valid"]:
        failures.append(f"model-capabilities.md failed capability check: {capability_status['status']}")
    installed = installed_skills(skill_dir)
    plans = sample_plans()
    expected_plan_count = sum(len(efforts) for efforts in MODEL_EFFORTS.values())
    if len(plans) != expected_plan_count:
        failures.append(f"sample plans do not cover all supported entry pairs (expected {expected_plan_count}, got {len(plans)})")
    if len({(plan["nodes"][0]["model"], plan["nodes"][0]["effort"]) for plan in plans.values()}) != expected_plan_count:
        failures.append("sample plans do not cover arbitrary supported entry model + effort")
    if not any(plan["complexity"] == "complex" for plan in plans.values()):
        failures.append("sample plans must include at least one complex route")
    plan_results = []
    for name, plan in plans.items():
        plan_failures = validate_plan(plan, installed)
        plan_results.append({"name": name, "status": "pass" if not plan_failures else "fail", "failures": plan_failures})
        failures.extend([f"plan {name}: {failure}" for failure in plan_failures])
    return {"valid": not failures, "skill_dir": str(skill_dir), "capability_status": capability_status, "plans": plan_results, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description="Validate independent Task Analyze routing and runtime-receipt contracts.")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--models-cache", type=Path, default=Path.home() / ".codex" / "models_cache.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--global-agents", type=Path, default=Path.home() / ".codex" / "AGENTS.md")
    parser.add_argument("--global-skills-root", type=Path, default=Path.home() / ".codex" / "skills")
    args = parser.parse_args()
    result = validate(args.skill_dir.resolve(), args.models_cache.resolve(), args.global_agents.resolve(), args.global_skills_root.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for plan in result["plans"]:
        print(f"task-analyze-skill plan {plan['name']}: {plan['status']}")
    if result["failures"]:
        print("Failures:", file=sys.stderr)
        for failure in result["failures"]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

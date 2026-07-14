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
        MODEL_EFFORTS,
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
    MODEL_EFFORTS = _routing_policy.MODEL_EFFORTS
    expected_owner_skill = _routing_policy.expected_owner_skill
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    is_tiny_spark_profile = _routing_policy.is_tiny_spark_profile
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry


INLINE_ROUTE_PREFIX = ["inline-current-model"]
ACTIVATED_INLINE_ROUTE_PREFIX = ["task-analyze-skill", "inline-current-model"]
BENCHMARK_ROUTE_PREFIX = ["task-analyze-skill", "benchmark runner"]
ADMITTED_ROUTE_PREFIX = ["task-analyze-skill", "workflow-skill"]
ACTIVE_MODEL_ORDER = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
ACTIVE_MODEL_EFFORTS = {model: MODEL_EFFORTS[model] for model in ACTIVE_MODEL_ORDER}
LEGACY_SPARK_MODEL = "gpt-5.3-codex-spark"
REQUIRED_WORKFLOW = [
    "one Obsidian-context Spark-first producer with a selected 5.6 fallback",
    "performance-admitted locked multi-node route",
    "Ineligible ordinary work remains inline",
    "universal Ending lifecycle after presentation",
    "comparable end-to-end admission evidence",
    "complete Global foreground path includes entry/controller plus child costs",
    "frozen, receipt-backed, Real-passing, and `trial=false`",
    "current entry model may execute inline",
    "not controller-only",
    "exact model and effort for each delegated node",
    "matching sanitized receipt",
    "Obsidian `Projects/<project-key>/ModelExperience`",
    "project/task/module/file/symbol/code",
    "obsidian_adaptive_model_runner.py",
    "Only a real graph with at least two model-executed nodes saves private schema-2 JSON",
    "Ending Real alone records receipt-backed pass/fail to Obsidian",
    "Spark attempt evidence to Obsidian",
    "Old local `model_experience.json` and legacy `model_routing_history.py` remain read-only compatibility only",
    "End-to-end performance admission remains separate",
    "Continue in the same task",
    "no hook is used",
    "complex admitted graph: task-specific Mermaid",
    "Workflow with models",
    "Every active registry-owned code-domain node loads `code-skill`",
    "Do not run Mini/Fast Verify before the user first sees the result",
    "show the main result immediately",
    "Ending Task begins only after the main result",
    "mandatory for read-only/write and simple/complex work",
    "bypasses result-producing performance admission",
    "Ending worker starts with `ENDING_TASK_WORKER`",
    "lifecycle ledger must report `PASS` or explicit `BLOCKED`",
    "repair as a new child lifecycle",
    "Real Verify",
    "independent optimization verification",
    "must not silently substitute another pair",
    "Runtime Receipt And Learning",
    "suite total never converts a losing class into a pass",
    "Ending Real time is separate",
    "stage=result-ready",
    "launch the CLI as an ongoing session",
    "Never wait for the final receipt manifest",
]
REQUIRED_TEMPLATE = ["Admitted Workflow Display Templates", "Ordinary requests", "stay inline on the current model", "## Admitted Single Node: Text Only", "## Admitted Complex Graph: Mermaid", "current selected model | current selected effort", "Show main result now", "Dispatch Ending Task", "Real Verify", "Independent optimization verification", "Main Result always precedes Ending Task", "Workflow With Models"]
REQUIRED_MATRIX = ["Ordinary requests stay on the current model regardless of apparent complexity", "never load full `task-analyze-skill` or `workflow-skill`", "activation still returns to inline", "Workflow executes admitted routes only", "ordinary-direct", "explicit-routing-no-admission", "admitted-single", "admitted-complex", "Every active registry-owned code-domain implementation uses `code-skill`", "Main Result precedes all verification", "background correctness failure", "--direct-task", "--bootstrap-task"]
REQUIRED_CODE = ["Obsidian-context Spark-first producer with a selected 5.6 fallback", "Obsidian `Projects/<project-key>/ModelExperience`", "project/task/module/file/symbol/code", "Easy text code tries Spark-low", "complex text code tries Spark-high", "zero-result, zero-token operational Spark failure", "new 5.6 repair lifecycle", "Old local `model_experience.json` remains legacy read-only", "mandatory post-result Ending lifecycle still runs", "After presentation, always start the independent Ending lifecycle", "different `verify-skill` worker performs independent verification"]
REQUIRED_VERIFY = ["Verification has one category", "Real Verify", "Every user task launches an independent post-result Ending lifecycle", "Never add Mini/Fast Verify before the user's first presentation", "current user-selected model", "PASS or explicit BLOCKED", "different optimizer/verifier identities", "reopen"]
REQUIRED_OPTIMIZATION = ["Do not infer optimization from repeated benchmark arms or exact-scoped read-only work", "Use this skill directly only when the user requests optimization", "current model and no foreground verifier", "positively admitted", "different verifier", "before/after", "--direct-task", "--bootstrap-task", "neither arm enters Task Analyze context"]
REQUIRED_MANAGEMENT = ["Do not load this skill for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms", "directly only for an explicit routing-record", "admitted a delegated route", "Projects/<project-key>/ModelExperience", "project/task/module/file/symbol/code", "obsidian_model_memory.py", "Ending Real", "matched producer receipt", "legacy read-only", "Never push/sync/publish unless the user explicitly requested publishing"]
REQUIRED_ENTRY = [
    "# Task Lifecycle",
    "Merge this section into `~/.codex/AGENTS.md`",
    "Eligible text/code producers read shared ladder",
    "Obsidian `Projects/<key>/ModelExperience`",
    "local JSON stays read-only",
    "Spark first: easy=low, complex=high",
    "Zero-result operational failure uses current 5.6 pair",
    "publish, then return",
    "Prompt/AI-instruction work loads `prompt-skill`",
    "durable edits load `project-memory-skill`",
    "recall first",
    "record reason/result/verification/files after Ending",
    "Every non-ENDING_TASK_WORKER task",
    "Ending start receipt",
    "independent Ending subagent",
    "Ending Real writes the receipt-backed outcome to Obsidian",
    "Parallelize isolated logs/docs",
    "Final requires PASS or BLOCKED",
    "quality/correctness failure",
    "new 5.6 repair lifecycle",
    "re-present",
    "different verifier",
    "No hook",
    "Exact read-only uses one bounded rg per authoritative file, anchored to exact members",
    "resolve aliases",
    "no subagent/route/plan, guesses, unrelated skills, broad search, reread, full-file read, or pre-result check",
]
REQUIRED_SELECTION = ["assets/model-capability-ladder.json", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol", "Obsidian `Projects/<project-key>/ModelExperience`", "project/task/module/file/symbol/code context", "Ending Real alone writes the verdict", "eligible text/code result producers try Spark-low for easy work or Spark-high for complex work", "old local `model_experience.json` stays legacy read-only", "Exact read-only stays inline", "obsidian_adaptive_model_runner.py", "Multi-node strategy remains separately performance-admitted"]
REQUIRED_ADAPTIVE = ["project/task/module/file/symbol/code context", "assets/model-capability-ladder.json", "Obsidian `Projects/<project-key>/ModelExperience`", "Ending Real alone stores sanitized producer receipts", "Old local `model_experience.json` is legacy read-only only", "Spark is a priority attempt, not a rung in the 5.6 quality ladder", "zero-result, zero-token operational failure", "Evidence does not cross project keys", "obsidian_adaptive_model_runner.py", "`strategy_performance.py` remains separate", "Ending Real alone records the matching producer pass/fail to Obsidian", "read-only compatibility surfaces only"]
REQUIRED_OBSIDIAN_RUNNER = ["project-memory-skill", "obsidian_model_memory.py", "obsidian_model_memory.recommend_model", "model_execution_receipt.adaptive_producer_authorization", "node_role=\"result-producer\"", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "immediate_operational_fallback", "ending_real_status"]
REQUIRED_OBSIDIAN_MEMORY = ["DEFAULT_LADDER", "model-capability-ladder.json", "Projects", "ModelExperience", "task_type", "module", "file", "symbol", "code_kind", "modality", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "recommend_model", "record_model_result", "receipt_status", "turn_completed", "model_match", "effort_match"]
REQUIRED_STRATEGY_PERFORMANCE = ["DEFAULT_MINIMUM_PAIRED_SAMPLES = 6", "DEFAULT_MINIMUM_SAVINGS_PERCENT = 0.0", "DEFAULT_MAXIMUM_PAIR_REGRESSION_PERCENT = 5.0", "MAXIMUM_PAIRED_TIME_REGRESSION_MS", "evaluate_paired_metric", "aggregate_totals_pass", "regression_bounds_pass", "strict_pareto_win", "delegated_adaptive", "inline_entry", "workload_prompt_sha256", "entry_pair", "config_cohort"]
FORBIDDEN = ["observable entry model and effort belong only to Task Analyze and route coordination", "selected entry model and effort run Task Analyze and route coordination only", "Every route begins with independent `task-analyze-skill`", "Registry-owned code-domain executor selected in the locked task-analyze-skill plan", "Use this as the verification executor named by the locked `task-analyze-skill` plan", "Use this skill only when the locked `task-analyze-skill` plan", "internal Task Analyze", "not a sixth top-level skill", "Task Analyze itself uses `GPT-5.6-Sol`", "Task Analyze still runs on Sol", "correctness-affecting Real Verify stays before", "Real Verify always stays before Main Goal Done", "approved five", "five-folder boundary", "private ledger remains authoritative", "Learning is shared across projects", "generalized task-type conditions"]
NEGATIVE_DESCRIPTION_PREFIXES = {"code": "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction", "verify": "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify", "optimization": "Do not infer optimization from repeated benchmark arms or exact-scoped read-only work", "management": "Do not use for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms"}
NEGATIVE_AGENT_PREFIXES = {"code_agent": "$code-skill: exact read-only lookup/audit stays skill-free", "verify_agent": "$verify-skill: every user task launches an independent post-result Ending lifecycle", "optimization_agent": "$optimization-skill: do not load from benchmark repetition alone or for exact-scoped read-only work", "management_agent": "$management-skill: do not load for ordinary exact-scoped read-only work or benchmark worker arms"}


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


def folded_prompt_text(text):
    match = re.search(r"^  default_prompt:\s*>-?\s*\n((?:    .*\n?)+)", text, flags=re.MULTILINE)
    return " ".join(line.strip() for line in match.group(1).splitlines()).strip() if match else None


def folded_prompt_length(text):
    prompt = folded_prompt_text(text)
    return len(prompt) if prompt is not None else None


def missing_terms(label, text, required):
    normalized = re.sub(r"\s+", " ", text).lower()
    return [f"{label} missing required contract: {term}" for term in required if re.sub(r"\s+", " ", term).lower() not in normalized]


def legacy_only_failures(label, text):
    failures = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        marker = "model_experience.json"
        if marker in lowered and not ("legacy" in lowered and "read-only" in lowered):
            failures.append(f"{label}:{line_number} references {marker} without legacy read-only scope")
    return failures


def validate_shared_ladder(text):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ["shared model-capability ladder is invalid JSON"]
    models = payload.get("models") if isinstance(payload.get("models"), list) else []
    model_ids = [model.get("id") for model in models if isinstance(model, dict)]
    failures = []
    if payload.get("scope") != "shared_non_personal":
        failures.append("shared model-capability ladder must remain non-personal")
    if model_ids != list(ACTIVE_MODEL_ORDER):
        failures.append("shared model-capability ladder must contain only ordered Luna, Terra, and Sol")
    if LEGACY_SPARK_MODEL in model_ids:
        failures.append("Spark must not be an active shared-ladder rung")
    spark = payload.get("spark_first")
    if not isinstance(spark, dict) or spark.get("id") != LEGACY_SPARK_MODEL or spark.get("adaptive_efforts") != ["low", "high"]:
        failures.append("shared model-capability ladder must define Spark low/high priority attempts")
    elif spark.get("effort_by_complexity") != {"easy": "low", "complex": "high"} or spark.get("eligible_modalities") != ["text"]:
        failures.append("shared Spark priority eligibility is invalid")
    if isinstance(spark, dict) and (spark.get("operational_fallback") != "current_obsidian_5_6_pair" or spark.get("quality_failure") != "record_to_obsidian_then_new_5_6_repair_lifecycle"):
        failures.append("shared Spark failure contract is invalid")
    return failures


def validate_graduated_fixture(path, skills_root, require_installed):
    fixture_globals = validate_fixture.__globals__
    dispatcher_factory = fixture_globals.get("_dispatcher_module")
    if dispatcher_factory is None:
        return validate_fixture(path, skills_root, require_installed)

    def active_dispatcher_factory():
        dispatcher = dispatcher_factory()
        if not hasattr(dispatcher, "MODEL_EFFORTS"):
            dispatcher.MODEL_EFFORTS = ACTIVE_MODEL_EFFORTS
        return dispatcher

    fixture_globals["_dispatcher_module"] = active_dispatcher_factory
    try:
        return validate_fixture(path, skills_root, require_installed)
    finally:
        fixture_globals["_dispatcher_module"] = dispatcher_factory


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


def can_show_main_result(requested_work_done):
    return bool(requested_work_done)


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
        if node.get("model") == LEGACY_SPARK_MODEL:
            failures.append(f"{node.get('id', '<unknown>')} Spark is injected only as a result-producer attempt and cannot be a plan node")
        elif node.get("model") and node.get("model") not in ACTIVE_MODEL_ORDER:
            failures.append(f"{node.get('id', '<unknown>')} model is outside the active shared GPT-5.6 ladder")
        if resolve_skill_path(node.get("skill"), skills_root) is None:
            failures.append(f"{node.get('id', '<unknown>')} names unavailable skill {node.get('skill')}")
    result_index = ids.index("main-result") if "main-result" in ids else -1
    ending_index = ids.index("ending-dispatch") if "ending-dispatch" in ids else -1
    if not (0 <= result_index < ending_index) or "mini-verify" in ids:
        failures.append("expected Main Result < Ending dispatch with no foreground Mini")
    for index, node in enumerate(trace):
        requested_verification_result = node.get("user_requested_verification_result")
        is_result_side_verifier = node.get("skill") == "verify-skill" and 0 <= index <= result_index
        if is_result_side_verifier and requested_verification_result is not True:
            failures.append(f"{node.get('id', '<unknown>')} foreground verify-skill requires user_requested_verification_result=true")
        elif "user_requested_verification_result" in node and not is_result_side_verifier:
            failures.append(f"{node.get('id', '<unknown>')} user_requested_verification_result is valid only for user-requested verification before Main Result")
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
    return {"name": name, "status": "pass" if not failures else "fail", "failures": failures}


def sample_traces():
    easy = [{"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill"}, {"id": "direct", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "real-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"}, {"id": "records", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}]
    complex_code = [{"id": "task-analyze", "model": "gpt-5.6-sol", "effort": "ultra", "skill": "task-analyze-skill"}, {"id": "audit", "model": "gpt-5.6-terra", "effort": "high", "skill": "workflow-skill"}, {"id": "implement", "model": "gpt-5.6-terra", "effort": "high", "skill": "code-skill", "language": "python", "purpose": "implement", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "medium", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "medium", "skill": "workflow-skill"}, {"id": "real-verify", "model": "gpt-5.6-terra", "effort": "high", "skill": "verify-skill"}, {"id": "optimization-verify", "model": "gpt-5.6-terra", "effort": "high", "skill": "verify-skill"}, {"id": "records", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}]
    terra_entry = [{"id": "task-analyze", "model": "gpt-5.6-terra", "effort": "medium", "skill": "task-analyze-skill"}, {"id": "direct", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"}, {"id": "real-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"}]
    return {"admitted-single-luna-entry": easy, "admitted-complex-sol-ultra-entry": complex_code, "admitted-single-terra-entry": terra_entry}


def validate(skill_dir):
    global_root = skill_dir.parent
    paths = {
        "workflow": skill_dir / "SKILL.md",
        "agent": skill_dir / "agents" / "openai.yaml",
        "template": skill_dir / "references" / "start-diagram-template.md",
        "matrix": skill_dir / "references" / "routing-matrix.md",
        "code": global_root / "code-skill" / "SKILL.md",
        "code_agent": global_root / "code-skill" / "agents" / "openai.yaml",
        "verify": global_root / "verify-skill" / "SKILL.md",
        "verify_agent": global_root / "verify-skill" / "agents" / "openai.yaml",
        "optimization": global_root / "optimization-skill" / "SKILL.md",
        "optimization_agent": global_root / "optimization-skill" / "agents" / "openai.yaml",
        "management": global_root / "management-skill" / "SKILL.md",
        "management_agent": global_root / "management-skill" / "agents" / "openai.yaml",
        "task_analyze": global_root / "task-analyze-skill" / "SKILL.md",
        "task_analyze_entry_rule": global_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md",
        "task_analyze_ladder": global_root / "task-analyze-skill" / "assets" / "model-capability-ladder.json",
        "task_analyze_selection": global_root / "task-analyze-skill" / "references" / "model-selection.md",
        "task_analyze_adaptive": global_root / "task-analyze-skill" / "references" / "adaptive-routing.md",
        "task_analyze_obsidian_runner": global_root / "task-analyze-skill" / "scripts" / "obsidian_adaptive_model_runner.py",
        "project_model_memory": global_root / "project-memory-skill" / "scripts" / "obsidian_model_memory.py",
        "task_analyze_strategy_performance": global_root / "task-analyze-skill" / "scripts" / "strategy_performance.py",
        "global_agents": global_root.parent / "AGENTS.md",
    }
    failures = []
    for label, path in paths.items():
        if not path.exists():
            failures.append(f"missing {label}: {path}")
    if failures:
        return {"failures": failures, "routes": [], "gates": [], "traces": [], "graduated": []}
    texts = {label: read_text(path) for label, path in paths.items()}
    metadata = parse_frontmatter(texts["workflow"])
    if set(metadata) != {"name", "description"} or metadata.get("name") != "workflow-skill":
        failures.append("workflow frontmatter must contain only name=workflow-skill and description")
    if len(metadata.get("description", "")) > 1024:
        failures.append("workflow frontmatter description exceeds 1024 characters")
    prompt_length = folded_prompt_length(texts["agent"])
    if prompt_length is None or prompt_length > 1024:
        failures.append(f"workflow agent default_prompt invalid length: {prompt_length}")
    for label, expected_name in (("code", "code-skill"), ("verify", "verify-skill"), ("optimization", "optimization-skill"), ("management", "management-skill")):
        executor_metadata = parse_frontmatter(texts[label])
        if set(executor_metadata) != {"name", "description"} or executor_metadata.get("name") != expected_name:
            failures.append(f"{expected_name} frontmatter must contain only name and description")
        if len(executor_metadata.get("description", "")) > 1024:
            failures.append(f"{expected_name} frontmatter description exceeds 1024 characters")
        expected_prefix = NEGATIVE_DESCRIPTION_PREFIXES[label]
        if not executor_metadata.get("description", "").lower().startswith(expected_prefix.lower()):
            failures.append(f"{expected_name} description must begin with the exact-scoped read-only negative preselection boundary: {expected_prefix}")
    failures.extend(missing_terms("workflow agent", texts["agent"], ["eligible text/code producers", "try Spark first", "easy low; complex high", "selected 5.6 pair as zero-result operational fallback", "Published output returns immediately", "Ending Real alone records", "quality/correctness failure", "new 5.6 repair lifecycle", "different verifier", "Local model_experience.json stays legacy read-only", "Multi-node JSON and savings need separate end-to-end admission", "independent Ending subagent", "isolated logs/docs run in parallel", "Final needs PASS or BLOCKED", "Ending time is outside first-result time", "No hook", "exposed machine plan"]))
    failures.extend(missing_terms("workflow", texts["workflow"], REQUIRED_WORKFLOW))
    failures.extend(missing_terms("template", texts["template"], REQUIRED_TEMPLATE))
    failures.extend(missing_terms("matrix", texts["matrix"], REQUIRED_MATRIX))
    failures.extend(missing_terms("code-skill", texts["code"], REQUIRED_CODE))
    failures.extend(missing_terms("verify-skill", texts["verify"], REQUIRED_VERIFY))
    failures.extend(missing_terms("optimization-skill", texts["optimization"], REQUIRED_OPTIMIZATION))
    failures.extend(missing_terms("management-skill", texts["management"], REQUIRED_MANAGEMENT))
    for label in ("code_agent", "verify_agent", "optimization_agent", "management_agent"):
        agent_prompt_length = folded_prompt_length(texts[label])
        if agent_prompt_length is None or agent_prompt_length > 1024:
            failures.append(f"{label} default_prompt invalid length: {agent_prompt_length}")
        prompt_text = folded_prompt_text(texts[label]) or ""
        expected_prefix = NEGATIVE_AGENT_PREFIXES[label]
        if not prompt_text.lower().startswith(expected_prefix.lower()):
            failures.append(f"{label} default_prompt must begin with the exact-scoped read-only negative preselection boundary: {expected_prefix}")
    failures.extend(missing_terms("code-skill agent", texts["code_agent"], ["exact read-only lookup/audit stays skill-free", "Implementation, edit, debug, refactor, or authored tests", "Try Spark first", "easy low; complex high", "zero-result operational failure uses the selected 5.6 pair", "Return published code immediately", "Ending Real alone records", "correctness/quality failure", "new 5.6 repair lifecycle", "different verifier", "Local model_experience.json stays legacy read-only", "independent Ending", "no foreground verify", "Ending time is outside first-result time"]))
    failures.extend(missing_terms("verify-skill agent", texts["verify_agent"], ["every user task launches an independent post-result Ending lifecycle", "Never add Mini/Fast Verify before first presentation", "producer shows the completed result", "record lifecycle started", "proportional Real Verify", "isolated logs/docs may run in parallel", "PASS or explicit BLOCKED opens the final gate", "persist lifecycle evidence", "before a new repair child", "different Ending verifier", "Ending time is separate"]))
    failures.extend(missing_terms("optimization-skill agent", texts["optimization_agent"], ["do not load from benchmark repetition alone", "user-requested optimization", "explicitly authorized reusable improvement", "positively admitted node", "present the optimized result immediately", "no foreground Mini/Fast Verify", "different Ending Real verifier", "Ending time is excluded from first-result time", "never self-certify savings"]))
    failures.extend(missing_terms("management-skill agent", texts["management_agent"], ["do not load for ordinary exact-scoped read-only work or benchmark worker arms", "explicit management request or admitted node", "Obsidian Projects/<project-key>/ModelExperience", "obsidian_model_memory.py", "local model_experience.json and central TaskModelExperience are legacy read-only", "Eligible text/code tries Spark low/high first", "operational failure is neutral and quality failure starts a new 5.6 repair", "Ending Real alone records a matched producer verdict", "never publish private state"]))
    failures.extend(missing_terms("task-analyze-entry-rule", texts["task_analyze_entry_rule"], REQUIRED_ENTRY))
    failures.extend(missing_terms("task-analyze-model-selection", texts["task_analyze_selection"], REQUIRED_SELECTION))
    failures.extend(missing_terms("task-analyze-adaptive", texts["task_analyze_adaptive"], REQUIRED_ADAPTIVE))
    failures.extend(missing_terms("task-analyze Obsidian runner", texts["task_analyze_obsidian_runner"], REQUIRED_OBSIDIAN_RUNNER))
    failures.extend(missing_terms("project Obsidian model memory", texts["project_model_memory"], REQUIRED_OBSIDIAN_MEMORY))
    failures.extend(missing_terms("separate multi-node strategy performance", texts["task_analyze_strategy_performance"], REQUIRED_STRATEGY_PERFORMANCE))
    failures.extend(validate_shared_ladder(texts["task_analyze_ladder"]))
    for label in ("task_analyze_obsidian_runner", "project_model_memory"):
        if "model_experience.json" in texts[label] or "local/adaptive-routing" in texts[label]:
            failures.append(f"{label} must not fall back to local model_experience.json")
    for label in ("workflow", "code", "management", "task_analyze", "task_analyze_selection", "task_analyze_adaptive"):
        failures.extend(legacy_only_failures(label, texts[label]))
    entry_body = texts["task_analyze_entry_rule"].replace("Merge this section into `~/.codex/AGENTS.md`.\n\n", "", 1)
    if len(entry_body.encode("utf-8")) > 1024:
        failures.append(f"global entry bootstrap exceeds compact limit: {len(entry_body.encode('utf-8'))} > 1024 bytes")
    if entry_body != texts["global_agents"]:
        failures.append("global entry asset does not exactly match global AGENTS after removing its merge directive")
    live_text = "\n".join(texts.values())
    for forbidden in FORBIDDEN:
        if forbidden.lower() in live_text.lower():
            failures.append(f"live contract contains obsolete text: {forbidden}")
    for obsolete_path in (skill_dir / "references" / "model-capabilities.md", skill_dir / "references" / "major-task-model-manager.md", skill_dir / "scripts" / "sync_model_capabilities.py"):
        if obsolete_path.exists():
            failures.append(f"Task Analyze-owned file remains under workflow-skill: {obsolete_path}")
    routes = parse_routes(texts["matrix"])
    route_results = []
    ordinary_routes = {"ordinary-direct", "open-chrome", "open-youtube", "search-cctv-on-youtube", "design-youtube-like-website", "ordinary-code-domain"}
    activated_inline_routes = {"explicit-routing-no-admission", "task-analyze-maintenance-no-admission"}
    admitted_routes = {"admitted-single", "admitted-complex"}
    for name, route in routes.items():
        expected_prefix = INLINE_ROUTE_PREFIX if name in ordinary_routes else ACTIVATED_INLINE_ROUTE_PREFIX if name in activated_inline_routes else BENCHMARK_ROUTE_PREFIX if name == "explicit-benchmark" else ADMITTED_ROUTE_PREFIX if name in admitted_routes else []
        route_failures = [] if route[:len(expected_prefix)] == expected_prefix else [f"route must begin {expected_prefix}, got {route[:len(expected_prefix)]}"]
        if name in {"ordinary-code-domain", "task-analyze-maintenance-no-admission"} and "code-skill" not in route:
            route_failures.append("registered code-domain route bypasses code-skill")
        route_results.append({"name": name, "status": "pass" if not route_failures else "fail", "route": route, "failures": route_failures})
        failures.extend([f"route {name}: {failure}" for failure in route_failures])
    gate_results = [{"name": "requested-work-done", "observed": can_show_main_result(True), "expected": True}, {"name": "requested-work-not-done", "observed": can_show_main_result(False), "expected": False}]
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
    graduated_failures = validate_graduated_fixture(fixture_path, global_root, True)
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

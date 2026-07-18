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
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry

try:
    from model_registry import load_registry, validate_registry
except ModuleNotFoundError:
    _model_registry_spec = importlib.util.spec_from_file_location("task_analyze_model_registry", TASK_ANALYZE_SCRIPTS / "model_registry.py")
    _model_registry = importlib.util.module_from_spec(_model_registry_spec)
    _model_registry_spec.loader.exec_module(_model_registry)
    load_registry = _model_registry.load_registry
    validate_registry = _model_registry.validate_registry


EXPECTED_ROUTE_PREFIXES = {
    "ordinary-production": ["entry bootstrap", "adaptive producer"],
    "exact-one-source-read": ["one bounded inline read", "result"],
    "tool-only-action": ["inline tool", "result"],
    "image-or-mixed": ["inline owning image/tool skill", "result"],
    "prompt-production": ["adaptive producer", "prompt-skill"],
    "ordinary-code-domain": ["adaptive producer", "code-skill"],
    "independent-small-sources": ["entry bootstrap", "one adaptive producer"],
    "independent-large-sources": ["entry bootstrap", "admitted source graph"],
    "dependent-multi-file": ["one adaptive producer", "owning skill"],
    "explicit-routing-no-graph": ["Task Analyze", "one contextual producer"],
    "task-analyze-maintenance": ["adaptive producer", "Task Analyze"],
    "explicit-benchmark": ["Task Analyze", "fixed Direct and receipt-proven Auto arms"],
    "admitted-complex": ["Task Analyze", "Workflow"],
}
MODEL_REGISTRY = load_registry()
ACTIVE_MODEL_ORDER = tuple(model["id"] for model in MODEL_REGISTRY["models"])
ACTIVE_MODEL_EFFORTS = {model["id"]: tuple(model["codex_efforts"]) for model in MODEL_REGISTRY["models"]}
PRIORITY_PRODUCER = MODEL_REGISTRY.get("priority_producer")
PRIORITY_PRODUCER_MODEL = PRIORITY_PRODUCER.get("id") if isinstance(PRIORITY_PRODUCER, dict) else None
REQUIRED_WORKFLOW = [
    "one Obsidian-context adaptive quality producer with a one-rung-stronger operational fallback",
    "performance-admitted locked multi-node route",
    "Ineligible ordinary work remains inline",
    "universal Ending lifecycle after presentation",
    "comparable end-to-end admission evidence",
    "Direct task versus Auto task",
    "Auto task + Ending",
    "excluded routing diagnostic",
    "frozen, receipt-backed, Real-passing, and `trial=false`",
    "must call `obsidian_adaptive_model_runner.py` once, including cold start",
    "reads the saved shared contract unchanged",
    "Ordinary tasks do not scan or refresh the local model cache",
    "Only an explicit user model-update request",
    "never fetch models over the network",
    "preserve the saved contract when the local cache is unavailable",
    "not controller-only",
    "exact model and effort for each delegated node",
    "matching sanitized receipt",
    "Obsidian broad `Model Switch.md`",
    "project/task/module/file/symbol/code",
    "obsidian_adaptive_model_runner.py",
    "Only a real graph with at least two model-executed nodes saves private schema-2 JSON",
    "initial-attempt evidence to Obsidian automatically",
    "sole current contextual experience authority",
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
    "A repair requires a new explicit user task",
    "Real Verify",
    "independent optimization verification",
    "must not silently substitute another pair",
    "Runtime Receipt And Learning",
    "Start it with `--producer-receipt`",
    "terminal ledger event automatically records receipt-backed pass/fail",
    "suite total never converts a losing class into a pass",
    "Ending Real time is separate",
    "stage=result-ready",
    "launch the CLI as an ongoing session",
    "Never wait for the final receipt manifest",
    "when `create_thread` is callable",
    "If thread tools are unavailable",
    "outer host creates the End Task",
    "never inspect app-server schemas/commands",
    "Tool absence must end the producer session",
]
REQUIRED_TEMPLATE = ["Admitted Workflow Display Templates", "Eligible ordinary production uses the compact adaptive runner but shows no pre-result route", "Exact one-source, tool-only, and image/mixed work stay inline", "## Admitted Single Node: Text Only", "## Admitted Complex Graph: Mermaid", "current selected model | current selected effort", "Show main result now", "Dispatch Ending Task", "Real Verify", "Independent optimization verification", "Main Result always precedes Ending Task", "Workflow With Models", "repair requires a new explicit task"]
REQUIRED_MATRIX = ["# Adaptive And Admitted Routing Matrix", "Eligible ordinary text/code production enters the compact adaptive runner exactly once", "Two or three independent read-only sources first cost-admit one contextual producer versus a graph", "`workflow-skill` executes only a positively admitted multi-node or locked route", "ordinary-production", "independent-small-sources", "independent-large-sources", "dependent-multi-file", "explicit-routing-no-graph", "explicit-benchmark", "admitted-complex", "One receipt-valid Real PASS retains the selected pair", "two matched PASS outcomes try one lower rung", "quality failure upgrades one rung", "Spark is schedule-source-only", "Direct uses the exact raw prompt", "public two-world comparison", "dispatcher/controller is disclosed but excluded", "--direct-task", "--bootstrap-task"]
REQUIRED_CODE = ["Obsidian-context catalog-derived quality pair", "Obsidian broad `Model Switch.md`", "project/task/module/file/symbol/code", "One Real PASS retains the pair", "two PASS results downgrade one rung", "quality FAIL upgrades one rung", "Spark is reserved for fixed disjoint-source schedule branches", "zero-result operational failure", "Old local `model_experience.json` remains legacy read-only", "mandatory post-result Ending lifecycle still runs", "When `create_thread` is callable", "When thread tools are unavailable", "outer host immediately", "Never inspect app-server internals", "same-task Ending subagent", "different `verify-skill` worker performs independent verification"]
REQUIRED_VERIFY = ["Verification has two scopes", "Ending handoff audit", "Every non-Ending user task creates that separate persistent Codex thread", "Never add Mini/Fast Verify before the user's first presentation", "current user-selected model", "PASS or explicit BLOCKED", "no extra tests, APIs, broad regression, user questions, waits, or automatic repair", "new explicit user task"]
REQUIRED_OPTIMIZATION = ["Do not infer optimization from repeated benchmark arms or exact-scoped read-only work", "Use this skill directly only when the user requests optimization", "catalog-derived adaptive producer", "positively admitted", "different verifier", "before/after", "producer receipt", "--direct-task", "--bootstrap-task", "neither arm enters Task Analyze context"]
REQUIRED_MANAGEMENT = ["Do not load this skill for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms", "directly only for an explicit routing-record", "admitted a delegated route", "broad Model Switch.md", "project/task/module/file/symbol/code", "obsidian_model_memory.py", "Ending Real starts with the producer receipt", "terminal ledger event records the result automatically", "legacy read-only", "Never push/sync/publish unless the user explicitly requested publishing"]
REQUIRED_ENTRY = ["# Task Lifecycle", "Merge this section into `~/.codex/AGENTS.md`", "pipe exact user text once via `/usr/bin/python3", "non-TTY", "obsidian_adaptive_model_runner.py", "before skills/memory/files", "except one-source exact read-only", "Wait 60s", "session id:resume once <=60s", "return result/pending", "NEVER spawn/read", "Receipt nodes direct", "never re-enter runner", "Saved ladder", "model-update refreshes cache", "never fetch", "Missing Obsidian:saved cold start,no block", "Auto=saved pair", "2 Real PASS:down 1 rung", "quality FAIL:up 1", "zero-result:stronger fallback", "Spark:schedule sources only", "2-3 sources cost-admit before reads", "single or fused graph", "dependent multi-file:one producer", "Producer owns files/skills/Mini Test", "light smoke", "heavy/API/large/side-effect checks syntax+names/references", "create/link `End Task-{task name}` if available", "never subtask/emulate/wait/self-verify", "Ending <=60s evidence-only", "never gates", "Benchmark 3 tiers", "`gpt-5.6-sol|ultra`", "Direct fixed/no verify", "Auto receipt=child/graph", "task vs task+Ending", "controller excluded", "Complex stage pairs", "Exact one-source read-only:one bounded rg/file", "no reread/full read/precheck", "No hook", "Final PASS/BLOCKED Ending-only"]
REQUIRED_SELECTION = ["# Catalog-Generated Model Selection", "assets/model-capability-ladder.json", "scripts/model_registry.py", "`~/.codex/models_cache.json`", "bootstrap it once", "Only an explicit user model-update request", "highest numeric GPT family", "Older numeric families remain catalog-only", "Obsidian broad `Model Switch.md`", "matching Obsidian broad `Model Switch.md` context", "terminal Ending event automatically records the matched producer verdict", "optional specialized schedule producer", "sole current contextual evidence authority", "Exact read-only", "obsidian_adaptive_model_runner.py", "Open-ended multi-node strategy and every savings claim remain separately performance-admitted"]
REQUIRED_ADAPTIVE = ["project/task/module/file/symbol/code context", "assets/model-capability-ladder.json", "last explicitly refreshed local Codex model order", "source digest", "Obsidian broad `Model Switch.md`", "sole active private authority", "contextual quality pair runs directly", "schedule-only for disjoint source branches", "zero-result, zero-token operational failure", "atomically bootstrapped from the local cache when missing", "Only an explicit user model-update request", "preserve the last valid registry", "Evidence never crosses project keys", "`strategy_performance.py` remains the separate authority", "Ending PASS/FAIL event automatically writes the producer outcome to Obsidian"]
REQUIRED_OBSIDIAN_RUNNER = ["project-memory-skill", "obsidian_model_memory.py", "obsidian_model_memory.recommend_model", "model_execution_receipt.adaptive_producer_authorization", "node_role=\"result-producer\"", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "immediate_operational_fallback", "ending_real_status", "resolve_fast_path_args", "hashlib.sha256", "explicit_fields", "fast_path", "adaptive-producer", "workspace-write", "scheduled_source_paths", "schedule_admission", "SINGLE_PRODUCER_SOURCE_BYTE_LIMIT", "single_producer_lower_estimated_logical_tokens", "parallel_independent_sources", "parallel_sources_fused_final", "fuses_owned_source_with_dependencies", "task_route_dispatcher.run_plan", "scheduled_result_node_count", "parallel_branch_count"]
REQUIRED_OBSIDIAN_MEMORY = ["DEFAULT_LADDER", "model-capability-ladder.json", "Model Switch.md", "task_type", "module", "file", "symbol", "code_kind", "modality", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "recommend_model", "record_model_result", "receipt_status", "turn_completed", "model_match", "effort_match"]
REQUIRED_STRATEGY_PERFORMANCE = ["DEFAULT_MINIMUM_PAIRED_SAMPLES = 6", "DEFAULT_MINIMUM_SAVINGS_PERCENT = 0.0", "DEFAULT_MAXIMUM_PAIR_REGRESSION_PERCENT = 5.0", "MAXIMUM_PAIRED_TIME_REGRESSION_MS", "evaluate_paired_metric", "aggregate_totals_pass", "regression_bounds_pass", "strict_pareto_win", "delegated_adaptive", "inline_entry", "workload_prompt_sha256", "entry_pair", "config_cohort"]
FORBIDDEN = ["observable entry model and effort belong only to Task Analyze and route coordination", "selected entry model and effort run Task Analyze and route coordination only", "Every route begins with independent `task-analyze-skill`", "Registry-owned code-domain executor selected in the locked task-analyze-skill plan", "Use this as the verification executor named by the locked `task-analyze-skill` plan", "Use this skill only when the locked `task-analyze-skill` plan", "internal Task Analyze", "not a sixth top-level skill", "Task Analyze itself uses `GPT-5.6-Sol`", "Task Analyze still runs on Sol", "correctness-affecting Real Verify stays before", "Real Verify always stays before Main Goal Done", "approved five", "five-folder boundary", "private ledger remains authoritative", "Learning is shared across projects", "generalized task-type conditions", "only ordered Luna, Terra, and Sol", "current 5.6 pair", "new 5.6 repair lifecycle", "auto-refreshed shared contract", "automatically refreshed shared contract", "passively refreshed shared contract", "priority-first producer", "try the optional priority producer first", "complete Global foreground path includes entry/controller plus child costs", "first_attempt_text_code_producer", "every visible, routable Codex model except the optional priority producer", "Obsidian selects from every current visible catalog model", "every visible supported non-priority catalog model from weakest to strongest"]
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
        if marker in lowered and "read-only" not in lowered:
            failures.append(f"{label}:{line_number} references {marker} without legacy read-only scope")
    return failures


def validate_shared_ladder(text):
    try:
        payload = json.loads(text)
        validate_registry(payload)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return [f"shared model-capability ladder is invalid: {error}"]
    models = payload["models"]
    model_ids = [model["id"] for model in models]
    failures = []
    active_family = payload.get("active_family")
    if not isinstance(active_family, dict) or active_family.get("selection") != "highest_numeric_gpt_family" or active_family.get("model_count") != len(models):
        failures.append("shared model-capability ladder must select exactly the highest numeric GPT family")
    else:
        family_id = active_family.get("id")
        if not isinstance(family_id, str) or any(model_id != family_id and not model_id.startswith(f"{family_id}-") for model_id in model_ids):
            failures.append("shared model-capability ladder contains a model outside its active numeric GPT family")
    catalog_models = payload.get("catalog_models")
    if not isinstance(catalog_models, list) or not catalog_models:
        failures.append("shared model-capability registry must preserve the visible catalog inventory")
    else:
        active_catalog_ids = {model.get("id") for model in catalog_models if isinstance(model, dict) and model.get("catalog_role") == "active_quality"}
        if active_catalog_ids != set(model_ids):
            failures.append("active quality ladder must exactly match active_quality catalog roles")
    if tuple(model_ids) != ACTIVE_MODEL_ORDER:
        failures.append("shared model-capability ladder quality models drifted from the active generated registry")
    for model in models:
        if tuple(model["codex_efforts"]) != ACTIVE_MODEL_EFFORTS.get(model["id"]):
            failures.append(f"shared model-capability ladder efforts drifted for {model['id']}")
    priority_producer = payload.get("priority_producer")
    observed_priority_model = priority_producer.get("id") if isinstance(priority_producer, dict) else None
    if observed_priority_model != PRIORITY_PRODUCER_MODEL:
        failures.append("shared model-capability ladder priority producer drifted from the active generated registry")
    if observed_priority_model in model_ids:
        failures.append("priority producer must remain outside the quality ladder")
    if isinstance(catalog_models, list) and observed_priority_model is not None and not any(model.get("id") == observed_priority_model and model.get("catalog_role") == "priority_producer" for model in catalog_models if isinstance(model, dict)):
        failures.append("priority producer must remain separately classified in the catalog inventory")
    if not isinstance(payload.get("source", {}).get("catalog_sha256"), str):
        failures.append("shared model-capability ladder must include the catalog source digest")
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
        if PRIORITY_PRODUCER_MODEL is not None and node.get("model") == PRIORITY_PRODUCER_MODEL:
            failures.append(f"{node.get('id', '<unknown>')} schedule producer is valid only for a disjoint source branch and cannot be a quality plan node")
        elif node.get("model") and node.get("model") not in ACTIVE_MODEL_ORDER:
            failures.append(f"{node.get('id', '<unknown>')} model is outside the active catalog-generated quality ladder")
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
    floor_model, floor_effort = MODEL_REGISTRY["role_pairs"]["floor"].split("|", 1)
    balanced_model, balanced_effort = MODEL_REGISTRY["role_pairs"]["balanced_default"].split("|", 1)
    complex_model, complex_effort = MODEL_REGISTRY["role_pairs"]["balanced_complex"].split("|", 1)
    frontier_model, frontier_effort = MODEL_REGISTRY["role_pairs"]["frontier_complex"].split("|", 1)
    middle_row = MODEL_REGISTRY["models"][len(MODEL_REGISTRY["models"]) // 2]
    middle_model, middle_effort = middle_row["id"], middle_row["default_effort"]
    easy = [{"id": "task-analyze", "model": floor_model, "effort": floor_effort, "skill": "task-analyze-skill"}, {"id": "direct", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "main-result", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "real-verify", "model": floor_model, "effort": floor_effort, "skill": "verify-skill"}, {"id": "records", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}]
    complex_code = [{"id": "task-analyze", "model": frontier_model, "effort": frontier_effort, "skill": "task-analyze-skill"}, {"id": "audit", "model": balanced_model, "effort": balanced_effort, "skill": "workflow-skill"}, {"id": "implement", "model": complex_model, "effort": complex_effort, "skill": "code-skill", "language": "python", "purpose": "implement", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"}, {"id": "main-result", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "real-verify", "model": complex_model, "effort": complex_effort, "skill": "verify-skill"}, {"id": "optimization-verify", "model": complex_model, "effort": complex_effort, "skill": "verify-skill"}, {"id": "records", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}]
    middle_entry = [{"id": "task-analyze", "model": middle_model, "effort": middle_effort, "skill": "task-analyze-skill"}, {"id": "direct", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "main-result", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "ending-dispatch", "model": floor_model, "effort": floor_effort, "skill": "workflow-skill"}, {"id": "real-verify", "model": floor_model, "effort": floor_effort, "skill": "verify-skill"}]
    traces = {"admitted-single-floor-entry": easy, "admitted-complex-frontier-entry": complex_code}
    if middle_model not in {floor_model, frontier_model}:
        traces["admitted-single-middle-entry"] = middle_entry
    return traces


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
    failures.extend(missing_terms("workflow agent", texts["agent"], ["eligible text/code producer", "matching Obsidian context", "saved highest-family quality pair", "One Real PASS keeps it", "two PASS results downgrade one rung", "quality FAIL upgrades one", "zero-result operational failure may use one stronger fallback", "Spark is schedule-only", "Ordinary tasks never refresh the model cache", "explicit user model-update", "local models_cache.json", "never network", "Publish output immediately", "start independent <=60s evidence-only Ending", "producer receipt", "return without waiting", "terminal event records PASS/FAIL learning", "concurrent change records BLOCKED", "Direct task versus Auto task", "Auto task+Ending", "controller is excluded diagnostic", "No hook", "visible machine plan"]))
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
    failures.extend(missing_terms("code-skill agent", texts["code_agent"], ["exact read-only lookup/audit stays skill-free", "Implementation, edit, debug, refactor, or authored tests", "saved contextual quality pair", "One Real PASS retains it", "two PASS results downgrade one rung", "quality FAIL upgrades one", "zero-result operational failure uses one stronger fallback", "Return published code immediately", "producer receipt", "terminal event records PASS/BLOCKED learning", "Local model_experience.json stays legacy read-only", "independent Ending", "no foreground verifier"]))
    failures.extend(missing_terms("verify-skill agent", texts["verify_agent"], ["every user task launches an independent post-result Ending lifecycle", "Never add Mini/Fast Verify before first presentation", "producer shows the completed result", "record lifecycle started", "<=60-second evidence-only audit", "no extra tests/API, user question, wait, or repair", "concurrent state change records terminal BLOCKED and exits", "Ending-only final gate", "never blocks the delivered result", "Ending time is separate"]))
    failures.extend(missing_terms("optimization-skill agent", texts["optimization_agent"], ["do not load from benchmark repetition alone", "user-requested optimization", "explicitly authorized reusable improvement", "positively admitted node", "catalog-generated ladder", "present the optimized result immediately", "no foreground Mini/Fast Verify", "different Real verifier", "Ending time is excluded from first-result time", "never self-certify savings"]))
    failures.extend(missing_terms("management-skill agent", texts["management_agent"], ["do not load for ordinary exact-scoped read-only work or benchmark worker arms", "explicit management request or admitted node", "broad Obsidian Model Switch.md", "local model_experience.json and central TaskModelExperience are legacy read-only", "saved quality pair", "two Real PASS results downgrade one rung", "quality FAIL upgrades one", "Spark is scheduled-source-only", "terminal ledger event records the verdict", "never publish private state"]))
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
    if len(entry_body.encode("utf-8")) > 1152:
        failures.append(f"global entry bootstrap exceeds compact limit: {len(entry_body.encode('utf-8'))} > 1152 bytes")
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
    for name, route in routes.items():
        expected_prefix = EXPECTED_ROUTE_PREFIXES.get(name)
        route_failures = []
        if expected_prefix is None:
            route_failures.append("unexpected scenario without a validator contract")
        elif route[:len(expected_prefix)] != expected_prefix:
            route_failures.append(f"route must begin {expected_prefix}, got {route[:len(expected_prefix)]}")
        if name == "ordinary-code-domain" and "code-skill" not in route:
            route_failures.append("registered code-domain route bypasses code-skill")
        route_results.append({"name": name, "status": "pass" if not route_failures else "fail", "route": route, "failures": route_failures})
        failures.extend([f"route {name}: {failure}" for failure in route_failures])
    for missing_name in sorted(set(EXPECTED_ROUTE_PREFIXES) - set(routes)):
        failures.append(f"matrix missing scenario: {missing_name}")
    gate_results = [{"name": "requested-work-done", "observed": can_show_main_result(True), "expected": True}, {"name": "requested-work-not-done", "observed": can_show_main_result(False), "expected": False}]
    for result in gate_results:
        if result["observed"] != result["expected"]:
            failures.append(f"gate {result['name']} mismatch")
    trace_results = [validate_trace(name, trace, global_root) for name, trace in sample_traces().items()]
    for result in trace_results:
        failures.extend([f"trace {result['name']}: {failure}" for failure in result["failures"]])
    entry_models = {trace[0]["model"] for trace in sample_traces().values()}
    if len(entry_models) < min(3, len(ACTIVE_MODEL_ORDER)):
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

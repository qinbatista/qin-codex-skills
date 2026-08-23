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
    "dynamic-code-graph": ["Task Analyze", "scored dependency-ready nodes"],
    "independent-small-sources": ["entry bootstrap", "one adaptive producer"],
    "independent-large-sources": ["entry bootstrap", "admitted source graph"],
    "dependent-multi-file": ["one adaptive producer or linear scored nodes", "owning skill"],
    "explicit-routing-no-graph": ["Task Analyze", "one contextual producer"],
    "task-analyze-maintenance": ["Task Analyze", "dynamically scored design/code/docs nodes"],
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
    "dynamically scored locked multi-node route",
    "Ineligible ordinary work remains inline",
    "exactly one execution lifecycle",
    "`direct` for eligible ultra-simple score-0-24 single-result work",
    "`planned_single` for every other single result",
    "`planned_graph` for an admitted multi-result dependency graph",
    "execution-lifecycle-notice",
    "A released result uses the independent Ending lifecycle after presentation only when it exposes `real_test`, `information_update`, or `memory_update`",
    "ending_skip_reason=no_real_test_or_information_or_memory_update",
    "Before making a savings claim",
    "reject the savings claim, not a structurally valid task graph",
    "Direct task versus Auto task",
    "Auto task + Ending",
    "excluded routing diagnostic",
    "frozen, receipt-backed, Real-passing, and `trial=false`",
    "single-node production tasks",
    "multi-node request instead materializes one `dynamic_task_graph`",
    "reads the saved shared contract unchanged",
    "Ordinary tasks do not scan or refresh the local model cache",
    "Only an explicit user model-update request",
    "never fetch models over the network",
    "preserve the saved contract when the local cache is unavailable",
    "not controller-only",
    "exact model and effort for each delegated node",
    "matching sanitized receipt",
    "deduplicated local/Obsidian routing history",
    "project/task/module/file/symbol/code",
    "obsidian_adaptive_model_runner.py",
    "at least two model-executed result nodes saves private schema-2 `dynamic_task_graph` JSON",
    "own score, band, selected pair",
    "regardless of parent score",
    "local routing ledger first",
    "projects the same event ID to the matching native Obsidian category page",
    "End-to-end performance admission remains separate",
    "Continue in the same task",
    "no hook is used",
    "complex admitted graph: task-specific Mermaid",
    "Workflow with models",
    "Every active registry-owned code-domain node loads `code-skill`",
    "Do not run broad verification before the user first sees the result",
    "show `CODE READY` or `MAIN RESULT READY` immediately",
    "Ending begins only after the whole producer flow has settled",
    "the final aggregate result has released",
    "A `LOCKED_ROUTE_NODE` never starts or waits for Ending",
    "entry parent binds that receipt",
    "bypasses result-producing performance admission",
    "The End Task starts with `ENDING_TASK_WORKER`",
    "ENDING_CHECK_WORKER",
    "all required checks must PASS",
    "automatically submits the generated repair prompt",
    "next fresh Ending",
    "Real Verify",
    "one persistent global projectless `End Task-{task}`",
    "one Ending primary is fixed `gpt-5.3-codex-spark|xhigh`",
    "registry-floor `gpt-5.6-luna|low` fallback",
    "as its sole lifecycle owner",
    "Runtime Receipt And Learning",
    "Start the local lifecycle with score, plan, and `--producer-receipt` when present",
    "Receipt-backed producer outcomes may move routing",
    "known assignment without a receipt is written as a non-learning observation",
    "suite total never converts a losing class into a pass",
    "Ending Real time is separate",
    "stage=result-ready",
    "model-switch-notice",
    "The notice names the task part, entry pair, selected/attempt pair",
    "code-rule-notice",
    "missing lifecycle disclosure is a routing failure",
    "universal philosophy, one active language profile",
    "Missing Code Gate disclosure or its universal reference is a routing failure",
    "New C# aliases resolve only to the Unity C# common profile",
    "launch the CLI as an ongoing session",
    "The origin returns after creating and linking the one global End Task",
    "when `create_thread` is callable",
    "create-launches",
    "actual pair plus any approved availability reason",
    "end_task_trigger_rate=100%",
    "Model stages (N):",
    "If thread tools are unavailable",
    "outer host creates the End Task",
    "never inspect app-server schemas/commands",
    "emits a BLOCKED handoff for the outer host",
]
REQUIRED_TEMPLATE = ["Admitted Workflow Display Templates", "Eligible ordinary production uses the compact adaptive runner but shows no pre-result route", "Exact one-source, tool-only, and image/mixed work stay inline", "## Admitted Single Node: Text Only", "## Admitted Complex Graph: Mermaid", "current selected model | current selected effort", "Show main result now", "Dispatch Ending Task", "Real Verify", "Independent optimization verification", "Main Result always precedes Ending Task", "Workflow With Models", "submits a bounded repair prompt", "fresh Ending verifier"]
REQUIRED_MATRIX = ["# Adaptive And Admitted Routing Matrix", "Eligible single-node text/code production enters the compact adaptive runner exactly once", "Multi-segment work creates one dynamically scored dependency graph", "dynamic-code-graph", "ordinary-production", "independent-small-sources", "independent-large-sources", "dependent-multi-file", "explicit-routing-no-graph", "explicit-benchmark", "admitted-complex", "One receipt-valid Real PASS retains the selected pair", "two matched PASS outcomes try one lower rung", "quality failure upgrades one rung", "Same-session outcome gate; then a small low-risk edit tries Spark only with no stronger session route", "all checks must PASS", "codex_app__send_message_to_thread", "fresh Spark-first verifier", "Direct uses the exact raw prompt", "public two-world comparison", "fixed Sol-ultra Direct task", "Luna-max-entry Auto task", "Auto excludes only its Luna-max entry controller", "--direct-task", "--bootstrap-task"]
REQUIRED_CODE = ["score role or Obsidian-context quality pair", "bounded native Obsidian route", "project/task/module/file/symbol/code", "One Real PASS retains a quality pair", "two PASS results downgrade one rung", "quality FAIL upgrades one rung", "requested output artifact is producer work", "run exactly one producer-side Quick Check", "Present `CODE READY`", "A successful durable code change normally exposes `real_test`", "ending_skip_reason=no_real_test_or_information_or_memory_update", "ending_verification_plan.py", "exactly one global projectless `End Task-{task}`", "codex_app__list_threads", "projectId=null", "gpt-5.3-codex-spark|xhigh", "registry-floor `gpt-5.6-luna|low`", "ENDING_CHECK_WORKER", "read every listed Skill", "never edit producer files", "All checks must PASS", "immutable origin", "codex_app__send_message_to_thread", "fresh Spark-first Ending", "do not poll"]
REQUIRED_VERIFY = ["Verification has two scopes", "post-result Ending Real Verify when the released result exposes", "persistent global projectless", "ending_verification_plan.py", "final aggregate producer receipt", "child/subprocess receipt never launches it", "compact, one-check actions", "each check keeps its own `0-100` score", "All required checks must PASS", "{\"type\":\"projectless\"", "codex_app__list_threads", "projectId=null", "--thread-scope global --thread-project-id null", "create-launches", "Model stages (N):", "remains visible", "Never call `set_thread_archived`", "origin project binding", "structured `model_assessment`", "learning_eligible=false", "fresh global projectless Ending", "gpt-5.3-codex-spark|xhigh", "gpt-5.6-luna|low", "ENDING_CHECK_WORKER", "delegated_check_worker", "BLOCKED does not count as verified"]
REQUIRED_OPTIMIZATION = ["Do not infer optimization from repeated benchmark arms or exact-scoped read-only work", "Use this skill directly only when the user requests optimization", "catalog-derived adaptive producer", "positively admitted", "code optimization normally exposes `real_test`", "ending_skip_reason=no_real_test_or_information_or_memory_update", "exactly one smallest local Quick Check", "ENDING_CHECK_WORKER", "different verifier", "before/after", "producer receipt", "--direct-task", "--bootstrap-task", "neither arm enters Task Analyze context"]
REQUIRED_MANAGEMENT = ["Do not load this skill for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms", "directly only for an explicit routing-record", "admitted a delegated route", "native Obsidian category page", "Every task stores a `0-100` score", "Eligible small low-risk edits with no stronger same-session outcome route try Spark first", "Spark quality failure suppresses", "two PASS results trial one rung down", "obsidian_model_memory.py", "A released result launches one visible global projectless Ending Task only when", "no-surface result records `intentionally_skipped_simple_task`", "terminal memory/classification/record closeout", "Terra/Sol check workers", "terminal ledger event records an Ending result automatically", "legacy read-only", "Model stages (N):", "end_task_trigger_rate=100%", "Never push/sync/publish unless the user explicitly requested publishing"]
REQUIRED_ENTRY = ["# Task Lifecycle", "Merge this section into `~/.codex/AGENTS.md` and `~/AGENTS.md`", "Score every submission 0-100", "Resolve entry first", "Sol/high may downgrade", "Luna-max/lower may upgrade", "exact step-capability/band history wins", "no match stays <=entry", "reuse lowest-correct", "classify material stages before any producer", "2+ result stages activate one graph", "single-stage only", "each stage records score,band,pair,purpose,deps,stop", "same-session gate→Spark-low if no stronger route", "Execution lifecycle:", "ultra-simple single result=>direct", "other single result=>plan+single execution", "multi-result=>plan+dependency graph", "emit execution-lifecycle-notice", "operational failure is quality-neutral", "new topic resets", "Independent nodes parallel", "shared writes/order/output deps linear", "obsidian_adaptive_model_runner.py", "graph-route-required", "route-required", "no model ran", "full Task Analyze", "no single-producer retry", "LOCKED_ROUTE_NODE emits Code Gate", "universal philosophy+one active language profile+matched categories", "missing Code Gate/reference is routing failure", "C# aliases use only Unity C#", "does code/result+one Quick Check,emits CODE READY,stops", "Parent launches one End only after final aggregate `ending-required` receipt/release", "child/subprocess receipts never launch it", "same End Task continues one bounded action at a time", "ENDING_TASK_WORKER sole lifecycle controller", "ENDING_CHECK_WORKER reads listed Skills", "no nested End/Fix", "dynamic_task_graph", "task_route_dispatcher.py run-plan", "task_complexity_score.py", "no reread/full-read/precheck", "output artifact MUST runner", "2 Real PASS trial down 1 rung", "quality FAIL up 1", "Only the final aggregate `ending-required` or `ending_required=true` receipt after all result nodes settle=>one independent global projectless Ending when real_test/information_update/memory_update exists", "create-launches --producer-receipt(final) --project-id(context-only)", "`intentionally_skipped_simple_task`=>no End Task", "ending_skip_reason=no_real_test_or_information_or_memory_update", "missing acknowledgement=>BLOCKED", "gpt-5.3-codex-spark|xhigh", "score scopes checks only", "Luna-low", "terminal memory/classification/record closeout", "call codex_app__create_thread target", "codex_app__list_threads", "projectId=null/absent", "resolve root with codex_app__list_projects", "ack threadId+hostId+originProjectId+threadProjectId=null+actual pair", "project/current-task/same-task-subtask placement", "audit-launches end_task_trigger_rate=100%", "all checks PASS", "End Task stays globally visible", "never auto-archive/delete", "attempts,first/retry pass", "suitability", "Obsidian link/status", "immutable origin session", "codex_app__send_message_to_thread", "repair_prompt", "fresh global projectless End Task", "--repair-of-lifecycle-id", "up to 3 repairs", "missing source session or failed prompt submission is BLOCKED", "BLOCKED only unavailable/external/limit", "Terminal events write local+same-ID Obsidian records", "only producer receipts move routing", "AUTO_BENCHMARK_ENTRY", "Direct `gpt-5.6-sol|ultra`", "Auto `gpt-5.6-luna|max`", "MUST child/graph then return child JSON", "gate owns separate Ending", "excludes only controller", "compare task vs +Ending", "all exact PASS", "Final Ending PASS/BLOCKED"]
REQUIRED_SELECTION = ["# Catalog-Generated Model Selection", "assets/model-capability-ladder.json", "scripts/model_registry.py", "`~/.codex/models_cache.json`", "bootstrap it once", "Only an explicit user model-update request", "highest numeric GPT family", "Older visible families may remain in the machine cache", "excluded from the saved registry", "bounded native Obsidian route", "merged local history", "terminal Ending event automatically records the matched producer verdict", "optional priority producer", "native project → Model Switch → category → shared-category projection", "Exact read-only", "task_complexity_score.py", "obsidian_adaptive_model_runner.py", "multi-node production task runs one `dynamic_task_graph`", "based on its own score, not the parent task score"]
REQUIRED_ADAPTIVE = ["project/task/module/file/symbol/code context", "assets/model-capability-ladder.json", "last explicitly refreshed local Codex model order", "source digest", "six stable category pages", "receipt-backed local event ledger is the durable fast history", "deduplicate stable event IDs", "deterministic `0-100` score and band", "scoring `0-24` runs the same-session outcome gate before Spark", "zero-result, zero-token Spark operational failure", "atomically bootstrapped from the local cache when missing", "Only an explicit user model-update request", "preserve the last valid registry", "Obsidian evidence and same-name/display-page evidence never cross project keys", "`strategy_performance.py` remains the separate authority", "automatically writes a receipt-backed producer outcome"]
REQUIRED_OBSIDIAN_RUNNER = ["project-memory-skill", "obsidian_model_memory.py", "obsidian_model_memory.recommend_model", "model_execution_receipt.adaptive_producer_authorization", "node_role=\"result-producer\"", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "immediate_operational_fallback", "result_lifecycle_policy", "ending_required", "ending_requirement", "ending_real_status", "intentionally_skipped_simple_task", "missing_expected_code_ending", "missing_expected_non_simple", "producer_check_scope", "one_smallest_local_quick_check", "first_result_release", "immediate_after_quick_check", "deferred_verification_owner", "_emit_ending_required", "ending-required", "create_projectless_end_task", "ack_required", "resolve_fast_path_args", "hashlib.sha256", "explicit_fields", "fast_path", "code_rule_bundle", "code-rule-notice", "execution_lifecycle_contract", "execution-lifecycle-notice", "recommendation = _exact_contract_recommendation(prompt, _recommend(args, prompt))", "adaptive-producer", "workspace-write", "scheduled_source_paths", "schedule_admission", "SINGLE_PRODUCER_SOURCE_BYTE_LIMIT", "single_producer_lower_estimated_logical_tokens", "parallel_independent_sources", "parallel_sources_fused_final", "fuses_owned_source_with_dependencies", "task_route_dispatcher.run_plan", "scheduled_result_node_count", "parallel_branch_count", "_graph_route_required_summary", "graph-route-required", "route-required", "material_result_stages", "graph_required", "multiple_material_result_stages_require_dynamic_task_graph", "build_dynamic_task_graph_and_call_task_route_dispatcher_once"]
REQUIRED_OBSIDIAN_MEMORY = ["DEFAULT_LADDER", "model-capability-ladder.json", "Model Switch.md", "task_type", "module", "file", "symbol", "code_kind", "modality", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "recommend_model", "record_model_result", "record_model_observation", "learning_eligible", "observation_id", "receipt_status", "turn_completed", "model_match", "effort_match"]
REQUIRED_STRATEGY_PERFORMANCE = ["DEFAULT_MINIMUM_PAIRED_SAMPLES = 6", "DEFAULT_MINIMUM_SAVINGS_PERCENT = 0.0", "DEFAULT_MAXIMUM_PAIR_REGRESSION_PERCENT = 5.0", "MAXIMUM_PAIRED_TIME_REGRESSION_MS", "evaluate_paired_metric", "aggregate_totals_pass", "regression_bounds_pass", "strict_pareto_win", "delegated_adaptive", "inline_entry", "workload_prompt_sha256", "entry_pair", "config_cohort"]
FORBIDDEN = ["observable entry model and effort belong only to Task Analyze and route coordination", "selected entry model and effort run Task Analyze and route coordination only", "Every route begins with independent `task-analyze-skill`", "Registry-owned code-domain executor selected in the locked task-analyze-skill plan", "Use this as the verification executor named by the locked `task-analyze-skill` plan", "Use this skill only when the locked `task-analyze-skill` plan", "internal Task Analyze", "not a sixth top-level skill", "Task Analyze itself uses `GPT-5.6-Sol`", "Task Analyze still runs on Sol", "correctness-affecting Real Verify stays before", "Real Verify always stays before Main Goal Done", "approved five", "five-folder boundary", "private ledger remains authoritative", "Learning is shared across projects", "generalized task-type conditions", "only ordered Luna, Terra, and Sol", "current 5.6 pair", "new 5.6 repair lifecycle", "auto-refreshed shared contract", "automatically refreshed shared contract", "passively refreshed shared contract", "priority-first producer", "try the optional priority producer first", "complete Global foreground path includes entry/controller plus child costs", "first_attempt_text_code_producer", "every visible, routable Codex model except the optional priority producer", "Obsidian selects from every current visible catalog model", "every visible supported non-priority catalog model from weakest to strongest"]
REQUIRED_WORKFLOW += [
    "[Task Resource Lifecycle](references/task-resource-lifecycle.md)",
    "durable-result, last-consumer, handoff, reverse-order release",
    "after the result is durably readable and presented",
    "Ending writes check evidence and its terminal record before release",
    "Resource cleanup never controls another Codex task, thread, session, or Ending",
]
REQUIRED_VERIFY += [
    "[Task Resource Lifecycle](../workflow-skill/references/task-resource-lifecycle.md)",
    "writes evidence and its terminal record first",
    "exact Ending-owned or explicitly handed-off disposable resources",
    "Resource cleanup never controls another Codex task, thread, session, or Ending",
]
REQUIRED_ENTRY += [
    "Resources:load `workflow-skill/references/task-resource-lifecycle.md`",
    "exact task-owned path/runtime/UI",
    "durable+last-consumer readback=>LIFO release",
    "delete `Cache/tmp-*` only",
    "retain/defer preexisting/shared/conflicted/Unity/date/remote",
    "cleanup never controls Codex tasks/threads/sessions/Endings",
    "short reuse=>`<YYYYMMDD>`+reason/review",
    "`remote-*`/`remote-test/`=>explicit retain only",
    "formal reusable tests stay source",
]
REQUIRED_RESOURCE_LIFECYCLE = [
    "Task Resource Lifecycle (内存优化)",
    "exclusive `Cache/tmp-<task>` root",
    "retention reason plus a next review point",
    "explicit consumer map",
    "reverse acquisition order",
    "Ending releases only exact resources it created or received by explicit handoff",
    "`deferred_conflict` is revalidatable",
    "same owner tool or typed adapter",
    "No resource cleanup or reclamation operation may message",
    "never a background janitor",
]
REQUIRED_RESOURCE_LEDGER = [
    "SCHEMA_VERSION = 2",
    "def new_ledger(",
    "def acquire_path(",
    "def seal_path(",
    "def cleanup_path(",
    "def acquire_runtime(",
    "def confirm_runtime_release(",
    "def record_evidence_persisted(",
    "def handoff(",
    "def defer_conflict(",
    "def resolve_conflict(",
    "owner_tool_graceful",
    "os.O_CREAT | os.O_EXCL",
    "os.replace",
    "os.rename",
    "FORBIDDEN_RUNTIME_KINDS",
]
FORBIDDEN += ["No lifecycle operation may message, interrupt"]
NEGATIVE_DESCRIPTION_PREFIXES = {"code": "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction", "verify": "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify", "optimization": "Do not infer optimization from repeated benchmark arms or exact-scoped read-only work", "management": "Do not use for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms"}
NEGATIVE_AGENT_PREFIXES = {"code_agent": "$code-skill: exact artifact-free read-only work stays outside", "verify_agent": "$verify-skill: Ending only when released result has real_test, information_update, or memory_update", "optimization_agent": "$optimization-skill: do not load from benchmark repetition alone or exact-scoped read-only work", "management_agent": "$management-skill: do not load for ordinary exact-scoped read-only work or benchmark workers"}


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
        "resource_lifecycle": skill_dir / "references" / "task-resource-lifecycle.md",
        "resource_ledger": skill_dir / "scripts" / "task_resource_ledger.py",
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
    failures.extend(missing_terms("workflow agent", texts["agent"], ["matching Obsidian context", "lowest-correct pair", "LOCKED_ROUTE_NODE loads required Skills+task-resource-lifecycle", "Quick Check→CODE READY", "broad tests/builds/UI/full lint/log cleanup/repeated review move to Ending", "Ending only when result has real_test, information_update, or memory_update", "intentionally_skipped_simple_task", "immutable origin", "project only as execution context", "one global-only projectless End", "codex_app__list_threads", "projectId=null/absent", "returns without polling", "gpt-5.3-codex-spark|xhigh", "gpt-5.6-luna|low", "ENDING_CHECK_WORKER", "read listed Skills", "without edits/repair/lifecycle", "All PASS", "codex_app__send_message_to_thread", "origin repairs", "fresh Spark-first verification", "max 3"]))
    failures.extend(missing_terms("workflow", texts["workflow"], REQUIRED_WORKFLOW))
    failures.extend(missing_terms("task resource lifecycle", texts["resource_lifecycle"], REQUIRED_RESOURCE_LIFECYCLE))
    failures.extend(missing_terms("task resource ledger", texts["resource_ledger"], REQUIRED_RESOURCE_LEDGER))
    for forbidden in ("subprocess", "os.kill(", "send_message_to_thread", "interrupt_agent", "set_thread_archived", "terminate_task"):
        if forbidden in texts["resource_ledger"]:
            failures.append(f"task resource ledger contains forbidden cleanup control primitive: {forbidden}")
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
    failures.extend(missing_terms("code-skill agent", texts["code_agent"], ["exact artifact-free read-only work stays outside", "references/code-writing-philosophy.md", "relevant language/platform/domain Skills", "Unity game C#", "Controller/Manager/ScriptableObject core", "exactly one smallest local Quick Check", "publish CODE READY", "broad tests/builds/UI/full lint/log cleanup/repeated review move to Ending", "Code normally exposes real_test through Quick Check and emits ending-required", "ending_verification_plan.py", "one visible global-only projectless End Task", "list_threads", "projectId=null/absent", "gpt-5.3-codex-spark|xhigh", "gpt-5.6-luna|low", "ENDING_CHECK_WORKER", "read listed Skills", "never edit/repair/route/lifecycle", "All checks PASS", "codex_app__send_message_to_thread", "immutable origin", "fresh Spark-first Ending", "Never self-verify"]));
    failures.extend(missing_terms("verify-skill agent", texts["verify_agent"], ["Ending only when released result has real_test, information_update, or memory_update", "ending_skip_reason=no_real_test_or_information_or_memory_update", "CODE READY", "one global-only projectless Ending", "ending_verification_plan.py", "codex_app__list_threads", "projectId=null/absent", "without polling", "gpt-5.3-codex-spark|xhigh", "gpt-5.6-luna|low", "ENDING_CHECK_WORKER", "read listed Skills", "never edit/repair/route/lifecycle", "Capture immutable origin", "all checks PASS", "codex_app__send_message_to_thread", "origin repairs", "fresh Spark-first Ending", "up to three", "Never self-repair", "Load task-resource-lifecycle", "evidence first", "LIFO-release exact owned/handoff resources", "cleanup never controls Codex tasks/threads/sessions/Endings"]));
    failures.extend(missing_terms("optimization-skill agent", texts["optimization_agent"], ["do not load from benchmark repetition alone", "requested optimization", "authorized reusable improvement", "admitted node", "Preserve behavior", "one smallest Quick Check", "present CODE READY", "Code optimization normally exposes real_test through Quick Check", "ending_skip_reason=no_real_test_or_information_or_memory_update", "one visible global-only projectless Ending", "list_threads", "projectId=null/absent", "gpt-5.3-codex-spark|xhigh", "Luna-low", "ENDING_CHECK_WORKER", "never edit or own lifecycle", "A different worker verifies", "Ending time stays separate", "Never self-certify savings"]));
    failures.extend(missing_terms("management-skill agent", texts["management_agent"], ["do not load for ordinary exact-scoped read-only work or benchmark workers", "explicit request/admitted node", "Native Obsidian links plus local receipts", "Producers score 0-100", "small edits pass session gate before Spark", "quality evidence moves producer routes", "Management Ending requires real_test, information_update, or memory_update", "no-surface result records intentionally_skipped_simple_task", "global-only projectless Ending", "list_threads", "projectId=null/absent", "gpt-5.3-codex-spark|xhigh", "Luna-low", "ENDING_CHECK_WORKER", "terminal memory/classification/record closeout", "Retained capabilities remain mandatory", "Local install/update writes a recoverable provisional copy first", "Codex runs installed/source/platform checks,repairs and reinstalls without user gate work", "PASS alone completes", "GitHub push requires pre-mutation PASS", "source/deployed/remote separate", "never publish private state"]));
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
    entry_body = texts["task_analyze_entry_rule"].replace("Merge this section into `~/.codex/AGENTS.md` and `~/AGENTS.md`.\n\n", "", 1)
    if len(entry_body.encode("utf-8")) > 7000:
        failures.append(f"global entry bootstrap exceeds compact limit: {len(entry_body.encode('utf-8'))} > 7000 bytes")
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

#!/usr/bin/env python3
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

try:
    from skill_resolver import resolve_skill_path
    from validate_graduated_routes import validate_fixture
except ModuleNotFoundError:
    _scripts_root = Path(__file__).resolve().parent
    _skill_resolver_spec = importlib.util.spec_from_file_location("task_analyze_skill_resolver", _scripts_root / "skill_resolver.py")
    _skill_resolver = importlib.util.module_from_spec(_skill_resolver_spec)
    _skill_resolver_spec.loader.exec_module(_skill_resolver)
    resolve_skill_path = _skill_resolver.resolve_skill_path
    _graduated_spec = importlib.util.spec_from_file_location("task_analyze_graduated_routes", _scripts_root / "validate_graduated_routes.py")
    _graduated = importlib.util.module_from_spec(_graduated_spec)
    _graduated_spec.loader.exec_module(_graduated)
    validate_fixture = _graduated.validate_fixture


try:
    from routing_policy import (
        EXECUTION_DOMAINS,
        PROFILE_PRESETS,
        MODEL_EFFORTS,
        expected_owner_skill,
        execution_domain_is_active,
        is_code_execution_domain,
        resolve_execution_domain,
        validate_profile_preset_registry,
        validate_execution_domain_registry,
    )
except ModuleNotFoundError:
    import importlib.util as _importlib_util

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = _importlib_util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = _importlib_util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    PROFILE_PRESETS = _routing_policy.PROFILE_PRESETS
    MODEL_EFFORTS = _routing_policy.MODEL_EFFORTS
    expected_owner_skill = _routing_policy.expected_owner_skill
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    validate_profile_preset_registry = _routing_policy.validate_profile_preset_registry
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry

try:
    from model_registry import build_registry, load_catalog, load_registry, registry_matches_catalog, validate_registry
except ModuleNotFoundError:
    _model_registry_path = Path(__file__).with_name("model_registry.py")
    _model_registry_spec = importlib.util.spec_from_file_location("task_analyze_model_registry", _model_registry_path)
    _model_registry = importlib.util.module_from_spec(_model_registry_spec)
    _model_registry_spec.loader.exec_module(_model_registry)
    build_registry = _model_registry.build_registry
    load_catalog = _model_registry.load_catalog
    load_registry = _model_registry.load_registry
    registry_matches_catalog = _model_registry.registry_matches_catalog
    validate_registry = _model_registry.validate_registry

MODEL_REGISTRY = load_registry()
ACTIVE_MODEL_ORDER = tuple(model["id"] for model in MODEL_REGISTRY["models"])
ACTIVE_MODEL_EFFORTS = {model["id"]: tuple(model["codex_efforts"]) for model in MODEL_REGISTRY["models"]}
PRIORITY_PRODUCER = MODEL_REGISTRY.get("priority_producer")
PRIORITY_PRODUCER_MODEL = PRIORITY_PRODUCER.get("id") if isinstance(PRIORITY_PRODUCER, dict) else None
REQUIRED_FILES = [
    ".gitignore",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/global-agents-entry-rule.md",
    "assets/model-capability-ladder.json",
    "references/route-contract.md",
    "references/model-selection.md",
    "references/runtime-receipts.md",
    "references/adaptive-routing.md",
    "references/model-capabilities.md",
    "references/related-memory.md",
    "scripts/resolve_entry_model.py",
    "scripts/model_execution_receipt.py",
    "scripts/obsidian_adaptive_model_runner.py",
    "scripts/model_registry.py",
    "scripts/sync_model_capabilities.py",
    "scripts/strategy_performance.py",
    "scripts/benchmark_suite_gate.py",
    "scripts/benchmark_suite_runner.py",
    "scripts/grounded_result_gate.py",
    "scripts/model_routing_history.py",
    "scripts/task_route_dispatcher.py",
    "scripts/skill_resolver.py",
    "scripts/validate_graduated_routes.py",
    "assets/graduated-route-fixtures.json",
    "assets/model-routing-benchmark-example.json",
    "scripts/validate_task_analyze_skill.py",
]
REQUIRED_SKILL_TEXT = [
    "full routing and model-strategy skill",
    "hookless bootstrap",
    "matching project-scoped broad Obsidian `Model Switch.md`",
    "mandatory post-result Ending lifecycle",
    "nested cache/fixture `SKILL.md`",
    "Activation Boundary",
    "Ordinary Inline Bootstrap",
    "must not read this full `SKILL.md`",
    "one direct task action",
    "Every eligible text/code production task must run `scripts/obsidian_adaptive_model_runner.py`",
    "one bounded `rg` per authoritative file",
    "every exact user-named target and direct definition",
    "Anchor named members directly",
    "never add enclosing-class or call-site anchors",
    "guess identifier prefixes or families",
    "then answer once",
    "exact allowlist",
    "current model",
    "regardless of apparent complexity",
    "no separate foreground self-review, Mini, or verification pass",
    "Present the completed result immediately",
    "Do not run Mini/Fast Verify before first presentation",
    "launch an independent Ending subagent for every task level",
    "Final requires lifecycle `PASS` or explicit `BLOCKED`",
    "End-to-End Performance Admission",
    "complete foreground path",
    "frozen model-visible catalogs and memory snapshot",
    "lower cohort total and raw median",
    "individual regressions remain visible diagnostics",
    "median-absolute-deviation noise envelope",
    "no correctness-preserving change remains",
    "frozen, receipt-backed, Real-passing, and `trial=false`",
    "resolve_entry_model.py",
    "quick bounded related-memory lookup",
    "There is no controller-only entry invariant",
    "Mermaid",
    "assets/model-capability-ladder.json",
    "Obsidian Adaptive Routing",
    "exact project/task/module/file/symbol/code context",
    "Ordinary work reads the saved ladder unchanged",
    "only an explicit user model-update request",
    "highest-version quality family",
    "Eligible text/code result producers try the optional priority producer first",
    "new quality-pair repair lifecycle",
    "Ending Real alone records receipt-backed producer pass/fail evidence",
    "ledger performs that write automatically",
    "producers and ordinary runners never write learning",
    "There is no Mini/Fast Verify gate before first presentation",
    "show it immediately",
    "Ending Task",
    "scripts/model_execution_receipt.py",
    "scripts/obsidian_adaptive_model_runner.py",
    "grounded_result_gate.py",
    "task_route_dispatcher.py run-plan",
    "Missing memory providers are a successful no-op",
    "receipt finalization, telemetry, and post-result Ending Real are excluded",
    "controller-stamped sanitized `result-ready` event",
    "runner-owned receipt and evidence timestamps to match exactly",
    "schema-version-2 JSON with only `result` and `ending` phases",
    "scripts/strategy_performance.py",
    "scripts/benchmark_suite_gate.py",
]
REQUIRED_ROUTE_TEXT = [
    "## First Result Principle",
    "show the completed result immediately",
    "Do not run Mini/Fast Verify before first presentation",
    "## Ordinary Entry Contract",
    "Eligible text/code production uses exactly one `obsidian_adaptive_model_runner.py` producer even on cold start",
    "exact read-only work stays on the current model inline",
    "Design a website like YouTube",
    "Apparent complexity alone does not create a dispatcher",
    "## Explicit Or Admitted Foreground Budget",
    "A multi-node foreground exists only after comparable end-to-end evidence positively admits it",
    "## Admitted Single Node: Text Route",
    "Do not draw Mermaid for one admitted node",
    "## Admitted Complex Graph: Mermaid Route",
    "```mermaid",
    "Workflow with models",
    "Main Goal Done Gate",
    "Show main result now",
    "Dispatch background Ending Task",
    "Real Verify",
    "Independent optimization verification",
    "## Internal Plan",
    "schema version 2 JSON",
    "bounded result and Ending nodes",
    "executes only result nodes before release",
    "After the main result is shown",
    "never conversation output",
    "Optional related-memory preflight",
    "terminal verdict is recorded automatically",
]
REQUIRED_SELECTION_TEXT = [
    "# Catalog-Generated Model Selection",
    "assets/model-capability-ladder.json",
    "scripts/model_registry.py",
    "`~/.codex/models_cache.json`",
    "bootstrap it once",
    "Only an explicit user model-update request",
    "highest numeric GPT family",
    "Older numeric families remain catalog-only",
    "## Quality Order",
    "## Cold Start And Priority Producer",
    "## Learning Boundary",
    "Obsidian broad `Model Switch.md`",
    "matching Obsidian broad `Model Switch.md` context",
    "terminal Ending event automatically records the matched producer verdict",
    "optional specialized priority text/code producer",
    "sole current contextual evidence authority",
    "Exact read-only",
    "obsidian_adaptive_model_runner.py",
    "Multi-node strategy and savings claims remain separately performance-admitted",
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
    "entry-context marker",
    "in-process authorization",
    "--direct-task --benchmark-run-id",
    "intentionally add no `LOCKED_ROUTE_NODE`",
    "--entry-task",
    "--bootstrap-task --benchmark-run-id",
    "run outside Task Analyze entry context",
    "wrong node type",
    "same raw prompt",
    "real suite-local `skills/` and `plugins/` directories",
    "copied model/memory snapshots",
    "Never symlink a benchmark catalog to live `~/.codex`",
    "validate the environment immediately before every arm",
    "config/memory drift invalidates the cohort",
    "cannot be resumed or learned as model quality",
    "flushes one sanitized `result-ready` event",
    "runner-owned timestamp exactly across evidence and receipt",
    "model_learning_context",
    "ending_task_ledger.py start --producer-receipt",
    "producer-bound `event pass` writes the matched Obsidian Model Switch record",
]
REQUIRED_ADAPTIVE_TEXT = [
    "project/task/module/file/symbol/code context",
    "## Two Routing Authorities",
    "assets/model-capability-ladder.json",
    "Obsidian broad `Model Switch.md`",
    "last explicitly refreshed local Codex model order",
    "source digest",
    "atomically bootstrapped from the local cache when missing",
    "Only an explicit user model-update request",
    "preserve the last valid registry",
    "sole active private authority",
    "optional priority producer runs first",
    "contextual quality pair",
    "zero-result, zero-token priority-producer operational failure",
    "Evidence never crosses project keys",
    "`strategy_performance.py` remains the separate authority",
    "Ending PASS/FAIL event automatically writes the producer outcome to Obsidian",
]
REQUIRED_OBSIDIAN_RUNNER_IMPLEMENTATION = ["project-memory-skill", "obsidian_model_memory.py", "obsidian_model_memory.recommend_model", "model_execution_receipt.adaptive_producer_authorization", "node_role=\"result-producer\"", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "immediate_operational_fallback", "ending_real_status", "pending"]
REQUIRED_MODEL_SWITCH_CATEGORIES = ["normal-script-update", "code-design", "finding-bugs", "tests-verification", "documentation-instructions", "general-work"]
REQUIRED_MODEL_SWITCH_DIRECTIONS = ["initial", "upgrade", "downgrade", "freeze", "no_switch", "operational_fallback"]
REQUIRED_OBSIDIAN_MEMORY_IMPLEMENTATION = ["DEFAULT_LADDER", "model-capability-ladder.json", "Model Switch.md", "_task_category", "_switch_details", "switch_direction", "rebuild_model_switches", "task_type", "module", "file", "symbol", "code_kind", "modality", "attempt_pair", "active_fallback_pair", "operational_failure_pairs", "recommend_model", "record_model_result", "receipt_status", "turn_completed", "model_match", "effort_match"] + REQUIRED_MODEL_SWITCH_CATEGORIES + REQUIRED_MODEL_SWITCH_DIRECTIONS
REQUIRED_MODEL_REGISTRY_IMPLEMENTATION = ["REGISTRY_SCHEMA_VERSION = 2", "models_cache.json", "catalog_sha256", "visibility", "parse_numeric_gpt_family", "active_family", "highest_numeric_gpt_family", "catalog_models", "catalog_role", "active_quality", "catalog_only", "provider_priority", "priority_producer", "atomic_write_registry", "ensure_registry", "refresh_registry", "registry_matches_catalog", "validate_registry"]
REQUIRED_STRATEGY_PERFORMANCE = ["DEFAULT_MINIMUM_PAIRED_SAMPLES = 6", "DEFAULT_MINIMUM_SAVINGS_PERCENT = 0.0", "DEFAULT_MAXIMUM_PAIR_REGRESSION_PERCENT = 5.0", "MAXIMUM_PAIRED_TIME_REGRESSION_MS", "evaluate_paired_metric", "aggregate_totals_pass", "regression_bounds_pass", "strict_pareto_win", "delegated_adaptive", "inline_entry", "workload_prompt_sha256", "entry_pair", "config_cohort"]
REQUIRED_RECEIPT_GUARD_IMPLEMENTATION = [
    "ENTRY_CONTEXT_ENV",
    "bootstrap-task",
    "benchmark-global-inline",
    "bootstrap_task_entry_context_forbidden",
    "benchmark_run_id_workload_mismatch",
    "adaptive_producer_authorization",
    "dispatcher_node_authorization",
    "dispatcher_adaptive_result_authorization",
    "recursive_entry_task_forbidden",
    "entry_context_adaptive_runner_required",
]
REQUIRED_GLOBAL_BOOTSTRAP_TEXT = ["# Task Lifecycle", "Eligible text/code MUST run adaptive producer", "Saved highest-family ladder", "only explicit user model-update", "local `models_cache.json`", "never fetch", "absent cache keeps it", "Obsidian broad `Model Switch.md`", "project/task/module/file/symbol as fields only", "no hierarchy notes", "local JSON authority", "Priority: easy=low, complex=high", "zero-result uses contextual quality pair", "publish then return", "Prompt/AI-instruction work loads `prompt-skill`", "Durable edits: `project-memory-skill`", "recall", "record reason/result/verification/files after Ending", "Every non-ENDING_TASK_WORKER task", "independent Ending", "routed Ending uses `--producer-receipt`", "writes PASS/FAIL to a broad page", "Parallel docs/logs", "Final requires PASS or BLOCKED", "Failure logs fields before repair", "re-present", "another verifier", "No hook", "Exact read-only: one bounded rg/file at exact members/aliases", "no subagent/route/plan, guesses, broad/reread/full read/pre-result check"]
REQUIRED_GLOBAL_ENTRY_ASSET_TEXT = ["Merge this section into `~/.codex/AGENTS.md`"] + REQUIRED_GLOBAL_BOOTSTRAP_TEXT
REQUIRED_PYTHON_REFERENCE_TEXT = ["## Post-Result Ending Simplicity Review", "Present the completed Python edit immediately", "After that first presentation, Ending Task", "correctness failure"]
REQUIRED_CSHARP_REFERENCE_TEXT = ["present the completed edit immediately", "afterward in Ending Task Real Verify", "do not gate the first presentation"]
REQUIRED_UNITY_REFERENCE_TEXT = ["uses this file plus", "Return the final updated C# code first"]
REQUIRED_PROMPT_SKILL_TEXT = ["Always use for every task", "100% global prompt-task gate across projects", "Ordinary prose does not trigger it", "Prompt-in-code also loads its owning code executor", "Present the completed prompt or instruction artifact immediately", "In Ending Real, test with representative cases"]
REQUIRED_PROMPT_AGENT_TEXT = ["Always use $prompt-skill", "100% global prompt-task gate across projects", "Ordinary prose does not trigger it", "present the completed prompt first"]
FORBIDDEN_GLOBAL_BOOTSTRAP_TEXT = ["TASK_ANALYZE_PLAN_JSON", "TASK_ANALYZE_PLAN_JSON_BEGIN", "LOCKED_ROUTE_NODE", "task_entry_hook.py", "trusted `Stop` hook", "user-level Codex hook", "local/adaptive-routing/model_experience.json"]
GLOBAL_ENTRY_ASSET_DIRECTIVE = "Merge this section into `~/.codex/AGENTS.md`.\n\n"
MAX_GLOBAL_BOOTSTRAP_BYTES = 1024
FORBIDDEN_TEXT = [
    "Use this skill first for every user task",
    "The entry is a bounded controller",
    "Easy adaptive model fast path is one blocking",
    "Easy tasks must use this exact visible shape before the answer",
    "Task Analyze always runs",
    "Task Analyze remains the 100 percent entry skill",
    "Show this compact route before execution",
    "mandatory internal phase of `workflow-skill`",
    "not a sixth top-level skill",
    "Run Task Analyze with `GPT-5.6-Sol`",
    "Task Analyze still runs on Sol",
    "entry model always Sol",
    "only ordered Luna, Terra, and Sol",
    "current 5.6 pair",
    "new 5.6 repair lifecycle",
    "auto-refreshed shared contract",
    "automatically refreshed shared contract",
    "passively refreshed shared contract",
    "Spark is a priority attempt, not a rung in the 5.6 quality ladder",
    "every visible, routable Codex model except the optional priority producer",
    "Obsidian selects from every current visible catalog model",
    "every visible supported non-priority catalog model from weakest to strongest",
    "correctness-affecting Real Verify stays before",
    "approved five",
    "user-level Codex hook",
    "trusted `Stop` hook",
    "TASK_ANALYZE_PLAN_JSON",
    "ends Task Analyze with the visible route and JSON handoff",
    "private schema-1 JSON",
    "applies a proportional local gate",
    "Private Adaptive Routing",
    "private ledger remains model-quality authority",
    "Learning is shared across projects",
    "generalized task-type conditions",
    "broad task-type profile reuses",
    "Keep adaptive history under `local/`",
    "scripts/adaptive_model_runner.py",
    "TaskModelExperience/",
    "local/adaptive-routing/model_experience.json",
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
    private_contract = payload.get("private_learning_contract")
    if not isinstance(private_contract, dict) or private_contract.get("authority") != "obsidian_broad_model_switch" or private_contract.get("path_template") != "Model Switch.md" or private_contract.get("specificity_order") != ["project_task", "module", "file", "symbol"] or private_contract.get("fields_only") is not True or private_contract.get("hierarchy_notes") is not False or private_contract.get("legacy_local_json") != "read_only_inactive":
        failures.append("shared model-capability ladder private learning contract is invalid")
    return failures


def check_model_cache_ladder(models_cache_path, ladder_text):
    try:
        _catalog, catalog_sha256 = load_catalog(models_cache_path)
        observed = json.loads(ladder_text)
        validate_registry(observed)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return {"valid": False, "status": "unreadable", "error": str(error), "expected_catalog_sha256": None, "observed_catalog_sha256": None}
    expected_digest = catalog_sha256
    observed_digest = observed["source"]["catalog_sha256"]
    valid = registry_matches_catalog(observed, catalog_sha256)
    return {"valid": valid, "status": "pass" if valid else "stale", "error": None, "expected_catalog_sha256": expected_digest, "observed_catalog_sha256": observed_digest}


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


def installed_skills(skills_root):
    return {path.name for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").exists()}




def _is_code_implementation(node):
    explicit_domain = node.get("execution_domain")
    language = node.get("language")
    try:
        execution_domain = resolve_execution_domain(
            owning_skill=node.get("skill"),
            purpose=node.get("purpose"),
            language=language,
            explicit_domain=explicit_domain,
        )
    except ValueError:
        execution_domain = "general"
    return is_code_execution_domain(execution_domain)


def _dependency_closure(node_id, node_by_id):
    closure = set()
    pending = list(node_by_id.get(node_id, {}).get("dependencies", []))
    while pending:
        dependency = pending.pop()
        if dependency in closure:
            continue
        closure.add(dependency)
        pending.extend(node_by_id.get(dependency, {}).get("dependencies", []))
    return closure


def validate_plan(plan, installed, skills_root=Path(__file__).resolve().parents[2]):
    failures = []
    try:
        validate_execution_domain_registry(skills_root)
    except ValueError as error:
        failures.append(f"execution-domain registry is invalid: {error}")
    if plan.get("schema_version") != 2:
        failures.append("schema_version must be 2")
    nodes = plan.get("nodes", [])
    entry = plan.get("entry") if isinstance(plan.get("entry"), dict) else {}
    entry_model = entry.get("model")
    entry_effort = entry.get("effort")
    node_by_id = {node.get("id"): node for node in nodes}
    if PRIORITY_PRODUCER_MODEL is not None and entry_model == PRIORITY_PRODUCER_MODEL:
        failures.append("entry priority producer is a result-producer first attempt only and cannot enter a schema-2 plan")
    elif entry_model not in ACTIVE_MODEL_EFFORTS or entry_effort not in ACTIVE_MODEL_EFFORTS.get(entry_model, set()):
        failures.append("entry has unsupported model/effort")
    if any(node.get("skill") == "task-analyze-skill" for node in nodes):
        failures.append("schema 2 dispatcher nodes must not contain Task Analyze")
    if plan.get("route_scope") != "admitted":
        failures.append("full route plans must be explicitly admitted")
    if plan.get("complexity") == "easy" and plan.get("display") != "text":
        failures.append("easy plans must use text display")
    if plan.get("complexity") == "complex" and plan.get("display") != "mermaid":
        failures.append("complex plans must use Mermaid display")
    for index, node in enumerate(nodes):
        node_id = node.get("id", "<missing>")
        model = node.get("model")
        effort = node.get("effort")
        skill = node.get("skill")
        if node.get("phase") not in {"result", "ending"}:
            failures.append(f"{node_id} phase must be result or ending")
        if PRIORITY_PRODUCER_MODEL is not None and model == PRIORITY_PRODUCER_MODEL:
            failures.append(f"{node_id} priority producer is injected only as a result-producer attempt and cannot be a schema-2 node")
        elif model not in ACTIVE_MODEL_EFFORTS or effort not in ACTIVE_MODEL_EFFORTS.get(model, set()):
            failures.append(f"{node_id} has unsupported model/effort")
        if skill not in installed and resolve_skill_path(skill, skills_root) is None:
            failures.append(f"{node_id} names unavailable skill {skill}")
        requested_verification_result = node.get("user_requested_verification_result")
        if node.get("phase") == "result" and skill == "verify-skill":
            if requested_verification_result is not True:
                failures.append(f"{node_id} verify-skill result nodes require user_requested_verification_result=true")
        elif "user_requested_verification_result" in node:
            failures.append(f"{node_id} user_requested_verification_result is valid only on a result-phase verify-skill node")
        for dependency in node.get("dependencies", []):
            if dependency not in node_by_id:
                failures.append(f"{node_id} has missing dependency {dependency}")
        explicit_domain = node.get("execution_domain")
        if isinstance(explicit_domain, str):
            explicit_domain = explicit_domain.strip() or None
        try:
            resolved_domain = resolve_execution_domain(
                owning_skill=skill,
                task_family=node.get("task_family"),
                explicit_domain=explicit_domain,
                language=node.get("language"),
                purpose=node.get("purpose"),
            )
        except ValueError:
            resolved_domain = str(explicit_domain or "")
            failures.append(f"{node_id} execution_domain is unknown")
        else:
            if not execution_domain_is_active(resolved_domain):
                failures.append(f"{node_id} execution_domain is non-active: {resolved_domain}")
            node["execution_domain"] = resolved_domain

        if node.get("execution_domain") is None:
            execution_domain = resolved_domain
        else:
            execution_domain = node.get("execution_domain")
        is_code_node = False if execution_domain not in EXECUTION_DOMAINS else is_code_execution_domain(execution_domain)
        if is_code_node and skill != "code-skill" and expected_owner_skill(execution_domain) is not None:
            failures.append(f"{node_id} bypasses code-skill")
    if "mini_verify_node" in plan:
        failures.append("mini_verify_node is not valid in schema 2")
    result_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "result"}
    ending_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "ending"}
    main_result_node = plan.get("main_result_node")
    main = node_by_id.get(main_result_node)
    if not result_ids:
        failures.append("plan must contain at least one result node")
    if not ending_ids:
        failures.append("plan must contain post-result Ending work")
    if not main or main.get("phase") != "result":
        failures.append("main_result_node must name a result node")
    else:
        missing_result_dependencies = result_ids - _dependency_closure(main_result_node, node_by_id) - {main_result_node}
        if missing_result_dependencies:
            failures.append("main_result_node must depend on every other result node")
    for result_id in sorted(result_ids):
        if any(dependency in ending_ids for dependency in node_by_id[result_id].get("dependencies", [])):
            failures.append(f"{result_id} must not depend on Ending work")
    for ending_id in sorted(ending_ids):
        if main_result_node not in node_by_id[ending_id].get("dependencies", []):
            failures.append(f"{ending_id} must depend directly on main_result_node")
    producer_real_verifiers = [
        node_id
        for node_id in ending_ids
        if node_by_id[node_id].get("skill") == "verify-skill" and not node_by_id[node_id].get("verifies_node")
    ]
    if len(producer_real_verifiers) != 1:
        failures.append("plan must contain exactly one post-result Real verifier for the main result")
    return failures
def _easy_followup_node_pair():
    return tuple(MODEL_REGISTRY["role_pairs"]["floor"].split("|", 1))


def _complex_followup_node_pair():
    return tuple(MODEL_REGISTRY["role_pairs"]["balanced_default"].split("|", 1))


def _complex_followup_implementation_pair():
    return tuple(MODEL_REGISTRY["role_pairs"]["balanced_complex"].split("|", 1))


def sample_plans():
    ordered_models = list(ACTIVE_MODEL_ORDER)
    easy_followup_model, easy_followup_effort = _easy_followup_node_pair()
    complex_followup_model, complex_followup_effort = _complex_followup_node_pair()
    implementation_model, implementation_effort = _complex_followup_implementation_pair()
    plans = {}
    for model in ordered_models:
        for effort in ACTIVE_MODEL_EFFORTS[model]:
            plans[f"admitted-single-{model}-{effort}"] = {
                "schema_version": 2,
                "route_scope": "admitted",
                "complexity": "easy",
                "display": "text",
                "entry": {"model": model, "effort": effort},
                "nodes": [
                    {
                        "id": "direct",
                        "phase": "result",
                        "skill": "workflow-skill",
                        "model": easy_followup_model,
                        "effort": easy_followup_effort,
                        "dependencies": [],
                        "execution_domain": "general",
                    },
                    {"id": "ending-real", "phase": "ending", "skill": "verify-skill", "model": easy_followup_model, "effort": easy_followup_effort, "dependencies": ["direct"], "execution_domain": "general"},
                    {"id": "records", "phase": "ending", "skill": "workflow-skill", "model": easy_followup_model, "effort": easy_followup_effort, "dependencies": ["direct"], "execution_domain": "general"},
                ],
                "main_result_node": "direct",
            }
            plans[f"admitted-complex-{model}-{effort}"] = {
                "schema_version": 2,
                "route_scope": "admitted",
                "complexity": "complex",
                "display": "mermaid",
                "entry": {"model": model, "effort": effort},
                "nodes": [
                    {
                        "id": "audit",
                        "phase": "result",
                        "skill": "workflow-skill",
                        "model": complex_followup_model,
                        "effort": complex_followup_effort,
                        "dependencies": [],
                        "execution_domain": "general",
                    },
                    {
                        "id": "implement",
                        "phase": "result",
                        "skill": "code-skill",
                        "model": implementation_model,
                        "effort": implementation_effort,
                        "dependencies": ["audit"],
                        "execution_domain": "python",
                        "language": "python",
                        "purpose": "implement",
                    },
                    {"id": "ending-real", "phase": "ending", "skill": "verify-skill", "model": complex_followup_model, "effort": complex_followup_effort, "dependencies": ["implement"], "execution_domain": "general"},
                    {"id": "records", "phase": "ending", "skill": "workflow-skill", "model": complex_followup_model, "effort": complex_followup_effort, "dependencies": ["implement"], "execution_domain": "general"},
                ],
                "main_result_node": "implement",
            }
    return plans


def validate(skill_dir, models_cache_path, global_agents_path=Path.home() / ".codex" / "AGENTS.md", global_skills_root=Path.home() / ".codex" / "skills", global_hooks_path=Path.home() / ".codex" / "hooks.json"):
    failures = []
    try:
        validate_profile_preset_registry()
    except ValueError as error:
        failures.append(f"profile-preset registry is invalid: {error}")
    required_profile_presets = {"analysis-complex", "code-complex", "code-easy", "command-generation", "document-complex", "document-easy", "general-answer-easy", "grounded-repository-answer-complex", "grounded-repository-answer-easy", "integration-complex", "spreadsheet-complex", "spreadsheet-easy", "summary-easy", "tiny-code", "tiny-text"}
    if set(PROFILE_PRESETS) != required_profile_presets:
        failures.append("profile-preset registry does not expose the complete stable preset set")
    paths = {relative: skill_dir / relative for relative in REQUIRED_FILES}
    obsidian_memory_path = global_skills_root / "project-memory-skill" / "scripts" / "obsidian_model_memory.py"
    missing_files = []
    for relative, path in paths.items():
        if not path.exists():
            missing_files.append(f"missing required file: {relative}")
    if not obsidian_memory_path.exists():
        missing_files.append("missing required file: project-memory-skill/scripts/obsidian_model_memory.py")
    failures.extend(missing_files)
    if missing_files:
        return {"valid": False, "failures": failures, "plans": [], "graduated": []}
    skill_text = read_text(paths["SKILL.md"])
    agent_text = read_text(paths["agents/openai.yaml"])
    route_text = read_text(paths["references/route-contract.md"])
    selection_text = read_text(paths["references/model-selection.md"])
    receipt_text = read_text(paths["references/runtime-receipts.md"])
    adaptive_text = read_text(paths["references/adaptive-routing.md"])
    shared_ladder_text = read_text(paths["assets/model-capability-ladder.json"])
    receipt_script_text = read_text(paths["scripts/model_execution_receipt.py"])
    benchmark_gate_text = read_text(paths["scripts/benchmark_suite_gate.py"])
    benchmark_runner_text = read_text(paths["scripts/benchmark_suite_runner.py"])
    adaptive_runner_text = read_text(paths["scripts/obsidian_adaptive_model_runner.py"])
    obsidian_memory_text = read_text(obsidian_memory_path)
    strategy_performance_text = read_text(paths["scripts/strategy_performance.py"])
    dispatcher_text = read_text(paths["scripts/task_route_dispatcher.py"])
    model_registry_text = read_text(paths["scripts/model_registry.py"])
    sync_model_capabilities_text = read_text(paths["scripts/sync_model_capabilities.py"])
    entry_asset_text = read_text(paths["assets/global-agents-entry-rule.md"])
    metadata = parse_frontmatter(skill_text)
    if set(metadata) != {"name", "description"} or metadata.get("name") != "task-analyze-skill":
        failures.append("frontmatter must contain only name=task-analyze-skill and description")
    if len(metadata.get("description", "")) > 1024:
        failures.append("frontmatter description exceeds 1024 characters")
    prompt_length = folded_prompt_length(agent_text)
    if prompt_length is None or prompt_length > 1024:
        failures.append(f"agent default_prompt invalid length: {prompt_length}")
    failures.extend(missing_terms("agents/openai.yaml", agent_text, ["eligible text/code producer", "saved catalog ladder", "optional priority producer first", "easy low; complex high", "selected quality pair as zero-result fallback", "Ordinary tasks never scan the model cache", "explicit user model-update", "unavailable cache keeps the saved ladder", "no network fetch", "Project, task, module, file, symbol, and code stay record fields on the broad page", "no hierarchy note is created", "bind the producer receipt to independent Ending", "terminal event writes PASS/FAIL learning", "quality-pair repair", "Multi-node savings need proof", "Load prompt-skill", "Exact read-only is bounded inline", "Final needs PASS or BLOCKED", "different verifier", "No hook", "visible machine plan"]))
    failures.extend(missing_terms("SKILL.md", skill_text, REQUIRED_SKILL_TEXT))
    failures.extend(missing_terms("route-contract", route_text, REQUIRED_ROUTE_TEXT))
    failures.extend(missing_terms("model-selection", selection_text, REQUIRED_SELECTION_TEXT))
    failures.extend(missing_terms("runtime-receipts", receipt_text, REQUIRED_RECEIPT_TEXT))
    failures.extend(missing_terms("adaptive-routing", adaptive_text, REQUIRED_ADAPTIVE_TEXT))
    failures.extend(missing_terms("SKILL.md model switch", skill_text, REQUIRED_MODEL_SWITCH_CATEGORIES + REQUIRED_MODEL_SWITCH_DIRECTIONS))
    failures.extend(missing_terms("adaptive-routing model switch", adaptive_text, REQUIRED_MODEL_SWITCH_CATEGORIES + REQUIRED_MODEL_SWITCH_DIRECTIONS))
    failures.extend(validate_shared_ladder(shared_ladder_text))
    failures.extend(missing_terms("Obsidian adaptive runner", adaptive_runner_text, REQUIRED_OBSIDIAN_RUNNER_IMPLEMENTATION))
    failures.extend(missing_terms("Obsidian model memory", obsidian_memory_text, REQUIRED_OBSIDIAN_MEMORY_IMPLEMENTATION))
    failures.extend(missing_terms("dynamic model registry", model_registry_text, REQUIRED_MODEL_REGISTRY_IMPLEMENTATION))
    failures.extend(missing_terms("model capability sync", sync_model_capabilities_text, ["model_registry", "load_catalog", "build_registry", "refresh_registry", "registry_matches_catalog", "model-capabilities.md", "--update", "--check"]))
    for label, implementation_text in (("Obsidian adaptive runner", adaptive_runner_text), ("Obsidian model memory", obsidian_memory_text)):
        if "model_experience.json" in implementation_text or "local/adaptive-routing" in implementation_text:
            failures.append(f"{label} must not fall back to local model_experience.json")
    failures.extend(missing_terms("receipt entry guard", receipt_script_text, REQUIRED_RECEIPT_GUARD_IMPLEMENTATION))
    failures.extend(missing_terms("benchmark mode gate", benchmark_gate_text, ["receipt_node_type_mismatch", "receipt_entry_context_active", "receipt_authorization_source_mismatch", "receipt_benchmark_run_id_mismatch", "receipt_workload_id_mismatch", "receipt_raw_prompt_mismatch", "receipt_result_ready_event_invalid", "receipt_result_ready_timing_mismatch", "benchmark-global-inline", "bootstrap-task", "MAXIMUM_PAIRED_TIME_REGRESSION_MS = 2_000", "material_pair_regression_count"]))
    failures.extend(missing_terms("benchmark runner mode", benchmark_runner_text, ["--direct-task", "--bootstrap-task", "benchmark-{run_plan['run_id']}", "role = \"result-producer\"", "receipt_result_ready_event_invalid", "receipt_result_ready_timing_invalid", "result_ready_monotonic_ns", "benchmark-runner-monotonic", "time.monotonic_ns()"]))
    failures.extend(missing_terms("adaptive runner authorization", adaptive_runner_text, ["with model_execution_receipt.adaptive_producer_authorization()", "obsidian_model_memory.recommend_model", "node_role=\"result-producer\""]))
    failures.extend(missing_terms("dispatcher result verifier boundary", dispatcher_text, ["verify-skill result nodes require user_requested_verification_result=true", "user_requested_verification_result is valid only on a result-phase verify-skill node", "Completed dependency handoff"]))
    failures.extend(missing_terms("strategy performance admission", strategy_performance_text, REQUIRED_STRATEGY_PERFORMANCE))
    failures.extend(missing_terms("dispatcher role authorization", dispatcher_text, ["with receipt_module.dispatcher_node_authorization(args.node_role)"]))
    if "/local/" not in read_text(paths[".gitignore"]):
        failures.append("task-analyze-skill .gitignore must exclude /local/")
    for obsolete_path in (skill_dir / "assets" / "hooks.json", skill_dir / "scripts" / "task_entry_hook.py", skill_dir / "tests" / "test_task_entry_hook.py"):
        if obsolete_path.exists():
            failures.append(f"obsolete hook artifact remains: {obsolete_path.relative_to(skill_dir)}")
    for label, contract_text in (("SKILL.md", skill_text), ("model-selection", selection_text), ("adaptive-routing", adaptive_text)):
        failures.extend(legacy_only_failures(label, contract_text))
    live_text = "\n".join([skill_text, agent_text, route_text, selection_text, receipt_text, adaptive_text])
    for forbidden in FORBIDDEN_TEXT:
        if normalize(forbidden) in normalize(live_text):
            failures.append(f"live contract contains obsolete text: {forbidden}")
    if not global_agents_path.exists():
        failures.append(f"always-loaded global AGENTS.md is missing: {global_agents_path}")
    else:
        global_agents_text = read_text(global_agents_path)
        failures.extend(missing_terms("global AGENTS", global_agents_text, REQUIRED_GLOBAL_BOOTSTRAP_TEXT))
        if len(global_agents_text.encode("utf-8")) > MAX_GLOBAL_BOOTSTRAP_BYTES:
            failures.append(f"global AGENTS exceeds compact bootstrap limit: {len(global_agents_text.encode('utf-8'))} > {MAX_GLOBAL_BOOTSTRAP_BYTES} bytes")
        for forbidden in FORBIDDEN_GLOBAL_BOOTSTRAP_TEXT:
            if normalize(forbidden) in normalize(global_agents_text):
                failures.append(f"global AGENTS contains forbidden hook or machine-plan contract: {forbidden}")
    failures.extend(missing_terms("global entry asset", entry_asset_text, REQUIRED_GLOBAL_ENTRY_ASSET_TEXT))
    if global_agents_path.exists() and entry_asset_text.replace(GLOBAL_ENTRY_ASSET_DIRECTIVE, "", 1) != global_agents_text:
        failures.append("global entry asset does not exactly match global AGENTS after removing its merge directive")
    for forbidden in FORBIDDEN_GLOBAL_BOOTSTRAP_TEXT:
        if normalize(forbidden) in normalize(entry_asset_text):
            failures.append(f"global entry asset contains forbidden hook or machine-plan contract: {forbidden}")
    if global_hooks_path.exists() and "task_entry_hook.py" in read_text(global_hooks_path):
        failures.append(f"obsolete Task Analyze lifecycle hook is still installed: {global_hooks_path}")
    code_reference_contracts = {
        "Python code rules": (global_skills_root / "code-skill" / "references" / "python-rules.md", REQUIRED_PYTHON_REFERENCE_TEXT),
        "C# code rules": (global_skills_root / "code-skill" / "references" / "csharp-rules.md", REQUIRED_CSHARP_REFERENCE_TEXT),
        "Unity C# code rules": (global_skills_root / "code-skill" / "references" / "unity-csharp-rules.md", REQUIRED_UNITY_REFERENCE_TEXT),
    }
    for label, (reference_path, required_terms) in code_reference_contracts.items():
        if not reference_path.exists():
            failures.append(f"{label} missing: {reference_path}")
            continue
        reference_text = read_text(reference_path)
        failures.extend(missing_terms(label, reference_text, required_terms))
        if "check before the main result" in normalize(reference_text) or "test the edited path with the smallest proportional check before the main result" in normalize(reference_text):
            failures.append(f"{label} still gates first presentation with a foreground check")
    prompt_contracts = {"Prompt skill": (global_skills_root / "prompt-skill" / "SKILL.md", REQUIRED_PROMPT_SKILL_TEXT), "Prompt skill agent": (global_skills_root / "prompt-skill" / "agents" / "openai.yaml", REQUIRED_PROMPT_AGENT_TEXT)}
    for label, (prompt_path, required_terms) in prompt_contracts.items():
        if not prompt_path.exists():
            failures.append(f"{label} missing: {prompt_path}")
            continue
        failures.extend(missing_terms(label, read_text(prompt_path), required_terms))
    nested_skill_files = [path for path in global_skills_root.rglob("SKILL.md") if ".system" not in path.relative_to(global_skills_root).parts and path.parent.parent != global_skills_root]
    if nested_skill_files:
        failures.append(f"loader-visible nested SKILL.md files remain under global skills: {len(nested_skill_files)}")
    capability_status = {"valid": True, "status": "saved", "error": None, "expected_catalog_sha256": None, "observed_catalog_sha256": None}
    installed = installed_skills(global_skills_root)
    plans = sample_plans()
    expected_plan_count = sum(len(efforts) for efforts in ACTIVE_MODEL_EFFORTS.values())
    expected_route_plan_count = expected_plan_count * 2
    if len(plans) != expected_route_plan_count:
        failures.append(f"sample plans do not cover admitted single+complex entry pairs (expected {expected_route_plan_count}, got {len(plans)})")
    if len({(plan["entry"]["model"], plan["entry"]["effort"]) for plan in plans.values()}) != expected_plan_count:
        failures.append("sample plans do not cover arbitrary supported entry model + effort")
    if not any(plan["complexity"] == "complex" for plan in plans.values()):
        failures.append("sample plans must include at least one complex route")
    plan_results = []
    for name, plan in plans.items():
        plan_failures = validate_plan(plan, installed, global_skills_root)
        plan_results.append({"name": name, "status": "pass" if not plan_failures else "fail", "failures": plan_failures})
        failures.extend([f"plan {name}: {failure}" for failure in plan_failures])
    fixture_path = skill_dir / "assets" / "graduated-route-fixtures.json"
    graduated_failures = validate_graduated_fixture(fixture_path, global_skills_root, True)
    try:
        graduated_count = len(json.loads(fixture_path.read_text(encoding="utf-8")).get("scenarios", []))
    except (OSError, json.JSONDecodeError):
        graduated_count = 0
    graduated_results = [{"name": "graduated-raw-prompts", "status": "pass" if not graduated_failures else "fail", "failures": graduated_failures, "scenario_count": graduated_count}]
    failures.extend([f"graduated scenario: {failure}" for failure in graduated_failures])
    return {"valid": not failures, "skill_dir": str(skill_dir), "capability_status": capability_status, "plans": plan_results, "graduated": graduated_results, "failures": failures}


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
    for scenario in result["graduated"]:
        print(f"task-analyze-skill graduated {scenario['name']}: {scenario['scenario_count'] if scenario['status'] == 'pass' else 0}/{scenario['scenario_count']} passed")
    if result["failures"]:
        print("Failures:", file=sys.stderr)
        for failure in result["failures"]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

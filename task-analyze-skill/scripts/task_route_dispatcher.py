#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
import queue
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

try:
    from skill_resolver import resolve_skill_path
except ModuleNotFoundError:
    _skill_resolver_path = Path(__file__).with_name("skill_resolver.py")
    _skill_resolver_spec = importlib.util.spec_from_file_location("task_analyze_skill_resolver", _skill_resolver_path)
    _skill_resolver = importlib.util.module_from_spec(_skill_resolver_spec)
    _skill_resolver_spec.loader.exec_module(_skill_resolver)
    resolve_skill_path = _skill_resolver.resolve_skill_path


RECEIPT_PATH = Path(__file__).resolve().parent / "model_execution_receipt.py"
RECEIPT_SPEC = importlib.util.spec_from_file_location(
    "task_analyze_model_execution_receipt", RECEIPT_PATH
)
receipt_module = importlib.util.module_from_spec(RECEIPT_SPEC)
RECEIPT_SPEC.loader.exec_module(receipt_module)
DISCLOSURE_PATH = Path(__file__).resolve().parent / "model_identity_disclosure.py"
DISCLOSURE_SPEC = importlib.util.spec_from_file_location(
    "task_analyze_model_identity_disclosure", DISCLOSURE_PATH
)
model_identity_disclosure = importlib.util.module_from_spec(DISCLOSURE_SPEC)
DISCLOSURE_SPEC.loader.exec_module(model_identity_disclosure)
try:
    from routing_policy import (
        ACTIVE_MODEL_EFFORTS,
        ENDING_FAST_CONFIG,
        ENDING_FAST_PRIMARY_PAIR,
        EXECUTION_DOMAINS,
        MODEL_ROLE_PAIRS,
        PRIORITY_PRODUCER_CONFIG,
        adaptive_pair_texts_for_profile,
        analyze_prompt_routing,
        code_rule_bundle,
        ending_fast_route_fields,
        execution_lifecycle_contract,
        execution_domain_is_active,
        expected_owner_skill,
        is_code_execution_domain,
        normal_adaptive_pair_texts,
        resolve_execution_domain,
        validate_execution_domain_registry,
    )
except ModuleNotFoundError:
    import importlib.util as _importlib_util

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = _importlib_util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = _importlib_util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    ACTIVE_MODEL_EFFORTS = _routing_policy.ACTIVE_MODEL_EFFORTS
    ENDING_FAST_CONFIG = _routing_policy.ENDING_FAST_CONFIG
    ENDING_FAST_PRIMARY_PAIR = _routing_policy.ENDING_FAST_PRIMARY_PAIR
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    MODEL_ROLE_PAIRS = _routing_policy.MODEL_ROLE_PAIRS
    PRIORITY_PRODUCER_CONFIG = _routing_policy.PRIORITY_PRODUCER_CONFIG
    adaptive_pair_texts_for_profile = _routing_policy.adaptive_pair_texts_for_profile
    analyze_prompt_routing = _routing_policy.analyze_prompt_routing
    code_rule_bundle = _routing_policy.code_rule_bundle
    ending_fast_route_fields = _routing_policy.ending_fast_route_fields
    execution_lifecycle_contract = _routing_policy.execution_lifecycle_contract
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    expected_owner_skill = _routing_policy.expected_owner_skill
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    normal_adaptive_pair_texts = _routing_policy.normal_adaptive_pair_texts
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry

HISTORY_PATH = Path(__file__).resolve().parent / "model_routing_history.py"
HISTORY_SPEC = importlib.util.spec_from_file_location(
    "task_analyze_model_routing_history", HISTORY_PATH
)
routing_history_module = importlib.util.module_from_spec(HISTORY_SPEC)
HISTORY_SPEC.loader.exec_module(routing_history_module)

OBSIDIAN_MEMORY_PATH = Path(__file__).resolve().parents[2] / "project-memory-skill" / "scripts" / "obsidian_model_memory.py"
OBSIDIAN_MEMORY_SPEC = importlib.util.spec_from_file_location("task_route_obsidian_model_memory", OBSIDIAN_MEMORY_PATH)
obsidian_model_memory = importlib.util.module_from_spec(OBSIDIAN_MEMORY_SPEC)
OBSIDIAN_MEMORY_SPEC.loader.exec_module(obsidian_model_memory)

_selected_policy_spec = importlib.util.spec_from_file_location("dispatcher_selected_model_policy", Path(__file__).with_name("selected_model_policy.py"))
selected_model_policy = importlib.util.module_from_spec(_selected_policy_spec)
_selected_policy_spec.loader.exec_module(selected_model_policy)

NODE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
DISPATCH_SCHEMA_VERSION = 2
DYNAMIC_ROUTING_MODE = "dynamic_task_graph"
ALLOWED_PHASES = {"result", "ending"}
ALLOWED_SANDBOXES = {"read-only", "workspace-write"}
DETERMINISTIC_SOURCE_READ = "deterministic-source-read"
DECOMPOSITION_POLICY = "max_safe"
ALLOWED_OPERATIONS = {"text", "code", "write", "execute", "other"}
ALLOWED_DECOMPOSITION_COUPLINGS = {"linear", "independent"}
ALLOWED_SPARK_EXCEPTION_CATEGORIES = {
    "ambiguity",
    "safety",
    "policy",
    "integration",
    "external_dependency",
    "quality_failure",
}
ENDING_SKILL = "project-memory-skill"
PROJECT_RESULT_CONSISTENCY_ACTIONS = {
    name: {"ending_status": "pass", "action": action, "memory_write": True, "existing_session_mutation": False}
    for name, action in {"aligned": "merge_current_memory", "no_prior_memory": "skip_missing_memory", "memory_record_defect": "correct_memory", "memory_projection_defect": "reconcile_projection"}.items()
}
PROJECT_RESULT_CONSISTENCY_POLICY = {"correction_owner": "ending_memory_only", "producer_defect_owner": "active_task", "next_task_memory": "project_scoped_current_only", "actions": PROJECT_RESULT_CONSISTENCY_ACTIONS}
ENDING_TERMINAL_CLOSEOUT = {"purpose": "memory_only", "model_policy": "user_selected", "verification_owner": "active_task"}


CONTROLLED_FIELDS = [
    "task_family",
    "artifact",
    "scope",
    "ambiguity",
    "modality",
    "risk",
    "complexity",
    "owning_skill",
    "project_family",
    "verification_shape",
    "execution_domain",
]
RECOMMENDATION_PROOF_FIELDS = ("selected_pair", "trial", "reason", "profile_fingerprint", "calibration_state", "best_pair", "selection_basis")

DISPATCHER_SKILLS_ROOT = Path(__file__).resolve().parents[2]


def complexity_band(score):
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("complexity score must be an integer from 0 to 100")
    if score <= 24:
        return "small"
    if score <= 49:
        return "standard"
    if score <= 74:
        return "complex"
    return "advanced"


def score_role_pair(score):
    band = complexity_band(score)
    role = {"small": "weak_default", "standard": "balanced_default", "complex": "balanced_complex", "advanced": "frontier_complex"}[band]
    return MODEL_ROLE_PAIRS[role]


def apply_ending_fast_route(plan):
    """Compatibility name: Ending now preserves the selected pair and writes memory."""
    entry = plan.get("entry", {})
    for node in plan.get("nodes", []):
        if isinstance(node, dict) and node.get("phase") == "ending":
            model = entry.get("model") or node.get("_entry_model") or node.get("model")
            effort = entry.get("effort") or node.get("_entry_effort") or node.get("effort")
            selected_model_policy.bind_node(node, model, effort)
            node["skill"] = ENDING_SKILL
            node["terminal_closeout"] = dict(ENDING_TERMINAL_CLOSEOUT)
    return plan


def ending_checklist_failures(node):
    forbidden = {"acceptance_checks", "verifies_node", "repair_launch", "check_workers"}.intersection(node)
    return [f"{node.get('id', 'ending')} Ending is memory-only; move {field} into active-task verification" for field in sorted(forbidden)]


def ending_worker_prompt(node):
    return ("Summarize completed changes and durable user preferences into current project memory. "
            "Use the user's selected model and effort. Read only this project's relevant existing memory; skip absent memory. "
            "Do not run tests, verify results, repair code or create tasks. "
            + node.get("prompt", ""))


def project_result_consistency_action(classification):
    if classification not in PROJECT_RESULT_CONSISTENCY_ACTIONS:
        raise ValueError(f"unknown project-result consistency classification: {classification}")
    return dict(PROJECT_RESULT_CONSISTENCY_ACTIONS[classification])


def ending_availability_fallback(receipt):
    return bool(isinstance(receipt, dict) and receipt.get("status") != "pass" and receipt.get("failure_class") == "availability" and receipt.get("turn_completed") is not True and receipt.get("result_published") is not True)


def _get_node_decomposition(node, decomposition):
    if not isinstance(decomposition, dict):
        return None
    node_id = node.get("id")
    for stage in decomposition.get("stage_inventory", []):
        if not isinstance(stage, dict):
            continue
        if stage.get("node_id") == node_id:
            return stage
    return None


def _stage_id_by_node(node, decomposition):
    stage = _get_node_decomposition(node, decomposition)
    return stage.get("stage_id") if isinstance(stage, dict) else None


def _stage_for_node_id(plan, node_id):
    if not isinstance(plan, dict) or not isinstance(node_id, str):
        return None
    return _get_node_decomposition({"id": node_id}, plan.get("decomposition", {}))


def normalize_legacy_dynamic_plan(plan):
    if plan.get("routing_mode") != DYNAMIC_ROUTING_MODE:
        return plan
    decomposition = plan.get("decomposition")
    stage_inventory = decomposition.get("stage_inventory") if isinstance(decomposition, dict) else None
    nodes = plan.get("nodes")
    if not isinstance(decomposition, dict) or decomposition.get("policy") != DECOMPOSITION_POLICY or not isinstance(stage_inventory, list) or not isinstance(nodes, list):
        return plan
    result_nodes = [node for node in nodes if isinstance(node, dict) and node.get("phase") == "result" and isinstance(node.get("id"), str)]
    stage_by_node = {stage.get("node_id"): stage for stage in stage_inventory if isinstance(stage, dict) and isinstance(stage.get("node_id"), str)}
    if set(stage_by_node) != {node["id"] for node in result_nodes}:
        return plan
    if any(not isinstance(stage.get("logical_stage_ids"), list) or stage.get("logical_stage_ids") != [stage.get("stage_id")] for stage in stage_inventory):
        return plan
    node_by_id = {node["id"]: node for node in result_nodes}
    for node_id, stage in stage_by_node.items():
        stage["dependencies"] = list(node_by_id[node_id].get("dependencies", []))
    wave_by_node = _summary_dependency_wave(node_by_id)
    waves = {}
    for node_id, wave in wave_by_node.items():
        waves.setdefault(wave, []).append(node_id)
    for members in waves.values():
        if len(members) < 2:
            continue
        stages = [stage_by_node[member] for member in members]
        if any(stage.get("coupling") != "linear" or stage.get("parallelizable") is not False or stage.get("deterministic_merge_node") for stage in stages):
            continue
        common_dependents = sorted(node_id for node_id, node in node_by_id.items() if set(members).issubset(set(node.get("dependencies", []))))
        if len(common_dependents) != 1:
            continue
        if any(set(stage.get("inputs", [])).intersection(other.get("inputs", [])) or set(stage.get("mutable_state", [])).intersection(other.get("mutable_state", [])) for index, stage in enumerate(stages) for other in stages[index + 1 :]):
            continue
        for stage in stages:
            stage["coupling"] = "independent"
            stage["parallelizable"] = True
            stage["deterministic_merge_node"] = common_dependents[0]
    return plan


def execution_lifecycle_for_plan(plan):
    result_node_count = sum(isinstance(node, dict) and node.get("phase") == "result" for node in plan.get("nodes", []))
    score = plan.get("complexity_score")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        score = 65 if plan.get("complexity") == "complex" else 35
    graph_admitted = plan.get("routing_mode") == DYNAMIC_ROUTING_MODE or result_node_count > 1
    return execution_lifecycle_contract(score, bool(plan.get("fast_path_eligible")), graph_admitted, max(1, result_node_count), plan.get("risk", "low"), plan.get("ambiguity", "low"))


def _dynamic_spark_eligible(node, stage=None):
    if selected_model_policy.uses_selected_model(node):
        return False
    if node.get("phase") != "result":
        return False
    try:
        score = node["complexity_score"]
        if complexity_band(score) != "small":
            return False
    except (KeyError, ValueError):
        return False
    condition = node.get("routing_condition") if isinstance(node.get("routing_condition"), dict) else {}
    if condition.get("modality", "text") != "text" or condition.get("risk", "low") != "low" or condition.get("ambiguity", "low") != "low":
        return False
    if stage is not None:
        return stage.get("operation") in {"text", "code", "write", "execute"} and stage.get("external_side_effects") is False
    purpose = node.get("purpose")
    task_family = condition.get("task_family")
    eligible_purpose = purpose in PRIORITY_PRODUCER_CONFIG.get("task_segment_purposes", [])
    eligible_family = task_family in {"tiny_text", "tiny_code", "command_generation"}
    eligible_source = isinstance(node.get("source_allowlist"), list) and len(node["source_allowlist"]) == 1
    return eligible_purpose or eligible_family or eligible_source


def _priority_result_node(node, stage=None):
    if PRIORITY_PRODUCER_CONFIG.get("enabled") is not True or node.get("priority_producer") is not True or node.get("phase") != "result":
        return False
    if node.get("model") != PRIORITY_PRODUCER_CONFIG.get("id") or node.get("effort") not in PRIORITY_PRODUCER_CONFIG.get("adaptive_efforts", []):
        return False
    legacy_source_branch = node.get("skill") == "workflow-skill" and node.get("dependencies") == [] and node.get("sandbox", "read-only") == "read-only" and isinstance(node.get("source_allowlist"), list) and len(node["source_allowlist"]) == 1
    dynamic_segment = _dynamic_spark_eligible(node, stage) and node.get("selection_basis") == "spark_priority" and node.get("effort") == PRIORITY_PRODUCER_CONFIG["effort_by_complexity"]["easy"]
    return legacy_source_branch or dynamic_segment


def resolve_skills_root(skills_root=None):
    if skills_root is None:
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
        installed_skills_root = codex_home / "skills"
        return installed_skills_root if installed_skills_root.is_dir() else DISPATCHER_SKILLS_ROOT
    return Path(skills_root).resolve()


def resolve_node_skill_path(skill_id, skills_root):
    try:
        return resolve_skill_path(skill_id, skills_root)
    except ValueError:
        return None


def _resolve_execution_domain(node):
    domain, _ = _resolve_execution_domain_with_flag(node)
    return domain


def _resolve_execution_domain_with_flag(node):
    explicit_domain = node.get("execution_domain")
    domain = resolve_execution_domain(
        owning_skill=node.get("skill"),
        task_family=node.get("task_family"),
        explicit_domain=explicit_domain,
        language=node.get("language"),
        purpose=node.get("purpose"),
    )
    return domain, bool(explicit_domain)


def _is_code_implementation(node):
    if node.get("phase") != "result":
        return False
    if node.get("purpose") in {"implement", "author-probe"}:
        return True
    try:
        execution_domain = _resolve_execution_domain(node)
    except ValueError:
        return False
    return is_code_execution_domain(execution_domain)


def _node_code_rule_bundle(node):
    execution_domain = _resolve_execution_domain(node)
    return code_rule_bundle(execution_domain, node.get("prompt", ""), node.get("language"), node.get("purpose", ""), (node.get("routing_condition") or {}).get("task_family", ""))


def _emit_code_gate_notice(bundle, node_id):
    event = {"schema_version": 1, "stage": "code-rule-notice", "user_visible": True, "node_id": node_id, **bundle}
    print(json.dumps(event, ensure_ascii=False, separators=(",", ":")), flush=True)


def receipt_node_role(node):
    if node.get("phase") == "ending":
        return "ending"
    if node.get("purpose") == "repair":
        return "repair"
    return "result-producer"


def _model_memory_task_type(node):
    condition = node.get("routing_condition") or {}
    family = str(condition.get("task_family") or "").lower()
    artifact = str(condition.get("artifact") or "").lower()
    execution_domain = str(condition.get("execution_domain") or "general").lower()
    if execution_domain != "general" or artifact in {"code", "script"}:
        return "debug" if family == "debug" else "code"
    if family in {"summary", "debug", "integration", "prompt", "visual"}:
        return family
    if artifact in {"spreadsheet", "workbook", "sheet"}:
        return "spreadsheet"
    if artifact in {"document", "report", "pdf"}:
        return "document"
    if artifact in {"image", "visual"}:
        return "visual"
    if artifact == "prompt":
        return "prompt"
    return "question"


def _model_memory_arguments(node, project_root, entry_model=None, entry_effort=None):
    condition = node.get("routing_condition") or {}
    scope = node.get("model_memory_scope") if isinstance(node.get("model_memory_scope"), dict) else {}
    return {
        "project_root": Path(project_root).expanduser().resolve(),
        "governing_skills": selected_model_policy.governing_skills(node),
        "skill_governed": selected_model_policy.uses_selected_model(node),
        "task_type": scope.get("task_type") or _model_memory_task_type(node),
        "module": scope.get("module") or node.get("skill") or "project-wide",
        "file_value": scope.get("file") or "",
        "symbol": scope.get("symbol") or "",
        "code_kind": scope.get("code_kind") or condition.get("execution_domain") or "general",
        "operation": scope.get("operation") or condition.get("task_family") or "work",
        "modality": condition.get("modality") or "text",
        "complexity": condition.get("complexity") or "easy",
        "complexity_score": node.get("complexity_score"),
        "risk": condition.get("risk") or "low",
        "ambiguity": condition.get("ambiguity") or "low",
        "task_summary": node.get("task_summary") or "",
        "task_name": scope.get("task_name") or node.get("task_name") or os.environ.get("CODEX_TASK_NAME", ""),
        "task_group": scope.get("task_group") or node.get("task_group") or os.environ.get("CODEX_TASK_GROUP", ""),
        "session_id": os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID", ""),
        "step_kind": scope.get("step_kind") or "",
        "capability_tags": scope.get("capability_tags"),
        "entry_model": entry_model or node.get("_entry_model") or "",
        "entry_effort": entry_effort or node.get("_entry_effort") or "",
    }


def _obsidian_recommendation_and_proof(node, project_root, entry_model=None, entry_effort=None):
    if selected_model_policy.uses_selected_model(node):
        model = entry_model or node.get("_entry_model") or node.get("model")
        effort = entry_effort or node.get("_entry_effort") or node.get("effort")
        recommendation = selected_model_policy.recommendation(model, effort)
        proof = {key: recommendation.get(key) for key in RECOMMENDATION_PROOF_FIELDS}
        proof["profile_fingerprint"] = hashlib.sha256(b"user-selected-skill-model").hexdigest()
        return recommendation, proof
    recommendation = obsidian_model_memory.recommend_model(**_model_memory_arguments(node, project_root, entry_model, entry_effort))
    condition = routing_history_module.validate_condition(node.get("routing_condition"))
    candidate_pairs = routing_history_module.canonical_pairs(node.get("candidate_ladder"))
    static_pair = routing_history_module.parse_pair(node.get("static_suggestion"))
    hard_pair = routing_history_module.parse_pair(node.get("hard_floor"))
    fingerprint = routing_history_module.profile_fingerprint(condition, candidate_pairs, static_pair, hard_pair)
    proof = {
        "selected_pair": recommendation.get("selected_pair"),
        "attempt_pair": recommendation.get("attempt_pair"),
        "active_fallback_pair": recommendation.get("active_fallback_pair"),
        "trial": recommendation.get("trial"),
        "reason": recommendation.get("reason"),
        "profile_fingerprint": fingerprint,
        "capability_fingerprint": recommendation.get("capability_fingerprint"),
        "step_kind": recommendation.get("step_kind"),
        "capability_tags": recommendation.get("capability_tags"),
        "calibration_state": recommendation.get("calibration_state"),
        "best_pair": recommendation.get("success_model"),
        "selection_basis": "dual_model_history" if recommendation.get("memory_available") is True else "shared_cold_start",
        "entry_pair": recommendation.get("entry_pair"),
        "entry_anchor_pair": recommendation.get("entry_anchor_pair"),
        "switch_direction": recommendation.get("switch_direction"),
    }
    return recommendation, proof


def validate_dispatcher_adaptive_result(node):
    try:
        routing_history_module.validate_summary(node.get("task_summary"))
        current_recommendation, current_proof = _obsidian_recommendation_and_proof(node, node.get("_project_root"))
        if not isinstance(current_recommendation, dict) or current_recommendation.get("selected_pair") is None:
            raise receipt_module.ReceiptAuthorizationError("dispatcher_adaptive_recommendation_invalid")
        locked_recommendation = node.get("routing_recommendation")
        selected_pair = f"{node['model']}|{node['effort']}"
        if not isinstance(locked_recommendation, dict) or current_proof.get("selected_pair") != selected_pair or current_proof.get("trial") is not node.get("trial") or any(locked_recommendation.get(field) != current_proof.get(field) for field in RECOMMENDATION_PROOF_FIELDS):
            raise receipt_module.ReceiptAuthorizationError("dispatcher_adaptive_recommendation_invalid")
    except receipt_module.ReceiptAuthorizationError:
        raise
    except (KeyError, OSError, TypeError, ValueError):
        raise receipt_module.ReceiptAuthorizationError("dispatcher_adaptive_recommendation_invalid")
    return current_recommendation


def path_is_within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def dependency_closure(node_id, node_by_id):
    closure = set()
    pending = list(node_by_id.get(node_id, {}).get("dependencies", []))
    while pending:
        dependency = pending.pop()
        if dependency in closure or dependency not in node_by_id:
            continue
        closure.add(dependency)
        pending.extend(node_by_id[dependency].get("dependencies", []))
    return closure


def dependency_wave(node_id, node_by_id, memo=None):
    memo = {} if memo is None else memo
    if node_id in memo:
        return memo[node_id]
    dependencies = node_by_id[node_id].get("dependencies", [])
    result_dependencies = [dependency for dependency in dependencies if dependency in node_by_id and node_by_id[dependency].get("phase") == "result"]
    memo[node_id] = 0 if not result_dependencies else max(dependency_wave(dependency, node_by_id, memo) for dependency in result_dependencies) + 1
    return memo[node_id]


def _summary_dependency_wave(node_by_id):
    remaining = set(node_by_id)
    waves = {}
    while remaining:
        ready = sorted(node_id for node_id in remaining if all(dependency in waves for dependency in node_by_id[node_id].get("dependencies", []) if dependency in node_by_id))
        if not ready:
            for node_id in sorted(remaining):
                waves[node_id] = None
            break
        for node_id in ready:
            dependency_waves = [waves[dependency] for dependency in node_by_id[node_id].get("dependencies", []) if dependency in waves]
            waves[node_id] = 0 if not dependency_waves else max(dependency_waves) + 1
            remaining.remove(node_id)
    return waves


def validate_dynamic_decomposition(plan, node_by_id):
    failures = []
    if plan.get("routing_mode") != DYNAMIC_ROUTING_MODE:
        return failures
    decomposition = plan.get("decomposition")
    if not isinstance(decomposition, dict):
        failures.append("decomposition is required for dynamic_task_graph plans")
        return failures

    policy = decomposition.get("policy")
    if policy != DECOMPOSITION_POLICY:
        failures.append(f"decomposition.policy must be {DECOMPOSITION_POLICY}")

    stage_inventory = decomposition.get("stage_inventory")
    if not isinstance(stage_inventory, list):
        failures.append("decomposition.stage_inventory must be a non-empty list")
        return failures
    if not stage_inventory:
        failures.append("decomposition.stage_inventory must contain at least one entry")

    stage_by_node = {}
    stage_ids = set()
    stage_nodes = set()
    for index, stage in enumerate(stage_inventory, start=1):
        if not isinstance(stage, dict):
            failures.append(f"decomposition stage #{index} must be an object")
            continue
        stage_id = stage.get("stage_id")
        node_id = stage.get("node_id")
        if not isinstance(stage_id, str) or not stage_id:
            failures.append(f"decomposition stage #{index} is missing stage_id")
            continue
        if stage_id in stage_ids:
            failures.append(f"decomposition stage_id must be unique: {stage_id}")
        stage_ids.add(stage_id)

        if not isinstance(node_id, str) or not node_id:
            failures.append(f"decomposition stage {stage_id} is missing node_id")
            continue
        if node_id in stage_nodes:
            failures.append(f"decomposition covers result node more than once: {node_id}")
            continue
        stage_nodes.add(node_id)
        stage_by_node[node_id] = stage

        if node_id not in node_by_id:
            failures.append(f"decomposition node_id does not exist: {node_id}")
            continue
        if node_by_id[node_id].get("phase") != "result":
            failures.append(f"decomposition node_id must be a result node: {node_id}")
            continue
        node = node_by_id[node_id]
        stage_node_id = stage.get("node_id")
        if stage_node_id != node_id:
            failures.append(f"decomposition stage {stage_id} node_id mismatch while validating result mapping")

        required_fields = (
            "logical_stage_ids",
            "purpose",
            "score",
            "band",
            "model_intent",
            "operation",
            "dependencies",
            "inputs",
            "outputs",
            "stop_condition",
            "coupling",
            "parallelizable",
            "objective_scope",
            "mutable_state",
            "failure_escalation",
            "external_side_effects",
        )
        for required in required_fields:
            if required not in stage:
                failures.append(f"decomposition stage {stage_id} is missing required field {required}")
        logical_stage_ids = stage.get("logical_stage_ids")
        if not isinstance(logical_stage_ids, list) or len(logical_stage_ids) == 0:
            failures.append(f"decomposition stage {stage_id} requires logical_stage_ids")
            logical_stage_ids = []
        elif any(not isinstance(logical_stage_id, str) or not logical_stage_id for logical_stage_id in logical_stage_ids) or len(set(logical_stage_ids)) != len(logical_stage_ids):
            failures.append(f"decomposition stage {stage_id} logical_stage_ids must be unique non-empty strings")
        elif stage_id not in logical_stage_ids:
            failures.append(f"decomposition stage {stage_id} logical_stage_ids must include stage_id")
        if len(logical_stage_ids) > 1:
            if stage.get("coupling") != "linear":
                failures.append(f"decomposition stage {stage_id} must use coupling=linear when logical_stage_ids has multiple entries")
            if stage.get("parallelizable") is not False:
                failures.append(f"decomposition stage {stage_id} requires parallelizable=false when logical_stage_ids are split")
            if not isinstance(stage.get("continuity_reason"), str) or not stage.get("continuity_reason").strip():
                failures.append(f"decomposition stage {stage_id} requires continuity_reason when logical_stage_ids has multiple entries")

        if stage.get("operation") not in ALLOWED_OPERATIONS:
            failures.append(f"decomposition stage {stage_id} operation must be one of {', '.join(sorted(ALLOWED_OPERATIONS))}")
        if stage.get("score") != node.get("complexity_score"):
            failures.append(f"decomposition stage {stage_id} score must match node {node_id} complexity_score")
        if stage.get("band") != node.get("complexity_band"):
            failures.append(f"decomposition stage {stage_id} band must match node {node_id} complexity_band")
        try:
            if not isinstance(stage.get("model_intent"), str):
                raise ValueError
            model_intent_model, model_intent_effort = stage["model_intent"].split("|")
            if model_intent_model != node.get("model") or model_intent_effort != node.get("effort"):
                failures.append(f"decomposition stage {stage_id} model_intent must match node {node_id} model/effort")
        except ValueError:
            failures.append(f"decomposition stage {stage_id} model_intent must be model|effort")
        if not isinstance(stage.get("dependencies"), list):
            failures.append(f"decomposition stage {stage_id} dependencies must be a list")
        elif stage.get("dependencies") != node.get("dependencies", []):
            failures.append(f"decomposition stage {stage_id} dependencies must match node {node_id} dependencies")
        if not isinstance(stage.get("inputs"), list):
            failures.append(f"decomposition stage {stage_id} inputs must be a list")
        elif any(not isinstance(value, str) or not value for value in stage["inputs"]):
            failures.append(f"decomposition stage {stage_id} inputs must contain concrete artifact ids")
        if not isinstance(stage.get("outputs"), list):
            failures.append(f"decomposition stage {stage_id} outputs must be a list")
        elif any(not isinstance(value, str) or not value for value in stage["outputs"]):
            failures.append(f"decomposition stage {stage_id} outputs must contain concrete artifact ids")
        if not isinstance(stage.get("mutable_state"), list):
            failures.append(f"decomposition stage {stage_id} mutable_state must be a list")
        elif any(not isinstance(value, str) or not value for value in stage["mutable_state"]):
            failures.append(f"decomposition stage {stage_id} mutable_state must contain state ids")
        if not isinstance(stage.get("external_side_effects"), bool):
            failures.append(f"decomposition stage {stage_id} external_side_effects must be a boolean")
        if not isinstance(stage.get("stop_condition"), str) or not stage.get("stop_condition"):
            failures.append(f"decomposition stage {stage_id} requires stop_condition")
        if not isinstance(stage.get("purpose"), str) or not stage.get("purpose").strip():
            failures.append(f"decomposition stage {stage_id} requires purpose")
        if not isinstance(stage.get("objective_scope"), str) or not stage.get("objective_scope").strip():
            failures.append(f"decomposition stage {stage_id} requires objective_scope")
        if stage.get("failure_escalation") != "quality_upgrade_one_notch":
            failures.append(f"decomposition stage {stage_id} requires failure_escalation=quality_upgrade_one_notch")
        coupling = stage.get("coupling")
        if coupling not in ALLOWED_DECOMPOSITION_COUPLINGS:
            failures.append(f"decomposition stage {stage_id} coupling must be one of {', '.join(sorted(ALLOWED_DECOMPOSITION_COUPLINGS))}")
        if coupling == "independent" and stage.get("parallelizable") is not True:
            failures.append(f"decomposition stage {stage_id} coupling=independent requires parallelizable=true")
        if coupling == "linear" and stage.get("parallelizable") is not False:
            failures.append(f"decomposition stage {stage_id} coupling=linear requires parallelizable=false")
        if not isinstance(stage.get("parallelizable"), bool):
            failures.append(f"decomposition stage {stage_id} parallelizable must be a boolean")

    result_nodes = [node_id for node_id, node in node_by_id.items() if node.get("phase") == "result"]
    missing = sorted(set(result_nodes) - set(stage_by_node.keys()))
    if missing:
        failures.append("decomposition must cover every result node: " + ", ".join(missing))
    extra = sorted(set(stage_by_node.keys()) - set(result_nodes))
    if extra:
        failures.append("decomposition includes non-result nodes: " + ", ".join(extra))
    if set(result_nodes) != set(stage_by_node.keys()):
        return failures

    node_wave_by_id = _summary_dependency_wave(node_by_id)
    waves = {}
    for node_id in result_nodes:
        waves.setdefault(node_wave_by_id.get(node_id), []).append(node_id)
    for wave, members in waves.items():
        if len(members) < 2:
            continue
        stage_members = [stage_by_node.get(member) for member in members]
        if any(stage_member.get("coupling") != "independent" or stage_member.get("parallelizable") is not True for stage_member in stage_members if isinstance(stage_member, dict)):
            failures.append(f"decomposition same-wave entries in wave {wave} must use coupling=independent and parallelizable=true")
        objective_scopes = {member.get("objective_scope") for member in stage_members if member is not None}
        if len(objective_scopes) != 1:
            failures.append(f"decomposition same-wave independent entries in wave {wave} require shared objective_scope")
        if len({member.get("deterministic_merge_node") for member in stage_members}) != 1:
            failures.append(f"decomposition same-wave independent entries in wave {wave} must share deterministic_merge_node")
            deterministic_merge_node = None
        else:
            deterministic_merge_node = stage_members[0].get("deterministic_merge_node")

        if not isinstance(deterministic_merge_node, str) or not deterministic_merge_node:
            failures.append(f"decomposition same-wave independent entries in wave {wave} require a deterministic_merge_node")
        elif deterministic_merge_node not in node_by_id:
            failures.append(f"decomposition deterministic_merge_node does not exist: {deterministic_merge_node}")
        elif deterministic_merge_node in members:
            failures.append(f"decomposition deterministic_merge_node {deterministic_merge_node} must be outside wave {wave}")
        else:
            closure = dependency_closure(deterministic_merge_node, node_by_id)
            if not set(members).issubset(closure):
                failures.append(f"decomposition requires deterministic_merge_node {deterministic_merge_node} to depend on every sibling in wave {wave}")

        for i, stage_member in enumerate(stage_members):
            for next_stage in stage_members[i + 1 :]:
                if not isinstance(stage_member, dict) or not isinstance(next_stage, dict):
                    continue
                if set(stage_member.get("inputs", [])).intersection(next_stage.get("inputs", [])):
                    failures.append(f"decomposition same-wave independent entries in wave {wave} must have disjoint inputs")
                if set(stage_member.get("mutable_state", [])).intersection(next_stage.get("mutable_state", [])):
                    failures.append(f"decomposition same-wave independent entries in wave {wave} must have disjoint mutable_state")
    return failures


def phase_verdict(path, pass_marker, fail_marker):
    if not path:
        return "unknown"
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    if pass_marker in text and fail_marker not in text:
        return "pass"
    if fail_marker in text and pass_marker not in text:
        return "fail"
    return "unknown"


def validate_plan(plan, entry_model, entry_effort, cwd, skills_root=None, *, enforce_current_recommendation=False, history_path=None):
    """Validate execution safety and dependency boundaries, not a prescribed workflow."""
    failures = []
    cwd = Path(cwd).resolve()
    skills_root = resolve_skills_root(skills_root)
    entry = plan.get("entry") or {}
    if entry != {"model": entry_model, "effort": entry_effort}:
        failures.append("plan entry pair must match the user's selected model and effort")
    try:
        selected_model_policy.selected_pair(entry_model, entry_effort)
    except ValueError as error:
        failures.append(str(error))
    if plan.get("schema_version") != DISPATCH_SCHEMA_VERSION:
        failures.append(f"schema_version must be {DISPATCH_SCHEMA_VERSION}")
    if plan.get("complexity") not in {"easy", "complex"}:
        failures.append("complexity must be easy or complex")
    if plan.get("topology") not in {"sequential", "parallel", "mixed"}:
        failures.append("topology must be sequential, parallel, or mixed")
    timeout = plan.get("first_result_timeout_seconds", 180 if plan.get("complexity") == "easy" else 600)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 900:
        failures.append("first_result_timeout_seconds must be 1 to 900")
    else:
        plan["first_result_timeout_seconds"] = timeout
    cache_value = plan.get("cache_dir")
    cache = (cwd / cache_value).resolve() if isinstance(cache_value, str) and cache_value else None
    if cache is None or not path_is_within(cache, cwd):
        failures.append("cache_dir must resolve inside the active project")
    elif cache.relative_to(cwd).parts[:1] != ("Cache",):
        failures.append("cache_dir must be inside project Cache")
    elif len(cache.relative_to(cwd).parts) < 2 or not cache.relative_to(cwd).parts[1].startswith("tmp-"):
        failures.append("task route scratch must use Cache/tmp-*")
    if plan.get("complexity_score") is not None:
        try:
            plan["complexity_band"] = complexity_band(plan["complexity_score"])
        except ValueError as error:
            failures.append(str(error))
    nodes = plan.get("nodes")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 32:
        return failures + ["nodes must contain 1 to 32 bounded tasks"]
    node_by_id = {}
    for node in nodes:
        if not isinstance(node, dict):
            failures.append("every node must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not NODE_ID_PATTERN.fullmatch(node_id):
            failures.append("node ids must be lowercase kebab-case")
            continue
        if node_id in node_by_id:
            failures.append(f"duplicate node id: {node_id}")
        node_by_id[node_id] = node
        if node.get("phase") not in ALLOWED_PHASES:
            failures.append(f"{node_id} invalid phase")
        try:
            selected_model_policy.bind_node(node, entry_model, entry_effort)
        except ValueError as error:
            failures.append(f"{node_id} {error}")
        if node.get("execution_kind") != DETERMINISTIC_SOURCE_READ:
            try:
                selected_model_policy.selected_pair(node.get("model"), node.get("effort"))
            except ValueError as error:
                failures.append(f"{node_id} {error}")
            if not selected_model_policy.uses_selected_model(node) and (node.get("model") not in ACTIVE_MODEL_EFFORTS or node.get("effort") not in ACTIVE_MODEL_EFFORTS.get(node.get("model"), set())) and not _priority_result_node(node):
                failures.append(f"{node_id} independent task pair is unavailable in the local catalog")
        else:
            sources = node.get("source_allowlist", [])
            if len(sources) != 1 or node.get("dependencies") or node.get("phase") != "result":
                failures.append(f"{node_id} deterministic capture needs one source and no dependencies")
        if node.get("sandbox", "read-only") not in ALLOWED_SANDBOXES:
            failures.append(f"{node_id} unsafe sandbox")
        for skill in selected_model_policy.governing_skills(node):
            if resolve_node_skill_path(skill, skills_root) is None:
                failures.append(f"{node_id} unavailable governing skill: {skill}")
        if node.get("skill") and resolve_node_skill_path(node["skill"], skills_root) is None:
            failures.append(f"{node_id} unavailable skill: {node['skill']}")
        if not isinstance(node.get("prompt"), str) or not node["prompt"].strip():
            failures.append(f"{node_id} requires a bounded task goal")
        if not isinstance(node.get("dependencies", []), list):
            failures.append(f"{node_id} dependencies must be a list")
        score = node.get("complexity_score")
        if score is None:
            score = analyze_prompt_routing(node.get("prompt") or "")["complexity_score"]
            node["complexity_score"] = score
            node["score_source"] = "prompt_analysis"
        else:
            node.setdefault("score_source", "planner_assignment")
        if score is not None:
            try:
                node["complexity_band"] = complexity_band(score)
            except ValueError as error:
                failures.append(f"{node_id} {error}")
        for key in ("source_allowlist", "read_allowlist", "write_allowlist"):
            paths = node.get(key, [])
            if not isinstance(paths, list) or any(not isinstance(path, str) or not path or not path_is_within((cwd / path).resolve(), cwd) for path in paths):
                failures.append(f"{node_id} {key} must stay inside the project")
        if node.get("phase") == "ending":
            failures.extend(ending_checklist_failures(node))
            if node.get("skill") != ENDING_SKILL:
                failures.append(f"{node_id} Ending must use {ENDING_SKILL}")
    if plan.get("complexity_score") is None:
        plan["complexity_score"] = max((node.get("complexity_score", 0) for node in node_by_id.values() if isinstance(node.get("complexity_score"), int)), default=0)
        plan["complexity_band"] = complexity_band(plan["complexity_score"])
        plan["score_source"] = "maximum_node_score"
    else:
        plan.setdefault("score_source", "planner_assignment")
    # Malformed container types cannot safely enter graph traversal or overlap checks.
    if any(not isinstance(node.get("dependencies", []), list) or any(not isinstance(dep, str) for dep in node.get("dependencies", [])) or any(not isinstance(node.get(key, []), list) or any(not isinstance(path, str) for path in node.get(key, [])) for key in ("source_allowlist", "read_allowlist", "write_allowlist")) for node in node_by_id.values()):
        return failures + ["dependencies and path allowlists must contain strings"]
    for node_id, node in node_by_id.items():
        deps = node.get("dependencies", [])
        if not isinstance(deps, list):
            continue
        if any(dep not in node_by_id or dep == node_id for dep in deps):
            failures.append(f"{node_id} has missing or self dependencies")
    remaining = set(node_by_id)
    settled = set()
    while remaining:
        ready = {node_id for node_id in remaining if isinstance(node_by_id[node_id].get("dependencies", []), list) and set(node_by_id[node_id].get("dependencies", [])).issubset(settled)}
        if not ready:
            failures.append("dependency graph contains a cycle or missing dependency")
            break
        remaining -= ready
        settled |= ready
    main = plan.get("main_result_node")
    if main not in node_by_id or node_by_id[main].get("phase") != "result":
        failures.append("main_result_node must name a result task")
    elif any(node_id not in dependency_closure(main, node_by_id) for node_id, node in node_by_id.items() if node.get("phase") == "result" and node_id != main):
        failures.append("final aggregate must depend on every result task")
    endings = [node for node in nodes if isinstance(node, dict) and node.get("phase") == "ending"]
    if len(endings) > 1:
        failures.append("use at most one memory closeout")
    for node in endings:
        if node.get("dependencies") != [main]:
            failures.append("memory closeout must depend on final aggregate")
    if plan.get("topology") != "sequential":
        result_nodes = [node for node in nodes if isinstance(node, dict) and node.get("id") in node_by_id and node.get("phase") == "result"]
        for index, left in enumerate(result_nodes):
            for right in result_nodes[index + 1:]:
                if left["id"] in dependency_closure(right["id"], node_by_id) or right["id"] in dependency_closure(left["id"], node_by_id):
                    continue
                for writer, reader in ((left, right), (right, left)):
                    writes = writer.get("write_allowlist", [])
                    reads = reader.get("read_allowlist", []) + reader.get("source_allowlist", []) + reader.get("write_allowlist", [])
                    if writer.get("sandbox") == "workspace-write" and not writes:
                        failures.append(f"{writer['id']} concurrent write task requires explicit write_allowlist")
                    if any(path_is_within((cwd / a).resolve(), (cwd / b).resolve()) or path_is_within((cwd / b).resolve(), (cwd / a).resolve()) for a in writes for b in reads):
                        failures.append(f"{writer['id']} and {reader['id']} share an unordered write surface")
    return list(dict.fromkeys(failures))


def dependency_context(node, completed):
    sections = []
    for dependency in node.get("dependencies", []):
        result_path = completed.get(dependency, {}).get("result_path")
        if result_path and Path(result_path).exists():
            text = Path(result_path).read_text(encoding="utf-8", errors="replace")[:12000]
            sections.append(f"Dependency {dependency} result:\n{text}")
    return "\n\n".join(sections)


def worker_identity(receipt):
    thread_id = receipt.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        return None
    return receipt_module.sha256_text(thread_id)


def _normalize_route_attempt(attempt_receipt, fallback_pair, status, phase_failure_class):
    candidate_attempt = None
    attempts = attempt_receipt.get("route_attempts")
    if isinstance(attempts, list) and attempts:
        first = attempts[0]
        if isinstance(first, dict):
            candidate_attempt = first

    requested_pair = candidate_attempt.get("requested_pair") if isinstance(candidate_attempt, dict) else None
    resolved_pair = candidate_attempt.get("resolved_pair") if isinstance(candidate_attempt, dict) else None
    effective_pair = candidate_attempt.get("effective_pair") if isinstance(candidate_attempt, dict) else None
    executed_pair = candidate_attempt.get("executed_pair") if isinstance(candidate_attempt, dict) else None
    tokens = candidate_attempt.get("tokens") if isinstance(candidate_attempt, dict) and isinstance(candidate_attempt.get("tokens"), dict) else attempt_receipt.get("tokens") if isinstance(attempt_receipt.get("tokens"), dict) else {}
    process_elapsed_ms = candidate_attempt.get("process_elapsed_ms") if isinstance(candidate_attempt, dict) else attempt_receipt.get("process_elapsed_ms")
    pre_execution_failure = candidate_attempt.get("pre_execution_failure") if isinstance(candidate_attempt, dict) and "pre_execution_failure" in candidate_attempt else attempt_receipt.get("pre_execution_failure")
    thread_id = candidate_attempt.get("thread_id") if isinstance(candidate_attempt, dict) and candidate_attempt.get("thread_id") is not None else attempt_receipt.get("thread_id")

    if status != "pass" and phase_failure_class == "execution" and not resolved_pair and not effective_pair:
        executed_pair = fallback_pair

    return {
        "requested_pair": requested_pair or fallback_pair,
        "resolved_pair": resolved_pair,
        "effective_pair": effective_pair,
        "executed_pair": executed_pair or fallback_pair,
        "status": status,
        "failure_class": phase_failure_class if status != "pass" else None,
        "model_match": bool(candidate_attempt.get("model_match") is True) if isinstance(candidate_attempt, dict) else False,
        "effort_match": bool(candidate_attempt.get("effort_match") is True) if isinstance(candidate_attempt, dict) else False,
        "pair_match": bool(candidate_attempt.get("pair_match") is True) if isinstance(candidate_attempt, dict) else False,
        "process_elapsed_ms": process_elapsed_ms,
        "model_turn_duration_ms": candidate_attempt.get("model_turn_duration_ms") if isinstance(candidate_attempt, dict) else None,
        "time_to_first_token_ms": candidate_attempt.get("time_to_first_token_ms") if isinstance(candidate_attempt, dict) else None,
        "tokens": dict(tokens),
        "thread_id": thread_id,
        "pre_execution_failure": bool(pre_execution_failure is True),
        "failure_stage": attempt_receipt.get("failure_stage"),
        "fallback_eligible": bool(attempt_receipt.get("fallback_eligible") is True),
    }


def _pair_text(record):
    if not isinstance(record, dict):
        return None
    requested = record.get("requested_pair")
    if isinstance(requested, str) and requested:
        return requested
    requested_model = record.get("requested_model")
    requested_effort = record.get("requested_effort")
    if requested_model and requested_effort:
        return f"{requested_model}|{requested_effort}"
    return None


def _pair_compare(left_pair, right_pair):
    if not left_pair or not right_pair:
        return 0
    try:
        left = receipt_module.parse_model_effort_pair(left_pair)
        right = receipt_module.parse_model_effort_pair(right_pair)
    except (TypeError, ValueError):
        return 0
    return routing_history_module.compare_pair(left, right)


def _route_change_for_node(record, requested_pair):
    if isinstance(record, dict) and record.get("failure_class") == "quality":
        return "upgrade", "Verified quality failure requires a one-notch upgrade."
    if isinstance(record, dict) and record.get("operational_fallback") is True:
        return "operational_fallback", "Runtime receipt recorded operational fallback."
    if not isinstance(record, dict) or record.get("evidence_level") != "runtime_receipt":
        return "freeze", "Known assignment has no runtime receipt."
    effective_pair = record.get("effective_pair")
    if not requested_pair or not effective_pair:
        return "freeze", "Runtime receipt lacks a complete pair."
    pair_comparison = _pair_compare(effective_pair, requested_pair)
    if pair_comparison > 0:
        return "upgrade", "Runtime receipt used a higher quality pair."
    if pair_comparison < 0:
        return "downgrade", "Runtime receipt used a lower quality pair."
    return "no_switch", "Runtime receipt confirmed the requested pair."


def build_model_switch_summary(plan, records, entry, *, ending_quality_failure_nodes=()):
    node_records = {
        record.get("id"): record
        for record in records
        if isinstance(record, dict) and record.get("id")
    }
    planned_nodes = [node for node in (plan.get("nodes") or []) if isinstance(node, dict) and node.get("id")]
    node_by_id = {node["id"]: node for node in planned_nodes}
    wave_by_node = _summary_dependency_wave(node_by_id)
    entry_pair = f"{entry.get('model')}|{entry.get('effort')}" if isinstance(entry, dict) and entry.get("model") and entry.get("effort") else None
    decomposition = plan.get("decomposition") if isinstance(plan.get("decomposition"), dict) else {}
    stage_inventory = (
        decomposition.get("stage_inventory")
        if isinstance(decomposition, dict) and isinstance(decomposition.get("stage_inventory"), list)
        else []
    )
    unsplit_continuity_groups = sum(
        1
        for stage in stage_inventory
        if isinstance(stage, dict) and stage.get("coupling") == "linear" and isinstance(stage.get("logical_stage_ids"), list) and len(stage["logical_stage_ids"]) > 1
    )

    result_waves = {}
    for node in planned_nodes:
        if node.get("phase") != "result":
            continue
        result_waves.setdefault(wave_by_node.get(node["id"]), []).append(node["id"])

    node_summary = []
    quality_failure_node_ids = set(ending_quality_failure_nodes)
    for node in planned_nodes:
        node_id = node["id"]
        record = node_records.get(node_id, {})
        planned_pair = f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None
        requested_pair = record.get("requested_pair") if isinstance(record.get("requested_pair"), str) and record.get("requested_pair") else planned_pair
        requested_model = record.get("requested_model") or node.get("model")
        requested_effort = record.get("requested_effort") or node.get("effort")
        if requested_pair is None and requested_model and requested_effort:
            requested_pair = f"{requested_model}|{requested_effort}"
        resolved_pair = record.get("resolved_pair") if isinstance(record.get("resolved_pair"), str) and record.get("resolved_pair") else None
        resolved_model = record.get("resolved_model")
        resolved_effort = record.get("resolved_effort")
        if resolved_pair is None and resolved_model and resolved_effort:
            resolved_pair = f"{resolved_model}|{resolved_effort}"
        if resolved_pair is None:
            resolved_pair = requested_pair
        effective_pair = record.get("effective_pair") if isinstance(record.get("effective_pair"), str) and record.get("effective_pair") else None
        effective_model = record.get("effective_model")
        effective_effort = record.get("effective_effort")
        if effective_pair is None and effective_model and effective_effort:
            effective_pair = f"{effective_model}|{effective_effort}"
        if effective_pair is None:
            effective_pair = resolved_pair
        if isinstance(requested_pair, str) and "|" in requested_pair:
            requested_model, requested_effort = requested_pair.split("|", 1)
        if isinstance(resolved_pair, str) and "|" in resolved_pair:
            resolved_model, resolved_effort = resolved_pair.split("|", 1)
        if isinstance(effective_pair, str) and "|" in effective_pair:
            effective_model, effective_effort = effective_pair.split("|", 1)
        evidence_source = record.get("model_evidence_source") if isinstance(record, dict) else None
        evidence_level = record.get("evidence_level") if isinstance(record, dict) else None
        status = record.get("status") or "pending"
        failure_class = record.get("failure_class") if isinstance(record, dict) else None
        if node_id in quality_failure_node_ids:
            status = "fail"
            failure_class = "quality"
        if evidence_level != "runtime_receipt":
            evidence_level = "UNVERIFIED (no runtime receipt)"
            if not evidence_source or evidence_source == "unavailable":
                evidence_source = "task_assignment" if requested_pair else "unavailable"
        elif not evidence_source:
            evidence_source = "runtime_receipt"
        summary_record = dict(record)
        summary_record.update({"effective_pair": effective_pair, "evidence_level": evidence_level, "failure_class": failure_class})
        route_change, reason = _route_change_for_node(summary_record, requested_pair)
        same_wave_node_ids = sorted(result_waves.get(wave_by_node.get(node_id), []))
        same_wave_siblings = [sibling for sibling in same_wave_node_ids if sibling != node_id]
        if not node.get("dependencies"):
            assignment = "entry_to_root_assignment"
        elif same_wave_siblings:
            assignment = "parallel_independent_assignment"
        else:
            assignment = "dependency_transition"
        stage_record = _stage_for_node_id(plan, node_id)
        summary_entry = {
            "node_id": node_id,
            "phase": node.get("phase"),
            "execution_kind": node.get("execution_kind", "model"),
            "purpose": node.get("purpose") or node.get("task_summary") or node_id,
            "goal": node.get("purpose") or node.get("task_summary") or node_id,
            "entry_pair": entry_pair,
            "assigned_pair": requested_pair,
            "actual_pair": effective_pair if evidence_level == "runtime_receipt" else None,
            "assignment_changed": bool(entry_pair and requested_pair and entry_pair != requested_pair),
            "skill": node.get("skill"),
            "stop_condition": node.get("stop_condition") or (stage_record.get("stop_condition") if isinstance(stage_record, dict) else None),
            "step_kind": (node.get("model_memory_scope") or {}).get("step_kind"),
            "capability_tags": list((node.get("model_memory_scope") or {}).get("capability_tags") or []),
            "score": node.get("complexity_score"),
            "band": node.get("complexity_band"),
            "requested_model": requested_model,
            "requested_effort": requested_effort,
            "requested_pair": requested_pair,
            "resolved_pair": resolved_pair,
            "resolved_model": resolved_model,
            "resolved_effort": resolved_effort,
            "effective_pair": effective_pair,
            "effective_model": effective_model,
            "effective_effort": effective_effort,
            "model_evidence_source": evidence_source,
            "evidence_level": evidence_level,
            "dependency_wave": wave_by_node.get(node_id),
            "relations": {
                "entry_pair": entry_pair,
                "dependencies": list(node.get("dependencies") or []),
                "same_wave_siblings": same_wave_siblings,
                "assignment": assignment,
            },
            "route_change": route_change,
            "reason": reason,
            "tokens": dict(record.get("tokens")) if isinstance(record.get("tokens"), dict) else {},
            "process_elapsed_ms": record.get("process_elapsed_ms"),
            "elapsed_ms": record.get("process_elapsed_ms"),
            "time": {"process_elapsed_ms": record.get("process_elapsed_ms"), "model_turn_duration_ms": record.get("model_turn_duration_ms"), "time_to_first_token_ms": record.get("time_to_first_token_ms")},
            "status": status,
            "failure_class": failure_class,
            "operational_fallback": bool(record.get("operational_fallback")) if isinstance(record, dict) else False,
        }
        if node_id in quality_failure_node_ids:
            summary_entry["quality_failure_attributed"] = True
        node_summary.append(summary_entry)

    stage_by_node = {stage.get("node_id"): stage for stage in stage_inventory if isinstance(stage, dict) and isinstance(stage.get("node_id"), str)}
    parallel_waves = sum(1 for members in result_waves.values() if len(members) > 1 and all(stage_by_node.get(node_id, {}).get("coupling") == "independent" and stage_by_node.get(node_id, {}).get("parallelizable") is True for node_id in members))
    spark_usage_nodes = sum(1 for summary_entry in node_summary if summary_entry["evidence_level"] == "runtime_receipt" and isinstance(summary_entry["effective_pair"], str) and "spark" in summary_entry["effective_pair"])
    quality_pair_nodes = sum(1 for summary_entry in node_summary if summary_entry["evidence_level"] == "runtime_receipt" and isinstance(summary_entry["effective_pair"], str) and "spark" not in summary_entry["effective_pair"])
    operational_fallback_nodes = sum(1 for summary_entry in node_summary if summary_entry["operational_fallback"])
    quality_failure_nodes = sum(1 for summary_entry in node_summary if summary_entry["failure_class"] == "quality")

    aggregate = {
        "spark_usage_nodes": spark_usage_nodes,
        "quality_pair_nodes": quality_pair_nodes,
        "operational_fallback_nodes": operational_fallback_nodes,
        "quality_failure_nodes": quality_failure_nodes,
        "parallel_waves": parallel_waves,
        "unsplit_continuity_groups": unsplit_continuity_groups,
    }
    return {"nodes": node_summary, "aggregate": aggregate}


def _aggregate_attempt_metrics(route_attempts):
    strategy_tokens = receipt_module.aggregate_token_maps([attempt.get("tokens", {}) for attempt in route_attempts])
    elapsed_values = [attempt.get("process_elapsed_ms") for attempt in route_attempts]
    strategy_elapsed_ms = sum(elapsed_values) if elapsed_values and all(isinstance(value, int) and value >= 0 for value in elapsed_values) else None
    return {"strategy_tokens": strategy_tokens, "strategy_elapsed_ms": strategy_elapsed_ms, "metrics_complete": strategy_tokens.get("total_tokens") is not None and strategy_elapsed_ms is not None}


def _ending_release_path(cache_dir, route_run_id):
    safe_route_run_id = re.sub(r"[^a-zA-Z0-9._-]", "-", route_run_id)
    return Path(cache_dir) / f"{safe_route_run_id}.ending-release.json"


def _release_record(route_run_id, completed, cache_dir):
    return {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "route_run_id": route_run_id,
        "released_at": datetime.now(timezone.utc).isoformat(),
        "released_by": "release-main-result",
        "main_result_node": completed.get("main_result_node"),
        "main_result_receipt_path": completed.get("main_result_receipt_path"),
        "main_result_path": completed.get("main_result_path"),
        "cache_dir": str(cache_dir),
    }


def _write_release_record(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _read_release_record(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _has_mismatched_release_record(cache_dir, route_run_id):
    for release_path in Path(cache_dir).glob("*.ending-release.json"):
        release_record = _read_release_record(release_path)
        if not isinstance(release_record, dict):
            continue
        if release_record.get("route_run_id") and release_record.get("route_run_id") != route_run_id:
            return True
    return False


def run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
    node = dict(node)
    selected_model_policy.bind_node(node, node.get("_entry_model") or node.get("model"), node.get("_entry_effort") or node.get("effort"))
    if node.get("phase") == "ending":
        node = dict(node)
        apply_ending_fast_route({"nodes": [node]})
        node["prompt"] = ending_worker_prompt(node)
    skills_root = resolve_skills_root(skills_root)
    node_id = node["id"]
    receipt_path = cache_dir / f"{node_id}-receipt.json"
    result_path = cache_dir / f"{node_id}-result.md"
    if node.get("execution_kind") == DETERMINISTIC_SOURCE_READ:
        return _run_deterministic_source_read(node, receipt_path, result_path, workdir)
    skills = selected_model_policy.governing_skills(node)
    skill_paths = []
    for skill in skills:
        path = resolve_node_skill_path(skill, skills_root)
        if path is None:
            raise ValueError(f"node governing skill cannot be resolved: {skill}")
        skill_paths.append(path.as_posix())
    dependency_text = dependency_context(node, completed)
    prompt = (f"Node: {node_id}. Phase: {node['phase']}. Execute this bounded goal. "
              + selected_model_policy.execution_guidance({**node, "project_root": str(workdir.resolve())})
              + (" Read governing skill sources: " + json.dumps(skill_paths) if skill_paths else "")
              + "\n\n" + node["prompt"])
    code_bundle = _node_code_rule_bundle(node) if selected_model_policy.uses_selected_model(node) and _is_code_implementation(node) else None
    if code_bundle is not None:
        resolved_references = [(skills_root / reference_path).as_posix() for reference_path in code_bundle["reference_paths"]]
        prompt += f"\n\nApply the relevant code preferences from: {json.dumps(resolved_references, ensure_ascii=False, separators=(',', ':'))}"
        _emit_code_gate_notice(code_bundle, node_id)
    if dependency_text:
        prompt += f"\n\nCompleted dependency handoff:\n{dependency_text}"
    if node["phase"] == "ending":
        prompt += "\n\nThis is a memory-only closeout. Include ENDING_TASK=PASS after scoped memory readback or an explicit missing-memory skip; otherwise ENDING_TASK=FAIL. Never verify or repair the project."

    route_marker = "ENDING_TASK_WORKER" if node["phase"] == "ending" else "LOCKED_ROUTE_NODE"
    fallback_pairs = receipt_module.normalize_fallback_pairs(node.get("allow_fallback", []))
    selected_pair = f"{node['model']}|{node['effort']}"
    adaptive_recommendation = None
    priority_node = _priority_result_node(node, node.get("_decomposition_stage"))
    fixed_scored_node = node.get("phase") == "result" and node.get("selection_basis") == "score_role" and f"{node.get('model')}|{node.get('effort')}" == score_role_pair(node.get("complexity_score"))
    if not node.get("model_locked") and node["phase"] == "result" and isinstance(node.get("routing_recommendation"), dict) and node.get("_project_root") and receipt_module.entry_context_active():
        try:
            adaptive_recommendation = validate_dispatcher_adaptive_result(node)
        except receipt_module.ReceiptAuthorizationError:
            adaptive_recommendation = None
    priority_attempt_pair = adaptive_recommendation.get("attempt_pair") if adaptive_recommendation else selected_pair
    planned_pairs = []
    for candidate in [priority_attempt_pair, selected_pair, *fallback_pairs]:
        if candidate and candidate not in planned_pairs:
            planned_pairs.append(candidate)
    route_attempts = []
    receipt = None
    status = "fail"
    for attempt_index, pair_text in enumerate(planned_pairs, start=1):
        attempt_model, attempt_effort = receipt_module.parse_model_effort_pair(pair_text)
        attempt_receipt_path = cache_dir / f"{node_id}-attempt-{attempt_index}-receipt.json"
        attempt_timeout = node.get("timeout", 180)
        deadline_monotonic = node.get("_deadline_monotonic")
        if isinstance(deadline_monotonic, (int, float)):
            remaining_seconds = deadline_monotonic - time.monotonic()
            if attempt_index > 1:
                reserve_seconds = max(0, int(node.get("_fallback_reserve_seconds", 0)))
                required_seconds = max(1, int(node.get("timeout", 180))) + reserve_seconds
                if remaining_seconds < required_seconds:
                    break
            if remaining_seconds <= 0:
                receipt = receipt_module.failed_run_receipt(SimpleNamespace(model=attempt_model, effort=attempt_effort, workload_id=f"task-route-{node_id}", entry_task=False, allow_fallback=[]), "timeout")
                receipt["process_elapsed_ms"] = 0
                receipt["route_attempts"][0]["process_elapsed_ms"] = 0
                route_attempts.append(_normalize_route_attempt(receipt, pair_text, "fail", "timeout"))
                status = "fail"
                break
            attempt_timeout = min(attempt_timeout, max(1, int(remaining_seconds)))
        args = SimpleNamespace(
            model=attempt_model,
            effort=attempt_effort,
            codex_bin=codex_bin,
            sandbox=node.get("sandbox", "read-only"),
            ignore_user_config=node.get("sandbox", "read-only") == "read-only" and not node.get("load_user_config", False),
            entry_task=False,
            node_role=receipt_node_role(node),
            route_marker=route_marker,
            stream_result_ready=receipt_node_role(node) == "result-producer",
            result_ready_callback=node.get("_result_ready_callback"),
            result_output=result_path,
            timeout=attempt_timeout,
            workdir=workdir.resolve(),
            state_db=state_db,
            workload_id=f"task-route-{node_id}",
            allow_fallback=[],
            code_rule_bundle=code_bundle,
        )
        try:
            if args.node_role == "result-producer":
                if receipt_module.entry_context_active():
                    if node.get("model_locked") or priority_node or fixed_scored_node:
                        authorized_pairs = {selected_pair, *fallback_pairs}
                    else:
                        current_recommendation = adaptive_recommendation or validate_dispatcher_adaptive_result(node)
                        authorized_pairs = {current_recommendation.get("attempt_pair"), current_recommendation.get("selected_pair"), *fallback_pairs}
                    if pair_text not in authorized_pairs:
                        raise receipt_module.ReceiptAuthorizationError("dispatcher_adaptive_recommendation_invalid")
                    with receipt_module.dispatcher_adaptive_result_authorization():
                        attempt_receipt = receipt_module.run_receipt(args, prompt)
                else:
                    attempt_receipt = receipt_module.run_receipt(args, prompt)
            else:
                with receipt_module.dispatcher_node_authorization(args.node_role):
                    attempt_receipt = receipt_module.run_receipt(args, prompt)
        except receipt_module.ReceiptAuthorizationError as error:
            attempt_receipt = receipt_module.rejected_run_receipt(args, error)
            failure_class = "authorization"
            status = "fail"
        except subprocess.TimeoutExpired:
            attempt_receipt = receipt_module.failed_run_receipt(args, "timeout")
            attempt_receipt["pre_execution_failure"] = False
            failure_class = "timeout"
            status = "fail"
        except (OSError, ValueError):
            attempt_receipt = {
                "schema_version": 1,
                "node_type": "locked-route-node",
                "workload_id": f"task-route-{node_id}",
                "requested_model": attempt_model,
                "requested_effort": attempt_effort,
                "requested_pair": pair_text,
                "resolved_model": None,
                "resolved_effort": None,
                "effective_model": None,
                "effective_pair": None,
                "allowed_fallback_pairs": fallback_pairs,
                "model_match": False,
                "effort_match": False,
                "pair_match": False,
                "turn_completed": False,
                "status": "fail",
                "process_elapsed_ms": 0,
                "tokens": {"input_tokens": 0, "cached_input_tokens": 0, "uncached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 0},
                "pre_execution_failure": True,
                "route_attempts": [{
                    "requested_pair": pair_text,
                    "resolved_pair": None,
                    "effective_pair": None,
                    "executed_pair": pair_text,
                    "status": "fail",
                    "failure_class": "execution",
                    "model_match": False,
                    "effort_match": False,
                    "pair_match": False,
                    "process_elapsed_ms": 0,
                    "model_turn_duration_ms": None,
                    "time_to_first_token_ms": None,
                    "tokens": {"input_tokens": 0, "cached_input_tokens": 0, "uncached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 0},
                    "thread_id": None,
                    "pre_execution_failure": True,
                }],
            }
            failure_class = "execution"
            status = "fail"
        else:
            failure_class = attempt_receipt.get("failure_class")
            status = attempt_receipt.get("status") or "fail"

        if status == "pass" and node["phase"] == "ending":
            status = phase_verdict(result_path, "ENDING_TASK=PASS", "ENDING_TASK=FAIL")
            if status != "pass":
                status = "fail"
                failure_class = "protocol"
                attempt_receipt["status"] = "fail"
        if status == "pass" and node["phase"] == "result" and (not result_path.is_file() or result_path.stat().st_size == 0):
            status = "fail"
            failure_class = "protocol"
            attempt_receipt["status"] = "fail"

        if status == "pass":
            failure_class = None
        if "complexity_score" in node:
            attempt_receipt["complexity_score"] = node["complexity_score"]
            attempt_receipt["complexity_band"] = node.get("complexity_band")
            attempt_receipt["selection_basis"] = node.get("selection_basis")
        attempt_receipt["result_published"] = bool(result_path.is_file() and result_path.stat().st_size > 0)
        attempt_receipt = receipt_module.annotate_operational_fallback(attempt_receipt)
        if node["phase"] == "ending":
            attempt_receipt["fallback_eligible"] = ending_availability_fallback(attempt_receipt)
            if attempt_receipt.get("route_attempts"):
                attempt_receipt["route_attempts"][-1]["fallback_eligible"] = attempt_receipt["fallback_eligible"]
        attempt_receipt_path.write_text(json.dumps(attempt_receipt, indent=2) + "\n", encoding="utf-8")
        route_attempts.append(_normalize_route_attempt(attempt_receipt, pair_text, status, failure_class))
        receipt = attempt_receipt
        if status == "pass":
            break
        result_fallback = node["phase"] == "result" and receipt_module.immediate_operational_fallback(attempt_receipt)
        ending_fallback = node["phase"] == "ending" and node.get("fallback_policy") == "availability_only" and ending_availability_fallback(attempt_receipt)
        if not result_fallback and not ending_fallback:
            break

    attempt_metrics = _aggregate_attempt_metrics(route_attempts)
    receipt["route_attempts"] = route_attempts
    receipt["priority_attempt_pair"] = priority_attempt_pair
    receipt["selected_pair"] = selected_pair
    receipt["model_locked"] = bool(node.get("model_locked"))
    receipt["selection_provenance"] = node.get("selection_basis")
    receipt["governing_skills"] = selected_model_policy.governing_skills(node)
    receipt["active_fallback_pair"] = fallback_pairs[0] if node["phase"] == "ending" and fallback_pairs else selected_pair if priority_attempt_pair != selected_pair else None
    receipt["fallback_policy"] = node.get("fallback_policy")
    receipt["allowed_fallback_pairs"] = planned_pairs[1:]
    receipt["operational_failure_pairs"] = [
        attempted_pair
        for attempted_pair, attempted_receipt in zip(planned_pairs, route_attempts)
        if attempted_receipt.get("fallback_eligible") is True
    ]
    receipt["operational_fallback"] = len(route_attempts) > 1 and any(attempt.get("fallback_eligible") is True for attempt in route_attempts[:-1])
    receipt["last_attempt_tokens"] = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
    receipt["last_attempt_process_elapsed_ms"] = receipt.get("process_elapsed_ms")
    receipt["strategy_tokens"] = attempt_metrics["strategy_tokens"]
    receipt["strategy_elapsed_ms"] = attempt_metrics["strategy_elapsed_ms"]
    receipt["attempt_metrics_complete"] = attempt_metrics["metrics_complete"]
    receipt["tokens"] = attempt_metrics["strategy_tokens"]
    receipt["process_elapsed_ms"] = attempt_metrics["strategy_elapsed_ms"]
    receipt["entry_model"] = node.get("_entry_model")
    receipt["entry_effort"] = node.get("_entry_effort")
    receipt["entry_pair"] = f"{node.get('_entry_model')}|{node.get('_entry_effort')}" if node.get("_entry_model") and node.get("_entry_effort") else None
    receipt["entry_source"] = "plan_entry" if receipt["entry_pair"] else "unavailable"
    receipt["selection_reason"] = adaptive_recommendation.get("attempt_reason") if adaptive_recommendation else node.get("selection_basis")
    receipt["recommendation_state"] = adaptive_recommendation.get("attempt_calibration_state") if adaptive_recommendation else node.get("selection_basis")
    receipt["trial"] = adaptive_recommendation.get("attempt_trial") if adaptive_recommendation else bool(node.get("trial"))
    receipt["switch_direction"] = adaptive_recommendation.get("switch_direction") if adaptive_recommendation else (node.get("routing_recommendation") or {}).get("switch_direction", "no_switch")
    if status == "pass" and node["phase"] == "result" and result_path.is_file() and result_path.stat().st_size > 0:
        result_text = result_path.read_text(encoding="utf-8", errors="replace")
        try:
            normalized_result = model_identity_disclosure.normalize_result_disclosure(
                result_text,
                node.get("complexity_score", 35),
                runtime_receipt=receipt,
            )
        except ValueError:
            pass
        else:
            result_path.write_text(normalized_result.rstrip("\n") + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    result_published = bool(node["phase"] == "result" and result_path.is_file() and result_path.stat().st_size > 0)
    result_ready_monotonic_ns = receipt.get("result_ready_monotonic_ns")
    if result_published and not isinstance(result_ready_monotonic_ns, int):
        result_ready_monotonic_ns = time.monotonic_ns()
    requested_pair = f"{node['model']}|{node['effort']}"
    resolved_pair = receipt.get("resolved_pair") if isinstance(receipt, dict) else None
    effective_pair = receipt.get("effective_pair") if isinstance(receipt, dict) else None
    receipt_resolved_model = receipt.get("resolved_model") if isinstance(receipt, dict) else None
    receipt_resolved_effort = receipt.get("resolved_effort") if isinstance(receipt, dict) else None
    receipt_effective_model = receipt.get("effective_model") if isinstance(receipt, dict) else None
    if not resolved_pair:
        if receipt_resolved_model and receipt_resolved_effort:
            resolved_pair = f"{receipt_resolved_model}|{receipt_resolved_effort}"
    if not resolved_pair:
        resolved_pair = receipt.get("last_attempt_pair") if isinstance(receipt, dict) else None
    if not effective_pair and receipt_effective_model and receipt_resolved_effort:
        effective_pair = f"{receipt_effective_model}|{receipt_resolved_effort}"
    if not resolved_pair:
        resolved_pair = requested_pair
    if not effective_pair:
        effective_pair = resolved_pair
    resolved_model = None
    resolved_effort = None
    effective_model = None
    effective_effort = None
    if isinstance(resolved_pair, str) and "|" in resolved_pair:
        resolved_model, resolved_effort = resolved_pair.split("|", 1)
    if isinstance(effective_pair, str) and "|" in effective_pair:
        effective_model, effective_effort = effective_pair.split("|", 1)
    runtime_identity = any(receipt.get(field) for field in ("resolved_model", "resolved_pair", "effective_model", "effective_pair"))
    model_evidence_source = "runtime_receipt" if runtime_identity else "task_assignment"
    evidence_level = "runtime_receipt" if runtime_identity else "UNVERIFIED (no runtime receipt)"
    if receipt.get("model_memory_pair") is not None or receipt.get("routing_recommendation") is not None:
        model_evidence_source = "obsidian"
    if node.get("phase") == "ending":
        model_evidence_source = "entry" if runtime_identity else "task_assignment"
    operational_fallback = bool(receipt.get("operational_fallback"))

    return {
        "id": node_id,
        "phase": node["phase"],
        "skill": node["skill"],
        "requested_model": node["model"],
        "requested_effort": node["effort"],
        "requested_pair": requested_pair,
        "resolved_model": resolved_model,
        "resolved_effort": resolved_effort,
        "resolved_pair": resolved_pair,
        "effective_model": effective_model,
        "effective_effort": effective_effort,
        "effective_pair": effective_pair,
        "model_evidence_source": model_evidence_source,
        "evidence_level": evidence_level,
        "failure_class": failure_class,
        "operational_fallback": operational_fallback,
        "model": effective_model or node["model"],
        "effort": effective_effort or node["effort"],
        "workload_id": f"task-route-{node_id}",
        "status": status,
        "receipt_path": str(receipt_path),
        "result_path": str(result_path) if result_path.exists() else None,
        "result_published": result_published,
        "result_ready_monotonic_ns": result_ready_monotonic_ns,
        "receipt_failure_after_result": bool(result_published and status != "pass"),
        "worker_identity": worker_identity(receipt),
        "tokens": receipt.get("tokens"),
        "process_elapsed_ms": receipt.get("process_elapsed_ms"),
        "model_turn_duration_ms": receipt.get("model_turn_duration_ms"),
        "time_to_first_token_ms": receipt.get("time_to_first_token_ms"),
        "complexity_score": node.get("complexity_score"),
        "complexity_band": node.get("complexity_band"),
        "selection_basis": node.get("selection_basis"),
        "dependencies": list(node.get("dependencies", [])),
    }


def _run_deterministic_source_read(node, receipt_path, result_path, workdir):
    started_ns = time.monotonic_ns()
    source = node["source_allowlist"][0]
    source_path = (Path(workdir).resolve() / source).resolve()
    status = "pass"
    failure_class = None
    failure_detail = None
    output_sha256 = None
    result_ready_monotonic_ns = None
    try:
        source_bytes = source_path.read_bytes()
        source_text = source_bytes.decode("utf-8")
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        output = f"SOURCE: {source}\nSHA256: {source_sha256}\nCONTENT-BEGIN\n{source_text}\nCONTENT-END\n"
        result_path.write_text(output, encoding="utf-8")
        output_sha256 = hashlib.sha256(output.rstrip("\n").encode("utf-8")).hexdigest()
        result_ready_monotonic_ns = time.monotonic_ns()
    except (OSError, UnicodeDecodeError) as error:
        status = "fail"
        failure_class = "execution"
        failure_detail = type(error).__name__
        source_sha256 = None
    elapsed_ms = round((time.monotonic_ns() - started_ns) / 1_000_000)
    tokens = {"input_tokens": 0, "cached_input_tokens": 0, "uncached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 0}
    receipt = {
        "schema_version": 2,
        "node_type": DETERMINISTIC_SOURCE_READ,
        "node_role": "context-provider",
        "workload_id": f"task-route-{node['id']}",
        "status": status,
        "turn_completed": status == "pass",
        "result_published": status == "pass",
        "result_ready_monotonic_ns": result_ready_monotonic_ns,
        "requested_model": None,
        "requested_effort": None,
        "requested_pair": None,
        "resolved_model": None,
        "resolved_effort": None,
        "resolved_pair": None,
        "effective_model": None,
        "effective_effort": None,
        "effective_pair": None,
        "model_match": True,
        "effort_match": True,
        "pair_match": True,
        "metrics_complete": True,
        "tokens": tokens,
        "strategy_tokens": tokens,
        "process_elapsed_ms": elapsed_ms,
        "model_turn_duration_ms": None,
        "time_to_first_token_ms": None,
        "failure_class": failure_class,
        "failure_detail": failure_detail,
        "pre_execution_failure": status != "pass",
        "route_attempts": [],
        "reroutes": [],
        "source_path": source,
        "source_sha256": source_sha256,
        "output_sha256": output_sha256,
        "deterministic": True,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    callback = node.get("_result_ready_callback")
    if status == "pass" and callable(callback):
        callback(result_path, result_ready_monotonic_ns)
    return {
        "id": node["id"],
        "phase": node["phase"],
        "skill": node["skill"],
        "execution_kind": DETERMINISTIC_SOURCE_READ,
        "requested_model": None,
        "requested_effort": None,
        "requested_pair": None,
        "resolved_model": None,
        "resolved_effort": None,
        "resolved_pair": None,
        "effective_model": None,
        "effective_effort": None,
        "effective_pair": None,
        "model_evidence_source": "deterministic_local_runtime",
        "evidence_level": "runtime_receipt",
        "failure_class": failure_class,
        "operational_fallback": False,
        "model": None,
        "effort": None,
        "workload_id": f"task-route-{node['id']}",
        "status": status,
        "receipt_path": str(receipt_path),
        "result_path": str(result_path) if result_path.exists() else None,
        "result_published": status == "pass",
        "result_ready_monotonic_ns": result_ready_monotonic_ns,
        "receipt_failure_after_result": False,
        "worker_identity": None,
        "tokens": tokens,
        "process_elapsed_ms": elapsed_ms,
        "model_turn_duration_ms": None,
        "time_to_first_token_ms": None,
        "complexity_score": node.get("complexity_score"),
        "complexity_band": node.get("complexity_band"),
        "selection_basis": "deterministic_local_runtime",
        "dependencies": [],
    }


def _route_run_id():
    return f"route-{uuid.uuid4().hex}"


def preflight_plan(plan, entry_model, entry_effort, cwd, skills_root=None, *, history_path=None):
    plan["execution_lifecycle"] = execution_lifecycle_for_plan(plan)
    failures = validate_plan(plan, entry_model, entry_effort, cwd, skills_root=skills_root, enforce_current_recommendation=plan.get("routing_mode") != DYNAMIC_ROUTING_MODE, history_path=history_path)
    return {"schema_version": DISPATCH_SCHEMA_VERSION, "stage": "pre-execution-validation", "status": "pass" if not failures else "fail", "failures": failures, "execution_lifecycle": plan["execution_lifecycle"]}


def _write_pre_result_repair_handoff(cache_dir, route_run_id, failures, completed_records, deadline_exhausted):
    """Compatibility no-op: the active task owns diagnosis and bounded retries."""
    return None


def _record_pre_result_operational_failures(plan, completed_records, project_root):
    node_by_id = {node["id"]: node for node in plan.get("nodes", []) if isinstance(node, dict) and isinstance(node.get("id"), str)}
    learning = []
    for record in completed_records:
        node = node_by_id.get(record.get("id"))
        failure_class = record.get("failure_class")
        if not node or node.get("phase") != "result" or record.get("status") == "pass" or record.get("result_published") is True or failure_class not in obsidian_model_memory.OPERATIONAL_FAILURES:
            continue
        receipt_path = record.get("receipt_path")
        if not isinstance(receipt_path, str) or not Path(receipt_path).is_file():
            continue
        memory_args = _model_memory_arguments(node, project_root)
        memory_project_root = memory_args.pop("project_root")
        memory_task_type = memory_args.pop("task_type")
        memory_module = memory_args.pop("module")
        reason = f"Dispatched node {record['id']} ended with {failure_class} before result publication."
        try:
            recorded = obsidian_model_memory.record_model_result(memory_project_root, memory_task_type, memory_module, receipt_path, "fail", failure_class, trial=bool(node.get("trial")), outcome_reason=reason, verification_count=0, **memory_args)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            learning.append({"node_id": record["id"], "status": "fail", "reason": f"dual_model_history_record_failed:{type(error).__name__}"})
        else:
            learning.append({"node_id": record["id"], "status": recorded.get("status"), "event_id": recorded.get("event_id"), "local": recorded.get("local"), "obsidian": recorded.get("obsidian")})
    return learning


def _run_record(result_path, verify_level, verify_status, main_result_receipt_path, route_run_id, main_node, project_root, execution_domain=None):
    if not main_result_receipt_path:
        return {"status": "skipped", "reason": "missing-main-result-receipt"}
    node = main_node
    condition = dict(node.get("routing_condition", {}))
    if execution_domain is not None:
        condition["execution_domain"] = execution_domain
    node = dict(node)
    node["routing_condition"] = condition
    verified_status = verify_status if verify_status in {"pass", "fail"} else "fail"
    failure_class = "none" if verified_status == "pass" else ("quality" if verify_status == "fail" else "execution")
    try:
        main_receipt = json.loads(Path(main_result_receipt_path).read_text(encoding="utf-8"))
        entry_model, entry_effort, _ = obsidian_model_memory._receipt_entry(main_receipt)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        entry_model, entry_effort = "", ""
    memory_args = _model_memory_arguments(node, project_root, entry_model, entry_effort)
    memory_project_root = memory_args.pop("project_root")
    memory_task_type = memory_args.pop("task_type")
    memory_module = memory_args.pop("module")
    try:
        recorder_result = obsidian_model_memory.record_model_result(
            memory_project_root,
            memory_task_type,
            memory_module,
            main_result_receipt_path,
            verified_status,
            failure_class,
            trial=bool(node.get("trial")),
            **memory_args,
        )
        recommendation = obsidian_model_memory.recommend_model(
            memory_project_root,
            memory_task_type,
            memory_module,
            **memory_args,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        return {"status": "fail", "reason": f"dual_model_history_record_failed:{type(error).__name__}"}
    return {"status": recorder_result.get("status"), "recorder_result": recorder_result, "recommendation": recommendation}


def memory_closeout_launch_packet(summary):
    """Request an app task; this CLI cannot create or acknowledge one."""
    pair = summary.get("entry_pair")
    if not pair:
        entry = summary.get("entry") or {}
        pair = f"{entry.get('model')}|{entry.get('effort')}"
    ready = summary.get("final_aggregate_receipt") is True and summary.get("ending_launch_ready") is True
    return {"schema_version": 3, "stage": "memory-closeout-required", "user_visible": True,
            "status": "launch-required" if ready else "waiting-for-aggregate-release",
            "parent_action": "create_visible_projectless_ending_task" if ready else "verify_and_release_final_aggregate",
            "message": f"Ending memory update: create one projectless task using {pair} after active-task verification and final aggregate release. Leave it as an ordinary unpinned task. Report its link and read back its completion by task ID, even if absent from recent tasks. Do not pin, move, reorder, or open it automatically; this launch packet is not a created task.",
            "target": {"type": "projectless"}, "task_count": 1, "task_created": False,
            "ending_purpose": "memory_only", "selected_model_required": True, "selected_pair": pair,
            "verification_owner": "active_task", "final_aggregate_receipt": ready,
            "ending_launch_ready": ready, "receipt_path": summary.get("receipt_path") or summary.get("downstream_receipt_path"),
            "result_path": summary.get("result_path") or summary.get("main_result_path"),
            "ending_handoff_path": summary.get("ending_handoff_path"),
            "aggregate_result_release_path": summary.get("release_path") or summary.get("aggregate_result_release_path"),
            "repair_chain_allowed": False, "auto_archive": False}


def _plan_model_disclosure(plan, records, entry, timing):
    stages = build_model_switch_summary(plan, records, entry)
    main = next((record for record in records if record.get("id") == plan.get("main_result_node")), {})
    runtime = main if main.get("evidence_level") == "runtime_receipt" and main.get("effective_pair") else None
    return model_identity_disclosure.model_disclosure_event(
        plan["complexity_score"], runtime_receipt=runtime,
        entry_resolution={"status": "task_assignment", **entry},
        model_switch_summary=stages, timing=timing)


def _release_main_result(handoff):
    handoff_data = dict(handoff)
    route_run_id = handoff_data.get("route_run_id")
    if not isinstance(route_run_id, str) or not route_run_id:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": None, "failures": ["ending handoff is missing route_run_id"]}

    cache_dir = Path(handoff_data.get("cache_dir") or Path.cwd()).expanduser().resolve()
    plan = handoff_data.get("plan") if isinstance(handoff_data.get("plan"), dict) else {}
    completed = {
        record.get("id"): record
        for record in handoff_data.get("completed", [])
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    main_node_id = handoff_data.get("main_result_node") or plan.get("main_result_node")
    main_record = completed.get(main_node_id) if isinstance(main_node_id, str) else None
    if main_record is None:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": route_run_id, "failures": ["ending handoff is missing the main result record"]}
    if main_record.get("status") != "pass":
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": route_run_id, "failures": ["main result must complete before release"]}
    unfinished_result_nodes = [node["id"] for node in plan.get("nodes", []) if isinstance(node, dict) and node.get("phase") == "result" and completed.get(node.get("id"), {}).get("status") != "pass"]
    if unfinished_result_nodes:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": route_run_id, "failures": ["all result nodes must complete before release: " + ", ".join(unfinished_result_nodes)]}
    main_result_path = Path(main_record.get("result_path") or "")
    if not main_result_path.is_file() or main_result_path.stat().st_size == 0:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": route_run_id, "failures": ["main result output must exist and be non-empty before release"]}

    release_path = _ending_release_path(cache_dir, route_run_id)
    release_record = _release_record(
        route_run_id,
        {
            "main_result_node": main_node_id,
            "main_result_receipt_path": main_record.get("receipt_path"),
            "main_result_path": main_record.get("result_path"),
        },
        cache_dir,
    )
    _write_release_record(release_path, release_record)
    handoff_data["released"] = True
    handoff_data["release_path"] = str(release_path)
    handoff_path = Path(handoff_data.get("ending_handoff_path") or cache_dir / "ending-handoff.json")
    handoff_path.write_text(json.dumps(handoff_data, indent=2) + "\n", encoding="utf-8")
    required = plan.get("ending_required") is True or any(node.get("phase") == "ending" for node in plan.get("nodes", []))
    summary = {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "pass", "route_run_id": route_run_id,
               "release_path": str(release_path), "entry": handoff_data.get("entry"),
               "main_result_path": str(main_result_path), "downstream_receipt_path": main_record.get("receipt_path"),
               "ending_handoff_path": str(handoff_path), "final_aggregate_receipt": True,
               "all_result_nodes_settled": True, "ending_required": required, "ending_launch_ready": required}
    if required:
        summary["memory_closeout"] = memory_closeout_launch_packet(summary)
    return summary


def run_plan(
    plan,
    entry_model,
    entry_effort,
    cwd,
    state_db=None,
    codex_bin="codex",
    skills_root=None,
    history_path=None,
    result_ready_callback=None,
    preflight=None,
):
    first_result_started = time.monotonic()
    first_result_started_ns = time.monotonic_ns()
    preflight = preflight or preflight_plan(plan, entry_model, entry_effort, cwd, skills_root, history_path=history_path)
    plan.setdefault("execution_lifecycle", preflight.get("execution_lifecycle") or execution_lifecycle_for_plan(plan))
    first_result_timeout_seconds = plan.get("first_result_timeout_seconds", 180 if plan.get("complexity") == "easy" else 600)
    failures = list(preflight["failures"])
    cache_dir = Path(plan["cache_dir"]).expanduser().resolve() if not failures else cwd.resolve() / "work" / "cache" / "invalid-task-route"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "dispatch-manifest.json"

    route_run_id = _route_run_id()

    if failures:
        summary_entry = {"model": entry_model, "effort": entry_effort}
        manifest = {
            "schema_version": DISPATCH_SCHEMA_VERSION,
            "stage": "validation",
            "status": "fail",
            "failures": failures,
            "entry": {"model": entry_model, "effort": entry_effort},
            "nodes": [],
            "route_run_id": route_run_id,
            "first_result_timeout_seconds": first_result_timeout_seconds,
            "first_result_elapsed_ms": round((time.monotonic() - first_result_started) * 1000),
            "deadline_exhausted": False,
            "repair_budget_remaining": 0,
            "result_published": False,
            "notification_required": False,
            "reopen_required": False,
            "repair_handoff_path": None,
            "model_switch_summary": build_model_switch_summary(plan, [], summary_entry),
            "execution_lifecycle": plan["execution_lifecycle"],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    for node in plan["nodes"]:
        selected_model_policy.bind_node(node, entry_model, entry_effort)
    assignment_notice = _plan_model_disclosure(plan, [], {"model": entry_model, "effort": entry_effort}, "assignment")
    print(json.dumps(assignment_notice, ensure_ascii=False, separators=(",", ":")), flush=True)
    node_by_id = {node["id"]: node for node in plan["nodes"]}
    first_result_timeout_seconds = plan.get("first_result_timeout_seconds", first_result_timeout_seconds)
    runnable_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "result"}
    completed = {}
    ready_records = {}
    ready_metadata = {}
    published_ids = set()
    publication_lock = threading.Lock()
    result_events = queue.Queue()
    running = {}
    active_producers = set()
    launch_order = []
    launch_metadata = {}
    deadline_exhausted = False
    result_execution_failed = False
    main_result_node = plan["main_result_node"]
    maximum_active_producers = 1 if plan["topology"] == "sequential" else 3

    def result_ready_callback_for(node_id):
        expected_path = (cache_dir / f"{node_id}-result.md").resolve()

        def accept_result_ready(result_path, ready_monotonic_ns):
            try:
                actual_path = Path(result_path).resolve()
                valid_result = actual_path == expected_path and actual_path.is_file() and actual_path.stat().st_size > 0
            except OSError:
                valid_result = False
            if not valid_result:
                return
            if isinstance(ready_monotonic_ns, bool) or not isinstance(ready_monotonic_ns, int) or ready_monotonic_ns < 0:
                ready_monotonic_ns = time.monotonic_ns()
            with publication_lock:
                if node_id in published_ids:
                    return
                published_ids.add(node_id)
            provisional_record = {"id": node_id, "phase": "result", "skill": node_by_id[node_id]["skill"], "status": "result-ready", "result_path": str(actual_path), "result_published": True, "result_ready_monotonic_ns": ready_monotonic_ns}
            result_events.put(("result-ready", node_id, provisional_record))
            if node_id == main_result_node and callable(result_ready_callback):
                result_ready_callback(actual_path, ready_monotonic_ns)

        return accept_result_ready

    result_node_count = len(runnable_ids)
    with ThreadPoolExecutor(max_workers=max(1, result_node_count)) as executor:
        while runnable_ids or running:
            while not result_execution_failed and not deadline_exhausted and len(active_producers) < maximum_active_producers:
                dependency_ready = sorted(node_id for node_id in runnable_ids if all(dependency in ready_records for dependency in node_by_id[node_id].get("dependencies", [])))
                if not dependency_ready:
                    break
                remaining_seconds = first_result_timeout_seconds - (time.monotonic() - first_result_started)
                if remaining_seconds <= 0:
                    failures.append("first-result deadline exhausted")
                    deadline_exhausted = True
                    break
                launch_ids = dependency_ready[: maximum_active_producers - len(active_producers)]
                ready_nodes = []
                for node_id in launch_ids:
                    ready_node = dict(node_by_id[node_id])
                    ready_node["timeout"] = min(ready_node.get("timeout", 180), max(1, int(remaining_seconds)))
                    ready_node["_deadline_monotonic"] = first_result_started + first_result_timeout_seconds
                    ready_node["_fallback_reserve_seconds"] = 30 if plan["complexity"] == "easy" else 90
                    ready_node["_project_root"] = str(Path(ready_node.get("routing_project_root") or cwd).expanduser().resolve())
                    ready_node["_entry_model"] = entry_model
                    ready_node["_entry_effort"] = entry_effort
                    ready_node["_result_ready_callback"] = result_ready_callback_for(node_id)
                    ready_node["_decomposition_stage"] = _stage_for_node_id(plan, node_id)
                    ready_nodes.append((node_id, ready_node))
                for node_id, ready_node in ready_nodes:
                    future = executor.submit(run_node, ready_node, cache_dir, dict(ready_records), state_db, cwd, codex_bin, skills_root)
                    future.add_done_callback(lambda settled_future, settled_node_id=node_id: result_events.put(("settled", settled_node_id, settled_future)))
                    running[node_id] = future
                    active_producers.add(node_id)
                    launch_order.append(node_id)
                    launch_metadata[node_id] = {"dependency_wave": dependency_wave(node_id, node_by_id), "launch_sequence": len(launch_order), "launched_monotonic_ns": time.monotonic_ns()}
                    runnable_ids.remove(node_id)

            if not running:
                if runnable_ids and not result_execution_failed and not deadline_exhausted:
                    failures.append("dispatcher could not satisfy node dependencies")
                break

            event_timeout = None
            if main_result_node not in ready_metadata and not deadline_exhausted:
                remaining_seconds = first_result_timeout_seconds - (time.monotonic() - first_result_started)
                if remaining_seconds <= 0:
                    failures.append("first-result deadline exhausted")
                    deadline_exhausted = True
                    result_execution_failed = True
                    continue
                event_timeout = remaining_seconds
            try:
                event_kind, node_id, payload = result_events.get(timeout=event_timeout)
            except queue.Empty:
                failures.append("first-result deadline exhausted")
                deadline_exhausted = True
                result_execution_failed = True
                continue

            if event_kind == "result-ready":
                if node_id not in ready_records:
                    ready_records[node_id] = payload
                    ready_metadata[node_id] = payload
                active_producers.discard(node_id)
                continue

            future = payload
            running.pop(node_id, None)
            active_producers.discard(node_id)
            record = future.result()
            record.update(launch_metadata.get(node_id, {}))
            record["settled_monotonic_ns"] = time.monotonic_ns()
            completed[node_id] = record
            if record.get("status") != "pass":
                failures.append(f"node {node_id} failed")
                result_execution_failed = True
                continue
            result_path = Path(record.get("result_path") or "")
            try:
                result_is_ready = result_path.is_file() and result_path.stat().st_size > 0
            except OSError:
                result_is_ready = False
            if node_id not in ready_records and result_is_ready:
                ready_monotonic_ns = record.get("result_ready_monotonic_ns")
                if isinstance(ready_monotonic_ns, bool) or not isinstance(ready_monotonic_ns, int) or ready_monotonic_ns < 0:
                    ready_monotonic_ns = time.monotonic_ns()
                with publication_lock:
                    published_ids.add(node_id)
                ready_records[node_id] = record
                ready_metadata[node_id] = {"result_ready_monotonic_ns": ready_monotonic_ns}
                if node_id == main_result_node and callable(result_ready_callback):
                    result_ready_callback(result_path, ready_monotonic_ns)
            elif node_id in ready_records:
                ready_records[node_id] = record

    ordered = [completed[node_id] for node_id in launch_order if node_id in completed]

    main_record = completed.get(plan["main_result_node"], {})

    if phase_verdict(main_record.get("result_path"), "Aggregate: PASS", "Aggregate: FAIL") == "fail":
        failures.append("final aggregate reported Aggregate: FAIL")
    status = "pass" if not failures and main_record.get("status") == "pass" else "fail"
    main_result_ready_ns = ready_metadata.get(plan["main_result_node"], {}).get("result_ready_monotonic_ns")
    if isinstance(main_result_ready_ns, bool) or not isinstance(main_result_ready_ns, int):
        main_result_ready_ns = main_record.get("result_ready_monotonic_ns")
    first_result_elapsed_ms = round((main_result_ready_ns - first_result_started_ns) / 1_000_000) if isinstance(main_result_ready_ns, int) and main_result_ready_ns >= first_result_started_ns else round((time.monotonic() - first_result_started) * 1000)
    result_published = bool(main_record.get("result_published") is True or plan["main_result_node"] in published_ids)
    receipt_failure_after_result = any(bool(record.get("result_published") is True or record.get("id") in published_ids) and record.get("status") != "pass" for record in ordered)
    ending_handoff_path = cache_dir / "ending-handoff.json"
    ending_manifest_path = cache_dir / "ending-dispatch-manifest.json"
    ending_release_path = _ending_release_path(cache_dir, route_run_id)

    if status == "pass":
        ending_handoff = {
            "purpose": "memory_only",
            "verification_owner": "active_task",
            "schema_version": DISPATCH_SCHEMA_VERSION,
            "cwd": str(cwd.resolve()),
            "state_db": str(Path(state_db).expanduser().resolve()) if state_db else None,
            "entry": {"model": entry_model, "effort": entry_effort},
            "route_run_id": route_run_id,
            "plan": plan,
            "completed": ordered,
            "main_result_node": plan.get("main_result_node"),
            "cache_dir": str(cache_dir),
            "released": False,
            "release_path": str(ending_release_path),
            "ending_manifest_path": str(ending_manifest_path),
        }
        ending_handoff_path.write_text(json.dumps(ending_handoff, indent=2) + "\n", encoding="utf-8")
        try:
            ending_handoff_path.chmod(0o600)
        except OSError:
            pass

    complete_summary_records = list(ordered)
    for node in plan.get("nodes", []):
        if not isinstance(node, dict) or node.get("phase") != "ending":
            continue
        if any(record.get("id") == node["id"] for record in ordered):
            continue
        complete_summary_records.append(
            {
                "id": node["id"],
                "model": node.get("model"),
                "effort": node.get("effort"),
                "status": "pending",
                "dependencies": list(node.get("dependencies", [])),
                "complexity_score": node.get("complexity_score"),
                "complexity_band": node.get("complexity_band"),
                "requested_model": node.get("model"),
                "requested_effort": node.get("effort"),
                "requested_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "resolved_model": node.get("model"),
                "resolved_effort": node.get("effort"),
                "resolved_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "effective_model": node.get("model"),
                "effective_effort": node.get("effort"),
                "effective_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "model_evidence_source": "task_assignment",
                "evidence_level": "UNVERIFIED (no runtime receipt)",
                "failure_class": None,
                "operational_fallback": False,
                "tokens": {},
                "process_elapsed_ms": None,
            }
        )
    model_switch_summary = build_model_switch_summary(
        plan,
        complete_summary_records,
        {"model": entry_model, "effort": entry_effort},
        ending_quality_failure_nodes=(),
    )
    operational_model_learning = _record_pre_result_operational_failures(plan, ordered, cwd)
    repair_handoff_path = _write_pre_result_repair_handoff(cache_dir, route_run_id, failures, ordered, deadline_exhausted) if not result_published else None
    pre_result_recovery_required = repair_handoff_path is not None

    manifest = {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "stage": "execution",
        "status": status,
        "failures": failures,
        "entry": {"model": entry_model, "effort": entry_effort},
        "complexity": plan["complexity"],
        "complexity_score": plan.get("complexity_score"),
        "complexity_band": plan.get("complexity_band"),
        "routing_mode": plan.get("routing_mode"),
        "topology": plan["topology"],
        "cache_dir": str(cache_dir),
        "nodes": ordered,
        "route_run_id": route_run_id,
        "main_result_node": plan["main_result_node"],
        "main_result_path": main_record.get("result_path"),
        "downstream_receipt_path": main_record.get("receipt_path"),
        "ending_nodes_pending": [node["id"] for node in plan["nodes"] if node.get("phase") == "ending"],
        "ending_handoff_path": str(ending_handoff_path) if status == "pass" else None,
        "ending_manifest_path": str(ending_manifest_path) if status == "pass" else None,
        "first_result_timeout_seconds": first_result_timeout_seconds,
        "first_result_elapsed_ms": first_result_elapsed_ms,
        "deadline_exhausted": deadline_exhausted,
        "repair_budget_remaining": 0,
        "result_published": result_published,
        "notification_required": receipt_failure_after_result or pre_result_recovery_required,
        "reopen_required": receipt_failure_after_result or pre_result_recovery_required,
        "repair_handoff_path": str(repair_handoff_path) if repair_handoff_path else None,
        "model_switch_summary": model_switch_summary,
        "operational_model_learning": operational_model_learning,
        "execution_lifecycle": plan["execution_lifecycle"],
        "model_disclosure": _plan_model_disclosure(plan, ordered, {"model": entry_model, "effort": entry_effort}, "result"),
        "ending_required": plan.get("ending_required") is True or any(node.get("phase") == "ending" for node in plan["nodes"]),
        "final_aggregate_receipt": False,
        "ending_launch_ready": False,
    }
    if manifest["ending_required"] and status == "pass":
        manifest["memory_closeout"] = memory_closeout_launch_packet(manifest)
    print(json.dumps(manifest["model_disclosure"], ensure_ascii=False, separators=(",", ":")), flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_ending_handoff(handoff_path, codex_bin="codex", skills_root=None):
    try:
        handoff = json.loads(handoff_path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "stage": "ending", "status": "fail", "failures": [f"invalid ending handoff: {type(error).__name__}"], "model_switch_summary": build_model_switch_summary({}, [], {}), "reopen_required": True, "notification_required": True}

    plan = handoff.get("plan") if isinstance(handoff.get("plan"), dict) else {}
    plan["execution_lifecycle"] = execution_lifecycle_for_plan(plan)
    cwd = Path(handoff.get("cwd") or Path.cwd()).expanduser().resolve()
    entry = handoff.get("entry") if isinstance(handoff.get("entry"), dict) else {}
    state_db = Path(handoff["state_db"]).expanduser().resolve() if handoff.get("state_db") else None
    route_run_id = handoff.get("route_run_id")
    failures = []
    if not route_run_id:
        failures.append("ending handoff is missing route_run_id")
    cache_dir = Path(handoff.get("cache_dir") or plan.get("cache_dir") or cwd / "work" / "cache" / "invalid-task-route").expanduser().resolve()
    if route_run_id:
        release_path = Path(handoff.get("release_path") or _ending_release_path(cache_dir, route_run_id))
        release_record = _read_release_record(release_path)
        if not isinstance(release_record, dict):
            if _has_mismatched_release_record(cache_dir, route_run_id):
                failures.append("ending handoff release does not match route_run_id")
            else:
                failures.append("ending handoff is not released")
        elif release_record.get("route_run_id") != route_run_id:
            failures.append("ending handoff release does not match route_run_id")
        elif handoff.get("released") is not True:
            failures.append("ending handoff is not marked released")
        elif release_record.get("main_result_node") != (handoff.get("main_result_node") or plan.get("main_result_node")):
            failures.append("ending handoff release does not match the main result node")
    if not failures:
        failures.extend(
            validate_plan(
                plan,
                entry.get("model"),
                entry.get("effort"),
                cwd,
                skills_root=skills_root,
                enforce_current_recommendation=False,
            )
        )
    manifest_path = Path(
        handoff.get("ending_manifest_path") or cache_dir / "ending-dispatch-manifest.json"
    ).expanduser().resolve()
    completed_records = handoff.get("completed") if isinstance(handoff.get("completed"), list) else []
    completed = {
        record.get("id"): record
        for record in completed_records
        if isinstance(record, dict) and record.get("status") == "pass" and record.get("id")
    }
    node_by_id = {
        node["id"]: node
        for node in plan.get("nodes", [])
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    }

    ending_ids = [node_id for node_id, node in node_by_id.items() if node.get("phase") == "ending"]
    main_node = node_by_id.get(plan.get("main_result_node"), {})
    main_record = completed.get(plan.get("main_result_node"), {})
    ordered = []
    routing_learning = None
    if not failures and ending_ids:
        ending_id = ending_ids[0]
        ending_node = dict(node_by_id[ending_id])
        ending_node["_entry_model"] = entry.get("model")
        ending_node["_entry_effort"] = entry.get("effort")
        if not all(dependency in completed for dependency in ending_node.get("dependencies", [])):
            failures.append("task-level Ending dependency was not satisfied")
        else:
            ending_record = run_node(
                ending_node,
                cache_dir,
                dict(completed),
                state_db,
                cwd,
                codex_bin,
                skills_root,
            )
            ordered.append(ending_record)
            if ending_record.get("status") != "pass":
                failures.append(f"Ending Task node {ending_record['id']} failed")
            ending_status = phase_verdict(ending_record.get("result_path"), "ENDING_TASK=PASS", "ENDING_TASK=FAIL")
            if ending_status != "pass":
                failures.append(f"Task-level Ending node {ending_record['id']} did not pass ENDING_TASK marker")

    status = (
        "pass"
        if not failures and all(record.get("status") == "pass" for record in ordered)
        else "fail"
    )
    summary_records = [record for record in completed_records if isinstance(record, dict)]
    summary_records.extend(ordered)
    completed_node_ids = {record.get("id") for record in summary_records if isinstance(record, dict) and record.get("id")}
    for node in plan.get("nodes", []):
        if not isinstance(node, dict) or not node.get("id") or node["id"] in completed_node_ids:
            continue
        summary_records.append(
            {
                "id": node["id"],
                "model": node.get("model"),
                "effort": node.get("effort"),
                "status": "pending",
                "dependencies": list(node.get("dependencies", [])),
                "requested_model": node.get("model"),
                "requested_effort": node.get("effort"),
                "requested_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "resolved_model": node.get("model"),
                "resolved_effort": node.get("effort"),
                "resolved_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "effective_model": node.get("model"),
                "effective_effort": node.get("effort"),
                "effective_pair": f"{node.get('model')}|{node.get('effort')}" if node.get("model") and node.get("effort") else None,
                "model_evidence_source": "task_assignment",
                "evidence_level": "UNVERIFIED (no runtime receipt)",
                "failure_class": None,
                "operational_fallback": False,
                "tokens": {},
                "process_elapsed_ms": None,
            }
        )
    quality_failure_nodes = []  # Memory closeout never grades the producer.
    model_switch_summary = build_model_switch_summary(
        plan,
        summary_records,
        entry,
        ending_quality_failure_nodes=quality_failure_nodes,
    )

    manifest = {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "stage": "ending",
        "status": status,
        "failures": failures,
        "entry": entry,
        "nodes": ordered,
        "model_switch_summary": model_switch_summary,
        "reopen_required": status != "pass",
        "notification_required": status != "pass",
        "routing_learning": routing_learning,
        "execution_lifecycle": plan["execution_lifecycle"],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def compact_run_plan_manifest(manifest):
    keys = ("schema_version", "status", "failures", "manifest_path", "main_result_path", "ending_handoff_path",
            "route_run_id", "first_result_elapsed_ms", "deadline_exhausted", "result_published", "notification_required",
            "reopen_required", "execution_lifecycle", "complexity_score", "complexity_band", "model_disclosure",
            "model_switch_summary", "ending_required", "final_aggregate_receipt", "ending_launch_ready", "memory_closeout")
    return {key: manifest[key] for key in keys if key in manifest}


def _emit_result_ready_event(result_path, ready_monotonic_ns):
    event = {"schema_version": DISPATCH_SCHEMA_VERSION, "stage": "result-ready", "result_path": str(result_path), "result_ready_monotonic_ns": ready_monotonic_ns}
    print(json.dumps(event, separators=(",", ":")), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Execute a validated internal Task Analyze route without lifecycle hooks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("run-plan")
    plan_parser.add_argument("plan", type=Path)
    plan_parser.add_argument("--cwd", type=Path, default=Path.cwd())
    plan_parser.add_argument("--state-db", type=Path, help="Optional explicit Codex runtime SQLite database; runtime discovery is used when omitted.")
    plan_parser.add_argument("--codex-bin", default="codex")
    plan_parser.add_argument("--skills-root", type=Path)
    preflight_parser = subparsers.add_parser("validate-plan")
    preflight_parser.add_argument("plan", type=Path)
    preflight_parser.add_argument("--cwd", type=Path, default=Path.cwd())
    preflight_parser.add_argument("--skills-root", type=Path)
    ending_parser = subparsers.add_parser("run-ending")
    ending_parser.add_argument("handoff", type=Path)
    ending_parser.add_argument("--codex-bin", default="codex")
    ending_parser.add_argument("--skills-root", type=Path)
    release_parser = subparsers.add_parser("release-main-result")
    release_parser.add_argument("handoff", type=Path)


    args = parser.parse_args()
    if args.command in {"run-plan", "validate-plan"}:
        plan = json.loads(args.plan.expanduser().resolve().read_text(encoding="utf-8"))
        entry = plan.get("entry") if isinstance(plan.get("entry"), dict) else {}
        preflight = preflight_plan(plan, entry.get("model"), entry.get("effort"), args.cwd.expanduser().resolve(), args.skills_root)
        if args.command == "validate-plan":
            manifest = preflight
        else:
            manifest = run_plan(plan, entry.get("model"), entry.get("effort"), args.cwd.expanduser().resolve(), args.state_db.expanduser().resolve() if args.state_db else None, args.codex_bin, args.skills_root, result_ready_callback=_emit_result_ready_event, preflight=preflight)
    elif args.command == "release-main-result":
        handoff = json.loads(args.handoff.expanduser().resolve().read_text(encoding="utf-8"))
        manifest = _release_main_result(handoff)
    else:
        manifest = run_ending_handoff(args.handoff, args.codex_bin, args.skills_root)
    if manifest.get("memory_closeout"):
        print(json.dumps(manifest["memory_closeout"], ensure_ascii=False, separators=(",", ":")), flush=True)
    stdout_manifest = compact_run_plan_manifest(manifest) if args.command == "run-plan" else manifest
    print(json.dumps(stdout_manifest, separators=(",", ":")))
    return 0 if manifest.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
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
try:
    from routing_policy import (
        ACTIVE_MODEL_EFFORTS,
        EXECUTION_DOMAINS,
        MODEL_ROLE_PAIRS,
        PRIORITY_PRODUCER_CONFIG,
        adaptive_pair_texts_for_profile,
        execution_domain_is_active,
        expected_owner_skill,
        is_code_execution_domain,
        normal_adaptive_pair_texts,
        resolve_execution_domain,
        reference_path_for,
        validate_execution_domain_registry,
    )
except ModuleNotFoundError:
    import importlib.util as _importlib_util

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = _importlib_util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = _importlib_util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    ACTIVE_MODEL_EFFORTS = _routing_policy.ACTIVE_MODEL_EFFORTS
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    MODEL_ROLE_PAIRS = _routing_policy.MODEL_ROLE_PAIRS
    PRIORITY_PRODUCER_CONFIG = _routing_policy.PRIORITY_PRODUCER_CONFIG
    adaptive_pair_texts_for_profile = _routing_policy.adaptive_pair_texts_for_profile
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    expected_owner_skill = _routing_policy.expected_owner_skill
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    normal_adaptive_pair_texts = _routing_policy.normal_adaptive_pair_texts
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    reference_path_for = _routing_policy.reference_path_for
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

NODE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
DISPATCH_SCHEMA_VERSION = 2
ALLOWED_PHASES = {"result", "ending"}
ALLOWED_SANDBOXES = {"read-only", "workspace-write"}
ENDING_SKILLS = {"verify-skill", "optimization-skill", "management-skill"}

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


def resolve_skills_root(skills_root=None):
    if skills_root is None:
        return DISPATCHER_SKILLS_ROOT
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


def _model_memory_arguments(node, project_root):
    condition = node.get("routing_condition") or {}
    scope = node.get("model_memory_scope") if isinstance(node.get("model_memory_scope"), dict) else {}
    return {
        "project_root": Path(project_root).expanduser().resolve(),
        "task_type": scope.get("task_type") or _model_memory_task_type(node),
        "module": scope.get("module") or node.get("skill") or "project-wide",
        "file_value": scope.get("file") or "",
        "symbol": scope.get("symbol") or "",
        "code_kind": scope.get("code_kind") or condition.get("execution_domain") or "general",
        "operation": scope.get("operation") or condition.get("task_family") or "work",
        "modality": condition.get("modality") or "text",
        "complexity": condition.get("complexity") or "easy",
        "risk": condition.get("risk") or "low",
        "ambiguity": condition.get("ambiguity") or "low",
        "task_summary": node.get("task_summary") or "",
    }


def _obsidian_recommendation_and_proof(node, project_root):
    recommendation = obsidian_model_memory.recommend_model(**_model_memory_arguments(node, project_root))
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
        "calibration_state": recommendation.get("calibration_state"),
        "best_pair": recommendation.get("success_model"),
        "selection_basis": "obsidian_broad_model_switch" if recommendation.get("memory_available") is True else "shared_cold_start",
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


def validate_plan(
    plan,
    entry_model,
    entry_effort,
    cwd,
    skills_root=None,
    *,
    enforce_current_recommendation=False,
    history_path=None,
):
    skills_root = resolve_skills_root(skills_root)
    failures = []
    try:
        validate_execution_domain_registry(skills_root)
    except ValueError as error:
        failures.append(f"execution_domain registry is invalid: {error}")
    if plan.get("schema_version") != DISPATCH_SCHEMA_VERSION:
        failures.append(f"schema_version must be {DISPATCH_SCHEMA_VERSION}")
    if plan.get("complexity") not in {"easy", "complex"}:
        failures.append("complexity must be easy or complex")
    first_result_timeout_seconds = plan.get("first_result_timeout_seconds", 180 if plan.get("complexity") == "easy" else 600)
    if not isinstance(first_result_timeout_seconds, int) or not 1 <= first_result_timeout_seconds <= 900:
        failures.append("first_result_timeout_seconds must be 1 to 900 seconds")
    else:
        plan["first_result_timeout_seconds"] = first_result_timeout_seconds
    if plan.get("topology") not in {"sequential", "parallel", "mixed"}:
        failures.append("topology must be sequential, parallel, or mixed")
    entry = plan.get("entry") if isinstance(plan.get("entry"), dict) else {}
    if entry.get("model") != entry_model or entry.get("effort") != entry_effort:
        failures.append("plan entry pair does not match the declared entrance pair")
    cache_dir_value = plan.get("cache_dir")
    cache_dir = Path(cache_dir_value).expanduser().resolve() if isinstance(cache_dir_value, str) and cache_dir_value else None
    if cache_dir is None or not path_is_within(cache_dir, cwd.resolve()):
        failures.append("cache_dir must be an absolute path inside the active cwd")

    nodes = plan.get("nodes") if isinstance(plan.get("nodes"), list) else []
    if not 2 <= len(nodes) <= 12:
        failures.append("nodes must contain 2 to 12 bounded nodes")

    node_by_id = {}
    main_candidate_pairs = []
    for node in nodes:
        if not isinstance(node, dict):
            failures.append("every node must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not NODE_ID_PATTERN.fullmatch(node_id):
            failures.append("every node id must be lowercase kebab-case")
            continue
        if node_id in node_by_id:
            failures.append(f"duplicate node id: {node_id}")
        node_by_id[node_id] = node

        model = node.get("model")
        effort = node.get("effort")
        priority_branch = bool(
            node.get("priority_producer") is True
            and node.get("phase") == "result"
            and node.get("skill") == "workflow-skill"
            and node.get("dependencies") == []
            and node.get("sandbox", "read-only") == "read-only"
            and isinstance(node.get("source_allowlist"), list)
            and len(node["source_allowlist"]) == 1
            and PRIORITY_PRODUCER_CONFIG.get("enabled") is True
            and model == PRIORITY_PRODUCER_CONFIG.get("id")
            and effort in PRIORITY_PRODUCER_CONFIG.get("adaptive_efforts", [])
        )
        if not priority_branch and (model not in ACTIVE_MODEL_EFFORTS or effort not in ACTIVE_MODEL_EFFORTS.get(model, set())):
            failures.append(f"{node_id} must use a model/effort from the catalog quality ladder")
        if "priority_producer" in node and not priority_branch:
            failures.append(f"{node_id} priority_producer is valid only for an admitted single-source read-only branch")
        skill = node.get("skill")
        if not isinstance(skill, str) or resolve_node_skill_path(skill, skills_root) is None:
            failures.append(f"{node_id} names unavailable skill {skill}")
        phase = node.get("phase")
        if phase not in ALLOWED_PHASES:
            failures.append(f"{node_id} has invalid phase")
        requested_verification_result = node.get("user_requested_verification_result")
        if phase == "result" and skill == "verify-skill":
            if requested_verification_result is not True:
                failures.append(f"{node_id} verify-skill result nodes require user_requested_verification_result=true")
        elif "user_requested_verification_result" in node:
            failures.append(f"{node_id} user_requested_verification_result is valid only on a result-phase verify-skill node")
        if node.get("sandbox", "read-only") not in ALLOWED_SANDBOXES:
            failures.append(f"{node_id} requests an unsafe automatic sandbox")
        if "load_user_config" in node and not isinstance(node["load_user_config"], bool):
            failures.append(f"{node_id} load_user_config must be a boolean")
        timeout = node.get("timeout", 180)
        if not isinstance(timeout, int) or not 1 <= timeout <= 300:
            failures.append(f"{node_id} timeout must be 1 to 300 seconds")

        prompt = node.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
            failures.append(f"{node_id} prompt must contain 1 to 12000 characters")

        dependencies = node.get("dependencies", [])
        if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
            failures.append(f"{node_id} dependencies must be a list of node ids")
        if "fuses_owned_source_with_dependencies" in node and not isinstance(node["fuses_owned_source_with_dependencies"], bool):
            failures.append(f"{node_id} fuses_owned_source_with_dependencies must be a boolean")

        allow_fallbacks = node.get("allow_fallback", [])
        if not isinstance(allow_fallbacks, list):
            failures.append(f"{node_id} allow_fallback must be a list")
        else:
            try:
                node["allow_fallback"] = receipt_module.normalize_fallback_pairs(allow_fallbacks)
                if any(model not in ACTIVE_MODEL_EFFORTS or effort not in ACTIVE_MODEL_EFFORTS[model] for model, effort in node["allow_fallback"]):
                    failures.append(f"{node_id} allow_fallback must stay inside the catalog quality ladder")
            except (TypeError, ValueError):
                failures.append(f"{node_id} allow_fallback contains unsupported model|effort pairs")

        spark_exception = node.get("spark_exception_reason", "")
        if not isinstance(spark_exception, str) or len(spark_exception) > 240:
            failures.append(f"{node_id} spark_exception_reason must be a string of at most 240 characters")

        try:
            execution_domain, explicitly_explicit = _resolve_execution_domain_with_flag(node)
        except ValueError:
            execution_domain = str(node.get("execution_domain") or "")
            failures.append(f"{node_id} execution_domain is unknown")
            explicitly_explicit = bool(node.get("execution_domain"))
        else:
            node["execution_domain"] = execution_domain

        expected_owner = None
        if execution_domain in EXECUTION_DOMAINS:
            if not execution_domain_is_active(execution_domain):
                failures.append(f"{node_id} execution_domain is non-active: {execution_domain}")
            expected_owner = expected_owner_skill(execution_domain) if is_code_execution_domain(execution_domain) else None
        else:
            expected_owner = None
        if expected_owner is not None and skill != expected_owner:
            failures.append(f"{node_id} bypasses code-skill; implementation owner mismatch for {execution_domain}")

        if node_id == plan.get("main_result_node"):
            routing_condition = node.get("routing_condition")
            if not isinstance(routing_condition, dict):
                failures.append(f"{node_id} requires routing_condition")
                routing_condition = {}
            elif "execution_domain" not in routing_condition:
                failures.append(f"{node_id} requires routing_condition.execution_domain")
            candidate_ladder = node.get("candidate_ladder")
            static_suggestion = node.get("static_suggestion")
            hard_floor = node.get("hard_floor")
            static_pair = None
            hard_pair = None
            if isinstance(routing_condition, dict):
                condition_domain = routing_condition.get("execution_domain")
                if condition_domain != execution_domain:
                    failures.append(
                        f"{node_id} execution_domain must match routing_condition.execution_domain"
                    )
                try:
                    routing_condition = routing_history_module.validate_condition(routing_condition)
                except ValueError as error:
                    failures.append(f"{node_id} routing_condition is invalid: {error}")
                node["routing_condition"] = routing_condition
                if routing_condition.get("owning_skill") != node.get("skill"):
                    failures.append(
                        f"{node_id} routing_condition.owning_skill must match the executing node skill"
                    )
            try:
                node["task_summary"] = routing_history_module.validate_summary(node.get("task_summary"))
            except ValueError as error:
                failures.append(f"{node_id} task_summary is invalid: {error}")
            if not isinstance(candidate_ladder, list):
                failures.append(f"{node_id} candidate_ladder must be a list")
            else:
                try:
                    candidate_pairs = routing_history_module.canonical_pairs(candidate_ladder)
                except (ValueError, TypeError) as error:
                    failures.append(f"{node_id} candidate_ladder is invalid: {error}")
                    candidate_pairs = []
                if candidate_pairs:
                    ordered_pairs = [routing_history_module.pair_text(*pair) for pair in candidate_pairs]
                    if ordered_pairs != candidate_ladder:
                        failures.append(f"{node_id} candidate_ladder must be canonical")
                    if routing_history_module.pair_text(model, effort) not in ordered_pairs:
                        failures.append(f"{node_id} selected pair must be in candidate_ladder")
                else:
                    ordered_pairs = []
                main_candidate_pairs = candidate_pairs
                if static_suggestion is None or hard_floor is None:
                    failures.append(f"{node_id} static_suggestion and hard_floor are required")
                else:
                    try:
                        static_pair = routing_history_module.parse_pair(static_suggestion)
                        hard_pair = routing_history_module.parse_pair(hard_floor)
                    except (TypeError, ValueError) as error:
                        failures.append(f"{node_id} static_suggestion or hard_floor is invalid: {error}")
                    else:
                        if static_pair not in candidate_pairs or hard_pair not in candidate_pairs:
                            failures.append(f"{node_id} static_suggestion and hard_floor must be in candidate_ladder")
                        if routing_history_module.parse_pair(routing_history_module.pair_text(model, effort)) in candidate_pairs and routing_history_module.compare_pair((model, effort), hard_pair) < 0:
                            failures.append(f"{node_id} selected pair must not be below hard_floor")
                        node["static_suggestion"] = routing_history_module.pair_text(*static_pair)
                        node["hard_floor"] = routing_history_module.pair_text(*hard_pair)
                if not isinstance(node.get("trial"), bool):
                    failures.append(f"{node_id} trial must be a boolean")
                if all(routing_condition.get(field) for field in CONTROLLED_FIELDS):
                    expected_ladder = adaptive_pair_texts_for_profile(
                        routing_condition["task_family"],
                        routing_condition["modality"],
                        routing_condition["risk"],
                        routing_condition["complexity"],
                        routing_condition["ambiguity"],
                    )
                    if ordered_pairs != expected_ladder:
                        failures.append(f"{node_id} candidate_ladder must exactly match the full catalog quality ladder")
                recommendation = node.get("routing_recommendation")
                if not isinstance(recommendation, dict):
                    failures.append(f"{node_id} requires routing_recommendation proof")
                elif candidate_pairs and static_pair is not None and hard_pair is not None:
                    required_proof_keys = set(RECOMMENDATION_PROOF_FIELDS)
                    missing_proof_keys = sorted(required_proof_keys - set(recommendation))
                    if missing_proof_keys:
                        failures.append(f"{node_id} routing_recommendation proof missing keys: {', '.join(missing_proof_keys)}")
                    expected_fingerprint = routing_history_module.profile_fingerprint(routing_condition, candidate_pairs, static_pair, hard_pair)
                    if recommendation.get("selected_pair") != routing_history_module.pair_text(model, effort) or recommendation.get("trial") is not node.get("trial"):
                        failures.append(f"{node_id} routing_recommendation must match the selected pair and trial")
                    if recommendation.get("profile_fingerprint") != expected_fingerprint:
                        failures.append(f"{node_id} routing_recommendation profile fingerprint is invalid")
                    if enforce_current_recommendation and not missing_proof_keys:
                        try:
                            current_recommendation, current_proof = _obsidian_recommendation_and_proof(node, cwd)
                        except (OSError, TypeError, ValueError) as error:
                            failures.append(f"{node_id} current Obsidian recommendation could not be verified: {type(error).__name__}")
                        else:
                            if current_recommendation.get("selected_pair") is None:
                                failures.append(f"{node_id} current Obsidian recommendation is exhausted")
                            if current_proof.get("selected_pair") != routing_history_module.pair_text(model, effort) or current_proof.get("trial") is not node.get("trial"):
                                failures.append(f"{node_id} selected pair/trial does not match current Obsidian recommendation")
                            stale_fields = [field for field in RECOMMENDATION_PROOF_FIELDS if recommendation.get(field) != current_proof.get(field)]
                            if stale_fields:
                                failures.append(f"{node_id} routing_recommendation is stale or not Obsidian-derived: {', '.join(stale_fields)}")

            for field in CONTROLLED_FIELDS:
                if field not in node.get("routing_condition", {}):
                    failures.append(f"{node_id} routing_condition missing {field}")

    for node_id, node in node_by_id.items():
        for dependency in node.get("dependencies", []):
            if dependency not in node_by_id:
                failures.append(f"{node_id} has missing dependency {dependency}")

    main_result_node = plan.get("main_result_node")
    if main_result_node not in node_by_id or node_by_id.get(main_result_node, {}).get("phase") != "result":
        failures.append("main_result_node must name a result-phase node")
    if "mini_verify_node" in plan:
        failures.append("mini_verify_node is not valid in schema 2")

    result_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "result"}
    visited = set()
    while len(visited) < len(result_ids):
        ready = [
            node_id
            for node_id in result_ids - visited
            if all(dependency in visited for dependency in node_by_id[node_id].get("dependencies", []))
        ]
        if not ready:
            failures.append("result dependencies contain a cycle or depend on Ending Task")
            break
        visited.update(ready)

    if main_result_node in node_by_id:
        missing_from_main = sorted(
            result_ids - dependency_closure(main_result_node, node_by_id) - {main_result_node}
        )
        if missing_from_main:
            failures.append("main_result_node must depend transitively on every result node: " + ", ".join(missing_from_main))
        main_routing_condition = node_by_id[main_result_node].get("routing_condition", {})
        is_grounded_read_only_answer = main_routing_condition.get("task_family") == "grounded" and main_routing_condition.get("artifact") == "answer" and main_routing_condition.get("modality") == "text" and main_routing_condition.get("risk") == "low"
        if is_grounded_read_only_answer and len(result_ids) > 1:
            branch_allowlists = [node_by_id[node_id].get("source_allowlist") for node_id in sorted(result_ids - {main_result_node})]
            branch_allowlists_are_disjoint = all(isinstance(allowlist, list) and allowlist and all(isinstance(source, str) and source for source in allowlist) for allowlist in branch_allowlists)
            seen_sources = set()
            for allowlist in branch_allowlists:
                if not isinstance(allowlist, list) or not allowlist or seen_sources.intersection(allowlist):
                    branch_allowlists_are_disjoint = False
                    break
                seen_sources.update(allowlist)
            main_node = node_by_id[main_result_node]
            dependency_only_merge = main_node.get("reads_dependency_results_only") is True and "source_allowlist" not in main_node and main_node.get("fuses_owned_source_with_dependencies") is not True
            fused_allowlist = main_node.get("source_allowlist")
            fused_merge = bool(
                main_node.get("fuses_owned_source_with_dependencies") is True
                and main_node.get("reads_dependency_results_only") is not True
                and isinstance(fused_allowlist, list)
                and len(fused_allowlist) == 1
                and not seen_sources.intersection(fused_allowlist)
                and set(main_node.get("dependencies", [])) == result_ids - {main_result_node}
            )
            if not branch_allowlists_are_disjoint or not (dependency_only_merge or fused_merge):
                failures.append("grounded read-only answers allow multiple result nodes only for disjoint source branches plus either a dependency-only merge or one disjoint owned source fused into the main merge")

    ending_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "ending"}
    optimization_ids = {node_id for node_id, node in node_by_id.items() if node.get("skill") == "optimization-skill"}
    if not ending_ids:
        failures.append("the locked plan must include at least one post-result Ending Task node")
    if len(ending_ids) > 3:
        failures.append("Ending Task supports at most three bounded sibling nodes")
    for node_id in sorted(ending_ids):
        ending_dependencies = node_by_id[node_id].get("dependencies", [])
        ending_node = node_by_id[node_id]
        ending_skill = ending_node.get("skill")
        if main_result_node not in ending_dependencies:
            failures.append(f"{node_id} must depend directly on the main result node")
        if ending_skill == "verify-skill":
            verifies_node = ending_node.get("verifies_node")
            if verifies_node is not None:
                target_node = node_by_id.get(verifies_node)
                if not isinstance(verifies_node, str):
                    failures.append(f"{node_id} verifies_node must be a node id string")
                elif not target_node:
                    failures.append(f"{node_id} verifies_node must reference an existing node: {verifies_node}")
                elif target_node.get("skill") != "optimization-skill":
                    failures.append(f"{node_id} verifies_node must target an optimization-skill node: {verifies_node}")
                elif verifies_node not in ending_dependencies:
                    failures.append(f"{node_id} must depend directly on its verifies_node target: {verifies_node}")
                elif node_id == verifies_node:
                    failures.append(f"{node_id} cannot verify itself")
                other_ending_dependencies = [
                    dependency
                    for dependency in ending_dependencies
                    if dependency in ending_ids and dependency != verifies_node
                ]
                if other_ending_dependencies:
                    failures.append(f"{node_id} can only depend on an Ending node for its verifies_node target: {other_ending_dependencies[0]}")
        elif any(dependency in ending_ids for dependency in ending_dependencies):
            failures.append(f"Ending Task node {node_id} must be an independent sibling, not depend on another Ending node")
        if ending_node.get("skill") not in ENDING_SKILLS:
            failures.append(
                f"Ending Task node {node_id} must use verify-skill, optimization-skill, or management-skill"
            )
    for optimization_node_id in sorted(optimization_ids):
        optimization_verifiers = [
            verifier_id
            for verifier_id, verifier_node in node_by_id.items()
            if verifier_node.get("phase") == "ending"
            and verifier_node.get("skill") == "verify-skill"
            and verifier_node.get("verifies_node") == optimization_node_id
        ]
        if len(optimization_verifiers) != 1:
            failures.append(
                f"optimization-skill node {optimization_node_id} must have exactly one ending verify-skill verifier targeting it"
            )
    producer_verifiers = [node_id for node_id in ending_ids if node_by_id[node_id].get("skill") == "verify-skill" and not node_by_id[node_id].get("verifies_node")]
    if len(producer_verifiers) != 1:
        failures.append("plans require exactly one non-targeted Ending verify-skill producer verifier")

    if main_candidate_pairs:
        candidate_pair_text = {routing_history_module.pair_text(*pair) for pair in main_candidate_pairs}
        for node_id, node in node_by_id.items():
            for fallback_pair in node.get("allow_fallback", []):
                if fallback_pair not in candidate_pair_text:
                    failures.append(f"{node_id} allow_fallback pair must be in main candidate_ladder: {fallback_pair}")

    return failures


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
    path.chmod(0o600)


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
    skills_root = resolve_skills_root(skills_root)
    node_id = node["id"]
    receipt_path = cache_dir / f"{node_id}-receipt.json"
    result_path = cache_dir / f"{node_id}-result.md"
    skill_path = resolve_node_skill_path(node["skill"], skills_root)
    if skill_path is None:
        raise ValueError(f"node skill cannot be resolved: {node['skill']}")
    dependency_text = dependency_context(node, completed)
    prompt = (
        f"Owning skill: {node['skill']}\n"
        f"Node id: {node_id}\n"
        f"Phase: {node['phase']}\n"
        f"Execute only this bounded locked node. Read and obey {skill_path}.\n\n"
        f"{node['prompt']}"
    )
    if execution_domain_is_active(_resolve_execution_domain(node)) and is_code_execution_domain(_resolve_execution_domain(node)):
        execution_domain, _ = _resolve_execution_domain_with_flag(node)
        reference_path = reference_path_for(execution_domain)
        if reference_path:
            prompt += f"\n\nReference rules for this execution domain: {skills_root / reference_path}"
    if dependency_text:
        prompt += f"\n\nCompleted dependency handoff:\n{dependency_text}"
    if node["phase"] == "ending":
        prompt += "\n\nThis is a direct post-result Ending Task worker. Include the exact line ENDING_TASK=PASS only when the bounded verification/optimization purpose passes. Otherwise include ENDING_TASK=FAIL."

    route_marker = "ENDING_TASK_WORKER" if node["phase"] == "ending" else "LOCKED_ROUTE_NODE"
    fallback_pairs = receipt_module.normalize_fallback_pairs(node.get("allow_fallback", []))
    selected_pair = f"{node['model']}|{node['effort']}"
    adaptive_recommendation = None
    if node["phase"] == "result" and isinstance(node.get("routing_recommendation"), dict) and node.get("_project_root") and receipt_module.entry_context_active():
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
        )
        try:
            if args.node_role == "result-producer":
                if receipt_module.entry_context_active():
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
        attempt_receipt["result_published"] = bool(result_path.is_file() and result_path.stat().st_size > 0)
        attempt_receipt = receipt_module.annotate_operational_fallback(attempt_receipt)
        attempt_receipt_path.write_text(json.dumps(attempt_receipt, indent=2) + "\n", encoding="utf-8")
        route_attempts.append(_normalize_route_attempt(attempt_receipt, pair_text, status, failure_class))
        receipt = attempt_receipt
        if status == "pass":
            break
        if node["phase"] != "result" or not receipt_module.immediate_operational_fallback(attempt_receipt):
            break

    attempt_metrics = _aggregate_attempt_metrics(route_attempts)
    receipt["route_attempts"] = route_attempts
    receipt["priority_attempt_pair"] = priority_attempt_pair
    receipt["active_fallback_pair"] = selected_pair if priority_attempt_pair != selected_pair else None
    receipt["allowed_fallback_pairs"] = planned_pairs[1:]
    receipt["operational_failure_pairs"] = [
        attempted_pair
        for attempted_pair, attempted_receipt in zip(planned_pairs, route_attempts)
        if attempted_receipt.get("fallback_eligible") is True
    ]
    receipt["last_attempt_tokens"] = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
    receipt["last_attempt_process_elapsed_ms"] = receipt.get("process_elapsed_ms")
    receipt["strategy_tokens"] = attempt_metrics["strategy_tokens"]
    receipt["strategy_elapsed_ms"] = attempt_metrics["strategy_elapsed_ms"]
    receipt["attempt_metrics_complete"] = attempt_metrics["metrics_complete"]
    receipt["tokens"] = attempt_metrics["strategy_tokens"]
    receipt["process_elapsed_ms"] = attempt_metrics["strategy_elapsed_ms"]
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    result_published = bool(node["phase"] == "result" and result_path.is_file() and result_path.stat().st_size > 0)
    result_ready_monotonic_ns = receipt.get("result_ready_monotonic_ns")
    if result_published and not isinstance(result_ready_monotonic_ns, int):
        result_ready_monotonic_ns = time.monotonic_ns()
    return {
        "id": node_id,
        "phase": node["phase"],
        "skill": node["skill"],
        "requested_model": receipt.get("requested_model", node["model"]),
        "requested_effort": receipt.get("requested_effort", node["effort"]),
        "model": receipt.get("effective_model") or receipt.get("requested_model"),
        "effort": receipt.get("resolved_effort") or receipt.get("requested_effort"),
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
    }


def _route_run_id():
    return f"route-{uuid.uuid4().hex}"


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
    memory_args = _model_memory_arguments(node, project_root)
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
        return {"status": "fail", "reason": f"obsidian_model_memory_record_failed:{type(error).__name__}"}
    return {"status": recorder_result.get("status"), "recorder_result": recorder_result, "recommendation": recommendation}


def _release_main_result(handoff):
    handoff_data = dict(handoff)
    route_run_id = handoff_data.get("route_run_id")
    if not isinstance(route_run_id, str) or not route_run_id:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "fail", "route_run_id": None, "failures": ["ending handoff is missing route_run_id"]}

    cache_dir = Path(handoff_data.get("cache_dir") or "/").expanduser().resolve()
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
    return {"schema_version": DISPATCH_SCHEMA_VERSION, "status": "pass", "route_run_id": route_run_id, "release_path": str(release_path)}


def run_plan(
    plan,
    entry_model,
    entry_effort,
    cwd,
    state_db=Path.home() / ".codex" / "state_5.sqlite",
    codex_bin="codex",
    skills_root=None,
    history_path=None,
    result_ready_callback=None,
):
    first_result_started = time.monotonic()
    first_result_started_ns = time.monotonic_ns()
    first_result_timeout_seconds = plan.get("first_result_timeout_seconds", 180 if plan.get("complexity") == "easy" else 600)
    failures = validate_plan(
        plan,
        entry_model,
        entry_effort,
        cwd,
        skills_root=skills_root,
        enforce_current_recommendation=True,
        history_path=history_path,
    )
    cache_dir = Path(plan["cache_dir"]).expanduser().resolve() if not failures else cwd.resolve() / "work" / "cache" / "invalid-task-route"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "dispatch-manifest.json"

    route_run_id = _route_run_id()

    if failures:
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
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    node_by_id = {node["id"]: node for node in plan["nodes"]}
    first_result_timeout_seconds = plan["first_result_timeout_seconds"]
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
                node_id = dependency_ready[0]
                remaining_seconds = first_result_timeout_seconds - (time.monotonic() - first_result_started)
                if remaining_seconds <= 0:
                    failures.append("first-result deadline exhausted")
                    deadline_exhausted = True
                    break
                ready_node = dict(node_by_id[node_id])
                ready_node["timeout"] = min(ready_node.get("timeout", 180), max(1, int(remaining_seconds)))
                ready_node["_deadline_monotonic"] = first_result_started + first_result_timeout_seconds
                ready_node["_fallback_reserve_seconds"] = 30 if plan["complexity"] == "easy" else 90
                ready_node["_project_root"] = str(cwd.resolve())
                ready_node["_result_ready_callback"] = result_ready_callback_for(node_id)
                future = executor.submit(run_node, ready_node, cache_dir, dict(ready_records), state_db, cwd, codex_bin, skills_root)
                future.add_done_callback(lambda settled_future, settled_node_id=node_id: result_events.put(("settled", settled_node_id, settled_future)))
                running[node_id] = future
                active_producers.add(node_id)
                launch_order.append(node_id)
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
            "schema_version": DISPATCH_SCHEMA_VERSION,
            "cwd": str(cwd.resolve()),
            "state_db": str(state_db.expanduser().resolve()),
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

    manifest = {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "stage": "execution",
        "status": status,
        "failures": failures,
        "entry": {"model": entry_model, "effort": entry_effort},
        "complexity": plan["complexity"],
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
        "notification_required": receipt_failure_after_result,
        "reopen_required": receipt_failure_after_result,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_ending_handoff(handoff_path, codex_bin="codex", skills_root=None):
    try:
        handoff = json.loads(handoff_path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"schema_version": DISPATCH_SCHEMA_VERSION, "stage": "ending", "status": "fail", "failures": [f"invalid ending handoff: {type(error).__name__}"], "reopen_required": True, "notification_required": True}

    plan = handoff.get("plan") if isinstance(handoff.get("plan"), dict) else {}
    cwd = Path(handoff.get("cwd") or "/").expanduser().resolve()
    entry = handoff.get("entry") if isinstance(handoff.get("entry"), dict) else {}
    state_db = Path(handoff.get("state_db") or Path.home() / ".codex" / "state_5.sqlite").expanduser().resolve()
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

    runnable_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "ending"}
    main_node = node_by_id.get(plan.get("main_result_node"), {})
    main_record = completed.get(plan.get("main_result_node"), {})
    ordered = []
    routing_learning = None
    if not failures:
        while runnable_ids:
            ready = sorted(
                node_id for node_id in runnable_ids
                if all(dependency in completed for dependency in node_by_id[node_id].get("dependencies", []))
            )
            if not ready:
                failures.append("Ending Task sibling dependencies were not satisfied")
                break
            completed_snapshot = dict(completed)
            with ThreadPoolExecutor(max_workers=min(3, len(ready))) as executor:
                futures = {
                    node_id: executor.submit(
                        run_node,
                        node_by_id[node_id],
                        cache_dir,
                        completed_snapshot,
                        state_db,
                        cwd,
                        codex_bin,
                        skills_root,
                    )
                    for node_id in ready
                }
                wave_records = [futures[node_id].result() for node_id in ready]
            ordered.extend(wave_records)
            for record in wave_records:
                runnable_ids.remove(record["id"])
                if record.get("status") == "pass":
                    completed[record["id"]] = record
                else:
                    failures.append(f"Ending Task node {record['id']} failed")

            for record in wave_records:
                verify_node = node_by_id.get(record["id"], {})
                if verify_node.get("skill") != "verify-skill":
                    continue
                verifies_node = verify_node.get("verifies_node")
                if not verifies_node:
                    continue

                target_record = completed.get(verifies_node)
                if not target_record:
                    failures.append(f"Targeted verifier {record['id']} could not read target node {verifies_node}")
                    record["status"] = "fail"
                    continue
                target_identity = target_record.get("worker_identity")
                verifier_identity = record.get("worker_identity")
                if not target_identity:
                    failures.append(f"Targeted verifier {record['id']} target {verifies_node} missing worker identity")
                    record["status"] = "fail"
                    continue
                if not verifier_identity:
                    failures.append(f"Targeted verifier {record['id']} missing worker identity")
                    record["status"] = "fail"
                    continue
                if verifier_identity == target_identity:
                    failures.append(
                        f"Targeted verifier {record['id']} must use a distinct execution worker from target {verifies_node}"
                    )
                    record["status"] = "fail"
                    continue

        for ending_record in ordered:
            if node_by_id.get(ending_record.get("id"), {}).get("skill") != "verify-skill" or not main_record or not main_node:
                continue
            if node_by_id.get(ending_record.get("id"), {}).get("verifies_node"):
                continue
            ending_status = phase_verdict(ending_record.get("result_path"), "ENDING_TASK=PASS", "ENDING_TASK=FAIL")
            if ending_status != "pass":
                failures.append(f"Non-targeted Ending verify node {ending_record['id']} did not pass ENDING_TASK marker")
            recorded_learning = _run_record(
                main_record.get("receipt_path"),
                "real",
                ending_status if ending_status in {"pass", "fail"} else "unknown",
                main_record.get("receipt_path"),
                route_run_id,
                main_node,
                cwd,
                execution_domain=main_node.get("routing_condition", {}).get("execution_domain"),
            )
            routing_learning = recorded_learning if isinstance(recorded_learning, dict) else None

    status = (
        "pass"
        if not failures and ordered and all(record.get("status") == "pass" for record in ordered)
        else "fail"
    )
    manifest = {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "stage": "ending",
        "status": status,
        "failures": failures,
        "entry": entry,
        "nodes": ordered,
        "reopen_required": status != "pass",
        "notification_required": status != "pass",
        "routing_learning": routing_learning,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def compact_run_plan_manifest(manifest):
    return {"schema_version": manifest.get("schema_version"), "status": manifest.get("status"), "failures": manifest.get("failures", []), "manifest_path": manifest.get("manifest_path"), "main_result_path": manifest.get("main_result_path"), "ending_handoff_path": manifest.get("ending_handoff_path"), "route_run_id": manifest.get("route_run_id"), "first_result_elapsed_ms": manifest.get("first_result_elapsed_ms"), "deadline_exhausted": manifest.get("deadline_exhausted", False), "result_published": manifest.get("result_published", False), "notification_required": manifest.get("notification_required", False), "reopen_required": manifest.get("reopen_required", False)}


def _emit_result_ready_event(result_path, ready_monotonic_ns):
    event = {"schema_version": DISPATCH_SCHEMA_VERSION, "stage": "result-ready", "result_path": str(result_path), "result_ready_monotonic_ns": ready_monotonic_ns}
    print(json.dumps(event, separators=(",", ":")), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Execute a validated internal Task Analyze route without lifecycle hooks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("run-plan")
    plan_parser.add_argument("plan", type=Path)
    plan_parser.add_argument("--cwd", type=Path, default=Path.cwd())
    plan_parser.add_argument("--state-db", type=Path, default=Path.home() / ".codex" / "state_5.sqlite")
    plan_parser.add_argument("--codex-bin", default="codex")
    plan_parser.add_argument("--skills-root", type=Path)
    ending_parser = subparsers.add_parser("run-ending")
    ending_parser.add_argument("handoff", type=Path)
    ending_parser.add_argument("--codex-bin", default="codex")
    ending_parser.add_argument("--skills-root", type=Path)
    release_parser = subparsers.add_parser("release-main-result")
    release_parser.add_argument("handoff", type=Path)


    args = parser.parse_args()
    if args.command == "run-plan":
        plan = json.loads(args.plan.expanduser().resolve().read_text(encoding="utf-8"))
        entry = plan.get("entry") if isinstance(plan.get("entry"), dict) else {}
        manifest = run_plan(
            plan,
            entry.get("model"),
            entry.get("effort"),
            args.cwd.expanduser().resolve(),
            args.state_db.expanduser().resolve(),
            args.codex_bin,
            args.skills_root,
            result_ready_callback=_emit_result_ready_event,
        )
    elif args.command == "release-main-result":
        handoff = json.loads(args.handoff.expanduser().resolve().read_text(encoding="utf-8"))
        manifest = _release_main_result(handoff)
    else:
        manifest = run_ending_handoff(args.handoff, args.codex_bin, args.skills_root)
    stdout_manifest = compact_run_plan_manifest(manifest) if args.command == "run-plan" else manifest
    print(json.dumps(stdout_manifest, separators=(",", ":")))
    return 0 if manifest.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

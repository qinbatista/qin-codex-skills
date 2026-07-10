#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import re
import subprocess
from datetime import datetime, timezone
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace


RECEIPT_PATH = Path(__file__).resolve().parent / "model_execution_receipt.py"
RECEIPT_SPEC = importlib.util.spec_from_file_location(
    "task_analyze_model_execution_receipt", RECEIPT_PATH
)
receipt_module = importlib.util.module_from_spec(RECEIPT_SPEC)
RECEIPT_SPEC.loader.exec_module(receipt_module)
MODEL_EFFORTS = receipt_module.MODEL_EFFORTS
try:
    from routing_policy import (
        EXECUTION_DOMAINS,
        execution_domain_is_active,
        expected_owner_skill,
        is_code_execution_domain,
        requires_spark_first,
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
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    execution_domain_is_active = _routing_policy.execution_domain_is_active
    expected_owner_skill = _routing_policy.expected_owner_skill
    is_code_execution_domain = _routing_policy.is_code_execution_domain
    requires_spark_first = _routing_policy.requires_spark_first
    resolve_execution_domain = _routing_policy.resolve_execution_domain
    reference_path_for = _routing_policy.reference_path_for
    validate_execution_domain_registry = _routing_policy.validate_execution_domain_registry

HISTORY_PATH = Path(__file__).resolve().parent / "model_routing_history.py"
HISTORY_SPEC = importlib.util.spec_from_file_location(
    "task_analyze_model_routing_history", HISTORY_PATH
)
routing_history_module = importlib.util.module_from_spec(HISTORY_SPEC)
HISTORY_SPEC.loader.exec_module(routing_history_module)

NODE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ALLOWED_PHASES = {"result", "mini", "ending"}
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

DISPATCHER_SKILLS_ROOT = Path(__file__).resolve().parents[2]


def resolve_skills_root(skills_root=None):
    if skills_root is None:
        return DISPATCHER_SKILLS_ROOT
    return Path(skills_root).resolve()


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


def validate_plan(plan, entry_model, entry_effort, cwd, skills_root=None):
    skills_root = resolve_skills_root(skills_root)
    failures = []
    try:
        validate_execution_domain_registry(skills_root)
    except ValueError as error:
        failures.append(f"execution_domain registry is invalid: {error}")
    if plan.get("schema_version") != 1:
        failures.append("schema_version must be 1")
    if plan.get("complexity") not in {"easy", "complex"}:
        failures.append("complexity must be easy or complex")
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
        if model not in MODEL_EFFORTS or effort not in MODEL_EFFORTS.get(model, set()):
            failures.append(f"{node_id} has unsupported model/effort")
        skill = node.get("skill")
        if not isinstance(skill, str) or not (skills_root / skill / "SKILL.md").exists():
            failures.append(f"{node_id} names unavailable skill {skill}")
        if node.get("phase") not in ALLOWED_PHASES:
            failures.append(f"{node_id} has invalid phase")
        if node.get("sandbox", "read-only") not in ALLOWED_SANDBOXES:
            failures.append(f"{node_id} requests an unsafe automatic sandbox")
        timeout = node.get("timeout", 180)
        if not isinstance(timeout, int) or not 1 <= timeout <= 300:
            failures.append(f"{node_id} timeout must be 1 to 300 seconds")

        prompt = node.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
            failures.append(f"{node_id} prompt must contain 1 to 12000 characters")

        dependencies = node.get("dependencies", [])
        if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
            failures.append(f"{node_id} dependencies must be a list of node ids")

        allow_fallbacks = node.get("allow_fallback", [])
        if not isinstance(allow_fallbacks, list):
            failures.append(f"{node_id} allow_fallback must be a list")
        else:
            try:
                node["allow_fallback"] = receipt_module.normalize_fallback_pairs(allow_fallbacks)
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

        if _is_code_implementation(node):
            spark_forced = requires_spark_first(execution_domain)
            if spark_forced and node.get("model") != "gpt-5.3-codex-spark" and not (
                spark_exception.strip() or node.get("fallback_reason", "").strip()
            ):
                failures.append(f"{node_id} has no fallback reason; implementation must be Spark-first or state spark_exception_reason/fallback_reason")

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
                        node["static_suggestion"] = routing_history_module.pair_text(*static_pair)
                        node["hard_floor"] = routing_history_module.pair_text(*hard_pair)
                if not isinstance(node.get("trial"), bool):
                    failures.append(f"{node_id} trial must be a boolean")

            for field in CONTROLLED_FIELDS:
                if field not in node.get("routing_condition", {}):
                    failures.append(f"{node_id} routing_condition missing {field}")

    for node_id, node in node_by_id.items():
        for dependency in node.get("dependencies", []):
            if dependency not in node_by_id:
                failures.append(f"{node_id} has missing dependency {dependency}")

    main_result_node = plan.get("main_result_node")
    mini_verify_node = plan.get("mini_verify_node")
    if main_result_node not in node_by_id or node_by_id.get(main_result_node, {}).get("phase") != "result":
        failures.append("main_result_node must name a result-phase node")
    if mini_verify_node not in node_by_id or node_by_id.get(mini_verify_node, {}).get("phase") != "mini":
        failures.append("mini_verify_node must name a mini-phase node")
    elif main_result_node not in node_by_id[mini_verify_node].get("dependencies", []):
        failures.append("Mini Verify must depend directly on the main result node")
    elif node_by_id[mini_verify_node].get("skill") != "verify-skill":
        failures.append("Mini Verify must be owned by verify-skill")

    result_mini_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") in {"result", "mini"}}
    visited = set()
    while len(visited) < len(result_mini_ids):
        ready = [
            node_id
            for node_id in result_mini_ids - visited
            if all(dependency in visited for dependency in node_by_id[node_id].get("dependencies", []))
        ]
        if not ready:
            failures.append("result/Mini dependencies contain a cycle or depend on Ending Task")
            break
        visited.update(ready)

    result_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") == "result"}
    if main_result_node in node_by_id:
        missing_from_main = sorted(
            result_ids - dependency_closure(main_result_node, node_by_id) - {main_result_node}
        )
        if missing_from_main:
            failures.append("main_result_node must depend transitively on every result node: " + ", ".join(missing_from_main))

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
        if mini_verify_node not in ending_dependencies:
            failures.append(f"{node_id} must depend directly on Mini Verify")
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
        "process_elapsed_ms": candidate_attempt.get("process_elapsed_ms") if isinstance(candidate_attempt, dict) else None,
        "model_turn_duration_ms": candidate_attempt.get("model_turn_duration_ms") if isinstance(candidate_attempt, dict) else None,
        "time_to_first_token_ms": candidate_attempt.get("time_to_first_token_ms") if isinstance(candidate_attempt, dict) else None,
    }


def _ending_release_path(cache_dir, route_run_id):
    safe_route_run_id = re.sub(r"[^a-zA-Z0-9._-]", "-", route_run_id)
    return Path(cache_dir) / f"{safe_route_run_id}.ending-release.json"


def _release_record(route_run_id, completed, cache_dir):
    return {
        "schema_version": 1,
        "route_run_id": route_run_id,
        "released_at": datetime.now(timezone.utc).isoformat(),
        "released_by": "run-plan",
        "main_result_node": completed.get("main_result_node"),
        "mini_verify_node": completed.get("mini_verify_node"),
        "main_result_receipt_path": completed.get("main_result_receipt_path"),
        "mini_verify_receipt_path": completed.get("mini_verify_receipt_path"),
        "mini_verify_result_path": completed.get("mini_verify_result_path"),
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
    dependency_text = dependency_context(node, completed)
    prompt = (
        f"Owning skill: {node['skill']}\n"
        f"Node id: {node_id}\n"
        f"Phase: {node['phase']}\n"
        f"Execute only this bounded locked node. Read and obey {skills_root / node['skill'] / 'SKILL.md'}.\n\n"
        f"{node['prompt']}"
    )
    if execution_domain_is_active(_resolve_execution_domain(node)) and is_code_execution_domain(_resolve_execution_domain(node)):
        execution_domain, _ = _resolve_execution_domain_with_flag(node)
        reference_path = reference_path_for(execution_domain)
        if reference_path:
            prompt += f"\n\nReference rules for this execution domain: {skills_root / reference_path}"
    if dependency_text:
        prompt += f"\n\nVerified dependency handoff:\n{dependency_text}"
    if node["phase"] == "mini":
        prompt += "\n\nReturn a concise verdict and include the exact line MINI_VERIFY=PASS only when the supplied result satisfies this node's acceptance target. Otherwise include MINI_VERIFY=FAIL."
    if node["phase"] == "ending":
        prompt += "\n\nThis is a direct post-result Ending Task worker. Include the exact line ENDING_TASK=PASS only when the bounded verification/optimization purpose passes. Otherwise include ENDING_TASK=FAIL."

    route_marker = "ENDING_TASK_WORKER" if node["phase"] == "ending" else "LOCKED_ROUTE_NODE"
    fallback_pairs = receipt_module.normalize_fallback_pairs(node.get("allow_fallback", []))
    planned_pairs = [f"{node['model']}|{node['effort']}"] + fallback_pairs
    route_attempts = []
    receipt = None
    status = "fail"
    for attempt_index, pair_text in enumerate(planned_pairs, start=1):
        attempt_model, attempt_effort = receipt_module.parse_model_effort_pair(pair_text)
        attempt_receipt_path = cache_dir / f"{node_id}-attempt-{attempt_index}-receipt.json"
        args = SimpleNamespace(
            model=attempt_model,
            effort=attempt_effort,
            codex_bin=codex_bin,
            sandbox=node.get("sandbox", "read-only"),
            ignore_user_config=False,
            entry_task=False,
            route_marker=route_marker,
            result_output=result_path,
            timeout=node.get("timeout", 180),
            workdir=workdir.resolve(),
            state_db=state_db,
            workload_id=f"task-route-{node_id}",
            allow_fallback=[],
        )
        try:
            attempt_receipt = receipt_module.run_receipt(args, prompt)
        except (subprocess.TimeoutExpired, OSError, ValueError) as error:
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
                    "process_elapsed_ms": None,
                    "model_turn_duration_ms": None,
                    "time_to_first_token_ms": None,
                }],
            }
            failure_class = "execution"
            status = "fail"
        else:
            failure_class = attempt_receipt.get("failure_class")
            status = attempt_receipt.get("status") or "fail"

        if status == "pass" and node["phase"] == "mini":
            status = phase_verdict(result_path, "MINI_VERIFY=PASS", "MINI_VERIFY=FAIL")
            if status != "pass":
                status = "fail"
                failure_class = "protocol"
                attempt_receipt["status"] = "fail"
        if status == "pass" and node["phase"] == "ending":
            status = phase_verdict(result_path, "ENDING_TASK=PASS", "ENDING_TASK=FAIL")
            if status != "pass":
                status = "fail"
                failure_class = "protocol"
                attempt_receipt["status"] = "fail"

        if status == "pass":
            failure_class = None
        attempt_receipt_path.write_text(json.dumps(attempt_receipt, indent=2) + "\n", encoding="utf-8")
        route_attempts.append(
            _normalize_route_attempt(
                attempt_receipt,
                pair_text,
                status,
                failure_class,
            )
        )
        receipt = attempt_receipt
        if status == "pass":
            break
        if node["phase"] != "result" or failure_class not in receipt_module.RUNTIME_FAILURES:
            break

    receipt["route_attempts"] = route_attempts
    receipt["allowed_fallback_pairs"] = fallback_pairs
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
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
        "worker_identity": worker_identity(receipt),
        "tokens": receipt.get("tokens"),
        "process_elapsed_ms": receipt.get("process_elapsed_ms"),
    }


def _route_run_id():
    return f"route-{uuid.uuid4().hex}"


def _run_record(result_path, verify_level, verify_status, main_result_receipt_path, route_run_id, main_node, execution_domain=None):
    if not main_result_receipt_path:
        return {"status": "skipped", "reason": "missing-main-result-receipt"}
    node = main_node
    condition = dict(node.get("routing_condition", {}))
    if execution_domain is not None:
        condition["execution_domain"] = execution_domain
    verify_status = verify_status if verify_status in {"pass", "fail", "unknown"} else "unknown"
    failure_class = "none"
    if verify_status == "fail":
        failure_class = "quality"
    if verify_status == "unknown":
        failure_class = "execution"
    args = SimpleNamespace(
        task_family=condition.get("task_family"),
        artifact=condition.get("artifact"),
        scope=condition.get("scope"),
        ambiguity=condition.get("ambiguity"),
        modality=condition.get("modality"),
        risk=condition.get("risk"),
        complexity=condition.get("complexity"),
        owning_skill=condition.get("owning_skill"),
        project_family=condition.get("project_family"),
        verification_shape=condition.get("verification_shape"),
        task_summary=node.get("task_summary", ""),
        candidate_ladder=node.get("candidate_ladder", []),
        static_suggestion=node.get("static_suggestion", ""),
        hard_floor=node.get("hard_floor", ""),
        execution_domain=condition.get("execution_domain") or None,
        receipt=main_result_receipt_path,
        verify_level=verify_level,
        verify_status=verify_status,
        failure_class=failure_class,
        run_id=route_run_id,
        trial=bool(node.get("trial")),
        history=Path(__file__).resolve().parents[1] / "local" / "adaptive-routing" / "model_experience.json",
    )
    return routing_history_module.record_event(args)


def _release_main_result(handoff):
    handoff_data = dict(handoff)
    route_run_id = handoff_data.get("route_run_id")
    if not isinstance(route_run_id, str) or not route_run_id:
        return {"schema_version": 1, "status": "fail", "route_run_id": None, "failures": ["ending handoff is missing route_run_id"]}

    cache_dir = Path(handoff_data.get("cache_dir") or "/").expanduser().resolve()
    plan = handoff_data.get("plan") if isinstance(handoff_data.get("plan"), dict) else {}
    node_by_id = {node.get("id"): node for node in plan.get("nodes", []) if isinstance(node, dict) and isinstance(node.get("id"), str)}
    completed = {
        record.get("id"): record
        for record in handoff_data.get("completed", [])
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    main_node_id = handoff_data.get("main_result_node") or plan.get("main_result_node")
    mini_node_id = handoff_data.get("mini_verify_node") or plan.get("mini_verify_node")
    main_record = completed.get(main_node_id) if isinstance(main_node_id, str) else None
    mini_record = completed.get(mini_node_id) if isinstance(mini_node_id, str) else None
    if main_record is None or mini_record is None:
        return {"schema_version": 1, "status": "fail", "route_run_id": route_run_id, "failures": ["ending handoff is missing main or mini record"]}
    if main_record.get("status") != "pass" or mini_record.get("status") != "pass":
        return {"schema_version": 1, "status": "fail", "route_run_id": route_run_id, "failures": ["main result and mini verify must both pass before release"]}
    mini_marker_status = phase_verdict(mini_record.get("result_path"), "MINI_VERIFY=PASS", "MINI_VERIFY=FAIL")
    if mini_marker_status != "pass":
        return {
            "schema_version": 1,
            "status": "fail",
            "route_run_id": route_run_id,
            "failures": ["Mini Verify result must contain an unambiguous MINI_VERIFY=PASS marker before release"],
        }

    release_path = _ending_release_path(cache_dir, route_run_id)
    release_record = _release_record(
        route_run_id,
        {
            "main_result_node": main_node_id,
            "mini_verify_node": mini_node_id,
            "main_result_receipt_path": main_record.get("receipt_path"),
            "mini_verify_receipt_path": mini_record.get("receipt_path"),
            "mini_verify_result_path": mini_record.get("result_path"),
        },
        cache_dir,
    )
    _write_release_record(release_path, release_record)
    handoff_data["released"] = True
    handoff_data["release_path"] = str(release_path)
    handoff_path = Path(handoff_data.get("ending_handoff_path") or cache_dir / "ending-handoff.json")
    handoff_path.write_text(json.dumps(handoff_data, indent=2) + "\n", encoding="utf-8")
    return {"schema_version": 1, "status": "pass", "route_run_id": route_run_id, "release_path": str(release_path)}


def run_plan(plan, entry_model, entry_effort, cwd, state_db=Path.home() / ".codex" / "state_5.sqlite", codex_bin="codex", skills_root=None):
    failures = validate_plan(plan, entry_model, entry_effort, cwd, skills_root=skills_root)
    cache_dir = Path(plan["cache_dir"]).expanduser().resolve() if not failures else cwd.resolve() / "work" / "cache" / "invalid-task-route"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "dispatch-manifest.json"

    route_run_id = _route_run_id()

    if failures:
        manifest = {
            "schema_version": 1,
            "stage": "validation",
            "status": "fail",
            "failures": failures,
            "entry": {"model": entry_model, "effort": entry_effort},
            "nodes": [],
            "route_run_id": route_run_id,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    node_by_id = {node["id"]: node for node in plan["nodes"]}
    runnable_ids = {node_id for node_id, node in node_by_id.items() if node.get("phase") in {"result", "mini"}}
    completed = {}
    ordered = []
    while runnable_ids:
        ready = sorted(
            node_id for node_id in runnable_ids if all(
                dependency in completed for dependency in node_by_id[node_id].get("dependencies", [])
            )
        )
        if not ready:
            failures.append("dispatcher could not satisfy node dependencies")
            break

        completed_snapshot = dict(completed)
        if plan["topology"] == "sequential" or len(ready) == 1:
            ready_records = {
                node_id: run_node(
                    node_by_id[node_id], cache_dir, completed_snapshot, state_db, cwd, codex_bin, skills_root
                )
                for node_id in ready
            }
        else:
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
                ready_records = {node_id: futures[node_id].result() for node_id in ready}

        for node_id in ready:
            record = ready_records[node_id]
            completed[node_id] = record
            ordered.append(record)
            runnable_ids.remove(node_id)
            if record["status"] != "pass":
                failures.append(f"node {node_id} failed")
                runnable_ids.clear()
                break

    main_node = node_by_id.get(plan["main_result_node"], {})
    mini_node_id = plan.get("mini_verify_node")
    main_record = completed.get(plan["main_result_node"], {})
    mini_record = completed.get(mini_node_id, {})

    if main_record:
        if mini_record:
            mini_status = phase_verdict(
                mini_record.get("result_path"), "MINI_VERIFY=PASS", "MINI_VERIFY=FAIL"
            )
            _run_record(
                main_record.get("receipt_path"),
                verify_level="mini",
                verify_status=mini_status if mini_status in {"pass", "fail"} else "unknown",
                main_result_receipt_path=main_record.get("receipt_path"),
                route_run_id=route_run_id,
                main_node=main_node,
                execution_domain=main_node.get("routing_condition", {}).get("execution_domain"),
            )
        elif main_record.get("status") != "pass":
            _run_record(
                main_record.get("receipt_path"),
                verify_level="mini",
                verify_status="unknown",
                main_result_receipt_path=main_record.get("receipt_path"),
                route_run_id=route_run_id,
                main_node=main_node,
                execution_domain=main_node.get("routing_condition", {}).get("execution_domain"),
            )

    status = "pass" if not failures and main_record.get("status") == "pass" and mini_record.get("status") == "pass" else "fail"
    ending_handoff_path = cache_dir / "ending-handoff.json"
    ending_manifest_path = cache_dir / "ending-dispatch-manifest.json"
    ending_release_path = _ending_release_path(cache_dir, route_run_id)

    if status == "pass":
        ending_handoff = {
            "schema_version": 1,
            "cwd": str(cwd.resolve()),
            "state_db": str(state_db.expanduser().resolve()),
            "entry": {"model": entry_model, "effort": entry_effort},
            "route_run_id": route_run_id,
            "plan": plan,
            "completed": ordered,
            "main_result_node": plan.get("main_result_node"),
            "mini_verify_node": mini_node_id,
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
        "schema_version": 1,
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
        "mini_verify_node": mini_node_id,
        "main_result_path": main_record.get("result_path"),
        "downstream_receipt_path": main_record.get("receipt_path"),
        "mini_receipt_path": mini_record.get("receipt_path"),
        "ending_nodes_pending": [node["id"] for node in plan["nodes"] if node.get("phase") == "ending"],
        "ending_handoff_path": str(ending_handoff_path) if status == "pass" else None,
        "ending_manifest_path": str(ending_manifest_path) if status == "pass" else None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def run_ending_handoff(handoff_path, codex_bin="codex", skills_root=None):
    try:
        handoff = json.loads(handoff_path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"schema_version": 1, "stage": "ending", "status": "fail", "failures": [f"invalid ending handoff: {type(error).__name__}"]}

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
        elif release_record.get("main_result_node") != (handoff.get("main_result_node") or plan.get("main_result_node")) or release_record.get("mini_verify_node") != (handoff.get("mini_verify_node") or plan.get("mini_verify_node")):
            failures.append("ending handoff release does not match main or mini node")
    if not failures:
        failures.extend(validate_plan(plan, entry.get("model"), entry.get("effort"), cwd, skills_root=skills_root))
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
    mini_record = completed.get(plan.get("mini_verify_node"), {})
    if not failures:
        mini_marker_status = phase_verdict(mini_record.get("result_path"), "MINI_VERIFY=PASS", "MINI_VERIFY=FAIL")
        if mini_marker_status != "pass":
            failures.append("ending handoff Mini Verify result is missing an unambiguous MINI_VERIFY=PASS marker")
    ordered = []
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
            _run_record(
                main_record.get("receipt_path"),
                "real",
                ending_status if ending_status in {"pass", "fail"} else "unknown",
                main_record.get("receipt_path"),
                route_run_id,
                main_node,
                execution_domain=main_node.get("routing_condition", {}).get("execution_domain"),
            )

    status = (
        "pass"
        if not failures and ordered and all(record.get("status") == "pass" for record in ordered)
        else "fail"
    )
    manifest = {
        "schema_version": 1,
        "stage": "ending",
        "status": status,
        "failures": failures,
        "entry": entry,
        "nodes": ordered,
        "reopen_required": status != "pass",
        "notification_required": status != "pass",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


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
        )
    elif args.command == "release-main-result":
        handoff = json.loads(args.handoff.expanduser().resolve().read_text(encoding="utf-8"))
        manifest = _release_main_result(handoff)
    else:
        manifest = run_ending_handoff(args.handoff, args.codex_bin, args.skills_root)
    print(json.dumps(manifest, separators=(",", ":")))
    return 0 if manifest.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

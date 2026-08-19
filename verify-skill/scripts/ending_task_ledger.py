#!/usr/bin/env python3
"""Ending lifecycle ledger for Windows, macOS, and Linux."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

if os.name == "nt":
    import msvcrt
else:
    import fcntl


DEFAULT_STORE = Path.home() / ".codex" / "ending-task-memory"
DEFAULT_MAX_REPAIR_ATTEMPTS = 3
SCHEMA_VERSION = 3
TERMINAL_EVENTS = {"pass", "fail", "blocked"}
ALL_EVENTS = TERMINAL_EVENTS | {"note"}
FAILURE_CLASSES = {"none", "availability", "timeout", "protocol", "telemetry", "execution", "receipt", "quality", "correctness"}
QUALITY_FAILURES = {"quality", "correctness"}
OPERATIONAL_FAILURES = FAILURE_CLASSES - QUALITY_FAILURES - {"none"}
MODEL_EVIDENCE_LEVELS = {"runtime_receipt", "verified_entry", "task_assignment", "configured_selection", "unavailable"}
ROUTE_CHANGES = {"upgrade", "downgrade", "freeze", "no_switch", "operational_fallback"}
UNKNOWN_MODEL_PAIR = "unknown|unknown"
ENDING_LAUNCH_ID = "task-ending"
AVAILABILITY_FALLBACK_REASONS = {
    "primary_model_unavailable",
    "primary_effort_unsupported",
    "primary_pair_not_in_registry",
    "scheduler_unavailable",
    "required_modality_unavailable",
}
REPAIR_DISPATCH_TOOL = "codex_app__send_message_to_thread"
REQUIRED_MODEL_CONTEXT_FIELDS = ("project_root", "task_type", "module", "file", "symbol", "code_kind", "operation", "modality", "complexity", "complexity_score", "complexity_band", "risk", "ambiguity", "task_summary")
OPTIONAL_MODEL_CONTEXT_FIELDS = ("step_kind", "capability_tags", "capability_fingerprint", "entry_model", "entry_effort", "entry_pair", "entry_source")
MODEL_CONTEXT_FIELDS = REQUIRED_MODEL_CONTEXT_FIELDS + OPTIONAL_MODEL_CONTEXT_FIELDS
PROJECT_MEMORY_CLASSIFICATIONS = {"aligned", "no_prior_memory", "memory_record_defect", "memory_projection_defect", "skill_contract_defect", "execution_drift", "insufficient_evidence"}
PROJECT_MEMORY_ACTIONS = {"record", "correction", "reconcile", "origin_repair", "blocked"}
PROJECT_MEMORY_STATUS_VALUES = {"match", "absent", "mismatch", "projection_missing", "projection_mismatch", "unavailable"}
CONSISTENCY_STATUS_VALUES = {"pass", "fail", "unavailable"}
PROJECT_MEMORY_INTENT_FIELDS = {"mode", "module", "scope", "change_kind", "summary", "reason", "result", "files", "symbols", "decisions", "risks", "supersedes"}
PROJECT_MEMORY_SCOPES = {"project", "feature", "code", "file"}
PROJECT_MEMORY_CHANGE_KINDS = {"add", "edit", "rename", "move", "delete", "mixed"}
SENSITIVE_MEMORY_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_-])(?:sk|rk|pk)-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s,;]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"https?://[^\s/:]+:[^\s/@]+@", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[^\s]+", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])[A-Z]:\\Users\\[^\s]+", re.IGNORECASE),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
)
PROJECT_MEMORY_CLASSIFICATION_RULES = {
    "aligned": {"event": "pass", "action": "record", "process_status": "pass", "execution_status": "pass", "memory_status": "match"},
    "no_prior_memory": {"event": "pass", "action": "record", "process_status": "pass", "execution_status": "pass", "memory_status": "absent"},
    "memory_record_defect": {"event": "pass", "action": "correction", "process_status": "pass", "execution_status": "pass", "memory_status": "mismatch"},
    "memory_projection_defect": {"event": "pass", "action": "reconcile", "process_status": "pass", "execution_status": "pass", "memory_status": {"projection_missing", "projection_mismatch"}},
    "skill_contract_defect": {"event": "fail", "action": "origin_repair", "process_status": "fail"},
    "execution_drift": {"event": "fail", "action": "origin_repair", "process_status": "pass", "execution_status": "fail"},
    "insufficient_evidence": {"event": "blocked", "action": "blocked"},
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _single_line(value, field_name, required=True, max_length=1200):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not text:
        raise ValueError(f"{field_name} is required")
    return text[:max_length]


def _sanitized_memory_line(value, field_name, required=True, max_length=1200):
    text = _single_line(value, field_name, required=required, max_length=max_length)
    if any(pattern.search(text) for pattern in SENSITIVE_MEMORY_PATTERNS):
        raise ValueError(f"{field_name} contains private or secret-like content")
    return text


def _normalize_files(project_root, file_values):
    if not project_root:
        if file_values:
            raise ValueError("--file requires --project-root")
        return []
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    normalized = []
    for file_value in file_values:
        candidate = Path(file_value).expanduser()
        relative = candidate.resolve().relative_to(root) if candidate.is_absolute() else PurePosixPath(candidate.as_posix())
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"file must be inside project_root: {file_value}")
        relative_text = relative.as_posix()
        if relative_text not in normalized:
            normalized.append(relative_text)
    return normalized


def _state_path(store, lifecycle_id):
    return store / "lifecycles" / f"{lifecycle_id}.json"


def _read_state(store, lifecycle_id):
    path = _state_path(store, lifecycle_id)
    if not path.is_file():
        raise ValueError(f"unknown lifecycle_id: {lifecycle_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(store, state):
    path = _state_path(store, state["lifecycle_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f".tmp-{uuid.uuid4().hex}")
    temporary_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)
    return path


def _append_event(store, event):
    index_path = store / "index.jsonl"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


@contextmanager
def _exclusive_file_lock(lock_path):
    path = Path(lock_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _model_pair(value, field_name):
    pair = _single_line(value, field_name, required=False, max_length=160)
    return pair if pair and pair != UNKNOWN_MODEL_PAIR else None


def _origin_session(thread_id="", host_id=""):
    if bool(thread_id) != bool(host_id):
        raise ValueError("origin session requires both origin_thread_id and origin_host_id")
    if not thread_id:
        return None
    return {"thread_id": _single_line(thread_id, "origin_thread_id", max_length=160), "host_id": _single_line(host_id, "origin_host_id", max_length=160)}


def _ending_plan_assignment(plan_path, ending_check_id, selected_pair, availability_reason=""):
    payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    policy = payload.get("ending_model_policy") if isinstance(payload, dict) else None
    if not isinstance(policy, dict):
        tasks = payload.get("ending_tasks") if isinstance(payload, dict) else None
        check = next((item for item in tasks if isinstance(item, dict) and item.get("check_id") == ending_check_id), None) if isinstance(tasks, list) else None
        if not check:
            return None
        planned_pair = _model_pair(check.get("selected_pair"), "plan selected_pair")
        if not planned_pair or selected_pair != planned_pair:
            raise ValueError("actual Ending selected_pair does not match the verification plan")
        if availability_reason:
            raise ValueError("legacy verification plan does not authorize an availability fallback")
        return {"primary_pair": planned_pair, "availability_fallback_pair": None, "selected_pair": selected_pair, "availability_fallback_reason": None}
    task_ids = [item.get("check_id") for item in payload.get("ending_tasks", []) if isinstance(item, dict)]
    if ending_check_id != ENDING_LAUNCH_ID and ending_check_id not in task_ids:
        raise ValueError("ending_check_id does not match the verification plan")
    primary_pair = _model_pair(policy.get("primary_pair"), "plan primary_pair")
    fallback_pair = _model_pair(policy.get("availability_fallback_pair"), "plan availability_fallback_pair")
    approved_pairs = policy.get("approved_pairs")
    if not primary_pair or not isinstance(approved_pairs, list) or selected_pair not in approved_pairs:
        raise ValueError("actual Ending selected_pair is not approved by the verification plan")
    reason_value = _single_line(availability_reason, "availability_fallback_reason", required=False, max_length=80) or None
    allowed_reasons = policy.get("availability_fallback_reasons")
    if fallback_pair and selected_pair == fallback_pair:
        if reason_value not in AVAILABILITY_FALLBACK_REASONS or reason_value not in (allowed_reasons or []):
            raise ValueError("availability fallback requires a sanitized availability reason")
    elif selected_pair == primary_pair:
        if reason_value:
            raise ValueError("primary Ending pair must not claim an availability fallback reason")
    else:
        raise ValueError("actual Ending selected_pair is neither the primary nor availability fallback pair")
    return {
        "primary_pair": primary_pair,
        "availability_fallback_pair": fallback_pair,
        "selected_pair": selected_pair,
        "availability_fallback_reason": reason_value,
        "primary_selection_reason": policy.get("primary_selection_reason"),
        "score_controls": policy.get("score_controls"),
        "quality_failure_model_fallback": False,
    }


def _model_disclosure(selected_pair, producer_binding, requested_pair="", resolved_pair="", effective_pair="", previous_pair="", model_evidence="", route_change="", switch_summary="", reason=""):
    assigned_pair = _model_pair(selected_pair, "selected_pair")
    receipt_requested_pair = producer_binding.get("requested_pair") if producer_binding else None
    receipt_resolved_pair = producer_binding.get("resolved_pair") if producer_binding else None
    receipt_effective_pair = producer_binding.get("effective_pair") if producer_binding else None
    requested_pair = _model_pair(requested_pair, "requested_pair") or receipt_requested_pair or assigned_pair
    resolved_pair = _model_pair(resolved_pair, "resolved_pair") or receipt_resolved_pair or assigned_pair or requested_pair
    effective_pair = receipt_effective_pair or _model_pair(effective_pair, "effective_pair") or resolved_pair or requested_pair or assigned_pair
    known_pair = effective_pair or resolved_pair or requested_pair or assigned_pair
    requested_pair = requested_pair or known_pair or UNKNOWN_MODEL_PAIR
    resolved_pair = resolved_pair or known_pair or UNKNOWN_MODEL_PAIR
    effective_pair = effective_pair or known_pair or UNKNOWN_MODEL_PAIR
    model_evidence = _single_line(model_evidence, "model_evidence", required=False, max_length=40) or ("runtime_receipt" if producer_binding else "task_assignment" if assigned_pair else "configured_selection" if known_pair else "unavailable")
    if model_evidence not in MODEL_EVIDENCE_LEVELS:
        raise ValueError(f"model_evidence must be one of {', '.join(sorted(MODEL_EVIDENCE_LEVELS))}")
    if producer_binding:
        model_evidence = "runtime_receipt"
    elif model_evidence == "runtime_receipt":
        raise ValueError("runtime_receipt model_evidence requires a validated producer receipt")
    elif not known_pair and model_evidence != "unavailable":
        raise ValueError("model_evidence requires a known model identity")
    elif known_pair and model_evidence == "unavailable":
        raise ValueError("unavailable model_evidence requires no model identity")
    current_pair = effective_pair
    previous_pair = _model_pair(previous_pair, "previous_pair") or (resolved_pair if producer_binding and resolved_pair != current_pair else "same as current" if current_pair != UNKNOWN_MODEL_PAIR else "none")
    route_change = _single_line(route_change, "route_change", required=False, max_length=40) or ("operational_fallback" if producer_binding and resolved_pair and resolved_pair != current_pair else "no_switch")
    if route_change not in ROUTE_CHANGES:
        raise ValueError(f"route_change must be one of {', '.join(sorted(ROUTE_CHANGES))}")
    switch_summary = _single_line(switch_summary, "switch_summary", required=False, max_length=600) or ("No model switch" if route_change == "no_switch" else f"Switched from {previous_pair} to {current_pair} per switch rule.")
    if route_change == "no_switch" and current_pair != UNKNOWN_MODEL_PAIR and (previous_pair != "same as current" or any(pair != current_pair for pair in (requested_pair, resolved_pair, effective_pair))):
        raise ValueError("no_switch requires one concrete pair and previous_pair=same as current")
    if route_change == "no_switch" and switch_summary != "No model switch":
        raise ValueError("no_switch requires switch_summary=No model switch")
    reason = _single_line(reason, "reason", required=False, max_length=600) or ("Runtime receipt conflicts with resolved pair." if producer_binding and resolved_pair != current_pair else "Runtime receipt identifies the effective pair." if producer_binding else "Best-known pair used; receipt not available." if current_pair != UNKNOWN_MODEL_PAIR else "Previous-model provenance unavailable: no assignment or receipt.")
    evidence_level = "runtime_receipt" if producer_binding else "UNVERIFIED (no runtime receipt)" if current_pair != UNKNOWN_MODEL_PAIR else "unavailable"
    return {"assigned_pair": assigned_pair, "current_pair": current_pair, "model_evidence": model_evidence, "requested_pair": requested_pair, "resolved_pair": resolved_pair, "effective_pair": effective_pair, "previous_pair": previous_pair, "route_change": route_change, "switch_summary": switch_summary, "reason": reason, "effective_evidence_level": evidence_level}


def _producer_binding(receipt_value, project_root=None):
    if not receipt_value:
        return None
    receipt_path = Path(receipt_value).expanduser().resolve()
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    context = receipt.get("model_learning_context") if isinstance(receipt, dict) else None
    context_fields = set(context) if isinstance(context, dict) else set()
    if not isinstance(context, dict) or not set(REQUIRED_MODEL_CONTEXT_FIELDS).issubset(context_fields) or context_fields - set(MODEL_CONTEXT_FIELDS):
        raise ValueError("producer receipt requires the exact sanitized model_learning_context fields")
    sanitized = {}
    for field in (field for field in MODEL_CONTEXT_FIELDS if field in context):
        value = context[field]
        if field == "complexity_score":
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError("producer model_learning_context.complexity_score must be an integer from 0 to 100")
            sanitized[field] = value
            continue
        if field == "capability_tags":
            if not isinstance(value, list) or len(value) > 32 or any(not isinstance(tag, str) for tag in value):
                raise ValueError("producer model_learning_context.capability_tags must be a bounded text list")
            cleaned_tags = [_single_line(tag, "model_learning_context.capability_tags", required=True, max_length=120) for tag in value]
            if cleaned_tags != value or len(cleaned_tags) != len(set(cleaned_tags)):
                raise ValueError("producer model_learning_context.capability_tags is not sanitized")
            sanitized[field] = cleaned_tags
            continue
        maximum = 1200 if field == "project_root" else 600 if field in {"file", "symbol", "task_summary"} else 160
        if not isinstance(value, str):
            raise ValueError(f"producer model_learning_context.{field} must be text")
        cleaned = _single_line(value, f"model_learning_context.{field}", required=field in {"project_root", "task_type", "module"}, max_length=maximum)
        if cleaned != value:
            raise ValueError(f"producer model_learning_context.{field} is not sanitized")
        sanitized[field] = cleaned
    if "capability_fingerprint" in sanitized and not re.fullmatch(r"[0-9a-f]{64}", sanitized["capability_fingerprint"]):
        raise ValueError("producer model_learning_context.capability_fingerprint must be lowercase SHA-256")
    if "entry_pair" in sanitized:
        expected_entry_pair = f"{sanitized.get('entry_model', '')}|{sanitized.get('entry_effort', '')}"
        if not sanitized.get("entry_model") or not sanitized.get("entry_effort") or sanitized["entry_pair"] != expected_entry_pair:
            raise ValueError("producer model_learning_context.entry_pair does not match entry_model and entry_effort")
    expected_band = "small" if sanitized["complexity_score"] <= 24 else "standard" if sanitized["complexity_score"] <= 49 else "complex" if sanitized["complexity_score"] <= 74 else "advanced"
    if sanitized["complexity_band"] != expected_band:
        raise ValueError("producer model_learning_context.complexity_band does not match complexity_score")
    context_root = Path(sanitized["project_root"]).expanduser().resolve()
    if not context_root.is_dir():
        raise ValueError("producer model_learning_context.project_root must be an existing directory")
    if project_root and context_root != Path(project_root).expanduser().resolve():
        raise ValueError("producer receipt project_root does not match lifecycle project_root")
    executed_pair = receipt.get("executed_pair") or receipt.get("effective_pair") or receipt.get("requested_pair")
    route_attempts = receipt.get("route_attempts")
    matched_route_attempt = next((attempt for attempt in route_attempts if isinstance(attempt, dict) and attempt.get("status") == "pass" and attempt.get("executed_pair") == executed_pair and attempt.get("model_match") is True and attempt.get("effort_match") is True), None) if isinstance(route_attempts, list) else None
    if receipt.get("status") != "pass" or receipt.get("result_published") is not True or receipt.get("turn_completed") is not True or receipt.get("model_match") is not True or receipt.get("effort_match") is not True or receipt.get("node_type") != "locked-route-node" or receipt.get("node_role") != "result-producer" or not isinstance(executed_pair, str) or not matched_route_attempt:
        raise ValueError("producer receipt must be a matched passing published producer receipt")
    return {"receipt_path": str(receipt_path), "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(), "model_learning_context": sanitized, "executed_pair": executed_pair, "requested_pair": _model_pair(receipt.get("requested_pair"), "producer receipt requested_pair") or executed_pair, "resolved_pair": _model_pair(receipt.get("resolved_pair"), "producer receipt resolved_pair") or _model_pair(receipt.get("requested_pair"), "producer receipt requested_pair") or executed_pair, "effective_pair": executed_pair, "status": "pending"}


def _load_model_memory_module():
    script_path = Path(__file__).resolve().parents[2] / "project-memory-skill" / "scripts" / "obsidian_model_memory.py"
    spec = importlib.util.spec_from_file_location("ending_task_obsidian_model_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_personal_memory_module():
    script_path = Path(__file__).resolve().parents[2] / "project-memory-skill" / "scripts" / "personal_memory.py"
    spec = importlib.util.spec_from_file_location("ending_task_personal_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_project_memory_module():
    script_path = Path(__file__).resolve().parents[2] / "project-memory-skill" / "scripts" / "project_change_memory.py"
    spec = importlib.util.spec_from_file_location("ending_task_project_change_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _memory_candidate_file(state, candidate_file):
    if not candidate_file:
        return None
    path = Path(candidate_file).expanduser()
    root_value = state.get("project_root") or state.get("cwd")
    root = Path(root_value).expanduser().resolve() if root_value else Path.cwd().resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("memory candidates file must stay inside the lifecycle project root") from error
    return resolved


def _project_memory_intent(state):
    intent = state.get("project_memory_closeout")
    if not isinstance(intent, dict):
        intent = {"mode": "none"}
    mode = intent.get("mode") or "none"
    if mode not in {"none", "durable"}:
        raise ValueError("verification plan project_memory_closeout mode is invalid")
    unknown_fields = sorted(set(intent) - ({"mode"} if mode == "none" else PROJECT_MEMORY_INTENT_FIELDS))
    if unknown_fields:
        raise ValueError("verification plan project_memory_closeout contains unknown fields: " + ", ".join(unknown_fields))
    if mode == "durable":
        if not state.get("project_root"):
            raise ValueError("durable project_memory_closeout requires project_root")
        required = {"module", "scope", "change_kind", "summary", "reason", "result", "files", "symbols", "decisions", "risks", "supersedes"}
        if not required.issubset(intent) or not isinstance(intent.get("files"), list) or not intent["files"]:
            raise ValueError("verification plan durable project_memory_closeout is incomplete")
        if intent["scope"] not in PROJECT_MEMORY_SCOPES or intent["change_kind"] not in PROJECT_MEMORY_CHANGE_KINDS:
            raise ValueError("verification plan durable project_memory_closeout has invalid scope or change_kind")
        for field in ("module", "summary", "reason", "result"):
            if not isinstance(intent[field], str) or _sanitized_memory_line(intent[field], f"project_memory_closeout.{field}") != intent[field]:
                raise ValueError(f"verification plan project_memory_closeout.{field} is not sanitized")
        for field, maximum in (("symbols", 240), ("decisions", 600), ("risks", 600)):
            values = intent[field]
            if not isinstance(values, list) or any(not isinstance(value, str) or _sanitized_memory_line(value, f"project_memory_closeout.{field}", max_length=maximum) != value for value in values):
                raise ValueError(f"verification plan project_memory_closeout.{field} is not sanitized")
        if intent["scope"] == "code" and not intent["symbols"]:
            raise ValueError("verification plan code project_memory_closeout requires a symbol")
        normalized_files = _normalize_files(state.get("project_root"), intent["files"])
        if normalized_files != intent["files"]:
            raise ValueError("verification plan project_memory_closeout.files is not normalized")
        if not isinstance(intent["supersedes"], str) or _single_line(intent["supersedes"], "project_memory_closeout.supersedes", required=False, max_length=120) != intent["supersedes"]:
            raise ValueError("verification plan project_memory_closeout.supersedes is not sanitized")
    return intent


def _memory_consistency_file(state, consistency_file):
    if not consistency_file:
        return None
    path = Path(consistency_file).expanduser()
    root_value = state.get("project_root") or state.get("cwd")
    root = Path(root_value).expanduser().resolve() if root_value else Path.cwd().resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("memory consistency file must stay inside the lifecycle project root") from error
    return resolved


def _validated_memory_consistency(state, event_name, consistency_file):
    intent = _project_memory_intent(state)
    if intent["mode"] == "none":
        if consistency_file:
            raise ValueError("project_memory_closeout mode=none must not receive a memory consistency file")
        return {"mode": "none", "status": "not-applicable", "written": False}
    path = _memory_consistency_file(state, consistency_file)
    if path is None or not path.is_file():
        raise ValueError("durable project_memory_closeout requires a memory consistency file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("memory consistency file is not readable JSON") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("memory consistency file requires schema_version=1")
    allowed_fields = {"schema_version", "classification", "action", "process_status", "execution_status", "memory_status", "evidence", "supersedes", "record_id"}
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ValueError("memory consistency file contains unknown fields: " + ", ".join(unknown_fields))
    classification = _single_line(payload.get("classification"), "memory_consistency.classification", max_length=80)
    action = _single_line(payload.get("action"), "memory_consistency.action", max_length=80)
    process_status = _single_line(payload.get("process_status"), "memory_consistency.process_status", max_length=40)
    execution_status = _single_line(payload.get("execution_status"), "memory_consistency.execution_status", max_length=40)
    memory_status = _single_line(payload.get("memory_status"), "memory_consistency.memory_status", max_length=40)
    if classification not in PROJECT_MEMORY_CLASSIFICATIONS or action not in PROJECT_MEMORY_ACTIONS:
        raise ValueError("memory consistency classification or action is invalid")
    if process_status not in CONSISTENCY_STATUS_VALUES or execution_status not in CONSISTENCY_STATUS_VALUES or memory_status not in PROJECT_MEMORY_STATUS_VALUES:
        raise ValueError("memory consistency status is invalid")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence or len(evidence) > 20:
        raise ValueError("memory consistency evidence must be a bounded non-empty list")
    normalized_evidence = [_sanitized_memory_line(value, "memory_consistency.evidence", max_length=600) for value in evidence]
    if normalized_evidence != evidence:
        raise ValueError("memory consistency evidence must already be sanitized")
    rule = PROJECT_MEMORY_CLASSIFICATION_RULES[classification]
    if event_name != rule["event"]:
        raise ValueError(f"{classification} requires terminal event {rule['event']}")
    if action != rule["action"]:
        raise ValueError(f"{classification} requires action {rule['action']}")
    for field, observed in (("process_status", process_status), ("execution_status", execution_status), ("memory_status", memory_status)):
        expected = rule.get(field)
        mismatch = observed not in expected if isinstance(expected, set) else expected is not None and observed != expected
        if mismatch:
            raise ValueError(f"{classification} requires {field}={expected}")
    if classification == "insufficient_evidence" and "unavailable" not in {process_status, execution_status, memory_status}:
        raise ValueError("insufficient_evidence requires an unavailable status")
    supersedes = _single_line(payload.get("supersedes"), "memory_consistency.supersedes", required=False, max_length=120)
    record_id = _single_line(payload.get("record_id"), "memory_consistency.record_id", required=False, max_length=120)
    if classification == "memory_record_defect" and not supersedes:
        raise ValueError("memory_record_defect requires supersedes")
    if classification == "memory_projection_defect" and not record_id:
        raise ValueError("memory_projection_defect requires record_id")
    root = Path(state.get("project_root") or state.get("cwd")).expanduser().resolve()
    return {"mode": "durable", "status": "validated", "classification": classification, "action": action, "process_status": process_status, "execution_status": execution_status, "memory_status": memory_status, "evidence": normalized_evidence, "supersedes": supersedes, "record_id": record_id, "source": path.relative_to(root).as_posix(), "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _projection_read_back(result, record_id):
    if not isinstance(result, dict):
        return False
    projection = result.get("projection") if isinstance(result.get("projection"), dict) else {}
    obsidian = result.get("obsidian") if isinstance(result.get("obsidian"), dict) else {}
    if projection.get("record_id") in {None, "", record_id} and projection.get("read_back_verified") is True:
        return True
    if obsidian.get("read_back_verified") is True:
        return True
    for item in result.get("records", []) if isinstance(result.get("records"), list) else []:
        if isinstance(item, dict) and item.get("record_id") == record_id and _projection_read_back(item, record_id):
            return True
    return False


def _projection_status(result, record_id):
    if not isinstance(result, dict):
        return "missing"
    projection = result.get("projection") if isinstance(result.get("projection"), dict) else {}
    if projection.get("record_id") in {None, "", record_id} and projection.get("status"):
        return projection["status"]
    for item in result.get("records", []) if isinstance(result.get("records"), list) else []:
        if isinstance(item, dict) and item.get("record_id") == record_id:
            nested = _projection_status(item, record_id)
            if nested != "missing":
                return nested
    return "missing"


def _record_project_memory_closeout(state, event_name, consistency_file):
    consistency = _validated_memory_consistency(state, event_name, consistency_file)
    if consistency["mode"] == "none":
        return consistency
    if event_name != "pass":
        return {**consistency, "status": "origin-repair-required" if event_name == "fail" else "blocked", "written": False}
    intent = _project_memory_intent(state)
    memory = _load_project_memory_module()
    if consistency["action"] == "reconcile":
        result = memory.reconcile_projections(state["project_root"], record_id=consistency["record_id"])
        record_id = consistency["record_id"]
    else:
        supersedes = consistency["supersedes"] if consistency["action"] == "correction" else ""
        result = memory.record_change(state["project_root"], intent["module"], intent["scope"], intent["change_kind"], intent["summary"], intent["reason"], intent["result"], "passed", intent["files"], consistency["evidence"], intent.get("decisions", []), intent.get("risks", []), supersedes, symbols=intent.get("symbols", []))
        record_id = result.get("record_id") if isinstance(result, dict) else ""
    if not record_id:
        raise ValueError("project-memory closeout did not return a record_id")
    search = memory.search_records(state["project_root"], intent["module"], intent["files"], "", 25, include_ambiguous=True, include_superseded=True, symbols=intent.get("symbols", []))
    read_back = next((match for match in search.get("matches", []) if match.get("id") == record_id), None)
    if not isinstance(read_back, dict):
        raise ValueError("project-memory closeout local readback failed")
    if read_back.get("effective") is False:
        raise ValueError("project-memory closeout readback is superseded")
    obsidian_read_back = _projection_read_back(result, record_id) or _projection_read_back(read_back, record_id)
    projection_status = _projection_status(result, record_id)
    if projection_status == "missing":
        projection_status = _projection_status(read_back, record_id)
    if not obsidian_read_back and projection_status != "unavailable":
        raise ValueError("project-memory closeout Obsidian readback failed")
    closeout_status = "verified" if obsidian_read_back else "projection-pending"
    return {**consistency, "status": closeout_status, "written": consistency["action"] in {"record", "correction"}, "record_id": record_id, "local_read_back_verified": True, "obsidian_read_back_verified": obsidian_read_back, "projection_status": projection_status, "projection_pending": not obsidian_read_back, "memory_result_status": result.get("status"), "read_back_effective": read_back.get("effective", True)}


def _record_personal_memory_candidates(state, event_name, candidate_file):
    if event_name not in TERMINAL_EVENTS or not candidate_file:
        return {"status": "no-candidates", "written": False, "candidates": 0}
    path = _memory_candidate_file(state, candidate_file)
    if not path or not path.is_file():
        return {"status": "no-candidates", "written": False, "candidates": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    memory = _load_personal_memory_module()
    verification_status = {"pass": "passed", "fail": "partial", "blocked": "partial"}[event_name]
    module = _routing_slug(state.get("module") or state.get("ending_check_id") or "ending-memory", "ending-memory")
    return memory.capture(candidates, project="Global Preferences", module=module, verification_status=verification_status)


def _record_bound_model_result(binding, real_status, failure_class, outcome_reason="", verification_count=0, *, ending_attempt_number=1, prior_quality_failure_count=0, prior_operational_failure_count=0):
    receipt_path = Path(binding["receipt_path"])
    if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != binding["receipt_sha256"]:
        raise ValueError("bound producer receipt changed after lifecycle start")
    context = binding["model_learning_context"]
    memory = _load_model_memory_module()
    return memory.record_model_result(context["project_root"], context["task_type"], context["module"], receipt_path, real_status, failure_class, file_value=context["file"], symbol=context["symbol"], code_kind=context["code_kind"], operation=context["operation"], modality=context["modality"], complexity=context["complexity"], complexity_score=context["complexity_score"], risk=context["risk"], ambiguity=context["ambiguity"], task_summary=context["task_summary"], step_kind=context.get("step_kind", ""), capability_tags=context.get("capability_tags"), entry_model=context.get("entry_model", ""), entry_effort=context.get("entry_effort", ""), bound_receipt=binding, outcome_reason=outcome_reason, verification_count=verification_count, ending_attempt_number=ending_attempt_number, prior_quality_failure_count=prior_quality_failure_count, prior_operational_failure_count=prior_operational_failure_count)


def _routing_slug(value, fallback):
    normalized = re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().lower()).strip("-._")
    return normalized[:80] if normalized else fallback


def _record_unbound_model_observation(state, real_status, failure_class, outcome_reason="", verification_count=0, *, ending_attempt_number=1, prior_quality_failure_count=0, prior_operational_failure_count=0):
    project_root = state.get("project_root")
    pair = state.get("selected_pair")
    if not project_root or not pair:
        return None
    score = state.get("complexity_score") if isinstance(state.get("complexity_score"), int) else 50
    disclosure = state.get("model_disclosure") if isinstance(state.get("model_disclosure"), dict) else {}
    model_evidence = disclosure.get("model_evidence")
    if model_evidence not in {"verified_entry", "task_assignment", "configured_selection"}:
        model_evidence = "task_assignment"
    memory = _load_model_memory_module()
    return memory.record_model_observation(
        project_root,
        _routing_slug(state.get("task_kind"), "verification"),
        _single_line(state.get("module") or state.get("ending_check_id") or "ending-verification", "module", max_length=160),
        pair,
        real_status,
        failure_class,
        observation_id=state["lifecycle_id"],
        file_value=(state.get("files") or [""])[0],
        symbol=state.get("symbol", ""),
        code_kind="general",
        operation="verify",
        modality="text",
        complexity="complex" if score >= 50 else "easy",
        complexity_score=score,
        risk="low",
        ambiguity="low",
        task_summary=_single_line(state.get("summary"), "task_summary", required=False, max_length=280),
        step_kind="verification",
        capability_tags=["local-test"],
        model_evidence=model_evidence,
        outcome_reason=outcome_reason,
        verification_count=verification_count,
        ending_attempt_number=ending_attempt_number,
        prior_quality_failure_count=prior_quality_failure_count,
        prior_operational_failure_count=prior_operational_failure_count,
    )


def _successful_model_learning_noop(result):
    return isinstance(result, dict) and result.get("status") == "no-op" and result.get("written") is False and result.get("reason") == "unregistered_or_missing_broad_model_switch"


def _root_lifecycle(store, state):
    current = state
    visited = {current["lifecycle_id"]}
    while current.get("repair_of_lifecycle_id"):
        current = _read_state(store, current["repair_of_lifecycle_id"])
        if current["lifecycle_id"] in visited:
            raise ValueError("repair lifecycle topology contains a cycle")
        visited.add(current["lifecycle_id"])
    return current


def _root_descendants(store, root):
    states = []
    for path in sorted((store / "lifecycles").glob("*.json")):
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["lifecycle_id"] != root["lifecycle_id"] and _root_lifecycle(store, state)["lifecycle_id"] == root["lifecycle_id"]:
            states.append(state)
    return sorted(states, key=lambda state: (state.get("created_at", ""), state["lifecycle_id"]))


def _has_limit_block(state):
    return any(event.get("event") == "blocked" and event.get("error_fingerprint") == "repair-attempt-limit-exceeded" for event in state.get("events", []))


def _normalize_root_attempts(store, root, descendants, repair_limit):
    for index, descendant in enumerate(descendants, start=1):
        changed = descendant.get("attempt_index") != index or descendant.get("max_repair_attempts") != repair_limit
        if changed:
            descendant["attempt_index"] = index
            descendant["max_repair_attempts"] = repair_limit
            _write_state(store, descendant)


def _terminal_event(state):
    return next((event for event in reversed(state.get("events", [])) if event.get("event") in TERMINAL_EVENTS), None)


def _state_pair(state):
    learning = state.get("model_learning") if isinstance(state.get("model_learning"), dict) else {}
    binding = state.get("producer_binding") if isinstance(state.get("producer_binding"), dict) else {}
    disclosure = state.get("model_disclosure") if isinstance(state.get("model_disclosure"), dict) else {}
    return learning.get("pair") or binding.get("effective_pair") or disclosure.get("current_pair") or state.get("selected_pair") or UNKNOWN_MODEL_PAIR


def _attempt_context(store, state):
    root = _root_lifecycle(store, state)
    chain = [root, *_root_descendants(store, root)]
    chain = [state if item.get("lifecycle_id") == state.get("lifecycle_id") else item for item in chain]
    attempt_number = int(state.get("attempt_index", 0)) + 1
    prior = [item for item in chain if int(item.get("attempt_index", 0)) < int(state.get("attempt_index", 0))]
    prior_events = [(item, _terminal_event(item)) for item in prior]
    prior_events = [(item, event) for item, event in prior_events if event]
    prior_quality = sum(event.get("event") == "fail" and event.get("failure_class") in QUALITY_FAILURES for _, event in prior_events)
    prior_operational = sum(event.get("event") == "fail" and event.get("failure_class") in OPERATIONAL_FAILURES for _, event in prior_events)
    attempts = [
        {
            "attempt": int(item.get("attempt_index", 0)) + 1,
            "lifecycle_id": item.get("lifecycle_id"),
            "status": event.get("event"),
            "failure_class": event.get("failure_class") or "none",
            "pair": _state_pair(item),
        }
        for item, event in prior_events
    ]
    return {
        "attempt_number": attempt_number,
        "prior_quality_failure_count": prior_quality,
        "prior_operational_failure_count": prior_operational,
        "initial_pair": _state_pair(root),
        "attempt_chain": attempts,
    }


def _model_assessment(state, event_name, failure_class, model_learning, attempt_context):
    learning = model_learning if isinstance(model_learning, dict) else {}
    binding = state.get("producer_binding") if isinstance(state.get("producer_binding"), dict) else {}
    has_producer = bool(binding)
    attempt_number = attempt_context["attempt_number"]
    producer_pair = binding.get("effective_pair") or UNKNOWN_MODEL_PAIR
    model_record_pair = learning.get("pair") or producer_pair
    ending_pair = state.get("selected_pair") or UNKNOWN_MODEL_PAIR
    next_pair = (learning.get("next_pair") or producer_pair) if has_producer else UNKNOWN_MODEL_PAIR
    prior_quality = attempt_context["prior_quality_failure_count"]
    prior_operational = attempt_context["prior_operational_failure_count"]
    quality_failures = prior_quality + int(event_name == "fail" and failure_class in QUALITY_FAILURES)
    operational_failures = prior_operational + int(event_name == "fail" and failure_class in OPERATIONAL_FAILURES)
    if event_name == "pass" and attempt_number == 1:
        pass_shape = "first_attempt_pass"
        if learning.get("next_pair_direction") == "downgrade" and next_pair != producer_pair:
            suitability = "producer_suitable_downgrade_candidate"
            routing_action = "producer_trial_downgrade_one_rung_next_matching_task"
            reason = "The first Ending attempt passed; accumulated matching Real PASS evidence reached the one-rung downgrade threshold."
        else:
            suitability = "producer_suitable"
            routing_action = "producer_retain_until_second_matching_first_pass"
            reason = "The first Ending attempt passed; retain this pair until the matching Real PASS threshold supports a one-rung trial."
    elif event_name == "pass" and prior_quality:
        pass_shape = "retry_pass"
        suitability = "producer_recovered_after_quality_repair"
        routing_action = "reuse_lowest_successful_producer_recovery_pair"
        reason = "A prior correctness or quality check failed and this retry passed; keep the lowest producer pair that produced the verified recovery. The Ending pair does not change."
    elif event_name == "pass":
        pass_shape = "retry_pass"
        suitability = "producer_suitable_after_operational_recovery"
        routing_action = "producer_retain_quality_boundary"
        reason = "The retry passed after an operational interruption; the interruption is quality-neutral."
    elif event_name == "fail" and failure_class in QUALITY_FAILURES:
        pass_shape = "failed_attempt"
        suitability = "producer_result_failed_quality_check"
        routing_action = "repair_producer_with_recorded_next_pair"
        reason = "The real check found a correctness or quality defect in the producer result. Producer learning may select a repair pair; the fixed Ending pair never upgrades from this failure."
    elif event_name == "fail":
        pass_shape = "failed_attempt"
        suitability = "producer_quality_unproven_operational_failure"
        routing_action = "producer_retry_without_quality_penalty"
        reason = "The check failed operationally, so producer quality is not downgraded or upgraded and the fixed Ending pair does not change."
    else:
        pass_shape = "blocked"
        suitability = "producer_unproven"
        routing_action = "producer_none_until_blocker_clears"
        reason = "The Ending check was blocked before a quality verdict was available."
    if has_producer:
        suitability = learning.get("model_suitability") or suitability
        routing_action = learning.get("routing_action") or routing_action
    else:
        suitability = "producer_unavailable_verifier_observation_only"
        routing_action = "no_producer_route_movement"
        next_pair = UNKNOWN_MODEL_PAIR
    ending_assignment = state.get("ending_model_assignment") if isinstance(state.get("ending_model_assignment"), dict) else {}
    availability_reason = state.get("availability_fallback_reason")
    ending_is_fallback = bool(availability_reason and ending_pair == ending_assignment.get("availability_fallback_pair"))
    if ending_pair == UNKNOWN_MODEL_PAIR:
        ending_suitability = "ending_pair_unassigned"
        ending_routing_action = "no_ending_route_assignment"
    else:
        ending_suitability = "availability_fallback_closeout" if ending_is_fallback else "fixed_fast_closeout"
        ending_routing_action = "availability_fallback_only" if ending_is_fallback else "retain_fixed_fast_ending_pair"
    current_attempt = {
        "attempt": attempt_number,
        "lifecycle_id": state.get("lifecycle_id"),
        "status": event_name,
        "failure_class": failure_class if event_name == "fail" else "none",
        "pair": producer_pair if producer_pair != UNKNOWN_MODEL_PAIR else ending_pair,
        "pair_role": "producer" if producer_pair != UNKNOWN_MODEL_PAIR else "ending_observation",
    }
    task_context = binding.get("model_learning_context") if isinstance(binding.get("model_learning_context"), dict) else {}
    return {
        "task_complexity_score": task_context.get("complexity_score"),
        "task_complexity_band": task_context.get("complexity_band"),
        "ending_complexity_score": state.get("complexity_score"),
        "ending_complexity_band": state.get("complexity_band"),
        "producer_pair": producer_pair,
        "ending_pair": ending_pair,
        "ending_primary_pair": ending_assignment.get("primary_pair"),
        "ending_availability_fallback_pair": ending_assignment.get("availability_fallback_pair"),
        "ending_availability_fallback_reason": availability_reason,
        "ending_model_suitability": ending_suitability,
        "ending_routing_action": ending_routing_action,
        "model_record_pair": model_record_pair,
        "initial_pair": attempt_context["initial_pair"],
        "attempt_count": attempt_number,
        "pass_attempt_number": attempt_number if event_name == "pass" else None,
        "pass_shape": pass_shape,
        "quality_failure_count": quality_failures,
        "operational_failure_count": operational_failures,
        "model_suitability": suitability,
        "routing_action": routing_action,
        "next_pair": next_pair,
        "producer_model_suitability": suitability,
        "producer_routing_action": routing_action,
        "producer_next_pair": next_pair,
        "recovery_from_pair": learning.get("recovery_from_pair"),
        "matched_pass_count_after": learning.get("matched_pass_count_after"),
        "minimum_passes_before_downgrade": learning.get("minimum_passes_before_downgrade"),
        "reason": reason,
        "attempt_chain": [*attempt_context["attempt_chain"], current_attempt],
        "model_record_status": learning.get("obsidian", {}).get("status") if isinstance(learning.get("obsidian"), dict) else learning.get("status") or "unavailable",
        "model_record_document": learning.get("model_record_document"),
        "model_record_link": learning.get("model_record_link"),
        "model_switch_document": learning.get("model_switch_document"),
        "model_switch_link": learning.get("model_switch_link"),
    }


def _repair_evidence(event):
    evidence = list(event.get("verification", []))
    project_memory = event.get("project_memory") if isinstance(event.get("project_memory"), dict) else {}
    evidence.extend(project_memory.get("evidence", []) if isinstance(project_memory.get("evidence"), list) else [])
    return list(dict.fromkeys(evidence))


def _repair_prompt(state, event):
    project_root = Path(state["project_root"]).expanduser().resolve() if state.get("project_root") else None
    plan_text = "the saved verification plan"
    if project_root and state.get("verification_plan"):
        try:
            plan_text = Path(state["verification_plan"]).expanduser().resolve().relative_to(project_root).as_posix()
        except ValueError:
            plan_text = "the saved verification plan"
    failure_class = event.get("failure_class") or "correctness"
    error_fingerprint = event.get("error_fingerprint") or "not-supplied"
    project_memory = event.get("project_memory") if isinstance(event.get("project_memory"), dict) else {}
    consistency_class = project_memory.get("classification")
    if consistency_class == "skill_contract_defect":
        failure_instruction = "Fresh execution evidence conflicts with the active Skill/process contract. Repair the smallest authorized Skill producer path; the Ending verifier must not edit it."
    elif consistency_class == "execution_drift":
        failure_instruction = "The active Skill/process contract is correct but the producer execution drifted from it. Repair the result in this exact origin session; do not rewrite result memory to hide the drift."
    elif error_fingerprint == "acceptance-mismatch" or failure_class in QUALITY_FAILURES:
        failure_instruction = "The final result is incorrect or differs from the original user request. Compare the delivered result and the original request before changing anything, even if the command exited successfully."
    elif failure_class == "timeout":
        failure_instruction = "The real check timed out. Determine whether the timeout is caused by the changed result or the verification environment, then repair only the result when the evidence supports it."
    else:
        failure_instruction = "The real check did not meet its expected runtime result. Inspect the exact evidence and repair the result only when the evidence identifies a producer defect."
    evidence_text = "\n".join(f"- {value}" for value in _repair_evidence(event)) or "- No additional verification text was supplied."
    evidence_text = evidence_text[:2400]
    files_text = ", ".join(state.get("files") or ["the files authorized by the original result task"])
    next_attempt = int(state.get("attempt_index", 0)) + 1
    max_attempts = int(state.get("max_repair_attempts", DEFAULT_MAX_REPAIR_ATTEMPTS))
    origin = state.get("origin_session") or {}
    return "\n".join(["ENDING_REPAIR_REQUEST", "Continue in this original source session; do not create a separate repair session or let the Ending verifier edit the target.", f"Original task: {state['summary']}", "Read the original user request and the current delivered result in this session before choosing the repair.", f"Acceptance check: {state.get('ending_check_id') or 'the same saved Ending check'}", f"Verification plan relative to project root: {plan_text}", f"Project binding id: {state.get('project_id') or 'resolve the exact saved project before launching the next Ending'}", f"Origin session thread id: {origin.get('thread_id') or 'current source session'}", f"Origin session host id: {origin.get('host_id') or 'current source session host'}", f"Repair attempt to run: {next_attempt} of {max_attempts}", f"Failure class: {failure_class}", f"Error fingerprint: {error_fingerprint}", f"Failure meaning: {failure_instruction}", "Observed evidence:", evidence_text, f"Authorized result files: {files_text}", "Required actions:", "1. Compare the current result with the original user request and the acceptance contract; if the result still differs, fix the smallest authorized producer path.", "2. Run the producer Quick Check and present the repaired result in this same source session.", f"3. Start a fresh global projectless Ending for the same acceptance check as a child of lifecycle {state['lifecycle_id']} using --repair-of-lifecycle-id; never reuse the failed verdict.", "4. Carry the same project binding only as execution context, create the Ending with exact projectless target, require list_threads projectId=null/absent readback, acknowledge it, and return without waiting for its verdict.", "5. If the repair limit is exhausted or the source session cannot complete the repair, record BLOCKED with the exact evidence; do not claim PASS."])


def _repair_handoff(state, event):
    common = {"repair_of_lifecycle_id": state["lifecycle_id"], "summary": event["summary"], "verification": _repair_evidence(event), "error_fingerprint": event["error_fingerprint"], "failure_class": event["failure_class"], "complexity_score": state.get("complexity_score"), "complexity_band": state.get("complexity_band"), "max_repair_attempts": state.get("max_repair_attempts")}
    origin = state.get("origin_session")
    next_attempt = int(state.get("attempt_index", 0)) + 1
    max_attempts = int(state.get("max_repair_attempts", DEFAULT_MAX_REPAIR_ATTEMPTS))
    if not origin:
        return {**common, "action": "blocked_origin_session_unavailable", "blocked_reason": "Ending automatic repair requires the exact source session thread_id and host_id captured at launch.", "requires_origin_session": True}
    if next_attempt > max_attempts:
        return {**common, "action": "repair_limit_exhausted", "blocked_reason": f"No automatic repair prompt is allowed after {max_attempts} repair attempts.", "requires_origin_session": True, "origin_session": origin}
    prompt = _repair_prompt(state, event)
    dispatch = {"tool": REPAIR_DISPATCH_TOOL, "arguments": {"threadId": origin["thread_id"], "hostId": origin["host_id"], "prompt": prompt}, "required": True}
    return {**common, "action": "send_repair_prompt_to_origin_session_then_fresh_ending", "requires_origin_session": True, "origin_session": origin, "repair_dispatch": dispatch, "repair_prompt": prompt, "next_step": "origin_session_repairs_then_starts_fresh_ending"}


def start_lifecycle(task_kind, cwd, summary, project_root=None, module="", files=None, repair_of_lifecycle_id="", store=DEFAULT_STORE, max_repair_attempts=DEFAULT_MAX_REPAIR_ATTEMPTS, producer_receipt=None, complexity_score=None, complexity_band="", verification_required=False, verification_plan=None, ending_check_id="", selected_pair="", requested_pair="", resolved_pair="", effective_pair="", previous_pair="", model_evidence="", route_change="", switch_summary="", reason="", project_id="", origin_thread_id="", origin_host_id="", symbol="", availability_fallback_reason="", late_repair_reason=""):
    cwd_path = Path(cwd).expanduser().resolve()
    if not cwd_path.is_dir():
        raise ValueError("cwd must be an existing directory")
    producer_binding = _producer_binding(producer_receipt, project_root)
    project_path = Path(project_root).expanduser().resolve() if project_root else None
    if project_path is None and producer_binding:
        project_path = Path(producer_binding["model_learning_context"]["project_root"])
    origin_session = _origin_session(origin_thread_id, origin_host_id)
    project_id_value = _single_line(project_id, "project_id", required=False, max_length=200) or None
    late_repair_reason_value = _single_line(late_repair_reason, "late_repair_reason", required=False, max_length=600)
    if late_repair_reason_value and not repair_of_lifecycle_id:
        raise ValueError("late_repair_reason requires repair_of_lifecycle_id")
    if producer_binding:
        bound_score = producer_binding["model_learning_context"]["complexity_score"]
        bound_band = producer_binding["model_learning_context"]["complexity_band"]
        if complexity_score is None:
            complexity_score = bound_score
            complexity_band = bound_band
    if complexity_score is not None:
        if isinstance(complexity_score, bool) or not 0 <= complexity_score <= 100:
            raise ValueError("complexity_score must be an integer from 0 to 100")
        expected_band = "small" if complexity_score <= 24 else "standard" if complexity_score <= 49 else "complex" if complexity_score <= 74 else "advanced"
        if complexity_band and complexity_band != expected_band:
            raise ValueError("complexity_band does not match complexity_score")
        complexity_band = expected_band
    normalized_files = _normalize_files(project_path, files or [])
    bound_symbol = producer_binding.get("model_learning_context", {}).get("symbol", "") if producer_binding else ""
    normalized_symbol = _single_line(symbol or bound_symbol, "symbol", required=False, max_length=600)
    lifecycle_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:12]}"
    created_at = _now()
    store_path = Path(store).expanduser().resolve()
    store_path.mkdir(parents=True, exist_ok=True)
    lock_path = store_path / ".lock"
    with _exclusive_file_lock(lock_path):
        parent = None
        root = None
        attempt_index = 0
        repair_limit = int(max_repair_attempts)
        if repair_limit < 0 or repair_limit > 10:
            raise ValueError("max_repair_attempts must be between 0 and 10")
        if repair_of_lifecycle_id:
            parent = _read_state(store_path, repair_of_lifecycle_id)
            if _has_limit_block(parent):
                raise ValueError("repair lifecycle requires a failed parent lifecycle or non-limit blocked parent lifecycle")
            if parent["status"] not in {"failed", "blocked"}:
                if parent["status"] != "passed" or not late_repair_reason_value:
                    raise ValueError("repair lifecycle requires a failed parent lifecycle or non-limit blocked parent lifecycle; a passed parent requires a non-empty late_repair_reason")
            elif late_repair_reason_value:
                raise ValueError("late_repair_reason is only allowed for a passed parent lifecycle")
            root = _root_lifecycle(store_path, parent)
            repair_limit = int(root.get("max_repair_attempts", DEFAULT_MAX_REPAIR_ATTEMPTS))
            descendants = _root_descendants(store_path, root)
            _normalize_root_attempts(store_path, root, descendants, repair_limit)
            attempt_index = len(descendants) + 1
            if attempt_index > repair_limit:
                blocked_at = _now()
                blocked_event = {"schema_version": SCHEMA_VERSION, "event": "blocked", "recorded_at": blocked_at, "lifecycle_id": root["lifecycle_id"], "summary": f"Repair attempt limit exhausted at {repair_limit}", "verification": [], "error_fingerprint": "repair-attempt-limit-exceeded"}
                if not _has_limit_block(root):
                    root["events"].append(blocked_event)
                    root["updated_at"] = blocked_at
                    root["status"] = "blocked"
                    _write_state(store_path, root)
                    _append_event(store_path, blocked_event)
                raise ValueError("repair attempt limit exceeded")
            parent_origin = parent.get("origin_session")
            if parent_origin and origin_session and parent_origin != origin_session:
                raise ValueError("repair lifecycle must preserve the origin session")
            origin_session = origin_session or parent_origin
            project_id_value = project_id_value or parent.get("project_id")
            if project_path is None and parent.get("project_root"):
                project_path = Path(parent["project_root"]).expanduser().resolve()
            verification_required = bool(verification_required or parent.get("verification_required"))
            verification_plan = verification_plan or parent.get("verification_plan")
            ending_check_id = ending_check_id or parent.get("ending_check_id") or ""
            selected_pair = selected_pair or parent.get("selected_pair") or ""
            availability_fallback_reason = availability_fallback_reason or parent.get("availability_fallback_reason") or ""
        if origin_session and not project_path:
            raise ValueError("origin session requires project_root")
        if origin_session and not project_id_value:
            raise ValueError("origin session requires project_id")
        verification_plan_path = Path(verification_plan).expanduser().resolve() if verification_plan else None
        if verification_required and (not verification_plan_path or not verification_plan_path.is_file()):
            raise ValueError("verification-required lifecycle requires an existing verification plan")
        project_memory_closeout = {"mode": "none"}
        if verification_plan_path:
            plan_payload = json.loads(verification_plan_path.read_text(encoding="utf-8"))
            candidate_closeout = plan_payload.get("project_memory_closeout", {"mode": "none"}) if isinstance(plan_payload, dict) else {"mode": "none"}
            if not isinstance(candidate_closeout, dict) or candidate_closeout.get("mode", "none") not in {"none", "durable"}:
                raise ValueError("verification plan project_memory_closeout is invalid")
            project_memory_closeout = _project_memory_intent({"project_memory_closeout": candidate_closeout, "project_root": str(project_path) if project_path else None})
        ending_assignment = None
        if verification_plan_path and selected_pair:
            ending_assignment = _ending_plan_assignment(verification_plan_path, ending_check_id, selected_pair, availability_fallback_reason)
        if ending_assignment and ending_assignment.get("availability_fallback_reason"):
            requested_pair = requested_pair or ending_assignment["primary_pair"]
            resolved_pair = resolved_pair or ending_assignment["primary_pair"]
            effective_pair = effective_pair or selected_pair
            previous_pair = previous_pair or ending_assignment["primary_pair"]
            model_evidence = model_evidence or "task_assignment"
            route_change = route_change or "operational_fallback"
            switch_summary = switch_summary or f"Availability fallback from {ending_assignment['primary_pair']} to {selected_pair}."
            reason = reason or f"Ending primary pair was unavailable: {ending_assignment['availability_fallback_reason']}."
        elif ending_assignment and ending_assignment.get("primary_selection_reason"):
            model_evidence = model_evidence or "configured_selection"
            reason = reason or f"Ending registry selected its primary pair: {ending_assignment['primary_selection_reason']}."
        ending_owns_model_identity = bool(selected_pair and (verification_required or ending_check_id))
        model_disclosure = _model_disclosure(selected_pair, None if ending_owns_model_identity else producer_binding, requested_pair, resolved_pair, effective_pair, previous_pair, model_evidence, route_change, switch_summary, reason)
        fallback_reason_value = ending_assignment.get("availability_fallback_reason") if ending_assignment else None
        event = {"schema_version": SCHEMA_VERSION, "event": "started", "recorded_at": created_at, "lifecycle_id": lifecycle_id, "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "late_repair_reason": late_repair_reason_value or None, "summary": _single_line(summary, "summary"), "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": _single_line(ending_check_id, "ending_check_id", required=False, max_length=80) or None, "selected_pair": _model_pair(selected_pair, "selected_pair"), "availability_fallback_reason": fallback_reason_value, "ending_model_assignment": ending_assignment, "model_disclosure": model_disclosure}
        state = {"schema_version": SCHEMA_VERSION, "lifecycle_id": lifecycle_id, "created_at": created_at, "updated_at": created_at, "status": "running", "task_kind": _single_line(task_kind, "task_kind", max_length=80), "cwd": str(cwd_path), "summary": event["summary"], "project_root": str(project_path) if project_path else None, "project_id": project_id_value, "origin_session": origin_session, "module": _single_line(module, "module", required=False, max_length=160), "symbol": normalized_symbol, "files": normalized_files, "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": event["ending_check_id"], "selected_pair": event["selected_pair"], "availability_fallback_reason": fallback_reason_value, "ending_model_assignment": ending_assignment, "model_disclosure": model_disclosure, "project_memory_closeout": project_memory_closeout, "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "late_repair_reason": late_repair_reason_value or None, "attempt_index": attempt_index, "max_repair_attempts": repair_limit, "repair_children": [], "producer_binding": producer_binding, "events": [event]}
        if parent:
            parent_event = {"schema_version": SCHEMA_VERSION, "event": "post_pass_repair_started" if late_repair_reason_value else "repair_started", "recorded_at": created_at, "lifecycle_id": parent["lifecycle_id"], "child_lifecycle_id": lifecycle_id, "late_repair_reason": late_repair_reason_value or None, "summary": f"Post-pass repair lifecycle {lifecycle_id} started" if late_repair_reason_value else f"Repair lifecycle {lifecycle_id} started"}
            parent["repair_children"].append(lifecycle_id)
            parent["events"].append(parent_event)
            parent["updated_at"] = created_at
            _write_state(store_path, parent)
            _append_event(store_path, parent_event)
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
    return {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": "running", "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": event["ending_check_id"], "selected_pair": event["selected_pair"], "availability_fallback_reason": fallback_reason_value, "late_repair_reason": late_repair_reason_value or None, "ending_model_assignment": ending_assignment, "model_disclosure": model_disclosure, "project_id": project_id_value, "origin_session": origin_session, "local": {"written": True, "store": str(store_path), "state": str(state_path)}}


def record_event(lifecycle_id, event_name, summary, verification=None, error_fingerprint="", store=DEFAULT_STORE, failure_class="none", memory_candidates_file=None, memory_consistency_file=None):
    if event_name not in ALL_EVENTS:
        raise ValueError(f"event must be one of {', '.join(sorted(ALL_EVENTS))}")
    if failure_class not in FAILURE_CLASSES:
        raise ValueError(f"failure_class must be one of {', '.join(sorted(FAILURE_CLASSES))}")
    store_path = Path(store).expanduser().resolve()
    lock_path = store_path / ".lock"
    with _exclusive_file_lock(lock_path):
        state = _read_state(store_path, lifecycle_id)
        if state["status"] != "running" and event_name != "note":
            prior_terminal = next((item for item in reversed(state["events"]) if item.get("event") in TERMINAL_EVENTS), None)
            if prior_terminal and prior_terminal.get("event") == event_name and prior_terminal.get("failure_class", "none") == failure_class:
                return {"status": "duplicate", "lifecycle_id": lifecycle_id, "lifecycle_status": state["status"], "model_learning": state.get("model_learning"), "personal_memory": state.get("personal_memory"), "project_memory": state.get("project_memory"), "local": {"written": True, "store": str(store_path), "state": str(_state_path(store_path, lifecycle_id))}}
            raise ValueError(f"lifecycle is already terminal: {state['status']}")
        project_memory_mode = _project_memory_intent(state)["mode"]
        if event_name == "pass" and project_memory_mode == "durable" and failure_class != "none":
            raise ValueError("a durable Ending pass requires failure_class=none")
        if event_name == "fail" and project_memory_mode == "durable" and failure_class == "none":
            raise ValueError("a durable Ending fail requires an explicit failure_class")
        project_memory = _record_project_memory_closeout(state, event_name, memory_consistency_file) if event_name in TERMINAL_EVENTS else None
        binding = state.get("producer_binding")
        model_learning = None
        attempt_context = _attempt_context(store_path, state)
        if binding and event_name in {"pass", "fail"}:
            if event_name == "pass" and failure_class != "none":
                raise ValueError("a bound Ending pass requires failure_class=none")
            if event_name == "fail" and failure_class == "none":
                raise ValueError("a bound Ending fail requires an explicit failure_class")
            model_learning = _record_bound_model_result(binding, event_name, failure_class, _single_line(summary, "summary", max_length=280), len(verification or []), ending_attempt_number=attempt_context["attempt_number"], prior_quality_failure_count=attempt_context["prior_quality_failure_count"], prior_operational_failure_count=attempt_context["prior_operational_failure_count"])
            state["model_learning"] = model_learning
            state["producer_binding"]["status"] = "no-op" if _successful_model_learning_noop(model_learning) else "recorded" if model_learning.get("written") is True else "unavailable"
        elif event_name in TERMINAL_EVENTS and state.get("project_root") and state.get("selected_pair"):
            model_learning = _record_unbound_model_observation(state, event_name, failure_class, _single_line(summary, "summary", max_length=280), len(verification or []), ending_attempt_number=attempt_context["attempt_number"], prior_quality_failure_count=attempt_context["prior_quality_failure_count"], prior_operational_failure_count=attempt_context["prior_operational_failure_count"])
            if model_learning is not None:
                state["model_learning"] = model_learning
        recorded_at = _now()
        event = {"schema_version": SCHEMA_VERSION, "event": event_name, "recorded_at": recorded_at, "lifecycle_id": lifecycle_id, "summary": _single_line(summary, "summary"), "verification": [_single_line(value, "verification", max_length=600) for value in (verification or [])], "error_fingerprint": _single_line(error_fingerprint, "error_fingerprint", required=False, max_length=160) or None, "failure_class": failure_class if event_name in {"pass", "fail"} else None, "complexity_score": state.get("complexity_score"), "complexity_band": state.get("complexity_band")}
        model_assessment = _model_assessment(state, event_name, failure_class, model_learning, attempt_context) if event_name in TERMINAL_EVENTS else None
        if model_learning is not None:
            event["model_learning"] = model_learning
            event["switch_direction"] = model_learning.get("switch_direction")
            event["switch_reason"] = model_learning.get("switch_reason")
            event["next_pair"] = model_learning.get("next_pair")
        if model_assessment is not None:
            event["model_assessment"] = model_assessment
            state["model_assessment"] = model_assessment
        if project_memory is not None:
            event["project_memory"] = project_memory
            state["project_memory"] = project_memory
        personal_memory = _record_personal_memory_candidates(state, event_name, memory_candidates_file)
        if event_name in TERMINAL_EVENTS:
            event["personal_memory"] = personal_memory
            state["personal_memory"] = personal_memory
        state["events"].append(event)
        state["updated_at"] = recorded_at
        if event_name in TERMINAL_EVENTS:
            state["status"] = {"pass": "passed", "fail": "failed", "blocked": "blocked"}[event_name]
        repair_handoff = _repair_handoff(state, event) if event_name == "fail" else None
        limit_blocked_event = None
        if repair_handoff is not None:
            event["repair_handoff"] = repair_handoff
            state["repair_handoff"] = repair_handoff
            if repair_handoff.get("action") == "repair_limit_exhausted":
                limit_blocked_event = {"schema_version": SCHEMA_VERSION, "event": "blocked", "recorded_at": recorded_at, "lifecycle_id": lifecycle_id, "summary": f"Repair attempt limit exhausted at {state.get('max_repair_attempts', DEFAULT_MAX_REPAIR_ATTEMPTS)}", "verification": event["verification"], "error_fingerprint": "repair-attempt-limit-exceeded", "failure_class": None, "repair_handoff": repair_handoff}
                state["events"].append(limit_blocked_event)
                state["status"] = "blocked"
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
        if limit_blocked_event is not None:
            _append_event(store_path, limit_blocked_event)
    output = {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": state["status"], "final_gate_passed": event_name == "pass", "local": {"written": True, "store": str(store_path), "state": str(state_path)}}
    if model_learning is not None:
        output["model_learning"] = model_learning
    if model_assessment is not None:
        output["model_assessment"] = model_assessment
    if event_name in TERMINAL_EVENTS:
        output["personal_memory"] = event.get("personal_memory")
        output["project_memory"] = event.get("project_memory")
    if event_name == "fail":
        output["repair_required"] = True
        output["repair_handoff"] = repair_handoff
    return output


def audit_lifecycle(lifecycle_id, store=DEFAULT_STORE):
    store_path = Path(store).expanduser().resolve()
    root = _root_lifecycle(store_path, _read_state(store_path, lifecycle_id))
    descendants = _root_descendants(store_path, root)
    active = descendants[-1] if descendants else root
    if _has_limit_block(root):
        terminal_status = "blocked"
    else:
        terminal_status = active["status"] if active["status"] in {"passed", "blocked"} else "pending"
    chain = [root["lifecycle_id"], *(state["lifecycle_id"] for state in descendants)]
    return {"status": "pass" if terminal_status == "passed" else terminal_status, "root_lifecycle_id": root["lifecycle_id"], "active_lifecycle_id": active["lifecycle_id"], "terminal_status": terminal_status, "complexity_score": active.get("complexity_score"), "complexity_band": active.get("complexity_band"), "selected_pair": active.get("selected_pair"), "availability_fallback_reason": active.get("availability_fallback_reason"), "attempt_count": int(active.get("attempt_index", 0)) + 1, "model_assessment": active.get("model_assessment"), "chain": chain, "descendants": [state["lifecycle_id"] for state in descendants], "final_gate_passed": terminal_status == "passed"}


def main():
    parser = argparse.ArgumentParser(description="Record eligible post-result Ending Task lifecycles")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--task-kind", required=True)
    start_parser.add_argument("--cwd", type=Path, required=True)
    start_parser.add_argument("--summary", required=True)
    start_parser.add_argument("--project-root", type=Path)
    start_parser.add_argument("--module", default="")
    start_parser.add_argument("--file", action="append", default=[])
    start_parser.add_argument("--symbol", default="")
    start_parser.add_argument("--repair-of-lifecycle-id", default="")
    start_parser.add_argument("--max-repair-attempts", type=int, default=DEFAULT_MAX_REPAIR_ATTEMPTS)
    start_parser.add_argument("--producer-receipt", type=Path)
    start_parser.add_argument("--complexity-score", type=int)
    start_parser.add_argument("--complexity-band", choices=("small", "standard", "complex", "advanced"), default="")
    start_parser.add_argument("--verification-required", action="store_true")
    start_parser.add_argument("--verification-plan", type=Path)
    start_parser.add_argument("--ending-check-id", default="")
    start_parser.add_argument("--selected-pair", default="")
    start_parser.add_argument("--requested-pair", default="")
    start_parser.add_argument("--resolved-pair", default="")
    start_parser.add_argument("--effective-pair", default="")
    start_parser.add_argument("--previous-pair", default="")
    start_parser.add_argument("--model-evidence", choices=sorted(MODEL_EVIDENCE_LEVELS), default="")
    start_parser.add_argument("--route-change", choices=sorted(ROUTE_CHANGES), default="")
    start_parser.add_argument("--switch-summary", default="")
    start_parser.add_argument("--reason", default="")
    start_parser.add_argument("--project-id", default="")
    start_parser.add_argument("--origin-thread-id", default="")
    start_parser.add_argument("--origin-host-id", default="")
    start_parser.add_argument("--availability-fallback-reason", choices=sorted(AVAILABILITY_FALLBACK_REASONS), default="")
    start_parser.add_argument("--late-repair-reason", default="")
    event_parser = subparsers.add_parser("event")
    event_parser.add_argument("--lifecycle-id", required=True)
    event_parser.add_argument("--event", choices=sorted(ALL_EVENTS), required=True)
    event_parser.add_argument("--summary", required=True)
    event_parser.add_argument("--verification", action="append", default=[])
    event_parser.add_argument("--error-fingerprint", default="")
    event_parser.add_argument("--failure-class", choices=sorted(FAILURE_CLASSES), default="none")
    event_parser.add_argument("--memory-candidates-file", type=Path)
    event_parser.add_argument("--memory-consistency-file", type=Path)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--lifecycle-id", required=True)
    args = parser.parse_args()
    if args.command == "start":
        output = start_lifecycle(args.task_kind, args.cwd, args.summary, args.project_root, args.module, args.file, args.repair_of_lifecycle_id, args.store, args.max_repair_attempts, args.producer_receipt, args.complexity_score, args.complexity_band, args.verification_required, args.verification_plan, args.ending_check_id, args.selected_pair, args.requested_pair, args.resolved_pair, args.effective_pair, args.previous_pair, args.model_evidence, args.route_change, args.switch_summary, args.reason, args.project_id, args.origin_thread_id, args.origin_host_id, args.symbol, args.availability_fallback_reason, args.late_repair_reason)
    elif args.command == "event":
        output = record_event(args.lifecycle_id, args.event, args.summary, args.verification, args.error_fingerprint, args.store, args.failure_class, args.memory_candidates_file, args.memory_consistency_file)
    else:
        output = audit_lifecycle(args.lifecycle_id, args.store)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("final_gate_passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

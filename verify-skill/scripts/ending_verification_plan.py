#!/usr/bin/env python3
"""Build and execute fast, real-test Ending tasks with fixed model routing."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

if os.name == "nt":
    import msvcrt
else:
    import fcntl

_ENDING_BACKEND_PATH = Path(__file__).with_name("ending_backend.py")
_ENDING_BACKEND_SPEC = importlib.util.spec_from_file_location("ending_verification_backend", _ENDING_BACKEND_PATH)
ending_backend = importlib.util.module_from_spec(_ENDING_BACKEND_SPEC)
_ENDING_BACKEND_SPEC.loader.exec_module(ending_backend)

_ROUTING_POLICY_PATH = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "routing_policy.py"
_ROUTING_POLICY_SPEC = importlib.util.spec_from_file_location("ending_verification_routing_policy", _ROUTING_POLICY_PATH)
_ROUTING_POLICY = importlib.util.module_from_spec(_ROUTING_POLICY_SPEC)
_ROUTING_POLICY_SPEC.loader.exec_module(_ROUTING_POLICY)


SCHEMA_VERSION = 12
ENDING_PRIMARY_PAIR = "gpt-5.3-codex-spark|xhigh"
ENDING_CHECK_WORKER_MARKER = "ENDING_CHECK_WORKER"
DIRECT_CHECK_SURFACES = {"command", "syntax", "unit", "api_state", "file_state"}
DELEGATED_CHECK_SURFACES = {"runtime_semantics", "integration_semantics", "code_quality", "ui_visual", "artifact_visual", "prompt_semantics"}
CHECK_SURFACES = DIRECT_CHECK_SURFACES | DELEGATED_CHECK_SURFACES
DEFAULT_WORKER_SKILLS = {"runtime_semantics": ["verify-skill"], "integration_semantics": ["verify-skill"], "code_quality": ["verify-skill", "code-skill", "cross-platform-execution"], "ui_visual": ["verify-skill", "emil-design-eng"], "artifact_visual": ["verify-skill"], "prompt_semantics": ["verify-skill", "prompt-skill"]}
ENDING_FALLBACK_ROLE = "floor"
ENDING_LAUNCH_ID = "task-ending"
AVAILABILITY_FALLBACK_REASONS = {
    "controller_cooling",
    "primary_model_unavailable",
    "primary_effort_unsupported",
    "primary_pair_not_in_registry",
    "scheduler_unavailable",
    "required_modality_unavailable",
}
THREAD_TARGET = {"type": "projectless"}
TERMINAL_THREAD_POLICY = {"pass": "keep_visible", "fail": "keep_visible", "blocked": "keep_visible"}
CREATE_THREAD_TOOL = "codex_app__create_thread"
THREAD_READBACK_TOOL = "codex_app__list_threads"
THREAD_SCOPE = "global"
CREATE_THREAD_ARGUMENT_KEYS = {"target", "title", "model", "thinking", "prompt"}
THREAD_PLACEMENT_POLICY = {"scope": THREAD_SCOPE, "target": THREAD_TARGET, "expected_project_id": None, "creation_tool": CREATE_THREAD_TOOL, "readback_tool": THREAD_READBACK_TOOL}
REPAIR_LAUNCH_CAPABILITY = "codex_app__create_thread"
REPAIR_RESTRICTION_DEFAULT_SECONDS = 5 * 60 * 60
DEFAULT_CONTROLLER_RESTRICTION_STORE = Path.home() / ".codex" / "ending-runtime" / "controller-restrictions.json"
CONTROLLER_RESTRICTION_REASONS = {"five_hour_limit", "model_quota_limit", "provider_rate_limit", "provider_retry_after"}
CONTROLLER_RESTRICTION_HISTORY_LIMIT = 64
LAUNCH_STATE_SCHEMA_VERSION = 2
LIFECYCLE_ID_PATTERN = re.compile(r"\A\d{8}T\d{6}-[0-9a-f]{12}\Z")
PROJECT_MEMORY_MODES = {"none", "durable"}
PROJECT_MEMORY_SCOPES = {"project", "feature", "code", "file"}
PROJECT_MEMORY_CHANGE_KINDS = {"add", "edit", "rename", "move", "delete", "mixed"}
MAX_ENDING_REPAIR_ROUNDS = _ROUTING_POLICY.ROUTING_THRESHOLDS["maximum_ending_repair_rounds"]
SENSITIVE_MEMORY_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_-])(?:sk|rk|pk)-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s,;]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"https?://[^\s/:]+:[^\s/@]+@", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[^\s]+", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])[A-Z]:\\Users\\[^\s]+", re.IGNORECASE),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
)


def complexity_band(score):
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("complexity score must be an integer from 0 to 100")
    return "small" if score <= 24 else "standard" if score <= 49 else "complex" if score <= 74 else "advanced"


def _clean(value, field, maximum=160):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text[:maximum]


def _normalize_origin_session(raw, project_root):
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("origin_session must be a JSON object")
    thread_id = _clean(raw.get("thread_id"), "origin_session.thread_id", 240)
    host_id = _clean(raw.get("host_id"), "origin_session.host_id", 160)
    project_id = _clean(raw.get("project_id"), "origin_session.project_id", 200)
    source_root = Path(raw.get("project_root") or project_root).expanduser().resolve()
    if source_root != project_root:
        raise ValueError("origin_session.project_root must match project_root")
    return {"thread_id": thread_id, "host_id": host_id, "project_id": project_id, "project_root": str(project_root), "immutable": True}


def _restriction_timestamp(value, field):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error


def _read_restrictions(store):
    path = Path(store).expanduser().resolve()
    if not path.is_file():
        return path, {"schema_version": 1, "restrictions": []}
    payload = _read_json(path, "controller restriction store")[1]
    if payload.get("schema_version") != 1 or not isinstance(payload.get("restrictions"), list):
        raise ValueError("controller restriction store is invalid")
    return path, payload


@contextmanager
def _restriction_lock(store):
    path = Path(store).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            if handle.seek(0, os.SEEK_END) == 0:
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


def record_controller_restriction(pair, reason, store=DEFAULT_CONTROLLER_RESTRICTION_STORE, retry_at="", source="launch_failure", now=None):
    pair_value = _clean(pair, "pair", 160)
    if pair_value.count("|") != 1:
        raise ValueError("pair must use model|effort")
    model, effort = pair_value.split("|", 1)
    reason_value = _clean(reason, "reason", 80)
    if reason_value not in CONTROLLER_RESTRICTION_REASONS:
        raise ValueError("reason is not an Ending controller restriction reason")
    recorded_at = now or datetime.now(timezone.utc)
    if recorded_at.tzinfo is None:
        raise ValueError("restriction timestamp must include a timezone")
    retry_time = _restriction_timestamp(retry_at, "retry_at") if retry_at else recorded_at + timedelta(seconds=REPAIR_RESTRICTION_DEFAULT_SECONDS)
    if retry_time.tzinfo is None or retry_time <= recorded_at:
        raise ValueError("retry_at must be after the restriction timestamp")
    entry = {"model": model, "pair": f"{model}|{effort}", "reason": reason_value, "restricted_at": recorded_at.isoformat(), "retry_at": retry_time.isoformat(), "cooldown_until": retry_time.isoformat(), "scope": "model", "source": _clean(source, "source", 160)}
    with _restriction_lock(store):
        path, payload = _read_restrictions(store)
        history = [item for item in payload["restrictions"] if not (isinstance(item, dict) and item.get("model") == model)] + [entry]
        payload["restrictions"] = history[-CONTROLLER_RESTRICTION_HISTORY_LIMIT:]
        _atomic_write(path, payload)
    return {"status": "recorded", "restriction": entry, "store": str(path)}


def _controller_ladder(registry):
    policy = _ending_model_policy(registry)
    quality_pairs = [f"{model['id']}|{effort}" for model in registry.get("models", []) if isinstance(model, dict) and isinstance(model.get("id"), str) for effort in model.get("codex_efforts", []) if isinstance(effort, str)]
    pairs = [policy["primary_pair"], *quality_pairs, policy.get("availability_fallback_pair")]
    return [pair for pair in dict.fromkeys(pairs) if isinstance(pair, str) and "|" in pair]


def _select_available_controller(registry, restriction_store, now=None):
    current_time = now or datetime.now(timezone.utc)
    restriction_path = Path(restriction_store).expanduser().resolve()
    if restriction_path.is_file():
        with _restriction_lock(restriction_path):
            _, restriction_state = _read_restrictions(restriction_path)
    else:
        restriction_state = {"schema_version": 1, "restrictions": []}
    active = {item.get("pair"): item for item in restriction_state["restrictions"] if isinstance(item, dict) and isinstance(item.get("pair"), str) and isinstance(item.get("cooldown_until"), str) and _restriction_timestamp(item["cooldown_until"], "cooldown_until") > current_time}
    cooling_models = {item.get("model") or pair.split("|", 1)[0] for pair, item in active.items()}
    ladder = _controller_ladder(registry)
    selected = next((pair for pair in ladder if pair not in active and pair.split("|", 1)[0] not in cooling_models), None)
    if selected is None:
        raise ValueError("all supported Ending controller pairs are cooling")
    return selected, ladder, active


def _normalize_repair_of_lifecycle_id(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not LIFECYCLE_ID_PATTERN.fullmatch(value):
        raise ValueError("repair_of_lifecycle_id must use YYYYMMDDTHHMMSS-12hex format")
    try:
        datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    except ValueError as error:
        raise ValueError("repair_of_lifecycle_id must contain a valid UTC timestamp") from error
    return value


def _registry():
    script = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "model_registry.py"
    spec = importlib.util.spec_from_file_location("ending_verification_model_registry", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_registry()


def _ending_model_policy(registry=None):
    payload = registry or _registry()
    registry_policy = payload.get("ending_fast")
    if not isinstance(registry_policy, dict):
        raise ValueError("model registry requires ending_fast policy")
    primary_pair = registry_policy.get("primary_pair")
    fallback_pair = registry_policy.get("availability_fallback_pair")
    floor_pair = payload.get("role_pairs", {}).get(ENDING_FALLBACK_ROLE)
    if not isinstance(primary_pair, str) or "|" not in primary_pair:
        raise ValueError("model registry ending_fast requires a concrete primary pair")
    if fallback_pair is not None and (not isinstance(fallback_pair, str) or "|" not in fallback_pair):
        raise ValueError("model registry ending_fast fallback pair must be concrete or null")
    if not isinstance(floor_pair, str) or "|" not in floor_pair or (fallback_pair is not None and fallback_pair != floor_pair) or (primary_pair != ENDING_PRIMARY_PAIR and primary_pair != floor_pair):
        raise ValueError("model registry ending_fast must use the registry floor when Spark-xhigh is unavailable")
    if registry_policy.get("selection_basis") != "ending_fast_primary" or registry_policy.get("fallback_policy") != "availability_only" or registry_policy.get("score_scope") != "check_only":
        raise ValueError("model registry ending_fast policy is inconsistent")
    quality_pairs = [f"{model['id']}|{effort}" for model in payload.get("models", []) if isinstance(model, dict) and isinstance(model.get("id"), str) for effort in model.get("codex_efforts", []) if isinstance(effort, str)]
    approved_pairs = list(dict.fromkeys(pair for pair in (primary_pair, *quality_pairs, fallback_pair) if pair))
    primary_supported = primary_pair == ENDING_PRIMARY_PAIR
    return {
        "selection_basis": registry_policy["selection_basis"],
        "preferred_pair": ENDING_PRIMARY_PAIR,
        "primary_pair": primary_pair,
        "primary_supported_by_registry": primary_supported,
        "availability_fallback_pair": fallback_pair,
        "availability_fallback_reasons": sorted(AVAILABILITY_FALLBACK_REASONS),
        "approved_pairs": approved_pairs,
        "cooldown_escalation_pairs": [pair for pair in approved_pairs if pair != primary_pair],
        "selected_pair": primary_pair,
        "primary_selection_reason": None if primary_supported else "primary_pair_not_in_registry",
        "default_availability_reason": None,
        "fallback_policy": registry_policy["fallback_policy"],
        "score_controls": "check_scope_and_classification_only",
        "quality_failure_model_fallback": False,
    }


def pair_for_score(score, registry=None):
    band = complexity_band(score)
    policy = _ending_model_policy(registry)
    pair = policy["selected_pair"]
    model, effort = pair.split("|", 1)
    return {
        "complexity_score": score,
        "complexity_band": band,
        **policy,
        "model": model,
        "effort": effort,
    }


def worker_pair_for_check(score, surface, registry=None):
    if surface in DIRECT_CHECK_SURFACES:
        return None
    if surface not in DELEGATED_CHECK_SURFACES:
        raise ValueError("check.verification_surface is invalid")
    payload = registry or _registry()
    role_pairs = payload.get("role_pairs") if isinstance(payload.get("role_pairs"), dict) else {}
    role = "frontier_complex" if surface in {"ui_visual", "artifact_visual"} or score >= 75 else "balanced_complex" if score >= 50 else "balanced_default"
    pair = role_pairs.get(role)
    if not isinstance(pair, str) or "|" not in pair:
        raise ValueError(f"model registry requires role pair {role}")
    model, effort = pair.split("|", 1)
    return {"marker": ENDING_CHECK_WORKER_MARKER, "pair": pair, "model": model, "effort": effort, "selection_basis": "ending_check_capability_route", "role": role}


def _inside(root, value, field):
    path = Path(value).expanduser().resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{field} must be inside project_root") from error
    return path


def _relative_project_file(project_root, value, field):
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        relative = candidate.resolve().relative_to(project_root)
    else:
        relative = PurePosixPath(candidate.as_posix())
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"{field} must be a project-relative file")
    return relative.as_posix()


def _clean_list(values, field, maximum=600):
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a JSON array")
    if any(not isinstance(value, str) for value in values):
        raise ValueError(f"{field} must contain only strings")
    normalized = [re.sub(r"\s+", " ", value).strip() for value in values]
    if any(not value or len(value) > maximum for value in normalized):
        raise ValueError(f"{field} contains an empty or overlong value")
    if any(pattern.search(value) for value in normalized for pattern in SENSITIVE_MEMORY_PATTERNS):
        raise ValueError(f"{field} contains private or secret-like content")
    return list(dict.fromkeys(normalized))


def _clean_memory_string(value, field, maximum, required=True):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    text = re.sub(r"\s+", " ", value).strip()
    if required and not text:
        raise ValueError(f"{field} is required")
    if len(text) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    if any(pattern.search(text) for pattern in SENSITIVE_MEMORY_PATTERNS):
        raise ValueError(f"{field} contains private or secret-like content")
    return text


def _normalize_project_memory_closeout(raw, project_root):
    if raw is None:
        return {"mode": "none"}
    if not isinstance(raw, dict):
        raise ValueError("project_memory_closeout must be a JSON object")
    mode = _clean(raw.get("mode") or "none", "project_memory_closeout.mode", 20)
    if mode not in PROJECT_MEMORY_MODES:
        raise ValueError("project_memory_closeout.mode must be none or durable")
    if mode == "none":
        if set(raw) - {"mode"}:
            raise ValueError("project_memory_closeout mode=none contains unknown fields")
        return {"mode": "none"}
    allowed_fields = {"mode", "module", "scope", "change_kind", "summary", "reason", "result", "files", "symbols", "decisions", "risks", "supersedes"}
    unknown_fields = sorted(set(raw) - allowed_fields)
    if unknown_fields:
        raise ValueError("project_memory_closeout contains unknown fields: " + ", ".join(unknown_fields))
    scope = _clean_memory_string(raw.get("scope"), "project_memory_closeout.scope", 20)
    change_kind = _clean_memory_string(raw.get("change_kind"), "project_memory_closeout.change_kind", 40)
    if scope not in PROJECT_MEMORY_SCOPES:
        raise ValueError("project_memory_closeout.scope is invalid")
    if change_kind not in PROJECT_MEMORY_CHANGE_KINDS:
        raise ValueError("project_memory_closeout.change_kind is invalid")
    raw_files = raw.get("files")
    if not isinstance(raw_files, list) or any(not isinstance(value, str) for value in raw_files):
        raise ValueError("project_memory_closeout.files must be a JSON string array")
    files = [_relative_project_file(project_root, value, "project_memory_closeout.files") for value in raw_files]
    files = list(dict.fromkeys(files))
    if not files:
        raise ValueError("durable project_memory_closeout requires files")
    symbols = _clean_list(raw.get("symbols"), "project_memory_closeout.symbols", 240)
    if scope == "code" and not symbols:
        raise ValueError("code project_memory_closeout requires at least one symbol")
    return {
        "mode": mode,
        "module": _clean_memory_string(raw.get("module"), "project_memory_closeout.module", 160),
        "scope": scope,
        "change_kind": change_kind,
        "summary": _clean_memory_string(raw.get("summary"), "project_memory_closeout.summary", 1200),
        "reason": _clean_memory_string(raw.get("reason"), "project_memory_closeout.reason", 1200),
        "result": _clean_memory_string(raw.get("result"), "project_memory_closeout.result", 1200),
        "files": files,
        "symbols": symbols,
        "decisions": _clean_list(raw.get("decisions"), "project_memory_closeout.decisions"),
        "risks": _clean_list(raw.get("risks"), "project_memory_closeout.risks"),
        "supersedes": _clean_memory_string(raw.get("supersedes", ""), "project_memory_closeout.supersedes", 120, required=False),
    }


def normalize_check(raw, project_root, task_name, task_score, origin_session, registry=None):
    if not isinstance(raw, dict):
        raise ValueError("each check must be a JSON object")
    name = _clean(raw.get("name"), "check.name", 80)
    check_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "check"
    command = raw.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(value, str) or not value for value in command):
        raise ValueError("check.command must be a non-empty JSON string array")
    cwd = _inside(project_root, raw.get("cwd") or project_root, "check.cwd")
    score = raw.get("complexity_score", task_score)
    route = pair_for_score(score, registry)
    timeout = raw.get("timeout_seconds", 300)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 1800:
        raise ValueError("check.timeout_seconds must be from 1 to 1800")
    expected_exit = raw.get("expected_exit_code", 0)
    if isinstance(expected_exit, bool) or not isinstance(expected_exit, int):
        raise ValueError("check.expected_exit_code must be an integer")
    acceptance = _clean(raw.get("acceptance") or name, "check.acceptance", 1200)
    repair_scope = _clean(raw.get("repair_scope") or "Only the original producer's authorized result scope.", "check.repair_scope", 600)
    verification_surface = _clean(raw.get("verification_surface") or "command", "check.verification_surface", 80)
    if verification_surface not in CHECK_SURFACES:
        raise ValueError("check.verification_surface is invalid")
    worker_route = worker_pair_for_check(score, verification_surface, registry)
    requested_skills = _clean_list(raw.get("required_skills"), "check.required_skills", 120)
    required_skills = list(dict.fromkeys([*(DEFAULT_WORKER_SKILLS.get(verification_surface) or []), *requested_skills])) if worker_route else []
    return {
        "check_id": check_id,
        "name": name,
        "cwd": str(cwd),
        "command": command,
        "expected_exit_code": expected_exit,
        "timeout_seconds": timeout,
        "independent": bool(raw.get("independent", True)),
        "acceptance": acceptance,
        "repair_scope": repair_scope,
        "verification_surface": verification_surface,
        "execution_mode": "delegated_check_worker" if worker_route else "spark_controller_direct",
        "worker_route": worker_route,
        "required_skills": required_skills,
        **route,
        "on_failure": {
            "action": "create_isolated_projectless_repair_then_fresh_ending",
            "dispatch_tool": REPAIR_LAUNCH_CAPABILITY,
            "error_fields": ["exit_code", "stdout", "stderr", "timed_out"],
            "max_repair_attempts": MAX_ENDING_REPAIR_ROUNDS,
            "origin_session_required": False,
            "origin_session": origin_session,
        },
    }


def build_plan(project_root, task_name, task_score, checks, origin_session=None, project_memory_closeout=None, repair_of_lifecycle_id=""):
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    cleaned_task = _clean(task_name, "task_name", 80)
    registry = _registry()
    normalized_origin_session = _normalize_origin_session(origin_session, root)
    normalized_closeout = _normalize_project_memory_closeout(project_memory_closeout, root)
    normalized_repair_of_lifecycle_id = _normalize_repair_of_lifecycle_id(repair_of_lifecycle_id)
    tasks = [normalize_check(check, root, cleaned_task, task_score, normalized_origin_session, registry) for check in checks]
    if not tasks:
        raise ValueError("at least one real verification check is required")
    ids = [task["check_id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("check names must produce unique ids")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "task_name": cleaned_task,
        "task_complexity": pair_for_score(task_score, registry),
        "verification_required": True,
        "execution": "one_persistent_ending_runs_all_checks",
        "all_checks_must_pass": True,
        "origin_session": normalized_origin_session,
        "repair_of_lifecycle_id": normalized_repair_of_lifecycle_id,
        "ending_model_policy": _ending_model_policy(registry),
        "repair_policy": {"action": "create_isolated_projectless_repair_then_fresh_ending", "origin_session_required": False, "immutable_origin_context_only": True, "dispatch_tool": REPAIR_LAUNCH_CAPABILITY, "max_repair_attempts": MAX_ENDING_REPAIR_ROUNDS, "repair_of_lifecycle_id": normalized_repair_of_lifecycle_id, "wait_when": ["active_task_owns_required_write_surface"], "blocked_when": ["external_state_unavailable", "repair_attempt_limit_exhausted"]},
        "project_memory_closeout": normalized_closeout,
        "ending_tasks": tasks,
    }


def _atomic_write(path, payload):
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    target.chmod(0o600)


def _read_json(path, field):
    source = Path(path).expanduser().resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{field} is not readable JSON") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{field} must contain a JSON object")
    return source, payload


def _validate_projectless_create_arguments(arguments):
    if not isinstance(arguments, dict):
        raise ValueError("Ending create_thread arguments must be a JSON object")
    unexpected = sorted(set(arguments) - CREATE_THREAD_ARGUMENT_KEYS)
    if unexpected:
        raise ValueError("Ending create_thread arguments contain project/current-task fields: " + ", ".join(unexpected))
    if arguments.get("target") != THREAD_TARGET:
        raise ValueError('Ending create_thread target must be exactly {"type":"projectless"}')


def _validate_projectless_launch_request(request):
    if not isinstance(request, dict):
        raise ValueError("Ending launch request must be a JSON object")
    if request.get("tool") != CREATE_THREAD_TOOL:
        raise ValueError(f"Ending launch tool must be {CREATE_THREAD_TOOL}")
    if request.get("thread_target") != THREAD_TARGET or request.get("thread_placement") != THREAD_PLACEMENT_POLICY:
        raise ValueError("Ending launch placement must be global projectless")
    if any(field in request for field in ("project_id", "projectId", "environment", "threadId", "parentThreadId")):
        raise ValueError("Ending launch request must not contain project/current-task attachment fields")
    _validate_projectless_create_arguments(request.get("arguments"))
    candidates = request.get("launch_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Ending launch request requires projectless launch candidates")
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Ending launch candidate must be a JSON object")
        candidate_arguments = candidate.get("arguments")
        _validate_projectless_create_arguments(candidate_arguments)
        candidate_sha256 = hashlib.sha256(json.dumps(candidate_arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if candidate.get("request_sha256") != candidate_sha256:
            raise ValueError("Ending launch candidate request digest does not match its projectless arguments")
    request_sha256 = hashlib.sha256(json.dumps(request["arguments"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if request.get("request_sha256") != request_sha256:
        raise ValueError("Ending launch request digest does not match its projectless arguments")


def _normalize_thread_project_id(value):
    if value is None or (isinstance(value, str) and value.strip().lower() == "null"):
        return None
    raise ValueError("thread_project_id must be null after codex_app__list_threads readback")


def _repair_handoff(check, origin_session, observed, mismatch_summary=""):
    mismatch = _clean(mismatch_summary, "requirement_mismatch", 1200) if mismatch_summary else ""
    evidence_reason = mismatch or ("The real acceptance command did not produce the expected exit result." if observed.get("timed_out") or observed.get("exit_code") != check["expected_exit_code"] else "The observed final result did not satisfy the original acceptance contract.")
    prompt_lines = ["ENDING_REPAIR_TASK", "This is a fresh independent projectless repair task. Never send to, steer, interrupt, terminate, hand off, move, or mutate an existing task or session.", "Immutable origin context is evidence only; do not resume it.", f"Original acceptance contract: {check['acceptance']}", f"Observed Ending issue: {evidence_reason}", f"Observed exit code: {observed.get('exit_code')}", f"Repair scope: {check['repair_scope']}", "Before any write, inspect task ownership read-only. If an active task owns a required file or state, record waiting_for_active_task_release and wait without messaging or interrupting that task. After release, repair only the authorized scope, run a bounded Quick Check, and create a fresh independent global projectless Ending after the repaired result is released."]
    repair_prompt = "\n".join(prompt_lines)
    repair_launch = {"tool": REPAIR_LAUNCH_CAPABILITY, "arguments": {"target": dict(THREAD_TARGET), "title": f"Repair Task-{check['check_id']}", "prompt": repair_prompt}, "required": True}
    return {"action": "create_isolated_projectless_repair_then_fresh_ending", "origin_context": origin_session, "origin_context_immutable": True, "origin_context_optional": True, "repair_launch": repair_launch, "repair_prompt": repair_prompt, "session_isolation": {"new_projectless_session": True, "prohibited_existing_session_actions": ["send", "steer", "interrupt", "terminate", "handoff", "move", "mutate"], "active_task_conflict_action": "wait_without_interruption"}, "conflict_policy": "waiting_for_active_task_release_without_interruption", "observed_issue": evidence_reason, "original_acceptance": check["acceptance"], "repair_scope": check["repair_scope"], "fresh_ending": "required_after_new_result_and_receipt", "max_repair_attempts": check["on_failure"]["max_repair_attempts"]}


def _final_producer_receipt(project_root, producer_receipt):
    if producer_receipt is None:
        raise ValueError("producer_receipt is required before launching an Ending")
    receipt_path = _inside(project_root, producer_receipt, "producer_receipt")
    if not receipt_path.is_file():
        raise ValueError("producer_receipt must be an existing file")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("producer_receipt is not readable JSON") from error
    if not isinstance(receipt, dict):
        raise ValueError("producer_receipt must prove a final passing published aggregate result")
    final_aggregate = receipt.get("final_aggregate_receipt") is True and receipt.get("all_result_nodes_settled") is True and receipt.get("subprocesses_settled") is True and receipt.get("ending_launch_ready") is True and receipt.get("aggregate_result_state") in {"released", "single_result_released"} and isinstance(receipt.get("aggregate_result_node_count"), int) and receipt["aggregate_result_node_count"] >= 1
    if receipt.get("status") != "pass" or receipt.get("result_published") is not True or receipt.get("turn_completed") is not True or receipt.get("node_type") != "locked-route-node" or receipt.get("node_role") != "result-producer" or not final_aggregate:
        raise ValueError("producer_receipt must prove a final passing published aggregate result")
    return {"path": receipt_path, "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(), "payload": receipt}


def _detached_project_root_line(project_root):
    return f"Origin project root (absolute): {project_root}. Resolve relative paths below from it; projectless cwd is unrelated."


def _worker_prompt(plan_path, plan, evidence_outputs, assigned_pair, producer_receipt, repair_of_lifecycle_id=None):
    project_root = Path(plan["project_root"]).expanduser().resolve()
    relative_plan = Path(plan_path).expanduser().resolve().relative_to(project_root).as_posix()
    relative_evidence_dir = Path(next(iter(evidence_outputs.values()))).expanduser().resolve().parent.relative_to(project_root).as_posix()
    receipt_line = Path(producer_receipt).expanduser().resolve().relative_to(project_root).as_posix()
    policy = plan["ending_model_policy"]
    repair_parent_line = f"Repair parent: {repair_of_lifecycle_id or 'none'}"
    repair_start_instruction = "Start the ledger with this exact --repair-of-lifecycle-id; use --late-repair-reason post-ending-verification-mismatch only for a later independent mismatch." if repair_of_lifecycle_id else "Initial Ending: do not pass --repair-of-lifecycle-id."
    return "\n".join(
        [
            "ENDING_TASK_WORKER",
            "Use only this global projectless Ending; never attach to/restart a producer.",
            _detached_project_root_line(project_root),
            f"Saved plan: {relative_plan}; evidence directory: {relative_evidence_dir}; final producer receipt: {receipt_line}.",
            f"Assigned pair: {assigned_pair}; primary: {policy['primary_pair']}; fallback: {policy['availability_fallback_pair']}.",
            repair_parent_line,
            repair_start_instruction,
            "Begin only after the final aggregate result is released; partial receipts never trigger. If origin active, wait without a ledger.",
            "Read the plan first. Run only the next check via ending_verification_plan.py run-check; an ENDING_CHECK_WORKER writes evidence only.",
            "Keep this task visible. Use compact continuation; omit full plan, manifest, and policy.",
            "With fresh evidence, run ending_task_ledger.py once using the plan, ending-check-id=task-ending, pair, receipt, and repair parent. Correctness, quality, protocol, timeout, or command failure never changes the Ending pair.",
            "On a real quota, five-hour limit, provider rate limit, or trusted retry-after, record-controller-restriction once, regenerate create-launches, and use its stronger controller. Never retry a cooling model; quality failures create no cooldown.",
            "For durable closeout compare process, evidence, and effective project-result memory. Classify only as aligned, no_prior_memory, memory_record_defect, memory_projection_defect, skill_contract_defect, execution_drift, or insufficient_evidence; write memory_consistency_output only in durable mode. Exclude raw prompts, results, paths, secrets, and reasoning from personal memory.",
            "PASS requires every check. On failure do not edit; create the saved independent projectless repair task. Never message, steer, interrupt, terminate, hand off, move, or mutate an existing session. If an active task owns a write surface, the repair waits without interruption. Keep the failed Ending visible.",
            "After closeout print structured model_assessment. Never call set_thread_archived or auto-delete this End Task.",
        ]
    )


def _independent_backend_prompt(plan_path, plan, checks, evidence_outputs, assigned_pair, producer_receipt, backend_id):
    """Give a portable verifier saved scope without claiming terminal proof."""
    project_root = Path(plan["project_root"]).expanduser().resolve()
    relative_plan = Path(plan_path).expanduser().resolve().relative_to(project_root).as_posix()
    receipt_line = Path(producer_receipt).expanduser().resolve().relative_to(project_root).as_posix() if producer_receipt else "none"
    return "\n".join(
        [
            "INDEPENDENT_ENDING_EVIDENCE_WORKER",
            f"Backend: {backend_id}.",
            "You are an independent verifier. Start without producer conversational context, read only the saved plan and supplied artifacts, and run only the listed checks.",
            _detached_project_root_line(project_root),
            f"Verification plan relative to project root: {relative_plan}.",
            f"Checks: {', '.join(check['check_id'] for check in checks)}.",
            f"Producer receipt relative to project root: {receipt_line}.",
            f"Assigned pair: {assigned_pair}.",
            "Use skills/verify-skill/scripts/ending_verification_plan.py run-check for each saved check and write only the declared evidence outputs under Cache.",
            "Never edit producer files, reroute models, create a task/thread, repair the result, write project memory, or claim PASS for the global projectless Ending lifecycle.",
            "Return the evidence locations and an independent evidence verdict only. The caller must still obtain projectless host creation plus readback before a terminal lifecycle PASS is possible.",
        ]
    )


def build_launch_spec(plan_path, evidence_dir, project_id, producer_receipt, repair_of_lifecycle_id="", backend_capabilities=None, restriction_store=DEFAULT_CONTROLLER_RESTRICTION_STORE, now=None):
    plan_file, plan = _read_json(plan_path, "plan")
    project_root = Path(plan.get("project_root", "")).expanduser().resolve()
    if not project_root.is_dir():
        raise ValueError("plan.project_root must be an existing directory")
    project_value = _clean(project_id, "project_id", 200)
    _inside(project_root, plan_file, "plan")
    origin_session = _normalize_origin_session(plan.get("origin_session"), project_root)
    if origin_session and origin_session["project_id"] != project_value:
        raise ValueError("origin_session.project_id must match project_id")
    plan_repair_of_lifecycle_id = _normalize_repair_of_lifecycle_id(plan.get("repair_of_lifecycle_id"))
    launch_repair_of_lifecycle_id = _normalize_repair_of_lifecycle_id(repair_of_lifecycle_id)
    if plan_repair_of_lifecycle_id and launch_repair_of_lifecycle_id and plan_repair_of_lifecycle_id != launch_repair_of_lifecycle_id:
        raise ValueError("create-launches repair_of_lifecycle_id conflicts with the saved plan")
    resolved_repair_of_lifecycle_id = launch_repair_of_lifecycle_id or plan_repair_of_lifecycle_id
    repair_policy = plan.get("repair_policy")
    if not isinstance(repair_policy, dict):
        raise ValueError("plan requires repair_policy")
    resolved_repair_policy = {**repair_policy, "repair_of_lifecycle_id": resolved_repair_of_lifecycle_id}
    evidence_root = _inside(project_root, evidence_dir, "evidence_dir")
    final_receipt = _final_producer_receipt(project_root, producer_receipt)
    receipt_path = final_receipt["path"]
    if final_receipt["payload"].get("project_memory_closeout_required") is True and plan.get("project_memory_closeout", {}).get("mode") != "durable":
        raise ValueError("material update requires durable project_memory_closeout before Ending launch")
    tasks = plan.get("ending_tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("plan must contain ending_tasks")
    backend_resolution = ending_backend.resolve_ending_backend(backend_capabilities)
    evidence_outputs = {}
    for check in tasks:
        check_id = check.get("check_id") if isinstance(check, dict) else None
        if not isinstance(check_id, str) or not check_id:
            raise ValueError("every ending task requires check_id")
        evidence_outputs[check_id] = str(evidence_root / f"{check_id}.json")
    policy = plan.get("ending_model_policy")
    if not isinstance(policy, dict):
        raise ValueError("plan requires ending_model_policy")
    primary_pair = policy.get("primary_pair")
    fallback_pair = policy.get("availability_fallback_pair")
    selected_pair = policy.get("selected_pair")
    if any(not isinstance(pair, str) or "|" not in pair for pair in (primary_pair, selected_pair)) or (fallback_pair is not None and (not isinstance(fallback_pair, str) or "|" not in fallback_pair)):
        raise ValueError("ending_model_policy requires concrete primary and selected pairs plus an optional concrete fallback")
    selected_pair, controller_ladder, active_restrictions = _select_available_controller(_registry(), restriction_store, now)
    title = f"End Task-{plan['task_name']}"
    memory_candidates_output = evidence_root / "task-ending.memory.json"
    memory_consistency_output = evidence_root / "task-ending.project-memory-consistency.json"
    if backend_resolution["status"] != "launchable":
        selected_backend = backend_resolution.get("selected") if isinstance(backend_resolution.get("selected"), dict) else None
        independent_requests = []
        if selected_backend is not None:
            independent_requests.append(
                {
                    "backend": selected_backend["backend"],
                    "tool": selected_backend["launch_tool"],
                    "execution": "independent_evidence_only",
                    "independent_context": selected_backend["independent_context"],
                    "producer_context_reuse": selected_backend["producer_context_reuse"],
                    "check_ids": [check["check_id"] for check in tasks],
                    "selected_pair": selected_pair,
                    "arguments": {"title": title, "prompt": _independent_backend_prompt(plan_file, plan, tasks, evidence_outputs, selected_pair, receipt_path, selected_backend["backend"])},
                    "evidence_outputs": evidence_outputs,
                }
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "plan": str(plan_file),
            "plan_sha256": hashlib.sha256(plan_file.read_bytes()).hexdigest(),
            "project_root": str(project_root),
            "project_binding": {"project_id": project_value, "project_root": str(project_root), "environment": {"type": "local"}, "resolver": "codex_app__list_projects exact canonical project root; execution context only, never create_thread target"},
            "thread_placement_policy": {**THREAD_PLACEMENT_POLICY, "target": dict(THREAD_TARGET)},
            "execution": "independent_evidence_only",
            "backend": backend_resolution,
            "origin_session": origin_session,
            "repair_of_lifecycle_id": resolved_repair_of_lifecycle_id,
            "repair_policy": resolved_repair_policy,
            "project_memory_closeout": plan.get("project_memory_closeout", {"mode": "none"}),
            "final_producer_receipt": {"path": str(receipt_path), "sha256": final_receipt["sha256"]},
            "required_launch_count": 0,
            "launch_requests": [],
            "independent_verification_request_count": len(independent_requests),
            "independent_verification_requests": independent_requests,
            "launch_gate": "blocked_until_a_projectless_host_can_create_and_read_back_the_global_end_task",
        }
    candidates = []
    candidate_pairs = [(pair, "primary" if pair == primary_pair else "cooldown_escalation") for pair in controller_ladder]
    for pair, role in candidate_pairs:
        model, thinking = pair.split("|", 1)
        prompt = _worker_prompt(plan_file, plan, evidence_outputs, pair, receipt_path, resolved_repair_of_lifecycle_id)
        arguments = {"target": dict(THREAD_TARGET), "title": title, "model": model, "thinking": thinking, "prompt": prompt}
        candidates.append(
            {
                "role": role,
                "pair": pair,
                "arguments": arguments,
                "request_sha256": hashlib.sha256(json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            }
        )
    selected_candidate = next(candidate for candidate in candidates if candidate["pair"] == selected_pair)
    request = {
        "check_id": ENDING_LAUNCH_ID,
        "check_ids": [check["check_id"] for check in tasks],
        "title": title,
        "thread_target": dict(THREAD_TARGET),
        "thread_placement": {**THREAD_PLACEMENT_POLICY, "target": dict(THREAD_TARGET)},
        "terminal_thread_policy": TERMINAL_THREAD_POLICY,
        "selected_pair": selected_pair,
        "primary_pair": primary_pair,
        "availability_fallback_pair": fallback_pair,
        "availability_fallback_reasons": policy["availability_fallback_reasons"],
        "default_availability_reason": policy.get("default_availability_reason"),
        "approved_pairs": controller_ladder,
        "controller_restriction_store": str(Path(restriction_store).expanduser().resolve()),
        "controller_restrictions": list(active_restrictions.values()),
        "controller_selection_reason": "primary" if selected_pair == primary_pair else "controller_cooling",
        "controller_selection": "spark_first_then_next_supported_pair_when_cooling",
        "complexity_score": plan["task_complexity"]["complexity_score"],
        "complexity_band": plan["task_complexity"]["complexity_band"],
        "tool": CREATE_THREAD_TOOL,
        "arguments": selected_candidate["arguments"],
        "request_sha256": selected_candidate["request_sha256"],
        "launch_candidates": candidates,
        "evidence_outputs": evidence_outputs,
        "memory_candidates_output": str(memory_candidates_output),
        "memory_consistency_output": str(memory_consistency_output),
        "project_memory_closeout": plan.get("project_memory_closeout", {"mode": "none"}),
        "final_producer_receipt": {"path": str(receipt_path), "sha256": final_receipt["sha256"]},
        "repair_of_lifecycle_id": resolved_repair_of_lifecycle_id,
        "acknowledgement_required": True,
    }
    _validate_projectless_launch_request(request)
    launch_requests = [request]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan": str(plan_file),
        "plan_sha256": hashlib.sha256(plan_file.read_bytes()).hexdigest(),
        "project_root": str(project_root),
        "project_binding": {
            "project_id": project_value,
            "project_root": str(project_root),
            "environment": {"type": "local"},
            "resolver": "codex_app__list_projects exact canonical project root; execution context only, never create_thread target",
        },
        "thread_placement_policy": {**THREAD_PLACEMENT_POLICY, "target": dict(THREAD_TARGET)},
        "execution": "host_persistent_create_thread",
        "backend": backend_resolution,
        "origin_session": origin_session,
        "repair_of_lifecycle_id": resolved_repair_of_lifecycle_id,
        "repair_policy": resolved_repair_policy,
        "project_memory_closeout": plan.get("project_memory_closeout", {"mode": "none"}),
        "required_launch_count": len(launch_requests),
        "launch_requests": launch_requests,
        "launch_gate": "one_global_projectless_ending_requires_thread_host_pair_list_threads_null_project_readback_and_availability_acknowledgement",
    }


def acknowledge_launch(launch_spec_path, check_id, thread_id, host_id, project_id, state_output, thread_scope, thread_project_id, placement_readback_tool, selected_pair="", availability_reason=""):
    launch_file, launch_spec = _read_json(launch_spec_path, "launch_spec")
    request = next((item for item in launch_spec.get("launch_requests", []) if item.get("check_id") == check_id), None)
    if not isinstance(request, dict):
        raise ValueError(f"unknown check_id: {check_id}")
    _validate_projectless_launch_request(request)
    thread_value = _clean(thread_id, "thread_id", 160)
    host_value = _clean(host_id, "host_id", 160)
    project_value = _clean(project_id, "project_id", 200)
    expected_project_id = launch_spec.get("project_binding", {}).get("project_id")
    if project_value != expected_project_id:
        raise ValueError("project_id does not match the origin project binding")
    thread_scope_value = _clean(thread_scope, "thread_scope", 40)
    if thread_scope_value != THREAD_SCOPE:
        raise ValueError("Ending thread_scope must be global projectless")
    observed_thread_project_id = _normalize_thread_project_id(thread_project_id)
    placement_readback_tool_value = _clean(placement_readback_tool, "placement_readback_tool", 160)
    if placement_readback_tool_value != THREAD_READBACK_TOOL:
        raise ValueError(f"Ending placement must be read back with {THREAD_READBACK_TOOL}")
    actual_pair = _clean(selected_pair or request.get("selected_pair"), "selected_pair", 160)
    candidates = {item.get("pair"): item for item in request.get("launch_candidates", []) if isinstance(item, dict)}
    candidate = candidates.get(actual_pair)
    if not isinstance(candidate, dict) or actual_pair not in request.get("approved_pairs", []):
        raise ValueError("selected_pair is not an approved Ending launch pair")
    primary_pair = request.get("primary_pair")
    fallback_pair = request.get("availability_fallback_pair")
    availability_reason_value = _clean(availability_reason, "availability_reason", 80) if availability_reason else None
    if actual_pair != request.get("selected_pair"):
        raise ValueError("selected_pair must match the restriction-aware launch request; record the restriction and regenerate before escalating")
    if actual_pair == primary_pair:
        if availability_reason_value:
            raise ValueError("primary Ending launch must not claim an availability fallback reason")
    else:
        availability_reason_value = availability_reason_value or "controller_cooling"
        if availability_reason_value != "controller_cooling":
            raise ValueError("restriction-aware controller escalation requires controller_cooling")
    state_path = Path(state_output).expanduser().resolve()
    state = {
        "schema_version": LAUNCH_STATE_SCHEMA_VERSION,
        "launch_spec": str(launch_file),
        "launch_spec_sha256": hashlib.sha256(launch_file.read_bytes()).hexdigest(),
        "launches": [],
    }
    if state_path.is_file():
        _, state = _read_json(state_path, "launch_state")
        if state.get("schema_version") != LAUNCH_STATE_SCHEMA_VERSION:
            raise ValueError("launch_state schema does not enforce global projectless placement")
        if state.get("launch_spec_sha256") != hashlib.sha256(launch_file.read_bytes()).hexdigest():
            raise ValueError("launch_state belongs to a different launch_spec")
    launches = [item for item in state.get("launches", []) if isinstance(item, dict) and item.get("check_id") != check_id]
    if any(item.get("thread_id") == thread_value for item in launches):
        raise ValueError("one End Task thread cannot acknowledge multiple checks")
    launches.append(
        {
            "check_id": check_id,
            "title": request["title"],
            "selected_pair": actual_pair,
            "primary_pair": primary_pair,
            "availability_fallback_pair": fallback_pair,
            "availability_fallback_reason": availability_reason_value,
            "request_sha256": candidate["request_sha256"],
            "thread_id": thread_value,
            "host_id": host_value,
            "origin_project_id": project_value,
            "thread_scope": thread_scope_value,
            "thread_target": dict(THREAD_TARGET),
            "thread_project_id": observed_thread_project_id,
            "placement_readback_tool": placement_readback_tool_value,
            "status": "launched",
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    state["launches"] = sorted(launches, key=lambda item: item["check_id"])
    _atomic_write(state_path, state)
    return {
        "status": "acknowledged",
        "check_id": check_id,
        "thread_id": thread_value,
        "host_id": host_value,
        "thread_scope": thread_scope_value,
        "thread_project_id": observed_thread_project_id,
        "placement_readback_tool": placement_readback_tool_value,
        "selected_pair": actual_pair,
        "availability_fallback_reason": availability_reason_value,
        "state": str(state_path),
    }


def audit_launches(launch_spec_path, state_path):
    launch_file, launch_spec = _read_json(launch_spec_path, "launch_spec")
    backend = launch_spec.get("backend") if isinstance(launch_spec.get("backend"), dict) else {}
    if backend.get("terminal_lifecycle") is not True:
        return {"status": "blocked", "end_task_trigger_rate": "0%", "required_launch_count": launch_spec.get("required_launch_count", 0), "launched_count": 0, "threads": [], "failures": [backend.get("reason") or "no terminal projectless Ending backend is available"]}
    launch_sha256 = hashlib.sha256(launch_file.read_bytes()).hexdigest()
    required = {item["check_id"]: item for item in launch_spec.get("launch_requests", []) if isinstance(item, dict) and item.get("check_id")}
    failures = []
    invalid_request_ids = set()
    for check_id, request in required.items():
        try:
            _validate_projectless_launch_request(request)
        except ValueError as error:
            invalid_request_ids.add(check_id)
            failures.append(f"End Task {check_id} has invalid global projectless placement: {error}")
    placement_policy_valid = launch_spec.get("thread_placement_policy") == THREAD_PLACEMENT_POLICY
    if not placement_policy_valid:
        failures.append("launch_spec thread placement policy is not global projectless")
    try:
        _, state = _read_json(state_path, "launch_state")
    except ValueError:
        return {
            "status": "blocked",
            "end_task_trigger_rate": "0%",
            "required_launch_count": len(required),
            "launched_count": 0,
            "threads": [],
            "failures": [*failures, "launch_state is unavailable; End Task has not been acknowledged"],
        }
    observed = {item["check_id"]: item for item in state.get("launches", []) if isinstance(item, dict) and item.get("check_id")}
    state_schema_valid = state.get("schema_version") == LAUNCH_STATE_SCHEMA_VERSION
    if not state_schema_valid:
        failures.append("launch_state schema does not enforce global projectless placement")
    if state.get("launch_spec_sha256") != launch_sha256:
        failures.append("launch_state does not match launch_spec")
    missing = sorted(set(required) - set(observed))
    extra = sorted(set(observed) - set(required))
    if missing:
        failures.append("missing End Task launch acknowledgements: " + ", ".join(missing))
    if extra:
        failures.append("unexpected End Task launch acknowledgements: " + ", ".join(extra))
    thread_ids = []
    qualified_launches = 0
    expected_origin_project_id = launch_spec.get("project_binding", {}).get("project_id")
    for check_id, request in required.items():
        launch = observed.get(check_id)
        if not launch:
            continue
        prior_failure_count = len(failures)
        thread_ids.append(launch.get("thread_id"))
        if launch.get("status") != "launched" or not launch.get("thread_id") or not launch.get("host_id") or not launch.get("origin_project_id"):
            failures.append(f"End Task {check_id} lacks a persistent thread acknowledgement")
        if launch.get("origin_project_id") != expected_origin_project_id or "project_id" in launch or "projectId" in launch:
            failures.append(f"End Task {check_id} origin binding is invalid or confused with thread placement")
        if launch.get("thread_scope") != THREAD_SCOPE or launch.get("thread_target") != THREAD_TARGET or "thread_project_id" not in launch or launch.get("thread_project_id") is not None or launch.get("placement_readback_tool") != THREAD_READBACK_TOOL:
            failures.append(f"End Task {check_id} was not read back as a global projectless thread with projectId=null")
        candidates = {item.get("pair"): item for item in request.get("launch_candidates", []) if isinstance(item, dict)}
        selected_pair = launch.get("selected_pair")
        candidate = candidates.get(selected_pair)
        if selected_pair not in request.get("approved_pairs", []) or not isinstance(candidate, dict):
            failures.append(f"End Task {check_id} used an unapproved Ending pair")
        if selected_pair != request.get("selected_pair"):
            failures.append(f"End Task {check_id} pair does not match the restriction-aware launch request")
        elif selected_pair == request.get("primary_pair"):
            if launch.get("availability_fallback_reason"):
                failures.append(f"End Task {check_id} primary launch has an invalid fallback reason")
        elif launch.get("availability_fallback_reason") != "controller_cooling":
            failures.append(f"End Task {check_id} cooldown escalation lacks controller_cooling evidence")
        if launch.get("title") != request.get("title") or launch.get("request_sha256") != (candidate or {}).get("request_sha256"):
            failures.append(f"End Task {check_id} acknowledgement does not match its launch request")
        if check_id not in invalid_request_ids and placement_policy_valid and state_schema_valid and len(failures) == prior_failure_count:
            qualified_launches += 1
    if len(thread_ids) != len(set(thread_ids)):
        failures.append("End Task launch acknowledgements must use unique thread ids")
    required_count = len(required)
    launched_count = qualified_launches
    trigger_rate = round(100 * launched_count / required_count) if required_count else 0
    return {
        "status": "pass" if not failures and launched_count == required_count else "blocked",
        "end_task_trigger_rate": f"{trigger_rate}%",
        "required_launch_count": required_count,
        "launched_count": launched_count,
        "threads": [observed[check_id] for check_id in sorted(required) if check_id in observed],
        "failures": failures,
    }


def run_check(plan_path, check_id, evidence_output):
    plan_file = Path(plan_path).expanduser().resolve()
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    check = next((item for item in plan.get("ending_tasks", []) if item.get("check_id") == check_id), None)
    if not check:
        raise ValueError(f"unknown check_id: {check_id}")
    started = datetime.now(timezone.utc)
    timed_out = False
    try:
        completed = subprocess.run(check["command"], cwd=check["cwd"], capture_output=True, text=True, timeout=check["timeout_seconds"], check=False)
        exit_code = completed.returncode
        stdout = completed.stdout[-12000:]
        stderr = completed.stderr[-12000:]
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = None
        stdout = (error.stdout or "")[-12000:] if isinstance(error.stdout, str) else ""
        stderr = (error.stderr or "")[-12000:] if isinstance(error.stderr, str) else ""
    passed = not timed_out and exit_code == check["expected_exit_code"]
    finished = datetime.now(timezone.utc)
    ending_title = f"End Task-{plan['task_name']}"
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if passed else "fail",
        "check_id": check_id,
        "title": ending_title,
        "selected_pair": check["selected_pair"],
        "complexity_score": check["complexity_score"],
        "complexity_band": check["complexity_band"],
        "failure_class": "none" if passed else "timeout" if timed_out else "execution",
        "repair_context": {"origin_session": plan.get("origin_session"), "acceptance": check["acceptance"], "repair_scope": check["repair_scope"], "max_repair_attempts": check["on_failure"]["max_repair_attempts"]},
        "command": check["command"],
        "cwd": check["cwd"],
        "expected_exit_code": check["expected_exit_code"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_ms": round((finished - started).total_seconds() * 1000),
        "plan_sha256": hashlib.sha256(plan_file.read_bytes()).hexdigest(),
    }
    if not passed:
        evidence["repair_handoff"] = {**_repair_handoff(check, plan.get("origin_session"), evidence), "failed_ending_title": ending_title, "failed_check_id": check_id, "error": {key: evidence[key] for key in check["on_failure"]["error_fields"]}, "terminal_thread_policy": TERMINAL_THREAD_POLICY}
    _atomic_write(evidence_output, evidence)
    return evidence


def record_requirement_mismatch(evidence_path, mismatch_summary):
    evidence_file, evidence = _read_json(evidence_path, "evidence")
    if not evidence.get("repair_context"):
        raise ValueError("evidence does not contain repair_context")
    summary = _clean(mismatch_summary, "requirement_mismatch", 1200)
    evidence["status"] = "fail"
    evidence["failure_class"] = "correctness"
    evidence["error_fingerprint"] = "acceptance-mismatch"
    evidence["requirement_mismatch"] = summary
    context = evidence["repair_context"]
    check = {"title": evidence.get("title"), "check_id": evidence.get("check_id"), "expected_exit_code": evidence.get("expected_exit_code"), "acceptance": context["acceptance"], "repair_scope": context["repair_scope"], "on_failure": {"max_repair_attempts": context["max_repair_attempts"]}}
    observed = {"exit_code": evidence.get("exit_code"), "stdout": evidence.get("stdout"), "stderr": evidence.get("stderr"), "timed_out": evidence.get("timed_out")}
    evidence["repair_handoff"] = {**_repair_handoff(check, context.get("origin_session"), observed, summary), "failed_ending_title": evidence.get("title"), "failed_check_id": evidence.get("check_id"), "error": {"exit_code": evidence.get("exit_code"), "stdout": evidence.get("stdout"), "stderr": evidence.get("stderr"), "timed_out": evidence.get("timed_out")}}
    _atomic_write(evidence_file, evidence)
    return evidence


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Plan and execute real-test Ending tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--project-root", type=Path, required=True)
    plan.add_argument("--task-name", required=True)
    plan.add_argument("--complexity-score", type=int, required=True)
    plan.add_argument("--origin-session-json", required=True)
    plan.add_argument("--repair-of-lifecycle-id", default="")
    plan.add_argument("--project-memory-closeout-json", default='{"mode":"none"}')
    plan.add_argument("--check-json", action="append", default=[])
    plan.add_argument("--output", type=Path, required=True)
    run = subparsers.add_parser("run-check")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--check-id", required=True)
    run.add_argument("--evidence-output", type=Path, required=True)
    mismatch = subparsers.add_parser("mismatch")
    mismatch.add_argument("--evidence", type=Path, required=True)
    mismatch.add_argument("--summary", required=True)
    launch = subparsers.add_parser("create-launches")
    launch.add_argument("--plan", type=Path, required=True)
    launch.add_argument("--evidence-dir", type=Path, required=True)
    launch.add_argument("--project-id", required=True)
    launch.add_argument("--producer-receipt", type=Path, required=True)
    launch.add_argument("--repair-of-lifecycle-id", default="")
    launch.add_argument("--restriction-store", type=Path, default=DEFAULT_CONTROLLER_RESTRICTION_STORE)
    launch.add_argument("--output", type=Path, required=True)
    restrict = subparsers.add_parser("record-controller-restriction")
    restrict.add_argument("--pair", required=True)
    restrict.add_argument("--reason", required=True)
    restrict.add_argument("--store", type=Path, default=DEFAULT_CONTROLLER_RESTRICTION_STORE)
    restrict.add_argument("--retry-at", default="")
    restrict.add_argument("--source", default="launch_failure")
    acknowledge = subparsers.add_parser("ack-launch")
    acknowledge.add_argument("--launch-spec", type=Path, required=True)
    acknowledge.add_argument("--check-id", required=True)
    acknowledge.add_argument("--thread-id", required=True)
    acknowledge.add_argument("--host-id", required=True)
    acknowledge.add_argument("--project-id", required=True)
    acknowledge.add_argument("--state-output", type=Path, required=True)
    acknowledge.add_argument("--thread-scope", choices=[THREAD_SCOPE], required=True)
    acknowledge.add_argument("--thread-project-id", choices=["null"], required=True)
    acknowledge.add_argument("--placement-readback-tool", choices=[THREAD_READBACK_TOOL], required=True)
    acknowledge.add_argument("--selected-pair", default="")
    acknowledge.add_argument("--availability-reason", choices=sorted(AVAILABILITY_FALLBACK_REASONS), default="")
    audit = subparsers.add_parser("audit-launches")
    audit.add_argument("--launch-spec", type=Path, required=True)
    audit.add_argument("--launch-state", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "plan":
        payload = build_plan(args.project_root, args.task_name, args.complexity_score, [json.loads(value) for value in args.check_json], json.loads(args.origin_session_json), json.loads(args.project_memory_closeout_json), args.repair_of_lifecycle_id)
        _atomic_write(args.output, payload)
        output = {"status": "written", "output": str(args.output.expanduser().resolve()), "ending_tasks": len(payload["ending_tasks"]), "selected_pairs": [task["selected_pair"] for task in payload["ending_tasks"]], "repair_of_lifecycle_id": payload["repair_of_lifecycle_id"]}
        code = 0
    elif args.command == "run-check":
        output = run_check(args.plan, args.check_id, args.evidence_output)
        code = 0 if output["status"] == "pass" else 1
    elif args.command == "mismatch":
        output = record_requirement_mismatch(args.evidence, args.summary)
        code = 0 if output["status"] == "pass" else 1
    elif args.command == "create-launches":
        output = build_launch_spec(args.plan, args.evidence_dir, args.project_id, args.producer_receipt, args.repair_of_lifecycle_id, restriction_store=args.restriction_store)
        _atomic_write(args.output, output)
        output = {"status": "written", "output": str(args.output.expanduser().resolve()), "required_launch_count": output["required_launch_count"], "selected_pairs": [item["selected_pair"] for item in output["launch_requests"]], "repair_of_lifecycle_id": output["repair_of_lifecycle_id"]}
        code = 0
    elif args.command == "record-controller-restriction":
        output = record_controller_restriction(args.pair, args.reason, args.store, args.retry_at, args.source)
        code = 0
    elif args.command == "ack-launch":
        output = acknowledge_launch(args.launch_spec, args.check_id, args.thread_id, args.host_id, args.project_id, args.state_output, args.thread_scope, args.thread_project_id, args.placement_readback_tool, args.selected_pair, args.availability_reason)
        code = 0
    else:
        output = audit_launches(args.launch_spec, args.launch_state)
        code = 0 if output["status"] == "pass" else 1
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

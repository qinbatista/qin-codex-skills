#!/usr/bin/env python3
import argparse
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkstemp

try:
    from routing_policy import (
        EXECUTION_DOMAINS,
        EXECUTION_DOMAIN_REGISTRY_LEGACY,
        EXECUTION_DOMAIN_REGISTRY_VERSION,
        MODEL_EFFORTS,
        MODEL_ORDER,
        canonical_pairs,
        compare_pair,
        downgrade_pair,
        infer_execution_domain,
        parse_pair,
        pair_text,
        public_execution_domain_rows,
        upgrade_pair,
    )
except ModuleNotFoundError:
    import importlib.util
    import sys

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = importlib.util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = importlib.util.module_from_spec(_routing_policy_spec)
    sys.modules[_routing_policy_spec.name] = _routing_policy
    _routing_policy_spec.loader.exec_module(_routing_policy)
    EXECUTION_DOMAINS = _routing_policy.EXECUTION_DOMAINS
    EXECUTION_DOMAIN_REGISTRY_LEGACY = _routing_policy.EXECUTION_DOMAIN_REGISTRY_LEGACY
    EXECUTION_DOMAIN_REGISTRY_VERSION = _routing_policy.EXECUTION_DOMAIN_REGISTRY_VERSION
    MODEL_EFFORTS = _routing_policy.MODEL_EFFORTS
    MODEL_ORDER = _routing_policy.MODEL_ORDER
    canonical_pairs = _routing_policy.canonical_pairs
    compare_pair = _routing_policy.compare_pair
    downgrade_pair = _routing_policy.downgrade_pair
    infer_execution_domain = _routing_policy.infer_execution_domain
    parse_pair = _routing_policy.parse_pair
    pair_text = _routing_policy.pair_text
    public_execution_domain_rows = _routing_policy.public_execution_domain_rows
    upgrade_pair = _routing_policy.upgrade_pair


DEFAULT_HISTORY_PATH = Path(__file__).resolve().parents[1] / "local" / "adaptive-routing" / "model_experience.json"
SCHEMA_VERSION = 3
CONTROL_FIELDS = ["task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "owning_skill", "project_family", "verification_shape", "execution_domain"]
CONTROL_ENUMS = {
    "task_family": {"code", "direct", "grounded", "integration", "visual", "management", "prompt", "document", "data", "safety", "legacy", "tiny_text", "tiny_code", "command_generation", "other"},
    "artifact": {"answer", "script", "note", "report", "evidence", "document", "patch", "log", "legacy"},
    "scope": {"single", "multi", "project"},
    "ambiguity": {"low", "medium", "high"},
    "modality": {"text", "image", "mixed"},
    "risk": {"low", "medium", "high"},
    "complexity": {"easy", "complex"},
    "verification_shape": {"mini_real", "mini", "real", "result"},
    "execution_domain": set(EXECUTION_DOMAINS),
}
QUALITY_FAILURES = {"quality", "correctness"}
RUNTIME_FAILURES = {"availability", "timeout", "protocol", "telemetry", "execution", "receipt"}
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
FORBIDDEN_SUMMARY = [re.compile(r"```"), re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://"), re.compile(r"(?:^|\s)/[^\s]+"), re.compile(r"\b(?:api|auth|secret|password|token)[_-]?(?:key|token|secret|password)?\s*[:=]", re.I)]


def sanitize_slug(value):
    value = str(value).strip().lower()
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError("condition values must be short lowercase slugs")
    return value


def _infer_or_get_domain(values):
    explicit = values.get("execution_domain")
    explicit_domain = None
    if explicit is not None:
        explicit_domain = str(explicit).strip().lower()
        if explicit_domain == "":
            explicit_domain = None
    if explicit_domain is None:
        return infer_execution_domain(owning_skill=values.get("owning_skill"), task_family=values.get("task_family"))
    return infer_execution_domain(
        owning_skill=values.get("owning_skill"),
        task_family=values.get("task_family"),
        explicit_domain=explicit_domain,
    )


def validate_condition(values, *, allow_history_only=False):
    if not isinstance(values, dict):
        raise ValueError("routing condition must be a mapping")
    supplied = dict(values)
    raw_explicit = supplied.get("execution_domain")
    has_explicit_domain = raw_explicit is not None and str(raw_explicit).strip() != ""
    try:
        supplied["execution_domain"] = _infer_or_get_domain(supplied)
    except ValueError as error:
        raise ValueError(f"execution_domain is unknown: {error}")
    if not allow_history_only and not EXECUTION_DOMAINS[supplied["execution_domain"]].get("active", False):
        if has_explicit_domain:
            raise ValueError(f"execution_domain must be active: {supplied['execution_domain']}")
        raise ValueError(f"execution_domain must not infer to inactive row: {supplied['execution_domain']}")
    condition = {field: sanitize_slug(supplied[field]) for field in CONTROL_FIELDS}
    for field, allowed in CONTROL_ENUMS.items():
        if condition[field] not in allowed:
            raise ValueError(f"{field} is invalid")
    return condition


def validate_summary(summary):
    if not isinstance(summary, str) or summary != summary.strip() or "\n" in summary or "\r" in summary or not 24 <= len(summary) <= 280:
        raise ValueError("task_summary must be one line with 24-280 characters")
    if any(pattern.search(summary) for pattern in FORBIDDEN_SUMMARY):
        raise ValueError("task_summary contains private content")
    return summary


def condition_key(condition, *, allow_history_only=False):
    condition = validate_condition(condition, allow_history_only=allow_history_only)
    payload = json.dumps({field: condition[field] for field in CONTROL_FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def empty_history():
    return {"schema_version": SCHEMA_VERSION, "updated_at": datetime.now(timezone.utc).isoformat(), "conditions": {}}


def _read_json(path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _safe_int(value):
    return value if isinstance(value, int) and value >= 0 else None


def _safe_text(value, fallback=None):
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _dedupe_pairs(values):
    seen = set()
    unique = []
    for value in values:
        if isinstance(value, tuple):
            pair = value
        else:
            try:
                pair = parse_pair(value)
            except (TypeError, ValueError):
                continue
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


def _write_locked(path, history):
    history["updated_at"] = datetime.now(timezone.utc).isoformat()
    descriptor, temporary_path = mkstemp(prefix=".model_experience-", suffix=".json", dir=path.parent)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(history, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary_path, 0o600)
    os.replace(temporary_path, path)
    os.chmod(path, 0o600)


def _parse_optional_pairs(values):
    parsed = []
    if not isinstance(values, list):
        return []
    for value in values:
        try:
            pair = parse_pair(value)
        except (TypeError, ValueError):
            continue
        if pair not in parsed:
            parsed.append(pair)
    return parsed


def _resolve_pair_text(value, pairs, fallback):
    try:
        pair = parse_pair(value) if isinstance(value, str) else parse_pair(str(value))
        if pair in pairs:
            return pair
    except (TypeError, ValueError):
        pass
    return fallback


def _normalize_task(raw_task, pair_fallback):
    if not isinstance(raw_task, dict):
        return None
    requested = _parse_optional_pairs([raw_task.get("requested_pair")])
    resolved = _parse_optional_pairs([raw_task.get("resolved_pair")])
    effective = _parse_optional_pairs([raw_task.get("effective_pair")])
    executed = _parse_optional_pairs([raw_task.get("executed_pair")])
    run_id = _safe_text(raw_task.get("run_id"))
    if not run_id or not RUN_ID_PATTERN.fullmatch(run_id):
        run_id = f"run_{os.urandom(8).hex()}"
    requested_pair = requested[0] if requested else pair_fallback
    resolved_pair = resolved[0] if resolved else requested_pair
    effective_pair = effective[0] if effective else resolved_pair
    executed_pair = executed[0] if executed else effective_pair
    operational_pairs = _parse_optional_pairs(raw_task.get("operational_failure_pairs", []))
    return {
        "run_id": run_id,
        "summary": _safe_text(raw_task.get("summary"), "Migrated routing-history task."),
        "requested_pair": pair_text(*requested_pair),
        "resolved_pair": pair_text(*resolved_pair),
        "effective_pair": pair_text(*effective_pair),
        "executed_pair": pair_text(*executed_pair),
        "operational_failure_pairs": canonical_pair_texts(operational_pairs),
        "receipt_status": "pass" if raw_task.get("receipt_status") == "pass" and raw_task.get("turn_completed") is True and raw_task.get("model_match") is True and raw_task.get("effort_match") is True else "fail",
        "mini_status": raw_task.get("mini_status", "unknown"),
        "real_status": raw_task.get("real_status", "unknown"),
        "effective_verdict": None,
        "allowlisted_failure_class": raw_task.get("allowlisted_failure_class", "none"),
        "turn_completed": bool(raw_task.get("turn_completed") is True),
        "model_match": bool(raw_task.get("model_match") is True),
        "effort_match": bool(raw_task.get("effort_match") is True),
        "trial": bool(raw_task.get("trial")),
        "token_totals": {
            "input": _safe_int((raw_task.get("token_totals") or {}).get("input")),
            "cached_input": _safe_int((raw_task.get("token_totals") or {}).get("cached_input")),
            "output": _safe_int((raw_task.get("token_totals") or {}).get("output")),
            "reasoning_output": _safe_int((raw_task.get("token_totals") or {}).get("reasoning_output")),
            "total": _safe_int((raw_task.get("token_totals") or {}).get("total")),
        },
        "process_ms": _safe_int(raw_task.get("process_ms")),
        "recorded_at": _safe_text(raw_task.get("recorded_at"), datetime.now(timezone.utc).isoformat()),
    }


def canonical_pair_texts(pairs):
    return [pair_text(*pair) for pair in canonical_pairs(pairs)]


def _record_for(history, condition, summary, pairs, static_pair, hard_pair):
    key = condition_key(condition)
    record = history["conditions"].setdefault(
        key,
        {
            "condition": condition,
            "summary": summary,
            "candidate_ladder": [pair_text(*pair) for pair in pairs],
            "static_suggestion": pair_text(*static_pair),
            "hard_floor": pair_text(*hard_pair),
            "success_model": None,
            "failed_model": None,
            "tasks": [],
        },
    )
    record["condition"] = condition
    record["summary"] = summary
    merged_pairs = _dedupe_pairs(list(pairs) + list(record.get("candidate_ladder", [])))
    record["candidate_ladder"] = canonical_pair_texts(merged_pairs)
    record["static_suggestion"] = pair_text(*static_pair)
    record["hard_floor"] = pair_text(*hard_pair)
    return record


def _normalize_history_record(raw_record, raw_key):
    if not isinstance(raw_record, dict):
        return None, None
    raw_condition_payload = raw_record.get("condition")
    if not isinstance(raw_condition_payload, dict):
        return None, None
    raw_condition = {
        "task_family": raw_condition_payload.get("task_family", raw_condition_payload.get("category", "legacy")),
        "artifact": raw_condition_payload.get("artifact", "legacy"),
        "scope": raw_condition_payload.get("scope", raw_condition_payload.get("phase", "result")),
        "ambiguity": raw_condition_payload.get("ambiguity", "medium"),
        "modality": raw_condition_payload.get("modality", "text"),
        "risk": raw_condition_payload.get("risk", "low"),
        "complexity": raw_condition_payload.get("complexity", "easy"),
        "owning_skill": raw_condition_payload.get("owning_skill", "workflow-skill"),
        "project_family": raw_condition_payload.get("project_family", "legacy"),
        "verification_shape": raw_condition_payload.get("verification_shape", raw_condition_payload.get("phase", "result")),
        "execution_domain": raw_condition_payload.get("execution_domain", raw_record.get("execution_domain", None)),
    }
    try:
        condition = validate_condition(raw_condition, allow_history_only=True)
    except ValueError:
        return None, None
    pairs = canonical_pairs(raw_record.get("candidate_ladder", []))
    if not pairs:
        return None, None
    static_pair = _resolve_pair_text(raw_record.get("static_suggestion"), pairs, pairs[0])
    hard_pair = _resolve_pair_text(raw_record.get("hard_floor"), pairs, pairs[0])
    record = {"summary": _safe_text(raw_record.get("summary"), "Migrated routing-history summary."), "condition": condition}
    record["candidate_ladder"] = canonical_pair_texts(pairs)
    record["static_suggestion"] = pair_text(*static_pair)
    record["hard_floor"] = pair_text(*hard_pair)
    record["success_model"] = raw_record.get("success_model")
    record["failed_model"] = raw_record.get("failed_model")
    record["tasks"] = []
    fallback_pair = pairs[0]
    for task in raw_record.get("tasks", []):
        normalized = _normalize_task(task, fallback_pair)
        if normalized is not None:
            record["tasks"].append(normalized)
    return condition_key(condition, allow_history_only=True), record


def _legacy_history(legacy_path):
    history = empty_history()
    if not legacy_path.exists():
        return history
    with legacy_path.open(encoding="utf-8", errors="ignore") as handle:
        lines = list(handle)
    for line in lines:
        try:
            event = json.loads(line)
            requested = parse_pair(f"{event['requested_model']}|{event['requested_effort']}")
            executed = parse_pair(f"{event.get('effective_model') or event.get('resolved_model') or requested[0]}|{event.get('effective_effort') or event.get('resolved_effort') or requested[1]}")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        raw_condition = {
            "task_family": event.get("task_family", event.get("category", "legacy")),
            "artifact": event.get("artifact", "legacy"),
            "scope": event.get("scope", event.get("phase", "result")),
            "ambiguity": event.get("ambiguity", "medium"),
            "modality": event.get("modality", "text"),
            "risk": event.get("risk", "low"),
            "complexity": event.get("complexity", "easy"),
            "owning_skill": event.get("owning_skill", "workflow-skill"),
            "project_family": event.get("project_family", "legacy"),
            "verification_shape": event.get("verification_shape", event.get("phase", "result")),
            "execution_domain": None,
        }
        try:
            condition = validate_condition(raw_condition, allow_history_only=True)
        except ValueError:
            continue
        key = condition_key(condition, allow_history_only=True)
        record = history["conditions"].setdefault(key, {"condition": condition, "summary": "Legacy adaptive-routing evidence imported without task content.", "candidate_ladder": [], "static_suggestion": pair_text(*executed), "hard_floor": pair_text(*executed), "success_model": None, "failed_model": None, "tasks": []})
        for pair in (requested, executed):
            text = pair_text(*pair)
            if text not in record["candidate_ladder"]:
                record["candidate_ladder"].append(text)
        status = event.get("verify_status") if event.get("verify_status") in {"pass", "fail"} else "unknown"
        failure_class = event.get("failure_class", "none")
        task = {
            "run_id": f"legacy_{os.urandom(8).hex()}",
            "summary": "Legacy adaptive-routing evidence imported without task content.",
            "requested_pair": pair_text(*requested),
            "resolved_pair": pair_text(*requested),
            "effective_pair": pair_text(*executed),
            "executed_pair": pair_text(*executed),
            "operational_failure_pairs": [],
            "receipt_status": "pass" if event.get("receipt_status") == "pass" and event.get("turn_completed") is True else "fail",
            "mini_status": status if event.get("verify_level") == "mini" else "unknown",
            "real_status": status if event.get("verify_level") == "real" else "unknown",
            "effective_verdict": None,
            "allowlisted_failure_class": failure_class if failure_class in QUALITY_FAILURES | RUNTIME_FAILURES else "none",
            "turn_completed": bool(event.get("turn_completed") is True or event.get("receipt_status") == "pass"),
            "model_match": True,
            "effort_match": True,
            "trial": bool(event.get("trial")),
            "token_totals": {"input": None, "cached_input": None, "output": None, "reasoning_output": None, "total": None},
            "process_ms": None,
            "recorded_at": event.get("recorded_at") or datetime.now(timezone.utc).isoformat(),
        }
        record["tasks"].append(task)
    for record in history["conditions"].values():
        record["candidate_ladder"] = canonical_pair_texts(record["candidate_ladder"])
        recompute_bounds(record)
    return history


def _history_from_schema2(raw_history):
    if not isinstance(raw_history, dict) or raw_history.get("schema_version") != 2:
        return None
    conditions = raw_history.get("conditions")
    if not isinstance(conditions, dict):
        return None
    history = empty_history()
    for raw_key, raw_record in conditions.items():
        key, record = _normalize_history_record(raw_record, raw_key)
        if key is None:
            continue
        candidate_success = record.get("success_model")
        candidate_failed = record.get("failed_model")
        if key in history["conditions"]:
            existing = history["conditions"][key]
            existing_pairs = canonical_pairs(existing.get("candidate_ladder", []))
            incoming_pairs = canonical_pairs(record.get("candidate_ladder", []))
            merged_pairs = canonical_pair_texts(_dedupe_pairs(existing_pairs + incoming_pairs))
            existing["candidate_ladder"] = merged_pairs
            existing["tasks"].extend(record.get("tasks", []))
            existing["summary"] = record["summary"]
            existing["static_suggestion"] = record["static_suggestion"]
            existing["hard_floor"] = record["hard_floor"]
            if candidate_success:
                existing["success_model"] = candidate_success
            if candidate_failed:
                existing["failed_model"] = candidate_failed
            recompute_bounds(existing)
            if candidate_success:
                existing["success_model"] = candidate_success
            if candidate_failed:
                existing["failed_model"] = candidate_failed
        else:
            history["conditions"][key] = record
            recompute_bounds(record)
            if candidate_success:
                history["conditions"][key]["success_model"] = candidate_success
            if candidate_failed:
                history["conditions"][key]["failed_model"] = candidate_failed
    return history


def _history_locked(path, mutate=None):
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(path.parent, 0o700)
    lock_path = path.with_suffix(path.suffix + ".lock")
    migrated = None
    with lock_path.open("a+", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        history = _read_json(path)
        if isinstance(history, dict) and history.get("schema_version") == SCHEMA_VERSION and isinstance(history.get("conditions"), dict):
            migrated = history
        else:
            if isinstance(history, dict) and history.get("schema_version") == 2:
                migrated = _history_from_schema2(history)
            if not isinstance(migrated, dict):
                migrated = _legacy_history(path.with_name("events.jsonl"))
        value = mutate(migrated) if mutate else None
        if mutate is not None:
            _write_locked(path, migrated)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return migrated, value


def load_history(path):
    # Loading is the explicit bootstrap operation; read-only public commands
    # must use their own path and never create the private ledger.
    return _history_locked(path, lambda history: history)[0]


def task_verdict(task):
    if task.get("receipt_status") != "pass" or task.get("turn_completed") is not True or task.get("model_match") is not True or task.get("effort_match") is not True:
        return None
    failure_class = task.get("allowlisted_failure_class")
    if failure_class in QUALITY_FAILURES and (
        task.get("mini_status") == "fail" or task.get("real_status") == "fail"
    ):
        return "fail"
    if failure_class in RUNTIME_FAILURES or task.get("executed_pair") in task.get("operational_failure_pairs", []):
        return None
    if task.get("real_status") == "pass":
        return "pass"
    if task.get("mini_status") == "pass":
        return "pass"
    return None


def _strongest_pair(values):
    selected = None
    for pair in values:
        if selected is None or compare_pair(pair, selected) > 0:
            selected = pair
    return selected


def _weakest_pair(values):
    selected = None
    for pair in values:
        if selected is None or compare_pair(pair, selected) < 0:
            selected = pair
    return selected


def recompute_bounds(record):
    pairs = canonical_pairs(record["candidate_ladder"])
    run_pair_verdicts = {}
    for task in record["tasks"]:
        try:
            pair = parse_pair(task.get("executed_pair"))
        except (TypeError, ValueError):
            continue
        if pair not in pairs:
            continue
        verdict = task_verdict(task)
        task["effective_verdict"] = verdict
        key = (pair, task.get("run_id"))
        if verdict == "fail":
            run_pair_verdicts[key] = "fail"
        elif verdict == "pass" and run_pair_verdicts.get(key) != "fail":
            run_pair_verdicts[key] = "pass"
    verdicts = {}
    for (pair, _), verdict in run_pair_verdicts.items():
        if verdict == "fail":
            verdicts[pair] = "fail"
        elif verdicts.get(pair) != "fail":
            verdicts[pair] = "pass"
    failures = [pair for pair, verdict in verdicts.items() if verdict == "fail"]
    strongest_failure = _strongest_pair(failures)
    success_candidates = [
        pair for pair, verdict in verdicts.items()
        if verdict == "pass" and (strongest_failure is None or compare_pair(pair, strongest_failure) > 0)
    ]
    record["failed_model"] = pair_text(*strongest_failure) if strongest_failure is not None else None
    record["success_model"] = pair_text(*_weakest_pair(success_candidates)) if success_candidates else None


def _pairs_between_bounds(pairs, hard_floor, failure_pair):
    floor = hard_floor
    def _within(pair):
        if compare_pair(pair, floor) < 0:
            return False
        if failure_pair is None:
            return True
        return compare_pair(pair, failure_pair) > 0
    return [pair for pair in pairs if _within(pair)]


def _passes_within(pairs, record):
    passing = set()
    for task in record["tasks"]:
        if task_verdict(task) != "pass":
            continue
        try:
            pair = parse_pair(task.get("executed_pair"))
        except (TypeError, ValueError):
            continue
        if pair in pairs:
            passing.add(pair)
    return passing


def _pair_verdict(record, target_pair):
    result = None
    for task in record["tasks"]:
        try:
            pair = parse_pair(task.get("executed_pair"))
        except (TypeError, ValueError):
            continue
        if pair != target_pair:
            continue
        verdict = task_verdict(task)
        if verdict == "fail":
            return "fail"
        if verdict == "pass":
            result = "pass"
    return result


def _has_unverified_quality_failure(record):
    return any(task.get("allowlisted_failure_class") in QUALITY_FAILURES and task.get("receipt_status") != "pass" for task in record["tasks"])


def _first_eligible_after_failure(failure_pair, eligible_pairs):
    candidate = upgrade_pair(failure_pair, eligible_pairs)
    if candidate is None:
        return None
    return candidate


def _first_eligible_below_pair(pair, eligible_pairs, hard_floor):
    candidate = downgrade_pair(pair, eligible_pairs)
    if candidate is None or compare_pair(candidate, hard_floor) < 0:
        return None
    return candidate


def _pick_weakest_passing_above_failure(pairs, failure_pair, hard_floor, record):
    candidates = _pairs_between_bounds(pairs, hard_floor, failure_pair)
    passing_pairs = _passes_within(candidates, record)
    for pair in pairs:
        if pair in passing_pairs:
            return pair
    return None


def _weakest_untested_between(failure_pair, success_pair, record, pairs):
    if failure_pair is None or success_pair is None:
        return None
    if compare_pair(success_pair, failure_pair) <= 0:
        return None
    for pair in pairs:
        if compare_pair(pair, failure_pair) <= 0:
            continue
        if compare_pair(pair, success_pair) >= 0:
            break
        if _pair_verdict(record, pair) is None:
            return pair
    return None


def _has_untested_between(failure_pair, success_pair, record, pairs):
    return _weakest_untested_between(failure_pair, success_pair, record, pairs) is not None


def recommend_route(args):
    condition, summary, pairs, static_pair, hard_pair = _profile(args)
    def recommend(history):
        record = _record_for(history, condition, summary, pairs, static_pair, hard_pair)
        recompute_bounds(record)
        failure_pair = parse_pair(record["failed_model"]) if record["failed_model"] else None
        success_pair = parse_pair(record["success_model"]) if record["success_model"] else None

        eligible_pairs = _pairs_between_bounds(pairs, hard_pair, failure_pair)
        if not eligible_pairs:
            reason = "quality_failure_boundary_exhausted" if failure_pair is not None else "no_bounds_use_static"
            return {"schema_version": SCHEMA_VERSION, "condition": condition, "selected_model": None, "selected_effort": None, "selected_pair": None, "reason": reason, "trial": False, "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": record["success_model"], "failed_model": record["failed_model"], "samples": len(record["tasks"])}

        static_eligible = static_pair in eligible_pairs
        tiny = ("gpt-5.3-codex-spark", "low") if condition["risk"] == "low" and condition["modality"] == "text" and condition["task_family"] in {"tiny_text", "tiny_code", "command_generation"} and ("gpt-5.3-codex-spark", "low") in pairs else None
        tiny_runtime_failure = bool(tiny and any(task.get("operational_failure_pairs") for task in record["tasks"]))

        selected = None
        reason = "no_bounds_use_static"
        trial = False

        if failure_pair is None and success_pair is None:
            if condition["risk"] == "high":
                selected = static_pair if static_eligible else pairs[-1]
                reason = "high_risk_no_autodowngrade"
            elif failure_pair is None and success_pair is None and tiny and not tiny_runtime_failure:
                selected = tiny
                reason = "tiny_spark_auto"
            else:
                selected = static_pair if static_eligible else pairs[0]
                reason = "no_bounds_use_static"
        elif failure_pair is None and success_pair is not None:
            if tiny_runtime_failure or _has_unverified_quality_failure(record):
                selected = static_pair if static_eligible else eligible_pairs[0]
                reason = "operational_failure_static_fallback" if tiny_runtime_failure else "quality_failure_receipt_unverified"
            elif condition["risk"] == "high":
                selected = static_pair if static_eligible else pairs[-1]
                reason = "high_risk_no_autodowngrade"
            elif success_pair == hard_pair:
                floor_has_real_evidence = any(
                    task_verdict(task) == "pass"
                    and task.get("real_status") == "pass"
                    and task.get("executed_pair") == pair_text(*hard_pair)
                    for task in record["tasks"]
                )
                selected = static_pair if floor_has_real_evidence and static_eligible else success_pair
                reason = "no_bounds_use_static" if selected != success_pair else "verified_floor_retained"
            else:
                selected = _first_eligible_below_pair(success_pair, eligible_pairs, hard_pair)
                if selected is None:
                    selected = static_pair if static_eligible else pairs[-1]
                    reason = "success_boundary_exhausted"
                else:
                    reason = "success_boundary_trial"
                    trial = True
        elif failure_pair is not None and success_pair is None:
            selected = _first_eligible_after_failure(failure_pair, eligible_pairs)
            if selected is None:
                reason = "quality_failure_boundary_exhausted"
            else:
                reason = "failure_and_success_boundary"
                trial = True
        else:
            selected = _pick_weakest_passing_above_failure(pairs, failure_pair, hard_pair, record)
            if selected is None:
                selected = _first_eligible_after_failure(failure_pair, eligible_pairs)
                if selected is None:
                    reason = "quality_failure_boundary_exhausted"
                    selected = None
                else:
                    reason = "failure_and_success_boundary"
                    trial = True
            else:
                intermediate = _weakest_untested_between(failure_pair, selected, record, pairs)
                if intermediate is not None:
                    selected = intermediate
                    reason = "success_and_failure_boundary"
                    trial = True
                else:
                    reason = "success_and_failure_boundary"
                    trial = False
            if selected is None:
                return {"schema_version": SCHEMA_VERSION, "condition": condition, "selected_model": None, "selected_effort": None, "selected_pair": None, "reason": reason, "trial": False, "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": record["success_model"], "failed_model": record["failed_model"], "samples": len(record["tasks"])}
        return {"schema_version": SCHEMA_VERSION, "condition": condition, "selected_model": selected[0], "selected_effort": selected[1], "selected_pair": pair_text(*selected), "reason": reason, "trial": trial, "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": record["success_model"], "failed_model": record["failed_model"], "samples": len(record["tasks"])}
    return _history_locked(args.history, recommend)[1]


def _receipt_pair(receipt, prefix, fallback=None):
    direct_pair = receipt.get(f"{prefix}_pair")
    if direct_pair is not None:
        return parse_pair(direct_pair)
    fallback_model, fallback_effort = fallback or (None, None)
    model = receipt.get(f"{prefix}_model") or fallback_model
    effort = receipt.get(f"{prefix}_effort") or fallback_effort
    return parse_pair(pair_text(model, effort))


def _operational_failure_pairs(receipt):
    route_attempts = receipt.get("route_attempts")
    if not isinstance(route_attempts, list):
        return []
    pairs = []
    for attempt in route_attempts:
        if not isinstance(attempt, dict) or attempt.get("status") not in {"fail", "failed"} or attempt.get("failure_class") not in RUNTIME_FAILURES:
            continue
        try:
            executed = _receipt_pair(attempt, "executed", None)
        except (TypeError, ValueError):
            continue
        if executed is None:
            continue
        text = pair_text(*executed)
        if text not in pairs:
            pairs.append(text)
    return canonical_pair_texts(pairs)


def record_event(args):
    condition, summary, pairs, static_pair, hard_pair = _profile(args)
    if args.verify_level not in {"mini", "real"} or args.verify_status not in {"pass", "fail", "unknown"} or args.failure_class not in QUALITY_FAILURES | RUNTIME_FAILURES | {"none"}:
        raise ValueError("verification evidence is invalid")
    receipt = json.loads(Path(args.receipt).expanduser().resolve().read_text(encoding="utf-8"))
    requested = _receipt_pair(receipt, "requested")
    resolved = _receipt_pair(receipt, "resolved", requested)
    effective = _receipt_pair(receipt, "effective", resolved)
    executed = _receipt_pair(receipt, "executed", effective)
    if requested not in pairs or executed not in pairs:
        raise ValueError("receipt pair is not in candidate_ladder")
    run_id = str(args.run_id or f"run_{os.urandom(8).hex()}")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be sanitized")
    def record(history):
        record = _record_for(history, condition, summary, pairs, static_pair, hard_pair)
        existing = next((task for task in record["tasks"] if task["run_id"] == run_id), None)
        task = existing or {"run_id": run_id, "summary": summary, "requested_pair": pair_text(*requested), "resolved_pair": pair_text(*resolved), "effective_pair": pair_text(*effective), "executed_pair": pair_text(*executed), "operational_failure_pairs": [], "receipt_status": "fail", "mini_status": "unknown", "real_status": "unknown", "effective_verdict": None, "allowlisted_failure_class": "none", "turn_completed": False, "model_match": False, "effort_match": False, "trial": bool(args.trial), "token_totals": {}, "process_ms": None, "recorded_at": datetime.now(timezone.utc).isoformat()}
        operational_pairs = _operational_failure_pairs(receipt)
        if args.failure_class in RUNTIME_FAILURES and args.verify_status == "fail":
            operational_pairs.append(pair_text(*executed))
        existing_pairs = _parse_optional_pairs(task.get("operational_failure_pairs", []))
        task["operational_failure_pairs"] = canonical_pair_texts(_dedupe_pairs(existing_pairs + operational_pairs))
        previous_verdict = task_verdict(task) if existing is not None else None
        previous_receipt_status = task.get("receipt_status") if existing is not None else None
        previous_mini_pass = existing is not None and task.get("mini_status") == "pass"
        task["turn_completed"] = bool(receipt.get("turn_completed") is True)
        task["model_match"] = bool(receipt.get("model_match") is True)
        task["effort_match"] = bool(receipt.get("effort_match") is True)
        task["receipt_status"] = "pass" if receipt.get("status") == "pass" and task["turn_completed"] and task["model_match"] and task["effort_match"] else "fail"
        receipt_is_valid = bool(
            receipt.get("status") == "pass"
            and receipt.get("turn_completed") is True
            and receipt.get("model_match") is True
            and receipt.get("effort_match") is True
        )
        preserve_primary_sample = existing is not None and (
            (args.failure_class in RUNTIME_FAILURES and args.verify_status == "fail")
            or (
                args.failure_class in QUALITY_FAILURES
                and args.verify_status == "fail"
                and not receipt_is_valid
                and (previous_verdict == "fail" or previous_receipt_status == "pass")
            )
        )
        preserve_identity = existing is not None and (
            (args.failure_class in RUNTIME_FAILURES and args.verify_status == "fail")
            or (
                args.failure_class in QUALITY_FAILURES
                and args.verify_status == "fail"
                and not receipt_is_valid
                and (previous_verdict == "pass" or previous_mini_pass)
                and previous_receipt_status == "pass"
            )
        )
        update_metrics = not preserve_primary_sample
        if not preserve_identity:
            task["requested_pair"] = pair_text(*requested)
            task["resolved_pair"] = pair_text(*resolved)
            task["effective_pair"] = pair_text(*effective)
            task["executed_pair"] = pair_text(*executed)
        status_field = f"{args.verify_level}_status"
        if task.get(status_field) != "fail" or task.get("allowlisted_failure_class") not in QUALITY_FAILURES:
            task[status_field] = args.verify_status
        if args.failure_class in QUALITY_FAILURES or task["allowlisted_failure_class"] not in QUALITY_FAILURES:
            task["allowlisted_failure_class"] = args.failure_class
        if update_metrics:
            tokens = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
            task["token_totals"] = {"input": _safe_int(tokens.get("input_tokens")), "cached_input": _safe_int(tokens.get("cached_input_tokens")), "output": _safe_int(tokens.get("output_tokens")), "reasoning_output": _safe_int(tokens.get("reasoning_output_tokens")), "total": _safe_int(tokens.get("total_tokens"))}
            task["process_ms"] = _safe_int(receipt.get("process_elapsed_ms"))
        if not existing:
            record["tasks"].append(task)
        recompute_bounds(record)
        return {"status": "recorded", "route_run_id": run_id, "receipt_status": task["receipt_status"], "verify_level": args.verify_level, "verify_status": args.verify_status}
    return _history_locked(args.history, record)[1]


def status(history_path):
    history_path = Path(history_path).expanduser().resolve()
    if not history_path.exists():
        _write_locked(history_path, empty_history())
    history = _history_locked(history_path)[0]
    return {"schema_version": SCHEMA_VERSION, "conditions": len(history["conditions"]), "tasks": sum(len(record["tasks"]) for record in history["conditions"].values())}


def _profile(args):
    condition = validate_condition(vars(args), allow_history_only=False)
    summary = validate_summary(args.task_summary)
    pairs = canonical_pairs(args.candidate_ladder)
    static_pair, hard_pair = parse_pair(args.static_suggestion), parse_pair(args.hard_floor)
    if static_pair not in pairs or hard_pair not in pairs:
        raise ValueError("static_suggestion and hard_floor must be in candidate_ladder")
    return condition, summary, pairs, static_pair, hard_pair


def add_profile_arguments(parser):
    for option in ("task-family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "project-family", "verification-shape"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--owning-skill", required=True, dest="owning_skill")
    parser.add_argument(
        "--execution-domain",
        choices=tuple(
            domain
            for domain, metadata in EXECUTION_DOMAINS.items()
            if metadata.get("active") and not metadata.get("history_only")
        ),
    )
    parser.add_argument("--task-summary", required=True)
    parser.add_argument("--candidate-ladder", action="append", required=True)
    parser.add_argument("--static-suggestion", required=True)
    parser.add_argument("--hard-floor", required=True)


def execution_domain_rows():
    return {
        "schema_version": 1,
        "registry_version": EXECUTION_DOMAIN_REGISTRY_VERSION,
        "rows": public_execution_domain_rows(),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Maintain privacy-safe adaptive-routing experience")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    recommend = commands.add_parser("recommend")
    record = commands.add_parser("record")
    commands.add_parser("domains")
    add_profile_arguments(recommend)
    add_profile_arguments(record)
    record.add_argument("--receipt", required=True)
    record.add_argument("--verify-level", required=True)
    record.add_argument("--verify-status", required=True)
    record.add_argument("--failure-class", default="none")
    record.add_argument("--run-id")
    record.add_argument("--trial", action="store_true")
    commands.add_parser("status")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "recommend":
        value = recommend_route(args)
    elif args.command == "record":
        value = record_event(args)
    elif args.command == "domains":
        value = execution_domain_rows()
    else:
        value = status(args.history)
    print(json.dumps(value, separators=(",", ":")))


if __name__ == "__main__":
    main()

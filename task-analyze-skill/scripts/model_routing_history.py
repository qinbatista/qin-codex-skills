#!/usr/bin/env python3
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from statistics import median
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkstemp


RECEIPT_PATH = Path(__file__).resolve().parent / "model_execution_receipt.py"
RECEIPT_SPEC = importlib.util.spec_from_file_location("task_analyze_model_execution_receipt", RECEIPT_PATH)
receipt_module = importlib.util.module_from_spec(RECEIPT_SPEC)
RECEIPT_SPEC.loader.exec_module(receipt_module)
MODEL_EFFORTS = receipt_module.MODEL_EFFORTS
MODEL_EFFORT_ORDER = {
    "gpt-5.3-codex-spark": ["low", "medium", "high", "xhigh"],
    "gpt-5.6-luna": ["low", "medium", "high", "xhigh", "max"],
    "gpt-5.6-terra": ["low", "medium", "high", "xhigh", "max", "ultra"],
    "gpt-5.6-sol": ["low", "medium", "high", "xhigh", "max", "ultra"],
}

DEFAULT_HISTORY_PATH = Path(__file__).resolve().parents[1] / "local" / "adaptive-routing" / "model_experience.json"
SCHEMA_VERSION = 2
MODEL_ORDER = ["gpt-5.3-codex-spark", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"]
EFFORT_ORDER = ["low", "medium", "high", "xhigh", "max", "ultra"]
CONTROL_FIELDS = ["task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "owning_skill", "project_family", "verification_shape"]
CONTROL_ENUMS = {
    "task_family": {"code", "direct", "grounded", "integration", "visual", "management", "prompt", "document", "data", "safety", "legacy", "tiny_text", "tiny_code", "command_generation", "other"},
    "artifact": {"answer", "script", "note", "report", "evidence", "document", "patch", "log", "legacy"},
    "scope": {"single", "multi", "project"},
    "ambiguity": {"low", "medium", "high"},
    "modality": {"text", "image", "mixed"},
    "risk": {"low", "medium", "high"},
    "complexity": {"easy", "complex"},
    "verification_shape": {"mini_real", "mini", "real", "result"},
}
QUALITY_FAILURES = {"quality", "correctness"}
RUNTIME_FAILURES = {"availability", "timeout", "protocol", "telemetry", "execution", "receipt"}
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
FORBIDDEN_SUMMARY = [re.compile(r"```"), re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://"), re.compile(r"(?:^|\s)/[^\s]+"), re.compile(r"\b(?:api|auth|secret|password|token)[_-]?(?:key|token|secret|password)?\s*[:=]", re.I)]


def pair_text(model, effort):
    return f"{model}|{effort}"


def parse_pair(value):
    if not isinstance(value, str):
        raise ValueError("model pair must be text")
    separator = "|" if "|" in value else ":"
    model, separator_found, effort = value.strip().partition(separator)
    if not separator_found or model not in MODEL_EFFORTS or effort not in MODEL_EFFORTS[model]:
        raise ValueError("unsupported model pair")
    return model, effort


def pair_rank(pair):
    effort_rank = MODEL_EFFORT_ORDER[pair[0]].index(pair[1])
    return MODEL_ORDER.index(pair[0]) * len(EFFORT_ORDER) + effort_rank


def canonical_pairs(values):
    pairs = [parse_pair(value) for value in values]
    if not pairs or len(set(pairs)) != len(pairs):
        raise ValueError("candidate_ladder must contain unique pairs")
    return sorted(pairs, key=pair_rank)


def sanitize_slug(value):
    value = str(value).strip().lower()
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError("condition values must be short lowercase slugs")
    return value


def validate_condition(values):
    if not isinstance(values, dict):
        raise ValueError("routing condition must be a mapping")
    condition = {field: sanitize_slug(values[field]) for field in CONTROL_FIELDS}
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


def condition_key(condition):
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
        raw_condition = {"task_family": event.get("task_family", event.get("category", "legacy")), "artifact": event.get("artifact", "legacy"), "scope": event.get("scope", event.get("phase", "result")), "ambiguity": event.get("ambiguity", "medium"), "modality": event.get("modality", "text"), "risk": event.get("risk", "low"), "complexity": event.get("complexity", "easy"), "owning_skill": event.get("owning_skill", "workflow-skill"), "project_family": event.get("project_family", "legacy"), "verification_shape": event.get("verification_shape", event.get("phase", "result"))}
        try:
            condition = validate_condition(raw_condition)
        except ValueError:
            continue
        key = condition_key(condition)
        record = history["conditions"].setdefault(key, {"condition": condition, "summary": "Legacy adaptive-routing evidence imported without task content.", "candidate_ladder": [], "static_suggestion": pair_text(*executed), "hard_floor": pair_text(*executed), "success_model": None, "failed_model": None, "tasks": []})
        for pair in (requested, executed):
            text = pair_text(*pair)
            if text not in record["candidate_ladder"]:
                record["candidate_ladder"].append(text)
        status = event.get("verify_status") if event.get("verify_status") in {"pass", "fail"} else "unknown"
        failure_class = event.get("failure_class", "none")
        task = {"run_id": f"legacy_{os.urandom(8).hex()}", "summary": "Legacy adaptive-routing evidence imported without task content.", "executed_pair": pair_text(*executed), "receipt_status": "pass" if event.get("receipt_status") == "pass" else "fail", "mini_status": status if event.get("verify_level") == "mini" else "unknown", "real_status": status if event.get("verify_level") == "real" else "unknown", "effective_verdict": None, "allowlisted_failure_class": failure_class if failure_class in QUALITY_FAILURES | RUNTIME_FAILURES else "none", "turn_completed": bool(event.get("turn_completed") is True or event.get("receipt_status") == "pass"), "model_match": True, "effort_match": True, "trial": bool(event.get("trial")), "token_totals": {"input": None, "cached_input": None, "output": None, "reasoning_output": None, "total": None}, "process_ms": None, "recorded_at": event.get("recorded_at") or datetime.now(timezone.utc).isoformat()}
        record["tasks"].append(task)
    for record in history["conditions"].values():
        record["candidate_ladder"] = [pair_text(*pair) for pair in canonical_pairs(record["candidate_ladder"])]
        recompute_bounds(record)
    return history


def _history_locked(path, mutate=None):
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(path.parent, 0o700)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        history = _read_json(path)
        if not isinstance(history, dict) or history.get("schema_version") != SCHEMA_VERSION or not isinstance(history.get("conditions"), dict):
            history = _legacy_history(path.with_name("events.jsonl"))
        value = mutate(history) if mutate else None
        _write_locked(path, history)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return history, value


def load_history(path):
    return _history_locked(path)[0]


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


def recompute_bounds(record):
    pairs = canonical_pairs(record["candidate_ladder"])
    run_pair_verdicts = {}
    for task in record["tasks"]:
        try:
            index = pairs.index(parse_pair(task.get("executed_pair")))
        except ValueError:
            continue
        verdict = task_verdict(task)
        task["effective_verdict"] = verdict
        run_id = task.get("run_id")
        key = (index, run_id)
        if verdict == "fail":
            run_pair_verdicts[key] = "fail"
        elif verdict == "pass" and run_pair_verdicts.get(key) != "fail":
            run_pair_verdicts[key] = "pass"
    verdicts = {}
    for (index, _), verdict in run_pair_verdicts.items():
        if verdict == "fail":
            verdicts[index] = "fail"
            continue
        if verdicts.get(index) != "fail":
            verdicts[index] = "pass"
    failures = [index for index, verdict in verdicts.items() if verdict == "fail"]
    strongest_failure = max(failures) if failures else None
    successes = [index for index, verdict in verdicts.items() if verdict == "pass" and (strongest_failure is None or index > strongest_failure)]
    record["failed_model"] = pair_text(*pairs[strongest_failure]) if strongest_failure is not None else None
    record["success_model"] = pair_text(*pairs[min(successes)]) if successes else None


def _record_for(history, condition, summary, pairs, static_pair, hard_pair):
    key = condition_key(condition)
    record = history["conditions"].setdefault(key, {"condition": condition, "summary": summary, "candidate_ladder": [pair_text(*pair) for pair in pairs], "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": None, "failed_model": None, "tasks": []})
    record["condition"] = condition
    record["summary"] = summary
    retained_pairs = list(record.get("candidate_ladder", []))
    retained_pairs.extend(pair_text(*pair) for pair in pairs)
    merged_pairs = []
    for value in retained_pairs:
        if value not in merged_pairs:
            merged_pairs.append(value)
    record["candidate_ladder"] = [pair_text(*pair) for pair in canonical_pairs(merged_pairs)]
    record["static_suggestion"] = pair_text(*static_pair)
    record["hard_floor"] = pair_text(*hard_pair)
    return record


def _profile(args):
    condition = validate_condition(vars(args))
    summary = validate_summary(args.task_summary)
    pairs = canonical_pairs(args.candidate_ladder)
    static_pair, hard_pair = parse_pair(args.static_suggestion), parse_pair(args.hard_floor)
    if static_pair not in pairs or hard_pair not in pairs:
        raise ValueError("static_suggestion and hard_floor must be in candidate_ladder")
    return condition, summary, pairs, static_pair, hard_pair


def recommend_route(args):
    condition, summary, pairs, static_pair, hard_pair = _profile(args)
    def recommend(history):
        record = _record_for(history, condition, summary, pairs, static_pair, hard_pair)
        recompute_bounds(record)
        hard_floor_rank = pair_rank(hard_pair)
        static_rank = pair_rank(static_pair)
        failure_pair = parse_pair(record["failed_model"]) if record["failed_model"] else None
        success_pair = parse_pair(record["success_model"]) if record["success_model"] else None
        failure_rank = pair_rank(failure_pair) if failure_pair else None
        success_rank = pair_rank(success_pair) if success_pair else None
        current_indices_above_failure = [index for index, pair in enumerate(pairs) if failure_rank is not None and pair_rank(pair) > failure_rank]
        eligible_indices = [index for index, pair in enumerate(pairs) if pair_rank(pair) >= hard_floor_rank and (failure_rank is None or pair_rank(pair) > failure_rank)]
        tiny = ("gpt-5.3-codex-spark", "low") if condition["risk"] == "low" and condition["modality"] == "text" and condition["task_family"] in {"tiny_text", "tiny_code", "command_generation"} and ("gpt-5.3-codex-spark", "low") in pairs else None
        tiny_runtime_failure = tiny and any(pair_text(*tiny) in task.get("operational_failure_pairs", []) for task in record["tasks"])
        selected = None
        reason = "no_bounds_use_static"
        trial = False
        if failure_rank is not None and not current_indices_above_failure:
            reason = "quality_failure_boundary_exhausted"
        elif condition["risk"] == "high":
            if failure_rank is not None:
                high_risk_indices = [index for index in eligible_indices if pair_rank(pairs[index]) >= static_rank]
                if high_risk_indices:
                    selected, reason = high_risk_indices[0], "high_risk_promote_above_failure"
                else:
                    reason = "quality_failure_boundary_exhausted"
            else:
                selected, reason = pairs.index(static_pair), "high_risk_no_autodowngrade"
        elif failure_rank is None and success_rank is None and tiny and not tiny_runtime_failure:
            selected, reason = pairs.index(tiny), "tiny_spark_auto"
        elif failure_rank is None and success_rank is None:
            selected, reason = pairs.index(static_pair), "no_bounds_use_static"
        elif failure_rank is None:
            weaker_indices = [index for index, pair in enumerate(pairs) if pair_rank(pair) < success_rank and pair_rank(pair) >= hard_floor_rank]
            if weaker_indices:
                if tiny and tiny_runtime_failure:
                    weaker_indices = [index for index in weaker_indices if pairs[index] != tiny]
                if weaker_indices:
                    selected, reason, trial = weaker_indices[-1], "success_boundary_trial", True
                else:
                    selected, reason, trial = pairs.index(static_pair), "success_boundary_exhausted", False
            else:
                selected, reason = pairs.index(static_pair), "success_boundary_exhausted"
        elif success_rank is None:
            promoted_indices = [index for index in eligible_indices if pair_rank(pairs[index]) >= static_rank]
            if promoted_indices:
                selected, reason, trial = promoted_indices[0], "failure_boundary_promoted", True
            else:
                reason = "quality_failure_boundary_exhausted"
        else:
            passing_indices = []
            for index in eligible_indices:
                candidate_pair = pair_text(*pairs[index])
                if any(task.get("executed_pair") == candidate_pair and task_verdict(task) == "pass" for task in record["tasks"]):
                    passing_indices.append(index)
            if not passing_indices:
                selected, reason, trial = eligible_indices[0], "failure_and_success_boundary", True
            else:
                performance = {}
                complete_performance = True
                for index in passing_indices:
                    candidate_pair = pair_text(*pairs[index])
                    candidate_tasks = [task for task in record["tasks"] if task.get("executed_pair") == candidate_pair and task_verdict(task) == "pass"]
                    token_values = [task.get("token_totals", {}).get("total") for task in candidate_tasks if _safe_int(task.get("token_totals", {}).get("total")) is not None]
                    process_values = [task.get("process_ms") for task in candidate_tasks if _safe_int(task.get("process_ms")) is not None]
                    if not token_values or not process_values:
                        complete_performance = False
                    performance[index] = (median(token_values) if token_values else None, median(process_values) if process_values else None)
                if complete_performance:
                    selected = min(passing_indices, key=lambda index: (performance[index][0], performance[index][1], pair_rank(pairs[index])))
                    reason = "performance_ranked"
                else:
                    selected, reason = min(passing_indices, key=lambda index: pair_rank(pairs[index])), "performance_nearest_weaker"
        if selected is None:
            return {"schema_version": SCHEMA_VERSION, "condition": condition, "selected_model": None, "selected_effort": None, "selected_pair": None, "reason": reason, "trial": False, "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": record["success_model"], "failed_model": record["failed_model"], "samples": len(record["tasks"])}
        return {"schema_version": SCHEMA_VERSION, "condition": condition, "selected_model": pairs[selected][0], "selected_effort": pairs[selected][1], "selected_pair": pair_text(*pairs[selected]), "reason": reason, "trial": trial, "static_suggestion": pair_text(*static_pair), "hard_floor": pair_text(*hard_pair), "success_model": record["success_model"], "failed_model": record["failed_model"], "samples": len(record["tasks"])}
    return _history_locked(args.history, recommend)[1]


def _receipt_pair(receipt, prefix, fallback=None):
    direct_pair = receipt.get(f"{prefix}_pair")
    if direct_pair is not None:
        return parse_pair(direct_pair)
    fallback_model, fallback_effort = fallback or (None, None)
    model = receipt.get(f"{prefix}_model") or fallback_model
    effort = receipt.get(f"{prefix}_effort") or fallback_effort
    return parse_pair(pair_text(model, effort))


def _receipt_pairs(receipt):
    requested = _receipt_pair(receipt, "requested")
    resolved = _receipt_pair(receipt, "resolved", requested)
    effective = _receipt_pair(receipt, "effective", resolved)
    executed = _receipt_pair(receipt, "executed", effective)
    return requested, resolved, effective, executed


def _operational_failure_pairs(receipt):
    route_attempts = receipt.get("route_attempts")
    if not isinstance(route_attempts, list):
        return []
    pairs = []
    for attempt in route_attempts:
        if not isinstance(attempt, dict) or attempt.get("status") not in {"fail", "failed"} or attempt.get("failure_class") not in RUNTIME_FAILURES:
            continue
        try:
            _, _, _, executed = _receipt_pairs(attempt)
        except (TypeError, ValueError):
            continue
        pair = pair_text(*executed)
        if pair not in pairs:
            pairs.append(pair)
    return [pair_text(*pair) for pair in canonical_pairs(pairs)] if pairs else []


def record_event(args):
    condition, summary, pairs, static_pair, hard_pair = _profile(args)
    if args.verify_level not in {"mini", "real"} or args.verify_status not in {"pass", "fail", "unknown"} or args.failure_class not in QUALITY_FAILURES | RUNTIME_FAILURES | {"none"}:
        raise ValueError("verification evidence is invalid")
    receipt = json.loads(Path(args.receipt).expanduser().resolve().read_text(encoding="utf-8"))
    requested, resolved, effective, executed = _receipt_pairs(receipt)
    if requested not in pairs or executed not in pairs:
        raise ValueError("receipt pair is not in candidate_ladder")
    run_id = str(args.run_id or f"run_{os.urandom(8).hex()}")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be sanitized")
    def record(history):
        record = _record_for(history, condition, summary, pairs, static_pair, hard_pair)
        existing = next((task for task in record["tasks"] if task["run_id"] == run_id), None)
        task = existing or {"run_id": run_id, "summary": summary, "requested_pair": pair_text(*requested), "resolved_pair": pair_text(*resolved), "effective_pair": pair_text(*effective), "executed_pair": pair_text(*executed), "operational_failure_pairs": [], "receipt_status": "fail", "mini_status": "unknown", "real_status": "unknown", "effective_verdict": None, "allowlisted_failure_class": "none", "turn_completed": False, "model_match": False, "effort_match": False, "trial": bool(args.trial), "token_totals": {}, "process_ms": None, "recorded_at": datetime.now(timezone.utc).isoformat()}
        task["requested_pair"] = pair_text(*requested)
        task["resolved_pair"] = pair_text(*resolved)
        task["effective_pair"] = pair_text(*effective)
        task["executed_pair"] = pair_text(*executed)
        operational_pairs = _operational_failure_pairs(receipt)
        if args.failure_class in RUNTIME_FAILURES and args.verify_status == "fail":
            operational_pairs.append(pair_text(*executed))
        task["operational_failure_pairs"] = sorted(set(task.get("operational_failure_pairs", [])) | set(operational_pairs), key=lambda value: pair_rank(parse_pair(value)))
        task["turn_completed"] = bool(receipt.get("turn_completed") is True)
        task["model_match"] = bool(receipt.get("model_match") is True)
        task["effort_match"] = bool(receipt.get("effort_match") is True)
        task["receipt_status"] = "pass" if receipt.get("status") == "pass" and task["turn_completed"] and task["model_match"] and task["effort_match"] else "fail"
        status_field = f"{args.verify_level}_status"
        if task.get(status_field) != "fail" or task.get("allowlisted_failure_class") not in QUALITY_FAILURES:
            task[status_field] = args.verify_status
        if args.failure_class in QUALITY_FAILURES or task["allowlisted_failure_class"] not in QUALITY_FAILURES:
            task["allowlisted_failure_class"] = args.failure_class
        tokens = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
        task["token_totals"] = {"input": _safe_int(tokens.get("input_tokens")), "cached_input": _safe_int(tokens.get("cached_input_tokens")), "output": _safe_int(tokens.get("output_tokens")), "reasoning_output": _safe_int(tokens.get("reasoning_output_tokens")), "total": _safe_int(tokens.get("total_tokens"))}
        task["process_ms"] = _safe_int(receipt.get("process_elapsed_ms"))
        if not existing:
            record["tasks"].append(task)
        recompute_bounds(record)
        return {"status": "recorded", "route_run_id": run_id, "receipt_status": task["receipt_status"], "verify_level": args.verify_level, "verify_status": args.verify_status}
    return _history_locked(args.history, record)[1]


def status(history_path):
    history = _history_locked(history_path)[0]
    return {"schema_version": SCHEMA_VERSION, "conditions": len(history["conditions"]), "tasks": sum(len(record["tasks"]) for record in history["conditions"].values())}


def add_profile_arguments(parser):
    for option in ("task-family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "project-family", "verification-shape"):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--owning-skill", required=True, dest="owning_skill")
    parser.add_argument("--task-summary", required=True)
    parser.add_argument("--candidate-ladder", action="append", required=True)
    parser.add_argument("--static-suggestion", required=True)
    parser.add_argument("--hard-floor", required=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Maintain privacy-safe adaptive-routing experience")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    recommend = commands.add_parser("recommend")
    record = commands.add_parser("record")
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
    value = recommend_route(args) if args.command == "recommend" else record_event(args) if args.command == "record" else status(args.history)
    print(json.dumps(value, separators=(",", ":")))


if __name__ == "__main__":
    main()

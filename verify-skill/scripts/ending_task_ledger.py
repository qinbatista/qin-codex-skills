#!/usr/bin/env python3
import argparse
import fcntl
import hashlib
import importlib.util
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


DEFAULT_STORE = Path.home() / ".codex" / "ending-task-memory"
DEFAULT_MAX_REPAIR_ATTEMPTS = 3
SCHEMA_VERSION = 1
TERMINAL_EVENTS = {"pass", "fail", "blocked"}
ALL_EVENTS = TERMINAL_EVENTS | {"note"}
FAILURE_CLASSES = {"none", "availability", "timeout", "protocol", "telemetry", "execution", "receipt", "quality", "correctness"}
MODEL_CONTEXT_FIELDS = ("project_root", "task_type", "module", "file", "symbol", "code_kind", "operation", "modality", "complexity", "complexity_score", "complexity_band", "risk", "ambiguity", "task_summary")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _single_line(value, field_name, required=True, max_length=1200):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not text:
        raise ValueError(f"{field_name} is required")
    return text[:max_length]


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


def _producer_binding(receipt_value, project_root=None):
    if not receipt_value:
        return None
    receipt_path = Path(receipt_value).expanduser().resolve()
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    context = receipt.get("model_learning_context") if isinstance(receipt, dict) else None
    if not isinstance(context, dict) or set(context) != set(MODEL_CONTEXT_FIELDS):
        raise ValueError("producer receipt requires the exact sanitized model_learning_context fields")
    sanitized = {}
    for field in MODEL_CONTEXT_FIELDS:
        value = context[field]
        if field == "complexity_score":
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError("producer model_learning_context.complexity_score must be an integer from 0 to 100")
            sanitized[field] = value
            continue
        maximum = 1200 if field == "project_root" else 600 if field in {"file", "symbol", "task_summary"} else 160
        if not isinstance(value, str):
            raise ValueError(f"producer model_learning_context.{field} must be text")
        cleaned = _single_line(value, f"model_learning_context.{field}", required=field in {"project_root", "task_type", "module"}, max_length=maximum)
        if cleaned != value:
            raise ValueError(f"producer model_learning_context.{field} is not sanitized")
        sanitized[field] = cleaned
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
    return {"receipt_path": str(receipt_path), "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(), "model_learning_context": sanitized, "executed_pair": executed_pair, "status": "pending"}


def _load_model_memory_module():
    script_path = Path(__file__).resolve().parents[2] / "project-memory-skill" / "scripts" / "obsidian_model_memory.py"
    spec = importlib.util.spec_from_file_location("ending_task_obsidian_model_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _record_bound_model_result(binding, real_status, failure_class):
    receipt_path = Path(binding["receipt_path"])
    if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != binding["receipt_sha256"]:
        raise ValueError("bound producer receipt changed after lifecycle start")
    context = binding["model_learning_context"]
    memory = _load_model_memory_module()
    return memory.record_model_result(context["project_root"], context["task_type"], context["module"], receipt_path, real_status, failure_class, file_value=context["file"], symbol=context["symbol"], code_kind=context["code_kind"], operation=context["operation"], modality=context["modality"], complexity=context["complexity"], complexity_score=context["complexity_score"], risk=context["risk"], ambiguity=context["ambiguity"], task_summary=context["task_summary"], bound_receipt=binding)


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


def start_lifecycle(task_kind, cwd, summary, project_root=None, module="", files=None, repair_of_lifecycle_id="", store=DEFAULT_STORE, max_repair_attempts=DEFAULT_MAX_REPAIR_ATTEMPTS, producer_receipt=None, complexity_score=None, complexity_band="", verification_required=False, verification_plan=None, ending_check_id="", selected_pair=""):
    cwd_path = Path(cwd).expanduser().resolve()
    if not cwd_path.is_dir():
        raise ValueError("cwd must be an existing directory")
    producer_binding = _producer_binding(producer_receipt, project_root)
    project_path = Path(project_root).expanduser().resolve() if project_root else None
    if project_path is None and producer_binding:
        project_path = Path(producer_binding["model_learning_context"]["project_root"])
    if producer_binding:
        bound_score = producer_binding["model_learning_context"]["complexity_score"]
        bound_band = producer_binding["model_learning_context"]["complexity_band"]
        if complexity_score is not None and complexity_score != bound_score:
            raise ValueError("lifecycle complexity_score does not match producer receipt")
        if complexity_band and complexity_band != bound_band:
            raise ValueError("lifecycle complexity_band does not match producer receipt")
        complexity_score = bound_score
        complexity_band = bound_band
    elif complexity_score is not None:
        if isinstance(complexity_score, bool) or not 0 <= complexity_score <= 100:
            raise ValueError("complexity_score must be an integer from 0 to 100")
        expected_band = "small" if complexity_score <= 24 else "standard" if complexity_score <= 49 else "complex" if complexity_score <= 74 else "advanced"
        if complexity_band and complexity_band != expected_band:
            raise ValueError("complexity_band does not match complexity_score")
        complexity_band = expected_band
    normalized_files = _normalize_files(project_path, files or [])
    lifecycle_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:12]}"
    created_at = _now()
    store_path = Path(store).expanduser().resolve()
    store_path.mkdir(parents=True, exist_ok=True)
    lock_path = store_path / ".lock"
    with lock_path.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        parent = None
        root = None
        attempt_index = 0
        repair_limit = int(max_repair_attempts)
        if repair_limit < 0 or repair_limit > 10:
            raise ValueError("max_repair_attempts must be between 0 and 10")
        if repair_of_lifecycle_id:
            parent = _read_state(store_path, repair_of_lifecycle_id)
            if parent["status"] not in {"failed", "blocked"} or _has_limit_block(parent):
                raise ValueError("repair lifecycle requires a failed parent lifecycle or non-limit blocked parent lifecycle")
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
        verification_plan_path = Path(verification_plan).expanduser().resolve() if verification_plan else None
        if verification_required and (not verification_plan_path or not verification_plan_path.is_file()):
            raise ValueError("verification-required lifecycle requires an existing verification plan")
        event = {"schema_version": SCHEMA_VERSION, "event": "started", "recorded_at": created_at, "lifecycle_id": lifecycle_id, "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "summary": _single_line(summary, "summary"), "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": _single_line(ending_check_id, "ending_check_id", required=False, max_length=80) or None, "selected_pair": _single_line(selected_pair, "selected_pair", required=False, max_length=160) or None}
        state = {"schema_version": SCHEMA_VERSION, "lifecycle_id": lifecycle_id, "created_at": created_at, "updated_at": created_at, "status": "running", "task_kind": _single_line(task_kind, "task_kind", max_length=80), "cwd": str(cwd_path), "summary": event["summary"], "project_root": str(project_path) if project_path else None, "module": _single_line(module, "module", required=False, max_length=160), "files": normalized_files, "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": event["ending_check_id"], "selected_pair": event["selected_pair"], "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "attempt_index": attempt_index, "max_repair_attempts": repair_limit, "repair_children": [], "producer_binding": producer_binding, "events": [event]}
        if parent:
            parent_event = {"schema_version": SCHEMA_VERSION, "event": "repair_started", "recorded_at": created_at, "lifecycle_id": parent["lifecycle_id"], "child_lifecycle_id": lifecycle_id, "summary": f"Repair lifecycle {lifecycle_id} started"}
            parent["repair_children"].append(lifecycle_id)
            parent["events"].append(parent_event)
            parent["updated_at"] = created_at
            _write_state(store_path, parent)
            _append_event(store_path, parent_event)
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
    return {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": "running", "complexity_score": complexity_score, "complexity_band": complexity_band or None, "verification_required": bool(verification_required), "verification_plan": str(verification_plan_path) if verification_plan_path else None, "ending_check_id": event["ending_check_id"], "selected_pair": event["selected_pair"], "local": {"written": True, "store": str(store_path), "state": str(state_path)}}


def record_event(lifecycle_id, event_name, summary, verification=None, error_fingerprint="", store=DEFAULT_STORE, failure_class="none"):
    if event_name not in ALL_EVENTS:
        raise ValueError(f"event must be one of {', '.join(sorted(ALL_EVENTS))}")
    if failure_class not in FAILURE_CLASSES:
        raise ValueError(f"failure_class must be one of {', '.join(sorted(FAILURE_CLASSES))}")
    store_path = Path(store).expanduser().resolve()
    lock_path = store_path / ".lock"
    with lock_path.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        state = _read_state(store_path, lifecycle_id)
        if state["status"] != "running" and event_name != "note":
            prior_terminal = next((item for item in reversed(state["events"]) if item.get("event") in TERMINAL_EVENTS), None)
            if prior_terminal and prior_terminal.get("event") == event_name and prior_terminal.get("failure_class", "none") == failure_class:
                return {"status": "duplicate", "lifecycle_id": lifecycle_id, "lifecycle_status": state["status"], "model_learning": state.get("model_learning"), "local": {"written": True, "store": str(store_path), "state": str(_state_path(store_path, lifecycle_id))}}
            raise ValueError(f"lifecycle is already terminal: {state['status']}")
        binding = state.get("producer_binding")
        model_learning = None
        if binding and event_name in {"pass", "fail"}:
            if event_name == "pass" and failure_class != "none":
                raise ValueError("a bound Ending pass requires failure_class=none")
            if event_name == "fail" and failure_class == "none":
                raise ValueError("a bound Ending fail requires an explicit failure_class")
            model_learning = _record_bound_model_result(binding, event_name, failure_class)
            state["model_learning"] = model_learning
            state["producer_binding"]["status"] = "no-op" if _successful_model_learning_noop(model_learning) else "recorded" if model_learning.get("written") is True else "unavailable"
        recorded_at = _now()
        event = {"schema_version": SCHEMA_VERSION, "event": event_name, "recorded_at": recorded_at, "lifecycle_id": lifecycle_id, "summary": _single_line(summary, "summary"), "verification": [_single_line(value, "verification", max_length=600) for value in (verification or [])], "error_fingerprint": _single_line(error_fingerprint, "error_fingerprint", required=False, max_length=160) or None, "failure_class": failure_class if event_name in {"pass", "fail"} else None, "complexity_score": state.get("complexity_score"), "complexity_band": state.get("complexity_band")}
        if model_learning is not None:
            event["model_learning"] = model_learning
            event["switch_direction"] = model_learning.get("switch_direction")
            event["switch_reason"] = model_learning.get("switch_reason")
            event["next_pair"] = model_learning.get("next_pair")
        state["events"].append(event)
        state["updated_at"] = recorded_at
        if event_name in TERMINAL_EVENTS:
            state["status"] = {"pass": "passed", "fail": "failed", "blocked": "blocked"}[event_name]
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
    output = {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": state["status"], "final_gate_passed": event_name == "pass", "local": {"written": True, "store": str(store_path), "state": str(state_path)}}
    if model_learning is not None:
        output["model_learning"] = model_learning
    if event_name == "fail":
        output["repair_required"] = True
        output["repair_handoff"] = {"action": "create_repair_task_then_fresh_ending", "repair_of_lifecycle_id": lifecycle_id, "summary": event["summary"], "verification": event["verification"], "error_fingerprint": event["error_fingerprint"], "complexity_score": state.get("complexity_score"), "complexity_band": state.get("complexity_band"), "max_repair_attempts": state.get("max_repair_attempts")}
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
    return {"status": "pass" if terminal_status == "passed" else terminal_status, "root_lifecycle_id": root["lifecycle_id"], "active_lifecycle_id": active["lifecycle_id"], "terminal_status": terminal_status, "complexity_score": active.get("complexity_score"), "complexity_band": active.get("complexity_band"), "chain": chain, "descendants": [state["lifecycle_id"] for state in descendants], "final_gate_passed": terminal_status == "passed"}


def main():
    parser = argparse.ArgumentParser(description="Record mandatory post-result Ending Task lifecycles")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--task-kind", required=True)
    start_parser.add_argument("--cwd", type=Path, required=True)
    start_parser.add_argument("--summary", required=True)
    start_parser.add_argument("--project-root", type=Path)
    start_parser.add_argument("--module", default="")
    start_parser.add_argument("--file", action="append", default=[])
    start_parser.add_argument("--repair-of-lifecycle-id", default="")
    start_parser.add_argument("--max-repair-attempts", type=int, default=DEFAULT_MAX_REPAIR_ATTEMPTS)
    start_parser.add_argument("--producer-receipt", type=Path)
    start_parser.add_argument("--complexity-score", type=int)
    start_parser.add_argument("--complexity-band", choices=("small", "standard", "complex", "advanced"), default="")
    start_parser.add_argument("--verification-required", action="store_true")
    start_parser.add_argument("--verification-plan", type=Path)
    start_parser.add_argument("--ending-check-id", default="")
    start_parser.add_argument("--selected-pair", default="")
    event_parser = subparsers.add_parser("event")
    event_parser.add_argument("--lifecycle-id", required=True)
    event_parser.add_argument("--event", choices=sorted(ALL_EVENTS), required=True)
    event_parser.add_argument("--summary", required=True)
    event_parser.add_argument("--verification", action="append", default=[])
    event_parser.add_argument("--error-fingerprint", default="")
    event_parser.add_argument("--failure-class", choices=sorted(FAILURE_CLASSES), default="none")
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--lifecycle-id", required=True)
    args = parser.parse_args()
    if args.command == "start":
        output = start_lifecycle(args.task_kind, args.cwd, args.summary, args.project_root, args.module, args.file, args.repair_of_lifecycle_id, args.store, args.max_repair_attempts, args.producer_receipt, args.complexity_score, args.complexity_band, args.verification_required, args.verification_plan, args.ending_check_id, args.selected_pair)
    elif args.command == "event":
        output = record_event(args.lifecycle_id, args.event, args.summary, args.verification, args.error_fingerprint, args.store, args.failure_class)
    else:
        output = audit_lifecycle(args.lifecycle_id, args.store)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("final_gate_passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

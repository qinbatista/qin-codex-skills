#!/usr/bin/env python3
import argparse
import fcntl
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


DEFAULT_STORE = Path.home() / ".codex" / "ending-task-memory"
DEFAULT_MAX_REPAIR_ATTEMPTS = 3
SCHEMA_VERSION = 1
TERMINAL_EVENTS = {"pass", "fail", "blocked"}
ALL_EVENTS = TERMINAL_EVENTS | {"note"}


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


def start_lifecycle(task_kind, cwd, summary, project_root=None, module="", files=None, repair_of_lifecycle_id="", store=DEFAULT_STORE, max_repair_attempts=DEFAULT_MAX_REPAIR_ATTEMPTS):
    cwd_path = Path(cwd).expanduser().resolve()
    if not cwd_path.is_dir():
        raise ValueError("cwd must be an existing directory")
    project_path = Path(project_root).expanduser().resolve() if project_root else None
    normalized_files = _normalize_files(project_path, files or [])
    lifecycle_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:12]}"
    created_at = _now()
    store_path = Path(store).expanduser().resolve()
    store_path.mkdir(parents=True, exist_ok=True)
    lock_path = store_path / ".lock"
    with lock_path.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        parent = None
        attempt_index = 0
        repair_limit = int(max_repair_attempts)
        if repair_limit < 0 or repair_limit > 10:
            raise ValueError("max_repair_attempts must be between 0 and 10")
        if repair_of_lifecycle_id:
            parent = _read_state(store_path, repair_of_lifecycle_id)
            if parent["status"] != "failed":
                raise ValueError("repair lifecycle requires a failed parent lifecycle")
            attempt_index = int(parent.get("attempt_index", 0)) + 1
            repair_limit = int(parent.get("max_repair_attempts", DEFAULT_MAX_REPAIR_ATTEMPTS))
            if attempt_index > repair_limit:
                blocked_at = _now()
                blocked_event = {"schema_version": SCHEMA_VERSION, "event": "blocked", "recorded_at": blocked_at, "lifecycle_id": parent["lifecycle_id"], "summary": f"Repair attempt limit exhausted at {repair_limit}", "verification": [], "error_fingerprint": "repair-attempt-limit-exceeded"}
                parent["events"].append(blocked_event)
                parent["updated_at"] = blocked_at
                parent["status"] = "blocked"
                _write_state(store_path, parent)
                _append_event(store_path, blocked_event)
                raise ValueError("repair attempt limit exceeded")
        event = {"schema_version": SCHEMA_VERSION, "event": "started", "recorded_at": created_at, "lifecycle_id": lifecycle_id, "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "summary": _single_line(summary, "summary")}
        state = {"schema_version": SCHEMA_VERSION, "lifecycle_id": lifecycle_id, "created_at": created_at, "updated_at": created_at, "status": "running", "task_kind": _single_line(task_kind, "task_kind", max_length=80), "cwd": str(cwd_path), "summary": event["summary"], "project_root": str(project_path) if project_path else None, "module": _single_line(module, "module", required=False, max_length=160), "files": normalized_files, "repair_of_lifecycle_id": repair_of_lifecycle_id or None, "attempt_index": attempt_index, "max_repair_attempts": repair_limit, "repair_children": [], "events": [event]}
        if parent:
            parent_event = {"schema_version": SCHEMA_VERSION, "event": "repair_started", "recorded_at": created_at, "lifecycle_id": parent["lifecycle_id"], "child_lifecycle_id": lifecycle_id, "summary": f"Repair lifecycle {lifecycle_id} started"}
            parent["repair_children"].append(lifecycle_id)
            parent["events"].append(parent_event)
            parent["updated_at"] = created_at
            _write_state(store_path, parent)
            _append_event(store_path, parent_event)
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
    return {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": "running", "local": {"written": True, "store": str(store_path), "state": str(state_path)}}


def record_event(lifecycle_id, event_name, summary, verification=None, error_fingerprint="", store=DEFAULT_STORE):
    if event_name not in ALL_EVENTS:
        raise ValueError(f"event must be one of {', '.join(sorted(ALL_EVENTS))}")
    store_path = Path(store).expanduser().resolve()
    lock_path = store_path / ".lock"
    with lock_path.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        state = _read_state(store_path, lifecycle_id)
        if state["status"] != "running" and event_name != "note":
            raise ValueError(f"lifecycle is already terminal: {state['status']}")
        recorded_at = _now()
        event = {"schema_version": SCHEMA_VERSION, "event": event_name, "recorded_at": recorded_at, "lifecycle_id": lifecycle_id, "summary": _single_line(summary, "summary"), "verification": [_single_line(value, "verification", max_length=600) for value in (verification or [])], "error_fingerprint": _single_line(error_fingerprint, "error_fingerprint", required=False, max_length=160) or None}
        state["events"].append(event)
        state["updated_at"] = recorded_at
        if event_name in TERMINAL_EVENTS:
            state["status"] = {"pass": "passed", "fail": "failed", "blocked": "blocked"}[event_name]
        state_path = _write_state(store_path, state)
        _append_event(store_path, event)
    return {"status": "written", "lifecycle_id": lifecycle_id, "lifecycle_status": state["status"], "local": {"written": True, "store": str(store_path), "state": str(state_path)}}


def audit_lifecycle(lifecycle_id, store=DEFAULT_STORE):
    store_path = Path(store).expanduser().resolve()
    state = _read_state(store_path, lifecycle_id)
    chain = [state["lifecycle_id"]]
    current = state
    while current["status"] == "failed" and current.get("repair_children"):
        current = _read_state(store_path, current["repair_children"][-1])
        chain.append(current["lifecycle_id"])
    terminal_status = current["status"] if current["status"] in {"passed", "blocked"} else "pending"
    return {"status": "pass" if terminal_status == "passed" else terminal_status, "root_lifecycle_id": lifecycle_id, "active_lifecycle_id": current["lifecycle_id"], "terminal_status": terminal_status, "chain": chain, "final_gate_passed": terminal_status in {"passed", "blocked"}}


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
    event_parser = subparsers.add_parser("event")
    event_parser.add_argument("--lifecycle-id", required=True)
    event_parser.add_argument("--event", choices=sorted(ALL_EVENTS), required=True)
    event_parser.add_argument("--summary", required=True)
    event_parser.add_argument("--verification", action="append", default=[])
    event_parser.add_argument("--error-fingerprint", default="")
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--lifecycle-id", required=True)
    args = parser.parse_args()
    if args.command == "start":
        output = start_lifecycle(args.task_kind, args.cwd, args.summary, args.project_root, args.module, args.file, args.repair_of_lifecycle_id, args.store, args.max_repair_attempts)
    elif args.command == "event":
        output = record_event(args.lifecycle_id, args.event, args.summary, args.verification, args.error_fingerprint, args.store)
    else:
        output = audit_lifecycle(args.lifecycle_id, args.store)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("final_gate_passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inspect external task roots and release purpose-reviewed completed resources.

Task liveness and purpose decisions come from fresh owning-tool readbacks. This
helper reuses the producer ledger's identity, consumer, lock and deletion rules;
it never controls processes, applications or Codex chats itself.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from pathlib import Path
from typing import Any

import task_resource_ledger as resources
from task_artifact_paths import project_artifact_directory


MAX_ROOTS = 64
MAX_READBACK_AGE_SECONDS = 120


def inspect_cache(project_root: str | Path, *, limit: int = MAX_ROOTS, artifact_root: str | Path | None = None) -> dict[str, Any]:
    """Inspect bounded external roots and legacy Cache; never create a directory."""
    if not isinstance(limit, int) or not 1 <= limit <= MAX_ROOTS:
        raise ValueError("artifact inspection limit must be between 1 and 64")
    root = resources._canonical_root(project_root)
    roots = []
    count = 0
    reached = False
    owners = ((project_artifact_directory(root, artifact_root=artifact_root), "external"), (root / "Cache", "legacy_cache"))
    for directory, location in owners:
        if not directory.exists() and not directory.is_symlink():
            continue
        resources._safe_lstat(directory, directory=True)
        with os.scandir(directory) as entries:
            observed = list(itertools.islice(entries, limit - count + 1))
        for entry in observed:
            count += 1
            if count > limit:
                reached = True
                break
            if location == "legacy_cache" and not entry.name.startswith(("temp-", "tmp-")):
                continue
            task_root = f"Cache/{entry.name}" if location == "legacy_cache" else Path(entry.path).as_posix()
            try:
                resources._task_root_path(task_root)
                resources._safe_lstat(Path(entry.path), directory=True)
                ledger_path = Path(entry.path) / resources.LEDGER_NAME
                resources._safe_lstat(ledger_path, directory=False)
                ledger = resources.load_ledger(ledger_path)
                resources._assert_ledger_location(root, ledger_path, ledger, read_only=True)
                roots.append({"task_root": task_root, "location": location, "read_only": location == "legacy_cache", "owner_task_key": ledger["owner_task_key"], "ledger_id": ledger["ledger_id"], "resources": [{key: item[key] for key in ("id", "kind", "purpose", "state")} for item in ledger["resources"]]})
            except (OSError, ValueError) as error:
                roots.append({"task_root": task_root, "location": location, "status": "pending", "reason": str(error), "action": "preserve_unknown"})
        if reached:
            break
    return {"status": "complete", "roots": roots, "limit_reached": reached}


def validate_task_readback(readback: Any, owner_task_key: str) -> dict[str, Any]:
    """Reject stale liveness evidence and same-name or unrelated-task matches."""
    if not isinstance(readback, dict):
        raise ValueError("task readback must be an object")
    required = {"task_id", "state", "purpose", "observed_at", "source"}
    if set(readback) != required:
        raise ValueError("task readback requires task_id, state, purpose, observed_at and source")
    for field in ("task_id", "purpose", "source"):
        resources._require_text(readback[field], field)
    if resources._task_key(readback["task_id"]) != owner_task_key:
        raise ValueError("task readback belongs to a different resource owner")
    if readback["state"] not in {"complete", "active", "review", "paused", "failed", "unknown"}:
        raise ValueError("task readback state is invalid; idle alone does not prove completion")
    observed = readback["observed_at"]
    if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not 0 <= time.time() - observed <= MAX_READBACK_AGE_SECONDS:
        raise ValueError("fresh owning-tool task readback is required immediately before cleanup")
    return readback


def validate_decisions(decisions: Any, ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Keep by default; release requires an explicit purpose and use assessment."""
    if not isinstance(decisions, list) or len(decisions) > resources.MAX_MANIFEST_ENTRIES:
        raise ValueError("purpose decisions must be a bounded list")
    known = {item["id"] for item in ledger["resources"]}
    indexed = {}
    required = {"id", "disposition", "reason", "evidence", "result_known", "needed_for_review", "needed_for_reuse", "active_use"}
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision) != required:
            raise ValueError("each decision requires exact id, disposition, reason, evidence and four use flags")
        if decision["id"] not in known or decision["id"] in indexed:
            raise ValueError("purpose decision has an unknown or duplicate resource id")
        if decision["disposition"] not in {"release", "keep", "unknown"}:
            raise ValueError("purpose disposition must be release, keep or unknown")
        for field in ("reason", "evidence"):
            resources._require_text(decision[field], field)
        for field in ("result_known", "needed_for_review", "needed_for_reuse", "active_use"):
            if not isinstance(decision[field], bool):
                raise ValueError("resource use flags must be booleans")
        if decision["disposition"] == "release" and (not decision["result_known"] or any(decision[field] for field in ("needed_for_review", "needed_for_reuse", "active_use"))):
            raise ValueError("review, reusable, active or unfinished resources cannot be released")
        indexed[decision["id"]] = decision
    return indexed


def audit_ledger(project_root: str | Path, task_root: str, task_readback: dict[str, Any], decisions: list[dict[str, Any]], *, apply: bool = False, runtime_receipts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Release exact paths; request owner actions for runtime and network handles."""
    root = resources._canonical_root(project_root)
    task_root = resources._task_root_path(task_root)
    path = resources._absolute(root, task_root) / resources.LEDGER_NAME
    resources._safe_lstat(path.parent, directory=True)
    resources._safe_lstat(path, directory=False)
    receipts = runtime_receipts if runtime_receipts is not None else {}
    if not isinstance(receipts, dict):
        raise ValueError("runtime receipts must be an object")
    initial = resources.load_ledger(path)
    resources._assert_ledger_location(root, path, initial, read_only=True)
    if initial["schema_version"] == resources.LEGACY_SCHEMA_VERSION:
        readback = validate_task_readback(task_readback, initial["owner_task_key"])
        validate_decisions(decisions, initial)
        return {"status": "pending", "task_root": task_root, "task_id": readback["task_id"], "applied": False, "resources": [], "bytes_removed": 0, "root_removed": False, "finalization_reason": "legacy Cache ledger is read-only; exact migration or cleanup belongs to its original owner"}
    results = []
    released_bytes = 0
    with resources.ledger_lock(path):
        ledger = resources.load_ledger(path)
        resources._assert_ledger_location(root, path, ledger)
        readback = validate_task_readback(task_readback, ledger["owner_task_key"])
        indexed = validate_decisions(decisions, ledger)
        runtime_ids = {item["id"] for item in ledger["resources"] if item["kind"] in resources.RUNTIME_KINDS}
        if set(receipts) - runtime_ids:
            raise ValueError("receipt has an unknown runtime resource")
        for item in sorted(ledger["resources"], key=lambda value: value["acquisition_sequence"], reverse=True):
            result = {"id": item["id"], "kind": item["kind"]}
            decision = indexed.get(item["id"])
            if item["state"] in {"released", "released_external"}:
                results.append({**result, "action": "already_released"})
                continue
            if readback["state"] != "complete" or item["state"] in {"retained", "preexisting"} or (decision and decision["disposition"] == "keep"):
                results.append({**result, "action": "keep", "reason": decision["reason"] if decision else f"protected {readback['state']} task or retained resource"})
                continue
            if not decision or decision["disposition"] == "unknown":
                results.append({**result, "action": "pending", "reason": "resource purpose or current use is unconfirmed"})
                continue
            if not apply:
                results.append({**result, "action": "release_candidate", "reason": decision["reason"]})
                continue
            try:
                validate_task_readback(task_readback, ledger["owner_task_key"])
                if item["state"] not in {"cleanup_in_progress", "cleanup_ready"}:
                    resources.prepare_release(ledger, item["id"], project_root=root)
                else:
                    resources._enforce_scope_lifo(ledger, item)
                    resources._release_barriers(ledger, item)
                resources.save_ledger(path, ledger, assume_locked=True)
                if item["kind"] == "path":
                    target = resources._absolute(root, item["path"])
                    bytes_before = 0
                    if target.exists() and not target.is_symlink():
                        bytes_before = sum(entry.get("size", 0) for entry in resources._tree_manifest(target, ledger["binding"]["task_root_identity"]["device"]))
                    removed = resources.cleanup_path(ledger, root, item["id"], persist_callback=lambda value: resources.save_ledger(path, value, assume_locked=True))
                    if item["state"] not in {"released", "released_external"}:
                        raise ValueError("path identity conflict; resource preserved")
                    if target.exists() or target.is_symlink():
                        raise ValueError("exact removed path is still present")
                    released_bytes += bytes_before if removed else 0
                    results.append({**result, "action": "released", "read_back_verified": True, "bytes_removed": bytes_before if removed else 0})
                elif item["id"] in receipts:
                    resources.confirm_runtime_release(ledger, item["id"], receipts[item["id"]])
                    resources.save_ledger(path, ledger, assume_locked=True)
                    results.append({**result, "action": "released", "read_back_verified": True})
                else:
                    results.append({**result, "action": "owner_action_required", "identity": item["identity"], "ledger_id": ledger["ledger_id"], "identity_digest": item["identity_digest"], "release_token": item["release_token"]})
            except (OSError, ValueError) as error:
                results.append({**result, "action": "pending", "reason": str(error)})
    finalized = False
    finalization_reason = None
    if apply and readback["state"] == "complete" and all(item["state"] in resources.FINAL_STATES for item in ledger["resources"]):
        try:
            validate_task_readback(task_readback, ledger["owner_task_key"])
            resources.finalize_task_root(ledger, root, path)
            finalized = not path.parent.exists()
        except (OSError, ValueError) as error:
            finalization_reason = str(error)
    pending = bool(finalization_reason) or any(item["action"] in {"pending", "owner_action_required"} for item in results)
    return {"status": "pending" if pending else "complete", "task_root": task_root, "task_id": readback["task_id"], "applied": apply, "resources": results, "bytes_removed": released_bytes, "root_removed": finalized, "finalization_reason": finalization_reason}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--project-root", type=Path, required=True)
    inspect.add_argument("--limit", type=int, default=MAX_ROOTS)
    inspect.add_argument("--artifact-root", type=Path)
    audit = commands.add_parser("audit")
    audit.add_argument("--project-root", type=Path, required=True)
    audit.add_argument("--task-root", required=True)
    audit.add_argument("--task-readback", type=Path, required=True)
    audit.add_argument("--decisions", type=Path, required=True)
    audit.add_argument("--apply", action="store_true")
    audit.add_argument("--runtime-receipts", type=Path)
    arguments = vars(parser.parse_args())
    command = arguments.pop("command")
    for name in ("task_readback", "decisions", "runtime_receipts"):
        if arguments.get(name) is not None:
            arguments[name] = json.loads(arguments[name].read_text(encoding="utf-8"))
    try:
        result = inspect_cache(**arguments) if command == "inspect" else audit_ledger(**arguments)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "pending", "reason": str(error)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return int(result["status"] == "pending")


if __name__ == "__main__":
    raise SystemExit(main())

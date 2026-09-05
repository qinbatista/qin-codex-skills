#!/usr/bin/env python3
"""Persist a selected-model summary of completed work. No verification or routing."""

import argparse
import importlib.util
import json
import os
from pathlib import Path

import project_change_memory as memory


OUTCOME_FIELDS = {"durable", "module", "scope", "change_kind", "summary", "reason", "result", "verification_status", "files", "verification", "decisions", "risks", "supersedes", "symbols"}


def validate_outcome(payload):
    if not isinstance(payload, dict):
        raise ValueError("memory outcome must be an object")
    if set(payload) - OUTCOME_FIELDS:
        raise ValueError("outcome contains unsupported fields; checks, commands, and project overrides are not accepted")


def _effective_session_pair(resolver, thread_id, sessions_root):
    """Read only this session's latest turn, including any provider reroute."""
    if not resolver._is_valid_thread_id(thread_id):
        return None
    normalized = thread_id.lower()
    pair = None
    for path in resolver._candidate_paths_for_thread(Path(sessions_root).expanduser().resolve(), normalized):
        session = None
        current = None
        try:
            with path.open(encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    session_id = resolver._parse_session_id(event)
                    if session_id is not None:
                        session = session_id
                        current = None
                    if session != normalized or not isinstance(event, dict):
                        continue
                    payload = event.get("payload")
                    if not isinstance(payload, dict):
                        continue
                    if event.get("type") == "turn_context":
                        current = {"model": payload.get("model"), "effort": payload.get("effort"), "turn_id": payload.get("turn_id")}
                    elif event.get("type") == "event_msg" and payload.get("type") == "model_reroute" and current is not None:
                        if payload.get("turn_id") and current.get("turn_id") and payload["turn_id"] != current["turn_id"]:
                            continue
                        current["model"] = payload.get("to_model")
                    if current is not None:
                        pair = f"{current['model']}|{current['effort']}" if current.get("model") and current.get("effort") else None
        except OSError:
            continue
    return pair


def verify_identity(selected_model, selected_effort, *, runtime_receipt=None):
    """Verify the summarizing model from local runtime evidence, not caller labels."""
    if runtime_receipt is not None:
        if not isinstance(runtime_receipt, dict) or str(runtime_receipt.get("status", "")).lower() != "pass" or runtime_receipt.get("turn_completed") is not True:
            raise ValueError("a completed passing runtime receipt is required")
        pair = runtime_receipt.get("effective_pair")
        model = runtime_receipt.get("effective_model")
        effort = runtime_receipt.get("effective_effort") or runtime_receipt.get("resolved_effort")
        if pair and model and effort and pair != f"{model}|{effort}":
            raise ValueError("runtime receipt model identity is inconsistent")
        actual_pair = pair or (f"{model}|{effort}" if model and effort else None)
        evidence = "runtime_receipt"
    else:
        path = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "resolve_entry_model.py"
        spec = importlib.util.spec_from_file_location("ending_entry_resolver", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual_pair = _effective_session_pair(module, os.environ.get("CODEX_THREAD_ID"), os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        if actual_pair is None:
            raise ValueError("verified runtime model evidence is required; executing-model labels are insufficient")
        evidence = "verified_session"
    if actual_pair != f"{selected_model}|{selected_effort}":
        raise ValueError("runtime evidence must match the user's selected model and effort")
    return {"source": evidence, "pair": actual_pair}


def closeout(payload, *, selected_model, selected_effort, executing_model, executing_effort, project_root, store=None, vault=None, runtime_receipt=None):
    if not all(isinstance(value, str) and value.strip() for value in (selected_model, selected_effort)):
        raise ValueError("the user's selected model and effort are required")
    if (selected_model, selected_effort) != (executing_model, executing_effort):
        raise ValueError("memory must use the user's selected model and effort")
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project root must exist")
    validate_outcome(payload)
    if not payload or payload.get("durable") is False:
        return {"status": "skipped", "reason": "no_durable_information"}
    resolved_vault = memory._resolve_vault(vault, root)
    if store is None and resolved_vault is None and not memory.DEFAULT_STORE.is_dir():
        return {"status": "skipped", "reason": "memory_unavailable"}
    identity = verify_identity(selected_model, selected_effort, runtime_receipt=runtime_receipt)
    fields = {key: value for key, value in payload.items() if key != "durable"}
    fields.setdefault("scope", "project")
    fields.setdefault("change_kind", "edit")
    fields.setdefault("verification_status", "not-run")
    result = memory.record_change(root, store=Path(store) if store is not None else memory.DEFAULT_STORE, vault=resolved_vault, inspect_working_line=False, **fields)
    readback = memory.search_records(root, module=fields["module"], store=Path(store) if store is not None else memory.DEFAULT_STORE, inspect_working_line=False, record_id=result["record_id"])
    if result["record_id"] not in {record["id"] for record in readback["matches"]}:
        raise RuntimeError("memory write did not read back in the same project")
    return {**result, "read_back_verified": True, "model": selected_model, "effort": selected_effort, "model_evidence": identity,
            "projection_required": resolved_vault is not None or vault is not None or bool(os.environ.get("CODEX_OBSIDIAN_VAULT")),
            "verification_owner": "active_task", "purpose": "memory_only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--selected-model", required=True)
    parser.add_argument("--selected-effort", required=True)
    parser.add_argument("--executing-model", required=True)
    parser.add_argument("--executing-effort", required=True)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--runtime-receipt", type=Path, help="Completed model execution receipt; otherwise resolve this Codex session")
    args = parser.parse_args()
    payload = json.loads(args.outcome.read_text(encoding="utf-8"))
    kwargs = vars(args)
    kwargs.pop("outcome")
    kwargs["runtime_receipt"] = json.loads(args.runtime_receipt.read_text(encoding="utf-8")) if args.runtime_receipt else None
    print(json.dumps(closeout(payload, **kwargs), ensure_ascii=False))


if __name__ == "__main__":
    main()

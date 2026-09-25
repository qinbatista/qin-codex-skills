#!/usr/bin/env python3
"""Persist a selected-model summary of completed work. No verification or routing."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import tempfile
from pathlib import Path

import project_change_memory as memory


OUTCOME_FIELDS = {"durable", "module", "scope", "change_kind", "summary", "reason", "result", "verification_status", "files", "verification", "decisions", "risks", "supersedes", "symbols"}
CURRENT_START = "<!-- BEGIN CODEX CURRENT MODULE MEMORY -->"
CURRENT_END = "<!-- END CODEX CURRENT MODULE MEMORY -->"


def _update_current_project_knowledge(vault, owner, event):
    """Keep one current owner entry per module while preserving other notes."""
    knowledge = vault / "Projects" / owner / "Knowledge.md"
    if knowledge.is_symlink() or not knowledge.resolve(strict=False).is_relative_to(vault.resolve()):
        raise ValueError("project Knowledge.md must stay inside the Obsidian vault")
    previous = knowledge.read_text(encoding="utf-8") if knowledge.exists() else f"# {owner} Knowledge\n"
    changes = event.get("module_changes") or []
    module = str(changes[0].get("module", "")).strip() if changes else ""
    if not module:
        raise ValueError("recorded event has no module for current project knowledge")
    marker = "<!-- codex-module:" + hashlib.sha256(module.casefold().encode("utf-8")).hexdigest()[:16] + " -->"
    entry = (f"{marker}\n### {module}\n\n"
             f"- Current: {event['summary']}\n- Why: {event['reason']}\n"
             f"- Result: {event['result']}\n- Verification: {event['verification_status']}\n"
             f"- Event ID: `{event['event_id']}`\n")
    if (CURRENT_START in previous) != (CURRENT_END in previous):
        raise ValueError("project Knowledge.md has an incomplete current memory section")
    if CURRENT_START in previous:
        if previous.count(CURRENT_START) != 1 or previous.count(CURRENT_END) != 1:
            raise ValueError("project Knowledge.md has duplicate current memory sections")
        before, rest = previous.split(CURRENT_START, 1)
        managed, after = rest.split(CURRENT_END, 1)
        match = re.search(rf"(?ms)^{re.escape(marker)}\n.*?(?=^<!-- codex-module:|\Z)", managed)
        managed = managed[:match.start()] + entry + managed[match.end():] if match else managed.rstrip() + "\n\n" + entry
        updated = before + CURRENT_START + "\n" + managed.strip("\n") + "\n" + CURRENT_END + after
    else:
        updated = previous.rstrip() + "\n\n" + CURRENT_START + "\n" + entry + CURRENT_END + "\n"
    if updated == previous:
        return
    knowledge.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=knowledge.parent,
                                     prefix=".Knowledge.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(updated)
    temporary.replace(knowledge)


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


def _vault_runtime(vault_path):
    runtime_path = vault_path / "AI Memory" / "ai_memory.py"
    if not runtime_path.is_file():
        raise ValueError("configured Obsidian vault has no supported AI Memory writer")
    spec = importlib.util.spec_from_file_location("ending_vault_memory", runtime_path)
    if spec is None or spec.loader is None:
        raise ValueError("configured Obsidian vault writer cannot be loaded")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    return runtime


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
    if store is not None:
        raise ValueError("Codex-local memory stores are retired; use the configured Obsidian vault")
    resolved_vault = memory._resolve_vault(vault, root)
    if resolved_vault is None or not (resolved_vault / "AI Memory" / "ai_memory.py").is_file():
        from obsidian_vault_setup import ensure_vault

        setup = ensure_vault(vault=vault, project_root=root)
        if setup["status"] not in {"ready", "created"}:
            return {"status": "pending", "reason": setup.get("reason", "obsidian_vault_unavailable"),
                    "written": False, "vault": setup.get("vault")}
        resolved_vault = Path(setup["vault"])
    project = memory._project_identity(root)
    owner = project.get("owner") or root.name
    identity = verify_identity(selected_model, selected_effort, runtime_receipt=runtime_receipt)
    fields = {key: value for key, value in payload.items() if key != "durable"}
    required = ("module", "summary", "reason", "result", "files")
    if any(not fields.get(key) for key in required):
        raise ValueError("memory outcome requires module, summary, reason, result, and files")
    files = memory._normalize_files(root, fields["files"])
    verification_status = fields.get("verification_status", "not-run")
    verification = fields.get("verification") or []
    if verification_status != "not-run" and not verification:
        raise ValueError("verified memory outcomes require verification evidence")
    runtime = _vault_runtime(resolved_vault)
    if not (resolved_vault / "Projects" / owner).is_dir():
        if not callable(getattr(runtime, "add_project", None)):
            return {"status": "pending", "reason": "obsidian_project_unregistered", "written": False,
                    "vault": str(resolved_vault)}
        runtime.add_project(owner, vault_root=resolved_vault)
    result = runtime.record_event(
        project=owner, module=fields["module"], event_type="general",
        summary=fields["summary"], reason=fields["reason"], result=fields["result"],
        verification_status=verification_status, files=files, verification=verification,
        decisions=fields.get("decisions") or [], risks=fields.get("risks") or [],
    )
    event_id = result["event_id"]
    events = runtime._read_events(runtime.EVENTS_PATH)
    readback = next((event for event in events if event.get("event_id") == event_id), None)
    if readback is None or readback.get("project") != owner or not any(change.get("module") == fields["module"] for change in readback.get("module_changes", [])):
        raise RuntimeError("memory write did not read back from the same Obsidian project")
    _update_current_project_knowledge(resolved_vault, owner, readback)
    runtime.render_views()
    return {"status": result["status"], "event_id": event_id, "project": owner,
            "vault": str(resolved_vault), "vault_document": "AI Memory/events.jsonl", "read_back_verified": True,
            "model": selected_model, "effort": selected_effort, "model_evidence": identity,
            "verification_owner": "active_task", "purpose": "memory_only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--selected-model", required=True)
    parser.add_argument("--selected-effort", required=True)
    parser.add_argument("--executing-model", required=True)
    parser.add_argument("--executing-effort", required=True)
    parser.add_argument("--store", type=Path, help="Retired; Codex-local memory stores are not supported")
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

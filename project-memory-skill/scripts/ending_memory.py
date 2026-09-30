#!/usr/bin/env python3
"""Persist a concise summary of completed work in the configured Obsidian vault."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import project_change_memory as memory
import project_knowledge as knowledge


OUTCOME_FIELDS = {"durable", "module", "scope", "change_kind", "summary", "reason", "result", "verification_status", "files", "verification", "decisions", "risks", "supersedes", "symbols", "source_hashes", "memories", "consolidation"}


def snapshot_sources(project_root, files):
    """Capture only the producer's named evidence files, never the whole project."""
    root = Path(project_root).resolve()
    snapshots = {}
    for relative in memory._normalize_files(root, files):
        source = root / relative
        if not source.resolve().is_relative_to(root):
            raise ValueError("source evidence must stay inside the exact project")
        if not source.exists():
            snapshots[relative] = None
            continue
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        snapshots[relative] = digest.hexdigest()
    return snapshots


def prepare_entries(payload, project_root, *, capture_sources=False):
    """Normalize entity ownership; only the originating task captures evidence."""
    files = memory._normalize_files(project_root, payload["files"])
    hashes = payload.get("source_hashes", {})
    if capture_sources and not hashes:
        hashes = snapshot_sources(project_root, files)
    shared = {key: payload[key] for key in ("summary", "reason", "result", "verification_status", "verification", "decisions", "risks") if key in payload}
    if "memories" in payload:
        entries = [{**shared, **entry} for entry in payload["memories"]]
    elif payload.get("symbols"):
        if len(files) != 1:
            raise ValueError("symbols spanning multiple files require explicitly scoped memories")
        entries = [{**shared, "scope": "method", "module": payload["module"], "file": files[0], "symbol": symbol} for symbol in payload["symbols"]]
    else:
        scope = payload.get("scope", "module")
        if scope in {"file", "document"}:
            entries = [{**shared, "scope": "document", "module": payload["module"], "file": file} for file in files]
        else:
            entries = [{**shared, "scope": scope, "module": payload["module"]}]
    for entry in entries:
        relative = entry.get("file")
        if relative and relative not in files:
            raise ValueError("each memory entity file must be among the completed outcome files")
        if "source_hashes" not in entry:
            entry["source_hashes"] = dict(hashes)
        if capture_sources and not entry["source_hashes"]:
            entry["source_hashes"] = snapshot_sources(project_root, [relative] if relative else files)
    return knowledge.normalize_entries(project_root, entries)


def history_fields(entries, decisions, consolidation):
    """Keep precise scopes in the vault's supported semantic history fields."""
    changes = []
    history = list(decisions)
    for entry in entries:
        identifier = entry["id"]
        changes.append(f"memory:{identifier}={entry['summary']}")
        for key in ("scope", "module", "file", "symbol", "status", "reason", "result", "verification_status"):
            if entry.get(key):
                history.append(f"Memory {identifier} {key}: {entry[key]}")
        for key in ("decisions", "risks", "verification"):
            for value in entry.get(key, []):
                history.append(f"Memory {identifier} {key}: {value}")
        for relative, digest in entry.get("source_hashes", {}).items():
            history.append(f"Memory {identifier} source: {json.dumps({relative: digest}, ensure_ascii=False)}")
        for relation in entry.get("relations", []):
            history.append(f"Memory {identifier} relation: {json.dumps(relation, ensure_ascii=False, sort_keys=True)}")
    if consolidation:
        history.append("Project consolidation: " + consolidation["summary"])
        for relation in consolidation["relations"]:
            history.append("Project consolidation relation: " + json.dumps(relation, ensure_ascii=False, sort_keys=True))
    payload_hash = hashlib.sha256(json.dumps({"entries": entries, "consolidation": consolidation}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    history.append("Current memory payload SHA256: " + payload_hash)
    if any(not isinstance(value, str) or len(value) > 600 or "\n" in value or "\r" in value for value in history):
        raise ValueError("history decisions must be single lines of at most 600 characters; summarize long facts before writing")
    return changes, list(dict.fromkeys(history))


def validate_outcome(payload):
    if not isinstance(payload, dict):
        raise ValueError("memory outcome must be an object")
    if set(payload) - OUTCOME_FIELDS:
        raise ValueError("outcome contains unsupported fields; checks, commands, and project overrides are not accepted")
    if payload.get("supersedes"):
        raise ValueError("retire an exact memory entity explicitly; history supersession is not supported by this writer")
    for field in ("files", "symbols", "verification", "decisions", "risks"):
        if field in payload and (not isinstance(payload[field], list) or any(not isinstance(value, str) for value in payload[field])):
            raise ValueError(f"{field} must be a list of strings")
    for field, maximum in (("module", 160), ("summary", 600), ("reason", 600), ("result", 600)):
        if field in payload and (not isinstance(payload[field], str) or len(payload[field]) > maximum):
            raise ValueError(f"{field} must be text of at most {maximum} characters")
    if "source_hashes" in payload and not isinstance(payload["source_hashes"], dict):
        raise ValueError("source_hashes must be a mapping of exact project files")
    if "memories" in payload and (not isinstance(payload["memories"], list) or not payload["memories"] or any(not isinstance(entry, dict) for entry in payload["memories"])):
        raise ValueError("memories must be a nonempty list of scoped entries")


def _vault_runtime(vault_path):
    runtime_path = vault_path / "AI Memory" / "ai_memory.py"
    knowledge._confined(vault_path.resolve(), runtime_path)
    if not runtime_path.is_file():
        raise ValueError("configured Obsidian vault has no supported AI Memory writer")
    spec = importlib.util.spec_from_file_location("ending_vault_memory", runtime_path)
    if spec is None or spec.loader is None:
        raise ValueError("configured Obsidian vault writer cannot be loaded")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    return runtime


def closeout(payload, *, project_root, store=None, vault=None):
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
    fields = {key: value for key, value in payload.items() if key != "durable"}
    required = ("module", "summary", "reason", "result", "files")
    if any(not fields.get(key) for key in required):
        raise ValueError("memory outcome requires module, summary, reason, result, and files")
    files = memory._normalize_files(root, fields["files"])
    verification_status = fields.get("verification_status", "not-run")
    verification = fields.get("verification") or []
    if verification_status != "not-run" and not verification:
        raise ValueError("verified memory outcomes require verification evidence")
    entries = prepare_entries(fields, root)
    consolidation = knowledge.normalize_consolidation(fields.get("consolidation"))
    module_changes, decisions = history_fields(entries, fields.get("decisions") or [], consolidation)
    runtime = _vault_runtime(resolved_vault)
    lock_path = knowledge._confined(resolved_vault.resolve(), resolved_vault / "AI Memory" / ".ending.lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        memory._acquire_file_lock(lock)
        knowledge.load_knowledge(root, resolved_vault)
        if not (resolved_vault / "Projects" / owner).is_dir():
            if not callable(getattr(runtime, "add_project", None)):
                return {"status": "pending", "reason": "obsidian_project_unregistered", "written": False, "vault": str(resolved_vault)}
            runtime.add_project(owner, vault_root=resolved_vault)
        result = runtime.record_event(
            project=owner, module=fields["module"], event_type="general",
            summary=fields["summary"], reason=fields["reason"], result=fields["result"],
            verification_status=verification_status, files=files, verification=verification,
            module_change_values=module_changes, decisions=decisions, risks=fields.get("risks") or [],
        )
        event_id = result["event_id"]
        events = runtime._read_events(runtime.EVENTS_PATH)
        readback = next((event for event in events if event.get("event_id") == event_id), None)
        if readback is None or readback.get("project") != owner or not any(change.get("module") == fields["module"] for change in readback.get("module_changes", [])):
            raise RuntimeError("memory write did not read back from the same Obsidian project")
        if readback.get("decisions") != decisions:
            raise RuntimeError("memory history did not preserve the exact entity scope and source evidence")
        current = knowledge.apply_entries(root, resolved_vault, entries, event_id=event_id, consolidation=consolidation)
        if current["read_back_verified"] is not True:
            return {"status": "pending", "reason": "current_knowledge_projection_pending", "event_id": event_id, "project": owner, "current_memory": current}
        runtime.render_views()
        return {"status": result["status"], "event_id": event_id, "project": owner,
                "vault": str(resolved_vault), "vault_document": "AI Memory/events.jsonl", "read_back_verified": True,
                "verification_owner": "active_task", "purpose": "memory_only", "current_memory": current}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--store", type=Path, help="Retired; Codex-local memory stores are not supported")
    parser.add_argument("--vault", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.outcome.read_text(encoding="utf-8"))
    kwargs = vars(args)
    kwargs.pop("outcome")
    print(json.dumps(closeout(payload, **kwargs), ensure_ascii=False))


if __name__ == "__main__":
    main()

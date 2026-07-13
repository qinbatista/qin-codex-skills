#!/usr/bin/env python3
import argparse
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


DEFAULT_STORE = Path.home() / ".codex" / "project-change-memory"
DEFAULT_VAULT = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "MyAILLM"
SCHEMA_VERSION = 1
SCOPE_VALUES = ("project", "feature", "code", "file")
CHANGE_KIND_VALUES = ("add", "edit", "rename", "move", "delete", "mixed")
VERIFICATION_STATUS_VALUES = ("passed", "partial", "failed", "not-run")


def _single_line(value, field_name, required=True, max_length=1200):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not text:
        raise ValueError(f"{field_name} is required")
    return text[:max_length]


def _slug(value, fallback="item"):
    normalized = re.sub(r"[^a-z0-9._-]+", "-", str(value).strip().lower()).strip("-._")
    return normalized[:80] or f"{fallback}-{hashlib.sha256(str(value).encode()).hexdigest()[:10]}"


def _project_identity(project_root):
    root = Path(project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    name = root.name or "project"
    path_hash = hashlib.sha256(str(root).encode()).hexdigest()[:10]
    return {"name": name, "root": str(root), "key": f"{_slug(name, 'project')}-{path_hash}"}


def _normalize_files(project_root, file_values):
    root = Path(project_root).expanduser().resolve()
    normalized = []
    for file_value in file_values:
        candidate = Path(file_value).expanduser()
        relative = candidate.resolve().relative_to(root) if candidate.is_absolute() else PurePosixPath(candidate.as_posix())
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"file must be inside project_root: {file_value}")
        relative_text = relative.as_posix()
        if relative_text not in normalized:
            normalized.append(relative_text)
    if not normalized:
        raise ValueError("at least one --file is required")
    return normalized


def _project_file_index_path(project_dir, relative_file):
    parts = [_slug(part, "path") for part in PurePosixPath(relative_file).parts]
    leaf_hash = hashlib.sha256(relative_file.encode()).hexdigest()[:10]
    return project_dir / "files" / Path(*parts[:-1]) / f"{parts[-1]}-{leaf_hash}.jsonl"


def _read_records(index_path):
    if not index_path.exists():
        return []
    return [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def _resolve_vault(vault):
    selected = Path(vault).expanduser() if vault else Path(os.environ.get("CODEX_OBSIDIAN_VAULT", DEFAULT_VAULT)).expanduser()
    return selected.resolve() if selected.exists() and selected.is_dir() else None


def _markdown_entry(record):
    files = "\n".join(f"  - `{file_path}`" for file_path in record["files"])
    verifications = "; ".join(record["verification"]) or "none supplied"
    decisions = "; ".join(record["decisions"]) or "none"
    risks = "; ".join(record["risks"]) or "none"
    supersedes = record["supersedes"] or "none"
    return f"## {record['recorded_at']} — {record['summary']}\n\n- Record ID: `{record['id']}`\n- Module: {record['module']}\n- Scope: {record['scope']}\n- Change kind: {record['change_kind']}\n- What changed: {record['summary']}\n- Why: {record['reason']}\n- Result: {record['result']}\n- Verification: {record['verification_status']} — {verifications}\n- Decisions: {decisions}\n- Remaining risks: {risks}\n- Supersedes: `{supersedes}`\n- Files:\n{files}\n\n"


def _append_markdown(path, title, entry):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {title}\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def _write_obsidian(record, vault):
    vault_path = _resolve_vault(vault)
    if vault_path is None:
        return {"status": "unavailable", "written": False}
    root = vault_path / "Projects" / record["project"]["key"] / "ChangeMemory"
    entry = _markdown_entry(record)
    timestamp = datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00"))
    _append_markdown(root / "index.md", f"{record['project']['name']} Change Memory", entry)
    _append_markdown(root / "modules" / f"{_slug(record['module'], 'module')}.md", f"Module: {record['module']}", entry)
    _append_markdown(root / "records" / timestamp.strftime("%Y") / f"{timestamp.strftime('%Y-%m')}.md", f"Changes {timestamp.strftime('%Y-%m')}", entry)
    for relative_file in record["files"]:
        parts = [_slug(part, "path") for part in PurePosixPath(relative_file).parts]
        file_path = root / "files" / Path(*parts[:-1]) / f"{parts[-1]}.md"
        _append_markdown(file_path, f"File: {relative_file}", entry)
    return {"status": "written", "written": True, "root": root.relative_to(vault_path).as_posix()}


def _fingerprint(record):
    payload = {key: record[key] for key in ("project", "module", "scope", "change_kind", "summary", "reason", "result", "verification_status", "verification", "decisions", "risks", "files", "supersedes")}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record_change(project_root, module, scope, change_kind, summary, reason, result, verification_status, files, verification=None, decisions=None, risks=None, supersedes="", store=DEFAULT_STORE, vault=None, recorded_at=None):
    project = _project_identity(project_root)
    timestamp = recorded_at or datetime.now(timezone.utc)
    record = {"schema_version": SCHEMA_VERSION, "id": "", "recorded_at": timestamp.isoformat(timespec="seconds").replace("+00:00", "Z"), "project": project, "module": _single_line(module, "module", max_length=160), "scope": scope, "change_kind": change_kind, "summary": _single_line(summary, "summary"), "reason": _single_line(reason, "reason"), "result": _single_line(result, "result"), "verification_status": verification_status, "verification": [_single_line(value, "verification", max_length=600) for value in (verification or [])], "decisions": [_single_line(value, "decision", max_length=600) for value in (decisions or [])], "risks": [_single_line(value, "risk", max_length=600) for value in (risks or [])], "files": _normalize_files(project["root"], files), "supersedes": _single_line(supersedes, "supersedes", required=False, max_length=120)}
    if scope not in SCOPE_VALUES:
        raise ValueError(f"scope must be one of {', '.join(SCOPE_VALUES)}")
    if change_kind not in CHANGE_KIND_VALUES:
        raise ValueError(f"change_kind must be one of {', '.join(CHANGE_KIND_VALUES)}")
    if verification_status not in VERIFICATION_STATUS_VALUES:
        raise ValueError(f"verification_status must be one of {', '.join(VERIFICATION_STATUS_VALUES)}")
    if verification_status != "not-run" and not record["verification"]:
        raise ValueError("at least one --verification is required unless verification-status is not-run")
    record["fingerprint"] = _fingerprint(record)
    record["id"] = f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{record['fingerprint'][:12]}"
    store_path = Path(store).expanduser().resolve()
    store_path.mkdir(parents=True, exist_ok=True)
    lock_path = store_path / ".lock"
    with lock_path.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        existing_records = _read_records(store_path / "index.jsonl")
        if record["supersedes"]:
            superseded = next((existing for existing in existing_records if existing.get("id") == record["supersedes"]), None)
            if not superseded:
                raise ValueError("supersedes must reference an existing record")
            if superseded.get("project", {}).get("key") != project["key"]:
                raise ValueError("supersedes must reference the same project")
            if superseded.get("module") != record["module"]:
                raise ValueError("supersedes must reference the same module")
            if not set(superseded.get("files", [])) & set(record["files"]):
                raise ValueError("supersedes must overlap at least one touched file")
        duplicate = next((existing for existing in reversed(existing_records) if existing.get("fingerprint") == record["fingerprint"]), None)
        if duplicate:
            return {"status": "duplicate", "record_id": duplicate["id"], "project": duplicate["project"], "files": duplicate["files"], "local": {"written": True, "store": str(store_path)}, "obsidian": {"status": "not-rewritten", "written": False}}
        project_dir = store_path / "projects" / project["key"]
        record_path = project_dir / "records" / timestamp.strftime("%Y") / timestamp.strftime("%m") / f"{record['id']}.json"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (project_dir / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _append_jsonl(store_path / "index.jsonl", record)
        _append_jsonl(project_dir / "index.jsonl", record)
        _append_jsonl(project_dir / "modules" / _slug(record["module"], "module") / "index.jsonl", record)
        for relative_file in record["files"]:
            _append_jsonl(_project_file_index_path(project_dir, relative_file), record)
        obsidian_status = _write_obsidian(record, vault)
    return {"status": "written", "record_id": record["id"], "project": project, "files": record["files"], "local": {"written": True, "store": str(store_path), "record": str(record_path)}, "obsidian": obsidian_status}


def search_records(project_root=None, module="", files=None, query="", max_results=8, store=DEFAULT_STORE):
    project_key = _project_identity(project_root)["key"] if project_root else ""
    normalized_files = _normalize_files(project_root, files) if project_root and files else list(files or [])
    terms = [term for term in re.findall(r"[\w.+-]+", query.lower()) if len(term) >= 2][:12]
    matches = []
    for record in reversed(_read_records(Path(store).expanduser().resolve() / "index.jsonl")):
        if project_key and record["project"]["key"] != project_key:
            continue
        if module and record["module"].lower() != module.strip().lower():
            continue
        if normalized_files and not any(file_path in record["files"] for file_path in normalized_files):
            continue
        searchable = " ".join([record["summary"], record["reason"], record["result"], record["module"], *record["files"], *record["verification"], *record["decisions"], *record["risks"]]).lower()
        if terms and not all(term in searchable for term in terms):
            continue
        matches.append({key: record[key] for key in ("id", "recorded_at", "project", "module", "scope", "change_kind", "summary", "reason", "result", "verification_status", "verification", "decisions", "risks", "files", "supersedes")})
        if len(matches) >= max(1, min(max_results, 25)):
            break
    return {"status": "ok" if matches else "no-matches", "matches": matches}


def memory_status(store=DEFAULT_STORE, vault=None):
    store_path = Path(store).expanduser().resolve()
    records = _read_records(store_path / "index.jsonl")
    vault_path = _resolve_vault(vault)
    return {"status": "ready", "local": {"store": str(store_path), "records": len(records)}, "obsidian": {"status": "available" if vault_path else "unavailable", "vault": str(vault_path) if vault_path else ""}}


def main():
    parser = argparse.ArgumentParser(description="Record and recall file-level project change rationale")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--vault", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--project-root", type=Path)
    search_parser.add_argument("--module", default="")
    search_parser.add_argument("--file", action="append", default=[])
    search_parser.add_argument("--query", default="")
    search_parser.add_argument("--max-results", type=int, default=8)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--project-root", type=Path, required=True)
    record_parser.add_argument("--module", required=True)
    record_parser.add_argument("--scope", choices=SCOPE_VALUES, required=True)
    record_parser.add_argument("--change-kind", choices=CHANGE_KIND_VALUES, required=True)
    record_parser.add_argument("--summary", required=True)
    record_parser.add_argument("--reason", required=True)
    record_parser.add_argument("--result", required=True)
    record_parser.add_argument("--verification-status", choices=VERIFICATION_STATUS_VALUES, required=True)
    record_parser.add_argument("--verification", action="append", default=[])
    record_parser.add_argument("--decision", action="append", default=[])
    record_parser.add_argument("--risk", action="append", default=[])
    record_parser.add_argument("--file", action="append", required=True)
    record_parser.add_argument("--supersedes", default="")
    subparsers.add_parser("status")
    args = parser.parse_args()
    if args.command == "search":
        output = search_records(args.project_root, args.module, args.file, args.query, args.max_results, args.store)
    elif args.command == "record":
        output = record_change(args.project_root, args.module, args.scope, args.change_kind, args.summary, args.reason, args.result, args.verification_status, args.file, args.verification, args.decision, args.risk, args.supersedes, args.store, args.vault)
    else:
        output = memory_status(args.store, args.vault)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()

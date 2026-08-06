#!/usr/bin/env python3
"""Enforce project, module, and method memory coverage.

The coverage ledger is a small local JSONL index.  Obsidian receives native
Markdown pages for the same project/module/method scopes; it is not used as a
second JSON sidecar or as a replacement for model-routing history.

Supported platforms: Windows, macOS, and Linux.
"""

import argparse
import hashlib
import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkstemp

try:
    import project_change_memory
except ModuleNotFoundError:
    import importlib.util

    _project_memory_path = Path(__file__).with_name("project_change_memory.py")
    _project_memory_spec = importlib.util.spec_from_file_location("project_change_memory", _project_memory_path)
    project_change_memory = importlib.util.module_from_spec(_project_memory_spec)
    _project_memory_spec.loader.exec_module(project_change_memory)


SCHEMA_VERSION = 1
DEFAULT_STORE = Path.home() / ".codex" / "project-memory-coverage" / "events.jsonl"
MODULE_SCOPE_SYMBOL = "__module__"
METHOD_SENTINELS = {MODULE_SCOPE_SYMBOL, "<module>", "module-level"}
CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}
EDIT_OPERATIONS = {
    "add",
    "create",
    "delete",
    "edit",
    "fix",
    "implement",
    "modify",
    "patch",
    "refactor",
    "repair",
    "replace",
    "update",
}


class CoverageError(ValueError):
    """Raised when a required scope cannot be covered safely."""


def _clean(value, field, maximum=240, required=False):
    text = str(value or "").strip()
    if required and not text:
        raise CoverageError(f"{field} is required")
    if "\n" in text or "\r" in text:
        raise CoverageError(f"{field} must be single-line")
    if len(text) > maximum:
        raise CoverageError(f"{field} exceeds {maximum} characters")
    return text


def _slug(value, fallback="item"):
    text = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip("-._")
    if text:
        return text[:80]
    return f"{fallback}-{hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:10]}"


def _timestamp(value=None):
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize_files(project_root, file_values):
    if not file_values:
        return []
    values = [file_values] if isinstance(file_values, (str, Path)) else list(file_values)
    return project_change_memory._normalize_files(project_root, values)


def _normalize_symbols(symbols):
    if not symbols:
        return []
    values = [symbols] if isinstance(symbols, str) else list(symbols)
    result = []
    for value in values:
        text = _clean(value, "symbol", maximum=240)
        if text and text not in result:
            result.append(text)
    return result


def is_module_scope_symbol(symbol):
    return str(symbol or "").strip().lower() in {value.lower() for value in METHOD_SENTINELS}


def requires_method_scope(task_type="", code_kind="", operation="", files=None):
    """Return whether a durable code action needs an explicit method symbol."""
    task = str(task_type or "").strip().lower()
    kind = str(code_kind or "").strip().lower()
    action = str(operation or "").strip().lower()
    normalized_files = [str(value) for value in (files or [])]
    code_file = any(Path(value).suffix.lower() in CODE_EXTENSIONS for value in normalized_files)
    code_task = task in {"code", "debug", "development", "implementation", "script"} or kind in {"code", "script", "python", "csharp", "javascript", "typescript", "unity"}
    edit_action = action in EDIT_OPERATIONS or (not action and code_file)
    return bool(code_task and (edit_action or code_file))


def _scope_key(project_key, scope_kind, module="", symbol=""):
    return "|".join((project_key, scope_kind, module, symbol))


def _record_id(scope_key):
    return hashlib.sha256(scope_key.encode("utf-8")).hexdigest()[:24]


def _read_records(store):
    path = Path(store).expanduser()
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        record = event.get("record") if isinstance(event, dict) else None
        if isinstance(record, dict) and record.get("scope_kind"):
            records.append(record)
    return records


def _merge_records(records):
    merged = {}
    for record in records:
        key = record.get("scope_key")
        if not key:
            continue
        current = merged.get(key)
        if current is None:
            current = dict(record)
            current["files"] = list(record.get("files") or [])
            current["sources"] = list(record.get("sources") or [])
            merged[key] = current
            continue
        current["files"] = sorted(set(current.get("files", [])) | set(record.get("files", [])))
        current["sources"] = sorted(set(current.get("sources", [])) | set(record.get("sources", [])))
        current["first_seen"] = min(current.get("first_seen", record.get("first_seen", "")), record.get("first_seen", ""))
        current["last_seen"] = max(current.get("last_seen", record.get("last_seen", "")), record.get("last_seen", ""))
        current["observation_count"] = int(current.get("observation_count", 0)) + int(record.get("observation_count", 1))
    return merged


@contextmanager
def _locked_append(path):
    lock_path = Path(f"{path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write("\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _append_records(store, records):
    path = Path(store).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _locked_append(path):
        with path.open("a", encoding="utf-8") as handle:
            for record in records:
                event = {
                    "coverage_schema": SCHEMA_VERSION,
                    "event": "scope-observed",
                    "event_id": _record_id(record["scope_key"]),
                    "record": record,
                }
                handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def _atomic_write(path, text):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _owner_directory(vault, owner):
    safe_owner = str(owner or "").replace("/", "-").replace("\\", "-").strip() or "Unregistered Project"
    if safe_owner == "Global Codex Skills":
        return Path(vault).expanduser() / "Skills"
    return Path(vault).expanduser() / "Projects" / safe_owner


def _coverage_root(vault, owner):
    return _owner_directory(vault, owner) / "Memory Coverage"


def _link(path):
    return f"[[{Path(path).with_suffix('').as_posix()}]]"


def _render_index(project, records):
    lines = [
        "# Memory Coverage",
        "",
        f"- Project: `{project['name']}`",
        f"- Project key: `{project['key']}`",
        "- Contract: project and module coverage are automatic; method-targeted code requires an explicit symbol.",
        "",
        "| Scope | Module | Method | Files | Sources | Last seen |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for record in sorted(records, key=lambda value: (value.get("scope_kind", ""), value.get("module", ""), value.get("symbol", ""))):
        lines.append(
            f"| {record.get('scope_kind', '')} | {record.get('module') or '—'} | {record.get('symbol') or '—'} | {len(record.get('files', []))} | {', '.join(record.get('sources', [])) or '—'} | {record.get('last_seen', '')} |"
        )
    lines.extend(("", "## Native scope pages", ""))
    for record in sorted(records, key=lambda value: (value.get("scope_kind", ""), value.get("module", ""), value.get("symbol", ""))):
        if record.get("scope_kind") == "project":
            continue
        folder = "Modules" if record.get("scope_kind") == "module" else "Methods"
        slug_value = record.get("module") or record.get("symbol") or "scope"
        if record.get("scope_kind") == "method":
            slug_value = f"{record.get('module', 'module')}--{record.get('symbol', 'method')}"
        page = Path(folder) / f"{_slug(slug_value)}.md"
        lines.append(f"- {_link(page)}")
    lines.append("")
    return "\n".join(lines)


def _render_scope(project, record):
    lines = [
        f"# {record.get('scope_kind', 'scope').title()} Memory",
        "",
        f"- Project: `{project['name']}`",
        f"- Project key: `{project['key']}`",
        f"- Scope: `{record.get('scope_kind', '')}`",
        f"- Module: `{record.get('module') or '—'}`",
        f"- Method: `{record.get('symbol') or '—'}`",
        f"- First seen: `{record.get('first_seen', '')}`",
        f"- Last seen: `{record.get('last_seen', '')}`",
        f"- Observations: `{record.get('observation_count', 0)}`",
        "",
        "## Files",
        "",
    ]
    lines.extend(f"- `{file_value}`" for file_value in record.get("files", []))
    if not record.get("files"):
        lines.append("- None recorded yet")
    lines.extend(("", "## Sources", ""))
    lines.extend(f"- `{source}`" for source in record.get("sources", []))
    lines.append("")
    return "\n".join(lines)


def _project_index_link(vault, owner, coverage_root):
    index = _owner_directory(vault, owner) / "index.md"
    if not index.exists():
        return False
    relative = coverage_root.relative_to(Path(vault).expanduser())
    link = f"- [[{relative.as_posix()}/index|Memory Coverage]]"
    text = index.read_text(encoding="utf-8")
    if link not in text:
        separator = "" if text.endswith("\n") else "\n"
        _atomic_write(index, f"{text}{separator}\n{link}\n")
    return True


def _project_page(project, files, source, recorded_at):
    base = {
        "coverage_schema": SCHEMA_VERSION,
        "project_key": project["key"],
        "project_name": project["name"],
        "project_owner": project.get("owner", ""),
        "module": "",
        "symbol": "",
        "files": files,
        "sources": [source] if source else [],
        "first_seen": recorded_at,
        "last_seen": recorded_at,
        "observation_count": 1,
    }
    base["scope_key"] = _scope_key(project["key"], "project")
    base["scope_kind"] = "project"
    return base


def _scope_record(project, scope_kind, module, symbol, files, source, recorded_at):
    base = {
        "coverage_schema": SCHEMA_VERSION,
        "project_key": project["key"],
        "project_name": project["name"],
        "project_owner": project.get("owner", ""),
        "scope_kind": scope_kind,
        "module": module,
        "symbol": symbol,
        "files": files,
        "sources": [source] if source else [],
        "first_seen": recorded_at,
        "last_seen": recorded_at,
        "observation_count": 1,
    }
    base["scope_key"] = _scope_key(project["key"], scope_kind, module, symbol)
    base["record_id"] = _record_id(base["scope_key"])
    return base


def _write_obsidian(project, records, vault):
    if not vault:
        return {"status": "unavailable", "written": False, "reason": "vault_not_configured"}
    vault_path = Path(vault).expanduser()
    if not vault_path.exists() or not vault_path.is_dir():
        return {"status": "unavailable", "written": False, "reason": "vault_not_found"}
    owner = project.get("owner")
    if not owner:
        return {"status": "unavailable", "written": False, "reason": "unregistered_project"}
    root = _coverage_root(vault_path, owner)
    root.mkdir(parents=True, exist_ok=True)
    project_records = [record for record in records if record.get("project_key") == project["key"]]
    _atomic_write(root / "index.md", _render_index(project, project_records))
    for record in project_records:
        if record.get("scope_kind") == "project":
            continue
        folder = root / ("Modules" if record.get("scope_kind") == "module" else "Methods")
        slug_value = record.get("module") or record.get("symbol") or "scope"
        if record.get("scope_kind") == "method":
            slug_value = f"{record.get('module', 'module')}--{record.get('symbol', 'method')}"
        _atomic_write(folder / f"{_slug(slug_value)}.md", _render_scope(project, record))
    linked = _project_index_link(vault_path, owner, root)
    return {
        "status": "written",
        "written": True,
        "root": root.relative_to(vault_path).as_posix(),
        "index": (root / "index.md").relative_to(vault_path).as_posix(),
        "project_index_linked": linked,
    }


def ensure_coverage(project_root, module, *, symbol="", symbols=None, files=None, task_type="", code_kind="", operation="", source="route", require_method=False, vault=None, store=None, recorded_at=None):
    """Record the required scopes and return a ready/blocked coverage receipt."""
    project = project_change_memory._project_identity(project_root)
    module = _clean(module, "module", maximum=160, required=True)
    requested_symbols = _normalize_symbols(symbols if symbols is not None else ([symbol] if symbol else []))
    symbol = requested_symbols[0] if requested_symbols else ""
    normalized_files = _normalize_files(project_root, files)
    strict = bool(require_method or requires_method_scope(task_type, code_kind, operation, normalized_files))
    if strict and not requested_symbols:
        raise CoverageError(
            "method memory is required for this code action; provide --symbol <method-or-symbol> or use --symbol __module__ for an explicit module-level change"
        )
    timestamp = _timestamp(recorded_at)
    events = [
        _project_page(project, normalized_files, source, timestamp),
        _scope_record(project, "module", module, "", normalized_files, source, timestamp),
    ]
    events.extend(
        _scope_record(project, "method", module, method, normalized_files, source, timestamp)
        for method in requested_symbols
        if not is_module_scope_symbol(method)
    )
    target_store = Path(store or os.environ.get("CODEX_PROJECT_MEMORY_COVERAGE") or DEFAULT_STORE).expanduser()
    _append_records(target_store, events)
    merged = _merge_records(_read_records(target_store))
    project_records = [record for record in merged.values() if record.get("project_key") == project["key"]]
    obsidian = _write_obsidian(project, project_records, vault)
    validation = validate_coverage(project_root, module, symbols=requested_symbols, files=normalized_files, require_method=strict, store=target_store)
    validation.update({"local_store": target_store.name, "obsidian": obsidian, "source": source})
    return validation


def validate_coverage(project_root, module, *, symbol="", symbols=None, files=None, require_method=False, store=None):
    project = project_change_memory._project_identity(project_root)
    module = _clean(module, "module", maximum=160, required=True)
    requested_symbols = _normalize_symbols(symbols if symbols is not None else ([symbol] if symbol else []))
    symbol = requested_symbols[0] if requested_symbols else ""
    target_store = Path(store or os.environ.get("CODEX_PROJECT_MEMORY_COVERAGE") or DEFAULT_STORE).expanduser()
    merged = _merge_records(_read_records(target_store))
    required = [(_scope_key(project["key"], "project"), "project"), (_scope_key(project["key"], "module", module), "module")]
    strict = bool(require_method)
    if strict and not requested_symbols:
        raise CoverageError("method memory validation requires --symbol <method-or-symbol> or --symbol __module__")
    if strict:
        required.extend(
            (_scope_key(project["key"], "method", module, method), "method")
            for method in requested_symbols
            if not is_module_scope_symbol(method)
        )
    missing = [scope for key, scope in required if key not in merged]
    return {
        "status": "ready" if not missing else "blocked",
        "project_key": project["key"],
        "project_name": project["name"],
        "module": module,
        "symbol": symbol,
        "required_scopes": [scope for _, scope in required],
        "missing_scopes": missing,
        "coverage": not missing,
    }


def coverage_status(project_root=None, *, store=None):
    target_store = Path(store or os.environ.get("CODEX_PROJECT_MEMORY_COVERAGE") or DEFAULT_STORE).expanduser()
    records = _merge_records(_read_records(target_store))
    if project_root:
        project = project_change_memory._project_identity(project_root)
        records = {key: value for key, value in records.items() if value.get("project_key") == project["key"]}
    return {"status": "ready", "local_store": target_store.name, "records": len(records), "scopes": sorted({record.get("scope_kind", "") for record in records.values()})}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Enforce project/module/method memory coverage")
    parser.add_argument("--store", type=Path)
    parser.add_argument("--vault", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    ensure = commands.add_parser("ensure")
    ensure.add_argument("--project-root", type=Path, required=True)
    ensure.add_argument("--module", required=True)
    ensure.add_argument("--symbol", action="append", default=[])
    ensure.add_argument("--file", action="append", default=[])
    ensure.add_argument("--task-type", default="")
    ensure.add_argument("--code-kind", default="")
    ensure.add_argument("--operation", default="")
    ensure.add_argument("--source", default="manual")
    ensure.add_argument("--require-method", action="store_true")
    validate = commands.add_parser("validate")
    validate.add_argument("--project-root", type=Path, required=True)
    validate.add_argument("--module", required=True)
    validate.add_argument("--symbol", action="append", default=[])
    validate.add_argument("--file", action="append", default=[])
    validate.add_argument("--require-method", action="store_true")
    status = commands.add_parser("status")
    status.add_argument("--project-root", type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "ensure":
            output = ensure_coverage(args.project_root, args.module, symbols=args.symbol, files=args.file, task_type=args.task_type, code_kind=args.code_kind, operation=args.operation, source=args.source, require_method=args.require_method, vault=args.vault, store=args.store)
        elif args.command == "validate":
            output = validate_coverage(args.project_root, args.module, symbols=args.symbol, files=args.file, require_method=args.require_method, store=args.store)
        else:
            output = coverage_status(args.project_root, store=args.store)
    except (CoverageError, ValueError, OSError) as error:
        output = {"status": "blocked", "error": str(error)}
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

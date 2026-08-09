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
from contextlib import ExitStack, contextmanager
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
MANAGED_MARKER = "<!-- managed-by: project-memory-skill/memory-coverage -->"
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


def _read_strict_snapshot(store):
    """Read a migration source without silently accepting malformed or mixed rows."""
    path = Path(store).expanduser()
    if not path.is_file():
        raise CoverageError("source-store must be an existing coverage JSONL file")
    payload = path.read_bytes()
    records = []
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CoverageError(f"source-store line {line_number} is not valid UTF-8 JSON") from error
        record = event.get("record") if isinstance(event, dict) else None
        if not isinstance(record, dict) or not record.get("scope_key") or not record.get("scope_kind"):
            raise CoverageError(f"source-store line {line_number} is not a coverage scope record")
        records.append(record)
    if not records:
        raise CoverageError("source-store has no coverage scope records")
    return hashlib.sha256(payload).hexdigest(), records


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


def _record_subsumes(target, source):
    if not isinstance(target, dict) or not isinstance(source, dict):
        return False
    for field in ("scope_key", "project_key", "scope_kind", "module", "symbol"):
        if str(target.get(field) or "") != str(source.get(field) or ""):
            return False
    if not set(source.get("files") or []) <= set(target.get("files") or []):
        return False
    if not set(source.get("sources") or []) <= set(target.get("sources") or []):
        return False
    source_first = str(source.get("first_seen") or "")
    target_first = str(target.get("first_seen") or "")
    if source_first and (not target_first or target_first > source_first):
        return False
    source_last = str(source.get("last_seen") or "")
    target_last = str(target.get("last_seen") or "")
    if source_last and (not target_last or target_last < source_last):
        return False
    return int(target.get("observation_count") or 0) >= int(source.get("observation_count") or 0)


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


def _append_records_unlocked(store, records):
    path = Path(store).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            event = {
                "coverage_schema": SCHEMA_VERSION,
                "event": "scope-observed",
                "event_id": _record_id(record["scope_key"]),
                "record": record,
            }
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _append_records(store, records):
    path = Path(store).expanduser()
    with _locked_append(path):
        _append_records_unlocked(path, records)


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
        MANAGED_MARKER,
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
        MANAGED_MARKER,
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


def _scope_page_path(root, record):
    folder = "Modules" if record.get("scope_kind") == "module" else "Methods"
    slug_value = record.get("module") or record.get("symbol") or "scope"
    if record.get("scope_kind") == "method":
        slug_value = f"{record.get('module', 'module')}--{record.get('symbol', 'method')}"
    return root / folder / f"{_slug(slug_value)}.md"


def _verify_obsidian_projection(project, records, vault):
    if not vault:
        return False, "vault_not_configured"
    vault_path = Path(vault).expanduser()
    owner = project.get("owner")
    if not vault_path.is_dir() or not owner:
        return False, "vault_or_owner_unavailable"
    owner_index = _owner_directory(vault_path, owner) / "index.md"
    root = _coverage_root(vault_path, owner)
    index = root / "index.md"
    if not owner_index.is_file() or not index.is_file():
        return False, "owner_or_coverage_index_missing"
    expected_index = _render_index(project, records)
    if index.read_text(encoding="utf-8") != expected_index:
        return False, "coverage_index_readback_mismatch"
    relative = root.relative_to(vault_path)
    if f"[[{relative.as_posix()}/index|Memory Coverage]]" not in owner_index.read_text(encoding="utf-8"):
        return False, "owner_index_link_missing"
    expected_pages = set()
    for record in records:
        if record.get("scope_kind") == "project":
            continue
        page = _scope_page_path(root, record)
        expected_pages.add(page)
        if not page.is_file() or page.read_text(encoding="utf-8") != _render_scope(project, record):
            return False, "coverage_scope_readback_mismatch"
    for folder_name in ("Modules", "Methods"):
        folder = root / folder_name
        if not folder.is_dir():
            continue
        for page in folder.glob("*.md"):
            if page in expected_pages:
                continue
            if MANAGED_MARKER in page.read_text(encoding="utf-8", errors="replace"):
                return False, "stale_managed_scope_page"
    return True, "verified"


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
    expected_pages = set()
    for record in project_records:
        if record.get("scope_kind") == "project":
            continue
        page = _scope_page_path(root, record)
        expected_pages.add(page)
        _atomic_write(page, _render_scope(project, record))
    removed_stale_pages = []
    for folder_name in ("Modules", "Methods"):
        folder = root / folder_name
        if not folder.is_dir():
            continue
        for page in folder.glob("*.md"):
            if page in expected_pages:
                continue
            if MANAGED_MARKER in page.read_text(encoding="utf-8", errors="replace"):
                page.unlink()
                removed_stale_pages.append(page.relative_to(vault_path).as_posix())
    linked = _project_index_link(vault_path, owner, root)
    readback_verified, readback_reason = _verify_obsidian_projection(project, project_records, vault_path)
    return {
        "status": "written",
        "written": True,
        "root": root.relative_to(vault_path).as_posix(),
        "index": (root / "index.md").relative_to(vault_path).as_posix(),
        "project_index_linked": linked,
        "readback_verified": readback_verified,
        "readback_reason": readback_reason,
        "removed_stale_pages": removed_stale_pages,
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
    with _locked_append(target_store):
        _append_records_unlocked(target_store, events)
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


def merge_coverage_store(project_root, source_store, *, store=None, vault=None, delete_source=False):
    """Merge one proven rogue coverage ledger into the canonical authority and reproject it."""
    project = project_change_memory._project_identity(project_root)
    source_path = Path(source_store).expanduser().resolve()
    target_path = Path(store or os.environ.get("CODEX_PROJECT_MEMORY_COVERAGE") or DEFAULT_STORE).expanduser().resolve()
    if source_path == target_path:
        raise CoverageError("source-store must differ from the canonical target store")
    if delete_source and not vault:
        raise CoverageError("delete-source requires a configured vault for linked projection readback")

    source_records = []
    source_scope_keys = set()
    target_scope_keys = set()
    merged_verified = False
    projection_verified = False
    source_deleted = False
    source_digest = ""
    obsidian = {"status": "unavailable", "written": False, "reason": "vault_not_configured"}
    with ExitStack() as locks:
        for path in sorted((source_path, target_path), key=lambda value: value.as_posix()):
            locks.enter_context(_locked_append(path))
        source_digest, source_records = _read_strict_snapshot(source_path)
        project_source_records = [record for record in source_records if record.get("project_key") == project["key"]]
        if not project_source_records:
            raise CoverageError("source-store has no scopes for the requested project")
        if delete_source and len(project_source_records) != len(source_records):
            raise CoverageError("delete-source requires every source-store scope to belong to the requested project")
        source_merged = _merge_records(project_source_records)
        target_before = _merge_records(_read_records(target_path))
        additions = [record for key, record in source_merged.items() if not _record_subsumes(target_before.get(key), record)]
        if additions:
            _append_records_unlocked(target_path, additions)
        target_records = _merge_records(_read_records(target_path))
        project_records = [record for record in target_records.values() if record.get("project_key") == project["key"]]
        source_scope_keys = set(source_merged)
        target_scope_keys = {record.get("scope_key") for record in project_records if record.get("scope_key")}
        merged_verified = all(_record_subsumes(target_records.get(key), record) for key, record in source_merged.items())
        obsidian = _write_obsidian(project, project_records, vault)
        projection_verified = bool(
            obsidian.get("written") is True
            and obsidian.get("project_index_linked") is True
            and obsidian.get("readback_verified") is True
        )
        current_digest, current_source_records = _read_strict_snapshot(source_path)
        source_unchanged = current_digest == source_digest and current_source_records == source_records
        if not merged_verified:
            raise CoverageError("merged coverage did not pass full target readback")
        if delete_source and not projection_verified:
            raise CoverageError("delete-source requires linked rendered projection readback")
        if delete_source and not source_unchanged:
            raise CoverageError("source-store changed during migration; source was preserved")
        if delete_source:
            source_path.unlink()
            source_deleted = not source_path.exists()
            if not source_deleted:
                raise CoverageError("source-store cleanup did not complete")

    if source_deleted:
        source_lock = Path(f"{source_path}.lock")
        if not source_path.exists() and source_lock.exists():
            source_lock.unlink()
        source_deleted = not source_path.exists()
    return {
        "status": "ready",
        "project_key": project["key"],
        "source_records": len(source_records),
        "source_digest": source_digest,
        "merged_scope_count": len(source_scope_keys),
        "target_scope_count": len(target_scope_keys),
        "merge_verified": merged_verified,
        "projection_verified": projection_verified,
        "source_deleted": source_deleted,
        "source_lock_deleted": source_deleted and not Path(f"{source_path}.lock").exists(),
        "local_store": target_path.name,
        "obsidian": obsidian,
    }


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
    merge = commands.add_parser("merge-store")
    merge.add_argument("--project-root", type=Path, required=True)
    merge.add_argument("--source-store", type=Path, required=True)
    merge.add_argument("--delete-source", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "ensure":
            output = ensure_coverage(args.project_root, args.module, symbols=args.symbol, files=args.file, task_type=args.task_type, code_kind=args.code_kind, operation=args.operation, source=args.source, require_method=args.require_method, vault=args.vault, store=args.store)
        elif args.command == "validate":
            output = validate_coverage(args.project_root, args.module, symbols=args.symbol, files=args.file, require_method=args.require_method, store=args.store)
        elif args.command == "merge-store":
            output = merge_coverage_store(args.project_root, args.source_store, store=args.store, vault=args.vault, delete_source=args.delete_source)
        else:
            output = coverage_status(args.project_root, store=args.store)
    except (CoverageError, ValueError, OSError) as error:
        output = {"status": "blocked", "error": str(error)}
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

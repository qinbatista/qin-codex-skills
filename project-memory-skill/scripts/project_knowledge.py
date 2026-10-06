#!/usr/bin/env python3
"""Maintain one exact-project current memory index and its readable projection."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

import project_change_memory as memory


SCHEMA_VERSION = 1
MAINTENANCE_WRITES = 20
MAINTENANCE_DAYS = 30
MAX_SYNTHESIS_ENTRIES = 50
MAX_SYNTHESIS_SOURCES = 64
CURRENT_START = "<!-- BEGIN CODEX CURRENT PROJECT KNOWLEDGE -->"
CURRENT_END = "<!-- END CODEX CURRENT PROJECT KNOWLEDGE -->"
LEGACY_START = "<!-- BEGIN CODEX CURRENT MODULE MEMORY -->"
LEGACY_END = "<!-- END CODEX CURRENT MODULE MEMORY -->"
ENTRY_FIELDS = {"id", "scope", "module", "file", "symbol", "summary", "reason", "result", "decisions", "risks", "verification_status", "verification", "relations", "source_hashes", "status"}
CONTINUITY_FIELDS = ("summary", "reason", "result", "decisions", "risks", "relations", "status")
EVIDENCE_FIELDS = ("verification_status", "verification", "source_hashes")
MAX_PROJECT_ALIASES = 32
PROJECT_ALIAS_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}-[a-f0-9]{10}")


class ProjectIdentityError(ValueError):
    """The requested root does not own this current memory index."""


def _text(value, field, *, required=True, maximum=600):
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > maximum:
        raise ValueError(f"{field} must be {'nonempty ' if required else ''}text of at most {maximum} characters")
    if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
        raise ValueError(f"{field} contains control characters")
    return memory._single_line(value, field, required=required, max_length=maximum)


def _owner(value):
    name = _text(value, "project", maximum=160)
    if name in {".", ".."} or any(character in name for character in '\\/:*?"<>|[]#') or name.rstrip(". ") != name:
        raise ValueError("project must be one folder-safe owner name")
    return name


def _relative_file(value, root=None):
    if not isinstance(value, str) or not value or len(value) > 500:
        raise ValueError("file must be an exact project-relative path")
    portable = PureWindowsPath(value)
    if portable.anchor or any(part in {"..", "."} for part in value.replace("\\", "/").split("/")) or any(character in value for character in ':\x00\n\r[]#|*?"<>'):
        raise ValueError("file must stay inside its project")
    normalized = PurePosixPath(*portable.parts).as_posix()
    if normalized in {"", "."}:
        raise ValueError("file must be an exact project-relative path")
    if root is not None and not (root / normalized).resolve().is_relative_to(root):
        raise ValueError("file target escapes project_root")
    return normalized


def _symbol(value):
    if not isinstance(value, str) or any(character in value for character in "\n\r\t\x00"):
        raise ValueError("symbol must be an exact single-line language signature")
    return _text(value, "symbol", maximum=240)


def _entry_id(scope, module, file="", symbol=""):
    identity = json.dumps([scope, module, file, symbol], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _relations(values):
    if not isinstance(values, list) or len(values) > 32:
        raise ValueError("relations must contain at most 32 explicit pointers")
    unique = {}
    for value in values:
        if not isinstance(value, dict) or set(value) - {"project", "module", "file", "symbol", "relation", "reason"}:
            raise ValueError("relation accepts only project, module, file, symbol, relation, and reason")
        relation = {"project": _owner(value.get("project")), "module": _text(value.get("module"), "relation module", maximum=160), "relation": _text(value.get("relation"), "relation", maximum=120), "reason": _text(value.get("reason"), "relation reason")}
        if value.get("file"):
            relation["file"] = _relative_file(value["file"])
        if value.get("symbol"):
            symbol = _symbol(value["symbol"])
            if not relation.get("file"):
                raise ValueError("method relation requires an exact file and symbol")
            relation["symbol"] = symbol
        unique[json.dumps(relation, sort_keys=True)] = relation
    return [unique[key] for key in sorted(unique)]


def normalize_consolidation(consolidation):
    if consolidation is None:
        return None
    if not isinstance(consolidation, dict) or set(consolidation) - {"summary", "relations", "entry_ids"}:
        raise ValueError("consolidation accepts only summary, relations, and entry_ids")
    normalized = {"summary": _text(consolidation.get("summary"), "consolidation summary"), "relations": _relations(consolidation.get("relations", []))}
    if "entry_ids" in consolidation:
        identifiers = consolidation["entry_ids"]
        if not isinstance(identifiers, list) or len(identifiers) > MAX_SYNTHESIS_ENTRIES or any(not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{24}", value) is None for value in identifiers):
            raise ValueError("consolidation entry_ids must contain at most 50 exact scope IDs")
        normalized["entry_ids"] = sorted(set(identifiers))
    return normalized


def normalize_entries(project_root, entries, *, existing_entries=None, defaults=None):
    """Merge only identical scopes; changed claims need newly supplied evidence."""
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    if not isinstance(entries, list) or len(entries) > 128:
        raise ValueError("entries must contain at most 128 current facts")
    normalized = {}
    existing_by_id = {entry["id"]: entry for entry in existing_entries or []}
    default_values = defaults or {}
    for value in entries:
        if not isinstance(value, dict) or set(value) - ENTRY_FIELDS:
            raise ValueError("entry contains unsupported fields")
        scope = value.get("scope")
        if scope not in {"project", "module", "method", "document"}:
            raise ValueError("entry scope must be project, module, method, or document")
        module = _text(value.get("module", "project-wide" if scope == "project" else None), "module", maximum=160)
        file = _relative_file(value["file"], root) if value.get("file") else ""
        symbol = _symbol(value["symbol"]) if value.get("symbol") else ""
        if scope == "method" and (not file or not symbol):
            raise ValueError("method memory requires a module, exact file, and symbol")
        if scope == "document" and (not file or symbol):
            raise ValueError("document memory requires a file and no symbol")
        if scope in {"project", "module"} and (file or symbol):
            raise ValueError("project and module entries cannot claim one method or document")
        entry_id = _entry_id(scope, module, file, symbol)
        if value.get("id", entry_id) != entry_id:
            raise ValueError("entry id does not match its exact scope")
        existing = existing_by_id.get(entry_id)
        supplied_evidence = {field: value[field] if field in value else default_values[field] for field in EVIDENCE_FIELDS if field in value or field in default_values}
        value = {**default_values, **({field: existing[field] for field in CONTINUITY_FIELDS} if existing else {}), **value}
        entry = {"id": entry_id, "scope": scope, "module": module, "file": file, "symbol": symbol, "summary": _text(value.get("summary"), "summary"), "reason": _text(value.get("reason", ""), "reason", required=False), "result": _text(value.get("result", ""), "result", required=False)}
        if value.get("status", "current") not in {"current", "retired"}:
            raise ValueError("entry status must be current or retired")
        entry["status"] = value.get("status", "current")
        for field in ("decisions", "risks"):
            values = value.get(field, [])
            if not isinstance(values, list) or len(values) > 32:
                raise ValueError(f"{field} must contain at most 32 concise statements")
            entry[field] = sorted(set(_text(item, field) for item in values))
        entry["relations"] = _relations(value.get("relations", []))
        changed_claims = existing is not None and any(entry[field] != existing[field] for field in CONTINUITY_FIELDS)
        evidence = {**({field: existing[field] for field in EVIDENCE_FIELDS} if existing and not changed_claims else {}), **supplied_evidence}
        verification = evidence.get("verification", [])
        if not isinstance(verification, list) or len(verification) > 32:
            raise ValueError("verification must contain at most 32 concise statements")
        entry["verification"] = sorted(set(_text(item, "verification") for item in verification))
        status = evidence.get("verification_status", "not-run")
        if "verification" in supplied_evidence and not verification and "verification_status" not in supplied_evidence:
            status = "not-run"
        if status not in memory.VERIFICATION_STATUS_VALUES or (status != "not-run" and not entry["verification"]):
            raise ValueError("verification status requires matching evidence")
        entry["verification_status"] = status
        source_hashes = evidence.get("source_hashes", {})
        if not isinstance(source_hashes, dict) or len(source_hashes) > 64:
            raise ValueError("source_hashes must map at most 64 exact project files")
        hashes = {}
        for path, digest in source_hashes.items():
            if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                raise ValueError("source hash must be a lowercase SHA256 or null for missing source")
            hashes[_relative_file(path, root)] = digest
        if scope == "method" and hashes and file not in hashes:
            raise ValueError("method source evidence must include its exact file")
        entry["source_hashes"] = dict(sorted(hashes.items()))
        if entry_id in normalized and normalized[entry_id] != entry:
            raise ValueError("one update contains conflicting facts for the same entity")
        normalized[entry_id] = entry
    return [normalized[key] for key in sorted(normalized)]


def _paths(project_root, vault):
    project = memory._project_identity(project_root)
    owner = _owner(project.get("owner") or project["name"])
    resolved = memory._resolve_vault(vault, project_root)
    if resolved is None:
        raise ValueError("configured Obsidian vault is unavailable")
    base = resolved.resolve()
    directory = base / "Projects" / owner
    paths = {"vault": base, "directory": directory, "index": directory / "Memory.json", "knowledge": directory / "Knowledge.md", "lock": directory / ".memory.lock"}
    for name, path in paths.items():
        if name != "vault":
            _confined(base, path)
    return {"key": project["key"], "owner": owner, "name": project["name"]}, paths


def _confined(vault, path):
    if not path.resolve().is_relative_to(vault):
        raise ValueError("memory path escapes the Obsidian vault")
    current = path
    while current != vault:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("memory paths must not traverse symlinks or junctions")
        current = current.parent
    return path


def _timestamp(now=None):
    instant = datetime.now(timezone.utc) if now is None else datetime.fromisoformat(now.replace("Z", "+00:00")) if isinstance(now, str) else now
    if not isinstance(instant, datetime) or instant.tzinfo is None:
        raise ValueError("memory time must include a timezone")
    return instant.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _index_project(state):
    """Validate identity metadata before inspecting any requested-root source."""
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION or not isinstance(state.get("project"), dict):
        raise ValueError("current project index has an unsupported schema")
    stored = state["project"]
    _owner(stored.get("owner"))
    _text(stored.get("key"), "project key", maximum=160)
    _text(stored.get("name"), "project name", maximum=160)
    aliases = stored.get("aliases", [])
    if not isinstance(aliases, list) or len(aliases) > MAX_PROJECT_ALIASES or any(not isinstance(alias, str) or PROJECT_ALIAS_PATTERN.fullmatch(alias) is None for alias in aliases) or len(set(aliases)) != len(aliases):
        raise ValueError("project aliases must be bounded unique portable root keys")
    return stored


def _validate_knowledge(project_root, state):
    """Validate the same complete index before ordinary reads and alias repairs."""
    _index_project(state)
    if not isinstance(state.get("entries"), list) or not isinstance(state.get("maintenance"), dict) or "synthesis" not in state:
        raise ValueError("current project index is incomplete")
    identifiers = set()
    for entry in state["entries"]:
        if not isinstance(entry, dict) or set(entry) - ENTRY_FIELDS - {"event_id", "updated_at"}:
            raise ValueError("current project index contains an invalid entry")
        normalized = normalize_entries(project_root, [{key: value for key, value in entry.items() if key in ENTRY_FIELDS}])[0]
        if normalized["id"] in identifiers or not entry.get("event_id") or not entry.get("updated_at"):
            raise ValueError("current project index contains duplicate or unbound entries")
        _text(entry["event_id"], "entry event id", maximum=160)
        _timestamp(entry["updated_at"])
        identifiers.add(normalized["id"])
    maintenance = state["maintenance"]
    if type(maintenance.get("writes_since_consolidation")) is not int or maintenance["writes_since_consolidation"] < 0 or not all(field in maintenance for field in ("created_at", "last_consolidated_at")):
        raise ValueError("current project index contains invalid maintenance state")
    for field in ("created_at", "last_consolidated_at"):
        if maintenance[field] is not None:
            _timestamp(maintenance[field])
    if state["synthesis"] is not None:
        synthesis = state["synthesis"]
        if not isinstance(synthesis, dict) or set(synthesis) - {"summary", "relations", "entry_ids", "event_id", "updated_at"} or not synthesis.get("event_id") or not synthesis.get("updated_at"):
            raise ValueError("current project synthesis is incomplete")
        normalize_consolidation({key: value for key, value in synthesis.items() if key in {"summary", "relations"}})
        _text(synthesis["event_id"], "synthesis event id", maximum=160)
        _timestamp(synthesis["updated_at"])
        if "entry_ids" in synthesis and (not isinstance(synthesis["entry_ids"], list) or any(not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{24}", value) is None for value in synthesis["entry_ids"]) or len(set(synthesis["entry_ids"])) != len(synthesis["entry_ids"])):
            raise ValueError("synthesis contributors must be unique exact scope IDs")
    return state


def load_knowledge(project_root, vault):
    project, paths = _paths(project_root, vault)
    if not paths["index"].exists():
        return {"schema_version": SCHEMA_VERSION, "project": project, "entries": [], "synthesis": None, "maintenance": {"writes_since_consolidation": 0, "created_at": None, "last_consolidated_at": None}}
    state = json.loads(paths["index"].read_text(encoding="utf-8"))
    stored = _index_project(state)
    registered = memory._registered_owner_project_keys(project["owner"])
    explicit = memory._registered_owner(project_root) == project["owner"] and project["key"] in registered and project["key"] in stored.get("aliases", [])
    same_project = stored.get("key") == project["key"] or (stored.get("key") in registered and project["key"] in registered) or explicit
    if stored.get("owner") != project["owner"] or not same_project:
        raise ProjectIdentityError("current memory belongs to a different exact project")
    return _validate_knowledge(project_root, state)


def register_alias(project_root, vault, *, expected_owner, expected_project_key, expected_index_sha256):
    """Explicitly bind one registered root without changing its existing memory."""
    root = Path(project_root).expanduser().absolute()
    _confined(Path(root.anchor), root)
    vault_path = Path(vault).expanduser().absolute()
    _confined(Path(vault_path.anchor), vault_path)
    owner = _owner(expected_owner)
    expected_key = _text(expected_project_key, "expected project key", maximum=160)
    if not isinstance(expected_index_sha256, str) or re.fullmatch(r"[a-f0-9]{64}", expected_index_sha256) is None:
        raise ValueError("expected index SHA must be a lowercase SHA256")
    project, paths = _paths(root, vault_path)
    if project["owner"] != owner or memory._registered_owner(root) != owner or project["key"] not in memory._registered_owner_project_keys(owner):
        raise ProjectIdentityError("alias requires this exact registered project root and owner")
    if not paths["index"].is_file():
        raise ValueError("alias requires an existing project memory index")
    ending_lock = _confined(paths["vault"], paths["vault"] / "AI Memory" / ".ending.lock")
    with ExitStack() as locks:
        for path in (ending_lock, paths["lock"]):
            _confined(paths["vault"], path)
            handle = locks.enter_context(path.open("a+", encoding="utf-8"))
            memory._acquire_file_lock(handle)
        _confined(paths["vault"], paths["index"])
        original = paths["index"].read_bytes()
        if hashlib.sha256(original).hexdigest() != expected_index_sha256:
            raise ValueError("project memory index changed; read its SHA again")
        state = _validate_knowledge(root, json.loads(original.decode("utf-8")))
        stored = state["project"]
        if stored["owner"] != owner or stored["key"] != expected_key:
            raise ProjectIdentityError("alias expected owner or stored project key differs")
        aliases = stored.get("aliases", [])
        status = "duplicate" if project["key"] == stored["key"] or project["key"] in aliases else "written"
        if status == "written":
            if len(aliases) == MAX_PROJECT_ALIASES:
                raise ValueError("project alias capacity reached")
            stored["aliases"] = sorted([*aliases, project["key"]])
            _confined(paths["vault"], paths["index"])
            if paths["index"].read_bytes() != original:
                raise ValueError("project memory index changed during alias validation")
            _atomic_text(paths["index"], json.dumps(state, ensure_ascii=False, indent=2) + "\n", paths["vault"])
        if load_knowledge(root, vault_path) != state:
            raise RuntimeError("project alias did not read back with unchanged memory")
        return {"status": status, "project": owner, "project_key": stored["key"], "alias_key": project["key"], "index_document": f"Projects/{owner}/Memory.json", "index_sha256": hashlib.sha256(paths["index"].read_bytes()).hexdigest(), "read_back_verified": True}


def _maintenance_due(state, now, *, synthesis_status=None):
    if not any(entry["status"] == "current" for entry in state["entries"]):
        return False
    if state["synthesis"] is None or not state["synthesis"].get("entry_ids") or (synthesis_status is not None and synthesis_status["status"] != "ready"):
        return True
    maintenance = state["maintenance"]
    start = maintenance.get("last_consolidated_at") or maintenance.get("created_at")
    age_due = bool(start and datetime.fromisoformat(now.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00")) >= timedelta(days=MAINTENANCE_DAYS))
    return maintenance["writes_since_consolidation"] >= MAINTENANCE_WRITES or age_due


def _atomic_text(path, value, vault):
    _confined(vault, path)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".temp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        _confined(vault, path)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _markdown(value):
    return str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`")


def _relation_link(relation, targets):
    scope = "method" if relation.get("symbol") else "document" if relation.get("file") else "module"
    entry_id = _entry_id(scope, relation["module"], relation.get("file", ""), relation.get("symbol", ""))
    exists, anchors = targets(relation["project"])
    if entry_id in anchors:
        return f"[[Projects/{relation['project']}/Knowledge#^memory-{entry_id}]]"
    owner = f"[[Projects/{relation['project']}/Knowledge]]" if exists else _markdown(relation["project"])
    source = " / ".join(_markdown(relation[field]) for field in ("module", "file", "symbol") if relation.get(field))
    return f"{owner} (source pointer: {source})"


def _render(state, previous, vault):
    for start, end in ((CURRENT_START, CURRENT_END), (LEGACY_START, LEGACY_END)):
        if previous.count(start) != previous.count(end) or previous.count(start) > 1:
            raise ValueError("Knowledge.md has an incomplete or duplicate managed section")
    if LEGACY_START in previous:
        previous = previous.replace(LEGACY_START, "<!-- BEGIN LEGACY MODULE MEMORY HISTORY -->\n> Migration history only; current facts come from Memory.json.").replace(LEGACY_END, "<!-- END LEGACY MODULE MEMORY HISTORY -->")
    known_targets = {state["project"]["owner"]: (True, {entry["id"] for entry in state["entries"]})}

    def targets(owner):
        if owner not in known_targets:
            path = Path(vault) / "Projects" / owner / "Knowledge.md"
            try:
                _confined(vault, path)
                text = path.read_text(encoding="utf-8")
                known_targets[owner] = (True, set(re.findall(r"(?m)^\^memory-([a-f0-9]{24})\s*$", text)))
            except (OSError, ValueError):
                known_targets[owner] = (False, set())
        return known_targets[owner]

    lines = [CURRENT_START, "## Current project memory", "", "Generated from `Memory.json`. Exact module and method facts are indexed there.", ""]
    if state["synthesis"]:
        lines.extend(["### Project synthesis", "", _markdown(state["synthesis"]["summary"]), ""])
        for relation in state["synthesis"]["relations"]:
            lines.append(f"- Reference only: {_relation_link(relation, targets)} ({_markdown(relation['relation'])}) — {_markdown(relation['reason'])}")
    for entry in state["entries"]:
        title = entry["module"] + (f" / {entry['file']}" if entry["file"] else "") + (f" / {entry['symbol']}" if entry["symbol"] else "")
        lines.extend([f"### {_markdown(entry['scope'])}: {_markdown(title)}", "", f"- {entry['status'].title()}: {_markdown(entry['summary'])}"])
        for field in ("reason", "result"):
            if entry[field]:
                lines.append(f"- {field.title()}: {_markdown(entry[field])}")
        for field in ("decisions", "risks", "verification"):
            if entry[field]:
                lines.append(f"- {field.title()}: " + "; ".join(_markdown(value) for value in entry[field]))
        lines.extend([f"- Verification status: {_markdown(entry['verification_status'])}", f"- Event: `{_markdown(entry['event_id'])}`", "", f"^memory-{entry['id']}", ""])
        for relation in entry["relations"]:
            lines.append(f"- Reference only: {_relation_link(relation, targets)} ({_markdown(relation['relation'])}) — {_markdown(relation['reason'])}")
    lines.append(CURRENT_END)
    block = "\n".join(lines)
    if CURRENT_START in previous:
        before, remaining = previous.split(CURRENT_START, 1)
        managed, after = remaining.split(CURRENT_END, 1)
        return before + block + after
    return previous.rstrip() + "\n\n" + block + "\n"


def apply_entries(project_root, vault, entries, *, event_id, consolidation=None, now=None, expected_index_sha256=None, _index_lock=None):
    normalize_entries(project_root, entries, existing_entries=load_knowledge(project_root, vault)["entries"])
    synthesis = normalize_consolidation(consolidation)
    event = _text(event_id, "event_id", maximum=160)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", event):
        raise ValueError("event_id must identify one existing memory event")
    timestamp = _timestamp(now)
    if expected_index_sha256 is not None and (not isinstance(expected_index_sha256, str) or re.fullmatch(r"[a-f0-9]{64}", expected_index_sha256) is None):
        raise ValueError("expected index SHA must be a lowercase SHA256")
    project, paths = _paths(project_root, vault)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    _confined(paths["vault"], paths["lock"])
    with ExitStack() as locks:
        lock = locks.enter_context(paths["lock"].open("a+", encoding="utf-8")) if _index_lock is None else _index_lock
        if lock.closed or Path(lock.name).resolve() != paths["lock"].resolve():
            raise ValueError("the held project lock must match this exact index")
        if _index_lock is None:
            memory._acquire_file_lock(lock)
        if expected_index_sha256 is not None and (not paths["index"].is_file() or hashlib.sha256(paths["index"].read_bytes()).hexdigest() != expected_index_sha256):
            raise ValueError("project memory index changed; read its SHA again")
        state = load_knowledge(project_root, vault)
        normalized = normalize_entries(project_root, entries, existing_entries=state["entries"])
        events_path = _confined(paths["vault"], paths["vault"] / "AI Memory" / "events.jsonl")
        if not events_path.is_file():
            raise ValueError("event_id must identify an existing memory event for this exact owner")
        matching_event = None
        with events_path.open(encoding="utf-8") as events:
            for line in events:
                if line.strip():
                    candidate = json.loads(line)
                    if candidate.get("event_id") == event:
                        matching_event = candidate
                        break
        if matching_event is None or matching_event.get("project") != project["owner"]:
            raise ValueError("event_id must identify an existing memory event for this exact owner")
        before = json.dumps(state, sort_keys=True, ensure_ascii=False)
        by_id = {entry["id"]: entry for entry in state["entries"]}
        changed = False
        for entry in normalized:
            existing = by_id.get(entry["id"])
            if existing is not None and {key: existing[key] for key in entry} == entry:
                continue
            by_id[entry["id"]] = {**entry, "event_id": event, "updated_at": timestamp}
            changed = True
        state["entries"] = sorted(by_id.values(), key=lambda entry: (entry["scope"], entry["module"], entry["file"], entry["symbol"]))
        if synthesis:
            context = synthesis_context(project_root, state, entry_ids=synthesis.get("entry_ids"))
            if context["status"] != "ready":
                raise ValueError(context["reason"])
            synthesis["entry_ids"] = context["entry_ids"]
        maintenance = state["maintenance"]
        if changed or synthesis:
            maintenance["created_at"] = maintenance["created_at"] or timestamp
        if changed:
            maintenance["writes_since_consolidation"] += 1
            state["synthesis"] = None
        if synthesis and (state["synthesis"] is None or {key: state["synthesis"].get(key) for key in synthesis} != synthesis or _maintenance_due(state, timestamp)):
            state["synthesis"] = {**synthesis, "event_id": event, "updated_at": timestamp}
            maintenance["writes_since_consolidation"] = 0
            maintenance["last_consolidated_at"] = timestamp
        serialized = json.dumps(state, sort_keys=True, ensure_ascii=False)
        status = "written" if serialized != before else "duplicate"
        if serialized != before or not paths["index"].exists():
            _atomic_text(paths["index"], json.dumps(state, ensure_ascii=False, indent=2) + "\n", paths["vault"])
        index_verified = load_knowledge(project_root, vault) == state
        synthesis_readback = _synthesis_status(project_root, state)
        result = {"status": status, "project": project["owner"], "knowledge_document": f"Projects/{project['owner']}/Knowledge.md", "index_document": f"Projects/{project['owner']}/Memory.json", "index_read_back_verified": index_verified, "read_back_verified": False, "maintenance_due": _maintenance_due(state, timestamp, synthesis_status=synthesis_readback), "synthesis_status": synthesis_readback}
        try:
            _confined(paths["vault"], paths["knowledge"])
            previous = paths["knowledge"].read_text(encoding="utf-8") if paths["knowledge"].exists() else f"# {project['owner']} Knowledge\n"
            rendered = _render(state, previous, paths["vault"])
            if rendered != previous:
                _atomic_text(paths["knowledge"], rendered, paths["vault"])
            result["read_back_verified"] = index_verified and paths["knowledge"].read_text(encoding="utf-8") == rendered
        except (OSError, ValueError) as error:
            result.update({"status": "pending", "reason": "knowledge_projection_pending", "detail": str(error)})
        return result


def _freshness(entry, root, source_cache=None):
    sources = entry.get("source_hashes", {})
    if not sources:
        return "unverified", "source_evidence_absent"
    try:
        for relative, expected in sources.items():
            path = root / _relative_file(relative, root)
            if not path.is_file():
                return "stale", "source_missing"
            actual = source_cache.get(relative) if source_cache is not None else None
            if actual is None:
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                actual = digest.hexdigest()
                if source_cache is not None:
                    source_cache[relative] = actual
            if expected is None or actual != expected:
                return "stale", "source_changed"
    except OSError:
        return "unverified", "source_unreadable"
    return "current", "source_hashes_match"


def synthesis_context(project_root, state, *, entry_ids=None, source_cache=None):
    """Select bounded, exact-owner inputs without promoting excluded claims."""
    root = Path(project_root).resolve()
    current = {entry["id"]: entry for entry in state["entries"] if entry["status"] == "current"}
    result = {"status": "ready", "entries": [], "entry_ids": [], "excluded": [], "excluded_count": 0, "limitations": [], "limits": {"entries": MAX_SYNTHESIS_ENTRIES, "sources": MAX_SYNTHESIS_SOURCES}}
    if not current:
        return {**result, "status": "skipped", "reason": "no_current_knowledge"}
    if entry_ids is not None and any(identifier not in current for identifier in entry_ids):
        return {**result, "status": "pending", "reason": "synthesis_contributor_not_current"}
    candidates = [current[identifier] for identifier in entry_ids] if entry_ids is not None else list(current.values())
    for entry in candidates:
        if entry["scope"] == "method" and not entry["source_hashes"]:
            result["excluded_count"] += 1
            if len(result["excluded"]) < 5:
                result["excluded"].append({"id": entry["id"], "reason": "source_evidence_absent"})
    candidates = [entry for entry in candidates if entry["scope"] != "method" or entry["source_hashes"]]
    sources = {relative for entry in candidates for relative in entry["source_hashes"]}
    if len(candidates) > MAX_SYNTHESIS_ENTRIES or len(sources) > MAX_SYNTHESIS_SOURCES:
        return {**result, "status": "pending", "reason": "project_synthesis_input_limit", "input_counts": {"entries": len(candidates), "sources": len(sources)}, "limitations": ["Select explicit contributing scope IDs within the synthesis bounds; no inputs were silently truncated."]}
    cache = source_cache if source_cache is not None else {}
    for entry in candidates:
        freshness, reason = _freshness(entry, root, cache)
        if freshness == "stale" or reason == "source_unreadable":
            result["excluded_count"] += 1
            if len(result["excluded"]) < 5:
                result["excluded"].append({"id": entry["id"], "reason": reason})
            continue
        result["entries"].append({**entry, "freshness": freshness})
        if freshness == "unverified":
            result["limitations"].append("Some synthesis inputs have no source hash evidence and remain unverified.")
        if entry["verification_status"] != "passed":
            result["limitations"].append(f"Some synthesis inputs have {entry['verification_status']} verification; preserve that limit.")
    result["entry_ids"] = sorted(entry["id"] for entry in result["entries"])
    result["limitations"] = sorted(set(result["limitations"]))
    if result["excluded_count"] and entry_ids is not None:
        return {**result, "status": "pending", "reason": "synthesis_contributor_not_eligible", "entries": [], "entry_ids": []}
    if not result["entries"]:
        return {**result, "status": "pending", "reason": "project_synthesis_inputs_unavailable"}
    return result


def _synthesis_status(project_root, state, source_cache=None):
    synthesis = state["synthesis"]
    if synthesis is None:
        return {"status": "missing", "reason": "project_synthesis_absent"}
    if "entry_ids" not in synthesis:
        return {"status": "pending", "reason": "synthesis_contributors_unknown"}
    context = synthesis_context(project_root, state, entry_ids=synthesis["entry_ids"], source_cache=source_cache)
    return {key: value for key, value in context.items() if key != "entries"}


def recall(project_root, vault, *, module="", files=None, symbols=None, query="", limit=5):
    root = Path(project_root).expanduser().resolve()
    module = _text(module, "module", required=False, maximum=160)
    selected_files = sorted(set(_relative_file(value, root) for value in (files or [])))
    selected_symbols = sorted(set(_symbol(value) for value in (symbols or [])))
    result = {"status": "no-matches", "entries": [], "parent_context": [], "references": [], "stale": [], "unverified": [], "retired": [], "maintenance_due": False, "limitations": []}
    if selected_symbols and (not module or len(selected_files) != 1):
        return {**result, "status": "skipped", "reason": "method_context_requires_module_exact_file_and_symbol"}
    project, paths = _paths(root, vault)
    if not paths["index"].exists():
        return {**result, "status": "skipped", "reason": "current_index_missing"}
    try:
        state = load_knowledge(root, vault)
    except ProjectIdentityError:
        return {**result, "status": "skipped", "reason": "exact_project_mismatch"}
    source_cache = {}
    synthesis_status = _synthesis_status(root, state, source_cache)
    result["synthesis_status"] = synthesis_status
    result["maintenance_due"] = _maintenance_due(state, _timestamp(), synthesis_status=synthesis_status)
    words = re.findall(r"[\w.+-]+", _text(query, "query", required=False).casefold())[:12]
    maximum = max(1, min(int(limit), 5))
    selected = []
    for entry in state["entries"]:
        if module and entry["module"] != module:
            continue
        if selected_files and entry["file"] not in selected_files:
            continue
        if selected_symbols and entry["symbol"] not in selected_symbols:
            continue
        searchable = " ".join([entry["summary"], entry["reason"], entry["result"], *entry["decisions"], *entry["risks"]]).casefold()
        if words and not all(word in searchable for word in words):
            continue
        selected.append(entry)
    references = {}
    for position, entry in enumerate(selected):
        if len(result["entries"]) == maximum:
            break
        if position == 50:
            result["limitations"].append("Source inspection stopped after 50 matching entries; narrow the scope to continue.")
            break
        pointer = {key: entry[key] for key in ("id", "scope", "module", "file", "symbol", "event_id")}
        if entry["status"] == "retired":
            if len(result["retired"]) < maximum:
                result["retired"].append(pointer)
            continue
        freshness, reason = _freshness(entry, root, source_cache)
        if freshness == "stale":
            if len(result["stale"]) < maximum:
                result["stale"].append({**pointer, "reason": reason})
            continue
        if freshness == "unverified" and (entry["scope"] == "method" or reason == "source_unreadable"):
            if len(result["unverified"]) < maximum:
                result["unverified"].append({**pointer, "reason": reason})
            continue
        result["entries"].append({**entry, "freshness": freshness})
        if freshness == "unverified":
            result["limitations"].append("Some recalled facts have no source hash evidence.")
        if entry["verification_status"] != "passed":
            result["limitations"].append(f"Some recalled facts have {entry['verification_status']} verification; source identity is not behavior proof.")
        for relation in entry["relations"]:
            references[json.dumps(relation, sort_keys=True)] = {**relation, "context_loaded": False, "cross_project": relation["project"] != state["project"]["owner"]}
    modules = {entry["module"] for entry in result["entries"]}
    selected_ids = {entry["id"] for entry in result["entries"]}
    for entry in state["entries"]:
        if entry["id"] in selected_ids or not result["entries"] or entry["status"] == "retired":
            continue
        if entry["scope"] == "project" or (entry["scope"] == "module" and entry["module"] in modules):
            freshness, reason = _freshness(entry, root, source_cache)
            if freshness != "stale" and reason != "source_unreadable":
                result["parent_context"].append({**entry, "freshness": freshness})
            if len(result["parent_context"]) == 3:
                break
    if result["entries"] and state["synthesis"] and synthesis_status["status"] == "ready":
        result["project_synthesis"] = {**state["synthesis"], "freshness": "unverified", "context_role": "navigation_only", "eligible_current_context": False}
        for relation in state["synthesis"]["relations"]:
            references[json.dumps(relation, sort_keys=True)] = {**relation, "context_loaded": False, "cross_project": relation["project"] != state["project"]["owner"]}
    if state["synthesis"] and synthesis_status["status"] != "ready":
        result["limitations"].append("Project synthesis was withheld because its contributing evidence is unavailable or stale.")
        result["limitations"].extend(synthesis_status.get("limitations", []))
    result["references"] = [references[key] for key in sorted(references)][:32]
    result["limitations"] = sorted(set(result["limitations"]))
    if result["entries"]:
        result["status"] = "ok"
    elif result["stale"] or result["unverified"] or result["retired"]:
        result["status"] = "skipped"
        result["reason"] = "no_current_source_verified_entries"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    read = commands.add_parser("recall")
    read.add_argument("--project-root", type=Path, required=True)
    read.add_argument("--vault", type=Path, required=True)
    read.add_argument("--module", default="")
    read.add_argument("--file", dest="files", action="append", default=[])
    read.add_argument("--symbol", dest="symbols", action="append", default=[])
    read.add_argument("--query", default="")
    read.add_argument("--limit", type=int, default=5)
    alias = commands.add_parser("register-alias")
    alias.add_argument("--project-root", type=Path, required=True)
    alias.add_argument("--vault", type=Path, required=True)
    alias.add_argument("--expected-owner", required=True)
    alias.add_argument("--expected-project-key", required=True)
    alias.add_argument("--expected-index-sha256", required=True)
    arguments = vars(parser.parse_args())
    action = arguments.pop("action")
    print(json.dumps(register_alias(**arguments) if action == "register-alias" else recall(**arguments), ensure_ascii=False))


if __name__ == "__main__":
    main()

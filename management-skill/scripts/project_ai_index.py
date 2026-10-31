#!/usr/bin/env python3
"""Inspect and reconcile an agent-curated, project-local AI index."""

import argparse
import base64
import fnmatch
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflow-skill" / "scripts"))
from task_artifact_paths import project_artifact_directory, validate_task_directory
import task_cache_cleanup


INDEX_DIRECTORY = ".agents/skills/ai-index"
VISIBLE_INDEX_DIRECTORY = "skills/ai-index"
SKILL_PATH = f"{INDEX_DIRECTORY}/SKILL.md"
MANIFEST_PATH = f"{INDEX_DIRECTORY}/index.json"
REQUIRED_RULES = {"repository", "structure", "verification"}
PRUNED_DIRECTORIES = {".git", ".codex", ".venv", "venv", "env", "node_modules", "vendor", "Cache", "data", "dist", "build", "__pycache__", ".pytest_cache"}
MAX_GUIDANCE_BYTES = 262144
MAX_INDEX_DOCUMENTS = 256
MAX_DISCOVERY_ENTRIES = 2000
MAX_DISCOVERY_DEPTH = 6
MAX_SOURCE_BYTES = 1048576
MAX_EXCERPT_BYTES = 16384
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
MAX_CACHE_ROWS = 512
MAX_CACHE_RECORDS = 4096
MAX_CACHE_RECORD_BYTES = 65536
MAX_CACHE_CURRENT_BYTES = 2097152
CACHE_IGNORE_BLOCK = "# managed-cache-current-start\ncurrent.json\n*.pending\n# managed-cache-current-end\n"
CACHE_README = """# Cache ownership and current state

Read this folder at task start/resume and finish. The project owns its cache
policy here; `current.json` is a bounded replacement of current operational
state, never a memory log. Refresh it with Management's
`project_ai_index.py cache --project-root ROOT --apply` after allocation,
retention changes and deletion. Missing paths disappear on refresh.

- Task support belongs to a fresh `Cache/temp-*` run. Release unused exports,
  builds, copied projects and other intermediates immediately when the user's
  actual objective and necessary output handoff finish. A verified upload can
  finish the local package's purpose without waiting for unrelated backend work.
- Local debugging keeps only its actual live inputs; delivered videos or other
  requested results may remain while disposable test projects are released.
  Failed, stopped or abandoned task support is due for cleanup after 72 hours
  without heartbeat or descendant changes, after fresh native consumer checks.
  Active resources, real recovery dependencies and canonical originals remain
  protected; age alone does not delete them.
- Canonical assets, configuration and service/runtime data keep their native
  owners. Describe project-specific owners in this README or optional
  `owners.json`; cleanup must use the actual native owner.
- `remote-*` requires a real long-term consumer and synchronization route.
  Offline task cases, reports and local-only scratch do not earn that name.
  Verify updates/remote readback through the synchronization owner; do not sweep
  a remote directory by prefix. Unproven mappings are review candidates.
- Codex sessions, databases and managed worktrees are user-managed and excluded.

The Workflow registry at `Cache/temp-task-cache-registry` owns exact task
identity, heartbeat, retention and deletion proofs. The ignored `current.json`
summarizes that registry and immediate Cache children without traversing remote
payloads. An inventory row is not permission to delete. Keep current state
ignored in Git; stable owner rules remain versioned. Do not add one file per run.
An existing `remote-task-cache-registry` is local control compatibility, not a
remote resource or disposable payload; preserve its active native owner.
"""


def reject_links(path):
    for ancestor in reversed((path, *path.parents)):
        if not os.path.lexists(ancestor):
            continue
        observed = ancestor.lstat()
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if stat.S_ISLNK(observed.st_mode) or getattr(observed, "st_file_attributes", 0) & reparse:
            raise ValueError(f"symlink or reparse point is outside the index contract: {ancestor}")


def project_root(value):
    text = os.fspath(value)
    path = Path(text)
    if not path.is_absolute() or any(part in {".", ".."} for part in text.replace("\\", "/").split("/")):
        raise ValueError("project_root must be an absolute path without dot segments")
    reject_links(path)
    if not path.is_dir():
        raise ValueError("project_root must be an existing directory")
    return path.resolve()


def relative_path(value):
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise ValueError("paths must be nonempty project-relative POSIX paths")
    pieces = value.split("/")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if any(part in {"", ".", "..", ".git"} or ":" in part or part.endswith((".", " ")) or part.split(".")[0].lower() in reserved or any(ord(char) < 32 for char in part) for part in pieces):
        raise ValueError(f"unsafe project-relative path: {value}")
    return PurePosixPath(value)


def contained_path(root, value):
    relative = relative_path(value)
    path = root.joinpath(*relative.parts)
    reject_links(path)
    return path


def index_directory(root):
    """Prefer the existing visible owner; preserve legacy projects and bootstrap consent."""
    for relative in (VISIBLE_INDEX_DIRECTORY, INDEX_DIRECTORY):
        if contained_path(root, relative).exists():
            return relative
    return INDEX_DIRECTORY


def guidance_target(root, value):
    path = contained_path(root, value)
    relative = relative_path(value)
    directory = index_directory(root)
    is_index_document = value.startswith(directory + "/") and relative.suffix == ".md" and relative.name.lower() != "agents.md"
    if value != "AGENTS.md" and value != f"{directory}/index.json" and not is_index_document:
        raise ValueError(f"write is outside root AGENTS.md and project ai-index: {value}")
    if path.exists() and not path.is_file():
        raise ValueError(f"guidance target must be a regular file: {value}")
    return path


def file_hash(path):
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"hash target must be a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def guidance_bytes(root, relative, overlay):
    if relative in overlay:
        return overlay[relative]
    path = contained_path(root, relative)
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > MAX_GUIDANCE_BYTES:
        raise ValueError(f"guidance must be a bounded regular file: {relative}")
    return path.read_bytes()


def document_text(root, relative, overlay):
    content = guidance_bytes(root, relative, overlay)
    if content is None:
        raise ValueError(f"missing guidance: {relative}")
    return content.decode("utf-8")


def validate_document(root, relative, overlay, issues, advisories, documents):
    guidance_target(root, relative)
    text = document_text(root, relative, overlay)
    if not text.strip():
        issues.append(f"empty guidance: {relative}")
    budget = 800 if relative in {"AGENTS.md", f"{index_directory(root)}/SKILL.md"} else 2000
    if len(text.split()) > budget:
        advisories.append(f"review mixed responsibilities or split linked detail: {relative} exceeds {budget} words")
    for raw in re.findall(r"\]\(([^)]+)\)", text):
        target = raw.strip().strip("<>").split(' "', 1)[0]
        parsed = urlsplit(target)
        if parsed.scheme.lower() == "file" or re.match(r"^[A-Za-z]:", unquote(target)):
            issues.append(f"local document links must be project-relative: {relative} -> {target}")
            continue
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        local_target = unquote(parsed.path)
        if local_target.startswith(("/", "~")) or "\\" in local_target:
            issues.append(f"local document links must be project-relative with forward slashes: {relative} -> {target}")
            continue
        candidate = root.joinpath(*PurePosixPath(relative).parent.parts, local_target)
        candidate = Path(os.path.abspath(candidate))
        if candidate != root and root not in candidate.parents:
            issues.append(f"local document link escapes project: {relative} -> {target}")
            continue
        reject_links(candidate)
        local = candidate.relative_to(root).as_posix()
        exists = overlay[local] is not None if local in overlay else candidate.exists()
        if not exists:
            issues.append(f"missing document link: {relative} -> {target}")
        elif local.startswith(index_directory(root) + "/") and local.endswith(".md"):
            documents.add(local)
    return text


def validate_index(root, overlay=None):
    overlay = {} if overlay is None else overlay
    directory = index_directory(root)
    skill_path, manifest_path = f"{directory}/SKILL.md", f"{directory}/index.json"
    issues, advisories = [], []
    documents = {"AGENTS.md", skill_path, manifest_path}
    documents.update(relative for relative, content in overlay.items() if content is not None and relative.endswith(".md"))
    manifest = None
    try:
        agents = validate_document(root, "AGENTS.md", overlay, issues, advisories, documents)
        if skill_path not in agents:
            issues.append(f"root AGENTS.md must point to {skill_path}")
        skill = validate_document(root, skill_path, overlay, issues, advisories, documents)
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", skill, re.DOTALL)
        if not frontmatter or not re.search(r"(?m)^name:\s*['\"]?ai-index['\"]?\s*$", frontmatter[1]):
            issues.append("project SKILL.md must have frontmatter name: ai-index")
        description = re.search(r"(?m)^description:[ \t]*(.*)$", frontmatter[1]) if frontmatter else None
        if not description or not description[1].strip().strip("'\"").strip() or description[1].lstrip().startswith("#"):
            issues.append("project SKILL.md must have a nonempty frontmatter description")
        if "index.json" not in skill:
            issues.append("project SKILL.md must point to index.json")
        manifest = json.loads(document_text(root, manifest_path, overlay))
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise ValueError("index.json requires schema_version 1")
        rules, modules = manifest.get("rules"), manifest.get("modules")
        if not isinstance(rules, dict) or not REQUIRED_RULES.issubset(rules):
            raise ValueError("index.json requires repository, structure and verification rules")
        if not isinstance(modules, list) or not modules:
            raise ValueError("index.json requires at least one module")
        identifiers = []
        for module in modules:
            if not isinstance(module, dict) or not isinstance(module.get("id"), str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", module["id"]):
                raise ValueError("module IDs must be lowercase hyphenated identifiers")
            identifiers.append(module["id"])
            if not isinstance(module.get("summary"), str) or not module["summary"].strip():
                raise ValueError(f"module summary is required: {module['id']}")
            sources = module.get("sources")
            if not isinstance(sources, list) or not sources:
                raise ValueError(f"module source paths are required: {module['id']}")
            for source in sources:
                source_path = contained_path(root, source)
                exists = overlay[source] is not None if source in overlay else source_path.exists()
                if not exists:
                    issues.append(f"missing module source: {module['id']} -> {source}")
            dependencies = module.get("dependencies", [])
            if not isinstance(dependencies, list):
                raise ValueError(f"module dependencies must be a list: {module['id']}")
            for dependency in dependencies:
                if not isinstance(dependency, dict) or not isinstance(dependency.get("reason"), str) or not dependency["reason"].strip():
                    raise ValueError(f"dependency reason is required: {module['id']}")
        if len(identifiers) != len(set(identifiers)):
            issues.append("module IDs must be unique")
        for module in modules:
            for dependency in module.get("dependencies", []):
                if dependency.get("module") not in identifiers or dependency["module"] == module["id"]:
                    issues.append(f"unknown or self dependency: {module['id']} -> {dependency.get('module')}")
        validate_code_targets(root, modules, overlay)
        for relative in [*rules.values(), *(module.get("document") for module in modules)]:
            if not isinstance(relative, str) or not relative.startswith(directory + "/") or not relative.endswith(".md"):
                raise ValueError("rule and module documents must be Markdown inside the project ai-index")
            documents.add(relative)
        checked = {"AGENTS.md", skill_path, manifest_path}
        while remaining := sorted(documents - checked):
            if len(documents) > MAX_INDEX_DOCUMENTS:
                raise ValueError(f"project index exceeds {MAX_INDEX_DOCUMENTS} guidance documents")
            relative = remaining[0]
            validate_document(root, relative, overlay, issues, advisories, documents)
            checked.add(relative)
    except (OSError, ValueError, TypeError, KeyError) as error:
        issues.append(str(error))
    return {"status": "needs_review" if issues else "ready", "structural_check_only": True, "issues": issues, "advisories": advisories, "documents": sorted(documents), "manifest": manifest}


def validate_code_targets(root, modules, overlay):
    targets = {}
    for module in modules:
        entries = module.get("code_targets", [])
        if not isinstance(entries, list) or len(entries) > 128:
            raise ValueError(f"code_targets must be a list of at most 128 focused entries: {module['id']}")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) - {"id", "file", "symbol", "anchor", "summary", "related"}:
                raise ValueError("code target requires only id, file, symbol, anchor, summary and optional related")
            if any(not isinstance(entry.get(key), str) or not entry[key].strip() or len(entry[key]) > 500 for key in ("id", "file", "symbol", "anchor", "summary")):
                raise ValueError("code target requires bounded nonempty id, file, symbol, anchor and summary")
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry["id"]) or entry["anchor"] != entry["anchor"].strip() or "\n" in entry["anchor"] or "\r" in entry["anchor"]:
                raise ValueError("code target ID must be lowercase hyphenated; anchor must be one trimmed source line")
            identity = (module["id"], entry["id"])
            if identity in targets:
                raise ValueError(f"duplicate code target: {identity}")
            path = contained_path(root, entry["file"])
            if not any(entry["file"] == source or entry["file"].startswith(source + "/") for source in module["sources"]):
                raise ValueError(f"code target file is outside module sources: {identity}")
            exists = overlay[entry["file"]] is not None if entry["file"] in overlay else path.is_file()
            if not exists:
                raise ValueError(f"missing code target file: {entry['file']}")
            related = entry.get("related", [])
            if not isinstance(related, list) or len(related) > 32:
                raise ValueError(f"code target related must be a bounded list: {identity}")
            targets[identity] = entry
    for identity, entry in targets.items():
        seen = set()
        for relation in entry.get("related", []):
            if not isinstance(relation, dict) or set(relation) != {"module", "target", "reason"} or any(not isinstance(value, str) or not value.strip() or len(value) > 500 for value in relation.values()):
                raise ValueError(f"code target relation requires module, target and reason: {identity}")
            destination = (relation["module"], relation["target"])
            if destination not in targets or destination == identity or destination in seen:
                raise ValueError(f"unknown, self or duplicate code target relation: {identity} -> {destination}")
            seen.add(destination)


def shallow_structure(root):
    names = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if len(names) == 80:
            break
        if path.name not in PRUNED_DIRECTORIES and not path.is_symlink():
            names.append(path.name + ("/" if path.is_dir() else ""))
    return names


def bootstrap_inventory(root):
    guides, candidates = [], []
    count, bounded = 0, False
    for current, directories, files in os.walk(root, followlinks=False):
        directory = Path(current)
        depth = len(directory.relative_to(root).parts)
        directories[:] = sorted(name for name in directories if name not in PRUNED_DIRECTORIES and not (directory / name).is_symlink() and not (directory / name / ".git").exists())
        if depth >= MAX_DISCOVERY_DEPTH:
            bounded = bounded or bool(directories)
            directories[:] = []
        count += len(directories) + len(files)
        if count > MAX_DISCOVERY_ENTRIES:
            bounded = True
            break
        for name in sorted(files):
            relative = (directory / name).relative_to(root).as_posix()
            if name == "AGENTS.md":
                guides.append(relative)
            if name == "SKILL.md" and "index" in directory.name.lower():
                candidates.append(relative)
    return {"agents_files": guides, "index_candidates": candidates, "bounded": bounded, "excluded_directories": sorted(PRUNED_DIRECTORIES)}


def bootstrap_state(root):
    return None if contained_path(root, index_directory(root)).exists() else "missing"


def reference_project_result(root, project_scope):
    if project_scope not in {"current", "reference"}:
        raise ValueError("project_scope must be current or reference")
    if project_scope == "reference":
        return {"status": "skipped", "project_root": str(root), "project_scope": "reference", "reason": "AI-index prompts and maintenance apply only to the current task project", "read_scope": "none", "blocks_project_work": False}
    return None


def cache_json(path):
    """Read bounded operational control data without following links."""
    reject_links(path)
    if not path.is_file() or path.stat().st_size > MAX_CACHE_RECORD_BYTES:
        raise ValueError(f"cache control must be a bounded regular file: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"cache control must be an object: {path.name}")
    return value


def collect_cache_inventory(root):
    """Summarize current task identities and shallow owners, never remote payloads."""
    cache = contained_path(root, "Cache")
    folder = contained_path(root, f"{index_directory(root)}/cache")
    policies = []
    owners = folder / "owners.json"
    if owners.exists():
        policy = cache_json(owners)
        if policy.get("schema_version") != 1 or not isinstance(policy.get("owners"), list) or len(policy["owners"]) > MAX_CACHE_ROWS:
            raise ValueError("cache owners.json requires schema_version 1 and a bounded owners list")
        for owner in policy["owners"]:
            if not isinstance(owner, dict) or owner.get("kind") not in {"task", "durable", "remote"}:
                raise ValueError("cache owner requires task, durable or remote kind")
            path = relative_path(owner.get("path"))
            if len(path.parts) != 2 or path.parts[0] != "Cache" or ("*" in str(path) and str(path) not in {"Cache/temp-*", "Cache/remote-*"}):
                raise ValueError("cache owner path must identify one immediate Cache child or temp/remote pattern")
            policies.append(owner)
    rows, issues, record_count = {}, [], 0
    registry = task_cache_cleanup._registry(cache, root)
    records = registry / "runs"
    reject_links(records)
    if records.is_dir():
        for entry in sorted(records.iterdir()):
            if entry.suffix != ".json":
                continue
            record_count += 1
            if record_count > MAX_CACHE_RECORDS:
                issues.append("registry exceeds bounded record inspection; native registry remains authoritative")
                break
            try:
                record = cache_json(entry)
                path = Path(record.get("path", ""))
                if not path.is_absolute() or not path.is_relative_to(cache) or record.get("project_root") != str(root):
                    raise ValueError("registry owner is outside this project Cache")
                reject_links(path)
                if not path.exists():
                    continue
                relative = path.relative_to(root).as_posix()
                observed = path.stat()
                row = {"path": relative, "kind": "task", "state": str(record.get("state", "unknown"))[:32], "task_id": str(record.get("task_id", ""))[:200], "activity": "requires_native_consumer_check", "modified_at": observed.st_mtime}
                for key in ("heartbeat", "retention_review_at"):
                    if isinstance(record.get(key), (int, float)):
                        row[key] = record[key]
                for key in ("retention_reason", "disposable_reason"):
                    if isinstance(record.get(key), str):
                        row[key] = record[key][:500]
                rows[relative] = row
            except (OSError, ValueError, TypeError) as error:
                if len(issues) < 32:
                    issues.append(f"{entry.name}: {error}")
    child_count = 0
    if cache.exists():
        if not cache.is_dir():
            raise ValueError("project Cache must be a directory")
        for entry in sorted(cache.iterdir()):
            if entry == registry:
                continue
            child_count += 1
            relative = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                rows[relative] = {"path": relative, "kind": "protected_link", "activity": "not_inspected"}
                continue
            observed = entry.lstat()
            row = rows.setdefault(relative, {"path": relative, "kind": "unclassified", "state": "unregistered", "activity": "requires_owner_review", "modified_at": observed.st_mtime})
            matching = [policy for policy in policies if fnmatch.fnmatchcase(relative, policy["path"])]
            matching.sort(key=lambda policy: "*" in policy["path"])
            policy = matching[0] if matching else None
            if policy:
                consumer = str(policy.get("consumer", "")).strip()
                sync = str(policy.get("sync", "")).strip()
                if policy["kind"] == "remote":
                    row["kind"] = "verified_remote" if consumer and sync else "remote_requires_review"
                elif policy["kind"] == "durable":
                    row["kind"] = "durable" if consumer else "unclassified"
                else:
                    row["kind"] = "task"
                for key in ("consumer", "sync", "cleanup"):
                    if isinstance(policy.get(key), str):
                        row[key] = policy[key][:500]
            elif entry.name.startswith("remote-"):
                row["kind"] = "remote_requires_review"
            elif entry.name.startswith("temp-"):
                row["kind"] = "task"
    ordered = [rows[key] for key in sorted(rows)]
    kinds = {kind: sum(row["kind"] == kind for row in ordered) for kind in sorted({row["kind"] for row in ordered})}
    states = {state: sum(row.get("state", "unknown") == state for row in ordered) for state in sorted({row.get("state", "unknown") for row in ordered})}
    return {"schema_version": 1, "registry": registry.relative_to(root).as_posix(), "scope": "immediate Cache children and registered task identities; no payload traversal", "cleanup_after_idle_seconds": 259200, "codex_sessions": "user_managed_excluded", "child_count": child_count, "record_count": record_count, "entry_count": len(ordered), "counts_by_kind": kinds, "counts_by_state": states, "entries": ordered[:MAX_CACHE_ROWS], "omitted_count": max(0, len(ordered) - MAX_CACHE_ROWS), "issues": issues}


def write_cache_control(target, content, expected):
    """Replace one current control file only if its inspected preimage still matches."""
    reject_links(target)
    temporary = target.with_name(target.name + ".pending")
    identity = None
    try:
        with temporary.open("xb") as stream:
            observed = os.fstat(stream.fileno())
            identity = (observed.st_dev, observed.st_ino)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        reject_links(target)
        current = target.read_bytes() if target.exists() else None
        if current != expected:
            raise ValueError(f"cache index changed during refresh: {target.name}")
        temporary.replace(target)
    finally:
        if identity is not None and temporary.exists():
            observed = temporary.lstat()
            if (observed.st_dev, observed.st_ino) == identity:
                temporary.unlink()


def sync_cache_index(root, *, apply=False, project_scope="current"):
    """Refresh one existing current project's bounded Cache operations index."""
    root = project_root(root)
    skipped = reference_project_result(root, project_scope)
    if skipped is not None:
        return skipped
    if bootstrap_state(root):
        return {"status": "approval_required", "project_root": str(root), "read_scope": "index_presence_only", "required_action": "ask_user", "blocks_project_work": True}
    folder = contained_path(root, f"{index_directory(root)}/cache")
    inventory = collect_cache_inventory(root)
    current = folder / "current.json"
    reject_links(current)
    if current.exists() and (not current.is_file() or current.stat().st_size > MAX_CACHE_CURRENT_BYTES):
        raise ValueError("cache current inventory must be a bounded regular file")
    previous = current.read_bytes() if current.is_file() else None
    content = (json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    stale = previous != content
    readme = folder / "README.md"
    ignore = folder / ".gitignore"
    for target in (readme, ignore):
        reject_links(target)
    ignored = ignore.read_bytes() if ignore.is_file() else b""
    ignore_text = ignored.decode("utf-8")
    unowned_ignore = re.sub(r"(?m)^# managed-cache-current-start\n.*?^# managed-cache-current-end\n?", "", ignore_text, flags=re.DOTALL)
    updated_ignore = (unowned_ignore.rstrip("\n") + "\n\n" if unowned_ignore.strip() else "") + CACHE_IGNORE_BLOCK
    ignore_stale = ignore_text != updated_ignore
    changed = []
    if apply:
        folder.mkdir(parents=True, exist_ok=True)
        if ignore_stale:
            write_cache_control(ignore, updated_ignore.encode("utf-8"), ignored if ignore.exists() else None)
            changed.append(ignore.relative_to(root).as_posix())
        if not readme.exists():
            write_cache_control(readme, CACHE_README.encode("utf-8"), None)
            changed.append(readme.relative_to(root).as_posix())
        if stale:
            write_cache_control(current, content, previous)
            changed.append(current.relative_to(root).as_posix())
    result = {"status": "complete" if changed else "unchanged" if apply else "needs_review" if stale or not readme.exists() or ignore_stale else "ready", "project_root": str(root), "cache_index": folder.relative_to(root).as_posix(), "current_path": current.relative_to(root).as_posix(), "stale": stale and not apply, "entry_count": inventory["entry_count"], "omitted_count": inventory["omitted_count"], "issues": inventory["issues"], "changed": changed, "payloads_deleted": False}
    if not apply and result["status"] == "needs_review":
        result["required_action"] = "refresh_cache_index"
    return result


def check_project(root, phase="start", changed_paths=None, *, bootstrap_approved=False, project_scope="current"):
    root = project_root(root)
    skipped = reference_project_result(root, project_scope)
    if skipped is not None:
        return skipped
    state = bootstrap_state(root)
    if state and not bootstrap_approved:
        return {"status": "approval_required", "project_root": str(root), "phase": phase, "index_state": state, "read_scope": "index_presence_only", "required_action": "ask_user", "blocks_project_work": True, "remind_at": "next_project_start_or_resume", "question": "This project has no AI index. May I read the necessary project guidance and create its first AI index?"}
    result = validate_index(root)
    manifest = result.pop("manifest")
    result.update({"project_root": str(root), "phase": phase, "structure": shallow_structure(root), "guidance_hashes": {}, "affected_modules": [], "unmapped_paths": []})
    for relative in result["documents"]:
        try:
            result["guidance_hashes"][relative] = file_hash(contained_path(root, relative))
        except (ValueError, OSError) as error:
            result["issues"].append(str(error))
    if state == "missing":
        result["status"] = "missing"
        result["discovery"] = bootstrap_inventory(root)
    modules = manifest.get("modules", []) if isinstance(manifest, dict) else []
    for changed in changed_paths or []:
        relative_path(changed)
        if changed == "AGENTS.md" or changed.startswith(index_directory(root) + "/"):
            continue
        owners = [module["id"] for module in modules if isinstance(module, dict) and isinstance(module.get("id"), str) and isinstance(module.get("sources"), list) and any(changed == source or changed.startswith(source + "/") for source in module["sources"] if isinstance(source, str))]
        result["affected_modules"].extend(owners)
        if not owners:
            result["unmapped_paths"].append(changed)
    result["affected_modules"] = sorted(set(result["affected_modules"]))
    if result["unmapped_paths"]:
        result["issues"].append("changed paths have no indexed owner; reconcile their responsibility before broad reading")
        if result["status"] != "missing":
            result["status"] = "needs_review"
    if result["issues"] and result["status"] == "ready":
        result["status"] = "needs_review"
    if state is None:
        try:
            result["cache_management"] = sync_cache_index(root)
        except (OSError, ValueError, TypeError) as error:
            result["cache_management"] = {"status": "pending", "reason": str(error), "required_action": "review_cache_owner", "payloads_deleted": False}
    return result


def route_module(root, identifier=None, target=None, context_lines=12, *, project_scope="current"):
    root = project_root(root)
    skipped = reference_project_result(root, project_scope)
    if skipped is not None:
        return skipped
    if bootstrap_state(root):
        return check_project(root)
    result = validate_index(root)
    manifest = result.pop("manifest")
    if result["status"] != "ready":
        return result
    if identifier is None:
        if target is not None:
            return {"status": "needs_review", "structural_check_only": True, "issues": ["--target requires --module; select a module from the route menu first"]}
        return {"status": "ready", "structural_check_only": True, "modules": [{key: module[key] for key in ("id", "summary", "document")} for module in manifest["modules"]]}
    modules = {module["id"]: module for module in manifest["modules"]}
    if identifier not in modules:
        return {"status": "needs_review", "structural_check_only": True, "issues": [f"unknown module: {identifier}"]}
    module = modules[identifier]
    dependencies = [{"module": dependency["module"], "reason": dependency["reason"], "document": modules[dependency["module"]]["document"]} for dependency in module.get("dependencies", [])]
    result = {"status": "ready", "structural_check_only": True, "module": identifier, "summary": module["summary"], "document": module["document"], "sources": module["sources"], "dependencies": dependencies}
    entries = module.get("code_targets", [])
    if target is None:
        result["code_targets"] = [{key: entry[key] for key in ("id", "file", "symbol", "summary")} for entry in entries]
        return result
    if isinstance(context_lines, bool) or not isinstance(context_lines, int) or not 0 <= context_lines <= 40:
        raise ValueError("context_lines must be between 0 and 40")
    selected = next((entry for entry in entries if entry["id"] == target), None)
    if selected is None:
        return {**result, "status": "needs_review", "issues": [f"unknown code target: {identifier}/{target}; search only the likely module and repair the route"]}
    path = contained_path(root, selected["file"])
    if path.stat().st_size > MAX_SOURCE_BYTES:
        return {**result, "status": "needs_review", "issues": ["selected source exceeds bounded read; use a scoped symbol tool"], "target": selected}
    with path.open("rb") as stream:
        content = stream.read(MAX_SOURCE_BYTES + 1)
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError("selected source grew beyond bounded read")
    lines = content.decode("utf-8").splitlines()
    matches = [number for number, line in enumerate(lines) if line.strip() == selected["anchor"]]
    if len(matches) != 1:
        return {**result, "status": "needs_review", "issues": ["code anchor missing or ambiguous; repair this target from scoped source before editing"], "target": selected}
    line = matches[0]
    start, end = max(0, line - context_lines), min(len(lines), line + context_lines + 1)
    excerpt = "\n".join(lines[start:end])
    if len(excerpt.encode("utf-8")) > MAX_EXCERPT_BYTES:
        return {**result, "status": "needs_review", "issues": ["selected excerpt exceeds 16 KiB; reduce context_lines or use a scoped symbol tool"], "target": selected}
    related = []
    for relation in selected.get("related", []):
        destination = next(entry for entry in modules[relation["module"]].get("code_targets", []) if entry["id"] == relation["target"])
        related.append({**relation, "file": destination["file"], "symbol": destination["symbol"]})
    result.update({"structural_check_only": False, "target": {key: selected[key] for key in ("id", "file", "symbol", "summary")}, "location": {"line": line + 1, "start_line": start + 1, "end_line": end}, "source_sha256": hashlib.sha256(content).hexdigest(), "excerpt": excerpt, "excerpt_scope": "bounded context, not a complete method or proof of behavior", "related": related})
    return result


def prepare_plan(root, plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != 1 or plan.get("project_root") != str(root):
        raise ValueError("plan must bind schema_version 1 to the exact project_root")
    if bootstrap_state(root) and plan.get("bootstrap_approved") is not True:
        raise ValueError("initial AI index creation requires explicit user approval; set bootstrap_approved only after the user agrees")
    evidence, files = plan.get("evidence"), plan.get("files")
    if not isinstance(evidence, dict) or not isinstance(files, list) or not files:
        raise ValueError("plan requires evidence mapping and a nonempty files list")
    for relative, expected in evidence.items():
        if not isinstance(expected, str) or not SHA256_PATTERN.fullmatch(expected) or file_hash(contained_path(root, relative)) != expected:
            raise ValueError(f"source evidence changed or invalid: {relative}")
    overlay, originals, identities = {}, {}, set()
    for record in files:
        if not isinstance(record, dict) or not {"path", "expected_sha256", "content"}.issubset(record):
            raise ValueError("each plan file requires path, expected_sha256 and content")
        relative = record["path"]
        target = guidance_target(root, relative)
        if relative.casefold() in identities:
            raise ValueError(f"duplicate or case-aliased plan target: {relative}")
        identities.add(relative.casefold())
        expected, content = record["expected_sha256"], record["content"]
        if expected is not None and (not isinstance(expected, str) or not SHA256_PATTERN.fullmatch(expected)):
            raise ValueError(f"invalid expected_sha256: {relative}")
        if file_hash(target) != expected:
            raise ValueError(f"guidance preimage changed: {relative}")
        if content is not None and (not isinstance(content, str) or not content.strip() or len(content.encode("utf-8")) > MAX_GUIDANCE_BYTES):
            raise ValueError(f"guidance content must be nonempty bounded UTF-8: {relative}")
        originals[relative] = target.read_bytes() if target.is_file() else None
        overlay[relative] = content.encode("utf-8") if content is not None else None
    validation = validate_index(root, overlay)
    if validation["status"] != "ready":
        raise ValueError("proposed index is invalid: " + "; ".join(validation["issues"]))
    return overlay, originals


@contextmanager
def project_lock(root):
    owner = project_artifact_directory(root, create=True)
    lock = owner / "ai-index.lock"
    token = uuid.uuid4().hex
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"token": token, "pid": os.getpid()}))
    try:
        yield
    finally:
        if lock.is_file() and not lock.is_symlink() and json.loads(lock.read_text(encoding="utf-8")).get("token") == token:
            lock.unlink()


def write_guidance(target, content):
    if content is None:
        target.unlink(missing_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def rollback_guidance(root, attempted, overlay, originals):
    unresolved = []
    for relative in reversed(attempted):
        try:
            target = guidance_target(root, relative)
            current = target.read_bytes() if target.is_file() else None
            if current == originals[relative]:
                continue
            if current != overlay[relative]:
                unresolved.append(relative)
                continue
            write_guidance(target, originals[relative])
        except (OSError, ValueError) as error:
            unresolved.append(f"{relative}: {error}")
    return unresolved


def apply_locked_plan(root, plan, work):
    attempted, overlay, originals, created_directories = [], {}, {}, []
    recovery = None
    try:
        overlay, originals = prepare_plan(root, plan)
        changed = [relative for relative in overlay if overlay[relative] != originals[relative]]
        if not changed:
            return {"status": "unchanged", "project_root": str(root), "changed": [], "guidance_hashes": {relative: file_hash(guidance_target(root, relative)) for relative in overlay}, "structural_check_only": True}
        work.mkdir(parents=True, exist_ok=True)
        recovery = work / f"ai-index-recovery-{uuid.uuid4().hex}.json"
        recovery.write_text(json.dumps({"project_root": str(root), "originals": {relative: base64.b64encode(value).decode("ascii") if value is not None else None for relative, value in originals.items()}, "intended_hashes": {relative: hashlib.sha256(value).hexdigest() if value is not None else None for relative, value in overlay.items()}}, indent=2), encoding="utf-8")
        for relative in changed:
            target = guidance_target(root, relative)
            current = target.read_bytes() if target.is_file() else None
            if current != originals[relative]:
                raise ValueError(f"guidance changed during apply: {relative}")
            for parent in reversed(target.parents):
                if parent != root and root in parent.parents and not parent.exists():
                    parent.mkdir()
                    created_directories.append(parent)
            attempted.append(relative)
            write_guidance(target, overlay[relative])
        for relative, expected in plan["evidence"].items():
            if relative not in overlay and file_hash(contained_path(root, relative)) != expected:
                raise ValueError(f"source evidence changed during apply: {relative}")
        validation = validate_index(root)
        if validation["status"] != "ready" or any((guidance_bytes(root, relative, {}) != content) for relative, content in overlay.items()):
            raise ValueError("guidance readback changed or failed validation")
        recovery.unlink()
        return {"status": "complete", "project_root": str(root), "changed": changed, "guidance_hashes": {relative: file_hash(guidance_target(root, relative)) for relative in overlay}, "advisories": validation["advisories"], "structural_check_only": True}
    except (OSError, ValueError) as error:
        unresolved = rollback_guidance(root, attempted, overlay, originals)
        for directory in reversed(created_directories):
            if directory.is_dir() and not directory.is_symlink() and not any(directory.iterdir()):
                directory.rmdir()
        if recovery is not None and not unresolved:
            recovery.unlink(missing_ok=True)
        return {"status": "pending", "project_root": str(root), "reason": str(error), "unresolved": unresolved, "recovery": str(recovery) if recovery is not None and recovery.exists() else None}


def apply_plan(root, plan, work_dir, *, project_scope="current"):
    root = project_root(root)
    skipped = reference_project_result(root, project_scope)
    if skipped is not None:
        return skipped
    work = validate_task_directory(work_dir, root)
    try:
        with project_lock(root):
            return apply_locked_plan(root, plan, work)
    except (OSError, ValueError) as error:
        return {"status": "pending", "project_root": str(root), "reason": str(error), "unresolved": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "check", "route", "apply", "cache"):
        command = commands.add_parser(name)
        command.add_argument("--project-root", required=True, type=Path)
        command.add_argument("--project-scope", choices=("current", "reference"), default="current", help="Current task project (default), or another project consulted only as a reference; reference scope skips index prompts, reads and writes")
        if name == "inspect":
            command.add_argument("--phase", choices=("start", "end"), default="start")
            command.add_argument("--changed-path", action="append", default=[])
        if name in {"inspect", "check"}:
            command.add_argument("--allow-bootstrap", action="store_true", help="Read bootstrap context only after explicit user approval")
        if name == "route":
            command.add_argument("--module", help="Select a module; omit to list the compact module menu")
            command.add_argument("--target", help="Read one indexed method or key-line anchor; related sources remain unopened")
            command.add_argument("--context-lines", type=int, default=12, help="Lines around the unique anchor, from 0 to 40")
        elif name == "apply":
            command.add_argument("--plan", required=True, type=Path)
            command.add_argument("--work-dir", required=True, type=Path)
        elif name == "cache":
            command.add_argument("--apply", action="store_true", help="Refresh the bounded current Cache inventory; never deletes cache payloads")
    args = parser.parse_args()
    try:
        root = project_root(args.project_root)
        skipped = reference_project_result(root, args.project_scope)
        if skipped is not None:
            print(json.dumps(skipped, ensure_ascii=False, sort_keys=True))
            return 0
        match args.command:
            case "inspect":
                result = check_project(root, args.phase, args.changed_path, bootstrap_approved=args.allow_bootstrap)
            case "check":
                result = check_project(root, bootstrap_approved=args.allow_bootstrap)
            case "route":
                result = route_module(root, args.module, args.target, args.context_lines)
            case "apply":
                validate_task_directory(args.plan.parent, root)
                reject_links(args.plan)
                result = apply_plan(root, json.loads(args.plan.read_text(encoding="utf-8")), args.work_dir)
            case "cache":
                result = sync_cache_index(root, apply=args.apply)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] in {"ready", "complete", "unchanged"} else 2
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "pending", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inspect and reconcile an agent-curated, project-local AI index."""

import argparse
import base64
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
from task_artifact_paths import project_artifact_directory, validate_external_directory


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


def check_project(root, phase="start", changed_paths=None, *, bootstrap_approved=False):
    root = project_root(root)
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
    return result


def route_module(root, identifier=None, target=None, context_lines=12):
    root = project_root(root)
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


def apply_plan(root, plan, work_dir):
    root = project_root(root)
    work = validate_external_directory(work_dir, root)
    try:
        with project_lock(root):
            return apply_locked_plan(root, plan, work)
    except (OSError, ValueError) as error:
        return {"status": "pending", "project_root": str(root), "reason": str(error), "unresolved": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "check", "route", "apply"):
        command = commands.add_parser(name)
        command.add_argument("--project-root", required=True, type=Path)
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
    args = parser.parse_args()
    try:
        root = project_root(args.project_root)
        match args.command:
            case "inspect":
                result = check_project(root, args.phase, args.changed_path, bootstrap_approved=args.allow_bootstrap)
            case "check":
                result = check_project(root, bootstrap_approved=args.allow_bootstrap)
            case "route":
                result = route_module(root, args.module, args.target, args.context_lines)
            case "apply":
                validate_external_directory(args.plan.parent, root)
                reject_links(args.plan)
                result = apply_plan(root, json.loads(args.plan.read_text(encoding="utf-8")), args.work_dir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] in {"ready", "complete", "unchanged"} else 2
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "pending", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

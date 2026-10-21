#!/usr/bin/env python3
"""Opportunistic, identity-bound cleanup of registered disposable task runs.

This is a local resource registry, not task memory or a scheduler. Invoke a
checkpoint at task boundaries. Discovery never makes an unknown Cache disposable.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path

import task_artifact_paths as artifacts

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options

REGISTRY = ".task-cache-registry"
SCHEMA = 1
STALE_SECONDS = 86400
PROTECTED_STATES = {"retained", "recovery", "blocked"}
STATES = PROTECTED_STATES | {"working", "complete", "obsolete"}
BARRIERS = {".git", ".keep", ".retain", ".task-cache-retain", ".codex-task-resource-owner.json", ".codex-task-resource-ledger.json"}
MAX_ENTRIES = 1000000


def _key(value):
    return hashlib.sha256(os.fsencode(os.path.normcase(str(value)))).hexdigest()


def _safe_stat(path):
    observed = path.lstat()
    if stat.S_ISLNK(observed.st_mode) or getattr(observed, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
        raise ValueError("symlinks and reparse points are protected")
    if not stat.S_ISDIR(observed.st_mode) and not stat.S_ISREG(observed.st_mode):
        raise ValueError("special files are protected")
    if stat.S_ISREG(observed.st_mode) and observed.st_nlink != 1:
        raise ValueError("hard-linked files are protected")
    return observed


def _identity(observed):
    return [observed.st_dev, observed.st_ino]


def _registry(base, project, create=False):
    base = artifacts.validate_external_directory(base, project)
    directory = base / REGISTRY
    artifacts._check_ancestors(directory)
    if create:
        for name in ("projects", "runs"):
            (directory / name).mkdir(parents=True, exist_ok=True)
            artifacts._check_ancestors(directory / name)
    return directory


def _read(path):
    artifacts._check_ancestors(path.parent)
    _safe_stat(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("unsupported resource registry record")
    return value


@contextlib.contextmanager
def _lock(path):
    lock = path.with_suffix(".lock")
    deadline = time.monotonic() + 3
    while True:
        try:
            with lock.open("x", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
                identity = _identity(os.fstat(stream.fileno()))
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ValueError("resource registry lock busy; retry a later checkpoint")
            time.sleep(0.02)
    try:
        yield
    finally:
        if _identity(_safe_stat(lock)) == identity:
            lock.unlink()


def _write(path, value):
    artifacts._check_ancestors(path.parent)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def register_project(project_root, artifact_root=None, cache_roots=None):
    project = artifacts._absolute_path(project_root, "project_root")
    artifacts._check_ancestors(project)
    project = project.resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    directory = _registry(base, project, create=True)
    record_path = directory / "projects" / (_key(project) + ".json")
    selected = []
    for candidate in cache_roots if cache_roots is not None else [project / "Cache"]:
        cache = artifacts._absolute_path(candidate, "cache_root")
        artifacts._check_ancestors(cache)
        if project not in cache.parents or cache.name.lower() != "cache":
            raise ValueError("Cache roots must be exact project-owned Cache directories")
        selected.append(str(cache))
    with _lock(record_path):
        previous = _read(record_path)["cache_roots"] if record_path.exists() else []
        _write(record_path, {"schema_version": SCHEMA, "project_root": str(project), "cache_roots": sorted(set(previous + selected))})
    return base


def _bound_path(path, project, base):
    artifacts._check_ancestors(path)
    if not path.is_dir():
        raise ValueError("run must be an existing exact directory")
    external = artifacts.project_artifact_directory(project, artifact_root=base)
    if path.parent == external and artifacts.RUN_NAME_RE.fullmatch(path.name):
        return "external"
    registry = _registry(base, project)
    project_record = _read(registry / "projects" / (_key(project) + ".json"))
    roots = [artifacts._absolute_path(root, "registered Cache") for root in project_record["cache_roots"]]
    if project_record["project_root"] != str(project) or any(project not in root.parents or root.name.lower() != "cache" for root in roots):
        raise ValueError("registered Cache ownership is inconsistent")
    if any(root in path.parents and path != root for root in roots):
        if any((ancestor / ".git").exists() for ancestor in (project, *project.parents)):
            git = shutil.which("git")
            if not git:
                raise ValueError("Git tracking probe unavailable")
            tracked = _run_command([git, "-C", str(project), "ls-files", "-z", "--", str(path)])
            if tracked.returncode or tracked.stderr.strip() or tracked.stdout:
                raise ValueError("tracked or unverified Git files are protected")
        return "legacy"
    raise ValueError("run is outside its registered project Cache or exact external owner")


def register_run(project_root, task_id, run_root, *, artifact_root=None, legacy_reason=None, state="working"):
    if not isinstance(task_id, str) or not task_id.strip() or any(ord(char) < 32 for char in task_id):
        raise ValueError("task_id must be a nonempty identifier")
    if state not in STATES:
        raise ValueError("invalid lifecycle state")
    project = artifacts._absolute_path(project_root, "project_root").resolve(strict=True)
    base = register_project(project, artifact_root)
    path = artifacts._absolute_path(run_root, "run_root")
    location = _bound_path(path, project, base)
    if location == "external" and artifacts.RUN_NAME_RE.fullmatch(path.name)["task_key"] != hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:24]:
        raise ValueError("task identifier does not match allocated run")
    # An existing run is never adopted from its name or age. Automatic allocation
    # registers an empty newly created run, before any payload is written.
    populated = any(path.iterdir())
    if (location == "legacy" or populated) and not (isinstance(legacy_reason, str) and legacy_reason.strip()):
        raise ValueError("existing runs require an exact audited disposable reason")
    snapshot = _snapshot(path)
    record_path = _registry(base, project) / "runs" / (_key(path) + ".json")
    now = time.time()
    record = {"schema_version": SCHEMA, "path": str(path), "project_root": str(project), "task_id": task_id, "run_id": artifacts.task_artifact_run_id(path) if location == "external" else uuid.uuid4().hex, "location": location, "identity": snapshot["identity"], "state": state, "heartbeat": now, "registered_at": now, "creator_pid": os.getpid(), "creator_identity": _process_identity(os.getpid()), "disposable_reason": legacy_reason or "fresh task-owned disposable support allocation"}
    with _lock(record_path):
        if record_path.exists():
            raise ValueError("run already registered; use touch/checkpoint without replacing ownership")
        _write(record_path, record)
    return record


def touch_run(project_root, task_id, run_root, *, artifact_root=None, state="working"):
    if state not in STATES:
        raise ValueError("invalid lifecycle state")
    project = Path(project_root).resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    path = artifacts._absolute_path(run_root, "run_root")
    record_path = _registry(base, project) / "runs" / (_key(path) + ".json")
    with _lock(record_path):
        record = _read(record_path)
        if record["task_id"] != task_id or record["project_root"] != str(project) or record["path"] != str(path):
            raise ValueError("lifecycle update does not own this exact task/project/run")
        _bound_path(path, project, base)
        if _identity(_safe_stat(path)) != record["identity"]:
            raise ValueError("run identity changed")
        if record["state"] == "blocked":
            raise ValueError("blocked deletion requires owner review; touch cannot bypass it")
        if record["state"] in {"retained", "recovery"} and state not in {"retained", "recovery"}:
            raise ValueError("retention/recovery must be released by its actual owner; finish cannot erase protection")
        record.update(state=state, heartbeat=time.time())
        _write(record_path, record)
    return record


def release_retention(project_root, task_id, run_root, *, run_id, expected_identity, reason,
                      artifact_root=None, budget_seconds=30):
    """Release only an actual owner's explicitly retired retention/recovery run."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("retention release requires the owner's nonempty reason")
    if not 0 < budget_seconds <= 300:
        raise ValueError("release budget must be between 0 and 300 seconds")
    deadline = time.monotonic() + budget_seconds
    project = Path(project_root).resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    path = artifacts._absolute_path(run_root, "run_root")
    record_path = _registry(base, project) / "runs" / (_key(path) + ".json")
    with _lock(record_path):
        record = _read(record_path)
        if (record["task_id"] != task_id or record["project_root"] != str(project)
                or record["path"] != str(path) or record["run_id"] != run_id):
            raise ValueError("retention release does not own this exact project/task/run")
        if record["state"] not in {"retained", "recovery"}:
            raise ValueError("only retained/recovery runs permit explicit owner release")
        if list(expected_identity) != record["identity"]:
            raise ValueError("retention release identity does not match registered run")
        _bound_path(path, project, base)
        snapshot = _snapshot(path, deadline)
        if snapshot["identity"] != record["identity"]:
            raise ValueError("retained run identity changed")
        activity = probe_activity(path, deadline=deadline)
        if not activity["safe"]:
            raise ValueError("retention release consumer check: " + activity["reason"])
        if _snapshot(path, deadline) != snapshot:
            raise ValueError("retained run changed during consumer readback")
        record["retention_release"] = {"previous_state": record["state"], "reason": reason.strip(),
                                       "released_at": time.time(), "consumer_probe": activity}
        record.update(state="complete", heartbeat=time.time())
        _write(record_path, record)
    return record


def _snapshot(path, deadline=None):
    artifacts._check_ancestors(path)
    root = _safe_stat(path)
    entries = {}
    latest = 0
    byte_count = 0
    pending = [path]
    while pending:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError("checkpoint inspection budget exhausted; preserve this run")
        current = pending.pop()
        observed = _safe_stat(current)
        if observed.st_dev != root.st_dev:
            raise ValueError("mounted filesystems are protected")
        if current != path and current.name in BARRIERS:
            raise ValueError("Git, retention or native resource-ledger barrier")
        latest = max(latest, observed.st_mtime_ns, observed.st_ctime_ns)
        relative = str(current.relative_to(path))
        # ctime tracks provider metadata too; retain it for inactivity age above,
        # but bind deletion to object, permissions, size and content-write time.
        entries[relative] = (observed.st_dev, observed.st_ino, observed.st_mode, observed.st_size, observed.st_mtime_ns)
        if len(entries) > MAX_ENTRIES:
            raise ValueError("run exceeds bounded inspection limit")
        if stat.S_ISDIR(observed.st_mode):
            pending.extend(current.iterdir())
        else:
            byte_count += observed.st_size
    return {"identity": _identity(root), "entries": entries, "latest": latest / 1000000000, "bytes": byte_count}


def _run_command(arguments, timeout=10):
    return subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=False, **hidden_process_options())


def _remaining(deadline):
    remaining = 10 if deadline is None else min(10, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("checkpoint activity budget exhausted")
    return remaining


def _process_identity(pid, deadline=None):
    if sys.platform == "darwin" or sys.platform.startswith("linux"):
        ps = shutil.which("ps")
        if ps:
            result = _run_command([ps, "-p", str(pid), "-o", "pid=,lstart="], timeout=_remaining(deadline))
            if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
                return None
            if result.returncode == 0 and result.stdout.strip() and not result.stderr.strip():
                return result.stdout.strip()
        return "unverified"
    else:
        return "unverified"


def _outside_mount_warnings(path, stderr, *, deadline=None):
    """Classify only macOS stat warnings for verified, disjoint mounts."""
    if sys.platform != "darwin":
        return None
    mount = shutil.which("mount")
    if not mount:
        return None
    inventory = _run_command([mount], timeout=_remaining(deadline))
    if inventory.returncode or inventory.stderr.strip():
        return None
    mounts = {}
    for line in inventory.stdout.splitlines():
        match = re.fullmatch(r".+ on (/.*) \(([^, )]+)(?:, (.*))?\)", line)
        if not match:
            return None
        location, filesystem, flags = match.groups()
        if location != os.path.normpath(location) or location in mounts:
            return None
        mounts[location] = (filesystem, set((flags or "").split(", ")))
    target = Path(path).resolve(strict=True)
    ancestors = [location for location in mounts if target.is_relative_to(location)]
    if not ancestors or "local" not in mounts[max(ancestors, key=len)][1]:
        return None
    lines = stderr.strip().splitlines()
    warnings = []
    index = 0
    while index < len(lines):
        match = re.fullmatch(r"lsof: WARNING: can't stat\(\) ([^ ]+) file system (/.*)", lines[index])
        if not match or index + 1 >= len(lines) or lines[index + 1].strip() != "Output information may be incomplete.":
            return None
        filesystem, location = match.groups()
        if filesystem != "smbfs" or location not in mounts or mounts[location][0] != filesystem or "local" in mounts[location][1]:
            return None
        warned = Path(location)
        if target.is_relative_to(warned) or warned.is_relative_to(target):
            return None
        block = lines[index:index + 2]
        index += 2
        if index < len(lines) and re.fullmatch(r'\s+assuming "dev=[0-9a-fA-Fx]+" from mount table', lines[index]):
            block.append(lines[index])
            index += 1
        warnings.append("\n".join(block))
    return warnings or None


def probe_activity(path, *, deadline=None):
    """Fresh native consumers; unsupported/inaccessible probes fail closed."""
    if sys.platform == "darwin" or sys.platform.startswith("linux"):
        lsof = shutil.which("lsof")
        ps = shutil.which("ps")
        if not lsof or not ps:
            return {"safe": False, "pending": True, "reason": "lsof/ps unavailable; consumer probe pending"}
        opened = _run_command([lsof, "-nP", "+D", str(path), "-Fpn"], timeout=_remaining(deadline))
        warnings = _outside_mount_warnings(path, opened.stderr, deadline=deadline) if opened.stderr.strip() and opened.returncode in {0, 1} else []
        if opened.returncode not in {0, 1} or warnings is None:
            return {"safe": False, "pending": True, "reason": "open-file probe incomplete: " + opened.stderr.strip()[:300]}
        context = {"scope_warnings": warnings} if warnings else {}
        if opened.stdout.strip():
            return {**context, "safe": False, "reason": "active open files or working directory"}
        processes = _run_command([ps, "-axo", "pid=,command="], timeout=_remaining(deadline))
        if processes.returncode or processes.stderr.strip():
            return {**context, "safe": False, "pending": True, "reason": "process probe incomplete"}
        for line in processes.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0] != str(os.getpid()) and str(path) in parts[1]:
                return {**context, "safe": False, "reason": "active process references exact run", "pid": parts[0]}
        return {**context, "safe": True, "reason": "native open-file and process probes clear"}
    elif sys.platform == "win32":
        return {"safe": False, "pending": True, "reason": "Windows native handle probe unavailable; owner-native cleanup required"}
    else:
        return {"safe": False, "pending": True, "reason": "unsupported host activity probe"}


def _remove_snapshot(path, snapshot):
    # Recheck each entry while deleting. Do not follow newly introduced links or
    # remove a replacement file. Failure remains blocked rather than auto-retried.
    for relative, expected in sorted(snapshot["entries"].items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
        current = path / relative
        artifacts._check_ancestors(current.parent)
        observed = _safe_stat(current)
        stable = (observed.st_dev, observed.st_ino, observed.st_mode)
        if stable != expected[:3]:
            raise ValueError("entry identity changed during deletion")
        if stat.S_ISDIR(observed.st_mode):
            current.rmdir()
        else:
            if (observed.st_size, observed.st_mtime_ns) != expected[3:]:
                raise ValueError("file changed during deletion")
            current.unlink()


def _sweep_record(record_path, base, task_id, current_run, apply, now, deadline):
    with _lock(record_path):
        record = _read(record_path)
        path = artifacts._absolute_path(record["path"], "registered run")
        project = Path(record["project_root"])
        result = {"path": str(path), "task_id": record["task_id"], "run_id": record["run_id"]}
        if record_path.stem != _key(path):
            raise ValueError("registry filename does not match exact run")
        if not path.exists() and not path.is_symlink():
            if apply:
                record_path.unlink()
            return {**result, "action": "absent"}
        if record["state"] not in STATES:
            raise ValueError("invalid registered lifecycle state")
        if record["state"] in PROTECTED_STATES or path == current_run:
            return {**result, "action": "keep", "reason": "current, retained, recovery or blocked run"}
        own = record["task_id"] == task_id
        if own and record["state"] not in {"complete", "obsolete"}:
            return {**result, "action": "keep", "reason": "own working run needs an exact completion or transition"}
        if not own and now - record["heartbeat"] < STALE_SECONDS:
            return {**result, "action": "keep", "reason": "foreign run updated within 24 hours"}
        _bound_path(path, project, base)
        snapshot = _snapshot(path, deadline)
        if snapshot["identity"] != record["identity"]:
            raise ValueError("registered run identity changed")
        inactive = now - max(record["heartbeat"], snapshot["latest"])
        if not own and inactive < STALE_SECONDS:
            return {**result, "action": "keep", "reason": "foreign run updated within 24 hours"}
        if not own and record["state"] == "working":
            creator = _process_identity(record["creator_pid"], deadline)
            if creator == "unverified":
                return {**result, "action": "pending", "reason": "original producer process identity is unverified"}
            if creator is not None and creator == record["creator_identity"]:
                return {**result, "action": "keep", "reason": "original producer process remains alive"}
        activity = probe_activity(path, deadline=deadline)
        if activity.get("scope_warnings"):
            result["scope_warnings"] = activity["scope_warnings"]
        if not activity["safe"]:
            return {**result, "action": "pending" if activity.get("pending") else "keep", "reason": activity["reason"]}
        if not apply:
            return {**result, "action": "eligible", "bytes": snapshot["bytes"], "inactive_seconds": inactive}
        # The scan output is never a deletion plan. Re-read the actual tree and
        # consumers under the registry lock immediately before touching payload.
        fresh = _snapshot(path, deadline)
        if fresh["entries"] != snapshot["entries"]:
            raise ValueError("run changed after inspection")
        activity = probe_activity(path, deadline=deadline)
        if activity.get("scope_warnings"):
            result["scope_warnings"] = list(dict.fromkeys(result.get("scope_warnings", []) + activity["scope_warnings"]))
        if not activity["safe"]:
            return {**result, "action": "pending" if activity.get("pending") else "keep", "reason": activity["reason"]}
        if _snapshot(path, deadline)["entries"] != snapshot["entries"]:
            raise ValueError("run changed during consumer readback")
        record["state"] = "blocked"
        record["block_reason"] = "deletion started; any interruption requires owner review"
        _write(record_path, record)
        _remove_snapshot(path, snapshot)
        record_path.unlink()
        return {**result, "action": "deleted", "bytes": snapshot["bytes"]}


def checkpoint(project_root, task_id, *, artifact_root=None, phase="start", current_run=None, obsolete_runs=(), apply=False, budget_seconds=30):
    if phase not in {"start", "transition", "finish"}:
        raise ValueError("invalid checkpoint phase")
    if not 0 < budget_seconds <= 300:
        raise ValueError("checkpoint budget must be between 0 and 300 seconds")
    deadline = time.monotonic() + budget_seconds
    project = Path(project_root).resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    current = artifacts._absolute_path(current_run, "current_run") if current_run else None
    if current in [Path(value) for value in obsolete_runs]:
        raise ValueError("current run cannot also be obsolete")
    if not apply and (obsolete_runs or phase == "finish"):
        raise ValueError("lifecycle changes require --apply; scan is read-only")
    for previous in obsolete_runs:
        touch_run(project, task_id, previous, artifact_root=base, state="obsolete")
    if phase == "finish":
        if current is None:
            raise ValueError("finish requires exact current_run")
        touch_run(project, task_id, current, artifact_root=base, state="complete")
        current = None
    directory = _registry(base, project)
    results = []
    for record_path in sorted((directory / "runs").glob("*.json")):
        if time.monotonic() >= deadline:
            results.append({"record": str(record_path), "action": "pending", "reason": "checkpoint budget exhausted; remaining records await next checkpoint"})
            break
        try:
            results.append(_sweep_record(record_path, base, task_id, current, apply, time.time(), deadline))
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            results.append({"record": str(record_path), "action": "pending", "reason": str(error)})
    return {"phase": phase, "applied": apply, "results": results, "bytes_deleted": sum(item.get("bytes", 0) for item in results if item["action"] == "deleted")}


def scan(project_root, artifact_root=None):
    project = Path(project_root).resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    directory = _registry(base, project)
    records = []
    errors = []
    known = set()
    for record_path in sorted((directory / "runs").glob("*.json")):
        try:
            record = _read(record_path)
            records.append(record)
            known.add(record["path"])
        except (OSError, ValueError, KeyError) as error:
            errors.append({"path": str(record_path), "reason": str(error)})
    unknown = []
    violations = []
    for record_path in sorted((directory / "projects").glob("*.json")):
        try:
            record = _read(record_path)
            owner = Path(record["project_root"])
            roots = [Path(value) for value in record["cache_roots"]]
            for cache in roots:
                if cache.is_dir():
                    violations.extend(_cache_violations(cache, owner))
            roots.append(artifacts.project_artifact_directory(owner, artifact_root=base))
            for root in roots:
                artifacts._check_ancestors(root)
                if root.is_dir():
                    unknown.extend({"path": str(child), "project_root": str(owner), "action": "needs-review"} for child in root.iterdir() if str(child) not in known)
        except (OSError, ValueError, KeyError) as error:
            errors.append({"path": str(record_path), "reason": str(error)})
    return {"registered": records, "unclassified": unknown, "violations": violations, "errors": errors}


def _cache_violations(cache, project):
    artifacts._check_ancestors(cache)
    return [{"path": str(child), "project_root": str(project), "action": "needs-review", "reason": "project Cache permits only temp-* or remote-* child directories"} for child in cache.iterdir() if child.is_symlink() or not child.is_dir() or not child.name.startswith(("temp-", "remote-"))]


def discover(search_roots, *, project_root, artifact_root=None, apply=False, limit=100000):
    """One bounded inventory; later checkpoints use the registry, not whole disk."""
    found = []
    violations = []
    unclassified = []
    errors = []
    project = Path(project_root).resolve(strict=True)
    base = artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    known = {str(project / "Cache"): project}
    for record_path in (_registry(base, project) / "projects").glob("*.json"):
        record = _read(record_path)
        known.update({value: Path(record["project_root"]) for value in record["cache_roots"]})
    count = 0
    for search in search_roots:
        root = artifacts._absolute_path(search, "search_root")
        artifacts._check_ancestors(root)
        device = root.stat().st_dev
        pending = [root]
        while pending and count < limit:
            current = pending.pop()
            count += 1
            try:
                observed = _safe_stat(current)
                if observed.st_dev != device:
                    continue
                if current.name.lower() == "cache":
                    owner = known.get(str(current))
                    if owner is None and (current.parent / ".git").exists():
                        owner = current.parent
                    if owner is None:
                        unclassified.append({"path": str(current), "action": "native_or_unclassified", "reason": "not a verified project Cache root; no naming violation or deletion authority"})
                    else:
                        found.append({"path": str(current), "project_root": str(owner), "action": "needs-review"})
                        violations.extend(_cache_violations(current, owner))
                        if apply:
                            register_project(owner, artifact_root=base, cache_roots=[current])
                    continue
                pending.extend(child for child in current.iterdir() if child.name not in {".git", "node_modules", REGISTRY, ".codex", ".agents"} and child.is_dir() and not child.is_symlink())
            except (OSError, ValueError) as error:
                errors.append({"path": str(current), "reason": str(error)})
    return {"cache_roots": found, "unclassified_cache_roots": unclassified, "violations": violations, "errors": errors, "visited": count, "limit_reached": count >= limit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "scan", "register", "touch", "release-retention", "checkpoint"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--task-id")
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--run-id", help="Registered run ID required for explicit retention release")
    parser.add_argument("--identity", type=int, nargs=2, metavar=("DEVICE", "INODE"), help="Registered directory identity required for retention release")
    parser.add_argument("--state", choices=sorted(STATES), default="working")
    parser.add_argument("--reason", help="Exact audited evidence that an existing run is disposable")
    parser.add_argument("--phase", choices=("start", "transition", "finish"), default="start")
    parser.add_argument("--current-run", type=Path)
    parser.add_argument("--obsolete-run", type=Path, action="append", default=[])
    parser.add_argument("--search-root", type=Path, action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--budget-seconds", type=float, default=30)
    args = parser.parse_args()
    try:
        if args.command in {"register", "touch", "release-retention", "checkpoint"} and not args.task_id:
            raise ValueError("this command requires --task-id")
        if args.command in {"register", "touch", "release-retention"} and args.run_root is None:
            raise ValueError("this command requires --run-root")
        if args.command == "discover":
            if not args.search_root:
                raise ValueError("discover requires explicit --search-root")
            result = discover(args.search_root, project_root=args.project_root, artifact_root=args.artifact_root, apply=args.apply)
        elif args.command == "scan":
            result = scan(args.project_root, args.artifact_root)
        elif args.command == "register":
            result = register_run(args.project_root, args.task_id, args.run_root, artifact_root=args.artifact_root, legacy_reason=args.reason, state=args.state)
        elif args.command == "touch":
            result = touch_run(args.project_root, args.task_id, args.run_root, artifact_root=args.artifact_root, state=args.state)
        elif args.command == "release-retention":
            if not args.run_id or args.identity is None:
                raise ValueError("retention release requires --run-id and --identity")
            result = release_retention(args.project_root, args.task_id, args.run_root, run_id=args.run_id,
                                       expected_identity=args.identity, reason=args.reason,
                                       artifact_root=args.artifact_root, budget_seconds=args.budget_seconds)
        else:
            result = checkpoint(args.project_root, args.task_id, artifact_root=args.artifact_root, phase=args.phase, current_run=args.current_run, obsolete_runs=args.obsolete_run, apply=args.apply, budget_seconds=args.budget_seconds)
        print(json.dumps(result, sort_keys=True))
        return 2 if any(item.get("action") == "pending" for item in result.get("results", [])) else 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "error", "reason": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

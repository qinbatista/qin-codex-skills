#!/usr/bin/env python3
"""Opportunistic, identity-bound cleanup of registered disposable task runs.

This is a local resource registry, not task memory or a scheduler. Invoke a
checkpoint at task boundaries. Discovery never makes an unknown Cache disposable.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import gzip
import hashlib
import json
import os
import plistlib
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

REGISTRY = "remote-task-cache-registry"
LEGACY_REGISTRY = ".task-cache-registry"
SCHEMA = 1
STALE_SECONDS = 86400
PROTECTED_STATES = {"retained", "recovery", "blocked"}
STATES = PROTECTED_STATES | {"working", "complete", "obsolete"}
BARRIERS = {".git", ".keep", ".retain", ".task-cache-retain", ".codex-task-resource-owner.json", ".codex-task-resource-ledger.json"}
MAX_ENTRIES = 1000000
MAX_PLAN_BYTES = 256 * 1024 * 1024
LOCK_PROTOCOL = "task-cache-native-lock-v1"


def _native_file_lock(stream, acquire):
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK if acquire else msvcrt.LK_UNLCK, 1)
    elif sys.platform == "darwin" or sys.platform.startswith("linux"):
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB if acquire else fcntl.LOCK_UN)
    else:
        raise ValueError("native registry locking unavailable on this host")


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


def _volume_identity(path):
    """macOS device numbers change after reboot; a volume UUID does not."""
    if sys.platform != "darwin":
        return None
    executable = shutil.which("diskutil")
    filesystem_tool = shutil.which("df")
    if executable is None or filesystem_tool is None:
        return None
    try:
        filesystem = _run_command([filesystem_tool, "-P", str(path)], timeout=5)
        rows = filesystem.stdout.splitlines()
        if filesystem.returncode or filesystem.stderr.strip() or len(rows) != 2:
            return None
        device = rows[1].split()[0]
        if re.fullmatch(r"/dev/disk[0-9]+(?:s[0-9]+)*", device) is None:
            return None
        result = _run_command([executable, "info", "-plist", device], timeout=5)
        if result.returncode or result.stderr.strip():
            return None
        volume = plistlib.loads(result.stdout.encode("utf-8"))
        if volume.get("DeviceNode") != device or Path(volume.get("MountPoint", "")).stat().st_dev != Path(path).stat().st_dev:
            return None
        value = volume.get("VolumeUUID")
        return str(uuid.UUID(value)) if isinstance(value, str) else None
    except (OSError, ValueError, plistlib.InvalidFileException, subprocess.TimeoutExpired):
        return None


def _record_identity_matches(path, record):
    identity = _identity(_safe_stat(path))
    if identity == record["identity"]:
        return True
    stored_volume = record.get("filesystem_uuid")
    return bool(stored_volume and identity[1] == record["identity"][1] and _volume_identity(path) == stored_volume)


def _cleanup_base(project, artifact_root=None):
    """Accept an existing legacy ledger for cleanup, never new allocation."""
    project = Path(project).resolve(strict=True)
    if artifact_root is None or Path(artifact_root) == project / "Cache":
        return artifacts.resolve_artifact_base(project, artifact_root=artifact_root)
    base = artifacts._absolute_path(artifact_root, "legacy artifact directory")
    artifacts._check_ancestors(base)
    codex = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve(strict=False)
    if (base == Path(base.anchor) or base == Path.home() or artifacts._codex_component(base)
            or any(artifacts._within(base, owner) for owner in (project, codex, Path.home() / ".agents"))
            or any((owner / ".git").exists() for owner in (base, *base.parents))):
        raise ValueError("legacy cleanup must remain outside projects and Codex storage")
    record = _read(base / LEGACY_REGISTRY / "projects" / (_key(project) + ".json"))
    if record.get("project_root") != str(project):
        raise ValueError("legacy artifact ledger does not own the exact project")
    return base


def _legacy_base(project):
    base = artifacts.legacy_artifact_base()
    if not (base / LEGACY_REGISTRY / "projects" / (_key(project) + ".json")).is_file():
        return None
    return _cleanup_base(project, base)


def _registry(base, project, create=False):
    base = artifacts.resolve_artifact_base(project, artifact_root=base) if create else _cleanup_base(project, base)
    directory = base / (REGISTRY if base == Path(project) / "Cache" else LEGACY_REGISTRY)
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
    """Finite native locks survive crashes; markers interoperate with old writers."""
    if path.parent.name not in {"projects", "runs"} or re.fullmatch(r"[0-9a-f]{64}\.json", path.name) is None:
        raise ValueError("registry lock requires an exact project or run record")
    directory = path.parent.parent
    pool = directory / "locks"
    artifacts._check_ancestors(pool)
    pool.mkdir(exist_ok=True)
    bucket = pool / (f"{int(_key(path)[:2], 16) % 64:02x}.lock")
    artifacts._check_ancestors(pool)
    lock = path.with_suffix(".lock")
    deadline = time.monotonic() + 3
    descriptor = os.open(bucket, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "r+b") as stream:
        opened = os.fstat(stream.fileno())
        named = bucket.lstat()
        if not stat.S_ISREG(named.st_mode) or getattr(named, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0) or _identity(opened) != _identity(named):
            raise ValueError("native registry lock identity changed")
        while True:
            try:
                _native_file_lock(stream, True)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                if time.monotonic() >= deadline:
                    raise ValueError("resource registry lock busy; native owner is still holding it") from error
                time.sleep(0.02)
        owned = False
        prepared = False
        try:
            opened = os.fstat(stream.fileno())
            if opened.st_nlink != 1:
                stream.seek(0)
                claim = json.loads(stream.read().decode("utf-8"))
                relative = claim.get("record", "")
                if opened.st_nlink != 2 or claim.get("protocol") != LOCK_PROTOCOL or claim.get("bucket") != bucket.name or re.fullmatch(r"(?:projects|runs)/[0-9a-f]{64}\.json", relative) is None:
                    raise ValueError("native lock claim proof is inconsistent; preserve its aliases")
                abandoned = (directory / relative).with_suffix(".lock")
                artifacts._check_ancestors(abandoned.parent)
                observed = abandoned.lstat()
                if _identity(observed) != _identity(opened) or not stat.S_ISREG(observed.st_mode):
                    raise ValueError("native lock marker identity changed")
                abandoned.unlink()
            prepared = True
            claim = {"protocol": LOCK_PROTOCOL, "bucket": bucket.name, "record": path.relative_to(directory).as_posix()}
            stream.seek(0)
            stream.truncate()
            stream.write(json.dumps(claim, sort_keys=True).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
            while True:
                try:
                    # Link a complete claim atomically; a killed writer cannot
                    # leave an ownerless, empty O_EXCL marker behind.
                    os.link(bucket, lock)
                    owned = True
                    if _identity(lock.lstat()) != _identity(os.fstat(stream.fileno())) or _identity(bucket.lstat()) != _identity(os.fstat(stream.fileno())):
                        raise ValueError("native registry lock namespace changed")
                    break
                except FileExistsError:
                    observed = _safe_stat(lock)
                    contents = lock.read_text(encoding="utf-8").strip()
                    if contents.isdigit() and _process_identity(int(contents)) is None:
                        if _identity(_safe_stat(lock)) != _identity(observed) or lock.read_text(encoding="utf-8").strip() != contents:
                            raise ValueError("legacy lock changed during owner readback")
                        lock.unlink()
                        continue
                    if not contents.isdigit():
                        raise ValueError("legacy lock owner proof is unavailable; owner review required")
                    if time.monotonic() >= deadline:
                        raise ValueError("legacy registry lock still has a live or unverified owner")
                    time.sleep(0.02)
            yield
        finally:
            try:
                if prepared:
                    observed = lock.lstat() if lock.exists() or lock.is_symlink() else None
                    if observed is not None and _identity(observed) == _identity(os.fstat(stream.fileno())) and stat.S_ISREG(observed.st_mode):
                        lock.unlink()
                    elif owned:
                        raise ValueError("registry lock marker changed during operation")
                    if os.fstat(stream.fileno()).st_nlink != 1:
                        raise ValueError("native registry lock has an unknown alias")
                    stream.seek(0)
                    stream.truncate()
                    stream.write(b"{}\n")
                    stream.flush()
            finally:
                _native_file_lock(stream, False)


def _write(path, value):
    artifacts._check_ancestors(path.parent)
    temporary = path.with_name(path.name + ".pending")
    _discard_control_pending(temporary)
    created = None
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            created = _identity(os.fstat(stream.fileno()))
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if created is not None and (temporary.exists() or temporary.is_symlink()):
            if _identity(_safe_stat(temporary)) != created:
                raise ValueError("temporary control record identity changed")
            temporary.unlink()


def _discard_control_pending(path):
    if path.exists() or path.is_symlink():
        before = _safe_stat(path)
        activity = probe_activity(path)
        if not activity["safe"]:
            raise ValueError("uncommitted control record has a current reader: " + activity["reason"])
        after = _safe_stat(path)
        fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in fields):
            raise ValueError("uncommitted control record changed")
        path.unlink()


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
    registry = _registry(base, project)
    project_record = _read(registry / "projects" / (_key(project) + ".json"))
    roots = [artifacts._absolute_path(root, "registered Cache") for root in project_record["cache_roots"]]
    if project_record["project_root"] != str(project) or any(project not in root.parents or root.name.lower() != "cache" for root in roots):
        raise ValueError("registered Cache ownership is inconsistent")
    external = base if base == project / "Cache" else base / ("p-" + _key(project)[:16])
    if path.parent == external and artifacts.RUN_NAME_RE.fullmatch(path.name):
        location, boundary = ("project" if base == project / "Cache" else "legacy-external"), external
    elif base != project / "Cache" and path.parent == external and re.fullmatch(r"t-[0-9a-f]{24}", path.name):
        location, boundary = "legacy-external", external
    else:
        matches = [root for root in roots if root in path.parents]
        if not matches:
            raise ValueError("run is outside its registered project Cache or exact external owner")
        location, boundary = "legacy", max(matches, key=lambda value: len(value.parts))
    if _safe_stat(path).st_dev != _safe_stat(boundary).st_dev:
        raise ValueError("mounted resources require their native owner")
    for ancestor in path.parents:
        if ancestor == boundary:
            break
        if any((ancestor / marker).exists() or (ancestor / marker).is_symlink() for marker in BARRIERS):
            raise ValueError("ancestor Git, retention or native resource ledger is protected")
        parent_record = registry / "runs" / (_key(ancestor) + ".json")
        if parent_record.is_file():
            parent = _read(parent_record)
            if parent.get("path") != str(ancestor) or parent.get("project_root") != str(project) or parent.get("state") in PROTECTED_STATES:
                raise ValueError("ancestor registered resource requires its owner's release")
    if project in path.parents and any((ancestor / ".git").exists() for ancestor in (project, *project.parents)):
        git = shutil.which("git")
        if not git:
            raise ValueError("Git tracking probe unavailable")
        tracked = _run_command([git, "-C", str(project), "ls-files", "-z", "--", str(path)])
        if tracked.returncode or tracked.stderr.strip() or tracked.stdout:
            raise ValueError("tracked or unverified Git files are protected")
    return location


def register_run(project_root, task_id, run_root, *, artifact_root=None, legacy_reason=None, state="working"):
    if not isinstance(task_id, str) or not task_id.strip() or any(ord(char) < 32 for char in task_id):
        raise ValueError("task_id must be a nonempty identifier")
    if state not in STATES:
        raise ValueError("invalid lifecycle state")
    project = artifacts._absolute_path(project_root, "project_root").resolve(strict=True)
    base = register_project(project, artifact_root)
    path = artifacts._absolute_path(run_root, "run_root")
    location = _bound_path(path, project, base)
    if location == "project" and artifacts.RUN_NAME_RE.fullmatch(path.name)["task_key"] != hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:24]:
        raise ValueError("task identifier does not match allocated run")
    # An existing run is never adopted from its name or age. Automatic allocation
    # registers an empty newly created run, before any payload is written.
    populated = any(path.iterdir())
    if (location == "legacy" or populated) and not (isinstance(legacy_reason, str) and legacy_reason.strip()):
        raise ValueError("existing runs require an exact audited disposable reason")
    now = time.time()
    retention = _retention_fields(state, legacy_reason, now)
    snapshot = _snapshot(path)
    record_path = _registry(base, project) / "runs" / (_key(path) + ".json")
    record = {"schema_version": SCHEMA, "path": str(path), "project_root": str(project), "task_id": task_id, "run_id": artifacts.task_artifact_run_id(path) if location == "project" else uuid.uuid4().hex, "location": location, "identity": snapshot["identity"], "state": state, "heartbeat": now, "registered_at": now, "creator_pid": os.getpid(), "creator_identity": _process_identity(os.getpid()), "disposable_reason": legacy_reason or "fresh task-owned disposable support allocation"}
    record["filesystem_uuid"] = _volume_identity(path)
    record.update(retention)
    with _lock(record_path):
        if record_path.exists():
            raise ValueError("run already registered; use touch/checkpoint without replacing ownership")
        _write(record_path, record)
    return record


def _retention_fields(state, reason, now):
    if state not in {"retained", "recovery"}:
        return {}
    if not isinstance(reason, str) or not reason.strip() or reason.strip() == "fresh task-owned disposable support allocation":
        raise ValueError("retention/recovery requires a concrete current consumer, review or minimum recovery reason")
    return {"retention_reason": reason.strip(), "retention_review_at": now + STALE_SECONDS}


def touch_run(project_root, task_id, run_root, *, artifact_root=None, state="working", reason=None):
    if state not in STATES:
        raise ValueError("invalid lifecycle state")
    project = Path(project_root).resolve(strict=True)
    base = _cleanup_base(project, artifact_root)
    if base != project / "Cache" and state == "working":
        raise ValueError("legacy external runs are cleanup inputs, not new working output")
    path = artifacts._absolute_path(run_root, "run_root")
    record_path = _registry(base, project) / "runs" / (_key(path) + ".json")
    with _lock(record_path):
        record = _read(record_path)
        if record["task_id"] != task_id or record["project_root"] != str(project) or record["path"] != str(path):
            raise ValueError("lifecycle update does not own this exact task/project/run")
        _bound_path(path, project, base)
        if not _record_identity_matches(path, record):
            raise ValueError("run identity changed")
        if record["state"] == "blocked":
            raise ValueError("blocked deletion requires owner review; touch cannot bypass it")
        if record["state"] in {"retained", "recovery"} and state not in {"retained", "recovery"}:
            raise ValueError("retention/recovery must be released by its actual owner; finish cannot erase protection")
        now = time.time()
        record.update(_retention_fields(state, reason, now))
        record.update(state=state, heartbeat=now)
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
    base = _cleanup_base(project, artifact_root)
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
        snapshot = _snapshot(path, deadline, registry=record_path.parent.parent)
        if not _record_identity_matches(path, record):
            raise ValueError("retained run identity changed")
        activity = probe_activity(path, deadline=deadline)
        if not activity["safe"]:
            raise ValueError("retention release consumer check: " + activity["reason"])
        if _snapshot(path, deadline, registry=record_path.parent.parent) != snapshot:
            raise ValueError("retained run changed during consumer readback")
        record["retention_release"] = {"previous_state": record["state"], "reason": reason.strip(),
                                       "released_at": time.time(), "consumer_probe": activity}
        record.update(state="complete", heartbeat=time.time())
        _write(record_path, record)
    return record


def _snapshot(path, deadline=None, *, include_ctime=False, registry=None):
    artifacts._check_ancestors(path)
    root = _safe_stat(path)
    entries = {}
    latest = 0
    byte_count = 0
    file_ctimes = {}
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
            if registry is not None and current != path:
                child_record = registry / "runs" / (_key(current) + ".json")
                if child_record.exists() or child_record.is_symlink():
                    raise ValueError("registered descendant has a separate lifecycle; close its exact owner before the parent")
            pending.extend(current.iterdir())
        else:
            byte_count += observed.st_size
            if include_ctime:
                file_ctimes[relative] = observed.st_ctime_ns
    result = {"identity": _identity(root), "entries": entries, "latest": latest / 1000000000, "bytes": byte_count}
    if include_ctime:
        result["file_ctimes"] = file_ctimes
    return result


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
        # Inventory open handles once instead of making lsof traverse every file
        # in a large build tree. NUL-delimited names preserve spaces/newlines.
        opened = _run_command([lsof, "-nP", "-Fpn0"], timeout=_remaining(deadline))
        warnings = _outside_mount_warnings(path, opened.stderr, deadline=deadline) if opened.stderr.strip() and opened.returncode in {0, 1} else []
        if opened.returncode not in {0, 1} or warnings is None:
            return {"safe": False, "pending": True, "reason": "open-file probe incomplete: " + opened.stderr.strip()[:300]}
        context = {"scope_warnings": warnings} if warnings else {}
        target = str(Path(path).resolve(strict=True))
        for field in opened.stdout.split("\0"):
            field = field.lstrip("\n")
            if field.startswith("n") and (field[1:] == target or field[1:].startswith(target + os.sep)):
                return {**context, "safe": False, "reason": "active open files or working directory"}
        if opened.stdout.strip() and "\0" not in opened.stdout:
            return {**context, "safe": False, "pending": True, "reason": "open-file probe returned unverified field format"}
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


def _plan_path(record_path):
    return record_path.parent.parent / "deletions" / (record_path.stem + ".json.gz")


def _write_deletion_plan(record_path, record, snapshot):
    target = _plan_path(record_path)
    artifacts._check_ancestors(target.parent)
    target.parent.mkdir(exist_ok=True)
    ignored = {"state", "block_reason", "deletion_plan", "deletion_error", "deletion_attempt_at"}
    plan = {"schema_version": 1, "authority": {key: value for key, value in record.items() if key not in ignored}, "snapshot": snapshot}
    temporary = target.with_name(target.name + ".pending")
    created = None
    try:
        _discard_control_pending(temporary)
        with temporary.open("xb") as stream:
            created = _identity(os.fstat(stream.fileno()))
            with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as compressed:
                count = 0
                for chunk in json.JSONEncoder(sort_keys=True, separators=(",", ":")).iterencode(plan):
                    data = chunk.encode("utf-8")
                    count += len(data)
                    if count > MAX_PLAN_BYTES:
                        raise ValueError("deletion proof exceeds its bounded size; payload preserved")
                    compressed.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        digest = artifacts._file_sha256(temporary)
        temporary.replace(target)
        return {"schema_version": 1, "sha256": digest, "entries": len(snapshot["entries"]), "bytes": snapshot["bytes"]}
    finally:
        if created is not None and temporary.exists():
            if _identity(_safe_stat(temporary)) != created:
                raise ValueError("temporary deletion proof identity changed")
            temporary.unlink()


def _read_deletion_plan(record_path, record):
    metadata = record.get("deletion_plan")
    if not isinstance(metadata, dict) or metadata.get("schema_version") != 1:
        raise ValueError("interrupted deletion has no original proof; exact owner review required")
    target = _plan_path(record_path)
    _safe_stat(target)
    if artifacts._file_sha256(target) != metadata.get("sha256"):
        raise ValueError("original deletion proof changed; payload preserved")
    with gzip.open(target, "rb") as stream:
        raw = stream.read(MAX_PLAN_BYTES + 1)
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError("deletion proof exceeds its bounded size")
    plan = json.loads(raw)
    if not isinstance(plan, dict):
        raise ValueError("invalid original deletion proof")
    ignored = {"state", "block_reason", "deletion_plan", "deletion_error", "deletion_attempt_at"}
    authority = {key: value for key, value in record.items() if key not in ignored}
    if plan.get("schema_version") != 1 or plan.get("authority") != authority:
        raise ValueError("deletion owner or retention evidence changed")
    snapshot = plan.get("snapshot", {})
    if not isinstance(snapshot, dict):
        raise ValueError("invalid original deletion snapshot")
    entries = snapshot.get("entries", {})
    file_ctimes = snapshot.get("file_ctimes", {})
    identity = snapshot.get("identity")
    if not isinstance(identity, list) or len(identity) != 2 or any(type(value) is not int for value in identity) or not isinstance(file_ctimes, dict):
        raise ValueError("invalid original deletion change identity")
    if type(metadata.get("bytes")) is not int or metadata["bytes"] < 0 or snapshot.get("bytes") != metadata["bytes"]:
        raise ValueError("invalid original deletion byte inventory")
    if not isinstance(entries, dict) or len(entries) != metadata.get("entries") or not 0 < len(entries) <= MAX_ENTRIES or "." not in entries:
        raise ValueError("invalid original deletion entry inventory")
    for relative, expected in entries.items():
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts or str(Path(relative)) != relative:
            raise ValueError("invalid original deletion member boundary")
        if not isinstance(expected, list) or len(expected) != 5 or any(type(value) is not int for value in expected):
            raise ValueError("invalid original deletion member identity")
        if stat.S_ISREG(expected[2]) and type(file_ctimes.get(relative)) is not int:
            raise ValueError("missing original deletion member change identity")
    snapshot["entries"] = {relative: tuple(expected) for relative, expected in entries.items()}
    return snapshot


def _remaining_deletion(path, original, deadline, registry=None):
    current = _snapshot(path, deadline, include_ctime=True, registry=registry)
    device = current["identity"][0]
    for relative, observed in current["entries"].items():
        expected = original["entries"].get(relative)
        if expected is None:
            raise ValueError("new member appeared after deletion started; owner review required")
        if expected[0] != original["identity"][0] or observed[:3] != (device, expected[1], expected[2]):
            raise ValueError("deletion member identity changed; replacement preserved")
        if stat.S_ISREG(observed[2]) and (observed[3:] != expected[3:] or current["file_ctimes"][relative] != original["file_ctimes"][relative]):
            raise ValueError("deletion member changed after interruption; payload preserved")
    return current


def _discard_deletion_plan(record_path, record):
    target = _plan_path(record_path)
    if target.exists() or target.is_symlink():
        _safe_stat(target)
        if artifacts._file_sha256(target) != record.get("deletion_plan", {}).get("sha256"):
            raise ValueError("payload is absent but deletion proof changed; owner review required")
        target.unlink()
    _discard_control_pending(target.with_name(target.name + ".pending"))
    _discard_control_pending(record_path.with_name(record_path.name + ".pending"))


def _finish_deletion(record_path, record, path, snapshot, result, deadline):
    try:
        _remove_snapshot(path, snapshot, deadline=deadline)
        if path.exists() or path.is_symlink():
            raise ValueError("deletion absence readback failed")
        _discard_deletion_plan(record_path, record)
        record_path.unlink()
    except Exception as error:
        record["deletion_error"] = {"type": type(error).__name__, "message": str(error)[:600], "at": time.time()}
        _write(record_path, record)
        raise
    return {**result, "action": "deleted", "bytes": snapshot["bytes"]}


def _remove_snapshot(path, snapshot, *, deadline=None):
    # Recheck each entry while deleting. Do not follow newly introduced links or
    # remove a replacement file. Persisted plans permit exact guarded continuation.
    for relative, expected in sorted(snapshot["entries"].items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("deletion paused at its budget; original proof permits the next checkpoint")
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
                _discard_deletion_plan(record_path, record)
                record_path.unlink()
            return {**result, "action": "absent"}
        if record["state"] not in STATES:
            raise ValueError("invalid registered lifecycle state")
        if path == current_run:
            return {**result, "action": "keep", "reason": "current run"}
        if record["state"] == "blocked":
            if not record.get("deletion_plan"):
                return {**result, "action": "pending", "reason": "interrupted legacy deletion has no original proof; exact owner review required"}
            _bound_path(path, project, base)
            if not _record_identity_matches(path, record):
                raise ValueError("interrupted run identity changed")
            original = _read_deletion_plan(record_path, record)
            remaining = _remaining_deletion(path, original, deadline, record_path.parent.parent)
            for attempt in range(2):
                activity = probe_activity(path, deadline=deadline)
                if not activity["safe"]:
                    return {**result, "action": "pending", "reason": activity["reason"], "resumable": True}
                fresh = _remaining_deletion(path, original, deadline, record_path.parent.parent)
                if fresh["entries"] != remaining["entries"] or fresh["file_ctimes"] != remaining["file_ctimes"]:
                    raise ValueError("interrupted deletion changed during consumer readback")
                remaining = fresh
            if not apply:
                return {**result, "action": "eligible", "bytes": remaining["bytes"], "resumable": True}
            return _finish_deletion(record_path, record, path, remaining, {**result, "resumed": True}, deadline)
        if record["state"] in {"retained", "recovery"}:
            retention_reason = record.get("retention_reason")
            review_at = record.get("retention_review_at")
            if (not isinstance(retention_reason, str) or not retention_reason.strip()
                    or retention_reason == "fresh task-owned disposable support allocation"
                    or not isinstance(review_at, (int, float)) or not now < review_at <= record["heartbeat"] + STALE_SECONDS):
                return {**result, "action": "pending", "reason": "retention owner review required; renew a concrete need or explicitly release the exact run", "retention_reason": retention_reason, "retention_review_at": review_at}
            return {**result, "action": "keep", "reason": "current retention need recorded", "retention_reason": retention_reason, "retention_review_at": review_at}
        own = record["task_id"] == task_id
        if own and record["state"] not in {"complete", "obsolete"}:
            return {**result, "action": "keep", "reason": "own working run needs an exact completion or transition"}
        if not own and record["state"] == "working" and now - record["heartbeat"] < STALE_SECONDS:
            return {**result, "action": "keep", "reason": "foreign run updated within 24 hours"}
        _bound_path(path, project, base)
        snapshot = _snapshot(path, deadline, registry=record_path.parent.parent)
        if not _record_identity_matches(path, record):
            raise ValueError("registered run identity changed")
        inactive = now - max(record["heartbeat"], snapshot["latest"])
        if not own and record["state"] == "working" and inactive < STALE_SECONDS:
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
        fresh = _snapshot(path, deadline, registry=record_path.parent.parent)
        if fresh["entries"] != snapshot["entries"]:
            raise ValueError("run changed after inspection")
        activity = probe_activity(path, deadline=deadline)
        if activity.get("scope_warnings"):
            result["scope_warnings"] = list(dict.fromkeys(result.get("scope_warnings", []) + activity["scope_warnings"]))
        if not activity["safe"]:
            return {**result, "action": "pending" if activity.get("pending") else "keep", "reason": activity["reason"]}
        proof = _snapshot(path, deadline, include_ctime=True, registry=record_path.parent.parent)
        if proof["entries"] != snapshot["entries"]:
            raise ValueError("run changed during consumer readback")
        record["deletion_plan"] = _write_deletion_plan(record_path, record, proof)
        record["state"] = "blocked"
        record["block_reason"] = "deletion started; resume only the unchanged original proof"
        _write(record_path, record)
        return _finish_deletion(record_path, record, path, proof, result, deadline)


def checkpoint(project_root, task_id, *, artifact_root=None, phase="start", current_run=None, obsolete_runs=(), apply=False, budget_seconds=30, requested_only=False):
    if phase not in {"start", "transition", "finish"}:
        raise ValueError("invalid checkpoint phase")
    if not 0 < budget_seconds <= 300:
        raise ValueError("checkpoint budget must be between 0 and 300 seconds")
    deadline = time.monotonic() + budget_seconds
    project = Path(project_root).resolve(strict=True)
    base = _cleanup_base(project, artifact_root)
    current = artifacts._absolute_path(current_run, "current_run") if current_run else None
    requested = [artifacts._absolute_path(value, "obsolete_run") for value in obsolete_runs]
    if phase == "finish" and current is not None:
        requested.append(current)
    if requested_only and not requested:
        raise ValueError("requested-only cleanup requires exact finished or obsolete runs")
    if current in [Path(value) for value in obsolete_runs]:
        raise ValueError("current run cannot also be obsolete")
    if not apply and (obsolete_runs or phase == "finish"):
        raise ValueError("lifecycle changes require --apply; scan is read-only")
    for previous in obsolete_runs:
        previous_path = Path(previous)
        previous_record = _registry(base, project) / "runs" / (_key(previous_path) + ".json")
        if previous_path.exists() and (not previous_record.exists() or _read(previous_record).get("state") != "blocked"):
            touch_run(project, task_id, previous, artifact_root=base, state="obsolete")
    if phase == "finish":
        if current is None:
            raise ValueError("finish requires exact current_run")
        current_record = _registry(base, project) / "runs" / (_key(current) + ".json")
        if current_record.exists():
            owner = _read(current_record)
            if owner.get("task_id") != task_id or owner.get("project_root") != str(project) or owner.get("path") != str(current):
                raise ValueError("finish does not own the exact project/task/run")
            if current.exists() and owner["state"] != "blocked":
                touch_run(project, task_id, current, artifact_root=base, state="complete")
        elif current.exists() or current.is_symlink():
            raise ValueError("finish cannot adopt an unregistered existing run")
        current = None
    bases = [base]
    if base == project / "Cache":
        legacy = _legacy_base(project)
        if legacy is not None and legacy != base:
            bases.append(legacy)
    results = []
    records = [(owner, record) for owner in bases for record in sorted((_registry(owner, project) / "runs").glob("*.json"))]
    requested_keys = {_key(path) for path in requested}
    if requested_only:
        records = [(owner, record) for owner, record in records if record.stem in requested_keys]
    def priority(item):
        owner, record_path = item
        if record_path.stem in requested_keys:
            return 0
        try:
            return 1 if _read(record_path).get("task_id") == task_id else 2
        except (OSError, ValueError):
            return 2
    records.sort(key=priority)
    for owner, record_path in records:
        if time.monotonic() >= deadline:
            results.append({"record": str(record_path), "action": "pending", "reason": "checkpoint budget exhausted; remaining records await next checkpoint"})
            break
        try:
            results.append(_sweep_record(record_path, owner, task_id, current, apply, time.time(), deadline))
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            results.append({"record": str(record_path), "action": "pending", "reason": str(error)})
    completed = all(not path.exists() and not path.is_symlink() and not (_registry(base, project) / "runs" / (_key(path) + ".json")).exists() for path in requested) if requested else None
    try:
        remote_review = _remote_owner_review(project / "Cache", project)
    except (OSError, ValueError) as error:
        remote_review = []
        results.append({"path": str(project / "Cache"), "action": "pending", "reason": "remote owner inventory failed: " + str(error)})
    return {"phase": phase, "applied": apply, "results": results, "requested_complete": completed, "remote_review": remote_review, "bytes_deleted": sum(item.get("bytes", 0) for item in results if item["action"] == "deleted")}


def scan(project_root, artifact_root=None):
    project = Path(project_root).resolve(strict=True)
    base = _cleanup_base(project, artifact_root)
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
    remote_review = {}
    try:
        remote_review.update((item["path"], item) for item in _remote_owner_review(project / "Cache", project))
    except (OSError, ValueError) as error:
        errors.append({"path": str(project / "Cache"), "reason": str(error)})
    for record_path in sorted((directory / "projects").glob("*.json")):
        try:
            record = _read(record_path)
            owner = Path(record["project_root"])
            roots = [Path(value) for value in record["cache_roots"]]
            for cache in roots:
                if cache.is_dir():
                    violations.extend(_cache_violations(cache, owner))
                    remote_review.update((item["path"], item) for item in _remote_owner_review(cache, owner))
            roots.append(owner / "Cache" if base == owner / "Cache" else base / ("p-" + _key(owner)[:16]))
            for root in roots:
                artifacts._check_ancestors(root)
                if root.is_dir():
                    unknown.extend({"path": str(child), "project_root": str(owner), "action": "needs-review"} for child in root.iterdir() if str(child) not in known)
        except (OSError, ValueError, KeyError) as error:
            errors.append({"path": str(record_path), "reason": str(error)})
    return {"registered": records, "unclassified": unknown, "violations": violations, "remote_review": list(remote_review.values()), "errors": errors}


def _remote_owner_review(cache, project):
    """Inventory direct remote names without inferring ownership or deletion consent."""
    if not cache.exists() and not cache.is_symlink():
        return []
    artifacts._check_ancestors(cache)
    return [{"path": str(child), "project_root": str(project), "action": "needs-owner-review", "reason": "remote-* supplies no durable owner or synchronization proof; verify native references and retire consumed test payloads"} for child in sorted(cache.iterdir()) if child.name.startswith("remote-") and child.name != REGISTRY]


def _cache_violations(cache, project):
    artifacts._check_ancestors(cache)
    return [{"path": str(child), "project_root": str(project), "action": "needs-review", "reason": "project Cache permits only temp-* or remote-* child directories"} for child in cache.iterdir() if child.is_symlink() or not child.is_dir() or not child.name.startswith(("temp-", "remote-"))]


def discover(search_roots, *, project_root, artifact_root=None, apply=False, limit=100000):
    """One bounded inventory; later checkpoints use the registry, not whole disk."""
    found = []
    violations = []
    remote_review = []
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
                        remote_review.extend(_remote_owner_review(current, owner))
                        if apply:
                            register_project(owner, artifact_root=base, cache_roots=[current])
                    continue
                pending.extend(child for child in current.iterdir() if child.name not in {".git", "node_modules", REGISTRY, ".codex", ".agents"} and child.is_dir() and not child.is_symlink())
            except (OSError, ValueError) as error:
                errors.append({"path": str(current), "reason": str(error)})
    return {"cache_roots": found, "unclassified_cache_roots": unclassified, "violations": violations, "remote_review": remote_review, "errors": errors, "visited": count, "limit_reached": count >= limit}


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
    parser.add_argument("--reason", help="Audited disposal/release evidence, or concrete current retention/recovery need")
    parser.add_argument("--phase", choices=("start", "transition", "finish"), default="start")
    parser.add_argument("--current-run", type=Path)
    parser.add_argument("--obsolete-run", type=Path, action="append", default=[])
    parser.add_argument("--search-root", type=Path, action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--requested-only", action="store_true", help="Close only explicit finished/obsolete runs, for nested owners and test fixtures")
    parser.add_argument("--budget-seconds", type=float, default=30)
    args = parser.parse_args()
    try:
        if args.requested_only and args.command != "checkpoint":
            raise ValueError("--requested-only applies only to checkpoint")
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
            result = touch_run(args.project_root, args.task_id, args.run_root, artifact_root=args.artifact_root, state=args.state, reason=args.reason)
        elif args.command == "release-retention":
            if not args.run_id or args.identity is None:
                raise ValueError("retention release requires --run-id and --identity")
            result = release_retention(args.project_root, args.task_id, args.run_root, run_id=args.run_id,
                                       expected_identity=args.identity, reason=args.reason,
                                       artifact_root=args.artifact_root, budget_seconds=args.budget_seconds)
        else:
            result = checkpoint(args.project_root, args.task_id, artifact_root=args.artifact_root, phase=args.phase, current_run=args.current_run, obsolete_runs=args.obsolete_run, apply=args.apply, budget_seconds=args.budget_seconds, requested_only=args.requested_only)
        print(json.dumps(result, sort_keys=True))
        return 2 if any(item.get("action") == "pending" for item in result.get("results", [])) else 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "error", "reason": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

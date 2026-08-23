#!/usr/bin/env python3
"""Track and safely release exact resources created by one task.

The ledger deliberately has no process-control or Codex task-control capability.
Runtime resources are closed by their owning tool and are marked released only
after a structured, identity-bound receipt is supplied.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator


SCHEMA_VERSION = 2
MARKER_NAME = ".codex-task-resource-owner.json"
LEDGER_NAME = ".codex-task-resource-ledger.json"
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
HASH_KEY_RE = re.compile(r"^[0-9a-f]{24}$")
DATE_RE = re.compile(r"^[0-9]{8}$")
MAX_MANIFEST_ENTRIES = 4096
RUNTIME_KINDS = {"process", "server", "browser_tab", "app_window", "software_instance"}
FORBIDDEN_RUNTIME_KINDS = {"task", "thread", "session", "ending", "codex_task", "codex_thread"}
ACTIVE_STATES = {
    "acquired",
    "cleanup_ready",
    "cleanup_in_progress",
    "cleanup_failed",
    "deferred_conflict",
}
FINAL_STATES = {"released", "released_external", "retained", "preexisting"}
ALL_STATES = ACTIVE_STATES | FINAL_STATES
PersistCallback = Callable[[dict[str, Any]], None]


def _fail(message: str) -> None:
    raise ValueError(message)


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{name} is required")
    if any(ord(character) < 32 for character in value):
        _fail(f"{name} contains control characters")
    return value


def _identifier(value: Any, name: str) -> str:
    value = _require_text(value, name)
    if not IDENTIFIER_RE.fullmatch(value):
        _fail(f"{name} must use letters, digits, dot, underscore, or hyphen")
    return value


def _digest(value: Any, name: str) -> str:
    value = _require_text(value, name).lower()
    if not DIGEST_RE.fullmatch(value):
        _fail(f"{name} must be a lowercase SHA-256 digest")
    return value


def _task_key(task_id: str) -> str:
    task_id = _require_text(task_id, "task_id")
    return hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:24]


def _identity_digest(identity: dict[str, Any]) -> str:
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_digest(entries: list[dict[str, Any]]) -> str:
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _relative_path(value: Any) -> str:
    value = _require_text(value, "path")
    if value != value.strip() or "\\" in value or ":" in value or value.startswith("/"):
        _fail("path must be a normalized POSIX project-relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail("path must not contain empty, dot, or parent segments")
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != value:
        _fail("path must already be normalized")
    return normalized


def _task_root_path(value: Any) -> str:
    value = _relative_path(value)
    parts = value.split("/")
    if len(parts) != 2 or parts[0] != "Cache" or not parts[1].startswith("tmp-"):
        _fail("task_root must be one exact Cache/tmp-<name> directory")
    suffix = parts[1][4:]
    if not suffix or not IDENTIFIER_RE.fullmatch(suffix):
        _fail("task_root tmp name must be non-empty and portable")
    return value


def _disposable_path(value: Any, task_root: str) -> str:
    value = _relative_path(value)
    root_parts = PurePosixPath(task_root).parts
    value_parts = PurePosixPath(value).parts
    if len(value_parts) <= len(root_parts) or value_parts[: len(root_parts)] != root_parts:
        _fail("disposable path must be strictly below this ledger's exact task_root")
    return value


def _retained_path(value: Any) -> tuple[str, str]:
    value = _relative_path(value)
    parts = PurePosixPath(value).parts
    if len(parts) < 2 or parts[0] != "Cache":
        _fail("retained task artifacts must remain below project Cache")
    category = parts[1]
    if category == "remote-test" or category.startswith("remote-"):
        return value, "remote"
    if DATE_RE.fullmatch(category):
        try:
            datetime.strptime(category, "%Y%m%d")
        except ValueError as error:
            raise ValueError("date retention folder must be a real YYYYMMDD date") from error
        return value, "dated"
    _fail("retained path must be below Cache/remote-*, Cache/remote-test, or Cache/YYYYMMDD")


def _canonical_root(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        _fail("project_root must be an existing directory")
    return root


def _fingerprint(root: Path) -> str:
    return hashlib.sha256(os.fsencode(str(root))).hexdigest()


def _is_reparse(stat_result: os.stat_result) -> bool:
    attributes = getattr(stat_result, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _safe_lstat(path: Path, *, directory: bool | None = None) -> os.stat_result:
    result = path.lstat()
    if stat.S_ISLNK(result.st_mode) or _is_reparse(result):
        _fail("symlink and reparse-point resources are never auto-cleaned")
    if directory is True and not stat.S_ISDIR(result.st_mode):
        _fail("expected an exact directory")
    if directory is False and stat.S_ISDIR(result.st_mode):
        _fail("expected a non-directory")
    return result


def _tree_manifest(path: Path, expected_device: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def visit(current: Path, relative: str) -> None:
        observed = _safe_lstat(current)
        if int(observed.st_dev) != expected_device:
            _fail("resource crosses a filesystem or mount boundary")
        entry = {
            "relative": relative,
            "device": int(observed.st_dev),
            "inode": int(observed.st_ino),
            "mode": int(stat.S_IFMT(observed.st_mode)),
        }
        if not stat.S_ISDIR(observed.st_mode):
            entry["size"] = int(observed.st_size)
            entry["mtime_ns"] = int(observed.st_mtime_ns)
        entries.append(entry)
        if len(entries) > MAX_MANIFEST_ENTRIES:
            _fail("resource manifest exceeds the bounded cleanup limit")
        if stat.S_ISDIR(observed.st_mode):
            with os.scandir(current) as directory_entries:
                child_names = sorted(item.name for item in directory_entries)
            for child_name in child_names:
                child_relative = child_name if relative == "." else f"{relative}/{child_name}"
                visit(current / child_name, child_relative)

    visit(path, ".")
    return entries


def _stat_identity(result: os.stat_result) -> dict[str, int]:
    identity = {
        "device": int(result.st_dev),
        "inode": int(result.st_ino),
        "mode": int(stat.S_IFMT(result.st_mode)),
        "ctime_ns": int(result.st_ctime_ns),
    }
    if not stat.S_ISDIR(result.st_mode):
        identity["size"] = int(result.st_size)
        identity["mtime_ns"] = int(result.st_mtime_ns)
    return identity


def _same_identity(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return all(observed.get(key) == value for key, value in expected.items())


def _same_object_identity(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return all(observed.get(key) == expected.get(key) for key in ("device", "inode", "mode"))


def _absolute(root: Path, relative_path: str) -> Path:
    return root.joinpath(*PurePosixPath(relative_path).parts)


def _audit(ledger: dict[str, Any], action: str, resource_id: str | None, state: str, reason: str) -> None:
    ledger["audit"].append(
        {
            "sequence": ledger["next_sequence"],
            "action": action,
            "resource_id": resource_id,
            "state": state,
            "reason": _require_text(reason, "audit reason"),
        }
    )
    ledger["next_sequence"] += 1


def _binding_identity(path: Path) -> dict[str, int]:
    observed = _safe_lstat(path, directory=True)
    if int(observed.st_ino) <= 0:
        _fail("filesystem does not expose a stable task-root file identity")
    return {
        "device": int(observed.st_dev),
        "inode": int(observed.st_ino),
        "mode": int(stat.S_IFMT(observed.st_mode)),
    }


def _marker_payload(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ledger_id": ledger["ledger_id"],
        "owner_task_key": ledger["owner_task_key"],
        "task_root_identity": ledger["binding"]["task_root_identity"],
    }


def new_ledger(
    project_root: str | Path,
    task_id: str,
    task_root: str,
    *,
    role: str = "producer",
) -> dict[str, Any]:
    """Create an exclusive task root and return its bound in-memory ledger."""
    if role not in {"producer", "ending"}:
        _fail("role must be producer or ending")
    task_root = _task_root_path(task_root)
    root = _canonical_root(project_root)
    cache_root = root / "Cache"
    if cache_root.exists() or cache_root.is_symlink():
        _safe_lstat(cache_root, directory=True)
    else:
        cache_root.mkdir()
    task_root_absolute = _absolute(root, task_root)
    task_root_absolute.mkdir(exist_ok=False)
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "ledger_id": uuid.uuid4().hex,
        "owner_task_key": _task_key(task_id),
        "owner_role": role,
        "task_root": task_root,
        "binding": {
            "project_fingerprint": _fingerprint(root),
            "cache_root_identity": _binding_identity(cache_root),
            "task_root_identity": _binding_identity(task_root_absolute),
        },
        "ending_evidence": {},
        "next_sequence": 1,
        "resources": [],
        "audit": [],
    }
    marker = task_root_absolute / MARKER_NAME
    with marker.open("x", encoding="utf-8") as marker_file:
        json.dump(_marker_payload(ledger), marker_file, sort_keys=True)
        marker_file.write("\n")
        marker_file.flush()
        os.fsync(marker_file.fileno())
    _audit(ledger, "init", None, "acquired", "exclusive task resource root created")
    return validate_ledger(ledger)


def validate_ledger(ledger: Any) -> dict[str, Any]:
    if not isinstance(ledger, dict) or ledger.get("schema_version") != SCHEMA_VERSION:
        _fail("unsupported task resource ledger")
    if not isinstance(ledger.get("ledger_id"), str) or not re.fullmatch(r"[0-9a-f]{32}", ledger["ledger_id"]):
        _fail("ledger_id is invalid")
    if not isinstance(ledger.get("owner_task_key"), str) or not HASH_KEY_RE.fullmatch(ledger["owner_task_key"]):
        _fail("owner_task_key is invalid")
    if ledger.get("owner_role") not in {"producer", "ending"}:
        _fail("owner_role is invalid")
    _task_root_path(ledger.get("task_root"))
    binding = ledger.get("binding")
    if not isinstance(binding, dict) or not DIGEST_RE.fullmatch(str(binding.get("project_fingerprint", ""))):
        _fail("project binding is invalid")
    for identity_name in ("cache_root_identity", "task_root_identity"):
        identity = binding.get(identity_name)
        if not isinstance(identity, dict) or not {"device", "inode", "mode"}.issubset(identity):
            _fail(f"{identity_name} is invalid")
    if not isinstance(ledger.get("resources"), list) or not isinstance(ledger.get("audit"), list):
        _fail("ledger resources and audit must be lists")
    if not isinstance(ledger.get("ending_evidence"), dict):
        _fail("ending_evidence must be an object")
    for task_key, digest in ledger["ending_evidence"].items():
        if not HASH_KEY_RE.fullmatch(str(task_key)) or not DIGEST_RE.fullmatch(str(digest)):
            _fail("ending evidence entry is invalid")
    resource_ids: set[str] = set()
    acquisition_sequences: set[int] = set()
    for resource in ledger["resources"]:
        if not isinstance(resource, dict):
            _fail("resource entry must be an object")
        resource_id = _identifier(resource.get("id"), "resource id")
        if resource_id in resource_ids:
            _fail("resource ids must be unique")
        resource_ids.add(resource_id)
        if resource.get("kind") not in ({"path"} | RUNTIME_KINDS):
            _fail("resource kind is invalid")
        if resource.get("state") not in ALL_STATES:
            _fail("resource state is invalid")
        if resource.get("owner_task_key") != ledger["owner_task_key"]:
            _fail("resource owner does not match ledger owner")
        sequence = resource.get("acquisition_sequence")
        if not isinstance(sequence, int) or sequence < 1 or sequence in acquisition_sequences:
            _fail("resource acquisition sequence is invalid")
        acquisition_sequences.add(sequence)
        _identifier(resource.get("scope"), "scope")
        consumers = resource.get("consumers")
        if not isinstance(consumers, dict) or not consumers:
            _fail("resource consumers must be a non-empty object")
        for task_key, consumer in consumers.items():
            if not HASH_KEY_RE.fullmatch(str(task_key)) or not isinstance(consumer, dict):
                _fail("consumer entry is invalid")
            if consumer.get("role") not in {"producer", "downstream", "ending"}:
                _fail("consumer role is invalid")
            readback = consumer.get("readback_digest")
            if readback is not None and not DIGEST_RE.fullmatch(str(readback)):
                _fail("consumer readback digest is invalid")
        durable = resource.get("durable_result_digest")
        if durable is not None and not DIGEST_RE.fullmatch(str(durable)):
            _fail("durable result digest is invalid")
        if resource["kind"] == "path":
            _relative_path(resource.get("path"))
            if resource.get("disposable"):
                _disposable_path(resource["path"], ledger["task_root"])
                manifest_digest = resource.get("manifest_digest")
                if manifest_digest is not None and not DIGEST_RE.fullmatch(str(manifest_digest)):
                    _fail("path manifest digest is invalid")
        else:
            _validate_runtime_identity(resource["kind"], resource.get("identity"), ledger["owner_task_key"])
            release_token = resource.get("release_token")
            if release_token is not None and not re.fullmatch(r"[0-9a-f]{32}", str(release_token)):
                _fail("runtime release token is invalid")
    expected_sequences = list(range(1, len(ledger["audit"]) + 1))
    observed_sequences = [entry.get("sequence") for entry in ledger["audit"] if isinstance(entry, dict)]
    if observed_sequences != expected_sequences or ledger.get("next_sequence") != len(ledger["audit"]) + 1:
        _fail("audit sequence is not contiguous")
    return ledger


def _verify_binding(ledger: dict[str, Any], project_root: str | Path) -> Path:
    validate_ledger(ledger)
    root = _canonical_root(project_root)
    if _fingerprint(root) != ledger["binding"]["project_fingerprint"]:
        _fail("ledger is bound to a different project root")
    cache_root = root / "Cache"
    task_root = _absolute(root, ledger["task_root"])
    if not _same_identity(ledger["binding"]["cache_root_identity"], _binding_identity(cache_root)):
        _fail("Cache root identity changed")
    if not _same_identity(ledger["binding"]["task_root_identity"], _binding_identity(task_root)):
        _fail("task root identity changed")
    marker = task_root / MARKER_NAME
    marker_stat = _safe_lstat(marker, directory=False)
    if not stat.S_ISREG(marker_stat.st_mode) or marker_stat.st_nlink != 1:
        _fail("task ownership marker is not one exact regular file")
    observed_marker = json.loads(marker.read_text(encoding="utf-8"))
    if observed_marker != _marker_payload(ledger):
        _fail("task ownership marker does not match ledger")
    return root


def _resource(ledger: dict[str, Any], resource_id: str) -> dict[str, Any]:
    resource_id = _identifier(resource_id, "resource id")
    for resource in validate_ledger(ledger)["resources"]:
        if resource["id"] == resource_id:
            return resource
    _fail("unknown resource")


def _new_resource(
    ledger: dict[str, Any], resource_id: str, kind: str, purpose: str, scope: str
) -> dict[str, Any]:
    validate_ledger(ledger)
    resource_id = _identifier(resource_id, "resource id")
    scope = _identifier(scope, "scope")
    purpose = _require_text(purpose, "purpose")
    if any(resource["id"] == resource_id for resource in ledger["resources"]):
        _fail("resource already exists")
    resource = {
        "id": resource_id,
        "kind": kind,
        "purpose": purpose,
        "scope": scope,
        "owner_task_key": ledger["owner_task_key"],
        "state": "acquired",
        "acquisition_sequence": ledger["next_sequence"],
        "durable_result_digest": None,
        "consumers": {
            ledger["owner_task_key"]: {"role": ledger["owner_role"], "readback_digest": None}
        },
    }
    ledger["resources"].append(resource)
    return resource


def _verify_ancestors(
    ledger: dict[str, Any], root: Path, relative_path: str, *, include_target: bool
) -> os.stat_result | None:
    task_root = _absolute(root, ledger["task_root"])
    root_identity = ledger["binding"]["task_root_identity"]
    if not _same_identity(root_identity, _binding_identity(task_root)):
        _fail("task root identity changed")
    target = _absolute(root, relative_path)
    relative_to_task = PurePosixPath(relative_path).relative_to(PurePosixPath(ledger["task_root"]))
    current = task_root
    parts = relative_to_task.parts if include_target else relative_to_task.parts[:-1]
    observed: os.stat_result | None = None
    for part in parts:
        current = current / part
        observed = _safe_lstat(current)
        if int(observed.st_dev) != int(root_identity["device"]):
            _fail("resource crosses a filesystem or mount boundary")
        if current != target and not stat.S_ISDIR(observed.st_mode):
            _fail("resource ancestor must be a directory")
    if include_target and not parts:
        observed = _safe_lstat(target)
    return observed


def acquire_path(
    ledger: dict[str, Any],
    project_root: str | Path,
    resource_id: str,
    path: str,
    purpose: str,
    *,
    scope: str = "main",
) -> dict[str, Any]:
    root = _verify_binding(ledger, project_root)
    path = _disposable_path(path, ledger["task_root"])
    target = _absolute(root, path)
    if target.exists() or target.is_symlink():
        _fail("disposable resource must be absent before this task acquires it")
    path_parts = PurePosixPath(path).parts
    for existing in ledger["resources"]:
        if existing.get("kind") != "path" or not existing.get("disposable"):
            continue
        existing_parts = PurePosixPath(existing["path"]).parts
        if path_parts[: len(existing_parts)] == existing_parts or existing_parts[: len(path_parts)] == path_parts:
            _fail("disposable resource paths must not overlap")
    _verify_ancestors(ledger, root, path, include_target=False)
    resource = _new_resource(ledger, resource_id, "path", purpose, scope)
    resource.update({"path": path, "disposable": True, "identity": None, "quarantine": None})
    _audit(ledger, "acquire_path", resource["id"], "acquired", "exact absent task path reserved")
    return resource


def record_retained_path(
    ledger: dict[str, Any],
    resource_id: str,
    path: str,
    purpose: str,
    reason: str,
    next_review: str,
    *,
    authorized_by_user: bool = False,
    authorized_by_contract: bool = False,
    scope: str = "main",
) -> dict[str, Any]:
    path, category = _retained_path(path)
    reason = _require_text(reason, "retention reason")
    next_review = _require_text(next_review, "next review")
    if category == "remote" and not (authorized_by_user or authorized_by_contract):
        _fail("remote retention requires explicit user or project-contract authorization")
    resource = _new_resource(ledger, resource_id, "path", purpose, scope)
    resource.update(
        {
            "path": path,
            "disposable": False,
            "identity": None,
            "state": "retained",
            "retained_reason": reason,
            "next_review": next_review,
            "retention_authority": "user" if authorized_by_user else "project_contract" if authorized_by_contract else "dated_review",
        }
    )
    _audit(ledger, "record_retained", resource["id"], "retained", reason)
    return resource


def record_preexisting_path(
    ledger: dict[str, Any],
    resource_id: str,
    path: str,
    purpose: str,
    *,
    scope: str = "main",
) -> dict[str, Any]:
    path = _relative_path(path)
    resource = _new_resource(ledger, resource_id, "path", purpose, scope)
    resource.update({"path": path, "disposable": False, "identity": None, "state": "preexisting"})
    _audit(ledger, "record_preexisting", resource["id"], "preexisting", "preexisting resource remains untouched")
    return resource


def seal_path(ledger: dict[str, Any], project_root: str | Path, resource_id: str) -> dict[str, Any]:
    root = _verify_binding(ledger, project_root)
    resource = _resource(ledger, resource_id)
    if resource["kind"] != "path" or not resource.get("disposable") or resource["state"] != "acquired":
        _fail("only an acquired disposable path can be sealed")
    if resource.get("identity") is not None:
        _fail("resource path is already sealed")
    observed = _verify_ancestors(ledger, root, resource["path"], include_target=True)
    if observed is None:
        _fail("resource path does not exist")
    resource["identity"] = _stat_identity(observed)
    resource["manifest_digest"] = _manifest_digest(
        _tree_manifest(
            _absolute(root, resource["path"]),
            int(ledger["binding"]["task_root_identity"]["device"]),
        )
    )
    _audit(ledger, "seal_path", resource["id"], "acquired", "exact task-created path identity sealed")
    return resource


def _validate_runtime_identity(kind: str, identity: Any, owner_task_key: str) -> dict[str, Any]:
    if kind in FORBIDDEN_RUNTIME_KINDS or kind not in RUNTIME_KINDS:
        _fail("runtime kind must never represent a Codex task, thread, session, or Ending")
    if not isinstance(identity, dict):
        _fail("runtime identity must be an object")
    required: dict[str, set[str]] = {
        "process": {"pid", "start_time", "executable", "cwd", "created_by_task_key"},
        "server": {"pid", "start_time", "executable", "cwd", "created_by_task_key"},
        "browser_tab": {"context_id", "window_id", "tab_id", "created_by_task_key"},
        "app_window": {"app_id", "process_id", "window_id", "start_time", "created_by_task_key"},
        "software_instance": {"app_id", "process_id", "instance_id", "start_time", "created_by_task_key"},
    }
    if not required[kind].issubset(identity):
        _fail("runtime identity is missing exact typed fields")
    if identity.get("created_by_task_key") != owner_task_key:
        _fail("runtime identity is not owned by this exact task")
    if kind in {"process", "server"} and (not isinstance(identity.get("pid"), int) or identity["pid"] <= 0):
        _fail("process runtime identity requires a positive pid")
    forbidden_keys = {"port", "process_name", "name", "task_id", "thread_id", "session_id", "ending_id"}
    if forbidden_keys.intersection(identity):
        _fail("runtime identity must not rely on names, ports, or Codex lifecycle identifiers")
    for key, value in identity.items():
        if key in {"pid", "process_id"}:
            if not isinstance(value, int) or value <= 0:
                _fail("runtime numeric identities must be positive integers")
        elif not isinstance(value, str) or not value:
            _fail("runtime identity fields must be non-empty strings")
    return identity


def acquire_runtime(
    ledger: dict[str, Any],
    resource_id: str,
    kind: str,
    identity: dict[str, Any],
    purpose: str,
    *,
    scope: str = "main",
) -> dict[str, Any]:
    if kind in FORBIDDEN_RUNTIME_KINDS or kind not in RUNTIME_KINDS:
        _fail("runtime kind must never represent a Codex task, thread, session, or Ending")
    identity = dict(identity)
    identity["created_by_task_key"] = ledger["owner_task_key"]
    _validate_runtime_identity(kind, identity, ledger["owner_task_key"])
    resource = _new_resource(ledger, resource_id, kind, purpose, scope)
    resource.update(
        {
            "identity": identity,
            "identity_digest": _identity_digest(identity),
            "cleanup_strategy": "owner_tool_graceful",
        }
    )
    _audit(ledger, "acquire_runtime", resource["id"], "acquired", "exact task-created runtime handle recorded")
    return resource


def record_durable_readback(ledger: dict[str, Any], resource_id: str, result_digest: str) -> None:
    resource = _resource(ledger, resource_id)
    if resource["state"] != "acquired":
        _fail("only acquired resources accept a durable result barrier")
    resource["durable_result_digest"] = _digest(result_digest, "result digest")
    _audit(ledger, "durable_readback", resource["id"], resource["state"], "durable result readback recorded")


def record_consumer_readback(
    ledger: dict[str, Any], resource_id: str, consumer_task_id: str, readback_digest: str
) -> None:
    resource = _resource(ledger, resource_id)
    if resource["state"] != "acquired":
        _fail("consumer readback must occur before release preparation")
    task_key = _task_key(consumer_task_id)
    if task_key not in resource["consumers"]:
        _fail("consumer is not an explicit owner or handoff")
    if resource["consumers"][task_key]["readback_digest"] is not None:
        _fail("consumer readback is single-use and cannot be replayed")
    resource["consumers"][task_key]["readback_digest"] = _digest(readback_digest, "readback digest")
    _audit(ledger, "consumer_readback", resource["id"], resource["state"], "exact consumer readback recorded")


def handoff(
    ledger: dict[str, Any],
    resource_id: str,
    downstream_task_id: str,
    *,
    role: str = "downstream",
) -> None:
    resource = _resource(ledger, resource_id)
    if resource["state"] != "acquired" or (resource["kind"] == "path" and resource.get("identity") is not None):
        _fail("handoff must be explicit before a path is sealed or release begins")
    if role not in {"downstream", "ending"}:
        _fail("handoff role must be downstream or ending")
    task_key = _task_key(downstream_task_id)
    if task_key in resource["consumers"]:
        _fail("duplicate consumer handoff is forbidden")
    resource["consumers"][task_key] = {"role": role, "readback_digest": None}
    _audit(ledger, "handoff", resource["id"], "acquired", f"explicit {role} consumer added")


def record_evidence_persisted(ledger: dict[str, Any], ending_task_id: str, evidence_digest: str) -> None:
    task_key = _task_key(ending_task_id)
    ending_keys = {
        consumer_key
        for resource in ledger["resources"]
        for consumer_key, consumer in resource["consumers"].items()
        if consumer.get("role") == "ending"
    }
    if ledger["owner_role"] == "ending":
        ending_keys.add(ledger["owner_task_key"])
    if task_key not in ending_keys:
        _fail("evidence receipt must belong to this ledger's exact Ending consumer")
    ledger["ending_evidence"][task_key] = _digest(evidence_digest, "evidence digest")
    _audit(ledger, "evidence_persisted", None, "acquired", "Ending evidence and terminal record persisted")


def _release_barriers(ledger: dict[str, Any], resource: dict[str, Any]) -> None:
    if not resource.get("durable_result_digest"):
        _fail("release requires durable result readback")
    incomplete = [consumer for consumer in resource["consumers"].values() if not consumer.get("readback_digest")]
    if incomplete:
        _fail("release requires every explicit consumer readback")
    ending_keys = [
        task_key for task_key, consumer in resource["consumers"].items() if consumer.get("role") == "ending"
    ]
    if ledger["owner_role"] == "ending" and ledger["owner_task_key"] not in ending_keys:
        ending_keys.append(ledger["owner_task_key"])
    if any(task_key not in ledger["ending_evidence"] for task_key in ending_keys):
        _fail("Ending must persist evidence and its terminal record before release")


def _enforce_scope_lifo(ledger: dict[str, Any], resource: dict[str, Any]) -> None:
    later = [
        item
        for item in ledger["resources"]
        if item["scope"] == resource["scope"]
        and item["acquisition_sequence"] > resource["acquisition_sequence"]
        and item["state"] in ACTIVE_STATES
    ]
    if later:
        _fail("active resources in the same scope must release in reverse acquisition order")


def prepare_release(ledger: dict[str, Any], resource_id: str) -> bool:
    resource = _resource(ledger, resource_id)
    if resource["state"] in {"released", "released_external"}:
        _audit(ledger, "prepare_release_idempotent", resource["id"], resource["state"], "resource already absent")
        return False
    if resource["state"] in {"retained", "preexisting", "deferred_conflict"}:
        _fail(f"{resource['state']} resource remains untouched")
    if resource["state"] not in {"acquired", "cleanup_failed", "cleanup_ready"}:
        _fail("resource is not ready for release preparation")
    _enforce_scope_lifo(ledger, resource)
    _release_barriers(ledger, resource)
    if resource["kind"] == "path" and resource.get("identity") is None:
        _fail("path release requires a sealed exact identity")
    resource["state"] = "cleanup_ready"
    if resource["kind"] in RUNTIME_KINDS:
        resource["release_token"] = uuid.uuid4().hex
    _audit(ledger, "prepare_release", resource["id"], "cleanup_ready", "all release barriers passed")
    return True


def defer_conflict(ledger: dict[str, Any], resource_id: str, reason: str, observation_digest: str) -> None:
    resource = _resource(ledger, resource_id)
    if resource["state"] not in {"acquired", "cleanup_ready", "cleanup_in_progress", "cleanup_failed"}:
        _fail("only an active resource can defer a conflict")
    resource["deferred_from_state"] = resource["state"]
    resource["state"] = "deferred_conflict"
    resource["conflict_reason"] = _require_text(reason, "conflict reason")
    resource["conflict_observation_digest"] = _digest(observation_digest, "observation digest")
    _audit(ledger, "defer_conflict", resource["id"], "deferred_conflict", reason)


def resolve_conflict(
    ledger: dict[str, Any],
    project_root: str | Path,
    resource_id: str,
    resolution: str,
    revalidation_digest: str,
) -> None:
    root = _verify_binding(ledger, project_root)
    resource = _resource(ledger, resource_id)
    if resource["state"] != "deferred_conflict":
        _fail("resource has no deferred conflict")
    _digest(revalidation_digest, "revalidation digest")
    target = _absolute(root, resource["path"]) if resource["kind"] == "path" else None
    if resolution == "released_external":
        if target is not None and (target.exists() or target.is_symlink()):
            _fail("released_external requires the exact path to be absent")
        resource["state"] = "released_external"
        _audit(ledger, "resolve_conflict", resource["id"], "released_external", "exact resource was released externally")
        return
    if resolution != "resume":
        _fail("conflict resolution must be resume or released_external")
    if resource["kind"] == "path" and resource.get("identity") is not None:
        observed = _verify_ancestors(ledger, root, resource["path"], include_target=True)
        manifest_matches = False
        if observed is not None and _same_identity(resource["identity"], _stat_identity(observed)):
            try:
                manifest_matches = resource.get("manifest_digest") == _manifest_digest(
                    _tree_manifest(target, int(ledger["binding"]["task_root_identity"]["device"]))
                )
            except ValueError:
                manifest_matches = False
        if not manifest_matches:
            _fail("path identity changed; conflict remains deferred")
    prior = resource.get("deferred_from_state", "acquired")
    resource["state"] = "cleanup_ready" if prior in {"cleanup_ready", "cleanup_failed"} else "acquired"
    for key in ("deferred_from_state", "conflict_reason", "conflict_observation_digest"):
        resource.pop(key, None)
    _audit(ledger, "resolve_conflict", resource["id"], resource["state"], "conflict revalidated for explicit resume")


def _persist(ledger: dict[str, Any], callback: PersistCallback | None) -> None:
    if callback is not None:
        callback(validate_ledger(ledger))


def _safe_remove_tree(path: Path, expected_device: int) -> None:
    observed = path.lstat()
    if int(observed.st_dev) != expected_device:
        _fail("cleanup crossed a filesystem boundary")
    if stat.S_ISLNK(observed.st_mode) or _is_reparse(observed):
        path.unlink()
        return
    if stat.S_ISDIR(observed.st_mode):
        with os.scandir(path) as entries:
            children = [Path(entry.path) for entry in entries]
        for child in children:
            _safe_remove_tree(child, expected_device)
        path.rmdir()
        return
    path.unlink()


def cleanup_path(
    ledger: dict[str, Any],
    project_root: str | Path,
    resource_id: str,
    *,
    persist_callback: PersistCallback | None = None,
) -> bool:
    root = _verify_binding(ledger, project_root)
    resource = _resource(ledger, resource_id)
    if resource["kind"] != "path" or not resource.get("disposable"):
        _fail("only exact disposable paths can be cleaned")
    if resource["state"] in {"released", "released_external"}:
        _audit(ledger, "cleanup_idempotent", resource["id"], resource["state"], "resource already absent")
        _persist(ledger, persist_callback)
        return False
    if resource["state"] not in {"cleanup_ready", "cleanup_in_progress", "cleanup_failed"}:
        _fail("path must pass release preparation before cleanup")
    target = _absolute(root, resource["path"])
    quarantine_name = f".codex-resource-{ledger['ledger_id'][:12]}-{hashlib.sha256(resource['id'].encode()).hexdigest()[:12]}"
    quarantine_relative = f"{ledger['task_root']}/{quarantine_name}"
    quarantine = _absolute(root, quarantine_relative)
    if resource["state"] in {"cleanup_ready", "cleanup_failed"}:
        if not target.exists() and not target.is_symlink():
            resource["state"] = "released_external"
            _audit(ledger, "cleanup_external_absence", resource["id"], "released_external", "exact path was already absent")
            _persist(ledger, persist_callback)
            return False
        observed = _verify_ancestors(ledger, root, resource["path"], include_target=True)
        manifest_matches = False
        if observed is not None and _same_identity(resource["identity"], _stat_identity(observed)):
            try:
                manifest_matches = resource.get("manifest_digest") == _manifest_digest(
                    _tree_manifest(target, int(ledger["binding"]["task_root_identity"]["device"]))
                )
            except ValueError:
                manifest_matches = False
        if not manifest_matches:
            defer_conflict(
                ledger,
                resource["id"],
                "exact path identity changed before cleanup",
                hashlib.sha256(b"path-identity-changed").hexdigest(),
            )
            _persist(ledger, persist_callback)
            return False
        if quarantine.exists() or quarantine.is_symlink():
            _fail("cleanup quarantine already exists; leave both paths untouched")
        resource["state"] = "cleanup_in_progress"
        resource["quarantine"] = quarantine_relative
        _audit(ledger, "cleanup_begin", resource["id"], "cleanup_in_progress", "exact path entered same-root quarantine")
        _persist(ledger, persist_callback)
        os.rename(target, quarantine)
    try:
        quarantine_stat = _safe_lstat(quarantine)
        quarantine_identity = _stat_identity(quarantine_stat)
        quarantine_manifest_matches = False
        if _same_object_identity(resource["identity"], quarantine_identity):
            try:
                quarantine_manifest_matches = resource.get("manifest_digest") == _manifest_digest(
                    _tree_manifest(quarantine, int(ledger["binding"]["task_root_identity"]["device"]))
                )
            except ValueError:
                quarantine_manifest_matches = False
        if not quarantine_manifest_matches:
            if not target.exists() and not target.is_symlink():
                os.rename(quarantine, target)
            defer_conflict(
                ledger,
                resource["id"],
                "quarantined path identity did not match sealed identity",
                hashlib.sha256(b"quarantine-identity-changed").hexdigest(),
            )
            _persist(ledger, persist_callback)
            return False
        _safe_remove_tree(quarantine, int(ledger["binding"]["task_root_identity"]["device"]))
    except Exception:
        resource["state"] = "cleanup_failed"
        _audit(ledger, "cleanup_failed", resource["id"], "cleanup_failed", "exact cleanup failed and requires explicit retry")
        _persist(ledger, persist_callback)
        raise
    resource["state"] = "released"
    resource["quarantine"] = None
    _audit(ledger, "cleanup_complete", resource["id"], "released", "exact task-owned path removed")
    _persist(ledger, persist_callback)
    return True


def confirm_runtime_release(ledger: dict[str, Any], resource_id: str, receipt: dict[str, Any]) -> bool:
    resource = _resource(ledger, resource_id)
    if resource["kind"] not in RUNTIME_KINDS:
        _fail("resource is not a runtime handle")
    if resource["state"] == "released":
        _audit(ledger, "runtime_release_idempotent", resource["id"], "released", "runtime already released")
        return False
    if resource["state"] != "cleanup_ready":
        _fail("runtime must pass release preparation before confirmation")
    if not isinstance(receipt, dict):
        _fail("owner-tool receipt must be an object")
    expected = {
        "ledger_id": ledger["ledger_id"],
        "resource_id": resource["id"],
        "identity_digest": resource["identity_digest"],
        "kind": resource["kind"],
        "release_token": resource["release_token"],
        "method": "graceful",
        "outcome": "PASS",
        "observed": "exact_handle_absent",
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        _fail("owner-tool receipt does not prove exact graceful release")
    owner_tool = _require_text(receipt.get("owner_tool"), "owner_tool")
    lowered = owner_tool.lower()
    if any(token in lowered for token in ("killall", "pkill", "task manager", "thread manager", "session manager")):
        _fail("owner-tool receipt names a forbidden broad cleanup mechanism")
    resource["state"] = "released"
    resource["release_receipt_digest"] = _identity_digest(receipt)
    _audit(ledger, "runtime_release_confirmed", resource["id"], "released", "owner tool confirmed exact handle absent")
    return True


@contextlib.contextmanager
def ledger_lock(path: str | Path) -> Iterator[None]:
    ledger_path = Path(path)
    lock_path = ledger_path.with_name(f"{ledger_path.name}.lock")
    descriptor: int | None = None
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.fsync(descriptor)
        yield
    except FileExistsError as error:
        raise RuntimeError("ledger is locked; do not remove the lock or guess ownership") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def load_ledger(path: str | Path) -> dict[str, Any]:
    return validate_ledger(json.loads(Path(path).read_text(encoding="utf-8")))


def save_ledger(path: str | Path, ledger: dict[str, Any], *, assume_locked: bool = False) -> None:
    ledger = validate_ledger(ledger)
    destination = Path(path)

    def write() -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")
        try:
            with temporary.open("x", encoding="utf-8") as output:
                json.dump(ledger, output, indent=2, sort_keys=True)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, destination)
            try:
                parent_descriptor = os.open(destination.parent, os.O_RDONLY)
            except OSError:
                parent_descriptor = None
            if parent_descriptor is not None:
                try:
                    os.fsync(parent_descriptor)
                finally:
                    os.close(parent_descriptor)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    if assume_locked:
        write()
    else:
        with ledger_lock(destination):
            write()


def _assert_ledger_location(project_root: str | Path, ledger_path: Path, ledger: dict[str, Any]) -> None:
    root = _verify_binding(ledger, project_root)
    expected = _absolute(root, ledger["task_root"]) / LEDGER_NAME
    if ledger_path.expanduser().resolve(strict=False) != expected:
        _fail(f"ledger file must use {LEDGER_NAME} inside its exact task root")


def _summary(ledger: dict[str, Any]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for resource in ledger["resources"]:
        state_counts[resource["state"]] = state_counts.get(resource["state"], 0) + 1
        kind_counts[resource["kind"]] = kind_counts.get(resource["kind"], 0) + 1
    return {
        "status": "ok",
        "schema_version": ledger["schema_version"],
        "owner_role": ledger["owner_role"],
        "resource_count": len(ledger["resources"]),
        "states": state_counts,
        "kinds": kind_counts,
        "audit_events": len(ledger["audit"]),
    }


def _json_argument(value: str, name: str) -> dict[str, Any]:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"{name} must be valid JSON") from error
    if not isinstance(result, dict):
        _fail(f"{name} must be a JSON object")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track exact task-owned resource lifecycles.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("ledger", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--task-id", required=True)
    init.add_argument("--task-root", required=True)
    init.add_argument("--role", choices=("producer", "ending"), default="producer")

    acquire = subparsers.add_parser("acquire-path")
    acquire.add_argument("--id", required=True)
    acquire.add_argument("--path", required=True)
    acquire.add_argument("--purpose", required=True)
    acquire.add_argument("--scope", default="main")

    seal = subparsers.add_parser("seal-path")
    seal.add_argument("--id", required=True)

    runtime = subparsers.add_parser("acquire-runtime")
    runtime.add_argument("--id", required=True)
    runtime.add_argument("--kind", required=True)
    runtime.add_argument("--identity-json", required=True)
    runtime.add_argument("--purpose", required=True)
    runtime.add_argument("--scope", default="main")

    retained = subparsers.add_parser("record-retained")
    retained.add_argument("--id", required=True)
    retained.add_argument("--path", required=True)
    retained.add_argument("--purpose", required=True)
    retained.add_argument("--reason", required=True)
    retained.add_argument("--next-review", required=True)
    retained.add_argument("--authorized-by-user", action="store_true")
    retained.add_argument("--authorized-by-contract", action="store_true")
    retained.add_argument("--scope", default="main")

    preexisting = subparsers.add_parser("record-preexisting")
    preexisting.add_argument("--id", required=True)
    preexisting.add_argument("--path", required=True)
    preexisting.add_argument("--purpose", required=True)
    preexisting.add_argument("--scope", default="main")

    durable = subparsers.add_parser("durable-readback")
    durable.add_argument("--id", required=True)
    durable.add_argument("--digest", required=True)

    consumer = subparsers.add_parser("consumer-readback")
    consumer.add_argument("--id", required=True)
    consumer.add_argument("--task-id", required=True)
    consumer.add_argument("--digest", required=True)

    handoff_parser = subparsers.add_parser("handoff")
    handoff_parser.add_argument("--id", required=True)
    handoff_parser.add_argument("--task-id", required=True)
    handoff_parser.add_argument("--role", choices=("downstream", "ending"), default="downstream")

    evidence = subparsers.add_parser("evidence-persisted")
    evidence.add_argument("--task-id", required=True)
    evidence.add_argument("--digest", required=True)

    prepare = subparsers.add_parser("prepare-release")
    prepare.add_argument("--id", required=True)

    cleanup = subparsers.add_parser("cleanup-path")
    cleanup.add_argument("--id", required=True)

    confirm = subparsers.add_parser("confirm-runtime-release")
    confirm.add_argument("--id", required=True)
    confirm.add_argument("--receipt-json", required=True)

    defer = subparsers.add_parser("defer-conflict")
    defer.add_argument("--id", required=True)
    defer.add_argument("--reason", required=True)
    defer.add_argument("--observation-digest", required=True)

    resolve = subparsers.add_parser("resolve-conflict")
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--resolution", choices=("resume", "released_external"), required=True)
    resolve.add_argument("--revalidation-digest", required=True)

    subparsers.add_parser("show")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    project_root = Path(args.project_root)
    try:
        if args.command == "init":
            ledger = new_ledger(project_root, args.task_id, args.task_root, role=args.role)
            _assert_ledger_location(project_root, args.ledger, ledger)
            with ledger_lock(args.ledger):
                if args.ledger.exists():
                    _fail("ledger already exists")
                save_ledger(args.ledger, ledger, assume_locked=True)
        else:
            with ledger_lock(args.ledger):
                ledger = load_ledger(args.ledger)
                _assert_ledger_location(project_root, args.ledger, ledger)
                if args.command == "acquire-path":
                    acquire_path(ledger, project_root, args.id, args.path, args.purpose, scope=args.scope)
                elif args.command == "seal-path":
                    seal_path(ledger, project_root, args.id)
                elif args.command == "acquire-runtime":
                    acquire_runtime(ledger, args.id, args.kind, _json_argument(args.identity_json, "identity"), args.purpose, scope=args.scope)
                elif args.command == "record-retained":
                    record_retained_path(
                        ledger,
                        args.id,
                        args.path,
                        args.purpose,
                        args.reason,
                        args.next_review,
                        authorized_by_user=args.authorized_by_user,
                        authorized_by_contract=args.authorized_by_contract,
                        scope=args.scope,
                    )
                elif args.command == "record-preexisting":
                    record_preexisting_path(ledger, args.id, args.path, args.purpose, scope=args.scope)
                elif args.command == "durable-readback":
                    record_durable_readback(ledger, args.id, args.digest)
                elif args.command == "consumer-readback":
                    record_consumer_readback(ledger, args.id, args.task_id, args.digest)
                elif args.command == "handoff":
                    handoff(ledger, args.id, args.task_id, role=args.role)
                elif args.command == "evidence-persisted":
                    record_evidence_persisted(ledger, args.task_id, args.digest)
                elif args.command == "prepare-release":
                    prepare_release(ledger, args.id)
                elif args.command == "cleanup-path":
                    cleanup_path(
                        ledger,
                        project_root,
                        args.id,
                        persist_callback=lambda value: save_ledger(args.ledger, value, assume_locked=True),
                    )
                elif args.command == "confirm-runtime-release":
                    confirm_runtime_release(ledger, args.id, _json_argument(args.receipt_json, "receipt"))
                elif args.command == "defer-conflict":
                    defer_conflict(ledger, args.id, args.reason, args.observation_digest)
                elif args.command == "resolve-conflict":
                    resolve_conflict(ledger, project_root, args.id, args.resolution, args.revalidation_digest)
                elif args.command != "show":
                    _fail("unsupported command")
                if args.command != "show":
                    save_ledger(args.ledger, ledger, assume_locked=True)
        print(json.dumps(_summary(ledger), sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate and aggregate privacy-safe logical plans for parallel child sessions.

This module deliberately has no Codex session-control capability. The root task
uses the collaboration control plane; this module handles boundaries and status
only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
MAX_BRANCHES = 8
BRANCH_STATUSES = {"passed", "working", "failed", "blocked", "cancelled", "skipped"}
CACHE_CLASSES = {"none", "temporary", "dated", "remote"}
FORBIDDEN_ACTIVE_STATUSES = {"working", "failed", "blocked", "cancelled"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DATE_RE = re.compile(r"^[0-9]{8}$")
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")
RAW_CONTROL_IDENTIFIER_RE = re.compile(r"\b(?:session|thread|agent)[_-][A-Za-z0-9_-]{8,}\b", re.IGNORECASE)
ABSOLUTE_PATH_RE = re.compile(r"(?:^|\s)(?:~[/\\]|[/\\](?:Users|home|tmp|var|etc)[/\\]|[A-Za-z]:[/\\]|\\\\)")
SECRET_RE = re.compile(r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:password|access[_-]?token|api[_-]?key|secret)\s*[:=]|\b(?:sk|ghp)_[A-Za-z0-9_-]{12,})", re.IGNORECASE)
FORBIDDEN_FIELD_NAMES = {"id", "session_id", "sessionid", "thread_id", "threadid", "agent_id", "agentid", "prompt", "raw_prompt", "result", "raw_result", "reasoning", "secret", "password", "token", "credential"}


class PlanValidationError(ValueError):
    """A sanitized plan or branch-status contract is invalid."""


def _fail(message: str) -> None:
    raise PlanValidationError(message)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{label} must be an object")
    return value


def _require_exact_keys(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required - optional)
    if missing:
        _fail(f"{label} is missing required fields: {', '.join(missing)}")
    if extra:
        _fail(f"{label} contains unsupported fields: {', '.join(extra)}")


def _sanitized_text(value: Any, label: str, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _fail(f"{label} must be non-empty trimmed text")
    if len(value) > 240 or any(ord(character) < 32 for character in value):
        _fail(f"{label} must be one bounded printable line")
    if EMAIL_RE.search(value) or UUID_RE.search(value) or RAW_CONTROL_IDENTIFIER_RE.search(value):
        _fail(f"{label} must not contain raw personal or session identifiers")
    if ABSOLUTE_PATH_RE.search(value):
        _fail(f"{label} must not contain an absolute path")
    if SECRET_RE.search(value):
        _fail(f"{label} must not contain secret material")
    return value


def _scan_sanitized_structure(value: Any, label: str = "plan") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                _fail(f"{label} field names must be text")
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in FORBIDDEN_FIELD_NAMES or normalized_key.endswith("_id"):
                _fail(f"{label} must not store raw prompts, results, reasoning, secrets, or IDs")
            _scan_sanitized_structure(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_sanitized_structure(child, f"{label}[{index}]")
    elif isinstance(value, str):
        _sanitized_text(value, label)


def _identifier(value: Any, label: str) -> str:
    value = _sanitized_text(value, label)
    if not IDENTIFIER_RE.fullmatch(value):
        _fail(f"{label} must use letters, digits, dot, underscore, or hyphen")
    return value


def _relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 512:
        _fail(f"{label} must be a bounded project-relative path")
    if any(ord(character) < 32 for character in value) or value.startswith(("/", "\\", "~")) or "\\" in value or ":" in value or any(character in value for character in "*?[]"):
        _fail(f"{label} must be a normalized POSIX project-relative path root")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or PurePosixPath(*parts).as_posix() != value:
        _fail(f"{label} must not contain empty, dot, or parent segments")
    return value


def _relative_workdir(value: Any, label: str) -> str:
    if value == ".":
        return value
    return _relative_path(value, label)


def _path_parts(value: str) -> tuple[str, ...]:
    return PurePosixPath(value).parts


def _path_overlap(left: str, right: str) -> bool:
    left_parts = _path_parts(left)
    right_parts = _path_parts(right)
    shared_length = min(len(left_parts), len(right_parts))
    return left_parts[:shared_length] == right_parts[:shared_length]


def _paths_overlap(left_paths: list[str], right_paths: list[str]) -> bool:
    return any(_path_overlap(left, right) for left in left_paths for right in right_paths)


def _path_within(value: str, root: str, strict: bool = False) -> bool:
    value_parts = _path_parts(value)
    root_parts = _path_parts(root)
    if strict and len(value_parts) <= len(root_parts):
        return False
    return len(value_parts) >= len(root_parts) and value_parts[: len(root_parts)] == root_parts


def _path_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        _fail(f"{label} must be a list")
    paths = [_relative_path(path, f"{label} path") for path in value]
    if len(paths) != len(set(paths)):
        _fail(f"{label} must not contain duplicate paths")
    for index, path in enumerate(paths):
        if any(_path_overlap(path, other) for other in paths[index + 1 :]):
            _fail(f"{label} must not contain overlapping path roots")
    return paths


def _identifier_list(value: Any, label: str, require_value: bool = False) -> list[str]:
    if not isinstance(value, list) or require_value and not value:
        _fail(f"{label} must be {'a non-empty list' if require_value else 'a list'}")
    identifiers = [_identifier(item, f"{label} item") for item in value]
    if len(identifiers) != len(set(identifiers)):
        _fail(f"{label} must not contain duplicates")
    return identifiers


def _temporary_root(value: Any) -> str | None:
    if value is None:
        return None
    value = _relative_path(value, "main.temporary_root")
    parts = _path_parts(value)
    if len(parts) != 2 or parts[0] != "Cache" or not parts[1].startswith("tmp-") or not IDENTIFIER_RE.fullmatch(parts[1][4:]):
        _fail("main.temporary_root must be one exact Cache/tmp-<name> directory")
    return value


def _validate_cache(cache_value: Any, branch_name: str, workdir: str, writes: list[str], temporary_root: str | None) -> dict[str, Any]:
    cache = _require_object(cache_value, f"branch {branch_name} cache")
    _require_exact_keys(cache, {"class"}, {"root", "retention_authority", "retention_reason", "review_point"}, f"branch {branch_name} cache")
    cache_class = cache["class"]
    if not isinstance(cache_class, str) or cache_class not in CACHE_CLASSES:
        _fail(f"branch {branch_name} cache class is invalid")
    if cache_class == "none":
        _require_exact_keys(cache, {"class"}, set(), f"branch {branch_name} cache")
        if workdir.startswith("Cache/") or any(path.startswith("Cache/") for path in writes):
            _fail(f"branch {branch_name} Cache writes require a declared cache class")
        return {"class": "none", "root": None}
    cache_root = _relative_path(cache.get("root"), f"branch {branch_name} cache root")
    if cache_root not in writes:
        _fail(f"branch {branch_name} cache root must be an exact write allowlist entry")
    if any(path.startswith("Cache/") and not _path_within(path, cache_root) for path in writes):
        _fail(f"branch {branch_name} Cache writes must stay inside its cache root")
    if workdir.startswith("Cache/") and not _path_within(workdir, cache_root):
        _fail(f"branch {branch_name} Cache workdir must stay inside its cache root")
    if cache_class == "temporary":
        _require_exact_keys(cache, {"class", "root"}, set(), f"branch {branch_name} cache")
        if temporary_root is None or cache_root != f"{temporary_root}/{branch_name}":
            _fail(f"branch {branch_name} temporary cache root must be its direct directory below main.temporary_root")
    elif cache_class == "dated":
        _require_exact_keys(cache, {"class", "root", "retention_reason", "review_point"}, set(), f"branch {branch_name} cache")
        parts = _path_parts(cache_root)
        if len(parts) < 3 or parts[0] != "Cache" or not DATE_RE.fullmatch(parts[1]):
            _fail(f"branch {branch_name} dated cache root must be below Cache/YYYYMMDD")
        try:
            datetime.strptime(parts[1], "%Y%m%d")
        except ValueError as error:
            raise PlanValidationError(f"branch {branch_name} dated cache root uses an invalid date") from error
        _sanitized_text(cache["retention_reason"], f"branch {branch_name} retention_reason")
        _sanitized_text(cache["review_point"], f"branch {branch_name} review_point")
    else:
        _require_exact_keys(cache, {"class", "root", "retention_authority", "retention_reason", "review_point"}, set(), f"branch {branch_name} cache")
        parts = _path_parts(cache_root)
        remote_category_valid = len(parts) >= 2 and parts[0] == "Cache" and (parts[1] == "remote-test" or parts[1].startswith("remote-") and len(parts[1]) > len("remote-"))
        if not remote_category_valid:
            _fail(f"branch {branch_name} remote cache root must be below Cache/remote-* or Cache/remote-test")
        if not isinstance(cache["retention_authority"], str) or cache["retention_authority"] not in {"user", "project_contract"}:
            _fail(f"branch {branch_name} remote cache requires user or project-contract authority")
        _sanitized_text(cache["retention_reason"], f"branch {branch_name} retention_reason")
        _sanitized_text(cache["review_point"], f"branch {branch_name} review_point")
    return {"class": cache_class, "root": cache_root}


def _topological_waves(names: list[str], dependencies: dict[str, set[str]]) -> list[list[str]]:
    settled: set[str] = set()
    remaining = set(names)
    waves: list[list[str]] = []
    while remaining:
        ready = [name for name in names if name in remaining and dependencies[name] <= settled]
        if not ready:
            _fail("branch dependencies contain a cycle")
        waves.append(ready)
        settled.update(ready)
        remaining.difference_update(ready)
    return waves


def _depends_on(branch_name: str, dependency_name: str, dependencies: dict[str, set[str]]) -> bool:
    pending = list(dependencies[branch_name])
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == dependency_name:
            return True
        if current not in visited:
            visited.add(current)
            pending.extend(dependencies[current])
    return False


def _dependency_ordered(left_name: str, right_name: str, dependencies: dict[str, set[str]]) -> bool:
    return _depends_on(left_name, right_name, dependencies) or _depends_on(right_name, left_name, dependencies)


def _declares_shared_overlap(shared_entries: list[dict[str, Any]], left_name: str, right_name: str, left_paths: list[str], right_paths: list[str]) -> bool:
    for shared in shared_entries:
        if left_name not in shared["branches"] or right_name not in shared["branches"]:
            continue
        if any(_path_overlap(shared["path"], left) and _path_overlap(shared["path"], right) for left in left_paths for right in right_paths):
            return True
    return False


def validate_plan(plan_value: Any) -> dict[str, Any]:
    _scan_sanitized_structure(plan_value)
    plan = _require_object(plan_value, "plan")
    _require_exact_keys(plan, {"schema_version", "main", "branches", "shared_mutable_state"}, set(), "plan")
    if plan["schema_version"] != SCHEMA_VERSION:
        _fail(f"schema_version must be {SCHEMA_VERSION}")
    main = _require_object(plan["main"], "main")
    main_fields = {"completion_policy", "ending_policy", "child_control_policy", "execution_surface", "parallelism_evaluated", "parallel_benefit", "fallback", "temporary_root"}
    _require_exact_keys(main, main_fields, set(), "main")
    if main["completion_policy"] != "root_only" or main["ending_policy"] != "root_only_after_final_aggregate" or main["child_control_policy"] != "root_only":
        _fail("main completion, child control, and Ending ownership must be root-only")
    if main["execution_surface"] != "collaboration_child_sessions":
        _fail("main.execution_surface must select collaboration_child_sessions for the whole graph")
    if main["parallelism_evaluated"] is not True:
        _fail("main.parallelism_evaluated must be true")
    if main["fallback"] != "existing_single_producer_or_dispatcher":
        _fail("main.fallback must preserve the existing single producer/dispatcher")
    parallel_benefit = _sanitized_text(main["parallel_benefit"], "main.parallel_benefit", allow_none=True)
    if parallel_benefit is not None and (len(parallel_benefit) < 12 or parallel_benefit.casefold() in {"none", "n/a", "unknown", "maybe", "tbd"}):
        _fail("main.parallel_benefit must state a concrete bounded wait or isolation benefit")
    temporary_root = _temporary_root(main["temporary_root"])
    branches_value = plan["branches"]
    if not isinstance(branches_value, list) or not branches_value:
        _fail("branches must be a non-empty list")
    if len(branches_value) > MAX_BRANCHES:
        _fail(f"branches must contain at most {MAX_BRANCHES} bounded child sessions")
    branch_fields = {"name", "relative_workdir", "read_allowlist", "write_allowlist", "dependencies", "inputs", "outputs", "required", "cache", "stop_condition"}
    branches: list[dict[str, Any]] = []
    names: list[str] = []
    for index, branch_value in enumerate(branches_value):
        branch = _require_object(branch_value, f"branch {index}")
        _require_exact_keys(branch, branch_fields, set(), f"branch {index}")
        name = _identifier(branch["name"], f"branch {index} name")
        if name in names:
            _fail("branch names must be unique")
        workdir = _relative_workdir(branch["relative_workdir"], f"branch {name} relative_workdir")
        reads = _path_list(branch["read_allowlist"], f"branch {name} read_allowlist")
        writes = _path_list(branch["write_allowlist"], f"branch {name} write_allowlist")
        if not isinstance(branch["dependencies"], list):
            _fail(f"branch {name} dependencies must be a list")
        dependency_names = [_identifier(dependency, f"branch {name} dependency") for dependency in branch["dependencies"]]
        if len(dependency_names) != len(set(dependency_names)):
            _fail(f"branch {name} dependencies must be unique")
        inputs = _identifier_list(branch["inputs"], f"branch {name} inputs")
        outputs = _identifier_list(branch["outputs"], f"branch {name} outputs", require_value=True)
        if type(branch["required"]) is not bool:
            _fail(f"branch {name} required must be boolean")
        _sanitized_text(branch["stop_condition"], f"branch {name} stop_condition")
        cache = _validate_cache(branch["cache"], name, workdir, writes, temporary_root)
        names.append(name)
        branches.append({"name": name, "workdir": workdir, "reads": reads, "writes": writes, "dependencies": dependency_names, "inputs": inputs, "outputs": outputs, "required": branch["required"], "cache": cache})
    name_set = set(names)
    dependencies = {branch["name"]: set(branch["dependencies"]) for branch in branches}
    for branch in branches:
        missing_dependencies = sorted(dependencies[branch["name"]] - name_set)
        if missing_dependencies:
            _fail(f"branch {branch['name']} references missing dependencies")
        if branch["name"] in dependencies[branch["name"]]:
            _fail(f"branch {branch['name']} cannot depend on itself")
    waves = _topological_waves(names, dependencies)
    output_owners: dict[str, str] = {}
    for branch in branches:
        for output in branch["outputs"]:
            if output in output_owners:
                _fail(f"logical output {output} must have exactly one branch owner")
            output_owners[output] = branch["name"]
    for branch in branches:
        for input_name in branch["inputs"]:
            owner = output_owners.get(input_name)
            if owner is not None and owner != branch["name"] and not _depends_on(branch["name"], owner, dependencies):
                _fail(f"branch {branch['name']} input {input_name} requires an explicit dependency on {owner}")
    shared_values = plan["shared_mutable_state"]
    if not isinstance(shared_values, list):
        _fail("shared_mutable_state must be a list")
    shared_entries: list[dict[str, Any]] = []
    shared_paths: set[str] = set()
    branch_by_name = {branch["name"]: branch for branch in branches}
    for index, shared_value in enumerate(shared_values):
        shared = _require_object(shared_value, f"shared_mutable_state {index}")
        _require_exact_keys(shared, {"path", "branches"}, set(), f"shared_mutable_state {index}")
        shared_path = _relative_path(shared["path"], f"shared_mutable_state {index} path")
        if shared_path in shared_paths:
            _fail("shared_mutable_state paths must be unique")
        if not isinstance(shared["branches"], list) or len(shared["branches"]) < 2:
            _fail(f"shared_mutable_state {index} must name at least two branches")
        participant_names = [_identifier(name, f"shared_mutable_state {index} branch") for name in shared["branches"]]
        if len(participant_names) != len(set(participant_names)) or not set(participant_names) <= name_set:
            _fail(f"shared_mutable_state {index} branches must be unique existing branches")
        if not any(any(_path_overlap(shared_path, path) for path in branch_by_name[name]["writes"]) for name in participant_names):
            _fail(f"shared_mutable_state {index} must include at least one writer")
        for name in participant_names:
            touched_paths = branch_by_name[name]["reads"] + branch_by_name[name]["writes"]
            if not any(_path_overlap(shared_path, path) for path in touched_paths):
                _fail(f"shared_mutable_state {index} branch does not touch the declared path")
        for left_index, left_name in enumerate(participant_names):
            for right_name in participant_names[left_index + 1 :]:
                if not _dependency_ordered(left_name, right_name, dependencies):
                    _fail("shared mutable state requires explicit dependency ordering")
        shared_paths.add(shared_path)
        shared_entries.append({"path": shared_path, "branches": participant_names})
    for left_index, left in enumerate(branches):
        for right in branches[left_index + 1 :]:
            ordered = _dependency_ordered(left["name"], right["name"], dependencies)
            write_write = _paths_overlap(left["writes"], right["writes"])
            left_write_right_read = _paths_overlap(left["writes"], right["reads"])
            right_write_left_read = _paths_overlap(right["writes"], left["reads"])
            mutable_overlap = write_write or left_write_right_read or right_write_left_read
            if mutable_overlap and not ordered:
                _fail(f"dependency-ready branches have overlapping mutable surfaces: {left['name']} and {right['name']}")
            if mutable_overlap:
                left_mutable_paths = left["writes"] + left["reads"]
                right_mutable_paths = right["writes"] + right["reads"]
                if not _declares_shared_overlap(shared_entries, left["name"], right["name"], left_mutable_paths, right_mutable_paths):
                    _fail(f"ordered shared mutable state must be declared: {left['name']} and {right['name']}")
    execution_mode = "parallel_sessions" if parallel_benefit is not None and any(len(wave) >= 2 for wave in waves) else "sequential_fallback"
    return {"schema_version": SCHEMA_VERSION, "valid": True, "execution_mode": execution_mode, "execution_surface": "collaboration_child_sessions" if execution_mode == "parallel_sessions" else "existing_single_producer_or_dispatcher", "branch_count": len(branches), "dependency_waves": waves, "completion_owner": "root", "ending_start_owner": "root"}


def aggregate_plan(plan_value: Any, status_value: Any) -> dict[str, Any]:
    plan_summary = validate_plan(plan_value)
    _scan_sanitized_structure(status_value, "status")
    status = _require_object(status_value, "status")
    _require_exact_keys(status, {"schema_version", "main_review_passed", "branches"}, set(), "status")
    if status["schema_version"] != SCHEMA_VERSION:
        _fail(f"status schema_version must be {SCHEMA_VERSION}")
    if type(status["main_review_passed"]) is not bool:
        _fail("status.main_review_passed must be boolean")
    if not isinstance(status["branches"], list):
        _fail("status.branches must be a list")
    plan_branches = {branch["name"]: branch for branch in plan_value["branches"]}
    reports: dict[str, dict[str, Any]] = {}
    report_fields = {"name", "status", "readback", "acceptance", "conflict"}
    for index, report_value in enumerate(status["branches"]):
        report = _require_object(report_value, f"status branch {index}")
        _require_exact_keys(report, report_fields, set(), f"status branch {index}")
        name = _identifier(report["name"], f"status branch {index} name")
        if name not in plan_branches or name in reports:
            _fail("status branches must name each plan branch exactly once")
        if not isinstance(report["status"], str) or report["status"] not in BRANCH_STATUSES:
            _fail(f"status branch {name} has an invalid status")
        if any(type(report[field]) is not bool for field in ("readback", "acceptance", "conflict")):
            _fail(f"status branch {name} evidence fields must be boolean")
        reports[name] = report
    if set(reports) != set(plan_branches):
        _fail("status must include every plan branch exactly once")
    blocking_reasons: list[str] = []
    if plan_summary["execution_mode"] != "parallel_sessions":
        blocking_reasons.append("collaboration_not_admitted")
    if not status["main_review_passed"]:
        blocking_reasons.append("main_review_pending")
    for name, plan_branch in plan_branches.items():
        report = reports[name]
        if report["status"] in FORBIDDEN_ACTIVE_STATUSES:
            blocking_reasons.append(f"{name}:status_{report['status']}")
        if plan_branch["required"] and report["status"] != "passed":
            blocking_reasons.append(f"{name}:required_not_passed")
        if report["status"] == "passed":
            for dependency_name in plan_branch["dependencies"]:
                if reports[dependency_name]["status"] != "passed":
                    blocking_reasons.append(f"{name}:dependency_{dependency_name}_not_passed")
        if report["status"] == "passed" and not report["readback"]:
            blocking_reasons.append(f"{name}:readback_missing")
        if report["status"] == "passed" and not report["acceptance"]:
            blocking_reasons.append(f"{name}:acceptance_missing")
        if report["conflict"]:
            blocking_reasons.append(f"{name}:conflict")
    main_complete = not blocking_reasons
    status_counts = {branch_status: sum(1 for report in reports.values() if report["status"] == branch_status) for branch_status in sorted(BRANCH_STATUSES)}
    return {"schema_version": SCHEMA_VERSION, "valid": True, "execution_mode": plan_summary["execution_mode"], "main_complete": main_complete, "ending_start_ready": main_complete, "completion_owner": "root", "ending_start_owner": "root", "branch_status_counts": status_counts, "blocking_reasons": blocking_reasons}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or aggregate a sanitized logical parallel child-session plan.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="Validate boundaries and report parallel admission.")
    validate_parser.add_argument("plan", type=Path)
    aggregate_parser = subparsers.add_parser("aggregate", help="Aggregate root-reviewed branch statuses.")
    aggregate_parser.add_argument("plan", type=Path)
    aggregate_parser.add_argument("status", type=Path)
    arguments = parser.parse_args(argv)
    try:
        plan = _load_json(arguments.plan)
        output = validate_plan(plan) if arguments.command == "validate" else aggregate_plan(plan, _load_json(arguments.status))
    except PlanValidationError as error:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "valid": False, "errors": [str(error)]}, sort_keys=True, separators=(",", ":")))
        return 2
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"schema_version": SCHEMA_VERSION, "valid": False, "errors": ["input JSON could not be read"]}, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build and execute real-test Ending tasks with score-based model selection."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
BAND_ROLES = {"small": "weak_default", "standard": "balanced_default", "complex": "balanced_complex", "advanced": "frontier_complex"}


def complexity_band(score):
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("complexity score must be an integer from 0 to 100")
    return "small" if score <= 24 else "standard" if score <= 49 else "complex" if score <= 74 else "advanced"


def _clean(value, field, maximum=160):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text[:maximum]


def _registry():
    script = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "model_registry.py"
    spec = importlib.util.spec_from_file_location("ending_verification_model_registry", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_registry()


def pair_for_score(score, registry=None):
    band = complexity_band(score)
    payload = registry or _registry()
    pair = payload["role_pairs"][BAND_ROLES[band]]
    model, effort = pair.split("|", 1)
    return {"complexity_score": score, "complexity_band": band, "selected_pair": pair, "model": model, "effort": effort}


def _inside(root, value, field):
    path = Path(value).expanduser().resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{field} must be inside project_root") from error
    return path


def normalize_check(raw, project_root, task_name, task_score, registry=None):
    if not isinstance(raw, dict):
        raise ValueError("each check must be a JSON object")
    name = _clean(raw.get("name"), "check.name", 80)
    check_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "check"
    command = raw.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(value, str) or not value for value in command):
        raise ValueError("check.command must be a non-empty JSON string array")
    cwd = _inside(project_root, raw.get("cwd") or project_root, "check.cwd")
    score = raw.get("complexity_score", task_score)
    route = pair_for_score(score, registry)
    timeout = raw.get("timeout_seconds", 300)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 1800:
        raise ValueError("check.timeout_seconds must be from 1 to 1800")
    expected_exit = raw.get("expected_exit_code", 0)
    if isinstance(expected_exit, bool) or not isinstance(expected_exit, int):
        raise ValueError("check.expected_exit_code must be an integer")
    return {
        "check_id": check_id,
        "name": name,
        "title": f"End Task-{task_name}-{name}",
        "cwd": str(cwd),
        "command": command,
        "expected_exit_code": expected_exit,
        "timeout_seconds": timeout,
        "independent": bool(raw.get("independent", True)),
        **route,
        "on_failure": {
            "action": "create_repair_task_then_fresh_ending",
            "repair_title": f"Fix Task-{task_name}-{name}",
            "error_fields": ["exit_code", "stdout", "stderr", "timed_out"],
            "max_repair_attempts": 3,
        },
    }


def build_plan(project_root, task_name, task_score, checks):
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    cleaned_task = _clean(task_name, "task_name", 80)
    registry = _registry()
    tasks = [normalize_check(check, root, cleaned_task, task_score, registry) for check in checks]
    if not tasks:
        raise ValueError("at least one real verification check is required")
    ids = [task["check_id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("check names must produce unique ids")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "task_name": cleaned_task,
        "task_complexity": pair_for_score(task_score, registry),
        "verification_required": True,
        "execution": "separate_persistent_tasks",
        "all_checks_must_pass": True,
        "ending_tasks": tasks,
    }


def _atomic_write(path, payload):
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    target.chmod(0o600)


def run_check(plan_path, check_id, evidence_output):
    plan_file = Path(plan_path).expanduser().resolve()
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    check = next((item for item in plan.get("ending_tasks", []) if item.get("check_id") == check_id), None)
    if not check:
        raise ValueError(f"unknown check_id: {check_id}")
    started = datetime.now(timezone.utc)
    timed_out = False
    try:
        completed = subprocess.run(check["command"], cwd=check["cwd"], capture_output=True, text=True, timeout=check["timeout_seconds"], check=False)
        exit_code = completed.returncode
        stdout = completed.stdout[-12000:]
        stderr = completed.stderr[-12000:]
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = None
        stdout = (error.stdout or "")[-12000:] if isinstance(error.stdout, str) else ""
        stderr = (error.stderr or "")[-12000:] if isinstance(error.stderr, str) else ""
    passed = not timed_out and exit_code == check["expected_exit_code"]
    finished = datetime.now(timezone.utc)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if passed else "fail",
        "check_id": check_id,
        "title": check["title"],
        "selected_pair": check["selected_pair"],
        "complexity_score": check["complexity_score"],
        "complexity_band": check["complexity_band"],
        "command": check["command"],
        "cwd": check["cwd"],
        "expected_exit_code": check["expected_exit_code"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_ms": round((finished - started).total_seconds() * 1000),
        "plan_sha256": hashlib.sha256(plan_file.read_bytes()).hexdigest(),
    }
    if not passed:
        evidence["repair_handoff"] = {**check["on_failure"], "failed_ending_title": check["title"], "failed_check_id": check_id, "error": {key: evidence[key] for key in check["on_failure"]["error_fields"]}}
    _atomic_write(evidence_output, evidence)
    return evidence


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Plan and execute real-test Ending tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--project-root", type=Path, required=True)
    plan.add_argument("--task-name", required=True)
    plan.add_argument("--complexity-score", type=int, required=True)
    plan.add_argument("--check-json", action="append", default=[])
    plan.add_argument("--output", type=Path, required=True)
    run = subparsers.add_parser("run-check")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--check-id", required=True)
    run.add_argument("--evidence-output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "plan":
        payload = build_plan(args.project_root, args.task_name, args.complexity_score, [json.loads(value) for value in args.check_json])
        _atomic_write(args.output, payload)
        output = {"status": "written", "output": str(args.output.expanduser().resolve()), "ending_tasks": len(payload["ending_tasks"]), "selected_pairs": [task["selected_pair"] for task in payload["ending_tasks"]]}
        code = 0
    else:
        output = run_check(args.plan, args.check_id, args.evidence_output)
        code = 0 if output["status"] == "pass" else 1
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

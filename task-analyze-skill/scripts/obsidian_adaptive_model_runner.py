#!/usr/bin/env python3
"""Run one Spark-first producer with an Obsidian-selected GPT-5.6 fallback."""

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from tempfile import mkstemp
from types import SimpleNamespace


def _load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = Path(__file__).resolve().parents[2]
model_execution_receipt = _load_file("obsidian_adaptive_receipt", SCRIPT_DIR / "model_execution_receipt.py")
obsidian_model_memory = _load_file(
    "obsidian_adaptive_memory",
    SKILLS_ROOT / "project-memory-skill" / "scripts" / "obsidian_model_memory.py",
)


def _emit_result_ready(result_path, ready_monotonic_ns):
    print(json.dumps({"schema_version": 1, "stage": "result-ready", "result_path": str(result_path), "result_ready_monotonic_ns": ready_monotonic_ns}, separators=(",", ":")), flush=True)


def _atomic_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _receipt_args(args, selected):
    return SimpleNamespace(
        model=selected[0],
        effort=selected[1],
        workload_id=args.workload_id,
        output=args.receipt_output,
        result_output=args.result_output,
        workdir=args.workdir,
        state_db=args.state_db,
        codex_bin=args.codex_bin,
        sandbox=args.sandbox,
        allow_fallback=[],
        ignore_user_config=args.ignore_user_config,
        entry_task=False,
        node_role="result-producer",
        route_marker="LOCKED_ROUTE_NODE",
        stream_result_ready=True,
        result_ready_callback=_emit_result_ready,
        timeout=args.timeout,
        emit_result=False,
    )


def _recommend(args):
    return obsidian_model_memory.recommend_model(
        args.project_root,
        args.task_type,
        args.module,
        file_value=args.file,
        symbol=args.symbol,
        code_kind=args.code_kind,
        operation=args.operation,
        modality=args.modality,
        complexity=args.complexity,
        risk=args.risk,
        ambiguity=args.ambiguity,
        task_summary=args.task_summary,
        vault=args.vault,
        ladder=args.ladder,
    )


def _zero_token_map():
    return {field: 0 for field in model_execution_receipt.TOKEN_FIELDS}


def _pre_execution_failure(receipt_args):
    receipt = model_execution_receipt.failed_run_receipt(receipt_args, "execution")
    receipt["tokens"] = _zero_token_map()
    receipt["process_elapsed_ms"] = 0
    receipt["pre_execution_failure"] = True
    if receipt.get("route_attempts"):
        receipt["route_attempts"][0]["tokens"] = _zero_token_map()
        receipt["route_attempts"][0]["process_elapsed_ms"] = 0
        receipt["route_attempts"][0]["pre_execution_failure"] = True
    return model_execution_receipt.annotate_operational_fallback(receipt)


def _attempt_pairs(args, recommendation):
    attempt_pair = recommendation.get("attempt_pair") or recommendation["selected_pair"]
    active_pair = recommendation.get("active_fallback_pair")
    _, active_pairs = obsidian_model_memory.load_shared_ladder(args.ladder)
    pairs = [attempt_pair]
    if active_pair and active_pair != attempt_pair:
        pairs.append(active_pair)
    for pair in model_execution_receipt.normalize_fallback_pairs(args.allow_fallback):
        if pair in active_pairs and pair not in pairs:
            pairs.append(pair)
    return pairs


def _merge_attempt_receipts(receipts, planned_pairs, attempt_pair, active_pair, result_output):
    receipt = dict(receipts[-1])
    route_attempts = []
    operational_failures = []
    for attempted_pair, attempted_receipt in zip(planned_pairs, receipts):
        attempts = attempted_receipt.get("route_attempts")
        if isinstance(attempts, list):
            route_attempts.extend(dict(attempt) for attempt in attempts if isinstance(attempt, dict))
        if model_execution_receipt.immediate_operational_fallback(attempted_receipt):
            operational_failures.append(attempted_pair)
    metrics = model_execution_receipt.aggregate_token_maps([
        attempted.get("tokens") if isinstance(attempted.get("tokens"), dict) else {}
        for attempted in receipts
    ])
    elapsed_values = [attempted.get("process_elapsed_ms") for attempted in receipts]
    elapsed = sum(elapsed_values) if elapsed_values and all(isinstance(value, int) and value >= 0 for value in elapsed_values) else None
    receipt["priority_attempt_pair"] = attempt_pair
    receipt["active_fallback_pair"] = active_pair
    receipt["allowed_fallback_pairs"] = planned_pairs[1:]
    receipt["operational_failure_pairs"] = operational_failures
    receipt["route_attempts"] = route_attempts
    receipt["last_attempt_tokens"] = dict(receipt.get("tokens") or {})
    receipt["last_attempt_process_elapsed_ms"] = receipt.get("process_elapsed_ms")
    receipt["strategy_tokens"] = metrics
    receipt["strategy_elapsed_ms"] = elapsed
    receipt["tokens"] = metrics
    receipt["process_elapsed_ms"] = elapsed
    receipt["result_published"] = bool(result_output.is_file() and result_output.stat().st_size > 0)
    return receipt


def run(args, prompt):
    started_ns = time.monotonic_ns()
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt_required")
    recommendation = _recommend(args)
    if recommendation.get("memory_available") is not True:
        return {"status": "blocked", "reason": "obsidian_model_memory_unavailable", "recommendation": recommendation}
    pair = recommendation.get("attempt_pair") or recommendation.get("selected_pair")
    if not pair:
        return {"status": "blocked", "reason": recommendation.get("reason"), "recommendation": recommendation}
    if args.result_output.exists():
        args.result_output.unlink()
    active_pair = recommendation.get("active_fallback_pair")
    planned_pairs = _attempt_pairs(args, recommendation)
    receipts = []
    attempted_pairs = []
    for planned_pair in planned_pairs:
        if args.result_output.exists() and args.result_output.stat().st_size == 0:
            args.result_output.unlink()
        selected = tuple(planned_pair.split("|", 1))
        receipt_args = _receipt_args(args, selected)
        try:
            with model_execution_receipt.adaptive_producer_authorization():
                attempt_receipt = model_execution_receipt.run_receipt(receipt_args, prompt)
        except (OSError, ValueError):
            attempt_receipt = _pre_execution_failure(receipt_args)
        visible_result = bool(args.result_output.is_file() and args.result_output.stat().st_size > 0)
        attempt_receipt["result_published"] = visible_result
        attempt_receipt = model_execution_receipt.annotate_operational_fallback(attempt_receipt)
        receipts.append(attempt_receipt)
        attempted_pairs.append(planned_pair)
        if attempt_receipt.get("status") == "pass" and visible_result:
            break
        if not model_execution_receipt.immediate_operational_fallback(attempt_receipt):
            break
    receipt = _merge_attempt_receipts(receipts, attempted_pairs, pair, active_pair, args.result_output)
    result_published = bool(receipt.get("result_published") is True and args.result_output.is_file() and args.result_output.stat().st_size > 0)
    receipt["result_published"] = result_published
    _atomic_write_json(args.receipt_output, receipt)
    tokens = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
    ready_ns = receipt.get("result_ready_monotonic_ns")
    summary = {
        "status": "pass" if receipt.get("status") == "pass" and result_published else "fail",
        "reason": recommendation.get("attempt_reason", recommendation["reason"]) if receipt.get("status") == "pass" and result_published else "producer_operational_failure",
        "execution_mode": "obsidian_adaptive_producer",
        "memory_source": recommendation["source"],
        "memory_available": recommendation["memory_available"],
        "selected_pair": pair,
        "active_fallback_pair": active_pair,
        "executed_pair": receipt.get("effective_pair") or receipt.get("requested_pair"),
        "operational_failure_pairs": receipt.get("operational_failure_pairs", []),
        "trial": recommendation.get("attempt_trial", recommendation["trial"]),
        "calibration_state": recommendation.get("attempt_calibration_state", recommendation["calibration_state"]),
        "specificity": recommendation["specificity"],
        "matched_records": recommendation["matched_records"],
        "project_key": recommendation["project_key"],
        "receipt_path": str(args.receipt_output),
        "result_path": str(args.result_output),
        "result_published": result_published,
        "total_tokens": tokens.get("total_tokens"),
        "elapsed_ms": receipt.get("process_elapsed_ms"),
        "first_result_elapsed_ms": round((ready_ns - started_ns) / 1_000_000) if isinstance(ready_ns, int) and ready_ns >= started_ns else None,
        "ending_real_status": "pending" if receipt.get("status") == "pass" and result_published else "not_started",
    }
    if args.emit_result and summary["status"] == "pass":
        summary["result"] = args.result_output.read_text(encoding="utf-8").rstrip("\n")
    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run one Obsidian-memory-selected Spark-first producer")
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--ladder", type=Path, default=obsidian_model_memory.DEFAULT_LADDER)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--file", default="")
    parser.add_argument("--symbol", default="")
    parser.add_argument("--code-kind", default="general")
    parser.add_argument("--operation", default="work")
    parser.add_argument("--modality", choices=sorted(obsidian_model_memory.MODALITY_VALUES), default="text")
    parser.add_argument("--complexity", choices=sorted(obsidian_model_memory.COMPLEXITY_VALUES), default="easy")
    parser.add_argument("--risk", choices=sorted(obsidian_model_memory.LEVEL_VALUES), default="low")
    parser.add_argument("--ambiguity", choices=sorted(obsidian_model_memory.LEVEL_VALUES), default="low")
    parser.add_argument("--task-summary", default="")
    parser.add_argument("--workload-id", required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--result-output", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    parser.add_argument("--state-db", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "state_5.sqlite")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--sandbox", choices=("read-only", "workspace-write", "danger-full-access"), default="read-only")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--ignore-user-config", action="store_true")
    parser.add_argument("--allow-fallback", action="append", default=[])
    parser.add_argument("--emit-result", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.receipt_output == args.result_output:
        parser.error("invalid runner output or timeout")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        summary = run(args, sys.stdin.read())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        summary = {"status": "fail", "reason": str(error)[:120] or "runner_validation_failed"}
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

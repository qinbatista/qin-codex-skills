#!/usr/bin/env python3
"""Run one adaptive producer without allowing the entry model to pick its pair."""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from tempfile import mkstemp
from types import SimpleNamespace


def _load_sibling(module_name):
    try:
        return __import__(module_name)
    except ModuleNotFoundError:
        import importlib.util

        module_path = Path(__file__).with_name(f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(f"adaptive_runner_{module_name}", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


model_routing_history = _load_sibling("model_routing_history")
model_execution_receipt = _load_sibling("model_execution_receipt")
strategy_performance = _load_sibling("strategy_performance")


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REASON_PATTERN = re.compile(r"^[a-z0-9_]{1,80}$")


class RunnerFailure(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _atomic_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _profile_arguments(args):
    return SimpleNamespace(
        task_family=args.task_family,
        artifact=args.artifact,
        scope=args.scope,
        ambiguity=args.ambiguity,
        modality=args.modality,
        risk=args.risk,
        complexity=args.complexity,
        project_family=args.project_family,
        verification_shape=args.verification_shape,
        owning_skill=args.owning_skill,
        execution_domain=args.execution_domain,
        task_summary=args.task_summary,
        candidate_ladder=args.candidate_ladder,
        static_suggestion=args.static_suggestion,
        hard_floor=args.hard_floor,
        history=args.history,
        enforce_candidate_policy=True,
    )


def _validated_recommendation(args):
    recommendation = model_routing_history.recommend_route(_profile_arguments(args))
    if not isinstance(recommendation, dict):
        raise RunnerFailure("recommendation_invalid")
    selected_text = recommendation.get("selected_pair")
    try:
        selected = model_routing_history.parse_pair(selected_text)
        hard_floor = model_routing_history.parse_pair(args.hard_floor)
        candidates = model_routing_history.canonical_pairs(args.candidate_ladder)
    except (TypeError, ValueError):
        raise RunnerFailure("recommendation_invalid")
    if (
        selected not in candidates
        or model_routing_history.compare_pair(selected, hard_floor) < 0
        or recommendation.get("selected_model") != selected[0]
        or recommendation.get("selected_effort") != selected[1]
        or not isinstance(recommendation.get("trial"), bool)
        or not SHA256_PATTERN.fullmatch(str(recommendation.get("profile_fingerprint", "")))
        or not REASON_PATTERN.fullmatch(str(recommendation.get("reason", "")))
    ):
        raise RunnerFailure("recommendation_invalid")
    for fallback_text in args.allow_fallback:
        try:
            fallback = model_routing_history.parse_pair(fallback_text)
        except (TypeError, ValueError):
            raise RunnerFailure("fallback_invalid")
        if fallback not in candidates or model_routing_history.compare_pair(fallback, hard_floor) < 0:
            raise RunnerFailure("fallback_invalid")
    return recommendation, selected


def _receipt_arguments(args, selected):
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
        allow_fallback=args.allow_fallback,
        ignore_user_config=args.ignore_user_config,
        entry_task=False,
        node_role="result-producer",
        route_marker="LOCKED_ROUTE_NODE",
        stream_result_ready=True,
        result_ready_callback=getattr(args, "result_ready_callback", None),
        timeout=args.timeout,
        emit_result=False,
    )


def _adaptive_run_id(args):
    run_id = getattr(args, "adaptive_run_id", None)
    if not isinstance(run_id, str) or not run_id:
        run_id = f"run_{os.urandom(8).hex()}"
        args.adaptive_run_id = run_id
    return run_id


def _emit_result_ready_event(result_path, ready_monotonic_ns):
    event = {"schema_version": 1, "stage": "result-ready", "result_path": str(result_path), "result_ready_monotonic_ns": ready_monotonic_ns}
    print(json.dumps(event, sort_keys=True, separators=(",", ":")), flush=True)


def _summary(args, *, status, selected_pair=None, trial=False, reason, profile_fingerprint=None, receipt=None, execution_mode=None, performance_admission=None):
    tokens = receipt.get("tokens") if isinstance(receipt, dict) and isinstance(receipt.get("tokens"), dict) else {}
    result_published = bool(isinstance(receipt, dict) and receipt.get("result_published") is True and args.result_output.is_file())
    result_ready_monotonic_ns = receipt.get("result_ready_monotonic_ns") if isinstance(receipt, dict) else None
    first_result_started_ns = getattr(args, "_first_result_started_ns", None)
    first_result_elapsed_ms = round((result_ready_monotonic_ns - first_result_started_ns) / 1_000_000) if isinstance(result_ready_monotonic_ns, int) and isinstance(first_result_started_ns, int) and result_ready_monotonic_ns >= first_result_started_ns else None
    failed_after_presentation = status == "fail" and result_published
    summary = {
        "status": status,
        "adaptive_run_id": _adaptive_run_id(args),
        "profile_preset": getattr(args, "profile_preset", None),
        "selected_pair": selected_pair,
        "trial": bool(trial),
        "reason": reason,
        "profile_fingerprint": profile_fingerprint,
        "receipt_path": str(args.receipt_output),
        "result_path": str(args.result_output),
        "elapsed_ms": receipt.get("process_elapsed_ms") if isinstance(receipt, dict) else None,
        "first_result_elapsed_ms": first_result_elapsed_ms,
        "total_tokens": tokens.get("total_tokens"),
        "real_verify_status": "pending" if status == "pass" else "not_started",
        "result_published": result_published,
        "notification_required": failed_after_presentation,
        "reopen_required": failed_after_presentation,
        "execution_mode": execution_mode or "delegated_adaptive" if status == "pass" else execution_mode,
    }
    if isinstance(performance_admission, dict):
        summary["performance_admission"] = performance_admission
    if getattr(args, "emit_result", False) and status == "pass" and args.result_output.exists():
        summary["result"] = args.result_output.read_text(encoding="utf-8").rstrip("\n")
    return summary


def _performance_arguments(args, recommendation, prompt_text):
    required = (getattr(args, "entry_pair", None), getattr(args, "config_cohort", None), getattr(args, "strategy_version", None), getattr(args, "producer_contract_version", None))
    if any(value is None for value in required):
        return None
    return SimpleNamespace(history=args.performance_history, profile_fingerprint=recommendation["profile_fingerprint"], entry_pair=args.entry_pair, config_cohort=args.config_cohort, sandbox_label=args.sandbox, strategy_version=args.strategy_version, producer_contract_version=args.producer_contract_version, workload_prompt_sha256=model_execution_receipt.sha256_text(prompt_text), minimum_paired_samples=args.minimum_paired_samples, minimum_savings_percent=args.minimum_savings_percent)


def _performance_admission(args, recommendation, prompt_text):
    if getattr(args, "benchmark_calibration", False):
        return {"schema_version": 1, "execution_mode": "delegated_adaptive", "reason": "explicit_benchmark_calibration", "admitted": False, "calibration": True}
    performance_args = _performance_arguments(args, recommendation, prompt_text)
    if performance_args is None:
        return {"schema_version": 1, "execution_mode": "inline_entry", "reason": "performance_admission_arguments_missing", "admitted": False}
    if recommendation.get("trial") is not False or recommendation.get("calibration_state") != "frozen":
        return {"schema_version": 1, "execution_mode": "inline_entry", "reason": "quality_pair_not_frozen", "admitted": False}
    return strategy_performance.recommend_mode(performance_args)


def run_adaptive(args, prompt_text):
    args._first_result_started_ns = time.monotonic_ns()
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise RunnerFailure("prompt_required")
    if args.timeout <= 0 or args.receipt_output == args.result_output:
        raise RunnerFailure("runner_arguments_invalid")
    if Path(args.history).expanduser().resolve() == model_routing_history.DEFAULT_HISTORY_PATH.resolve():
        if args.result_output.exists():
            args.result_output.unlink()
        return _summary(args, status="inline", reason="legacy_local_model_history_inactive", execution_mode="inline_entry")
    recommendation, selected = _validated_recommendation(args)
    performance_admission = _performance_admission(args, recommendation, prompt_text)
    if performance_admission.get("execution_mode") != "delegated_adaptive":
        if args.result_output.exists():
            args.result_output.unlink()
        return _summary(args, status="inline", selected_pair=recommendation["selected_pair"], trial=recommendation["trial"], reason=performance_admission.get("reason", "delegation_not_admitted"), profile_fingerprint=recommendation["profile_fingerprint"], execution_mode="inline_entry", performance_admission=performance_admission)
    if args.result_output.exists():
        args.result_output.unlink()
    receipt = None
    receipt_args = _receipt_arguments(args, selected)
    try:
        with model_execution_receipt.adaptive_producer_authorization():
            receipt = model_execution_receipt.run_receipt(receipt_args, prompt_text)
    except (OSError, ValueError):
        receipt = model_execution_receipt.failed_run_receipt(receipt_args, "execution")
        if args.result_output.is_file() and args.result_output.stat().st_size > 0:
            receipt.update({"result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "result_output_path": str(args.result_output)})
    if receipt.get("requested_pair") != recommendation["selected_pair"]:
        raise RunnerFailure("receipt_pair_override")
    result_published = bool(receipt.get("result_published") is True and args.result_output.is_file() and args.result_output.stat().st_size > 0)
    receipt["result_published"] = result_published
    if not result_published:
        receipt.pop("result_output_path", None)
    _atomic_write_json(args.receipt_output, receipt)
    if receipt.get("status") != "pass":
        failure_reason = "producer_receipt_failure_after_result" if result_published else "producer_operational_failure"
        return _summary(args, status="fail", selected_pair=recommendation["selected_pair"], trial=recommendation["trial"], reason=failure_reason, profile_fingerprint=recommendation["profile_fingerprint"], receipt=receipt, execution_mode="delegated_adaptive", performance_admission=performance_admission)
    if not result_published:
        return _summary(args, status="fail", selected_pair=recommendation["selected_pair"], trial=recommendation["trial"], reason="result_missing", profile_fingerprint=recommendation["profile_fingerprint"], receipt=receipt, execution_mode="delegated_adaptive", performance_admission=performance_admission)
    os.chmod(args.result_output, 0o600)
    return _summary(args, status="pass", selected_pair=recommendation["selected_pair"], trial=recommendation["trial"], reason=recommendation["reason"], profile_fingerprint=recommendation["profile_fingerprint"], receipt=receipt, execution_mode="delegated_adaptive", performance_admission=performance_admission)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Select and execute one receipt-backed adaptive model producer.")
    parser.add_argument("--history", type=Path, default=model_routing_history.DEFAULT_HISTORY_PATH)
    model_routing_history.add_profile_arguments(parser)
    parser.add_argument("--workload-id", required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--result-output", type=Path, required=True)
    parser.add_argument("--emit-result", action="store_true", help="Return the saved passing result in the command summary; never store it in routing history or the receipt.")
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    parser.add_argument("--state-db", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "state_5.sqlite")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--sandbox", choices=["read-only", "workspace-write", "danger-full-access"], default="read-only")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--ignore-user-config", action="store_true")
    parser.add_argument("--allow-fallback", action="append", default=[])
    parser.add_argument("--performance-history", type=Path, default=strategy_performance.DEFAULT_HISTORY_PATH)
    parser.add_argument("--entry-pair")
    parser.add_argument("--config-cohort")
    parser.add_argument("--strategy-version")
    parser.add_argument("--producer-contract-version")
    parser.add_argument("--minimum-paired-samples", type=int, default=strategy_performance.DEFAULT_MINIMUM_PAIRED_SAMPLES)
    parser.add_argument("--minimum-savings-percent", type=float, default=strategy_performance.DEFAULT_MINIMUM_SAVINGS_PERCENT)
    parser.add_argument("--benchmark-calibration", action="store_true", help="Explicit benchmark-only bypass used to collect admission evidence; never use for ordinary foreground routing.")
    return model_routing_history.resolve_profile_arguments(parser.parse_args(argv))


def main(argv=None):
    args = parse_args(argv)
    args.result_ready_callback = _emit_result_ready_event
    try:
        summary = run_adaptive(args, sys.stdin.read())
    except RunnerFailure as failure:
        summary = _summary(args, status="fail", reason=failure.code)
    except (OSError, ValueError):
        summary = _summary(args, status="fail", reason="runner_validation_failed")
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if summary["status"] in {"pass", "inline"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

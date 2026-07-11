#!/usr/bin/env python3
"""Run one adaptive producer without allowing the entry model to pick its pair."""

import argparse
import json
import os
import re
import sys
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
grounded_result_gate = _load_sibling("grounded_result_gate")


GATE_KEYS = {
    "schema_version",
    "json_required_keys",
    "json_key_order",
    "sorted_json_pointers",
    "source_root",
    "source_files_pointer",
}
GROUNDED_GATE_PRESETS = {
    "json-object": {"required_keys": [], "expected_key_order": None, "sorted_json_pointers": [], "source_files_pointer": None},
    "grounded-source-json-v1": {"required_keys": ["source_files"], "expected_key_order": None, "sorted_json_pointers": ["/source_files"], "source_files_pointer": "/source_files"},
    "workflow-graph-json-v1": {"required_keys": ["entry", "early_exit_conditions", "stages", "final_merge_fields", "public_return_keys", "source_files"], "expected_key_order": ["entry", "early_exit_conditions", "stages", "final_merge_fields", "public_return_keys", "source_files"], "sorted_json_pointers": ["/stages/*/agents", "/final_merge_fields", "/public_return_keys", "/source_files"], "source_files_pointer": "/source_files"},
    "workflow-graph-json-v2": {"required_keys": ["entry", "early_exit_conditions", "stages", "final_merge_fields", "always_return_keys", "optional_return_keys", "source_files"], "expected_key_order": ["entry", "early_exit_conditions", "stages", "final_merge_fields", "always_return_keys", "optional_return_keys", "source_files"], "sorted_json_pointers": ["/stages/*/agents", "/final_merge_fields", "/always_return_keys", "/optional_return_keys", "/source_files"], "source_files_pointer": "/source_files"},
}
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


def _private_result_temp(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    os.chmod(temporary_path, 0o600)
    return Path(temporary_path)


def _string_list(value, field, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise RunnerFailure("grounded_gate_config_invalid")
    if len(value) != len(set(value)):
        raise RunnerFailure("grounded_gate_config_invalid")
    return value


def load_gate_config(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RunnerFailure("grounded_gate_config_invalid")
    if not isinstance(value, dict) or set(value) - GATE_KEYS or value.get("schema_version") != 1:
        raise RunnerFailure("grounded_gate_config_invalid")
    required_keys = _string_list(value.get("json_required_keys", []), "json_required_keys")
    key_order = _string_list(value.get("json_key_order"), "json_key_order", optional=True)
    sorted_pointers = _string_list(value.get("sorted_json_pointers", []), "sorted_json_pointers")
    source_root = value.get("source_root")
    source_pointer = value.get("source_files_pointer")
    if (source_root is None) != (source_pointer is None):
        raise RunnerFailure("grounded_gate_config_invalid")
    if source_root is not None and (not isinstance(source_root, str) or not source_root):
        raise RunnerFailure("grounded_gate_config_invalid")
    if source_pointer is not None and (not isinstance(source_pointer, str) or not source_pointer):
        raise RunnerFailure("grounded_gate_config_invalid")
    return {
        "required_keys": required_keys,
        "expected_key_order": key_order,
        "sorted_json_pointers": sorted_pointers,
        "source_root": Path(source_root) if source_root is not None else None,
        "source_files_pointer": source_pointer,
    }


def load_gate_preset(profile_preset, source_root=None):
    if profile_preset not in GROUNDED_GATE_PRESETS:
        raise RunnerFailure("grounded_gate_preset_invalid")
    preset = GROUNDED_GATE_PRESETS[profile_preset]
    source_pointer = preset["source_files_pointer"]
    if source_pointer is not None and source_root is None:
        raise RunnerFailure("grounded_gate_source_root_required")
    if source_pointer is None and source_root is not None:
        raise RunnerFailure("grounded_gate_source_root_unused")
    return {"required_keys": list(preset["required_keys"]), "expected_key_order": list(preset["expected_key_order"]) if preset["expected_key_order"] is not None else None, "sorted_json_pointers": list(preset["sorted_json_pointers"]), "source_root": source_root, "source_files_pointer": source_pointer}


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


def _receipt_arguments(args, selected, temporary_result):
    return SimpleNamespace(
        model=selected[0],
        effort=selected[1],
        workload_id=args.workload_id,
        output=args.receipt_output,
        result_output=temporary_result,
        workdir=args.workdir,
        state_db=args.state_db,
        codex_bin=args.codex_bin,
        sandbox=args.sandbox,
        allow_fallback=args.allow_fallback,
        ignore_user_config=args.ignore_user_config,
        entry_task=False,
        node_role="result-producer",
        route_marker="LOCKED_ROUTE_NODE",
        timeout=args.timeout,
        emit_result=False,
    )


def _record_arguments(args, receipt_path, recommendation, run_id, mini_status, failure_class):
    values = vars(_profile_arguments(args)).copy()
    values.update(
        receipt=str(receipt_path),
        verify_level="mini",
        verify_status=mini_status,
        failure_class=failure_class,
        run_id=run_id,
        trial=recommendation["trial"],
    )
    return SimpleNamespace(**values)


def _summary(args, *, status, selected_pair=None, trial=False, reason, profile_fingerprint=None, mini_status="not_run", receipt=None):
    tokens = receipt.get("tokens") if isinstance(receipt, dict) and isinstance(receipt.get("tokens"), dict) else {}
    summary = {
        "status": status,
        "profile_preset": getattr(args, "profile_preset", None),
        "selected_pair": selected_pair,
        "trial": bool(trial),
        "reason": reason,
        "profile_fingerprint": profile_fingerprint,
        "receipt_path": str(args.receipt_output),
        "result_path": str(args.result_output),
        "elapsed_ms": receipt.get("process_elapsed_ms") if isinstance(receipt, dict) else None,
        "total_tokens": tokens.get("total_tokens"),
        "mini_status": mini_status,
    }
    if getattr(args, "emit_result", False) and status == "pass" and args.result_output.exists():
        summary["result"] = args.result_output.read_text(encoding="utf-8").rstrip("\n")
    return summary


def run_adaptive(args, prompt_text):
    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise RunnerFailure("prompt_required")
    if args.timeout <= 0 or args.receipt_output == args.result_output:
        raise RunnerFailure("runner_arguments_invalid")
    gate_config_path = getattr(args, "grounded_gate_config", None)
    gate_preset = getattr(args, "grounded_gate_preset", None)
    if gate_config_path is not None and gate_preset is not None:
        raise RunnerFailure("grounded_gate_selector_conflict")
    gate_config = load_gate_config(gate_config_path) if gate_config_path is not None else load_gate_preset(gate_preset, getattr(args, "grounded_source_root", None)) if gate_preset is not None else None
    recommendation, selected = _validated_recommendation(args)
    temporary_result = _private_result_temp(args.result_output)
    receipt = None
    result_saved = False
    try:
        receipt_args = _receipt_arguments(args, selected, temporary_result)
        try:
            with model_execution_receipt.adaptive_producer_authorization():
                receipt = model_execution_receipt.run_receipt(receipt_args, prompt_text)
        except OSError:
            receipt = model_execution_receipt.failed_run_receipt(receipt_args, "execution")
        if receipt.get("requested_pair") != recommendation["selected_pair"]:
            raise RunnerFailure("receipt_pair_override")
        if receipt.get("status") == "pass" and temporary_result.stat().st_size > 0:
            os.replace(temporary_result, args.result_output)
            os.chmod(args.result_output, 0o600)
            receipt["result_output_path"] = str(args.result_output)
            result_saved = True
        _atomic_write_json(args.receipt_output, receipt)
        if receipt.get("status") != "pass":
            return _summary(
                args,
                status="fail",
                selected_pair=recommendation["selected_pair"],
                trial=recommendation["trial"],
                reason="producer_operational_failure",
                profile_fingerprint=recommendation["profile_fingerprint"],
                receipt=receipt,
            )
        if not result_saved:
            return _summary(
                args,
                status="fail",
                selected_pair=recommendation["selected_pair"],
                trial=recommendation["trial"],
                reason="result_missing",
                profile_fingerprint=recommendation["profile_fingerprint"],
                receipt=receipt,
            )
        mini_status = "not_run"
        if gate_config is not None:
            run_id = f"run_{os.urandom(8).hex()}"
            try:
                grounded_result_gate.validate_grounded_result(
                    receipt_path=args.receipt_output,
                    result_path=args.result_output,
                    **gate_config,
                )
            except grounded_result_gate.GateFailure:
                mini_status = "fail"
                model_routing_history.record_event(
                    _record_arguments(args, args.receipt_output, recommendation, run_id, "fail", "correctness")
                )
                return _summary(
                    args,
                    status="fail",
                    selected_pair=recommendation["selected_pair"],
                    trial=recommendation["trial"],
                    reason="grounded_gate_failed",
                    profile_fingerprint=recommendation["profile_fingerprint"],
                    mini_status=mini_status,
                    receipt=receipt,
                )
            mini_status = "pass"
            model_routing_history.record_event(
                _record_arguments(args, args.receipt_output, recommendation, run_id, "pass", "none")
            )
        return _summary(
            args,
            status="pass",
            selected_pair=recommendation["selected_pair"],
            trial=recommendation["trial"],
            reason=recommendation["reason"],
            profile_fingerprint=recommendation["profile_fingerprint"],
            mini_status=mini_status,
            receipt=receipt,
        )
    finally:
        if temporary_result.exists():
            temporary_result.unlink()


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
    parser.add_argument("--grounded-gate-config", type=Path)
    parser.add_argument("--grounded-gate-preset", choices=tuple(GROUNDED_GATE_PRESETS))
    parser.add_argument("--grounded-source-root", type=Path)
    return model_routing_history.resolve_profile_arguments(parser.parse_args(argv))


def main(argv=None):
    args = parse_args(argv)
    try:
        summary = run_adaptive(args, sys.stdin.read())
    except RunnerFailure as failure:
        summary = _summary(args, status="fail", reason=failure.code)
    except (OSError, ValueError):
        summary = _summary(args, status="fail", reason="runner_validation_failed")
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import contextvars
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    from routing_policy import MODEL_EFFORTS, parse_model_effort_pair, pair_text
except ModuleNotFoundError:
    import importlib.util

    _routing_policy_path = Path(__file__).with_name("routing_policy.py")
    _routing_policy_spec = importlib.util.spec_from_file_location("task_analyze_routing_policy", _routing_policy_path)
    _routing_policy = importlib.util.module_from_spec(_routing_policy_spec)
    _routing_policy_spec.loader.exec_module(_routing_policy)
    MODEL_EFFORTS = _routing_policy.MODEL_EFFORTS
    parse_model_effort_pair = _routing_policy.parse_model_effort_pair
    pair_text = _routing_policy.pair_text

ROUTE_MARKERS = {"LOCKED_ROUTE_NODE", "ENDING_TASK_WORKER"}
RUNTIME_FAILURES = {"availability", "timeout", "protocol", "telemetry", "execution", "receipt"}
ENTRY_CONTEXT_ENV = "CODEX_TASK_ANALYZE_ENTRY_CONTEXT"
NODE_ROLES = {"entry", "result-producer", "verification", "repair", "ending", "benchmark-baseline"}
DISPATCHER_FIXED_ROLES = {"verification", "repair", "ending"}
_NODE_AUTHORIZATION = contextvars.ContextVar("task_analyze_receipt_node_authorization", default=None)


class ReceiptAuthorizationError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def entry_context_active():
    return ENTRY_CONTEXT_ENV in os.environ


def receipt_node_role(args):
    if getattr(args, "entry_task", False):
        return "entry"
    explicit_role = getattr(args, "node_role", None)
    if explicit_role is not None:
        if explicit_role not in NODE_ROLES - {"entry"}:
            raise ReceiptAuthorizationError("node_role_invalid")
        return explicit_role
    return "ending" if getattr(args, "route_marker", "LOCKED_ROUTE_NODE") == "ENDING_TASK_WORKER" else "result-producer"


@contextmanager
def adaptive_producer_authorization():
    token = _NODE_AUTHORIZATION.set(("adaptive-runner", "result-producer"))
    try:
        yield
    finally:
        _NODE_AUTHORIZATION.reset(token)


@contextmanager
def dispatcher_adaptive_result_authorization():
    token = _NODE_AUTHORIZATION.set(("dispatcher-adaptive-recommendation", "result-producer"))
    try:
        yield
    finally:
        _NODE_AUTHORIZATION.reset(token)


@contextmanager
def dispatcher_node_authorization(node_role):
    if node_role not in DISPATCHER_FIXED_ROLES:
        raise ReceiptAuthorizationError("dispatcher_node_role_invalid")
    token = _NODE_AUTHORIZATION.set(("dispatcher", node_role))
    try:
        yield
    finally:
        _NODE_AUTHORIZATION.reset(token)


def authorize_receipt_run(args):
    node_role = receipt_node_role(args)
    inherited_context_active = entry_context_active()
    if getattr(args, "entry_task", False) and inherited_context_active:
        raise ReceiptAuthorizationError("recursive_entry_task_forbidden")
    context_active = bool(getattr(args, "entry_task", False) or inherited_context_active)
    if getattr(args, "entry_task", False):
        source = "entry-launch"
    elif not context_active:
        source = "outside-entry-context"
    else:
        authorization = _NODE_AUTHORIZATION.get()
        if node_role == "result-producer" and authorization == ("adaptive-runner", "result-producer"):
            source = "adaptive-runner"
        elif node_role == "result-producer" and authorization == ("dispatcher-adaptive-recommendation", "result-producer"):
            source = "dispatcher-adaptive-recommendation"
        elif node_role in DISPATCHER_FIXED_ROLES and authorization == ("dispatcher", node_role):
            source = "dispatcher"
        else:
            raise ReceiptAuthorizationError("entry_context_adaptive_runner_required" if node_role in {"result-producer", "benchmark-baseline"} else "entry_context_dispatcher_authorization_required")
    args._receipt_node_role = node_role
    args._receipt_entry_context_active = context_active
    args._receipt_authorization_source = source
    return {"node_role": node_role, "entry_context_active": context_active, "authorization_status": "authorized", "authorization_source": source}


def receipt_authorization_fields(args, status=None, source=None, reason=None):
    authorization_source = source if source is not None else getattr(args, "_receipt_authorization_source", None)
    authorization_status = status if status is not None else "authorized" if authorization_source is not None else "not-evaluated"
    fields = {"node_role": getattr(args, "_receipt_node_role", receipt_node_role(args)), "entry_context_active": bool(getattr(args, "_receipt_entry_context_active", getattr(args, "entry_task", False) or entry_context_active())), "authorization_status": authorization_status, "authorization_source": authorization_source}
    if reason is not None:
        fields["authorization_reason"] = reason
    return fields


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_fallback_pairs(values):
    if not isinstance(values, list):
        raise ValueError("allow_fallback must be a list")
    pairs = []
    for value in values:
        pair = parse_model_effort_pair(value)
        if pair not in pairs:
            pairs.append(pair)
    return [pair_text(model, effort) for model, effort in pairs]


def infer_failure_class(process, status, turn_completed, turn_failed, model_match, effort_match, pair_match, token_consistent):
    if status == "pass":
        return None
    if process is None:
        return "execution"
    if process.returncode != 0 or turn_failed or not turn_completed:
        return "execution"
    if not model_match or not effort_match or not pair_match:
        return "protocol"
    if not token_consistent:
        return "protocol"
    return "execution"


def route_attempt_summary(
    requested_pair,
    resolved_pair,
    effective_pair,
    status,
    model_match,
    effort_match,
    pair_match,
    process_elapsed_ms,
    task_complete,
    execution_failure_class,
):
    resolved_pair = pair_text(*resolved_pair) if resolved_pair else None
    effective_pair = pair_text(*effective_pair) if effective_pair else None
    if (
        status != "pass"
        and execution_failure_class == "execution"
        and not effective_pair
        and not resolved_pair
    ):
        executed_pair = requested_pair
    else:
        executed_pair = effective_pair or resolved_pair or requested_pair
    return {
        "requested_pair": requested_pair,
        "resolved_pair": resolved_pair,
        "effective_pair": effective_pair,
        "executed_pair": executed_pair,
        "status": "pass" if status == "pass" else "fail",
        "failure_class": execution_failure_class if status != "pass" else None,
        "model_match": bool(model_match),
        "effort_match": bool(effort_match),
        "pair_match": bool(pair_match),
        "process_elapsed_ms": process_elapsed_ms,
        "model_turn_duration_ms": task_complete.get("duration_ms"),
        "time_to_first_token_ms": task_complete.get("time_to_first_token_ms"),
    }


def failed_run_receipt(args, failure_class):
    requested_pair = f"{args.model}|{args.effort}"
    attempt = {
        "requested_pair": requested_pair,
        "resolved_pair": None,
        "effective_pair": None,
        "executed_pair": requested_pair,
        "status": "fail",
        "failure_class": failure_class,
        "model_match": False,
        "effort_match": False,
        "pair_match": False,
        "process_elapsed_ms": None,
        "model_turn_duration_ms": None,
        "time_to_first_token_ms": None,
    }
    receipt = {
        "schema_version": 1,
        "proof_level": "local-operational-not-cryptographic",
        "workload_id": args.workload_id,
        "node_type": "task-analyze-entry" if getattr(args, "entry_task", False) else "locked-route-node",
        "requested_model": args.model,
        "requested_effort": args.effort,
        "requested_pair": requested_pair,
        "resolved_model": None,
        "resolved_effort": None,
        "effective_model": None,
        "effective_pair": None,
        "allowed_fallback_pairs": normalize_fallback_pairs(getattr(args, "allow_fallback", [])),
        "model_match": False,
        "effort_match": False,
        "pair_match": False,
        "tokens": {},
        "metrics_complete": False,
        "tokens_lower_bound": False,
        "process_elapsed_ms": None,
        "turn_completed": False,
        "status": "fail",
        "failure_class": failure_class,
        "route_attempts": [attempt],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "limitations": "Execution failed before complete runtime metadata was available; no model execution success is claimed.",
    }
    receipt.update(receipt_authorization_fields(args))
    return receipt


def rejected_run_receipt(args, error):
    receipt = failed_run_receipt(args, "authorization")
    receipt.update(receipt_authorization_fields(args, status="rejected", source=None, reason=error.code))
    receipt["limitations"] = "Execution was rejected before a model launch because the entry-context node authorization contract was not satisfied."
    return receipt


def parse_stdout_events(stdout_text):
    summary = {"thread_id": None, "usage": {}, "output_hash": None, "turn_completed": False, "turn_failed": False}
    for raw_line in stdout_text.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type == "thread.started":
            summary["thread_id"] = event.get("thread_id")
        elif event_type == "turn.completed":
            summary["usage"] = event.get("usage", {})
            summary["turn_completed"] = True
        elif event_type in {"turn.failed", "error"}:
            summary["turn_failed"] = True
        elif event_type == "item.completed" and isinstance(event.get("item"), dict) and event["item"].get("type") == "agent_message":
            summary["output_hash"] = sha256_text(event["item"].get("text", ""))
    return summary


def extract_last_agent_message(stdout_text):
    last_message = None
    for raw_line in stdout_text.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed" and isinstance(event.get("item"), dict) and event["item"].get("type") == "agent_message":
            last_message = event["item"].get("text", "")
    return last_message


def read_thread_state(state_db_path, thread_id):
    if not state_db_path.exists() or not thread_id:
        return None
    for _ in range(30):
        connection = sqlite3.connect(f"file:{state_db_path}?mode=ro", uri=True)
        row = connection.execute("SELECT rollout_path, model, reasoning_effort, tokens_used, cli_version, model_provider, source FROM threads WHERE id = ?", (thread_id,)).fetchone()
        connection.close()
        if row:
            return {"rollout_path": Path(row[0]), "model": row[1], "effort": row[2], "tokens_used": row[3], "cli_version": row[4], "model_provider": row[5], "source": row[6]}
        time.sleep(0.1)
    return None


def parse_rollout_allowlist(rollout_path):
    observed = {"turn_context": None, "reroutes": [], "usage": None, "task_complete": None, "availability": None}
    if not rollout_path or not rollout_path.exists():
        return observed
    with rollout_path.open(encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if event_type == "turn_context":
                observed["turn_context"] = {"turn_id": payload.get("turn_id"), "model": payload.get("model"), "effort": payload.get("effort")}
            elif event_type == "event_msg" and payload.get("type") == "model_reroute":
                observed["reroutes"].append({"from_model": payload.get("from_model"), "to_model": payload.get("to_model"), "reason": payload.get("reason")})
            elif event_type == "event_msg" and payload.get("type") == "token_count" and isinstance(payload.get("info"), dict):
                observed["usage"] = payload["info"].get("total_token_usage")
            if event_type == "event_msg" and payload.get("type") == "token_count" and isinstance(payload.get("rate_limits"), dict):
                rate_limits = payload["rate_limits"]
                credits = rate_limits.get("credits") if isinstance(rate_limits.get("credits"), dict) else {}
                observed["availability"] = {"limit_id": rate_limits.get("limit_id"), "has_credits": credits.get("has_credits"), "unlimited": credits.get("unlimited"), "rate_limit_reached_type": rate_limits.get("rate_limit_reached_type")}
            elif event_type == "event_msg" and payload.get("type") == "task_complete":
                observed["task_complete"] = {"duration_ms": payload.get("duration_ms"), "time_to_first_token_ms": payload.get("time_to_first_token_ms")}
    return observed


def normalize_usage(usage):
    input_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    cached_input_tokens = usage.get("cached_input_tokens", 0) if isinstance(usage, dict) else None
    output_tokens = usage.get("output_tokens") if isinstance(usage, dict) else None
    reasoning_output_tokens = usage.get("reasoning_output_tokens", 0) if isinstance(usage, dict) else None
    total_tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
    total_tokens = input_tokens + output_tokens if total_tokens is None and input_tokens is not None and output_tokens is not None else total_tokens
    uncached_input_tokens = input_tokens - cached_input_tokens if input_tokens is not None and cached_input_tokens is not None else None
    return {"input_tokens": input_tokens, "cached_input_tokens": cached_input_tokens, "uncached_input_tokens": uncached_input_tokens, "output_tokens": output_tokens, "reasoning_output_tokens": reasoning_output_tokens, "total_tokens": total_tokens}


def run_receipt(args, prompt_text):
    authorization = authorize_receipt_run(args)
    requested_pair_tuple = parse_model_effort_pair(pair_text(args.model, args.effort))
    allowed_fallback_pairs = normalize_fallback_pairs(getattr(args, "allow_fallback", []))
    requested_pair = requested_pair_tuple
    allowed_pairs = [requested_pair] + [parse_model_effort_pair(value) for value in allowed_fallback_pairs]
    command = [args.codex_bin, "exec", "--model", args.model, "-c", f'model_reasoning_effort="{args.effort}"', "--sandbox", args.sandbox, "--skip-git-repo-check", "--json"]
    command.extend(["--ignore-user-config"] if args.ignore_user_config else [])
    command.append("-")
    if args.entry_task:
        execution_prompt = prompt_text
    else:
        marker = getattr(args, "route_marker", "LOCKED_ROUTE_NODE")
        if marker not in ROUTE_MARKERS:
            raise ValueError(f"unsupported route marker {marker}")
        execution_prompt = f"{marker}\nThis is a bounded node from an already-returned Task Analyze route. Execute the assigned node directly; do not restart Task Analyze or redesign the route.\n\n{prompt_text}"
    started = time.perf_counter_ns()
    timed_out = False
    command_environment = None
    if args.entry_task:
        command_environment = os.environ.copy()
        command_environment[ENTRY_CONTEXT_ENV] = "1"
    try:
        process = subprocess.run(command, input=execution_prompt, text=True, cwd=args.workdir, capture_output=True, check=False, shell=False, timeout=args.timeout, **({"env": command_environment} if command_environment is not None else {}))
    except subprocess.TimeoutExpired as error:
        process = None
        timed_out = True
        process_stdout = error.stdout.decode("utf-8", errors="replace") if isinstance(error.stdout, bytes) else error.stdout or ""
        process_stderr = error.stderr.decode("utf-8", errors="replace") if isinstance(error.stderr, bytes) else error.stderr or ""
    else:
        process_stdout = process.stdout.decode("utf-8", errors="replace") if isinstance(process.stdout, bytes) else process.stdout or ""
        process_stderr = process.stderr.decode("utf-8", errors="replace") if isinstance(process.stderr, bytes) else process.stderr or ""
    elapsed_ms = round((time.perf_counter_ns() - started) / 1_000_000)
    stdout_summary = parse_stdout_events(process_stdout)
    thread_state = read_thread_state(args.state_db, stdout_summary["thread_id"])
    rollout = parse_rollout_allowlist(thread_state["rollout_path"] if thread_state else None)
    turn_context = rollout["turn_context"] if rollout.get("turn_context") else {}
    reroutes = rollout["reroutes"]
    has_turn_context = bool(turn_context.get("model") and turn_context.get("effort"))
    if has_turn_context:
        resolved_model = turn_context.get("model")
        resolved_effort = turn_context.get("effort")
        effective_model = reroutes[-1]["to_model"] if reroutes else resolved_model
    else:
        resolved_model = None
        resolved_effort = None
        effective_model = None
    usage = normalize_usage(rollout["usage"] or stdout_summary["usage"])
    allowed_models = {model for model, _ in allowed_pairs}
    allowed_efforts = {effort for _, effort in allowed_pairs}
    model_match = resolved_model in allowed_models
    effort_match = resolved_effort in allowed_efforts
    pair_match = (effective_model, resolved_effort) in allowed_pairs if effective_model and resolved_effort else False
    token_consistent = thread_state is not None and usage["total_tokens"] == thread_state.get("tokens_used")
    status = "pass" if not timed_out and process.returncode == 0 and stdout_summary["turn_completed"] and not stdout_summary["turn_failed"] and pair_match and token_consistent else "fail"
    task_complete = rollout["task_complete"] or {}
    failure_class = "timeout" if timed_out else infer_failure_class(process, status, stdout_summary["turn_completed"], stdout_summary["turn_failed"], model_match, effort_match, pair_match, token_consistent)
    requested_pair = f"{args.model}|{args.effort}"
    attempt = route_attempt_summary(requested_pair=requested_pair, resolved_pair=(resolved_model, resolved_effort) if resolved_model and resolved_effort else None, effective_pair=(effective_model, resolved_effort) if effective_model and resolved_effort else None, status=status, model_match=model_match, effort_match=effort_match, pair_match=pair_match, process_elapsed_ms=elapsed_ms, task_complete=task_complete, execution_failure_class=failure_class)
    if status == "pass":
        failure_class = None
    receipt = {"schema_version": 1, "proof_level": "local-operational-not-cryptographic", "workload_id": args.workload_id, "node_type": "task-analyze-entry" if args.entry_task else "locked-route-node", **authorization, "workload_prompt_sha256": sha256_text(prompt_text), "prompt_sha256": sha256_text(execution_prompt), "output_sha256": stdout_summary["output_hash"], "thread_id": stdout_summary["thread_id"], "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": resolved_model, "resolved_effort": resolved_effort, "effective_model": effective_model, "effective_pair": f"{effective_model}|{resolved_effort}" if effective_model and resolved_effort else None, "reroutes": reroutes, "allowed_fallback_pairs": allowed_fallback_pairs, "model_match": model_match, "effort_match": effort_match, "pair_match": pair_match, "tokens": usage, "metrics_complete": not timed_out and stdout_summary["turn_completed"] and token_consistent, "tokens_lower_bound": timed_out and usage["total_tokens"] is not None, "availability": rollout.get("availability"), "state_tokens_used": (thread_state or {}).get("tokens_used"), "token_total_consistent": token_consistent, "model_turn_duration_ms": task_complete.get("duration_ms"), "time_to_first_token_ms": task_complete.get("time_to_first_token_ms"), "process_elapsed_ms": elapsed_ms, "exit_code": process.returncode if process is not None else None, "turn_completed": False if timed_out else stdout_summary["turn_completed"], "stderr_line_count": len(process_stderr.splitlines()), "cli_version": (thread_state or {}).get("cli_version"), "model_provider": (thread_state or {}).get("model_provider"), "source": (thread_state or {}).get("source"), "status": status, "recorded_at": datetime.now(timezone.utc).isoformat(), "limitations": "Resolved/effective values come from local Codex runtime metadata and reroute events; this is not a cryptographically signed backend attestation."}
    receipt["failure_class"] = failure_class
    receipt["route_attempts"] = [attempt]
    last_message = extract_last_agent_message(process_stdout) if args.result_output and not timed_out else None
    if args.result_output and last_message is not None:
        args.result_output.parent.mkdir(parents=True, exist_ok=True)
        args.result_output.write_text(last_message + "\n", encoding="utf-8")
        receipt["result_output_path"] = str(args.result_output)
    return receipt


def compare_receipts(routed, baseline, acceptance_evidence=None):
    failures = []
    workload_prompt_sha256 = routed.get("workload_prompt_sha256")
    if not workload_prompt_sha256 or workload_prompt_sha256 != baseline.get("workload_prompt_sha256"):
        failures.append("workload prompt hash mismatch")
    if routed.get("workload_id") != baseline.get("workload_id"):
        failures.append("workload ID mismatch")
    if routed.get("status") != "pass" or baseline.get("status") != "pass":
        failures.append("both receipts must pass before comparison")
    output_hash_match = bool(routed.get("output_sha256") and routed.get("output_sha256") == baseline.get("output_sha256"))
    external_acceptance_pass = bool(acceptance_evidence and acceptance_evidence.get("status") == "pass" and acceptance_evidence.get("workload_id") == routed.get("workload_id") and acceptance_evidence.get("same_acceptance_criteria") is True)
    if not output_hash_match and not external_acceptance_pass:
        failures.append("outputs differ and no matching external acceptance evidence passed")
    routed_tokens = routed.get("tokens", {})
    baseline_tokens = baseline.get("tokens", {})
    token_savings = baseline_tokens.get("total_tokens") - routed_tokens.get("total_tokens") if baseline_tokens.get("total_tokens") is not None and routed_tokens.get("total_tokens") is not None else None
    uncached_input_savings = baseline_tokens.get("uncached_input_tokens") - routed_tokens.get("uncached_input_tokens") if baseline_tokens.get("uncached_input_tokens") is not None and routed_tokens.get("uncached_input_tokens") is not None else None
    elapsed_savings_ms = baseline.get("process_elapsed_ms") - routed.get("process_elapsed_ms") if baseline.get("process_elapsed_ms") is not None and routed.get("process_elapsed_ms") is not None else None
    token_savings_percent = round(token_savings / baseline_tokens["total_tokens"] * 100, 2) if token_savings is not None and baseline_tokens.get("total_tokens") else None
    elapsed_savings_percent = round(elapsed_savings_ms / baseline["process_elapsed_ms"] * 100, 2) if elapsed_savings_ms is not None and baseline.get("process_elapsed_ms") else None
    return {"schema_version": 1, "valid_like_for_like_smoke": not failures, "failures": failures, "workload_id": routed.get("workload_id"), "workload_prompt_sha256": workload_prompt_sha256, "acceptance": {"output_hash_match": output_hash_match, "external_evidence_pass": external_acceptance_pass, "evidence_type": "exact-output-hash" if output_hash_match else "external-semantic-verification" if external_acceptance_pass else "missing"}, "routed": {"model": routed.get("effective_model"), "effort": routed.get("resolved_effort"), "total_tokens": routed_tokens.get("total_tokens"), "uncached_input_tokens": routed_tokens.get("uncached_input_tokens"), "process_elapsed_ms": routed.get("process_elapsed_ms")}, "entry_model_leakage_baseline": {"model": baseline.get("effective_model"), "effort": baseline.get("resolved_effort"), "total_tokens": baseline_tokens.get("total_tokens"), "uncached_input_tokens": baseline_tokens.get("uncached_input_tokens"), "process_elapsed_ms": baseline.get("process_elapsed_ms")}, "measured_savings": {"total_tokens": token_savings, "total_tokens_percent": token_savings_percent, "uncached_input_tokens": uncached_input_savings, "process_elapsed_ms": elapsed_savings_ms, "process_elapsed_percent": elapsed_savings_percent}, "interpretation": "Positive savings favor the designed route. Tokens are a usage proxy, not a currency claim. One pair is a smoke result; alternate repeated runs and compare medians for a durable claim."}


def run_command_summary(args, result):
    summary = {"output": str(args.output), "status": result.get("status", "fail")}
    if getattr(args, "emit_result", False) and args.result_output and result.get("status") == "pass" and args.result_output.exists():
        summary["result"] = args.result_output.read_text(encoding="utf-8").rstrip("\n")
    return summary


def parse_args():
    parser = argparse.ArgumentParser(description="Capture sanitized Codex model receipts and compare like-for-like runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--model", choices=sorted(MODEL_EFFORTS), required=True)
    run_parser.add_argument("--effort", required=True)
    run_parser.add_argument("--workload-id", required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--result-output", type=Path, help="Optional task-cache path for the final child result. Raw stdout/stderr are never stored in the receipt.")
    run_parser.add_argument("--emit-result", action="store_true", help="Return the saved final result in the command summary for a bounded parent fast path; never stores it in the receipt.")
    run_parser.add_argument("--workdir", type=Path, default=Path.cwd())
    run_parser.add_argument("--state-db", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "state_5.sqlite")
    run_parser.add_argument("--codex-bin", default="codex")
    run_parser.add_argument("--sandbox", choices=["read-only", "workspace-write", "danger-full-access"], default="read-only")
    run_parser.add_argument("--allow-fallback", action="append", default=[])
    run_parser.add_argument("--ignore-user-config", action="store_true")
    run_parser.add_argument("--entry-task", action="store_true", help="Use only when capturing the Task Analyze entry itself; downstream nodes receive the LOCKED_ROUTE_NODE marker by default.")
    run_parser.add_argument("--route-marker", choices=sorted(ROUTE_MARKERS), default="LOCKED_ROUTE_NODE")
    run_parser.add_argument("--timeout", type=int, default=900)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--routed", type=Path, required=True)
    compare_parser.add_argument("--baseline", type=Path, required=True)
    compare_parser.add_argument("--acceptance-evidence", type=Path)
    compare_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "run":
        prompt_text = sys.stdin.read()
        if not prompt_text.strip():
            raise SystemExit("prompt must be supplied on stdin")
        try:
            result = run_receipt(args, prompt_text)
        except ReceiptAuthorizationError as error:
            result = rejected_run_receipt(args, error)
        except subprocess.TimeoutExpired:
            result = failed_run_receipt(args, "timeout")
        except OSError:
            result = failed_run_receipt(args, "execution")
    else:
        acceptance_evidence = json.loads(args.acceptance_evidence.read_text(encoding="utf-8")) if args.acceptance_evidence else None
        result = compare_receipts(json.loads(args.routed.read_text(encoding="utf-8")), json.loads(args.baseline.read_text(encoding="utf-8")), acceptance_evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run_command_summary(args, result) if args.command == "run" else {"output": str(args.output), "status": "pass" if result.get("valid_like_for_like_smoke") else "fail"}))
    return 0 if result.get("status", "pass" if result.get("valid_like_for_like_smoke") else "fail") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

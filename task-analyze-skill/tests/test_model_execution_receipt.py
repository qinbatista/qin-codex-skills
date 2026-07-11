#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "model_execution_receipt.py"
MODULE_SPEC = importlib.util.spec_from_file_location("model_execution_receipt", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class ModelExecutionReceiptTests(unittest.TestCase):
    def test_parse_stdout_uses_only_safe_summary_fields(self):
        stdout_text = "\n".join([json.dumps({"type": "thread.started", "thread_id": "thread-1"}), json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "secret response text"}}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 10, "reasoning_output_tokens": 2}})])
        summary = module.parse_stdout_events(stdout_text)
        self.assertEqual(summary["thread_id"], "thread-1")
        self.assertTrue(summary["turn_completed"])
        self.assertEqual(summary["usage"]["input_tokens"], 100)
        self.assertEqual(summary["output_hash"], module.sha256_text("secret response text"))
        self.assertNotIn("secret response text", json.dumps(summary))

    def test_raw_result_extraction_is_separate_from_sanitized_summary(self):
        stdout_text = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "result kept only when requested"}})
        self.assertEqual(module.extract_last_agent_message(stdout_text), "result kept only when requested")
        self.assertNotIn("result kept only when requested", json.dumps(module.parse_stdout_events(stdout_text)))

    def test_parse_rollout_allowlist_reads_resolved_model_reroute_tokens_and_timing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rollout_path = Path(temp_dir) / "rollout.jsonl"
            events = [{"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "gpt-5.6-terra", "effort": "high", "base_instructions": "do not copy"}}, {"type": "event_msg", "payload": {"type": "model_reroute", "from_model": "gpt-5.6-terra", "to_model": "gpt-5.6-luna", "reason": "allowed fallback"}}, {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 120, "cached_input_tokens": 20, "output_tokens": 30, "reasoning_output_tokens": 10, "total_tokens": 150}}, "rate_limits": {"limit_id": "premium", "credits": {"has_credits": True, "unlimited": False}, "rate_limit_reached_type": None}}}, {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 420, "time_to_first_token_ms": 40}}]
            rollout_path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
            observed = module.parse_rollout_allowlist(rollout_path)
        self.assertEqual(observed["turn_context"], {"turn_id": "turn-1", "model": "gpt-5.6-terra", "effort": "high"})
        self.assertEqual(observed["reroutes"][-1]["to_model"], "gpt-5.6-luna")
        self.assertEqual(observed["usage"]["total_tokens"], 150)
        self.assertEqual(observed["task_complete"]["time_to_first_token_ms"], 40)
        self.assertEqual(observed["availability"]["limit_id"], "premium")
        self.assertTrue(observed["availability"]["has_credits"])
        self.assertNotIn("base_instructions", json.dumps(observed))

    def test_run_receipt_requests_exact_model_and_effort_over_stdin(self):
        stdout_text = "\n".join([json.dumps({"type": "thread.started", "thread_id": "thread-1"}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 10, "reasoning_output_tokens": 2}})])
        process = SimpleNamespace(stdout=stdout_text, stderr="one warning\n", returncode=0)
        thread_state = {"rollout_path": Path("/tmp/rollout"), "model": "gpt-5.3-codex-spark", "effort": "high", "tokens_used": 110, "cli_version": "test", "model_provider": "openai", "source": "exec"}
        rollout = {"turn_context": {"turn_id": "turn-1", "model": "gpt-5.3-codex-spark", "effort": "high"}, "reroutes": [], "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 10, "reasoning_output_tokens": 2, "total_tokens": 110}, "task_complete": {"duration_ms": 300, "time_to_first_token_ms": 100}}
        args = argparse.Namespace(model="gpt-5.3-codex-spark", effort="high", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="same-work", allow_fallback=[])
        with patch.object(module.subprocess, "run", return_value=process) as run_mock, patch.object(module, "read_thread_state", return_value=thread_state), patch.object(module, "parse_rollout_allowlist", return_value=rollout):
            receipt = module.run_receipt(args, "same prompt")
        command = run_mock.call_args.args[0]
        self.assertIn("gpt-5.3-codex-spark", command)
        self.assertIn('model_reasoning_effort="high"', command)
        self.assertEqual(command[-1], "-")
        self.assertTrue(run_mock.call_args.kwargs["input"].startswith("LOCKED_ROUTE_NODE"))
        self.assertTrue(run_mock.call_args.kwargs["input"].endswith("same prompt"))
        self.assertTrue(run_mock.call_args.kwargs["shell"] is False)
        self.assertEqual(receipt["status"], "pass")
        self.assertTrue(receipt["model_match"])
        self.assertTrue(receipt["effort_match"])

    def test_run_receipt_includes_sanitized_route_attempt_metadata(self):
        stdout_text = "\n".join([
            json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "secret response text"}},
            ),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 101, "cached_input_tokens": 1, "output_tokens": 9, "reasoning_output_tokens": 0}}),
        ])
        process = SimpleNamespace(stdout=stdout_text, stderr="", returncode=0)
        thread_state = {"rollout_path": Path("/tmp/rollout"), "model": "gpt-5.6-luna", "effort": "low", "tokens_used": 110, "cli_version": "test", "model_provider": "openai", "source": "exec"}
        rollout = {"turn_context": {"turn_id": "turn-2", "model": "gpt-5.6-luna", "effort": "low"}, "reroutes": [], "usage": {"input_tokens": 101, "cached_input_tokens": 1, "output_tokens": 9, "reasoning_output_tokens": 0, "total_tokens": 110}, "task_complete": {"duration_ms": 200, "time_to_first_token_ms": 20}}
        args = argparse.Namespace(model="gpt-5.6-luna", effort="low", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="route-attempt", allow_fallback=[])
        with patch.object(module.subprocess, "run", return_value=process) as run_mock, patch.object(module, "read_thread_state", return_value=thread_state), patch.object(module, "parse_rollout_allowlist", return_value=rollout):
            receipt = module.run_receipt(args, "same prompt")
        self.assertEqual(run_mock.call_args.args[0], ["codex", "exec", "--model", "gpt-5.6-luna", "-c", "model_reasoning_effort=\"low\"", "--sandbox", "read-only", "--skip-git-repo-check", "--json", "--ignore-user-config", "-"])
        attempt = receipt["route_attempts"][0]
        self.assertEqual(attempt["requested_pair"], "gpt-5.6-luna|low")
        self.assertEqual(attempt["resolved_pair"], "gpt-5.6-luna|low")
        self.assertEqual(attempt["effective_pair"], "gpt-5.6-luna|low")
        self.assertEqual(attempt["executed_pair"], "gpt-5.6-luna|low")
        self.assertEqual(attempt["status"], "pass")
        self.assertIsNone(attempt["failure_class"])
        self.assertTrue(attempt["model_match"])
        self.assertTrue(attempt["effort_match"])
        self.assertEqual(attempt["pair_match"], True)
        self.assertNotIn("secret response text", json.dumps(attempt))

    def test_run_receipt_marks_execution_failure_class_when_runtime_fails_before_resolution(self):
        stdout_text = json.dumps({"type": "thread.started", "thread_id": "thread-1"})
        process = SimpleNamespace(stdout=stdout_text, stderr="boom", returncode=1)
        thread_state = {"rollout_path": Path("/tmp/rollout"), "model": "gpt-5.3-codex-spark", "effort": "low", "tokens_used": 110, "cli_version": "test", "model_provider": "openai", "source": "exec"}
        rollout = {"turn_context": {}, "reroutes": [], "usage": {}, "task_complete": {}}
        args = argparse.Namespace(model="gpt-5.3-codex-spark", effort="low", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="runtime-fail", allow_fallback=[])
        with patch.object(module.subprocess, "run", return_value=process) as run_mock, patch.object(module, "read_thread_state", return_value=thread_state), patch.object(module, "parse_rollout_allowlist", return_value=rollout):
            receipt = module.run_receipt(args, "same prompt")
        self.assertEqual(run_mock.call_args.args[0][0], "codex")
        attempt = receipt["route_attempts"][0]
        self.assertEqual(attempt["status"], "fail")
        self.assertEqual(attempt["failure_class"], "execution")
        self.assertEqual(attempt["requested_pair"], "gpt-5.3-codex-spark|low")
        self.assertIsNone(attempt["resolved_pair"])
        self.assertIsNone(attempt["effective_pair"])
        self.assertIsNone(receipt["resolved_model"])
        self.assertIsNone(receipt["effective_model"])
        self.assertFalse(attempt["model_match"])
        self.assertFalse(attempt["effort_match"])
        self.assertFalse(attempt["pair_match"])
        self.assertNotIn("boom", json.dumps(attempt))

    def test_run_receipt_ignores_stale_thread_state_when_rollout_missing_turn_context(self):
        stdout_text = json.dumps({"type": "thread.started", "thread_id": "thread-1"})
        process = SimpleNamespace(stdout=stdout_text, stderr="boom", returncode=1)
        thread_state = {"rollout_path": Path("/tmp/rollout"), "model": "gpt-5.3-codex-spark", "effort": "low", "tokens_used": 110, "cli_version": "test", "model_provider": "openai", "source": "exec"}
        rollout = {"turn_context": {}, "reroutes": [], "usage": {}, "task_complete": {}}
        args = argparse.Namespace(model="gpt-5.6-terra", effort="low", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="runtime-fail-stale", allow_fallback=[])
        with patch.object(module.subprocess, "run", return_value=process), patch.object(module, "read_thread_state", return_value=thread_state), patch.object(module, "parse_rollout_allowlist", return_value=rollout):
            receipt = module.run_receipt(args, "same prompt")
        attempt = receipt["route_attempts"][0]
        self.assertIsNone(attempt["resolved_pair"])
        self.assertIsNone(attempt["effective_pair"])
        self.assertIsNone(receipt["resolved_model"])
        self.assertIsNone(receipt["effective_model"])
        self.assertEqual(attempt["status"], "fail")
        self.assertFalse(receipt["turn_completed"])
        self.assertEqual(attempt["executed_pair"], "gpt-5.6-terra|low")

    def test_failed_run_receipt_is_sanitized_and_does_not_claim_execution(self):
        args = argparse.Namespace(
            model="gpt-5.6-luna",
            effort="high",
            workload_id="timeout-proof",
            entry_task=False,
            allow_fallback=["gpt-5.6-terra|medium"],
        )
        receipt = module.failed_run_receipt(args, "timeout")
        self.assertEqual(receipt["status"], "fail")
        self.assertEqual(receipt["failure_class"], "timeout")
        self.assertIsNone(receipt["effective_model"])
        self.assertFalse(receipt["turn_completed"])
        self.assertFalse(receipt["metrics_complete"])
        self.assertFalse(receipt["tokens_lower_bound"])
        self.assertEqual(receipt["route_attempts"][0]["executed_pair"], "gpt-5.6-luna|high")
        self.assertNotIn("error", json.dumps(receipt).lower())

    def test_run_receipt_preserves_sanitized_timeout_telemetry_from_partial_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_output = Path(temp_dir) / "partial-result.md"
            partial_stdout = "\n".join([json.dumps({"type": "thread.started", "thread_id": "thread-timeout"}), json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "secret partial response"}}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 70, "output_tokens": 30, "total_tokens": 100}})])
            timeout_error = module.subprocess.TimeoutExpired(["codex", "exec"], 30, output=partial_stdout.encode("utf-8"), stderr=b"private stderr")
            thread_state = {"rollout_path": Path(temp_dir) / "rollout.jsonl", "model": "gpt-5.6-luna", "effort": "low", "tokens_used": 125, "cli_version": "test", "model_provider": "openai", "source": "exec"}
            rollout = {"turn_context": {"turn_id": "turn-timeout", "model": "gpt-5.6-luna", "effort": "low"}, "reroutes": [{"from_model": "gpt-5.6-luna", "to_model": "gpt-5.6-terra", "reason": "capacity"}], "usage": {"input_tokens": 80, "cached_input_tokens": 5, "output_tokens": 45, "reasoning_output_tokens": 12, "total_tokens": 125}, "task_complete": {"duration_ms": 900, "time_to_first_token_ms": 30}}
            args = argparse.Namespace(model="gpt-5.6-luna", effort="low", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, result_output=result_output, timeout=30, workdir=Path(temp_dir), state_db=Path(temp_dir) / "state.sqlite", workload_id="timeout-work", allow_fallback=["gpt-5.6-terra|low"])
            with patch.object(module.subprocess, "run", side_effect=timeout_error), patch.object(module, "read_thread_state", return_value=thread_state) as read_state, patch.object(module, "parse_rollout_allowlist", return_value=rollout):
                receipt = module.run_receipt(args, "confidential prompt")
        self.assertEqual(read_state.call_args.args[1], "thread-timeout")
        self.assertEqual(receipt["status"], "fail")
        self.assertEqual(receipt["failure_class"], "timeout")
        self.assertFalse(receipt["turn_completed"])
        self.assertFalse(receipt["metrics_complete"])
        self.assertTrue(receipt["tokens_lower_bound"])
        self.assertEqual(receipt["tokens"]["total_tokens"], 125)
        self.assertEqual(receipt["resolved_model"], "gpt-5.6-luna")
        self.assertEqual(receipt["effective_model"], "gpt-5.6-terra")
        self.assertEqual(receipt["route_attempts"][0]["failure_class"], "timeout")
        self.assertEqual(receipt["workload_prompt_sha256"], module.sha256_text("confidential prompt"))
        self.assertGreaterEqual(receipt["process_elapsed_ms"], 0)
        self.assertFalse(result_output.exists())
        self.assertNotIn("secret partial response", json.dumps(receipt))
        self.assertNotIn("private stderr", json.dumps(receipt))
        self.assertNotIn("confidential prompt", json.dumps(receipt))

    def test_compare_receipts_reports_positive_savings_for_routed_run(self):
        routed = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "same-workload", "prompt_sha256": "wrapper-a", "output_sha256": "same-output", "effective_model": "gpt-5.3-codex-spark", "resolved_effort": "high", "process_elapsed_ms": 800, "tokens": {"total_tokens": 120, "uncached_input_tokens": 80}}
        baseline = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "same-workload", "prompt_sha256": "wrapper-b", "output_sha256": "same-output", "effective_model": "gpt-5.6-sol", "resolved_effort": "ultra", "process_elapsed_ms": 1400, "tokens": {"total_tokens": 200, "uncached_input_tokens": 130}}
        comparison = module.compare_receipts(routed, baseline)
        self.assertTrue(comparison["valid_like_for_like_smoke"])
        self.assertEqual(comparison["measured_savings"]["total_tokens"], 80)
        self.assertEqual(comparison["measured_savings"]["process_elapsed_ms"], 600)

    def test_compare_receipts_rejects_different_workload_prompt_hashes(self):
        routed = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "a", "output_sha256": "same-output", "tokens": {}}
        baseline = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "b", "output_sha256": "same-output", "tokens": {}}
        comparison = module.compare_receipts(routed, baseline)
        self.assertFalse(comparison["valid_like_for_like_smoke"])
        self.assertIn("workload prompt hash mismatch", comparison["failures"])

    def test_compare_receipts_accepts_external_semantic_verification(self):
        routed = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "same-hash", "output_sha256": "output-a", "process_elapsed_ms": 80, "tokens": {"total_tokens": 12, "uncached_input_tokens": 8}}
        baseline = {"status": "pass", "workload_id": "same-work", "workload_prompt_sha256": "same-hash", "output_sha256": "output-b", "process_elapsed_ms": 100, "tokens": {"total_tokens": 20, "uncached_input_tokens": 10}}
        evidence = {"status": "pass", "workload_id": "same-work", "same_acceptance_criteria": True}
        comparison = module.compare_receipts(routed, baseline, evidence)
        self.assertTrue(comparison["valid_like_for_like_smoke"])
        self.assertEqual(comparison["acceptance"]["evidence_type"], "external-semantic-verification")

    def test_run_command_summary_emits_result_only_when_explicit_and_passed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.md"
            result_path.write_text("bounded result\n", encoding="utf-8")
            args = argparse.Namespace(output=Path(temp_dir) / "receipt.json", result_output=result_path, emit_result=True)
            summary = module.run_command_summary(args, {"status": "pass"})
            self.assertEqual(summary["result"], "bounded result")
            args.emit_result = False
            self.assertNotIn("result", module.run_command_summary(args, {"status": "pass"}))
            args.emit_result = True
            self.assertNotIn("result", module.run_command_summary(args, {"status": "fail"}))

    def test_entry_launch_installs_inherited_context_marker(self):
        stdout_text = "\n".join([json.dumps({"type": "thread.started", "thread_id": "entry-thread"}), json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 2, "reasoning_output_tokens": 0}})])
        process = SimpleNamespace(stdout=stdout_text, stderr="", returncode=0)
        thread_state = {"rollout_path": Path("/tmp/entry-rollout"), "model": "gpt-5.6-sol", "effort": "ultra", "tokens_used": 12, "cli_version": "test", "model_provider": "openai", "source": "exec"}
        rollout = {"turn_context": {"turn_id": "entry-turn", "model": "gpt-5.6-sol", "effort": "ultra"}, "reroutes": [], "usage": {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 2, "reasoning_output_tokens": 0, "total_tokens": 12}, "task_complete": {"duration_ms": 5, "time_to_first_token_ms": 1}}
        args = argparse.Namespace(model="gpt-5.6-sol", effort="ultra", codex_bin="codex", sandbox="read-only", ignore_user_config=False, entry_task=True, result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="entry-marker", allow_fallback=[])
        with patch.dict(os.environ, {}, clear=False), patch.object(module.subprocess, "run", return_value=process) as run_mock, patch.object(module, "read_thread_state", return_value=thread_state), patch.object(module, "parse_rollout_allowlist", return_value=rollout):
            os.environ.pop(module.ENTRY_CONTEXT_ENV, None)
            receipt = module.run_receipt(args, "entry task")
        self.assertEqual(run_mock.call_args.kwargs["env"][module.ENTRY_CONTEXT_ENV], "1")
        self.assertEqual(receipt["node_role"], "entry")
        self.assertTrue(receipt["entry_context_active"])
        self.assertEqual(receipt["authorization_source"], "entry-launch")

    def test_direct_result_producer_is_rejected_inside_entry_context(self):
        args = argparse.Namespace(model="gpt-5.6-terra", effort="high", codex_bin="codex", sandbox="read-only", ignore_user_config=True, entry_task=False, route_marker="LOCKED_ROUTE_NODE", result_output=None, timeout=30, workdir=Path("/tmp"), state_db=Path("/tmp/state.sqlite"), workload_id="blocked-fixed-result", allow_fallback=[])
        with patch.dict(os.environ, {module.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module.subprocess, "run") as run_mock:
            with self.assertRaisesRegex(module.ReceiptAuthorizationError, "entry_context_adaptive_runner_required") as raised:
                module.run_receipt(args, "private bounded prompt")
            rejected = module.rejected_run_receipt(args, raised.exception)
        run_mock.assert_not_called()
        self.assertEqual(rejected["status"], "fail")
        self.assertEqual(rejected["failure_class"], "authorization")
        self.assertEqual(rejected["authorization_status"], "rejected")
        self.assertEqual(rejected["authorization_reason"], "entry_context_adaptive_runner_required")
        self.assertNotIn("private bounded prompt", json.dumps(rejected))
        self.assertNotIn(module.ENTRY_CONTEXT_ENV, json.dumps(rejected))

    def test_recursive_entry_flag_cannot_bypass_entry_context_guard(self):
        args = argparse.Namespace(entry_task=True, route_marker="LOCKED_ROUTE_NODE")
        with patch.dict(os.environ, {module.ENTRY_CONTEXT_ENV: "1"}, clear=False):
            with self.assertRaisesRegex(module.ReceiptAuthorizationError, "recursive_entry_task_forbidden"):
                module.authorize_receipt_run(args)

    def test_fixed_result_baseline_remains_authorized_outside_entry_context(self):
        args = argparse.Namespace(entry_task=False, route_marker="LOCKED_ROUTE_NODE")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(module.ENTRY_CONTEXT_ENV, None)
            authorization = module.authorize_receipt_run(args)
        self.assertEqual(authorization["node_role"], "result-producer")
        self.assertEqual(authorization["authorization_source"], "outside-entry-context")
        self.assertFalse(authorization["entry_context_active"])

    def test_dispatcher_fixed_roles_require_matching_in_process_authorization(self):
        with patch.dict(os.environ, {module.ENTRY_CONTEXT_ENV: "1"}, clear=False):
            for node_role in sorted(module.DISPATCHER_FIXED_ROLES):
                args = argparse.Namespace(entry_task=False, node_role=node_role, route_marker="LOCKED_ROUTE_NODE")
                with self.assertRaises(module.ReceiptAuthorizationError):
                    module.authorize_receipt_run(args)
                with module.dispatcher_node_authorization(node_role):
                    authorization = module.authorize_receipt_run(args)
                self.assertEqual(authorization["authorization_source"], "dispatcher")
                self.assertEqual(authorization["node_role"], node_role)


if __name__ == "__main__":
    unittest.main()

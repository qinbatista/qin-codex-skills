#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "adaptive_model_runner.py"
MODULE_SPEC = importlib.util.spec_from_file_location("adaptive_model_runner", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


CONDITION = {
    "task_family": "grounded",
    "artifact": "answer",
    "scope": "single",
    "ambiguity": "low",
    "modality": "text",
    "risk": "low",
    "complexity": "easy",
    "project_family": "global",
    "verification_shape": "real",
    "owning_skill": "workflow-skill",
    "execution_domain": "general",
}
SUMMARY = "Return one bounded grounded answer with deterministic JSON proof."
FINGERPRINT = "f" * 64


def recommendation(pair="gpt-5.6-terra|max", reason="verified_quality_boundary", trial=False):
    model, effort = pair.split("|")
    return {
        "selected_pair": pair,
        "selected_model": model,
        "selected_effort": effort,
        "trial": trial,
        "reason": reason,
        "profile_fingerprint": FINGERPRINT,
        "calibration_state": "frozen",
    }


def arguments(root, ladder=None, static="gpt-5.6-terra|medium", hard="gpt-5.6-luna|low"):
    ladder = ladder or ["gpt-5.6-luna|low", "gpt-5.6-terra|medium", "gpt-5.6-terra|max", "gpt-5.6-sol|max"]
    values = dict(
        **CONDITION,
        task_summary=SUMMARY,
        candidate_ladder=ladder,
        static_suggestion=static,
        hard_floor=hard,
        history=root / "history.json",
        workload_id="adaptive-test",
        receipt_output=root / "receipt.json",
        result_output=root / "result.json",
        workdir=root,
        state_db=root / "state.sqlite",
        codex_bin="codex",
        sandbox="read-only",
        timeout=30,
        ignore_user_config=True,
        allow_fallback=[],
        performance_history=root / "strategy-performance.json",
        entry_pair=None,
        config_cohort=None,
        strategy_version=None,
        producer_contract_version=None,
        minimum_paired_samples=6,
        minimum_savings_percent=5.0,
        benchmark_calibration=True,
    )
    return SimpleNamespace(**values)


def fake_receipt_run(secret_result='{"answer":"ok"}', thread_id="private-session-id"):
    def run(receipt_args, prompt_text):
        receipt_args.result_output.write_text(secret_result + "\n", encoding="utf-8")
        return {
            "schema_version": 1,
            "node_type": "locked-route-node",
            "status": "pass",
            "failure_class": None,
            "turn_completed": True,
            "exit_code": 0,
            "metrics_complete": True,
            "model_match": True,
            "effort_match": True,
            "pair_match": True,
            "requested_model": receipt_args.model,
            "requested_effort": receipt_args.effort,
            "requested_pair": f"{receipt_args.model}|{receipt_args.effort}",
            "resolved_model": receipt_args.model,
            "resolved_effort": receipt_args.effort,
            "effective_model": receipt_args.model,
            "effective_pair": f"{receipt_args.model}|{receipt_args.effort}",
            "output_sha256": hashlib.sha256(secret_result.encode("utf-8")).hexdigest(),
            "workload_prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            "tokens": {"total_tokens": 123},
            "process_elapsed_ms": 456,
            "result_published": True,
            "result_ready_monotonic_ns": time.monotonic_ns(),
            "result_output_path": str(receipt_args.result_output),
            "thread_id": thread_id,
        }
    return run


class AdaptiveModelRunnerTests(unittest.TestCase):
    def test_missing_performance_admission_returns_inline_without_model_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.benchmark_calibration = False
            with patch.object(module, "_validated_recommendation", return_value=(recommendation(), ("gpt-5.6-terra", "max"))), patch.object(module.model_execution_receipt, "run_receipt") as execute:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "inline")
        self.assertEqual(summary["execution_mode"], "inline_entry")
        execute.assert_not_called()

    def test_admitted_frozen_pair_launches_one_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.benchmark_calibration = False
            args.entry_pair = "gpt-5.6-sol|ultra"
            args.config_cohort = "c" * 64
            args.strategy_version = "inline-v1"
            args.producer_contract_version = "producer-v1"
            admission = {"schema_version": 1, "execution_mode": "delegated_adaptive", "reason": "repeated_end_to_end_pareto_win", "admitted": True}
            with patch.object(module, "_validated_recommendation", return_value=(recommendation(), ("gpt-5.6-terra", "max"))), patch.object(module.strategy_performance, "recommend_mode", return_value=admission), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()) as execute:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["execution_mode"], "delegated_adaptive")
        execute.assert_called_once()

    def test_concise_complex_preset_resolves_exact_calibrated_profile(self):
        args = module.parse_args(["--profile-preset", "grounded-repository-answer-complex", "--project-family", "museai", "--owning-skill", "muse-ai-plugin:muse-ai-dev-skill", "--task-summary", SUMMARY, "--workload-id", "preset-test", "--receipt-output", "cache/preset-receipt.json", "--result-output", "cache/preset-result.json"])
        self.assertEqual(args.task_family, "grounded")
        self.assertEqual(args.artifact, "answer")
        self.assertEqual(args.scope, "multi")
        self.assertEqual(args.execution_domain, "general")
        self.assertEqual(args.static_suggestion, "gpt-5.6-terra|high")
        self.assertEqual(args.hard_floor, "gpt-5.6-luna|low")
        self.assertEqual(args.candidate_ladder, module.model_routing_history.normal_adaptive_pair_texts())

    def test_frozen_sol_max_is_executed_instead_of_terra_static(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.candidate_ladder = module.model_routing_history.adaptive_pair_texts_for_profile(
                args.task_family, args.modality, args.risk, args.complexity, args.ambiguity
            )
            condition = module.model_routing_history.validate_condition(vars(args))
            pairs = module.model_routing_history.canonical_pairs(args.candidate_ladder)
            static_pair = module.model_routing_history.parse_pair(args.static_suggestion)
            hard_pair = module.model_routing_history.parse_pair(args.hard_floor)
            selected_pair = ("gpt-5.6-sol", "max")
            history = module.model_routing_history.empty_history()
            history["conditions"][module.model_routing_history.condition_key(condition)] = {
                "condition": condition,
                "summary": SUMMARY,
                "candidate_ladder": args.candidate_ladder,
                "static_suggestion": args.static_suggestion,
                "hard_floor": args.hard_floor,
                "success_model": "gpt-5.6-sol|max",
                "failed_model": None,
                "active_ladder_fingerprint": module.model_routing_history.ladder_fingerprint(pairs, hard_pair),
                "profile_fingerprint": module.model_routing_history.profile_fingerprint(condition, pairs, static_pair, hard_pair),
                "calibration_state": "frozen",
                "best_pair": "gpt-5.6-sol|max",
                "selection_basis": "quality_boundary",
                "cost_evidence": {"status": "not_evaluated", "compared_pairs": [], "shared_cohort_count": 0, "shared_cohort_digest": None, "scores": {}},
                "tasks": [{
                    "run_id": "run-frozen",
                    "summary": SUMMARY,
                    "requested_pair": "gpt-5.6-sol|max",
                    "resolved_pair": "gpt-5.6-sol|max",
                    "effective_pair": "gpt-5.6-sol|max",
                    "executed_pair": "gpt-5.6-sol|max",
                    "operational_failure_pairs": [],
                    "receipt_status": "pass",
                    "real_status": "pass",
                    "effective_verdict": "pass",
                    "allowlisted_failure_class": "none",
                    "turn_completed": True,
                    "model_match": True,
                    "effort_match": True,
                    "trial": False,
                    "workload_prompt_sha256": "a" * 64,
                    "token_totals": {"input": 10, "cached_input": 0, "output": 2, "reasoning_output": 0, "total": 12},
                    "process_ms": 5,
                    "recorded_at": "2026-07-10T00:00:00+00:00",
                }],
            }
            args.history.write_text(json.dumps(history), encoding="utf-8")
            calls = []

            def capture(receipt_args, prompt_text):
                calls.append((receipt_args.model, receipt_args.effort))
                return fake_receipt_run()(receipt_args, prompt_text)

            with patch.object(module.model_execution_receipt, "run_receipt", side_effect=capture):
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["selected_pair"], "gpt-5.6-sol|max")
        self.assertEqual(calls, [("gpt-5.6-sol", "max")])

    def test_empty_history_uses_static_suggestion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.candidate_ladder = module.model_routing_history.adaptive_pair_texts_for_profile(
                args.task_family, args.modality, args.risk, args.complexity, args.ambiguity
            )
            args.static_suggestion = "gpt-5.6-terra|medium"
            args.hard_floor = "gpt-5.6-luna|low"
            selected = []

            def capture(receipt_args, prompt_text):
                selected.append(f"{receipt_args.model}|{receipt_args.effort}")
                return fake_receipt_run()(receipt_args, prompt_text)

            with patch.object(module.model_execution_receipt, "run_receipt", side_effect=capture):
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["reason"], "no_bounds_use_static")
        self.assertEqual(selected, ["gpt-5.6-terra|medium"])

    def test_missing_selected_pair_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = arguments(Path(temporary))
            bad = recommendation()
            bad.update(selected_pair=None, selected_model=None, selected_effort=None)
            with patch.object(module.model_routing_history, "recommend_route", return_value=bad), patch.object(module.model_execution_receipt, "run_receipt") as execute:
                with self.assertRaisesRegex(module.RunnerFailure, "recommendation_invalid"):
                    module.run_adaptive(args, "bounded prompt")
        execute.assert_not_called()

    def test_success_publishes_result_without_foreground_verification_or_learning(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()) as execute, patch.object(module.model_routing_history, "record_event") as record:
                summary = module.run_adaptive(args, "bounded prompt")
            published_result = args.result_output.read_text(encoding="utf-8")
            receipt = json.loads(args.receipt_output.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["real_verify_status"], "pending")
        self.assertEqual(published_result, '{"answer":"ok"}\n')
        self.assertNotIn("mini_status", receipt)
        execute.assert_called_once()
        record.assert_not_called()

    def test_public_result_is_ready_before_delayed_receipt_finishes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            ready_event = threading.Event()
            ready_records = []

            def controller_ready(result_path, ready_ns):
                ready_records.append((str(result_path), ready_ns))
                ready_event.set()

            args.result_ready_callback = controller_ready

            def delayed_receipt(receipt_args, prompt_text):
                receipt = fake_receipt_run()(receipt_args, prompt_text)
                receipt_args.result_ready_callback(receipt_args.result_output, receipt["result_ready_monotonic_ns"])
                time.sleep(0.15)
                return receipt

            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=delayed_receipt), ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(module.run_adaptive, args, "bounded prompt")
                self.assertTrue(ready_event.wait(timeout=1))
                published_result = args.result_output.read_text(encoding="utf-8")
                self.assertFalse(future.done())
                summary = future.result(timeout=2)
        self.assertEqual(published_result, '{"answer":"ok"}\n')
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["result_published"])
        self.assertEqual(ready_records[0][0], str(args.result_output))
        self.assertIsInstance(summary["first_result_elapsed_ms"], int)
        self.assertLess(summary["first_result_elapsed_ms"], 100)

    def test_receipt_failure_after_presentation_requires_notification_and_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)

            def failed_after_result(receipt_args, _prompt_text):
                receipt_args.result_output.write_text('{"answer":"presented"}\n', encoding="utf-8")
                return {"status": "fail", "requested_pair": f"{receipt_args.model}|{receipt_args.effort}", "failure_class": "protocol", "tokens": {"total_tokens": 9}, "process_elapsed_ms": 150, "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "result_output_path": str(receipt_args.result_output), "duplicate_result_detected": True}

            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=failed_after_result):
                summary = module.run_adaptive(args, "bounded prompt")
            presented_result = args.result_output.read_text(encoding="utf-8")
        self.assertEqual(presented_result, '{"answer":"presented"}\n')
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["reason"], "producer_receipt_failure_after_result")
        self.assertTrue(summary["result_published"])
        self.assertTrue(summary["notification_required"])
        self.assertTrue(summary["reopen_required"])

    def test_adaptive_run_id_is_stable_without_a_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()):
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertTrue(summary["adaptive_run_id"].startswith("run_"))
        self.assertEqual(summary["adaptive_run_id"], args.adaptive_run_id)

    def test_emit_result_returns_only_passing_result_and_never_adds_it_to_receipt(self):
        secret_result = '{"answer":"bounded-parent-result"}'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.emit_result = True
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run(secret_result)):
                summary = module.run_adaptive(args, "bounded prompt")
            receipt_text = args.receipt_output.read_text(encoding="utf-8")
        self.assertEqual(summary["result"], secret_result)
        self.assertNotIn("bounded-parent-result", receipt_text)

    def test_operational_failure_is_not_recorded_as_quality(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.result_output.write_text("stale result\n", encoding="utf-8")
            failed = {"status": "fail", "requested_pair": "gpt-5.6-terra|max", "failure_class": "timeout", "tokens": {"total_tokens": 9}, "process_elapsed_ms": 30}
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", return_value=failed), patch.object(module.model_routing_history, "record_event") as record:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["reason"], "producer_operational_failure")
        record.assert_not_called()
        self.assertFalse(args.result_output.exists())

    def test_prompt_absence_fails_before_recommendation_or_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = arguments(Path(temporary))
            with patch.object(module.model_routing_history, "recommend_route") as recommend, patch.object(module.model_execution_receipt, "run_receipt") as execute:
                with self.assertRaisesRegex(module.RunnerFailure, "prompt_required"):
                    module.run_adaptive(args, "  ")
        recommend.assert_not_called()
        execute.assert_not_called()

    def test_compact_output_omits_prompt_result_and_session_id(self):
        secret_prompt = "private prompt token=do-not-print"
        secret_result = '{"answer":"private-result-do-not-print"}'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run(secret_result, "private-session-do-not-print")):
                summary = module.run_adaptive(args, secret_prompt)
            encoded = json.dumps(summary)
            self.assertNotIn(secret_prompt, encoded)
            self.assertNotIn("private-result-do-not-print", encoded)
            self.assertNotIn("private-session-do-not-print", encoded)
            self.assertEqual(summary["total_tokens"], 123)
            self.assertNotIn("result", summary)
            self.assertEqual(stat.S_IMODE(args.receipt_output.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(args.result_output.stat().st_mode), 0o600)

    def test_entry_context_authorizes_only_the_adaptive_in_process_producer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            observed = []

            def guarded_run(receipt_args, prompt_text):
                authorization = module.model_execution_receipt.authorize_receipt_run(receipt_args)
                observed.append((authorization["node_role"], authorization["authorization_source"]))
                return fake_receipt_run()(receipt_args, prompt_text)

            with patch.dict(os.environ, {module.model_execution_receipt.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=guarded_run):
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(observed, [("result-producer", "adaptive-runner")])


if __name__ == "__main__":
    unittest.main()

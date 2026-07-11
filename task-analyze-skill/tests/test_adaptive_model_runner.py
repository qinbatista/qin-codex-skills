#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
import unittest
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
    "verification_shape": "mini_real",
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
    }


def arguments(root, ladder=None, static="gpt-5.6-terra|medium", hard="gpt-5.6-luna|low", gate=False):
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
        grounded_gate_config=None,
    )
    if gate:
        gate_path = root / "gate.json"
        gate_path.write_text(json.dumps({"schema_version": 1, "json_required_keys": ["answer"]}), encoding="utf-8")
        values["grounded_gate_config"] = gate_path
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
            "thread_id": thread_id,
        }
    return run


class AdaptiveModelRunnerTests(unittest.TestCase):
    def test_concise_complex_preset_resolves_exact_calibrated_profile(self):
        args = module.parse_args(["--profile-preset", "grounded-repository-answer-complex", "--project-family", "museai", "--owning-skill", "muse-ai-plugin:muse-ai-dev-skill", "--task-summary", SUMMARY, "--workload-id", "preset-test", "--receipt-output", "cache/preset-receipt.json", "--result-output", "cache/preset-result.json"])
        self.assertEqual(args.task_family, "grounded")
        self.assertEqual(args.artifact, "answer")
        self.assertEqual(args.scope, "multi")
        self.assertEqual(args.execution_domain, "general")
        self.assertEqual(args.static_suggestion, "gpt-5.6-terra|high")
        self.assertEqual(args.hard_floor, "gpt-5.6-luna|low")
        self.assertEqual(args.candidate_ladder, module.model_routing_history.normal_adaptive_pair_texts())

    def test_workflow_graph_gate_preset_is_one_call_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = module.load_gate_preset("workflow-graph-json-v1", root)
        self.assertEqual(gate["source_root"], root)
        self.assertEqual(gate["source_files_pointer"], "/source_files")
        self.assertEqual(gate["expected_key_order"], ["entry", "early_exit_conditions", "stages", "final_merge_fields", "public_return_keys", "source_files"])
        self.assertIn("/stages/*/agents", gate["sorted_json_pointers"])
        self.assertNotIn("/stages/*/depends_on", gate["sorted_json_pointers"])

    def test_workflow_graph_gate_preset_requires_source_root(self):
        with self.assertRaisesRegex(module.RunnerFailure, "grounded_gate_source_root_required"):
            module.load_gate_preset("workflow-graph-json-v1")

    def test_workflow_graph_v2_gate_separates_always_and_optional_return_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = module.load_gate_preset("workflow-graph-json-v2", root)
        expected_keys = ["entry", "early_exit_conditions", "stages", "final_merge_fields", "always_return_keys", "optional_return_keys", "source_files"]
        self.assertEqual(gate["required_keys"], expected_keys)
        self.assertEqual(gate["expected_key_order"], expected_keys)
        self.assertEqual(gate["sorted_json_pointers"], ["/stages/*/agents", "/final_merge_fields", "/always_return_keys", "/optional_return_keys", "/source_files"])
        self.assertEqual(gate["source_files_pointer"], "/source_files")

    def test_workflow_graph_gate_executes_and_records_inside_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "workflow.py").write_text("pass\n", encoding="utf-8")
            result = json.dumps({"entry": "Example.run", "early_exit_conditions": ["empty"], "stages": [{"id": "read", "mode": "parallel", "agents": ["AgentA", "AgentB"], "depends_on": []}], "final_merge_fields": ["id", "name"], "public_return_keys": ["Measurement", "sample_size"], "source_files": ["workflow.py"]}, separators=(",", ":"))
            args = arguments(root)
            args.grounded_gate_preset = "workflow-graph-json-v1"
            args.grounded_source_root = root
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run(result)), patch.object(module.model_routing_history, "record_event", return_value={"status": "recorded"}) as record:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["mini_status"], "pass")
        self.assertEqual(record.call_count, 1)

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
                    "mini_status": "unknown",
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

    def test_grounded_gate_pass_records_same_producer_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root, gate=True)
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()), patch.object(module.grounded_result_gate, "validate_grounded_result", return_value={"status": "pass"}), patch.object(module.model_routing_history, "record_event", return_value={"status": "recorded"}) as record:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["mini_status"], "pass")
        record_args = record.call_args.args[0]
        self.assertEqual(record_args.receipt, str(args.receipt_output))
        self.assertEqual(record_args.verify_level, "mini")
        self.assertEqual(record_args.verify_status, "pass")
        self.assertTrue(record_args.run_id.startswith("run_"))

    def test_grounded_gate_failure_records_quality_and_never_repairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root, gate=True)
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()) as execute, patch.object(module.grounded_result_gate, "validate_grounded_result", side_effect=module.grounded_result_gate.GateFailure("json_required_key_missing")), patch.object(module.model_routing_history, "record_event", return_value={"status": "recorded"}) as record:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["mini_status"], "fail")
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(record.call_args.args[0].failure_class, "correctness")

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

    def test_emit_result_is_absent_when_grounded_gate_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root, gate=True)
            args.emit_result = True
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_receipt_run()), patch.object(module.grounded_result_gate, "validate_grounded_result", side_effect=module.grounded_result_gate.GateFailure("json_required_key_missing")), patch.object(module.model_routing_history, "record_event", return_value={"status": "recorded"}):
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["status"], "fail")
        self.assertNotIn("result", summary)

    def test_operational_failure_is_not_recorded_as_quality(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root, gate=True)
            failed = {"status": "fail", "requested_pair": "gpt-5.6-terra|max", "failure_class": "timeout", "tokens": {"total_tokens": 9}, "process_elapsed_ms": 30}
            with patch.object(module.model_routing_history, "recommend_route", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", return_value=failed), patch.object(module.model_routing_history, "record_event") as record:
                summary = module.run_adaptive(args, "bounded prompt")
        self.assertEqual(summary["reason"], "producer_operational_failure")
        record.assert_not_called()

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

    def test_gate_config_rejects_unknown_fields_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = arguments(root)
            args.grounded_gate_config = root / "gate.json"
            args.grounded_gate_config.write_text(json.dumps({"schema_version": 1, "source_contents": "secret"}), encoding="utf-8")
            with patch.object(module.model_execution_receipt, "run_receipt") as execute:
                with self.assertRaisesRegex(module.RunnerFailure, "grounded_gate_config_invalid"):
                    module.run_adaptive(args, "bounded prompt")
        execute.assert_not_called()

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

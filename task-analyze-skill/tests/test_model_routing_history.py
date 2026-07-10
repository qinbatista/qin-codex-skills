#!/usr/bin/env python3
import importlib.util
import json
import multiprocessing
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "model_routing_history.py"
MODULE_SPEC = importlib.util.spec_from_file_location("model_routing_history", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


CONDITION = {"task_family": "code", "artifact": "script", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "owning_skill": "code-skill", "project_family": "global", "verification_shape": "mini_real"}
SUMMARY = "Implement a compact verified routing-history behavior test."
LADDER = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-terra|low"]
FULL_SOL_LADDER = [
    "gpt-5.3-codex-spark|low",
    "gpt-5.3-codex-spark|medium",
    "gpt-5.3-codex-spark|high",
    "gpt-5.3-codex-spark|xhigh",
    "gpt-5.6-luna|low",
    "gpt-5.6-luna|medium",
    "gpt-5.6-luna|high",
    "gpt-5.6-luna|xhigh",
    "gpt-5.6-luna|max",
    "gpt-5.6-terra|low",
    "gpt-5.6-terra|medium",
    "gpt-5.6-terra|high",
    "gpt-5.6-terra|xhigh",
    "gpt-5.6-terra|max",
    "gpt-5.6-terra|ultra",
    "gpt-5.6-sol|low",
    "gpt-5.6-sol|medium",
    "gpt-5.6-sol|high",
    "gpt-5.6-sol|xhigh",
    "gpt-5.6-sol|max",
    "gpt-5.6-sol|ultra",
]


def arguments(history, receipt, verify_level="mini", verify_status="pass", failure_class="none", run_id="run-one"):
    return SimpleNamespace(**CONDITION, task_summary=SUMMARY, candidate_ladder=LADDER, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=history, receipt=receipt, verify_level=verify_level, verify_status=verify_status, failure_class=failure_class, run_id=run_id, trial=False)


def write_receipt(path, model="gpt-5.6-luna", effort="low", status="pass", turn_completed=None, total_tokens=12, process_elapsed_ms=5, route_attempts=None):
    if turn_completed is None:
        turn_completed = status == "pass"
    payload = {"requested_model": model, "requested_effort": effort, "resolved_model": model, "resolved_effort": effort, "effective_model": model, "status": status, "turn_completed": turn_completed, "model_match": True, "effort_match": True, "tokens": {"total_tokens": total_tokens}, "process_elapsed_ms": process_elapsed_ms}
    if route_attempts is not None:
        payload["route_attempts"] = route_attempts
    path.write_text(json.dumps(payload), encoding="utf-8")


def route_attempt_fail(model="gpt-5.3-codex-spark", effort="low", failure_class="execution"):
    return [{"status": "fail", "failure_class": failure_class, "requested_model": model, "requested_effort": effort, "resolved_model": model, "resolved_effort": effort, "effective_model": model, "effective_effort": effort, "executed_model": model, "executed_effort": effort}]


def concurrent_record(history, receipt, number):
    module.record_event(arguments(Path(history), Path(receipt), run_id=f"run-{number}"))


class ModelRoutingHistoryTests(unittest.TestCase):
    def test_bootstrap_preserves_legacy_and_private_summary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "events.jsonl"
            source = json.dumps({"requested_model": "gpt-5.6-luna", "requested_effort": "low", "receipt_status": "pass", "verify_level": "mini", "verify_status": "pass"}) + "\n"
            legacy.write_text(source, encoding="utf-8")
            history = root / "model_experience.json"
            loaded = module.load_history(history)
            self.assertEqual(legacy.read_text(encoding="utf-8"), source)
            self.assertEqual(loaded["schema_version"], 2)
            self.assertEqual(stat.S_IMODE(history.stat().st_mode), 0o600)
            with self.assertRaises(ValueError):
                module.validate_summary("Read /private/token.txt and api_key=secret now.")

    def test_condition_identity_ignores_summary_and_effort_precedes_model(self):
        self.assertEqual([module.pair_text(*pair) for pair in module.canonical_pairs(["gpt-5.6-terra|xhigh", "gpt-5.3-codex-spark|medium", "gpt-5.6-luna|low", "gpt-5.6-luna|max", "gpt-5.6-sol|xhigh", "gpt-5.6-terra|medium", "gpt-5.6-sol|max"])], ["gpt-5.3-codex-spark|medium", "gpt-5.6-luna|low", "gpt-5.6-luna|max", "gpt-5.6-terra|medium", "gpt-5.6-terra|xhigh", "gpt-5.6-sol|xhigh", "gpt-5.6-sol|max"])
        self.assertEqual(module.condition_key(CONDITION), module.condition_key(dict(CONDITION)))

    def test_cross_model_failure_promotes_within_model_before_moving_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            candidate_ladder = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-luna|max", "gpt-5.6-terra|xhigh", "gpt-5.6-terra|max", "gpt-5.6-sol|xhigh", "gpt-5.6-sol|max"]
            args = arguments(root / "history.json", receipt, run_id="run-pass")
            args.candidate_ladder = candidate_ladder
            args.static_suggestion = "gpt-5.6-luna|low"
            write_receipt(receipt, "gpt-5.6-sol", "max", "pass")
            module.record_event(args)
            write_receipt(receipt, "gpt-5.6-sol", "xhigh", "pass")
            failure = arguments(root / "history.json", receipt, verify_level="real", verify_status="fail", failure_class="quality", run_id="run-fail")
            failure.candidate_ladder = candidate_ladder
            failure.static_suggestion = "gpt-5.6-luna|low"
            module.record_event(failure)
            recommendation = module.recommend_route(args)
            self.assertEqual(recommendation["selected_pair"], "gpt-5.6-sol|max")

    def test_static_tiny_success_failure_and_runtime_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            write_receipt(receipt, "gpt-5.6-luna")
            args = arguments(root / "history.json", receipt)
            self.assertEqual(module.recommend_route(args)["selected_pair"], "gpt-5.6-luna|low")
            tiny_condition = dict(CONDITION, task_family="tiny_code")
            tiny = SimpleNamespace(**tiny_condition, task_summary=SUMMARY, candidate_ladder=LADDER, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=root / "tiny.json")
            self.assertEqual(module.recommend_route(tiny)["selected_pair"], "gpt-5.3-codex-spark|low")
            module.record_event(arguments(root / "history.json", receipt, "mini", "fail", "quality", "run-fail"))
            self.assertEqual(module.recommend_route(args)["selected_pair"], "gpt-5.6-terra|low")
            module.record_event(arguments(root / "history.json", receipt, "real", "pass", "none", "run-success"))
            self.assertEqual(module.recommend_route(args)["selected_pair"], "gpt-5.6-terra|low")
            module.record_event(arguments(root / "history.json", receipt, "real", "fail", "quality", "run-success"))
            self.assertEqual(module.recommend_route(args)["failed_model"], "gpt-5.6-luna|low")
            module.record_event(arguments(root / "history.json", receipt, "mini", "pass", "none", "run-boundary"))
            module.record_event(arguments(root / "history.json", receipt, "real", "fail", "quality", "run-boundary"))
            self.assertEqual(module.recommend_route(args)["failed_model"], "gpt-5.6-luna|low")

    def test_quality_failure_is_sticky_within_one_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            history = root / "history.json"
            write_receipt(receipt, "gpt-5.6-luna")

            module.record_event(arguments(history, receipt, "mini", "fail", "quality", "run-mini"))
            module.record_event(arguments(history, receipt, "real", "pass", "none", "run-mini"))
            mini_record = module.load_history(history)["conditions"][module.condition_key(CONDITION)]["tasks"][0]
            self.assertEqual(module.task_verdict(mini_record), "fail")

            module.record_event(arguments(history, receipt, "mini", "pass", "none", "run-real"))
            module.record_event(arguments(history, receipt, "real", "fail", "quality", "run-real"))
            module.record_event(arguments(history, receipt, "real", "pass", "none", "run-real"))
            real_record = module.load_history(history)["conditions"][module.condition_key(CONDITION)]["tasks"][1]
            self.assertEqual(real_record["real_status"], "fail")
            self.assertEqual(module.task_verdict(real_record), "fail")

    def test_merged_and_narrowed_same_condition_ladders_preserve_historical_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            history = root / "history.json"
            initial_ladder = ["gpt-5.3-codex-spark|low", "gpt-5.3-codex-spark|medium", "gpt-5.6-luna|low", "gpt-5.6-luna|medium"]
            initial = SimpleNamespace(**CONDITION, task_summary=SUMMARY, candidate_ladder=initial_ladder, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=history, receipt=receipt, verify_level="mini", verify_status="fail", failure_class="quality", run_id="run-fail", trial=False)
            write_receipt(receipt, "gpt-5.3-codex-spark", "low", total_tokens=88, process_elapsed_ms=11)
            module.record_event(initial)
            recovery = SimpleNamespace(**CONDITION, task_summary=SUMMARY, candidate_ladder=initial_ladder, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=history, receipt=receipt, verify_level="real", verify_status="pass", failure_class="none", run_id="run-pass", trial=False)
            write_receipt(receipt, "gpt-5.6-luna", "low", total_tokens=64, process_elapsed_ms=9)
            module.record_event(recovery)
            merged_key = module.condition_key(CONDITION)
            merged = module.load_history(history)["conditions"][merged_key]
            self.assertEqual(merged["failed_model"], "gpt-5.3-codex-spark|low")
            self.assertEqual(merged["success_model"], "gpt-5.6-luna|low")
            narrowed = SimpleNamespace(**CONDITION, task_summary=SUMMARY, candidate_ladder=["gpt-5.6-luna|low", "gpt-5.6-terra|low"], static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.6-luna|low", history=history, receipt=receipt, verify_level="real", verify_status="pass", failure_class="none", run_id="run-narrow", trial=False)
            write_receipt(receipt, "gpt-5.6-terra", "low", total_tokens=72, process_elapsed_ms=13)
            module.record_event(narrowed)
            narrowed_record = module.load_history(history)["conditions"][merged_key]
            self.assertEqual(narrowed_record["failed_model"], "gpt-5.3-codex-spark|low")
            self.assertEqual(narrowed_record["success_model"], "gpt-5.6-luna|low")
            self.assertIn("gpt-5.3-codex-spark|low", narrowed_record["candidate_ladder"])

    def test_top_quality_failure_exhausts_with_no_selected_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            history = root / "history.json"
            args = arguments(history, receipt, verify_level="real", verify_status="fail", failure_class="quality", run_id="run-top")
            args.candidate_ladder = ["gpt-5.6-sol|ultra"]
            args.static_suggestion = "gpt-5.6-sol|ultra"
            args.hard_floor = "gpt-5.6-sol|ultra"
            write_receipt(receipt, "gpt-5.6-sol", "ultra", total_tokens=40, process_elapsed_ms=20)
            module.record_event(args)
            recommendation = module.recommend_route(args)
            self.assertIsNone(recommendation["selected_pair"])
            self.assertEqual(recommendation["reason"], "quality_failure_boundary_exhausted")
            self.assertEqual(recommendation["failed_model"], "gpt-5.6-sol|ultra")

    def test_route_attempts_runtime_failure_prevents_tiny_spark_trial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            history = root / "history.json"
            tiny_condition = dict(CONDITION, task_family="tiny_code")
            args = SimpleNamespace(**tiny_condition, task_summary=SUMMARY, candidate_ladder=LADDER, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=history, receipt=receipt, verify_level="mini", verify_status="pass", failure_class="none", run_id="run-tiny-route", trial=False)
            write_receipt(receipt, "gpt-5.6-luna", "low", total_tokens=16, process_elapsed_ms=7, route_attempts=route_attempt_fail())
            module.record_event(args)
            recommendation = module.recommend_route(args)
            self.assertEqual(recommendation["selected_pair"], "gpt-5.6-luna|low")
            self.assertIsNone(recommendation["failed_model"])
            self.assertFalse(recommendation["trial"])

    def test_bounds_compare_median_totals_then_process_for_verified_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            history = root / "history.json"
            ladder = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-luna|high"]
            failure = arguments(history, receipt, verify_level="mini", verify_status="fail", failure_class="quality", run_id="run-failure")
            failure.candidate_ladder = ladder
            write_receipt(receipt, "gpt-5.3-codex-spark", "low", total_tokens=50, process_elapsed_ms=30)
            module.record_event(failure)
            weak_low_a = arguments(history, receipt, verify_level="real", verify_status="pass", failure_class="none", run_id="run-low-a")
            weak_low_a.candidate_ladder = ladder
            write_receipt(receipt, "gpt-5.6-luna", "low", total_tokens=100, process_elapsed_ms=200)
            module.record_event(weak_low_a)
            weak_low_b = arguments(history, receipt, verify_level="real", verify_status="pass", failure_class="none", run_id="run-low-b")
            weak_low_b.candidate_ladder = ladder
            write_receipt(receipt, "gpt-5.6-luna", "low", total_tokens=200, process_elapsed_ms=400)
            module.record_event(weak_low_b)
            strong = arguments(history, receipt, verify_level="real", verify_status="pass", failure_class="none", run_id="run-high")
            strong.candidate_ladder = ladder
            write_receipt(receipt, "gpt-5.6-luna", "high", total_tokens=150, process_elapsed_ms=50)
            module.record_event(strong)
            recommendation = module.recommend_route(weak_low_a)
            self.assertEqual(recommendation["selected_pair"], "gpt-5.6-luna|high")
            self.assertEqual(recommendation["reason"], "performance_ranked")

    def test_high_risk_does_not_downgrade_and_concurrent_records_are_atomic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            write_receipt(receipt)
            high = SimpleNamespace(**dict(CONDITION, risk="high"), task_summary=SUMMARY, candidate_ladder=LADDER, static_suggestion="gpt-5.6-luna|low", hard_floor="gpt-5.3-codex-spark|low", history=root / "high.json")
            self.assertEqual(module.recommend_route(high)["selected_pair"], "gpt-5.6-luna|low")
            processes = [multiprocessing.Process(target=concurrent_record, args=(str(root / "shared.json"), str(receipt), number)) for number in range(4)]
            for process in processes:
                process.start()
            for process in processes:
                process.join()
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(module.status(root / "shared.json")["tasks"], 4)

    def test_sol_ultra_pass_recommends_sol_max_on_full_sol_ladder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            history = root / "history.json"
            receipt = root / "receipt.json"
            args = arguments(history, receipt, run_id="run-sol-ultra")
            args.candidate_ladder = FULL_SOL_LADDER
            args.static_suggestion = "gpt-5.6-luna|low"
            args.hard_floor = "gpt-5.3-codex-spark|low"
            write_receipt(receipt, "gpt-5.6-sol", "ultra", "pass")
            module.record_event(args)
            recommendation = module.recommend_route(args)
            self.assertEqual(recommendation["selected_pair"], "gpt-5.6-sol|max")
            self.assertNotIn("terra", recommendation["selected_pair"])

    def test_quality_failures_raise_failed_model_rung_by_rung(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            history = root / "history.json"
            receipt = root / "receipt.json"
            ladder = [
                "gpt-5.6-luna|low",
                "gpt-5.6-luna|medium",
                "gpt-5.6-luna|high",
                "gpt-5.6-terra|low",
            ]
            args = arguments(history, receipt, verify_level="mini", verify_status="fail", failure_class="quality", run_id="sol-failure")
            args.candidate_ladder = ladder
            args.static_suggestion = "gpt-5.6-luna|low"
            args.hard_floor = "gpt-5.6-luna|low"
            for index, pair in enumerate(ladder[:3], start=1):
                model, effort = pair.split("|", 1)
                write_receipt(receipt, model, effort, "pass")
                args.run_id = f"run-fail-{index}"
                args.verify_level = "mini"
                args.verify_status = "fail"
                args.failure_class = "quality"
                module.record_event(args)
                self.assertEqual(module.recommend_route(args)["failed_model"], pair)

    def test_condition_fields_share_experience_without_summary_changes_and_split_on_field_delta(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            write_receipt(receipt, "gpt-5.6-luna", "low", "pass")
            args = arguments(root / "history.json", receipt, run_id="run-shared")
            args.task_summary = "A detailed but safe routing summary used for testing."
            module.record_event(args)
            args.run_id = "run-shared-2"
            args.task_summary = "A different detailed but safe summary should not split the key."
            module.record_event(args)
            shared_history = module.load_history(root / "history.json")
            shared_key = module.condition_key(CONDITION)
            self.assertIn(shared_key, shared_history["conditions"])
            self.assertEqual(len(shared_history["conditions"][shared_key]["tasks"]), 2)

            args.risk = "high"
            args.run_id = "run-split"
            args.task_summary = "A high-risk but still safe summary."
            module.record_event(args)
            split_history = module.load_history(root / "history.json")
            self.assertEqual(len(split_history["conditions"]), 2)


if __name__ == "__main__":
    unittest.main()

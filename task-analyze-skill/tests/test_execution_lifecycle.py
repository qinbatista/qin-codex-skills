#!/usr/bin/env python3
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing_policy = load_module("routing_policy")
runner = load_module("obsidian_adaptive_model_runner")
dispatcher = load_module("task_route_dispatcher")
entry_resolver = load_module("resolve_entry_model")
session_effort = load_module("session_effort")


class ExecutionLifecycleTests(unittest.TestCase):
    def test_every_score_and_fast_path_state_resolves_exactly_one_mode(self):
        modes = {"direct", "planned_single", "planned_graph"}
        for score in range(101):
            for fast_path in (False, True):
                contract = routing_policy.execution_lifecycle_contract(score, fast_path)
                self.assertIn(contract["mode"], modes)
                self.assertEqual(contract["execution_stages"], ["execute"] if contract["mode"] == "direct" else ["plan", "execute"])

    def test_ultra_simple_low_risk_task_executes_directly(self):
        contract = routing_policy.execution_lifecycle_contract(24, True)
        self.assertEqual(contract["mode"], "direct")
        self.assertFalse(contract["plan_required"])
        self.assertEqual(contract["model_selection"], "user_selected_for_governing_skills_else_adaptive")

    def test_risk_or_ambiguity_forces_a_plan(self):
        for risk, ambiguity in (("high", "low"), ("low", "high")):
            contract = routing_policy.execution_lifecycle_contract(12, True, risk=risk, ambiguity=ambiguity)
            self.assertEqual(contract["mode"], "planned_single")
            self.assertTrue(contract["plan_required"])

    def test_standard_complex_and_advanced_single_tasks_stay_single_threaded(self):
        for score in (25, 49, 50, 74, 75, 100):
            contract = routing_policy.execution_lifecycle_contract(score, False)
            self.assertEqual(contract["mode"], "planned_single")
            self.assertEqual(contract["execution_topology"], "single")

    def test_any_multi_result_plan_uses_dependency_graph_lifecycle(self):
        for topology in ("sequential", "parallel", "mixed"):
            plan = {"schema_version": 2, "complexity": "complex", "complexity_score": 68, "topology": topology, "routing_mode": dispatcher.DYNAMIC_ROUTING_MODE, "nodes": [{"id": "one", "phase": "result"}, {"id": "two", "phase": "result"}]}
            contract = dispatcher.execution_lifecycle_for_plan(plan)
            self.assertEqual(contract["mode"], "planned_graph")
            self.assertEqual(contract["execution_topology"], "dependency_graph")

    def test_route_start_notice_discloses_the_selected_lifecycle(self):
        contract = routing_policy.execution_lifecycle_contract(35)
        output = io.StringIO()
        with redirect_stdout(output):
            runner._emit_execution_lifecycle_notice(contract)
        event = json.loads(output.getvalue())
        self.assertEqual(event["stage"], "execution-lifecycle-notice")
        self.assertTrue(event["user_visible"])
        self.assertEqual(event["execution_lifecycle"], contract)

    def test_model_family_and_reasoning_effort_follow_problem_shape(self):
        simple = session_effort.classify_task("Implement one bounded function.", task_type="code", operation="implement", complexity_score=18)
        difficult = session_effort.classify_task("Diagnose and repair a difficult architecture bug in 8 steps with dependencies.", task_type="debug", operation="fix", complexity_score=60)
        frontier = session_effort.classify_task("Deep research across many sources with comprehensive all context.", task_type="research", complexity_score=90)
        self.assertEqual(simple["model_family"], "gpt-5.6-terra")
        self.assertEqual(difficult["model_family"], "gpt-5.6-terra")
        self.assertEqual(frontier["model_family"], "gpt-5.6-sol")
        self.assertIn(difficult["estimated_effort"], {"medium", "high", "max", "ultra"})

    def test_repeated_quality_failure_strengthens_only_the_same_solving_route(self):
        summary = {"preferred_solving_pair": "gpt-5.6-terra|low", "route_reason": "bounded_core_solving_low_route"}
        pairs = ["gpt-5.6-luna|low", "gpt-5.6-terra|low", "gpt-5.6-sol|low"]
        upgraded = session_effort.solve_route_pair(summary, "gpt-5.6-terra|low", pairs)
        self.assertEqual(upgraded["pair"], "gpt-5.6-sol|low")
        self.assertEqual(upgraded["reason"], "repeated_core_route_model_upgrade_same_task_class")
        contract = routing_policy.execution_lifecycle_contract(60)
        self.assertEqual(contract["operational_failure"], "quality_neutral_retry_or_allowed_fallback")

    def test_acceptance_is_surface_gated_and_final_aggregate_only(self):
        required = runner.result_lifecycle_policy(True, "code", 18, "low")
        skipped = runner.result_lifecycle_policy(True, "question", 12, "low")
        receipt = {"status": "pass", "result_published": True, "turn_completed": True, "ending_required": required["ending_required"]}
        aggregate = runner._final_aggregate_fields(receipt, 2, "released")
        self.assertTrue(required["ending_required"])
        self.assertTrue(aggregate["ending_launch_ready"])
        self.assertTrue(aggregate["final_aggregate_receipt"])
        self.assertFalse(skipped["ending_required"])
        self.assertEqual(skipped["ending_real_status"], "skipped")

    def test_missing_desktop_session_file_is_unavailable_not_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "sessions").mkdir()
            thread_id = "12345678-1234-1234-1234-1234567890ab"
            self.assertEqual(entry_resolver.resolve_entry_model(thread_id, root), {"status": "unavailable"})
            session_dir = root / "sessions" / "2026" / "08" / "23"
            session_dir.mkdir(parents=True)
            (session_dir / f"session-{thread_id}.jsonl").write_text(json.dumps({"type": "session_meta", "payload": {"id": thread_id}}), encoding="utf-8")
            self.assertEqual(entry_resolver.resolve_entry_model(thread_id, root), {"status": "unavailable"})


if __name__ == "__main__":
    unittest.main()

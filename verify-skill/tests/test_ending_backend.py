#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


BACKEND_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ending_backend.py"
BACKEND_SPEC = importlib.util.spec_from_file_location("test_ending_backend", BACKEND_SCRIPT)
BACKEND = importlib.util.module_from_spec(BACKEND_SPEC)
BACKEND_SPEC.loader.exec_module(BACKEND)

PLAN_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ending_verification_plan.py"
PLAN_SPEC = importlib.util.spec_from_file_location("test_ending_verification_plan", PLAN_SCRIPT)
PLAN = importlib.util.module_from_spec(PLAN_SPEC)
PLAN_SPEC.loader.exec_module(PLAN)


class EndingBackendTests(unittest.TestCase):
    def test_projectless_host_remains_the_only_terminal_backend(self):
        resolution = BACKEND.resolve_ending_backend({"projectless_host": True, "standard_subagent": True, "local_codex_exec": True})
        self.assertEqual(resolution["status"], "launchable")
        self.assertTrue(resolution["terminal_lifecycle"])
        self.assertEqual(resolution["selected"]["backend"], "projectless_host")
        self.assertTrue(resolution["selected"]["independent_context"])
        self.assertFalse(resolution["selected"]["producer_context_reuse"])

    def test_subagent_and_local_exec_are_independent_evidence_fallbacks_not_false_terminal_passes(self):
        subagent = BACKEND.resolve_ending_backend({"projectless_host": False, "standard_subagent": True, "local_codex_exec": True})
        local = BACKEND.resolve_ending_backend({"projectless_host": False, "standard_subagent": False, "local_codex_exec": True})
        unavailable = BACKEND.resolve_ending_backend({"projectless_host": False, "standard_subagent": False, "local_codex_exec": False})
        self.assertEqual(subagent["selected"]["backend"], "standard_subagent")
        self.assertEqual(local["selected"]["backend"], "local_codex_exec")
        self.assertEqual(subagent["status"], "blocked")
        self.assertEqual(local["status"], "blocked")
        self.assertEqual(unavailable["reason"], "no_independent_ending_backend_available")

    def test_launch_plan_preserves_a_portable_independent_request_when_projectless_host_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            plan = PLAN.build_plan(
                root,
                "portable-ending",
                60,
                [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}],
                {"thread_id": "source-session", "host_id": "host", "project_id": "project", "project_root": str(root)},
            )
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            producer_receipt = root / "producer-receipt.json"
            producer_receipt.write_text(json.dumps({"status": "pass", "result_published": True, "turn_completed": True, "node_type": "locked-route-node", "node_role": "result-producer", "final_aggregate_receipt": True, "all_result_nodes_settled": True, "subprocesses_settled": True, "ending_launch_ready": True, "aggregate_result_state": "single_result_released", "aggregate_result_node_count": 1}), encoding="utf-8")
            launch = PLAN.build_launch_spec(
                plan_path,
                root / "Cache" / "tests" / "ending",
                "project",
                producer_receipt,
                backend_capabilities={"projectless_host": False, "standard_subagent": True, "local_codex_exec": True},
            )
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            audit = PLAN.audit_launches(launch_path, root / "launch-state.json")
        self.assertEqual(launch["execution"], "independent_evidence_only")
        self.assertEqual(launch["required_launch_count"], 0)
        self.assertEqual(launch["independent_verification_request_count"], 1)
        request = launch["independent_verification_requests"][0]
        self.assertEqual(request["backend"], "standard_subagent")
        self.assertTrue(request["independent_context"])
        self.assertFalse(request["producer_context_reuse"])
        self.assertNotIn("target", request["arguments"])
        self.assertIn("INDEPENDENT_ENDING_EVIDENCE_WORKER", request["arguments"]["prompt"])
        self.assertEqual(audit["status"], "blocked")


if __name__ == "__main__":
    unittest.main()

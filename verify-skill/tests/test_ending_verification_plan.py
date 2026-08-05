import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "ending_verification_plan.py"
SPEC = importlib.util.spec_from_file_location("ending_verification_plan", SCRIPT_PATH)
PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLAN)


class EndingVerificationPlanTests(unittest.TestCase):
    def test_score_bands_select_increasing_quality_roles(self):
        routes = [PLAN.pair_for_score(score) for score in (12, 35, 60, 90)]
        self.assertEqual([route["complexity_band"] for route in routes], ["small", "standard", "complex", "advanced"])
        self.assertEqual(len({route["selected_pair"] for route in routes}), 4)

    def test_each_independent_check_becomes_its_own_ending_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = PLAN.build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])
        self.assertEqual(plan["execution"], "separate_persistent_tasks")
        self.assertEqual(plan["schema_version"], 3)
        self.assertEqual(plan["thread_target"]["type"], "projectless")
        self.assertNotIn("environment", plan["thread_target"])
        self.assertEqual(plan["thread_target"]["project_root"], str(root.resolve()))
        self.assertEqual(plan["terminal_thread_policy"], {"pass": "keep_visible", "fail": "keep_visible", "blocked": "keep_visible"})
        self.assertEqual([task["title"] for task in plan["ending_tasks"]], ["End Task-routing-unit", "End Task-routing-integration"])
        self.assertTrue(all(task["thread_target"]["type"] == "projectless" for task in plan["ending_tasks"]))
        self.assertTrue(all(task["terminal_thread_policy"]["pass"] == "keep_visible" for task in plan["ending_tasks"]))
        self.assertNotEqual(plan["ending_tasks"][0]["selected_pair"], plan["ending_tasks"][1]["selected_pair"])

    def test_run_check_executes_real_command_and_records_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan = PLAN.build_plan(root, "real", 20, [{"name": "test", "command": ["python3", "-c", "print('REAL PASS')"]}])
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            evidence = PLAN.run_check(plan_path, "test", evidence_path)
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["exit_code"], 0)
        self.assertIn("REAL PASS", evidence["stdout"])

    def test_failed_real_command_emits_exact_repair_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan = PLAN.build_plan(root, "repair", 45, [{"name": "unit", "command": ["python3", "-c", "import sys; print('broken', file=sys.stderr); raise SystemExit(7)"]}])
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            evidence = PLAN.run_check(plan_path, "unit", evidence_path)
        self.assertEqual(evidence["status"], "fail")
        self.assertEqual(evidence["repair_handoff"]["action"], "create_repair_task_then_fresh_ending")
        self.assertEqual(evidence["repair_handoff"]["thread_target"]["type"], "project")
        self.assertEqual(evidence["repair_handoff"]["thread_target"]["environment"], {"type": "local"})
        self.assertEqual(evidence["repair_handoff"]["thread_target"]["project_id"], "resolve_exact_project_root")
        self.assertEqual(evidence["repair_handoff"]["thread_target"]["project_root"], str(root.resolve()))
        self.assertEqual(evidence["repair_handoff"]["terminal_thread_policy"]["fail"], "keep_visible")
        self.assertEqual(evidence["repair_handoff"]["error"]["exit_code"], 7)
        self.assertIn("broken", evidence["repair_handoff"]["error"]["stderr"])

    def test_launch_spec_requires_one_real_projectless_thread_per_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(PLAN.build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")
        self.assertEqual(launch["execution"], "host_persistent_create_thread")
        self.assertEqual(launch["required_launch_count"], 2)
        self.assertEqual({item["tool"] for item in launch["launch_requests"]}, {"codex_app__create_thread"})
        self.assertEqual(launch["project_binding"]["project_root"], str(root.resolve()))
        self.assertTrue(all(item["arguments"]["target"] == {"type": "projectless"} for item in launch["launch_requests"]))
        self.assertTrue(all(item["arguments"]["prompt"].startswith("ENDING_TASK_WORKER\n") for item in launch["launch_requests"]))
        self.assertTrue(all("Verification plan relative to project root: plan.json" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("Evidence output relative to project root: Cache/tests/ending-evidence/" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("Personal memory candidates output relative to project root: Cache/tests/ending-evidence/" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all(str(root / "plan.json") not in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("Never call set_thread_archived" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("structured model_assessment" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("If the scan finds no durable preference" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertEqual(
            [f"{item['arguments']['model']}|{item['arguments']['thinking']}" for item in launch["launch_requests"]],
            [item["selected_pair"] for item in launch["launch_requests"]],
        )

    def test_launch_audit_blocks_until_every_thread_is_acknowledged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(PLAN.build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            not_launched = PLAN.audit_launches(launch_path, state_path)
            PLAN.acknowledge_launch(launch_path, "unit", "thread-unit", "host-unit", "project-123", state_path)
            blocked = PLAN.audit_launches(launch_path, state_path)
            PLAN.acknowledge_launch(launch_path, "integration", "thread-integration", "host-integration", "project-123", state_path)
            passed = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(not_launched["status"], "blocked")
        self.assertEqual(not_launched["end_task_trigger_rate"], "0%")
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["end_task_trigger_rate"], "50%")
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(passed["end_task_trigger_rate"], "100%")
        self.assertEqual(passed["launched_count"], 2)

    def test_one_thread_cannot_acknowledge_two_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(PLAN.build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"]},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"]},
            ])), encoding="utf-8")
            launch_path.write_text(json.dumps(PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")), encoding="utf-8")
            PLAN.acknowledge_launch(launch_path, "unit", "same-thread", "host", "project-123", state_path)
            with self.assertRaisesRegex(ValueError, "cannot acknowledge multiple checks"):
                PLAN.acknowledge_launch(launch_path, "integration", "same-thread", "host", "project-123", state_path)


if __name__ == "__main__":
    unittest.main()

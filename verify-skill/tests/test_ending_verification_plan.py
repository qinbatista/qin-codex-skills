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
        self.assertEqual([task["title"] for task in plan["ending_tasks"]], ["End Task-routing-unit", "End Task-routing-integration"])
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
        self.assertEqual(evidence["repair_handoff"]["error"]["exit_code"], 7)
        self.assertIn("broken", evidence["repair_handoff"]["error"]["stderr"])


if __name__ == "__main__":
    unittest.main()

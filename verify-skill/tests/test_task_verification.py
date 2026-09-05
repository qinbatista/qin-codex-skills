import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("task_verification", Path(__file__).resolve().parents[1] / "scripts/task_verification.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerificationScopeTests(unittest.TestCase):
    def test_simple_values_skip_unless_requested(self):
        self.assertFalse(MODULE.verification_plan("value")["required"])
        self.assertEqual(MODULE.verification_plan("value", requested=True)["checks"], ["changed_value_readback"])

    def test_ui_requires_rendered_behavior(self):
        plan = MODULE.verification_plan("ui")
        self.assertIn("rendered_state", plan["checks"])
        self.assertEqual(plan["owner"], "active_task")
        self.assertFalse(plan["whole_project_allowed"])
        self.assertEqual(plan["ending_checks"], [])

    def test_static_presentations_check_pages_without_invented_interactions(self):
        plan = MODULE.verification_plan("presentation")
        self.assertEqual(plan["owner"], "active_task")
        self.assertIn("rendered_page_or_slide", plan["checks"])
        self.assertIn("intended_reading_size", plan["checks"])
        self.assertIn("containment_and_readability", plan["checks"])
        self.assertNotIn("affected_interaction", plan["checks"])
        self.assertFalse(plan["whole_project_allowed"])
        self.assertEqual(plan["ending_checks"], [])

    def test_structure_stays_bounded_unless_whole_scope_requested(self):
        self.assertFalse(MODULE.verification_plan("structure")["whole_project_allowed"])
        self.assertTrue(MODULE.verification_plan("structure", whole_project_requested=True)["whole_project_allowed"])

    def test_unknown_change_is_not_silently_skipped(self):
        with self.assertRaises(ValueError):
            MODULE.verification_plan("mystery")

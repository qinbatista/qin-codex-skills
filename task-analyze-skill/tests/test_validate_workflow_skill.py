import importlib.util
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_current_workflow", ROOT / "workflow-skill/scripts/validate_workflow_skill.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class CurrentWorkflowTests(unittest.TestCase):
    def test_source_links_resolve(self):
        self.assertEqual(MODULE.validate(ROOT / "workflow-skill"), [])
    def test_verification_after_completion_is_rejected(self):
        result=MODULE.validate_trace("bad", [{"id":"main-result"},{"purpose":"verify"}])
        self.assertEqual(result["status"],"fail")
    def test_memory_cannot_launch_checks(self):
        node={"phase":"ending","purpose":"memory","checks":["old check"],"model":"gpt-6-astra","effort":"ultra","selected_pair":"gpt-6-astra|ultra"}
        self.assertEqual(MODULE.validate_trace("bad",[node])["status"],"fail")
    def test_missing_or_changed_selected_pair_is_rejected(self):
        for node in [{"skill":"code-skill"},{"phase":"ending","purpose":"memory","selected_pair":"gpt-6-astra|ultra","model":"gpt-5.6-luna","effort":"max"}]:
            self.assertEqual(MODULE.validate_trace("bad",[node])["status"],"fail")

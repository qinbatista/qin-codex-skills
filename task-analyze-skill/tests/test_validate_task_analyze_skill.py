import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_current_task", ROOT / "task-analyze-skill/scripts/validate_task_analyze_skill.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class CurrentContractTests(unittest.TestCase):
    def test_current_source_contract(self):
        self.assertEqual(MODULE.validate(ROOT / "task-analyze-skill")["failures"], [])
    def test_missing_package_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(MODULE.validate(Path(directory))["status"], "fail")

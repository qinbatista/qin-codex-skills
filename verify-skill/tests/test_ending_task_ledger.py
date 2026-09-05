import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


class RetiredEndingTests(unittest.TestCase):
    def test_old_check_and_launch_commands_are_rejected_without_execution(self):
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        for name in ("ending_verification_plan.py", "ending_task_ledger.py"):
            for command in ("run-check", "create-launches", "start", "event"):
                result = subprocess.run([sys.executable, "-B", str(scripts / name), command], capture_output=True, text=True, **hidden_process_options())
                self.assertEqual(result.returncode, 2)
                self.assertIn("memory-only", result.stderr)
                self.assertEqual(result.stdout, "")

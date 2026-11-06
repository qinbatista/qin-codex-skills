import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


HOOK = ROOT / "task-analyze-skill" / "scripts" / "closeout_stop_hook.py"


class CloseoutStopHookTests(unittest.TestCase):
    def run_hook(self, event):
        return subprocess.run([sys.executable, "-B", str(HOOK)], input=json.dumps(event), text=True, capture_output=True, timeout=10, check=False, **hidden_process_options())

    def test_first_stop_requests_same_chat_closeout_with_scope_guards(self):
        result = self.run_hook({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "block")
        for requirement in ("cleanup", "Obsidian", "AI-index", "read-only", "first-index consent", "do not", "Ending chat"):
            self.assertIn(requirement, output["reason"])

    def test_continued_stop_does_not_loop(self):
        result = self.run_hook({"hook_event_name": "Stop", "stop_hook_active": True})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})

    def test_invalid_event_fails_without_requesting_continuation(self):
        for event in ({}, {"hook_event_name": "Stop", "stop_hook_active": "false"}, {"hook_event_name": "SessionEnd", "stop_hook_active": False}):
            with self.subTest(event=event):
                result = self.run_hook(event)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()

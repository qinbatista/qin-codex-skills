import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("ending_backend", Path(__file__).resolve().parents[1] / "scripts/ending_backend.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MemoryBackendTests(unittest.TestCase):
    def test_memory_is_inline_even_when_legacy_task_tools_exist(self):
        result = MODULE.resolve_ending_backend({"projectless_host": True})
        self.assertEqual(result["status"], "inline")
        self.assertIsNone(result["selected"]["launch_tool"])
        self.assertFalse(result["terminal_lifecycle"])

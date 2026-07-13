#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_memory_bridge.py"
MODULE_SPEC = importlib.util.spec_from_file_location("obsidian_memory_bridge", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class ObsidianMemoryBridgeTests(unittest.TestCase):
    def test_missing_vault_is_non_blocking(self):
        missing = Path(tempfile.gettempdir()) / "missing-obsidian-memory-bridge-vault"
        self.assertEqual(module.search_memory("routing failure", missing)["status"], "unavailable")
        self.assertEqual(module.record_model_experience("bounded task", "integration", "complex", "python", "code-skill", "gpt-5.6-terra|high", "pass", "frozen", vault=missing)["status"], "unavailable")

    def test_search_prefers_task_model_experience_and_bounds_digest(self):
        with tempfile.TemporaryDirectory(prefix="obsidian-memory-search-") as temporary:
            vault = Path(temporary)
            (vault / "TaskModelExperience").mkdir()
            (vault / "wiki").mkdir()
            (vault / "TaskModelExperience" / "routing.md").write_text("Python routing failure used Terra high and then effort-first xhigh.\n", encoding="utf-8")
            (vault / "wiki" / "log.md").write_text("Python routing failure historical log.\n", encoding="utf-8")
            result = module.search_memory("python routing failure", vault, max_results=2, max_chars=120)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["matches"][0]["path"], "TaskModelExperience/routing.md")
            self.assertLessEqual(len(result["digest"]), 120)

    def test_generic_model_memory_does_not_hide_more_related_project_memory(self):
        with tempfile.TemporaryDirectory(prefix="obsidian-memory-project-") as temporary:
            vault = Path(temporary)
            (vault / "TaskModelExperience").mkdir()
            (vault / "Projects" / "MuseAI").mkdir(parents=True)
            (vault / "TaskModelExperience" / "index.md").write_text("Operational failure model records.\n", encoding="utf-8")
            (vault / "Projects" / "MuseAI" / "index.md").write_text("MuseAI coordinate agent failure and correction.\n", encoding="utf-8")
            result = module.search_memory("MuseAI coordinate failure", vault, max_results=2)
            self.assertEqual(result["matches"][0]["path"], "Projects/MuseAI/index.md")

    def test_record_creates_sanitized_month_page_and_index(self):
        with tempfile.TemporaryDirectory(prefix="obsidian-model-record-") as temporary:
            vault = Path(temporary)
            recorded_at = datetime(2026, 7, 10, 20, 0, tzinfo=timezone.utc)
            result = module.record_model_experience("update bounded memory routing", "integration", "complex", "python", "code-skill", "gpt-5.6-terra|xhigh", "pass", "frozen", best_pair="gpt-5.6-terra|xhigh", failed_pair="gpt-5.6-terra|high", previous_pair="gpt-5.6-terra|high", switch_direction="upgrade_effort", switch_reason="Real quality failure", total_tokens=123, process_ms=456, comparison_status="same_workload", vault=vault, recorded_at=recorded_at)
            self.assertEqual(result["status"], "written")
            record_text = (vault / "TaskModelExperience" / "2026" / "2026-07.md").read_text(encoding="utf-8")
            self.assertIn("gpt-5.6-terra|high -> gpt-5.6-terra|xhigh", record_text)
            self.assertIn("tokens=123; process_ms=456", record_text)
            self.assertIn("Real=pass", record_text)
            self.assertNotIn("Mini=", record_text)
            self.assertIn("[[TaskModelExperience/2026/2026-07]]", (vault / "TaskModelExperience" / "index.md").read_text(encoding="utf-8"))

    def test_record_rejects_non_durable_real_status(self):
        with tempfile.TemporaryDirectory(prefix="obsidian-model-verdict-") as temporary:
            with self.assertRaisesRegex(ValueError, "real_status must be pass or fail"):
                module.record_model_experience("update bounded memory routing", "integration", "complex", "python", "code-skill", "gpt-5.6-terra|high", "unknown", "cold_start", vault=Path(temporary))

    def test_record_rejects_sensitive_or_path_like_summary(self):
        with tempfile.TemporaryDirectory(prefix="obsidian-model-secret-") as temporary:
            with self.assertRaises(ValueError):
                module.record_model_experience(f"read {Path.home() / 'private'}", "integration", "complex", "python", "code-skill", "gpt-5.6-terra|high", "pass", "frozen", vault=Path(temporary))


if __name__ == "__main__":
    unittest.main()

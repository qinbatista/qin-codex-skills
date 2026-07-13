import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "project_change_memory.py"
SPEC = importlib.util.spec_from_file_location("project_change_memory", SCRIPT_PATH)
MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEMORY)


class ProjectChangeMemoryTests(unittest.TestCase):
    def test_record_search_duplicate_and_obsidian_projection(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "ExampleProject"
            store = root / "store"
            vault = root / "vault"
            project.mkdir()
            vault.mkdir()
            (project / "src").mkdir()
            (project / "src" / "feature.py").write_text("value = 1\n", encoding="utf-8")
            recorded_at = datetime(2026, 7, 12, 20, 0, tzinfo=timezone.utc)
            first = MEMORY.record_change(project, "feature-engine", "code", "edit", "Added stable feature behavior", "Preserve the public contract while fixing the implementation", "Focused behavior now passes", "passed", ["src/feature.py"], ["python unit test passed"], ["Keep the public key exact"], ["none"], store=store, vault=vault, recorded_at=recorded_at)
            duplicate = MEMORY.record_change(project, "feature-engine", "code", "edit", "Added stable feature behavior", "Preserve the public contract while fixing the implementation", "Focused behavior now passes", "passed", ["src/feature.py"], ["python unit test passed"], ["Keep the public key exact"], ["none"], store=store, vault=vault, recorded_at=recorded_at)
            search = MEMORY.search_records(project, "feature-engine", ["src/feature.py"], "stable feature", 8, store)
            self.assertEqual(first["status"], "written")
            self.assertEqual(first["obsidian"]["status"], "written")
            self.assertEqual(duplicate["status"], "duplicate")
            self.assertEqual(search["matches"][0]["reason"], "Preserve the public contract while fixing the implementation")
            self.assertEqual(len((store / "index.jsonl").read_text(encoding="utf-8").splitlines()), 1)
            self.assertTrue((vault / first["obsidian"]["root"] / "files" / "src" / "feature.py.md").exists())

    def test_rejects_files_outside_project(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            project.mkdir()
            with self.assertRaises(ValueError):
                MEMORY.record_change(project, "project-wide", "project", "edit", "Changed settings", "Match the requested behavior", "Settings updated", "not-run", [root / "outside.txt"], store=root / "store", vault=root / "missing-vault")


if __name__ == "__main__":
    unittest.main()

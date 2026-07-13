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

    def test_failed_record_is_written_before_repair_supersedes_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            store = root / "store"
            project.mkdir()
            (project / "script.py").write_text("value = 1\n", encoding="utf-8")
            failed = MEMORY.record_change(project, "runtime", "file", "edit", "Changed runtime value", "Implement the requested behavior", "Ending Real found an incorrect value", "failed", ["script.py"], ["Expected 2 but observed 1"], ["Repair is a new lifecycle"], ["Incorrect durable edit remains"], store=store, vault=root / "missing-vault")
            repaired = MEMORY.record_change(project, "runtime", "file", "edit", "Repaired runtime value", "Correct the verified failure", "Independent Ending Real passed", "passed", ["script.py"], ["Focused regression passed"], ["Preserve the verified value"], ["none"], supersedes=failed["record_id"], store=store, vault=root / "missing-vault")
            records = MEMORY._read_records(store / "index.jsonl")
            self.assertEqual(failed["status"], "written")
            self.assertEqual(repaired["status"], "written")
            self.assertEqual(records[1]["supersedes"], failed["record_id"])
            self.assertEqual([record["verification_status"] for record in records], ["failed", "passed"])

    def test_supersedes_rejects_unknown_or_unrelated_record(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            store = root / "store"
            project.mkdir()
            (project / "script.py").write_text("value = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "existing record"):
                MEMORY.record_change(project, "runtime", "file", "edit", "Repair", "Correct failure", "Passed", "passed", ["script.py"], ["test passed"], supersedes="missing-record", store=store, vault=root / "missing-vault")


if __name__ == "__main__":
    unittest.main()

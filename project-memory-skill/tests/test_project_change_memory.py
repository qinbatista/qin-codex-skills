import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_change_memory.py"
SPEC = importlib.util.spec_from_file_location("project_change_memory", SCRIPT)
MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEMORY)


class RetiredCodexMemoryTests(unittest.TestCase):
    def test_legacy_writers_refuse_to_create_codex_local_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            store = Path(temporary) / "memory"
            with self.assertRaisesRegex(RuntimeError, "Obsidian"):
                MEMORY.record_change(project, "module", "project", "edit", "Summary", "Reason", "Result", "not-run", ["file.py"], store=store)
            with self.assertRaisesRegex(RuntimeError, "read-only legacy"):
                MEMORY.remove_invalid_record(project, "record-id", "reason", store=store)
            with self.assertRaisesRegex(RuntimeError, "retired"):
                MEMORY.reconcile_projections(project, store=store)
            self.assertFalse(store.exists())

    def test_explicit_existing_vault_is_resolved_without_local_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            (vault / "AI Memory").mkdir(parents=True)
            (vault / "Projects").mkdir()
            (vault / "AI Memory" / "ai_memory.py").write_text("# runtime\n")
            self.assertEqual(MEMORY._resolve_vault(vault), vault.resolve())
            self.assertFalse((vault / "events.jsonl").exists())

    def test_legacy_search_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            store = Path(temporary) / "missing-store"
            result = MEMORY.search_records(project, store=store)
            self.assertEqual(result["matches"], [])
            self.assertFalse(store.exists())


if __name__ == "__main__":
    unittest.main()

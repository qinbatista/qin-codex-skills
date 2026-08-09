import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "memory_coverage.py"
SPEC = importlib.util.spec_from_file_location("memory_coverage", SCRIPT)
memory_coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory_coverage)


class MemoryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "ExampleProject"
        (self.project / "src").mkdir(parents=True)
        (self.project / "src" / "example.py").write_text("class Example:\n    def run(self):\n        return 1\n", encoding="utf-8")
        self.vault = self.root / "vault"
        (self.vault / "Projects" / "ExampleProject").mkdir(parents=True)
        (self.vault / "Projects" / "ExampleProject" / "index.md").write_text("# ExampleProject\n", encoding="utf-8")
        self.store = self.root / "coverage" / "events.jsonl"
        self.when = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
        self.owner_patcher = mock.patch.object(
            memory_coverage.project_change_memory,
            "_registered_owner",
            return_value="ExampleProject",
        )
        self.owner_patcher.start()

    def tearDown(self):
        self.owner_patcher.stop()
        self.temporary.cleanup()

    def test_route_creates_project_module_and_method_native_pages(self):
        result = memory_coverage.ensure_coverage(
            self.project,
            "example-module",
            symbol="Example.run",
            files=["src/example.py"],
            task_type="code",
            code_kind="python",
            operation="edit",
            source="model-route",
            vault=self.vault,
            store=self.store,
            recorded_at=self.when,
        )
        coverage_root = self.vault / "Projects" / "ExampleProject" / "Memory Coverage"
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["required_scopes"], ["project", "module", "method"])
        self.assertTrue((coverage_root / "index.md").is_file())
        self.assertTrue((coverage_root / "Modules" / "example-module.md").is_file())
        self.assertTrue((coverage_root / "Methods" / "example-module--Example.run.md").is_file())
        self.assertIn("Memory Coverage", (self.vault / "Projects" / "ExampleProject" / "index.md").read_text(encoding="utf-8"))
        self.assertNotIn(str(self.project), self.store.read_text(encoding="utf-8"))

    def test_repeated_route_merges_without_duplicate_native_rows(self):
        kwargs = {"symbol": "Example.run", "files": ["src/example.py"], "source": "model-route", "vault": self.vault, "store": self.store}
        memory_coverage.ensure_coverage(self.project, "example-module", recorded_at=self.when, **kwargs)
        memory_coverage.ensure_coverage(self.project, "example-module", recorded_at=self.when, **kwargs)
        index = self.vault / "Projects" / "ExampleProject" / "Memory Coverage" / "index.md"
        text = index.read_text(encoding="utf-8")
        self.assertEqual(text.count("| method | example-module | Example.run |"), 1)
        self.assertEqual(len(self.store.read_text(encoding="utf-8").splitlines()), 6)

    def test_method_is_required_for_code_action_but_module_sentinel_is_explicit(self):
        with self.assertRaisesRegex(memory_coverage.CoverageError, "method memory is required"):
            memory_coverage.ensure_coverage(
                self.project,
                "example-module",
                files=["src/example.py"],
                task_type="code",
                operation="edit",
                store=self.store,
            )
        with self.assertRaisesRegex(memory_coverage.CoverageError, "validation requires"):
            memory_coverage.validate_coverage(self.project, "example-module", require_method=True, store=self.store)
        result = memory_coverage.ensure_coverage(
            self.project,
            "example-module",
            symbol="__module__",
            files=["src/example.py"],
            task_type="code",
            operation="edit",
            store=self.store,
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["missing_scopes"], [])
        self.assertEqual(memory_coverage.coverage_status(self.project, store=self.store)["scopes"], ["module", "project"])

    def test_scope_policy_distinguishes_code_actions_from_questions(self):
        self.assertTrue(memory_coverage.requires_method_scope("code", "python", "edit", ["src/example.py"]))
        self.assertFalse(memory_coverage.requires_method_scope("question", "general", "work", ["src/example.py"]))
        self.assertFalse(memory_coverage.requires_method_scope("documentation", "markdown", "edit", ["README.md"]))

    def test_merge_store_preserves_canonical_scopes_reprojects_and_deletes_rogue_store(self):
        rogue_store = self.root / "rogue" / "memory-coverage-events.jsonl"
        (self.project / "src" / "rogue.py").write_text("def rogue():\n    return True\n", encoding="utf-8")
        memory_coverage.ensure_coverage(
            self.project,
            "canonical-module",
            symbol="Example.run",
            files=["src/example.py"],
            source="model-route",
            vault=self.vault,
            store=self.store,
            recorded_at=self.when,
        )
        memory_coverage.ensure_coverage(
            self.project,
            "rogue-module",
            symbol="Example.rogue",
            files=["src/example.py"],
            source="canonical-route",
            vault=self.vault,
            store=self.store,
            recorded_at=self.when,
        )
        memory_coverage.ensure_coverage(
            self.project,
            "rogue-module",
            symbol="Example.rogue",
            files=["src/rogue.py"],
            source="rogue-route",
            store=rogue_store,
            recorded_at=self.when,
        )
        merged = memory_coverage.merge_coverage_store(
            self.project,
            rogue_store,
            store=self.store,
            vault=self.vault,
            delete_source=True,
        )
        coverage_root = self.vault / "Projects" / "ExampleProject" / "Memory Coverage"
        index_text = (coverage_root / "index.md").read_text(encoding="utf-8")
        records = memory_coverage._merge_records(memory_coverage._read_records(self.store))
        modules = {record.get("module") for record in records.values() if record.get("scope_kind") == "module"}
        rogue_module = next(record for record in records.values() if record.get("scope_kind") == "module" and record.get("module") == "rogue-module")
        self.assertEqual(merged["status"], "ready")
        self.assertTrue(merged["merge_verified"])
        self.assertTrue(merged["projection_verified"])
        self.assertTrue(merged["source_deleted"])
        self.assertTrue(merged["source_lock_deleted"])
        self.assertEqual(modules, {"canonical-module", "rogue-module"})
        self.assertEqual(rogue_module["files"], ["src/example.py", "src/rogue.py"])
        self.assertEqual(rogue_module["sources"], ["canonical-route", "rogue-route"])
        self.assertIn("Modules/canonical-module", index_text)
        self.assertIn("Modules/rogue-module", index_text)
        self.assertFalse(rogue_store.exists())
        self.assertFalse(Path(f"{rogue_store}.lock").exists())

    def test_delete_source_requires_a_vault_and_preserves_source(self):
        rogue_store = self.root / "rogue-no-vault" / "events.jsonl"
        memory_coverage.ensure_coverage(self.project, "rogue-module", source="rogue-route", store=rogue_store, recorded_at=self.when)
        with self.assertRaisesRegex(memory_coverage.CoverageError, "configured vault"):
            memory_coverage.merge_coverage_store(self.project, rogue_store, store=self.store, delete_source=True)
        self.assertTrue(rogue_store.is_file())

    def test_delete_source_requires_linked_owner_index_and_preserves_source(self):
        rogue_store = self.root / "rogue-unlinked" / "events.jsonl"
        memory_coverage.ensure_coverage(self.project, "rogue-module", source="rogue-route", store=rogue_store, recorded_at=self.when)
        (self.vault / "Projects" / "ExampleProject" / "index.md").unlink()
        with self.assertRaisesRegex(memory_coverage.CoverageError, "linked rendered projection"):
            memory_coverage.merge_coverage_store(self.project, rogue_store, store=self.store, vault=self.vault, delete_source=True)
        self.assertTrue(rogue_store.is_file())

    def test_source_change_during_projection_is_preserved(self):
        rogue_store = self.root / "rogue-changing" / "events.jsonl"
        memory_coverage.ensure_coverage(self.project, "rogue-module", source="rogue-route", store=rogue_store, recorded_at=self.when)
        project = memory_coverage.project_change_memory._project_identity(self.project)
        late_record = memory_coverage._scope_record(
            project,
            "module",
            "late-module",
            "",
            ["src/example.py"],
            "late-writer",
            "2026-08-06T12:01:00Z",
        )
        original_write = memory_coverage._write_obsidian

        def write_then_mutate(*args, **kwargs):
            result = original_write(*args, **kwargs)
            memory_coverage._append_records_unlocked(rogue_store, [late_record])
            return result

        with mock.patch.object(memory_coverage, "_write_obsidian", side_effect=write_then_mutate):
            with self.assertRaisesRegex(memory_coverage.CoverageError, "changed during migration"):
                memory_coverage.merge_coverage_store(self.project, rogue_store, store=self.store, vault=self.vault, delete_source=True)
        self.assertTrue(rogue_store.is_file())
        self.assertIn("late-module", rogue_store.read_text(encoding="utf-8"))

    def test_failed_projection_retry_is_idempotent_and_then_deletes_source(self):
        rogue_store = self.root / "rogue-retry" / "events.jsonl"
        memory_coverage.ensure_coverage(self.project, "rogue-module", source="rogue-route", store=rogue_store, recorded_at=self.when)
        failed_projection = {
            "status": "written",
            "written": True,
            "project_index_linked": True,
            "readback_verified": False,
            "readback_reason": "forced_failure",
        }
        with mock.patch.object(memory_coverage, "_write_obsidian", return_value=failed_projection):
            with self.assertRaisesRegex(memory_coverage.CoverageError, "linked rendered projection"):
                memory_coverage.merge_coverage_store(self.project, rogue_store, store=self.store, vault=self.vault, delete_source=True)
        self.assertTrue(rogue_store.is_file())
        first_records = memory_coverage._merge_records(memory_coverage._read_records(self.store))
        first_module = next(record for record in first_records.values() if record.get("scope_kind") == "module")
        self.assertEqual(first_module["observation_count"], 1)

        result = memory_coverage.merge_coverage_store(self.project, rogue_store, store=self.store, vault=self.vault, delete_source=True)
        final_records = memory_coverage._merge_records(memory_coverage._read_records(self.store))
        final_module = next(record for record in final_records.values() if record.get("scope_kind") == "module")
        self.assertTrue(result["source_deleted"])
        self.assertEqual(final_module["observation_count"], 1)

    def test_projection_removes_only_stale_managed_scope_pages(self):
        memory_coverage.ensure_coverage(self.project, "example-module", source="model-route", vault=self.vault, store=self.store, recorded_at=self.when)
        modules = self.vault / "Projects" / "ExampleProject" / "Memory Coverage" / "Modules"
        managed_stale = modules / "managed-stale.md"
        user_page = modules / "user-page.md"
        managed_stale.write_text(f"{memory_coverage.MANAGED_MARKER}\n# stale\n", encoding="utf-8")
        user_page.write_text("# User-owned note\n", encoding="utf-8")
        result = memory_coverage.ensure_coverage(self.project, "example-module", source="model-route", vault=self.vault, store=self.store, recorded_at=self.when)
        self.assertTrue(result["obsidian"]["readback_verified"])
        self.assertFalse(managed_stale.exists())
        self.assertTrue(user_page.is_file())


if __name__ == "__main__":
    unittest.main()

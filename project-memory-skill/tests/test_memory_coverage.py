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


if __name__ == "__main__":
    unittest.main()

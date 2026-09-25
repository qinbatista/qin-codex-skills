import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ending_memory_launch.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("ending_memory_launch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EndingLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "ExampleProject"
        self.project.mkdir()
        (self.project / "script.py").write_text("value = 1\n")
        self.completed = {"status": "complete", "task_id": "task-1", "project_root": str(self.project),
                          "outcome": {"module": "example", "summary": "Saved result", "reason": "Preserve outcome", "result": "Available", "files": ["script.py"]}}

    def prepare(self, **changes):
        args = {"project_root": self.project, "selected_model": "gpt-6-astra", "selected_effort": "ultra", "memory_available": True}
        args.update(changes)
        return MODULE.prepare_launch(self.completed, **args)

    def acknowledged(self):
        packet = self.prepare()
        return MODULE.acknowledge_launch(packet, {"threadId": "thread-1", "hostId": "local"},
                                         {"threadId": "thread-1", "projectId": None, "archived": False})

    def vault_result(self):
        return {"status": "written", "purpose": "memory_only", "event_id": "event-1", "vault_document": "AI Memory/events.jsonl",
                "read_back_verified": True, "project": "ExampleProject", "model_evidence": {"source": "runtime_receipt", "pair": "gpt-6-astra|ultra"}}

    def test_unavailable_vault_keeps_memory_pending_without_launch(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "pending", "reason": "obsidian_vault_unavailable"}):
            packet = self.prepare(memory_available=False)
        self.assertEqual(packet["status"], "pending")
        self.assertEqual(packet["reason"], "obsidian_vault_unavailable")
        self.assertIsNone(packet["create_thread"])

    def test_missing_vault_setup_enables_memory_handoff(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "created", "vault": "/vault"}):
            packet = self.prepare(memory_available=False)
        self.assertEqual(packet["status"], "pending")
        self.assertIsNotNone(packet["create_thread"])
        self.assertEqual(packet["vault_setup"]["status"], "created")

    def test_no_durable_information_skips(self):
        self.completed["outcome"] = {}
        packet = self.prepare()
        self.assertEqual(packet["status"], "skipped")
        self.assertIsNone(packet["create_thread"])

    def test_prompt_requires_only_obsidian_and_selected_model(self):
        packet = self.prepare()
        prompt = packet["create_thread"]["prompt"]
        self.assertIn("Obsidian vault", prompt)
        self.assertIn("gpt-6-astra|ultra", prompt)
        self.assertIn("without a Codex-local memory or queue", prompt)

    def test_completion_requires_vault_event_and_matching_project(self):
        packet = self.acknowledged()
        result = MODULE.record_completion(packet, self.vault_result())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["event_id"], "event-1")
        self.assertEqual(result["memory_sync"], "verified")
        for changed in ({"read_back_verified": False}, {"vault_document": "local/store.jsonl"}, {"project": "OtherProject"}, {"event_id": ""}):
            with self.assertRaises(ValueError):
                MODULE.record_completion(packet, {**self.vault_result(), **changed})

    def test_pending_writer_cannot_be_reported_as_complete(self):
        result = MODULE.record_completion(self.acknowledged(), {"status": "pending", "reason": "obsidian_vault_unavailable"})
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["reason"], "obsidian_vault_unavailable")


if __name__ == "__main__":
    unittest.main()

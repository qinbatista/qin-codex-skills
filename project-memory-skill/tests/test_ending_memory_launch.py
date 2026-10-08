import importlib.util
import json
import os
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
        cache = Path(os.environ.get("ENDING_LAUNCH_TEST_CACHE", Path(__file__).resolve().parents[2] / "Cache/temp-ending-launch-tests"))
        cache.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-ending-launch-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "ExampleProject"
        self.project.mkdir()
        (self.project / "script.py").write_text("value = 1\n")
        self.vault = Path(self.temporary.name) / "vault"
        (self.vault / "Projects").mkdir(parents=True)
        (self.vault / "AI Memory").mkdir()
        self.vault_patch = mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault)
        self.vault_patch.start()
        self.addCleanup(self.vault_patch.stop)
        self.completed = {"status": "complete", "task_id": "task-1", "project_root": str(self.project),
                          "outcome": {"module": "example", "summary": "Saved result", "reason": "Preserve outcome", "result": "Available", "files": ["script.py"]}}

    def prepare(self, **changes):
        args = {"project_root": self.project, "memory_available": True}
        args.update(changes)
        return MODULE.prepare_launch(self.completed, **args)

    def acknowledged(self):
        packet = self.prepare()
        return MODULE.acknowledge_launch(packet, {"threadId": "thread-1", "hostId": "local"},
                                         {"threadId": "thread-1", "projectId": None, "archived": False})

    def vault_result(self):
        return {"status": "written", "purpose": "memory_only", "event_id": "event-1", "vault_document": "AI Memory/events.jsonl",
                "read_back_verified": True, "project": "ExampleProject", "current_memory": {"read_back_verified": True, "maintenance_due": False}}

    def test_unavailable_vault_does_not_block_resource_audit_launch(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "pending", "reason": "obsidian_vault_unavailable"}):
            packet = self.prepare(memory_available=False)
        self.assertEqual(packet["status"], "pending")
        self.assertEqual(packet["reason"], "obsidian_vault_unavailable")
        self.assertIsNotNone(packet["create_thread"])
        self.assertEqual(packet["memory_status"], "pending")
        self.assertTrue(packet["resource_audit"])

    def test_unavailable_vault_without_a_resource_audit_remains_pending(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "pending", "reason": "obsidian_vault_unavailable"}):
            packet = self.prepare(memory_available=False, resource_audit=False)
        self.assertIsNone(packet["create_thread"])

    def test_missing_vault_setup_enables_memory_handoff(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "created", "vault": "/vault"}):
            packet = self.prepare(memory_available=False)
        self.assertEqual(packet["status"], "pending")
        self.assertIsNotNone(packet["create_thread"])
        self.assertEqual(packet["vault_setup"]["status"], "created")

    def test_no_durable_information_skips_memory_only_and_still_audits_resources(self):
        self.completed["outcome"] = {}
        packet = self.prepare()
        self.assertEqual(packet["memory_status"], "skipped")
        self.assertIsNotNone(packet["create_thread"])
        skipped = self.prepare(resource_audit=False)
        self.assertEqual(skipped["status"], "skipped")
        self.assertIsNone(skipped["create_thread"])

    def test_handoff_uses_app_defaults_and_scoped_obsidian_prompt(self):
        packet = self.prepare()
        prompt = packet["create_thread"]["prompt"]
        self.assertIn("Obsidian vault", prompt)
        self.assertEqual(set(packet["create_thread"]), {"target", "title", "prompt"})
        self.assertEqual(packet["create_thread"]["target"], {"type": "projectless"})
        self.assertIn("without a Codex-local memory or queue", prompt)
        self.assertIn(json.dumps(str(SCRIPT.with_name("ending_memory.py"))), prompt)
        self.assertIn("ending-resource-audit.md", prompt)
        self.assertIn("In parallel", prompt)
        self.assertIn("review or reuse", prompt)
        self.assertIn("up to ten recent chats", prompt)
        self.assertIn("unavailable memory vault must not block", prompt)
        for resource_audit in (True, False):
            with self.subTest(resource_audit=resource_audit):
                handoff = self.prepare(resource_audit=resource_audit)["create_thread"]
                self.assertEqual(handoff["title"], "Ending Task | ExampleProject")
                self.assertEqual(set(handoff), {"target", "title", "prompt"})
                self.assertEqual(handoff["target"], {"type": "projectless"})

    def test_handoff_keeps_the_installation_that_prepared_it(self):
        installed = self.project / ".agents" / "skills" / "project-memory-skill" / "scripts" / "ending_memory_launch.py"
        with mock.patch.object(MODULE, "__file__", str(installed)):
            packet = self.prepare()
        writer = installed.with_name("ending_memory.py")
        self.assertIn(json.dumps(str(writer)), packet["create_thread"]["prompt"])

    def test_existing_ending_is_reused_only_for_the_same_outcome(self):
        existing = self.acknowledged()
        reused = self.prepare(previous=existing)
        self.assertEqual(reused["thread_id"], "thread-1")
        self.assertIsNone(reused["create_thread"])
        self.completed["outcome"]["summary"] = "Changed durable result"
        with self.assertRaisesRegex(ValueError, "different outcome or project"):
            self.prepare(previous=existing)

    def test_completion_requires_vault_event_and_matching_project(self):
        packet = self.acknowledged()
        result = MODULE.record_completion(packet, self.vault_result(), self.resource_result())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["event_id"], "event-1")
        self.assertEqual(result["memory_sync"], "verified")
        for changed in ({"read_back_verified": False}, {"vault_document": "local/store.jsonl"}, {"project": "OtherProject"}, {"event_id": ""}, {"current_memory": {}}):
            with self.assertRaises(ValueError):
                MODULE.record_completion(packet, {**self.vault_result(), **changed})

    def resource_result(self, **changes):
        return {"status": "complete", "origin_task_id": "task-1", "read_back_verified": True, "released": [], "retained": [], "pending": [], **changes}

    def test_memory_success_cannot_hide_pending_cleanup(self):
        result = MODULE.record_completion(self.acknowledged(), self.vault_result())
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["memory_status"], "complete")
        self.assertEqual(result["resource_status"], "pending")

    def test_resource_success_survives_pending_or_skipped_memory(self):
        for memory_result in ({"status": "pending", "reason": "vault unavailable"}, {"status": "skipped", "reason": "no_durable_information"}):
            with self.subTest(memory_result=memory_result):
                result = MODULE.record_completion(self.acknowledged(), memory_result, self.resource_result())
                self.assertEqual(result["resource_status"], "complete")
                self.assertEqual(result["status"], "pending")

    def test_resource_completion_requires_originating_task_and_real_readback(self):
        for changes in ({"origin_task_id": "other"}, {"read_back_verified": False}, {"status": "invented"}):
            with self.assertRaises(ValueError):
                MODULE.record_completion(self.acknowledged(), self.vault_result(), self.resource_result(**changes))

    def test_handoff_binds_method_evidence_before_ending(self):
        self.completed["outcome"]["symbols"] = ["Worker.read"]
        packet = self.prepare()
        prompt = packet["create_thread"]["prompt"]
        data = json.loads(prompt.split("Completed outcome data:\n", 1)[1])
        entry = data["outcome"]["memories"][0]
        self.assertEqual((entry["module"], entry["file"], entry["symbol"]), ("example", "script.py", "Worker.read"))
        self.assertEqual(len(entry["source_hashes"]["script.py"]), 64)
        (self.project / "script.py").write_text("value = 2\n")
        with self.assertRaisesRegex(ValueError, "different outcome or project"):
            self.prepare(previous=packet)

    def test_handoff_carries_merged_corrections_and_pending_items(self):
        scope = {"scope": "module", "module": "example"}
        established = {**scope, "summary": "Keep the verified original contract", "reason": "The user corrected repeated lost settings", "result": "The original restoration workaround passed", "decisions": ["Preserve the correction"], "risks": ["Pending: verify another machine"], "verification_status": "passed", "verification": ["Observed the original restoration output"]}
        (self.vault / "AI Memory/events.jsonl").write_text(json.dumps({"event_id": "original-event", "project": "ExampleProject"}) + "\n", encoding="utf-8")
        MODULE.knowledge.apply_entries(self.project, self.vault, [established], event_id="original-event")
        self.completed["outcome"]["memories"] = [{**scope, "summary": "Keep the revised restoration contract pending verification"}]
        packet = self.prepare()
        data = json.loads(packet["create_thread"]["prompt"].split("Completed outcome data:\n", 1)[1])
        current = data["outcome"]["memories"][0]
        for field in ("reason", "result", "decisions", "risks"):
            self.assertEqual(current[field], established[field])
        self.assertEqual(current["verification_status"], "not-run")
        self.assertEqual(current["verification"], [])
        self.assertEqual(len(current["source_hashes"]["script.py"]), 64)
        self.assertIn("user corrections", packet["create_thread"]["prompt"])

    def test_pending_writer_cannot_be_reported_as_complete(self):
        result = MODULE.record_completion(self.acknowledged(), {"status": "pending", "reason": "obsidian_vault_unavailable"})
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["reason"], "obsidian_vault_unavailable")

    def test_due_synthesis_blocks_completion_while_resource_result_survives(self):
        memory = {**self.vault_result(), "current_memory": {"read_back_verified": True, "maintenance_due": True}}
        result = MODULE.record_completion(self.acknowledged(), memory, self.resource_result())
        self.assertEqual((result["status"], result["memory_status"], result["resource_status"]), ("pending", "pending", "complete"))
        self.assertEqual(result["reason"], "project_synthesis_due")
        with self.assertRaisesRegex(ValueError, "explicit synthesis cadence"):
            MODULE.record_completion(self.acknowledged(), {**memory, "current_memory": {"read_back_verified": True}}, self.resource_result())

    def test_empty_outcome_still_prepares_due_synthesis_without_resource_audit(self):
        entry = {"scope": "module", "module": "example", "summary": "Preserve the established restoration contract", "verification_status": "partial", "verification": ["Only the original environment was observed"]}
        (self.vault / "AI Memory/events.jsonl").write_text(json.dumps({"event_id": "original-event", "project": "ExampleProject"}) + "\n", encoding="utf-8")
        MODULE.knowledge.apply_entries(self.project, self.vault, [entry], event_id="original-event")
        self.completed["outcome"] = {}
        packet = self.prepare(resource_audit=False)
        self.assertTrue(packet["consolidation_required"])
        self.assertTrue(packet["memory_required"])
        self.assertEqual(packet["synthesis_context"]["entries"][0]["verification_status"], "partial")
        self.assertIsNotNone(packet["create_thread"])
        self.completed["outcome"] = {"consolidation": {"summary": "The original restoration environment was observed, with other environments pending"}}
        consolidated = self.prepare(resource_audit=False)
        self.assertIsNotNone(consolidated["create_thread"])
        data = json.loads(consolidated["create_thread"]["prompt"].split("Completed outcome data:\n", 1)[1])
        self.assertNotIn("memories", data["outcome"])
        self.assertNotIn("files", data["outcome"])

if __name__ == "__main__":
    unittest.main()

import importlib.util
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ARTIFACT_PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT_PROJECT / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root, validate_external_directory


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ending_memory_launch.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("ending_memory_launch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EndingLaunchTests(unittest.TestCase):
    def setUp(self):
        override = os.environ.get("ENDING_LAUNCH_TEST_CACHE")
        cache = validate_external_directory(override, ARTIFACT_PROJECT) if override is not None else resolve_task_artifact_root(ARTIFACT_PROJECT, "ending-launch-tests", create=True)
        cache.mkdir(parents=True, exist_ok=True)
        if override is None:
            self.addCleanup(cache.rmdir)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-ending-launch-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "ExampleProject"
        self.project.mkdir()
        (self.project / "script.py").write_text("value = 1\n")
        for relative, content in self.index_documents().items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.vault = Path(self.temporary.name) / "vault"
        (self.vault / "Projects").mkdir(parents=True)
        (self.vault / "AI Memory").mkdir()
        self.vault_patch = mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault)
        self.vault_patch.start()
        self.addCleanup(self.vault_patch.stop)
        self.completed = {"status": "complete", "task_id": "task-1", "project_root": str(self.project),
                          "outcome": {"module": "example", "summary": "Saved result", "reason": "Preserve outcome", "result": "Available", "files": ["script.py"]}}

    def prepare(self, **changes):
        args = {"project_root": self.project, "memory_available": True, "native_delete_available": True}
        args.update(changes)
        return MODULE.prepare_launch(self.completed, **args)

    def index_documents(self):
        directory = ".agents/skills/ai-index"
        rules = {name: f"{directory}/{name}.md" for name in ("repository", "structure", "verification")}
        manifest = {"schema_version": 1, "rules": rules, "modules": [{"id": "example", "summary": "Example project behavior", "document": f"{directory}/example.md", "sources": ["script.py"]}]}
        return {"AGENTS.md": f"# ExampleProject\nRead [AI index]({directory}/SKILL.md).\n", f"{directory}/SKILL.md": "---\nname: ai-index\ndescription: Route ExampleProject tasks to their owners.\n---\nRead [the route map](index.json).\n", f"{directory}/index.json": json.dumps(manifest), f"{directory}/example.md": "# Example\nThe script owns the example behavior.\n", **{relative: f"# {name.title()}\nKeep this responsibility in its declared owner.\n" for name, relative in rules.items()}}

    def index_result(self, **changes):
        return {"project_root": str(self.project), "origin_task_id": "task-1", "status": "complete", "read_back_verified": True, "source": "project_ai_index.py check and exact guidance readback", "changed_files": [], **changes}

    def complete(self, packet, memory_result, resource_result=None):
        return MODULE.record_completion(packet, memory_result, resource_result, self.index_result())

    def test_missing_deletion_route_never_creates_a_saved_ending(self):
        packet = self.prepare(native_delete_available=False)
        self.assertEqual(packet["status"], "inline_required")
        self.assertIsNone(packet["create_thread"])
        self.assertFalse(packet["visible"])
        self.assertEqual(packet["closeout_owner"], "current_chat")
        with self.assertRaises(ValueError):
            self.prepare(native_delete_available="yes")

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
        self.assertEqual(packet["reason"], "obsidian_maintenance_unavailable")
        self.assertIsNotNone(packet["create_thread"])
        self.assertEqual(packet["memory_status"], "pending")
        self.assertTrue(packet["resource_audit"])

    def test_unavailable_vault_still_launches_independent_memory_work(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", return_value={"status": "pending", "reason": "obsidian_vault_unavailable"}):
            packet = self.prepare(memory_available=False, resource_audit=False)
        self.assertIsNotNone(packet["create_thread"])
        self.assertFalse(packet["parent_wait_required"])

    def test_parent_never_runs_vault_setup_recall_or_synthesis(self):
        with mock.patch("obsidian_vault_setup.ensure_vault", side_effect=AssertionError("parent vault setup")), mock.patch.object(MODULE.memory, "_resolve_vault", side_effect=AssertionError("parent vault resolution")), mock.patch.object(MODULE.knowledge, "load_knowledge", side_effect=AssertionError("parent recall")), mock.patch.object(MODULE.knowledge, "synthesis_context", side_effect=AssertionError("parent synthesis")):
            for memory_available in (True, False):
                for resource_audit in (True, False):
                    packet = self.prepare(memory_available=memory_available, resource_audit=resource_audit)
                    self.assertIsNotNone(packet["create_thread"])
                    self.assertTrue(packet["maintenance_check_required"])
                    self.assertFalse(packet["parent_wait_required"])

    def test_no_durable_information_defers_cadence_decision_to_ending(self):
        self.completed["outcome"] = {}
        packet = self.prepare()
        self.assertEqual(packet["memory_status"], "pending")
        self.assertIsNotNone(packet["create_thread"])
        memory_only = self.prepare(resource_audit=False)
        self.assertTrue(memory_only["maintenance_check_required"])
        self.assertIsNotNone(memory_only["create_thread"])

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
        self.assertIn("remove only this exact Ending conversation as the final step", prompt)
        self.assertIn("ending_conversation.py", prompt)
        self.assertIn("native thread/delete API", prompt)
        self.assertIn("Do not substitute set_thread_archived for deletion", prompt)
        self.assertIn("stop immediately without further messages", prompt)
        self.assertNotIn("do not move, reorder, open, archive, delete", prompt)
        for resource_audit in (True, False):
            with self.subTest(resource_audit=resource_audit):
                handoff = self.prepare(resource_audit=resource_audit)["create_thread"]
                self.assertEqual(handoff["title"], "Ending Task | ExampleProject")
                self.assertEqual(set(handoff), {"target", "title", "prompt"})
                self.assertEqual(handoff["target"], {"type": "projectless"})

    def test_app_acknowledgement_releases_parent_without_ending_readback(self):
        packet = MODULE.acknowledge_launch(self.prepare(), {"threadId": "thread-1", "hostId": "local"})
        self.assertEqual(packet["status"], "launched")
        self.assertTrue(packet["parent_may_finish"])
        self.assertFalse(packet["parent_wait_required"])
        self.assertEqual(packet["completion_owner"], "ending")
        self.assertIsNone(packet["create_thread"])
        with self.assertRaisesRegex(ValueError, "projectless"):
            MODULE.acknowledge_launch(self.prepare(), {"threadId": "thread-1", "hostId": "local"}, {"threadId": "other", "projectId": None})

    def test_handoff_binds_origin_and_keeps_recovery_in_ending(self):
        self.completed["host_id"] = "remote-ssh-discovered:mypi"
        packet = self.prepare()
        prompt = packet["create_thread"]["prompt"]
        data = json.loads(prompt.split("Completed outcome data:\n", 1)[1])
        self.assertEqual(data["origin_thread"], {"threadId": "task-1", "hostId": "remote-ssh-discovered:mypi"})
        self.assertEqual(packet["origin_thread"], data["origin_thread"])
        self.assertTrue(packet["deletion_required"])
        self.assertIn("read_thread with the exact origin_thread", prompt)
        self.assertIn("must never wait for Ending at any stage", prompt)
        self.assertIn("Do not message, wake or wait for the origin thread", prompt)
        self.assertIn("Deletion of this Ending is mandatory", prompt)
        self.assertNotIn("leave that step to the originating task", prompt)
        self.assertNotIn("wait_threads", prompt)
        with self.assertRaisesRegex(ValueError, "different outcome or project"):
            self.prepare(previous={**packet, "outcome_fingerprint": "other"})

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
        result = self.complete(packet, self.vault_result(), self.resource_result())
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["branch_status"], "complete")
        self.assertEqual(result["event_id"], "event-1")
        self.assertEqual(result["memory_sync"], "verified")
        self.assertEqual(result["conversation_cleanup"]["status"], "ready")
        self.assertEqual(result["conversation_cleanup"]["thread_id"], "thread-1")
        for changed in ({"read_back_verified": False}, {"vault_document": "local/store.jsonl"}, {"project": "OtherProject"}, {"event_id": ""}, {"current_memory": {}}):
            with self.assertRaises(ValueError):
                self.complete(packet, {**self.vault_result(), **changed})

    def resource_result(self, **changes):
        return {"status": "complete", "origin_task_id": "task-1", "read_back_verified": True, "released": [], "retained": [], "pending": [], **changes}

    def test_memory_success_cannot_hide_pending_cleanup(self):
        result = self.complete(self.acknowledged(), self.vault_result())
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["memory_status"], "complete")
        self.assertEqual(result["resource_status"], "pending")
        self.assertEqual(result["conversation_cleanup"]["status"], "waiting")

    def test_native_archive_is_separate_from_local_deletion(self):
        completed = self.complete(self.acknowledged(), self.vault_result(), self.resource_result())
        archive = {"thread_id": "thread-1", "host_id": "local", "status": "archived", "read_back_verified": True, "source": "native archive receipt and archived-thread readback"}
        result = MODULE.record_conversation_cleanup(completed, archive)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["branch_status"], "complete")
        self.assertEqual(result["conversation_cleanup"]["status"], "archived")
        self.assertEqual(result["conversation_cleanup"]["local_deletion_status"], "pending")
        self.assertEqual(result["conversation_cleanup"]["reason"], "archive_retains_local_records")
        deleted = MODULE.record_conversation_cleanup(result, {**archive, "status": "deleted", "local_record_absent": True})
        self.assertEqual(deleted["status"], "complete")
        self.assertEqual(deleted["conversation_cleanup"]["local_deletion_status"], "complete")
        self.assertNotIn("reason", deleted["conversation_cleanup"])
        for change in ({"thread_id": "other"}, {"host_id": "other"}, {"read_back_verified": False}, {"source": ""}, {"local_record_absent": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                MODULE.record_conversation_cleanup(completed, {**archive, **change})

    def test_cleanup_waits_for_both_branches_and_native_local_absence(self):
        receipt = {"thread_id": "thread-1", "host_id": "local", "status": "deleted", "read_back_verified": True, "source": "native deletion receipt and local-record absence readback", "local_record_absent": True}
        for memory_result, resource_result in (({"status": "pending", "reason": "vault unavailable"}, self.resource_result()), (self.vault_result(), self.resource_result(status="pending"))):
            packet = self.complete(self.acknowledged(), memory_result, resource_result)
            with self.assertRaisesRegex(ValueError, "branch completion"):
                MODULE.record_conversation_cleanup(packet, receipt)
        completed = self.complete(self.acknowledged(), self.vault_result(), self.resource_result())
        with self.assertRaisesRegex(ValueError, "local-record absence"):
            MODULE.record_conversation_cleanup(completed, {**receipt, "local_record_absent": False})
        deleted = MODULE.record_conversation_cleanup(completed, receipt)
        self.assertEqual(deleted["conversation_cleanup"]["local_deletion_status"], "complete")
        pending = MODULE.record_conversation_cleanup(completed, {"thread_id": "thread-1", "host_id": "local", "status": "pending", "reason": "native action unavailable"})
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["conversation_cleanup"]["local_deletion_status"], "pending")

    def test_resource_success_survives_pending_or_skipped_memory(self):
        for memory_result in ({"status": "pending", "reason": "vault unavailable"}, {"status": "skipped", "reason": "no_durable_information"}):
            with self.subTest(memory_result=memory_result):
                result = self.complete(self.acknowledged(), memory_result, self.resource_result())
                self.assertEqual(result["resource_status"], "complete")
                self.assertEqual(result["status"], "pending")

    def test_resource_completion_requires_originating_task_and_real_readback(self):
        for changes in ({"origin_task_id": "other"}, {"read_back_verified": False}, {"status": "invented"}):
            with self.assertRaises(ValueError):
                self.complete(self.acknowledged(), self.vault_result(), self.resource_result(**changes))

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

    def test_handoff_leaves_existing_knowledge_merge_to_ending(self):
        scope = {"scope": "module", "module": "example"}
        established = {**scope, "summary": "Keep the verified original contract", "reason": "The user corrected repeated lost settings", "result": "The original restoration workaround passed", "decisions": ["Preserve the correction"], "risks": ["Pending: verify another machine"], "verification_status": "passed", "verification": ["Observed the original restoration output"]}
        (self.vault / "AI Memory/events.jsonl").write_text(json.dumps({"event_id": "original-event", "project": "ExampleProject"}) + "\n", encoding="utf-8")
        MODULE.knowledge.apply_entries(self.project, self.vault, [established], event_id="original-event")
        self.completed["outcome"]["memories"] = [{**scope, "summary": "Keep the revised restoration contract pending verification"}]
        packet = self.prepare()
        data = json.loads(packet["create_thread"]["prompt"].split("Completed outcome data:\n", 1)[1])
        current = data["outcome"]["memories"][0]
        self.assertEqual(current["summary"], "Keep the revised restoration contract pending verification")
        self.assertNotIn("risks", current)
        existing = MODULE.knowledge.load_knowledge(self.project, self.vault)["entries"]
        merged = MODULE.prepare_entries(data["outcome"], self.project, existing_entries=existing)[0]
        for field in ("reason", "result", "decisions", "risks"):
            self.assertEqual(merged[field], established[field])
        self.assertEqual(merged["verification_status"], "not-run")
        self.assertEqual(merged["verification"], [])
        self.assertEqual(len(current["source_hashes"]["script.py"]), 64)
        self.assertIn("user corrections", packet["create_thread"]["prompt"])

    def test_pending_writer_cannot_be_reported_as_complete(self):
        result = self.complete(self.acknowledged(), {"status": "pending", "reason": "obsidian_vault_unavailable"})
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["reason"], "obsidian_vault_unavailable")

    def test_due_synthesis_blocks_completion_while_resource_result_survives(self):
        memory = {**self.vault_result(), "current_memory": {"read_back_verified": True, "maintenance_due": True}}
        result = self.complete(self.acknowledged(), memory, self.resource_result())
        self.assertEqual((result["status"], result["memory_status"], result["resource_status"]), ("pending", "pending", "complete"))
        self.assertEqual(result["reason"], "project_synthesis_due")
        with self.assertRaisesRegex(ValueError, "explicit synthesis cadence"):
            self.complete(self.acknowledged(), {**memory, "current_memory": {"read_back_verified": True}}, self.resource_result())

    def test_empty_outcome_still_prepares_due_synthesis_without_resource_audit(self):
        entry = {"scope": "module", "module": "example", "summary": "Preserve the established restoration contract", "verification_status": "partial", "verification": ["Only the original environment was observed"]}
        (self.vault / "AI Memory/events.jsonl").write_text(json.dumps({"event_id": "original-event", "project": "ExampleProject"}) + "\n", encoding="utf-8")
        MODULE.knowledge.apply_entries(self.project, self.vault, [entry], event_id="original-event")
        self.completed["outcome"] = {}
        packet = self.prepare(resource_audit=False)
        self.assertTrue(packet["maintenance_check_required"])
        self.assertFalse(packet["consolidation_required"])
        self.assertTrue(packet["memory_required"])
        self.assertNotIn("synthesis_context", packet)
        self.assertIsNotNone(packet["create_thread"])
        self.completed["outcome"] = {"consolidation": {"summary": "The original restoration environment was observed, with other environments pending"}}
        consolidated = self.prepare(resource_audit=False)
        self.assertIsNotNone(consolidated["create_thread"])
        data = json.loads(consolidated["create_thread"]["prompt"].split("Completed outcome data:\n", 1)[1])
        self.assertNotIn("memories", data["outcome"])
        self.assertNotIn("files", data["outcome"])

    def test_empty_memory_still_requires_residual_project_index_inspection(self):
        self.completed["outcome"] = {}
        packet = self.prepare()
        self.assertTrue(packet["index_required"])
        self.assertEqual(packet["index_status"], "pending")
        self.assertEqual(packet["project_index"], {"project_root": str(self.project), "origin_task_id": "task-1", "phase": "end", "plan": None, "skip_reason": None})
        prompt = packet["create_thread"]["prompt"]
        self.assertIn("Always run inspect --project-root ROOT --phase end", prompt)
        self.assertIn("Do not create additional AGENTS.md files", prompt)
        self.assertIn("local-only unless separate explicit delivery authorization", prompt)
        data = json.loads(prompt.split("Completed outcome data:\n", 1)[1])
        self.assertEqual(data["project_index"], packet["project_index"])
        self.assertEqual(data["outcome"], {})

    def index_plan(self):
        root_document = self.project / "AGENTS.md"
        return {"schema_version": 1, "project_root": str(self.project), "evidence": {"script.py": hashlib.sha256((self.project / "script.py").read_bytes()).hexdigest()}, "files": [{"path": "AGENTS.md", "expected_sha256": hashlib.sha256(root_document.read_bytes()).hexdigest(), "content": root_document.read_text() + "Keep example behavior in script.py.\n"}]}

    def test_index_plan_handoff_uses_shared_scope_and_source_guards(self):
        plan = self.index_plan()
        packet = self.prepare(project_index={"project_root": str(self.project), "origin_task_id": "task-1", "plan": plan})
        self.assertEqual(packet["project_index"]["plan"], plan)
        self.assertNotIn("project_index", json.loads(packet["create_thread"]["prompt"].split("Completed outcome data:\n", 1)[1])["outcome"])
        for path in ("../outside.md", "script.py", ".agents/skills/ai-index/nested/AGENTS.md", "plugins/ai-index/SKILL.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.prepare(project_index={"plan": {**plan, "files": [{**plan["files"][0], "path": path}]}})
        (self.project / "script.py").write_text("value = 2\n")
        with self.assertRaisesRegex(ValueError, "source evidence"):
            self.prepare(project_index={"plan": plan})
        plan = self.index_plan()
        (self.project / "AGENTS.md").write_text("Concurrent project guidance\n")
        with self.assertRaisesRegex(ValueError, "preimage changed"):
            self.prepare(project_index={"plan": plan})

    def test_index_handoff_rejects_cross_project_and_origin_mismatches(self):
        for handoff in ({"project_root": str(self.project.parent)}, {"project_root": "relative"}, {"origin_task_id": "other"}, {"skip_reason": "unnecessary"}, {"skip_reason": "read_only", "plan": self.index_plan()}):
            with self.subTest(handoff=handoff), self.assertRaises(ValueError):
                self.prepare(project_index=handoff)
        packet = self.prepare()
        with self.assertRaisesRegex(ValueError, "different outcome or project"):
            self.prepare(previous=packet, project_index={"skip_reason": "read_only"})

    def test_plan_postimages_and_source_evidence_gate_closure_and_scoped_refresh(self):
        helper = MODULE.project_index_helper()
        obsolete = ".agents/skills/ai-index/obsolete.md"
        (self.project / obsolete).write_text("Obsolete detail\n")
        plan = self.index_plan()
        plan["evidence"]["AGENTS.md"] = plan["files"][0]["expected_sha256"]
        plan["evidence"][obsolete] = helper.file_hash(self.project / obsolete)
        plan["files"].append({"path": obsolete, "expected_sha256": plan["evidence"][obsolete], "content": None})
        packet = MODULE.acknowledge_launch(self.prepare(project_index={"plan": plan}), {"threadId": "thread-1", "hostId": "local"})
        for supplied in (self.index_result(), self.index_result(status="skipped", reason="unchanged")):
            before = MODULE.record_completion(packet, self.vault_result(), self.resource_result(), supplied)
            self.assertEqual(before["index_result"]["check"]["status"], "ready")
            self.assertEqual(before["index_status"], "pending")
            self.assertEqual(before["index_result"]["reason"], "project_index_plan_readback_failed")
            self.assertEqual(before["resource_status"], "complete")
        with mock.patch.dict(os.environ, {"YOFA_TASK_ARTIFACT_ROOT": str(self.project.parent / "artifacts")}):
            applied = helper.apply_plan(self.project, plan, self.project.parent / "apply-original")
            self.assertEqual(applied["status"], "complete")
            after = self.complete(packet, self.vault_result(), self.resource_result())
            self.assertEqual(after["index_status"], "complete")
            self.assertEqual(after["index_result"]["plan_readback"]["postimages"][obsolete], {"expected": None, "actual": None})
            self.assertEqual(set(after["index_result"]["plan_readback"]["evidence"]), {"script.py"})
            self.assertEqual(set(after["index_result"]["changed_files"]), {"AGENTS.md", obsolete})
            self.assertEqual(after["index_result"]["delivery"], "local_only")
            (self.project / "script.py").write_text("value = 2\n")
            drifted = self.complete(packet, self.vault_result(), self.resource_result())
            self.assertEqual((drifted["index_status"], drifted["resource_status"]), ("pending", "complete"))
            self.assertIn("source evidence changed", drifted["index_result"]["plan_readback"]["issues"][0])
            refreshed_plan = self.index_plan()
            refreshed = MODULE.refresh_index_plan(drifted, {"plan": refreshed_plan})
            for field in ("thread_id", "origin_task_id", "project_key", "project_owner"):
                self.assertEqual(refreshed[field], packet[field])
            self.assertEqual(refreshed["conversation_cleanup"]["status"], "waiting")
            self.assertEqual(helper.apply_plan(self.project, refreshed_plan, self.project.parent / "apply-refreshed")["status"], "complete")
            self.assertEqual(self.complete(refreshed, self.vault_result(), self.resource_result())["index_status"], "complete")
        for handoff in ({}, {"origin_task_id": "other", "plan": self.index_plan()}, {"project_root": str(self.project.parent), "plan": self.index_plan()}):
            with self.subTest(handoff=handoff), self.assertRaises(ValueError):
                MODULE.refresh_index_plan(packet, handoff)

    def test_index_completion_runs_current_helper_and_preserves_cleanup_results(self):
        packet = self.acknowledged()
        result = self.complete(packet, self.vault_result(), self.resource_result())
        self.assertEqual(result["index_status"], "complete")
        self.assertEqual(result["index_result"]["check"]["status"], "ready")
        self.assertEqual(result["index_result"]["check"]["project_root"], str(self.project))
        self.assertEqual(result["index_result"]["check"]["guidance_hashes"]["AGENTS.md"], hashlib.sha256((self.project / "AGENTS.md").read_bytes()).hexdigest())
        (self.project / ".agents/skills/ai-index/example.md").unlink()
        result = self.complete(packet, self.vault_result(), self.resource_result())
        self.assertEqual((result["index_status"], result["memory_status"], result["resource_status"]), ("pending", "complete", "complete"))
        self.assertEqual(result["index_result"]["reason"], "project_index_check_failed")
        self.assertEqual(result["conversation_cleanup"]["status"], "waiting")

    def test_missing_or_pending_index_result_cannot_complete_new_handoffs(self):
        packet = self.acknowledged()
        for index_result in (None, self.index_result(status="pending", reason="source changed", read_back_verified=False)):
            result = MODULE.record_completion(packet, self.vault_result(), self.resource_result(), index_result)
            self.assertEqual(result["branch_status"], "pending")
            self.assertEqual(result["resource_status"], "complete")
            with self.assertRaisesRegex(ValueError, "branch completion"):
                MODULE.record_conversation_cleanup(result, {})
        for changed in ({"project_root": str(self.project.parent)}, {"origin_task_id": "other"}, {"read_back_verified": False}, {"source": ""}, {"status": "invented"}, {"changed_files": ["script.py"]}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                MODULE.record_completion(packet, self.vault_result(), self.resource_result(), self.index_result(**changed))

    def test_index_boundary_skips_are_explicit_and_unchanged_requires_real_check(self):
        for reason in ("read_only", "no_project"):
            packet = MODULE.acknowledge_launch(self.prepare(project_index={"skip_reason": reason}), {"threadId": "thread-1", "hostId": "local"})
            original = json.dumps(packet, sort_keys=True)
            for handoff in ({"plan": self.index_plan()}, {"plan": self.index_plan(), "skip_reason": None}):
                with self.subTest(reason=reason, handoff=handoff), self.assertRaisesRegex(ValueError, "originating handoff boundary"):
                    MODULE.refresh_index_plan(packet, handoff)
                self.assertEqual(json.dumps(packet, sort_keys=True), original)
            for supplied in (self.index_result(), self.index_result(changed_files=["AGENTS.md"]), self.index_result(status="skipped", reason="unchanged"), self.index_result(status="skipped", reason=reason, changed_files=["AGENTS.md"])):
                with self.subTest(reason=reason, supplied=supplied):
                    result = MODULE.record_completion(packet, self.vault_result(), self.resource_result(), supplied)
                    self.assertEqual((result["index_status"], result["resource_status"]), ("pending", "complete"))
                    self.assertEqual(result["index_result"]["reason"], "project_index_boundary_requires_skip")
                    self.assertEqual(result["index_result"]["boundary"], reason)
            result = MODULE.record_completion(packet, self.vault_result(), self.resource_result(), self.index_result(status="skipped", reason=reason))
            self.assertEqual(result["index_status"], "skipped")
            with self.assertRaisesRegex(ValueError, "boundary skip"):
                MODULE.record_completion(self.acknowledged(), self.vault_result(), self.resource_result(), self.index_result(status="skipped", reason=reason))
        result = MODULE.record_completion(self.acknowledged(), self.vault_result(), self.resource_result(), self.index_result(status="skipped", reason="unchanged"))
        self.assertEqual(result["index_result"]["check"]["status"], "ready")
        with self.assertRaises(ValueError):
            MODULE.record_completion(self.acknowledged(), self.vault_result(), self.resource_result(), self.index_result(status="skipped", reason="unchanged", changed_files=["AGENTS.md"]))

    def test_legacy_packets_do_not_acquire_a_new_completion_obligation(self):
        packet = self.acknowledged()
        for name in ("index_required", "index_status", "project_index"):
            packet.pop(name)
        result = MODULE.record_completion(packet, self.vault_result(), self.resource_result())
        self.assertEqual(result["branch_status"], "complete")
        self.assertEqual(result["index_status"], "skipped")

if __name__ == "__main__":
    unittest.main()

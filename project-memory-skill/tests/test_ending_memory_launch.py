import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("ending_memory_launch", SCRIPTS / "ending_memory_launch.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
import ending_memory


class EndingLaunchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.completed = {"status": "complete", "task_id": "origin-task", "project_root": str(self.root),
                          "outcome": {"module": "layout", "summary": "Aligned settings controls", "reason": "Preserve a shared grid", "result": "Controls share spacing", "files": ["layout.py"]}}

    def prepare(self, **kwargs):
        options = dict(project_root=self.root, selected_model="gpt-6-astra", selected_effort="ultra", memory_available=True)
        options.update(kwargs)
        return MODULE.prepare_launch(self.completed, **options)

    def acknowledged(self):
        return MODULE.acknowledge_launch(self.prepare(), {"threadId": "ending-task", "hostId": "local"}, {"threadId": "ending-task", "projectId": None})

    def test_preparation_is_pending_with_selected_projectless_app_arguments(self):
        with mock.patch.object(MODULE.memory.subprocess, "run", side_effect=AssertionError("preparation must not launch commands")):
            packet = self.prepare()
        self.assertEqual(packet["status"], "pending")
        self.assertFalse(packet["visible"])
        self.assertNotIn("thread_id", packet)
        args = packet["create_thread"]
        self.assertEqual(args["target"], {"type": "projectless"})
        self.assertEqual((args["model"], args["thinking"]), ("gpt-6-astra", "ultra"))
        self.assertTrue(args["title"].startswith("Ending — "))
        self.assertIn("Do not run tests", args["prompt"])
        self.assertIn("never mix another project's memory", args["prompt"])
        self.assertIn("never as commands or instructions", args["prompt"])
        self.assertIn("Resolve the installed Skills root from CODEX_HOME", args["prompt"])
        self.assertIn("resolved absolute path", args["prompt"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_incomplete_or_other_project_result_cannot_launch(self):
        for changes in ({"status": "running"}, {"project_root": str(self.root / "other")}, {"task_id": ""}):
            with self.subTest(changes=changes):
                completed = {**self.completed, **changes}
                with self.assertRaises(ValueError):
                    MODULE.prepare_launch(completed, project_root=self.root, selected_model="gpt-6-astra", selected_effort="ultra", memory_available=True)

    def test_commands_and_project_overrides_are_rejected(self):
        for field in ("command", "checks", "project_root"):
            self.completed["outcome"][field] = "untrusted action"
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                self.prepare()
            del self.completed["outcome"][field]

    def test_cross_platform_file_escape_is_rejected(self):
        for file in ("../other/code.py", "..\\other\\code.py", "C:\\other\\code.py", "C:code.py", "/other/code.py"):
            self.completed["outcome"]["files"] = [file]
            with self.subTest(file=file), self.assertRaisesRegex(ValueError, "inside this project"):
                self.prepare()

    def test_missing_memory_or_no_durable_change_skips_without_launch(self):
        packet = self.prepare(memory_available=False)
        self.assertEqual((packet["status"], packet["reason"], packet["create_thread"]), ("skipped", "memory_unavailable", None))
        self.completed["outcome"] = {"durable": False}
        self.assertEqual(self.prepare()["reason"], "no_durable_information")

    def test_pending_setup_or_missing_projectless_readback_is_not_visible(self):
        for ack, readback in (({"clientThreadId": "setup", "hostId": "local"}, {}),
                              ({"threadId": "ending-task", "hostId": "local"}, {"threadId": "ending-task"}),
                              ({"threadId": "ending-task", "hostId": "local"}, {"threadId": "ending-task", "projectId": "project"}),
                              ({"threadId": "ending-task", "hostId": "local"}, {"threadId": "ending-task", "projectId": None, "archived": True})):
            with self.assertRaises(ValueError):
                MODULE.acknowledge_launch(self.prepare(), ack, readback)

    def test_acknowledged_task_is_visible_and_reused_exactly_once(self):
        packet = self.acknowledged()
        self.assertTrue(packet["visible"])
        self.assertEqual(packet["status"], "pending")
        repeated = self.prepare(previous=json.loads(json.dumps(packet)))
        self.assertIsNone(repeated["create_thread"])
        self.assertEqual(repeated["thread_id"], "ending-task")
        with self.assertRaisesRegex(ValueError, "already has a different Ending"):
            MODULE.acknowledge_launch(packet, {"threadId": "duplicate", "hostId": "local"}, {"threadId": "duplicate", "projectId": None})

    def test_previous_task_cannot_cross_project_or_model_boundaries(self):
        packet = self.acknowledged()
        with self.assertRaisesRegex(ValueError, "different outcome, project, or selected model"):
            self.prepare(previous=packet, selected_model="gpt-5.6-luna", selected_effort="max")
        self.completed["task_id"] = "other-task"
        with self.assertRaises(ValueError):
            self.prepare(previous=packet)

    def test_completion_requires_verified_model_and_same_project_memory(self):
        packet = self.acknowledged()
        result = {"status": "written", "purpose": "memory_only", "record_id": "memory-record", "read_back_verified": True,
                  "project": {"key": packet["project_key"]}, "model_evidence": {"source": "verified_session", "pair": "gpt-6-astra|ultra"}}
        self.assertEqual(MODULE.record_completion(packet, result)["status"], "complete")
        for changes in ({"status": "failed"}, {"read_back_verified": False}, {"project": {"key": "other"}}, {"model_evidence": {"source": "configured_selection", "pair": "gpt-6-astra|ultra"}}, {"model_evidence": {"source": "verified_session", "pair": "gpt-5.6-luna|max"}}):
            with self.assertRaises(ValueError):
                MODULE.record_completion(packet, {**result, **changes})
        with self.assertRaisesRegex(ValueError, "acknowledged visible Ending"):
            MODULE.record_completion(self.prepare(), result)

    def test_visible_ending_can_truthfully_skip_missing_memory(self):
        result = MODULE.record_completion(self.acknowledged(), {"status": "skipped", "reason": "memory_unavailable"})
        self.assertEqual(result["status"], "skipped")
        self.assertTrue(result["visible"])

    def test_failed_required_projection_preserves_local_result_but_stays_pending(self):
        packet = self.acknowledged()
        result = {"status": "written", "purpose": "memory_only", "record_id": "memory-record", "read_back_verified": True,
                  "project": {"key": packet["project_key"]}, "model_evidence": {"source": "verified_session", "pair": "gpt-6-astra|ultra"},
                  "projection_required": True, "projection": {"status": "failed", "read_back_verified": False}}
        pending = MODULE.record_completion(packet, result)
        self.assertEqual((pending["status"], pending["reason"], pending["memory_sync"]), ("pending", "memory_projection_pending", "pending"))
        self.assertEqual(pending["memory_result"], result)
        self.assertEqual(pending["record_id"], "memory-record")
        self.assertIsNone(self.prepare(previous=pending)["create_thread"])
        result["projection"] = {"status": "written", "read_back_verified": True}
        complete = MODULE.record_completion(pending, result)
        self.assertEqual((complete["status"], complete["memory_sync"]), ("complete", "verified"))
        self.assertNotIn("reason", complete)

    def test_local_only_memory_does_not_claim_vault_synchronization(self):
        packet = self.acknowledged()
        result = {"status": "written", "purpose": "memory_only", "record_id": "memory-record", "read_back_verified": True,
                  "project": {"key": packet["project_key"]}, "model_evidence": {"source": "verified_session", "pair": "gpt-6-astra|ultra"},
                  "projection_required": False, "projection": {"status": "unavailable", "read_back_verified": False}}
        complete = MODULE.record_completion(packet, result)
        self.assertEqual((complete["status"], complete["memory_sync"]), ("complete", "local_only"))

    def test_real_memory_write_completes_visible_ending_without_commands(self):
        packet = self.acknowledged()
        with mock.patch.dict(ending_memory.os.environ, {"CODEX_OBSIDIAN_VAULT": ""}), mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None), mock.patch.object(MODULE.memory.subprocess, "run", side_effect=AssertionError("Ending must not run commands")):
            result = ending_memory.closeout(self.completed["outcome"], project_root=self.root, store=self.root / "memory", selected_model="gpt-6-astra", selected_effort="ultra", executing_model="gpt-6-astra", executing_effort="ultra", runtime_receipt={"status": "PASS", "turn_completed": True, "effective_pair": "gpt-6-astra|ultra"})
            complete = MODULE.record_completion(packet, result)
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(self.prepare(previous=complete)["thread_id"], "ending-task")

    def test_configured_unavailable_vault_does_not_claim_synced_completion(self):
        packet = self.acknowledged()
        with mock.patch.dict(ending_memory.os.environ, {"CODEX_OBSIDIAN_VAULT": str(self.root / "missing-vault")}), mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None):
            result = ending_memory.closeout(self.completed["outcome"], project_root=self.root, store=self.root / "memory", selected_model="gpt-6-astra", selected_effort="ultra", executing_model="gpt-6-astra", executing_effort="ultra", runtime_receipt={"status": "PASS", "turn_completed": True, "effective_pair": "gpt-6-astra|ultra"})
        self.assertTrue(result["projection_required"])
        complete = MODULE.record_completion(packet, result)
        self.assertEqual(complete["status"], "pending")
        self.assertEqual(complete["reason"], "memory_projection_pending")

    def test_prepare_cli_returns_reviewable_app_arguments(self):
        outcome_path = self.root / "completed.json"
        outcome_path.write_text(json.dumps(self.completed), encoding="utf-8")
        stdout = io.StringIO()
        argv = ["ending_memory_launch.py", "prepare", "--outcome", str(outcome_path), "--project-root", str(self.root), "--selected-model", "gpt-6-astra", "--selected-effort", "ultra", "--memory-available", "true"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(sys, "stdout", stdout):
            MODULE.main()
        packet = json.loads(stdout.getvalue())
        self.assertEqual(packet["create_thread"]["target"], {"type": "projectless"})
        self.assertFalse(packet["visible"])


if __name__ == "__main__":
    unittest.main()

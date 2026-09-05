import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("ending_memory", SCRIPTS / "ending_memory.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EndingMemoryTests(unittest.TestCase):
    def call(self, root, payload, **changes):
        args = dict(selected_model="gpt-6-astra", selected_effort="ultra", executing_model="gpt-6-astra", executing_effort="ultra", project_root=root, runtime_receipt={"status": "PASS", "turn_completed": True, "effective_pair": "gpt-6-astra|ultra"})
        args.update(changes)
        return MODULE.closeout(payload, **args)

    def test_model_and_effort_must_remain_selected(self):
        for changes in ({"executing_model": "gpt-5.6-luna"}, {"executing_effort": "high"}):
            with self.assertRaisesRegex(ValueError, "selected model and effort"):
                self.call(SCRIPTS, {"summary": "A useful change"}, **changes)

    def test_blank_selected_identity_is_not_execution_evidence(self):
        for changes in ({"selected_model": " "}, {"selected_effort": ""}):
            with self.assertRaisesRegex(ValueError, "selected model and effort"):
                self.call(SCRIPTS, {}, **changes)

    def test_runtime_evidence_must_match_and_show_completed_execution(self):
        for receipt in ({"status": "PASS", "turn_completed": True, "effective_pair": "gpt-5.6-luna|max"}, {"status": "PASS", "effective_pair": "gpt-6-astra|ultra"}):
            with self.assertRaises(ValueError):
                MODULE.verify_identity("gpt-6-astra", "ultra", runtime_receipt=receipt)

    def test_runner_lowercase_receipt_status_is_supported(self):
        receipt = {"status": "pass", "turn_completed": True, "effective_model": "gpt-6-astra", "effective_effort": "ultra", "effective_pair": "gpt-6-astra|ultra"}
        self.assertEqual(MODULE.verify_identity("gpt-6-astra", "ultra", runtime_receipt=receipt), {"source": "runtime_receipt", "pair": "gpt-6-astra|ultra"})
        for status in ("failed", "pending", None):
            with self.assertRaisesRegex(ValueError, "completed passing runtime"):
                MODULE.verify_identity("gpt-6-astra", "ultra", runtime_receipt={**receipt, "status": status})

    def test_caller_model_labels_alone_are_not_proof(self):
        with mock.patch.dict(MODULE.os.environ, {"CODEX_THREAD_ID": "not-a-real-thread"}):
            with self.assertRaisesRegex(ValueError, "runtime model evidence"):
                MODULE.verify_identity("gpt-6-astra", "ultra")

    def test_verified_session_is_accepted_without_launching_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            thread = "00000000-0000-0000-0000-000000000123"
            sessions = root / "sessions" / "2026" / "09" / "05"
            sessions.mkdir(parents=True)
            (sessions / f"rollout-{thread}.jsonl").write_text('{"type":"session_meta","payload":{"id":"' + thread + '"}}\n{"type":"turn_context","payload":{"model":"gpt-6-astra","effort":"ultra"}}\n')
            with mock.patch.dict(MODULE.os.environ, {"CODEX_THREAD_ID": thread, "CODEX_HOME": str(root)}):
                identity = MODULE.verify_identity("gpt-6-astra", "ultra")
            self.assertEqual(identity, {"source": "verified_session", "pair": "gpt-6-astra|ultra"})

    def identity_from_events(self, events):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            thread = "00000000-0000-0000-0000-000000000123"
            sessions = root / "sessions" / "2026" / "09" / "05"
            sessions.mkdir(parents=True)
            metadata = {"type": "session_meta", "payload": {"id": thread}}
            (sessions / f"rollout-{thread}.jsonl").write_text("\n".join(json.dumps(event) for event in [metadata, *events]), encoding="utf-8")
            with mock.patch.dict(MODULE.os.environ, {"CODEX_THREAD_ID": thread, "CODEX_HOME": str(root)}):
                return MODULE.verify_identity("gpt-6-astra", "ultra")

    def test_latest_turn_provider_reroute_cannot_claim_selected_model(self):
        context = {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "ultra", "turn_id": "latest"}}
        reroute = {"type": "event_msg", "payload": {"type": "model_reroute", "to_model": "gpt-5.6-sol"}}
        with self.assertRaisesRegex(ValueError, "runtime evidence must match"):
            self.identity_from_events([context, reroute])

    def test_previous_turn_or_other_session_reroutes_do_not_change_latest_identity(self):
        context = {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "ultra", "turn_id": "latest"}}
        old = {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "ultra", "turn_id": "old"}}
        reroute = {"type": "event_msg", "payload": {"type": "model_reroute", "to_model": "gpt-5.6-sol"}}
        other = {"type": "session_meta", "payload": {"id": "00000000-0000-0000-0000-000000000456"}}
        for events in ([old, reroute, context], [context, other, reroute], [context, {**reroute, "payload": {**reroute["payload"], "turn_id": "old"}}]):
            self.assertEqual(self.identity_from_events(events)["pair"], "gpt-6-astra|ultra")

    def test_missing_memory_and_no_durable_change_skip_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(MODULE.memory, "DEFAULT_STORE", root / "absent"), mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None):
                self.assertEqual(self.call(root, {"summary": "A useful change"})["reason"], "memory_unavailable")
                self.assertEqual(self.call(root, {})["reason"], "no_durable_information")
                self.assertEqual(list(root.iterdir()), [])

    def test_ending_refuses_commands_and_project_override(self):
        for field in ("checks", "command", "project_root"):
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                self.call(SCRIPTS, {field: "untrusted input"})

    def test_project_required_for_recall(self):
        with self.assertRaisesRegex(ValueError, "project-root is required"):
            MODULE.memory.search_records()

    def test_real_write_reads_back_only_the_same_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "alpha"
            other = root / "beta"
            project.mkdir()
            other.mkdir()
            (project / "layout.py").write_text("spacing = 12\n")
            store = root / "memory"
            outcome = dict(module="layout", summary="Aligned the settings controls", reason="Keep consistent spacing", result="Settings controls now share spacing", files=["layout.py"], verification_status="passed", verification=["Focused layout assertions passed"])
            with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None):
                result = self.call(project, outcome, store=store)
            self.assertTrue(result["read_back_verified"])
            self.assertEqual(result["purpose"], "memory_only")
            self.assertEqual(MODULE.memory.search_records(other, store=store)["matches"], [])

    def test_memory_closeout_never_launches_git_or_check_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = dict(module="layout", summary="Aligned controls", reason="Preserve a shared grid", result="Controls share the same gutter", files=["layout.py"])
            with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None), mock.patch.object(MODULE.memory.subprocess, "run", side_effect=AssertionError("Ending cannot launch commands")) as command:
                result = self.call(root, payload, store=root / "memory")
            self.assertTrue(result["read_back_verified"])
            command.assert_not_called()

    def test_duplicate_readback_is_not_limited_to_recent_five_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = dict(module="layout", summary="Aligned controls", reason="Preserve a shared grid", result="Controls share the same gutter", files=["layout.py"])
            with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None):
                original = self.call(root, payload, store=root / "memory")
                for number in range(6):
                    self.call(root, {**payload, "summary": f"Adjusted panel spacing {number}"}, store=root / "memory")
                repeated = self.call(root, payload, store=root / "memory")
            self.assertEqual(repeated["status"], "duplicate")
            self.assertEqual(repeated["record_id"], original["record_id"])
            self.assertTrue(repeated["read_back_verified"])

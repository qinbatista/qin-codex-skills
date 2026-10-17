import base64
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "project-memory-skill" / "scripts"))
sys.path.insert(0, str(ROOT / "workflow-skill" / "scripts"))
import ending_conversation as ending
from task_artifact_paths import resolve_task_artifact_root


class EndingConversationTests(unittest.TestCase):
    def setUp(self):
        self.root = resolve_task_artifact_root(ROOT, "ending-native-tests", create=True)
        self.addCleanup(self.root.rmdir)
        self.temporary = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.temporary.cleanup)
        self.rollout = Path(self.temporary.name) / "rollout.jsonl"
        self.rollout.write_text("fixture")
        self.thread = {"id": "ending", "name": "Ending Task | Example", "path": str(self.rollout), "status": {"type": "idle"}}
        self.children = []
        self.retained = False
        self.client = mock.Mock()
        self.client.call.side_effect = self.native_call

    def native_call(self, method, params):
        if method == "thread/read":
            return {"thread": self.thread}
        if method == "thread/delete":
            if not self.retained:
                self.rollout.unlink()
            return {}
        if "ancestorThreadId" in params:
            return {"data": self.children if not params["archived"] else [], "nextCursor": None}
        return {"data": [], "nextCursor": None}

    def delete(self, **changes):
        arguments = {"thread_id": "ending", "expected_title": "Ending Task | Example", "origin_thread_id": "origin", "apply": True}
        arguments.update(changes)
        return ending.delete_ending(self.client, **arguments)

    def assert_not_deleted(self):
        self.assertFalse(any(call.args[0] == "thread/delete" for call in self.client.call.call_args_list))
        self.assertTrue(self.rollout.exists())

    def test_probe_requires_creating_service_ownership(self):
        self.client.transport = "daemon"
        self.client.call.side_effect = [{"data": [], "nextCursor": "more"}, {"data": ["origin"]}]
        self.assertTrue(ending.probe_deletion_route(self.client, "origin")["native_delete_available"])
        self.client.call.side_effect = [{"data": ["another-server-thread"]}]
        self.assertFalse(ending.probe_deletion_route(self.client, "origin")["native_delete_available"])

    def test_protects_origin_and_non_ending_titles(self):
        for changes in ({"thread_id": "origin"}, {"expected_title": "Fix Ending problem"}, {"expected_title": "Ending rules"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.delete(**changes)
        self.assert_not_deleted()

    def test_title_change_refuses_deletion(self):
        self.thread["name"] = "User retained work"
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.delete()
        self.assert_not_deleted()

    def test_unreviewed_cascade_and_origin_descendant_refuse(self):
        self.children = [{**self.thread, "id": "origin"}]
        for descendants in ([], ["origin"]):
            with self.assertRaisesRegex(ValueError, "cascades"):
                self.delete(descendants=descendants)
        self.assert_not_deleted()

    def test_active_other_thread_refuses(self):
        self.thread["status"] = {"type": "active"}
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "origin"}), self.assertRaisesRegex(ValueError, "Active"):
            self.delete()
        self.assert_not_deleted()

    def test_active_descendant_cannot_use_self_exception(self):
        self.children = [{**self.thread, "id": "worker", "status": {"type": "active"}}]
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "ending"}), self.assertRaisesRegex(ValueError, "Active"):
            self.delete(descendants=["worker"])
        self.assert_not_deleted()

    def test_preview_is_read_only(self):
        self.assertEqual(self.delete(apply=False)["status"], "ready")
        self.assert_not_deleted()

    def test_native_success_requires_rollout_absence(self):
        self.retained = True
        with self.assertRaisesRegex(RuntimeError, "readback failed"):
            self.delete()

    def test_native_success_requires_metadata_absence(self):
        self.client.call.side_effect = [{"thread": self.thread}, {"data": []}, {"data": []}, {}, {"data": [self.thread]}, {"data": []}]
        with self.assertRaisesRegex(RuntimeError, "readback failed"):
            self.delete()

    def test_native_error_is_not_retried_or_archived(self):
        self.client.call.side_effect = [ {"thread": self.thread}, {"data": []}, {"data": []}, ending.NativeError("thread/delete", {"message": "active writer"}) ]
        with self.assertRaises(ending.NativeError):
            self.delete()
        self.assertEqual([call.args[0] for call in self.client.call.call_args_list].count("thread/delete"), 1)
        self.assertTrue(self.rollout.exists())

    def test_verified_native_receipt(self):
        receipt = self.delete()
        self.assertTrue(receipt["local_record_absent"])
        self.assertEqual(receipt["status"], "deleted")
        self.assertFalse(self.rollout.exists())

    def test_inventory_uses_every_provider_and_archive_page(self):
        self.client.call.side_effect = [{"data": [self.thread], "nextCursor": "next"}, {"data": [{**self.thread, "id": "second"}]}, {"data": [{**self.thread, "id": "archived"}]}]
        self.assertEqual(len(ending.list_endings(self.client)), 3)
        calls = self.client.call.call_args_list
        self.assertEqual(calls[1].args[1]["cursor"], "next")
        self.assertTrue(calls[2].args[1]["archived"])
        for call in calls:
            self.assertEqual(call.args[1]["modelProviders"], [])
            self.assertEqual(call.args[1]["sourceKinds"], ending.SOURCE_KINDS)

    def test_repeated_cursor_refuses_partial_inventory(self):
        self.client.call.side_effect = [{"data": [], "nextCursor": "same"}] * 2
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            ending.list_threads(self.client)

    def test_websocket_fragment_ping_and_masked_reply(self):
        client = ending.AppServer(executable="codex", transport="daemon")
        client.websocket_key = "test-key"
        accept = base64.b64encode(hashlib.sha1((client.websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        message = json.dumps({"id": 1, "result": {}}).encode()
        frames = bytes([1, 5]) + message[:5] + b"\x89\x01p" + bytes([128, len(message) - 5]) + message[5:] + b"\x88\x00"
        response = f"HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode() + frames
        client.process = SimpleNamespace(stdout=io.BytesIO(response), stdin=io.BytesIO())
        client.read_websocket()
        self.assertTrue(client.messages.get_nowait())
        self.assertEqual(client.messages.get_nowait()["id"], 1)
        pong = client.process.stdin.getvalue()
        self.assertEqual(pong[:2], b"\x8a\x81")
        self.assertEqual(bytes([pong[6] ^ pong[2]]), b"p")

    def test_websocket_extended_frame_lengths(self):
        client = ending.AppServer(executable="codex")
        for size in (1, 126, 65536):
            with self.subTest(size=size):
                client.process = SimpleNamespace(stdin=io.BytesIO())
                client.send_frame(b"x" * size)
                frame = client.process.stdin.getvalue()
                marker = frame[1] & 127
                offset = 2 if marker < 126 else 4 if marker == 126 else 10
                mask = frame[offset:offset + 4]
                payload = frame[offset + 4:]
                self.assertEqual(bytes(value ^ mask[index % 4] for index, value in enumerate(payload)), b"x" * size)

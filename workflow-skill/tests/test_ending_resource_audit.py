import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import ending_resource_audit as AUDIT
import task_resource_ledger as LEDGER


HASH = "a" * 64


class EndingResourceAuditTests(unittest.TestCase):
    def setUp(self):
        cache = SCRIPTS.parents[1] / "Cache"
        cache.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-ending-resource-tests-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.task_id = "finished-task"
        self.task_root = "Cache/temp-owned-test"
        self.ledger = LEDGER.new_ledger(self.project, self.task_id, self.task_root)
        self.ledger_path = self.project / self.task_root / LEDGER.LEDGER_NAME
        self.readback = {"task_id": self.task_id, "state": "complete", "purpose": "Completed website and package test", "observed_at": time.time(), "source": "owning-chat final outcome and current readback"}

    def file(self, resource_id, *, scope="main"):
        path = f"{self.task_root}/{resource_id}.txt"
        LEDGER.acquire_path(self.ledger, self.project, resource_id, path, "test intermediate", scope=scope)
        absolute = self.project / path
        absolute.write_text("completed test output", encoding="utf-8")
        LEDGER.seal_path(self.ledger, self.project, resource_id)
        LEDGER.record_durable_readback(self.ledger, resource_id, HASH)
        LEDGER.record_consumer_readback(self.ledger, resource_id, self.task_id, HASH)
        LEDGER.save_ledger(self.ledger_path, self.ledger)
        return absolute

    def decision(self, resource_id, **changes):
        decision = {"id": resource_id, "disposition": "release", "reason": "known-result disposable test output", "evidence": "originating task's accepted result and exact creation history", "result_known": True, "needed_for_review": False, "needed_for_reuse": False, "active_use": False}
        decision.update(changes)
        return decision

    def audit(self, decisions, **options):
        return AUDIT.audit_ledger(self.project, self.task_root, self.readback, decisions, **options)

    def test_completed_disposable_files_and_empty_root_are_actually_removed(self):
        first = self.file("first")
        second = self.file("second")
        bytes_before = first.stat().st_size + second.stat().st_size
        result = self.audit([self.decision("first"), self.decision("second")], apply=True)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["bytes_removed"], bytes_before)
        self.assertEqual([item["id"] for item in result["resources"]], ["second", "first"])
        self.assertTrue(all(item["read_back_verified"] for item in result["resources"]))
        self.assertTrue(result["root_removed"])
        self.assertFalse((self.project / self.task_root).exists())

    def test_review_reuse_and_live_user_files_survive_beside_disposable_work(self):
        disposable = self.file("disposable", scope="disposable")
        protected = [self.file(name, scope=name) for name in ("review-image", "reusable-simulation", "active-preview")]
        decisions = [self.decision("disposable")]
        for name, flag in (("review-image", "needed_for_review"), ("reusable-simulation", "needed_for_reuse"), ("active-preview", "active_use")):
            decisions.append(self.decision(name, disposition="keep", reason=flag, **{flag: True}))
        result = self.audit(decisions, apply=True)
        self.assertFalse(disposable.exists())
        self.assertTrue(all(path.read_text() == "completed test output" for path in protected))
        self.assertEqual(sum(item["action"] == "keep" for item in result["resources"]), 3)
        self.assertFalse(result["root_removed"])

    def test_active_paused_failed_review_and_unknown_tasks_are_not_cleaned(self):
        target = self.file("live")
        for state in ("active", "paused", "failed", "review", "unknown"):
            with self.subTest(state=state):
                self.readback["state"] = state
                saved = self.ledger_path.read_bytes()
                result = self.audit([self.decision("live")], apply=True)
                self.assertEqual(result["resources"][0]["action"], "keep")
                self.assertEqual(self.ledger_path.read_bytes(), saved)
                self.assertTrue(target.exists())

    def test_stale_or_wrong_task_evidence_cannot_release_files(self):
        target = self.file("output")
        for changes in ({"task_id": "another-task"}, {"observed_at": time.time() - 121}, {"observed_at": time.time() + 3600}, {"observed_at": float("nan")}, {"state": "idle"}):
            with self.subTest(changes=changes):
                readback = {**self.readback, **changes}
                with self.assertRaises(ValueError):
                    AUDIT.audit_ledger(self.project, self.task_root, readback, [self.decision("output")], apply=True)
                self.assertTrue(target.exists())

    def test_release_decisions_cannot_override_review_reuse_active_or_unfinished(self):
        target = self.file("output")
        for flag in ("needed_for_review", "needed_for_reuse", "active_use", "result_known"):
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    self.audit([self.decision("output", **{flag: flag != "result_known"})], apply=True)
                self.assertTrue(target.exists())

    def test_missing_purpose_and_dry_run_preserve_files(self):
        target = self.file("unknown")
        result = self.audit([], apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(target.exists())
        before = self.ledger_path.read_bytes()
        result = self.audit([self.decision("unknown")])
        self.assertEqual(result["resources"][0]["action"], "release_candidate")
        self.assertEqual(self.ledger_path.read_bytes(), before)
        self.assertTrue(target.exists())

    def test_changed_file_identity_and_unknown_root_files_survive(self):
        target = self.file("changed")
        target.write_text("user changed these bytes", encoding="utf-8")
        result = self.audit([self.decision("changed")], apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(target.read_text(), "user changed these bytes")
        other = self.file("independent", scope="other")
        unknown = self.ledger_path.parent / "unrecorded-document.txt"
        unknown.write_text("preserve unknown content")
        result = self.audit([self.decision("independent")], apply=True)
        self.assertFalse(other.exists())
        self.assertEqual(unknown.read_text(), "preserve unknown content")
        self.assertFalse(result["root_removed"])

    def test_unknown_files_block_finalization_even_after_known_files_close(self):
        target = self.file("output")
        unknown = self.ledger_path.parent / "review-document.txt"
        unknown.write_text("user review")
        result = self.audit([self.decision("output")], apply=True)
        self.assertFalse(target.exists())
        self.assertFalse(result["root_removed"])
        self.assertIn("unknown files", result["finalization_reason"])
        self.assertEqual(unknown.read_text(), "user review")

    def test_consumer_barrier_and_busy_ledger_prevent_cleanup(self):
        target = self.file("downstream")
        ledger = LEDGER.load_ledger(self.ledger_path)
        ledger["resources"][0]["consumers"][LEDGER._task_key("consumer")] = {"role": "downstream", "readback_digest": None}
        LEDGER.save_ledger(self.ledger_path, ledger)
        result = self.audit([self.decision("downstream")], apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(target.exists())
        with LEDGER.ledger_lock(self.ledger_path):
            with self.assertRaises(RuntimeError):
                self.audit([self.decision("downstream")], apply=True)
        self.assertTrue(target.exists())

    def test_bounded_inspection_preserves_unknown_roots_and_retained_cache(self):
        target = self.file("output")
        unknown = self.project / "Cache" / "temp-old-unknown"
        unknown.mkdir()
        retained = self.project / "Cache" / "remote-review"
        retained.mkdir()
        (retained / "image.png").write_bytes(b"user image")
        result = AUDIT.inspect_cache(self.project)
        self.assertEqual(len(result["roots"]), 2)
        self.assertTrue(any(item.get("action") == "preserve_unknown" for item in result["roots"]))
        self.assertTrue(target.exists())
        self.assertTrue((retained / "image.png").exists())
        self.assertTrue(AUDIT.inspect_cache(self.project, limit=1)["limit_reached"])
        with self.assertRaises(ValueError):
            AUDIT.inspect_cache(self.project, limit=65)

    def test_inspection_and_release_never_traverse_symlink_roots(self):
        target = self.file("output")
        linked = self.project / "Cache" / "temp-linked"
        try:
            linked.symlink_to(self.ledger_path.parent, target_is_directory=True)
        except OSError:
            self.skipTest("directory symlinks unavailable")
        result = AUDIT.inspect_cache(self.project)
        self.assertTrue(any(item.get("action") == "preserve_unknown" and item["task_root"] == "Cache/temp-linked" for item in result["roots"]))
        with self.assertRaises(ValueError):
            AUDIT.audit_ledger(self.project, "Cache/temp-linked", self.readback, [self.decision("output")], apply=True)
        self.assertTrue(target.exists())

    def test_runtime_actions_require_owning_tool_and_identity_bound_absence(self):
        identity = {"pid": 54321, "start_time": "unique-start", "executable": "python", "cwd": str(self.project)}
        LEDGER.acquire_runtime(self.ledger, "server", "server", identity, "finished test server")
        LEDGER.record_durable_readback(self.ledger, "server", HASH)
        LEDGER.record_consumer_readback(self.ledger, "server", self.task_id, HASH)
        LEDGER.save_ledger(self.ledger_path, self.ledger)
        result = self.audit([self.decision("server")], apply=True)
        action = result["resources"][0]
        self.assertEqual(action["action"], "owner_action_required")
        self.assertEqual(action["identity"]["pid"], 54321)
        self.assertFalse(result["root_removed"])
        invalid = self.audit([self.decision("server")], apply=True, runtime_receipts={"server": {"outcome": "PASS"}})
        self.assertEqual(invalid["status"], "pending")
        self.assertTrue(self.ledger_path.exists())
        receipt = {key: action[key] for key in ("ledger_id", "identity_digest", "release_token")}
        receipt.update(resource_id="server", kind="server", method="graceful", outcome="PASS", observed="exact_handle_absent", owner_tool="controlled owner receipt fixture")
        completed = self.audit([self.decision("server")], apply=True, runtime_receipts={"server": receipt})
        self.assertEqual(completed["status"], "complete")
        self.assertTrue(completed["root_removed"])


if __name__ == "__main__":
    unittest.main()

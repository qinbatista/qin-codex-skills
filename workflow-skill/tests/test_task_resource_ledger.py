import ast
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "task_resource_ledger.py"
SPEC = importlib.util.spec_from_file_location("task_resource_ledger", SCRIPT_PATH)
LEDGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LEDGER)
HASH = hashlib.sha256(b"verified-readback").hexdigest()


class TaskResourceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.scratch_parent = Path.cwd() / "Cache" / "temp-task-resource-units"
        self.scratch_parent.mkdir(parents=True, exist_ok=True)
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="case-", dir=self.scratch_parent
        )
        self.project_root = Path(self.temporary_directory.name)
        (self.project_root / "Cache").mkdir()
        self.task_id = "producer-task"
        self.task_root = f"Cache/temp-case-{uuid.uuid4().hex}"
        self.ledger = LEDGER.new_ledger(
            self.project_root, self.task_id, self.task_root
        )

    def tearDown(self):
        self.temporary_directory.cleanup()
        try:
            self.scratch_parent.rmdir()
            self.scratch_parent.parent.rmdir()
        except OSError:
            pass

    def _path(self, name):
        return f"{self.task_root}/{name}"

    def _acquire_file(self, resource_id, name, *, scope="main", content="owned"):
        relative_path = self._path(name)
        LEDGER.acquire_path(
            self.ledger,
            self.project_root,
            resource_id,
            relative_path,
            "unit fixture",
            scope=scope,
        )
        target = self.project_root.joinpath(*relative_path.split("/"))
        target.write_text(content, encoding="utf-8")
        LEDGER.seal_path(self.ledger, self.project_root, resource_id)
        return target

    def _pass_barriers(self, resource_id, *consumers):
        LEDGER.record_durable_readback(self.ledger, resource_id, HASH)
        LEDGER.record_consumer_readback(
            self.ledger, resource_id, self.task_id, HASH
        )
        for consumer in consumers:
            LEDGER.record_consumer_readback(
                self.ledger, resource_id, consumer, HASH
            )

    def _durable_receipt(self, *, disposition="delivery", owner_root="Outputs/current", content=b"final owner bytes"):
        owner = self.project_root.joinpath(*owner_root.split("/"))
        owner.mkdir(parents=True, exist_ok=True)
        declaration = {"owner_id": "current-output", "owner_kind": "output", "owner_root": owner_root}
        record = owner / "owner.json"
        record.write_text(json.dumps(declaration), encoding="utf-8")
        target = owner / "result.bin"
        target.write_bytes(content)
        return {**declaration, "owner_record": f"{owner_root}/owner.json", "owner_record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(), "path": f"{owner_root}/result.bin", "sha256": hashlib.sha256(content).hexdigest(), "disposition": disposition, "purpose": "final_output" if disposition == "delivery" else "resume_state"}

    def test_exact_disposable_cleanup_is_two_phase_and_idempotent(self):
        target = self._acquire_file("output", "output.txt")
        self._pass_barriers("output")
        self.assertTrue(LEDGER.prepare_release(self.ledger, "output"))
        persisted_states = []

        def persist(value):
            persisted_states.append(
                next(item for item in value["resources"] if item["id"] == "output")[
                    "state"
                ]
            )

        self.assertTrue(
            LEDGER.cleanup_path(
                self.ledger,
                self.project_root,
                "output",
                persist_callback=persist,
            )
        )
        self.assertFalse(target.exists())
        self.assertIn("cleanup_in_progress", persisted_states)
        self.assertEqual(persisted_states[-1], "released")
        self.assertFalse(
            LEDGER.cleanup_path(self.ledger, self.project_root, "output")
        )

    def test_durable_and_every_consumer_barrier_are_independent(self):
        LEDGER.acquire_path(
            self.ledger,
            self.project_root,
            "shared",
            self._path("shared.txt"),
            "shared fixture",
        )
        LEDGER.handoff(self.ledger, "shared", "consumer-a")
        LEDGER.handoff(self.ledger, "shared", "consumer-b")
        with self.assertRaisesRegex(ValueError, "duplicate consumer"):
            LEDGER.handoff(self.ledger, "shared", "consumer-a")
        target = self.project_root.joinpath(*self._path("shared.txt").split("/"))
        target.write_text("shared", encoding="utf-8")
        LEDGER.seal_path(self.ledger, self.project_root, "shared")
        LEDGER.record_durable_readback(self.ledger, "shared", HASH)
        LEDGER.record_consumer_readback(
            self.ledger, "shared", self.task_id, HASH
        )
        LEDGER.record_consumer_readback(
            self.ledger, "shared", "consumer-a", HASH
        )
        with self.assertRaisesRegex(ValueError, "every explicit consumer"):
            LEDGER.prepare_release(self.ledger, "shared")
        LEDGER.record_consumer_readback(
            self.ledger, "shared", "consumer-b", HASH
        )
        with self.assertRaisesRegex(ValueError, "single-use"):
            LEDGER.record_consumer_readback(
                self.ledger, "shared", "consumer-b", HASH
            )
        self.assertTrue(LEDGER.prepare_release(self.ledger, "shared"))

    def test_scope_local_reverse_order_does_not_block_other_branch(self):
        first = self._acquire_file("first", "first.txt", scope="branch-a")
        second = self._acquire_file("second", "second.txt", scope="branch-a")
        other = self._acquire_file("other", "other.txt", scope="branch-b")
        for resource_id in ("first", "second", "other"):
            self._pass_barriers(resource_id)
        LEDGER.prepare_release(self.ledger, "other")
        LEDGER.cleanup_path(self.ledger, self.project_root, "other")
        self.assertFalse(other.exists())
        with self.assertRaisesRegex(ValueError, "reverse acquisition order"):
            LEDGER.prepare_release(self.ledger, "first")
        LEDGER.prepare_release(self.ledger, "second")
        LEDGER.cleanup_path(self.ledger, self.project_root, "second")
        LEDGER.prepare_release(self.ledger, "first")
        LEDGER.cleanup_path(self.ledger, self.project_root, "first")
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())

    def test_ending_cannot_own_resources_or_delay_cleanup(self):
        with self.assertRaisesRegex(ValueError, "active producer"):
            LEDGER.new_ledger(
                self.project_root, "ending-task", "Cache/temp-ending-task", role="ending"
            )
        LEDGER.acquire_path(
            self.ledger,
            self.project_root,
            "ending-output",
            self._path("ending.txt"),
            "legacy Ending fixture",
        )
        with self.assertRaisesRegex(ValueError, "memory-only"):
            LEDGER.handoff(
                self.ledger, "ending-output", "ending-task", role="ending"
            )
        resource = next(
            item for item in self.ledger["resources"] if item["id"] == "ending-output"
        )
        resource["consumers"][LEDGER._task_key("ending-task")] = {
            "role": "ending", "readback_digest": None
        }
        self.ledger["ending_evidence"] = {}
        LEDGER.validate_ledger(self.ledger)
        target = self.project_root.joinpath(*self._path("ending.txt").split("/"))
        target.write_text("released by main task", encoding="utf-8")
        LEDGER.seal_path(self.ledger, self.project_root, "ending-output")
        self._pass_barriers("ending-output")
        self.assertTrue(LEDGER.prepare_release(self.ledger, "ending-output"))
        self.assertTrue(LEDGER.cleanup_path(self.ledger, self.project_root, "ending-output"))
        self.assertFalse(target.exists())

    def test_retained_and_preexisting_resources_are_never_release_candidates(self):
        with self.assertRaisesRegex(ValueError, "outside temporary"):
            LEDGER.record_retained_path(
                self.ledger,
                "dated",
                "Cache/tmp-dated/report.json",
                "short reuse",
                "inspect tomorrow",
                "2026-08-24",
                authorized_by_user=True,
            )
        with self.assertRaisesRegex(ValueError, "explicit user or project-contract"):
            LEDGER.record_retained_path(
                self.ledger,
                "remote-denied",
                "Cache/remote-test/result.json",
                "retained test",
                "release audit",
                "next release",
            )
        with self.assertRaisesRegex(ValueError, "exact durable owner receipt"):
            LEDGER.record_retained_path(self.ledger, "remote-prefix", "Cache/remote-test/result.json", "review", "debug downstream retry", "later", authorized_by_contract=True, project_root=self.project_root)
        receipt = self._durable_receipt(owner_root="Cache/remote-actual-resource")
        remote = LEDGER.record_retained_path(
            self.ledger,
            "remote",
            receipt["path"],
            "retained test",
            "release audit",
            "next release",
            authorized_by_contract=True,
            project_root=self.project_root,
            owner_receipt=receipt,
        )
        preexisting = LEDGER.record_preexisting_path(
            self.ledger,
            "unity-cache",
            "Library/Artifacts",
            "Unity-managed cache",
        )
        self.assertEqual(remote["state"], "retained")
        self.assertEqual(remote["sync_status"], "local_bytes_verified")
        self.assertEqual(preexisting["state"], "preexisting")
        for resource_id in ("remote", "unity-cache"):
            with self.assertRaisesRegex(ValueError, "remains untouched"):
                LEDGER.prepare_release(self.ledger, resource_id)

    def test_delivery_and_minimal_recovery_handoff_release_pending_scratch_consumers(self):
        for disposition in ("delivery", "recovery"):
            with self.subTest(disposition=disposition):
                resource_id = f"scratch-{disposition}"
                path = self._path(f"{disposition}.txt")
                LEDGER.acquire_path(self.ledger, self.project_root, resource_id, path, "disposable", scope=disposition)
                LEDGER.handoff(self.ledger, resource_id, "pending-downstream")
                target = self.project_root.joinpath(*path.split("/"))
                target.write_text("scratch only", encoding="utf-8")
                LEDGER.seal_path(self.ledger, self.project_root, resource_id)
                receipt = self._durable_receipt(disposition=disposition, owner_root=f"Outputs/{disposition}")
                LEDGER.record_durable_handoff(self.ledger, self.project_root, resource_id, receipt)
                resource = LEDGER._resource(self.ledger, resource_id)
                consumer = resource["consumers"][LEDGER._task_key("pending-downstream")]
                self.assertIsNone(consumer["readback_digest"])
                self.assertEqual(consumer["durable_owner_digest"], LEDGER._identity_digest(resource["durable_owner"]))
                with self.assertRaisesRegex(ValueError, "current project_root"):
                    LEDGER.prepare_release(self.ledger, resource_id)
                self.assertTrue(LEDGER.prepare_release(self.ledger, resource_id, project_root=self.project_root))
                self.assertTrue(LEDGER.cleanup_path(self.ledger, self.project_root, resource_id))
                self.assertFalse(target.exists())
                self.assertEqual(self.project_root.joinpath(*receipt["path"].split("/")).read_bytes(), b"final owner bytes")

    def test_durable_handoff_rejects_prefix_reason_unverified_owner_and_byte_drift(self):
        target = self._acquire_file("handoff", "handoff.txt")
        receipt = self._durable_receipt()
        invalid_receipts = ({**receipt, "disposition": "review"}, {**receipt, "disposition": "recovery", "purpose": "debug"}, {**receipt, "owner_root": self.task_root}, {**receipt, "owner_root": "Cache/tmp-other"}, {**receipt, "owner_id": "unrelated"}, {**receipt, "sha256": HASH}, {**receipt, "owner_record": "Cache/remote-renamed/owner.json"})
        for invalid in invalid_receipts:
            with self.subTest(receipt=invalid):
                with self.assertRaises((ValueError, FileNotFoundError)):
                    LEDGER.record_durable_handoff(self.ledger, self.project_root, "handoff", invalid)
                self.assertNotIn("durable_owner", LEDGER._resource(self.ledger, "handoff"))
        LEDGER.record_durable_handoff(self.ledger, self.project_root, "handoff", receipt)
        LEDGER.prepare_release(self.ledger, "handoff", project_root=self.project_root)
        self.project_root.joinpath(*receipt["path"].split("/")).write_bytes(b"changed owner")
        with self.assertRaisesRegex(ValueError, "identity changed|byte readback"):
            LEDGER.cleanup_path(self.ledger, self.project_root, "handoff")
        self.assertTrue(target.exists())

    def test_durable_handoff_cannot_bypass_runtime_owner_receipt(self):
        runtime = LEDGER.acquire_runtime(self.ledger, "runtime-handoff", "browser_tab", {"tab_id": "tab-owned", "context_id": "iab", "window_id": "owned-window"}, "owned tab")
        with self.assertRaisesRegex(ValueError, "never a runtime"):
            LEDGER.record_durable_handoff(self.ledger, self.project_root, runtime["id"], self._durable_receipt())

    def test_recovery_rejects_whole_scratch_archive_even_after_renaming(self):
        target = self._acquire_file("archive", "archive.txt")
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(f"{self.task_root}/debug.txt", "whole scratch must not survive")
        receipt = self._durable_receipt(disposition="recovery", content=archive.getvalue())
        with self.assertRaisesRegex(ValueError, "never a scratch archive"):
            LEDGER.record_durable_handoff(self.ledger, self.project_root, "archive", receipt)
        self.assertTrue(target.exists())
        self.assertNotIn("durable_owner", LEDGER._resource(self.ledger, "archive"))

    def test_exact_temp_and_tmp_task_roots_finalize_without_touching_durable_or_preexisting_owners(self):
        for prefix in ("temp", "tmp"):
            with self.subTest(prefix=prefix):
                task_root = f"Cache/{prefix}-finalize-{uuid.uuid4().hex}"
                ledger = LEDGER.new_ledger(self.project_root, "finalize-task", task_root)
                LEDGER.record_preexisting_path(ledger, "preexisting", "Library/Artifacts", "preexisting owner")
                receipt = self._durable_receipt(owner_root=f"Outputs/{prefix}")
                LEDGER.record_retained_path(ledger, "final-output", receipt["path"], "delivered", "requested output", "owner lifetime", authorized_by_user=True, project_root=self.project_root, owner_receipt=receipt)
                ledger_path = self.project_root.joinpath(*task_root.split("/")) / LEDGER.LEDGER_NAME
                LEDGER.save_ledger(ledger_path, ledger)
                LEDGER.finalize_task_root(ledger, self.project_root, ledger_path)
                self.assertFalse(ledger_path.parent.exists())
                self.assertTrue(self.project_root.joinpath(*receipt["path"].split("/")).exists())

    def test_finalize_requires_closed_resources_and_rejects_unknown_files_or_ledger_drift(self):
        target = self._acquire_file("active", "active.txt")
        ledger_path = target.parent / LEDGER.LEDGER_NAME
        LEDGER.save_ledger(ledger_path, self.ledger)
        with self.assertRaisesRegex(ValueError, "every resource to be closed"):
            LEDGER.finalize_task_root(self.ledger, self.project_root, ledger_path)
        self._pass_barriers("active")
        LEDGER.prepare_release(self.ledger, "active")
        LEDGER.cleanup_path(self.ledger, self.project_root, "active")
        LEDGER.save_ledger(ledger_path, self.ledger)
        unknown = target.parent / "user.txt"
        unknown.write_text("preserve user", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unknown files"):
            LEDGER.finalize_task_root(self.ledger, self.project_root, ledger_path)
        self.assertEqual(unknown.read_text(encoding="utf-8"), "preserve user")
        unknown.unlink()
        altered = json.loads(ledger_path.read_text(encoding="utf-8"))
        altered["owner_role"] = "ending"
        ledger_path.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "saved ledger does not match"):
            LEDGER.finalize_task_root(self.ledger, self.project_root, ledger_path)
        self.assertTrue(ledger_path.exists())

    def test_finalize_detects_marker_replacement_and_preserves_racing_unknown_file(self):
        ledger_path = self.project_root.joinpath(*self.task_root.split("/")) / LEDGER.LEDGER_NAME
        LEDGER.save_ledger(ledger_path, self.ledger)
        marker = ledger_path.parent / LEDGER.MARKER_NAME
        marker.write_bytes(marker.read_bytes())
        with self.assertRaisesRegex(ValueError, "marker identity changed"):
            LEDGER.finalize_task_root(self.ledger, self.project_root, ledger_path)
        self.ledger["binding"]["marker_identity"] = LEDGER._stat_identity(marker.stat())
        LEDGER.save_ledger(ledger_path, self.ledger)
        original_rename = os.rename

        def inject_after_rename(source, destination):
            original_rename(source, destination)
            if Path(source) == ledger_path.parent:
                (Path(destination) / "racing-user.txt").write_text("keep racing user", encoding="utf-8")

        with mock.patch.object(LEDGER.os, "rename", side_effect=inject_after_rename):
            with self.assertRaisesRegex(ValueError, "task root changed"):
                LEDGER.finalize_task_root(self.ledger, self.project_root, ledger_path)
        self.assertEqual((ledger_path.parent / "racing-user.txt").read_text(encoding="utf-8"), "keep racing user")
        self.assertTrue(marker.exists())
        self.assertTrue(ledger_path.exists())

    def test_conflict_is_revalidatable_and_identity_drift_is_not_deleted(self):
        target = self._acquire_file("conflict", "conflict.txt")
        LEDGER.defer_conflict(
            self.ledger, "conflict", "user editing", HASH
        )
        with self.assertRaisesRegex(ValueError, "remains untouched"):
            LEDGER.prepare_release(self.ledger, "conflict")
        LEDGER.resolve_conflict(
            self.ledger, self.project_root, "conflict", "resume", HASH
        )
        self._pass_barriers("conflict")
        LEDGER.prepare_release(self.ledger, "conflict")
        target.unlink()
        target.write_text("replacement", encoding="utf-8")
        self.assertFalse(
            LEDGER.cleanup_path(self.ledger, self.project_root, "conflict")
        )
        resource = next(
            item for item in self.ledger["resources"] if item["id"] == "conflict"
        )
        self.assertEqual(resource["state"], "deferred_conflict")
        self.assertEqual(target.read_text(encoding="utf-8"), "replacement")

    def test_overlapping_paths_and_nested_manifest_drift_are_not_deleted(self):
        relative_directory = self._path("tree")
        LEDGER.acquire_path(
            self.ledger,
            self.project_root,
            "tree",
            relative_directory,
            "tree fixture",
        )
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            LEDGER.acquire_path(
                self.ledger,
                self.project_root,
                "nested",
                f"{relative_directory}/nested.txt",
                "overlap",
            )
        target = self.project_root.joinpath(*relative_directory.split("/"))
        target.mkdir()
        nested = target / "nested.txt"
        nested.write_text("sealed", encoding="utf-8")
        LEDGER.seal_path(self.ledger, self.project_root, "tree")
        self._pass_barriers("tree")
        LEDGER.prepare_release(self.ledger, "tree")
        nested.write_text("user changed", encoding="utf-8")
        self.assertFalse(
            LEDGER.cleanup_path(self.ledger, self.project_root, "tree")
        )
        self.assertEqual(nested.read_text(encoding="utf-8"), "user changed")
        resource = next(
            item for item in self.ledger["resources"] if item["id"] == "tree"
        )
        self.assertEqual(resource["state"], "deferred_conflict")

    def test_cross_project_and_preexisting_task_root_are_rejected(self):
        target = self._acquire_file("bound", "bound.txt")
        self._pass_barriers("bound")
        LEDGER.prepare_release(self.ledger, "bound")
        other_root = self.project_root / "other-project"
        (other_root / "Cache").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "different project root"):
            LEDGER.cleanup_path(self.ledger, other_root, "bound")
        self.assertTrue(target.exists())
        occupied = self.project_root / "Cache" / "temp-occupied"
        occupied.mkdir()
        sentinel = occupied / "user.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            LEDGER.new_ledger(
                self.project_root, "other-task", "Cache/temp-occupied"
            )
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_marker_alias_symlink_and_nonportable_paths_fail_closed(self):
        marker = self.project_root.joinpath(*self.task_root.split("/")) / LEDGER.MARKER_NAME
        alias = marker.with_name("marker-hardlink")
        os.link(marker, alias)
        with self.assertRaisesRegex(ValueError, "one exact regular file"):
            LEDGER.acquire_path(
                self.ledger,
                self.project_root,
                "blocked",
                self._path("blocked.txt"),
                "blocked",
            )
        alias.unlink()
        invalid_paths = (
            "../outside",
            "/absolute/path",
            "Cache/temp-case/../outside",
            "Cache\\tmp-case\\file",
            "C:/outside/file",
            "//server/share/file",
            "Cache/temp-case/file:stream",
            "Cache/temp-case/control\x01",
            "Cache/temp-/file",
        )
        for index, invalid_path in enumerate(invalid_paths):
            with self.subTest(path=invalid_path):
                with self.assertRaises(ValueError):
                    LEDGER.acquire_path(
                        self.ledger,
                        self.project_root,
                        f"invalid-{index}",
                        invalid_path,
                        "invalid",
                    )
        external = self.project_root / "external.txt"
        external.write_text("keep", encoding="utf-8")
        link_path = self.project_root.joinpath(*self._path("link.txt").split("/"))
        LEDGER.acquire_path(
            self.ledger,
            self.project_root,
            "link",
            self._path("link.txt"),
            "symlink",
        )
        link_path.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "symlink"):
            LEDGER.seal_path(self.ledger, self.project_root, "link")
        self.assertEqual(external.read_text(encoding="utf-8"), "keep")

    def test_runtime_requires_typed_identity_and_structured_owner_tool_receipt(self):
        with self.assertRaisesRegex(ValueError, "must never represent"):
            LEDGER.acquire_runtime(
                self.ledger, "bad", "session", {}, "forbidden"
            )
        runtime = LEDGER.acquire_runtime(
            self.ledger,
            "server",
            "server",
            {
                "pid": 4812,
                "start_time": "2026-08-23T01:00:00Z",
                "executable": "python-runtime",
                "cwd": "project-root-fingerprint",
            },
            "test server",
        )
        self._pass_barriers("server")
        LEDGER.prepare_release(self.ledger, "server")
        with self.assertRaisesRegex(ValueError, "does not prove"):
            LEDGER.confirm_runtime_release(
                self.ledger,
                "server",
                {"identity_verified": True, "cleanup_succeeded": True},
            )
        receipt = {
            "ledger_id": self.ledger["ledger_id"],
            "resource_id": "server",
            "identity_digest": runtime["identity_digest"],
            "kind": "server",
            "release_token": runtime["release_token"],
            "owner_tool": "subprocess-handle-adapter",
            "method": "graceful",
            "outcome": "PASS",
            "observed": "exact_handle_absent",
        }
        self.assertTrue(
            LEDGER.confirm_runtime_release(self.ledger, "server", receipt)
        )
        self.assertFalse(
            LEDGER.confirm_runtime_release(self.ledger, "server", receipt)
        )

    def test_lock_failure_preserves_previous_valid_ledger(self):
        ledger_path = self.project_root.joinpath(*self.task_root.split("/")) / LEDGER.LEDGER_NAME
        LEDGER.save_ledger(ledger_path, self.ledger)
        before = ledger_path.read_bytes()
        lock_path = ledger_path.with_name(f"{ledger_path.name}.lock")
        lock_path.write_text("occupied", encoding="utf-8")
        try:
            with self.assertRaisesRegex(RuntimeError, "ledger is locked"):
                LEDGER.save_ledger(ledger_path, self.ledger)
            self.assertEqual(ledger_path.read_bytes(), before)
            LEDGER.load_ledger(ledger_path)
        finally:
            lock_path.unlink()

    def test_cli_round_trip_removes_only_the_registered_path(self):
        cli_project = self.project_root / "cli-project"
        (cli_project / "Cache").mkdir(parents=True)
        cli_task_root = "Cache/temp-cli-roundtrip"
        ledger_path = cli_project / cli_task_root / LEDGER.LEDGER_NAME

        def run(*arguments):
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "--project-root",
                str(cli_project),
                str(ledger_path),
                *arguments,
            ]
            return subprocess.run(
                command, check=True, capture_output=True, text=True
            , **hidden_process_options())

        run("init", "--task-id", "cli-task", "--task-root", cli_task_root)
        run(
            "acquire-path",
            "--id",
            "artifact",
            "--path",
            f"{cli_task_root}/artifact.txt",
            "--purpose",
            "cli fixture",
        )
        run("handoff", "--id", "artifact", "--task-id", "pending-cli-consumer")
        target = cli_project / cli_task_root / "artifact.txt"
        sentinel = cli_project / cli_task_root / "sentinel.txt"
        target.write_text("delete me", encoding="utf-8")
        sentinel.write_text("keep me", encoding="utf-8")
        run("seal-path", "--id", "artifact")
        owner_root = "Outputs/cli"
        owner = cli_project / "Outputs" / "cli"
        owner.mkdir(parents=True)
        declaration = {"owner_id": "cli-output", "owner_kind": "output", "owner_root": owner_root}
        record = owner / "owner.json"
        record.write_text(json.dumps(declaration), encoding="utf-8")
        final_output = owner / "result.txt"
        final_output.write_text("delivered CLI bytes", encoding="utf-8")
        receipt = {**declaration, "owner_record": f"{owner_root}/owner.json", "owner_record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(), "path": f"{owner_root}/result.txt", "sha256": hashlib.sha256(final_output.read_bytes()).hexdigest(), "disposition": "delivery", "purpose": "final_output"}
        run("durable-handoff", "--id", "artifact", "--receipt-json", json.dumps(receipt))
        run("prepare-release", "--id", "artifact")
        output = run("cleanup-path", "--id", "artifact")
        summary = json.loads(output.stdout)
        self.assertEqual(summary["states"], {"released": 1})
        self.assertFalse(target.exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
        with self.assertRaises(subprocess.CalledProcessError) as blocked:
            run("finalize")
        self.assertIn("unknown files", blocked.exception.stderr)
        self.assertTrue(ledger_path.exists())
        sentinel.unlink()
        output = run("finalize")
        self.assertTrue(json.loads(output.stdout)["finalized"])
        self.assertFalse(ledger_path.parent.exists())
        self.assertEqual(final_output.read_text(encoding="utf-8"), "delivered CLI bytes")

    def test_implementation_has_no_resource_or_codex_control_primitives(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("subprocess", imported)
        for forbidden in (
            "os.kill(",
            "signal.",
            "send_message_to_thread",
            "interrupt_agent",
            "set_thread_archived",
            "terminate_task",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import task_artifact_paths as artifacts
import task_cache_cleanup as cleanup

sys.path.insert(0, str(SCRIPTS.parents[1] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


class TaskCacheCleanupTests(unittest.TestCase):
    def setUp(self):
        self.owner = artifacts.resolve_task_artifact_root(SCRIPTS.parents[1], "cache-cleanup-tests", create=True)
        self.fixture = tempfile.TemporaryDirectory(dir=self.owner)
        self.root = Path(self.fixture.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.base = self.root / "artifacts"

    def tearDown(self):
        self.fixture.cleanup()
        self.owner.rmdir()

    def run_root(self, task="mine"):
        return artifacts.resolve_task_artifact_root(self.project, task, artifact_root=self.base, create=True)

    def record_path(self, path):
        return self.base / cleanup.REGISTRY / "runs" / (cleanup._key(path) + ".json")

    def sweep(self, **kwargs):
        return cleanup.checkpoint(self.project, "mine", artifact_root=self.base, apply=True, **kwargs)

    def finish_when_native_readers_close(self, run, finish):
        # Spotlight can briefly read a new fixture; keep every native guard active.
        deadline = time.monotonic() + 5
        for attempt in range(10):
            result = finish()
            entries = result.get("results", [])
            waiting = len(entries) == 1 and entries[0].get("path") == str(run) and entries[0].get("action") == "keep" and entries[0].get("reason") == "active open files or working directory"
            if not waiting or attempt == 9 or time.monotonic() >= deadline:
                return result
            self.assertTrue(run.exists(), result)
            time.sleep(0.1)

    def test_allocator_registers_task_project_run_without_payload_pollution(self):
        run = self.run_root()
        record = json.loads(self.record_path(run).read_text())
        self.assertEqual(record["task_id"], "mine")
        self.assertEqual(record["project_root"], str(self.project))
        self.assertEqual(record["run_id"], artifacts.task_artifact_run_id(run))
        self.assertEqual(record["state"], "working")
        self.assertEqual(list(run.iterdir()), [])

    def test_allocator_automatically_cleans_finished_predecessor(self):
        previous = self.run_root()
        (previous / "disposable.bin").write_bytes(b"old")
        cleanup.touch_run(self.project, "mine", previous, artifact_root=self.base, state="complete")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            following = self.run_root()
        self.assertFalse(previous.exists())
        self.assertTrue(following.is_dir())
        self.assertTrue(self.record_path(following).is_file())

    def test_allocator_proceeds_when_old_run_probe_is_pending(self):
        previous = self.run_root()
        cleanup.touch_run(self.project, "mine", previous, artifact_root=self.base, state="complete")
        with mock.patch.object(cleanup, "probe_activity", side_effect=subprocess.TimeoutExpired("probe", 30)):
            following = self.run_root()
        self.assertTrue(previous.exists())
        self.assertTrue(following.is_dir())

    def test_concurrent_allocators_keep_distinct_registered_runs(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            runs = list(pool.map(self.run_root, ["mine"] * 8))
        self.assertEqual(len(set(runs)), 8)
        self.assertTrue(all(path.is_dir() and self.record_path(path).is_file() for path in runs))

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "native POSIX activity check")
    def test_real_native_finish_deletes_payload_and_registry(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        run = self.run_root()
        (run / "nested").mkdir()
        (run / "nested" / "result.bin").write_bytes(b"disposable" * 100)
        result = self.finish_when_native_readers_close(run, lambda: self.sweep(phase="finish", current_run=run))
        self.assertEqual(result["results"][0]["action"], "deleted", result)
        self.assertEqual(result["bytes_deleted"], 1000)
        self.assertFalse(run.exists())
        self.assertFalse(self.record_path(run).exists())

    def test_transition_cleans_exact_obsolete_run_preserves_current_and_unfinished(self):
        previous, current, working = self.run_root(), self.run_root(), self.run_root()
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep(phase="transition", current_run=current, obsolete_runs=[previous])
        self.assertFalse(previous.exists(), result)
        self.assertTrue(current.exists())
        self.assertTrue(working.exists())
        with self.assertRaises(ValueError):
            self.sweep(current_run=current, obsolete_runs=[current])

    def test_foreign_stale_run_deletes_but_recent_file_and_heartbeat_protect(self):
        old = self.run_root("foreign-old")
        recent = self.run_root("foreign-recent")
        touched = self.run_root("foreign-heartbeat")
        (old / "payload").write_bytes(b"old")
        later = time.time() + 90000
        (recent / "deep").mkdir()
        (recent / "deep" / "new").write_bytes(b"new")
        os.utime(recent / "deep" / "new", (later, later))
        with mock.patch.object(cleanup.time, "time", return_value=later):
            cleanup.touch_run(self.project, "foreign-heartbeat", touched, artifact_root=self.base)
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}), mock.patch.object(cleanup, "_process_identity", return_value=None):
                result = self.sweep()
        self.assertFalse(old.exists(), result)
        self.assertTrue(recent.exists())
        self.assertTrue(touched.exists())

    def test_foreign_old_working_run_protects_original_live_pid_identity(self):
        run = self.run_root("foreign-producer")
        with mock.patch.object(cleanup.time, "time", return_value=time.time() + 90000), mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep()
        self.assertTrue(run.exists())
        self.assertIn("producer", result["results"][0]["reason"])

    def test_retention_recovery_and_native_ledger_always_protected(self):
        retained, recovery, ledger = self.run_root("retain"), self.run_root("recover"), self.run_root("ledger")
        cleanup.touch_run(self.project, "retain", retained, artifact_root=self.base, state="retained")
        cleanup.touch_run(self.project, "recover", recovery, artifact_root=self.base, state="recovery")
        (ledger / ".codex-task-resource-ledger.json").write_text("{}")
        with mock.patch.object(cleanup.time, "time", return_value=time.time() + 90000), mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep()
        self.assertTrue(all(path.exists() for path in (retained, recovery, ledger)), result)
        self.assertTrue(any(item["action"] == "pending" for item in result["results"]))
        for protected in (retained, recovery):
            owner = json.loads(self.record_path(protected).read_text())["task_id"]
            with self.assertRaisesRegex(ValueError, "finish cannot erase"):
                cleanup.checkpoint(self.project, owner, artifact_root=self.base, phase="finish", current_run=protected, apply=True)

    def test_unknown_legacy_is_never_deleted_then_exact_audited_adoption_cleans(self):
        legacy = self.project / "Cache" / "old-generated"
        legacy.mkdir(parents=True)
        (legacy / "intermediate.bin").write_bytes(b"trash")
        cleanup.register_project(self.project, self.base)
        self.assertEqual(cleanup.scan(self.project, self.base)["unclassified"][0]["action"], "needs-review")
        self.assertEqual(self.sweep()["results"], [])
        with self.assertRaises(ValueError):
            cleanup.register_run(self.project, "mine", legacy, artifact_root=self.base)
        cleanup.register_run(self.project, "mine", legacy, artifact_root=self.base, legacy_reason="Exact source hash verified; completed test intermediate has no consumers", state="complete")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            self.sweep()
        self.assertFalse(legacy.exists())

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "native POSIX activity check")
    def test_explicit_owner_release_rejects_open_consumer_then_finishes(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        run = self.run_root()
        payload = run / "input.bin"
        payload.write_bytes(b"retired recovery")
        record = cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="recovery")
        arguments = dict(artifact_root=self.base, run_id=record["run_id"],
                         expected_identity=record["identity"], reason="Actual owner retired this recovery input")
        child = subprocess.Popen([sys.executable, "-c",
                                  "import sys; f=open(sys.argv[1], 'rb'); print('ready', flush=True); sys.stdin.read(1)",
                                  str(payload)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                 **hidden_process_options())
        try:
            self.assertEqual(child.stdout.readline().strip(), "ready")
            with self.assertRaisesRegex(ValueError, "consumer check"):
                cleanup.release_retention(self.project, "mine", run, **arguments)
            self.assertEqual(cleanup._read(self.record_path(run))["state"], "recovery")
        finally:
            child.communicate("x", timeout=10)
        released = cleanup.release_retention(self.project, "mine", run, **arguments)
        self.assertEqual(released["state"], "complete")
        self.assertEqual(released["retention_release"]["previous_state"], "recovery")
        self.assertTrue(run.is_dir(), "release marks completion; checkpoint owns deletion")
        result = self.sweep()
        self.assertFalse(run.exists(), result)
        self.assertFalse(self.record_path(run).exists())

    def test_explicit_owner_release_rejects_wrong_identity_owner_and_blocked(self):
        run = self.run_root()
        record = cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="retained")
        arguments = dict(artifact_root=self.base, run_id=record["run_id"],
                         expected_identity=record["identity"], reason="Actual owner release")
        for changes in ({"expected_identity": [0, 0]}, {"run_id": "wrong"}, {"reason": " "}):
            with self.assertRaises(ValueError):
                cleanup.release_retention(self.project, "mine", run, **(arguments | changes))
        with self.assertRaises(ValueError):
            cleanup.release_retention(self.project, "other", run, **arguments)
        other_project = self.root / "other-project"
        other_project.mkdir()
        with self.assertRaises(ValueError):
            cleanup.release_retention(other_project, "mine", run, **arguments)
        with self.assertRaisesRegex(ValueError, "finish cannot erase"):
            cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="complete")
        self.assertEqual(cleanup._read(self.record_path(run))["state"], "retained")
        record["state"] = "blocked"
        cleanup._write(self.record_path(run), record)
        with self.assertRaisesRegex(ValueError, "only retained/recovery"):
            cleanup.release_retention(self.project, "mine", run, **arguments)
        self.assertEqual(cleanup._read(self.record_path(run))["state"], "blocked")

    def test_path_replacement_and_wrong_task_cannot_be_adopted_or_deleted(self):
        run = self.run_root()
        with self.assertRaises(ValueError):
            cleanup.touch_run(self.project, "another", run, artifact_root=self.base, state="complete")
        original = run.with_name("saved-original")
        run.rename(original)
        run.mkdir()
        (run / "keep").write_bytes(b"new identity")
        with self.assertRaises(ValueError):
            self.sweep(phase="finish", current_run=run)
        self.assertEqual((run / "keep").read_bytes(), b"new identity")

    def test_recursive_mutation_during_probe_invalidates_fresh_plan(self):
        run = self.run_root()
        (run / "nested").mkdir()
        payload = run / "nested" / "payload"
        payload.write_bytes(b"first")
        count = 0
        def mutate_probe(path, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                payload.write_bytes(b"second")
            return {"safe": True}
        with mock.patch.object(cleanup, "probe_activity", side_effect=mutate_probe):
            result = self.sweep(phase="finish", current_run=run)
        self.assertEqual(result["results"][0]["action"], "pending")
        self.assertEqual(payload.read_bytes(), b"second")

    def test_interrupted_deletion_blocks_automatic_retry(self):
        run = self.run_root()
        (run / "payload").write_bytes(b"first")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}), mock.patch.object(cleanup, "_remove_snapshot", side_effect=OSError("permission denied")):
            result = self.sweep(phase="finish", current_run=run)
        self.assertEqual(result["results"][0]["action"], "pending")
        self.assertEqual(json.loads(self.record_path(run).read_text())["state"], "blocked")
        with self.assertRaises(ValueError):
            cleanup.touch_run(self.project, "mine", run, artifact_root=self.base)
        self.assertEqual(self.sweep()["results"][0]["action"], "keep")

    def test_git_and_retention_markers_block_even_inside_deep_tree(self):
        for barrier in (".git", ".keep", ".task-cache-retain"):
            run = self.run_root()
            (run / "nested").mkdir()
            (run / "nested" / barrier).write_text("keep")
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
                self.sweep(phase="finish", current_run=run)
            self.assertTrue(run.exists())

    def test_tracked_legacy_files_cannot_be_registered(self):
        git = shutil.which("git")
        if not git:
            self.skipTest("Git unavailable")
        subprocess.run([git, "init", "-q", str(self.project)], check=True, capture_output=True, **hidden_process_options())
        candidate = self.project / "Cache" / "canonical"
        candidate.mkdir(parents=True)
        (candidate / "source.txt").write_text("authored")
        subprocess.run([git, "-C", str(self.project), "add", "Cache"], check=True, capture_output=True, **hidden_process_options())
        with self.assertRaisesRegex(ValueError, "tracked"):
            cleanup.register_run(self.project, "mine", candidate, artifact_root=self.base, legacy_reason="incorrect assertion")
        self.assertTrue((candidate / "source.txt").exists())

    @unittest.skipIf(sys.platform == "win32", "link privilege differs on Windows")
    def test_link_inside_candidate_cannot_delete_external_target(self):
        run = self.run_root()
        target = self.root / "keep"
        target.write_text("original")
        (run / "link").symlink_to(target)
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            self.sweep(phase="finish", current_run=run)
        self.assertEqual(target.read_text(), "original")
        self.assertTrue(run.exists())

    def test_discovery_registers_roots_only_and_scan_is_fast_without_full_walk(self):
        cache = self.project / "Cache"
        cache.mkdir()
        (cache / "canonical-assets").mkdir()
        (cache / "temp-allowed").mkdir()
        (cache / "remote-allowed").mkdir()
        (cache / "loose.zip").write_bytes(b"unknown")
        dependency = self.project / "node_modules" / "dependency" / "cache"
        dependency.mkdir(parents=True)
        sibling = self.root / "another" / "Cache"
        sibling.mkdir(parents=True)
        (sibling.parent / ".git").mkdir()
        native = self.project / "Library" / "Native" / "Cache"
        native.mkdir(parents=True)
        (native / "data").write_bytes(b"native")
        result = cleanup.discover([self.root], project_root=self.project, artifact_root=self.base, apply=True)
        self.assertEqual({item["path"] for item in result["cache_roots"]}, {str(cache), str(sibling)})
        self.assertEqual([item["path"] for item in result["unclassified_cache_roots"]], [str(native)])
        self.assertEqual({Path(item["path"]).name for item in result["violations"]}, {"canonical-assets", "loose.zip"})
        scanned = cleanup.scan(self.project, self.base)
        self.assertEqual(scanned["registered"], [])
        self.assertEqual(scanned["violations"], result["violations"])
        self.assertTrue(any(item["path"] == str(cache / "canonical-assets") for item in scanned["unclassified"]))
        self.assertEqual(self.sweep()["results"], [])

    def test_windows_and_unknown_platform_fail_closed(self):
        run = self.run_root()
        for platform in ("win32", "unsupported"):
            with mock.patch.object(cleanup.sys, "platform", platform):
                self.assertFalse(cleanup.probe_activity(run)["safe"])

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "native POSIX activity check")
    def test_real_open_file_and_process_reference_are_protected(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        run = self.run_root()
        payload = run / "open.bin"
        payload.write_bytes(b"keep")
        # Keep the path out of argv/cwd so ps cannot mask a missing native handle.
        command = "import sys; stream=open(sys.stdin.readline().strip(), 'rb'); print('ready',flush=True); sys.stdin.readline(); stream.close(); print('closed',flush=True); sys.stdin.readline()"
        process = subprocess.Popen([sys.executable, "-c", command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.root, **hidden_process_options())
        try:
            process.stdin.write(str(payload) + "\n")
            process.stdin.flush()
            self.assertEqual(process.stdout.readline().strip(), "ready")
            active = cleanup.probe_activity(run)
            self.assertFalse(active["safe"], active)
            self.assertEqual(active["reason"], "active open files or working directory", active)
            result = self.sweep(phase="finish", current_run=run)
            self.assertEqual(result["results"][0]["action"], "keep", result)
            self.assertTrue(payload.exists())
            process.stdin.write("close\n")
            process.stdin.flush()
            self.assertEqual(process.stdout.readline().strip(), "closed")
            inactive = cleanup.probe_activity(run)
            self.assertTrue(inactive["safe"], inactive)
        finally:
            process.terminate()
            process.communicate(timeout=10)

    @unittest.skipIf(sys.platform == "win32", "macOS mount syntax requires POSIX paths")
    def test_only_verified_disjoint_macos_mount_warnings_are_scoped(self):
        run = self.run_root()
        outside = self.root / "other-mount"
        warning = f"lsof: WARNING: can't stat() smbfs file system {outside}\n      Output information may be incomplete.\n      assuming \"dev=36000040\" from mount table\n"
        inventory = subprocess.CompletedProcess([], 0, f"disk on / (apfs, local)\nnetwork on {outside} (smbfs, nobrowse)\n", "")
        def native(arguments, **kwargs):
            if Path(arguments[0]).name == "lsof":
                return subprocess.CompletedProcess(arguments, 1, "", warning)
            if Path(arguments[0]).name == "mount":
                return inventory
            return subprocess.CompletedProcess(arguments, 0, "", "")
        with mock.patch.object(cleanup.sys, "platform", "darwin"), mock.patch.object(cleanup.shutil, "which", side_effect=lambda name: name), mock.patch.object(cleanup, "_run_command", side_effect=native):
            clear = cleanup.probe_activity(run)
            self.assertTrue(clear["safe"], clear)
            self.assertEqual(clear["scope_warnings"], [warning.rstrip()])
            for rejected in (warning + "lsof: unexpected warning\n", warning.replace(str(outside), str(run)), warning.replace(str(outside), str(run / "nested-mount")), warning.replace(str(outside), "/"), warning.replace("smbfs", "nfs")):
                with mock.patch.object(cleanup, "_run_command", side_effect=lambda arguments, **kwargs: subprocess.CompletedProcess(arguments, 1, "", rejected) if Path(arguments[0]).name == "lsof" else inventory):
                    result = cleanup.probe_activity(run)
                    self.assertFalse(result["safe"], result)
                    self.assertTrue(result["pending"], result)
            # Target/child mounts must fail even when present in the native table.
            for location in (run, run / "nested-mount"):
                inventory.stdout = f"disk on / (apfs, local)\nnetwork on {location} (smbfs, nobrowse)\n"
                warning = f"lsof: WARNING: can't stat() smbfs file system {location}\n      Output information may be incomplete.\n"
                self.assertFalse(cleanup.probe_activity(run)["safe"])

    def test_cli_scan_reads_actual_registry(self):
        run = self.run_root()
        result = subprocess.run([sys.executable, str(SCRIPTS / "task_cache_cleanup.py"), "scan", "--project-root", str(self.project), "--artifact-root", str(self.base)], capture_output=True, text=True, check=True, **hidden_process_options())
        readback = json.loads(result.stdout)
        self.assertEqual(readback["registered"][0]["path"], str(run))

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "native POSIX activity check")
    def test_allocator_main_and_cleanup_main_complete_real_cli_lifecycle(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        allocated = subprocess.run([sys.executable, str(SCRIPTS / "task_artifact_paths.py"), "--project-root", str(self.project), "--task-id", "cli-task", "--artifact-root", str(self.base), "--create"], capture_output=True, text=True, check=True, **hidden_process_options())
        run = Path(json.loads(allocated.stdout)["task_root"])
        (run / "payload").write_bytes(b"cli")
        def finish():
            finished = subprocess.run([sys.executable, str(SCRIPTS / "task_cache_cleanup.py"), "checkpoint", "--project-root", str(self.project), "--task-id", "cli-task", "--artifact-root", str(self.base), "--phase", "finish", "--current-run", str(run), "--apply"], capture_output=True, text=True, check=True, **hidden_process_options())
            return json.loads(finished.stdout)
        result = self.finish_when_native_readers_close(run, finish)
        self.assertEqual(result["results"][0]["action"], "deleted", result)
        self.assertFalse(run.exists())
        self.assertFalse(self.record_path(run).exists())


if __name__ == "__main__":
    unittest.main()

import json
import contextlib
import hashlib
import io
import os
import shutil
import subprocess
import sys
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
sys.path.insert(0, str(SCRIPTS.parents[1] / "management-skill" / "tests"))
from test_project_cache_artifact_policy import ProjectCacheTestCase


class TaskCacheCleanupTests(ProjectCacheTestCase):
    fixture_task_name = "cache-cleanup-tests"

    def setUp(self):
        self.owner = self.fixture_root.parent
        self.root = self.fixture_root
        self.project = self.root / "project"
        self.project.mkdir()
        self.base = self.project / "Cache"

    def run_root(self, task="mine"):
        return artifacts.resolve_task_artifact_root(self.project, task, artifact_root=self.base, create=True)

    def record_path(self, path):
        return self.base / cleanup.REGISTRY / "runs" / (cleanup._key(path) + ".json")

    def sweep(self, **kwargs):
        return cleanup.checkpoint(self.project, "mine", artifact_root=self.base, apply=True, **kwargs)

    def legacy_run(self):
        base = self.root / "legacy-store"
        registry = base / cleanup.LEGACY_REGISTRY
        for name in ("projects", "runs"):
            (registry / name).mkdir(parents=True)
        (registry / "projects" / (cleanup._key(self.project) + ".json")).write_text(json.dumps({"schema_version": 1, "project_root": str(self.project), "cache_roots": [str(self.base)]}))
        name = artifacts.RUN_NAME_RE.fullmatch(self.run_root().name)
        run = base / ("p-" + cleanup._key(self.project)[:16]) / name[0]
        run.mkdir(parents=True)
        (run / "payload").write_bytes(b"retired legacy support")
        record = json.loads(self.record_path(self.base / name[0]).read_text())
        record.update(path=str(run), identity=cleanup._identity(run.stat()), state="retained", location="external")
        record_path = registry / "runs" / (cleanup._key(run) + ".json")
        record_path.write_text(json.dumps(record))
        return base, run, record, record_path

    def test_legacy_cleanup_retains_guards_and_never_allows_new_output(self):
        base, run, record, record_path = self.legacy_run()
        # Model a legacy external store inside the required task-owned fixture.
        exists = Path.exists
        def fixture_exists(path):
            if path.name == ".git" and path.parent in self.owner.parents:
                return False
            return exists(path)
        with mock.patch.object(Path, "exists", fixture_exists):
            self.assertEqual(cleanup._bound_path(run, self.project, base), "legacy-external")
            with self.assertRaises(ValueError):
                artifacts.resolve_task_artifact_root(self.project, "mine", artifact_root=base, create=True)
            with self.assertRaises(ValueError):
                cleanup.touch_run(self.project, "mine", run, artifact_root=base, state="working")
            result = cleanup.checkpoint(self.project, "mine", artifact_root=base, apply=True)
            self.assertEqual(result["results"][0]["action"], "pending")
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": False, "reason": "live reader"}), self.assertRaises(ValueError):
                cleanup.release_retention(self.project, "mine", run, run_id=record["run_id"], expected_identity=record["identity"], reason="Audited retired support", artifact_root=base)
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
                cleanup.release_retention(self.project, "mine", run, run_id=record["run_id"], expected_identity=record["identity"], reason="Audited retired support", artifact_root=base)
                result = cleanup.checkpoint(self.project, "mine", artifact_root=base, apply=True)
            self.assertEqual(result["results"][0]["action"], "deleted", result)
            self.assertFalse(run.exists())
            self.assertFalse(record_path.exists())

    def test_legacy_owner_identity_and_automatic_checkpoint_remain_exact(self):
        base, run, record, record_path = self.legacy_run()
        exists = Path.exists
        def fixture_exists(path):
            return False if path.name == ".git" and path.parent in self.owner.parents else exists(path)
        with mock.patch.object(Path, "exists", fixture_exists), mock.patch.object(cleanup, "_legacy_base", return_value=base):
            result = self.sweep()
            self.assertTrue(any(item.get("path") == str(run) and item["action"] == "pending" for item in result["results"]))
            with self.assertRaises(ValueError):
                cleanup.release_retention(self.project, "mine", run, run_id=record["run_id"], expected_identity=[0, 0], reason="Audited retired support", artifact_root=base)
            (run / ".git").mkdir()
            with self.assertRaises(ValueError):
                cleanup.release_retention(self.project, "mine", run, run_id=record["run_id"], expected_identity=record["identity"], reason="Audited retired support", artifact_root=base)
        self.assertTrue(run.exists())
        self.assertTrue(record_path.exists())

    def test_remounted_device_requires_original_volume_and_inode(self):
        run = self.run_root()
        record = json.loads(self.record_path(run).read_text())
        record["identity"][0] += 1
        with mock.patch.object(cleanup, "_volume_identity", return_value="same-volume"):
            self.assertFalse(cleanup._record_identity_matches(run, record))
            record["filesystem_uuid"] = "same-volume"
            self.assertTrue(cleanup._record_identity_matches(run, record))
            record["identity"][1] += 1
            self.assertFalse(cleanup._record_identity_matches(run, record))
        record["identity"][1] -= 1
        with mock.patch.object(cleanup, "_volume_identity", return_value="different-volume"):
            self.assertFalse(cleanup._record_identity_matches(run, record))

    def finish_when_native_readers_close(self, run, finish):
        # Spotlight can briefly read a new fixture; keep every native guard active.
        deadline = time.monotonic() + 5
        for attempt in range(10):
            result = finish()
            if "safe" in result:
                waiting = result["safe"] is False and result.get("reason") == "active open files or working directory"
            else:
                entries = result.get("results", [])
                waiting = len(entries) == 1 and entries[0].get("path") == str(run) and entries[0].get("action") in {"keep", "pending"} and entries[0].get("reason") == "active open files or working directory"
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

    def test_allocator_bounds_repeated_pending_review_diagnostics(self):
        report = {"bytes_deleted": 0, "results": [{"action": "pending", "reason": "review required", "path": f"run-{index}"} for index in range(20)]}
        stderr = io.StringIO()
        with mock.patch.object(cleanup, "checkpoint", return_value=report), contextlib.redirect_stderr(stderr):
            run = self.run_root()
        event = json.loads(stderr.getvalue())
        self.assertEqual(event["result_counts"], {"deleted": 0, "pending": 20})
        self.assertEqual(len(event["results"]), 5)
        self.assertEqual(event["results_omitted"], 15)
        self.assertTrue(run.exists())

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
        cleanup.touch_run(self.project, "retain", retained, artifact_root=self.base, state="retained", reason="User is reviewing this exact exported fixture")
        cleanup.touch_run(self.project, "recover", recovery, artifact_root=self.base, state="recovery", reason="Retry still needs this exact failed-job input")
        (ledger / ".codex-task-resource-ledger.json").write_text("{}")
        with mock.patch.object(cleanup.time, "time", return_value=time.time() + 90000), mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep()
        self.assertTrue(all(path.exists() for path in (retained, recovery, ledger)), result)
        self.assertTrue(any(item["action"] == "pending" for item in result["results"]))
        for protected in (retained, recovery):
            owner = json.loads(self.record_path(protected).read_text())["task_id"]
            with self.assertRaisesRegex(ValueError, "finish cannot erase"):
                cleanup.checkpoint(self.project, owner, artifact_root=self.base, phase="finish", current_run=protected, apply=True)

    def test_retention_requires_concrete_reason_and_due_review_does_not_delete(self):
        run = self.run_root()
        for state in ("retained", "recovery"):
            for reason in (None, " ", "fresh task-owned disposable support allocation"):
                with self.assertRaisesRegex(ValueError, "concrete current"):
                    cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state=state, reason=reason)
        record = cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="retained", reason="User reviews this native fixture until its acceptance decision")
        self.assertEqual(record["retention_review_at"], record["heartbeat"] + cleanup.STALE_SECONDS)
        current = self.sweep()
        self.assertEqual(current["results"][0]["action"], "keep")
        with mock.patch.object(cleanup.time, "time", return_value=record["retention_review_at"] + 1):
            due = self.sweep()
        self.assertEqual(due["results"][0]["action"], "pending")
        self.assertIn("owner review required", due["results"][0]["reason"])
        self.assertTrue(run.exists())
        record.pop("retention_reason")
        record.pop("retention_review_at")
        cleanup._write(self.record_path(run), record)
        legacy = self.sweep()
        self.assertEqual(legacy["results"][0]["action"], "pending")
        self.assertTrue(run.exists())

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
        record = cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="recovery", reason="Recovery input needed for an identified retry")
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
        record = cleanup.touch_run(self.project, "mine", run, artifact_root=self.base, state="retained", reason="Explicit user fixture review remains open")
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

    def test_metadata_only_changes_during_native_probes_keep_exact_cleanup_valid(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        run = self.run_root()
        payload = run / "payload"
        payload.write_bytes(b"unchanged")
        native_probe = cleanup.probe_activity
        def update_metadata(path, **kwargs):
            result = native_probe(path, **kwargs)
            os.chmod(payload, payload.stat().st_mode)
            return result
        with mock.patch.object(cleanup, "probe_activity", side_effect=update_metadata):
            result = self.finish_when_native_readers_close(run, lambda: self.sweep(phase="finish", current_run=run))
        self.assertEqual(result["results"][0]["action"], "deleted", result)
        self.assertFalse(run.exists())

    def test_interrupted_deletion_resumes_only_its_original_proof(self):
        run = self.run_root()
        (run / "payload").write_bytes(b"first")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}), mock.patch.object(cleanup, "_remove_snapshot", side_effect=OSError("permission denied")):
            result = self.sweep(phase="finish", current_run=run)
        self.assertEqual(result["results"][0]["action"], "pending")
        self.assertEqual(json.loads(self.record_path(run).read_text())["state"], "blocked")
        with self.assertRaises(ValueError):
            cleanup.touch_run(self.project, "mine", run, artifact_root=self.base)
        self.assertTrue(cleanup._plan_path(self.record_path(run)).is_file())
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            resumed = self.sweep(phase="finish", current_run=run)
        self.assertTrue(resumed["requested_complete"], resumed)
        self.assertTrue(resumed["results"][0]["resumed"])
        self.assertFalse(run.exists())
        self.assertFalse(cleanup._plan_path(self.record_path(run)).exists())
        self.assertTrue(self.sweep(phase="finish", current_run=run)["requested_complete"])

    def test_original_plan_rejects_new_changed_and_corrupt_recovery_inputs(self):
        for mutation in ("new", "changed", "proof", "retention"):
            run = self.run_root()
            payload = run / "payload"
            payload.write_bytes(b"first")
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}), mock.patch.object(cleanup, "_remove_snapshot", side_effect=OSError("injected interrupted unlink")):
                self.sweep(phase="finish", current_run=run)
            if mutation == "new":
                (run / "new-input").write_bytes(b"future consumer")
            elif mutation == "changed":
                details = payload.stat()
                payload.write_bytes(b"later")
                os.utime(payload, ns=(details.st_atime_ns, details.st_mtime_ns))
            elif mutation == "proof":
                cleanup._plan_path(self.record_path(run)).write_bytes(b"changed proof")
            else:
                (run / ".retain").write_text("Concrete future review consumer")
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
                result = self.sweep(phase="finish", current_run=run, requested_only=True)
            self.assertFalse(result["requested_complete"], result)
            self.assertTrue(run.is_dir())
            self.assertEqual(payload.read_bytes(), b"later" if mutation == "changed" else b"first")

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "native POSIX process/consumer checks")
    def test_process_death_releases_lock_and_resumes_real_partial_deletion(self):
        if not shutil.which("lsof") or not shutil.which("ps"):
            self.skipTest("native probes unavailable")
        run = self.run_root()
        (run / "first").write_bytes(b"first payload")
        (run / "second").write_bytes(b"second payload")
        program = "\n".join([
            "import json,os,sys,time; from pathlib import Path",
            "sys.path.insert(0,sys.argv[1]); import task_cache_cleanup as c",
            "def interrupt(path,snapshot,**kwargs):",
            "    (path/'first').unlink()",
            "    os._exit(41)",
            "c._remove_snapshot=interrupt",
            "deadline=time.monotonic()+8",
            "for attempt in range(15):",
            "    result=c.checkpoint(Path(sys.argv[2]),'mine',phase='finish',current_run=Path(sys.argv[3]),apply=True,requested_only=True)",
            "    entries=result.get('results',[])",
            "    waiting=len(entries)==1 and entries[0].get('reason')=='active open files or working directory'",
            "    if not waiting or time.monotonic()>=deadline: break",
            "    time.sleep(.1)",
            "print(json.dumps(result))",
        ])
        child = subprocess.run([sys.executable, "-B", "-c", program, str(SCRIPTS), str(self.project), str(run)], capture_output=True, text=True, timeout=30, **hidden_process_options())
        self.assertEqual(child.returncode, 41, child.stdout + child.stderr)
        self.assertFalse((run / "first").exists())
        self.assertTrue((run / "second").exists())
        self.assertTrue(self.record_path(run).with_suffix(".lock").exists())
        result = self.finish_when_native_readers_close(run, lambda: self.sweep(phase="finish", current_run=run, requested_only=True))
        self.assertTrue(result["requested_complete"], result)
        self.assertFalse(self.record_path(run).with_suffix(".lock").exists())
        self.assertFalse(cleanup._plan_path(self.record_path(run)).exists())

    def test_requested_finish_precedes_slow_foreign_records(self):
        def allocate(task, prefix):
            task_key = hashlib.sha256(task.encode()).hexdigest()[:24]
            for number in range(1000):
                run_id = f"{number:032x}"
                candidate = self.base / f"temp-{task_key}-{run_id}"
                if cleanup._key(candidate).startswith(prefix):
                    return artifacts.resolve_task_artifact_root(self.project, task, run_id=run_id, create=True)
            self.fail("could not construct ordered registry fixture")
        own = allocate("mine", "f")
        foreign = allocate("foreign", "0")
        calls = []
        sweep = cleanup._sweep_record
        def delayed(record_path, *args):
            calls.append(record_path.stem)
            if record_path.stem == cleanup._key(foreign):
                time.sleep(1.1)
            return sweep(record_path, *args)
        with mock.patch.object(cleanup, "_sweep_record", side_effect=delayed), mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep(phase="finish", current_run=own, budget_seconds=1)
        self.assertTrue(result["requested_complete"], result)
        self.assertEqual(calls[0], cleanup._key(own))
        self.assertTrue(foreign.is_dir())

    def test_fresh_completed_foreign_run_closes_without_delaying_a_day(self):
        retired = self.run_root("completed-owner")
        (retired / "payload").write_bytes(b"delivered disposable support")
        cleanup.touch_run(self.project, "completed-owner", retired, state="complete")
        active = self.run_root("still-working")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep()
        self.assertFalse(retired.exists(), result)
        self.assertFalse(self.record_path(retired).exists())
        self.assertTrue(active.is_dir())

    def test_allocator_cli_failure_closes_created_payload_and_registration(self):
        created = []
        native_environment = artifacts.task_artifact_environment
        def fail_after_tmp_creation(root, **kwargs):
            created.append(root)
            native_environment(root, **kwargs)
            (root / "tmp" / "partial-output").write_bytes(b"failed setup support")
            raise OSError("injected environment setup failure")
        argv = ["task_artifact_paths.py", "--project-root", str(self.project), "--task-id", "mine", "--create"]
        output = io.StringIO()
        with mock.patch.object(sys, "argv", argv), mock.patch.object(artifacts, "task_artifact_environment", side_effect=fail_after_tmp_creation), mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}), contextlib.redirect_stderr(output):
            status = artifacts.main()
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["cleanup"], "removed")
        self.assertEqual(len(created), 1)
        self.assertFalse(created[0].exists())
        self.assertFalse(self.record_path(created[0]).exists())

    def test_abandoned_control_writes_have_one_slot_and_close_with_owner(self):
        run = self.run_root()
        record = self.record_path(run)
        pending = record.with_name(record.name + ".pending")
        pending.write_bytes(b"interrupted record write")
        plan_pending = cleanup._plan_path(record).with_name(cleanup._plan_path(record).name + ".pending")
        plan_pending.parent.mkdir(exist_ok=True)
        plan_pending.write_bytes(b"interrupted proof write")
        with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
            result = self.sweep(phase="finish", current_run=run, requested_only=True)
        self.assertTrue(result["requested_complete"], result)
        self.assertFalse(pending.exists())
        self.assertFalse(plan_pending.exists())

        protected = self.run_root()
        pending = self.record_path(protected).with_name(self.record_path(protected).name + ".pending")
        pending.write_bytes(b"old interrupted slot")
        def writer_reappears(path, **kwargs):
            pending.write_bytes(b"new writer input")
            return {"safe": True}
        with mock.patch.object(cleanup, "probe_activity", side_effect=writer_reappears), self.assertRaisesRegex(ValueError, "control record changed"):
            self.sweep(phase="finish", current_run=protected, requested_only=True)
        self.assertEqual(pending.read_bytes(), b"new writer input")
        self.assertTrue(protected.is_dir())

    def test_child_cleanup_cannot_bypass_parent_retention_or_native_ledger(self):
        for marker in (None, ".codex-task-resource-ledger.json", ".retain", ".git"):
            parent = self.run_root("parent")
            child = parent / "Library"
            child.mkdir()
            (child / "source-input").write_bytes(b"future input")
            if marker is None:
                cleanup.touch_run(self.project, "parent", parent, state="retained", reason="Prepared environment needed after pending artwork")
            else:
                (parent / marker).write_text("original native owner")
            with self.assertRaises(ValueError):
                cleanup.register_run(self.project, "mine", child, legacy_reason="Attempted independent child cleanup", state="complete")
            self.assertEqual((child / "source-input").read_bytes(), b"future input")

    def test_parent_cleanup_cannot_bypass_registered_child_lifecycle(self):
        for state in ("working", "retained", "complete"):
            parent = self.run_root()
            child = parent / "prepared-input"
            child.mkdir()
            payload = child / "source-input"
            payload.write_bytes(b"separate consumer input")
            reason = "Prepared child consumed after pending artwork" if state == "retained" else None
            cleanup.register_run(self.project, "child-owner", child, state=state, legacy_reason=reason or "Exact child created by the fixture")
            with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
                result = self.sweep(phase="finish", current_run=parent, requested_only=True)
            self.assertFalse(result["requested_complete"], result)
            self.assertEqual(payload.read_bytes(), b"separate consumer input")
            self.assertTrue(self.record_path(child).exists())
            if state == "complete":
                with mock.patch.object(cleanup, "probe_activity", return_value={"safe": True}):
                    child_result = cleanup.checkpoint(self.project, "child-owner", phase="finish", current_run=child, apply=True, requested_only=True)
                    parent_result = self.sweep(phase="finish", current_run=parent, requested_only=True)
                self.assertTrue(child_result["requested_complete"], child_result)
                self.assertTrue(parent_result["requested_complete"], parent_result)

    def test_native_lock_storage_is_bounded_and_live_legacy_owner_is_preserved(self):
        run = self.run_root()
        path = self.record_path(run)
        marker = path.with_suffix(".lock")
        marker.write_text(str(os.getpid()))
        before = marker.read_bytes()
        with self.assertRaises(ValueError):
            with cleanup._lock(path):
                self.fail("live legacy lock was bypassed")
        self.assertEqual(marker.read_bytes(), before)
        marker.unlink()
        for number in range(90):
            target = path.with_name(hashlib.sha256(str(number).encode()).hexdigest() + ".json")
            with cleanup._lock(target):
                self.assertTrue(target.with_suffix(".lock").exists())
        self.assertLessEqual(len(list((self.base / cleanup.REGISTRY / "locks").iterdir())), 64)
        self.assertEqual(list(path.parent.glob("*.lock")), [])

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

    def test_remote_prefix_requires_owner_review_without_adopting_or_deleting(self):
        names = {"remote-game-config", "remote-ios-runtime-evidence", *{f"remote-test-{index}" for index in range(6)}}
        for name in names:
            payload = self.base / name / "nested" / "Cache"
            payload.mkdir(parents=True)
            (payload / "payload").write_bytes(name.encode())
        discovered = cleanup.discover([self.project], project_root=self.project, artifact_root=self.base)
        scanned = cleanup.scan(self.project, self.base)
        checkpoint = self.sweep()
        for report in (discovered, scanned, checkpoint):
            self.assertEqual({Path(item["path"]).name for item in report["remote_review"]}, names)
            self.assertTrue(all(item["action"] == "needs-owner-review" for item in report["remote_review"]))
        self.assertEqual(scanned["registered"], [])
        self.assertEqual(checkpoint["results"], [])
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            run = self.run_root()
        event = json.loads(stderr.getvalue())
        self.assertEqual(event["remote_review_count"], len(names))
        self.assertEqual(len(event["remote_review"]), 5)
        self.assertEqual(event["remote_review_omitted"], 3)
        self.assertTrue(run.is_dir())
        self.assertEqual({Path(item["path"]).name for item in self.sweep()["remote_review"]}, names)
        for name in names:
            self.assertEqual((self.base / name / "nested" / "Cache" / "payload").read_bytes(), name.encode())

    def test_open_handle_inventory_uses_exact_directory_boundary(self):
        run = self.run_root()
        def native(arguments, **kwargs):
            if Path(arguments[0]).name == "lsof":
                self.assertNotIn("+D", arguments)
                self.assertIn("-Fpn0", arguments)
                return subprocess.CompletedProcess(arguments, 0, fields, "")
            return subprocess.CompletedProcess(arguments, 0, "", "")
        with mock.patch.object(cleanup.sys, "platform", "darwin"), mock.patch.object(cleanup.shutil, "which", side_effect=lambda name: name), mock.patch.object(cleanup, "_run_command", side_effect=native):
            fields = f"p123\0\nn{run}-sibling/open.bin\0\n"
            self.assertTrue(cleanup.probe_activity(run)["safe"])
            fields += f"n{run}/directory with spaces/file\nname.bin\0\n"
            self.assertEqual(cleanup.probe_activity(run)["reason"], "active open files or working directory")
            fields = "unverified output"
            self.assertTrue(cleanup.probe_activity(run)["pending"])

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
            inactive = self.finish_when_native_readers_close(run, lambda: cleanup.probe_activity(run))
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

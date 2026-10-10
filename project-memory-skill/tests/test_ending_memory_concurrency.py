import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ARTIFACT_PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT_PROJECT / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root, validate_external_directory


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "project-memory-skill" / "scripts"
sys.path.insert(0, str(ROOT / "code-skill" / "scripts"))
from hidden_process import hidden_process_options
from test_ending_memory import MODULE as ending, RUNTIME


BARRIER = '''
import os
import time
from pathlib import Path
ready = os.environ.get("ENDING_FIXTURE_READY")
start = os.environ.get("ENDING_FIXTURE_START")
if ready and start:
    Path(ready).write_text("ready", encoding="utf-8")
    deadline = time.monotonic() + 15
    while not Path(start).exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("Ending fixture barrier timed out")
        time.sleep(0.01)
'''

RUNTIME_BOUNDARY = '''
original_record_event = record_event

def record_event(**fields):
    if os.environ.get("ENDING_FIXTURE_FAIL") == "true":
        raise RuntimeError("injected Ending runtime failure")
    marker = os.environ.get("ENDING_FIXTURE_RECORD_STARTED")
    if marker:
        Path(marker).write_text("recording", encoding="utf-8")
    time.sleep(0.15)
    return original_record_event(**fields)
'''


class EndingMemoryConcurrencyTests(unittest.TestCase):
    def setUp(self):
        override = os.environ.get("ENDING_CONCURRENCY_TEST_CACHE")
        cache = validate_external_directory(override, ARTIFACT_PROJECT) if override is not None else resolve_task_artifact_root(ARTIFACT_PROJECT, "ending-memory-concurrency-tests", create=True)
        cache.mkdir(parents=True, exist_ok=True)
        if override is None:
            self.addCleanup(cache.rmdir)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-ending-concurrency-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.vault = self.root / "vault"
        (self.vault / "AI Memory").mkdir(parents=True)
        (self.vault / "Projects" / "SharedProject").mkdir(parents=True)
        (self.vault / "AI Memory" / "ai_memory.py").write_text(BARRIER + RUNTIME + RUNTIME_BOUNDARY, encoding="utf-8")
        self.first = self.create_project("first")
        self.second = self.create_project("second")

    def create_project(self, directory):
        project = self.root / directory / "SharedProject"
        project.mkdir(parents=True)
        (project / "worker.py").write_text("class Worker:\n    def read(self): return 1\n    def write(self): return 2\n", encoding="utf-8")
        return project

    def outcome(self, project, symbol):
        return {"module": "worker", "summary": f"Preserve the {symbol} contract", "reason": "Keep exact method ownership", "result": "The completed method contract remains available", "files": ["worker.py"], "symbols": [symbol], "source_hashes": {"worker.py": hashlib.sha256((project / "worker.py").read_bytes()).hexdigest()}, "verification_status": "passed", "verification": ["The originating task verified this exact method"]}

    def stop_process(self, process):
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)

    def launch(self, project, symbol, label, *, barrier=False, fail=False, payload=None):
        outcome = self.root / f"{label}.json"
        outcome.write_text(json.dumps(self.outcome(project, symbol) if payload is None else payload), encoding="utf-8")
        environment = {**os.environ, "CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": str(self.vault), "PYTHONIOENCODING": "utf-8", "ENDING_FIXTURE_FAIL": "true" if fail else "false", "ENDING_FIXTURE_READY": str(self.root / f"{label}.ready") if barrier else "", "ENDING_FIXTURE_START": str(self.root / "start") if barrier else "", "ENDING_FIXTURE_RECORD_STARTED": str(self.root / f"{label}.record")}
        process = subprocess.Popen([sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "ending_memory.py"), "--project-root", str(project), "--vault", str(self.vault), "--outcome", str(outcome)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=environment, **hidden_process_options())
        self.addCleanup(self.stop_process, process)
        return process

    def run_concurrent(self, jobs):
        processes = [self.launch(project, symbol, label, barrier=True) for project, symbol, label in jobs]
        ready = [self.root / f"{label}.ready" for project, symbol, label in jobs]
        deadline = time.monotonic() + 10
        while not all(path.is_file() for path in ready):
            for process in processes:
                if process.poll() is not None:
                    output, error = process.communicate(timeout=5)
                    self.fail(f"Ending exited before the synchronized start: {process.returncode}, {output}, {error}")
            if time.monotonic() >= deadline:
                self.fail("Both Ending processes did not reach the runtime-load barrier")
            time.sleep(0.01)
        (self.root / "start").write_text("start", encoding="utf-8")
        results = []
        for process in processes:
            output, error = process.communicate(timeout=20)
            results.append({"returncode": process.returncode, "output": output, "error": error})
        return results

    def read_events(self):
        path = self.vault / "AI Memory" / "events.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_guarded_synthesis_holds_project_lock_across_history_and_index_write(self):
        original = self.launch(self.first, "Worker.read", "original")
        output, error = original.communicate(timeout=20)
        self.assertEqual(original.returncode, 0, error)
        index = self.vault / "Projects/SharedProject/Memory.json"
        expected = hashlib.sha256(index.read_bytes()).hexdigest()
        runtime = ending._vault_runtime(self.vault)
        event = runtime.record_event(project="SharedProject", module="worker", event_type="general", summary="A direct concurrent update must respect the reviewed index", reason="Check the real shared project lock", result="Direct writes use the same guarded index", verification_status="not-run", files=["worker.py"], verification=[], decisions=[], risks=[], module_change_values=[])
        synthesis = self.launch(self.first, "Worker.read", "synthesis", payload={"expected_index_sha256": expected, "consolidation": {"summary": "Navigation for the established worker contract"}})
        marker = self.root / "synthesis.record"
        deadline = time.monotonic() + 10
        while not marker.exists():
            if synthesis.poll() is not None or time.monotonic() >= deadline:
                self.fail("Synthesis did not reach its protected canonical record boundary")
            time.sleep(0.01)
        program = "import sys; sys.path.insert(0,sys.argv[1]); import project_knowledge as knowledge; knowledge.apply_entries(sys.argv[2],sys.argv[3],[{'scope':'module','module':'worker','summary':'This direct update must not replace the reviewed snapshot'}],event_id=sys.argv[4],expected_index_sha256=sys.argv[5])"
        direct = subprocess.Popen([sys.executable, "-B", "-c", program, str(SCRIPTS), str(self.first), str(self.vault), event["event_id"], expected], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", **hidden_process_options())
        self.addCleanup(self.stop_process, direct)
        output, error = synthesis.communicate(timeout=20)
        self.assertEqual(synthesis.returncode, 0, error)
        self.assertFalse(json.loads(output)["current_memory"]["maintenance_due"])
        output, error = direct.communicate(timeout=20)
        self.assertNotEqual(direct.returncode, 0)
        self.assertIn("index changed", error)
        saved = json.loads(index.read_text(encoding="utf-8"))
        self.assertEqual(saved["synthesis"]["summary"], "Navigation for the established worker contract")
        self.assertEqual(len(saved["entries"]), 1)

    def test_same_name_competing_roots_reject_loser_before_history_append(self):
        results = self.run_concurrent([(self.first, "Worker.read", "first"), (self.second, "Worker.write", "second")])
        successful = [result for result in results if result["returncode"] == 0]
        rejected = [result for result in results if result["returncode"] != 0]
        self.assertEqual(len(successful), 1, results)
        self.assertEqual(len(rejected), 1, results)
        self.assertIn("different exact project", rejected[0]["error"])
        receipt = json.loads(successful[0]["output"])
        self.assertEqual(receipt["status"], "written")
        self.assertTrue(receipt["read_back_verified"])
        events = self.read_events()
        index = json.loads((self.vault / "Projects" / "SharedProject" / "Memory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(events), 1)
        self.assertEqual(len(index["entries"]), 1)
        self.assertEqual(index["entries"][0]["event_id"], events[0]["event_id"])
        self.assertEqual(receipt["event_id"], events[0]["event_id"])
        self.assertFalse((self.root / "codex").exists())

    def test_same_root_concurrent_methods_keep_both_history_and_current_entries(self):
        results = self.run_concurrent([(self.first, "Worker.read", "read"), (self.first, "Worker.write", "write")])
        self.assertTrue(all(result["returncode"] == 0 for result in results), results)
        receipts = [json.loads(result["output"]) for result in results]
        self.assertTrue(all(receipt["read_back_verified"] and receipt["current_memory"]["read_back_verified"] for receipt in receipts))
        events = self.read_events()
        index = json.loads((self.vault / "Projects" / "SharedProject" / "Memory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(events), 2)
        self.assertEqual({entry["symbol"] for entry in index["entries"]}, {"Worker.read", "Worker.write"})
        self.assertEqual({entry["event_id"] for entry in index["entries"]}, {event["event_id"] for event in events})
        self.assertEqual(len({receipt["event_id"] for receipt in receipts}), 2)

    def test_runtime_exception_releases_global_lock_for_retry(self):
        failed = self.launch(self.first, "Worker.read", "failed", fail=True)
        failed_output, failed_error = failed.communicate(timeout=20)
        self.assertNotEqual(failed.returncode, 0, failed_output)
        self.assertIn("injected Ending runtime failure", failed_error)
        self.assertEqual(self.read_events(), [])
        retry = self.launch(self.first, "Worker.read", "retry")
        output, error = retry.communicate(timeout=20)
        self.assertEqual(retry.returncode, 0, error)
        self.assertTrue(json.loads(output)["read_back_verified"])
        self.assertEqual(len(self.read_events()), 1)


if __name__ == "__main__":
    unittest.main()

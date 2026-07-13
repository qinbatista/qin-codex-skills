import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "ending_task_ledger.py"
SPEC = importlib.util.spec_from_file_location("ending_task_ledger", SCRIPT_PATH)
LEDGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LEDGER)


class EndingTaskLedgerTests(unittest.TestCase):
    def test_passed_lifecycle_opens_final_gate(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "project"
            project.mkdir()
            (project / "script.py").write_text("value = 1\n", encoding="utf-8")
            store = root / "store"
            started = LEDGER.start_lifecycle("code", project, "Implemented the requested script change", project, "runtime", ["script.py"], store=store)
            pending = LEDGER.audit_lifecycle(started["lifecycle_id"], store)
            passed = LEDGER.record_event(started["lifecycle_id"], "pass", "Independent Real Verify passed", ["Focused test passed"], store=store)
            audit = LEDGER.audit_lifecycle(started["lifecycle_id"], store)
            self.assertEqual(pending["terminal_status"], "pending")
            self.assertEqual(passed["lifecycle_status"], "passed")
            self.assertTrue(audit["final_gate_passed"])
            self.assertEqual(audit["chain"], [started["lifecycle_id"]])

    def test_failure_is_logged_before_repair_and_repair_has_own_ending(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = root / "store"
            original = LEDGER.start_lifecycle("code", root, "Original task result", store=store)
            LEDGER.record_event(original["lifecycle_id"], "fail", "Real Verify found a correctness error", ["Expected 2 but observed 1"], "value-mismatch", store)
            repair = LEDGER.start_lifecycle("repair", root, "Repair the verified value mismatch", repair_of_lifecycle_id=original["lifecycle_id"], store=store)
            before_reverify = LEDGER.audit_lifecycle(original["lifecycle_id"], store)
            LEDGER.record_event(repair["lifecycle_id"], "pass", "A different Ending verifier passed the repaired result", ["Regression passed"], store=store)
            after_reverify = LEDGER.audit_lifecycle(original["lifecycle_id"], store)
            events = [json.loads(line) for line in (store / "index.jsonl").read_text(encoding="utf-8").splitlines()]
            failure_index = next(index for index, event in enumerate(events) if event["event"] == "fail")
            repair_index = next(index for index, event in enumerate(events) if event["event"] == "repair_started")
            self.assertEqual(before_reverify["terminal_status"], "pending")
            self.assertLess(failure_index, repair_index)
            self.assertEqual(after_reverify["terminal_status"], "passed")
            self.assertEqual(after_reverify["chain"], [original["lifecycle_id"], repair["lifecycle_id"]])

    def test_repair_requires_a_failed_parent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = root / "store"
            original = LEDGER.start_lifecycle("text", root, "Original result", store=store)
            with self.assertRaisesRegex(ValueError, "failed parent"):
                LEDGER.start_lifecycle("repair", root, "Invalid early repair", repair_of_lifecycle_id=original["lifecycle_id"], store=store)

    def test_repair_attempts_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = root / "store"
            original = LEDGER.start_lifecycle("code", root, "Original result", store=store, max_repair_attempts=1)
            LEDGER.record_event(original["lifecycle_id"], "fail", "First verification failed", store=store)
            repair = LEDGER.start_lifecycle("repair", root, "First repair", repair_of_lifecycle_id=original["lifecycle_id"], store=store)
            LEDGER.record_event(repair["lifecycle_id"], "fail", "Repair verification failed", store=store)
            with self.assertRaisesRegex(ValueError, "repair attempt limit exceeded"):
                LEDGER.start_lifecycle("repair", root, "Disallowed second repair", repair_of_lifecycle_id=repair["lifecycle_id"], store=store)
            audit = LEDGER.audit_lifecycle(original["lifecycle_id"], store)
            repair_state = json.loads((store / "lifecycles" / f"{repair['lifecycle_id']}.json").read_text(encoding="utf-8"))
            events = [json.loads(line) for line in (store / "index.jsonl").read_text(encoding="utf-8").splitlines()]
            repair_failure_index = next(index for index, event in enumerate(events) if event["event"] == "fail" and event["lifecycle_id"] == repair["lifecycle_id"])
            blocked_index = next(index for index, event in enumerate(events) if event["event"] == "blocked" and event["lifecycle_id"] == repair["lifecycle_id"])
            self.assertEqual(audit["terminal_status"], "blocked")
            self.assertEqual(audit["status"], "blocked")
            self.assertTrue(audit["final_gate_passed"])
            self.assertEqual(audit["chain"], [original["lifecycle_id"], repair["lifecycle_id"]])
            self.assertEqual(repair_state["status"], "blocked")
            self.assertEqual(repair_state["events"][-1]["event"], "blocked")
            self.assertLess(repair_failure_index, blocked_index)
            self.assertEqual(sum(event["event"] == "started" for event in events), 2)


if __name__ == "__main__":
    unittest.main()

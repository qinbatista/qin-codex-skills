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


RUNTIME = '''
import json
from pathlib import Path
EVENTS_PATH = Path(__file__).with_name("events.jsonl")
def _read_events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []
def add_project(project, vault_root):
    (Path(vault_root) / 'Projects' / project).mkdir(parents=True)
    return {'status': 'written', 'project': project}
def record_event(**fields):
    events = _read_events(EVENTS_PATH)
    duplicate = next((event for event in events if event['semantic'] == fields), None)
    if duplicate:
        return {"status": "duplicate", "event_id": duplicate["event_id"]}
    changes = [{"module": fields["module"]}] + [{"module": value.split('=', 1)[0], "summary": value.split('=', 1)[1]} for value in fields.get('module_change_values', [])]
    event = {"event_id": "vault-event-" + str(len(events) + 1), "module_changes": changes, "semantic": fields, **fields}
    with EVENTS_PATH.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event) + "\\n")
    return {"status": "written", "event_id": event["event_id"]}
def render_views():
    return {"status": "ready"}
'''


class EndingMemoryTests(unittest.TestCase):
    def setUp(self):
        cache = Path(__file__).resolve().parents[2] / "Cache"
        cache.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-ending-memory-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "ExampleProject"
        self.project.mkdir()
        (self.project / "script.py").write_text("value = 1\n")
        self.vault = self.root / "vault"
        (self.vault / "Projects" / "ExampleProject").mkdir(parents=True)
        runtime_path = self.vault / "AI Memory" / "ai_memory.py"
        runtime_path.parent.mkdir()
        runtime_path.write_text(RUNTIME)
        self.outcome = {"module": "example", "summary": "Saved one result", "reason": "Preserve the outcome", "result": "Result available", "files": ["script.py"], "verification_status": "passed", "verification": ["Observed real output"]}

    def closeout(self, payload=None, **changes):
        args = {"project_root": self.project}
        args.update(changes)
        return MODULE.closeout(self.outcome if payload is None else payload, **args)

    def test_unsafe_missing_vault_is_pending_and_creates_no_local_memory(self):
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=None):
            result = self.closeout(vault=self.project / "Cache" / "memory")
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["reason"], "unsafe_vault_location")
        self.assertFalse((self.root / "memory").exists())

    def test_no_durable_outcome_is_skipped(self):
        self.assertEqual(self.closeout({})["reason"], "no_durable_information")

    def test_local_store_argument_is_refused(self):
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault):
            with self.assertRaisesRegex(ValueError, "Codex-local memory stores are retired"):
                self.closeout(store=self.root / "memory")
        self.assertFalse((self.root / "memory").exists())

    def test_observable_vault_write_and_duplicate_readback(self):
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault):
            first = self.closeout()
            second = self.closeout()
        self.assertEqual(first["status"], "written")
        self.assertEqual(second["status"], "duplicate")
        self.assertEqual(first["event_id"], "vault-event-1")
        self.assertTrue(first["read_back_verified"])
        self.assertEqual(set(first), {"status", "event_id", "project", "vault", "vault_document", "read_back_verified", "verification_owner", "purpose", "current_memory"})
        self.assertTrue(first["current_memory"]["read_back_verified"])
        events = [json.loads(line) for line in (self.vault / "AI Memory" / "events.jsonl").read_text().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["project"], "ExampleProject")
        self.assertFalse((self.project / "memory").exists())

    def test_new_project_is_registered_in_the_vault_before_write(self):
        (self.vault / "Projects" / "ExampleProject").rmdir()
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault):
            result = self.closeout()
        self.assertEqual(result["status"], "written")
        self.assertTrue((self.vault / "Projects" / "ExampleProject").is_dir())
        self.assertEqual(result["vault"], str(self.vault))

    def test_outcome_cannot_override_project_or_run_commands(self):
        for key in ("project_root", "command", "checks"):
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                self.closeout({**self.outcome, key: "do something"})

    def test_distinct_methods_keep_their_parent_and_separate_history(self):
        self.closeout(vault=self.vault)
        first = self.closeout({**self.outcome, "symbols": ["Worker.read"]}, vault=self.vault)
        second = self.closeout({**self.outcome, "symbols": ["Worker.write"]}, vault=self.vault)
        self.assertNotEqual(first["event_id"], second["event_id"])
        state = MODULE.knowledge.load_knowledge(self.project, self.vault)
        self.assertEqual({(entry["scope"], entry["symbol"]) for entry in state["entries"]}, {("module", ""), ("method", "Worker.read"), ("method", "Worker.write")})
        events = [json.loads(line) for line in (self.vault / "AI Memory/events.jsonl").read_text().splitlines()]
        self.assertEqual(len(events), 3)
        self.assertTrue(any("Worker.read" in line for line in events[1]["decisions"]))

    def test_ambiguous_symbols_and_foreign_entity_file_fail_before_history(self):
        invalid = [{**self.outcome, "files": ["script.py", "other.py"], "symbols": ["run"]}, {**self.outcome, "memories": [{"scope": "method", "module": "example", "file": "other.py", "symbol": "run", "summary": "Other method"}]}]
        for outcome in invalid:
            with self.assertRaises(ValueError):
                self.closeout(outcome, vault=self.vault)
        self.assertFalse((self.vault / "AI Memory/events.jsonl").exists())

    def test_ending_keeps_producer_evidence_when_source_changes(self):
        payload = {**self.outcome, "symbols": ["Worker.read"]}
        entries = MODULE.prepare_entries(payload, self.project, capture_sources=True)
        expected_hash = entries[0]["source_hashes"]["script.py"]
        (self.project / "script.py").write_text("value = 2\n")
        self.closeout({**payload, "memories": entries}, vault=self.vault)
        state = MODULE.knowledge.load_knowledge(self.project, self.vault)
        self.assertEqual(state["entries"][0]["source_hashes"]["script.py"], expected_hash)
        recalled = MODULE.knowledge.recall(self.project, self.vault, module="example", files=["script.py"], symbols=["Worker.read"])
        self.assertFalse(recalled["entries"])
        self.assertTrue(recalled["stale"])

    def test_method_supporting_source_change_invalidates_recall(self):
        (self.project / "schema.json").write_text('{"version": 1}')
        payload = {**self.outcome, "files": ["script.py", "schema.json"], "memories": [{"scope": "method", "module": "example", "file": "script.py", "symbol": "Worker.read"}]}
        entries = MODULE.prepare_entries(payload, self.project, capture_sources=True)
        self.assertEqual(set(entries[0]["source_hashes"]), {"script.py", "schema.json"})
        self.closeout({**payload, "memories": entries}, vault=self.vault)
        (self.project / "schema.json").write_text('{"version": 2}')
        recalled = MODULE.knowledge.recall(self.project, self.vault, module="example", files=["script.py"], symbols=["Worker.read"])
        self.assertFalse(recalled["entries"])
        self.assertTrue(recalled["stale"])

    def test_entity_decision_versions_remain_readable_in_history(self):
        for decision in ("Use the original structure", "Use the revised structure"):
            entry = {"scope": "method", "module": "example", "file": "script.py", "symbol": "Worker.read", "decisions": [decision], "risks": ["Preserve existing callers"], "verification": ["Observed method output"], "verification_status": "passed"}
            self.closeout({**self.outcome, "memories": [entry]}, vault=self.vault)
        events = [json.loads(line) for line in (self.vault / "AI Memory/events.jsonl").read_text().splitlines()]
        self.assertEqual(len(events), 2)
        for event, expected in zip(events, ("Use the original structure", "Use the revised structure")):
            history = "\n".join(event["decisions"])
            for evidence in (expected, "Preserve existing callers", "Observed method output", "verification_status: passed"):
                self.assertIn(evidence, history)
        current = MODULE.knowledge.load_knowledge(self.project, self.vault)["entries"][0]
        self.assertEqual(current["decisions"], ["Use the revised structure"])


if __name__ == "__main__":
    unittest.main()

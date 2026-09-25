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
    event = {"event_id": "vault-event-1", "project": fields["project"], "module_changes": [{"module": fields["module"]}], **fields}
    if not events:
        EVENTS_PATH.write_text(json.dumps(event) + "\\n")
        return {"status": "written", "event_id": event["event_id"]}
    return {"status": "duplicate", "event_id": events[0]["event_id"]}
def render_views():
    return {"status": "ready"}
'''


class EndingMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
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
        args = {"selected_model": "gpt-6-astra", "selected_effort": "ultra", "executing_model": "gpt-6-astra", "executing_effort": "ultra", "project_root": self.project,
                "runtime_receipt": {"status": "pass", "turn_completed": True, "effective_pair": "gpt-6-astra|ultra"}}
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

    def test_selected_pair_requires_matching_runtime_evidence(self):
        with self.assertRaisesRegex(ValueError, "selected model and effort"):
            self.closeout(executing_model="gpt-6-luna")
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault):
            with self.assertRaisesRegex(ValueError, "runtime evidence must match"):
                self.closeout(runtime_receipt={"status": "pass", "turn_completed": True, "effective_pair": "gpt-6-luna|max"})

    def test_observable_vault_write_and_duplicate_readback(self):
        with mock.patch.object(MODULE.memory, "_resolve_vault", return_value=self.vault):
            first = self.closeout()
            second = self.closeout()
        self.assertEqual(first["status"], "written")
        self.assertEqual(second["status"], "duplicate")
        self.assertEqual(first["event_id"], "vault-event-1")
        self.assertTrue(first["read_back_verified"])
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


if __name__ == "__main__":
    unittest.main()

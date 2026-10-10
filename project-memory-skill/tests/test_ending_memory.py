import importlib.util
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ARTIFACT_PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT_PROJECT / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root, validate_external_directory


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SUPPORTED_RUNTIME = Path(os.environ.get("PROJECT_MEMORY_TEST_RUNTIME", SCRIPTS.parents[2] / "qin-llm-wiki/qin_llm_wiki/templates/vault/AI Memory/ai_memory.py"))
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
        override = os.environ.get("ENDING_MEMORY_TEST_CACHE")
        cache = validate_external_directory(override, ARTIFACT_PROJECT) if override is not None else resolve_task_artifact_root(ARTIFACT_PROJECT, "ending-memory-tests", create=True)
        cache.mkdir(parents=True, exist_ok=True)
        if override is None:
            self.addCleanup(cache.rmdir)
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
        args = {"project_root": self.project, "vault": self.vault}
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

    def test_sparse_memory_update_records_the_complete_merged_entry(self):
        scope = {"scope": "module", "module": "example"}
        entry = {**scope, "summary": "Keep the original restoration workaround", "reason": "The user corrected repeated lost settings", "result": "The restoration workaround was verified", "decisions": ["Preserve the user correction"], "risks": ["Unresolved: verify restoration on another machine"], "status": "retired"}
        self.closeout({**self.outcome, "memories": [entry]}, vault=self.vault)
        updated = {**self.outcome, "verification_status": "not-run", "verification": [], "memories": [{**scope, "summary": "Keep the revised restoration contract pending verification"}]}
        result = self.closeout(updated, vault=self.vault)
        current = MODULE.knowledge.load_knowledge(self.project, self.vault)["entries"][0]
        for field in ("reason", "result", "decisions", "risks", "status"):
            self.assertEqual(current[field], entry[field])
        self.assertEqual(current["verification_status"], "not-run")
        events = json.loads((self.vault / "AI Memory/events.jsonl").read_text().splitlines()[-1])
        self.assertEqual(events["event_id"], result["event_id"])
        history = "\n".join(events["decisions"])
        for fact in (entry["reason"], entry["result"], *entry["decisions"], *entry["risks"], "status: retired", "verification_status: not-run"):
            self.assertIn(fact, history)

    def test_explicit_empty_source_evidence_is_not_recaptured(self):
        entries = MODULE.prepare_entries({**self.outcome, "symbols": ["Worker.read"], "source_hashes": {}}, self.project, capture_sources=True)
        self.assertEqual(entries[0]["source_hashes"], {})

    def test_noop_checks_due_then_consolidation_only_preserves_entry_proof(self):
        first = self.closeout()
        before = MODULE.knowledge.load_knowledge(self.project, self.vault)
        self.assertTrue(first["current_memory"]["maintenance_due"])
        pending = self.closeout({})
        self.assertEqual(pending["reason"], "project_synthesis_due")
        self.assertFalse(pending["written"])
        completed = self.closeout({"consolidation": {"summary": "The original verified result has a bounded restoration contract"}})
        self.assertFalse(completed["current_memory"]["maintenance_due"])
        after = MODULE.knowledge.load_knowledge(self.project, self.vault)
        self.assertEqual(after["entries"], before["entries"])
        self.assertEqual(after["synthesis"]["entry_ids"], [before["entries"][0]["id"]])
        event = json.loads((self.vault / "AI Memory/events.jsonl").read_text().splitlines()[-1])
        self.assertEqual((event["event_type"], event["verification_status"], event["files"], event["verification"]), ("documentation", "not-run", [], []))
        self.assertIn("Project consolidation scope: " + before["entries"][0]["id"], event["decisions"])
        snapshot = {path: path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        skipped = self.closeout({})
        self.assertEqual(skipped["status"], "skipped")
        self.assertEqual({path: path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}, snapshot)

    def test_stale_synthesis_preimage_refuses_history_and_index_writes(self):
        self.closeout()
        index = self.vault / "Projects/ExampleProject/Memory.json"
        expected = hashlib.sha256(index.read_bytes()).hexdigest()
        self.closeout({**self.outcome, "summary": "Preserve the concurrent revised result"})
        snapshot = {path: path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        result = self.closeout({"expected_index_sha256": expected, "consolidation": {"summary": "This obsolete draft must not overwrite current knowledge"}})
        self.assertEqual(result["reason"], "project_memory_index_changed")
        self.assertFalse(result["written"])
        self.assertEqual({path: path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}, snapshot)
        fresh = hashlib.sha256(index.read_bytes()).hexdigest()
        saved = self.closeout({"expected_index_sha256": fresh, "consolidation": {"summary": "The concurrent revised result remains bounded to its established scope"}})
        self.assertFalse(saved["current_memory"]["maintenance_due"])

    def test_consolidation_refuses_stale_method_inputs(self):
        entries = MODULE.prepare_entries({**self.outcome, "symbols": ["Worker.read"]}, self.project, capture_sources=True)
        self.closeout({**self.outcome, "memories": entries})
        identifier = entries[0]["id"]
        (self.project / "script.py").write_text("value = 2\n")
        original_events = (self.vault / "AI Memory/events.jsonl").read_bytes()
        result = self.closeout({"consolidation": {"summary": "The old method claim cannot become new proof", "entry_ids": [identifier]}})
        self.assertEqual(result["reason"], "synthesis_contributor_not_eligible")
        self.assertFalse(result["written"])
        self.assertEqual((self.vault / "AI Memory/events.jsonl").read_bytes(), original_events)

    @unittest.skipUnless(SUPPORTED_RUNTIME.is_file(), "set PROJECT_MEMORY_TEST_RUNTIME to the supported qin-llm-wiki writer")
    def test_supported_vault_runtime_saves_and_recalls_corrections_and_pending_work(self):
        runtime_path = self.vault / "AI Memory/ai_memory.py"
        runtime_path.write_bytes(SUPPORTED_RUNTIME.read_bytes())
        classifier = SUPPORTED_RUNTIME.with_name("auto_classify.py")
        if classifier.is_file():
            runtime_path.with_name("auto_classify.py").write_bytes(classifier.read_bytes())
        scope = {"scope": "module", "module": "example"}
        established = {**scope, "summary": "Preserve the verified restoration workaround", "reason": "The user struggled with repeated lost settings", "result": "The settings restore works within the verified environment", "decisions": ["User correction: preserve the established settings"], "risks": ["Next step: verify the recovered settings", "Unresolved: restore on another machine"]}
        original = MODULE.prepare_entries({**self.outcome, "memories": [established]}, self.project, capture_sources=True)
        first = self.closeout({**self.outcome, "memories": original, "consolidation": {"summary": "The original restoration workaround was verified"}}, vault=self.vault)
        runtime = MODULE._vault_runtime(self.vault)
        original_event = next(event for event in runtime._read_events(runtime.EVENTS_PATH) if event["event_id"] == first["event_id"])
        updated = {"module": "example", "summary": "The revised restoration contract needs verification", "reason": "Record the new explanation", "result": "The new explanation is awaiting verification", "files": ["script.py"], "memories": [{**scope, "summary": "Preserve restoration continuity pending a fresh check"}]}
        second = self.closeout(updated, vault=self.vault)
        recalled = MODULE.knowledge.recall(self.project, self.vault, module="example")
        self.assertEqual(recalled["status"], "ok")
        current = recalled["entries"][0]
        for field in ("reason", "result", "decisions", "risks"):
            self.assertEqual(current[field], established[field])
        self.assertEqual(current["verification_status"], "not-run")
        self.assertEqual(current["source_hashes"], {})
        self.assertEqual(current["freshness"], "unverified")
        self.assertNotIn("project_synthesis", recalled)
        events = runtime._read_events(runtime.EVENTS_PATH)
        self.assertEqual(len(events), 2)
        self.assertEqual(next(event for event in events if event["event_id"] == first["event_id"]), original_event)
        self.assertEqual(original_event["verification_status"], "passed")
        self.assertTrue(any("Project consolidation:" in decision for decision in original_event["decisions"]))
        saved = next(event for event in events if event["event_id"] == second["event_id"])
        for fact in (established["reason"], established["result"], *established["decisions"], *established["risks"], "verification_status: not-run"):
            self.assertIn(fact, "\n".join(saved["decisions"]))
        self.assertTrue(first["read_back_verified"] and second["read_back_verified"])
        pending = self.closeout({})
        self.assertEqual(pending["reason"], "project_synthesis_due")
        before_refresh = MODULE.knowledge.load_knowledge(self.project, self.vault)["entries"]
        synthesis = self.closeout({"consolidation": {"summary": "Restoration retains the original workaround and correction while another-machine verification remains pending"}})
        navigation = MODULE.knowledge.recall(self.project, self.vault, module="example")["project_synthesis"]
        self.assertFalse(navigation["eligible_current_context"])
        self.assertEqual(navigation["context_role"], "navigation_only")
        self.assertFalse(synthesis["current_memory"]["maintenance_due"])
        self.assertEqual(MODULE.knowledge.load_knowledge(self.project, self.vault)["entries"], before_refresh)


if __name__ == "__main__":
    unittest.main()

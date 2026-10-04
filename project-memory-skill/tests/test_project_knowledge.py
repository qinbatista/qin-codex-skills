import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "project-memory-skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "code-skill" / "scripts"))
import project_knowledge as knowledge
from hidden_process import hidden_process_options


class ProjectKnowledgeTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / "Cache"
        cache.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="temp-project-knowledge-", dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "source" / "ExampleProject"
        self.project.mkdir(parents=True)
        self.vault = self.root / "vault"
        (self.vault / "Projects").mkdir(parents=True)
        self.now = datetime(2026, 9, 30, tzinfo=timezone.utc)
        for relative in ("src/first.py", "src/second.py", "docs/contract.md"):
            path = self.project / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("def run():\n    return 1\n", encoding="utf-8")

    def method(self, file="src/first.py", symbol="Worker.run", module="engine", summary="Keep the stable execution contract", **changes):
        value = {"scope": "method", "module": module, "file": file, "symbol": symbol, "summary": summary, "source_hashes": {file: hashlib.sha256((self.project / file).read_bytes()).hexdigest()}}
        return {**value, **changes}

    def write(self, entries, event="event-1", **kwargs):
        return knowledge.apply_entries(self.project, self.vault, entries, event_id=event, now=self.now, **kwargs)

    def read(self, **kwargs):
        return knowledge.recall(self.project, self.vault, **kwargs)

    def test_exact_method_filters_intersect_and_keep_same_symbols_in_other_files(self):
        first = self.method()
        second = self.method(file="src/second.py", summary="Use the separate execution contract")
        unrelated = self.method(file="src/first.py", module="different", summary="Preserve another module contract")
        result = self.write([first, second, unrelated])
        self.assertTrue(result["read_back_verified"])
        found = self.read(module="engine", files=["src/second.py"], symbols=["Worker.run"], query="separate")
        self.assertEqual(len(found["entries"]), 1)
        self.assertEqual(found["entries"][0]["file"], "src/second.py")
        self.assertEqual(found["entries"][0]["freshness"], "current")
        self.assertEqual(self.read(module="engine", files=["src/first.py"], symbols=["Worker.run"], query="separate")["entries"], [])
        self.assertEqual(len({entry["id"] for entry in knowledge.load_knowledge(self.project, self.vault)["entries"]}), 3)

    def test_ambiguous_method_query_skips_without_loose_fallback(self):
        self.write([self.method(), self.method(file="src/second.py")])
        for filters in ({"symbols": ["Worker.run"]}, {"module": "engine", "symbols": ["Worker.run"]}, {"module": "engine", "files": ["src/first.py", "src/second.py"], "symbols": ["Worker.run"]}):
            result = self.read(**filters)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["entries"], [])

    def test_upsert_preserves_other_scopes_and_has_no_file_explosion(self):
        self.write([self.method(), self.method(file="src/second.py"), {"scope": "module", "module": "other", "summary": "Preserve the unrelated module"}])
        self.write([self.method(summary="Use the updated execution contract")], event="event-2")
        state = knowledge.load_knowledge(self.project, self.vault)
        self.assertEqual(len(state["entries"]), 3)
        self.assertEqual(self.read(module="other")["entries"][0]["summary"], "Preserve the unrelated module")
        self.assertEqual(sorted(path.name for path in (self.vault / "Projects" / "ExampleProject").iterdir()), [".memory.lock", "Knowledge.md", "Memory.json"])

    def test_repeated_fact_is_idempotent_and_conflicting_duplicate_is_refused(self):
        self.write([self.method(), self.method()])
        index = self.vault / "Projects" / "ExampleProject" / "Memory.json"
        previous = index.read_bytes()
        result = self.write([self.method()], event="event-new-but-same-fact")
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(index.read_bytes(), previous)
        with self.assertRaisesRegex(ValueError, "conflicting"):
            self.write([self.method(), self.method(summary="Different contract")])
        self.assertEqual(index.read_bytes(), previous)

    def test_same_named_unregistered_project_cannot_read_or_overwrite(self):
        self.write([self.method()])
        other = self.root / "clone" / self.project.name
        other.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "different exact project"):
            knowledge.load_knowledge(other, self.vault)
        self.assertEqual(knowledge.recall(other, self.vault)["reason"], "exact_project_mismatch")
        with self.assertRaisesRegex(ValueError, "different exact project"):
            knowledge.apply_entries(other, self.vault, [{"scope": "project", "summary": "Another project's facts"}], event_id="other-event")
        self.assertEqual(self.read(module="engine")["entries"][0]["event_id"], "event-1")

    def test_registered_project_aliases_reuse_the_same_owner(self):
        other = self.root / "renamed-project"
        other.mkdir()
        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "Registered"), (other, "Registered"))):
            self.write([{"scope": "project", "summary": "Retain shared registered owner facts"}])
            result = knowledge.recall(other, self.vault)
        self.assertEqual(result["entries"][0]["summary"], "Retain shared registered owner facts")

    def alias_index(self):
        self.write([self.method(), {"scope": "module", "module": "unrelated", "summary": "Preserve unrelated project knowledge"}], consolidation={"summary": "Retain the complete project synthesis"})
        index = self.vault / "Projects/ExampleProject/Memory.json"
        state = json.loads(index.read_text(encoding="utf-8"))
        state["project"]["key"] = "exampleproject-0123456789"
        index.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.vault / "AI Memory").mkdir()
        (self.vault / "AI Memory/events.jsonl").write_bytes(b"immutable history\r\n")
        return index, state

    def alias_arguments(self, index, state):
        return {"expected_owner": state["project"]["owner"], "expected_project_key": state["project"]["key"], "expected_index_sha256": hashlib.sha256(index.read_bytes()).hexdigest()}

    def test_explicit_alias_preserves_primary_facts_history_view_and_lock_order(self):
        index, before = self.alias_index()
        preserved = {path: path.read_bytes() for path in (index.with_name("Knowledge.md"), self.vault / "AI Memory/events.jsonl")}
        acquired = []
        real_lock = knowledge.memory._acquire_file_lock

        def acquire(handle):
            acquired.append(Path(handle.name).relative_to(self.vault).as_posix())
            real_lock(handle)

        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "ExampleProject"),)), mock.patch.object(knowledge.memory, "_acquire_file_lock", side_effect=acquire):
            self.assertEqual(self.read()["reason"], "exact_project_mismatch")
            result = knowledge.register_alias(self.project, self.vault, **self.alias_arguments(index, before))
            after = knowledge.load_knowledge(self.project, self.vault)
            self.assertEqual(self.read(module="engine", files=["src/first.py"], symbols=["Worker.run"])["status"], "ok")
        self.assertEqual(result["status"], "written")
        self.assertTrue(result["read_back_verified"])
        self.assertEqual(after["project"]["aliases"], [knowledge.memory._project_key_for_root(self.project)])
        del after["project"]["aliases"]
        self.assertEqual(after, before)
        self.assertEqual(acquired, ["AI Memory/.ending.lock", "Projects/ExampleProject/.memory.lock"])
        self.assertTrue(all(path.read_bytes() == content for path, content in preserved.items()))

    def test_alias_repeat_is_byte_preserving_and_stale_cas_is_rejected(self):
        index, state = self.alias_index()
        original_arguments = self.alias_arguments(index, state)
        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "ExampleProject"),)):
            knowledge.register_alias(self.project, self.vault, **original_arguments)
            saved = index.read_bytes()
            with self.assertRaisesRegex(ValueError, "changed"):
                knowledge.register_alias(self.project, self.vault, **original_arguments)
            result = knowledge.register_alias(self.project, self.vault, **self.alias_arguments(index, state))
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(index.read_bytes(), saved)

    def test_alias_rejects_wrong_owner_key_sha_and_unregistered_same_name_clone(self):
        index, state = self.alias_index()
        original = index.read_bytes()
        arguments = self.alias_arguments(index, state)
        clone = self.root / "unregistered" / self.project.name
        clone.mkdir(parents=True)
        variants = [{**arguments, "expected_owner": "AnotherProject"}, {**arguments, "expected_project_key": "exampleproject-abcdefabcd"}, {**arguments, "expected_index_sha256": "a" * 64}]
        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "ExampleProject"),)):
            for changed in variants:
                with self.subTest(arguments=changed), self.assertRaises(ValueError):
                    knowledge.register_alias(self.project, self.vault, **changed)
                self.assertEqual(index.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, "registered"):
                knowledge.register_alias(clone, self.vault, **arguments)
            state["project"]["aliases"] = [knowledge.memory._project_key_for_root(clone)]
            index.write_text(json.dumps(state), encoding="utf-8")
            self.assertEqual(knowledge.recall(clone, self.vault)["reason"], "exact_project_mismatch")
        self.assertEqual(json.loads(index.read_text())["project"]["key"], arguments["expected_project_key"])

    def test_alias_validates_all_entries_and_bounded_portable_aliases_before_write(self):
        index, original = self.alias_index()
        invalid_aliases = [None, [None], ["../foreign"], ["C:\\foreign"], ["exampleproject-1234567890"] * 2, [f"exampleproject-{number:010x}" for number in range(knowledge.MAX_PROJECT_ALIASES + 1)]]
        states = []
        for aliases in invalid_aliases:
            value = json.loads(json.dumps(original))
            value["project"]["aliases"] = aliases
            states.append(value)
        malformed = json.loads(json.dumps(original))
        malformed["entries"][0]["event_id"] = ""
        states.append(malformed)
        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "ExampleProject"),)):
            for value in states:
                with self.subTest(state=value):
                    index.write_text(json.dumps(value), encoding="utf-8")
                    saved = index.read_bytes()
                    with self.assertRaises(ValueError):
                        knowledge.register_alias(self.project, self.vault, **self.alias_arguments(index, original))
                    self.assertEqual(index.read_bytes(), saved)

    def test_alias_rejects_index_and_lock_symlinks_without_touching_target(self):
        index, state = self.alias_index()
        target = self.root / "external-index.json"
        target.write_bytes(index.read_bytes())
        target_bytes = target.read_bytes()
        try:
            probe = self.root / "link-probe"
            probe.symlink_to(target)
            probe.unlink()
        except OSError as error:
            self.skipTest(f"Host cannot create symlink fixture: {error}")
        arguments = self.alias_arguments(index, state)
        with mock.patch.object(knowledge.memory, "_registered_project_owner_paths", return_value=((self.project, "ExampleProject"),)):
            for path in (index, self.vault / "AI Memory/.ending.lock"):
                previous = path.read_bytes() if path.exists() else None
                path.unlink(missing_ok=True)
                path.symlink_to(target)
                with self.subTest(path=path), self.assertRaises(ValueError):
                    knowledge.register_alias(self.project, self.vault, **arguments)
                self.assertEqual(target.read_bytes(), target_bytes)
                path.unlink()
                if previous is not None:
                    path.write_bytes(previous)

    def test_wrong_clone_identity_rejects_before_inspecting_its_symlink_sources(self):
        self.write([self.method()])
        clone = self.root / "clone" / self.project.name
        clone.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (clone / "src").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create symlink fixture: {error}")
        self.assertEqual(knowledge.recall(clone, self.vault)["reason"], "exact_project_mismatch")

    def test_alias_cli_uses_actual_registered_home_root_and_reads_back(self):
        home = self.root / "registered-home"
        project = home / "Documents/YofaGames/YoFaAssets"
        shutil.copytree(self.project, project)
        with mock.patch.object(knowledge.memory.Path, "home", return_value=home):
            self.assertEqual(knowledge.memory._registered_owner(project), "YoFaAssets")
            knowledge.apply_entries(project, self.vault, [self.method()], event_id="same-project-proof", now=self.now)
        index = self.vault / "Projects/YoFaAssets/Memory.json"
        state = json.loads(index.read_text())
        state["project"]["key"] = "yofaassets-0123456789"
        index.write_text(json.dumps(state), encoding="utf-8")
        (self.vault / "AI Memory").mkdir()
        arguments = self.alias_arguments(index, state)
        command = [sys.executable, "-B", str(SCRIPTS / "project_knowledge.py"), "register-alias", "--project-root", str(project), "--vault", str(self.vault)]
        for key, value in arguments.items():
            command.extend(["--" + key.replace("_", "-"), value])
        environment = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False, env=environment, **hidden_process_options())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["read_back_verified"])
        with mock.patch.object(knowledge.memory.Path, "home", return_value=home):
            self.assertEqual(knowledge.recall(project, self.vault, module="engine", files=["src/first.py"], symbols=["Worker.run"])["status"], "ok")

    def test_explicit_relationships_remain_pointers_and_context_stays_local(self):
        relation = {"project": "OtherProject", "module": "shared-api", "file": "api.py", "symbol": "Client.send", "relation": "uses", "reason": "Consumes the documented API"}
        self.write([{"scope": "project", "summary": "Project ownership remains local"}, {"scope": "module", "module": "engine", "summary": "The engine owns execution"}, self.method(relations=[relation, relation])])
        foreign = self.vault / "Projects" / "OtherProject"
        foreign.mkdir()
        (foreign / "Memory.json").write_text("invalid external content must never load", encoding="utf-8")
        result = self.read(module="engine", files=["src/first.py"], symbols=["Worker.run"])
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual({entry["scope"] for entry in result["parent_context"]}, {"project", "module"})
        self.assertEqual(len(result["references"]), 1)
        self.assertFalse(result["references"][0]["context_loaded"])
        self.assertTrue(result["references"][0]["cross_project"])
        target_id = knowledge.normalize_entries(self.project, [{"scope": "method", "module": "shared-api", "file": "api.py", "symbol": "Client.send", "summary": "The external API contract"}])[0]["id"]
        document = (self.vault / "Projects" / "ExampleProject" / "Knowledge.md").read_text(encoding="utf-8")
        self.assertIn(f"[[Projects/OtherProject/Knowledge#^memory-{target_id}]]", document)
        self.assertIn("^memory-" + result["entries"][0]["id"], document)

    def test_missing_index_does_not_promote_unindexed_notes(self):
        owner = self.vault / "Projects" / "ExampleProject"
        owner.mkdir()
        (owner / "Knowledge.md").write_text("Unindexed legacy prose", encoding="utf-8")
        self.assertEqual(self.read()["reason"], "current_index_missing")

    def test_overloaded_and_generic_signatures_remain_distinct(self):
        symbols = ["Namespace.Worker.Run(int)", "Namespace.Worker.Run(string)", "Namespace.Worker.Map<T>(T)", "Namespace.Worker.Run(int[])", "Worker.run(value: int | str)"]
        self.write([self.method(symbol=symbol) for symbol in symbols])
        for symbol in symbols:
            result = self.read(module="engine", files=["src/first.py"], symbols=[symbol])
            self.assertEqual([entry["symbol"] for entry in result["entries"]], [symbol])

    def test_unreadable_selected_source_is_reported_without_effective_content(self):
        self.write([self.method()])
        real_open = Path.open

        def reject_source(path, *args, **kwargs):
            if path == self.project / "src/first.py":
                raise PermissionError("isolated source permission failure")
            return real_open(path, *args, **kwargs)

        with mock.patch.object(Path, "open", reject_source):
            result = self.read(module="engine")
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["unverified"][0]["reason"], "source_unreadable")

    def test_stale_or_retired_entries_do_not_consume_current_result_limit(self):
        retired = [self.method(symbol=f"Worker.old{number}", status="retired") for number in range(7)]
        self.write([*retired, self.method(symbol="Worker.usable")])
        result = self.read(module="engine", limit=1)
        self.assertEqual([entry["symbol"] for entry in result["entries"]], ["Worker.usable"])
        self.assertEqual(len(result["retired"]), 1)

    def test_changed_and_missing_sources_are_separated_from_effective_facts(self):
        self.write([self.method(), self.method(file="src/second.py")])
        (self.project / "src/first.py").write_text("changed bytes", encoding="utf-8")
        (self.project / "src/second.py").unlink()
        result = self.read(module="engine")
        self.assertEqual(result["entries"], [])
        self.assertEqual({entry["reason"] for entry in result["stale"]}, {"source_changed", "source_missing"})
        self.assertTrue(all("summary" not in entry for entry in result["stale"]))

    def test_supporting_source_change_invalidates_exact_method(self):
        entry = self.method()
        entry["source_hashes"]["docs/contract.md"] = hashlib.sha256((self.project / "docs/contract.md").read_bytes()).hexdigest()
        self.write([entry])
        (self.project / "docs/contract.md").write_text("The supporting contract changed", encoding="utf-8")
        self.assertEqual(self.read(module="engine")["stale"][0]["reason"], "source_changed")

    def test_unverified_method_is_not_current_but_module_reports_limitation(self):
        self.write([self.method(source_hashes={}), {"scope": "module", "module": "overview", "summary": "Maintain the module overview"}])
        result = self.read(module="engine")
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["unverified"][0]["reason"], "source_evidence_absent")
        module = self.read(module="overview")
        self.assertEqual(module["entries"][0]["freshness"], "unverified")
        self.assertTrue(module["limitations"])

    def test_method_rename_can_retire_old_identity_and_free_function_is_exact(self):
        self.write([self.method(symbol="run")])
        self.write([self.method(symbol="run", status="retired"), self.method(symbol="execute")], event="event-rename")
        old = self.read(module="engine", files=["src/first.py"], symbols=["run"])
        self.assertEqual(old["entries"], [])
        self.assertEqual(len(old["retired"]), 1)
        new = self.read(module="engine", files=["src/first.py"], symbols=["execute"])
        self.assertEqual(new["entries"][0]["symbol"], "execute")

    def test_invalid_paths_links_and_incomplete_scope_fail_before_mutation(self):
        cases = [self.method(file="src/first.py", source_hashes={"../secret": "a" * 64}), {**self.method(), "file": "../secret"}, {**self.method(), "symbol": ""}, {**self.method(), "module": ""}, self.method(relations=[{"project": "../Other", "module": "other", "relation": "uses", "reason": "Invalid owner"}]), self.method(relations=[{"project": "Other", "module": "other", "file": "../secret", "relation": "uses", "reason": "Invalid path"}]), self.method(summary="x" * 601)]
        for entry in cases:
            with self.assertRaises(ValueError):
                self.write([entry])
        self.assertFalse((self.vault / "Projects" / "ExampleProject").exists())

    def test_symlink_boundaries_reject_project_escape_and_vault_alias(self):
        outside = self.root / "outside"
        outside.mkdir()
        target = self.project / "external"
        try:
            target.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create symlink fixture: {error}")
        with self.assertRaisesRegex(ValueError, "escapes project_root"):
            knowledge.normalize_entries(self.project, [{"scope": "document", "module": "docs", "file": "external/file.md", "summary": "Outside source"}])
        (self.vault / "Projects" / "ExampleProject").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.write([self.method()])
        self.assertEqual(list(outside.iterdir()), [])

    def test_due_and_consolidation_reset_without_unbounded_history(self):
        for number in range(knowledge.MAINTENANCE_WRITES):
            result = self.write([self.method(summary=f"Preserve contract revision {number}")], event=f"event-{number}")
        self.assertTrue(result["maintenance_due"])
        relation = {"project": "SupportingProject", "module": "protocol", "relation": "uses", "reason": "Keep the protocol dependency explicit"}
        consolidated = self.write([], event="consolidated", consolidation={"summary": "The stable engine contract is centralized", "relations": [relation]})
        self.assertFalse(consolidated["maintenance_due"])
        state = knowledge.load_knowledge(self.project, self.vault)
        self.assertEqual(state["maintenance"]["writes_since_consolidation"], 0)
        self.assertEqual(len(state["entries"]), 1)
        self.assertEqual(state["synthesis"]["summary"], "The stable engine contract is centralized")
        document = (self.vault / "Projects" / "ExampleProject" / "Knowledge.md").read_text(encoding="utf-8")
        self.assertIn("[[Projects/SupportingProject/Knowledge#^memory-", document)
        self.assertEqual(self.read(module="engine")["references"][0]["project"], "SupportingProject")
        aged = knowledge.apply_entries(self.project, self.vault, [], event_id="age-check", now=self.now + timedelta(days=30))
        self.assertTrue(aged["maintenance_due"])

    def test_manual_content_preserved_and_previous_generated_section_is_history(self):
        owner = self.vault / "Projects" / "ExampleProject"
        owner.mkdir()
        document = owner / "Knowledge.md"
        document.write_text("# Manual project notes\nKeep my hand-written instructions.\n" + knowledge.LEGACY_START + "\nOld loose module summary\n" + knowledge.LEGACY_END + "\n", encoding="utf-8")
        self.write([self.method()])
        text = document.read_text(encoding="utf-8")
        self.assertIn("Keep my hand-written instructions.", text)
        self.assertIn("Migration history only", text)
        self.assertIn("Old loose module summary", text)
        self.assertNotIn(knowledge.LEGACY_START, text)
        self.assertNotIn("Old loose module summary", json.dumps(self.read()))

    def test_failed_projection_keeps_index_and_retry_repairs_view(self):
        real_atomic = knowledge._atomic_text

        def fail_view(path, value, vault):
            if path.name == "Knowledge.md":
                raise OSError("isolated view failure")
            return real_atomic(path, value, vault)

        with mock.patch.object(knowledge, "_atomic_text", side_effect=fail_view):
            result = self.write([self.method()])
        self.assertEqual(result["status"], "pending")
        self.assertTrue(result["index_read_back_verified"])
        self.assertFalse(result["read_back_verified"])
        self.assertEqual(len(self.read(module="engine")["entries"]), 1)
        repaired = self.write([self.method()])
        self.assertEqual(repaired["status"], "duplicate")
        self.assertTrue(repaired["read_back_verified"])

    def test_concurrent_process_updates_keep_both_module_entries(self):
        program = "import sys; sys.path.insert(0, sys.argv[1]); import project_knowledge as knowledge; result=knowledge.apply_entries(sys.argv[2],sys.argv[3],[{'scope':'module','module':sys.argv[4],'summary':'Preserve the module contract'}],event_id=sys.argv[4]); print(result['status'])"
        processes = []
        for module in ("alpha", "beta"):
            processes.append(subprocess.Popen([sys.executable, "-c", program, str(SCRIPTS), str(self.project), str(self.vault), module], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", **hidden_process_options()))
        for process in processes:
            output, error = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, error)
            self.assertIn("written", output)
        self.assertEqual({entry["module"] for entry in knowledge.load_knowledge(self.project, self.vault)["entries"]}, {"alpha", "beta"})

    def test_cli_returns_exact_bounded_current_context(self):
        self.write([self.method()])
        result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "project_knowledge.py"), "recall", "--project-root", str(self.project), "--vault", str(self.vault), "--module", "engine", "--file", "src/first.py", "--symbol", "Worker.run"], capture_output=True, text=True, encoding="utf-8", timeout=20, check=True, **hidden_process_options())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["entries"][0]["symbol"], "Worker.run")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_model_memory.py"
SPEC = importlib.util.spec_from_file_location("obsidian_model_memory", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class ObsidianModelMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.local_store = self.root / "model-routing-memory" / "events.jsonl"
        self.local_store_patcher = mock.patch.dict(os.environ, {"CODEX_MODEL_ROUTING_MEMORY": str(self.local_store)})
        self.local_store_patcher.start()
        self.path_home_patcher = mock.patch.object(module.Path, "home", lambda: self.home)
        self.path_home_patcher.start()
        self.project = self.home / "Documents" / "YofaGames" / "ThisIsMyOregon" / "ExampleProject"
        (self.project / "src").mkdir(parents=True)
        (self.project / "src" / "example.py").write_text("result = 1\n", encoding="utf-8")
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "Projects" / "ThisIsMyOregon").mkdir(parents=True)
        self.broad_page = self.vault / "Projects" / "ThisIsMyOregon" / "Model Switch.md"
        self.broad_page.write_text("# Model Switch\n", encoding="utf-8")
        self.broad_index = self.vault / "Projects" / "ThisIsMyOregon" / "index.md"
        self.broad_index.write_text("# ThisIsMyOregon\n", encoding="utf-8")
        self.receipt = self.root / "receipt.json"

    def tearDown(self):
        self.path_home_patcher.stop()
        self.local_store_patcher.stop()
        self.temporary.cleanup()

    def write_receipt(self, pair, path=None, context=None):
        target = path or self.receipt
        receipt = {"status": "pass", "result_published": True, "turn_completed": True, "model_match": True, "effort_match": True, "requested_pair": pair, "executed_pair": pair, "priority_attempt_pair": pair, "workload_prompt_sha256": "1" * 64, "tokens": {"total_tokens": 101}, "process_elapsed_ms": 1001}
        if context is not None:
            receipt.update({"node_type": "locked-route-node", "node_role": "result-producer", "model_learning_context": context, "route_attempts": [{"status": "pass", "executed_pair": pair, "model_match": True, "effort_match": True}]})
        target.write_text(json.dumps(receipt), encoding="utf-8")
        return target

    def quality_record(self, pair, *, status="pass", workload="1", tokens=100, elapsed=1000):
        return {
            "pair": pair,
            "receipt_status": "pass",
            "turn_completed": True,
            "model_match": True,
            "effort_match": True,
            "real_status": status,
            "failure_class": "none" if status == "pass" else "correctness",
            "workload_prompt_sha256": workload * 64,
            "total_tokens": tokens,
            "process_ms": elapsed,
        }

    def write_local_history(self, records, prefix="history"):
        self.local_store.parent.mkdir(parents=True, exist_ok=True)
        self.local_store.write_text(
            "".join(
                json.dumps({"local_model_memory_schema": 1, "event": "model-result", "event_id": f"{prefix}-{index}", "record": record}) + "\n"
                for index, record in enumerate(records)
            ),
            encoding="utf-8",
        )

    def active(self, records):
        shared, pairs = module.load_shared_ladder()
        query = {"task_type": "code", "complexity": "easy"}
        return module._active_recommendation(shared, pairs, query, records), pairs

    def record(self, recorded_at=datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)):
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault)
        self.write_receipt(recommendation["attempt_pair"])
        return module.record_model_result(self.project, "code", "example-module", self.receipt, "pass", "none", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault, recorded_at=recorded_at)

    def test_write_is_one_broad_page_with_one_structured_record(self):
        written = self.record()
        page = self.vault / written["obsidian_note"]
        text = page.read_text(encoding="utf-8")
        self.assertEqual(written["status"], "written")
        self.assertEqual(text.count("<!-- model-experience: "), 1)
        self.assertIn("## Normal Script Update", text)
        self.assertFalse(any(self.vault.rglob("ModelExperience/*.md")))
        self.assertFalse(any(self.vault.rglob(".model-experience.lock")))

    def test_receipt_replay_is_byte_idempotent(self):
        first = self.record()
        page = self.vault / first["obsidian_note"]
        before = page.read_bytes()
        replay = self.record(datetime(2026, 7, 13, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(replay["status"], "duplicate")
        self.assertEqual(page.read_bytes(), before)

    def test_sequential_path_backed_writes_and_stress_stay_on_one_page(self):
        first = self.record()
        page = self.vault / first["obsidian_note"]
        for index in range(1, 100):
            receipt = self.root / f"receipt-{index}.json"
            recommendation = module.recommend_model(self.project, "code", "example-module", file_value=Path("src") / f"example-{index}.py", symbol=f"Example.run{index}", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Sequential Path-backed write.", vault=self.vault)
            receipt.write_text(json.dumps({"status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "requested_pair": recommendation["attempt_pair"], "executed_pair": recommendation["attempt_pair"], "priority_attempt_pair": recommendation["attempt_pair"], "workload_prompt_sha256": f"{index:064x}", "tokens": {"total_tokens": index}, "process_elapsed_ms": index}), encoding="utf-8")
            written = module.record_model_result(self.project, "code", "example-module", receipt, "pass", "none", file_value=Path("src") / f"example-{index}.py", symbol=f"Example.run{index}", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Sequential Path-backed write.", vault=self.vault, recorded_at=datetime(2026, 7, 13, 12, 0, index % 60, tzinfo=timezone.utc))
            self.assertEqual(written["status"], "written")
        self.assertEqual(page.read_text(encoding="utf-8").count("<!-- model-experience: "), 100)
        self.assertEqual(len(list(self.vault.rglob("*.md"))), 2)

    def test_reader_scopes_records_from_its_single_page(self):
        self.record()
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault)
        self.assertEqual(recommendation["matched_records"], 1)
        self.assertEqual(recommendation["specificity"], "symbol")
        self.assertEqual(recommendation["local_record_count"], 1)
        self.assertEqual(recommendation["obsidian_record_count"], 1)
        self.assertEqual(recommendation["merged_record_count"], 1)
        self.assertEqual(recommendation["selection_basis"], "local_and_obsidian")

    def test_local_first_write_survives_vault_outage_and_reconciles_later(self):
        unavailable_vault = self.root / "unavailable-vault"
        recommendation = module.recommend_model(self.project, "code", "offline-routing", file_value="src/example.py", symbol="Example.offline", code_kind="python", operation="edit", modality="text", complexity_score=35, risk="low", ambiguity="low", task_summary="Record offline model routing result.", vault=unavailable_vault)
        self.write_receipt(recommendation["attempt_pair"])
        written = module.record_model_result(self.project, "code", "offline-routing", self.receipt, "pass", "none", file_value="src/example.py", symbol="Example.offline", code_kind="python", operation="edit", modality="text", complexity_score=35, risk="low", ambiguity="low", task_summary="Record offline model routing result.", vault=unavailable_vault, outcome_reason="Focused offline verification passed.", verification_count=1)
        self.assertTrue(written["local"]["written"])
        self.assertEqual(written["obsidian"]["status"], "pending")
        self.assertEqual(written["pending_projection_count"], 1)
        self.assertEqual(len(module._read_local_records()), 1)
        reconciled = module.reconcile_local_model_history(self.project, vault=self.vault)
        self.assertEqual(reconciled["projected"], 1)
        self.assertEqual(reconciled["pending"], 0)
        projected = module._read_project_records(self.broad_page)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]["event_id"], written["event_id"])
        self.assertEqual(projected[0]["outcome_reason"], "Focused offline verification passed.")

    def test_failure_then_stronger_pass_records_recovery_route_and_reasons(self):
        context = {"file_value": "src/example.py", "symbol": "Example.recover", "code_kind": "python", "operation": "feature", "modality": "text", "complexity_score": 35, "risk": "medium", "ambiguity": "low", "task_summary": "Recover a failed model routing task.", "vault": self.vault}
        first = module.recommend_model(self.project, "code", "recovery-routing", **context)
        self.write_receipt(first["attempt_pair"])
        failed = module.record_model_result(self.project, "code", "recovery-routing", self.receipt, "fail", "correctness", outcome_reason="Focused verification found an incorrect result.", verification_count=1, **context)
        second = module.recommend_model(self.project, "code", "recovery-routing", **context)
        self.assertEqual(second["attempt_reason"], "quality_failure_one_rung_up")
        self.assertNotEqual(second["attempt_pair"], first["attempt_pair"])
        second_receipt = self.root / "second-receipt.json"
        self.write_receipt(second["attempt_pair"], path=second_receipt)
        passed = module.record_model_result(self.project, "code", "recovery-routing", second_receipt, "pass", "none", outcome_reason="Regression verification passed after the model upgrade.", verification_count=2, **context)
        records = [record for record in module._read_local_records() if record["module"] == "recovery-routing"]
        self.assertEqual(len(records), 2)
        self.assertEqual(failed["next_pair"], second["attempt_pair"])
        self.assertEqual(passed["recovery_from_pair"], first["attempt_pair"])
        self.assertEqual(records[-1]["completed_pair"], second["attempt_pair"])
        self.assertEqual(records[-1]["outcome_reason"], "Regression verification passed after the model upgrade.")
        recommendation = module.recommend_model(self.project, "code", "recovery-routing", **context)
        self.assertEqual(recommendation["local_record_count"], 2)
        self.assertEqual(recommendation["obsidian_record_count"], 2)
        self.assertEqual(recommendation["merged_record_count"], 2)

    def test_pre_result_timeout_records_neutral_operational_fallback(self):
        context = {"file_value": "src/example.py", "symbol": "Example.timeout", "code_kind": "python", "operation": "design", "modality": "text", "complexity_score": 82, "risk": "high", "ambiguity": "high", "task_summary": "Record a timed out routing stage.", "vault": self.vault}
        recommendation = module.recommend_model(self.project, "code-design", "timeout-routing", **context)
        receipt = {"status": "fail", "turn_completed": False, "model_match": False, "effort_match": False, "requested_pair": "gpt-5.6-sol|high", "tokens": {"total_tokens": 20}, "process_elapsed_ms": 300000}
        self.receipt.write_text(json.dumps(receipt), encoding="utf-8")
        recorded = module.record_model_result(self.project, "code-design", "timeout-routing", self.receipt, "fail", "timeout", outcome_reason="The routed stage timed out before publishing.", **context)
        self.assertEqual(recorded["switch_direction"], "operational_fallback")
        self.assertEqual(recorded["next_pair"], recommendation["attempt_pair"])
        self.assertEqual(recorded["outcome_reason"], "The routed stage timed out before publishing.")

    def test_shared_page_ignores_another_project_record(self):
        foreign = {"model_experience_schema": 1, "project_key": "other-project", "task_type": "code", "module": "example-module", "file": "src/example.py", "symbol": "Example.run", "code_kind": "python", "operation": "edit", "modality": "text", "complexity": "easy", "risk": "low", "ambiguity": "low", "pair": "gpt-5.6-terra|high", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "pass", "failure_class": "none"}
        self.broad_page.write_text("# Model Switch\n\n<!-- model-experience: " + json.dumps(foreign) + " -->\n", encoding="utf-8")
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Isolation test.", vault=self.vault)
        self.assertEqual(recommendation["matched_records"], 0)

    def test_registered_project_move_reuses_old_model_learning(self):
        old_root = self.home / "Documents" / "YofaGames" / "XNews"
        current_root = self.home / "Documents" / "PythonProject" / "XNews"
        (old_root / "src").mkdir(parents=True)
        (current_root / "src").mkdir(parents=True)
        page = self.vault / "Projects" / "XNews" / "Model Switch.md"
        page.parent.mkdir(parents=True)
        old_key = module.project_change_memory._project_identity(old_root)["key"]
        old_record = {"model_experience_schema": 1, "project_key": old_key, "task_type": "code", "module": "feed", "file": "src/feed.py", "symbol": "Feed.run", "code_kind": "python", "operation": "edit", "modality": "text", "complexity": "easy", "risk": "low", "ambiguity": "low", "pair": "gpt-5.6-terra|high", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "pass", "failure_class": "none", "recorded_at": "2026-07-15T12:00:00Z"}
        page.write_text("# Model Switch\n\n<!-- model-experience: " + json.dumps(old_record) + " -->\n", encoding="utf-8")
        recommendation = module.recommend_model(current_root, "code", "feed", file_value="src/feed.py", symbol="Feed.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Update feed parser.", vault=self.vault)
        self.assertEqual(recommendation["matched_records"], 1)
        self.assertEqual(recommendation["specificity"], "symbol")

    def test_rebuild_hides_foreign_rows_but_preserves_structured_record(self):
        self.record()
        own = module._read_project_records(self.broad_page)[0]
        foreign = dict(own, record_id="foreign", project_key="unrelated-project", project_owner="Unrelated", module="foreign-module")
        self.broad_page.write_text("# Model Switch\n\n" + "\n".join("<!-- model-experience: " + json.dumps(record) + " -->" for record in (own, foreign)) + "\n", encoding="utf-8")
        result = module.rebuild_model_switches(self.project, vault=self.vault)
        text = self.broad_page.read_text(encoding="utf-8")
        records = module._read_project_records(self.broad_page)
        self.assertEqual(result["records"], 1)
        self.assertEqual(result["page_records"], 2)
        self.assertNotIn("| foreign-module |", text)
        self.assertEqual({record.get("record_id") for record in records}, {own.get("record_id"), "foreign"})

    def test_same_name_project_rebuild_no_op_with_local_only_clone(self):
        root_one = self.home / "Documents" / "Muse" / "SVGDrawer"
        root_two = self.root / "other" / "SVGDrawer"
        root_one.mkdir(parents=True)
        root_two.mkdir(parents=True)
        shared_page = self.vault / "Projects" / "SVGDrawer" / "Model Switch.md"
        shared_page.parent.mkdir(parents=True)
        foreign = {"model_experience_schema": 1, "project_key": module.project_change_memory._project_identity(root_one)["key"], "task_type": "code", "module": "root-one", "file": "src/one.py", "symbol": "run", "code_kind": "python", "operation": "edit", "modality": "text", "complexity": "easy", "risk": "low", "ambiguity": "low", "pair": "gpt-5.6-terra|high", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "pass", "failure_class": "none"}
        shared_page.write_text("# Model Switch\n\n<!-- model-experience: " + json.dumps(foreign) + " -->\n", encoding="utf-8")
        result = module.rebuild_model_switches(root_two, vault=self.vault)
        records = module._read_project_records(shared_page)
        self.assertEqual(result["status"], "no-op")
        self.assertEqual(records, [foreign])

    def test_unknown_root_status_reports_missing_broad_page_without_crash(self):
        status = module.memory_status(self.project, vault=self.vault)
        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["memory_available"])
        self.assertIsNone(status["reason"])
        self.broad_page.unlink()
        status = module.memory_status(self.project, vault=self.vault)
        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["memory_available"])
        self.assertEqual(status["reason"], "configured_broad_page_missing")

    def test_first_receipt_backed_record_lazily_creates_broad_page_and_links_index(self):
        self.broad_page.unlink()
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault)
        self.write_receipt(recommendation["attempt_pair"], path=self.root / "first.json")
        result = module.record_model_result(self.project, "code", "example-module", self.root / "first.json", "pass", "none", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault)
        self.assertEqual(result["status"], "written")
        text = self.broad_page.read_text(encoding="utf-8")
        index = self.broad_index.read_text(encoding="utf-8")
        self.assertEqual(text.count("<!-- model-experience: "), 1)
        self.assertIn("- [[Projects/ThisIsMyOregon/Model Switch.md]]", index)

    def test_real_absolute_nested_svgdrawer_mapping_is_more_specific_than_muse(self):
        query = {"project": {"name": "skill", "root": str(self.home / "Documents" / "Muse" / "SVGDrawer" / "skill"), "key": "svgdrawer-test"}}
        (self.vault / "Projects" / "SVGDrawer").mkdir(parents=True)
        (self.vault / "Projects" / "SVGDrawer" / "Model Switch.md").write_text("# Model Switch\n", encoding="utf-8")
        _, page = module._memory_root(query, self.vault)
        self.assertEqual(page.resolve(), (self.vault / "Projects" / "SVGDrawer" / "Model Switch.md").resolve())

    def test_unknown_root_cannot_create_a_broad_page(self):
        unknown = self.root / "Desktop"
        unknown.mkdir()
        before = list((self.vault / "Projects").rglob("*.md"))
        result = module.rebuild_model_switches(unknown, vault=self.vault)
        self.assertEqual(result["status"], "no-op")
        self.assertEqual(list((self.vault / "Projects").rglob("*.md")), before)

    def test_categories_are_fixed(self):
        self.assertEqual(len(module.MODEL_SWITCH_CATEGORIES), 6)
        self.assertEqual(module._task_category({"task_type": "code", "code_kind": "python", "operation": "edit"}), "normal-script-update")

    def test_standard_score_cold_start_executes_recommended_quality_pair(self):
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Cold start.", vault=self.vault)
        self.assertEqual(recommendation["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["attempt_pair"], recommendation["selected_pair"])
        self.assertEqual(recommendation["active_fallback_pair"], "gpt-5.6-terra|high")
        self.assertEqual(recommendation["complexity_score"], 35)
        self.assertEqual(recommendation["priority_producer_scope"], "bounded_text_code_and_scheduled_independent_sources")

    def test_sol_ultra_entry_routes_down_to_contextual_cold_start(self):
        recommendation = module.recommend_model(self.project, "code", "entry-aware", operation="work", complexity_score=35, task_summary="Route from a frontier entry.", entry_model="gpt-5.6-sol", entry_effort="ultra", vault=self.vault)
        self.assertEqual(recommendation["entry_pair"], "gpt-5.6-sol|ultra")
        self.assertEqual(recommendation["entry_anchor_pair"], "gpt-5.6-sol|ultra")
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["switch_direction"], "downgrade")
        self.assertEqual(recommendation["reason"], "shared_cold_start")
        self.assertEqual(recommendation["entry_route_reason"], "contextual_static_below_entry")

    def test_luna_max_entry_starts_at_entry_without_history(self):
        recommendation = module.recommend_model(self.project, "code", "entry-aware", operation="work", complexity_score=35, task_summary="Route from a lower entry.", entry_model="gpt-5.6-luna", entry_effort="max", vault=self.vault)
        self.assertEqual(recommendation["entry_pair"], "gpt-5.6-luna|max")
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-luna|max")
        self.assertEqual(recommendation["switch_direction"], "no_switch")
        self.assertEqual(recommendation["reason"], "entry_anchored_cold_start")

    def test_matching_task_and_difficulty_reuse_local_boundary_across_project_roots(self):
        foreign_project = self.root / "archived" / "ExampleProject"
        foreign_project.mkdir(parents=True)
        foreign_key = module.project_change_memory._project_identity(foreign_project)["key"]
        common = {"model_experience_schema": 1, "project_key": foreign_key, "task_type": "code", "module": "portable-routing", "file": "", "symbol": "", "code_kind": "python", "operation": "work", "modality": "text", "complexity": "easy", "complexity_score": 42, "complexity_band": "standard", "risk": "low", "ambiguity": "low", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True}
        records = [
            {**common, "pair": "gpt-5.6-luna|max", "real_status": "fail", "failure_class": "correctness"},
            {**common, "pair": "gpt-5.6-terra|low", "real_status": "fail", "failure_class": "correctness"},
            {**common, "pair": "gpt-5.6-terra|medium", "real_status": "pass", "failure_class": "none"},
        ]
        self.local_store.parent.mkdir(parents=True)
        self.local_store.write_text("".join(json.dumps({"local_model_memory_schema": 1, "event": "model-result", "event_id": f"transfer-{index}", "record": record}) + "\n" for index, record in enumerate(records)), encoding="utf-8")
        recommendation = module.recommend_model(self.project, "code", "portable-routing", code_kind="python", operation="work", modality="text", complexity_score=42, risk="low", ambiguity="low", task_summary="Reuse a matching historical boundary.", entry_model="gpt-5.6-luna", entry_effort="max", vault=self.vault)
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["selection_basis"], "local_transfer_history")
        self.assertEqual(recommendation["specificity"], "cross_project_module")
        self.assertEqual(recommendation["transfer_record_count"], 3)
        self.assertEqual(recommendation["switch_direction"], "upgrade")

    def test_cross_project_history_requires_matching_task_difficulty(self):
        foreign = {"model_experience_schema": 1, "project_key": "foreign-project", "task_type": "code", "module": "portable-routing", "file": "", "symbol": "", "code_kind": "python", "operation": "work", "modality": "text", "complexity": "complex", "complexity_score": 68, "complexity_band": "complex", "risk": "low", "ambiguity": "low", "pair": "gpt-5.6-terra|high", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "pass", "failure_class": "none"}
        self.local_store.parent.mkdir(parents=True)
        self.local_store.write_text(json.dumps({"local_model_memory_schema": 1, "event": "model-result", "event_id": "wrong-band", "record": foreign}) + "\n", encoding="utf-8")
        recommendation = module.recommend_model(self.project, "code", "portable-routing", code_kind="python", operation="work", modality="text", complexity_score=42, risk="low", ambiguity="low", task_summary="Do not transfer a different difficulty.", entry_model="gpt-5.6-luna", entry_effort="max", vault=self.vault)
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-luna|max")
        self.assertEqual(recommendation["transfer_record_count"], 0)

    def test_verified_boundary_overrides_both_low_and_high_entries(self):
        project = module.project_change_memory._project_identity(self.project)
        context = {"model_experience_schema": 1, "project_key": project["key"], "project_owner": "ThisIsMyOregon", "task_type": "code", "module": "stable-entry-aware", "file": "src/example.py", "symbol": "Example.route", "code_kind": "python", "operation": "work", "modality": "text", "complexity": "easy", "complexity_score": 35, "complexity_band": "standard", "risk": "low", "ambiguity": "low", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True}
        failed = {**context, "pair": "gpt-5.6-terra|medium", "real_status": "fail", "failure_class": "correctness"}
        passed = {**context, "pair": "gpt-5.6-terra|high", "real_status": "pass", "failure_class": "none"}
        self.broad_page.write_text("# Model Switch\n\n" + "\n".join("<!-- model-experience: " + json.dumps(record) + " -->" for record in (failed, passed)) + "\n", encoding="utf-8")
        common = {"file_value": "src/example.py", "symbol": "Example.route", "code_kind": "python", "operation": "work", "complexity_score": 35, "task_summary": "Reuse the verified routing boundary.", "vault": self.vault}
        low = module.recommend_model(self.project, "code", "stable-entry-aware", entry_model="gpt-5.6-luna", entry_effort="low", **common)
        high = module.recommend_model(self.project, "code", "stable-entry-aware", entry_model="gpt-5.6-sol", entry_effort="ultra", **common)
        self.assertEqual(low["attempt_pair"], "gpt-5.6-terra|high")
        self.assertEqual(low["switch_direction"], "upgrade")
        self.assertEqual(high["attempt_pair"], "gpt-5.6-terra|high")
        self.assertEqual(high["switch_direction"], "downgrade")
        self.assertEqual(low["calibration_state"], "frozen")

    def test_similar_image_control_step_reuses_recovered_model_from_both_entries(self):
        foreign_project = self.root / "archived" / "ImageController"
        foreign_project.mkdir(parents=True)
        profile = module.task_capability_profile(
            "code", "python", "work", "mixed", 42, "low", "low",
            "Control code that generates images through a local tool.",
        )
        common = {
            "model_experience_schema": 1,
            "project_key": module.project_change_memory._project_identity(foreign_project)["key"],
            "task_type": "code",
            "task_summary": "Control code that generates images through a local tool.",
            "module": "legacy-image-controller",
            "file": "",
            "symbol": "",
            "code_kind": "python",
            "operation": "work",
            "modality": "mixed",
            "complexity": "easy",
            "complexity_score": 42,
            "complexity_band": "standard",
            "risk": "low",
            "ambiguity": "low",
            "step_kind": profile["step_kind"],
            "capability_tags": profile["capability_tags"],
            "capability_fingerprint": profile["capability_fingerprint"],
            "receipt_status": "pass",
            "turn_completed": True,
            "model_match": True,
            "effort_match": True,
        }
        self.write_local_history([
            {**common, "pair": "gpt-5.6-luna|max", "real_status": "fail", "failure_class": "correctness"},
            {**common, "pair": "gpt-5.6-terra|medium", "real_status": "pass", "failure_class": "none"},
        ], prefix="image-control")
        scope = {
            "code_kind": "python",
            "operation": "work",
            "modality": "mixed",
            "complexity_score": 42,
            "risk": "low",
            "ambiguity": "low",
            "task_summary": "用代码控制图片生成，并调用本地工具。",
            "step_kind": "image-generation-control",
            "capability_tags": ["image-generation", "tool-control"],
            "vault": self.vault,
        }
        low_entry = module.recommend_model(self.project, "code", "new-image-controller", entry_model="gpt-5.6-luna", entry_effort="max", **scope)
        high_entry = module.recommend_model(self.project, "code", "new-image-controller", entry_model="gpt-5.6-sol", entry_effort="ultra", **scope)
        for recommendation in (low_entry, high_entry):
            self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-terra|medium")
            self.assertEqual(recommendation["reason"], "verified_quality_boundary")
            self.assertEqual(recommendation["calibration_state"], "frozen")
            self.assertEqual(recommendation["selection_basis"], "local_transfer_history")
            self.assertEqual(recommendation["transfer_record_count"], 2)
            self.assertEqual(recommendation["step_kind"], "image-generation-control")
        self.assertEqual(low_entry["switch_direction"], "upgrade")
        self.assertEqual(high_entry["switch_direction"], "downgrade")

    def test_compound_implementation_and_local_test_steps_reuse_separate_models(self):
        project = module.project_change_memory._project_identity(self.project)
        implementation_profile = module.task_capability_profile("code", "python", "implement", "text", 38, "low", "low", "Implement the bounded parser change.")
        test_profile = module.task_capability_profile("code", "python", "test", "text", 18, "low", "low", "Run the local pytest regression suite.")
        common = {
            "model_experience_schema": 1,
            "project_key": project["key"],
            "project_owner": "ThisIsMyOregon",
            "task_type": "code",
            "module": "compound-parser",
            "file": "src/example.py",
            "symbol": "",
            "code_kind": "python",
            "modality": "text",
            "risk": "low",
            "ambiguity": "low",
            "receipt_status": "pass",
            "turn_completed": True,
            "model_match": True,
            "effort_match": True,
            "real_status": "pass",
            "failure_class": "none",
        }
        implementation = {**common, "task_summary": "Implement the bounded parser change.", "operation": "implement", "complexity": "easy", "complexity_score": 38, "complexity_band": "standard", "pair": "gpt-5.6-terra|medium", "step_kind": implementation_profile["step_kind"], "capability_tags": implementation_profile["capability_tags"], "capability_fingerprint": implementation_profile["capability_fingerprint"]}
        local_test = {**common, "task_summary": "Run the local pytest regression suite.", "operation": "test", "complexity": "easy", "complexity_score": 18, "complexity_band": "small", "pair": "gpt-5.6-luna|low", "step_kind": test_profile["step_kind"], "capability_tags": test_profile["capability_tags"], "capability_fingerprint": test_profile["capability_fingerprint"]}
        self.write_local_history([implementation, local_test], prefix="compound")
        implementation_route = module.recommend_model(self.project, "code", "compound-parser", file_value="src/example.py", code_kind="python", operation="implement", complexity_score=38, task_summary="Implement the bounded parser change.", entry_model="gpt-5.6-sol", entry_effort="ultra", vault=self.vault)
        test_route = module.recommend_model(self.project, "code", "compound-parser", file_value="src/example.py", code_kind="python", operation="test", complexity_score=18, task_summary="Run the local pytest regression suite.", entry_model="gpt-5.6-sol", entry_effort="ultra", vault=self.vault)
        self.assertEqual(implementation_route["attempt_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(implementation_route["step_kind"], "implementation")
        self.assertEqual(test_route["attempt_pair"], "gpt-5.6-luna|low")
        self.assertEqual(test_route["step_kind"], "local-test")
        self.assertNotEqual(implementation_route["capability_fingerprint"], test_route["capability_fingerprint"])
        self.assertEqual(implementation_route["switch_direction"], "downgrade")
        self.assertEqual(test_route["switch_direction"], "downgrade")

    def test_nearby_but_different_capability_does_not_reuse_image_control_history(self):
        foreign_project = self.root / "archived" / "ImageMetadata"
        foreign_project.mkdir(parents=True)
        profile = module.task_capability_profile("code", "python", "work", "text", 42, "low", "low", "Control code that generates images.")
        foreign = {"model_experience_schema": 1, "project_key": module.project_change_memory._project_identity(foreign_project)["key"], "task_type": "code", "task_summary": "Control code that generates images.", "module": "image-pipeline", "file": "", "symbol": "", "code_kind": "python", "operation": "work", "modality": "text", "complexity": "easy", "complexity_score": 42, "complexity_band": "standard", "risk": "low", "ambiguity": "low", "pair": "gpt-5.6-terra|medium", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "pass", "failure_class": "none", "step_kind": profile["step_kind"], "capability_tags": profile["capability_tags"], "capability_fingerprint": profile["capability_fingerprint"]}
        self.write_local_history([foreign], prefix="nearby")
        recommendation = module.recommend_model(self.project, "code", "image-pipeline", code_kind="python", operation="work", modality="text", complexity_score=42, task_summary="Update image metadata labels.", entry_model="gpt-5.6-luna", entry_effort="max", vault=self.vault)
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-luna|max")
        self.assertEqual(recommendation["transfer_record_count"], 0)
        self.assertEqual(recommendation["reason"], "entry_anchored_cold_start")

    def test_record_projects_entry_pair_with_task_difficulty(self):
        recommendation = module.recommend_model(self.project, "code", "record-entry", operation="work", complexity_score=35, task_summary="Record entry-aware routing.", entry_model="gpt-5.6-luna", entry_effort="max", vault=self.vault)
        self.write_receipt(recommendation["attempt_pair"])
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt.update({"entry_model": "gpt-5.6-luna", "entry_effort": "max", "entry_pair": "gpt-5.6-luna|max", "entry_source": "explicit"})
        self.receipt.write_text(json.dumps(receipt), encoding="utf-8")
        recorded = module.record_model_result(self.project, "code", "record-entry", self.receipt, "pass", "none", operation="work", complexity_score=35, task_summary="Record entry-aware routing.", vault=self.vault)
        record = next(record for record in module._read_project_records(self.broad_page) if record["module"] == "record-entry")
        self.assertEqual(recorded["entry_pair"], "gpt-5.6-luna|max")
        self.assertEqual(record["entry_anchor_pair"], "gpt-5.6-luna|max")
        self.assertEqual(record["complexity_band"], "standard")
        self.assertEqual(record["step_kind"], "implementation")
        self.assertRegex(record["capability_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertIn("code-authoring", record["capability_tags"])
        self.assertIn("Step / capability", self.broad_page.read_text(encoding="utf-8"))
        self.assertIn("gpt-5.6-luna|max / gpt-5.6-luna|max", self.broad_page.read_text(encoding="utf-8"))

    def test_small_edit_score_uses_spark_priority_with_quality_fallback(self):
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity_score=12, risk="low", ambiguity="low", task_summary="Edit one bounded Python method.", vault=self.vault)
        self.assertEqual(recommendation["complexity_band"], "small")
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.3-codex-spark|low")
        self.assertEqual(recommendation["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["active_fallback_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["switch_direction"], "downgrade")

    def test_small_question_uses_spark_priority_with_quality_fallback(self):
        recommendation = module.recommend_model(self.project, "question", "example-module", operation="answer", modality="text", complexity_score=8, risk="low", ambiguity="low", task_summary="What is seven times eight?", vault=self.vault)
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.3-codex-spark|low")
        self.assertEqual(recommendation["selected_pair"], "gpt-5.6-luna|low")
        self.assertEqual(recommendation["active_fallback_pair"], "gpt-5.6-luna|low")

    def test_spark_verify_failure_suppresses_matching_score_band_and_upgrades(self):
        project = module.project_change_memory._project_identity(self.project)
        failed = {"model_experience_schema": 1, "project_key": project["key"], "task_type": "code", "module": "other-module", "file": "", "symbol": "", "code_kind": "python", "operation": "edit", "modality": "text", "complexity": "easy", "complexity_score": 18, "complexity_band": "small", "risk": "low", "ambiguity": "low", "pair": "gpt-5.3-codex-spark|low", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": "fail", "failure_class": "correctness"}
        self.broad_page.write_text("# Model Switch\n\n<!-- model-experience: " + json.dumps(failed) + " -->\n", encoding="utf-8")
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity_score=8, risk="low", ambiguity="low", task_summary="Edit another bounded Python method.", vault=self.vault)
        self.assertEqual(recommendation["priority_verdict"], "fail")
        self.assertEqual(recommendation["attempt_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["switch_direction"], "upgrade")
        self.assertEqual(recommendation["attempt_reason"], "spark_verify_failure_upgrade")

    def test_one_real_pass_collects_evidence_and_two_passes_downgrade_one_rung(self):
        first, pairs = self.active([self.quality_record("gpt-5.6-terra|medium")])
        second, _ = self.active([
            self.quality_record("gpt-5.6-terra|medium", workload="1"),
            self.quality_record("gpt-5.6-terra|medium", workload="2"),
        ])
        self.assertEqual(first["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(first["reason"], "real_pass_collecting_evidence")
        self.assertFalse(first["trial"])
        self.assertEqual(second["selected_pair"], pairs[pairs.index("gpt-5.6-terra|medium") - 1])
        self.assertEqual(second["reason"], "repeated_real_pass_one_rung_down")
        self.assertTrue(second["trial"])

    def test_quality_failure_upgrades_exactly_one_rung(self):
        active, pairs = self.active([self.quality_record("gpt-5.6-terra|medium", status="fail")])
        self.assertEqual(active["selected_pair"], pairs[pairs.index("gpt-5.6-terra|medium") + 1])
        self.assertEqual(active["reason"], "quality_failure_one_rung_up")

    def test_like_for_like_cost_ranks_tokens_then_time_then_weaker_pair(self):
        records = [
            self.quality_record("gpt-5.6-luna|low", workload="1", tokens=200, elapsed=100),
            self.quality_record("gpt-5.6-terra|medium", workload="1", tokens=100, elapsed=500),
        ]
        token_winner, _ = self.active(records)
        self.assertEqual(token_winner["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(token_winner["reason"], "receipt_cost_best_verified")
        records[0].update(total_tokens=100, process_ms=300)
        records[1].update(total_tokens=100, process_ms=500)
        time_winner, _ = self.active(records)
        self.assertEqual(time_winner["selected_pair"], "gpt-5.6-luna|low")
        records[0]["process_ms"] = records[1]["process_ms"] = 500
        tie_winner, _ = self.active(records)
        self.assertEqual(tie_winner["selected_pair"], "gpt-5.6-luna|low")

    def test_bound_historical_failure_records_once_after_recommendation_advances(self):
        pair = "gpt-5.6-terra|high"
        context = {"project_root": str(self.project.resolve()), "task_type": "documentation-instructions", "module": "example-module", "file": "src/example.py", "symbol": "Example.run", "code_kind": "python", "operation": "repair", "modality": "text", "complexity": "complex", "risk": "high", "ambiguity": "low", "task_summary": "Record a bound historical failure."}
        first_receipt = self.write_receipt(pair, self.root / "historical-one.json", context)
        first_binding = {"receipt_sha256": module.hashlib.sha256(first_receipt.read_bytes()).hexdigest(), "model_learning_context": context, "executed_pair": pair}
        first = module.record_model_result(self.project, "documentation-instructions", "example-module", first_receipt, "fail", "correctness", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="repair", modality="text", complexity="complex", risk="high", ambiguity="low", task_summary="Record a bound historical failure.", vault=self.vault, bound_receipt=first_binding)
        advanced = module.recommend_model(self.project, "documentation-instructions", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="repair", modality="text", complexity="complex", risk="high", ambiguity="low", task_summary="Record a bound historical failure.", vault=self.vault)
        second_receipt = self.write_receipt(pair, self.root / "historical-two.json", context)
        second_payload = json.loads(second_receipt.read_text(encoding="utf-8"))
        second_payload["workload_prompt_sha256"] = "2" * 64
        second_receipt.write_text(json.dumps(second_payload), encoding="utf-8")
        second_binding = {"receipt_sha256": module.hashlib.sha256(second_receipt.read_bytes()).hexdigest(), "model_learning_context": context, "executed_pair": pair}
        second = module.record_model_result(self.project, "documentation-instructions", "example-module", second_receipt, "fail", "correctness", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="repair", modality="text", complexity="complex", risk="high", ambiguity="low", task_summary="Record a bound historical failure.", vault=self.vault, bound_receipt=second_binding)
        replay = module.record_model_result(self.project, "documentation-instructions", "example-module", second_receipt, "fail", "correctness", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="repair", modality="text", complexity="complex", risk="high", ambiguity="low", task_summary="Record a bound historical failure.", vault=self.vault, bound_receipt=second_binding)
        final = module.recommend_model(self.project, "documentation-instructions", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="repair", modality="text", complexity="complex", risk="high", ambiguity="low", task_summary="Record a bound historical failure.", vault=self.vault)
        self.assertEqual(first["status"], "written")
        self.assertEqual(advanced["selected_pair"], "gpt-5.6-terra|xhigh")
        self.assertEqual(advanced["attempt_pair"], advanced["selected_pair"])
        self.assertEqual(second["status"], "written")
        self.assertEqual(replay["status"], "duplicate")
        self.assertEqual(final["selected_pair"], "gpt-5.6-terra|xhigh")
        self.assertEqual(final["attempt_pair"], final["selected_pair"])


if __name__ == "__main__":
    unittest.main()

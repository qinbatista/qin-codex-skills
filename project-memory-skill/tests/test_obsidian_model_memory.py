import importlib.util
import json
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

    def test_cold_start_executes_recommended_quality_pair_not_schedule_producer(self):
        recommendation = module.recommend_model(self.project, "code", "example-module", file_value="src/example.py", symbol="Example.run", code_kind="python", operation="edit", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="Cold start.", vault=self.vault)
        self.assertEqual(recommendation["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(recommendation["attempt_pair"], recommendation["selected_pair"])
        self.assertEqual(recommendation["active_fallback_pair"], "gpt-5.6-terra|high")
        self.assertEqual(recommendation["priority_producer_scope"], "scheduled_independent_sources_only")

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

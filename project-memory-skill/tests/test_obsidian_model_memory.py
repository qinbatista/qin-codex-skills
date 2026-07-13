#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_model_memory.py"
SPEC = importlib.util.spec_from_file_location("obsidian_model_memory", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class ObsidianModelMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "ExampleProject"
        self.project.mkdir()
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.receipt = self.root / "receipt.json"
        self.counter = 0

    def tearDown(self):
        self.temporary.cleanup()

    def write_receipt(self, pair, *, valid=True):
        self.counter += 1
        model, effort = pair.split("|", 1)
        payload = {
            "status": "pass" if valid else "fail",
            "turn_completed": valid,
            "model_match": valid,
            "effort_match": valid,
            "requested_model": model,
            "requested_effort": effort,
            "requested_pair": pair,
            "executed_pair": pair,
            "workload_prompt_sha256": f"{self.counter:064x}",
            "tokens": {"total_tokens": 100 + self.counter},
            "process_elapsed_ms": 1000 + self.counter,
        }
        self.receipt.write_text(json.dumps(payload), encoding="utf-8")

    def scope(self, **overrides):
        values = {
            "file_value": "src/example.py",
            "symbol": "Example.run",
            "code_kind": "python",
            "operation": "edit",
            "modality": "mixed",
            "complexity": "easy",
            "risk": "low",
            "ambiguity": "low",
            "task_summary": "Edit one bounded Python method and preserve its verified contract.",
            "vault": self.vault,
        }
        values.update(overrides)
        return values

    def record(self, pair, *, real_status="pass", failure_class="none", **scope_overrides):
        self.write_receipt(pair, valid=failure_class not in module.OPERATIONAL_FAILURES)
        return module.record_model_result(
            self.project,
            "code",
            "example-module",
            self.receipt,
            real_status,
            failure_class,
            recorded_at=datetime(2026, 7, 13, 12, 0, self.counter, tzinfo=timezone.utc),
            **self.scope(**scope_overrides),
        )

    def recommend(self, **scope_overrides):
        return module.recommend_model(
            self.project,
            "code",
            "example-module",
            **self.scope(**scope_overrides),
        )

    def test_cold_start_reads_shared_ladder_without_creating_local_json(self):
        result = self.recommend()
        self.assertEqual(result["source"], "obsidian_project_memory")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(result["reason"], "shared_cold_start")
        self.assertEqual(result["matched_records"], 0)
        self.assertFalse(any(self.root.rglob("model_experience.json")))

    def test_text_code_uses_spark_first_and_complex_uses_high(self):
        easy = self.recommend(modality="text")
        complex_result = self.recommend(modality="text", complexity="complex")
        self.assertEqual(easy["attempt_pair"], "gpt-5.3-codex-spark|low")
        self.assertEqual(easy["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(easy["attempt_reason"], "spark_first_text_code")
        self.assertEqual(complex_result["attempt_pair"], "gpt-5.3-codex-spark|high")
        self.assertEqual(complex_result["selected_pair"], "gpt-5.6-terra|high")

    def test_spark_quality_failure_moves_to_new_5_6_repair_pair(self):
        self.record("gpt-5.3-codex-spark|low", real_status="fail", failure_class="correctness", modality="text")
        result = self.recommend(modality="text")
        self.assertEqual(result["attempt_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(result["attempt_reason"], "spark_quality_failure_to_5_6")
        self.assertEqual(result["spark_verdict"], "fail")

    def test_verified_spark_is_retained(self):
        self.record("gpt-5.3-codex-spark|low", modality="text")
        result = self.recommend(modality="text")
        self.assertEqual(result["attempt_pair"], "gpt-5.3-codex-spark|low")
        self.assertEqual(result["attempt_reason"], "verified_spark_retained")
        self.assertEqual(result["attempt_calibration_state"], "frozen")

    def test_real_pass_moves_one_rung_down_and_writes_project_indexes(self):
        written = self.record("gpt-5.6-terra|medium")
        self.assertEqual(written["status"], "written")
        result = self.recommend()
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|low")
        self.assertEqual(result["reason"], "real_pass_one_rung_down")
        self.assertTrue(result["trial"])
        project_root = self.vault / "Projects" / result["project_key"] / "ModelExperience"
        self.assertTrue((project_root / "index.md").is_file())
        self.assertTrue(any((project_root / "modules").glob("*.md")))
        self.assertTrue(any((project_root / "files").rglob("*.md")))
        self.assertTrue(any((project_root / "symbols").rglob("*.md")))
        record = module._read_project_records(project_root)[0]
        self.assertEqual(record["selection_reason"], "shared_cold_start")
        self.assertEqual(record["recommendation_state"], "cold_start")
        self.assertEqual(record["specificity"], "project_task")

    def test_repeated_real_passes_descend_to_luna_low_and_freeze(self):
        recommendation = self.recommend()
        visited = []
        for _ in range(20):
            pair = recommendation["selected_pair"]
            visited.append(pair)
            self.record(pair)
            recommendation = self.recommend()
            if recommendation["calibration_state"] == "frozen":
                break
        self.assertEqual(recommendation["selected_pair"], "gpt-5.6-luna|low")
        self.assertEqual(recommendation["reason"], "verified_floor_retained")
        self.assertFalse(recommendation["trial"])
        self.assertIn("gpt-5.6-terra|low", visited)
        self.assertIn("gpt-5.6-luna|max", visited)

    def test_quality_failure_moves_exactly_one_rung_up(self):
        self.record("gpt-5.6-terra|medium", real_status="fail", failure_class="quality")
        result = self.recommend()
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|high")
        self.assertEqual(result["reason"], "quality_failure_one_rung_up")
        self.assertTrue(result["trial"])

    def test_operational_failure_is_neutral(self):
        self.record("gpt-5.6-terra|medium", real_status="fail", failure_class="timeout")
        result = self.recommend()
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(result["reason"], "shared_cold_start")
        self.assertEqual(result["quality_samples"], 0)

    def test_matched_receipt_must_use_the_current_obsidian_recommendation(self):
        with self.assertRaisesRegex(ValueError, "current Obsidian recommendation"):
            self.record("gpt-5.6-sol|high")
        self.assertFalse(any(self.vault.rglob("*.md")))

    def test_same_receipt_and_verdict_are_idempotent_after_boundary_moves(self):
        self.write_receipt("gpt-5.6-terra|medium")
        arguments = self.scope()
        first = module.record_model_result(
            self.project,
            "code",
            "example-module",
            self.receipt,
            "pass",
            "none",
            recorded_at=datetime(2026, 7, 13, 12, 30, tzinfo=timezone.utc),
            **arguments,
        )
        second = module.record_model_result(
            self.project,
            "code",
            "example-module",
            self.receipt,
            "pass",
            "none",
            recorded_at=datetime(2026, 7, 13, 12, 31, tzinfo=timezone.utc),
            **arguments,
        )
        self.assertEqual(first["status"], "written")
        self.assertEqual(second["status"], "duplicate")
        self.assertEqual(first["record_id"], second["record_id"])

    def test_exact_symbol_evidence_outranks_other_file_evidence(self):
        self.record("gpt-5.6-terra|medium", real_status="fail", failure_class="correctness")
        self.record(
            "gpt-5.6-terra|high",
            file_value="src/other.py",
            symbol="Other.run",
            task_summary="Edit another bounded Python method and preserve its contract.",
        )
        result = self.recommend()
        self.assertEqual(result["specificity"], "symbol")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|high")
        self.assertEqual(result["matched_records"], 1)

    def test_same_symbol_name_in_another_file_cannot_cross_the_file_boundary(self):
        self.record("gpt-5.6-terra|medium", real_status="fail", failure_class="correctness", symbol="")
        self.record(
            "gpt-5.6-terra|high",
            file_value="src/other.py",
            symbol="Example.run",
            task_summary="Edit a same-named method in a different file.",
        )
        result = self.recommend()
        self.assertEqual(result["specificity"], "file")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|high")
        self.assertEqual(result["matched_records"], 1)

    def test_status_names_obsidian_as_the_authority(self):
        status = module.memory_status(self.project, vault=self.vault)
        self.assertEqual(status["authority"], "obsidian_project_memory")
        self.assertEqual(status["records"], 0)
        self.assertGreater(status["active_pairs"], 0)


if __name__ == "__main__":
    unittest.main()

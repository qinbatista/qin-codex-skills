#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "routing_benchmark.py"
SPEC = importlib.util.spec_from_file_location("routing_benchmark", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class RoutingBenchmarkTests(unittest.TestCase):
    def test_frozen_cjk_mixed_and_unity_cohorts_pass_without_model_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            report = BENCHMARK.run_benchmark(iterations=2)
            BENCHMARK._atomic_write_json(output, report)
            saved = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "pass")
        self.assertEqual(saved["model_execution"], "not_run")
        self.assertEqual(saved["case_count"], 46)
        self.assertEqual(saved["passed_case_count"], 46)
        self.assertEqual(saved["cohorts"]["cjk_simple"]["case_count"], 10)
        self.assertEqual(saved["cohorts"]["cjk_medium"]["case_count"], 10)
        self.assertEqual(saved["cohorts"]["cjk_complex"]["case_count"], 10)
        self.assertEqual(saved["cohorts"]["unity"]["case_count"], 8)
        self.assertNotIn("这个函数是干什么的", json.dumps(saved, ensure_ascii=False))

    def test_invalid_iteration_count_fails_closed(self):
        with self.assertRaisesRegex(BENCHMARK.RoutingBenchmarkError, "iterations"):
            BENCHMARK.run_benchmark(iterations=0)


if __name__ == "__main__":
    unittest.main()

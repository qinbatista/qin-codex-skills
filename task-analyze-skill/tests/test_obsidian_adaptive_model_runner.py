#!/usr/bin/env python3
import importlib.util
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_adaptive_model_runner.py"
SPEC = importlib.util.spec_from_file_location("obsidian_adaptive_model_runner", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def recommendation(pair="gpt-5.6-terra|medium", attempt_pair=None):
    model, effort = pair.split("|", 1)
    return {
        "source": "obsidian_broad_model_switch",
        "memory_available": True,
        "selected_pair": pair,
        "selected_model": model,
        "selected_effort": effort,
        "attempt_pair": attempt_pair or pair,
        "active_fallback_pair": pair if attempt_pair and attempt_pair != pair else None,
        "attempt_trial": True,
        "attempt_reason": "spark_first_text_code" if attempt_pair else "real_pass_one_rung_down",
        "attempt_calibration_state": "cold_start" if attempt_pair else "provisional",
        "trial": True,
        "reason": "real_pass_one_rung_down",
        "calibration_state": "provisional",
        "specificity": "symbol",
        "matched_records": 2,
        "project_key": "example-123",
    }


class ObsidianAdaptiveRunnerTests(unittest.TestCase):
    def arguments(self, root):
        project = root / "project"
        project.mkdir()
        return SimpleNamespace(
            project_root=project,
            task_type="code",
            module="module",
            file="src/a.py",
            symbol="A.run",
            code_kind="python",
            operation="edit",
            modality="text",
            complexity="easy",
            risk="low",
            ambiguity="low",
            task_summary="Edit one method.",
            vault=root / "vault",
            ladder=module.obsidian_model_memory.DEFAULT_LADDER,
            workload_id="workload",
            receipt_output=root / "receipt.json",
            result_output=root / "result.md",
            workdir=project,
            state_db=root / "state.db",
            codex_bin="codex",
            sandbox="read-only",
            allow_fallback=[],
            ignore_user_config=True,
            timeout=60,
            emit_result=True,
        )

    def test_executes_exact_obsidian_selected_pair_and_returns_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))

            def fake_run(receipt_args, prompt):
                self.assertEqual((receipt_args.model, receipt_args.effort), ("gpt-5.6-terra", "medium"))
                receipt_args.result_output.write_text("RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|medium", "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 12, "tokens": {"total_tokens": 34}}

            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["memory_source"], "obsidian_broad_model_switch")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(result["result"], "RESULT")

    def test_zero_argument_stdin_fast_path_derives_safe_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workdir = root / "fixture"
            workdir.mkdir()
            with patch.dict(module.os.environ, {"CODEX_HOME": str(root / "codex-home")}, clear=False):
                args = module.resolve_fast_path_args(module.parse_args(["--workdir", str(workdir)]), "  Implement one function.\nRun tests.  ")
        self.assertEqual(args.project_root, workdir.resolve())
        self.assertEqual(args.task_type, "code")
        self.assertEqual(args.module, "fixture")
        self.assertEqual(args.task_summary, "Implement one function. Run tests.")
        self.assertEqual(args.complexity, "easy")
        self.assertRegex(args.workload_id, r"^fast-[0-9a-f]{16}$")
        self.assertEqual(args.receipt_output.parent, args.result_output.parent)
        self.assertEqual(args.receipt_output.parent.parent.parent, (root / "codex-home" / "tmp").resolve())
        self.assertEqual(args.sandbox, "workspace-write")
        self.assertTrue(args.emit_result)

    def test_explicit_route_arguments_keep_read_only_and_emit_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = ["--project-root", str(root), "--task-type", "code", "--module", "module", "--workload-id", "explicit", "--receipt-output", str(root / "receipt.json"), "--result-output", str(root / "result.txt")]
            args = module.resolve_fast_path_args(module.parse_args(argv), "Do work")
        self.assertEqual(args.workload_id, "explicit")
        self.assertEqual(args.sandbox, "read-only")
        self.assertFalse(args.emit_result)
        self.assertEqual(args.complexity, "easy")

    def test_fast_path_infers_numeric_and_multifile_complexity(self):
        with tempfile.TemporaryDirectory() as temporary:
            numeric = module.resolve_fast_path_args(
                module.parse_args(["--workdir", temporary]),
                "Use Decimal, ROUND_HALF_UP cents, tax, and percent calculations.",
            )
            multifile = module.resolve_fast_path_args(
                module.parse_args(["--workdir", temporary]),
                "Complete the six-file store quote pipeline.",
            )
            explicit = module.resolve_fast_path_args(
                module.parse_args(["--workdir", temporary, "--complexity", "easy"]),
                "Complete the six-file store quote pipeline.",
            )
        self.assertEqual(numeric.complexity, "complex")
        self.assertEqual(multifile.complexity, "complex")
        self.assertEqual(explicit.complexity, "easy")

    def test_fast_path_summary_respects_memory_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "word " * 200)
        self.assertEqual(len(args.task_summary), 280)

    def test_fast_path_identity_is_stable_per_project_and_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "Do A")
            second = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "Do A")
            different = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "Do B")
            different_metadata = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary, "--module", "other"]), "Do A")
        self.assertEqual(first.workload_id, second.workload_id)
        self.assertNotEqual(first.workload_id, different.workload_id)
        self.assertNotEqual(first.workload_id, different_metadata.workload_id)

    def test_main_zero_argument_path_resolves_before_run_without_refresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            workdir = Path(temporary)
            with patch.object(module.Path, "cwd", return_value=workdir), patch.object(module.sys, "stdin", io.StringIO("Implement one function")), patch.object(module.sys, "stdout", io.StringIO()), patch.object(module, "_recommend") as recommend, patch.object(module, "run", return_value={"status": "pass"}) as execute:
                status = module.main([])
        self.assertEqual(status, 0)
        recommend.assert_not_called()
        args, prompt = execute.call_args.args
        self.assertEqual(prompt, "Implement one function")
        self.assertEqual(args.task_type, "code")
        self.assertEqual(args.sandbox, "workspace-write")
        self.assertTrue(args.emit_result)

    def test_receipt_and_summary_embed_only_sanitized_model_learning_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.task_summary = "  Edit one method.\nKeep behavior stable.  "

            def fake_run(receipt_args, prompt):
                receipt_args.result_output.write_text("RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|medium", "effective_pair": "gpt-5.6-terra|medium", "result_published": True, "turn_completed": True, "model_match": True, "effort_match": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 12, "tokens": {"total_tokens": 34}}

            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "SECRET RAW PROMPT MUST NOT BE STORED")
            receipt = json.loads(args.receipt_output.read_text(encoding="utf-8"))
        expected_fields = {"project_root", "task_type", "module", "file", "symbol", "code_kind", "operation", "modality", "complexity", "risk", "ambiguity", "task_summary"}
        self.assertEqual(set(result["model_learning_context"]), expected_fields)
        self.assertEqual(receipt["model_learning_context"], result["model_learning_context"])
        self.assertEqual(result["model_learning_context"]["task_summary"], "Edit one method. Keep behavior stable.")
        self.assertNotIn("SECRET RAW PROMPT", json.dumps(receipt))
        self.assertNotIn("SECRET RAW PROMPT", json.dumps(result))

    def test_receipt_args_use_an_exact_supported_route_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            receipt_args = module._receipt_args(args, ("gpt-5.3-codex-spark", "low"))
        self.assertEqual(receipt_args.route_marker, "LOCKED_ROUTE_NODE")
        self.assertIn(receipt_args.route_marker, module.model_execution_receipt.ROUTE_MARKERS)

    def test_blocked_boundary_does_not_launch_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            blocked = recommendation()
            blocked.update({"selected_pair": None, "attempt_pair": None, "reason": "quality_boundary_exhausted", "calibration_state": "blocked"})
            with patch.object(module, "_recommend", return_value=blocked), patch.object(module.model_execution_receipt, "run_receipt") as execute:
                result = module.run(args, "Do the work")
        self.assertEqual(result["status"], "blocked")
        execute.assert_not_called()

    def test_missing_obsidian_memory_stays_inline_without_launching_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            unavailable = recommendation()
            unavailable["memory_available"] = False
            with patch.object(module, "_recommend", return_value=unavailable), patch.object(module.model_execution_receipt, "run_receipt") as execute:
                result = module.run(args, "Do the work")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "obsidian_model_memory_unavailable")
        execute.assert_not_called()

    def test_failed_execution_is_operational_and_not_quality_learning(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            failed = {"status": "fail", "requested_pair": "gpt-5.6-terra|medium", "result_published": False, "process_elapsed_ms": 5, "tokens": {}}
            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", return_value=failed):
                result = module.run(args, "Do the work")
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["reason"], "producer_operational_failure")
        self.assertEqual(result["ending_real_status"], "not_started")

    def test_spark_pre_execution_failure_falls_back_once_to_active_5_6(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            calls = []

            def fake_run(receipt_args, prompt):
                pair = f"{receipt_args.model}|{receipt_args.effort}"
                calls.append(pair)
                if pair.startswith("gpt-5.3-codex-spark|"):
                    return {
                        "status": "fail",
                        "failure_class": "availability",
                        "requested_pair": pair,
                        "turn_completed": False,
                        "model_match": False,
                        "effort_match": False,
                        "tokens": {"total_tokens": 0},
                        "process_elapsed_ms": 2,
                        "route_attempts": [{"requested_pair": pair, "tokens": {"total_tokens": 0}}],
                    }
                receipt_args.result_output.write_text("FALLBACK RESULT", encoding="utf-8")
                return {
                    "status": "pass",
                    "requested_pair": pair,
                    "effective_pair": pair,
                    "turn_completed": True,
                    "model_match": True,
                    "effort_match": True,
                    "result_published": True,
                    "result_ready_monotonic_ns": time.monotonic_ns(),
                    "process_elapsed_ms": 7,
                    "tokens": {"total_tokens": 20},
                    "route_attempts": [{"requested_pair": pair, "effective_pair": pair, "tokens": {"total_tokens": 20}}],
                }

            spark = recommendation(attempt_pair="gpt-5.3-codex-spark|low")
            with patch.object(module, "_recommend", return_value=spark), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
            receipt = __import__("json").loads(args.receipt_output.read_text(encoding="utf-8"))
        self.assertEqual(calls, ["gpt-5.3-codex-spark|low", "gpt-5.6-terra|medium"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["result"], "FALLBACK RESULT")
        self.assertEqual(receipt["operational_failure_pairs"], ["gpt-5.3-codex-spark|low"])
        self.assertEqual(len(receipt["route_attempts"]), 2)

    def test_spark_published_result_never_foreground_fallbacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            calls = []

            def fake_run(receipt_args, prompt):
                pair = f"{receipt_args.model}|{receipt_args.effort}"
                calls.append(pair)
                receipt_args.result_output.write_text("SPARK RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": pair, "effective_pair": pair, "turn_completed": True, "model_match": True, "effort_match": True, "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 3, "tokens": {"total_tokens": 9}, "route_attempts": [{"requested_pair": pair, "effective_pair": pair, "tokens": {"total_tokens": 9}}]}

            spark = recommendation(attempt_pair="gpt-5.3-codex-spark|low")
            with patch.object(module, "_recommend", return_value=spark), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
        self.assertEqual(calls, ["gpt-5.3-codex-spark|low"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["ending_real_status"], "pending")


if __name__ == "__main__":
    unittest.main()

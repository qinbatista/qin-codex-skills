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
            entry_model="gpt-5.6-sol",
            entry_effort="ultra",
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

    def test_independent_read_only_sources_enable_safe_schedule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_text("A = 1\n", encoding="utf-8")
            (root / "b.py").write_text("B = 2\n", encoding="utf-8")
            prompt = "Complete two independent source audits. Do not edit files.\n- a.py\n- b.py\nReturn JSON."
            sources = module.scheduled_source_paths(prompt, root)
            compressed = module.scheduled_source_paths("Audit independent a.py, b.py. Read-only, no edits.", root)
            dependent = module.scheduled_source_paths("Complete a two-file pipeline. Do not edit files.\n- a.py\n- b.py", root)
        self.assertEqual(sources, ["a.py", "b.py"])
        self.assertEqual(compressed, ["a.py", "b.py"])
        self.assertEqual(dependent, [])

    def test_exact_expression_contract_does_not_fan_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_text("A = 1\n", encoding="utf-8")
            (root / "b.py").write_text("B = 2\n", encoding="utf-8")
            prompt = "Audit independent a.py and b.py. Read-only. Return exactly JSON; copy each exact expression, preserve key order and the exact literal."
            sources = module.scheduled_source_paths(prompt, root)
        self.assertEqual(sources, [])

    def test_safe_source_graph_overrides_mislabeled_easy_complexity(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "easy"
            (args.workdir / "a.py").write_text("A = 1\n", encoding="utf-8")
            (args.workdir / "b.py").write_text("B = 2\n", encoding="utf-8")
            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module, "_run_scheduled_graph", return_value={"status": "pass"}) as scheduled:
                result = module.run(args, "Audit independent a.py, b.py. Read-only, no edits.")
        self.assertEqual(result["status"], "pass")
        scheduled.assert_called_once()

    def test_scheduled_plan_uses_parallel_priority_branches_and_adaptive_merge(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "complex"
            (args.workdir / "a.py").write_text("A = 1\n", encoding="utf-8")
            (args.workdir / "b.py").write_text("B = 2\n", encoding="utf-8")
            proof = {"selected_pair": "gpt-5.6-terra|medium", "attempt_pair": "gpt-5.3-codex-spark|high", "active_fallback_pair": "gpt-5.6-terra|medium", "trial": False, "reason": "shared_cold_start", "profile_fingerprint": "fingerprint", "calibration_state": "cold_start", "best_pair": None, "selection_basis": "shared_cold_start"}
            adaptive = {"selected_pair": "gpt-5.6-terra|medium", "trial": False}
            with patch.object(module.task_route_dispatcher, "_obsidian_recommendation_and_proof", return_value=(adaptive, proof)):
                plan, merge_recommendation = module._scheduled_plan(
                    args,
                    "Complete two independent source audits. Do not edit files.\n- a.py\n- b.py",
                    ["a.py", "b.py"],
                    "gpt-5.6-sol",
                    "ultra",
                    recommendation(attempt_pair="gpt-5.3-codex-spark|high"),
                )
        result_nodes = [node for node in plan["nodes"] if node["phase"] == "result"]
        self.assertEqual(plan["topology"], "parallel")
        self.assertEqual(plan["entry"], {"model": "gpt-5.6-sol", "effort": "ultra"})
        self.assertEqual([node["source_allowlist"] for node in result_nodes[:-1]], [["a.py"], ["b.py"]])
        self.assertEqual([(node["model"], node["effort"]) for node in result_nodes[:-1]], [("gpt-5.3-codex-spark", "low"), ("gpt-5.3-codex-spark", "low")])
        self.assertTrue(all(node["priority_producer"] is True for node in result_nodes[:-1]))
        self.assertIn("Omit unsupported fields", result_nodes[0]["prompt"])
        self.assertIn("Prefer direct defining-source facts", result_nodes[-1]["prompt"])
        self.assertEqual((result_nodes[-1]["model"], result_nodes[-1]["effort"]), ("gpt-5.6-terra", "medium"))
        self.assertEqual(result_nodes[-1]["routing_recommendation"]["attempt_pair"], "gpt-5.3-codex-spark|high")
        self.assertEqual(merge_recommendation, adaptive)

    def test_exact_expression_schedule_raises_branch_quality(self):
        exact = "Return exactly one JSON object. Copy the exact expression, preserve key order, and preserve the exact literal."
        relaxed = "Summarize two independent files as JSON."
        self.assertEqual(module._scheduled_branch_pair(exact, "gpt-5.6-luna|low"), ("gpt-5.6-terra", "medium"))
        self.assertEqual(module._scheduled_branch_pair(relaxed, "gpt-5.6-luna|low"), ("gpt-5.6-luna", "low"))

    def test_exact_expression_single_producer_uses_frontier_quality_guard(self):
        base = recommendation()
        exact = "Return exactly JSON; copy the exact expression, preserve key order, and preserve the exact literal."
        guarded = module._exact_contract_recommendation(exact, base)
        self.assertEqual(guarded["selected_pair"], "gpt-5.6-sol|high")
        self.assertEqual(guarded["attempt_pair"], "gpt-5.6-sol|high")
        self.assertEqual(guarded["attempt_reason"], "exact_expression_quality_guard")
        self.assertIsNone(guarded["active_fallback_pair"])
        self.assertEqual(base["selected_pair"], "gpt-5.6-terra|medium")

    def test_scheduled_branch_receives_only_its_owned_contract(self):
        prompt = """Complete independent source audits. Do not edit files.
- a.py
- b.py
Return exactly one JSON object.

alpha is owned only by a.py and uses key value.
- value is the exact assignment.

beta is owned only by b.py and uses key name.
- name is the exact function name.

source_files must list both sources."""
        first = module._scheduled_branch_prompt(prompt, "a.py")
        second = module._scheduled_branch_prompt(prompt, "b.py")
        self.assertIn("alpha is owned only by a.py", first)
        self.assertNotIn("beta is owned only by b.py", first)
        self.assertIn("beta is owned only by b.py", second)
        self.assertNotIn("alpha is owned only by a.py", second)
        self.assertIn("Return exactly one JSON object", first)
        self.assertIn("Do not read another source", first)

    def test_owned_contract_handles_long_prefix_offsets_as_search_positions(self):
        prefix = "Global rule. " * 40
        prompt = f"""{prefix}
alpha is owned only by a.py and uses key value.
- value is exact.

beta is owned only by b.py and uses key name.
- name is exact.

source_files must list both sources."""
        contract = module._owned_source_contract(prompt, "a.py")
        self.assertIn("alpha is owned only by a.py", contract)
        self.assertNotIn("beta is owned only by b.py", contract)

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

    def test_missing_obsidian_memory_uses_shared_cold_start_instead_of_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            unavailable = recommendation()
            unavailable["memory_available"] = False
            def fake_run(receipt_args, prompt):
                receipt_args.result_output.write_text("COLD START RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|medium", "effective_pair": "gpt-5.6-terra|medium", "result_published": True, "turn_completed": True, "model_match": True, "effort_match": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 12, "tokens": {"total_tokens": 34}}
            with patch.object(module, "_recommend", return_value=unavailable), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run) as execute:
                result = module.run(args, "Do the work")
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["memory_available"])
        self.assertEqual(result["result"], "COLD START RESULT")
        execute.assert_called_once()

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

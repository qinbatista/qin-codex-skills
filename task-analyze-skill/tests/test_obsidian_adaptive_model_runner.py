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


def recommendation(pair="gpt-5.6-terra|medium", fallback_pair="gpt-5.6-terra|high"):
    model, effort = pair.split("|", 1)
    return {
        "source": "local_and_obsidian_model_history",
        "memory_available": True,
        "selected_pair": pair,
        "selected_model": model,
        "selected_effort": effort,
        "attempt_pair": pair,
        "active_fallback_pair": fallback_pair,
        "attempt_trial": True,
        "attempt_reason": "repeated_real_pass_one_rung_down",
        "attempt_calibration_state": "provisional",
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
            complexity_score=12,
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
            cache_root=project / "Cache" / "tmp-task-analyze",
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
        self.assertEqual(result["memory_source"], "local_and_obsidian_model_history")
        self.assertEqual(result["entry_pair"], "gpt-5.6-sol|ultra")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(result["result"], "RESULT")

    def test_recommendation_receives_resolved_entry_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.resolved_entry_model = "gpt-5.6-luna"
            args.resolved_entry_effort = "max"
            with patch.object(module.obsidian_model_memory, "recommend_model", return_value=recommendation()) as recommend:
                module._recommend(args)
        self.assertEqual(recommend.call_args.kwargs["entry_model"], "gpt-5.6-luna")
        self.assertEqual(recommend.call_args.kwargs["entry_effort"], "max")

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
        self.assertIsInstance(args.complexity_score, int)
        self.assertEqual(args.complexity_band, module.obsidian_model_memory.complexity_band(args.complexity_score))
        self.assertRegex(args.workload_id, r"^fast-[0-9a-f]{16}$")
        self.assertEqual(args.receipt_output.parent, args.result_output.parent)
        expected_output_root = workdir / "Cache" / "tmp-task-analyze" / "adaptive-producer" / args.workload_id
        self.assertEqual(args.receipt_output.parent, expected_output_root.resolve())
        self.assertNotIn("codex-home", str(args.receipt_output))
        self.assertEqual(args.sandbox, "workspace-write")
        self.assertTrue(args.emit_result)

    def test_route_ready_event_is_flushed_before_producer_call(self):
        class FlushTrackingStream(io.StringIO):
            def __init__(self):
                super().__init__()
                self.flush_count = 0

            def flush(self):
                self.flush_count += 1
                super().flush()

        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            stream = FlushTrackingStream()
            adaptive = recommendation()

            def fake_run(receipt_args, prompt):
                self.assertTrue(stream.getvalue().splitlines())
                self.assertEqual(receipt_args.code_rule_bundle["execution_domain"], "python")
                receipt_args.result_output.write_text("RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|medium", "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 12, "tokens": {"total_tokens": 34}}

            with patch.object(module.sys, "stdout", stream), patch.object(module, "_recommend", return_value=adaptive), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
            events = [json.loads(line) for line in stream.getvalue().splitlines()]
            event = events[0]
            notice_event = events[1]
            code_notice_event = events[2]
            lifecycle_notice_event = events[3]
        expected_notice = module._model_route_notice(args, adaptive)
        self.assertEqual(event, {"schema_version": 1, "stage": "route-ready", "task_type": "code", "operation": "edit", "complexity_score": 12, "complexity_band": "small", "fast_path_eligible": False, "routing_reasons": [], "entry_pair": "gpt-5.6-sol|ultra", "entry_source": "explicit", "selected_pair": "gpt-5.6-terra|medium", "attempt_pair": "gpt-5.6-terra|medium", "active_fallback_pair": "gpt-5.6-terra|high", "switch_direction": "no_switch", "switch_change": "initial->gpt-5.6-terra|medium", "receipt_path": str(args.receipt_output), "result_path": str(args.result_output), "result_pending": True, "user_visible_message": expected_notice["message"], "model_route_notice": expected_notice})
        self.assertEqual(notice_event, {"schema_version": 1, "stage": "model-switch-notice", "user_visible": True, **expected_notice})
        self.assertEqual(code_notice_event["stage"], "code-rule-notice")
        self.assertTrue(code_notice_event["user_visible"])
        self.assertEqual(code_notice_event["execution_domain"], "python")
        self.assertEqual(code_notice_event["reference_paths"][:2], [module.routing_policy.CODE_SKILL_ENTRY_REFERENCE, module.routing_policy.CODE_WRITING_PHILOSOPHY_REFERENCE])
        self.assertEqual([event["stage"] for event in events[:3]], ["route-ready", "model-switch-notice", "code-rule-notice"])
        self.assertEqual(lifecycle_notice_event["stage"], "execution-lifecycle-notice")
        self.assertEqual(lifecycle_notice_event["execution_lifecycle"]["mode"], "planned_single")
        self.assertGreaterEqual(stream.flush_count, 1)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["model_route_notice"], expected_notice)

    def test_repeated_failure_notice_names_the_higher_model_and_task_part(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.resolved_entry_model = "gpt-5.6-luna"
            args.resolved_entry_effort = "max"
            adaptive = recommendation(pair="gpt-5.6-terra|low", fallback_pair="gpt-5.6-terra|medium")
            adaptive.update({"step_kind": "debugging", "session_effort": {"failure_recorded": True, "user_effort": 10, "last_model_pair": "gpt-5.6-luna|max", "solving_surface": "core_solving", "step_estimate": 1, "estimated_effort": "low", "model_difficulty": "difficult", "information_burden": "low"}, "session_escalation": {"applied": True, "from_pair": "gpt-5.6-luna|max", "to_pair": "gpt-5.6-terra|low"}})
            notice = module._model_route_notice(args, adaptive)
        self.assertEqual(notice["kind"], "session_model_escalation")
        self.assertIn("increased the model to gpt-5.6-terra|low", notice["message"])
        self.assertIn("core solving / debugging part", notice["message"])
        self.assertIn("Entry model remains gpt-5.6-luna|max", notice["message"])
        self.assertEqual(notice["estimated_steps"], 1)

    def test_graph_notice_lists_each_modelled_task_part(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.resolved_entry_model = "gpt-5.6-luna"
            args.resolved_entry_effort = "max"
            plan = {"nodes": [{"id": "source-1", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "step_kind": "analysis", "dependencies": []}, {"id": "merge-result", "phase": "result", "model": "gpt-5.6-terra", "effort": "medium", "step_kind": "integration", "dependencies": ["source-1"]}, {"id": "ending-verify", "phase": "ending", "model": "gpt-5.6-terra", "effort": "high", "dependencies": ["merge-result"]}]}
            notice = module._graph_model_route_notice(args, plan, recommendation(), recommendation(pair="gpt-5.6-terra|medium"))
        self.assertEqual(notice["kind"], "graph_model_route")
        self.assertEqual([part["node_id"] for part in notice["parts"]], ["source-1", "merge-result", "ending-verify"])
        self.assertIn("3 task parts have routed model/effort assignments", notice["message"])
        self.assertIn("0 source captures run locally", notice["message"])

    def test_explicit_route_arguments_keep_read_only_and_emit_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = ["--project-root", str(root), "--task-type", "code", "--module", "module", "--workload-id", "explicit", "--receipt-output", str(root / "receipt.json"), "--result-output", str(root / "result.txt")]
            args = module.resolve_fast_path_args(module.parse_args(argv), "Do work")
        self.assertEqual(args.workload_id, "explicit")
        self.assertEqual(args.sandbox, "read-only")
        self.assertFalse(args.emit_result)
        self.assertEqual(args.complexity, "easy")
        self.assertEqual(args.symbol, "__module__")

    def test_fast_path_defaults_an_unscoped_code_request_to_module_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "Fix the lifecycle trigger and deploy it.")
        self.assertEqual(args.task_type, "code")
        self.assertEqual(args.symbol, "__module__")

    def test_fast_path_uses_session_aware_recommendation_and_keeps_code_ending_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            prompt = "修改 PlayerController.cs，把 jumpHeight 从5改成6"
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), prompt)
            adaptive = recommendation(pair="gpt-5.6-terra|low", fallback_pair="gpt-5.6-terra|medium")
            adaptive.update({"session_effort": {"available": True, "failure_recorded": True, "resolution_state": "feedback_unresolved", "user_effort": 3, "last_model_pair": "gpt-5.6-luna|low", "solving_surface": "core_solving", "step_estimate": 1, "estimated_effort": "low", "model_difficulty": "bounded", "information_burden": "low"}, "session_escalation": {"applied": True, "from_pair": "gpt-5.6-luna|low", "to_pair": "gpt-5.6-terra|low"}})

            def fake_run(receipt_args, _prompt):
                self.assertEqual((receipt_args.model, receipt_args.effort), ("gpt-5.6-terra", "low"))
                receipt_args.result_output.parent.mkdir(parents=True, exist_ok=True)
                receipt_args.result_output.write_text("RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|low", "effective_pair": "gpt-5.6-terra|low", "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 1, "tokens": {"total_tokens": 1}}

            with patch.object(module, "_recommend", return_value=adaptive) as recommend, patch.object(module, "_resolved_entry_pair", return_value=("gpt-5.6-terra", "medium", "configured")), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, prompt)
        recommend.assert_called_once_with(args, prompt)
        self.assertEqual(result["memory_source"], "local_and_obsidian_model_history")
        self.assertEqual(result["selected_pair"], "gpt-5.6-terra|low")
        self.assertTrue(result["fast_path_eligible"])
        self.assertTrue(result["session_escalation"]["applied"])
        self.assertTrue(result["ending_required"])
        self.assertEqual(result["execution_summary"]["selected_pair"], "gpt-5.6-terra|low")

    def test_route_attempts_are_bounded_to_primary_plus_one_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.allow_fallback = ["gpt-5.6-luna|low", "gpt-5.6-sol|high"]
            recommendation_value = recommendation("gpt-5.6-terra|medium", "gpt-5.6-terra|high")
            with patch.object(module.obsidian_model_memory, "load_shared_ladder", return_value=({}, ["gpt-5.6-terra|medium", "gpt-5.6-terra|high", "gpt-5.6-luna|low", "gpt-5.6-sol|high"])):
                pairs = module._attempt_pairs(args, recommendation_value)
        self.assertEqual(pairs, ["gpt-5.6-terra|medium", "gpt-5.6-terra|high"])
        self.assertEqual(len(pairs), module.MAX_PRODUCER_ROUTE_ATTEMPTS)

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

    def test_explicit_numeric_score_overrides_inference_and_drives_band(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary, "--complexity-score", "9"]), "Complete a multi-file architecture migration.")
        self.assertEqual(args.complexity_score, 9)
        self.assertEqual(args.complexity, "easy")
        self.assertEqual(module.obsidian_model_memory.complexity_band(args.complexity_score), "small")
        self.assertEqual(module.infer_operation("Please change one text value"), "edit")

    def test_complex_global_lifecycle_request_is_not_masked_by_small_edit_wording(self):
        prompt = "Update global skills so small edits use Spark, add model routing downgrade and upgrade, build real verification tests, split independent Ending tasks, record Obsidian history, and run repair loops with fresh verifiers."
        score = module.infer_complexity_score(prompt)
        self.assertGreaterEqual(score, 75)
        self.assertEqual(module.obsidian_model_memory.complexity_band(score), "advanced")

    def test_one_local_typo_remains_small(self):
        score = module.infer_complexity_score("Fix one typo in a single Python function.")
        self.assertLessEqual(score, 24)
        self.assertEqual(module.obsidian_model_memory.complexity_band(score), "small")

    def test_simple_question_is_classified_for_spark_without_explicit_metadata(self):
        prompt = "What is 7 times 8?"
        with tempfile.TemporaryDirectory() as temporary:
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), prompt)
        self.assertEqual(args.task_type, "question")
        self.assertEqual(args.operation, "answer")
        self.assertLessEqual(args.complexity_score, 24)
        self.assertEqual(args.complexity_band, "small")

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

    def test_explicit_latency_source_graph_overrides_mislabeled_easy_complexity(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "easy"
            (args.workdir / "a.py").write_text("A = 1\n", encoding="utf-8")
            (args.workdir / "b.py").write_text("B = 2\n", encoding="utf-8")
            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module, "_run_scheduled_graph", return_value={"status": "pass"}) as scheduled:
                result = module.run(args, "Audit independent a.py, b.py. Read-only, no edits. Must run in parallel for latency.")
        self.assertEqual(result["status"], "pass")
        scheduled.assert_called_once()
        self.assertEqual(scheduled.call_args.args[0].code_rule_bundle["execution_domain"], "python")

    def test_scheduled_graph_releases_every_result_before_emitting_ending_ready(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = self.arguments(root)
            args.resolved_entry_model = "gpt-5.6-sol"
            args.resolved_entry_effort = "ultra"
            args.resolved_entry_source = "explicit"
            args.result_output.write_text("MERGED RESULT", encoding="utf-8")
            branch_receipt = root / "branch-receipt.json"
            main_receipt = root / "main-receipt.json"
            receipt = {"status": "pass", "result_published": True, "turn_completed": True, "node_type": "locked-route-node", "node_role": "result-producer", "tokens": {"total_tokens": 4}, "route_attempts": []}
            branch_receipt.write_text(json.dumps(receipt), encoding="utf-8")
            main_receipt.write_text(json.dumps(receipt), encoding="utf-8")
            handoff_path = root / "ending-handoff.json"
            handoff = {
                "schema_version": 2,
                "route_run_id": "graph-final",
                "cache_dir": str(root / "Cache" / "tmp-task-analyze"),
                "plan": {"nodes": [{"id": "branch", "phase": "result"}, {"id": "merge", "phase": "result"}]},
                "completed": [
                    {"id": "branch", "status": "pass", "phase": "result", "receipt_path": str(branch_receipt), "result_path": str(root / "branch-result.md")},
                    {"id": "merge", "status": "pass", "phase": "result", "receipt_path": str(main_receipt), "result_path": str(args.result_output)},
                ],
                "main_result_node": "merge",
                "ending_handoff_path": str(handoff_path),
            }
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            plan = {
                "main_result_node": "merge",
                "schedule_mode": "parallel_independent_sources",
                "parallel_branch_count": 1,
                "fused_source": None,
                "nodes": [
                    {"id": "branch", "phase": "result", "model": "gpt-5.6-terra", "effort": "medium", "dependencies": []},
                    {"id": "merge", "phase": "result", "model": "gpt-5.6-terra", "effort": "medium", "dependencies": ["branch"]},
                ],
            }
            manifest = {
                "status": "pass",
                "route_run_id": "graph-final",
                "manifest_path": str(root / "manifest.json"),
                "ending_handoff_path": str(handoff_path),
                "first_result_elapsed_ms": 12,
                "nodes": [
                    {"id": "branch", "phase": "result", "receipt_path": str(branch_receipt), "requested_model": "gpt-5.6-terra", "requested_effort": "medium", "model": "gpt-5.6-terra", "effort": "medium", "tokens": {"total_tokens": 4}},
                    {"id": "merge", "phase": "result", "receipt_path": str(main_receipt), "requested_model": "gpt-5.6-terra", "requested_effort": "medium", "model": "gpt-5.6-terra", "effort": "medium", "tokens": {"total_tokens": 4}},
                ],
            }
            with patch.object(module, "_scheduled_plan", return_value=(plan, recommendation())), patch.object(module.task_route_dispatcher, "run_plan", return_value=manifest):
                summary = module._run_scheduled_graph(args, "Audit both sources", ["a.py", "b.py"], recommendation(), time.monotonic_ns(), {"admitted": True})
            outer_receipt = json.loads(args.receipt_output.read_text(encoding="utf-8"))
            release_exists = Path(summary["aggregate_result_release_path"]).is_file()
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["ending_launch_ready"])
        self.assertTrue(outer_receipt["final_aggregate_receipt"])
        self.assertTrue(outer_receipt["all_result_nodes_settled"])
        self.assertTrue(outer_receipt["subprocesses_settled"])
        self.assertEqual(outer_receipt["aggregate_result_state"], "released")
        self.assertTrue(release_exists)

    def test_schedule_admission_prefers_one_producer_for_small_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = ["a.py", "b.py", "c.py"]
            for source in sources:
                (root / source).write_text("VALUE = 1\n", encoding="utf-8")
            decision = module.schedule_admission("Audit independent a.py, b.py, c.py. Read-only, no edits.", root, sources)
        self.assertFalse(decision["admitted"])
        self.assertEqual(decision["decision"], "single_adaptive_producer")
        self.assertEqual(decision["reason"], "single_producer_lower_estimated_logical_tokens")
        self.assertLess(decision["estimated_single_input_tokens"], decision["estimated_scheduled_input_tokens"])

    def test_schedule_admission_uses_graph_for_context_pressure_or_explicit_latency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = ["a.py", "b.py", "c.py"]
            for source in sources:
                (root / source).write_text("X" * 70000, encoding="utf-8")
            pressure = module.schedule_admission("Audit independent a.py, b.py, c.py. Read-only, no edits.", root, sources)
            for source in sources:
                (root / source).write_text("X", encoding="utf-8")
            latency = module.schedule_admission("Audit independent a.py, b.py, c.py. Read-only, no edits. Parallel is required for latency-critical delivery.", root, sources)
        self.assertTrue(pressure["admitted"])
        self.assertEqual(pressure["reason"], "single_producer_context_budget_exceeded")
        self.assertTrue(latency["admitted"])
        self.assertEqual(latency["reason"], "explicit_parallel_latency_contract")

    def test_scheduled_plan_uses_parallel_priority_branches_and_adaptive_merge(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "complex"
            (args.workdir / "a.py").write_text("A = 1\n", encoding="utf-8")
            (args.workdir / "b.py").write_text("B = 2\n", encoding="utf-8")
            proof = {"selected_pair": "gpt-5.6-terra|medium", "attempt_pair": "gpt-5.6-terra|medium", "active_fallback_pair": "gpt-5.6-terra|high", "trial": False, "reason": "shared_cold_start", "profile_fingerprint": "fingerprint", "calibration_state": "cold_start", "best_pair": None, "selection_basis": "shared_cold_start"}
            adaptive = {"selected_pair": "gpt-5.6-terra|medium", "trial": False}
            with patch.object(module.task_route_dispatcher, "_obsidian_recommendation_and_proof", return_value=(adaptive, proof)):
                plan, merge_recommendation = module._scheduled_plan(
                    args,
                    "Complete two independent source audits. Do not edit files.\n- a.py\n- b.py",
                    ["a.py", "b.py"],
                    "gpt-5.6-sol",
                    "ultra",
                    recommendation(),
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
        self.assertEqual(result_nodes[-1]["routing_recommendation"]["attempt_pair"], "gpt-5.6-terra|medium")
        ending = next(node for node in plan["nodes"] if node["phase"] == "ending")
        self.assertEqual({field: ending[field] for field in ("model", "effort", "selection_basis", "allow_fallback", "fallback_policy")}, module.task_route_dispatcher.ending_fast_route_fields())
        self.assertEqual(merge_recommendation, adaptive)

    def test_exact_owned_three_source_schedule_fuses_final_source_with_merge(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "complex"
            sources = ["a.py", "b.py", "c.py"]
            for source in sources:
                (args.workdir / source).write_text(f"VALUE = {source!r}\n", encoding="utf-8")
            prompt = """Complete three independent read-only source audits. Do not edit files.
a.py
b.py
c.py
Return one minified JSON object.

alpha is owned only by a.py
- value: exact assignment

beta is owned only by b.py
- value: exact assignment

gamma is owned only by c.py
- value: exact assignment

source_files must list all sources in order."""
            proof = {"selected_pair": "gpt-5.6-terra|medium", "attempt_pair": "gpt-5.6-terra|medium", "active_fallback_pair": "gpt-5.6-terra|high", "trial": False, "reason": "shared_cold_start", "profile_fingerprint": "fingerprint", "calibration_state": "cold_start", "best_pair": None, "selection_basis": "shared_cold_start"}
            adaptive = {"selected_pair": "gpt-5.6-terra|medium", "trial": False}
            with patch.object(module.task_route_dispatcher, "_obsidian_recommendation_and_proof", return_value=(adaptive, proof)):
                plan, _ = module._scheduled_plan(args, prompt, sources, "gpt-5.6-sol", "ultra", recommendation())
        result_nodes = [node for node in plan["nodes"] if node["phase"] == "result"]
        self.assertEqual(plan["topology"], "mixed")
        self.assertEqual(plan["schedule_mode"], "parallel_sources_fused_final")
        self.assertEqual(plan["parallel_branch_count"], 2)
        self.assertEqual(plan["fused_source"], "c.py")
        self.assertEqual(len(result_nodes), 3)
        self.assertEqual([node["source_allowlist"] for node in result_nodes], [["a.py"], ["b.py"], ["c.py"]])
        self.assertEqual([(node["model"], node["effort"]) for node in result_nodes[:-1]], [("gpt-5.6-luna", "low"), ("gpt-5.6-luna", "low")])
        self.assertTrue(all("priority_producer" not in node for node in result_nodes[:-1]))
        self.assertEqual(result_nodes[-1]["dependencies"], ["source-1", "source-2"])
        self.assertTrue(result_nodes[-1]["fuses_owned_source_with_dependencies"])
        self.assertNotIn("reads_dependency_results_only", result_nodes[-1])
        self.assertIn("Dependency results own every other section", result_nodes[-1]["prompt"])
        self.assertEqual((result_nodes[-1]["model"], result_nodes[-1]["effort"]), ("gpt-5.6-terra", "medium"))

    def test_small_exact_owned_sources_use_parallel_local_capture_and_one_model_synthesis(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity = "complex"
            sources = ["a.py", "b.py", "c.json"]
            for source in sources:
                (args.workdir / source).write_text(f"VALUE = {source!r}\n", encoding="utf-8")
            prompt = """Complete three independent read-only source audits. Do not edit files.
a.py
b.py
c.json
Return exactly one single-line minified JSON object.

alpha is owned only by a.py
- alpha

beta is owned only by b.py
- beta

gamma is owned only by c.json
- gamma

source_files must list all sources in order."""
            proof = {"selected_pair": "gpt-5.6-luna|low", "attempt_pair": "gpt-5.6-luna|low", "active_fallback_pair": None, "trial": False, "reason": "local_history", "profile_fingerprint": "fingerprint", "calibration_state": "frozen", "best_pair": "gpt-5.6-luna|low", "selection_basis": "local_history"}
            adaptive = {"selected_pair": "gpt-5.6-luna|low", "trial": False}
            with patch.object(module.task_route_dispatcher, "_obsidian_recommendation_and_proof", return_value=(adaptive, proof)):
                plan = module._scheduled_plan(args, prompt, sources, "gpt-5.6-sol", "ultra", recommendation())[0]
        result_nodes = [node for node in plan["nodes"] if node["phase"] == "result"]
        captures = result_nodes[:-1]
        merge = result_nodes[-1]
        self.assertEqual(plan["schedule_mode"], "parallel_source_capture_single_synthesis")
        self.assertTrue(plan["deterministic_source_capture"])
        self.assertEqual(plan["parallel_branch_count"], 3)
        self.assertEqual([node["execution_kind"] for node in captures], [module.task_route_dispatcher.DETERMINISTIC_SOURCE_READ] * 3)
        self.assertEqual([node["source_allowlist"] for node in captures], [["a.py"], ["b.py"], ["c.json"]])
        self.assertTrue(all(node["model"] is None and node["effort"] is None for node in captures))
        self.assertEqual(merge["dependencies"], ["source-1", "source-2", "source-3"])
        self.assertTrue(merge["reads_dependency_results_only"])
        self.assertEqual(merge["routing_project_root"], str(Path(args.project_root).resolve()))
        self.assertEqual((merge["model"], merge["effort"]), ("gpt-5.6-luna", "low"))

    def test_large_exact_owned_sources_keep_model_source_audit_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = ["a.py", "b.py"]
            for source in sources:
                (root / source).write_text("X" * (module.DETERMINISTIC_CAPTURE_SOURCE_BYTE_LIMIT + 1), encoding="utf-8")
            prompt = """Return exactly one single-line minified JSON object.
alpha is owned only by a.py
- alpha
beta is owned only by b.py
- beta
source_files must list all sources in order."""
            eligible = module._deterministic_capture_eligible(prompt, root, sources)
        self.assertFalse(eligible)

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

    def test_fast_path_classifies_read_only_source_audit_as_question(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = module.resolve_fast_path_args(module.parse_args(["--workdir", temporary]), "Audit independent a.py and b.py. Read-only, no edits.")
        self.assertEqual(args.task_type, "question")

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

    def test_zero_argument_multi_stage_task_requires_dynamic_graph_before_any_model_execution(self):
        prompt = "查看近期代码任务并模拟重放；如果 Skill 没触发就更改规则，测试后部署并提交。"
        with tempfile.TemporaryDirectory() as temporary:
            workdir = Path(temporary)
            stream = io.StringIO()
            with patch.object(module.Path, "cwd", return_value=workdir), patch.object(module.sys, "stdin", io.StringIO(prompt)), patch.object(module.sys, "stdout", stream), patch.object(module, "run") as execute:
                status = module.main([])
        summary = json.loads(stream.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(summary["status"], "route-required")
        self.assertEqual(summary["routing_mode"], module.task_route_dispatcher.DYNAMIC_ROUTING_MODE)
        self.assertEqual(summary["parent_action"], "build_dynamic_task_graph_and_call_task_route_dispatcher_once")
        self.assertEqual(summary["execution_lifecycle"]["mode"], "planned_graph")
        self.assertTrue(summary["code_gate_required"])
        self.assertFalse(summary["runner_executed"])
        execute.assert_not_called()

    def test_explicit_already_decomposed_node_does_not_reenter_graph_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arguments = ["--project-root", str(root), "--task-type", "code", "--module", "task-analyze-skill", "--workload-id", "repair-node", "--receipt-output", str(root / "receipt.json"), "--result-output", str(root / "result.txt"), "--workdir", str(root)]
            args = module.resolve_fast_path_args(module.parse_args(arguments), "Fix the classifier, test it, deploy it, and commit it.")
        self.assertFalse(args.graph_required)
        self.assertEqual(args.material_result_stages, ["change", "test", "deploy", "publish"])

    def test_main_emits_ending_required_event_before_the_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            summary = {"status": "pass", "ending_required": True, "ending_launch_ready": True, "final_aggregate_receipt": True, "aggregate_result_state": "released", "ending_real_status": "missing_expected_non_simple", "complexity_score": 25, "complexity_band": "standard", "receipt_path": str(args.receipt_output), "result_path": str(args.result_output)}
            stream = io.StringIO()
            with patch.object(module.sys, "stdin", io.StringIO("Repair the lifecycle")), patch.object(module.sys, "stdout", stream), patch.object(module, "resolve_fast_path_args", return_value=args), patch.object(module, "run", return_value=summary):
                status = module.main([])
        events = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(status, 0)
        self.assertEqual(events[0]["stage"], "ending-required")
        self.assertEqual(events[0]["parent_action"], "create_projectless_end_task")
        self.assertEqual(events[0]["launch_state"], "required_unacknowledged")
        self.assertEqual(events[0]["host_tool"], "codex_app__create_thread")
        self.assertEqual(events[0]["thread_target"], {"type": "projectless"})
        self.assertEqual(events[0]["placement_readback_tool"], "codex_app__list_threads")
        self.assertTrue(events[0]["ack_required"])
        self.assertTrue(events[0]["final_aggregate_receipt"])
        self.assertEqual(events[0]["aggregate_result_state"], "released")
        self.assertEqual(events[1], summary)

    def test_main_waits_when_a_child_or_subprocess_receipt_is_not_final(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            summary = {"status": "pass", "ending_required": True, "ending_launch_ready": False, "ending_real_status": "missing_expected_non_simple", "receipt_path": str(args.receipt_output), "result_path": str(args.result_output)}
            stream = io.StringIO()
            with patch.object(module.sys, "stdin", io.StringIO("Wait for all results")), patch.object(module.sys, "stdout", stream), patch.object(module, "resolve_fast_path_args", return_value=args), patch.object(module, "run", return_value=summary):
                status = module.main([])
        events = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(status, 0)
        self.assertEqual(events, [summary])

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
        expected_fields = {"project_root", "task_type", "module", "file", "symbol", "code_kind", "operation", "modality", "complexity", "complexity_score", "complexity_band", "risk", "ambiguity", "task_name", "task_group", "task_scope_key", "task_group_key", "codex_session_key", "task_summary", "step_kind", "capability_tags", "capability_fingerprint", "entry_model", "entry_effort", "entry_pair", "entry_source"}
        self.assertEqual(set(result["model_learning_context"]), expected_fields)
        self.assertEqual(receipt["model_learning_context"], result["model_learning_context"])
        self.assertEqual(result["model_learning_context"]["task_summary"], "Edit one method. Keep behavior stable.")
        self.assertEqual(result["model_learning_context"]["step_kind"], "implementation")
        self.assertRegex(result["model_learning_context"]["capability_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertEqual(receipt["entry_pair"], "gpt-5.6-sol|ultra")
        self.assertNotIn("SECRET RAW PROMPT", json.dumps(receipt))
        self.assertNotIn("SECRET RAW PROMPT", json.dumps(result))

    def test_receipt_args_use_an_exact_supported_route_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            receipt_args = module._receipt_args(args, ("gpt-5.3-codex-spark", "low"))
        self.assertEqual(receipt_args.route_marker, "LOCKED_ROUTE_NODE")
        self.assertIn(receipt_args.route_marker, module.model_execution_receipt.ROUTE_MARKERS)

    def test_small_and_standard_non_code_leaf_use_minimal_context_without_changing_code_or_complex_routes(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.ignore_user_config = False
            args.task_type = "analysis"
            args.code_rule_bundle = None
            small = module._receipt_args(args, ("gpt-5.6-luna", "low"))
            args.complexity_score = 42
            standard = module._receipt_args(args, ("gpt-5.6-luna", "low"))
            args.complexity_score = 68
            complex_route = module._receipt_args(args, ("gpt-5.6-luna", "low"))
            args.complexity_score = 18
            args.task_type = "code"
            args.code_rule_bundle = {"schema_version": 1}
            code = module._receipt_args(args, ("gpt-5.6-luna", "low"))
        self.assertTrue(small.minimal_context_mode)
        self.assertTrue(small.ignore_user_config)
        self.assertTrue(standard.minimal_context_mode)
        self.assertTrue(standard.ignore_user_config)
        self.assertFalse(complex_route.minimal_context_mode)
        self.assertFalse(complex_route.ignore_user_config)
        self.assertFalse(code.minimal_context_mode)
        self.assertFalse(code.ignore_user_config)

    def test_lean_context_requires_tiny_generic_immutable_exact_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.task_type = "analysis"
            args.code_kind = "general"
            args.operation = "analyze"
            args.modality = "text"
            args.complexity_score = 18
            args.risk = "low"
            args.ambiguity = "low"
            args.code_rule_bundle = None
            (args.workdir / "a.json").write_text('{"value":1}', encoding="utf-8")
            (args.workdir / "b.json").write_text('{"value":2}', encoding="utf-8")
            prompt = "Analyze only `a.json` and `b.json`; the files are immutable. Return exactly one single-line minified JSON object."
            self.assertTrue(module._lean_context_eligible(args, prompt))
            self.assertFalse(module._lean_context_eligible(args, prompt, admitted_schedule=True))
            args.task_type = "code"
            self.assertFalse(module._lean_context_eligible(args, prompt))

    def test_lean_context_rejects_large_or_non_exact_source_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.task_type = "analysis"
            args.modality = "text"
            args.complexity_score = 18
            args.risk = "low"
            args.ambiguity = "low"
            args.code_rule_bundle = None
            (args.workdir / "large.json").write_text("x" * (module.DETERMINISTIC_CAPTURE_SOURCE_BYTE_LIMIT + 1), encoding="utf-8")
            exact = "Read only `large.json`; do not edit files. Return exactly one single-line minified JSON object."
            prose = "Read only `large.json`; do not edit files. Return a prose summary."
            self.assertFalse(module._lean_context_eligible(args, exact))
            self.assertFalse(module._lean_context_eligible(args, prose))

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
        self.assertTrue(result["result"].startswith("Complexity: 12/100 (small) · Model: gpt-5.6-terra|medium · Route: no switch\nEvidence: runtime receipt"))
        self.assertTrue(result["result"].endswith("COLD START RESULT"))
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

    def test_selected_pair_pre_execution_failure_falls_back_once_to_stronger_pair(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            calls = []

            def fake_run(receipt_args, prompt):
                pair = f"{receipt_args.model}|{receipt_args.effort}"
                calls.append(pair)
                if pair == "gpt-5.6-terra|medium":
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

            adaptive = recommendation()
            with patch.object(module, "_recommend", return_value=adaptive), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
            receipt = __import__("json").loads(args.receipt_output.read_text(encoding="utf-8"))
        self.assertEqual(calls, ["gpt-5.6-terra|medium", "gpt-5.6-terra|high"])
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["result"].startswith("Complexity: 12/100 (small) · Model: gpt-5.6-terra|high · Route: fallback"))
        self.assertIn("Model path: gpt-5.6-terra|medium -> gpt-5.6-terra|high", result["result"])
        self.assertTrue(result["result"].endswith("FALLBACK RESULT"))
        self.assertEqual(receipt["operational_failure_pairs"], ["gpt-5.6-terra|medium"])
        self.assertEqual(len(receipt["route_attempts"]), 2)

    def test_selected_pair_confirmed_rate_limit_with_null_telemetry_falls_back_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            calls = []

            def fake_run(receipt_args, prompt):
                pair = f"{receipt_args.model}|{receipt_args.effort}"
                calls.append(pair)
                if len(calls) == 1:
                    return {
                        "status": "fail",
                        "failure_class": "availability",
                        "failure_detail": "rate_limited",
                        "requested_pair": pair,
                        "resolved_model": receipt_args.model,
                        "resolved_pair": pair,
                        "effective_model": receipt_args.model,
                        "effective_pair": pair,
                        "availability": {"has_credits": False},
                        "turn_completed": False,
                        "result_published": False,
                        "tokens": {"input_tokens": None, "output_tokens": None, "total_tokens": None},
                        "process_elapsed_ms": 2,
                        "route_attempts": [{"requested_pair": pair, "resolved_pair": pair, "effective_pair": pair, "tokens": {"total_tokens": None}}],
                    }
                receipt_args.result_output.write_text("LIMIT FALLBACK RESULT", encoding="utf-8")
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

            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
            receipt = json.loads(args.receipt_output.read_text(encoding="utf-8"))
        self.assertEqual(calls, ["gpt-5.6-terra|medium", "gpt-5.6-terra|high"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(receipt["operational_failure_pairs"], ["gpt-5.6-terra|medium"])
        self.assertEqual(len(receipt["route_attempts"]), 2)

    def test_small_code_result_returns_after_quick_check_and_requires_detached_ending(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            calls = []

            def fake_run(receipt_args, prompt):
                pair = f"{receipt_args.model}|{receipt_args.effort}"
                calls.append(pair)
                receipt_args.result_output.write_text("ADAPTIVE RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": pair, "effective_pair": pair, "turn_completed": True, "model_match": True, "effort_match": True, "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 3, "tokens": {"total_tokens": 9}, "route_attempts": [{"requested_pair": pair, "effective_pair": pair, "tokens": {"total_tokens": 9}}]}

            adaptive = recommendation()
            with patch.object(module, "_recommend", return_value=adaptive), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the work")
        self.assertEqual(calls, ["gpt-5.6-terra|medium"])
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["ending_required"])
        self.assertEqual(result["ending_requirement"], "required")
        self.assertEqual(result["ending_real_status"], "missing_expected_code_ending")
        self.assertEqual(result["producer_check_scope"], "one_smallest_local_quick_check")
        self.assertEqual(result["first_result_release"], "immediate_after_quick_check")
        self.assertEqual(result["deferred_verification_owner"], "projectless_ending")

    def test_result_lifecycle_policy_replays_sanitized_today_task_classes(self):
        cases = [
            ("remove-debug-log", "code", 8, "low", False, "", True),
            ("local-model-route", "code", 18, "low", False, "", True),
            ("global-skill-flow", "code", 35, "low", True, "", True),
            ("file-copy", "question", 30, "low", False, "", False),
            ("git-release", "question", 60, "medium", True, "Update the release information.", True),
            ("read-only-monitor", "question", 12, "low", False, "Read the current monitor state.", False),
            ("calendar-ui", "question", 35, "medium", False, "Visually verify the calendar UI.", True),
            ("visual-artifact", "question", 45, "medium", False, "Review the rendered visual artifact.", True),
        ]
        for name, task_type, score, risk, multi_stage, prompt, expected_ending in cases:
            with self.subTest(name=name):
                policy = module.result_lifecycle_policy(True, task_type, score, risk, multi_stage, prompt)
                self.assertEqual(policy["ending_required"], expected_ending)
                self.assertEqual(policy["first_result_release"], "immediate_after_quick_check")
                self.assertEqual(policy["deferred_verification_owner"], "projectless_ending" if expected_ending else "none")

    def test_ending_skips_complex_plain_answer_without_real_surface(self):
        policy = module.result_lifecycle_policy(True, "question", 85, "high", True, "Explain the difference between two terms.")
        self.assertFalse(policy["ending_required"])
        self.assertEqual(policy["ending_requirement"], "no_real_ending_surface")
        self.assertEqual(policy["ending_real_status"], "intentionally_skipped_simple_task")
        self.assertEqual(policy["ending_skip_reason"], "no_real_test_or_information_or_memory_or_material_update")
        self.assertEqual(policy["ending_surface"], {"real_test": False, "information_update": False, "memory_update": False})

    def test_ending_requires_explicit_information_or_memory_surface(self):
        information = module.result_lifecycle_policy(True, "question", 85, "low", True, "Update the project documentation.")
        memory = module.result_lifecycle_policy(True, "question", 85, "low", True, "Record this decision in project memory.")
        self.assertEqual(information["ending_triggers"], ["information_update"])
        self.assertIn("memory_update", memory["ending_triggers"])
        self.assertTrue(information["ending_required"])
        self.assertTrue(memory["ending_required"])

    def test_explicit_real_test_surface_overrides_plain_task_type(self):
        policy = module.result_lifecycle_policy(True, "question", 10, "low", False, "Answer briefly.", real_test=True)
        self.assertTrue(policy["ending_required"])
        self.assertEqual(policy["ending_triggers"], ["real_test"])

    def test_material_updates_require_ending_and_memory_closeout_but_explicit_trivial_value_only_may_skip(self):
        for prompt, expected in (("Refactor the structural lifecycle owner.", "structural"), ("Implement the requested code change.", "code"), ("Update the conceptual design.", "conceptual"), ("Update the workflow process.", "process")):
            with self.subTest(prompt=prompt):
                policy = module.result_lifecycle_policy(True, "code" if "code" in prompt or "Refactor" in prompt else "question", 12, "low", False, prompt)
                self.assertTrue(policy["ending_required"])
                self.assertIn("material_update", policy["ending_triggers"])
                self.assertEqual(policy["material_update_classification"], expected)
                self.assertTrue(policy["project_memory_closeout_required"])
        trivial = module.result_lifecycle_policy(True, "question", 12, "low", False, "Make a trivial value-only edit.")
        self.assertFalse(trivial["ending_required"])
        self.assertEqual(trivial["material_update_classification"], "trivial_value_only")
        self.assertFalse(trivial["project_memory_closeout_required"])
        explicit = module.result_lifecycle_policy(True, "question", 12, "low", False, "Small text.", material_update_kind="structural")
        self.assertTrue(explicit["ending_required"])
        self.assertTrue(explicit["project_memory_closeout_required"])
        self.assertEqual(explicit["material_update_classification"], "structural")

    def test_fast_path_default_producer_timeout_is_five_minutes(self):
        self.assertEqual(module.parse_args([]).timeout, 300)

    def test_non_simple_result_requires_an_ending_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.arguments(Path(temporary))
            args.complexity_score = 25

            def fake_run(receipt_args, prompt):
                receipt_args.result_output.write_text("STANDARD RESULT", encoding="utf-8")
                return {"status": "pass", "requested_pair": "gpt-5.6-terra|medium", "effective_pair": "gpt-5.6-terra|medium", "result_published": True, "turn_completed": True, "model_match": True, "effort_match": True, "result_ready_monotonic_ns": time.monotonic_ns(), "process_elapsed_ms": 3, "tokens": {"total_tokens": 9}}

            with patch.object(module, "_recommend", return_value=recommendation()), patch.object(module.model_execution_receipt, "run_receipt", side_effect=fake_run):
                result = module.run(args, "Do the standard work")
            receipt = json.loads(args.receipt_output.read_text(encoding="utf-8"))
        self.assertTrue(result["ending_required"])
        self.assertEqual(result["ending_requirement"], "required")
        self.assertEqual(result["ending_real_status"], "missing_expected_non_simple")
        self.assertTrue(receipt["ending_required"])
        self.assertEqual(receipt["ending_real_status"], "missing_expected_non_simple")
        self.assertTrue(receipt["final_aggregate_receipt"])
        self.assertTrue(receipt["ending_launch_ready"])
        self.assertEqual(receipt["aggregate_result_state"], "single_result_released")


if __name__ == "__main__":
    unittest.main()

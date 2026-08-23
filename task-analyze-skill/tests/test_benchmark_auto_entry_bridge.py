#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_auto_entry_bridge.py"
MODULE_SPEC = importlib.util.spec_from_file_location("benchmark_auto_entry_bridge", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class BenchmarkAutoEntryBridgeTests(unittest.TestCase):
    def test_bridge_binds_prompt_invokes_adaptive_runner_and_emits_plain_object(self):
        prompt = "bounded benchmark workload\nComplexity score: 18.\n"
        child_result = "Complexity: 18/100 (small) · Model: gpt-5.3-codex-spark|low · Route: downgrade\nModel path: gpt-5.6-luna|max -> gpt-5.3-codex-spark|low\nEvidence: runtime receipt\n\n{\"b\":2,\"a\":1}"
        ready_event = json.dumps({"schema_version": 1, "stage": "result-ready"}, separators=(",", ":"))
        summary = ready_event + "\n" + json.dumps({"status": "pass", "result": child_result}, separators=(",", ":")) + "\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "input.json").write_text('{"ok":true}\n', encoding="utf-8")
            codex_home = root / "home"
            prompt_path = root / "prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            adaptive_runner = codex_home / "skills" / "task-analyze-skill" / "scripts" / "obsidian_adaptive_model_runner.py"
            adaptive_runner.parent.mkdir(parents=True)
            adaptive_runner.write_text("# runner\n", encoding="utf-8")
            args = argparse.Namespace(prompt_file=prompt_path, workdir=source)
            environment = {
                "CODEX_HOME": str(codex_home),
                module.PROMPT_PATH_ENV: str(prompt_path),
                module.PROMPT_SHA256_ENV: hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                module.CODEX_BIN_ENV: "codex-test",
                module.CHILD_TIMEOUT_ENV: "120",
                module.CACHE_ROOT_ENV: str(root / "Cache" / "bridge"),
                module.PYTHON_ENV: str(Path(module.sys.executable).resolve()),
                module.ENTRY_MODEL_ENV: "gpt-5.6-luna",
                module.ENTRY_EFFORT_ENV: "max",
                module.TASK_SANDBOX_ENV: "read-only",
            }
            execution = {"schema_version": 2, "receipt_sha256": "a" * 64, "selected_pair": "gpt-5.6-sol|ultra", "effective_pair": "gpt-5.6-sol|ultra", "steady_state_logical_tokens": 12, "steady_state_execution_elapsed_ms": 5, "calibration_attempt_count": 0, "calibration_failure_elapsed_ms": 0, "calibration_failure_logical_tokens": 0, "route_signature": {"selected_pair": "gpt-5.6-sol|ultra", "effective_pair": "gpt-5.6-sol|ultra", "scheduled_graph": False, "assigned_pairs": ["gpt-5.6-sol|ultra"], "trial": False, "recommendation_state": "frozen", "selection_provenance": "local_history", "capability_assignment": [{"node_id": "result", "effective_pair": "gpt-5.6-sol|ultra"}]}}
            with patch.dict(os.environ, environment, clear=False), patch.object(module, "run_adaptive_entry", return_value=({"b": 2, "a": 1}, execution)) as run_mock:
                result = module.run_bridge(args)
        self.assertEqual(result, {"b": 2, "a": 1})
        self.assertEqual(run_mock.call_count, 1)
        self.assertEqual(run_mock.call_args_list[0].args[1], ("gpt-5.6-luna", "max"))
        self.assertEqual(run_mock.call_args_list[0].args[2], "read-only")

    def test_bridge_rejects_prompt_hash_drift_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt_path = root / "prompt.txt"
            prompt_path.write_text("prompt", encoding="utf-8")
            environment = {module.PROMPT_PATH_ENV: str(prompt_path), module.PROMPT_SHA256_ENV: "0" * 64}
            with patch.dict(os.environ, environment, clear=False), self.assertRaisesRegex(ValueError, "hash"):
                module.validated_prompt(prompt_path)

    def test_bridge_rejects_an_interpreter_that_differs_from_its_binding(self):
        prompt = "bounded benchmark workload\nComplexity score: 18.\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt_path = root / "prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            environment = {
                "CODEX_HOME": str(root),
                module.PROMPT_PATH_ENV: str(prompt_path),
                module.PROMPT_SHA256_ENV: hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                module.PYTHON_ENV: str(prompt_path),
            }
            with patch.dict(os.environ, environment, clear=False), self.assertRaisesRegex(ValueError, "interpreter"):
                module.run_bridge(argparse.Namespace(prompt_file=prompt_path, workdir=root))

    def test_bridge_requires_passing_summary_and_json_result(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            module.extract_result_document("[]")
        with self.assertRaisesRegex(ValueError, "no result payload"):
            module.extract_result_document("Complexity: 18/100 (small) · Model: x|y · Route: no switch\nEvidence: runtime receipt")

    def test_bridge_requires_one_valid_complexity_score(self):
        self.assertEqual(module.benchmark_complexity_score("Complexity score: 68."), 68)
        with self.assertRaisesRegex(ValueError, "one complexity score"):
            module.benchmark_complexity_score("no score")
        with self.assertRaisesRegex(ValueError, "invalid"):
            module.benchmark_complexity_score("Complexity score: 101.")

    def test_receipt_projection_discloses_bounded_context_mode(self):
        receipt = {
            "status": "pass",
            "metrics_complete": True,
            "result_published": True,
            "trial": False,
            "recommendation_state": "frozen",
            "selection_provenance": "local_history",
            "selected_pair": "gpt-5.6-luna|low",
            "effective_pair": "gpt-5.6-luna|low",
            "process_elapsed_ms": 7,
            "tokens": {"total_tokens": 11},
            "route_attempts": [{"status": "pass"}],
            "reroutes": [],
            "node_role": "result-producer",
            "lean_context_mode": "active",
            "capability_assignment": [{"node_id": "result", "effective_pair": "gpt-5.6-luna|low"}],
        }
        projection = module.receipt_projection(receipt)
        self.assertEqual(projection["route_signature"]["context_mode"], "lean_bounded_worker")
        receipt["lean_context_mode"] = "not_requested"
        self.assertEqual(module.receipt_projection(receipt)["route_signature"]["context_mode"], "full")

    def test_adaptive_entry_removes_parent_session_scope_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_root = root / "output"
            output_root.mkdir()
            (output_root / "receipt.json").write_text("{}\n", encoding="utf-8")
            process = SimpleNamespace(returncode=0, stdout=json.dumps({"status": "pass", "result": '{"ok":true}'}) + "\n")
            projection = {
                "selected_pair": "gpt-5.6-luna|low",
                "route_signature": {"selected_pair": "gpt-5.6-luna|low"},
            }
            environment = {
                "CODEX_THREAD_ID": "parent-thread",
                "CODEX_SESSION_ID": "parent-session",
                "BENCHMARK_ENV_MARKER": "preserved",
            }
            with patch.dict(os.environ, environment, clear=False), patch.object(module.subprocess, "run", return_value=process) as run_mock, patch.object(module, "receipt_projection", return_value=projection):
                result, execution = module.run_adaptive_entry(root / "runner.py", ("gpt-5.6-luna", "max"), "read-only", root / "source", root / "workspace", root / "runtime", output_root, 18, "codex-test", 120, "prompt")
        command_environment = run_mock.call_args.kwargs["env"]
        self.assertNotIn("CODEX_THREAD_ID", command_environment)
        self.assertNotIn("CODEX_SESSION_ID", command_environment)
        self.assertEqual(command_environment["BENCHMARK_ENV_MARKER"], "preserved")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(execution, projection)

    def test_adaptive_entry_classifies_failure_without_leaking_raw_reason(self):
        process = SimpleNamespace(returncode=1, stdout=json.dumps({"status": "fail", "reason": "Operation not permitted: /private/path"}) + "\n", stderr="private detail")
        with tempfile.TemporaryDirectory() as temporary, patch.object(module.subprocess, "run", return_value=process):
            root = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "adaptive runner failed: runner_permission_denied") as raised:
                module.run_adaptive_entry(root / "runner.py", ("gpt-5.6-luna", "max"), "read-only", root / "source", root / "workspace", root / "runtime", root / "output", 18, "codex-test", 120, "prompt")
        self.assertNotIn("private", str(raised.exception))

    def test_adaptive_failure_classifies_routing_memory_permission_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            memory_path = Path(temporary) / "memories" / "routing.jsonl"
            denied_path = memory_path.parent / ".routing.lock"
            process = SimpleNamespace(returncode=1, stdout=json.dumps({"status": "fail", "reason": f"[Errno 1] Operation not permitted: '{denied_path}'"}) + "\n", stderr="")
            with patch.dict(os.environ, {"CODEX_MODEL_ROUTING_MEMORY": str(memory_path)}, clear=False):
                self.assertEqual(module.adaptive_runner_failure_code(process), "runner_memory_permission_denied")

    def test_workspace_copy_is_exact_and_outside_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "input.json").write_text('{"ok":true}\n', encoding="utf-8")
            workspace = module.prepare_read_only_workspace(source, root / "Cache" / "bridge")
            self.assertEqual(module.source_tree_sha256(source), module.source_tree_sha256(workspace))
            self.assertTrue(workspace.is_relative_to((root / "Cache" / "bridge").resolve()))
            with self.assertRaisesRegex(ValueError, "outside"):
                module.prepare_read_only_workspace(source, source / "Cache")

    def test_launch_claim_allows_exactly_one_adaptive_producer(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary) / "Cache" / "bridge"
            claim_path = module.claim_adaptive_launch(cache_root, "a" * 64, ("gpt-5.6-luna", "max"))
            self.assertEqual(
                json.loads(claim_path.read_text(encoding="utf-8")),
                {"schema_version": 3, "workload_sha256": "a" * 64, "entry_pair": "gpt-5.6-luna|max"},
            )
            with self.assertRaisesRegex(ValueError, "already launched"):
                module.claim_adaptive_launch(cache_root, "a" * 64, ("gpt-5.6-luna", "max"))


if __name__ == "__main__":
    unittest.main()

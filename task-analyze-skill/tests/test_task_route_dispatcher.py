#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "task_route_dispatcher.py"
MODULE_SPEC = importlib.util.spec_from_file_location("task_route_dispatcher", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class TaskRouteDispatcherTests(unittest.TestCase):
    def plan(self, cache_dir):
        condition = {"task_family": "direct", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "owning_skill": "workflow-skill", "project_family": "global", "verification_shape": "mini_real"}
        ladder = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-terra|low"]
        return {"schema_version": 1, "complexity": "easy", "topology": "sequential", "cache_dir": str(cache_dir), "entry": {"model": "gpt-5.6-terra", "effort": "low"}, "nodes": [{"id": "direct", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return RESULT=12", "sandbox": "read-only", "routing_condition": condition, "task_summary": "Return a verified direct arithmetic answer for this task.", "candidate_ladder": ladder, "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.3-codex-spark|low", "trial": False}, {"id": "mini-verify", "phase": "mini", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Verify the dependency result equals 12", "sandbox": "read-only"}, {"id": "ending-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["mini-verify"], "prompt": "Run the bounded post-result verification inventory.", "sandbox": "read-only"}], "main_result_node": "direct", "mini_verify_node": "mini-verify"}

    def plan_with_ending_optimization(self, cache_dir):
        condition = {"task_family": "direct", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "owning_skill": "workflow-skill", "project_family": "global", "verification_shape": "mini_real"}
        ladder = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-terra|low"]
        return {
            "schema_version": 1,
            "complexity": "easy",
            "topology": "sequential",
            "cache_dir": str(cache_dir),
            "entry": {"model": "gpt-5.6-terra", "effort": "low"},
            "nodes": [
                {
                    "id": "direct",
                    "phase": "result",
                    "skill": "workflow-skill",
                    "model": "gpt-5.6-luna",
                    "effort": "low",
                    "dependencies": [],
                    "prompt": "Return a base result",
                    "sandbox": "read-only",
                    "routing_condition": condition,
                    "task_summary": "Return a validated result for this task.",
                    "candidate_ladder": ladder,
                    "static_suggestion": "gpt-5.6-luna|low",
                    "hard_floor": "gpt-5.3-codex-spark|low",
                    "trial": False,
                },
                {"id": "optimization", "phase": "ending", "skill": "optimization-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["mini-verify"], "prompt": "Optimize this result independently.", "sandbox": "read-only"},
                {"id": "mini-verify", "phase": "mini", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Verify the dependency result is valid.", "sandbox": "read-only"},
                {
                    "id": "optimization-verify",
                    "phase": "ending",
                    "skill": "verify-skill",
                    "model": "gpt-5.6-luna",
                    "effort": "low",
                    "dependencies": ["mini-verify", "optimization"],
                    "verifies_node": "optimization",
                    "prompt": "Verify optimization output.",
                    "sandbox": "read-only",
                },
                {"id": "real-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["mini-verify"], "prompt": "Run real verify.", "sandbox": "read-only"},
            ],
            "main_result_node": "direct",
            "mini_verify_node": "mini-verify",
        }

    def test_valid_plan_keeps_entry_separate_from_downstream(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])
        self.assertEqual(plan["nodes"][0]["model"], "gpt-5.6-luna")

    def test_plan_rejects_wrong_entry_pair_and_unsafe_sandbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["entry"]["model"] = "gpt-5.6-sol"
            plan["nodes"][0]["sandbox"] = "danger-full-access"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("entry pair" in failure for failure in failures))
        self.assertTrue(any("unsafe automatic sandbox" in failure for failure in failures))

    def test_plan_requires_optimization_node_verifier_with_missing_verifies_node(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan_with_ending_optimization(root / "work" / "cache" / "route")
            plan["nodes"][3].pop("verifies_node")
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(
            any("must have exactly one ending verify-skill verifier targeting it" in failure for failure in failures)
        )

    def test_plan_rejects_optimization_node_with_wrong_verifies_node(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan_with_ending_optimization(root / "work" / "cache" / "route")
            plan["nodes"][3]["verifies_node"] = "missing-target"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("verifies_node must reference an existing node" in failure for failure in failures))

    def test_plan_allows_optimization_node_with_valid_verifies_node(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan_with_ending_optimization(root / "work" / "cache" / "route")
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

    def test_run_plan_executes_result_then_mini_sequentially(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            calls = []
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                calls.append(node["id"])
                result_path = cache_dir / f"{node['id']}-result.md"
                receipt_path = cache_dir / f"{node['id']}-receipt.json"
                result_path.write_text("MINI_VERIFY=PASS\n" if node["phase"] == "mini" else "RESULT=12\n", encoding="utf-8")
                receipt_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "model": node["model"], "effort": node["effort"], "status": "pass", "receipt_path": str(receipt_path), "result_path": str(result_path), "tokens": {}, "process_elapsed_ms": 1}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", return_value={"status": "recorded"}) as record_event:
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(calls, ["direct", "mini-verify"])
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(manifest["entry"], {"model": "gpt-5.6-terra", "effort": "low"})
        self.assertEqual(manifest["ending_nodes_pending"], ["ending-verify"])
        self.assertEqual(record_event.call_args.args[0], str((cache_dir / "direct-receipt.json").resolve()))
        self.assertEqual(record_event.call_args.kwargs["main_result_receipt_path"], str((cache_dir / "direct-receipt.json").resolve()))
        self.assertEqual(manifest["route_run_id"], record_event.call_args.kwargs["route_run_id"])
        self.assertIn("route_run_id", manifest)
        self.assertEqual(record_event.call_args.kwargs["main_node"]["id"], plan.get("main_result_node"))
        self.assertEqual(record_event.call_args.kwargs["verify_level"], "mini")

    def test_run_node_retries_only_operational_failures_with_exact_planned_pairs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            node = {
                "id": "direct",
                "phase": "result",
                "skill": "workflow-skill",
                "model": "gpt-5.3-codex-spark",
                "effort": "low",
                "dependencies": [],
                "prompt": "Return RESULT=12",
                "sandbox": "read-only",
                "allow_fallback": ["gpt-5.6-luna|low", "gpt-5.6-terra|low"],
            }
            plan["nodes"] = [node]
            plan["main_result_node"] = "direct"
            plan["mini_verify_node"] = "direct"
            calls = []

            def fake_run_receipt(_args, _prompt):
                calls.append((_args.model, _args.effort))
                if (_args.model, _args.effort) == ("gpt-5.3-codex-spark", "low"):
                    return {
                        "schema_version": 1,
                        "requested_model": "gpt-5.3-codex-spark",
                        "requested_effort": "low",
                        "requested_pair": "gpt-5.3-codex-spark|low",
                        "failure_class": "execution",
                        "resolved_model": "gpt-5.3-codex-spark",
                        "resolved_effort": "low",
                        "effective_model": "gpt-5.3-codex-spark",
                        "status": "fail",
                        "route_attempts": [{
                            "requested_pair": "gpt-5.3-codex-spark|low",
                            "resolved_pair": "gpt-5.3-codex-spark|low",
                            "effective_pair": "gpt-5.3-codex-spark|low",
                            "executed_pair": "gpt-5.3-codex-spark|low",
                            "status": "fail",
                            "failure_class": "execution",
                            "model_match": False,
                            "effort_match": False,
                            "pair_match": False,
                            "process_elapsed_ms": 1,
                            "model_turn_duration_ms": None,
                            "time_to_first_token_ms": None,
                        }],
                        "process_elapsed_ms": 1,
                    }
                return {
                    "schema_version": 1,
                    "requested_model": "gpt-5.6-luna",
                    "requested_effort": "low",
                    "requested_pair": "gpt-5.6-luna|low",
                    "resolved_model": "gpt-5.6-luna",
                    "resolved_effort": "low",
                    "effective_model": "gpt-5.6-luna",
                    "status": "pass",
                    "route_attempts": [{
                        "requested_pair": "gpt-5.6-luna|low",
                        "resolved_pair": "gpt-5.6-luna|low",
                        "effective_pair": "gpt-5.6-luna|low",
                        "executed_pair": "gpt-5.6-luna|low",
                        "status": "pass",
                        "failure_class": None,
                        "model_match": True,
                        "effort_match": True,
                        "pair_match": True,
                        "process_elapsed_ms": 5,
                        "model_turn_duration_ms": 2,
                        "time_to_first_token_ms": 1,
                    }],
                    "process_elapsed_ms": 5,
                }

            with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
                cache_dir.mkdir(parents=True, exist_ok=True)
                completed = module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
            self.assertEqual(calls, [("gpt-5.3-codex-spark", "low"), ("gpt-5.6-luna", "low")])
            self.assertEqual(completed["status"], "pass")
            result = json.loads((cache_dir / "direct-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual([attempt["requested_pair"] for attempt in result["route_attempts"]], ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low"])
            self.assertEqual(result["route_attempts"][0]["failure_class"], "execution")

    def test_run_node_does_not_retry_mini_on_verdict_phase_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            node = {
                "id": "mini-verify",
                "phase": "mini",
                "skill": "verify-skill",
                "model": "gpt-5.6-luna",
                "effort": "low",
                "dependencies": ["main"],
                "prompt": "This should fail verdict",
                "sandbox": "read-only",
                "allow_fallback": ["gpt-5.3-codex-spark|low", "gpt-5.6-terra|low"],
            }
            calls = []

            def fake_run_receipt(_args, _prompt):
                calls.append((_args.model, _args.effort))
                return {
                    "schema_version": 1,
                    "requested_model": "gpt-5.6-luna",
                    "requested_effort": "low",
                    "requested_pair": "gpt-5.6-luna|low",
                    "resolved_model": "gpt-5.6-luna",
                    "resolved_effort": "low",
                    "effective_model": "gpt-5.6-luna",
                    "status": "pass",
                    "route_attempts": [{
                        "requested_pair": "gpt-5.6-luna|low",
                        "resolved_pair": "gpt-5.6-luna|low",
                        "effective_pair": "gpt-5.6-luna|low",
                        "executed_pair": "gpt-5.6-luna|low",
                        "status": "pass",
                        "failure_class": None,
                        "model_match": True,
                        "effort_match": True,
                        "pair_match": True,
                        "process_elapsed_ms": 2,
                        "model_turn_duration_ms": 1,
                        "time_to_first_token_ms": 1,
                    }],
                    "process_elapsed_ms": 2,
                }

        with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / "mini-verify-result.md").write_text("MINI_VERIFY=FAIL\n", encoding="utf-8")
            completed = module.run_node(node, cache_dir, {"main": {"status": "pass", "result_path": str(cache_dir / "main-result.md")}}, root / "state.sqlite", root)
        self.assertEqual(calls, [("gpt-5.6-luna", "low")])
        self.assertEqual(completed["status"], "fail")
        self.assertEqual(completed["result_path"], str(cache_dir / "mini-verify-result.md"))

    def test_run_plan_records_unknown_execution_failure_before_mini(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            calls = []

            def fake_run_node(node, cache_dir, completed, _state_db, _workdir, codex_bin="codex"):
                calls.append(node["id"])
                if node["phase"] != "result":
                    return {"id": node["id"], "phase": node["phase"], "status": "pass", "receipt_path": str(cache_dir / f"{node['id']}-receipt.json"), "result_path": str(cache_dir / f"{node['id']}-result.md"), "requested_model": node["model"], "requested_effort": node["effort"], "model": node["model"], "effort": node["effort"], "tokens": {}, "process_elapsed_ms": 1}
                result_receipt = {
                    "schema_version": 1,
                    "requested_model": node["model"],
                    "requested_effort": node["effort"],
                    "requested_pair": f"{node['model']}|{node['effort']}",
                    "resolved_model": node["model"],
                    "resolved_effort": node["effort"],
                    "effective_model": node["model"],
                    "effective_pair": f"{node['model']}|{node['effort']}",
                    "status": "fail",
                    "route_attempts": [{
                        "requested_pair": f"{node['model']}|{node['effort']}",
                        "resolved_pair": f"{node['model']}|{node['effort']}",
                        "effective_pair": f"{node['model']}|{node['effort']}",
                        "executed_pair": f"{node['model']}|{node['effort']}",
                        "status": "fail",
                        "failure_class": "execution",
                        "model_match": False,
                        "effort_match": False,
                        "pair_match": False,
                        "process_elapsed_ms": 1,
                        "model_turn_duration_ms": None,
                        "time_to_first_token_ms": None,
                    }],
                    "process_elapsed_ms": 1,
                }
                receipt_path = cache_dir / f"{node['id']}-receipt.json"
                cache_dir.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(json.dumps(result_receipt), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "status": "fail", "receipt_path": str(receipt_path), "result_path": str(cache_dir / f"{node['id']}-result.md"), "requested_model": node["model"], "requested_effort": node["effort"], "model": node["model"], "effort": node["effort"], "tokens": {}, "process_elapsed_ms": 1}

            recorded_calls = []

            def fake_record_event(args):
                recorded_calls.append(args)
                return {"status": "recorded"}

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module.routing_history_module, "record_event", side_effect=fake_record_event):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(calls, ["direct"])
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_status, "unknown")
        self.assertEqual(recorded_calls[0].failure_class, "execution")
        self.assertEqual(recorded_calls[0].verify_level, "mini")

    def test_plan_requires_all_result_work_before_main_and_ending_after_mini(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"].insert(1, {"id": "orphan-result", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return an orphan result.", "sandbox": "read-only"})
            plan["nodes"][-1]["dependencies"] = []
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("every result node" in failure for failure in failures))
        self.assertTrue(any("depend directly on Mini Verify" in failure for failure in failures))

    def test_sol_ultra_entry_is_not_used_for_luna_downstream_nodes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["entry"] = {"model": "gpt-5.6-sol", "effort": "ultra"}
            failures = module.validate_plan(plan, "gpt-5.6-sol", "ultra", root)
        self.assertEqual(failures, [])
        self.assertTrue(all(node["model"] == "gpt-5.6-luna" for node in plan["nodes"]))

    def test_parallel_plan_runs_ready_branches_before_merge_and_mini(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            plan["complexity"] = "complex"
            plan["topology"] = "parallel"
            direct = plan["nodes"][0]
            condition = direct["routing_condition"]
            profile = {"routing_condition": condition, "task_summary": direct["task_summary"], "candidate_ladder": direct["candidate_ladder"], "static_suggestion": direct["static_suggestion"], "hard_floor": direct["hard_floor"], "trial": False}
            plan["nodes"] = [{"id": "branch-a", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return A.", "sandbox": "read-only"}, {"id": "branch-b", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return B.", "sandbox": "read-only"}, {"id": "merge", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["branch-a", "branch-b"], "prompt": "Merge A and B.", "sandbox": "read-only", **profile}, {"id": "mini-verify", "phase": "mini", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["merge"], "prompt": "Verify the merge.", "sandbox": "read-only"}, {"id": "ending-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-terra", "effort": "low", "dependencies": ["mini-verify"], "prompt": "Run post-result verification.", "sandbox": "read-only"}]
            plan["main_result_node"] = "merge"
            calls = []
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                calls.append(node["id"])
                result_path = cache_dir / f"{node['id']}-result.md"
                receipt_path = cache_dir / f"{node['id']}-receipt.json"
                result_path.write_text("MINI_VERIFY=PASS\n" if node["phase"] == "mini" else node["id"] + "\n", encoding="utf-8")
                receipt_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "model": node["model"], "effort": node["effort"], "status": "pass", "receipt_path": str(receipt_path), "result_path": str(result_path), "tokens": {}, "process_elapsed_ms": 1}
        with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", return_value={"status": "recorded"}):
            manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(set(calls[:2]), {"branch-a", "branch-b"})
        self.assertEqual(calls[2:], ["merge", "mini-verify"])
        self.assertEqual(manifest["status"], "pass")

    def test_ending_handoff_runs_ending_optimization_then_targeted_verifier_by_wave(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan_with_ending_optimization(cache_dir)
            route_run_id = "route-end-wave-001"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md")},
                ],
                "ending_handoff_path": str(cache_dir / "ending-handoff.json"),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path = cache_dir / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            calls = []
            identities = {
                "optimization": "opt-target",
                "optimization-verify": "opt-verifier",
                "real-verify": "real-worker",
            }

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                calls.append(node["id"])
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING_TASK=PASS\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                    "worker_identity": identities[node["id"]],
                    "skill": node["skill"],
                }

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", return_value={"status": "recorded"}):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "pass")
        self.assertLess(calls.index("optimization"), calls.index("optimization-verify"))

    def test_ending_handoff_fails_targeted_verifier_when_worker_identity_matches_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan_with_ending_optimization(cache_dir)
            route_run_id = "route-end-worker-001"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md"), "worker_identity": "main-worker"},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md"), "worker_identity": "mini-worker"},
                ],
                "ending_handoff_path": str(cache_dir / "ending-handoff.json"),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path = cache_dir / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING_TASK=PASS\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                    "worker_identity": "shared-worker",
                }

            recorded_calls = []
            def fake_record_event(args):
                recorded_calls.append(args)
                return {"status": "recorded"}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module.routing_history_module, "record_event", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_level, "real")

    def test_ending_handoff_targeted_verifier_does_not_record_real_status_updates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan_with_ending_optimization(cache_dir)
            route_run_id = "route-end-targeted-record-001"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md"), "worker_identity": "main-worker"},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md"), "worker_identity": "mini-worker"},
                ],
                "ending_handoff_path": str(cache_dir / "ending-handoff.json"),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path = cache_dir / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

            identities = {
                "optimization": "opt-target-worker",
                "optimization-verify": "opt-verifier-worker",
                "real-verify": "real-worker",
            }

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING_TASK=PASS\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                    "worker_identity": identities[node["id"]],
                    "skill": node["skill"],
                }

            recorded_calls = []
            def fake_record_event(args):
                recorded_calls.append(args)
                return {"status": "recorded"}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module.routing_history_module, "record_event", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_level, "real")
        self.assertEqual(recorded_calls[0].verify_status, "pass")
        self.assertEqual(recorded_calls[0].run_id, route_run_id)
        self.assertEqual(recorded_calls[0].receipt, str(cache_dir / "direct-receipt.json"))

    def test_ending_handoff_uses_original_route_run_id_and_main_receipt_on_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan(cache_dir)
            route_run_id = "route-end-pass-001"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md")},
                ],
                "ending_handoff_path": str(cache_dir / "ending-handoff.json"),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path = cache_dir / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING_TASK=PASS\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                }

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record") as record_event:
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(len(record_event.call_args_list), 1)
        self.assertEqual(record_event.call_args.args[0], str(cache_dir / "direct-receipt.json"))
        self.assertEqual(record_event.call_args.args[3], str(cache_dir / "direct-receipt.json"))
        self.assertEqual(record_event.call_args.args[4], route_run_id)
        self.assertNotEqual(record_event.call_args.args[0], str(cache_dir / "ending-verify-receipt.json"))
        self.assertEqual(record_event.call_args.args[1], "real")

    def test_ending_handoff_explicit_fail_records_real_quality_failure_semantics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan(cache_dir)
            route_run_id = "route-end-fail-001"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md")},
                ],
                "ending_handoff_path": str(cache_dir / "ending-handoff.json"),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path = cache_dir / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex"):
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING_TASK=FAIL\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                }

            recorded_calls = []

            def fake_record_event(args):
                recorded_calls.append(args)
                return {"status": "recorded"}

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module.routing_history_module, "record_event", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_level, "real")
        self.assertEqual(recorded_calls[0].verify_status, "fail")
        self.assertEqual(recorded_calls[0].failure_class, "quality")
        self.assertEqual(recorded_calls[0].run_id, route_run_id)
        self.assertEqual(recorded_calls[0].receipt, str(cache_dir / "direct-receipt.json"))


if __name__ == "__main__":
    unittest.main()

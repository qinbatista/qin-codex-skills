#!/usr/bin/env python3
import importlib.util
import json
from copy import deepcopy
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "task_route_dispatcher.py"
MODULE_SPEC = importlib.util.spec_from_file_location("task_route_dispatcher", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class TaskRouteDispatcherTests(unittest.TestCase):
    def plan(self, cache_dir):
        condition = {
            "task_family": "direct",
            "artifact": "answer",
            "scope": "single",
            "ambiguity": "low",
            "modality": "text",
            "risk": "low",
            "complexity": "easy",
            "owning_skill": "workflow-skill",
            "project_family": "global",
            "verification_shape": "mini_real",
            "execution_domain": "general",
        }
        ladder = ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-terra|low"]
        return {"schema_version": 1, "complexity": "easy", "topology": "sequential", "cache_dir": str(cache_dir), "entry": {"model": "gpt-5.6-terra", "effort": "low"}, "nodes": [{"id": "direct", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return RESULT=12", "sandbox": "read-only", "routing_condition": condition, "task_summary": "Return a verified direct arithmetic answer for this task.", "candidate_ladder": ladder, "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.3-codex-spark|low", "trial": False}, {"id": "mini-verify", "phase": "mini", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Verify the dependency result equals 12", "sandbox": "read-only"}, {"id": "ending-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["mini-verify"], "prompt": "Run the bounded post-result verification inventory.", "sandbox": "read-only"}], "main_result_node": "direct", "mini_verify_node": "mini-verify"}

    def plan_with_ending_optimization(self, cache_dir):
        condition = {
            "task_family": "direct",
            "artifact": "answer",
            "scope": "single",
            "ambiguity": "low",
            "modality": "text",
            "risk": "low",
            "complexity": "easy",
            "owning_skill": "workflow-skill",
            "project_family": "global",
            "verification_shape": "mini_real",
            "execution_domain": "general",
        }
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

    def _release_ending_handoff(self, handoff):
        handoff.setdefault("cache_dir", str(Path(handoff["ending_handoff_path"]).resolve().parent))
        mini_record = next(record for record in handoff.get("completed", []) if record.get("id") == "mini-verify")
        mini_result = Path(mini_record.setdefault("result_path", Path(handoff["cache_dir"]) / "mini-verify-result.md"))
        mini_result.parent.mkdir(parents=True, exist_ok=True)
        mini_result.write_text("MINI_VERIFY=PASS\n", encoding="utf-8")
        release = module._release_main_result(handoff)
        if release["status"] != "pass":
            raise AssertionError(f"release-main-result failed: {release.get('failures')}")
        return release

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

    def test_plan_rejects_unity_csharp_result_node_not_owned_by_code_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["language"] = "unity_csharp"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("bypasses code-skill" in failure for failure in failures))

    def test_plan_rejects_unity_csharp_non_spark_node_without_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["language"] = "unity_csharp"
            plan["nodes"][0]["skill"] = "code-skill"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("has no fallback reason" in failure for failure in failures))

    def test_qualified_plugin_result_node_resolves_and_uses_its_skill_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            synthetic_skills_root = root / "skills"
            plugin_skill = root / "plugins" / "cache" / "openai-curated-remote" / "build-web-apps" / "1.0.0" / "skills" / "frontend-app-builder" / "SKILL.md"
            plugin_skill.parent.mkdir(parents=True)
            plugin_skill.write_text("frontend-app-builder\n", encoding="utf-8")
            for skill_name in ("workflow-skill", "verify-skill"):
                skill_path = synthetic_skills_root / skill_name / "SKILL.md"
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text(f"{skill_name}\n", encoding="utf-8")
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["skill"] = "build-web-apps:frontend-app-builder"
            node["purpose"] = "implement"
            node["execution_domain"] = "general"
            node["routing_condition"]["owning_skill"] = "build-web-apps:frontend-app-builder"
            with patch.object(module, "validate_execution_domain_registry"):
                self.assertEqual(module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root), [])
            (root / "work" / "cache" / "route").mkdir(parents=True)
            captured = []
            def fake_run_receipt(_args, prompt):
                captured.append(prompt)
                Path(_args.result_output).write_text("RESULT=plugin\n", encoding="utf-8")
                return {"status": "pass", "failure_class": None, "requested_model": _args.model, "requested_effort": _args.effort, "requested_pair": f"{_args.model}|{_args.effort}", "resolved_model": _args.model, "resolved_effort": _args.effort, "effective_model": _args.model, "effective_pair": f"{_args.model}|{_args.effort}", "turn_completed": True, "route_attempts": [{"requested_pair": f"{_args.model}|{_args.effort}", "resolved_pair": f"{_args.model}|{_args.effort}", "effective_pair": f"{_args.model}|{_args.effort}", "executed_pair": f"{_args.model}|{_args.effort}", "status": "pass", "model_match": True, "effort_match": True, "pair_match": True}]}
            with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
                record = module.run_node(node, root / "work" / "cache" / "route", {}, root / "state.sqlite", root, skills_root=synthetic_skills_root)
            self.assertEqual(record["status"], "pass")
            self.assertIn("skills/frontend-app-builder/SKILL.md", captured[0])

    def test_run_plan_executes_result_then_mini_sequentially(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            calls = []
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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

            def fake_run_node(node, cache_dir, completed, _state_db, _workdir, codex_bin="codex", skills_root=None):
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
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
            self._release_ending_handoff(handoff)
            calls = []
            identities = {
                "optimization": "opt-target",
                "optimization-verify": "opt-verifier",
                "real-verify": "real-worker",
            }

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
            self._release_ending_handoff(handoff)
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
            self._release_ending_handoff(handoff)

            identities = {
                "optimization": "opt-target-worker",
                "optimization-verify": "opt-verifier-worker",
                "real-verify": "real-worker",
            }

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
            self._release_ending_handoff(handoff)

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
            self._release_ending_handoff(handoff)

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_level, "real")
        self.assertEqual(recorded_calls[0].verify_status, "fail")
        self.assertEqual(recorded_calls[0].failure_class, "quality")
        self.assertEqual(recorded_calls[0].run_id, route_run_id)
        self.assertEqual(recorded_calls[0].receipt, str(cache_dir / "direct-receipt.json"))

    def test_ending_handoff_records_unknown_status_when_non_targeted_marker_missing_or_malformed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan(cache_dir)
            route_run_id = "route-end-unknown-001"
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
            self._release_ending_handoff(handoff)

            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
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

            recorded_calls = []

            def fake_record_event(args):
                recorded_calls.append(args)
                return {"status": "recorded"}

            def run_no_marker(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
                ending_receipt = cache_dir / f"{node['id']}-receipt.json"
                ending_result = cache_dir / f"{node['id']}-result.md"
                ending_result.write_text("ENDING summary only\n", encoding="utf-8")
                ending_receipt.write_text("{}", encoding="utf-8")
                return {
                    "id": node["id"],
                    "phase": node["phase"],
                    "status": "pass",
                    "receipt_path": str(ending_receipt),
                    "result_path": str(ending_result),
                }

            with patch.object(module, "run_node", side_effect=lambda *args, **kwargs: (
                fake_run_node(*args, **kwargs) if args[0]["id"] != "ending-verify" else run_no_marker(*args, **kwargs)
            )), patch.object(module.routing_history_module, "record_event", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_status, "unknown")
        self.assertEqual(recorded_calls[0].failure_class, "execution")

    def test_plan_rejects_explicit_history_only_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "code_unspecified"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("execution_domain is non-active: code_unspecified" in failure for failure in failures))

    def test_release_main_result_requires_passed_main_and_mini_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            handoff = {
                "schema_version": 1,
                "route_run_id": "route-release-miss",
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "plan": {
                    "nodes": [
                        {"id": "main-result"},
                        {"id": "mini-verify"},
                    ],
                },
                "completed": [
                    {"id": "main-result", "status": "fail", "phase": "result", "receipt_path": str(root / "main-receipt.json")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "receipt_path": str(root / "mini-receipt.json")},
                ],
                "main_result_node": "main-result",
                "mini_verify_node": "mini-verify",
            }
            (root / "mini-result.md").write_text("MINI_VERIFY=PASS\n", encoding="utf-8")
            handoff["completed"][1]["result_path"] = str(root / "mini-result.md")
            handoff_path = root / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            release = module._release_main_result(handoff)
        self.assertEqual(release["status"], "fail")
        self.assertEqual(release.get("failures"), ["main result and mini verify must both pass before release"])

    def test_release_main_result_persists_ack_and_marks_handoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            handoff = {
                "schema_version": 1,
                "route_run_id": "route-release-pass",
                "cache_dir": str(root),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "plan": {
                    "nodes": [],
                },
                "completed": [
                    {"id": "main-result", "status": "pass", "phase": "result", "receipt_path": str(root / "main-receipt.json")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "receipt_path": str(root / "mini-receipt.json")},
                ],
                "main_result_node": "main-result",
                "mini_verify_node": "mini-verify",
            }
            mini_result = root / "mini-result.md"
            mini_result.write_text("MINI_VERIFY=PASS\n", encoding="utf-8")
            handoff["completed"][1]["result_path"] = str(mini_result)
            handoff_path = root / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            release = module._release_main_result(handoff)
            self.assertEqual(release["status"], "pass")
            self.assertEqual(release["route_run_id"], "route-release-pass")
            self.assertTrue(Path(release["release_path"]).exists())
            self.assertEqual(handoff["completed"][0]["status"], "pass")

    @contextmanager
    def _with_rust_domain(self, owner="code-skill", spark_first=True, language_alias="rust"):
        original = deepcopy(module.EXECUTION_DOMAINS)
        original_history_domains = deepcopy(module.routing_history_module.EXECUTION_DOMAINS)
        original_history_control = deepcopy(module.routing_history_module.CONTROL_ENUMS["execution_domain"])
        with tempfile.TemporaryDirectory(prefix="task-route-dispatcher-skills-") as temporary:
            temporary_skills_root = Path(temporary)
            rust_reference_path = "code-skill/references/rust-small-code.md"
            module.EXECUTION_DOMAINS["rust"] = {
                "display_name": "Rust",
                "kind": "code",
                "language_aliases": [language_alias],
                "owner_skill": owner,
                "owner_enforced": True,
                "spark_first": spark_first,
                "reference_path": rust_reference_path,
                "active": True,
                "history_only": False,
            }
            module.routing_history_module.EXECUTION_DOMAINS["rust"] = module.EXECUTION_DOMAINS["rust"]
            module.routing_history_module.CONTROL_ENUMS["execution_domain"] = set(module.routing_history_module.EXECUTION_DOMAINS.keys())
            required_owners = {"task-analyze-skill", "workflow-skill", "code-skill", "verify-skill", "optimization-skill", "management-skill"}
            for metadata in module.EXECUTION_DOMAINS.values():
                owner_skill = metadata["owner_skill"]
                skill_dir = temporary_skills_root / owner_skill
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(f"{owner_skill} skill\n", encoding="utf-8")
                reference = temporary_skills_root / metadata["reference_path"]
                reference.parent.mkdir(parents=True, exist_ok=True)
                reference.write_text(f"reference: {metadata['reference_path']}\n", encoding="utf-8")
            for owner_skill in required_owners:
                skill_dir = temporary_skills_root / owner_skill
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(f"{owner_skill} skill\n", encoding="utf-8")
            yield temporary_skills_root
            module.EXECUTION_DOMAINS.clear()
            module.routing_history_module.EXECUTION_DOMAINS.clear()
            module.EXECUTION_DOMAINS.update(original)
            module.routing_history_module.EXECUTION_DOMAINS.update(original_history_domains)
            module.routing_history_module.CONTROL_ENUMS["execution_domain"] = original_history_control
        # cleanup via TemporaryDirectory context

    def test_plan_rejects_invalid_execution_domain_registry_with_missing_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            with self._with_rust_domain() as synthetic_skills_root:
                missing_reference = synthetic_skills_root / module.EXECUTION_DOMAINS["general"]["reference_path"]
                missing_reference.unlink()
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertTrue(any("execution_domain registry is invalid" in failure for failure in failures))
        self.assertFalse(any("execution_domain is unknown" in failure for failure in failures))

    def test_plan_accepts_valid_execution_domain_registry_for_temp_skills_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            with self._with_rust_domain() as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertEqual(failures, [])

    def test_plan_rejects_rust_domain_wrong_owner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust"
            plan["nodes"][0]["language"] = "rust"
            plan["nodes"][0]["skill"] = "workflow-skill"
            with self._with_rust_domain(owner="code-skill") as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertTrue(any("implementation owner mismatch for rust" in failure for failure in failures))

    def test_plan_rejects_unknown_execution_domain_with_clean_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust_lang"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("execution_domain is unknown" in failure for failure in failures))
        self.assertFalse(any("implementation owner mismatch" in failure for failure in failures))

    def test_plan_rejects_rust_domain_non_spark_without_reason(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust"
            plan["nodes"][0]["language"] = "rust"
            plan["nodes"][0]["skill"] = "code-skill"
            plan["nodes"][0]["model"] = "gpt-5.6-luna"
            with self._with_rust_domain() as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertTrue(any("has no fallback reason" in failure for failure in failures))

    def test_plan_main_result_rejects_routing_condition_domain_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "python"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "general"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("execution_domain must match routing_condition.execution_domain" in failure for failure in failures))

    def test_plan_main_result_rejects_routing_condition_owner_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "python"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "python"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "workflow-skill"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("bypasses code-skill; implementation owner mismatch for python" in failure for failure in failures))

    def test_plan_main_result_rejects_general_routing_condition_owner_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["skill"] = "management-skill"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "general"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "workflow-skill"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("routing_condition.owning_skill must match the executing node skill" in failure for failure in failures))

    def test_plan_main_result_allows_management_skill_general_with_matching_condition_owner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["skill"] = "management-skill"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "general"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "management-skill"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

    def test_plan_accepts_rust_domain_with_spark(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust"
            plan["nodes"][0]["language"] = "rust"
            plan["nodes"][0]["skill"] = "code-skill"
            plan["nodes"][0]["model"] = "gpt-5.3-codex-spark"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "rust"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "code-skill"
            with self._with_rust_domain() as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertEqual(failures, [])

    def test_plan_injects_reference_prompt_for_synthetic_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            node = {
                "id": "main-result",
                "phase": "result",
                "skill": "code-skill",
                "model": "gpt-5.3-codex-spark",
                "effort": "low",
                "dependencies": [],
                "prompt": "Return a minimal rust answer",
                "sandbox": "read-only",
                "execution_domain": "rust",
                "language": "rust",
                "routing_condition": {
                    "task_family": "code",
                    "artifact": "script",
                    "scope": "single",
                    "ambiguity": "low",
                    "modality": "text",
                    "risk": "low",
                    "complexity": "easy",
                    "owning_skill": "code-skill",
                    "project_family": "global",
                    "verification_shape": "mini_real",
                    "execution_domain": "rust",
                },
                "task_summary": "Emit a rust answer.",
                "candidate_ladder": ["gpt-5.3-codex-spark|low"],
                "static_suggestion": "gpt-5.3-codex-spark|low",
                "hard_floor": "gpt-5.3-codex-spark|low",
                "trial": False,
            }
            captured = {}

            def fake_run_receipt(_args, prompt):
                captured["prompt"] = prompt
                return {
                    "schema_version": 1,
                    "requested_model": "gpt-5.3-codex-spark",
                    "requested_effort": "low",
                    "requested_pair": "gpt-5.3-codex-spark|low",
                    "resolved_model": "gpt-5.3-codex-spark",
                    "resolved_effort": "low",
                    "effective_model": "gpt-5.3-codex-spark",
                    "status": "pass",
                    "route_attempts": [{
                        "requested_pair": "gpt-5.3-codex-spark|low",
                        "resolved_pair": "gpt-5.3-codex-spark|low",
                        "effective_pair": "gpt-5.3-codex-spark|low",
                        "executed_pair": "gpt-5.3-codex-spark|low",
                        "status": "pass",
                        "failure_class": None,
                        "model_match": True,
                        "effort_match": True,
                        "pair_match": True,
                        "process_elapsed_ms": 1,
                        "model_turn_duration_ms": 1,
                        "time_to_first_token_ms": 1,
                    }],
                    "process_elapsed_ms": 1,
                }

            with self._with_rust_domain() as synthetic_skills_root:
                with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
                    result = module.run_node(
                        node,
                        cache_dir,
                        {},
                        root / "state.sqlite",
                        root,
                        skills_root=synthetic_skills_root,
                    )
        self.assertEqual(result["status"], "pass")
        prompt_lines = captured["prompt"].splitlines()
        owner_line = f"Execute only this bounded locked node. Read and obey {synthetic_skills_root.resolve() / 'code-skill/SKILL.md'}."
        self.assertIn(owner_line, prompt_lines)
        self.assertIn(
            f"Reference rules for this execution domain: {synthetic_skills_root.resolve() / 'code-skill/references/rust-small-code.md'}",
            prompt_lines,
        )

    def test_run_ending_rejects_unreleased_or_mismatched_handoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan(cache_dir)
            handoff_path = cache_dir / "ending-handoff.json"
            handoff = {
                "schema_version": 1,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": "route-unreleased",
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
                    {"id": "mini-verify", "status": "pass", "phase": "mini", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "mini-verify-receipt.json"), "result_path": str(cache_dir / "mini-verify-result.md")},
                ],
                "ending_handoff_path": str(handoff_path),
                "ending_manifest_path": str(cache_dir / "ending-dispatch-manifest.json"),
            }
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            with patch.object(module, "run_node", side_effect=AssertionError("run_node should not execute")):
                unreleased = module.run_ending_handoff(handoff_path)
        self.assertEqual(unreleased["status"], "fail")
        self.assertTrue(any("ending handoff is not released" in failure for failure in unreleased["failures"]))
        release_plan = {
            "schema_version": 1,
            "cache_dir": str(cache_dir),
            "route_run_id": "route-release",
            "entry": {"model": "gpt-5.6-terra", "effort": "low"},
            "plan": {
                "nodes": [],
            },
            "completed": [
                {"id": "main-result", "status": "pass", "phase": "result", "receipt_path": str(cache_dir / "main-receipt.json")},
                {"id": "mini-verify", "status": "pass", "phase": "mini", "receipt_path": str(cache_dir / "mini-receipt.json")},
            ],
            "main_result_node": "main-result",
            "mini_verify_node": "mini-verify",
        }
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "mini-result.md").write_text("MINI_VERIFY=PASS\n", encoding="utf-8")
        release_plan["completed"][1]["result_path"] = str(cache_dir / "mini-result.md")
        release = module._release_main_result(json.loads(json.dumps(release_plan)))
        self.assertEqual(release["status"], "pass")
        handoff["route_run_id"] = "route-release-mismatch"
        mismatch_path = cache_dir / "ending-handoff-mismatch.json"
        mismatch_path.write_text(json.dumps(handoff), encoding="utf-8")
        with patch.object(module, "run_node", side_effect=AssertionError("run_node should not execute")):
            mismatched = module.run_ending_handoff(mismatch_path)
        self.assertEqual(mismatched["status"], "fail")
        self.assertTrue(any("ending handoff release does not match route_run_id" in failure for failure in mismatched["failures"]))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import importlib.util
import json
import os
import time
from copy import deepcopy
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "task_route_dispatcher.py"
MODULE_SPEC = importlib.util.spec_from_file_location("task_route_dispatcher", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class TaskRouteDispatcherTests(unittest.TestCase):
    def refresh_recommendation(self, node):
        pairs = module.routing_history_module.canonical_pairs(node["candidate_ladder"])
        fingerprint = module.routing_history_module.profile_fingerprint(node["routing_condition"], pairs, module.routing_history_module.parse_pair(node["static_suggestion"]), module.routing_history_module.parse_pair(node["hard_floor"]))
        node["routing_recommendation"] = {"selected_pair": f"{node['model']}|{node['effort']}", "trial": node["trial"], "reason": "shared_cold_start", "profile_fingerprint": fingerprint, "calibration_state": "cold_start", "best_pair": None, "selection_basis": "obsidian_project_memory"}

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
            "verification_shape": "real",
            "execution_domain": "general",
        }
        ladder = module.normal_adaptive_pair_texts()
        fingerprint = module.routing_history_module.profile_fingerprint(
            condition,
            module.routing_history_module.canonical_pairs(ladder),
            module.routing_history_module.parse_pair("gpt-5.6-luna|low"),
            module.routing_history_module.parse_pair("gpt-5.6-luna|low"),
        )
        return {"schema_version": 2, "complexity": "easy", "topology": "sequential", "cache_dir": str(cache_dir), "entry": {"model": "gpt-5.6-terra", "effort": "low"}, "nodes": [{"id": "direct", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return RESULT=12", "sandbox": "read-only", "routing_condition": condition, "task_summary": "Return a direct arithmetic answer for this task.", "candidate_ladder": ladder, "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.6-luna|low", "trial": False, "routing_recommendation": {"selected_pair": "gpt-5.6-luna|low", "trial": False, "reason": "shared_cold_start", "profile_fingerprint": fingerprint, "calibration_state": "cold_start", "best_pair": None, "selection_basis": "obsidian_project_memory"}}, {"id": "ending-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Run Real Verify after the result is released.", "sandbox": "read-only"}], "main_result_node": "direct"}

    def dependent_plan(self, cache_dir):
        plan = self.plan(cache_dir)
        main_node = plan["nodes"][0]
        main_node["id"] = "main-result"
        main_node["dependencies"] = ["upstream"]
        plan["nodes"].insert(0, {"id": "upstream", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return the upstream result.", "sandbox": "read-only"})
        plan["nodes"][-1]["dependencies"] = ["main-result"]
        plan["main_result_node"] = "main-result"
        return plan

    def result_receipt(self, args, ready_monotonic_ns, status="pass", failure_class=None):
        pair = f"{args.model}|{args.effort}"
        return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": pair, "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": pair, "status": status, "failure_class": failure_class, "route_attempts": [], "process_elapsed_ms": 1, "tokens": {"total_tokens": 1}, "result_published": True, "result_ready_monotonic_ns": ready_monotonic_ns}

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
            "verification_shape": "real",
            "execution_domain": "general",
        }
        ladder = module.normal_adaptive_pair_texts()
        fingerprint = module.routing_history_module.profile_fingerprint(
            condition,
            module.routing_history_module.canonical_pairs(ladder),
            module.routing_history_module.parse_pair("gpt-5.6-luna|low"),
            module.routing_history_module.parse_pair("gpt-5.6-luna|low"),
        )
        return {
            "schema_version": 2,
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
                    "hard_floor": "gpt-5.6-luna|low",
                    "trial": False,
                    "routing_recommendation": {"selected_pair": "gpt-5.6-luna|low", "trial": False, "reason": "shared_cold_start", "profile_fingerprint": fingerprint, "calibration_state": "cold_start", "best_pair": None, "selection_basis": "obsidian_project_memory"},
                },
                {"id": "optimization", "phase": "ending", "skill": "optimization-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Optimize this result independently.", "sandbox": "read-only"},
                {
                    "id": "optimization-verify",
                    "phase": "ending",
                    "skill": "verify-skill",
                    "model": "gpt-5.6-luna",
                    "effort": "low",
                    "dependencies": ["direct", "optimization"],
                    "verifies_node": "optimization",
                    "prompt": "Verify optimization output.",
                    "sandbox": "read-only",
                },
                {"id": "real-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Run real verify.", "sandbox": "read-only"},
            ],
            "main_result_node": "direct",
        }

    def _release_ending_handoff(self, handoff):
        handoff.setdefault("cache_dir", str(Path(handoff["ending_handoff_path"]).resolve().parent))
        main_node_id = handoff.get("main_result_node") or handoff["plan"]["main_result_node"]
        main_record = next(record for record in handoff.get("completed", []) if record.get("id") == main_node_id)
        main_result = Path(main_record.setdefault("result_path", Path(handoff["cache_dir"]) / f"{main_node_id}-result.md"))
        main_result.parent.mkdir(parents=True, exist_ok=True)
        if not main_result.exists():
            main_result.write_text("RESULT=12\n", encoding="utf-8")
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

    def test_schema_two_rejects_legacy_foreground_mini(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"].insert(1, {"id": "mini-verify", "phase": "mini", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["direct"], "prompt": "Legacy Mini Verify.", "sandbox": "read-only"})
            plan["mini_verify_node"] = "mini-verify"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("invalid phase" in failure for failure in failures))
        self.assertIn("mini_verify_node is not valid in schema 2", failures)

    def test_result_phase_verify_skill_requires_explicit_user_requested_verification_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            result_node = plan["nodes"][0]
            result_node.update({"id": "quick-check", "skill": "verify-skill"})
            result_node["routing_condition"]["owning_skill"] = "verify-skill"
            self.refresh_recommendation(result_node)
            plan["nodes"][1]["dependencies"] = ["quick-check"]
            plan["main_result_node"] = "quick-check"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
            result_node["user_requested_verification_result"] = True
            authorized_failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertIn("quick-check verify-skill result nodes require user_requested_verification_result=true", failures)
        self.assertEqual(authorized_failures, [])

    def test_user_requested_verification_flag_is_rejected_on_non_verifier_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["user_requested_verification_result"] = True
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertIn("direct user_requested_verification_result is valid only on a result-phase verify-skill node", failures)

    def test_schema_one_plan_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["schema_version"] = 1
            with patch.object(module, "run_node") as run_node:
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(manifest["status"], "fail")
        self.assertIn("schema_version must be 2", manifest["failures"])
        run_node.assert_not_called()

    def test_plan_rejects_routing_recommendation_proof_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["routing_recommendation"]["selected_pair"] = "gpt-5.6-terra|low"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("routing_recommendation must match" in failure for failure in failures))

    def test_plan_rejects_incomplete_routing_recommendation_proof(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            del plan["nodes"][0]["routing_recommendation"]["selection_basis"]
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("proof missing keys: selection_basis" in failure for failure in failures))

    def test_initial_dispatch_accepts_current_obsidian_recommendation_without_legacy_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            with patch.object(module.routing_history_module, "recommend_route", side_effect=AssertionError("legacy JSON recommendation used")) as legacy:
                failures = module.validate_plan(
                    plan,
                    "gpt-5.6-terra",
                    "low",
                    root,
                    enforce_current_recommendation=True,
                    history_path=root / "history.json",
                )
        self.assertEqual(failures, [])
        legacy.assert_not_called()

    def test_ending_record_uses_obsidian_model_memory_without_legacy_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            node = self.plan(root / "work" / "cache" / "route")["nodes"][0]
            next_recommendation = {"selected_pair": "gpt-5.6-luna|low"}
            with patch.object(module.obsidian_model_memory, "record_model_result", return_value={"status": "written"}) as record, patch.object(module.obsidian_model_memory, "recommend_model", return_value=next_recommendation) as recommend, patch.object(module.routing_history_module, "record_event", side_effect=AssertionError("legacy JSON write used")) as legacy:
                result = module._run_record("unused", "real", "pass", root / "producer-receipt.json", "route-1", node, root)
        self.assertEqual(result["status"], "written")
        record.assert_called_once()
        recommend.assert_called_once()
        legacy.assert_not_called()

    def test_initial_dispatch_rejects_plan_and_proof_forged_together(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["model"] = "gpt-5.6-terra"
            node["effort"] = "low"
            node["routing_recommendation"]["selected_pair"] = "gpt-5.6-terra|low"
            failures = module.validate_plan(
                plan,
                "gpt-5.6-terra",
                "low",
                root,
                enforce_current_recommendation=True,
                history_path=root / "history.json",
            )
        self.assertTrue(any("does not match current Obsidian recommendation" in failure for failure in failures))
        self.assertTrue(any("stale or not Obsidian-derived" in failure for failure in failures))

    def test_initial_dispatch_rejects_forged_recommendation_reason(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["routing_recommendation"]["reason"] = "forged_reason_not_from_learner"
            failures = module.validate_plan(
                plan,
                "gpt-5.6-terra",
                "low",
                root,
                enforce_current_recommendation=True,
                history_path=root / "history.json",
            )
        self.assertTrue(any("stale or not Obsidian-derived: reason" in failure for failure in failures))

    def test_plan_rejects_selected_pair_below_hard_floor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["hard_floor"] = "gpt-5.6-terra|medium"
            node["static_suggestion"] = "gpt-5.6-terra|medium"
            self.refresh_recommendation(node)
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("selected pair must not be below hard_floor" in failure for failure in failures))

    def test_run_plan_does_not_execute_forged_recommendation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["model"] = "gpt-5.6-terra"
            node["effort"] = "low"
            node["routing_recommendation"]["selected_pair"] = "gpt-5.6-terra|low"
            with patch.object(module, "run_node") as run_node:
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(manifest["status"], "fail")
        run_node.assert_not_called()

    def test_tiny_profile_uses_the_same_full_gpt56_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["routing_condition"]["task_family"] = "tiny_text"
            self.refresh_recommendation(node)
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

    def test_tiny_profile_rejects_spark(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            node = plan["nodes"][0]
            node["routing_condition"]["task_family"] = "tiny_text"
            node["candidate_ladder"] = ["gpt-5.3-codex-spark|low"] + module.normal_adaptive_pair_texts()
            node["hard_floor"] = "gpt-5.3-codex-spark|low"
            node["model"] = "gpt-5.3-codex-spark"
            node["effort"] = "medium"
            self.refresh_recommendation(node)
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("shared active GPT-5.6 ladder" in failure for failure in failures))
        self.assertTrue(any("selected pair must be in candidate_ladder" in failure for failure in failures))

    def test_real_verify_rejects_management_only_ending(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][-1]["skill"] = "management-skill"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("exactly one non-targeted Ending verify-skill" in failure for failure in failures))

    def test_non_tiny_profile_requires_the_complete_gpt56_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["candidate_ladder"] = plan["nodes"][0]["candidate_ladder"][:-1]
            self.refresh_recommendation(plan["nodes"][0])
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("exactly match the shared full GPT-5.6 ladder" in failure for failure in failures))

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
            plan["nodes"][2].pop("verifies_node")
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(
            any("must have exactly one ending verify-skill verifier targeting it" in failure for failure in failures)
        )

    def test_plan_rejects_optimization_node_with_wrong_verifies_node(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan_with_ending_optimization(root / "work" / "cache" / "route")
            plan["nodes"][2]["verifies_node"] = "missing-target"
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

    def test_plan_accepts_complex_unity_csharp_with_terra(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["language"] = "unity_csharp"
            plan["nodes"][0]["skill"] = "code-skill"
            plan["nodes"][0]["model"] = "gpt-5.6-terra"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "unity_csharp"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "code-skill"
            self.refresh_recommendation(plan["nodes"][0])
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

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
            self.refresh_recommendation(node)
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

    def test_run_plan_returns_after_result_without_foreground_verify(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            calls = []
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
                calls.append(node["id"])
                result_path = cache_dir / f"{node['id']}-result.md"
                receipt_path = cache_dir / f"{node['id']}-receipt.json"
                result_path.write_text("RESULT=12\n", encoding="utf-8")
                receipt_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "model": node["model"], "effort": node["effort"], "status": "pass", "receipt_path": str(receipt_path), "result_path": str(result_path), "tokens": {}, "process_elapsed_ms": 1}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", return_value={"status": "recorded"}) as record_event:
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(calls, ["direct"])
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(manifest["entry"], {"model": "gpt-5.6-terra", "effort": "low"})
        self.assertEqual(manifest["ending_nodes_pending"], ["ending-verify"])
        record_event.assert_not_called()
        self.assertIn("route_run_id", manifest)

    def test_main_result_readiness_precedes_delayed_receipt_telemetry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            ready_event = threading.Event()
            ready_records = []

            def controller_ready(result_path, ready_ns):
                ready_records.append((str(result_path), ready_ns))
                ready_event.set()

            def delayed_receipt(args, _prompt):
                module.receipt_module.atomic_write_private_text(args.result_output, "RESULT=12\n")
                ready_ns = time.monotonic_ns()
                args.result_ready_callback(args.result_output, ready_ns)
                time.sleep(0.15)
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "pass", "failure_class": None, "route_attempts": [], "process_elapsed_ms": 150, "tokens": {"total_tokens": 1}, "result_published": True, "result_ready_monotonic_ns": ready_ns}

            with patch.object(module.receipt_module, "run_receipt", side_effect=delayed_receipt), ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(module.run_plan, plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json", result_ready_callback=controller_ready)
                result_path = cache_dir / "direct-result.md"
                self.assertTrue(ready_event.wait(timeout=1))
                presented_result = result_path.read_text(encoding="utf-8")
                self.assertFalse(future.done())
                manifest = future.result(timeout=2)
        self.assertEqual(presented_result, "RESULT=12\n")
        self.assertEqual(manifest["status"], "pass")
        self.assertTrue(manifest["result_published"])
        self.assertEqual(Path(ready_records[0][0]).resolve(), (cache_dir / "direct-result.md").resolve())
        self.assertLess(manifest["first_result_elapsed_ms"], 100)
        self.assertEqual(manifest["ending_nodes_pending"], ["ending-verify"])

    def test_dependent_result_starts_before_upstream_receipt_settles_and_main_timing_excludes_receipt_tail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.dependent_plan(cache_dir)
            downstream_started = threading.Event()
            upstream_receipt_settled = threading.Event()
            main_ready = threading.Event()
            main_receipt_release = threading.Event()
            downstream_started_before_upstream_settled = []

            def controller_ready(_result_path, _ready_ns):
                main_ready.set()

            def delayed_receipt(args, prompt):
                node_id = args.workload_id.removeprefix("task-route-")
                if node_id == "upstream":
                    module.receipt_module.atomic_write_private_text(args.result_output, "UPSTREAM=ready\n")
                    ready_ns = time.monotonic_ns()
                    args.result_ready_callback(args.result_output, ready_ns)
                    if not downstream_started.wait(timeout=1):
                        raise AssertionError("dependent did not start from the atomic upstream result")
                    upstream_receipt_settled.set()
                    return self.result_receipt(args, ready_ns)
                downstream_started_before_upstream_settled.append(not upstream_receipt_settled.is_set())
                self.assertIn("UPSTREAM=ready", prompt)
                downstream_started.set()
                module.receipt_module.atomic_write_private_text(args.result_output, "RESULT=12\n")
                ready_ns = time.monotonic_ns()
                args.result_ready_callback(args.result_output, ready_ns)
                if not main_receipt_release.wait(timeout=1):
                    raise AssertionError("test did not release delayed main receipt")
                return self.result_receipt(args, ready_ns)

            with patch.object(module.receipt_module, "run_receipt", side_effect=delayed_receipt), ThreadPoolExecutor(max_workers=1) as executor:
                run_started = time.monotonic()
                future = executor.submit(module.run_plan, plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json", result_ready_callback=controller_ready)
                self.assertTrue(main_ready.wait(timeout=1))
                self.assertTrue(downstream_started.is_set())
                self.assertFalse(future.done())
                time.sleep(0.15)
                main_receipt_release.set()
                manifest = future.result(timeout=2)
                total_elapsed_ms = round((time.monotonic() - run_started) * 1000)
        self.assertEqual(downstream_started_before_upstream_settled, [True])
        self.assertEqual(manifest["status"], "pass")
        self.assertTrue(manifest["result_published"])
        self.assertGreaterEqual(total_elapsed_ms - manifest["first_result_elapsed_ms"], 100)

    def test_parallel_merge_starts_from_branch_publications_while_all_receipt_tails_are_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.dependent_plan(cache_dir)
            plan["topology"] = "parallel"
            main_node = next(node for node in plan["nodes"] if node["id"] == "main-result")
            main_node["dependencies"] = ["branch-a", "branch-b", "branch-c"]
            plan["nodes"] = [node for node in plan["nodes"] if node["id"] != "upstream"]
            for branch_id in reversed(main_node["dependencies"]):
                plan["nodes"].insert(0, {"id": branch_id, "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": f"Return {branch_id}.", "sandbox": "read-only"})
            merge_started = threading.Event()
            branch_receipt_settled = {branch_id: threading.Event() for branch_id in main_node["dependencies"]}
            merge_started_before_receipts_settled = []

            def delayed_receipt(args, _prompt):
                node_id = args.workload_id.removeprefix("task-route-")
                if node_id in branch_receipt_settled:
                    module.receipt_module.atomic_write_private_text(args.result_output, f"{node_id}=ready\n")
                    ready_ns = time.monotonic_ns()
                    args.result_ready_callback(args.result_output, ready_ns)
                    if not merge_started.wait(timeout=1):
                        raise AssertionError("merge did not start while branch receipts were blocked")
                    branch_receipt_settled[node_id].set()
                    return self.result_receipt(args, ready_ns)
                merge_started_before_receipts_settled.append(not any(event.is_set() for event in branch_receipt_settled.values()))
                merge_started.set()
                module.receipt_module.atomic_write_private_text(args.result_output, "RESULT=merged\n")
                ready_ns = time.monotonic_ns()
                args.result_ready_callback(args.result_output, ready_ns)
                return self.result_receipt(args, ready_ns)

            with patch.object(module.receipt_module, "run_receipt", side_effect=delayed_receipt):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(merge_started_before_receipts_settled, [True])
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual([record["id"] for record in manifest["nodes"]], ["branch-a", "branch-b", "branch-c", "main-result"])

    def test_late_upstream_receipt_failure_after_main_publication_reopens_and_blocks_ending(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.dependent_plan(cache_dir)
            main_published = threading.Event()

            def controller_ready(_result_path, _ready_ns):
                main_published.set()

            def late_failure(args, _prompt):
                node_id = args.workload_id.removeprefix("task-route-")
                module.receipt_module.atomic_write_private_text(args.result_output, f"{node_id}=ready\n")
                ready_ns = time.monotonic_ns()
                args.result_ready_callback(args.result_output, ready_ns)
                if node_id == "upstream":
                    if not main_published.wait(timeout=1):
                        raise AssertionError("main result was not published before upstream receipt failure")
                    return self.result_receipt(args, ready_ns, status="fail", failure_class="protocol")
                return self.result_receipt(args, ready_ns)

            with patch.object(module.receipt_module, "run_receipt", side_effect=late_failure):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json", result_ready_callback=controller_ready)
        self.assertTrue(main_published.is_set())
        self.assertEqual(manifest["status"], "fail")
        self.assertTrue(manifest["result_published"])
        self.assertTrue(manifest["notification_required"])
        self.assertTrue(manifest["reopen_required"])
        self.assertIsNone(manifest["ending_handoff_path"])
        self.assertFalse((cache_dir / "ending-handoff.json").exists())

    def test_main_receipt_failure_after_presentation_requires_notification_and_reopen(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)

            def failed_after_result(args, _prompt):
                module.receipt_module.atomic_write_private_text(args.result_output, "RESULT=12\n")
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "fail", "failure_class": "protocol", "route_attempts": [], "process_elapsed_ms": 150, "tokens": {"total_tokens": 1}, "result_published": True, "result_ready_monotonic_ns": time.monotonic_ns(), "duplicate_result_detected": True}

            with patch.object(module.receipt_module, "run_receipt", side_effect=failed_after_result):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
            presented_result = (cache_dir / "direct-result.md").read_text(encoding="utf-8")
        self.assertEqual(presented_result, "RESULT=12\n")
        self.assertEqual(manifest["status"], "fail")
        self.assertTrue(manifest["result_published"])
        self.assertTrue(manifest["notification_required"])
        self.assertTrue(manifest["reopen_required"])
        self.assertIsNone(manifest["ending_handoff_path"])

    def test_run_node_retries_only_zero_token_pre_execution_failure_and_aggregates_attempts(self):
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
                        "tokens": {"total_tokens": 0},
                        "pre_execution_failure": True,
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
                _args.result_output.write_text("RESULT=12\n", encoding="utf-8")
                return {
                    "schema_version": 1,
                    "requested_model": "gpt-5.6-luna",
                    "requested_effort": "low",
                    "requested_pair": "gpt-5.6-luna|low",
                    "resolved_model": "gpt-5.6-luna",
                    "resolved_effort": "low",
                    "effective_model": "gpt-5.6-luna",
                    "status": "pass",
                    "tokens": {"total_tokens": 5},
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
            self.assertEqual(result["strategy_tokens"]["total_tokens"], 5)
            self.assertEqual(result["strategy_elapsed_ms"], 6)
            self.assertEqual(completed["tokens"]["total_tokens"], 5)
            self.assertEqual(completed["process_elapsed_ms"], 6)

    def test_run_node_does_not_fallback_after_consumed_timeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            node = {"id": "bounded-result", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-terra", "effort": "high", "dependencies": [], "prompt": "Return a bounded result.", "sandbox": "read-only", "allow_fallback": ["gpt-5.6-sol|low"]}
            calls = []

            def fake_run_receipt(args, _prompt):
                calls.append((args.model, args.effort))
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "fail", "failure_class": "timeout", "turn_completed": False, "tokens": {"total_tokens": 25}, "process_elapsed_ms": 70, "pre_execution_failure": False, "route_attempts": []}

            with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
                completed = module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
            receipt = json.loads((cache_dir / "bounded-result-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(calls, [("gpt-5.6-terra", "high")])
        self.assertEqual(completed["status"], "fail")
        self.assertEqual(receipt["strategy_tokens"]["total_tokens"], 25)
        self.assertEqual(receipt["strategy_elapsed_ms"], 70)

    def test_run_node_does_not_retry_ending_on_verdict_phase_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            node = {
                "id": "ending-verify",
                "phase": "ending",
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
                (cache_dir / "ending-verify-result.md").write_text("ENDING_TASK=FAIL\n", encoding="utf-8")
                completed = module.run_node(node, cache_dir, {"main": {"status": "pass", "result_path": str(cache_dir / "main-result.md")}}, root / "state.sqlite", root)
            self.assertEqual(calls, [("gpt-5.6-luna", "low")])
            self.assertEqual(completed["status"], "fail")
            self.assertEqual(completed["result_path"], str(cache_dir / "ending-verify-result.md"))

    def test_run_node_skips_operational_fallback_when_deadline_cannot_cover_attempt_and_reserve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            node = {
                "id": "bounded-result",
                "phase": "result",
                "skill": "workflow-skill",
                "model": "gpt-5.6-terra",
                "effort": "high",
                "dependencies": [],
                "prompt": "Return a bounded result.",
                "sandbox": "read-only",
                "allow_fallback": ["gpt-5.6-terra|xhigh"],
                "timeout": 80,
                "_deadline_monotonic": 100,
                "_fallback_reserve_seconds": 30,
            }
            calls = []

            def fake_run_receipt(args, _prompt):
                calls.append((args.model, args.effort))
                return {
                    "schema_version": 1,
                    "requested_model": args.model,
                    "requested_effort": args.effort,
                    "requested_pair": f"{args.model}|{args.effort}",
                    "resolved_model": args.model,
                    "resolved_effort": args.effort,
                    "effective_model": args.model,
                    "effective_pair": f"{args.model}|{args.effort}",
                    "status": "fail",
                    "failure_class": "timeout",
                    "route_attempts": [],
                    "process_elapsed_ms": 80_000,
                    "tokens": {"total_tokens": 10},
                }

            with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt), patch.object(module.time, "monotonic", side_effect=[0, 50]):
                completed = module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
            self.assertEqual(calls, [("gpt-5.6-terra", "high")])
            self.assertEqual(completed["status"], "fail")
            receipt = json.loads((cache_dir / "bounded-result-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual([attempt["requested_pair"] for attempt in receipt["route_attempts"]], ["gpt-5.6-terra|high"])

    def test_run_plan_does_not_record_learning_before_real_verify(self):
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

            def fake_record_event(result_path, verify_level, verify_status, receipt, run_id, main_node, project_root, execution_domain=None):
                recorded_calls.append(SimpleNamespace(verify_level=verify_level, verify_status=verify_status, failure_class="none" if verify_status == "pass" else ("quality" if verify_status == "fail" else "execution"), run_id=run_id, receipt=receipt))
                return {"status": "recorded"}

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", side_effect=fake_record_event):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(calls, ["direct"])
        self.assertEqual(recorded_calls, [])

    def test_plan_requires_all_result_work_before_main_and_ending_after_main(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"].insert(1, {"id": "orphan-result", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return an orphan result.", "sandbox": "read-only"})
            plan["nodes"][-1]["dependencies"] = []
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("every result node" in failure for failure in failures))
        self.assertTrue(any("depend directly on the main result node" in failure for failure in failures))

    def test_sol_ultra_entry_is_not_used_for_luna_downstream_nodes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["entry"] = {"model": "gpt-5.6-sol", "effort": "ultra"}
            failures = module.validate_plan(plan, "gpt-5.6-sol", "ultra", root)
        self.assertEqual(failures, [])
        self.assertTrue(all(node["model"] == "gpt-5.6-luna" for node in plan["nodes"]))

    def test_parallel_plan_returns_after_ready_branches_and_merge(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            plan = self.plan(cache_dir)
            plan["complexity"] = "complex"
            plan["topology"] = "parallel"
            direct = plan["nodes"][0]
            condition = direct["routing_condition"]
            profile = {"routing_condition": condition, "task_summary": direct["task_summary"], "candidate_ladder": direct["candidate_ladder"], "static_suggestion": direct["static_suggestion"], "hard_floor": direct["hard_floor"], "trial": False, "routing_recommendation": direct["routing_recommendation"]}
            plan["nodes"] = [{"id": "branch-a", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return A.", "sandbox": "read-only"}, {"id": "branch-b", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Return B.", "sandbox": "read-only"}, {"id": "merge", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": ["branch-a", "branch-b"], "prompt": "Merge A and B.", "sandbox": "read-only", **profile}, {"id": "ending-verify", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-terra", "effort": "low", "dependencies": ["merge"], "prompt": "Run post-result verification.", "sandbox": "read-only"}]
            plan["main_result_node"] = "merge"
            calls = []
            def fake_run_node(node, cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
                calls.append(node["id"])
                result_path = cache_dir / f"{node['id']}-result.md"
                receipt_path = cache_dir / f"{node['id']}-receipt.json"
                result_path.write_text(node["id"] + "\n", encoding="utf-8")
                receipt_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "model": node["model"], "effort": node["effort"], "status": "pass", "receipt_path": str(receipt_path), "result_path": str(result_path), "tokens": {}, "process_elapsed_ms": 1}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", return_value={"status": "recorded"}):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(set(calls[:2]), {"branch-a", "branch-b"})
        self.assertEqual(calls[2:], ["merge"])
        self.assertEqual(manifest["status"], "pass")

    def test_ending_handoff_runs_ending_optimization_then_targeted_verifier_by_wave(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan_with_ending_optimization(cache_dir)
            route_run_id = "route-end-wave-001"
            handoff = {
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
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
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md"), "worker_identity": "main-worker"},
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
            def fake_record_event(result_path, verify_level, verify_status, receipt, run_id, main_node, project_root, execution_domain=None):
                recorded_calls.append(SimpleNamespace(verify_level=verify_level, verify_status=verify_status, failure_class="none" if verify_status == "pass" else ("quality" if verify_status == "fail" else "execution"), run_id=run_id, receipt=receipt))
                return {"status": "recorded"}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", side_effect=fake_record_event):
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
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md"), "worker_identity": "main-worker"},
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
            def fake_record_event(result_path, verify_level, verify_status, receipt, run_id, main_node, project_root, execution_domain=None):
                recorded_calls.append(SimpleNamespace(verify_level=verify_level, verify_status=verify_status, failure_class="none" if verify_status == "pass" else ("quality" if verify_status == "fail" else "execution"), run_id=run_id, receipt=receipt))
                return {"status": "recorded"}
            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", side_effect=fake_record_event):
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
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
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
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
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

            def fake_record_event(result_path, verify_level, verify_status, receipt, run_id, main_node, project_root, execution_domain=None):
                recorded_calls.append(SimpleNamespace(verify_level=verify_level, verify_status=verify_status, failure_class="none" if verify_status == "pass" else ("quality" if verify_status == "fail" else "execution"), run_id=run_id, receipt=receipt))
                return {"status": "recorded"}

            with patch.object(module, "run_node", side_effect=fake_run_node), patch.object(module, "_run_record", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_level, "real")
        self.assertEqual(recorded_calls[0].verify_status, "fail")
        self.assertEqual(recorded_calls[0].failure_class, "quality")
        self.assertEqual(recorded_calls[0].run_id, route_run_id)
        self.assertEqual(recorded_calls[0].receipt, str(cache_dir / "direct-receipt.json"))
        self.assertTrue(manifest["reopen_required"])
        self.assertTrue(manifest["notification_required"])

    def test_ending_handoff_records_unknown_status_when_non_targeted_marker_missing_or_malformed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True, exist_ok=True)
            plan = self.plan(cache_dir)
            route_run_id = "route-end-unknown-001"
            handoff = {
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": route_run_id,
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
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

            def fake_record_event(result_path, verify_level, verify_status, receipt, run_id, main_node, project_root, execution_domain=None):
                recorded_calls.append(SimpleNamespace(verify_level=verify_level, verify_status=verify_status, failure_class="none" if verify_status == "pass" else ("quality" if verify_status == "fail" else "execution"), run_id=run_id, receipt=receipt))
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
            )), patch.object(module, "_run_record", side_effect=fake_record_event):
                manifest = module.run_ending_handoff(handoff_path)
        self.assertEqual(manifest["status"], "fail")
        self.assertEqual(len(recorded_calls), 1)
        self.assertEqual(recorded_calls[0].verify_status, "unknown")
        self.assertEqual(recorded_calls[0].failure_class, "execution")
        self.assertTrue(manifest["reopen_required"])
        self.assertTrue(manifest["notification_required"])

    def test_plan_rejects_explicit_history_only_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "code_unspecified"
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("execution_domain is non-active: code_unspecified" in failure for failure in failures))

    def test_release_main_result_requires_completed_main_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            handoff = {
                "schema_version": 2,
                "route_run_id": "route-release-miss",
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "plan": {
                    "nodes": [{"id": "main-result"}],
                },
                "completed": [
                    {"id": "main-result", "status": "fail", "phase": "result", "receipt_path": str(root / "main-receipt.json"), "result_path": str(root / "main-result.md")},
                ],
                "main_result_node": "main-result",
            }
            (root / "main-result.md").write_text("RESULT=12\n", encoding="utf-8")
            handoff_path = root / "ending-handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            release = module._release_main_result(handoff)
        self.assertEqual(release["status"], "fail")
        self.assertEqual(release.get("failures"), ["main result must complete before release"])

    def test_release_main_result_persists_ack_and_marks_handoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            handoff = {
                "schema_version": 2,
                "route_run_id": "route-release-pass",
                "cache_dir": str(root),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "plan": {
                    "nodes": [],
                },
                "completed": [
                    {"id": "main-result", "status": "pass", "phase": "result", "receipt_path": str(root / "main-receipt.json"), "result_path": str(root / "main-result.md")},
                ],
                "main_result_node": "main-result",
            }
            (root / "main-result.md").write_text("RESULT=12\n", encoding="utf-8")
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

    def test_plan_accepts_complex_rust_with_terra(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust"
            plan["nodes"][0]["language"] = "rust"
            plan["nodes"][0]["skill"] = "code-skill"
            plan["nodes"][0]["model"] = "gpt-5.6-luna"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "rust"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "code-skill"
            self.refresh_recommendation(plan["nodes"][0])
            with self._with_rust_domain() as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertEqual(failures, [])

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
            self.refresh_recommendation(plan["nodes"][0])
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

    def test_plan_rejects_complex_rust_with_spark(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["nodes"][0]["execution_domain"] = "rust"
            plan["nodes"][0]["language"] = "rust"
            plan["nodes"][0]["skill"] = "code-skill"
            plan["nodes"][0]["model"] = "gpt-5.3-codex-spark"
            plan["nodes"][0]["routing_condition"]["execution_domain"] = "rust"
            plan["nodes"][0]["routing_condition"]["owning_skill"] = "code-skill"
            self.refresh_recommendation(plan["nodes"][0])
            with self._with_rust_domain() as synthetic_skills_root:
                failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root, synthetic_skills_root)
        self.assertTrue(any("shared active GPT-5.6 ladder" in failure for failure in failures))

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
                    "verification_shape": "real",
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
                _args.result_output.write_text("RESULT=rust\n", encoding="utf-8")
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
                "schema_version": 2,
                "cwd": str(root.resolve()),
                "state_db": str((root / "state.db").resolve()),
                "entry": {"model": "gpt-5.6-terra", "effort": "low"},
                "route_run_id": "route-unreleased",
                "plan": plan,
                "completed": [
                    {"id": "direct", "status": "pass", "phase": "result", "model": "gpt-5.6-luna", "effort": "low", "receipt_path": str(cache_dir / "direct-receipt.json"), "result_path": str(cache_dir / "direct-result.md")},
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
            "schema_version": 2,
            "cache_dir": str(cache_dir),
            "route_run_id": "route-release",
            "entry": {"model": "gpt-5.6-terra", "effort": "low"},
            "plan": {
                "nodes": [],
            },
            "completed": [
                {"id": "main-result", "status": "pass", "phase": "result", "receipt_path": str(cache_dir / "main-receipt.json"), "result_path": str(cache_dir / "main-result.md")},
            ],
            "main_result_node": "main-result",
        }
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "main-result.md").write_text("RESULT=12\n", encoding="utf-8")
        release = module._release_main_result(json.loads(json.dumps(release_plan)))
        self.assertEqual(release["status"], "pass")
        handoff["route_run_id"] = "route-release-mismatch"
        mismatch_path = cache_dir / "ending-handoff-mismatch.json"
        mismatch_path.write_text(json.dumps(handoff), encoding="utf-8")
        with patch.object(module, "run_node", side_effect=AssertionError("run_node should not execute")):
            mismatched = module.run_ending_handoff(mismatch_path)
        self.assertEqual(mismatched["status"], "fail")
        self.assertTrue(any("ending handoff release does not match route_run_id" in failure for failure in mismatched["failures"]))

    def test_grounded_read_only_answer_rejects_redundant_result_fanout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            main_node = plan["nodes"][0]
            main_node["routing_condition"]["task_family"] = "grounded"
            main_node["dependencies"] = ["source-branch"]
            self.refresh_recommendation(main_node)
            plan["nodes"].insert(0, {"id": "source-branch", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Read the same source again.", "sandbox": "read-only"})
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertTrue(any("grounded read-only answers allow multiple result nodes" in failure for failure in failures))

    def test_grounded_read_only_answer_allows_disjoint_dependency_only_merge(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            main_node = plan["nodes"][0]
            main_node["routing_condition"]["task_family"] = "grounded"
            main_node["dependencies"] = ["source-branch"]
            main_node["reads_dependency_results_only"] = True
            self.refresh_recommendation(main_node)
            plan["nodes"].insert(0, {"id": "source-branch", "phase": "result", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Read one disjoint source.", "source_allowlist": ["source-a"], "sandbox": "read-only"})
            failures = module.validate_plan(plan, "gpt-5.6-terra", "low", root)
        self.assertEqual(failures, [])

    def test_run_plan_stops_before_node_when_first_result_deadline_is_exhausted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.plan(root / "work" / "cache" / "route")
            plan["first_result_timeout_seconds"] = 1
            with patch.object(module.time, "monotonic", side_effect=[0, 2, 3]), patch.object(module, "run_node", side_effect=AssertionError("deadline must stop execution")):
                manifest = module.run_plan(plan, "gpt-5.6-terra", "low", root, history_path=root / "history.json")
        self.assertEqual(manifest["status"], "fail")
        self.assertTrue(manifest["deadline_exhausted"])
        self.assertIn("first-result deadline exhausted", manifest["failures"])
        self.assertEqual(manifest["nodes"], [])

    def test_read_only_node_uses_minimal_config_unless_explicitly_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True)
            node = self.plan(cache_dir)["nodes"][0]
            observed = []

            def fake_run_receipt(args, _prompt):
                observed.append(args.ignore_user_config)
                args.result_output.write_text("RESULT=12\n", encoding="utf-8")
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "pass", "failure_class": None, "route_attempts": [], "process_elapsed_ms": 1, "tokens": {"total_tokens": 1}}

            with patch.object(module.receipt_module, "run_receipt", side_effect=fake_run_receipt):
                module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
                node["load_user_config"] = True
                module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
        self.assertEqual(observed, [True, False])

    def test_compact_run_plan_manifest_omits_nodes_and_embedded_plan(self):
        compact = module.compact_run_plan_manifest({"schema_version": 1, "status": "pass", "failures": [], "manifest_path": "/tmp/manifest", "main_result_path": "/tmp/result", "ending_handoff_path": "/tmp/handoff", "route_run_id": "route-1", "first_result_elapsed_ms": 12, "deadline_exhausted": False, "nodes": [{"private": "large"}], "plan": {"private": "large"}})
        self.assertEqual(set(compact), {"schema_version", "status", "failures", "manifest_path", "main_result_path", "ending_handoff_path", "route_run_id", "first_result_elapsed_ms", "deadline_exhausted", "result_published", "notification_required", "reopen_required"})
        self.assertNotIn("nodes", compact)
        self.assertNotIn("plan", compact)

    def test_dispatcher_authorizes_repair_and_ending_roles_in_entry_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "route"
            cache_dir.mkdir(parents=True)
            nodes = [
                {"id": "repair-guard", "phase": "result", "purpose": "repair", "skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "Repair.", "sandbox": "read-only"},
                {"id": "ending-guard", "phase": "ending", "skill": "verify-skill", "model": "gpt-5.6-luna", "effort": "low", "dependencies": [], "prompt": "End.", "sandbox": "read-only"},
            ]
            observed = []

            def guarded_run(args, _prompt):
                authorization = module.receipt_module.authorize_receipt_run(args)
                observed.append((args.node_role, authorization["authorization_source"]))
                marker = "ENDING_TASK=PASS\n" if args.node_role == "ending" else "REPAIRED\n"
                args.result_output.write_text(marker, encoding="utf-8")
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "pass", "failure_class": None, "route_attempts": [], "process_elapsed_ms": 1, "tokens": {"total_tokens": 1}}

            with patch.dict(os.environ, {module.receipt_module.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module.receipt_module, "run_receipt", side_effect=guarded_run):
                for node in nodes:
                    record = module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
                    self.assertEqual(record["status"], "pass")
        self.assertEqual(observed, [("repair", "dispatcher"), ("ending", "dispatcher")])

    def test_dispatcher_entry_context_runs_only_fresh_adaptive_result_recommendation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            valid_cache = root / "work" / "cache" / "valid"
            valid_cache.mkdir(parents=True)
            valid_node = self.plan(valid_cache)["nodes"][0]
            valid_node["_project_root"] = str(root)
            current_recommendation = deepcopy(valid_node["routing_recommendation"])
            observed_sources = []

            def guarded_model_stub(args, _prompt):
                authorization = module.receipt_module.authorize_receipt_run(args)
                observed_sources.append(authorization["authorization_source"])
                args.result_output.write_text("RESULT=12\n", encoding="utf-8")
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": f"{args.model}|{args.effort}", "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": f"{args.model}|{args.effort}", "status": "pass", "failure_class": None, "route_attempts": [], "process_elapsed_ms": 1, "tokens": {"total_tokens": 1}}

            with patch.dict(os.environ, {module.receipt_module.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module, "_obsidian_recommendation_and_proof", return_value=({"selected_pair": "gpt-5.6-luna|low"}, current_recommendation)) as recommend_mock, patch.object(module.receipt_module, "run_receipt", side_effect=guarded_model_stub) as model_stub:
                valid_record = module.run_node(valid_node, valid_cache, {}, root / "state.sqlite", root)
            self.assertEqual(valid_record["status"], "pass")
            self.assertEqual(recommend_mock.call_count, 1)
            self.assertEqual(model_stub.call_count, 1)
            self.assertEqual(observed_sources, ["dispatcher-adaptive-recommendation"])

            forged_cache = root / "work" / "cache" / "forged"
            forged_cache.mkdir(parents=True)
            forged_node = deepcopy(valid_node)
            forged_node["model"] = "gpt-5.6-terra"
            forged_node["effort"] = "low"
            forged_node["routing_recommendation"]["selected_pair"] = "gpt-5.6-terra|low"
            with patch.dict(os.environ, {module.receipt_module.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module, "_obsidian_recommendation_and_proof", return_value=({"selected_pair": "gpt-5.6-luna|low"}, current_recommendation)), patch.object(module.receipt_module, "run_receipt") as forged_model_stub:
                forged_record = module.run_node(forged_node, forged_cache, {}, root / "state.sqlite", root)
            forged_receipt = json.loads((forged_cache / "direct-receipt.json").read_text(encoding="utf-8"))
        forged_model_stub.assert_not_called()
        self.assertEqual(forged_record["status"], "fail")
        self.assertEqual(forged_receipt["failure_class"], "authorization")
        self.assertEqual(forged_receipt["authorization_reason"], "dispatcher_adaptive_recommendation_invalid")
        self.assertEqual(len(forged_receipt["route_attempts"]), 1)

    def test_dispatcher_injects_spark_then_uses_selected_5_6_on_zero_result_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_dir = root / "work" / "cache" / "spark"
            cache_dir.mkdir(parents=True)
            node = self.plan(cache_dir)["nodes"][0]
            node["_project_root"] = str(root)
            proof = deepcopy(node["routing_recommendation"])
            recommendation = {"selected_pair": "gpt-5.6-luna|low", "attempt_pair": "gpt-5.3-codex-spark|low", "active_fallback_pair": "gpt-5.6-luna|low"}
            calls = []

            def routed_stub(args, _prompt):
                pair = f"{args.model}|{args.effort}"
                calls.append(pair)
                if pair.startswith("gpt-5.3-codex-spark|"):
                    return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": pair, "status": "fail", "failure_class": "availability", "turn_completed": False, "pre_execution_failure": True, "route_attempts": [{"requested_pair": pair, "tokens": {"total_tokens": 0}, "pre_execution_failure": True}], "process_elapsed_ms": 1, "tokens": {"total_tokens": 0}}
                args.result_output.write_text("FALLBACK RESULT\n", encoding="utf-8")
                return {"schema_version": 1, "requested_model": args.model, "requested_effort": args.effort, "requested_pair": pair, "resolved_model": args.model, "resolved_effort": args.effort, "effective_model": args.model, "effective_pair": pair, "status": "pass", "failure_class": None, "turn_completed": True, "model_match": True, "effort_match": True, "route_attempts": [{"requested_pair": pair, "effective_pair": pair, "tokens": {"total_tokens": 4}}], "process_elapsed_ms": 2, "tokens": {"total_tokens": 4}}

            with patch.dict(os.environ, {module.receipt_module.ENTRY_CONTEXT_ENV: "1"}, clear=False), patch.object(module, "_obsidian_recommendation_and_proof", return_value=(recommendation, proof)), patch.object(module.receipt_module, "run_receipt", side_effect=routed_stub):
                record = module.run_node(node, cache_dir, {}, root / "state.sqlite", root)
            receipt = json.loads((cache_dir / "direct-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(calls, ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low"])
        self.assertEqual(record["status"], "pass")
        self.assertEqual(receipt["priority_attempt_pair"], "gpt-5.3-codex-spark|low")
        self.assertEqual(receipt["operational_failure_pairs"], ["gpt-5.3-codex-spark|low"])
        self.assertEqual(len(receipt["route_attempts"]), 2)


if __name__ == "__main__":
    unittest.main()

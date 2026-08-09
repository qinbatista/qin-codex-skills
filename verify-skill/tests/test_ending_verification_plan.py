import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "ending_verification_plan.py"
SPEC = importlib.util.spec_from_file_location("ending_verification_plan", SCRIPT_PATH)
PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLAN)


def origin_session(root, project_id="project-123"):
    return {"thread_id": "source-session-001", "host_id": "host-local", "project_id": project_id, "project_root": str(root)}


def build_plan(root, task_name, task_score, checks, project_id="project-123", project_memory_closeout=None):
    return PLAN.build_plan(root, task_name, task_score, checks, origin_session(root, project_id), project_memory_closeout)


class EndingVerificationPlanTests(unittest.TestCase):
    def test_score_bands_scope_checks_but_keep_fixed_spark_xhigh(self):
        routes = [PLAN.pair_for_score(score) for score in (12, 35, 60, 90)]
        self.assertEqual([route["complexity_band"] for route in routes], ["small", "standard", "complex", "advanced"])
        self.assertEqual({route["selected_pair"] for route in routes}, {"gpt-5.3-codex-spark|xhigh"})
        self.assertTrue(all(route["selection_basis"] == "ending_fast_primary" for route in routes))
        self.assertTrue(all(route["score_controls"] == "check_scope_and_classification_only" for route in routes))
        self.assertTrue(all(route["quality_failure_model_fallback"] is False for route in routes))

    def test_missing_spark_capability_uses_only_the_registry_floor(self):
        registry = json.loads(json.dumps(PLAN._registry()))
        registry["catalog_models"] = [model for model in registry["catalog_models"] if model["id"] != "gpt-5.3-codex-spark"]
        registry["ending_fast"] = {
            "selection_basis": "ending_fast_primary",
            "primary_pair": registry["role_pairs"]["floor"],
            "availability_fallback_pair": None,
            "fallback_policy": "availability_only",
            "score_scope": "check_only",
        }
        route = PLAN.pair_for_score(90, registry)
        self.assertEqual(route["complexity_band"], "advanced")
        self.assertEqual(route["selected_pair"], registry["role_pairs"]["floor"])
        self.assertEqual(route["primary_selection_reason"], "primary_pair_not_in_registry")
        self.assertEqual(route["approved_pairs"], [registry["role_pairs"]["floor"]])

    def test_plan_keeps_bounded_checks_for_one_task_ending(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])
        self.assertEqual(plan["execution"], "one_persistent_ending_runs_all_checks")
        self.assertEqual(plan["schema_version"], 7)
        self.assertEqual(plan["project_memory_closeout"], {"mode": "none"})
        self.assertNotIn("title", plan)
        self.assertNotIn("thread_target", plan)
        self.assertNotIn("terminal_thread_policy", plan)
        thread_fields = {"title", "thread_target", "terminal_thread_policy", "tool", "arguments", "launch_candidates"}
        self.assertTrue(all(thread_fields.isdisjoint(task) for task in plan["ending_tasks"]))
        self.assertTrue(all("terminal_thread_policy" not in task["on_failure"] for task in plan["ending_tasks"]))
        legacy_launchable_checks = [task for task in plan["ending_tasks"] if {"title", "thread_target"}.issubset(task)]
        self.assertEqual(legacy_launchable_checks, [])
        self.assertEqual({task["selected_pair"] for task in plan["ending_tasks"]}, {"gpt-5.3-codex-spark|xhigh"})
        self.assertEqual(plan["ending_model_policy"]["availability_fallback_pair"], "gpt-5.6-luna|low")
        self.assertEqual(plan["origin_session"]["thread_id"], "source-session-001")
        self.assertEqual(plan["repair_policy"]["action"], "send_repair_prompt_to_origin_session_then_fresh_ending")

    def test_durable_plan_carries_sanitized_project_memory_intent_and_consistency_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "runtime.py").write_text("value = 1\n", encoding="utf-8")
            closeout = {"mode": "durable", "module": "runtime", "scope": "code", "change_kind": "edit", "summary": "Added the runtime value.", "reason": "The requested behavior needs one owned value.", "result": "The runtime now exposes the verified value.", "files": ["runtime.py"], "symbols": ["value"], "decisions": ["Keep ownership in runtime.py."], "risks": ["Future callers must preserve the value contract."]}
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "memory", 35, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], project_memory_closeout=closeout)), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending", "project-123")
        self.assertEqual(launch["project_memory_closeout"]["mode"], "durable")
        self.assertEqual(launch["project_memory_closeout"]["files"], ["runtime.py"])
        self.assertTrue(launch["launch_requests"][0]["memory_consistency_output"].endswith("task-ending.project-memory-consistency.json"))
        prompt = launch["launch_requests"][0]["arguments"]["prompt"]
        self.assertIn("aligned, no_prior_memory, memory_record_defect, memory_projection_defect, skill_contract_defect, execution_drift, or insufficient_evidence", prompt)
        self.assertIn("only memory_projection_defect may reconcile", prompt)
        self.assertIn("three independent flows", prompt)

    def test_code_memory_closeout_requires_a_symbol(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            closeout = {"mode": "durable", "module": "runtime", "scope": "code", "change_kind": "edit", "summary": "Added runtime behavior.", "reason": "The task requires it.", "result": "The behavior is available.", "files": ["runtime.py"]}
            with self.assertRaisesRegex(ValueError, "requires at least one symbol"):
                build_plan(root, "memory", 35, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], project_memory_closeout=closeout)

    def test_memory_closeout_rejects_raw_or_unknown_process_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            closeout = {"mode": "durable", "module": "runtime", "scope": "code", "change_kind": "edit", "summary": "Added runtime behavior.", "reason": "The task requires it.", "result": "The behavior is available.", "files": ["runtime.py"], "symbols": ["run"], "raw_prompt": "private prompt", "process_contract": "raw instructions"}
            with self.assertRaisesRegex(ValueError, "unknown fields"):
                build_plan(root, "memory", 35, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], project_memory_closeout=closeout)

    def test_memory_closeout_rejects_non_array_files_and_non_string_values(self):
        base = {"mode": "durable", "module": "runtime", "scope": "code", "change_kind": "edit", "summary": "Added runtime behavior.", "reason": "The task requires it.", "result": "The behavior is available.", "files": ["runtime.py"], "symbols": ["run"]}
        invalid_updates = (
            ({"files": "runtime.py"}, "files must be a JSON string array"),
            ({"files": [1]}, "files must be a JSON string array"),
            ({"symbols": [{"raw": "value"}]}, "symbols must contain only strings"),
            ({"decisions": [7]}, "decisions must contain only strings"),
            ({"summary": {"raw": "value"}}, "summary must be a string"),
            ({"result": "Observed /" + "Users/example/private/result.txt"}, "result contains private or secret-like content"),
        )
        for update, error in invalid_updates:
            with self.subTest(update=update), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                closeout = {**base, **update}
                with self.assertRaisesRegex(ValueError, error):
                    build_plan(root, "memory", 35, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], project_memory_closeout=closeout)

    def test_run_check_executes_real_command_and_records_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan = build_plan(root, "real", 20, [{"name": "test", "command": ["python3", "-c", "print('REAL PASS')"], "acceptance": "The real command prints REAL PASS."}])
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            evidence = PLAN.run_check(plan_path, "test", evidence_path)
        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["exit_code"], 0)
        self.assertIn("REAL PASS", evidence["stdout"])
        self.assertEqual(evidence["repair_context"]["origin_session"]["thread_id"], "source-session-001")

    def test_failed_real_command_emits_exact_repair_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan = build_plan(root, "repair", 45, [{"name": "unit", "command": ["python3", "-c", "import sys; print('broken', file=sys.stderr); raise SystemExit(7)"], "acceptance": "The repair check exits successfully."}])
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            evidence = PLAN.run_check(plan_path, "unit", evidence_path)
        self.assertEqual(evidence["status"], "fail")
        self.assertEqual(evidence["repair_handoff"]["action"], "send_repair_prompt_to_origin_session_then_fresh_ending")
        self.assertEqual(evidence["repair_handoff"]["origin_session"]["thread_id"], "source-session-001")
        self.assertEqual(evidence["repair_handoff"]["repair_dispatch"]["tool"], "codex_app__send_message_to_thread")
        self.assertEqual(evidence["repair_handoff"]["repair_dispatch"]["arguments"]["threadId"], "source-session-001")
        self.assertEqual(evidence["repair_handoff"]["repair_dispatch"]["arguments"]["hostId"], "host-local")
        self.assertIn("Original acceptance contract: The repair check exits successfully.", evidence["repair_handoff"]["repair_prompt"])
        self.assertIn("parent will launch a fresh projectless Ending", evidence["repair_handoff"]["repair_prompt"])
        self.assertEqual(evidence["repair_handoff"]["terminal_thread_policy"]["fail"], "keep_visible")
        self.assertEqual(evidence["repair_handoff"]["error"]["exit_code"], 7)
        self.assertIn("broken", evidence["repair_handoff"]["error"]["stderr"])

    def test_launch_spec_requires_one_projectless_thread_for_all_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")
        self.assertEqual(launch["execution"], "host_persistent_create_thread")
        self.assertEqual(launch["required_launch_count"], 1)
        self.assertEqual({item["tool"] for item in launch["launch_requests"]}, {"codex_app__create_thread"})
        self.assertEqual(launch["project_binding"]["project_root"], str(root.resolve()))
        self.assertEqual(launch["origin_session"]["thread_id"], "source-session-001")
        self.assertTrue(all(item["arguments"]["target"] == {"type": "projectless"} for item in launch["launch_requests"]))
        self.assertTrue(all(item["arguments"]["prompt"].startswith("ENDING_TASK_WORKER\n") for item in launch["launch_requests"]))
        self.assertTrue(all("Verification plan relative to project root: plan.json" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertEqual(launch["launch_requests"][0]["check_id"], "task-ending")
        self.assertEqual(launch["launch_requests"][0]["title"], "End Task-routing")
        self.assertEqual(launch["launch_requests"][0]["thread_target"], {"type": "projectless"})
        self.assertEqual(launch["launch_requests"][0]["terminal_thread_policy"], {"pass": "keep_visible", "fail": "keep_visible", "blocked": "keep_visible"})
        self.assertEqual(launch["launch_requests"][0]["check_ids"], ["unit", "integration"])
        self.assertEqual(set(launch["launch_requests"][0]["evidence_outputs"]), {"unit", "integration"})
        self.assertIn("Checks and evidence outputs:", launch["launch_requests"][0]["arguments"]["prompt"])
        self.assertIn("Personal memory candidates output relative to project root: Cache/tests/ending-evidence/", launch["launch_requests"][0]["arguments"]["prompt"])
        self.assertTrue(all(str(root / "plan.json") not in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("Never call set_thread_archived" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("structured model_assessment" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("If no durable candidate exists" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("Origin producer session (immutable)" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("automatically submit the generated repair_prompt" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertEqual(
            [f"{item['arguments']['model']}|{item['arguments']['thinking']}" for item in launch["launch_requests"]],
            [item["selected_pair"] for item in launch["launch_requests"]],
        )
        request = launch["launch_requests"][0]
        self.assertEqual([candidate["pair"] for candidate in request["launch_candidates"]], ["gpt-5.3-codex-spark|xhigh", "gpt-5.6-luna|low"])
        self.assertIn("scheduler_unavailable", request["availability_fallback_reasons"])
        self.assertIn("required_modality_unavailable", request["availability_fallback_reasons"])
        self.assertIn("Correctness, quality, protocol, timeout, or command execution failures never change the Ending pair.", request["arguments"]["prompt"])

    def test_launch_audit_requires_the_single_task_ending_acknowledgement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            not_launched = PLAN.audit_launches(launch_path, state_path)
            PLAN.acknowledge_launch(launch_path, "task-ending", "thread-ending", "host-ending", "project-123", state_path)
            passed = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(not_launched["status"], "blocked")
        self.assertEqual(not_launched["end_task_trigger_rate"], "0%")
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(passed["end_task_trigger_rate"], "100%")
        self.assertEqual(passed["launched_count"], 1)

    def test_availability_fallback_requires_an_approved_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"]},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"]},
            ])), encoding="utf-8")
            launch_path.write_text(json.dumps(PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "sanitized availability reason"):
                PLAN.acknowledge_launch(launch_path, "task-ending", "fallback-thread", "host", "project-123", state_path, "gpt-5.6-luna|low")
            acknowledged = PLAN.acknowledge_launch(
                launch_path,
                "task-ending",
                "fallback-thread",
                "host",
                "project-123",
                state_path,
                "gpt-5.6-luna|low",
                "primary_model_unavailable",
            )
            passed = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(acknowledged["selected_pair"], "gpt-5.6-luna|low")
        self.assertEqual(acknowledged["availability_fallback_reason"], "primary_model_unavailable")
        self.assertEqual(passed["status"], "pass")

    def test_requirement_mismatch_turns_a_passing_command_into_source_session_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan = build_plan(root, "mismatch", 20, [{"name": "artifact", "command": ["python3", "-c", "print('command pass')"], "acceptance": "The final artifact contains the approved construction line."}])
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            PLAN.run_check(plan_path, "artifact", evidence_path)
            evidence = PLAN.record_requirement_mismatch(evidence_path, "The command passed, but the final artifact omits the approved construction line.")
        self.assertEqual(evidence["status"], "fail")
        self.assertEqual(evidence["failure_class"], "correctness")
        self.assertEqual(evidence["repair_handoff"]["action"], "send_repair_prompt_to_origin_session_then_fresh_ending")
        self.assertIn("omits the approved construction line", evidence["repair_handoff"]["repair_prompt"])

    def test_launch_requires_the_original_source_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(PLAN.build_plan(root, "unbound", 20, [{"name": "unit", "command": ["python3", "-c", "print('unit')"]}])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "origin_session is required"):
                PLAN.build_launch_spec(plan_path, root / "Cache" / "tests" / "ending-evidence", "project-123")


if __name__ == "__main__":
    unittest.main()

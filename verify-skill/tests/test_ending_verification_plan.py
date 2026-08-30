import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "ending_verification_plan.py"
SPEC = importlib.util.spec_from_file_location("ending_verification_plan", SCRIPT_PATH)
PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLAN)


def origin_session(root, project_id="project-123"):
    return {"thread_id": "source-session-001", "host_id": "host-local", "project_id": project_id, "project_root": str(root)}


def build_plan(root, task_name, task_score, checks, project_id="project-123", project_memory_closeout=None, repair_of_lifecycle_id=""):
    return PLAN.build_plan(root, task_name, task_score, checks, origin_session(root, project_id), project_memory_closeout, repair_of_lifecycle_id)


def final_producer_receipt(root, **updates):
    receipt = {"status": "pass", "result_published": True, "turn_completed": True, "node_type": "locked-route-node", "node_role": "result-producer", "final_aggregate_receipt": True, "all_result_nodes_settled": True, "subprocesses_settled": True, "ending_launch_ready": True, "aggregate_result_state": "single_result_released", "aggregate_result_node_count": 1}
    receipt.update(updates)
    path = root / "producer-receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path


def build_launch_spec(root, plan_path, evidence_dir, project_id="project-123", producer_receipt=None, repair_of_lifecycle_id="", backend_capabilities=None):
    return PLAN.build_launch_spec(plan_path, evidence_dir, project_id, producer_receipt or final_producer_receipt(root), repair_of_lifecycle_id, backend_capabilities)


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
        self.assertEqual(route["approved_pairs"][0], registry["role_pairs"]["floor"])
        self.assertIn(registry["role_pairs"]["frontier_complex"], route["approved_pairs"])

    def test_restriction_records_default_five_hour_cooldown_and_launch_skips_cooling_spark(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / "controller-restrictions.json"
            recorded_at = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)
            restriction = PLAN.record_controller_restriction("gpt-5.3-codex-spark|xhigh", "model_quota_limit", store, now=recorded_at)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "cooldown", 35, [{"name": "unit", "command": ["python3", "-c", "print('ok')"]}])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending", "project-123", final_producer_receipt(root), restriction_store=store, now=recorded_at + timedelta(minutes=1))
            restored = PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending", "project-123", final_producer_receipt(root), restriction_store=store, now=recorded_at + timedelta(hours=6))
        self.assertEqual(restriction["restriction"]["cooldown_until"], (recorded_at + timedelta(hours=5)).isoformat())
        self.assertEqual(restriction["restriction"]["retry_at"], (recorded_at + timedelta(hours=5)).isoformat())
        self.assertEqual(restriction["restriction"]["model"], "gpt-5.3-codex-spark")
        self.assertNotEqual(launch["launch_requests"][0]["selected_pair"], "gpt-5.3-codex-spark|xhigh")
        self.assertEqual(restored["launch_requests"][0]["selected_pair"], "gpt-5.3-codex-spark|xhigh")

    def test_material_update_receipt_requires_durable_project_memory_closeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            receipt = final_producer_receipt(root, project_memory_closeout_required=True, material_update_classification="structural")
            plan_path.write_text(json.dumps(build_plan(root, "material", 35, [{"name": "unit", "command": ["python3", "-c", "print('ok')"]}])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "durable project_memory_closeout"):
                PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending", "project-123", receipt)
            closeout = {"mode": "durable", "module": "ending.lifecycle", "summary": "Ending lifecycle changed.", "reason": "The structural update requires durable lifecycle memory.", "result": "The lifecycle now enforces durable closeout.", "files": ["runtime.py"], "symbols": ["runtime"], "change_kind": "edit", "scope": "code"}
            plan_path.write_text(json.dumps(build_plan(root, "material", 35, [{"name": "unit", "command": ["python3", "-c", "print('ok')"]}], project_memory_closeout=closeout)), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending", "project-123", receipt)
        self.assertEqual(launch["project_memory_closeout"]["mode"], "durable")

    def test_plan_keeps_bounded_checks_for_one_task_ending(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])
        self.assertEqual(plan["execution"], "one_persistent_ending_runs_all_checks")
        self.assertEqual(plan["schema_version"], 12)
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
        self.assertEqual(plan["repair_policy"]["action"], "create_isolated_projectless_repair_then_fresh_ending")
        self.assertEqual(plan["repair_policy"]["max_repair_attempts"], PLAN.MAX_ENDING_REPAIR_ROUNDS)
        self.assertTrue(all(task["on_failure"]["max_repair_attempts"] == PLAN.MAX_ENDING_REPAIR_ROUNDS for task in plan["ending_tasks"]))

    def test_today_replay_routes_only_semantic_checks_to_capability_workers(self):
        checks = [
            {"name": "file-state", "command": ["python3", "-c", "print('file')"], "complexity_score": 12, "verification_surface": "file_state"},
            {"name": "runtime", "command": ["python3", "-c", "print('runtime')"], "complexity_score": 55, "verification_surface": "runtime_semantics", "required_skills": ["domain-runtime-skill"]},
            {"name": "code-quality", "command": ["python3", "-c", "print('code')"], "complexity_score": 45, "verification_surface": "code_quality"},
            {"name": "ui", "command": ["python3", "-c", "print('ui')"], "complexity_score": 60, "verification_surface": "ui_visual"},
            {"name": "artifact", "command": ["python3", "-c", "print('artifact')"], "complexity_score": 35, "verification_surface": "artifact_visual"},
            {"name": "prompt", "command": ["python3", "-c", "print('prompt')"], "complexity_score": 80, "verification_surface": "prompt_semantics"},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan = build_plan(root, "today-replay", 60, checks)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending")
        by_id = {check["check_id"]: check for check in plan["ending_tasks"]}
        self.assertEqual(by_id["file-state"]["execution_mode"], "spark_controller_direct")
        self.assertIsNone(by_id["file-state"]["worker_route"])
        self.assertEqual(by_id["runtime"]["worker_route"]["pair"], "gpt-5.6-terra|high")
        self.assertIn("domain-runtime-skill", by_id["runtime"]["required_skills"])
        self.assertEqual(by_id["code-quality"]["worker_route"]["pair"], "gpt-5.6-terra|medium")
        self.assertEqual(by_id["ui"]["worker_route"]["pair"], "gpt-5.6-sol|high")
        self.assertEqual(by_id["artifact"]["worker_route"]["pair"], "gpt-5.6-sol|high")
        self.assertEqual(by_id["prompt"]["worker_route"]["pair"], "gpt-5.6-sol|high")
        prompt = launch["launch_requests"][0]["arguments"]["prompt"]
        self.assertIn("ENDING_CHECK_WORKER", prompt)
        self.assertIn("final aggregate result is released", prompt)
        self.assertIn("compact continuation", prompt)
        self.assertNotIn("print('runtime')", prompt)

    def test_invalid_check_surface_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "verification_surface"):
                build_plan(root, "invalid", 35, [{"name": "invalid", "command": ["python3", "-c", "print('x')"], "verification_surface": "unknown"}])

    def test_saved_plan_repair_parent_propagates_to_launch_and_worker_command(self):
        repair_parent = "20260809T200317-f2d0890fdeb2"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = PLAN.main(["plan", "--project-root", str(root), "--task-name", "repair", "--complexity-score", "45", "--origin-session-json", json.dumps(origin_session(root)), "--repair-of-lifecycle-id", repair_parent, "--check-json", json.dumps({"name": "unit", "command": ["python3", "-c", "print('pass')"]}), "--output", str(plan_path)])
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending")
        self.assertEqual(code, 0)
        self.assertEqual(plan["repair_of_lifecycle_id"], repair_parent)
        self.assertEqual(plan["repair_policy"]["repair_of_lifecycle_id"], repair_parent)
        self.assertEqual(launch["repair_of_lifecycle_id"], repair_parent)
        self.assertEqual(launch["repair_policy"]["repair_of_lifecycle_id"], repair_parent)
        self.assertEqual(launch["launch_requests"][0]["repair_of_lifecycle_id"], repair_parent)
        for candidate in launch["launch_requests"][0]["launch_candidates"]:
            prompt = candidate["arguments"]["prompt"]
            self.assertIn(f"Repair parent: {repair_parent}", prompt)
            self.assertIn("Start the ledger with this exact --repair-of-lifecycle-id", prompt)
            self.assertIn("--late-repair-reason post-ending-verification-mismatch", prompt)
            self.assertEqual(prompt.count(repair_parent), 1)
            self.assertLess(len(prompt), 2300)

    def test_create_launches_cli_repair_flag_propagates_when_plan_has_no_parent(self):
        repair_parent = "20260809T201501-a1b2c3d4e5f6"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            plan_path.write_text(json.dumps(build_plan(root, "repair", 45, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}])), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = PLAN.main(["create-launches", "--plan", str(plan_path), "--evidence-dir", str(root / "Cache" / "remote-test" / "ending"), "--project-id", "project-123", "--producer-receipt", str(final_producer_receipt(root)), "--repair-of-lifecycle-id", repair_parent, "--output", str(launch_path)])
            launch = json.loads(launch_path.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(launch["repair_of_lifecycle_id"], repair_parent)
        self.assertEqual(launch["repair_policy"]["repair_of_lifecycle_id"], repair_parent)
        prompt = launch["launch_requests"][0]["arguments"]["prompt"]
        self.assertIn(f"Repair parent: {repair_parent}", prompt)
        self.assertIn("Start the ledger with this exact --repair-of-lifecycle-id", prompt)
        self.assertIn("--late-repair-reason post-ending-verification-mismatch", prompt)
        self.assertEqual(prompt.count(repair_parent), 1)
        self.assertLess(len(prompt), 2300)

    def test_repair_parent_rejects_malformed_invalid_timestamp_and_conflict(self):
        invalid_values = ["../20260809T200317-f2d0890fdeb2", "20260809T200317-F2D0890FDEB2", "20261340T250000-f2d0890fdeb2", "20260809T200317-f2d0890fdeb"]
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with self.assertRaisesRegex(ValueError, "repair_of_lifecycle_id"):
                    build_plan(root, "repair", 45, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], repair_of_lifecycle_id=invalid_value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "repair", 45, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], repair_of_lifecycle_id="20260809T200317-f2d0890fdeb2")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicts with the saved plan"):
                build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending", repair_of_lifecycle_id="20260809T201501-a1b2c3d4e5f6")

    def test_durable_plan_carries_sanitized_project_memory_intent_and_consistency_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "runtime.py").write_text("value = 1\n", encoding="utf-8")
            closeout = {"mode": "durable", "module": "runtime", "scope": "code", "change_kind": "edit", "summary": "Added the runtime value.", "reason": "The requested behavior needs one owned value.", "result": "The runtime now exposes the verified value.", "files": ["runtime.py"], "symbols": ["value"], "decisions": ["Keep ownership in runtime.py."], "risks": ["Future callers must preserve the value contract."]}
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "memory", 35, [{"name": "unit", "command": ["python3", "-c", "print('pass')"]}], project_memory_closeout=closeout)), encoding="utf-8")
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending")
        self.assertEqual(launch["project_memory_closeout"]["mode"], "durable")
        self.assertEqual(launch["project_memory_closeout"]["files"], ["runtime.py"])
        self.assertTrue(launch["launch_requests"][0]["memory_consistency_output"].endswith("task-ending.project-memory-consistency.json"))
        prompt = launch["launch_requests"][0]["arguments"]["prompt"]
        self.assertIn("aligned, no_prior_memory, memory_record_defect, memory_projection_defect, skill_contract_defect, execution_drift, or insufficient_evidence", prompt)
        self.assertIn("memory_record_defect, memory_projection_defect", prompt)
        self.assertIn("memory_consistency_output", prompt)

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
        self.assertEqual(evidence["repair_handoff"]["action"], "create_isolated_projectless_repair_then_fresh_ending")
        self.assertEqual(evidence["repair_handoff"]["origin_context"]["thread_id"], "source-session-001")
        self.assertEqual(evidence["repair_handoff"]["repair_launch"]["tool"], "codex_app__create_thread")
        self.assertEqual(evidence["repair_handoff"]["repair_launch"]["arguments"]["target"], {"type": "projectless"})
        self.assertNotIn("threadId", evidence["repair_handoff"]["repair_launch"]["arguments"])
        self.assertIn("Original acceptance contract: The repair check exits successfully.", evidence["repair_handoff"]["repair_prompt"])
        self.assertIn("waiting_for_active_task_release", evidence["repair_handoff"]["repair_prompt"])
        self.assertEqual(evidence["repair_handoff"]["error"]["exit_code"], 7)
        self.assertIn("broken", evidence["repair_handoff"]["error"]["stderr"])

    def test_launch_requires_a_final_passing_published_producer_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "receipt-gate", 20, [{"name": "unit", "command": ["python3", "-c", "print('unit')"]}])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "producer_receipt is required"):
                PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending-evidence", "project-123", None)
            incomplete = final_producer_receipt(root, turn_completed=False)
            with self.assertRaisesRegex(ValueError, "final passing published aggregate result"):
                PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending-evidence", "project-123", incomplete)
            child = final_producer_receipt(root, final_aggregate_receipt=False)
            with self.assertRaisesRegex(ValueError, "final passing published aggregate result"):
                PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending-evidence", "project-123", child)

    def test_launch_spec_requires_one_projectless_thread_for_all_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"], "complexity_score": 20},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"], "complexity_score": 65},
            ])), encoding="utf-8")
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")
            detached_resolution_exists = (root.resolve() / "plan.json").is_file()
        self.assertEqual(launch["execution"], "host_persistent_create_thread")
        self.assertEqual(launch["required_launch_count"], 1)
        self.assertEqual({item["tool"] for item in launch["launch_requests"]}, {"codex_app__create_thread"})
        self.assertEqual(launch["project_binding"]["project_root"], str(root.resolve()))
        self.assertEqual(launch["thread_placement_policy"], {"scope": "global", "target": {"type": "projectless"}, "expected_project_id": None, "creation_tool": "codex_app__create_thread", "readback_tool": "codex_app__list_threads"})
        self.assertEqual(launch["origin_session"]["thread_id"], "source-session-001")
        self.assertTrue(all(item["arguments"]["target"] == {"type": "projectless"} for item in launch["launch_requests"]))
        self.assertTrue(all("projectId" not in item["arguments"] and "project_id" not in item["arguments"] and "environment" not in item["arguments"] for item in launch["launch_requests"]))
        self.assertTrue(all(item["arguments"]["prompt"].startswith("ENDING_TASK_WORKER\n") for item in launch["launch_requests"]))
        self.assertTrue(all("Saved plan: plan.json" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertEqual(launch["launch_requests"][0]["check_id"], "task-ending")
        self.assertEqual(launch["launch_requests"][0]["title"], "End Task-routing")
        self.assertEqual(launch["launch_requests"][0]["thread_target"], {"type": "projectless"})
        self.assertEqual(launch["launch_requests"][0]["thread_placement"]["scope"], "global")
        self.assertIsNone(launch["launch_requests"][0]["thread_placement"]["expected_project_id"])
        self.assertNotIn("project_id", launch["launch_requests"][0])
        self.assertEqual(launch["launch_requests"][0]["terminal_thread_policy"], {"pass": "keep_visible", "fail": "keep_visible", "blocked": "keep_visible"})
        self.assertEqual(launch["launch_requests"][0]["check_ids"], ["unit", "integration"])
        self.assertEqual(set(launch["launch_requests"][0]["evidence_outputs"]), {"unit", "integration"})
        prompt = launch["launch_requests"][0]["arguments"]["prompt"]
        self.assertIn("evidence directory: Cache/remote-test/ending-evidence", prompt)
        self.assertIn(f"Origin project root (absolute): {root.resolve()}.", prompt)
        self.assertIn("projectless cwd is unrelated", prompt)
        self.assertEqual(prompt.count(str(root.resolve())), 1)
        self.assertTrue(detached_resolution_exists)
        self.assertTrue(all("print('unit')" not in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all(len(item["arguments"]["prompt"]) < 2300 for item in launch["launch_requests"]))
        self.assertTrue(all("Never call set_thread_archived" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("structured model_assessment" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("final aggregate result is released" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("compact continuation" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertTrue(all("create the saved independent projectless repair task" in item["arguments"]["prompt"] for item in launch["launch_requests"]))
        self.assertEqual(
            [f"{item['arguments']['model']}|{item['arguments']['thinking']}" for item in launch["launch_requests"]],
            [item["selected_pair"] for item in launch["launch_requests"]],
        )
        request = launch["launch_requests"][0]
        self.assertEqual(request["launch_candidates"][0]["pair"], "gpt-5.3-codex-spark|xhigh")
        self.assertEqual(request["launch_candidates"][1]["pair"], "gpt-5.6-luna|low")
        self.assertGreater(len(request["launch_candidates"]), 2)
        self.assertIn("scheduler_unavailable", request["availability_fallback_reasons"])
        self.assertIn("required_modality_unavailable", request["availability_fallback_reasons"])
        self.assertIn("Correctness, quality, protocol, timeout, or command failure never changes the Ending pair.", request["arguments"]["prompt"])

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
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            not_launched = PLAN.audit_launches(launch_path, state_path)
            PLAN.acknowledge_launch(launch_path, "task-ending", "thread-ending", "host-ending", "project-123", state_path, "global", None, "codex_app__list_threads")
            passed = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(not_launched["status"], "blocked")
        self.assertEqual(not_launched["end_task_trigger_rate"], "0%")
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(passed["end_task_trigger_rate"], "100%")
        self.assertEqual(passed["launched_count"], 1)
        self.assertIsNone(passed["threads"][0]["thread_project_id"])
        self.assertNotIn("project_id", passed["threads"][0])

    def test_launch_ack_rejects_project_current_or_unreadback_placement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [{"name": "unit", "command": ["python3", "-c", "print('unit')"]}])), encoding="utf-8")
            launch_path.write_text(json.dumps(build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "global projectless"):
                PLAN.acknowledge_launch(launch_path, "task-ending", "project-thread", "host", "project-123", state_path, "project", "project-123", "codex_app__list_threads")
            with self.assertRaisesRegex(ValueError, "thread_project_id must be null"):
                PLAN.acknowledge_launch(launch_path, "task-ending", "project-thread", "host", "project-123", state_path, "global", "project-123", "codex_app__list_threads")
            with self.assertRaisesRegex(ValueError, "codex_app__list_threads"):
                PLAN.acknowledge_launch(launch_path, "task-ending", "unreadback-thread", "host", "project-123", state_path, "global", None, "codex_app__read_thread")

    def test_launch_audit_counts_a_project_attached_thread_as_zero(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [{"name": "unit", "command": ["python3", "-c", "print('unit')"]}])), encoding="utf-8")
            launch_path.write_text(json.dumps(build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")), encoding="utf-8")
            PLAN.acknowledge_launch(launch_path, "task-ending", "thread-ending", "host-ending", "project-123", state_path, "global", None, "codex_app__list_threads")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["launches"][0]["thread_project_id"] = "project-123"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            audit = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(audit["status"], "blocked")
        self.assertEqual(audit["end_task_trigger_rate"], "0%")
        self.assertEqual(audit["launched_count"], 0)
        self.assertTrue(any("projectId=null" in failure for failure in audit["failures"]))

    def test_launch_ack_rejects_tampered_project_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [{"name": "unit", "command": ["python3", "-c", "print('unit')"]}])), encoding="utf-8")
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")
            launch["launch_requests"][0]["arguments"]["target"] = {"type": "project", "projectId": "project-123", "environment": {"type": "local"}}
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "target must be exactly"):
                PLAN.acknowledge_launch(launch_path, "task-ending", "project-thread", "host", "project-123", state_path, "global", None, "codex_app__list_threads")

    def test_cooling_controller_acknowledges_the_planned_escalation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            launch_path = root / "launch.json"
            state_path = root / "launch-state.json"
            restriction_store = root / "controller-restrictions.json"
            PLAN.record_controller_restriction("gpt-5.3-codex-spark|xhigh", "five_hour_limit", restriction_store)
            plan_path.write_text(json.dumps(build_plan(root, "routing", 60, [
                {"name": "unit", "command": ["python3", "-c", "print('unit')"]},
                {"name": "integration", "command": ["python3", "-c", "print('integration')"]},
            ])), encoding="utf-8")
            launch = PLAN.build_launch_spec(plan_path, root / "Cache" / "remote-test" / "ending-evidence", "project-123", final_producer_receipt(root), restriction_store=restriction_store)
            launch_path.write_text(json.dumps(launch), encoding="utf-8")
            selected_pair = launch["launch_requests"][0]["selected_pair"]
            acknowledged = PLAN.acknowledge_launch(
                launch_path,
                "task-ending",
                "fallback-thread",
                "host",
                "project-123",
                state_path,
                "global",
                None,
                "codex_app__list_threads",
                selected_pair,
            )
            passed = PLAN.audit_launches(launch_path, state_path)
        self.assertEqual(acknowledged["selected_pair"], selected_pair)
        self.assertEqual(acknowledged["availability_fallback_reason"], "controller_cooling")
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
        self.assertEqual(evidence["repair_handoff"]["action"], "create_isolated_projectless_repair_then_fresh_ending")
        self.assertIn("omits the approved construction line", evidence["repair_handoff"]["repair_prompt"])

    def test_launch_and_repair_do_not_require_or_resume_the_original_source_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            evidence_path = root / "evidence.json"
            plan_path.write_text(json.dumps(PLAN.build_plan(root, "unbound", 20, [{"name": "unit", "command": ["python3", "-c", "raise SystemExit(7)"]}])), encoding="utf-8")
            launch = build_launch_spec(root, plan_path, root / "Cache" / "remote-test" / "ending-evidence")
            evidence = PLAN.run_check(plan_path, "unit", evidence_path)
        self.assertIsNone(launch["origin_session"])
        self.assertEqual(evidence["repair_handoff"]["repair_launch"]["tool"], "codex_app__create_thread")
        self.assertNotIn("threadId", evidence["repair_handoff"]["repair_launch"]["arguments"])
        self.assertTrue(evidence["repair_handoff"]["session_isolation"]["new_projectless_session"])


if __name__ == "__main__":
    unittest.main()

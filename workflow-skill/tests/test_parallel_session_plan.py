import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "parallel_session_plan.py"
SPEC = importlib.util.spec_from_file_location("parallel_session_plan", SCRIPT_PATH)
PARALLEL_PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARALLEL_PLAN)


def branch(name, workdir, reads, writes, dependencies=None, inputs=None, outputs=None, required=True, cache=None):
    dependency_names = [] if dependencies is None else dependencies
    input_names = [] if inputs is None else inputs
    output_names = [f"{name}-output"] if outputs is None else outputs
    cache_contract = {"class": "none"} if cache is None else cache
    return {"name": name, "relative_workdir": workdir, "read_allowlist": reads, "write_allowlist": writes, "dependencies": dependency_names, "inputs": input_names, "outputs": output_names, "required": required, "cache": cache_contract, "stop_condition": "Bounded output and branch receipt are readable"}


def plan(branches, benefit=None, temporary_root=None, shared=None):
    main = {"completion_policy": "root_only", "ending_policy": "root_only_after_final_aggregate", "child_control_policy": "root_only", "execution_surface": "collaboration_child_sessions", "parallelism_evaluated": True, "parallel_benefit": benefit, "fallback": "existing_single_producer_or_dispatcher", "temporary_root": temporary_root}
    return {"schema_version": 1, "main": main, "branches": branches, "shared_mutable_state": [] if shared is None else shared}


def report(name, status="passed", readback=True, acceptance=True, conflict=False):
    return {"name": name, "status": status, "readback": readback, "acceptance": acceptance, "conflict": conflict}


class ParallelSessionPlanTests(unittest.TestCase):
    def test_single_branch_uses_sequential_fallback(self):
        logical_plan = plan([branch("core", "Modules/Core", ["Modules/Core"], ["Modules/Core/Generated"])])
        summary = PARALLEL_PLAN.validate_plan(logical_plan)
        self.assertEqual(summary["execution_mode"], "sequential_fallback")
        self.assertEqual(summary["completion_owner"], "root")

    def test_safe_disjoint_modules_admit_parallel_sessions(self):
        branches = [branch("core", ".", ["Modules/Core"], ["Modules/Core/Generated"]), branch("interface", ".", ["Modules/Interface"], ["Modules/Interface/Generated"])]
        summary = PARALLEL_PLAN.validate_plan(plan(branches, benefit="Independent modules shorten the critical path"))
        self.assertEqual(summary["execution_mode"], "parallel_sessions")
        self.assertEqual(summary["dependency_waves"], [["core", "interface"]])
        self.assertEqual(summary["execution_surface"], "collaboration_child_sessions")

    def test_dependency_ready_write_overlap_is_rejected(self):
        branches = [branch("first", "Modules/First", ["Inputs/First"], ["Shared/Generated"]), branch("second", "Modules/Second", ["Inputs/Second"], ["Shared"])]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "overlapping mutable surfaces"):
            PARALLEL_PLAN.validate_plan(plan(branches, benefit="Independent work should be faster"))

    def test_platform_builds_use_isolated_temporary_copies(self):
        task_root = "Cache/tmp-platform-build"
        platforms = ["windows", "macos", "linux"]
        branches = [branch(name, f"{task_root}/{name}", [f"BuildInputs/{name}"], [f"{task_root}/{name}"], cache={"class": "temporary", "root": f"{task_root}/{name}"}) for name in platforms]
        summary = PARALLEL_PLAN.validate_plan(plan(branches, benefit="Independent platform copies reduce package time", temporary_root=task_root))
        self.assertEqual(summary["execution_mode"], "parallel_sessions")
        self.assertEqual(summary["branch_count"], 3)

    def test_shared_mutable_state_requires_dependencies_and_declaration(self):
        unordered = [branch("producer", "Modules/Producer", ["Inputs/Producer"], ["Shared/manifest.json"]), branch("consumer", "Modules/Consumer", ["Shared/manifest.json"], ["Modules/Consumer/Generated"])]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "overlapping mutable surfaces"):
            PARALLEL_PLAN.validate_plan(plan(unordered, benefit="Independent work should be faster"))
        ordered = [unordered[0], branch("consumer", "Modules/Consumer", ["Shared/manifest.json"], ["Modules/Consumer/Generated"], dependencies=["producer"])]
        shared = [{"path": "Shared/manifest.json", "branches": ["producer", "consumer"]}]
        summary = PARALLEL_PLAN.validate_plan(plan(ordered, benefit="Downstream work remains explicitly ordered", shared=shared))
        self.assertEqual(summary["execution_mode"], "sequential_fallback")

    def test_root_only_aggregate_rejects_active_or_failed_children(self):
        branches = [branch("core", "Modules/Core", ["Modules/Core"], ["Modules/Core/Generated"]), branch("interface", "Modules/Interface", ["Modules/Interface"], ["Modules/Interface/Generated"])]
        logical_plan = plan(branches, benefit="Independent modules shorten the critical path")
        active_status = {"schema_version": 1, "main_review_passed": True, "branches": [report("core"), report("interface", status="working", readback=False, acceptance=False)]}
        active_summary = PARALLEL_PLAN.aggregate_plan(logical_plan, active_status)
        self.assertFalse(active_summary["main_complete"])
        self.assertFalse(active_summary["ending_start_ready"])
        for child_status in ("cancelled", "blocked", "failed"):
            failed_status = copy.deepcopy(active_status)
            failed_status["branches"][1]["status"] = child_status
            self.assertFalse(PARALLEL_PLAN.aggregate_plan(logical_plan, failed_status)["main_complete"])
        passed_status = {"schema_version": 1, "main_review_passed": True, "branches": [report("core"), report("interface")]}
        passed_summary = PARALLEL_PLAN.aggregate_plan(logical_plan, passed_status)
        self.assertTrue(passed_summary["main_complete"])
        self.assertEqual(passed_summary["completion_owner"], "root")
        self.assertEqual(passed_summary["ending_start_owner"], "root")
        non_root_plan = copy.deepcopy(logical_plan)
        non_root_plan["main"]["completion_policy"] = "child_allowed"
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "root-only"):
            PARALLEL_PLAN.validate_plan(non_root_plan)

    def test_aggregate_requires_passed_dependency_status(self):
        branches = [branch("optional-source", "Modules/Source", ["Inputs"], ["Modules/Source/Generated"], required=False, outputs=["source-artifact"]), branch("consumer", "Modules/Consumer", ["Inputs/Consumer"], ["Modules/Consumer/Generated"], dependencies=["optional-source"], inputs=["source-artifact"])]
        logical_plan = plan(branches, benefit="Parallel sibling work reduces waiting")
        status = {"schema_version": 1, "main_review_passed": True, "branches": [report("optional-source", status="skipped", readback=False, acceptance=False), report("consumer")]}
        summary = PARALLEL_PLAN.aggregate_plan(logical_plan, status)
        self.assertFalse(summary["main_complete"])
        self.assertIn("consumer:dependency_optional-source_not_passed", summary["blocking_reasons"])

    def test_logical_artifact_requires_declared_dependency(self):
        branches = [branch("producer", "Modules/Producer", ["Inputs"], ["Modules/Producer/Generated"], outputs=["shared-artifact"]), branch("consumer", "Modules/Consumer", ["Inputs"], ["Modules/Consumer/Generated"], inputs=["shared-artifact"])]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "explicit dependency"):
            PARALLEL_PLAN.validate_plan(plan(branches, benefit="Independent preparation reduces waiting"))
        branches[1]["dependencies"] = ["producer"]
        summary = PARALLEL_PLAN.validate_plan(plan(branches, benefit="Independent preparation reduces waiting"))
        self.assertEqual(summary["dependency_waves"], [["producer"], ["consumer"]])

    def test_placeholder_benefit_branch_cap_and_surface_are_rejected(self):
        branches = [branch("one", "Modules/One", ["Inputs"], ["Modules/One/Generated"]), branch("two", "Modules/Two", ["Inputs"], ["Modules/Two/Generated"])]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "concrete bounded"):
            PARALLEL_PLAN.validate_plan(plan(branches, benefit="none"))
        too_many = [branch(f"branch-{index}", f"Modules/{index}", [f"Inputs/{index}"], [f"Modules/{index}/Generated"]) for index in range(9)]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "at most 8"):
            PARALLEL_PLAN.validate_plan(plan(too_many, benefit="Bounded branches reduce the critical path"))
        wrong_surface = plan(branches, benefit="Independent modules reduce the critical path")
        wrong_surface["main"]["execution_surface"] = "dispatcher"
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "whole graph"):
            PARALLEL_PLAN.validate_plan(wrong_surface)

    def test_missing_dependencies_cycles_and_invalid_remote_cache_are_rejected(self):
        missing = plan([branch("consumer", "Modules/Consumer", ["Inputs"], ["Modules/Consumer/Generated"], dependencies=["producer"])])
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "missing dependencies"):
            PARALLEL_PLAN.validate_plan(missing)
        cycle_branches = [branch("first", "Modules/First", ["Inputs/First"], ["Modules/First/Generated"], dependencies=["second"]), branch("second", "Modules/Second", ["Inputs/Second"], ["Modules/Second/Generated"], dependencies=["first"])]
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "cycle"):
            PARALLEL_PLAN.validate_plan(plan(cycle_branches))
        remote_branch = branch("remote", "Cache/remote-build/remote", ["Inputs/Remote"], ["Cache/remote-build/remote"], cache={"class": "remote", "root": "Cache/remote-build/remote", "retention_reason": "Reusable remote fixture", "review_point": "Next release"})
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "missing required fields"):
            PARALLEL_PLAN.validate_plan(plan([remote_branch]))

    def test_raw_control_ids_emails_and_absolute_paths_are_rejected(self):
        logical_plan = plan([branch("core", "Modules/Core", ["Modules/Core"], ["Modules/Core/Generated"])])
        with_identifier = copy.deepcopy(logical_plan)
        with_identifier["session_id"] = "session-12345678"
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "must not store"):
            PARALLEL_PLAN.validate_plan(with_identifier)
        with_email = copy.deepcopy(logical_plan)
        with_email["main"]["parallel_benefit"] = "Notify owner@example.com when ready"
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "identifiers"):
            PARALLEL_PLAN.validate_plan(with_email)
        with_absolute_path = copy.deepcopy(logical_plan)
        with_absolute_path["branches"][0]["relative_workdir"] = "C:\\Temp\\example-project"
        with self.assertRaisesRegex(PARALLEL_PLAN.PlanValidationError, "absolute path|project-relative"):
            PARALLEL_PLAN.validate_plan(with_absolute_path)


if __name__ == "__main__":
    unittest.main()

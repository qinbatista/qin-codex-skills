import copy
import importlib.util
import io
import json
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/task_route_dispatcher.py"
SPEC = importlib.util.spec_from_file_location("selected_dispatcher_tests", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SKILLS_ROOT = SCRIPT.parents[2]


def node(name, dependencies=None, **kwargs):
    return {"id": name, "phase": "result", "skill": "code-skill", "model": "gpt-5.3-codex-spark", "effort": "low", "prompt": "Update the scoped source and verify the changed behavior.", "dependencies": dependencies or [], "sandbox": "read-only", "complexity_score": 20, **kwargs}


def plan(root, nodes=None):
    nodes = nodes or [node("result")]
    return {"schema_version": 2, "entry": {"model": "gpt-6-astra", "effort": "ultra"}, "complexity": "complex", "topology": "parallel", "cache_dir": str(root / "Cache/tmp-route"), "nodes": nodes, "main_result_node": nodes[-1]["id"]}


def fake_record(item, cache, text="Result ready"):
    result = cache / (item["id"] + ".md")
    receipt = cache / (item["id"] + ".json")
    result.write_text(text)
    receipt.write_text(json.dumps({"status": "pass"}))
    return {"id": item["id"], "phase": item["phase"], "model": item["model"], "effort": item["effort"], "status": "pass", "receipt_path": str(receipt), "result_path": str(result), "tokens": {}, "process_elapsed_ms": 1}


class TaskRouteDispatcherTests(unittest.TestCase):
    def test_validation_keeps_user_pair_for_code_even_when_caller_requests_spark(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root)
            self.assertEqual(module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT), [])
            self.assertEqual((value["nodes"][0]["model"], value["nodes"][0]["effort"]), ("gpt-6-astra", "ultra"))

    def test_independent_node_can_choose_cheaper_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root, [node("collect", skill=None, model="gpt-5.6-luna", effort="low")])
            self.assertEqual(module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT), [])
            self.assertEqual(value["nodes"][0]["model"], "gpt-5.6-luna")

    def test_missing_selected_model_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root)
            value["entry"] = {"model": "unknown", "effort": "unknown"}
            self.assertTrue(module.validate_plan(value, "unknown", "unknown", root, SKILLS_ROOT))

    def test_parallel_write_overlap_requires_ordering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = node("branch-a", sandbox="workspace-write", write_allowlist=["src"])
            b = node("branch-b", sandbox="workspace-write", write_allowlist=["src/shared.py"])
            value = plan(root, [a, b, node("merge", ["branch-a", "branch-b"])])
            self.assertTrue(any("unordered write" in error for error in module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT)))
            b["dependencies"] = ["branch-a"]
            self.assertEqual(module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT), [])

    def test_parallel_writer_requires_explicit_write_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root, [node("a", sandbox="workspace-write"), node("b"), node("merge", ["a", "b"])])
            self.assertTrue(any("explicit write_allowlist" in error for error in module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT)))

    def test_cycle_and_missing_dependency_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for nodes in ([node("a", ["b"]), node("b", ["a"])], [node("a", ["missing"])]):
                value = plan(root, nodes)
                self.assertTrue(module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT))

    def test_final_aggregate_must_cover_every_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root, [node("a"), node("b")])
            self.assertTrue(any("every result" in error for error in module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT)))

    def test_memory_ending_optional_selected_and_cannot_verify(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ending = node("memory", ["result"], phase="ending", skill="project-memory-skill", prompt="Summarize scoped memory.")
            value = plan(root, [node("result"), ending])
            value["main_result_node"] = "result"
            self.assertEqual(module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT), [])
            self.assertEqual((ending["model"], ending["effort"]), ("gpt-6-astra", "ultra"))
            ending["acceptance_checks"] = [{"command": ["build"]}]
            self.assertTrue(any("memory-only" in error for error in module.validate_plan(value, "gpt-6-astra", "ultra", root, SKILLS_ROOT)))

    def test_run_plan_launches_ready_branches_in_parallel_before_merge(self):
        # Retains the user's existing regression for launching a whole ready wave.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root, [node("branch-a"), node("branch-b"), node("merge", ["branch-a", "branch-b"])])
            gate = threading.Barrier(2)
            calls = []
            def run(item, cache, completed, *args):
                calls.append(item["id"])
                if item["id"] != "merge":
                    gate.wait(timeout=3)
                else:
                    self.assertEqual(set(completed), {"branch-a", "branch-b"})
                return fake_record(item, cache)
            with patch.object(module, "run_node", side_effect=run), redirect_stdout(io.StringIO()):
                result = module.run_plan(value, "gpt-6-astra", "ultra", root, skills_root=SKILLS_ROOT)
            self.assertEqual(result["status"], "pass", result["failures"])
            self.assertEqual(set(calls[:2]), {"branch-a", "branch-b"})
            self.assertEqual(calls[2:], ["merge"])
            self.assertTrue(all(item["model"] == "gpt-6-astra" for item in result["nodes"]))

    def test_run_plan_rejects_semantic_final_aggregate_failure_without_ending_handoff(self):
        # Retains the user's existing Aggregate: FAIL acceptance regression.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root)
            with patch.object(module, "run_node", side_effect=lambda item, cache, *args: fake_record(item, cache, "Aggregate: FAIL\n")), redirect_stdout(io.StringIO()):
                result = module.run_plan(value, "gpt-6-astra", "ultra", root, skills_root=SKILLS_ROOT)
            self.assertEqual(result["status"], "fail")
            self.assertIn("final aggregate reported Aggregate: FAIL", result["failures"])
            self.assertIsNone(result["ending_handoff_path"])
            self.assertFalse((Path(value["cache_dir"]) / "ending-handoff.json").exists())

    def test_run_node_rebinds_pair_even_without_plan_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = node("result", _entry_model="gpt-5.6-luna", _entry_effort="max", allow_fallback=["gpt-5.6-sol|high"])
            calls = []
            def execute(args, prompt):
                calls.append((args.model, args.effort, prompt))
                args.result_output.write_text("done")
                pair = f"{args.model}|{args.effort}"
                return {"status": "pass", "turn_completed": True, "requested_pair": pair, "effective_pair": pair, "resolved_pair": pair, "model_match": True, "effort_match": True, "pair_match": True, "tokens": {}, "process_elapsed_ms": 1}
            with patch.object(module.receipt_module, "run_receipt", side_effect=execute), redirect_stdout(io.StringIO()):
                result = module.run_node(item, root, {}, None, root, skills_root=SKILLS_ROOT)
            self.assertEqual(result["status"], "pass")
            self.assertEqual([(model, effort) for model, effort, _ in calls], [("gpt-5.6-luna", "max")])
            self.assertIn("missing memory is optional", calls[0][2])

    def test_failed_memory_does_not_grade_or_repair_producer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            value = plan(root)
            ending = node("memory", ["result"], phase="ending", skill="project-memory-skill", prompt="Summarize existing memory.")
            value["nodes"].append(ending)
            with patch.object(module, "run_node", side_effect=lambda item, cache, *args: fake_record(item, cache)), redirect_stdout(io.StringIO()):
                result = module.run_plan(value, "gpt-6-astra", "ultra", root, skills_root=SKILLS_ROOT)
            handoff = Path(result["ending_handoff_path"])
            module._release_main_result(json.loads(handoff.read_text()))
            with patch.object(module, "_run_record", side_effect=AssertionError("memory must not grade")), patch.object(module, "run_node", side_effect=lambda item, cache, *args: fake_record(item, cache, "ENDING_TASK=FAIL\n")):
                ending_result = module.run_ending_handoff(handoff, skills_root=SKILLS_ROOT)
            self.assertEqual(ending_result["status"], "fail")
            self.assertIsNone(ending_result["routing_learning"])
            self.assertNotIn("repair_launch", ending_result)


if __name__ == "__main__":
    unittest.main()

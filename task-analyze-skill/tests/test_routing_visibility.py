"""Offline visibility and aggregate handoff regressions; no live model/task claims."""
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/task_route_dispatcher.py"
SPEC = importlib.util.spec_from_file_location("routing_visibility", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
ROOT = SCRIPT.parents[2]


class RoutingVisibilityTests(unittest.TestCase):
    def make_plan(self, root):
        return {"schema_version": 2, "entry": {"model": "gpt-6-astra", "effort": "ultra"},
                "complexity": "complex", "complexity_score": 59, "topology": "sequential",
                "cache_dir": str(root / "Cache/tmp-visible-route"), "main_result_node": "result", "ending_required": True,
                "nodes": [{"id": "collect", "phase": "result", "model": "gpt-5.6-luna", "effort": "low",
                           "skill_independent": True, "purpose": "Collect a bounded count", "complexity_score": 5,
                           "prompt": "Count the listed items.", "dependencies": []},
                          {"id": "result", "phase": "result", "skill": "code-skill", "purpose": "Apply the code preference",
                           "model": "gpt-5.6-luna", "effort": "low", "prompt": "Update the scoped function.", "dependencies": ["collect"]}]}

    def test_disclosure_and_projectless_memory_launch_wait_for_aggregate_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.make_plan(root)
            def fake_run(node, cache, *args):
                result = cache / (node["id"] + ".md")
                result.write_text("Aggregate: PASS")
                pair = f"{node['model']}|{node['effort']}"
                return {"id": node["id"], "status": "pass", "result_path": str(result),
                        "requested_pair": pair, "resolved_pair": pair, "effective_pair": pair,
                        "evidence_level": "runtime_receipt", "model_evidence_source": "runtime_receipt"}
            output = io.StringIO()
            with patch.object(module, "run_node", side_effect=fake_run), redirect_stdout(output):
                manifest = module.run_plan(plan, "gpt-6-astra", "ultra", root, skills_root=ROOT)
            self.assertEqual(manifest["status"], "pass", manifest.get("failures"))
            notices = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual([event["timing"] for event in notices], ["assignment", "result"])
            assigned = notices[0]["model_stages"]
            actual = notices[1]["model_stages"]
            self.assertIsNone(assigned[0]["actual_pair"])
            self.assertEqual(actual[0]["actual_pair"], "gpt-5.6-luna|low")
            self.assertEqual(actual[1]["actual_pair"], "gpt-6-astra|ultra")
            self.assertEqual(actual[1]["relations"]["dependencies"], ["collect"])
            self.assertEqual(actual[1]["goal"], "Apply the code preference")
            self.assertIsInstance(actual[1]["score"], int)
            compact = module.compact_run_plan_manifest(manifest)
            self.assertEqual(compact["complexity_score"], 59)
            self.assertIn("Assignment: gpt-6-astra|ultra -> gpt-5.6-luna|low", compact["model_disclosure"]["message"])
            self.assertEqual(manifest["memory_closeout"]["status"], "waiting-for-aggregate-release")
            self.assertFalse(manifest["ending_launch_ready"])
            handoff = json.loads(Path(manifest["ending_handoff_path"]).read_text())
            incomplete = copy.deepcopy(handoff)
            incomplete["completed"] = incomplete["completed"][-1:]
            self.assertEqual(module._release_main_result(incomplete)["status"], "fail")
            released = module._release_main_result(handoff)
            packet = released["memory_closeout"]
            self.assertEqual(packet["status"], "launch-required")
            self.assertEqual(packet["target"], {"type": "projectless"})
            self.assertEqual(packet["selected_pair"], "gpt-6-astra|ultra")
            self.assertEqual(packet["task_count"], 1)
            self.assertFalse(packet["task_created"])
            self.assertEqual(packet["ending_purpose"], "memory_only")
            self.assertEqual(packet["verification_owner"], "active_task")
            self.assertFalse(packet["repair_chain_allowed"])
            self.assertIn("ordinary unpinned task", packet["message"])
            self.assertIn("even if absent from recent tasks", packet["message"])
            self.assertIn("Do not pin, move, reorder, or open it automatically", packet["message"])


if __name__ == "__main__":
    unittest.main()

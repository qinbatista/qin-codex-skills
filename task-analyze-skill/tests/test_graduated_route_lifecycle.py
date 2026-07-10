#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURE = Path(__file__).resolve().parents[1] / "assets" / "graduated-route-fixtures.json"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_graduated_routes")
dispatcher = load_module("task_route_dispatcher")


class GraduatedRouteLifecycleTests(unittest.TestCase):
    def test_run_plan_release_then_ending_dispatches_the_producer_verifier(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        template = next(scenario["dispatcher_plan"] for scenario in fixture["scenarios"] if scenario.get("complexity") == "complex")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache_dir = root / "work" / "cache" / "route"
            plan = validator.materialize_dispatcher_plan(template, cache_dir, "gpt-5.6-luna", "low")
            calls = []

            def fake_run_node(node, node_cache_dir, completed, state_db, workdir, codex_bin="codex", skills_root=None):
                calls.append(node["id"])
                result_path = node_cache_dir / f"{node['id']}-result.md"
                receipt_path = node_cache_dir / f"{node['id']}-receipt.json"
                marker = "MINI_VERIFY=PASS\n" if node["phase"] == "mini" else "ENDING_TASK=PASS\n" if node["phase"] == "ending" else "RESULT=approved\n"
                result_path.write_text(marker, encoding="utf-8")
                receipt_path.write_text(json.dumps({"status": "pass", "thread_id": node["id"]}), encoding="utf-8")
                return {"id": node["id"], "phase": node["phase"], "skill": node["skill"], "model": node["model"], "effort": node["effort"], "status": "pass", "receipt_path": str(receipt_path), "result_path": str(result_path), "worker_identity": node["id"]}

            with patch.object(dispatcher, "run_node", side_effect=fake_run_node), patch.object(dispatcher, "_run_record", return_value={"status": "recorded"}):
                manifest = dispatcher.run_plan(plan, "gpt-5.6-luna", "low", root)
            self.assertEqual(calls, ["design", "implementation", "mini"])
            self.assertEqual(manifest["ending_nodes_pending"], ["ending-real"])
            handoff_path = Path(manifest["ending_handoff_path"])
            with patch.object(dispatcher, "run_node", side_effect=AssertionError("Ending ran before release")):
                unreleased = dispatcher.run_ending_handoff(handoff_path)
            self.assertEqual(unreleased["status"], "fail")
            self.assertTrue(any("not released" in failure for failure in unreleased["failures"]))

            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            release = dispatcher._release_main_result(handoff)
            self.assertEqual(release["status"], "pass")
            with patch.object(dispatcher, "run_node", side_effect=fake_run_node), patch.object(dispatcher, "_run_record", return_value={"status": "recorded"}):
                ending = dispatcher.run_ending_handoff(handoff_path)
            self.assertEqual(ending["status"], "pass")
            self.assertEqual(ending["routing_learning"], {"status": "recorded"})
            self.assertEqual(calls[:3], ["design", "implementation", "mini"])
            self.assertEqual(calls[3:], ["ending-real"])


if __name__ == "__main__":
    unittest.main()

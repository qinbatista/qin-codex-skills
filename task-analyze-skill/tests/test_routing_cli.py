"""Offline CLI integration: fake Codex receipts, never live model/app task proof."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "task-analyze-skill/scripts"
FAKE = Path(__file__).resolve().parent / "fixtures/fake_codex.py"


def environment(root):
    values = {key: value for key, value in os.environ.items() if not key.startswith("CODEX_")}
    values["CODEX_HOME"] = str(root / "codex-home")
    return values


class RoutingCLITests(unittest.TestCase):
    def test_runner_preserves_each_selected_pair_through_offline_subprocess(self):
        for model, effort in [("gpt-5.6-luna", "max"), ("gpt-6-astra", "ultra")]:
            with self.subTest(model=model), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                command = [sys.executable, str(SCRIPTS / "obsidian_adaptive_model_runner.py"), "--workdir", str(root), "--task-type", "question", "--governing-skill", "code-skill", "--entry-model", model, "--entry-effort", effort, "--codex-bin", str(FAKE), "--state-db", str(root / "fixture-state.sqlite"), "--timeout", "15"]
                completed = subprocess.run(command, input="Apply the governing structure preference to this bounded result.", text=True, capture_output=True, cwd=root, env=environment(root), timeout=25, **hidden_process_options())
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                events = [json.loads(line) for line in completed.stdout.splitlines()]
                summary = events[-1]
                notices = [event for event in events if event.get("stage") == "model-disclosure"]
                self.assertEqual([event["timing"] for event in notices], ["assignment", "result"])
                self.assertIn("Evidence: task assignment (no runtime receipt)", notices[0]["message"])
                self.assertIn("Evidence: runtime receipt", notices[1]["message"])
                self.assertIn("Complexity:", summary["model_disclosure"]["message"])
                self.assertEqual(notices[1]["parent_action"], "surface_disclosure_in_conversation")
                self.assertEqual(summary["executed_pair"], f"{model}|{effort}")
                self.assertEqual(summary["verification_owner"], "active_task")
                captured = json.loads((root / "fixture-call.json").read_text())
                self.assertEqual((captured["model"], captured["effort"]), (model, effort))
                self.assertIn("inside this active task", captured["prompt"])
                self.assertIn("workflow-skill/references/readable-ui.md", captured["prompt"])
                self.assertFalse(any(event.get("stage") == "ending-required" for event in events))
                receipt = json.loads(Path(summary["receipt_path"]).read_text())
                self.assertTrue(receipt["pair_match"])
                self.assertEqual(receipt["allowed_fallback_pairs"], [])

    def test_dispatcher_preserves_selected_pair_through_offline_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = {"schema_version": 2, "entry": {"model": "gpt-6-astra", "effort": "ultra"}, "complexity": "easy", "topology": "sequential", "cache_dir": str(root / "Cache/tmp-route"), "main_result_node": "result", "nodes": [{"id": "result", "phase": "result", "skill": "code-skill", "model": "gpt-5.3-codex-spark", "effort": "low", "prompt": "Apply the current code structure preference.", "dependencies": [], "sandbox": "read-only", "complexity_score": 5}]}
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan))
            command = [sys.executable, str(SCRIPTS / "task_route_dispatcher.py"), "run-plan", str(plan_path), "--cwd", str(root), "--codex-bin", str(FAKE), "--skills-root", str(ROOT), "--state-db", str(root / "fixture-state.sqlite")]
            completed = subprocess.run(command, text=True, capture_output=True, cwd=root, env=environment(root), timeout=25, **hidden_process_options())
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            summary = json.loads(completed.stdout.splitlines()[-1])
            manifest = json.loads(Path(summary["manifest_path"]).read_text())
            self.assertEqual(manifest["nodes"][0]["effective_pair"], "gpt-6-astra|ultra")
            captured = json.loads((root / "fixture-call.json").read_text())
            self.assertEqual((captured["model"], captured["effort"]), ("gpt-6-astra", "ultra"))
            self.assertNotIn("ENDING_TASK_WORKER", captured["prompt"])
            self.assertEqual(manifest["ending_nodes_pending"], [])
            self.assertEqual(summary["complexity_score"], 5)
            self.assertIn("Complexity: 5/100 (small)", summary["model_disclosure"]["message"])
            stages = summary["model_switch_summary"]["nodes"]
            self.assertEqual(stages[0]["actual_pair"], "gpt-6-astra|ultra")
            self.assertEqual(stages[0]["relations"]["dependencies"], [])
            self.assertEqual(stages[0]["status"], "pass")
            receipt = json.loads(Path(manifest["nodes"][0]["receipt_path"]).read_text())
            self.assertTrue(receipt["model_locked"])
            self.assertEqual(receipt["selection_provenance"], "user_selected")
            self.assertEqual(receipt["governing_skills"], ["code-skill"])


    def test_memory_only_launch_packet_is_visible_but_not_a_created_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            command = [sys.executable, str(SCRIPTS / "obsidian_adaptive_model_runner.py"), "--workdir", str(root),
                       "--task-type", "question", "--governing-skill", "project-memory-skill", "--memory-update",
                       "--entry-model", "gpt-6-astra", "--entry-effort", "ultra", "--codex-bin", str(FAKE),
                       "--state-db", str(root / "fixture-state.sqlite"), "--timeout", "15"]
            completed = subprocess.run(command, input="Record this durable project preference after verification.", text=True,
                                       capture_output=True, cwd=root, env=environment(root), timeout=25, **hidden_process_options())
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            events = [json.loads(line) for line in completed.stdout.splitlines()]
            packets = [event for event in events if event.get("stage") == "memory-closeout-required"]
            self.assertEqual(len(packets), 1)
            packet = packets[0]
            self.assertEqual(packet["selected_pair"], "gpt-6-astra|ultra")
            self.assertEqual(packet["status"], "launch-required")
            self.assertTrue(packet["ending_launch_ready"])
            self.assertTrue(packet["final_aggregate_receipt"])
            self.assertEqual(packet["target"], {"type": "projectless"})
            self.assertFalse(packet["task_created"])
            self.assertFalse(packet["repair_chain_allowed"])
            self.assertEqual(packet["ending_purpose"], "memory_only")
            self.assertEqual(packet["verification_owner"], "active_task")
            self.assertEqual(events[-1]["memory_closeout"], packet)



if __name__ == "__main__":
    unittest.main()

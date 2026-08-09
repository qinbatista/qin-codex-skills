import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "global_skill_regression_gate.py"
MODULE_SPEC = importlib.util.spec_from_file_location("global_skill_regression_gate", MODULE_PATH)
GATE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(GATE)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GlobalSkillRegressionGateTests(unittest.TestCase):
    def test_catalog_has_stable_unique_retained_capabilities_and_referenced_checks(self):
        catalog = GATE.load_catalog(PROJECT_ROOT)
        capability_ids = [item["id"] for item in catalog["capabilities"]]
        check_ids = {item["id"] for item in catalog["checks"]}
        referenced = {check_id for item in catalog["capabilities"] for check_id in item["checks"]}
        self.assertEqual(len(capability_ids), 25)
        self.assertEqual(len(capability_ids), len(set(capability_ids)))
        self.assertEqual(check_ids, referenced)
        self.assertTrue(catalog["policy"]["local_deployment_requires_pass"])
        self.assertTrue(catalog["policy"]["github_publication_requires_pass"])

    def test_capability_counters_report_runs_and_assertions_separately(self):
        catalog = {
            "capabilities": [
                {"id": "GSR-001", "owner_skill": "test", "name": "one", "function": "one", "checks": ["a", "b"]},
                {"id": "GSR-002", "owner_skill": "test", "name": "two", "function": "two", "checks": ["b"]},
            ]
        }
        results = [
            {"check_id": "a", "status": "pass", "test_count": 3, "passed_count": 3},
            {"check_id": "b", "status": "pass", "test_count": 5, "passed_count": 5},
        ]
        summaries = GATE.capability_results(catalog, results)
        self.assertEqual((summaries[0]["test_runs"], summaries[0]["passed_runs"]), (2, 2))
        self.assertEqual((summaries[0]["test_count"], summaries[0]["passed_count"]), (8, 8))
        self.assertEqual(summaries[0]["status"], "pass")
        self.assertEqual((summaries[1]["test_runs"], summaries[1]["passed_runs"]), (1, 1))

    def test_capability_fails_when_any_mapped_check_fails(self):
        catalog = {"capabilities": [{"id": "GSR-001", "owner_skill": "test", "name": "one", "function": "one", "checks": ["a"]}]}
        summary = GATE.capability_results(catalog, [{"check_id": "a", "status": "fail", "test_count": 4, "passed_count": 3}])[0]
        self.assertEqual(summary["status"], "fail")
        self.assertEqual((summary["test_count"], summary["passed_count"]), (4, 3))

    def test_zero_test_command_is_a_failure_even_with_exit_zero(self):
        completed = subprocess.CompletedProcess(["test"], 0, stdout="Ran 0 tests\nOK\n", stderr="")
        with mock.patch.object(GATE.subprocess, "run", return_value=completed):
            result = GATE.command_result("zero", "source", ["test"], PROJECT_ROOT, 1, {})
        self.assertEqual(result["status"], "fail")
        self.assertEqual((result["test_count"], result["passed_count"]), (0, 0))

    def test_attestation_rejects_a_stale_watched_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watched = root / "code-skill" / "SKILL.md"
            watched.parent.mkdir(parents=True)
            watched.write_text("before", encoding="utf-8")
            attestation = root / "management-skill" / "assets" / "attestation.json"
            attestation.parent.mkdir(parents=True)
            attestation.write_text(json.dumps({
                "schema_version": 1,
                "check_id": "sample",
                "status": "pass",
                "trial_count": 3,
                "passed_trials": 3,
                "watched_files": {"code-skill/SKILL.md": GATE.sha256_file(watched)},
            }), encoding="utf-8")
            check = {"id": "sample", "kind": "attestation", "path": "management-skill/assets/attestation.json", "watched_files": ["code-skill/SKILL.md"]}
            self.assertEqual(GATE.attestation_result(check, root)["status"], "pass")
            watched.write_text("after", encoding="utf-8")
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("stale watched file", result["errors"][0])

    def test_candidate_layout_installs_global_agents_and_excludes_private_local_state(self):
        catalog = GATE.load_catalog(PROJECT_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            deployed = Path(temp_dir) / "deployed"
            deployed.mkdir()
            for skill_name in catalog["managed_skills"]:
                source = PROJECT_ROOT / skill_name
                target = deployed / skill_name
                GATE.shutil.copytree(source, target)
            private = deployed / "task-analyze-skill" / "local" / "events.jsonl"
            private.parent.mkdir(parents=True)
            private.write_text("private", encoding="utf-8")
            with GATE.candidate_layouts(PROJECT_ROOT, deployed, catalog["managed_skills"]) as roots:
                self.assertTrue((roots["source"].parent / "AGENTS.md").is_file())
                self.assertTrue((roots["deployed"].parent / "AGENTS.md").is_file())
                self.assertFalse((roots["deployed"] / "task-analyze-skill" / "local").exists())

    def test_runner_uses_argument_arrays_without_shell_execution(self):
        text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("shell=True", text)
        self.assertIn("sys.executable", text)
        self.assertIn("subprocess.run(command", text)


if __name__ == "__main__":
    unittest.main()

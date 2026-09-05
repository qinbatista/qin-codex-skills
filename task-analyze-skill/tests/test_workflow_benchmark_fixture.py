"""Check that the frozen benchmark oracle rejects defects and accepts real behavior."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "workflow_benchmark"
SPEC = importlib.util.spec_from_file_location("workflow_benchmark_check", FIXTURE / "check_behavior.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


VALID_RUNNER = '''import subprocess
import sys

def run_job(args, *, cwd=None, env=None, timeout=10, input_text=None):
    options = {"start_new_session": True}
    if sys.platform == "win32":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        options = {"creationflags": subprocess.CREATE_NO_WINDOW, "startupinfo": startup}
    return subprocess.run(args, shell=False, cwd=cwd, env=env, timeout=timeout,
                          input=input_text, capture_output=True, text=True,
                          check=False, **options)
'''


class WorkflowBenchmarkFixtureTests(unittest.TestCase):
    def setUp(self):
        cache = Path(__file__).resolve().parents[2] / "Cache"
        cache.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="tmp-workflow-benchmark-oracle-", dir=str(cache))
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)
        shutil.copytree(FIXTURE / "input", self.workspace, dirs_exist_ok=True)
        (self.workspace / "process_runner.py.in").rename(self.workspace / "process_runner.py")

    def write_valid_output(self):
        (self.workspace / "process_runner.py").write_text(VALID_RUNNER, encoding="utf-8")
        (self.workspace / "totals.json").write_text(json.dumps(CHECKER.EXPECTED_TOTALS), encoding="utf-8")

    def test_broken_input_fails_without_launching_unsafe_process(self):
        with mock.patch.object(CHECKER, "real_execution_check", side_effect=AssertionError("Unsafe input must never execute")) as execute:
            result = CHECKER.check(self.workspace)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(execute.call_count, 0)
        self.assertTrue(all(not check["pass"] for check in result["checks"]))

    def test_correct_candidate_passes_real_subprocess_and_three_platform_contracts(self):
        self.write_valid_output()
        result = CHECKER.check(self.workspace)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(len(result["checks"]), 5)
        self.assertEqual(result["checks"][-1]["detail"]["exit_code"], 7)

    def test_plausible_but_duplicate_counting_totals_fail(self):
        self.write_valid_output()
        incorrect = dict(CHECKER.EXPECTED_TOTALS, Birch="900.00")
        (self.workspace / "totals.json").write_text(json.dumps(incorrect), encoding="utf-8")
        result = CHECKER.check(self.workspace)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["checks"][0]["pass"])
        self.assertTrue(all(check["pass"] for check in result["checks"][1:]))

    def test_missing_hidden_startup_contract_blocks_real_execution(self):
        self.write_valid_output()
        unsafe = VALID_RUNNER.replace(', "startupinfo": startup', '')
        (self.workspace / "process_runner.py").write_text(unsafe, encoding="utf-8")
        with mock.patch.object(CHECKER, "real_execution_check") as execute:
            result = CHECKER.check(self.workspace)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(execute.call_count, 0)
        windows = next(check for check in result["checks"] if check["name"] == "launch_contract_win32")
        self.assertIn("STARTUPINFO", windows["error"])

    def test_os_name_platform_system_and_import_aliases_are_supported(self):
        for detector_import, detector in (
            ("import os", "os.name == 'nt'"),
            ("import os as operating_system", "operating_system.name == 'nt'"),
            ("import platform", "platform.system() == 'Windows'"),
            ("from platform import system as host_system", "host_system() == 'Windows'"),
            ("from os import name as host_name", "host_name == 'nt'"),
            ("from sys import platform as host_platform", "host_platform == 'win32'"),
        ):
            with self.subTest(detector=detector):
                self.write_valid_output()
                candidate = VALID_RUNNER.replace("import sys", detector_import).replace('sys.platform == "win32"', detector)
                (self.workspace / "process_runner.py").write_text(candidate, encoding="utf-8")
                result = CHECKER.check(self.workspace)
                self.assertEqual(result["status"], "passed", result)

    def test_checker_api_reports_nondictionary_totals_as_failure(self):
        self.write_valid_output()
        (self.workspace / "totals.json").write_text("[]", encoding="utf-8")
        result = CHECKER.check(self.workspace)
        self.assertEqual(result["status"], "failed")

    def test_ui_oracle_rejects_incomplete_exports_and_closed_popups(self):
        node = os.environ.get("BENCHMARK_NODE") or shutil.which("node")
        if not node:
            self.skipTest("Node runtime unavailable; run test_ui_oracle.cjs with the declared benchmark Node")
        result = subprocess.run(
            [node, str(FIXTURE / "test_ui_oracle.cjs")], capture_output=True,
            text=True, encoding="utf-8", timeout=10, check=False, **hidden_process_options(),
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")


if __name__ == "__main__":
    unittest.main()

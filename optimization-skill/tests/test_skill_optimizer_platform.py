import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_optimizer.py"
SPECIFICATION = importlib.util.spec_from_file_location("skill_optimizer_platform_test", SCRIPT_PATH)
OPTIMIZER = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[SPECIFICATION.name] = OPTIMIZER
SPECIFICATION.loader.exec_module(OPTIMIZER)


class SkillOptimizerPlatformTests(unittest.TestCase):
    def test_applescript_returns_clear_unsupported_error_off_macos(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            script_path = Path(temporary_directory) / "sample.applescript"
            script_path.write_text("return 1\n", encoding="utf-8")
            with mock.patch.object(OPTIMIZER.sys, "platform", "win32"), mock.patch.object(OPTIMIZER.subprocess, "run") as run:
                errors = OPTIMIZER.validate_script(script_path)
        self.assertEqual(["AppleScript syntax check is unsupported on win32; run it on macOS."], errors)
        run.assert_not_called()

    def test_shell_validation_resolves_bash_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            script_path = Path(temporary_directory) / "sample.sh"
            script_path.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.object(OPTIMIZER.shutil, "which", return_value="/portable/bash"), mock.patch.object(OPTIMIZER.subprocess, "run", return_value=completed) as run:
                self.assertEqual([], OPTIMIZER.validate_script(script_path))
        run.assert_called_once_with(["/portable/bash", "-n", str(script_path)], capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()

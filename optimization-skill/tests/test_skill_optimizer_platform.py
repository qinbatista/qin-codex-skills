import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_optimizer.py"
SPECIFICATION = importlib.util.spec_from_file_location("skill_optimizer_platform_test", SCRIPT_PATH)
OPTIMIZER = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[SPECIFICATION.name] = OPTIMIZER
SPECIFICATION.loader.exec_module(OPTIMIZER)


class SkillOptimizerPlatformTests(unittest.TestCase):
    def test_collect_skills_reads_only_direct_visible_skill_children(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            for directory, name in ((skills_root, "active-skill"), (skills_root / "Cache", "cached-skill"), (skills_root / ".scratch", "hidden-skill"), (skills_root / "fixtures", "nested-skill")):
                skill_dir = directory / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use for tests.\n---\n# Skill\n", encoding="utf-8")

            skills = OPTIMIZER.collect_skills(skills_root)

        self.assertEqual(["active-skill"], [skill.name for skill in skills])

    def test_command_paths_resolve_source_relative_global_skill_prefixes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            skill_dir = repo_root / "optimization-skill"
            skill_dir.mkdir()
            paths = [repo_root / "code-skill" / "scripts" / "check.py", repo_root / "project-memory-skill" / "scripts" / "memory.py", repo_root / "workflow-skill" / "scripts" / "run.py"]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("pass\n", encoding="utf-8")
            text = "`skills/code-skill/scripts/check.py` `<codex-home>/skills/project-memory-skill/scripts/memory.py` `~/.codex/skills/workflow-skill/scripts/run.py` and the external data file `AI Memory/ai_memory.py`"

            resolved, errors = OPTIMIZER.extract_command_paths(text, skill_dir, repo_root)

        self.assertEqual([path.resolve() for path in paths], resolved)
        self.assertEqual([], errors)

    def test_command_paths_preserve_explicit_relative_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            skill_dir = repo_root / "sample-skill"
            skill_dir.mkdir()
            paths = [skill_dir / "check.py", repo_root / "parent-check.py", repo_root / "absolute-check.py"]
            for path in paths:
                path.write_text("pass\n", encoding="utf-8")
            text = f"`./check.py` `../parent-check.py` `{paths[2]}` and the external data file `AI Memory/ai_memory.py`"

            resolved, errors = OPTIMIZER.extract_command_paths(text, skill_dir, repo_root)

        self.assertEqual([paths[0].resolve(), paths[1].resolve(), paths[2]], resolved)
        self.assertEqual([], errors)

    def test_semantic_sections_do_not_create_ceremonial_heading_warnings(self):
        headings = ["Activation Boundary", "Admitted Execution", "Privacy And Authorization", "Acceptance Checklist"]
        warnings = OPTIMIZER.build_warnings("# Skill\n", headings, [], [], [], [Path("scripts/check.py")])
        self.assertEqual([], warnings)

    def test_scan_is_concise_by_default_and_verbose_on_request(self):
        summary = OPTIMIZER.SkillSummary(Path("sample"), Path("sample/SKILL.md"), "sample", "long description", ["Scope", "Workflow"], 12)
        concise_output = io.StringIO()
        verbose_output = io.StringIO()
        with redirect_stdout(concise_output):
            OPTIMIZER.print_skill_scan([summary], Path("."))
        with redirect_stdout(verbose_output):
            OPTIMIZER.print_skill_scan([summary], Path("."), verbose=True)
        self.assertNotIn("long description", concise_output.getvalue())
        self.assertIn("long description", verbose_output.getvalue())

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

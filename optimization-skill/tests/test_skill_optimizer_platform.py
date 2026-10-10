import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ARTIFACT_PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT_PROJECT / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_optimizer.py"
SPECIFICATION = importlib.util.spec_from_file_location("skill_optimizer_platform_test", SCRIPT_PATH)
OPTIMIZER = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[SPECIFICATION.name] = OPTIMIZER
SPECIFICATION.loader.exec_module(OPTIMIZER)


class SkillOptimizerPlatformTests(unittest.TestCase):
    def setUp(self):
        self.cache = resolve_task_artifact_root(ARTIFACT_PROJECT, "skill-optimizer-platform-tests", create=True)
        self.addCleanup(self.cache.rmdir)

    def test_collect_skills_reads_only_direct_visible_skill_children(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary_directory:
            skills_root = Path(temporary_directory)
            for directory, name in ((skills_root, "active-skill"), (skills_root / "Cache", "cached-skill"), (skills_root / ".scratch", "hidden-skill"), (skills_root / "fixtures", "nested-skill")):
                skill_dir = directory / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use for tests.\n---\n# Skill\n", encoding="utf-8")

            skills = OPTIMIZER.collect_skills(skills_root)

        self.assertEqual(["active-skill"], [skill.name for skill in skills])

    def test_command_paths_resolve_source_relative_global_skill_prefixes(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary_directory:
            repo_root = Path(temporary_directory)
            skill_dir = repo_root / "optimization-skill"
            skill_dir.mkdir()
            paths = [repo_root / "code-skill" / "scripts" / "check.py", repo_root / "project-memory-skill" / "scripts" / "memory.py", repo_root / "workflow-skill" / "scripts" / "run.py", repo_root / "verify-skill" / "check.py"]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("pass\n", encoding="utf-8")
            text = "`skills/code-skill/scripts/check.py` `<codex-home>/skills/project-memory-skill/scripts/memory.py` `~/.codex/skills/workflow-skill/scripts/run.py` `~/.agents/skills/verify-skill/check.py` and the external data file `AI Memory/ai_memory.py`"
            for command_text in (text, text.replace("/", "\\")):
                with self.subTest(command_text=command_text):
                    resolved, errors = OPTIMIZER.extract_command_paths(command_text, skill_dir, repo_root)
                    self.assertEqual([path.resolve() for path in paths], resolved)
                    self.assertEqual([], errors)

    def test_command_paths_preserve_explicit_relative_and_absolute_paths(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary_directory:
            repo_root = Path(temporary_directory)
            skill_dir = repo_root / "sample-skill"
            skill_dir.mkdir()
            paths = [skill_dir / "check.py", repo_root / "parent-check.py", repo_root / "absolute-check.py"]
            for path in paths:
                path.write_text("pass\n", encoding="utf-8")
            texts = [f"`./check.py` `../parent-check.py` `{paths[2]}`", f"`./check.py` `../parent-check.py` `{paths[2].as_posix()}`", f"`.\\check.py` `..\\parent-check.py` `{paths[2]}`"]
            for command_text in texts:
                with self.subTest(command_text=command_text):
                    resolved, errors = OPTIMIZER.extract_command_paths(command_text + " and the external data file `AI Memory/ai_memory.py`", skill_dir, repo_root)
                    self.assertEqual([paths[0].resolve(), paths[1].resolve(), paths[2]], resolved)
                    self.assertEqual([], errors)

    def test_compact_skill_needs_no_ceremonial_sections(self):
        warnings = OPTIMIZER.build_warnings("Use for bounded edits. Preserve scope and check the changed output.\n", [], [])
        self.assertEqual([], warnings)

    def test_duplicate_rules_are_still_reported_without_heading_checks(self):
        duplicate = OPTIMIZER.DuplicateInstruction([2, 3], "Keep a clear ownership boundary.")
        warnings = OPTIMIZER.build_warnings("# Skill\n", [], [duplicate])
        self.assertEqual(1, len(warnings))
        self.assertIn("duplicate", warnings[0])

    def test_audit_cli_operation_hints_do_not_require_skill_changes(self):
        cases = [("operation-only", "Open the browser and check the result file.\n", 0, False), ("duplicate-policy", "- Preserve source ownership during updates.\n- Preserve source ownership during updates.\n", 0, True), ("broken-reference", "Read [required context](missing.md).\n", 1, False)]
        with tempfile.TemporaryDirectory(prefix="temp-authoring-audit-", dir=self.cache) as directory:
            for name, body, exit_code, recommended in cases:
                with self.subTest(name=name):
                    skill = Path(directory) / name
                    skill.mkdir()
                    source = f"---\nname: {name}\ndescription: Review a bounded operation.\n---\n# Skill\n\n{body}"
                    (skill / "SKILL.md").write_text(source, encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPT_PATH), "audit", str(skill)], capture_output=True, text=True, encoding="utf-8", timeout=20, **OPTIMIZER.hidden_process_options())
                    self.assertEqual(result.returncode, exit_code, result.stderr + result.stdout)
                    self.assertIn(f"- recommended: {'yes' if recommended else 'no'}", result.stdout)
                    if name == "operation-only":
                        self.assertIn("Optional Operation Review", result.stdout)
                    self.assertEqual([path.name for path in skill.iterdir()], ["SKILL.md"])
                    self.assertEqual((skill / "SKILL.md").read_text(encoding="utf-8"), source)

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
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary_directory:
            script_path = Path(temporary_directory) / "sample.applescript"
            script_path.write_text("return 1\n", encoding="utf-8")
            with mock.patch.object(OPTIMIZER.sys, "platform", "win32"), mock.patch.object(OPTIMIZER.subprocess, "run") as run:
                errors = OPTIMIZER.validate_script(script_path)
        self.assertEqual(["AppleScript syntax check is unsupported on win32; run it on macOS."], errors)
        run.assert_not_called()

    def test_shell_validation_resolves_bash_before_launch(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary_directory:
            script_path = Path(temporary_directory) / "sample.sh"
            script_path.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.object(OPTIMIZER.shutil, "which", return_value="/portable/bash"), mock.patch.object(OPTIMIZER.subprocess, "run", return_value=completed) as run:
                self.assertEqual([], OPTIMIZER.validate_script(script_path))
        run.assert_called_once()
        self.assertEqual(run.call_args.args, (["/portable/bash", "-n", str(script_path)],))
        options = run.call_args.kwargs
        self.assertTrue(options["capture_output"])
        self.assertTrue(options["text"])
        if sys.platform == "win32":
            self.assertEqual(set(options), {"capture_output", "text", "creationflags", "startupinfo"})
            self.assertTrue(options["creationflags"] & subprocess.CREATE_NO_WINDOW)
            self.assertTrue(options["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW)
            self.assertEqual(options["startupinfo"].wShowWindow, subprocess.SW_HIDE)
        else:
            self.assertEqual(options, {"capture_output": True, "text": True})


if __name__ == "__main__":
    unittest.main()

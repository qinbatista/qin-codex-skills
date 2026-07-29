import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


CHECKER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_platform_check.py"
CHECKER_SPEC = importlib.util.spec_from_file_location("skill_platform_check", CHECKER_PATH)
skill_platform_check = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(skill_platform_check)
SYNC_PATH = Path(__file__).resolve().parents[2] / "management-skill" / "scripts" / "sync_global_skills.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_global_skills", SYNC_PATH)
sync_global_skills = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(sync_global_skills)
SKILLS_DIR = Path(__file__).resolve().parents[2]


class SkillPlatformCheckTest(unittest.TestCase):
    def fixture_root(self, script_text):
        temporary_directory = tempfile.TemporaryDirectory()
        root = Path(temporary_directory.name) / "skills"
        script_path = root / "sample-skill" / "scripts" / "helper.py"
        script_path.parent.mkdir(parents=True)
        (root / "sample-skill" / "SKILL.md").write_text("---\nname: sample\ndescription: sample\n---\n", encoding="utf-8")
        script_path.write_text(script_text, encoding="utf-8")
        return temporary_directory, root

    def empty_baseline(self):
        return {"schema_version": skill_platform_check.SCHEMA_VERSION, "generated_by": skill_platform_check.BASELINE_GENERATOR, "findings": []}

    def test_portable_python_helper_passes(self):
        temporary_directory, root = self.fixture_root("from pathlib import Path\nimport os\nimport shutil\nimport tempfile\nhome = Path.home()\ncache = os.getenv('CACHE_DIR')\ntemporary = tempfile.gettempdir()\ntool = shutil.which('git')\n")
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_guarded_macos_helper_passes(self):
        source = "import shutil\nimport subprocess\nimport sys\nif sys.platform == 'darwin':\n    tool = shutil.which('osacompile')\n    if tool is None:\n        raise RuntimeError('macOS tool missing')\n    subprocess.run([tool, '--version'])\nelse:\n    raise RuntimeError('macOS only')\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_guarded_windows_helper_passes(self):
        source = "import shutil\nimport subprocess\nimport sys\nif sys.platform == 'win32':\n    tool = shutil.which('cmd.exe')\n    if tool is None:\n        raise RuntimeError('Windows tool missing')\n    subprocess.run([tool, '/c', 'echo'])\nelse:\n    raise RuntimeError('Windows only')\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_pure_platform_control_flow_passes(self):
        source = "import os\ncodex_bin = 'codex'\nif os.name == 'nt':\n    resolved_bin = codex_bin\nelse:\n    resolved_bin = 'WindowsCodex'\nif os.name != 'nt' or codex_bin != 'codex':\n    resolved_bin = codex_bin\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_guarded_windows_command_without_fallback_or_resolver_fails(self):
        source = "import os\nimport subprocess\nif os.name == 'nt':\n    subprocess.run(['cmd.exe', '/c', 'echo'])\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG003"])
        self.assertEqual([finding["line"] for finding in findings], [3])

    def test_guarded_platform_command_with_explicit_return_fallback_passes(self):
        source = "import shutil\nimport subprocess\nimport sys\ndef validate():\n    if sys.platform == 'darwin':\n        tool = shutil.which('osacompile')\n        subprocess.run([tool])\n    else:\n        return 'unsupported'\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_unguarded_macos_command_fails(self):
        temporary_directory, root = self.fixture_root("import subprocess\nsubprocess.run(['osascript', '-e', 'beep'])\n")
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG002"])
        self.assertEqual([finding["line"] for finding in findings], [2])

    def test_unguarded_windows_command_fails(self):
        temporary_directory, root = self.fixture_root("import subprocess\nsubprocess.run(['cmd.exe', '/c', 'echo'])\n")
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG002"])
        self.assertEqual([finding["line"] for finding in findings], [2])

    def test_command_words_in_help_and_error_text_pass(self):
        source = "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--open', help='Open the file')\nraise RuntimeError('Run python3 tool.py on macOS or py -3 tool.py on Windows')\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_unguarded_posix_process_api_fails(self):
        source = "import os\nimport signal\nos.killpg(42, signal.SIGTERM)\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG004"])

    def test_guarded_platform_modules_pass(self):
        source = "import os\nif os.name == 'nt':\n    import msvcrt\nelse:\n    import fcntl\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            self.assertEqual(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline()), [])

    def test_unguarded_platform_subprocess_option_fails(self):
        source = "import subprocess\nsubprocess.Popen(['tool'], start_new_session=True)\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG004"])

    def test_shell_true_fails(self):
        source = "import subprocess\nsubprocess.run(['tool'], shell=True)\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG005"])

    def test_hard_coded_python_child_fails_and_sys_executable_passes(self):
        source = "import subprocess\nimport sys\nsubprocess.run(['python3', 'child.py'])\nsubprocess.run([sys.executable, 'child.py'])\n"
        temporary_directory, root = self.fixture_root(source)
        with temporary_directory:
            findings = skill_platform_check.new_findings(skill_platform_check.collect_findings(root), self.empty_baseline())
        self.assertEqual([finding["rule"] for finding in findings], ["SPG006"])

    def test_selected_file_may_be_relative_to_skills_root(self):
        temporary_directory, root = self.fixture_root("import subprocess\nsubprocess.run(['python3', 'child.py'])\n")
        with temporary_directory:
            findings = skill_platform_check.collect_findings(root, [Path("sample-skill/scripts/helper.py")])
        self.assertEqual([finding["rule"] for finding in findings], ["SPG006"])

    def test_baseline_suppresses_only_existing_occurrence(self):
        temporary_directory, root = self.fixture_root("import subprocess\nsubprocess.run(['osascript'])\n")
        with temporary_directory:
            initial_findings = skill_platform_check.collect_findings(root)
            baseline = {"schema_version": skill_platform_check.SCHEMA_VERSION, "generated_by": skill_platform_check.BASELINE_GENERATOR, "findings": initial_findings}
            self.assertEqual(skill_platform_check.new_findings(initial_findings, baseline), [])
            helper_path = root / "sample-skill" / "scripts" / "helper.py"
            helper_path.write_text("import subprocess\nsubprocess.run(['osascript'])\nsubprocess.run(['osascript'])\n", encoding="utf-8")
            self.assertEqual(len(skill_platform_check.new_findings(skill_platform_check.collect_findings(root), baseline)), 1)

    def test_publisher_fails_before_mutating_repository(self):
        with tempfile.TemporaryDirectory() as temporary_name:
            root = Path(temporary_name)
            staged_skills = root / "skills"
            shutil.copytree(SKILLS_DIR, staged_skills, ignore=shutil.ignore_patterns("cache", "work", "__pycache__"))
            introduced_path = staged_skills / "code-skill" / "scripts" / "introduced.py"
            introduced_path.write_text("import subprocess\nsubprocess.run(['cmd.exe', '/c', 'echo'])\n", encoding="utf-8")
            repository_dir = root / "repository"
            repository_dir.mkdir()
            (repository_dir / "sentinel.txt").write_text("unchanged", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SPG002"):
                sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertEqual((repository_dir / "sentinel.txt").read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()

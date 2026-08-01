import importlib.util
import json
import os
import shutil
import unittest
from unittest import mock
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_AGENTS_PATH = SKILLS_ROOT.parent / "AGENTS.md"
GLOBAL_ENTRY_RULE_PATH = SKILLS_ROOT / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
SYNC_SCRIPT_PATH = SKILLS_ROOT / "management-skill" / "scripts" / "sync_global_skills.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_global_skills", SYNC_SCRIPT_PATH)
SYNC = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(SYNC)
PRIMARY_SKILLS = (
    "task-analyze-skill",
    "workflow-skill",
    "prompt-skill",
    "code-skill",
    "project-memory-skill",
    "verify-skill",
    "optimization-skill",
    "management-skill",
)
REQUIRED_POLICY_TEXT = (
    "<project-root>/Cache/",
    "project-support write",
    "test scripts",
    "intermediate code",
    "`Cache/tests/<task>`",
    "`Cache/debug/<task>`",
    "`Cache/images/<task>`",
    "`~/.codex/cache`",
    "`~/.codex/tmp`",
    "`tmp/`",
    "`tests/`",
    "`work/`",
    "project-root `AGENTS.md`",
    "owner/source",
    "important Cache",
    "explicit authorization",
    "local-machine path",
    "not only Cache paths",
    "project-root-relative",
    "runtime",
    "native path APIs",
    "compact structural contract",
    "not a project notebook",
    "ownership boundaries",
    "critical entry points",
    "hard constraints",
    "Do not write implementation details",
    "task history",
    "test results",
    "generated data",
    "troubleshooting",
    "Cache/cache_path.json",
    "AI-only",
    "project-external",
    "bounded",
    "Obsidian",
)
REQUIRED_DETAILED_PATH_TEXT = (
    "POSIX home absolute path",
    "Windows drive-letter absolute path",
)
REQUIRED_DETAILED_AGENTS_TEXT = (
    "retention/version-control status",
    "one concise registry entry",
    "owning source, project documentation, or a README",
    "Update `AGENTS.md` only when",
)
REQUIRED_DETAILED_REGISTRY_TEXT = (
    "schema_version",
    "scope",
    "ai_only",
    "file|directory|application",
    "package scripts",
    "credentials",
    "replace the registry atomically",
    "CODEX_OBSIDIAN_VAULT",
)


class ProjectCacheArtifactPolicyTests(unittest.TestCase):
    def test_every_primary_skill_has_the_same_project_cache_contract(self):
        for skill_name in PRIMARY_SKILLS:
            skill_text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Project Cache Artifact Policy", skill_text, skill_name)
            for required_text in REQUIRED_POLICY_TEXT:
                self.assertIn(required_text, skill_text, f"{skill_name}: {required_text}")
            for required_text in REQUIRED_DETAILED_PATH_TEXT:
                self.assertIn(required_text, skill_text, f"{skill_name}: {required_text}")
            for required_text in REQUIRED_DETAILED_AGENTS_TEXT:
                self.assertIn(required_text, skill_text, f"{skill_name}: {required_text}")
            for required_text in REQUIRED_DETAILED_REGISTRY_TEXT:
                self.assertIn(required_text, skill_text, f"{skill_name}: {required_text}")

    def test_global_agents_and_installable_entry_rule_have_the_same_contract(self):
        for policy_path in (GLOBAL_AGENTS_PATH, GLOBAL_ENTRY_RULE_PATH):
            policy_text = policy_path.read_text(encoding="utf-8")
            self.assertIn("Project Cache artifact policy", policy_text, str(policy_path))
            for required_text in REQUIRED_POLICY_TEXT:
                self.assertIn(required_text, policy_text, f"{policy_path}: {required_text}")

    def test_existing_cache_category_is_reused_and_task_cleanup_is_scoped(self):
        task_root = SKILLS_ROOT / "management-skill" / "Cache" / "tests" / "cache-artifact-policy-smoke"
        project_root = task_root / "fixture-project"
        cache_root = project_root / "Cache"
        existing_category = cache_root / "images"
        artifact = existing_category / "inspection.json"
        try:
            existing_category.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"status":"placed-in-existing-category"}\n', encoding="utf-8")
            self.assertTrue(artifact.is_file())
            self.assertEqual(artifact.parent, existing_category)
            self.assertEqual(existing_category.parent, cache_root)
            self.assertNotIn("tmp", artifact.parts)
            self.assertNotIn("work", artifact.parts)
        finally:
            shutil.rmtree(task_root)
            for directory in (task_root.parent, task_root.parent.parent):
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()

    def test_management_sync_uses_the_configured_project_cache(self):
        task_root = SKILLS_ROOT / "management-skill" / "Cache" / "tests" / "cache-artifact-policy-sync-smoke"
        try:
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(task_root)}):
                with SYNC.temporary_workspace("mirror-") as workspace:
                    marker = workspace / "marker.txt"
                    marker.write_text("cache-backed\n", encoding="utf-8")
                    self.assertEqual(workspace.parent, task_root)
                    self.assertTrue(marker.is_file())
        finally:
            shutil.rmtree(task_root)
            for directory in (task_root.parent, task_root.parent.parent):
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()

    def test_management_sync_default_paths_are_derived_from_the_project(self):
        expected_project_root = SYNC_SCRIPT_PATH.resolve().parents[3]
        self.assertEqual(SYNC.DEFAULT_PROJECT_ROOT, expected_project_root)
        self.assertEqual(SYNC.DEFAULT_CACHE_ROOT, expected_project_root / "Cache" / "management-skill-sync")
        self.assertEqual(SYNC.DEFAULT_STATE_FILE, expected_project_root / "state" / "management-skill-sync.json")

    def test_important_cache_content_is_registered_in_project_agents(self):
        task_root = SKILLS_ROOT / "management-skill" / "Cache" / "tests" / "cache-agents-registration-smoke"
        project_root = task_root / "fixture-project"
        important_path = project_root / "Cache" / "tests" / "logic-regression" / "run_check.py"
        details_path = important_path.parent / "README.md"
        agents_path = project_root / "AGENTS.md"
        try:
            important_path.parent.mkdir(parents=True, exist_ok=True)
            important_path.write_text("print('project logic regression')\n", encoding="utf-8")
            details_path.write_text("Run with the project Python runtime. Dependencies: standard library.\n", encoding="utf-8")
            agents_path.write_text(
                "# Project structure\n\n"
                "- `Cache/tests/logic-regression/` — retained, source-controlled regression entry point; owner: project test policy; details: `Cache/tests/logic-regression/README.md`.\n",
                encoding="utf-8",
            )
            agents_text = agents_path.read_text(encoding="utf-8")
            self.assertTrue(important_path.is_relative_to(project_root / "Cache"))
            for expected in ("Cache/tests/logic-regression/", "regression entry point", "owner:", "retained", "source-controlled", "README.md"):
                self.assertIn(expected, agents_text)
            for forbidden in ("Dependencies:", "Run/use/regenerate:", "test result", "troubleshooting"):
                self.assertNotIn(forbidden, agents_text)
            self.assertIn("Dependencies:", details_path.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(task_root)
            for directory in (task_root.parent, task_root.parent.parent):
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()

    def test_absolute_path_registry_is_ai_only_and_project_code_does_not_depend_on_it(self):
        task_root = SKILLS_ROOT / "management-skill" / "Cache" / "tests" / "cache-path-registry-smoke"
        project_root = task_root / "fixture-project"
        registry_path = project_root / "Cache" / "cache_path.json"
        external_target = task_root / "external" / "vault"
        project_source = project_root / "src" / "app.py"
        try:
            external_target.mkdir(parents=True, exist_ok=True)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "scope": "ai_only",
                        "paths": {
                            "obsidian_vault": {
                                "path": str(external_target.resolve()),
                                "kind": "directory",
                                "purpose": "AI-only vault access",
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            project_source.parent.mkdir(parents=True, exist_ok=True)
            project_source.write_text("def run():\n    return 'project-runtime-independent'\n", encoding="utf-8")

            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            entry = registry["paths"]["obsidian_vault"]
            self.assertEqual(registry["schema_version"], 1)
            self.assertEqual(registry["scope"], "ai_only")
            self.assertTrue(Path(entry["path"]).is_absolute())
            self.assertTrue(Path(entry["path"]).is_dir())
            self.assertTrue(registry_path.is_relative_to(project_root / "Cache"))
            self.assertNotIn("cache_path.json", project_source.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(task_root)
            for directory in (task_root.parent, task_root.parent.parent):
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()

    def test_project_handoffs_do_not_require_absolute_project_paths(self):
        instruction_paths = (
            SKILLS_ROOT / "task-analyze-skill" / "SKILL.md",
            SKILLS_ROOT / "workflow-skill" / "SKILL.md",
            SKILLS_ROOT / "code-skill" / "SKILL.md",
            SKILLS_ROOT / "verify-skill" / "SKILL.md",
            SKILLS_ROOT / "task-analyze-skill" / "references" / "route-contract.md",
        )
        for instruction_path in instruction_paths:
            instruction_text = instruction_path.read_text(encoding="utf-8")
            self.assertIn("project-root-relative paths", instruction_text, str(instruction_path))
            self.assertNotIn("absolute project paths", instruction_text, str(instruction_path))


if __name__ == "__main__":
    unittest.main()

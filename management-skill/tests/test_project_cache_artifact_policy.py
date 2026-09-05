import importlib.util
import json
import os
import shutil
import unittest
from unittest import mock
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_AGENTS_PATH = Path.home() / ".codex" / "AGENTS.md"
GLOBAL_ENTRY_RULE_PATH = SKILLS_ROOT / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
PROJECT_CACHE_POLICY_PATH = SKILLS_ROOT / "workflow-skill" / "references" / "project-cache-artifact-policy.md"
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
    "ordinary test scratch",
    "intermediate code",
    "`Cache/tmp-<name>/`",
    "`Cache/remote-<name>/`",
    "`Cache/<YYYYMMDD>/`",
    "`Cache/remote-test/`",
    "top-level `tmp/`, `tests/`, or `work/`",
    "legacy top-level directory",
    "`~/.codex/cache`",
    "`~/.codex/tmp`",
    "Project-root `AGENTS.md`",
    "owner/source",
    "Important retained Cache",
    "explicit authorization",
    "local-machine path",
    "not only Cache paths",
    "project-root-relative",
    "runtime",
    "native APIs",
    "compact structural contract",
    "not a project notebook",
    "ownership boundaries",
    "critical entry points",
    "hard constraints",
    "Do not put implementation details",
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
    "one concise `AGENTS.md` registry entry",
    "owning source, project documentation, or a README",
    "Update `AGENTS.md` only when",
)
REQUIRED_DETAILED_REGISTRY_TEXT = (
    "schema_version",
    "scope",
    "ai_only",
    "`file|directory|application`",
    "package scripts",
    "credentials",
    "replace the registry atomically",
    "CODEX_OBSIDIAN_VAULT",
)
REQUIRED_GLOBAL_POLICY_TEXT = (
    "Cache:project support only in `<project-root>/Cache/`",
    "one-task scratch/test/intermediate=>`tmp-*`",
    "short reuse=>`<YYYYMMDD>`+reason/review",
    "`remote-*`/`remote-test/`=>explicit retain only",
    "formal reusable tests stay source",
)


class ProjectCacheArtifactPolicyTests(unittest.TestCase):
    def test_canonical_project_cache_contract_retains_every_required_rule(self):
        policy_text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        for required_text in (*REQUIRED_POLICY_TEXT, *REQUIRED_DETAILED_PATH_TEXT, *REQUIRED_DETAILED_AGENTS_TEXT, *REQUIRED_DETAILED_REGISTRY_TEXT):
            self.assertIn(required_text, policy_text, f"{PROJECT_CACHE_POLICY_PATH}: {required_text}")

    def test_workflow_links_the_single_cache_policy(self):
        text = (SKILLS_ROOT / "workflow-skill/SKILL.md").read_text()
        self.assertIn("references/project-cache-artifact-policy.md", text)
        self.assertIn("references/task-resource-lifecycle.md", text)


    def test_installable_entry_keeps_scoped_scratch_and_preservation(self):
        text = GLOBAL_ENTRY_RULE_PATH.read_text()
        self.assertIn("project Cache/tmp-*", text)
        self.assertIn("preserve unrelated work", text)


    @unittest.skipUnless(os.environ.get("VERIFY_INSTALLED_GLOBAL_SKILLS") == "1", "installed-global parity is checked after deployment")
    def test_installed_global_agents_has_the_same_contract(self):
        self.assertIn("project Cache/tmp-*", GLOBAL_AGENTS_PATH.read_text())


    def test_resource_policy_limits_automatic_cleanup(self):
        text = (SKILLS_ROOT / "workflow-skill/references/task-resource-lifecycle.md").read_text()
        self.assertIn("last consumer", text)
        self.assertIn("task-owned `Cache/tmp-*`", text)
        self.assertIn("shared, pre-existing, conflicted, Unity, dated, or remote", text)
        self.assertIn("never controls, interrupts, archives, or deletes another", text)


    def test_existing_cache_category_is_reused_and_task_cleanup_is_scoped(self):
        task_root = SKILLS_ROOT / "Cache" / "tmp-cache-artifact-policy-smoke"
        project_root = task_root / "fixture-project"
        cache_root = project_root / "Cache"
        existing_category = cache_root / "remote-test"
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
        task_root = SKILLS_ROOT / "Cache" / "tmp-cache-artifact-policy-sync-smoke"
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
        expected_project_root = SYNC_SCRIPT_PATH.resolve().parents[2]
        expected_cache_root = expected_project_root / "Cache" / "tmp-management-skill-sync"
        self.assertEqual(SYNC.DEFAULT_SOURCE_DIR, expected_project_root)
        self.assertEqual(SYNC.DEFAULT_PROJECT_ROOT, expected_project_root)
        self.assertEqual(SYNC.DEFAULT_CACHE_ROOT, expected_cache_root)
        self.assertEqual(SYNC.DEFAULT_STATE_FILE, expected_cache_root / "state" / "management-skill-sync.json")

    def test_important_cache_content_is_registered_in_project_agents(self):
        task_root = SKILLS_ROOT / "Cache" / "tmp-cache-agents-registration-smoke"
        project_root = task_root / "fixture-project"
        important_path = project_root / "Cache" / "remote-test" / "logic-regression" / "run_check.py"
        details_path = important_path.parent / "README.md"
        agents_path = project_root / "AGENTS.md"
        try:
            important_path.parent.mkdir(parents=True, exist_ok=True)
            important_path.write_text("print('project logic regression')\n", encoding="utf-8")
            details_path.write_text("Run with the project Python runtime. Dependencies: standard library.\n", encoding="utf-8")
            agents_path.write_text(
                "# Project structure\n\n"
                "- `Cache/remote-test/logic-regression/` — retained, source-controlled regression entry point; owner: project test policy; details: `Cache/remote-test/logic-regression/README.md`.\n",
                encoding="utf-8",
            )
            agents_text = agents_path.read_text(encoding="utf-8")
            self.assertTrue(important_path.is_relative_to(project_root / "Cache"))
            for expected in ("Cache/remote-test/logic-regression/", "regression entry point", "owner:", "retained", "source-controlled", "README.md"):
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
        task_root = SKILLS_ROOT / "Cache" / "tmp-cache-path-registry-smoke"
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

    def test_portable_paths_have_one_canonical_owner(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text()
        self.assertIn("project-root-relative paths", text)
        self.assertIn("native APIs", text)
        self.assertIn("AI-only", text)



if __name__ == "__main__":
    unittest.main()

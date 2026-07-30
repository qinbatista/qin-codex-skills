import importlib.util
import os
import shutil
import unittest
from unittest import mock
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[2]
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
    "inspect an existing `Cache/` and reuse its established top-level category",
    "`Cache/tests/<task>`, `Cache/debug/<task>`, or `Cache/images/<task>`",
    "`~/.codex/cache`, `~/.codex/tmp`",
    "an ad hoc `tmp`/`work` path",
    "current task's named Cache folder",
)


class ProjectCacheArtifactPolicyTests(unittest.TestCase):
    def test_every_primary_skill_has_the_same_project_cache_contract(self):
        for skill_name in PRIMARY_SKILLS:
            skill_text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Project Cache Artifact Policy", skill_text, skill_name)
            for required_text in REQUIRED_POLICY_TEXT:
                self.assertIn(required_text, skill_text, f"{skill_name}: {required_text}")

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


if __name__ == "__main__":
    unittest.main()

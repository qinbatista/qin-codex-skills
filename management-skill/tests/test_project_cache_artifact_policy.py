import importlib.util
import os
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


SKILLS_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ENTRY_RULE_PATH = SKILLS_ROOT / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
PROJECT_CACHE_POLICY_PATH = SKILLS_ROOT / "workflow-skill" / "references" / "project-cache-artifact-policy.md"
SYNC_SCRIPT_PATH = SKILLS_ROOT / "management-skill" / "scripts" / "sync_global_skills.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_global_skills", SYNC_SCRIPT_PATH)
SYNC = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(SYNC)
ARTIFACT_SCRIPT_PATH = SKILLS_ROOT / "workflow-skill" / "scripts" / "task_artifact_paths.py"
ARTIFACT_SPEC = importlib.util.spec_from_file_location("policy_task_artifact_paths", ARTIFACT_SCRIPT_PATH)
ARTIFACTS = importlib.util.module_from_spec(ARTIFACT_SPEC)
ARTIFACT_SPEC.loader.exec_module(ARTIFACTS)
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


@contextmanager
def external_fixture():
    task_root = ARTIFACTS.resolve_task_artifact_root(
        SKILLS_ROOT, f"external-policy-test-{uuid.uuid4().hex}", create=True
    )
    try:
        with tempfile.TemporaryDirectory(prefix="policy-", dir=task_root) as directory:
            yield Path(directory)
    finally:
        task_root.rmdir()


class ProjectCacheArtifactPolicyTests(unittest.TestCase):
    def test_canonical_policy_requires_external_first_write_and_real_owner_preservation(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        required_rules = (
            "outside every project directory and Codex-managed storage from its first write",
            "YOFA_TASK_ARTIFACT_ROOT",
            "Discovered home joined with",
            "XDG_CACHE_HOME",
            "task_artifact_paths.py",
            "resolve_task_artifact_root",
            "task_artifact_environment",
            "Missing, invalid or unavailable",
            "Reject links/reparse points",
            "`tempfile` only with an explicit directory",
            "Disable project-local bytecode, pytest, coverage",
            "canonical asset originals/history",
            "versioned non-runtime tests",
            "requested final deliverables",
            "Do not blanket move a project's Cache",
            "creation history, file identity and current consumer checks",
            "preserve bytes/hashes",
            "never a way to bypass a rejected deletion",
            "git diff --cached --name-status",
            "Temporary files never enter Git",
            "configured Obsidian vault",
        )
        for required in required_rules:
            with self.subTest(rule=required):
                self.assertIn(required, text)
        self.assertNotIn("Use only the resolved workspace's ignored", text)

    def test_all_managed_entries_link_the_single_external_policy_before_support_writes(self):
        for skill in PRIMARY_SKILLS:
            text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("project-cache-artifact-policy.md", text)
                self.assertIn("first write", text)
                self.assertIn("external", text)
                self.assertNotIn("`Cache/temp-<task>/`", text)

    def test_installable_entry_preserves_global_agents_and_forbids_project_scratch(self):
        text = GLOBAL_ENTRY_RULE_PATH.read_text(encoding="utf-8")
        for required in (
            "deploy, pull, and sync preserve user AGENTS.md files",
            "outside every project directory and Codex-managed storage",
            "from its first write",
            "YOFA_TASK_ARTIFACT_ROOT",
            "exact project identity and task ID",
            "child TMP/TEMP/TMPDIR before launch",
            "real runtime/asset Cache owners",
            "moving is never a bypass for rejected deletion",
            "temporary files never enter Git",
            "minimum recovery inputs/state",
            "preserve unrelated work",
        ):
            with self.subTest(rule=required):
                self.assertIn(required, text)
        self.assertNotIn("current task workspace's Cache", text)
        self.assertNotIn("Cache/temp-<task>/", text)

    @unittest.skipUnless(
        os.environ.get("VERIFY_INSTALLED_GLOBAL_SKILLS") == "1",
        "installed Skill policy is checked after deployment; user AGENTS is preserved",
    )
    def test_installed_skill_entries_have_the_same_external_contract(self):
        installed_root = Path.home() / ".agents" / "skills"
        for skill in PRIMARY_SKILLS:
            expected = (SKILLS_ROOT / skill / "SKILL.md").read_bytes()
            actual = (installed_root / skill / "SKILL.md").read_bytes()
            with self.subTest(skill=skill):
                self.assertEqual(actual, expected)

    def test_resource_cleanup_is_exact_and_preserves_review_recovery_and_other_tasks(self):
        text = (SKILLS_ROOT / "workflow-skill/references/task-resource-lifecycle.md").read_text(encoding="utf-8")
        for required in (
            "external artifact policy",
            "Legacy project-Cache ledgers stay read-only",
            "fresh process or website request",
            "minimum inputs and resumable state",
            "never authorizes indefinite temp retention",
            "bounds-check every deletion target",
            "no unknown files remain",
            "never controls, interrupts, archives, or deletes another",
        ):
            self.assertIn(required, text)
        self.assertNotIn("`Cache/temp-<task>/` scratch", text)
        owners = (
            SKILLS_ROOT / "AGENTS.md",
            SKILLS_ROOT / "workflow-skill/SKILL.md",
            SKILLS_ROOT / "verify-skill/SKILL.md",
            SKILLS_ROOT / "management-skill/SKILL.md",
            GLOBAL_ENTRY_RULE_PATH,
            PROJECT_CACHE_POLICY_PATH,
        )
        for path in owners:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("owner", text)
                self.assertIn("recovery", text)
                self.assertRegex(text, r"review.{0,20}reuse")

    def test_test_and_private_fixture_registry_placement_keeps_source_independent(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        for required in (
            "Remove obsolete and duplicate cases",
            "versioned, non-runtime development area",
            "execute the affected test from its final location",
            "private non-memory registry in a declared external AI resource owner",
            '"schema_version": 2',
            '"scope": "ai_only"',
            "Project source, runtime, tests, package scripts, build, CI, and shipped configuration must never read this registry",
            "compact structural contract, not a project notebook",
        ):
            self.assertIn(required, text)
        self.assertNotIn("Cache/remote-ai-paths/registry.json", text)

    def test_public_readmes_inherit_the_maintained_external_policy(self):
        with external_fixture() as fixture:
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(fixture)}):
                with SYNC.temporary_workspace("readme-policy-") as workspace:
                    SYNC.render_source_readmes(workspace, [SKILLS_ROOT / name for name in PRIMARY_SKILLS])
                    for suffix in ("", ".zh"):
                        template = SKILLS_ROOT / "management-skill/assets/readme" / f"github-readme-template{suffix}.md"
                        rule = next(
                            line for line in template.read_text(encoding="utf-8").splitlines()
                            if "YoFaAI/TaskArtifacts" in line
                        )
                        with self.subTest(language=suffix or "en"):
                            published = (workspace / f"README{suffix}.md").read_text(encoding="utf-8")
                            self.assertIn(rule, published)
                            self.assertNotIn("Cache/temp-<task>/", rule)
                self.assertFalse(workspace.exists())

    def test_resolved_projects_and_tasks_are_isolated_and_preserve_canonical_cache(self):
        with external_fixture() as fixture:
            project_one = fixture / "one" / "game"
            project_two = fixture / "two" / "game"
            project_one.mkdir(parents=True)
            project_two.mkdir(parents=True)
            original = project_one / "Cache" / "remote-assets" / "original.bin"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"canonical asset bytes")
            base = fixture / "task-artifacts"
            roots = (
                ARTIFACTS.resolve_task_artifact_root(project_one, "same-task", artifact_root=base, create=True),
                ARTIFACTS.resolve_task_artifact_root(project_two, "same-task", artifact_root=base, create=True),
                ARTIFACTS.resolve_task_artifact_root(project_one, "other-task", artifact_root=base, create=True),
            )
            self.assertEqual(len(set(roots)), 3)
            for root in roots:
                self.assertTrue(root.is_relative_to(base))
                self.assertFalse(root.is_relative_to(project_one))
                self.assertFalse(root.is_relative_to(project_two))
            environment = ARTIFACTS.task_artifact_environment(roots[0], create=True)
            for name in ("TMP", "TEMP", "TMPDIR"):
                self.assertEqual(Path(environment[name]), roots[0] / "tmp")
            self.assertEqual(original.read_bytes(), b"canonical asset bytes")
            self.assertEqual(list(project_one.iterdir()), [project_one / "Cache"])

    def test_management_workspace_cleanup_is_scoped_and_keeps_adjacent_resources(self):
        with external_fixture() as fixture:
            retained = fixture / "retained.bin"
            retained.write_bytes(b"keep for user review")
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(fixture)}):
                with SYNC.temporary_workspace("mirror-") as workspace:
                    marker = workspace / "marker.txt"
                    marker.write_text("external support\n", encoding="utf-8")
                    self.assertEqual(workspace.parent, fixture)
                    self.assertFalse(workspace.is_relative_to(SKILLS_ROOT))
                    self.assertEqual(marker.read_text(encoding="utf-8"), "external support\n")
                self.assertFalse(workspace.exists())
                self.assertEqual(retained.read_bytes(), b"keep for user review")

    def test_invalid_management_paths_fail_before_any_scratch_write(self):
        invalid_paths = (
            SKILLS_ROOT / "Cache" / "temp-retired",
            SKILLS_ROOT / "management-skill",
            Path.home() / ".codex" / "policy-test",
            Path("relative-scratch"),
            Path("%SystemDrive%") / "policy-test",
        )
        for invalid in invalid_paths:
            with self.subTest(invalid=invalid):
                with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(invalid)}):
                    with mock.patch.object(Path, "mkdir", side_effect=AssertionError("invalid scratch must fail before writing")):
                        with self.assertRaises(ValueError):
                            with SYNC.temporary_workspace("rejected-"):
                                self.fail("invalid scratch was accepted")

    def test_management_default_state_and_support_are_external(self):
        self.assertEqual(SYNC.DEFAULT_SOURCE_DIR, SYNC_SCRIPT_PATH.resolve().parents[2])
        self.assertEqual(SYNC.DEFAULT_PROJECT_ROOT, Path.cwd().resolve())
        expected_root = ARTIFACTS.resolve_task_artifact_root(SYNC.DEFAULT_PROJECT_ROOT, "management-skill-sync")
        self.assertEqual(SYNC.DEFAULT_CACHE_ROOT, expected_root)
        self.assertEqual(SYNC.DEFAULT_STATE_FILE, expected_root / "state" / "management-skill-sync.json")
        self.assertFalse(expected_root.is_relative_to(SYNC.DEFAULT_PROJECT_ROOT))


if __name__ == "__main__":
    unittest.main()

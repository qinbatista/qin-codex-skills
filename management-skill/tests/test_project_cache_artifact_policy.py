import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


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
    def test_canonical_policy_requires_project_cache_first_write_and_owner_preservation(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        required_rules = (
            "owning project's ignored `Cache/temp-<task>/` from their first write",
            "task_artifact_paths.py",
            "TMP`, `TEMP` and `TMPDIR",
            "Reject links and reparse paths",
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
        self.assertNotIn("outside every project directory and Codex-managed storage", text)

    def test_all_managed_entries_link_the_single_cache_policy_before_support_writes(self):
        for skill in PRIMARY_SKILLS:
            text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("project-cache-artifact-policy.md", text)
                self.assertIn("first write", text)
                self.assertIn("Cache", text)

    def test_installable_entry_preserves_global_agents_and_requires_project_cache(self):
        text = GLOBAL_ENTRY_RULE_PATH.read_text(encoding="utf-8")
        for required in (
            "deploy, pull, and sync preserve user AGENTS.md files",
            "owning project's ignored Cache/temp-<task>/",
            "from their first write",
            "fresh task run for each execution",
            "child TMP/TEMP/TMPDIR",
            "actual runtime or asset owners",
            "temporary files never enter Git",
            "minimum recovery inputs/state",
            "preserve unrelated work",
        ):
            with self.subTest(rule=required):
                self.assertIn(required, text)
        self.assertNotIn("outside every project directory and Codex-managed storage", text)

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
            "project Cache artifact policy",
            "project Cache ledgers remain bound",
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
                            if "Cache/temp-<task>/" in line
                        )
                        with self.subTest(language=suffix or "en"):
                            published = (workspace / f"README{suffix}.md").read_text(encoding="utf-8")
                            self.assertIn(rule, published)
                            self.assertIn("Cache/temp-<task>/", rule)
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
            roots = (
                ARTIFACTS.resolve_task_artifact_root(project_one, "same-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_two, "same-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_one, "other-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_one, "same-task", create=True),
            )
            self.assertEqual(len(set(roots)), 4)
            for root, owner in zip(roots, (project_one, project_two, project_one, project_one)):
                self.assertEqual(root.parent, owner / "Cache")
            environment = ARTIFACTS.task_artifact_environment(roots[0], create=True)
            for name in ("TMP", "TEMP", "TMPDIR"):
                self.assertEqual(Path(environment[name]), roots[0] / "tmp")
            self.assertEqual(original.read_bytes(), b"canonical asset bytes")
            self.assertEqual(list(project_one.iterdir()), [project_one / "Cache"])

    def test_continuation_copies_selected_bytes_without_links_overwrites_or_old_builds(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            base = project / "Cache"
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", artifact_root=base, create=True)
            following = ARTIFACTS.resolve_task_artifact_root(project, "chat", artifact_root=base, create=True)
            (previous / "input.bin").write_bytes(b"useful input")
            (previous / "build.bin").write_bytes(b"discard build output")
            receipts = ARTIFACTS.copy_run_inputs(project, previous, following, ["input.bin"])
            self.assertEqual((following / "input.bin").read_bytes(), b"useful input")
            self.assertEqual(receipts, [{"path": "input.bin", "sha256": ARTIFACTS._file_sha256(previous / "input.bin")}])
            self.assertFalse((following / "build.bin").exists())
            for selection in (["../build.bin"], ["input.bin"], ["input.bin", "input.bin"]):
                with self.subTest(selection=selection), self.assertRaises(ValueError):
                    ARTIFACTS.copy_run_inputs(project, previous, following, selection)
            with self.assertRaises(ValueError):
                ARTIFACTS.copy_run_inputs(project, previous, previous, ["input.bin"])
            link = previous / "linked.bin"
            try:
                link.symlink_to(previous / "build.bin")
            except OSError:
                return
            with self.assertRaises(ValueError):
                ARTIFACTS.copy_run_inputs(project, previous, following, ["linked.bin"])
            self.assertFalse((following / "linked.bin").exists())

    def test_cli_continuation_allocates_fresh_run_for_same_chat(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            command = [sys.executable, "-B", str(ARTIFACT_SCRIPT_PATH), "--project-root", str(project), "--task-id", "same-chat", "--create"]
            previous = json.loads(subprocess.run(command, capture_output=True, text=True, check=True, **hidden_process_options()).stdout)
            source = Path(previous["task_root"])
            (source / "fixture.bin").write_bytes(b"continued test input")
            following = json.loads(subprocess.run([*command, "--copy-from", str(source), "--input", "fixture.bin"], capture_output=True, text=True, check=True, **hidden_process_options()).stdout)
            destination = Path(following["task_root"])
            self.assertNotEqual(source, destination)
            self.assertNotEqual(previous["run_id"], following["run_id"])
            self.assertEqual((destination / "fixture.bin").read_bytes(), b"continued test input")
            self.assertEqual(following["temporary_environment"]["TMPDIR"], str(destination / "tmp"))

    def test_failed_cli_copy_removes_new_run_and_keeps_original_inputs(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            (previous / "input.bin").write_bytes(b"keep original input")
            command = [sys.executable, "-B", str(ARTIFACT_SCRIPT_PATH), "--project-root", str(project), "--task-id", "chat", "--create", "--copy-from", str(previous), "--input", "missing.bin"]
            result = subprocess.run(command, capture_output=True, text=True, check=False, **hidden_process_options())
            self.assertEqual(result.returncode, 2)
            failure = json.loads(result.stderr)
            self.assertEqual(failure["cleanup"], "removed")
            self.assertFalse(Path(failure["task_root"]).exists())
            self.assertNotEqual(Path(failure["task_root"]), previous)
            self.assertEqual((previous / "input.bin").read_bytes(), b"keep original input")

    def test_partial_copy_error_rolls_back_only_newly_created_files(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            following = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            (previous / "input.bin").write_bytes(b"keep original")
            sentinel = following / "other.bin"
            sentinel.write_bytes(b"keep unrelated destination")
            def partial_failure(reader, writer):
                writer.write(reader.read(4))
                raise OSError("injected write failure")
            with mock.patch.object(ARTIFACTS.shutil, "copyfileobj", side_effect=partial_failure), self.assertRaises(OSError):
                ARTIFACTS.copy_run_inputs(project, previous, following, ["input.bin"])
            self.assertEqual(list(following.iterdir()), [sentinel])
            self.assertEqual(sentinel.read_bytes(), b"keep unrelated destination")
            self.assertEqual((previous / "input.bin").read_bytes(), b"keep original")

    def test_management_workspace_cleanup_is_scoped_and_keeps_adjacent_resources(self):
        with external_fixture() as fixture:
            retained = fixture / "retained.bin"
            retained.write_bytes(b"keep for user review")
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(fixture)}):
                with SYNC.temporary_workspace("mirror-") as workspace:
                    marker = workspace / "marker.txt"
                    marker.write_text("external support\n", encoding="utf-8")
                    self.assertEqual(workspace.parent, fixture)
                    self.assertTrue(workspace.is_relative_to(SKILLS_ROOT / "Cache"))
                    self.assertEqual(marker.read_text(encoding="utf-8"), "external support\n")
                self.assertFalse(workspace.exists())
                self.assertEqual(retained.read_bytes(), b"keep for user review")

    def test_invalid_management_paths_fail_before_any_scratch_write(self):
        invalid_paths = (
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

    def test_management_default_state_and_support_are_in_project_cache(self):
        self.assertEqual(SYNC.DEFAULT_SOURCE_DIR, SYNC_SCRIPT_PATH.resolve().parents[2])
        self.assertEqual(SYNC.DEFAULT_PROJECT_ROOT, Path.cwd().resolve())
        expected_root = ARTIFACTS.resolve_task_artifact_root(SYNC.DEFAULT_PROJECT_ROOT, "management-skill-sync", run_id=ARTIFACTS.task_artifact_run_id(SYNC.DEFAULT_CACHE_ROOT))
        self.assertEqual(SYNC.DEFAULT_CACHE_ROOT, expected_root)
        self.assertEqual(SYNC.DEFAULT_STATE_FILE, expected_root / "state" / "management-skill-sync.json")
        self.assertEqual(expected_root.parent, SYNC.DEFAULT_PROJECT_ROOT / "Cache")


if __name__ == "__main__":
    unittest.main()

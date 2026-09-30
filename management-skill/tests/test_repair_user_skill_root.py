import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("repair_user_skill_root", SCRIPTS / "repair_user_skill_root.py")
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)
INSTALLER = REPAIR.load_installer()


class UserSkillRootRepairTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="skill-root-repair-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "home"
        self.codex = self.home / "custom-codex"
        self.legacy = self.codex / "skills"
        self.official = self.home / ".agents" / "skills"
        self.backups = self.home / ".agents" / "skill-migration-backups"
        environment = mock.patch.dict(os.environ, {"CODEX_HOME": str(self.codex)})
        environment.start()
        self.addCleanup(environment.stop)
        home = mock.patch.object(Path, "home", return_value=self.home)
        home.start()
        self.addCleanup(home.stop)

    def skill(self, root, name="custom-skill", content="legacy instructions"):
        path = root / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(content, encoding="utf-8")
        (path / "AGENTS.md").write_bytes(b"User rules\r\n")
        (path / "empty").mkdir()
        return path

    def test_audit_is_read_only_and_missing_target_is_planned(self):
        source = self.skill(self.legacy)
        original = REPAIR.tree_manifest(source)
        result = REPAIR.repair_user_skill_root()
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["entries"][0]["action"], "copy_then_retire")
        self.assertEqual(REPAIR.tree_manifest(source), original)
        self.assertFalse(self.official.exists())
        self.assertFalse(self.backups.exists())
        self.assertFalse((self.codex / INSTALLER.INSTALL_LOCK_NAME).exists())

    def test_apply_preserves_all_bytes_and_non_skill_entries_and_is_idempotent(self):
        source = self.skill(self.legacy)
        expected = REPAIR.tree_manifest(source)
        bundled = self.skill(self.legacy, ".system", "bundled")
        (self.legacy / "AGENTS.md").write_text("root rules", encoding="utf-8")
        (self.legacy / "notes").mkdir()
        (self.legacy / "notes" / "keep.txt").write_bytes(b"keep")
        result = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(result["status"], "repaired")
        entry = next(item for item in result["entries"] if item["name"] == source.name)
        self.assertFalse(source.exists())
        self.assertEqual(REPAIR.tree_manifest(self.official / source.name), expected)
        self.assertEqual(REPAIR.tree_manifest(Path(entry["backup"]) / "copy"), expected)
        self.assertEqual(REPAIR.tree_manifest(Path(entry["retired"])), expected)
        self.assertTrue(bundled.exists())
        self.assertEqual((self.legacy / "AGENTS.md").read_text(encoding="utf-8"), "root rules")
        self.assertEqual((self.legacy / "notes" / "keep.txt").read_bytes(), b"keep")
        backups = sorted(self.backups.iterdir())
        self.assertEqual(REPAIR.repair_user_skill_root(apply=True)["status"], "unchanged")
        self.assertEqual(sorted(self.backups.iterdir()), backups)

    def test_identical_target_is_retained_and_conflicting_target_is_pending(self):
        self.skill(self.legacy, "same")
        same = self.skill(self.official, "same")
        self.skill(self.legacy, "conflict", "old")
        conflict = self.skill(self.official, "conflict", "new")
        before = REPAIR.tree_manifest(same)
        result = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertFalse((self.legacy / "same").exists())
        self.assertEqual(REPAIR.tree_manifest(same), before)
        self.assertEqual((conflict / "SKILL.md").read_text(encoding="utf-8"), "new")
        self.assertEqual((self.legacy / "conflict" / "SKILL.md").read_text(encoding="utf-8"), "old")

    def test_managed_conflict_requires_matching_explicit_source(self):
        source = self.root / "maintained"
        self.skill(source, "code-skill", "new")
        self.skill(self.official, "code-skill", "new")
        legacy = self.skill(self.legacy, "code-skill", "old")
        kwargs = {"apply": True, "source_dir": source, "authoritative_names": ["code-skill"]}
        (self.official / "code-skill" / "SKILL.md").write_text("unrelated change", encoding="utf-8")
        self.assertEqual(REPAIR.repair_user_skill_root(**kwargs)["status"], "pending")
        self.assertTrue(legacy.exists())
        (self.official / "code-skill" / "SKILL.md").write_text("new", encoding="utf-8")
        result = REPAIR.repair_user_skill_root(**kwargs)
        self.assertEqual(result["status"], "repaired")
        self.assertEqual(result["entries"][0]["action"], "retire_superseded")
        self.assertEqual((Path(result["entries"][0]["backup"]) / "copy" / "SKILL.md").read_text(encoding="utf-8"), "old")

    def test_read_or_copy_permission_failure_is_pending_without_retirement(self):
        source = self.skill(self.legacy)
        scandir = os.scandir

        def deny_legacy_read(path):
            if isinstance(path, (str, os.PathLike)) and Path(path) == self.legacy:
                raise PermissionError("access denied")
            return scandir(path)

        with mock.patch.object(REPAIR.os, "scandir", side_effect=deny_legacy_read):
            result = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(result["status"], "pending")
        with mock.patch.object(REPAIR.shutil, "copytree", side_effect=PermissionError("copy denied")):
            result = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(Path(result["entries"][0]["backup"]).is_dir())
        self.assertIn("staged_backup", result["entries"][0])
        self.assertTrue(source.exists())
        self.assertFalse((self.official / source.name).exists())

    def test_retirement_permission_failure_retains_original_and_can_retry(self):
        source = self.skill(self.legacy)
        rename = os.rename

        def deny_retirement(original, target):
            if Path(original) == source:
                raise PermissionError("retirement denied")
            return rename(original, target)

        with mock.patch.object(REPAIR.os, "rename", side_effect=deny_retirement):
            first = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(first["status"], "pending")
        self.assertIn("retirement_target", first["entries"][0])
        self.assertEqual(REPAIR.tree_manifest(source), REPAIR.tree_manifest(self.official / source.name))
        backups = sorted(self.backups.iterdir())
        second = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(second["status"], "repaired")
        self.assertEqual(sorted(self.backups.iterdir()), backups)
        self.assertFalse(source.exists())

    def test_content_and_root_links_are_pending_without_touching_external_files(self):
        source = self.skill(self.legacy)
        external = self.root / "external"
        external.mkdir()
        (external / "private.txt").write_bytes(b"private")
        try:
            (source / "linked").symlink_to(external, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create test symlinks: {error}")
        self.assertEqual(REPAIR.repair_user_skill_root(apply=True)["status"], "pending")
        self.assertFalse(self.backups.exists())
        linked_root = self.root / "linked-root"
        linked_root.symlink_to(self.legacy, target_is_directory=True)
        self.assertEqual(REPAIR.repair_user_skill_root(legacy_root=linked_root, apply=True)["status"], "pending")
        self.official.symlink_to(external, target_is_directory=True)
        self.assertEqual(REPAIR.repair_user_skill_root(apply=True)["status"], "pending")
        self.assertEqual((external / "private.txt").read_bytes(), b"private")
        self.assertTrue(source.exists())

    def test_nested_roots_are_rejected_before_writes(self):
        source = self.skill(self.legacy)
        result = REPAIR.repair_user_skill_root(official_root=self.legacy / "nested", apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertFalse((self.legacy / "nested").exists())
        self.assertTrue(source.exists())

    def test_sibling_explicit_roots_share_one_installation_lock(self):
        legacy, official = self.root / "old-skills", self.root / "new-skills"
        source = self.skill(legacy)
        result = REPAIR.repair_user_skill_root(legacy_root=legacy, official_root=official, apply=True)
        self.assertEqual(result["status"], "repaired")
        self.assertFalse(source.exists())
        self.assertTrue((official / source.name / "SKILL.md").is_file())

    def test_authoritative_source_link_is_refused_without_following_it(self):
        maintained = self.root / "maintained"
        source = self.skill(maintained, "code-skill", "new")
        self.skill(self.official, "code-skill", "new")
        legacy = self.skill(self.legacy, "code-skill", "old")
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (source / "external").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create test symlinks: {error}")
        result = REPAIR.repair_user_skill_root(apply=True, source_dir=maintained, authoritative_names=["code-skill"])
        self.assertEqual(result["status"], "pending")
        self.assertTrue(legacy.exists())
        self.assertFalse(self.backups.exists())

    def test_corrupt_backup_is_pending_before_installing_or_retiring(self):
        source = self.skill(self.legacy)
        copytree = REPAIR.shutil.copytree

        def corrupt_copy(original, target, *args, **kwargs):
            result = copytree(original, target, *args, **kwargs)
            if Path(original) == source:
                (Path(target) / "SKILL.md").write_text("corrupt", encoding="utf-8")
            return result

        with mock.patch.object(REPAIR.shutil, "copytree", side_effect=corrupt_copy):
            result = REPAIR.repair_user_skill_root(apply=True)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(source.exists())
        self.assertFalse((self.official / source.name).exists())
        self.assertTrue(Path(result["entries"][0]["staged_backup"]).is_dir())

    def test_project_cli_keeps_skills_in_project_and_backups_outside_it(self):
        project = self.root / "project"
        source = self.skill(project / ".codex" / "skills")
        global_source = self.skill(self.legacy, "global-skill")
        with mock.patch("builtins.print") as printer:
            self.assertEqual(REPAIR.main(["apply", "--project-root", str(project)]), 0)
        result = json.loads(printer.call_args.args[0])
        self.assertFalse(source.exists())
        self.assertTrue((project / ".agents" / "skills" / source.name / "SKILL.md").is_file())
        self.assertFalse(self.official.exists())
        self.assertTrue(global_source.exists())
        self.assertTrue(Path(result["backup_root"]).is_relative_to(self.backups))
        self.assertFalse(Path(result["backup_root"]).is_relative_to(project))

    def test_default_deploy_uses_installed_helper_but_custom_target_skips_repair(self):
        repository = Path(__file__).resolve().parents[2]
        legacy = self.skill(self.legacy, "code-skill", "old")
        with mock.patch.object(INSTALLER, "OFFICIAL_USER_SKILLS_DIRECTORY", self.official), mock.patch("builtins.print"):
            INSTALLER.deploy(repository, self.official)
        self.assertFalse(legacy.exists())
        self.assertTrue((self.official / "management-skill" / "scripts" / "repair_user_skill_root.py").is_file())
        saved = next(self.backups.glob("code-skill-*/copy/SKILL.md"))
        self.assertEqual(saved.read_text(encoding="utf-8"), "old")
        self.skill(self.legacy, "code-skill", "new legacy data")
        with mock.patch.object(INSTALLER, "repair_legacy_user_skills", side_effect=AssertionError("custom targets must not inspect the user legacy root")), mock.patch("builtins.print"):
            INSTALLER.deploy(repository, self.root / "isolated" / "skills")
        self.assertEqual((legacy / "SKILL.md").read_text(encoding="utf-8"), "new legacy data")

    def test_default_deploy_rejects_linked_ancestor_before_any_external_write(self):
        repository = Path(__file__).resolve().parents[2]
        outside = self.root / "outside"
        previous = self.skill(outside / "skills", "code-skill", "outside original")
        self.home.mkdir(parents=True)
        try:
            (self.home / ".agents").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create test symlinks: {error}")
        with mock.patch.object(INSTALLER, "OFFICIAL_USER_SKILLS_DIRECTORY", self.official):
            with self.assertRaisesRegex(RuntimeError, "cannot traverse"):
                INSTALLER.deploy(repository, self.official)
        self.assertEqual((previous / "SKILL.md").read_text(encoding="utf-8"), "outside original")
        self.assertEqual(sorted(path.name for path in outside.iterdir()), ["skills"])
        self.assertFalse((outside / "skills" / "management-skill").exists())


if __name__ == "__main__":
    unittest.main()

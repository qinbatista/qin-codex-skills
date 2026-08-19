#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_alias_install.py"
INSTALLER_SPEC = importlib.util.spec_from_file_location("skill_alias_install", INSTALLER_PATH)
INSTALLER = importlib.util.module_from_spec(INSTALLER_SPEC)
INSTALLER_SPEC.loader.exec_module(INSTALLER)

RESOLVER_PATH = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "skill_resolver.py"
RESOLVER_SPEC = importlib.util.spec_from_file_location("skill_alias_resolver", RESOLVER_PATH)
RESOLVER = importlib.util.module_from_spec(RESOLVER_SPEC)
RESOLVER_SPEC.loader.exec_module(RESOLVER)


class SkillAliasInstallTests(unittest.TestCase):
    @staticmethod
    def create_skill(root, name="verify-skill", content="version one"):
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(content, encoding="utf-8")
        return skill

    def test_install_is_idempotent_and_compatible_discovery_follows_canonical_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical_root = root / "codex" / "skills"
            agents_root = root / "agents" / "skills"
            canonical = self.create_skill(canonical_root)
            first = INSTALLER.apply_aliases("install", canonical_root, agents_root)
            second = INSTALLER.apply_aliases("upgrade", canonical_root, agents_root)
            discovered = RESOLVER.resolve_compatible_skill_path("verify-skill", canonical_root, agents_root)
            (canonical / "SKILL.md").write_text("version two", encoding="utf-8")
            alias_content = (agents_root / "verify-skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(first["results"], [{"skill": "verify-skill", "action": "linked"}])
        self.assertEqual(second["results"], [{"skill": "verify-skill", "action": "unchanged"}])
        self.assertEqual(discovered, (canonical / "SKILL.md").resolve())
        self.assertEqual(alias_content, "version two")

    def test_install_and_uninstall_refuse_to_overwrite_or_remove_user_owned_skills(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical_root = root / "codex" / "skills"
            agents_root = root / "agents" / "skills"
            self.create_skill(canonical_root)
            user_skill = self.create_skill(agents_root, content="user owned")
            with self.assertRaisesRegex(INSTALLER.SkillAliasError, "overwrite user Skill"):
                INSTALLER.apply_aliases("install", canonical_root, agents_root)
            with self.assertRaisesRegex(INSTALLER.SkillAliasError, "remove a user-owned Skill"):
                INSTALLER.apply_aliases("uninstall", canonical_root, agents_root)
            user_content = (user_skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(user_content, "user owned")

    def test_uninstall_removes_only_the_managed_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical_root = root / "codex" / "skills"
            agents_root = root / "agents" / "skills"
            canonical = self.create_skill(canonical_root)
            INSTALLER.apply_aliases("install", canonical_root, agents_root)
            result = INSTALLER.apply_aliases("uninstall", canonical_root, agents_root)
            canonical_exists = canonical.is_dir()
            alias_exists = (agents_root / "verify-skill").exists()
        self.assertEqual(result["results"], [{"skill": "verify-skill", "action": "unlinked"}])
        self.assertTrue(canonical_exists)
        self.assertFalse(alias_exists)


if __name__ == "__main__":
    unittest.main()

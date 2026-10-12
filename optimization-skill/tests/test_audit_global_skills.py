import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("audit_global_skills", MODULE_PATH)
audit_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(audit_global_skills)


class AuditGlobalSkillsTest(unittest.TestCase):
    def write_skill(self, skills_root, name, body):
        skill_dir = skills_root / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use for regression tests.\n---\n# Skill\n{body}\n", encoding="utf-8")
        return skill_dir

    def test_split_frontmatter_accepts_literal_and_folded_block_scalars(self):
        literal_metadata, _, literal_errors = audit_global_skills.split_frontmatter("---\nname: chronicle\ndescription: |\n  Use when a screen history is needed.\n\n  Keep the second paragraph.\n---\n# Chronicle\n")
        folded_metadata, _, folded_errors = audit_global_skills.split_frontmatter("---\nname: folded\ndescription: >\n  Use when folded text\n  needs one line.\n---\n# Folded\n")

        self.assertEqual(literal_errors, [])
        self.assertEqual(literal_metadata["description"], "Use when a screen history is needed.\n\nKeep the second paragraph.")
        self.assertEqual(folded_errors, [])
        self.assertEqual(folded_metadata["description"], "Use when folded text needs one line.")

    def test_cross_skill_command_path_resolves_from_global_skills_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            checked_skill = self.write_skill(skills_root, "checked-skill", "Run `verify-skill/scripts/ending_task_ledger.py` after delivery.")
            ending_ledger = skills_root / "verify-skill" / "scripts" / "ending_task_ledger.py"
            ending_ledger.parent.mkdir(parents=True)
            ending_ledger.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)

        self.assertNotIn("missing command/reference path: verify-skill/scripts/ending_task_ledger.py", audit_result["errors"])

    def test_missing_cross_skill_command_path_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            checked_skill = self.write_skill(skills_root, "checked-skill", "Run `verify-skill/scripts/missing_ending_ledger.py` after delivery.")
            (skills_root / "verify-skill").mkdir()

            audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)

        self.assertIn("missing command/reference path: verify-skill/scripts/missing_ending_ledger.py", audit_result["errors"])

    def test_clean_host_audit_does_not_require_documented_installation_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            home = skills_root / "empty-home"
            home.mkdir()
            checked_skill = self.write_skill(skills_root, "checked-skill", "Install in `~/.agents/skills` or `~/.agents/skills/`; configuration lives in `~/.codex`. Read [installation root](~/.agents/skills) and [rules](references/rules.md).")
            reference = checked_skill / "references" / "rules.md"
            reference.parent.mkdir()
            reference.write_text("Keep declared owners.\n", encoding="utf-8")
            with mock.patch.object(Path, "expanduser", autospec=True, side_effect=lambda path: home.joinpath(*path.parts[1:]) if path.parts[:1] == ("~",) else path):
                audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)
            self.assertEqual([], audit_result["errors"])
            self.assertEqual([], list(home.iterdir()))

    def test_missing_helpers_below_documented_install_roots_are_still_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            home = skills_root / "empty-home"
            home.mkdir()
            checked_skill = self.write_skill(skills_root, "checked-skill", "Run `~/.agents/skills/check.py` and `~/.codex/setup.py` after installation.")
            with mock.patch.object(Path, "expanduser", autospec=True, side_effect=lambda path: home.joinpath(*path.parts[1:]) if path.parts[:1] == ("~",) else path):
                audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)
            self.assertEqual(["missing command/reference path: ~/.agents/skills/check.py", "missing command/reference path: ~/.codex/setup.py"], audit_result["errors"])
            self.assertEqual([], list(home.iterdir()))

    def test_markdown_link_followed_by_punctuation_is_a_real_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            checked_skill = self.write_skill(skills_root, "checked-skill", "Read [rules](references/rules.md); preserve the contract.")
            reference = checked_skill / "references" / "rules.md"
            reference.parent.mkdir()
            reference.write_text("Keep one rule per behavior.\n", encoding="utf-8")
            audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)
        self.assertEqual([], audit_result["errors"])

    def test_compact_skill_does_not_require_routing_or_placement_sections(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            checked_skill = self.write_skill(skills_root, "checked-skill", "Keep one owner and check the changed behavior.")
            audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)
        self.assertEqual([], audit_result["warnings"])

    def test_prose_slash_list_with_trailing_punctuation_is_not_a_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            skills_root = Path(temporary_directory)
            checked_skill = self.write_skill(skills_root, "checked-skill", "Keep scripts/results/fixtures, logs, and receipts under Cache.")
            audit_result = audit_global_skills.audit_skill(checked_skill, skills_root)

        self.assertNotIn("missing command/reference path: scripts/results/fixtures,", audit_result["errors"])

    def test_command_paths_preserve_absolute_skill_paths_without_hyphen_suffixes(self):
        text = "Use `~/.codex/skills/code-skill/scripts/code_rule_guard.py` and `~/.codex/skills/project-memory-skill/scripts/project_change_memory.py`; leave https://example.test//not-a-local-path alone."
        command_paths = audit_global_skills.command_paths(text)

        self.assertIn("~/.codex/skills/code-skill/scripts/code_rule_guard.py", command_paths)
        self.assertIn("~/.codex/skills/project-memory-skill/scripts/project_change_memory.py", command_paths)
        self.assertNotIn("skill/scripts/code_rule_guard.py", command_paths)
        self.assertNotIn("memory-skill/scripts/project_change_memory.py", command_paths)
        self.assertNotIn("//not-a-local-path", command_paths)

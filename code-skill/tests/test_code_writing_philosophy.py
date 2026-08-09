import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CODE_SKILL_PATH = REPOSITORY_ROOT / "code-skill" / "SKILL.md"
PHILOSOPHY_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "code-writing-philosophy.md"
CODING_APPROACH_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "coding-approach.md"
AGENT_METADATA_PATH = REPOSITORY_ROOT / "code-skill" / "agents" / "openai.yaml"


class CodeWritingPhilosophyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code_skill = CODE_SKILL_PATH.read_text(encoding="utf-8")
        cls.philosophy = PHILOSOPHY_PATH.read_text(encoding="utf-8")
        cls.coding_approach = CODING_APPROACH_PATH.read_text(encoding="utf-8")
        cls.agent_metadata = AGENT_METADATA_PATH.read_text(encoding="utf-8")

    def test_triggering_covers_all_code_writing_and_excludes_exact_read_only(self):
        self.assertTrue(self.code_skill.startswith("---\nname: code-skill\ndescription:"))
        self.assertIn("every code creation, repair, feature, refactor, or test-writing node, including a small edit", self.code_skill)
        self.assertIn("in any programming language", self.code_skill)
        self.assertIn("another domain Skill owns implementation", self.code_skill)
        self.assertIn("exact-scoped read-only lookup stays outside this gate", self.code_skill)
        self.assertIn("references/code-writing-philosophy.md", self.agent_metadata)

    def test_all_four_process_stages_remain_required(self):
        for stage in ["## 1. Establish the current contract", "## 2. Classify ownership and overlap", "## 3. Write the minimum coherent change", "## 4. Check lifecycle and continuity"]:
            self.assertIn(stage, self.philosophy)
        for requirement in ["nearest project `AGENTS.md`", "existing code", "minimum coherent change", "bounded memory use", "resource cleanup", "concurrency/event subscriptions", "long-running behavior"]:
            self.assertIn(requirement, self.philosophy)

    def test_agents_boundary_and_process_memory_separation_remain_explicit(self):
        self.assertIn("Keep it free of this full philosophy, task history, results, logs, and speculative architecture", self.philosophy)
        self.assertIn("project-memory-skill` records sanitized, verified outcomes only after independent Ending PASS", self.philosophy)
        self.assertIn("Neither substitutes for the other", self.philosophy)
        self.assertIn("compact observed-evidence contract", self.philosophy)
        self.assertIn("stable structure/ownership/entry points/constraints/definition-of-done guidance", self.philosophy)

    def test_coding_approach_extends_instead_of_competing_with_the_process(self):
        self.assertIn("mandatory before/during-writing process authority", self.coding_approach)
        self.assertIn("does not duplicate or replace its four process stages", self.coding_approach)


if __name__ == "__main__":
    unittest.main()

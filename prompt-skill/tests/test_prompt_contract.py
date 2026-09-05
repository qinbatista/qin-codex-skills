"""Test prompt policy boundaries without freezing every explanatory sentence."""

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class PromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        cls.code_reference = (SKILL_ROOT.parent / "code-skill" / "references" / "prompt-generation.md").read_text(encoding="utf-8")

    def test_trigger_model_and_optional_project_memory(self):
        for concept in ("reusable prompts", "durable AI instructions", "Ordinary prose does not trigger", "user's selected model and effort", "delegated prompt work", "every task", "skip it when unavailable", "project facts scoped to that project"):
            self.assertIn(concept, self.skill)

    def test_prompt_defines_only_material_controls(self):
        for concept in ("objective", "inputs and their roles", "output contract", "success/failure criteria", "missing-value behavior", "one authoritative rule", "resolve contradictions", "only when they change the result", "Examples illustrate", "private chain-of-thought"):
            self.assertIn(concept, self.skill)

    def test_verification_is_proportional_and_in_active_task(self):
        for concept in ("Verify within this active task", "semantic correctness", "simple value-only", "skip verification", "Do not start the whole project", "Ending only summarizes", "no verification or repair", "one good sample does not prove stability"):
            self.assertIn(concept, self.skill)

    def test_retired_route_and_ending_verifier_contracts_are_absent(self):
        for document in (self.skill, self.metadata, self.code_reference):
            for retired in ("CODE READY", "Spark-xhigh", "Quick Check", "global projectless Ending", "prompt-task routing failure", "all checks PASS"):
                self.assertNotIn(retired, document)

    def test_spelling_and_input_authority_preserve_external_data(self):
        for concept in ("unambiguous spelling", "original-to-canonical mapping", "quoted user prose", "external names", "persisted/public contracts", "Current instructions and fresh source"):
            self.assertIn(concept, self.skill)

    def test_format_semantics_and_code_interpolation_are_separate(self):
        for concept in ("Schema", "allowed missing values", "cross-field consistency", "Each reference's role", "checkerboard is not alpha", "sprite-specific restrictions"):
            self.assertIn(concept, self.skill)
        for concept in ("{{", "}}", "{source_text}", "actual language version", "active task", "Do not defer validation to Ending"):
            self.assertIn(concept, self.code_reference)

    def test_entry_and_metadata_are_compact_with_resolvable_links(self):
        self.assertLess(len(self.skill.split()), 650)
        self.assertLess(len(self.metadata), 750)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", self.skill):
            with self.subTest(target=target):
                self.assertTrue((SKILL_ROOT / target).exists())


if __name__ == "__main__":
    unittest.main()

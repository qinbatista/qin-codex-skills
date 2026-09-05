"""Protect durable preferences and reject retired workflow requirements."""

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class CodeWritingPhilosophyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {str(path.relative_to(SKILL_ROOT)): path.read_text(encoding="utf-8") for path in [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md")), SKILL_ROOT / "agents" / "openai.yaml"]}

    def assert_concepts(self, relative_path, concepts):
        document = self.documents[relative_path].casefold()
        for concept in concepts:
            with self.subTest(file=relative_path, concept=concept):
                self.assertIn(concept.casefold(), document)

    def test_skill_governed_work_keeps_selected_model_and_optional_scoped_memory(self):
        self.assert_concepts("SKILL.md", ["user's selected model and effort", "including a delegated subtask", "every task", "if no memory is available, continue", "another project's", "mechanical shell command"])

    def test_checking_stays_in_task_and_memory_closeout_is_separate(self):
        self.assert_concepts("SKILL.md", ["Verify meaningful behavior in this active task", "simple value-only", "Ending only summarizes", "does not verify or repair", "Do not start the whole project", "unless the user requests it", "remaining limitations"])

    def test_instructions_no_longer_require_route_or_ending_ritual(self):
        retired = ("Code Gate", "CODE READY", "Spark-xhigh", "ENDING_CHECK_WORKER", "LOCKED_ROUTE_NODE", "detached Ending", "exactly one producer-side Quick Check", "independent Ending PASS")
        for relative_path, content in self.documents.items():
            for phrase in retired:
                with self.subTest(file=relative_path, phrase=phrase):
                    self.assertNotIn(phrase, content)

    def test_direct_code_and_lifecycle_preferences_survive(self):
        self.assert_concepts("references/code-writing-philosophy.md", ["nearest project `AGENTS.md`", "same-project memory", "existing code", "same arguments and return value", "Do not assign or unpack into `_`", "_ = SomeTask()", "case _", "one physical line", "bounded memory use", "resource cleanup", "concurrency/event subscriptions", "long-running behavior"])

    def test_naming_preserves_real_contract_boundaries(self):
        self.assert_concepts("references/code-writing-philosophy.md", ["Correct unambiguous English spelling", "external/public/persisted", "declarations and direct references", "original-to-canonical mapping", "quoted user data", "third-party names"])

    def test_ui_geometry_feedback_accessibility_and_rendered_proof_survive(self):
        self.assert_concepts("references/coding-approach.md", ["../../workflow-skill/references/readable-ui.md", "without code changes", "another project's design"])
        document = (SKILL_ROOT.parent / "workflow-skill/references/readable-ui.md").read_text().casefold()
        for concept in ("outer edges", "gutters", "one row", "long text", "one visual boundary", "loading", "real application state", "accessibility", "Immediately acknowledge", "queued, in-progress, completed, and failed", "accessible text", "rendered checks"):
            with self.subTest(concept=concept):
                self.assertIn(concept.casefold(), document)

    def test_unity_style_and_applicability_are_explicit(self):
        self.assert_concepts("references/unity-csharp-rules.md", ["other C# work uses its actual runtime", "unity_csharp", "one physical line", "single-statement", "explicit concrete type", "`private`", "underscore names", "`internal` access modifier", "case _:", "unless requested"])

    def test_unity_structure_is_general_and_keeps_data_exceptions(self):
        self.assert_concepts("references/unity-game-code-structure-design.md", ["not feature recipes", "do not apply to Editor", "XXController", "XXManager", "single-instance", "operate autonomously", "serializes ScriptableObject references only", "Transient runtime state", "Immutable constants", "canonical ScriptableObject location", "Factory", "Object Pool", "State", "Command", "Observer", "Prototype", "Singleton"])
        for consumer_name in ("SpriteTamerSystem", "SpriteMovementState", "DamageNumberManager", "CombatService"):
            self.assertNotIn(consumer_name, self.documents["references/unity-game-code-structure-design.md"])

    def test_optional_unity_categories_preserve_lifecycle_and_provider_ownership(self):
        self.assert_concepts("references/unity-lifecycle-and-serialization.md", ["symmetric pair", "named field", "Unity main thread", "serialized field compatibility", "Do not repeat `GetComponent`"])
        self.assert_concepts("references/unity-service-integration.md", ["optional or interchangeable", "neutral contract", "Do not manufacture", "Forward each callback or operation once", "uninitialized, initializing, ready, and failed", "exact surface has fresh evidence"])

    def test_python_is_concise_without_exporting_a_project_logger(self):
        self.assert_concepts("references/python-rules.md", ["manual formatting", "formatter unless requested", "match", "Python 3.10+", "untrusted inputs", "When the project has this logger", "Do not add this project logger to unrelated projects"])

    def test_references_resolve_and_entry_is_compact(self):
        for relative_path, content in self.documents.items():
            if not relative_path.endswith(".md"):
                continue
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if "://" in target:
                    continue
                with self.subTest(file=relative_path, target=target):
                    self.assertTrue(((SKILL_ROOT / relative_path).parent / target.split("#", 1)[0]).exists())
        self.assertLess(len(self.documents["SKILL.md"].split()), 850)


if __name__ == "__main__":
    unittest.main()

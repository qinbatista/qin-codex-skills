import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CODE_SKILL_PATH = REPOSITORY_ROOT / "code-skill" / "SKILL.md"
PHILOSOPHY_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "code-writing-philosophy.md"
CODING_APPROACH_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "coding-approach.md"
AGENT_METADATA_PATH = REPOSITORY_ROOT / "code-skill" / "agents" / "openai.yaml"
UNITY_RULES_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-csharp-rules.md"
UNITY_STRUCTURE_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-game-code-structure-design.md"


class CodeWritingPhilosophyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code_skill = CODE_SKILL_PATH.read_text(encoding="utf-8")
        cls.philosophy = PHILOSOPHY_PATH.read_text(encoding="utf-8")
        cls.coding_approach = CODING_APPROACH_PATH.read_text(encoding="utf-8")
        cls.agent_metadata = AGENT_METADATA_PATH.read_text(encoding="utf-8")
        cls.unity_rules = UNITY_RULES_PATH.read_text(encoding="utf-8")
        cls.unity_structure = UNITY_STRUCTURE_PATH.read_text(encoding="utf-8")

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

    def test_automatic_spelling_correction_is_canonical_and_boundary_safe(self):
        for required_fragment in [
            "## Automatic spelling correction at naming boundaries",
            "every unambiguous English spelling error",
            "not an allow-list of examples",
            "misspelled English word or technical name",
            "Oraganization",
            "Organization",
            "documentation",
            "search declarations and direct references first",
            "update every internal use to the canonical spelling",
            "external API, public, persisted, serialized, or third-party boundary",
            "Do not silently rewrite user data or third-party names",
            "finish with a factual mapping",
        ]:
            self.assertIn(required_fragment, self.coding_approach)

    def test_user_experience_philosophy_requires_immediate_honest_feedback_and_visual_aids(self):
        self.assertIn("## User Experience Philosophy", self.coding_approach)
        for requirement in [
            "immediately acknowledge a user action",
            "Move non-blocking work to the background when appropriate",
            "Never present an unfinished operation as complete",
            "queued, in-progress, completed, and failed work",
            "prefer the smallest useful visual aid",
            "icon, emoji, image, status treatment, or diagram",
            "must not be the only way to understand it",
        ]:
            self.assertIn(requirement, self.coding_approach)
        self.assertIn("user-facing UI information", self.code_skill)
        self.assertIn("User Experience Philosophy", self.code_skill)

    def test_unity_game_nodes_must_load_the_structure_reference_before_pattern_selection(self):
        self.assertIn("references/unity-game-code-structure-design.md", self.code_skill)
        self.assertIn("unity-game-code-structure-design.md", self.unity_rules)
        self.assertIn("references/unity-game-code-structure-design.md", self.agent_metadata)
        self.assertIn("Every Unity game C# writing node must also load", self.code_skill)
        self.assertIn("nearest project `AGENTS.md`", self.unity_structure)
        self.assertIn("Patterns solve a demonstrated lifecycle or coordination need", self.unity_rules)

    def test_unity_constructor_and_collection_entries_stay_flat(self):
        for required_fragment in [
            "constructor calls and object-creation expressions on one physical line",
            "each `new Type(...)` entry flat",
            "vertically stacked arguments",
            "new InAppPurchaseProduct(ProductId.Coin500.ToString(), \"coins_500_ios\", \"coins_500_android\", 500, 3.99m, \"USD\", InAppPurchaseProductKind.Consumable),",
        ]:
            self.assertIn(required_fragment, self.unity_rules)
        self.assertNotIn("new InAppPurchaseProduct(\n", self.unity_rules)

    def test_unity_code_that_fits_stays_on_one_line(self):
        required_fragments = ["every self-contained Unity C# statement or expression that fits clearly on one physical line", "declarations, assignments, returns, conditions, calls, logs, constructors, object creation, initializer entries, and ternary expressions", "Do not vertically wrap code that fits", "split a ternary assignment only to indent its branches", "wrap only when it cannot fit without harming readability, correctness, or tooling"]
        for required_fragment in required_fragments:
            self.assertIn(required_fragment, self.unity_rules)
            self.assertIn(required_fragment, self.code_skill)
        self.assertIn("every self-contained Unity C# statement/expression that fits clearly on one physical line", self.agent_metadata)
        self.assertIn("do not vertically wrap code that fits or split a ternary assignment only to indent its branches unless required or requested", self.agent_metadata)

    def test_agent_metadata_preserves_prior_lifecycle_routing_and_unity_requirements(self):
        required = [
            "$code-skill: artifact-free exact read-only lookup/audit stays skill-free",
            "references/code-writing-philosophy.md",
            "references/unity-game-code-structure-design.md",
            "relevant language/platform/domain Skills",
            "Controller/Manager/ScriptableObject core",
            "exactly one smallest local Quick Check",
            "publish CODE READY",
            "broad tests/builds/UI/full lint/log cleanup/repeated review move to Ending",
            "Code normally exposes real_test through Quick Check and emits ending-required",
            "ending_verification_plan.py",
            "projectless End Task",
            "gpt-5.3-codex-spark|xhigh",
            "gpt-5.6-luna|low",
            "ENDING_CHECK_WORKER",
            "never edit/repair/route/lifecycle",
            "All checks PASS",
            "codex_app__send_message_to_thread",
            "immutable origin",
            "fresh Spark-first Ending",
            "Never self-verify",
        ]
        for fragment in required:
            self.assertIn(fragment, self.agent_metadata)

    def test_unity_reference_frontmatter_boundary_and_preselection_negatives_remain_first(self):
        frontmatter = CODE_SKILL_PATH.read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("name: code-skill", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("Do not apply this reference to non-game Unity tooling", self.unity_structure)
        self.assertLess(self.unity_structure.index("Do not apply this reference to non-game Unity tooling"), self.unity_structure.index("## Ownership and lifecycle"))
        self.assertLess(self.unity_structure.index("## Ownership and lifecycle"), self.unity_structure.index("## Pattern decisions, not ceremony"))

    def test_unity_structure_contract_covers_ownership_data_exceptions_and_patterns(self):
        for requirement in ["only gameplay runtime-behavior roles", "`XXController`", "single-instance `XXManager`", "A Manager serializes ScriptableObject references only", "Controller may serialize only", "existing canonical ScriptableObject location", "hidden mutable globals", "runtime observations", "cached component references", "IDs and handles", "Factory", "Object Pool", "State", "Command", "Observer", "Prototype", "Singleton"]:
            self.assertIn(requirement, self.unity_structure)

    def test_global_core_cannot_be_weakened_by_project_defaults(self):
        self.assertIn("cannot silently weaken the Controller/Manager/ScriptableObject core", self.unity_structure)
        self.assertIn("deleting that reiteration later does not disable this global gate", self.unity_structure)
        self.assertIn("result memory never replaces this process gate", self.unity_structure)
        self.assertIn("may refine paths, bootstrap, naming, and stricter constraints", self.unity_structure)

    def test_project_agents_companion_is_compact_by_design(self):
        self.assertIn("## Conflict precedence and explicit exceptions", self.unity_structure)
        self.assertIn("project `AGENTS.md` may carry a compact reiteration", self.unity_structure)
        self.assertIn("A scoped exception must name its owner and why it is necessary", self.unity_structure)
        self.assertIn("Do not turn `AGENTS.md` into a task log", self.unity_structure)

    def test_five_disposable_trials_are_structurally_checkable(self):
        disposable_trials = {"controller-local-owner": "repeatable, GameObject-bound local behavior belongs to an `XXController`", "manager-lifecycle-owner": "one single-instance `XXManager`", "scriptableobject-tuning-boundary": "Every Manager functional or tunable parameter", "negative-third-runtime-role": "Negative — a `CombatService` MonoBehaviour", "negative-pattern-ceremony": "Negative — wrapping a single immediate method call"}
        self.assertEqual(len(disposable_trials), 5)
        for required_fragment in disposable_trials.values():
            self.assertIn(required_fragment, self.unity_structure)


if __name__ == "__main__":
    unittest.main()

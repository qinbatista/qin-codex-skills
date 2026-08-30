import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CODE_SKILL_PATH = REPOSITORY_ROOT / "code-skill" / "SKILL.md"
PHILOSOPHY_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "code-writing-philosophy.md"
CODING_APPROACH_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "coding-approach.md"
AGENT_METADATA_PATH = REPOSITORY_ROOT / "code-skill" / "agents" / "openai.yaml"
UNITY_RULES_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-csharp-rules.md"
UNITY_STRUCTURE_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-game-code-structure-design.md"
UNITY_LIFECYCLE_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-lifecycle-and-serialization.md"
UNITY_SERVICE_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "unity-service-integration.md"
CSHARP_HISTORY_PATH = REPOSITORY_ROOT / "code-skill" / "references" / "csharp-rules.md"


class CodeWritingPhilosophyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code_skill = CODE_SKILL_PATH.read_text(encoding="utf-8")
        cls.philosophy = PHILOSOPHY_PATH.read_text(encoding="utf-8")
        cls.coding_approach = CODING_APPROACH_PATH.read_text(encoding="utf-8")
        cls.agent_metadata = AGENT_METADATA_PATH.read_text(encoding="utf-8")
        cls.unity_rules = UNITY_RULES_PATH.read_text(encoding="utf-8")
        cls.unity_structure = UNITY_STRUCTURE_PATH.read_text(encoding="utf-8")
        cls.unity_lifecycle = UNITY_LIFECYCLE_PATH.read_text(encoding="utf-8")
        cls.unity_service = UNITY_SERVICE_PATH.read_text(encoding="utf-8")
        cls.csharp_history = CSHARP_HISTORY_PATH.read_text(encoding="utf-8")

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

    def test_code_gate_is_visible_and_universal_before_source_work(self):
        for required_fragment in ["emit one visible `Code Gate` notice", "Before reading or editing task source", "universal philosophy", "active language profile", "matched optional categories", "missing disclosure or a missing universal reference is a routing failure"]:
            self.assertIn(required_fragment, self.code_skill)
        self.assertIn("before source work emit Code Gate", self.agent_metadata)

    def test_direct_result_ownership_and_no_wrapper_rules_are_universal(self):
        for required_fragment in ["Do not assign or unpack into `_`", "never use `_ = SomeTask()`", "Call the real owner directly", "SaveData() { SaveData(); }", "same arguments and return value", "one physical line"]:
            self.assertIn(required_fragment, self.philosophy)
        for required_fragment in ["_ = SaveDataAsync();", "same arguments and return value", "void SaveData() { SaveData(); }", "explicit concrete type instead of `var`", "case _:"]:
            self.assertIn(required_fragment, self.unity_rules)
        for required_fragment in ["scripts/code_rule_guard.py --diff-from HEAD", "ignoring unchanged legacy lines", "detached Ending or authorized release gate", "does not replace them"]:
            self.assertIn(required_fragment, self.code_skill)

    def test_csharp_has_one_active_unity_profile_with_conditional_categories(self):
        self.assertIn("C# and Unity C# | `unity_csharp`", self.code_skill)
        self.assertIn("Historical plain C# | `csharp`", self.code_skill)
        self.assertIn("history-only", self.csharp_history)
        self.assertIn("must not create a second rule path", self.unity_rules)
        self.assertIn("may add only their domain facts and APIs", self.unity_rules)
        self.assertIn("must not duplicate, fork, or compete", self.unity_rules)
        for reference in ["unity-game-code-structure-design.md", "unity-lifecycle-and-serialization.md", "unity-service-integration.md"]:
            self.assertIn(reference, self.unity_rules)
            self.assertIn(reference, self.code_skill)

    def test_unity_structure_category_loads_before_pattern_selection(self):
        self.assertIn("materially changes gameplay ownership", self.unity_structure)
        self.assertIn("nearest project `AGENTS.md`", self.unity_structure)
        self.assertIn("Patterns solve a demonstrated lifecycle or coordination need", self.unity_rules)

    def test_unity_lifecycle_category_covers_callback_async_and_serialization_pits(self):
        for required_fragment in ["`OnEnable()` and `OnDisable()` as a symmetric pair", "Do not write `_ = SomeTask()`", "named field", "Unity main thread", "[SerializeField] private ConcreteType _field;", "Do not rely on accidental script execution order", "Do not repeat `GetComponent`"]:
            self.assertIn(required_fragment, self.unity_lifecycle)

    def test_unity_service_category_keeps_one_real_provider_boundary(self):
        for required_fragment in ["public facade -> neutral interface -> selected provider -> optional SDK", "same arguments and return value", "uninitialized, initializing, ready, and failed", "Forward each callback or operation once", "thin test UI", "Claim editor, device, cloud"]:
            self.assertIn(required_fragment, self.unity_service)

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
        self.assertIn("keep complete clear code on one line", self.agent_metadata)

    def test_agent_metadata_preserves_code_gate_quick_check_and_ending_boundaries(self):
        required = [
            "$code-skill: exact artifact-free read-only work stays outside",
            "before source work emit Code Gate",
            "references/code-writing-philosophy.md",
            "New C# always routes to unity_csharp",
            "Never hide results or Tasks in _",
            "same-argument pass-through wrappers",
            "accidental self-recursion",
            "Run one smallest Quick Check",
            "publish CODE READY",
            "global projectless Ending",
        ]
        for fragment in required:
            self.assertIn(fragment, self.agent_metadata)

    def test_unity_reference_frontmatter_boundary_and_preselection_negatives_remain_first(self):
        frontmatter = CODE_SKILL_PATH.read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("name: code-skill", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("Do not apply this category to non-game Unity tooling", self.unity_structure)
        self.assertLess(self.unity_structure.index("Do not apply this category to non-game Unity tooling"), self.unity_structure.index("## Ownership and lifecycle"))
        self.assertLess(self.unity_structure.index("## Ownership and lifecycle"), self.unity_structure.index("## Pattern decisions, not ceremony"))

    def test_unity_structure_contract_covers_ownership_data_exceptions_and_patterns(self):
        for requirement in ["only gameplay runtime-behavior roles", "`XXController`", "single-instance `XXManager`", "A Manager serializes ScriptableObject references only", "Controller may serialize only", "existing canonical ScriptableObject location", "hidden mutable globals", "runtime observations", "cached component references", "IDs and handles", "Factory", "Object Pool", "State", "Command", "Observer", "Prototype", "Singleton"]:
            self.assertIn(requirement, self.unity_structure)

    def test_global_core_cannot_be_weakened_by_project_defaults(self):
        self.assertIn("cannot silently weaken the Controller/Manager/ScriptableObject core", self.unity_structure)
        self.assertIn("deleting that reiteration later does not disable this global gate", self.unity_structure)
        self.assertIn("result memory never replaces this process gate", self.unity_structure)
        self.assertIn("may refine paths, bootstrap, naming, and stricter constraints", self.unity_structure)

    def test_global_unity_profile_routes_consumer_contracts_without_owning_them(self):
        self.assertIn("## Shared and consumer boundary", self.unity_rules)
        self.assertIn("must not repeat the Controller/Manager/ScriptableObject core", self.unity_rules)
        self.assertIn("fixed-membership or pool topology", self.unity_rules)
        self.assertIn("centralized Job/native-container boundary", self.unity_rules)
        global_references = "\n".join((self.unity_rules, self.unity_structure, self.unity_service))
        for consumer_only_term in ("SpriteTamerSystem", "SpriteMovementState", "JobRuntimeData", "FollowingPlayer"):
            self.assertNotIn(consumer_only_term, global_references)

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

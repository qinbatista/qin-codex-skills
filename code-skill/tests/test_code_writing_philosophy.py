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

    def test_unity_game_nodes_must_load_the_structure_reference_before_pattern_selection(self):
        self.assertIn("references/unity-game-code-structure-design.md", self.code_skill)
        self.assertIn("unity-game-code-structure-design.md", self.unity_rules)
        self.assertIn("references/unity-game-code-structure-design.md", self.agent_metadata)
        self.assertIn("Every Unity game C# writing node must also load", self.code_skill)
        self.assertIn("nearest project `AGENTS.md`", self.unity_structure)
        self.assertIn("Patterns solve a demonstrated lifecycle or coordination need", self.unity_rules)

    def test_agent_metadata_preserves_prior_lifecycle_routing_and_unity_requirements(self):
        required = [
            "$code-skill: artifact-free exact read-only lookup/audit stays skill-free",
            "references/code-writing-philosophy.md",
            "references/unity-game-code-structure-design.md",
            "Controller/Manager/ScriptableObject core",
            "Requested Cache/report output requires the runner",
            "Score every submission 0-100",
            "Spark-low",
            "quality failure suppresses the matching band",
            "immutable origin session",
            "smallest completion/record check",
            "projectless End Task",
            "all must PASS and remain visible",
            "Never auto-archive/delete",
            "attempts, first/retry pass, suitability, and Obsidian link",
            "codex_app__send_message_to_thread repairs in the source session",
            "fresh projectless verification",
            "Never self-verify or use a same-task subagent",
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

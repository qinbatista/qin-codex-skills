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

    def test_trigger_and_optional_project_memory(self):
        for concept in ("reusable prompts", "durable AI instructions", "Ordinary prose does not trigger", "every task", "skip it when unavailable", "project facts scoped to that project"):
            self.assertIn(concept, self.skill)

    def test_prompt_defines_only_material_controls(self):
        for concept in ("objective", "inputs and their roles", "output contract", "success/failure criteria", "missing-value behavior", "one authoritative rule", "resolve contradictions", "only when they change the result", "Examples illustrate", "private chain-of-thought"):
            self.assertIn(concept, self.skill)

    def test_verification_is_proportional_and_in_active_task(self):
        for concept in ("Verify within this active task", "semantic correctness", "simple value-only", "Read back", "Do not start the whole project", "Ending's memory branch", "no product verification or code repair", "one good sample does not prove stability"):
            self.assertIn(concept, self.skill)

    def test_retired_route_and_ending_verifier_contracts_are_absent(self):
        for document in (self.skill, self.metadata, self.code_reference):
            for retired in ("CODE READY", "Spark-xhigh", "Quick Check", "global projectless Ending", "prompt-task routing failure", "all checks PASS"):
                self.assertNotIn(retired, document)

    def test_spelling_and_input_authority_preserve_external_data(self):
        for concept in ("unambiguous spelling", "task-analyze-skill/SKILL.md#correct-task-names", "quoted user prose", "external names", "persisted/public contracts", "Current instructions and fresh source"):
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
                self.assertTrue((SKILL_ROOT / target.split("#", 1)[0]).exists())

    def test_action_requests_require_delivery_and_recovery_before_stopping(self):
        task_entry = (SKILL_ROOT.parent / "task-analyze-skill/SKILL.md").read_text(encoding="utf-8")
        policy = task_entry.split("## Complete action requests\n", 1)[1].split("\n## ", 1)[0]
        for concept in ("carry out its intended work within scope", "Deliver the requested change or artifact", "Keep working while a useful authorized route remains", "inspect the cause", "retry the affected step", "suitable available alternative", "Complete independent work", "does not by itself justify abandoning implementation", "do not use a fixed retry count"):
            self.assertIn(concept, policy)

    def test_action_blockers_require_evidence_and_preserve_truthful_partial_delivery(self):
        task_entry = (SKILL_ROOT.parent / "task-analyze-skill/SKILL.md").read_text(encoding="utf-8")
        policy = task_entry.split("## Complete action requests\n", 1)[1].split("\n## ", 1)[0]
        for concept in ("concrete blocker", "reasonable available actions within scope", "relevant attempts or authoritative evidence", "observed cause and what was attempted", "minimum external change needed", "Never bypass permissions, weaken acceptance, or invent success", "what was actually delivered", "Distinguish implementation, testing, deployment and publication", "A blocked check does not erase completed work", "If no requested result is achievable", "specific evidenced reason"):
            self.assertIn(concept, policy)

    def test_execution_entries_share_the_completion_owner_and_retire_premature_gap_exit(self):
        for relative in ("workflow-skill/SKILL.md", "verify-skill/SKILL.md", "code-skill/SKILL.md", "prompt-skill/SKILL.md"):
            with self.subTest(relative=relative):
                text = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                self.assertIn("../task-analyze-skill/SKILL.md#complete-action-requests", text)
                self.assertNotIn("report the gap instead of claiming success", text)
        workflow = (SKILL_ROOT.parent / "workflow-skill/SKILL.md").read_text(encoding="utf-8")
        verification = (SKILL_ROOT.parent / "verify-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("budget bounds polling for that step", workflow)
        self.assertIn("does not declare the whole task failed", workflow)
        self.assertIn("complete the authorized implementation and available focused checks first", verification)

    def test_completion_entry_points_keep_recovery_and_result_states_visible(self):
        for relative in ("task-analyze-skill/agents/openai.yaml", "workflow-skill/agents/openai.yaml", "verify-skill/agents/openai.yaml"):
            with self.subTest(relative=relative):
                metadata = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                self.assertIn("recoverable failures", metadata)
                self.assertLess(len(metadata), 750)
        template = (SKILL_ROOT.parent / "task-analyze-skill/assets/global-agents-entry-rule.md").read_text(encoding="utf-8")
        self.assertIn("action completion rule in `task-analyze-skill/SKILL.md`", template)
        self.assertIn("Separate verification blockers from implementation", template)

    def test_skill_reporting_records_use_for_one_final_summary(self):
        task_entry = (SKILL_ROOT.parent / "task-analyze-skill/SKILL.md").read_text(encoding="utf-8")
        policy = task_entry.split("## Mandatory visible Skill reporting\n", 1)[1].split("\n## ", 1)[0]
        for concept in ("record", "exact Skill name", "step", "reason", "actually used", "final response"):
            with self.subTest(concept=concept):
                self.assertIn(concept.lower(), policy.lower())
        for retired_rule in ("before the first tool call, tell the user", "Every user-facing progress update must include", "Repeat this at analysis"):
            with self.subTest(retired_rule=retired_rule):
                self.assertNotIn(retired_rule, policy)

    def test_skill_reporting_preserves_truth_and_delegated_actual_use(self):
        task_entry = (SKILL_ROOT.parent / "task-analyze-skill/SKILL.md").read_text(encoding="utf-8")
        policy = task_entry.split("## Mandatory visible Skill reporting\n", 1)[1].split("\n## ", 1)[0]
        for concept in ("actually used", "delegated", "planned", "unused", "missing", "Skills: none", "private chain-of-thought"):
            with self.subTest(concept=concept):
                self.assertIn(concept.lower(), policy.lower())

    def test_skill_reporting_is_reachable_from_always_loaded_and_skill_entries(self):
        for relative in ("workflow-skill/SKILL.md", "task-analyze-skill/assets/global-agents-entry-rule.md"):
            with self.subTest(relative=relative):
                entry = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                self.assertIn("task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting", entry)
        template = (SKILL_ROOT.parent / "task-analyze-skill/assets/global-agents-entry-rule.md").read_text(encoding="utf-8")
        for concept in ("final response", "exact Skill name", "step", "reason", "delegated", "Skills: none"):
            self.assertIn(concept.lower(), template.lower())
        self.assertNotIn("Every user-facing progress update must repeat", template)
        for relative in ("task-analyze-skill/agents/openai.yaml", "workflow-skill/agents/openai.yaml"):
            with self.subTest(relative=relative):
                metadata = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                for concept in ("final", "step", "reason", "branches"):
                    self.assertIn(concept, metadata.lower())
                self.assertNotIn("every progress update and phase transition", metadata)
                self.assertLess(len(metadata), 750)


if __name__ == "__main__":
    unittest.main()

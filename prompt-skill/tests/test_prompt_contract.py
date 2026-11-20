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
        for requirement in (
            "before detailed execution",
            "concrete final result, what will prove it",
            "feasible given the known prerequisites",
            "Carry out every technically viable step within that authority",
            "diagnose the cause, repair it within scope",
            "retry the affected step or use another authorized approach",
            "continue independent work while waiting",
            "check every requested outcome against actual evidence",
            "Continue on every unmet requirement that still has a viable authorized path",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, policy)

    def test_action_requests_limit_questions_updates_and_blocker_reports(self):
        task_entry = (SKILL_ROOT.parent / "task-analyze-skill/SKILL.md").read_text(encoding="utf-8")
        policy = task_entry.split("## Complete action requests\n", 1)[1].split("\n## ", 1)[0]
        for requirement in (
            "reasonable reversible assumptions to resolve routine choices without asking",
            "Ask only for indispensable input, a decision only the user can make, or required authorization",
            "Ask for the exact dependency once",
            "Never use an interim update to list unfinished work",
            "relevant attempts or authoritative evidence",
            "no further useful authorized work",
            "Lead with verified results",
            "minimum external change needed",
            "Keep the acceptance criteria unless the user changes them",
            "Report only supported results",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, policy)

    def test_execution_entries_share_the_completion_owner_and_retire_premature_gap_exit(self):
        for relative in ("workflow-skill/SKILL.md", "verify-skill/SKILL.md", "code-skill/SKILL.md", "prompt-skill/SKILL.md"):
            with self.subTest(relative=relative):
                text = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                self.assertIn("../task-analyze-skill/SKILL.md#complete-action-requests", text)
                self.assertNotIn("report the gap instead of claiming success", text)
        workflow = (SKILL_ROOT.parent / "workflow-skill/SKILL.md").read_text(encoding="utf-8")
        verification = (SKILL_ROOT.parent / "verify-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("If a check budget expires or a client stays stale", workflow)
        self.assertIn("another viable recovery path", workflow)
        self.assertIn("once no useful authorized action remains", workflow)
        self.assertIn("An authoritative receipt proves submission", workflow)
        self.assertIn("follow the job to its authoritative final state and verify its output", workflow)
        self.assertIn("complete the authorized implementation and available focused checks first", verification)

    def test_completion_entry_points_keep_recovery_and_result_states_visible(self):
        for relative in ("task-analyze-skill/agents/openai.yaml", "workflow-skill/agents/openai.yaml", "verify-skill/agents/openai.yaml"):
            with self.subTest(relative=relative):
                metadata = (SKILL_ROOT.parent / relative).read_text(encoding="utf-8")
                self.assertIn("recoverable failures", metadata)
                self.assertLess(len(metadata), 750)
        template = (SKILL_ROOT.parent / "task-analyze-skill/assets/global-agents-entry-rule.md").read_text(encoding="utf-8")
        self.assertIn("task-analyze-skill/SKILL.md#complete-action-requests", template)
        self.assertIn("observable acceptance criteria", template)
        self.assertIn("continue through verification and delivery while a viable authorized path remains", template)

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

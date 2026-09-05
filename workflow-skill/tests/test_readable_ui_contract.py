"""Protect one shared visual baseline and no-code presentation activation."""

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "workflow-skill/references/readable-ui.md"
spec = importlib.util.spec_from_file_location("ui_selected_policy", ROOT / "task-analyze-skill/scripts/selected_model_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class ReadableUIContractTests(unittest.TestCase):
    def test_one_baseline_covers_the_twelve_requested_concepts(self):
        text = (ROOT / REFERENCE).read_text()
        self.assertEqual(re.findall(r"^(\d+)\. ", text, re.M), [str(n) for n in range(1, 13)])
        for concept in ("horizontal headers", "Group simply", "unnecessary wrapping", "labels with their components", "functional sections", "Align panels", "fewer rows", "explanatory text", "desktop and mobile consistent", "Contain every element", "useful information per page", "Balance typography"):
            with self.subTest(concept=concept):
                self.assertIn(concept, text)
        self.assertIn("not shrinking everything", text)
        self.assertIn("placeholders alone are not labels", text)
        self.assertIn("no code changes", text)
        self.assertLess(len(text.split()), 1000)

    def test_global_and_workflow_entries_activate_for_non_code_presentations(self):
        for entry in ("task-analyze-skill/assets/global-agents-entry-rule.md", "workflow-skill/SKILL.md"):
            text = (ROOT / entry).read_text()
            with self.subTest(entry=entry):
                self.assertIn("readable-ui.md", text)
                for surface in ("websites", "PDF reports", "documents", "slide presentations", "without code changes"):
                    self.assertIn(surface, text)

    def test_existing_owners_link_to_the_same_real_source(self):
        for entry in ("workflow-skill/SKILL.md", "code-skill/references/coding-approach.md", "verify-skill/SKILL.md", "verify-skill/references/ui-problem-index.md"):
            path = ROOT / entry
            links = re.findall(r"\[[^\]]+\]\(([^)]+readable-ui\.md)\)", path.read_text())
            self.assertEqual(len(links), 1, entry)
            self.assertEqual((path.parent / links[0]).resolve(), ROOT / REFERENCE)

    def test_no_code_presentation_cannot_be_routed_as_unconstrained_work(self):
        for task_type in ("visual", "ui", "pdf", "report", "presentation", "slides"):
            node = {"task_type": task_type, "skill": "workflow-skill", "skill_independent": True}
            policy.bind_node(node, "gpt-6-astra", "ultra")
            with self.subTest(task_type=task_type):
                self.assertEqual((node["model"], node["effort"]), ("gpt-6-astra", "ultra"))
                self.assertTrue(node["model_locked"])
        self.assertTrue(policy.uses_selected_model({"routing_condition": {"artifact": "pdf"}}))
        self.assertFalse(policy.uses_selected_model({"task_type": "question", "skill": "workflow-skill"}))

    def test_visual_workers_receive_baseline_and_keep_selected_pair(self):
        for skill, task_type in (("emil-design-eng", "visual"), ("pdf:pdf", "document"), ("presentations:Presentations", "presentation")):
            for model, effort in (("gpt-5.6-luna", "max"), ("gpt-6-astra", "ultra")):
                node = {"skill": skill, "task_type": task_type, "model": "gpt-5.3-codex-spark", "effort": "low"}
                policy.bind_node(node, model, effort)
                with self.subTest(skill=skill, model=model):
                    self.assertEqual((node["model"], node["effort"]), (model, effort))
                    self.assertEqual(node["allow_fallback"], [])
                    self.assertIn(REFERENCE, policy.execution_guidance(node))


if __name__ == "__main__":
    unittest.main()

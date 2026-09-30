"""Protect one shared visual baseline and no-code presentation activation."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "workflow-skill/references/readable-ui.md"


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


if __name__ == "__main__":
    unittest.main()

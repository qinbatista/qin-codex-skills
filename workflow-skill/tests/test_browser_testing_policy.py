"""Protect the global default browser surface for test and verification work."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE = "prefer the Codex or ChatGPT built-in browser surface"
EXTERNAL_RULE = "Use a named external browser only when the user explicitly requests that browser."
FALLBACK_RULE = "If the built-in browser is unavailable, record that limitation"


class BrowserTestingPolicyTests(unittest.TestCase):
    def test_global_and_execution_entries_use_the_builtin_browser_by_default(self):
        entries = (
            ROOT / "task-analyze-skill/assets/global-agents-entry-rule.md",
            ROOT / "workflow-skill/SKILL.md",
            ROOT / "verify-skill/SKILL.md",
            ROOT / "code-skill/references/skill-platform-compatibility.md",
        )
        for path in entries:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(DEFAULT_RULE, text)
                self.assertIn(EXTERNAL_RULE, text)
                self.assertIn(FALLBACK_RULE, text)

    def test_policy_does_not_leave_the_old_unconditional_browser_show_rule(self):
        for relative in (
            "task-analyze-skill/assets/global-agents-entry-rule.md",
            "workflow-skill/SKILL.md",
            "verify-skill/SKILL.md",
            "code-skill/references/skill-platform-compatibility.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("opening or activating a browser requires an explicit request", text.lower())


if __name__ == "__main__":
    unittest.main()

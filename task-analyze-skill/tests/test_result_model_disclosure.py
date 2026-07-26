#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_task_analyze_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_task_analyze_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)
SKILLS_ROOT = Path(__file__).resolve().parents[2]


class ResultModelDisclosureTests(unittest.TestCase):
    def test_incomplete_screenshot_style_result_is_rejected(self):
        disclosure_text = "Complexity: 52/100 (complex)\nRoute change: upgrade\n"
        failures = module.validate_result_model_disclosure(disclosure_text)
        self.assertIn("missing or invalid Current model disclosure", failures)
        self.assertIn("missing or invalid Model pairs disclosure", failures)
        self.assertIn("missing or invalid Previous model disclosure", failures)
        self.assertIn("missing or invalid Reason disclosure", failures)

    def test_complete_no_switch_disclosure_is_accepted(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard)", "Current model: gpt-5.6-terra | high", "Model pairs (requested / resolved / effective): requested=gpt-5.6-terra|medium -> resolved=gpt-5.6-terra|high -> effective=gpt-5.6-terra|high", "Previous model: gpt-5.6-terra | medium", "Route change: no_switch", "Reason: No capability or budget trigger for escalation was detected."])
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_contract_exists_across_owning_skills(self):
        required_terms = ("Complexity:", "Current model:", "Model pairs (requested / resolved / effective):", "Previous model:", "Route change: upgrade|downgrade|freeze|no_switch|operational_fallback", "Reason:", "effective=UNVERIFIED (no runtime receipt)", "verified entry metadata or `unverified`", "no-switch")
        source_paths = [SKILLS_ROOT / "task-analyze-skill" / "SKILL.md", SKILLS_ROOT / "task-analyze-skill" / "references" / "route-contract.md", SKILLS_ROOT / "workflow-skill" / "SKILL.md", SKILLS_ROOT / "prompt-skill" / "SKILL.md", SKILLS_ROOT / "code-skill" / "SKILL.md", SKILLS_ROOT / "verify-skill" / "SKILL.md", SKILLS_ROOT / "optimization-skill" / "SKILL.md", SKILLS_ROOT / "management-skill" / "SKILL.md"]
        for source_path in source_paths:
            source_text = source_path.read_text(encoding="utf-8")
            for required_term in required_terms:
                self.assertIn(required_term, source_text, f"{source_path}: {required_term}")


if __name__ == "__main__":
    unittest.main()

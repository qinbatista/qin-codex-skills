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
        self.assertIn("missing or invalid Model evidence disclosure", failures)
        self.assertIn("missing or invalid Model pairs disclosure", failures)
        self.assertIn("missing or invalid Current model evidence-level disclosure", failures)
        self.assertIn("missing or invalid Previous model disclosure", failures)
        self.assertIn("missing or invalid Switch summary disclosure", failures)
        self.assertIn("missing or invalid Reason disclosure", failures)

    def test_complete_no_switch_disclosure_is_accepted(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard)", "Current model: gpt-5.6-terra | ultra", "Model evidence: task_assignment", "Model pairs (requested / resolved / effective): requested=gpt-5.6-terra|ultra -> resolved=gpt-5.6-terra|ultra -> effective=gpt-5.6-terra|ultra", "Current model evidence-level: UNVERIFIED (no runtime receipt)", "Previous model: same as current", "Route change: no_switch", "Switch summary: No model switch", "Reason: Assigned pair is known, but no runtime receipt is available."])
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_unverified_identity_and_inconsistent_no_switch_are_rejected(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard)", "Current model: unverified | unverified", "Model evidence: task_assignment", "Model pairs (requested / resolved / effective): requested=gpt-5.6-terra|ultra -> resolved=gpt-5.6-terra|ultra -> effective=gpt-5.6-terra|ultra", "Current model evidence-level: UNVERIFIED (no runtime receipt)", "Previous model: gpt-5.6-terra | max", "Route change: no_switch", "Switch summary: Switched models", "Reason: Assignment provenance is available."])
        failures = module.validate_result_model_disclosure(disclosure_text)
        self.assertIn("Current model must retain a known pair instead of unverified | unverified", failures)
        self.assertIn("Current model must match the effective model pair", failures)
        self.assertIn("no_switch requires one pair, Previous model: same as current (or none when unknown), and Switch summary: No model switch", failures)

    def test_unknown_identity_is_allowed_only_with_unavailable_evidence(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard)", "Current model: unknown | unknown", "Model evidence: unavailable", "Model pairs (requested / resolved / effective): requested=unknown|unknown -> resolved=unknown|unknown -> effective=unknown|unknown", "Current model evidence-level: unavailable", "Previous model: none", "Route change: no_switch", "Switch summary: No model switch", "Reason: No model identity source is available."])
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_contract_exists_across_owning_skills(self):
        required_terms = ("Complexity:", "Current model:", "Model evidence:", "Model pairs (requested / resolved / effective):", "Current model evidence-level:", "Previous model:", "Route change: upgrade|downgrade|freeze|no_switch|operational_fallback", "Switch summary:", "Reason:", "known assigned/configured/verified-entry pair", "unverified | unverified", "unknown | unknown", "No model switch")
        source_paths = [SKILLS_ROOT / "task-analyze-skill" / "SKILL.md", SKILLS_ROOT / "task-analyze-skill" / "references" / "route-contract.md", SKILLS_ROOT / "workflow-skill" / "SKILL.md", SKILLS_ROOT / "prompt-skill" / "SKILL.md", SKILLS_ROOT / "code-skill" / "SKILL.md", SKILLS_ROOT / "verify-skill" / "SKILL.md", SKILLS_ROOT / "optimization-skill" / "SKILL.md", SKILLS_ROOT / "management-skill" / "SKILL.md"]
        for source_path in source_paths:
            source_text = source_path.read_text(encoding="utf-8")
            for required_term in required_terms:
                self.assertIn(required_term, source_text, f"{source_path}: {required_term}")


if __name__ == "__main__":
    unittest.main()

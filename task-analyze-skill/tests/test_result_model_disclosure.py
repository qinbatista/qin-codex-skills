#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_task_analyze_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_task_analyze_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)
DISCLOSURE_SCRIPT_PATH = SCRIPT_PATH.with_name("model_identity_disclosure.py")
DISCLOSURE_MODULE_SPEC = importlib.util.spec_from_file_location(
    "model_identity_disclosure_for_tests", DISCLOSURE_SCRIPT_PATH
)
disclosure_module = importlib.util.module_from_spec(DISCLOSURE_MODULE_SPEC)
DISCLOSURE_MODULE_SPEC.loader.exec_module(disclosure_module)
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
        disclosure_text = "\n".join(["Complexity: 38/100 (standard)", "Current model: gpt-5.6-terra | ultra", "Model evidence: verified_entry", "Model pairs (requested / resolved / effective): requested=gpt-5.6-terra|ultra -> resolved=gpt-5.6-terra|ultra -> effective=gpt-5.6-terra|ultra", "Current model evidence-level: UNVERIFIED (no runtime receipt)", "Previous model: same as current", "Route change: no_switch", "Switch summary: No model switch", "Reason: Verified entry context supplied the current model identity."])
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

    def test_target_failure_replays_to_verified_entry_pair(self):
        target_entry = {"status": "verified", "model": "gpt-5.6-sol", "effort": "high"}
        repaired = disclosure_module.render_disclosure(75, entry_resolution=target_entry)
        self.assertIn("Current model: gpt-5.6-sol | high", repaired)
        self.assertIn("Model evidence: verified_entry", repaired)
        self.assertEqual(module.validate_result_model_disclosure(repaired), [])
        defective = "\n".join(["Complexity: 75/100 (advanced)", "Current model: GPT-5 | unknown", "Model evidence: configured system identity", "Model pairs (requested / resolved / effective): requested=GPT-5|unknown -> resolved=GPT-5|unknown -> effective=GPT-5|unknown", "Current model evidence-level: UNVERIFIED (no runtime receipt)", "Previous model: same as current", "Route change: no_switch", "Switch summary: No model switch", "Reason: Configured system identity."])
        self.assertTrue(module.validate_result_model_disclosure(defective))

    def test_runtime_receipt_is_higher_authority_than_verified_entry(self):
        disclosure_text = disclosure_module.render_disclosure(38, runtime_receipt={"requested_pair": "gpt-5.6-sol|high", "resolved_pair": "gpt-5.6-sol|high", "effective_pair": "gpt-5.6-terra|medium"}, entry_resolution={"status": "verified", "model": "gpt-5.6-sol", "effort": "high"})
        self.assertIn("Current model: gpt-5.6-terra | medium", disclosure_text)
        self.assertIn("Model evidence: runtime_receipt", disclosure_text)
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_only_active_quality_family_and_spark_pairs_are_allowed(self):
        allowed_pairs = disclosure_module._allowed_pairs()
        self.assertIn("gpt-5.6-sol|high", allowed_pairs)
        self.assertIn("gpt-5.6-terra|medium", allowed_pairs)
        self.assertIn("gpt-5.6-luna|low", allowed_pairs)
        self.assertIn("gpt-5.3-codex-spark|low", allowed_pairs)
        self.assertNotIn("gpt-5.5|high", allowed_pairs)
        self.assertNotIn("gpt-5.4|high", allowed_pairs)
        self.assertNotIn("GPT-5|unknown", allowed_pairs)

    def test_runtime_receipt_split_fields_build_exact_pairs(self):
        receipt = {"requested_model": "gpt-5.6-sol", "requested_effort": "high", "resolved_model": "gpt-5.6-terra", "resolved_effort": "high", "effective_model": "gpt-5.6-terra", "effective_effort": "medium"}
        identity = disclosure_module.resolve_disclosure_identity(runtime_receipt=receipt)
        self.assertEqual(identity["requested_pair"], "gpt-5.6-sol|high")
        self.assertEqual(identity["resolved_pair"], "gpt-5.6-terra|high")
        self.assertEqual(identity["effective_pair"], "gpt-5.6-terra|medium")

    def test_contract_exists_across_owning_skills(self):
        required_terms = ("Complexity:", "Current model:", "Model evidence:", "Model pairs (requested / resolved / effective):", "Current model evidence-level:", "Previous model:", "Route change: upgrade|downgrade|freeze|no_switch|operational_fallback", "Switch summary:", "Reason:", "known assigned/configured/verified-entry pair", "unverified | unverified", "unknown | unknown", "No model switch")
        source_paths = [SKILLS_ROOT / "task-analyze-skill" / "SKILL.md", SKILLS_ROOT / "task-analyze-skill" / "references" / "route-contract.md", SKILLS_ROOT / "workflow-skill" / "SKILL.md", SKILLS_ROOT / "prompt-skill" / "SKILL.md", SKILLS_ROOT / "code-skill" / "SKILL.md", SKILLS_ROOT / "verify-skill" / "SKILL.md", SKILLS_ROOT / "optimization-skill" / "SKILL.md", SKILLS_ROOT / "management-skill" / "SKILL.md"]
        for source_path in source_paths:
            source_text = source_path.read_text(encoding="utf-8")
            for required_term in required_terms:
                self.assertIn(required_term, source_text, f"{source_path}: {required_term}")


if __name__ == "__main__":
    unittest.main()

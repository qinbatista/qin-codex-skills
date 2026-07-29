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
        self.assertEqual(failures, ["missing or invalid compact model disclosure"])

    def test_complete_no_switch_disclosure_is_accepted(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard) · Model: gpt-5.6-terra|ultra · Route: no switch", "Evidence: verified entry (no runtime receipt)"])
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_unverified_identity_and_inconsistent_no_switch_are_rejected(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard) · Model: unverified|unverified · Route: no switch", "Model path: gpt-5.6-terra|ultra -> gpt-5.6-terra|max", "Evidence: task assignment (no runtime receipt)"])
        failures = module.validate_result_model_disclosure(disclosure_text)
        self.assertIn("model disclosure contains unsupported model pair: unverified|unverified", failures)
        self.assertIn("no switch or frozen route must omit Model path", failures)

    def test_unknown_identity_is_allowed_only_with_unavailable_evidence(self):
        disclosure_text = "\n".join(["Complexity: 38/100 (standard) · Model: unknown|unknown · Route: no switch", "Evidence: unavailable"])
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_target_failure_replays_to_verified_entry_pair(self):
        target_entry = {"status": "verified", "model": "gpt-5.6-sol", "effort": "high"}
        repaired = disclosure_module.render_disclosure(75, entry_resolution=target_entry)
        self.assertEqual(repaired, "\n".join(["Complexity: 75/100 (advanced) · Model: gpt-5.6-sol|high · Route: no switch", "Evidence: verified entry (no runtime receipt)"]))
        self.assertEqual(module.validate_result_model_disclosure(repaired), [])
        defective = "\n".join(["Complexity: 75/100 (advanced) · Model: GPT-5|unknown · Route: no switch", "Evidence: configured selection (no runtime receipt)"])
        self.assertTrue(module.validate_result_model_disclosure(defective))

    def test_runtime_receipt_is_higher_authority_than_verified_entry(self):
        disclosure_text = disclosure_module.render_disclosure(38, runtime_receipt={"requested_pair": "gpt-5.6-sol|high", "resolved_pair": "gpt-5.6-sol|high", "effective_pair": "gpt-5.6-terra|medium"}, entry_resolution={"status": "verified", "model": "gpt-5.6-sol", "effort": "high"})
        self.assertEqual(disclosure_text, "\n".join(["Complexity: 38/100 (standard) · Model: gpt-5.6-terra|medium · Route: fallback", "Model path: gpt-5.6-sol|high -> gpt-5.6-terra|medium", "Evidence: runtime receipt"]))
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_priority_selection_displays_adaptive_model_movement(self):
        receipt = {
            "requested_pair": "gpt-5.3-codex-spark|low",
            "resolved_pair": "gpt-5.3-codex-spark|low",
            "effective_pair": "gpt-5.3-codex-spark|low",
            "switch_direction": "downgrade",
            "switch_change": "gpt-5.6-terra|medium->gpt-5.3-codex-spark|low",
        }
        disclosure_text = disclosure_module.render_disclosure(12, runtime_receipt=receipt)
        self.assertEqual(disclosure_text, "\n".join([
            "Complexity: 12/100 (small) · Model: gpt-5.3-codex-spark|low · Route: downgrade",
            "Model path: gpt-5.6-terra|medium -> gpt-5.3-codex-spark|low",
            "Evidence: runtime receipt",
        ]))
        self.assertEqual(module.validate_result_model_disclosure(disclosure_text), [])

    def test_default_disclosure_omits_duplicate_detail_lines(self):
        disclosure_text = disclosure_module.render_disclosure(1, entry_resolution={"status": "verified", "model": "gpt-5.6-sol", "effort": "high"})
        self.assertEqual(len(disclosure_text.splitlines()), 2)
        for obsolete_label in ("Current model:", "Model pairs", "Previous model:", "Switch summary:", "Reason:"):
            self.assertNotIn(obsolete_label, disclosure_text)

    def test_runtime_receipt_replaces_wrong_or_verbose_leading_disclosure(self):
        receipt = {
            "requested_pair": "gpt-5.3-codex-spark|low",
            "resolved_pair": "gpt-5.3-codex-spark|low",
            "effective_pair": "gpt-5.3-codex-spark|low",
        }
        wrong = "\n".join([
            "Complexity: 8/100 (small) · Model: gpt-5.6-sol|high · Route: no switch",
            "Evidence: verified entry (no runtime receipt)",
            "",
            "Changed the value.",
        ])
        normalized = disclosure_module.normalize_result_disclosure(wrong, 8, runtime_receipt=receipt)
        self.assertTrue(normalized.startswith("Complexity: 8/100 (small) · Model: gpt-5.3-codex-spark|low · Route: no switch\nEvidence: runtime receipt"))
        self.assertEqual(normalized.count("Complexity:"), 1)
        self.assertIn("Changed the value.", normalized)

        verbose = "\n".join([
            "Complexity: 8/100 (small)",
            "Current model: gpt-5.6-sol | high",
            "Model evidence: verified_entry",
            "Previous model: same as current",
            "Route change: no_switch",
            "",
            "Answer: 56",
        ])
        compact = disclosure_module.normalize_result_disclosure(verbose, 8, runtime_receipt=receipt)
        self.assertNotIn("Current model:", compact)
        self.assertEqual(compact.count("Complexity:"), 1)
        self.assertIn("Answer: 56", compact)

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
        canonical_terms = ("Complexity:", "· Model:", "· Route:", "Evidence:", "verified entry (no runtime receipt)", "Model path:", "only when", "full routing data")
        canonical_paths = [SKILLS_ROOT / "task-analyze-skill" / "SKILL.md", SKILLS_ROOT / "task-analyze-skill" / "references" / "route-contract.md"]
        for source_path in canonical_paths:
            source_text = source_path.read_text(encoding="utf-8")
            for required_term in canonical_terms:
                self.assertIn(required_term, source_text, f"{source_path}: {required_term}")
        reference_paths = [SKILLS_ROOT / "workflow-skill" / "SKILL.md", SKILLS_ROOT / "prompt-skill" / "SKILL.md", SKILLS_ROOT / "code-skill" / "SKILL.md", SKILLS_ROOT / "verify-skill" / "SKILL.md", SKILLS_ROOT / "optimization-skill" / "SKILL.md", SKILLS_ROOT / "management-skill" / "SKILL.md"]
        for source_path in reference_paths:
            source_text = source_path.read_text(encoding="utf-8")
            for required_term in ("compact Result Model Disclosure", "task-analyze-skill/references/route-contract.md", "Do not expand"):
                self.assertIn(required_term, source_text, f"{source_path}: {required_term}")


if __name__ == "__main__":
    unittest.main()

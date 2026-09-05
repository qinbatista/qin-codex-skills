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

    def test_assignment_disclosure_never_claims_a_runtime_receipt(self):
        event = disclosure_module.model_disclosure_event(59, entry_resolution={"status": "task_assignment", "model": "gpt-6-astra", "effort": "ultra"})
        self.assertIn("Complexity: 59/100 (complex)", event["message"])
        self.assertIn("Evidence: task assignment (no runtime receipt)", event["message"])
        self.assertEqual(event["parent_action"], "surface_disclosure_in_conversation")
        self.assertTrue(event["user_visible"])

    def test_selected_model_outside_old_catalog_keeps_observed_switch_path(self):
        receipt = {"requested_pair": "gpt-5.6-luna|low", "resolved_pair": "gpt-5.6-luna|low",
                   "effective_pair": "gpt-5.6-luna|low", "switch_direction": "downgrade",
                   "switch_change": "gpt-6-astra|ultra->gpt-5.6-luna|low"}
        value = disclosure_module.render_disclosure(9, runtime_receipt=receipt)
        self.assertIn("Route: downgrade", value)
        self.assertIn("Model path: gpt-6-astra|ultra -> gpt-5.6-luna|low", value)
        self.assertEqual(disclosure_module.validate_disclosure(value), [])

    def test_deterministic_stage_does_not_invent_a_model(self):
        stages = {"nodes": [{"node_id": "capture", "phase": "result", "purpose": "Read bounded input",
                              "score": 2, "band": "small", "execution_kind": "deterministic-source-read",
                              "model_evidence_source": "deterministic_local_runtime", "status": "pass"}]}
        rendered = disclosure_module.render_stage_summary(stages)
        self.assertIn("Model: none (local process)", rendered)
        self.assertIn("Evidence: local process receipt (no model)", rendered)

    def test_default_disclosure_omits_duplicate_detail_lines(self):
        disclosure_text = disclosure_module.render_disclosure(1, entry_resolution={"status": "verified", "model": "gpt-5.6-sol", "effort": "high"})
        self.assertEqual(len(disclosure_text.splitlines()), 2)
        for obsolete_label in ("Current model:", "Model pairs", "Previous model:", "Switch summary:", "Reason:"):
            self.assertNotIn(obsolete_label, disclosure_text)

    def test_multi_stage_disclosure_lists_every_stage_score_pair_and_status(self):
        summary = {
            "nodes": [
                {
                    "node_id": "implementation",
                    "phase": "result",
                    "purpose": "Implement lifecycle gate",
                    "score": 84,
                    "band": "advanced",
                    "requested_pair": "gpt-5.6-sol|max",
                    "resolved_pair": "gpt-5.6-sol|max",
                    "effective_pair": "gpt-5.6-sol|max",
                    "model_evidence_source": "runtime_receipt",
                    "route_change": "no_switch",
                    "status": "pass",
                    "relations": {"dependencies": []},
                },
                {
                    "node_id": "quick-test",
                    "phase": "result",
                    "purpose": "Run focused tests",
                    "score": 32,
                    "band": "standard",
                    "requested_pair": "gpt-5.6-terra|medium",
                    "resolved_pair": "gpt-5.6-terra|medium",
                    "effective_pair": "gpt-5.6-terra|medium",
                    "model_evidence_source": "runtime_receipt",
                    "route_change": "no_switch",
                    "status": "pass",
                    "relations": {"dependencies": ["implementation"]},
                },
                {
                    "node_id": "ending-real",
                    "phase": "ending",
                    "purpose": "Independent real verification",
                    "score": 67,
                    "band": "complex",
                    "requested_pair": "gpt-5.6-sol|high",
                    "resolved_pair": "gpt-5.6-sol|high",
                    "effective_pair": "gpt-5.6-sol|high",
                    "model_evidence_source": "task_assignment",
                    "route_change": "freeze",
                    "status": "pending",
                    "relations": {"dependencies": ["quick-test"]},
                },
            ]
        }
        rendered = disclosure_module.render_disclosure(
            84,
            entry_resolution={"status": "verified", "model": "gpt-5.6-sol", "effort": "max"},
            model_switch_summary=summary,
        )
        self.assertIn("Model stages (3):", rendered)
        self.assertIn("Implement lifecycle gate [result:implementation] · Complexity: 84/100 (advanced) · Model: gpt-5.6-sol|max", rendered)
        self.assertIn("Run focused tests [result:quick-test] · Complexity: 32/100 (standard) · Model: gpt-5.6-terra|medium", rendered)
        self.assertIn("Independent real verification [ending:ending-real] · Complexity: 67/100 (complex) · Model: gpt-5.6-sol|high", rendered)
        self.assertIn("Status: PENDING · Evidence: task assignment (no runtime receipt)", rendered)
        self.assertEqual(module.validate_result_model_disclosure(rendered), [])

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
        self.assertNotIn("GPT-5|unknown", allowed_pairs)

    def test_runtime_receipt_split_fields_build_exact_pairs(self):
        receipt = {"requested_model": "gpt-5.6-sol", "requested_effort": "high", "resolved_model": "gpt-5.6-terra", "resolved_effort": "high", "effective_model": "gpt-5.6-terra", "effective_effort": "medium"}
        identity = disclosure_module.resolve_disclosure_identity(runtime_receipt=receipt)
        self.assertEqual(identity["requested_pair"], "gpt-5.6-sol|high")
        self.assertEqual(identity["resolved_pair"], "gpt-5.6-terra|high")
        self.assertEqual(identity["effective_pair"], "gpt-5.6-terra|medium")



if __name__ == "__main__":
    unittest.main()

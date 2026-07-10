#!/usr/bin/env python3
import importlib.util
from copy import deepcopy
import unittest
from pathlib import Path


SCRIPT_PATH = __import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "routing_policy.py"
MODULE_SPEC = importlib.util.spec_from_file_location("routing_policy", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class RoutingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.pairs = module.canonical_pairs(
            [
                "gpt-5.3-codex-spark|low",
                "gpt-5.3-codex-spark|medium",
                "gpt-5.3-codex-spark|high",
                "gpt-5.3-codex-spark|xhigh",
                "gpt-5.6-luna|low",
                "gpt-5.6-luna|medium",
                "gpt-5.6-luna|high",
                "gpt-5.6-luna|xhigh",
                "gpt-5.6-luna|max",
                "gpt-5.6-terra|low",
                "gpt-5.6-terra|medium",
                "gpt-5.6-terra|high",
                "gpt-5.6-terra|xhigh",
                "gpt-5.6-terra|max",
                "gpt-5.6-terra|ultra",
                "gpt-5.6-sol|low",
                "gpt-5.6-sol|medium",
                "gpt-5.6-sol|high",
                "gpt-5.6-sol|xhigh",
                "gpt-5.6-sol|max",
                "gpt-5.6-sol|ultra",
            ]
        )

    def test_downgrade_boundary_transitions(self):
        self.assertEqual(module.downgrade_pair(("gpt-5.6-sol", "ultra"), self.pairs), ("gpt-5.6-sol", "max"))
        self.assertEqual(module.downgrade_pair(("gpt-5.6-sol", "low"), self.pairs), ("gpt-5.6-terra", "ultra"))
        self.assertEqual(module.downgrade_pair(("gpt-5.6-terra", "low"), self.pairs), ("gpt-5.6-luna", "max"))
        self.assertEqual(module.downgrade_pair(("gpt-5.6-luna", "low"), self.pairs), ("gpt-5.3-codex-spark", "xhigh"))
        self.assertIsNone(module.downgrade_pair(("gpt-5.3-codex-spark", "low"), self.pairs))

    def test_upgrade_boundary_transitions(self):
        self.assertEqual(module.upgrade_pair(("gpt-5.3-codex-spark", "low"), self.pairs), ("gpt-5.3-codex-spark", "medium"))
        self.assertEqual(module.upgrade_pair(("gpt-5.3-codex-spark", "xhigh"), self.pairs), ("gpt-5.6-luna", "low"))
        self.assertEqual(module.upgrade_pair(("gpt-5.6-luna", "medium"), self.pairs), ("gpt-5.6-luna", "high"))
        self.assertEqual(module.upgrade_pair(("gpt-5.6-luna", "max"), self.pairs), ("gpt-5.6-terra", "low"))
        self.assertEqual(module.upgrade_pair(("gpt-5.6-terra", "ultra"), self.pairs), ("gpt-5.6-sol", "low"))
        self.assertIsNone(module.upgrade_pair(("gpt-5.6-sol", "ultra"), self.pairs))

    def test_sparse_eligible_pairs_preserve_model_then_effort_rules(self):
        sparse_upgrade = [("gpt-5.6-luna", "low"), ("gpt-5.6-luna", "max"), ("gpt-5.6-terra", "xhigh"), ("gpt-5.6-sol", "low")]
        sparse_upgrade_pairs = module.canonical_pairs([f"{model}|{effort}" for model, effort in sparse_upgrade])
        self.assertEqual(module.upgrade_pair(("gpt-5.6-luna", "low"), sparse_upgrade_pairs), ("gpt-5.6-luna", "max"))

        sparse_downgrade = [("gpt-5.6-luna", "max"), ("gpt-5.6-luna", "xhigh"), ("gpt-5.6-terra", "ultra"), ("gpt-5.3-codex-spark", "medium")]
        sparse_downgrade_pairs = module.canonical_pairs([f"{model}|{effort}" for model, effort in sparse_downgrade])
        self.assertEqual(module.downgrade_pair(("gpt-5.6-terra", "low"), sparse_downgrade_pairs), ("gpt-5.6-luna", "max"))

    def test_registry_extension_without_rank_code_changes(self):
        original_definitions = deepcopy(module.MODEL_DEFINITIONS)
        original_order = module.MODEL_ORDER[:]
        original_effort_order = module.MODEL_EFFORT_ORDER[:]
        original_efforts = {model: set(efforts) for model, efforts in module.MODEL_EFFORTS.items()}
        original_indexes = {model: dict(indexes) for model, indexes in module.MODEL_EFFORT_INDEX.items()}
        original_position = dict(module.MODEL_POSITION)
        try:
            module.MODEL_ORDER[:] = original_order[:2] + ["gpt-5.6-aurora"] + original_order[2:]
            module.MODEL_EFFORTS["gpt-5.6-aurora"] = {"low", "high"}
            module.MODEL_EFFORT_INDEX["gpt-5.6-aurora"] = {"low": 0, "high": 1}
            module.MODEL_POSITION = {model: index for index, model in enumerate(module.MODEL_ORDER)}

            extended_pairs = module.canonical_pairs(["gpt-5.3-codex-spark|low", "gpt-5.6-luna|high", "gpt-5.6-aurora|low", "gpt-5.6-aurora|high", "gpt-5.6-terra|low"])
            self.assertEqual(module.upgrade_pair(("gpt-5.6-luna", "high"), extended_pairs), ("gpt-5.6-aurora", "low"))
            self.assertEqual(module.downgrade_pair(("gpt-5.6-aurora", "low"), extended_pairs), ("gpt-5.6-luna", "high"))
        finally:
            module.MODEL_DEFINITIONS.clear()
            module.MODEL_DEFINITIONS.update(original_definitions)
            module.MODEL_ORDER[:] = original_order
            module.MODEL_EFFORT_ORDER[:] = original_effort_order
            module.MODEL_EFFORTS.clear()
            module.MODEL_EFFORTS.update(original_efforts)
            module.MODEL_EFFORT_INDEX.clear()
            module.MODEL_EFFORT_INDEX.update(original_indexes)
            module.MODEL_POSITION.clear()
            module.MODEL_POSITION.update(original_position)

    def test_parse_model_effort_pair_trims_whitespace(self):
        self.assertEqual(module.parse_model_effort_pair(" gpt-5.6-luna | medium "), ("gpt-5.6-luna", "medium"))
        self.assertEqual(module.parse_model_effort_pair("\tgpt-5.6-terra|\txhigh "), ("gpt-5.6-terra", "xhigh"))
        self.assertEqual(module.parse_model_effort_pair("gpt-5.6-sol |xhigh"), ("gpt-5.6-sol", "xhigh"))

    def test_parse_model_effort_pair_requires_exactly_one_separator_after_trimming(self):
        with self.assertRaises(ValueError):
            module.parse_model_effort_pair(" gpt-5.6-luna| medium| high ")
        with self.assertRaises(ValueError):
            module.parse_model_effort_pair("gpt-5.6-luna||low")

    def test_execution_domain_reference_paths_are_real_files(self):
        expected_paths = {
            "general": "task-analyze-skill/references/model-selection.md",
            "python": "code-skill/references/python-rules.md",
            "csharp": "code-skill/references/unity-csharp-rules.md",
            "unity_csharp": "code-skill/references/unity-csharp-rules.md",
            "code_unspecified": "code-skill/references/spark-small-code.md",
        }
        for domain in expected_paths:
            self.assertEqual(module.EXECUTION_DOMAINS[domain]["reference_path"], expected_paths[domain])
            path = Path("/Users/qin/.codex/skills") / expected_paths[domain]
            self.assertTrue(path.is_file(), f"reference path missing: {path}")


if __name__ == "__main__":
    unittest.main()

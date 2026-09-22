#!/usr/bin/env python3
"""Registry behavior against local catalog fixtures."""

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import model_registry


def catalog_model(slug, priority, efforts):
    return {"slug": slug, "display_name": slug.upper(), "description": "Available Codex model", "default_reasoning_level": "medium", "supported_reasoning_levels": [{"effort": effort} for effort in efforts], "visibility": "list", "supported_in_api": True, "priority": priority, "additional_speed_tiers": [], "input_modalities": ["text", "image"], "context_window": 272000}


def catalog():
    full = ("low", "medium", "high", "xhigh", "max", "ultra")
    return {"client_version": "1.2.3", "fetched_at": "2026-09-22T00:00:00Z", "models": [catalog_model("gpt-6-astra", 1, full), catalog_model("gpt-6-sol", 2, full), catalog_model("gpt-6-luna", 3, full[:-1]), catalog_model("retired-model", 20, full)]}


class ModelRegistryTests(unittest.TestCase):
    def test_only_three_current_models_and_supported_efforts_are_active(self):
        registry = model_registry.build_registry(catalog(), "a" * 64)
        self.assertEqual(registry["active_family"], {"id": "gpt-6", "numeric_version": [6], "selection": "requested_gpt6_variants", "model_count": 3})
        self.assertEqual([row["id"] for row in registry["models"]], ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"])
        self.assertEqual([row["id"] for row in registry["catalog_models"]], ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna"])
        self.assertEqual(registry["models"][0]["codex_efforts"], ["low", "medium", "high", "xhigh", "max"])
        self.assertEqual(registry["models"][-1]["codex_efforts"][-1], "ultra")
        self.assertIsNone(registry["priority_producer"])
        self.assertEqual(registry["role_models"], {"weak": "gpt-6-luna", "balanced": "gpt-6-sol", "frontier": "gpt-6-astra"})
        self.assertEqual(registry["default_cold_start"], "gpt-6-sol|medium")
        self.assertEqual(registry["cold_start_defaults"]["debug"]["complex"], "gpt-6-astra|high")
        self.assertNotIn("ending_fast", registry)
        self.assertIs(model_registry.validate_registry(registry), registry)

    def test_unrelated_models_do_not_change_active_digest_or_registry(self):
        original = catalog()
        without_retired = deepcopy(original)
        without_retired["models"].pop()
        self.assertEqual(model_registry.semantic_catalog_sha256(original), model_registry.semantic_catalog_sha256(without_retired))
        self.assertEqual(model_registry.build_registry(original)["models"], model_registry.build_registry(without_retired)["models"])

    def test_missing_duplicate_and_unknown_efforts_fail(self):
        missing = catalog()
        missing["models"] = [row for row in missing["models"] if row["slug"] != "gpt-6-sol"]
        with self.assertRaisesRegex(ValueError, "Astra, Sol, and Luna"):
            model_registry.build_registry(missing)
        duplicate = catalog()
        duplicate["models"].append(deepcopy(duplicate["models"][0]))
        with self.assertRaisesRegex(ValueError, "Astra, Sol, and Luna"):
            model_registry.build_registry(duplicate)
        unknown_effort = catalog()
        unknown_effort["models"][0]["supported_reasoning_levels"].append({"effort": "unsupported"})
        with self.assertRaisesRegex(ValueError, "unsupported reasoning effort"):
            model_registry.build_registry(unknown_effort)

    def test_new_supported_effort_is_reflected_without_inventing_one(self):
        updated = catalog()
        updated["models"][2]["supported_reasoning_levels"].append({"effort": "ultra"})
        registry = model_registry.build_registry(updated)
        self.assertEqual(registry["models"][0]["codex_efforts"][-1], "ultra")
        model_registry.validate_registry(registry)

    def test_validate_rejects_an_extra_route(self):
        registry = model_registry.build_registry(catalog())
        registry["models"].append(deepcopy(registry["models"][-1]))
        with self.assertRaisesRegex(ValueError, "ladder is incomplete"):
            model_registry.validate_registry(registry)

    def test_ensure_refresh_and_retention_use_file_readback(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cache_path = root / "models_cache.json"
            registry_path = root / "registry.json"
            initial = catalog()
            cache_path.write_text(json.dumps(initial), encoding="utf-8")
            generated = model_registry.ensure_registry(registry_path, cache_path)
            self.assertEqual(generated["status"], "generated")
            self.assertEqual(model_registry.load_registry(registry_path)["models"], generated["registry"]["models"])
            volatile = deepcopy(initial)
            volatile["fetched_at"] = "2026-09-23T00:00:00Z"
            cache_path.write_text(json.dumps(volatile), encoding="utf-8")
            self.assertEqual(model_registry.refresh_registry(registry_path, cache_path)["status"], "current")
            changed = deepcopy(initial)
            changed["models"][2]["supported_reasoning_levels"].append({"effort": "ultra"})
            cache_path.write_text(json.dumps(changed), encoding="utf-8")
            self.assertEqual(model_registry.refresh_registry(registry_path, cache_path)["status"], "refreshed")
            self.assertEqual(model_registry.load_registry(registry_path)["models"][0]["codex_efforts"][-1], "ultra")
            cache_path.unlink()
            self.assertEqual(model_registry.refresh_registry(registry_path, cache_path)["status"], "retained")

    def test_missing_catalog_and_registry_fail_clearly(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with self.assertRaisesRegex(RuntimeError, "saved model registry is missing"):
                model_registry.ensure_registry(root / "registry.json", root / "models_cache.json")


if __name__ == "__main__":
    unittest.main()

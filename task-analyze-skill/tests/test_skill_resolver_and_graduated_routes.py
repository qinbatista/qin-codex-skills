#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolver = load_module("skill_resolver")
validator = load_module("validate_graduated_routes")


class SkillResolverAndGraduatedRouteTests(unittest.TestCase):
    def test_resolves_global_and_synthetic_plugin_skills(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_path = root / "skills" / "verify-skill" / "SKILL.md"
            plugin_path = root / "plugins" / "cache" / "openai-curated-remote" / "vendor" / "1.0.0" / "skills" / "frontend-app-builder" / "SKILL.md"
            global_path.parent.mkdir(parents=True)
            plugin_path.parent.mkdir(parents=True)
            global_path.write_text("global", encoding="utf-8")
            plugin_path.write_text("plugin", encoding="utf-8")
            self.assertEqual(resolver.resolve_skill_path("verify-skill", root / "skills"), global_path.resolve())
            self.assertEqual(resolver.resolve_skill_path("vendor:frontend-app-builder", root / "skills"), plugin_path.resolve())

    def test_rejects_traversal_and_unqualified_plugin_leaf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            with self.assertRaises(ValueError):
                resolver.resolve_skill_path("../verify-skill", skills_root)
            self.assertIsNone(resolver.resolve_skill_path("frontend-app-builder", skills_root))

    def test_fixture_accepts_required_routes(self):
        self.assertEqual(validator.validate_fixture(), [])

    def test_fixture_require_installed_uses_synthetic_plugin_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skills_root = root / "skills"
            for skill_name in ("task-analyze-skill", "workflow-skill", "code-skill", "verify-skill", "optimization-skill", "management-skill"):
                skill_path = skills_root / skill_name / "SKILL.md"
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text(f"{skill_name}\n", encoding="utf-8")
            for reference in ("task-analyze-skill/references/model-selection.md", "code-skill/references/python-rules.md", "code-skill/references/csharp-rules.md", "code-skill/references/unity-csharp-rules.md", "code-skill/references/spark-small-code.md"):
                reference_path = skills_root / reference
                reference_path.parent.mkdir(parents=True, exist_ok=True)
                reference_path.write_text("reference\n", encoding="utf-8")
            for plugin_id, skill_name in (("chrome", "control-chrome"), ("build-web-apps", "frontend-app-builder")):
                skill_path = root / "plugins" / "cache" / "openai-curated-remote" / plugin_id / "1.0.0" / "skills" / skill_name / "SKILL.md"
                skill_path.parent.mkdir(parents=True)
                skill_path.write_text(f"{plugin_id}:{skill_name}\n", encoding="utf-8")
            self.assertEqual(validator.validate_fixture(validator.FIXTURE_PATH, skills_root, True), [])

    def test_fixture_require_installed_derives_missing_global_and_plugin_skills(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skills_root = root / "skills"
            for skill_name in ("task-analyze-skill", "workflow-skill", "management-skill"):
                skill_path = skills_root / skill_name / "SKILL.md"
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text(skill_name, encoding="utf-8")
            failures = validator.validate_fixture(validator.FIXTURE_PATH, skills_root, True)
        self.assertTrue(any("skill is not installed: verify-skill" in failure for failure in failures))
        self.assertTrue(any("skill is not installed: build-web-apps:frontend-app-builder" in failure for failure in failures))
        self.assertTrue(any("skill is not installed: chrome:control-chrome" in failure for failure in failures))

    def test_plugin_symlink_outside_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root / "outside" / "SKILL.md"
            outside.parent.mkdir()
            outside.write_text("outside", encoding="utf-8")
            link = root / "plugins" / "cache" / "openai-curated-remote" / "vendor" / "1.0.0" / "skills" / "skill" / "SKILL.md"
            link.parent.mkdir(parents=True)
            link.symlink_to(outside)
            self.assertIsNone(resolver.resolve_skill_path("vendor:skill", root / "skills"))

    def test_global_symlink_outside_skills_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root / "outside" / "SKILL.md"
            outside.parent.mkdir()
            outside.write_text("outside", encoding="utf-8")
            link = root / "skills" / "verify-skill" / "SKILL.md"
            link.parent.mkdir(parents=True)
            link.symlink_to(outside)
            self.assertIsNone(resolver.resolve_skill_path("verify-skill", root / "skills"))

    def test_direct_fixture_rejects_dispatch_receipt_and_adaptive_leakage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = json.loads(validator.FIXTURE_PATH.read_text(encoding="utf-8"))
            fixture["scenarios"][0]["dispatcher"] = True
            fixture["scenarios"][0]["receipt"] = True
            fixture["scenarios"][0]["adaptive_sample"] = True
            path = Path(temp_dir) / "fixture.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")
            self.assertTrue(any("leaks dispatch" in failure for failure in validator.validate_fixture(path)))

    def test_malformed_top_level_json_returns_validation_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.json"
            path.write_text("[]", encoding="utf-8")
            self.assertEqual(validator.validate_fixture(path), ["graduated fixture must contain exactly four scenarios"])

    def test_complex_fixture_rejects_wrong_shape_pair_and_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = json.loads(validator.FIXTURE_PATH.read_text(encoding="utf-8"))
            website = fixture["scenarios"][3]
            website["complexity"] = "easy"
            website.pop("dispatcher_plan")
            website["illustrative_cold_start_pairs"]["mini"] = "unsupported-model|high"
            website["skill"] = "frontend-app-builder"
            path = Path(temp_dir) / "fixture.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")
            failures = validator.validate_fixture(path)
            self.assertTrue(any("complex model_dispatch" in failure for failure in failures))
            self.assertTrue(any("static model/effort" in failure for failure in failures))
            self.assertTrue(any("dispatcher_plan" in failure for failure in failures))

    def test_complex_fixture_rejects_wrong_node_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = json.loads(validator.FIXTURE_PATH.read_text(encoding="utf-8"))
            website = fixture["scenarios"][3]
            website["dispatcher_plan"]["nodes"][1]["dependencies"] = ["mini"]
            path = Path(temp_dir) / "fixture.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")
            failures = validator.validate_fixture(path)
        self.assertTrue(any("role is incorrect for implementation" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

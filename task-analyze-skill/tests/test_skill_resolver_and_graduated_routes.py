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
    def test_canonicalizes_unambiguous_plugin_leaf_without_alias_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for version in ("1.0.0", "1.1.0"):
                plugin_path = root / "plugins" / "cache" / "synthetic-source" / "synthetic-package" / version / "skills" / "synthetic-skill" / "SKILL.md"
                plugin_path.parent.mkdir(parents=True)
                plugin_path.write_text("plugin", encoding="utf-8")
            canonical = resolver.canonicalize_installed_skill_id("synthetic-skill", root / "skills", root / "plugins" / "cache")
            prefixed = resolver.canonicalize_installed_skill_id("synthetic-package:synthetic-skill", root / "skills", root / "plugins" / "cache")
        self.assertEqual(canonical, "synthetic-package:synthetic-skill")
        self.assertEqual(prefixed, "synthetic-package:synthetic-skill")

    def test_canonical_global_skill_remains_unprefixed_when_plugin_leaf_matches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_path = root / "skills" / "shared-skill" / "SKILL.md"
            plugin_path = root / "plugins" / "cache" / "synthetic-source" / "synthetic-package" / "1.0.0" / "skills" / "shared-skill" / "SKILL.md"
            global_path.parent.mkdir(parents=True)
            plugin_path.parent.mkdir(parents=True)
            global_path.write_text("global", encoding="utf-8")
            plugin_path.write_text("plugin", encoding="utf-8")
            canonical = resolver.canonicalize_installed_skill_id("shared-skill", root / "skills", root / "plugins" / "cache")
        self.assertEqual(canonical, "shared-skill")

    def test_canonicalization_fails_closed_for_ambiguous_or_uninstalled_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for package in ("package-one", "package-two"):
                plugin_path = root / "plugins" / "cache" / "synthetic-source" / package / "1.0.0" / "skills" / "shared-plugin-skill" / "SKILL.md"
                plugin_path.parent.mkdir(parents=True)
                plugin_path.write_text("plugin", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                resolver.canonicalize_installed_skill_id("shared-plugin-skill", root / "skills", root / "plugins" / "cache")
            with self.assertRaisesRegex(ValueError, "not installed"):
                resolver.canonicalize_installed_skill_id("missing-skill", root / "skills", root / "plugins" / "cache")
            with self.assertRaisesRegex(ValueError, "not installed"):
                resolver.canonicalize_installed_skill_id("missing-package:shared-plugin-skill", root / "skills", root / "plugins" / "cache")

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







if __name__ == "__main__":
    unittest.main()

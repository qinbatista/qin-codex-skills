"""Exercise registry drift and duplicate-purpose detection."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SKILL_ROOT.parents[2]
SPEC = importlib.util.spec_from_file_location("audit_registry", SKILL_ROOT / "scripts" / "audit_registry.py")
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class RegistryAuditTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((SKILL_ROOT / "references" / "test-registry.json").read_text(encoding="utf-8"))

    def test_real_project_registry_matches_test_files(self):
        self.assertEqual(AUDITOR.audit_registry(PROJECT_ROOT, self.registry), [])

    def test_missing_entry_and_duplicate_purpose_are_reported(self):
        missing = json.loads(json.dumps(self.registry))
        omitted = missing["tests"].pop()
        self.assertIn(f"unregistered test file: {omitted['path']}", AUDITOR.audit_registry(PROJECT_ROOT, missing))

        duplicate = json.loads(json.dumps(self.registry))
        duplicate["tests"][1]["purpose"] = duplicate["tests"][0]["purpose"]
        self.assertIn(f"duplicate purpose: {duplicate['tests'][0]['purpose']}", AUDITOR.audit_registry(PROJECT_ROOT, duplicate))

        duplicate_goal = json.loads(json.dumps(self.registry))
        duplicate_goal["tests"][1]["goal"] = duplicate_goal["tests"][0]["goal"].upper().replace(",", "  ")
        self.assertTrue(any(issue.startswith("duplicate goal:") for issue in AUDITOR.audit_registry(PROJECT_ROOT, duplicate_goal)))

    def test_required_external_test_location_is_registered_without_copying(self):
        cache_root = PROJECT_ROOT / "Cache" / "temp-testing-skill"
        cache_root.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix="external-test-", dir=cache_root) as temporary_root:
                project_root = Path(temporary_root)
                skill_file = project_root / ".agents" / "skills" / "testing-skill" / "SKILL.md"
                skill_file.parent.mkdir(parents=True)
                skill_file.write_text("---\nname: testing-skill\n---\n", encoding="utf-8")
                external_test = project_root / "UnityGame" / "Assets" / "Tests" / "Editor" / "test_interaction.py"
                external_test.parent.mkdir(parents=True)
                external_test.write_text("# Editor-only test fixture\n", encoding="utf-8")
                registry = {"schema_version": 1, "tests": [{"path": external_test.relative_to(project_root).as_posix(), "purpose": "unity-interaction", "goal": "Verify the editor interaction at its required test location.", "level": 2, "runner": "Unity EditMode", "owner": "UnityGame"}]}
                self.assertEqual(AUDITOR.audit_registry(project_root, registry), [])
                skill_file.write_text("---\nname: wrong-skill\n---\n", encoding="utf-8")
                self.assertIn("testing-skill/SKILL.md requires frontmatter name: testing-skill", AUDITOR.audit_registry(project_root, registry))
        finally:
            try:
                cache_root.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()

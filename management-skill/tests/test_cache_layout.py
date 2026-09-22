import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cache_layout.py"
SPEC = importlib.util.spec_from_file_location("cache_layout", SCRIPT_PATH)
CACHE_LAYOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CACHE_LAYOUT)


class CacheLayoutTests(unittest.TestCase):
    def test_allowed_categories_are_classified(self):
        self.assertEqual(CACHE_LAYOUT.classify_directory("temp-build"), "temp")
        self.assertEqual(CACHE_LAYOUT.classify_directory("remote-test"), "remote")
        self.assertIsNone(CACHE_LAYOUT.classify_directory("20260820"))
        self.assertIsNone(CACHE_LAYOUT.classify_directory("tmp-build"))
        self.assertIsNone(CACHE_LAYOUT.classify_directory("tests"))
        self.assertIsNone(CACHE_LAYOUT.classify_directory("20261340"))

    def test_check_rejects_non_category_entries_and_uses_relative_reports(self):
        with tempfile.TemporaryDirectory(prefix="cache-layout-") as temporary:
            root = Path(temporary)
            cache_root = root / "Cache"
            cache_root.mkdir()
            (cache_root / "remote-test").mkdir()
            (cache_root / "temp-build").mkdir()
            report = CACHE_LAYOUT.inspect_project(root)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["cache_roots"][0]["invalid_entries"], [])
            self.assertEqual(report["cache_roots"][0]["path"], "Cache")
            self.assertEqual(report["project_root"], ".")

            (cache_root / "tests").mkdir()
            (cache_root / "20260820").mkdir()
            (cache_root / "cache_path.json").write_text("{}\n", encoding="utf-8")
            report = CACHE_LAYOUT.inspect_project(root)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["cache_roots"][0]["invalid_entries"], ["20260820", "cache_path.json", "tests"])

    def test_discovery_does_not_descend_into_cache_or_engine_directories(self):
        with tempfile.TemporaryDirectory(prefix="cache-discovery-") as temporary:
            root = Path(temporary)
            (root / "Project" / "Cache" / "remote-test").mkdir(parents=True)
            (root / "Project" / "Library" / "Nested" / "Cache").mkdir(parents=True)
            (root / ".git" / "Nested" / "Cache").mkdir(parents=True)
            discovered = CACHE_LAYOUT.discover_cache_roots(root)
            self.assertEqual(discovered, [root / "Project" / "Cache"])


if __name__ == "__main__":
    unittest.main()

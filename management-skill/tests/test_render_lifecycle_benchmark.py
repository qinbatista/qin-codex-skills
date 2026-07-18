import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "render_lifecycle_benchmark.py"
ASSET_ROOT = SKILL_ROOT / "assets" / "readme"
SUMMARY_PATH = ASSET_ROOT / "lifecycle-skill-benchmark.json"
SVG_PATH = ASSET_ROOT / "lifecycle-skill-benchmark.svg"
REPORT_PATH = ASSET_ROOT / "lifecycle-skill-benchmark.md"

SPEC = importlib.util.spec_from_file_location("render_lifecycle_benchmark", SCRIPT_PATH)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class LifecycleBenchmarkRendererTests(unittest.TestCase):
    def test_public_summary_is_the_exact_two_world_pass_contract(self):
        summary = renderer.load_summary(SUMMARY_PATH)
        self.assertEqual(summary["comparison_contract"], "exactly_two_worlds")
        self.assertEqual(summary["entry_pair_both_arms"], "gpt-5.6-sol|ultra")
        self.assertEqual((summary["pairs"], summary["main_runs"], summary["ending_runs"]), (6, 12, 6))
        self.assertIs(summary["all_main_correct"], True)
        self.assertIs(summary["all_endings_pass"], True)
        self.assertEqual(summary["world_without_skill_task"]["detached_check_tokens"], 0)
        self.assertEqual(summary["world_without_skill_task"]["detached_check_time_ms"], 0)
        self.assertEqual(summary["world_with_skill_task"]["tokens"], 552662)
        self.assertEqual(summary["world_with_skill_background_check"]["tokens"], 270556)
        self.assertEqual(summary["world_with_skill_task_plus_check"]["tokens"], 823218)
        self.assertAlmostEqual(summary["world_with_skill_task"]["token_saved_percent"], 56.41088737982002)
        self.assertAlmostEqual(summary["world_with_skill_task_plus_check"]["token_saved_percent"], 35.07181222345787)

    def test_checked_in_svg_matches_summary_and_stays_inside_viewbox(self):
        summary = renderer.load_summary(SUMMARY_PATH)
        root = ElementTree.parse(SVG_PATH).getroot()
        self.assertEqual(root.attrib["viewBox"], "0 0 1800 1550")
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        metadata = root.find("svg:metadata", namespace)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.attrib.get("id"), "benchmark-data")
        self.assertEqual(json.loads(metadata.text), summary)
        visible = " ".join("".join(node.itertext()) for node in root.findall(".//svg:text", namespace))
        for expected in (
            "Real two-world benchmark · PASS",
            "FINISH JOB FIRST → RETURN RESULT → BACKGROUND VERIFY IN A NEW END TASK",
            "56.411% fewer task tokens",
            "67.873% faster first result",
            "35.072% fewer tokens · 53.681% faster",
            "Ending evidence cost",
            "270,556 tokens / 66.513s",
            "common Sol-ultra dispatcher 404,598 tokens / 361.038s",
            "0 retry, fallback, or repair",
        ):
            self.assertIn(expected, visible)
        for rect in root.findall(".//svg:rect", namespace):
            x = float(rect.attrib.get("x", 0))
            y = float(rect.attrib.get("y", 0))
            width = float(rect.attrib.get("width", 0))
            height = float(rect.attrib.get("height", 0))
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + width, 1800)
            self.assertLessEqual(y + height, 1550)

    def test_renderer_is_deterministic(self):
        summary = renderer.load_summary(SUMMARY_PATH)
        expected = SVG_PATH.read_text(encoding="utf-8")
        self.assertEqual(renderer.render(summary), expected)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "benchmark.svg"
            renderer._atomic_write(output, renderer.render(summary))
            self.assertEqual(output.read_text(encoding="utf-8"), expected)

    def test_report_exposes_all_costs_and_no_private_paths(self):
        report = REPORT_PATH.read_text(encoding="utf-8")
        for expected in (
            "Entry model in both arms: `gpt-5.6-sol | ultra`",
            "56.411% fewer logical tokens",
            "35.072% fewer tokens",
            "Direct rows have no verifier",
            "404,598 tokens / 361.038s",
            "1,227,816 tokens / 578.124s",
            "Simple pair 1 (-4.851%)",
            "Medium pair 2 (-38.784%)",
            "68,483 bytes",
            "53,121 input tokens",
            "125,121 input tokens",
            "End Task-<related task name>",
        ):
            self.assertIn(expected, report)
        for forbidden in ("/Users/", '"thread_id"', '"receipt_path"'):
            self.assertNotIn(forbidden, report)


if __name__ == "__main__":
    unittest.main()

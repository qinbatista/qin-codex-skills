import importlib.util
import json
import re
import tempfile
import unittest
import unicodedata
import xml.etree.ElementTree as ElementTree
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("sync_global_skills", MODULE_PATH)
sync_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(sync_global_skills)
SKILLS_DIR = Path(__file__).resolve().parents[2]
README_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "readme"
BENCHMARK_RENDERER_PATH = SKILLS_DIR / "task-analyze-skill" / "scripts" / "render_benchmark_svg.py"
BENCHMARK_RENDERER_SPEC = importlib.util.spec_from_file_location("management_benchmark_renderer", BENCHMARK_RENDERER_PATH)
benchmark_renderer = importlib.util.module_from_spec(BENCHMARK_RENDERER_SPEC)
BENCHMARK_RENDERER_SPEC.loader.exec_module(benchmark_renderer)
NON_BENCHMARK_VISUAL_NAMES = ("qin-codex-skills-hero", "task-lifecycle", "model-router", "model-experience", "verification-topologies", "runtime-receipt")


def svg_character_width_factor(character):
    if character.isspace():
        return 0.32
    if character in "ilI1.,:;!|'`·":
        return 0.28
    if character in "MW@#%&":
        return 0.85
    if ord(character) > 127:
        return 1.0 if unicodedata.east_asian_width(character) in "WFA" else 0.65
    if character.isupper():
        return 0.63
    if character.islower() or character.isdigit():
        return 0.52
    return 0.45


def svg_bounds_issues(svg_path):
    root = ElementTree.parse(svg_path).getroot()
    viewbox_x, viewbox_y, viewbox_width, viewbox_height = [float(value) for value in root.attrib["viewBox"].split()]
    viewbox_right = viewbox_x + viewbox_width
    viewbox_bottom = viewbox_y + viewbox_height
    issues = []
    pending = [(root, 0.0, 0.0, 16.0, "start")]
    while pending:
        element, inherited_x, inherited_y, inherited_font_size, inherited_anchor = pending.pop()
        translate_x = inherited_x
        translate_y = inherited_y
        translate_match = re.fullmatch(r"translate\(([-\d.]+)(?:[ ,]+([-\d.]+))?\)", element.attrib.get("transform", ""))
        if translate_match:
            translate_x += float(translate_match.group(1))
            translate_y += float(translate_match.group(2) or 0)
        font_size = float(element.attrib.get("font-size", inherited_font_size))
        text_anchor = element.attrib.get("text-anchor", inherited_anchor)
        tag_name = element.tag.rsplit("}", 1)[-1]
        if tag_name == "rect":
            left = translate_x + float(element.attrib.get("x", 0))
            top = translate_y + float(element.attrib.get("y", 0))
            right = left + float(element.attrib.get("width", 0))
            bottom = top + float(element.attrib.get("height", 0))
            if left < viewbox_x or top < viewbox_y or right > viewbox_right or bottom > viewbox_bottom:
                issues.append(f"rect ({left}, {top}, {right}, {bottom})")
        elif tag_name == "line":
            line_x = [translate_x + float(element.attrib[key]) for key in ("x1", "x2")]
            line_y = [translate_y + float(element.attrib[key]) for key in ("y1", "y2")]
            if min(line_x) < viewbox_x or max(line_x) > viewbox_right or min(line_y) < viewbox_y or max(line_y) > viewbox_bottom:
                issues.append(f"line ({line_x}, {line_y})")
        elif tag_name == "text" and "x" in element.attrib and "y" in element.attrib:
            visible_text = "".join(element.itertext()).strip()
            text_x = translate_x + float(element.attrib["x"])
            text_y = translate_y + float(element.attrib["y"])
            estimated_width = font_size * sum(svg_character_width_factor(character) for character in visible_text) + 12.0
            text_left = text_x - estimated_width / 2 if text_anchor == "middle" else text_x - estimated_width if text_anchor == "end" else text_x
            text_right = text_left + estimated_width
            if text_left < viewbox_x or text_right > viewbox_right or text_y - font_size * 1.1 < viewbox_y or text_y + font_size * 0.25 > viewbox_bottom:
                issues.append(f"text {visible_text!r} ({text_left}, {text_right}, {text_y})")
        for child in element:
            pending.append((child, translate_x, translate_y, font_size, text_anchor))
    return issues


class SyncGlobalSkillsReadmeTest(unittest.TestCase):
    def primary_skill_paths(self):
        return [SKILLS_DIR / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]

    def test_approved_public_mirror_is_exactly_eight_including_project_memory(self):
        expected_order = ["task-analyze-skill", "workflow-skill", "prompt-skill", "code-skill", "project-memory-skill", "verify-skill", "optimization-skill", "management-skill"]

        self.assertEqual(sync_global_skills.PRIMARY_SKILL_ORDER, expected_order)
        self.assertEqual(sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES, set(expected_order))
        with tempfile.TemporaryDirectory() as temp_dir:
            repository_dir = Path(temp_dir)
            for skill_name in expected_order:
                (repository_dir / skill_name).mkdir()
                (repository_dir / skill_name / "SKILL.md").write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
            sync_global_skills.assert_repository_skill_set(repository_dir)
            (repository_dir / "project-memory-skill" / "SKILL.md").unlink()
            with self.assertRaisesRegex(RuntimeError, "project-memory-skill"):
                sync_global_skills.assert_repository_skill_set(repository_dir)

    def staged_skill_copy(self, root):
        skills_dir = root / "skills"
        skills_dir.mkdir()
        for skill_path in self.primary_skill_paths():
            sync_global_skills.copy_skill_directory(skill_path, skills_dir / skill_path.name)
        return skills_dir

    def test_external_file_symlink_is_rejected_even_when_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            link = skill_dir / "local" / "linked.txt"
            link.parent.mkdir()
            link.symlink_to(outside)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.included_files(skill_dir)

    def test_external_directory_symlink_is_rejected_even_when_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("outside", encoding="utf-8")
            link = skill_dir / "local"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.snapshot_hash([skill_dir])

    def test_symlink_rejection_does_not_copy_outside_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            outside = root / "outside.txt"
            outside.write_text("must stay outside", encoding="utf-8")
            (source / "SKILL.md").write_text("source", encoding="utf-8")
            (source / "linked.txt").symlink_to(outside)
            (target / "sentinel.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.copy_skill_directory(source, target)
            self.assertEqual(outside.read_text(encoding="utf-8"), "must stay outside")
            self.assertEqual((target / "sentinel.txt").read_text(encoding="utf-8"), "keep")
            self.assertFalse((target / "linked.txt").exists())

    def test_target_and_repository_sentinels_survive_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            staged_skills = self.staged_skill_copy(root)
            outside_target = root / "outside-target"
            outside_target.mkdir()
            (outside_target / "sentinel.txt").write_text("target sentinel", encoding="utf-8")
            target_link = root / "target"
            target_link.symlink_to(outside_target, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.copy_skill_directory(staged_skills / "task-analyze-skill", target_link)
            self.assertEqual((outside_target / "sentinel.txt").read_text(encoding="utf-8"), "target sentinel")

            outside_repository = root / "outside-repository"
            outside_repository.mkdir()
            (outside_repository / "sentinel.txt").write_text("repository sentinel", encoding="utf-8")
            repository_link = root / "repository"
            repository_link.symlink_to(outside_repository, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.prepare_repository_snapshot(repository_link, staged_skills)
            self.assertEqual((outside_repository / "sentinel.txt").read_text(encoding="utf-8"), "repository sentinel")

    def test_english_readme_uses_durable_template_and_current_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        template = sync_global_skills.ENGLISH_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template.replace("<!-- EXECUTION_DOMAIN_TABLE -->", sync_global_skills.execution_domain_table(sync_global_skills.load_staged_routing_policy(self.primary_skill_paths())))

        self.assertEqual(readme, expected)
        self.assertLessEqual(len(template.splitlines()), 130)
        self.assertLessEqual(len(template.split()), 900)
        self.assertEqual(readme.count("```mermaid"), 3)
        skills_section = readme.split("## Eight public Skills", 1)[1].split("\n## ", 1)[0]
        skill_rows = re.findall(r"^\| .*?\[`([^`]+)`\]\(\./([^/]+)/SKILL\.md\)", skills_section, re.M)
        expected_skill_rows = {"Task Analyze": "task-analyze-skill", "Workflow": "workflow-skill", "Prompt": "prompt-skill", "Code": "code-skill", "Project Memory": "project-memory-skill", "Verify": "verify-skill", "Optimization": "optimization-skill", "Management": "management-skill"}
        self.assertEqual(len(skill_rows), 8)
        self.assertEqual(dict(skill_rows), expected_skill_rows)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"./{skill_name}/SKILL.md", readme)

        self.assertIn("# AutoBestModel for Codex", readme)
        self.assertIn("mirrored identically to `qin-codex-skills` and `auto-best-model`", readme)
        self.assertIn("first tested and used with **GPT-5.6**", readme)
        self.assertIn("latest registered Codex models", readme)
        self.assertIn("Ordinary work stays inline on the current Codex model", readme)
        self.assertIn("Model delegation happens only for an explicit routing request", readme)
        self.assertIn("Project + functional module + target files", readme)
        self.assertIn("Authoritative local JSONL ledger", readme)
        self.assertIn("Obsidian is optional and never blocks work", readme)
        self.assertIn("Present completed result", readme)
        self.assertIn("Ending Real verifies the result", readme)
        self.assertIn("<!-- EXECUTION_DOMAIN_TABLE -->", template)
        self.assertNotIn("<!-- EXECUTION_DOMAIN_TABLE -->", readme)
        self.assertIn("Publishing runs a public-safety scan", readme)
        self.assertNotIn("model-benchmark-example.svg", readme)
        self.assertNotIn("benchmark_v5", readme)
        self.assertNotIn('"schema_version":', readme)
        self.assertNotIn('"conditions":', readme)
        self.assertNotIn('"producer":', readme)
        self.assertNotIn('"requested_pair":', readme)
        self.assertNotIn('"resolved_pair":', readme)
        self.assertNotIn('"effective_pair":', readme)
        self.assertNotIn("/Users/", readme)
        self.assertNotIn("hooks.json", readme)
        self.assertNotIn("TASK_ANALYZE_PLAN_JSON", readme)

    def test_readme_names_gpt_56_primary_ladder_and_latest_codex_registry(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        self.assertNotIn("Spark-first executor", readme)
        self.assertIn("primary adaptive ladder starts at GPT-5.6", readme)
        self.assertIn("latest registered Codex models", readme)
        self.assertIn("`gpt-5.6-luna`", readme)
        self.assertIn("`gpt-5.6-terra`", readme)
        self.assertIn("`gpt-5.6-sol`", readme)
        self.assertIn("optional compatibility route only for explicitly admitted tiny tasks", readme)
        self.assertIn("Spark obvious-task eligible", readme)
        self.assertNotIn("| Spark first |", readme)

    def test_chinese_readme_is_compact_diagram_first_and_has_memory_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="zh")
        template = sync_global_skills.CHINESE_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template.replace("<!-- EXECUTION_DOMAIN_TABLE -->", sync_global_skills.execution_domain_table(sync_global_skills.load_staged_routing_policy(self.primary_skill_paths())))
        self.assertEqual(readme, expected)
        self.assertLessEqual(len(template.splitlines()), 130)
        self.assertEqual(readme.count("```mermaid"), 3)
        self.assertIn("给 Codex 使用", readme)
        self.assertIn("从 **GPT-5.6** 开始测试和使用", readme)
        self.assertIn("按项目 + 功能模块 + 文件回溯记忆", readme)
        self.assertIn("本地 JSONL 权威记录", readme)
        self.assertIn("Obsidian 只做可读投影，未连接也不阻塞", readme)
        self.assertIn("## 八个公开 Skill", readme)

    def test_readme_explains_project_module_file_memory_and_optional_obsidian(self):
        readme = (README_ASSET_DIR / "github-readme-template.md").read_text(encoding="utf-8")
        self.assertIn("Project change memory", readme)
        self.assertIn("Project index", readme)
        self.assertIn("Module index", readme)
        self.assertIn("File-level history", readme)
        self.assertIn("Obsidian", readme)
        self.assertIn("Local memory remains authoritative", readme)

    def test_public_benchmark_asset_satisfies_current_strict_contract(self):
        evidence_path = SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json"
        evidence = benchmark_renderer.load_public_json(evidence_path)
        self.assertEqual(evidence["tier_repeat_counts"], {"simple": 2, "medium": 2, "complex": 2})
        self.assertEqual(evidence["expected_run_count"], 12)

    def test_readme_benchmark_is_sanitized_and_matches_public_evidence(self):
        readme = (README_ASSET_DIR / "github-readme-template.md").read_text(encoding="utf-8")
        evidence_path = SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json"
        evidence_text = evidence_path.read_text(encoding="utf-8")
        evidence = benchmark_renderer.load_public_json(evidence_path)
        benchmark_exporter = benchmark_renderer.benchmark_public_export
        benchmark_gate = benchmark_exporter.benchmark_suite_gate
        self.assertEqual(set(evidence), set(benchmark_renderer.PUBLIC_KEYS))
        self.assertEqual(evidence["schema_version"], benchmark_exporter.PUBLIC_SCHEMA_VERSION)
        self.assertIsNotNone(benchmark_gate.RUN_ID_PATTERN.fullmatch(evidence["suite_id"]))
        self.assertIsNotNone(benchmark_exporter.SHA256_PATTERN.fullmatch(evidence["plan_sha256"]))
        self.assertEqual(evidence["entry_pair"], "gpt-5.6-sol|ultra")
        self.assertEqual(evidence["evidence_scope"], benchmark_renderer.EVIDENCE_SCOPE)
        self.assertEqual(evidence["overall_status"], "pass")
        self.assertIs(evidence["all_correct"], True)
        self.assertEqual(evidence["tier_repeat_counts"], {"simple": 2, "medium": 2, "complex": 2})
        self.assertEqual(evidence["expected_run_count"], 12)
        self.assertEqual(
            evidence["rules"],
            {
                "tokens": benchmark_exporter.TOKEN_RULE,
                "time": benchmark_exporter.TIME_RULE,
                "overall": benchmark_exporter.OVERALL_RULE,
                "minimum_pairs_per_tier": benchmark_exporter.MINIMUM_PUBLIC_PAIR_COUNT,
            },
        )
        integrity = evidence["execution_integrity"]
        self.assertEqual(set(integrity), set(benchmark_renderer.INTEGRITY_KEYS))
        self.assertEqual(integrity["complete_runs"], evidence["expected_run_count"])
        self.assertGreaterEqual(integrity["runtime_session_count"], evidence["expected_run_count"])
        self.assertEqual(
            integrity["runtime_session_count"],
            integrity["complete_runs"] + integrity["runtime_descendant_count"],
        )
        self.assertLessEqual(integrity["multi_session_run_count"], integrity["complete_runs"])
        self.assertLessEqual(integrity["multi_session_run_count"], integrity["runtime_descendant_count"])
        self.assertEqual(integrity["retry_count"], 0)
        self.assertEqual(integrity["fallback_count"], 0)
        self.assertEqual(integrity["repair_count"], 0)
        self.assertEqual(set(evidence["configuration"]), set(benchmark_renderer.CONFIGURATION_KEYS))
        self.assertIs(evidence["configuration"]["config_hash_equal"], True)
        self.assertIs(evidence["configuration"]["catalog_hash_equal"], True)
        self.assertIsNotNone(benchmark_exporter.SHA256_PATTERN.fullmatch(evidence["configuration"]["config_sha256"]))
        self.assertEqual(set(evidence["configuration"]["agents_sha256"]), set(benchmark_gate.ARMS))
        for agents_sha256 in evidence["configuration"]["agents_sha256"].values():
            self.assertIsNotNone(benchmark_exporter.SHA256_PATTERN.fullmatch(agents_sha256))
        self.assertNotEqual(evidence["configuration"]["agents_sha256"]["direct"], evidence["configuration"]["agents_sha256"]["global"])
        self.assertIs(evidence["configuration"]["runtime_context_hash_equal"], True)
        self.assertIsNotNone(benchmark_exporter.SHA256_PATTERN.fullmatch(evidence["configuration"]["models_cache_sha256"]))
        self.assertIsNotNone(benchmark_exporter.SHA256_PATTERN.fullmatch(evidence["configuration"]["memories_sha256"]))
        self.assertEqual(set(evidence["caveats"]), {"generalization", "tokens", "first_result"})
        self.assertIn("not a universal guarantee", evidence["caveats"]["generalization"])
        self.assertIn("not a billing-token or price claim", evidence["caveats"]["tokens"])
        self.assertIn("Ending Task Real Verify is excluded", evidence["caveats"]["first_result"])
        self.assertEqual([task["tier"] for task in evidence["tasks"]], ["simple", "medium", "complex"])
        self.assertEqual(sum(task["pair_count"] for task in evidence["tasks"]), 6)
        self.assertEqual(sum(task["run_count"] for task in evidence["tasks"]), evidence["expected_run_count"])
        for task in evidence["tasks"]:
            self.assertEqual(set(task), set(benchmark_renderer.TASK_KEYS))
            self.assertEqual(task["label"], benchmark_exporter.TASK_LABELS[task["tier"]])
            self.assertEqual(task["pair_count"], 2)
            self.assertEqual(task["run_count"], 4)
            for metric_group in ("direct_totals", "global_totals", "direct_medians", "global_medians", "paired_savings_percent_medians"):
                self.assertEqual(set(task[metric_group]), set(benchmark_renderer.METRIC_KEYS))
            self.assertEqual(set(task["paired_wins"]), set(benchmark_renderer.METRIC_KEYS))
            self.assertEqual(set(task["metric_gates"]), set(benchmark_renderer.GATED_METRIC_KEYS))
            for metric, metric_gate in task["metric_gates"].items():
                expected_gate_keys = benchmark_renderer.TIME_METRIC_GATE_KEYS if metric == "first_result_elapsed_ms" else benchmark_renderer.METRIC_GATE_KEYS
                self.assertEqual(set(metric_gate), set(expected_gate_keys))
                self.assertEqual(metric_gate["status"], "pass")
                if metric == "logical_total_tokens":
                    self.assertLess(task["global_totals"][metric], task["direct_totals"][metric])
                    self.assertLess(task["global_medians"][metric], task["direct_medians"][metric])
                    self.assertGreaterEqual(task["paired_savings_percent_medians"][metric], metric_gate["minimum_paired_savings_percent"])
                    self.assertIs(metric_gate["regression_bound_required"], False)
                else:
                    self.assertIs(metric_gate["regression_bound_required"], False)
                    self.assertEqual(metric_gate["maximum_pair_regression_ms"], benchmark_gate.MAXIMUM_PAIRED_TIME_REGRESSION_MS)
                    self.assertGreaterEqual(metric_gate["material_pair_regression_count"], 0)
                    if task["tier"] == "medium":
                        self.assertLess(task["global_totals"][metric], task["direct_totals"][metric])
                        self.assertLess(task["global_medians"][metric], task["direct_medians"][metric])
                        self.assertGreaterEqual(task["paired_savings_percent_medians"][metric], metric_gate["minimum_paired_savings_percent"])
                    self.assertGreaterEqual(metric_gate["worst_pair_regression_ms"], 0)
                if metric_gate["strict_majority_required"]:
                    self.assertGreater(task["paired_wins"][metric], task["pair_count"] / 2)

        self.assertNotIn("benchmark_v5", readme)
        self.assertNotIn("Historical cohort", readme)
        self.assertNotIn("model-benchmark-example.svg", readme)
        for forbidden in ("/Users/", "thread_id", "session_id", "workload_prompt_sha256", "producer_run_id", '"prompt"', '"result"', '"receipt"', '"source_path"', '"plan_path"'):
            self.assertNotIn(forbidden, evidence_text)
        self.assertNotIn("timeout", evidence_text.lower())
        for filename in ("model-benchmark-example.svg", "model-benchmark-example-mobile.svg"):
            svg_path = README_ASSET_DIR / filename
            svg_text = svg_path.read_text(encoding="utf-8")
            svg_root = ElementTree.parse(svg_path).getroot()
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            metadata = svg_root.find("svg:metadata", namespace)
            self.assertIsNotNone(metadata, filename)
            self.assertEqual(metadata.attrib.get("id"), "benchmark-data", filename)
            self.assertEqual(json.loads(metadata.text), evidence, filename)
            visible_text = " ".join("".join(element.itertext()) for element in svg_root.findall(".//svg:text", namespace))
            self.assertIn("Real A/B benchmark · PASS", visible_text)
            self.assertIn(benchmark_renderer.integrity_summary(evidence), visible_text)
            for task in evidence["tasks"]:
                self.assertIn(task["label"], visible_text)
                self.assertIn(f"PASS · {task['pair_count']} pairs · {task['run_count']} runs", visible_text)
                self.assertIn(f"{benchmark_renderer.aggregate_savings_percent(task, 'logical_total_tokens'):.3f}%", visible_text)
                self.assertIn(f"{benchmark_renderer.aggregate_savings_percent(task, 'first_result_elapsed_ms'):.3f}%", visible_text)
            self.assertNotIn("timeout", svg_text.lower())
            for forbidden in ("/Users/", "thread_id", "session_id", '"prompt"', '"result"', '"receipt"'):
                self.assertNotIn(forbidden, svg_text)

    def test_desktop_benchmark_keeps_right_values_and_verdict_inside_viewbox(self):
        svg_path = README_ASSET_DIR / "model-benchmark-example.svg"
        root = ElementTree.parse(svg_path).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        viewbox = [float(value) for value in root.attrib["viewBox"].split()]
        self.assertEqual(viewbox, [0.0, 0.0, 1200.0, 760.0])
        self.assertEqual(root.attrib.get("width"), "1200")
        self.assertEqual(root.attrib.get("height"), "760")
        card_groups = []
        for group in root.findall(".//svg:g", namespace):
            card = group.find("svg:rect", namespace)
            if card is not None and card.attrib.get("width") == "1104" and card.attrib.get("height") == "166":
                card_groups.append(group)
        self.assertEqual(len(card_groups), 3)
        self.assertEqual([group.attrib.get("transform") for group in card_groups], ["translate(48 104)", "translate(48 288)", "translate(48 472)"])
        for group in card_groups:
            translate = re.fullmatch(r"translate\(([-\d.]+)\s+([-\d.]+)\)", group.attrib["transform"])
            self.assertIsNotNone(translate)
            translate_x = float(translate.group(1))
            translate_y = float(translate.group(2))
            card = group.find("svg:rect", namespace)
            self.assertGreaterEqual(translate_x, viewbox[0])
            self.assertGreaterEqual(translate_y, viewbox[1])
            self.assertLessEqual(translate_x + float(card.attrib["width"]), viewbox[2])
            self.assertLessEqual(translate_y + float(card.attrib["height"]), viewbox[3])
            pass_labels = [text for text in group.findall("svg:text", namespace) if "PASS ·" in "".join(text.itertext())]
            self.assertEqual(len(pass_labels), 1)
            self.assertEqual(pass_labels[0].attrib.get("text-anchor"), "end")
            self.assertLessEqual(translate_x + float(pass_labels[0].attrib["x"]), viewbox[2] - 48)

        verdict_rects = [rect for rect in root.findall("svg:rect", namespace) if rect.attrib.get("x") == "48" and rect.attrib.get("y") == "662" and rect.attrib.get("width") == "1104" and rect.attrib.get("height") == "76"]
        self.assertEqual(len(verdict_rects), 1)
        self.assertLessEqual(float(verdict_rects[0].attrib["x"]) + float(verdict_rects[0].attrib["width"]), viewbox[2])
        self.assertLessEqual(float(verdict_rects[0].attrib["y"]) + float(verdict_rects[0].attrib["height"]), viewbox[3])
        summary_lines = [text for text in root.findall("svg:text", namespace) if text.attrib.get("x") == "600" and text.attrib.get("text-anchor") == "middle"]
        self.assertEqual(len(summary_lines), 2)
        self.assertTrue(all(text.attrib.get("text-anchor") == "middle" for text in summary_lines))
        summary_text = " ".join("".join(text.itertext()) for text in summary_lines)
        evidence_path = SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json"
        evidence = benchmark_renderer.load_public_json(evidence_path)
        self.assertIn(f"All tiers PASS · {benchmark_renderer.metric_gate_verdict(evidence)}", summary_text)
        self.assertIn("gpt-5.6-sol | ultra", summary_text)
        self.assertIn("not a universal guarantee", summary_text)
        self.assertIn("not billing tokens", summary_text)

    def test_learning_visuals_do_not_present_fixed_code_model_pairs(self):
        visual_names = ("qin-codex-skills-hero", "task-lifecycle", "model-router", "model-experience", "verification-topologies")
        for visual_name in visual_names:
            for suffix in ("", "-mobile"):
                svg_text = (README_ASSET_DIR / f"{visual_name}{suffix}.svg").read_text(encoding="utf-8")
                self.assertNotRegex(svg_text, r"\[(?:Spark|Luna|Terra|Sol) \| ")
                self.assertNotIn("Spark first", svg_text)
        for suffix in ("", "-mobile"):
            hero_text = (README_ASSET_DIR / f"qin-codex-skills-hero{suffix}.svg").read_text(encoding="utf-8").lower()
            lifecycle_text = (README_ASSET_DIR / f"task-lifecycle{suffix}.svg").read_text(encoding="utf-8").lower()
            self.assertIn("inline", hero_text)
            self.assertIn("token + time", hero_text)
            self.assertIn("inline", lifecycle_text)
            self.assertIn("current model", lifecycle_text)
            self.assertIn("present", lifecycle_text)
            self.assertIn("first-result", lifecycle_text)
            self.assertIn("ending real", lifecycle_text)
        desktop_router = (README_ASSET_DIR / "model-router.svg").read_text(encoding="utf-8")
        mobile_router = (README_ASSET_DIR / "model-router-mobile.svg").read_text(encoding="utf-8")
        for svg_text in (desktop_router, mobile_router):
            self.assertIn("cold-start hint", svg_text)
            self.assertIn("Spark-low obvious-only", svg_text)
            self.assertIn("full normal fallback", svg_text)
        for visual_name in ("model-experience", "model-experience-mobile"):
            svg_text = (README_ASSET_DIR / f"{visual_name}.svg").read_text(encoding="utf-8").lower()
            self.assertIn("dynamic learned pair", svg_text)
            self.assertIn("same cohort", svg_text)
            self.assertIn("quality boundary", svg_text)
            self.assertIn("private", svg_text)
        desktop_verification = (README_ASSET_DIR / "verification-topologies.svg").read_text(encoding="utf-8")
        mobile_verification = (README_ASSET_DIR / "verification-topologies-mobile.svg").read_text(encoding="utf-8")
        self.assertIn("dynamic learned pair", desktop_verification)
        self.assertIn("first-result stops", mobile_verification)
        self.assertIn("no foreground verifier", mobile_verification)
        self.assertIn("Ending Real updates the same producer", mobile_verification)

    def test_snapshot_renders_synthetic_registered_rust_domain_without_generator_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, staged_skills / skill_path.name)
            policy = staged_skills / "task-analyze-skill" / "scripts" / "routing_policy.py"
            text = policy.read_text(encoding="utf-8")
            text = text.replace('    "code_unspecified": {', '    "rust": {"display_name": "Rust", "kind": "code", "language_aliases": ["rust", "rs"], "owner_skill": "code-skill", "owner_enforced": True, "spark_first": True, "reference_path": "code-skill/references/rust-rules.md", "active": True, "history_only": False},\n    "code_unspecified": {')
            policy.write_text(text, encoding="utf-8")
            (staged_skills / "code-skill" / "references" / "rust-rules.md").write_text("# Rust rules\n", encoding="utf-8")
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertIn("`rust` (active)", (repository_dir / "README.md").read_text(encoding="utf-8"))

    def test_snapshot_rejects_staged_domain_missing_owner_or_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, staged_skills / skill_path.name)
            policy = staged_skills / "task-analyze-skill" / "scripts" / "routing_policy.py"
            policy.write_text(policy.read_text(encoding="utf-8").replace('"code-skill/references/python-rules.md"', '"missing-skill/references/missing.md"'), encoding="utf-8")
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            with self.assertRaisesRegex(RuntimeError, "owner SKILL.md is missing|reference file is missing"):
                sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)

    def test_repository_snapshot_contains_every_local_readme_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, staged_skills / skill_path.name)

            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            copied_names = sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            readme = (repository_dir / "README.md").read_text(encoding="utf-8")

            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            local_references = set(re.findall(r'(?:src="|srcset="|\]\()(\./[^\"#)]+)', readme))
            svg_references = {reference for reference in local_references if reference.lower().endswith(".svg")}
            self.assertEqual(svg_references, set())
            for reference in local_references:
                referenced_path = repository_dir / reference.removeprefix("./")
                self.assertTrue(referenced_path.exists(), f"Missing generated README reference: {reference}")

    def test_readme_svgs_are_parseable_accessible_and_self_contained(self):
        svg_paths = sorted(README_ASSET_DIR.glob("*.svg"))
        self.assertEqual(len(svg_paths), 14)

        for svg_path in svg_paths:
            root = ElementTree.parse(svg_path).getroot()
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            self.assertIsNotNone(root.find("svg:title", namespace), svg_path.name)
            self.assertIsNotNone(root.find("svg:desc", namespace), svg_path.name)
            self.assertEqual(root.attrib.get("role"), "img", svg_path.name)
            self.assertIn("viewBox", root.attrib, svg_path.name)

            forbidden_tags = {element.tag.rsplit("}", 1)[-1] for element in root.iter() if element.tag.rsplit("}", 1)[-1] in {"script", "foreignObject"}}
            self.assertFalse(forbidden_tags, f"{svg_path.name}: {forbidden_tags}")
            for element in root.iter():
                for attribute, value in element.attrib.items():
                    if attribute.rsplit("}", 1)[-1] == "href":
                        self.assertFalse(value.startswith(("http://", "https://")), f"{svg_path.name}: external SVG reference {value}")

    def test_non_benchmark_diagram_cards_text_and_arrows_stay_inside_viewboxes(self):
        for visual_name in NON_BENCHMARK_VISUAL_NAMES:
            for suffix in ("", "-mobile"):
                svg_path = README_ASSET_DIR / f"{visual_name}{suffix}.svg"
                self.assertEqual(svg_bounds_issues(svg_path), [], svg_path.name)
        for visual_name in ("task-lifecycle", "verification-topologies"):
            for suffix in ("", "-mobile"):
                root = ElementTree.parse(README_ASSET_DIR / f"{visual_name}{suffix}.svg").getroot()
                marker_count = sum(1 for element in root.iter() if "marker-end" in element.attrib)
                self.assertGreaterEqual(marker_count, 3, f"{visual_name}{suffix}.svg")

    def test_unrelated_local_skill_is_ignored_and_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, staged_skills / skill_path.name)
            unrelated = staged_skills / "chronicle"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("---\nname: chronicle\ndescription: local only\n---\n")
            selected = sync_global_skills.skill_directories(staged_skills)
            self.assertEqual([path.name for path in selected], sync_global_skills.PRIMARY_SKILL_ORDER)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            copied_names = sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertTrue(unrelated.exists())
            self.assertFalse((repository_dir / "chronicle").exists())

    def test_pull_preserves_unrelated_local_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = sandbox / "repository"
            local_dir = sandbox / "local"
            repository_dir.mkdir()
            local_dir.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, repository_dir / skill_path.name)
                sync_global_skills.copy_skill_directory(skill_path, local_dir / skill_path.name)
            unrelated = local_dir / "chronicle"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("---\nname: chronicle\ndescription: local only\n---\n")
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertTrue(unrelated.exists())

    def test_private_model_experience_json_is_excluded_and_preserved_on_pull(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = sandbox / "repository"
            local_dir = sandbox / "local"
            repository_dir.mkdir()
            local_dir.mkdir()
            for skill_path in self.primary_skill_paths():
                sync_global_skills.copy_skill_directory(skill_path, repository_dir / skill_path.name)
                sync_global_skills.copy_skill_directory(skill_path, local_dir / skill_path.name)
            private_model_experience = local_dir / "task-analyze-skill" / "local" / "adaptive-routing" / "model_experience.json"
            private_model_experience.parent.mkdir(parents=True)
            private_model_experience_data = {
                "schema_version": 3,
                "updated_at": "2026-07-10T06:00:00.000000+00:00",
                "conditions": {
                    "local-model-experience-test": {
                        "condition": {
                            "task_family": "document",
                            "artifact": "document",
                            "execution_domain": "general",
                            "scope": "single",
                            "ambiguity": "low",
                            "modality": "text",
                            "risk": "low",
                            "complexity": "easy",
                            "owning_skill": "management-skill",
                            "project_family": "global-codex-skills",
                            "verification_shape": "mini_real",
                        },
                        "summary": "test local private model_experience preservation",
                        "candidate_ladder": ["gpt-5.3-codex-spark|low", "gpt-5.6-luna|low", "gpt-5.6-luna|medium"],
                        "hard_floor": "gpt-5.3-codex-spark|low",
                        "static_suggestion": "gpt-5.6-luna|low",
                        "failed_model": "gpt-5.6-luna|low",
                        "success_model": "gpt-5.6-luna|medium",
                        "tasks": [],
                    }
                },
            }
            private_model_experience_payload = json.dumps(private_model_experience_data, sort_keys=True, indent=2) + "\n"
            private_model_experience.write_text(private_model_experience_payload, encoding="utf-8")
            self.assertEqual(json.loads(private_model_experience.read_text(encoding="utf-8")), private_model_experience_data)

            local_skill_paths = [local_dir / skill_name for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER]
            private_hash_before = sync_global_skills.snapshot_hash(local_skill_paths)
            self.assertNotIn(private_model_experience, sync_global_skills.included_files(local_dir / "task-analyze-skill"))
            self.assertEqual(private_hash_before, sync_global_skills.snapshot_hash(local_skill_paths))

            snapshot_dir = sandbox / "snapshot"
            snapshot_dir.mkdir()
            copied_names = sync_global_skills.prepare_repository_snapshot(snapshot_dir, local_dir)
            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertFalse((snapshot_dir / "task-analyze-skill" / "local").exists())
            self.assertNotIn(private_model_experience, sync_global_skills.included_files(local_dir / "task-analyze-skill"))
            self.assertEqual(private_hash_before, sync_global_skills.snapshot_hash([snapshot_dir / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.assertIn("model_experience", private_model_experience.read_text(encoding="utf-8"))

            (repository_dir / "task-analyze-skill" / "SKILL.md").write_text((repository_dir / "task-analyze-skill" / "SKILL.md").read_text(encoding="utf-8") + "\nremote update\n", encoding="utf-8")
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertEqual(private_model_experience.read_text(encoding="utf-8"), private_model_experience_payload)


if __name__ == "__main__":
    unittest.main()

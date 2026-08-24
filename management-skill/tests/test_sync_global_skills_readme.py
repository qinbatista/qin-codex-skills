import importlib.util
import json
import re
import sys
import tempfile
import threading
import time
import unittest
import unicodedata
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("sync_global_skills", MODULE_PATH)
sync_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(sync_global_skills)
REAL_RUN_RELEASE_GATE = sync_global_skills.run_release_gate
SKILLS_DIR = Path(__file__).resolve().parents[2]
README_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "readme"
BENCHMARK_RENDERER_PATH = SKILLS_DIR / "task-analyze-skill" / "scripts" / "render_benchmark_svg.py"
BENCHMARK_RENDERER_SPEC = importlib.util.spec_from_file_location("management_benchmark_renderer", BENCHMARK_RENDERER_PATH)
benchmark_renderer = importlib.util.module_from_spec(BENCHMARK_RENDERER_SPEC)
BENCHMARK_RENDERER_SPEC.loader.exec_module(benchmark_renderer)
NON_BENCHMARK_VISUAL_NAMES = ("qin-codex-skills-hero", "task-lifecycle", "model-router", "model-experience", "verification-topologies", "runtime-receipt", "core-flow", "core-flow-zh")


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
    def setUp(self):
        self.release_gate_patcher = mock.patch.object(sync_global_skills, "run_release_gate")
        self.release_gate = self.release_gate_patcher.start()
        self.addCleanup(self.release_gate_patcher.stop)

    def primary_skill_paths(self):
        return [SKILLS_DIR / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]

    def test_default_runtime_state_stays_under_project_cache(self):
        self.assertEqual(sync_global_skills.DEFAULT_PROJECT_ROOT, Path.cwd().resolve())
        self.assertEqual(
            sync_global_skills.DEFAULT_STATE_FILE,
            sync_global_skills.DEFAULT_CACHE_ROOT / "state" / "management-skill-sync.json",
        )
        self.assertEqual(sync_global_skills.DEFAULT_CACHE_ROOT.parent.parent, sync_global_skills.DEFAULT_PROJECT_ROOT)

    def test_repository_git_url_falls_back_when_gh_lookup_fails(self):
        failure = sync_global_skills.subprocess.CalledProcessError(1, ["gh", "repo", "view"])
        with mock.patch.object(sync_global_skills.shutil, "which", return_value="gh"), mock.patch.object(sync_global_skills, "run_command", side_effect=failure):
            resolved_url = sync_global_skills.repository_git_url("owner/repository")

        self.assertEqual(resolved_url, "git@github.com:owner/repository.git")

    def test_repository_git_url_falls_back_when_gh_returns_no_url(self):
        completed = mock.Mock(stdout="\n")
        with mock.patch.object(sync_global_skills.shutil, "which", return_value="gh"), mock.patch.object(sync_global_skills, "run_command", return_value=completed):
            resolved_url = sync_global_skills.repository_git_url("owner/repository")

        self.assertEqual(resolved_url, "git@github.com:owner/repository.git")

    def test_read_only_repository_git_url_falls_back_to_https_without_gh(self):
        with mock.patch.object(sync_global_skills.shutil, "which", return_value=None):
            resolved_url = sync_global_skills.repository_git_url("owner/repository", read_only=True)

        self.assertEqual(resolved_url, "https://github.com/owner/repository.git")

    def test_read_only_repository_git_url_asks_gh_for_https_url(self):
        completed = mock.Mock(stdout="https://github.com/owner/repository\n")
        with mock.patch.object(sync_global_skills.shutil, "which", return_value="gh"), mock.patch.object(sync_global_skills, "run_command", return_value=completed) as runner:
            resolved_url = sync_global_skills.repository_git_url("owner/repository", read_only=True)

        self.assertEqual(resolved_url, "https://github.com/owner/repository")
        runner.assert_called_once_with(["gh", "repo", "view", "owner/repository", "--json", "url", "--jq", ".url"])

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

    def test_public_safety_rejects_absolute_user_home_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"private path: {Path('/', 'Users', 'example', 'private', 'file.txt')}\n", encoding="utf-8")
            issues = sync_global_skills.public_safety_issues([skill_dir])
        self.assertEqual(len(issues), 1)
        self.assertIn("secret-like content", issues[0])

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
        self.assertLessEqual(len(template.splitlines()), 100)
        self.assertLessEqual(len(template.split()), 1050)
        self.assertEqual(readme.count("```mermaid"), 0)
        self.assertIn("|---", readme)
        rules_section = readme.split("## Rules", 1)[1].split("\n## ", 1)[0]
        rule_lines = [line for line in rules_section.splitlines() if line.startswith("- ")]
        self.assertEqual(len(rule_lines), 9)
        self.assertLessEqual(max(map(len, rule_lines)), 160)
        skills_section = readme.split("## 🧩 Eight public Skills", 1)[1].split("\n## ", 1)[0]
        skill_rows = re.findall(r"^- \[`([^`]+)`\]\(\./([^/]+)/SKILL\.md\)", skills_section, re.M)
        expected_skill_rows = {"Task Analyze": "task-analyze-skill", "Workflow": "workflow-skill", "Prompt": "prompt-skill", "Code": "code-skill", "Project Memory": "project-memory-skill", "Verify": "verify-skill", "Optimization": "optimization-skill", "Management": "management-skill"}
        self.assertEqual(len(skill_rows), 8)
        self.assertEqual(dict(skill_rows), expected_skill_rows)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"./{skill_name}/SKILL.md", readme)

        self.assertIn("# 🚀 Auto Best Model", readme)
        self.assertIn("**Codex-only · score every task · finish first · Ending only for real evidence**", readme)
        self.assertNotIn("AutoBestModel", readme)
        self.assertIn("**Mirrors:** `qin-codex-skills` · `auto-best-model`", readme)
        self.assertIn("Saved highest-family quality ladder", readme)
        self.assertIn("refreshed only when you request a local model update", readme)
        self.assertIn("Small 0–24 low-risk edits try Spark-low after same-session outcome gate", readme)
        self.assertIn("larger work uses the saved quality ladder", readme)
        self.assertIn("Delegate only on explicit request or current end-to-end proof", readme)
        self.assertIn("Recall project/module/file history before editing", readme)
        self.assertIn("Native project → Model Switch → category → shared-category links", readme)
        self.assertIn("no JSON sidecar or full-history read", readme)
        self.assertIn("context kept as fields", readme)
        self.assertNotIn("private model learning stays under the existing project hierarchy", readme)
        self.assertNotIn("existing project/task/module/file/symbol hierarchy", readme)
        self.assertIn("## ⚡ Models & private learning", readme)
        self.assertIn("Cold start", readme)
        self.assertIn("zero-result failure gets one stronger fallback", readme)
        self.assertIn("Finish first. End only when there is real evidence", readme)
        self.assertIn("exactly one global-only projectless `End Task-<task name>`", readme)
        self.assertIn('create_thread.target={"type":"projectless"}', readme)
        self.assertIn("list_threads` readback must show `projectId=null` or absent", readme)
        self.assertIn("gpt-5.3-codex-spark|xhigh", readme)
        self.assertIn("the 0–100 score only scopes checks", readme)
        self.assertIn("registry-floor `gpt-5.6-luna|low` fallback", readme)
        self.assertIn("The one Ending runs the smallest real/completion checks and one terminal closeout", readme)
        self.assertIn("current immutable release report by checking its digest and final state", readme)
        self.assertIn("A low-risk, single-result small task", readme)
        self.assertIn("Project/current-task/same-task-subtask placement or missing readback is BLOCKED", readme)
        self.assertNotIn("no preference candidate means no preference write, never no Ending", readme)
        self.assertIn("all required checks must PASS", readme)
        self.assertIn("PASS/FAIL/BLOCKED stays visible", readme)
        self.assertIn("routing classification/model history", readme)
        self.assertIn("nothing auto-archives or deletes itself", readme)
        self.assertIn("## Rules", readme)
        self.assertIn("## 📊 Real adaptive benchmark: finish first, verify in background", readme)
        self.assertIn("20/20 expected results and evidence gates PASS", readme)
        self.assertIn("every tier and the aggregate lower both primary metrics", readme)
        self.assertIn("+80.774%", readme)
        self.assertIn("+64.686%", readme)
        self.assertIn("265.243s → 294.040s", readme)
        self.assertIn("1.378s` combined", readme)
        self.assertIn("<!-- EXECUTION_DOMAIN_TABLE -->", template)
        self.assertNotIn("<!-- EXECUTION_DOMAIN_TABLE -->", readme)
        self.assertIn("every publish runs a safety scan", readme)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-benchmark-example.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-benchmark-example-mobile.svg"), 1)
        self.assertEqual(readme.count("./task-analyze-skill/TEST_AND_BENCHMARK.md"), 1)
        self.assertEqual(readme.count("./task-analyze-skill/assets/model-routing-benchmark-example.json"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/core-flow.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/core-flow-mobile.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-router.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-router-mobile.svg"), 1)
        self.assertNotIn('"schema_version":', readme)
        self.assertNotIn('"conditions":', readme)
        self.assertNotIn('"producer":', readme)
        self.assertNotIn('"requested_pair":', readme)
        self.assertNotIn('"resolved_pair":', readme)
        self.assertNotIn('"effective_pair":', readme)
        self.assertNotIn("/Users/", readme)
        self.assertNotIn("hooks.json", readme)
        self.assertNotIn("TASK_ANALYZE_PLAN_JSON", readme)

    def test_readme_names_saved_manually_refreshed_highest_family_ladder(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        self.assertIn("Small 0–24 low-risk edits try Spark-low after same-session outcome gate", readme)
        self.assertIn("larger work uses the saved quality ladder", readme)
        self.assertIn("Saved highest-family quality ladder", readme)
        self.assertIn("refreshed only when you request a local model update", readme)
        self.assertIn("Use saved ladder", readme)
        self.assertIn("explicit update refreshes highest GPT family", readme)
        self.assertIn("missing cache preserves it", readme)
        self.assertNotIn("auto-switches", readme)
        self.assertIn("- `python` · code · `code-skill` · active · Spark schedule: source-eligible", readme)
        self.assertNotIn("| Spark first |", readme)

    def test_chinese_readme_is_compact_diagram_first_and_has_memory_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="zh")
        template = sync_global_skills.CHINESE_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template.replace("<!-- EXECUTION_DOMAIN_TABLE -->", sync_global_skills.execution_domain_table(sync_global_skills.load_staged_routing_policy(self.primary_skill_paths())))
        self.assertEqual(readme, expected)
        self.assertLessEqual(len(template.splitlines()), 100)
        self.assertEqual(readme.count("```mermaid"), 0)
        self.assertIn("|---", readme)
        rules_section = readme.split("## 规则", 1)[1].split("\n## ", 1)[0]
        rule_lines = [line for line in rules_section.splitlines() if line.startswith("- ")]
        self.assertEqual(len(rule_lines), 9)
        self.assertLessEqual(max(map(len, rule_lines)), 100)
        self.assertIn("# 🚀 Auto Best Model", readme)
        self.assertIn("专用于 Codex", readme)
        self.assertIn("只有真实证据才做 Ending", readme)
        self.assertIn("最高版本家族质量梯级", readme)
        self.assertIn("只有你主动要求本地模型更新时才刷新", readme)
        self.assertIn("修改前回溯项目/模块/文件历史", readme)
        self.assertIn("Model Switch 与原生类别链接", readme)
        self.assertIn("不用 JSON sidecar", readme)
        self.assertIn("项目/任务等保持为字段", readme)
        self.assertNotIn("私有模型学习挂在已有项目层级下", readme)
        self.assertNotIn("已有项目/任务/模块/文件/方法层级", readme)
        self.assertIn("## ⚡ 模型与私有学习", readme)
        self.assertIn("0–24 分小型低风险编辑先经同会话结果门再试 Spark-low", readme)
        self.assertIn("更大任务使用已保存的质量梯级", readme)
        self.assertIn("通过 `codex_app__send_message_to_thread` 把精确证据送回不可变 origin", readme)
        self.assertIn("最小真实/完成检查", readme)
        self.assertIn("低风险、单结果 small", readme)
        self.assertIn("缺少 thread 回执就是 BLOCKED", readme)
        self.assertNotIn("没有候选就不写偏好记忆，但绝不跳过 Ending", readme)
        self.assertIn("PASS/FAIL/BLOCKED 永久可见", readme)
        self.assertIn("不自动归档或删除", readme)
        self.assertIn("## 规则", readme)
        self.assertIn("## 📊 真实自适应 Benchmark：先完成，再后台验证", readme)
        self.assertIn("20/20 预期结果和证据门 PASS", readme)
        self.assertIn("每个档位和总体的两个主指标都下降", readme)
        self.assertIn("+80.774%", readme)
        self.assertIn("+64.686%", readme)
        self.assertIn("265.243s → 294.040s", readme)
        self.assertIn("合计 `1.378s`", readme)
        self.assertIn("## 🧩 八个公开 Skill", readme)
        self.assertEqual(readme.count("./management-skill/assets/readme/core-flow-zh.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/core-flow-zh-mobile.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-router.svg"), 1)
        self.assertEqual(readme.count("./management-skill/assets/readme/model-router-mobile.svg"), 1)

    def test_readme_separates_change_memory_from_private_model_learning(self):
        readme = (README_ASSET_DIR / "github-readme-template.md").read_text(encoding="utf-8")
        self.assertIn("project/module/file history", readme)
        self.assertIn("record the verified change", readme)
        self.assertIn("Obsidian", readme)
        self.assertIn("Change history is local JSONL + optional Obsidian", readme)
        self.assertIn("Native project → Model Switch → category → shared-category links", readme)
        self.assertIn("no JSON sidecar or full-history read", readme)
        self.assertIn("context kept as fields", readme)
        self.assertNotIn("private model learning stays under the existing project hierarchy", readme)
        self.assertNotIn("existing project/task/module/file/symbol hierarchy", readme)

    def test_model_switch_visuals_use_native_obsidian_category_graph(self):
        for filename in ("model-experience.svg", "model-experience-mobile.svg"):
            svg_text = (README_ASSET_DIR / filename).read_text(encoding="utf-8")
            self.assertIn("NATIVE OBSIDIAN GRAPH", svg_text)
            self.assertIn("shared category", svg_text.lower())
            self.assertIn("fields only", svg_text.lower())
            self.assertIn("no json sidecar", svg_text.lower())
            self.assertNotIn("REUSE PROJECT HIERARCHY", svg_text)

    def test_available_agent_short_descriptions_are_at_most_64_characters(self):
        available_agent_paths = [SKILLS_DIR / skill_name / "agents" / "openai.yaml" for skill_name in sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES if (SKILLS_DIR / skill_name / "agents" / "openai.yaml").exists()]

        self.assertEqual(len(available_agent_paths), 7)
        for agent_path in available_agent_paths:
            description_match = re.search(r'^  short_description: "([^"]+)"$', agent_path.read_text(encoding="utf-8"), re.M)
            self.assertIsNotNone(description_match, agent_path)
            self.assertLessEqual(len(description_match.group(1)), 64, agent_path)

    def test_public_benchmark_asset_satisfies_current_strict_contract(self):
        evidence_path = SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json"
        evidence = benchmark_renderer.load_public_json(evidence_path)
        expected_repeats = {"simple": 4, "medium": 2, "complex": 2, "advanced": 2}
        expected_run_count = sum(expected_repeats.values()) * 2
        expected_probe_count = len(benchmark_renderer.benchmark_public_export.benchmark_suite_gate.TIERS)
        self.assertEqual(evidence["schema_version"], benchmark_renderer.benchmark_public_export.PUBLIC_SCHEMA_VERSION)
        self.assertEqual(evidence["entry_pairs"], {"direct": "gpt-5.6-sol|ultra", "global": "gpt-5.6-luna|max"})
        self.assertEqual(evidence["tier_repeat_counts"], expected_repeats)
        self.assertEqual(evidence["expected_run_count"], expected_run_count)
        self.assertEqual(evidence["execution_integrity"]["complete_runs"], expected_run_count)
        self.assertEqual(evidence["execution_integrity"]["retry_count"], 0)
        self.assertEqual(evidence["execution_integrity"]["fallback_count"], 0)
        self.assertEqual(evidence["execution_integrity"]["repair_count"], 0)
        self.assertEqual(evidence["execution_integrity"]["sol_entry_probe_count"], expected_probe_count)
        self.assertEqual(evidence["execution_integrity"]["sol_entry_probe_pass_count"], expected_probe_count)
        self.assertIs(evidence["all_correct"], True)
        self.assertIs(evidence["all_optimized"], True)
        self.assertEqual(evidence["overall_status"], "pass")
        self.assertEqual(evidence["ending_diagnostics"]["status"], "pass")
        self.assertIs(evidence["ending_diagnostics"]["excluded_from_primary"], True)
        for metric_gate in evidence["cohort_metric_gates"].values():
            self.assertEqual(metric_gate["status"], "pass")
            self.assertLess(metric_gate["global_total"], metric_gate["direct_total"])

    def test_readme_benchmark_is_sanitized_and_matches_public_evidence(self):
        readme = (README_ASSET_DIR / "github-readme-template.md").read_text(encoding="utf-8")
        evidence_path = SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json"
        evidence_text = evidence_path.read_text(encoding="utf-8")
        evidence = benchmark_renderer.load_public_json(evidence_path)
        pair_count = sum(task["pair_count"] for task in evidence["tasks"])
        integrity = evidence["execution_integrity"]
        token_gate = evidence["cohort_metric_gates"]["steady_state_logical_tokens"]
        time_gate = evidence["cohort_metric_gates"]["steady_state_execution_elapsed_ms"]
        token_savings = (token_gate["direct_total"] - token_gate["global_total"]) * 100 / token_gate["direct_total"]
        time_savings = (time_gate["direct_total"] - time_gate["global_total"]) * 100 / time_gate["direct_total"]
        self.assertIn("Frozen v48", readme)
        self.assertIn(f"**{pair_count} A/B pairs · {evidence['expected_run_count']} runs", readme)
        self.assertIn(f"{integrity['sol_entry_probe_pass_count']}/{integrity['sol_entry_probe_count']} Sol-entry route probes PASS", readme)
        self.assertIn(f"**+{token_savings:.3f}%**", readme)
        self.assertIn(f"**+{time_savings:.3f}%**", readme)
        self.assertIn("every tier and the aggregate lower both primary metrics", readme)
        self.assertIn("Ending stays after the primary benchmark", readme)
        for task in evidence["tasks"]:
            self.assertIn(f"{task['direct_totals']['steady_state_logical_tokens']:,}", readme)
            self.assertIn(f"{task['global_totals']['steady_state_logical_tokens']:,}", readme)
            self.assertIn(f"+{benchmark_renderer.aggregate_savings_percent(task, 'steady_state_logical_tokens'):.3f}%", readme)
            self.assertIn(f"+{benchmark_renderer.aggregate_savings_percent(task, 'steady_state_execution_elapsed_ms'):.3f}%", readme)
        for forbidden in ("/Users/", "thread_id", "session_id", "workload_prompt_sha256", "producer_run_id", '"prompt"', '"result"', '"receipt"', '"source_path"', '"plan_path"'):
            self.assertNotIn(forbidden, readme)
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
                self.assertIn(f"CORRECT · {task['pair_count']} pairs · {task['run_count']} runs", visible_text)
                self.assertIn(f"{benchmark_renderer.aggregate_savings_percent(task, 'steady_state_logical_tokens'):.3f}%", visible_text)
                self.assertIn(f"{benchmark_renderer.aggregate_savings_percent(task, 'steady_state_execution_elapsed_ms'):.3f}%", visible_text)
            self.assertNotIn("timeout", svg_text.lower())
            self.assertEqual(svg_bounds_issues(svg_path), [])
            for forbidden in ("/Users/", "thread_id", "session_id", '"prompt"', '"result"', '"receipt"'):
                self.assertNotIn(forbidden, svg_text)

    def test_desktop_benchmark_keeps_right_values_and_verdict_inside_viewbox(self):
        svg_path = README_ASSET_DIR / "model-benchmark-example.svg"
        root = ElementTree.parse(svg_path).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        metadata = root.find("svg:metadata", namespace)
        evidence = benchmark_renderer.load_public_json(SKILLS_DIR / "task-analyze-skill" / "assets" / "model-routing-benchmark-example.json")
        expected_height = 104 + len(evidence["tasks"]) * 184 + 92 + 100
        self.assertEqual(root.attrib.get("viewBox"), f"0 0 1200 {expected_height}")
        self.assertEqual(root.attrib.get("width"), "1200")
        self.assertEqual(root.attrib.get("height"), str(expected_height))
        self.assertIsNotNone(metadata)
        self.assertEqual(json.loads(metadata.text), evidence)
        text = " ".join("".join(element.itertext()) for element in root.iter() if element.tag.rsplit("}", 1)[-1] in {"title", "desc", "text"})
        self.assertIn("Real A/B benchmark · PASS", text)
        self.assertIn("all runs correctness/evidence PASS", text)
        for task in evidence["tasks"]:
            self.assertIn(task["label"], text)

        card_groups = []
        for group in root.findall(".//svg:g", namespace):
            card = group.find("svg:rect", namespace)
            if card is not None and card.attrib.get("width") == "1104" and card.attrib.get("height") == "166":
                card_groups.append(group)
        self.assertEqual(len(card_groups), len(evidence["tasks"]))
        self.assertEqual([group.attrib.get("transform") for group in card_groups], [f"translate(48 {104 + index * 184})" for index in range(len(evidence["tasks"]))])
        for group in card_groups:
            status_labels = [element for element in group.findall("svg:text", namespace) if "pairs" in "".join(element.itertext()) and "runs" in "".join(element.itertext())]
            self.assertEqual(len(status_labels), 1)
            self.assertEqual(status_labels[0].attrib.get("text-anchor"), "end")
            self.assertLessEqual(float(status_labels[0].attrib["x"]), 1104 - 22)

        self.assertEqual(svg_bounds_issues(svg_path), [])

    def test_learning_visuals_do_not_present_fixed_code_model_pairs(self):
        visual_names = ("qin-codex-skills-hero", "task-lifecycle", "model-router", "model-experience", "verification-topologies")
        for visual_name in visual_names:
            for suffix in ("", "-mobile"):
                svg_text = (README_ASSET_DIR / f"{visual_name}{suffix}.svg").read_text(encoding="utf-8")
                self.assertNotRegex(svg_text, r"\[(?:Spark|Luna|Terra|Sol) \| ")
        for suffix in ("", "-mobile"):
            hero_text = (README_ASSET_DIR / f"qin-codex-skills-hero{suffix}.svg").read_text(encoding="utf-8").lower()
            lifecycle_text = (README_ASSET_DIR / f"task-lifecycle{suffix}.svg").read_text(encoding="utf-8").lower()
            self.assertIn("adaptive", hero_text)
            self.assertIn("cost admission", hero_text)
            self.assertIn("adaptive", lifecycle_text)
            self.assertIn("contextual", lifecycle_text)
            self.assertIn("present", lifecycle_text)
            self.assertIn("first-result", lifecycle_text)
            self.assertIn("ending real", lifecycle_text)
        desktop_router = (README_ASSET_DIR / "model-router.svg").read_text(encoding="utf-8")
        mobile_router = (README_ASSET_DIR / "model-router-mobile.svg").read_text(encoding="utf-8")
        for svg_text in (desktop_router, mobile_router):
            self.assertIn("task strategy", svg_text.lower())
            self.assertIn("small", svg_text.lower())
            self.assertIn("0–24", svg_text)
            self.assertIn("obsidian", svg_text.lower())
            self.assertIn("quality", svg_text)
        for visual_name in ("model-experience", "model-experience-mobile"):
            svg_text = (README_ASSET_DIR / f"{visual_name}.svg").read_text(encoding="utf-8").lower()
            self.assertIn("priority", svg_text)
            self.assertIn("quality", svg_text)
            self.assertIn("obsidian", svg_text)
            self.assertIn("quality failure", svg_text)
            self.assertIn("private", svg_text)
        desktop_verification = (README_ASSET_DIR / "verification-topologies.svg").read_text(encoding="utf-8")
        mobile_verification = (README_ASSET_DIR / "verification-topologies-mobile.svg").read_text(encoding="utf-8")
        self.assertIn("dynamic learned pair", desktop_verification)
        self.assertIn("fixed Spark-xhigh", desktop_verification)
        self.assertIn("unavailable → Luna-low", desktop_verification)
        self.assertIn("first-result stops", mobile_verification)
        self.assertIn("no foreground verifier", mobile_verification)
        self.assertIn("One fast Ending Task", mobile_verification)
        self.assertIn("Fixed Spark-xhigh", mobile_verification)
        self.assertIn("Luna-low only when Spark is unavailable", mobile_verification)

    def test_current_lifecycle_visuals_distinguish_material_ending_policy(self):
        for filename in (
            "qin-codex-skills-hero.svg",
            "qin-codex-skills-hero-mobile.svg",
            "task-lifecycle.svg",
            "task-lifecycle-mobile.svg",
            "core-flow.svg",
            "core-flow-mobile.svg",
        ):
            svg_text = (README_ASSET_DIR / filename).read_text(encoding="utf-8").lower()
            self.assertIn("material", svg_text, filename)
            self.assertIn("ending", svg_text, filename)
        for filename in ("core-flow-zh.svg", "core-flow-zh-mobile.svg"):
            svg_text = (README_ASSET_DIR / filename).read_text(encoding="utf-8")
            self.assertIn("材料", svg_text, filename)
            self.assertIn("Ending", svg_text, filename)

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
            self.assertIn("- `rust` · code · `code-skill` · active · Spark schedule: source-eligible", (repository_dir / "README.md").read_text(encoding="utf-8"))

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
            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            expected_svg_references = {"README.md": {"./management-skill/assets/readme/core-flow.svg", "./management-skill/assets/readme/core-flow-mobile.svg", "./management-skill/assets/readme/model-router.svg", "./management-skill/assets/readme/model-router-mobile.svg", "./management-skill/assets/readme/model-benchmark-example.svg", "./management-skill/assets/readme/model-benchmark-example-mobile.svg"}, "README.zh.md": {"./management-skill/assets/readme/core-flow-zh.svg", "./management-skill/assets/readme/core-flow-zh-mobile.svg", "./management-skill/assets/readme/model-router.svg", "./management-skill/assets/readme/model-router-mobile.svg", "./management-skill/assets/readme/model-benchmark-example.svg", "./management-skill/assets/readme/model-benchmark-example-mobile.svg"}}
            for readme_name, expected_references in expected_svg_references.items():
                readme = (repository_dir / readme_name).read_text(encoding="utf-8")
                local_references = set(re.findall(r'(?:src="|srcset="|\]\()(\./[^\"#)]+)', readme))
                svg_references = {reference for reference in local_references if reference.lower().endswith(".svg")}
                self.assertEqual(svg_references, expected_references)
                for reference in local_references:
                    referenced_path = repository_dir / reference.removeprefix("./")
                    self.assertTrue(referenced_path.exists(), f"Missing generated README reference: {reference}")

    def test_readme_svgs_are_parseable_accessible_and_self_contained(self):
        svg_paths = sorted(README_ASSET_DIR.glob("*.svg"))
        self.assertEqual(len(svg_paths), 19)

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

    def test_publication_snapshot_platform_check_is_limited_to_managed_skills(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = self.staged_skill_copy(sandbox)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            checker = mock.Mock(unsafe=True)
            with mock.patch.object(sync_global_skills, "load_skill_platform_checker", return_value=checker):
                sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            checker.assert_skill_platform_safe.assert_called_once_with(staged_skills, staged_skills / "code-skill" / "assets" / "skill-platform-baseline.json", selected_skill_names=sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES)

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
            remote_unrelated = repository_dir / "remote-extra" / "SKILL.md"
            remote_unrelated.parent.mkdir()
            remote_unrelated.write_text("---\nname: remote-extra\ndescription: remote only\n---\n", encoding="utf-8")
            unrelated = local_dir / "chronicle"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("---\nname: chronicle\ndescription: local only\n---\n")
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertTrue(unrelated.exists())
            self.release_gate.assert_not_called()

    def test_consumer_deploy_replaces_all_targets_without_semantic_checks_or_snapshot_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            with mock.patch.object(sync_global_skills, "load_staged_routing_policy", side_effect=AssertionError("consumer install must not load routing")) as routing, mock.patch.object(sync_global_skills, "load_skill_platform_checker", side_effect=AssertionError("consumer install must not run platform checks")) as platform, mock.patch.object(sync_global_skills, "run_release_gate", side_effect=AssertionError("consumer install must not run release gates")) as gate, mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer install must not run parity checks")) as parity, mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("consumer install must not hash skill trees")) as hasher:
                changed_names = sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertEqual([path.name for path in sync_global_skills.skill_directories(target_dir)], sync_global_skills.PRIMARY_SKILL_ORDER)
            routing.assert_not_called()
            platform.assert_not_called()
            gate.assert_not_called()
            parity.assert_not_called()
            hasher.assert_not_called()

    def test_pull_updates_to_latest_published_bytes_without_consumer_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = self.staged_skill_copy(sandbox)
            published_skill = repository_dir / "management-skill" / "SKILL.md"
            published_skill.write_text(published_skill.read_text(encoding="utf-8") + "\npublished-latest\n", encoding="utf-8")
            target_dir = sandbox / "global-skills"
            old_skill = target_dir / "management-skill" / "SKILL.md"
            old_skill.parent.mkdir(parents=True)
            old_skill.write_text("old-installation\n", encoding="utf-8")
            private_state = target_dir / "task-analyze-skill" / "local" / "events.jsonl"
            private_state.parent.mkdir(parents=True)
            private_state.write_text("private\n", encoding="utf-8")
            unrelated = target_dir / "chronicle" / "SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("unrelated\n", encoding="utf-8")

            with mock.patch.object(sync_global_skills, "clone_repository", return_value=repository_dir), mock.patch.object(sync_global_skills, "repository_head", return_value="published-head"), mock.patch.object(sync_global_skills, "write_sync_state") as state_writer, mock.patch.object(sync_global_skills, "load_staged_routing_policy", side_effect=AssertionError("consumer pull must not load routing")) as routing, mock.patch.object(sync_global_skills, "load_skill_platform_checker", side_effect=AssertionError("consumer pull must not run platform checks")) as platform, mock.patch.object(sync_global_skills, "assert_public_safe", side_effect=AssertionError("consumer pull must not run public safety")) as public_safety, mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer pull must not check parity")) as parity, mock.patch.object(sync_global_skills, "path_differs", side_effect=AssertionError("consumer pull must not pre-diff")) as differ, mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("consumer pull must not hash trees")) as hasher:
                changed_names = sync_global_skills.pull("owner/repository", target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertIn("published-latest", old_skill.read_text(encoding="utf-8"))
            self.assertEqual(private_state.read_text(encoding="utf-8"), "private\n")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "unrelated\n")
            self.assertEqual((target_dir.parent / "AGENTS.md").read_text(encoding="utf-8"), sync_global_skills.materialized_global_agents_text(repository_dir))
            state_writer.assert_called_once_with(sync_global_skills.DEFAULT_STATE_FILE, "owner/repository", "published-head", "", "")
            for forbidden in (routing, platform, public_safety, parity, differ, hasher, self.release_gate):
                forbidden.assert_not_called()

    def test_consumer_deploy_ignores_routing_validator_and_replaces_previous_opaque_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            target_dir = sandbox / "global-skills"
            outside = sandbox / "outside"
            outside.mkdir()
            outside_sentinel = outside / "sentinel.txt"
            outside_sentinel.write_text("outside\n", encoding="utf-8")
            previous_target = target_dir / "management-skill"
            previous_target.parent.mkdir(parents=True)
            previous_target.symlink_to(outside, target_is_directory=True)

            with mock.patch.object(sync_global_skills, "load_staged_routing_policy", side_effect=AssertionError("consumer install must not load routing")) as routing:
                sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertFalse(previous_target.is_symlink())
            self.assertTrue((previous_target / "SKILL.md").is_file())
            self.assertEqual(outside_sentinel.read_text(encoding="utf-8"), "outside\n")
            routing.assert_not_called()
            self.release_gate.assert_not_called()

    def test_deploy_replaces_file_symlink_and_directory_agents_targets_without_traversal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            target_dir = sandbox / "global-skills"
            target_dir.mkdir()
            outside = sandbox / "outside"
            outside.mkdir()
            outside_sentinel = outside / "sentinel.txt"
            outside_sentinel.write_text("outside\n", encoding="utf-8")
            (target_dir / "management-skill").symlink_to(outside, target_is_directory=True)
            (target_dir / "verify-skill").write_text("malformed old target\n", encoding="utf-8")
            agents_target = target_dir.parent / "AGENTS.md"
            agents_target.mkdir()
            (agents_target / "old.txt").write_text("old agents directory\n", encoding="utf-8")

            changed_names = sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertTrue((target_dir / "management-skill" / "SKILL.md").is_file())
            self.assertTrue((target_dir / "verify-skill" / "SKILL.md").is_file())
            self.assertTrue(agents_target.is_file())
            self.assertEqual(outside_sentinel.read_text(encoding="utf-8"), "outside\n")

    def test_missing_managed_source_stops_only_materialization_and_preserves_installation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = self.staged_skill_copy(sandbox)
            (source_dir / "verify-skill" / "SKILL.md").unlink()
            target_dir = sandbox / "global-skills"
            previous_skill = target_dir / "management-skill" / "SKILL.md"
            previous_skill.parent.mkdir(parents=True)
            previous_skill.write_text("previous-installation\n", encoding="utf-8")

            with mock.patch.object(sync_global_skills, "replace_path_entry", wraps=sync_global_skills.replace_path_entry) as replacer, self.assertRaisesRegex(RuntimeError, "source bytes could not be materialized"):
                sync_global_skills.deploy(source_dir, target_dir)

            self.assertEqual(previous_skill.read_text(encoding="utf-8"), "previous-installation\n")
            replacer.assert_not_called()
            self.release_gate.assert_not_called()

    def test_excluded_source_local_symlink_does_not_block_or_enter_installation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = self.staged_skill_copy(sandbox)
            outside = sandbox / "private-local"
            outside.mkdir()
            outside_sentinel = outside / "sentinel.txt"
            outside_sentinel.write_text("private\n", encoding="utf-8")
            source_local = source_dir / "management-skill" / "local"
            source_local.symlink_to(outside, target_is_directory=True)
            target_dir = sandbox / "global-skills"

            sync_global_skills.deploy(source_dir, target_dir)

            self.assertFalse((target_dir / "management-skill" / "local").exists())
            self.assertEqual(outside_sentinel.read_text(encoding="utf-8"), "private\n")

    def test_consumer_deploy_replaces_global_agents_bytes_without_semantic_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = self.staged_skill_copy(sandbox)
            source_asset = source_dir / sync_global_skills.GLOBAL_AGENTS_ASSET
            source_asset.write_text("# malformed lifecycle\n", encoding="utf-8")
            target_dir = sandbox / "global-skills"
            previous_agents = target_dir.parent / "AGENTS.md"
            previous_agents.write_text("# previous lifecycle\n", encoding="utf-8")
            replacement_observed = []
            real_replace = sync_global_skills.replace_path_entry

            def observe_replace(source, target):
                if Path(target) == previous_agents and "staged-agents" in Path(source).parts:
                    replacement_observed.append(Path(source).read_text(encoding="utf-8"))
                return real_replace(source, target)

            with mock.patch.object(sync_global_skills, "replace_path_entry", side_effect=observe_replace), mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer install must not validate AGENTS parity")) as parity:
                sync_global_skills.deploy(source_dir, target_dir)

            self.assertEqual(replacement_observed, ["# malformed lifecycle\n"])
            self.assertEqual(previous_agents.read_text(encoding="utf-8"), "# malformed lifecycle\n")
            parity.assert_not_called()
            self.release_gate.assert_not_called()

    def test_root_symlink_is_a_safe_write_blocker_and_external_target_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_root = sandbox / ".codex"
            codex_root.mkdir()
            outside = sandbox / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_text("outside\n", encoding="utf-8")
            logical_skills = codex_root / "skills"
            logical_skills.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "global Skill root"):
                sync_global_skills.deploy(SKILLS_DIR, logical_skills)

            self.assertTrue(logical_skills.is_symlink())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "outside\n")
            self.assertFalse((outside / "management-skill").exists())
            self.assertFalse((codex_root / "AGENTS.md").exists())

    def test_interrupted_partial_installation_is_restored_from_persistent_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            target_dir = sandbox / "global-skills"
            previous_skill = target_dir / "task-analyze-skill" / "SKILL.md"
            previous_skill.parent.mkdir(parents=True)
            previous_skill.write_text("previous task analyze\n", encoding="utf-8")
            private_state = previous_skill.parent / "local" / "events.jsonl"
            private_state.parent.mkdir()
            private_state.write_text("private\n", encoding="utf-8")
            transaction_root = sync_global_skills.create_installation_workspace(target_dir)
            bundle = sync_global_skills.stage_installation_bundle(SKILLS_DIR, target_dir, transaction_root)
            snapshot = sync_global_skills.new_deployment_snapshot(target_dir, transaction_root, bundle)
            sync_global_skills.write_installation_manifest(snapshot, "prepared")
            sync_global_skills.capture_deployment_snapshot(snapshot)
            for record in snapshot["records"][:3]:
                sync_global_skills.replace_path_entry(record["staged"], record["target"])

            sync_global_skills.recover_interrupted_installations(target_dir)

            self.assertEqual(previous_skill.read_text(encoding="utf-8"), "previous task analyze\n")
            self.assertEqual(private_state.read_text(encoding="utf-8"), "private\n")
            self.assertFalse((target_dir / "workflow-skill").exists())
            self.assertFalse(transaction_root.exists())

    def test_failed_backup_restore_is_recovered_on_next_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            target_dir = sandbox / "global-skills"
            previous_skill = target_dir / "management-skill" / "SKILL.md"
            previous_skill.parent.mkdir(parents=True)
            previous_skill.write_text("previous installation\n", encoding="utf-8")
            real_replace = sync_global_skills.replace_path_entry
            injected_install_failure = []
            injected_restore_failure = []

            def fail_one_backup_restore(source, target):
                source_path = Path(source)
                target_path = Path(target)
                if not injected_install_failure and "staged-skills" in source_path.parts and target_path.name == "verify-skill":
                    injected_install_failure.append(True)
                    raise PermissionError("injected target write failure")
                if injected_install_failure and not injected_restore_failure and "previous" in source_path.parts and target_path == previous_skill.parent:
                    injected_restore_failure.append(True)
                    raise PermissionError("injected backup restore failure")
                return real_replace(source, target)

            with mock.patch.object(sync_global_skills, "replace_path_entry", side_effect=fail_one_backup_restore), self.assertRaisesRegex(RuntimeError, "automatic restore also failed"):
                sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertFalse(previous_skill.is_file())
            self.assertTrue(list(target_dir.parent.glob(f"{sync_global_skills.INSTALL_TRANSACTION_PREFIX}*")))
            sync_global_skills.recover_interrupted_installations(target_dir)
            self.assertEqual(previous_skill.read_text(encoding="utf-8"), "previous installation\n")
            self.assertFalse(list(target_dir.parent.glob(f"{sync_global_skills.INSTALL_TRANSACTION_PREFIX}*")))

    def test_installation_lock_waits_for_the_active_writer_then_acquires(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            acquired = []
            failures = []

            def wait_for_lock():
                try:
                    with sync_global_skills.installation_lock(target_dir, timeout_seconds=2.0):
                        acquired.append(True)
                except Exception as error:
                    failures.append(error)

            with sync_global_skills.installation_lock(target_dir):
                waiter = threading.Thread(target=wait_for_lock)
                waiter.start()
                time.sleep(0.2)
                self.assertEqual(acquired, [])
            waiter.join(timeout=2.0)
            self.assertEqual(failures, [])
            self.assertEqual(acquired, [True])

    def test_deploy_copies_repository_skills_and_preserves_local_private_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            private_state = target_dir / "task-analyze-skill" / "local" / "adaptive-routing" / "events.jsonl"
            private_state.parent.mkdir(parents=True)
            private_state.write_text("private-state\n", encoding="utf-8")
            unrelated = target_dir / "chronicle" / "SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("local-only\n", encoding="utf-8")
            global_agents = target_dir.parent / "AGENTS.md"
            global_agents.write_text("# stale lifecycle\n", encoding="utf-8")

            changed_names = sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertEqual(private_state.read_text(encoding="utf-8"), "private-state\n")
            self.assertTrue(unrelated.is_file())
            self.assertEqual(global_agents.read_text(encoding="utf-8"), sync_global_skills.canonical_global_agents_text(SKILLS_DIR))
            self.assertEqual(sync_global_skills.snapshot_hash(self.primary_skill_paths()), sync_global_skills.snapshot_hash([target_dir / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.release_gate.assert_not_called()

    def test_deployed_release_gate_bootstraps_from_provisional_installed_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = sandbox / "source"
            skills_dir = sandbox / "global-skills"
            source_dir.mkdir()
            installed_gate = skills_dir / "management-skill" / "scripts" / "global_skill_regression_gate.py"
            installed_gate.parent.mkdir(parents=True)
            installed_gate.write_text("# installed gate\n", encoding="utf-8")
            completed = mock.Mock(stdout="", stderr="", returncode=0)

            with mock.patch.object(sync_global_skills.subprocess, "run", return_value=completed) as runner:
                REAL_RUN_RELEASE_GATE(source_dir, skills_dir, "deployed")

            command = runner.call_args.args[0]
            self.assertEqual(Path(command[1]), installed_gate.resolve())

    def test_deploy_preserves_unrelated_runtime_skill_without_running_platform_checker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            unrelated_script = target_dir / "external-windows-tool" / "scripts" / "apply.ps1"
            unrelated_script.parent.mkdir(parents=True)
            (unrelated_script.parents[1] / "SKILL.md").write_text("---\nname: external-windows-tool\ndescription: local only\n---\n", encoding="utf-8")
            unrelated_script.write_text("param([switch]$SkipStartupEntry)\n", encoding="utf-8")
            unrelated_before = unrelated_script.read_bytes()

            with mock.patch.object(sync_global_skills, "load_skill_platform_checker", side_effect=AssertionError("consumer install must not run platform checks")) as platform:
                sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(unrelated_script.read_bytes(), unrelated_before)
            platform.assert_not_called()


    def test_deploy_cli_accepts_skills_dir_after_subcommand(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            argv = [
                "sync_global_skills.py",
                "deploy",
                "--source-dir",
                str(SKILLS_DIR),
                "--skills-dir",
                str(target_dir),
            ]
            with mock.patch.object(sys, "argv", argv):
                sync_global_skills.main()
            self.assertEqual(sync_global_skills.snapshot_hash(self.primary_skill_paths()), sync_global_skills.snapshot_hash([target_dir / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.assertEqual((target_dir.parent / "AGENTS.md").read_text(encoding="utf-8"), sync_global_skills.canonical_global_agents_text(SKILLS_DIR))

    def test_pull_cli_accepts_repository_and_skills_dir_after_subcommand(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            argv = ["sync_global_skills.py", "pull", "--repo", "owner/repository", "--skills-dir", str(target_dir)]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "pull") as pull_command:
                sync_global_skills.main()
            pull_command.assert_called_once_with("owner/repository", target_dir)

    def test_legacy_sync_is_an_unconditional_install_only_pull_without_prediff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            with mock.patch.object(sync_global_skills, "pull", return_value=sync_global_skills.PRIMARY_SKILL_ORDER) as installer, mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("sync must not pre-diff")) as hasher:
                changed_names = sync_global_skills.sync("owner/repository", target_dir, "unused publication message")
            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            installer.assert_called_once_with("owner/repository", target_dir)
            hasher.assert_not_called()

    def test_post_install_sync_state_failure_is_only_a_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = sandbox / "repository"
            skills_dir = sandbox / "global-skills"
            repository_dir.mkdir()
            skills_dir.mkdir()
            with mock.patch.object(sync_global_skills, "repository_head", return_value="abc123"), mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("pull bookkeeping must not hash trees")) as hasher, mock.patch.object(sync_global_skills, "write_sync_state", side_effect=PermissionError("state locked")), mock.patch("builtins.print") as printer:
                recorded = sync_global_skills.record_pull_state("owner/repository", repository_dir, skills_dir)
            self.assertFalse(recorded)
            hasher.assert_not_called()
            printer.assert_called_once_with("Installation complete; sync state could not be recorded (PermissionError).")

    def test_render_readme_cli_uses_chinese_template_for_zh_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "README.zh.md"
            argv = ["sync_global_skills.py", "--skills-dir", str(SKILLS_DIR), "render-readme", "--output", str(output)]
            with mock.patch.object(sys, "argv", argv):
                sync_global_skills.main()
            self.assertEqual(output.read_text(encoding="utf-8"), sync_global_skills.build_readme(self.primary_skill_paths(), language="zh"))

    def test_deploy_installs_both_codex_and_host_discoverable_global_agents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"
            target_dir = home_dir / ".codex" / "skills"
            sync_global_skills.deploy(SKILLS_DIR, target_dir)
            expected = sync_global_skills.canonical_global_agents_text(SKILLS_DIR)
            targets = sync_global_skills.global_agents_targets(target_dir)
            self.assertEqual(targets, [(home_dir / ".codex" / "AGENTS.md").absolute(), (home_dir / "AGENTS.md").absolute()])
            self.assertEqual([target.read_text(encoding="utf-8") for target in targets], [expected, expected])
            parity = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
            self.assertEqual(parity["status"], "pass")
            self.assertEqual(parity["targets"], [str(target) for target in targets])

    def test_push_cli_defaults_to_the_maintained_repository_source(self):
        argv = ["sync_global_skills.py", "push", "--message", "source-first smoke"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "push") as publisher:
            sync_global_skills.main()
        publisher.assert_called_once_with(
            sync_global_skills.DEFAULT_REPOSITORY,
            sync_global_skills.DEFAULT_SOURCE_DIR,
            "source-first smoke",
            False,
            Path.home() / ".codex" / "skills",
        )

    def test_publishable_source_paths_exclude_unrelated_or_private_content(self):
        self.assertTrue(sync_global_skills.publishable_source_path(Path("verify-skill/SKILL.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path("AGENTS.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path("README.zh.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path(".github/workflows/ci.yml")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("notes.txt")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".github/workflows/other.yml")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("task-analyze-skill/local/private.json")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("verify-skill/auth.json")))

    def test_push_commits_the_source_repository_and_verifies_remote_head(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = sandbox / "source"
            remote_dir = sandbox / "remote.git"
            source_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(source_dir, SKILLS_DIR)
            (source_dir / "AGENTS.md").write_text((SKILLS_DIR / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
            sync_global_skills.run_command(["git", "init"], cwd=source_dir)
            sync_global_skills.run_command(["git", "branch", "-M", "master"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.name", "Source Publish Test"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.email", "source-publish@example.invalid"], cwd=source_dir)
            sync_global_skills.run_command(["git", "add", "-A"], cwd=source_dir)
            sync_global_skills.run_command(["git", "commit", "-m", "initial"], cwd=source_dir)
            sync_global_skills.run_command(["git", "init", "--bare", str(remote_dir)], cwd=sandbox)
            sync_global_skills.run_command(["git", "remote", "add", "origin", str(remote_dir)], cwd=source_dir)
            sync_global_skills.run_command(["git", "push", "-u", "origin", "master"], cwd=source_dir)
            skill_path = source_dir / "verify-skill" / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nSource-first publish smoke.\n", encoding="utf-8")
            previous_head = sync_global_skills.repository_head(source_dir)
            state_file = sandbox / "state.json"
            with mock.patch.object(sync_global_skills, "DEFAULT_STATE_FILE", state_file):
                sync_global_skills.push("fixture/repository", source_dir, "Publish source change", False)
            current_head = sync_global_skills.repository_head(source_dir)
            remote_head = sync_global_skills.remote_branch_head(source_dir, "master")
            self.assertNotEqual(previous_head, current_head)
            self.assertEqual(current_head, remote_head)
            self.assertEqual(sync_global_skills.run_command(["git", "status", "--short"], cwd=source_dir).stdout, "")
            self.assertTrue(state_file.is_file())

    def test_push_gate_failure_precedes_readme_index_commit_and_remote_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(source_dir, SKILLS_DIR)
            (source_dir / "AGENTS.md").write_text((SKILLS_DIR / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
            sync_global_skills.run_command(["git", "init"], cwd=source_dir)
            sync_global_skills.run_command(["git", "branch", "-M", "master"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.name", "Gate Test"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.email", "gate@example.invalid"], cwd=source_dir)
            sync_global_skills.run_command(["git", "add", "-A"], cwd=source_dir)
            sync_global_skills.run_command(["git", "commit", "-m", "initial"], cwd=source_dir)
            changed = source_dir / "verify-skill" / "SKILL.md"
            changed.write_text(changed.read_text(encoding="utf-8") + "\nGate candidate.\n", encoding="utf-8")
            before_readmes = [(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")]
            before_head = sync_global_skills.repository_head(source_dir)
            self.release_gate.side_effect = RuntimeError("full regression failed")
            with self.assertRaisesRegex(RuntimeError, "full regression failed"):
                sync_global_skills.push("fixture/repository", source_dir, "must not publish", False, Path(temp_dir) / "deployed")
            self.assertEqual([(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")], before_readmes)
            self.assertEqual(sync_global_skills.repository_head(source_dir), before_head)
            self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [])

    def test_installed_snapshot_cannot_bypass_source_first_publication(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "not a publication source"):
                sync_global_skills.push_global_snapshot("fixture/repository", Path(temp_dir), "forbidden", False)

    def test_deploy_always_replaces_matching_skills_without_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            sync_global_skills.deploy(SKILLS_DIR, target_dir)
            with mock.patch.object(sync_global_skills, "stage_skill_directory", wraps=sync_global_skills.stage_skill_directory) as stager, mock.patch.object(sync_global_skills, "path_differs", side_effect=AssertionError("install must not pre-diff")) as differ, mock.patch("builtins.print") as printer:
                changed_names = sync_global_skills.deploy(SKILLS_DIR, target_dir)
        self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
        self.assertEqual(stager.call_count, len(sync_global_skills.PRIMARY_SKILL_ORDER))
        differ.assert_not_called()
        printer.assert_any_call("Replaced managed repository Skills in the local global Skill directory:")
        printer.assert_any_call("Installation complete: consumer install/update replaced the published managed source without rerunning validation gates.")

    def test_global_agents_parity_detects_stale_always_loaded_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            sync_global_skills.deploy(SKILLS_DIR, target_dir)
            matching = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
            (target_dir.parent / "AGENTS.md").write_text("# stale\n", encoding="utf-8")
            stale = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
        self.assertEqual(matching["status"], "pass")
        self.assertEqual(stale["status"], "fail")
        self.assertIn("differs", stale["reason"])

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

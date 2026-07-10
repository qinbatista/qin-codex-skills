import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("sync_global_skills", MODULE_PATH)
sync_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(sync_global_skills)
SKILLS_DIR = Path(__file__).resolve().parents[2]
README_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "readme"


class SyncGlobalSkillsReadmeTest(unittest.TestCase):
    def primary_skill_paths(self):
        return [SKILLS_DIR / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]

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
        expected = template.replace(
            "<!-- EXECUTION_DOMAIN_TABLE -->",
            sync_global_skills.execution_domain_table(sync_global_skills.load_staged_routing_policy(self.primary_skill_paths())),
        )

        self.assertEqual(readme, expected)
        self.assertLessEqual(len(template.splitlines()), 230)
        self.assertLessEqual(len(template.split()), 1700)
        skills_section = readme.split("## 🧩 Six independent skills", 1)[1].split("\n## ", 1)[0]
        skill_rows = re.findall(r"^\| .*?\[`([^`]+)`\]\(\./([^/]+)/SKILL\.md\)", skills_section, re.M)
        expected_skill_rows = {"Task Analyze": "task-analyze-skill", "Workflow": "workflow-skill", "Code": "code-skill", "Verify": "verify-skill", "Optimization": "optimization-skill", "Management": "management-skill"}
        self.assertEqual(len(skill_rows), 6)
        self.assertEqual(dict(skill_rows), expected_skill_rows)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"./{skill_name}/SKILL.md", readme)

        visual_pairs = ("qin-codex-skills-hero", "task-lifecycle", "model-router", "runtime-receipt", "model-experience", "verification-topologies")
        svg_references = sum(readme.count(f"./management-skill/assets/readme/{asset_name}{suffix}.svg") for asset_name in visual_pairs for suffix in ("", "-mobile"))
        self.assertEqual(svg_references, 12)
        for asset_name in visual_pairs:
            self.assertEqual(readme.count(f"./management-skill/assets/readme/{asset_name}.svg"), 1)
            self.assertEqual(readme.count(f"./management-skill/assets/readme/{asset_name}-mobile.svg"), 1)

        self.assertIn("hookless, 100% entry", readme)
        self.assertIn("entry model and effort analyze and route only", readme)
        self.assertIn("First Result Principle", readme)
        self.assertIn("(#-hookless-first-result-principle)", readme)
        self.assertNotIn("(#-the-hookless-promise)", readme)
        self.assertIn("per-node `model | effort`", readme)
        self.assertIn("Downgrade exactly one eligible rung", readme)
        self.assertIn("effort first", readme)
        self.assertIn("upgrade in the exact reverse direction", readme)
        self.assertIn("reuse the calibrated/frozen pair", readme)
        self.assertIn("Static floors, safety, domain ownership, and correctness always win", readme)
        self.assertIn("may start at Spark-low; runtime failure uses the static fallback without a quality penalty", readme)
        self.assertIn("an exhausted top boundary returns no selected pair", readme)
        self.assertIn("sanitized runtime receipt", readme)
        self.assertIn("receipt-backed", readme)
        self.assertIn("like-for-like", readme)
        self.assertIn("private `local/model_experience.json` ledger is **condition-keyed**", readme)
        self.assertIn("success_model` / `failed_model`", readme)
        self.assertIn("neutral operational events", readme)
        self.assertIn("Mini Verify", readme)
        self.assertIn("Before the result", readme)
        self.assertIn("Real Verify runs in background Ending Task", readme)
        self.assertIn("a **different** [`verify-skill`](./verify-skill/SKILL.md) worker", readme)
        self.assertIn("One obvious reversible action with no dependency graph", readme)
        for example in ("Open Chrome", "Open YouTube", "Search CCTV on YouTube", "Design a YouTube-like website"):
            self.assertIn(example, readme)
        self.assertIn("generated table above is injected at the exact `EXECUTION_DOMAIN_TABLE` marker", readme)
        self.assertIn("publishes only after an explicit current request", readme)
        self.assertIn("exactly six public skills", readme)
        self.assertNotIn('"schema_version":', readme)
        self.assertNotIn('"conditions":', readme)
        self.assertNotIn('"producer":', readme)
        self.assertNotIn('"requested_pair":', readme)
        self.assertNotIn('"resolved_pair":', readme)
        self.assertNotIn('"effective_pair":', readme)
        self.assertNotIn("/Users/", readme)
        self.assertNotIn("hooks.json", readme)
        self.assertNotIn("TASK_ANALYZE_PLAN_JSON", readme)

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
            self.assertEqual(len(svg_references), 12)
            for reference in local_references:
                referenced_path = repository_dir / reference.removeprefix("./")
                self.assertTrue(referenced_path.exists(), f"Missing generated README reference: {reference}")

    def test_readme_svgs_are_parseable_accessible_and_self_contained(self):
        svg_paths = sorted(README_ASSET_DIR.glob("*.svg"))
        self.assertEqual(len(svg_paths), 12)

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

            (repository_dir / "task-analyze-skill" / "SKILL.md").write_text(
                (repository_dir / "task-analyze-skill" / "SKILL.md").read_text(encoding="utf-8") + "\nremote update\n",
                encoding="utf-8",
            )
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertEqual(private_model_experience.read_text(encoding="utf-8"), private_model_experience_payload)


if __name__ == "__main__":
    unittest.main()

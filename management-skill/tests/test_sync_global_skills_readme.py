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

    def test_english_readme_uses_durable_template_and_current_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        template = sync_global_skills.ENGLISH_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"

        self.assertEqual(readme, template)
        self.assertIn("## 🧩 The six independent skills", readme)
        self.assertIn("The model selected when the user starts the task runs Task Analyze and route coordination only", readme)
        self.assertIn("The local `task-analyze-skill/local/adaptive-routing/model_experience.json` ledger is condition-keyed", readme)
        self.assertIn("success_model", readme)
        self.assertIn("failed_model", readme)
        self.assertIn("requested_pair", readme)
        self.assertIn("resolved_pair", readme)
        self.assertIn("effective_pair", readme)
        self.assertIn("operational_failure_pairs", readme)
        self.assertNotIn('"producer":', readme)
        self.assertIn("exhausted top boundary returns no selected pair", readme)
        self.assertIn("effort-first", readme.lower())
        self.assertIn("schema_version", readme)
        self.assertIn("Spark-low", readme)
        self.assertIn("static", readme)
        self.assertIn("Easy tasks do not need a forced diagram", readme)
        self.assertIn("Mini Verify is the main-result gate", readme)
        self.assertIn("Real Verify runs in background Ending Task", readme)
        self.assertIn("First Result Principle", readme)
        self.assertIn("show the basically verified result immediately", readme)
        self.assertIn("never describe Mini Verify as exhaustive proof", readme)
        self.assertIn("weak-to-strong quality ladder", readme)
        self.assertIn("Downgrade exactly one eligible rung", readme)
        self.assertIn("correctness-first routing", readme)
        self.assertIn("Open Chrome", readme)
        self.assertIn("Open YouTube", readme)
        self.assertIn("Search CCTV on YouTube", readme)
        self.assertIn("Design a YouTube-like website", readme)
        self.assertIn("## 🧰 Extension recipe", readme)
        self.assertIn("execution_domain", readme)
        self.assertIn("reasonable response time and token use", readme)
        self.assertIn("exactly six public skills", readme)
        self.assertIn("a **different** `verify-skill` worker", readme)
        self.assertIn("Runtime receipts", readme)
        self.assertIn("hookless", readme)
        self.assertIn("task_route_dispatcher.py", readme)
        self.assertNotIn("hooks.json", readme)
        self.assertNotIn("Task Analyze is an internal phase", readme)
        self.assertNotIn("Real Verify always stays before", readme)
        self.assertNotIn("model_experience.json` ledger is mirrored", readme)
        self.assertNotIn("TASK_ANALYZE_PLAN_JSON", readme)
        self.assertNotIn("median token", readme.lower())
        self.assertNotIn("cheapest-to-strongest", readme.lower())
        self.assertNotIn("fastest reasonable", readme.lower())
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"./{skill_name}/SKILL.md", readme)

        model_experience_match = re.search(r"\{\n  \"schema_version\": 3,.*?\n\}", readme, re.S)
        self.assertIsNotNone(model_experience_match)
        model_experience_payload = json.loads(model_experience_match.group(0))
        self.assertEqual(model_experience_payload["schema_version"], 3)
        condition = model_experience_payload["conditions"]["799b5cc30bcb4d107e081f34c0e6dff164d70cb85dc99397ca7ebca18c907729"]["condition"]
        self.assertIn("execution_domain", condition)
        self.assertEqual(condition["execution_domain"], "general")
        self.assertNotIn("producer", model_experience_payload)
        self.assertIn("requested_pair", model_experience_payload["conditions"]["799b5cc30bcb4d107e081f34c0e6dff164d70cb85dc99397ca7ebca18c907729"]["tasks"][0])

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

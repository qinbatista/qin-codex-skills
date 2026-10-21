import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT / "management-skill" / "scripts" / "project_ai_index.py"
SPEC = importlib.util.spec_from_file_location("project_ai_index", SCRIPT)
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)
sys.path.insert(0, str(PROJECT / "code-skill" / "scripts"))
from hidden_process import hidden_process_options
from task_artifact_paths import resolve_task_artifact_root
from task_cache_cleanup import checkpoint


class ProjectAIIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("CODEX_PROJECT_CACHE_ROOT")
        cls.owned_run = not configured
        cls.output = Path(configured) if configured else resolve_task_artifact_root(PROJECT, "project-ai-index-tests", create=True)
        cls.output.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.owned_run:
            checkpoint(PROJECT, "project-ai-index-tests", phase="finish", current_run=cls.output, apply=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ai-index-", dir=self.output)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.project = self.base / "project"
        self.work = self.base / "work"
        self.project.mkdir()
        self.work.mkdir()
        environment = mock.patch.dict(os.environ, {"YOFA_TASK_ARTIFACT_ROOT": str(self.base / "artifacts")})
        environment.start()
        self.addCleanup(environment.stop)
        self.write("src/api.py", "def request():\n    return 'accepted'\n")
        self.write("assets/original.txt", "source asset\n")
        self.write("src/AGENTS.md", "Scoped source instructions must survive.\n")
        self.write("unrelated.txt", "uncommitted user work\n")

    def write(self, relative, content):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def manifest(self):
        prefix = INDEX.INDEX_DIRECTORY
        return {"schema_version": 1, "rules": {"repository": f"{prefix}/rules/repository.md", "structure": f"{prefix}/rules/structure.md", "verification": f"{prefix}/rules/verification.md"}, "modules": [{"id": "api", "summary": "Request handling", "document": f"{prefix}/modules/api.md", "sources": ["src/api.py"], "dependencies": [{"module": "assets", "reason": "Requests may refer to canonical assets."}]}, {"id": "assets", "summary": "Original asset ownership", "document": f"{prefix}/modules/assets.md", "sources": ["assets"], "dependencies": []}]}

    def plan(self):
        prefix = INDEX.INDEX_DIRECTORY
        contents = {"AGENTS.md": "# Project\nKeep original assets. Read [AI index](.agents/skills/ai-index/SKILL.md).\n", INDEX.SKILL_PATH: "---\nname: ai-index\ndescription: Route project work to its owning instructions.\n---\nRead [the index](index.json), then the selected module only.\n", INDEX.MANIFEST_PATH: json.dumps(self.manifest(), indent=2), f"{prefix}/rules/repository.md": "# Repository and assets\nPreserve unrelated changes and canonical assets.\n", f"{prefix}/rules/structure.md": "# Structure\nRequests belong in src; originals belong in assets.\n", f"{prefix}/rules/verification.md": "# Verification\nExercise the affected request and read its actual result.\n", f"{prefix}/modules/api.md": "# API\nRequest handler: src/api.py::request.\n", f"{prefix}/modules/assets.md": "# Assets\nUNRELATED_ASSET_DETAIL is scoped to asset tasks.\n"}
        return {"schema_version": 1, "project_root": str(self.project), "evidence": {"src/api.py": INDEX.file_hash(self.project / "src/api.py")}, "files": [{"path": relative, "expected_sha256": INDEX.file_hash(self.project / relative), "content": content} for relative, content in contents.items()]}

    def bootstrap(self):
        result = INDEX.apply_plan(self.project, self.plan(), self.work)
        self.assertEqual(result["status"], "complete", result)
        return result

    def cli(self, command, *arguments):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), command, "--project-root", str(self.project), *arguments], capture_output=True, text=True, timeout=30, check=False, **hidden_process_options())

    def test_real_cli_bootstrap_repeat_and_selected_route(self):
        first = self.cli("inspect", "--phase", "start")
        before = json.loads(first.stdout)
        self.assertEqual(first.returncode, 2)
        self.assertEqual(before["status"], "missing")
        self.assertIn("src/AGENTS.md", before["discovery"]["agents_files"])
        self.assertNotIn("def request", first.stdout)
        plan_path = self.work / "plan.json"
        plan_path.write_text(json.dumps(self.plan()), encoding="utf-8")
        applied = self.cli("apply", "--plan", str(plan_path), "--work-dir", str(self.work))
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        fresh = self.cli("check")
        self.assertEqual(json.loads(fresh.stdout)["status"], "ready")
        self.assertTrue(json.loads(fresh.stdout)["structural_check_only"])
        routed = self.cli("route", "--module", "api")
        route = json.loads(routed.stdout)
        self.assertEqual(route["sources"], ["src/api.py"])
        self.assertEqual(route["dependencies"][0]["module"], "assets")
        self.assertNotIn("UNRELATED_ASSET_DETAIL", routed.stdout)
        self.assertNotIn("content", route)
        timestamps = {record["path"]: (self.project / record["path"]).stat().st_mtime_ns for record in self.plan()["files"]}
        plan_path.write_text(json.dumps(self.plan()), encoding="utf-8")
        repeated = self.cli("apply", "--plan", str(plan_path), "--work-dir", str(self.work))
        self.assertEqual(json.loads(repeated.stdout)["status"], "unchanged")
        self.assertEqual(timestamps, {path: (self.project / path).stat().st_mtime_ns for path in timestamps})
        self.assertEqual((self.project / "src/AGENTS.md").read_text(), "Scoped source instructions must survive.\n")
        self.assertEqual((self.project / "unrelated.txt").read_text(), "uncommitted user work\n")
        self.assertFalse(list(self.work.glob("ai-index-recovery-*")))

    def test_existing_index_does_not_discover_the_whole_project(self):
        self.bootstrap()
        with mock.patch.object(INDEX, "bootstrap_inventory", side_effect=AssertionError("unexpected whole-tree discovery")):
            result = INDEX.check_project(self.project, "end", ["src/api.py", "new-module/worker.py"])
        self.assertEqual(result["affected_modules"], ["api"])
        self.assertEqual(result["unmapped_paths"], ["new-module/worker.py"])
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("src/", result["structure"])

    def test_changed_directory_source_maps_descendants_and_guidance_is_ignored(self):
        self.bootstrap()
        result = INDEX.check_project(self.project, "end", ["assets/new.png", "AGENTS.md", INDEX.SKILL_PATH])
        self.assertEqual(result["affected_modules"], ["assets"])
        self.assertEqual(result["unmapped_paths"], [])

    def test_user_intent_and_module_rename_reconcile_with_real_end_readback(self):
        self.bootstrap()
        self.write("src/jobs.py", "def submit():\n    return 'queued'\n")
        plan = self.plan()
        plan["evidence"]["src/jobs.py"] = INDEX.file_hash(self.project / "src/jobs.py")
        manifest = self.manifest()
        manifest["modules"][0].update({"id": "jobs", "summary": "Asynchronous submission", "document": f"{INDEX.INDEX_DIRECTORY}/modules/jobs.md", "sources": ["src/jobs.py"]})
        for record in plan["files"]:
            if record["path"] == INDEX.MANIFEST_PATH:
                record["content"] = json.dumps(manifest)
            if record["path"] == "AGENTS.md":
                record["content"] += "All task submissions return a job ID.\n"
            if record["path"].endswith("/modules/api.md"):
                record["content"] = None
        plan["files"].append({"path": f"{INDEX.INDEX_DIRECTORY}/modules/jobs.md", "expected_sha256": None, "content": "# Jobs\nSubmit jobs through src/jobs.py::submit.\n"})
        result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "complete", result)
        self.assertFalse((self.project / INDEX.INDEX_DIRECTORY / "modules/api.md").exists())
        self.assertEqual(INDEX.check_project(self.project, "end", ["src/jobs.py"])["affected_modules"], ["jobs"])
        self.assertEqual(INDEX.route_module(self.project, "api")["status"], "needs_review")
        self.assertIn("job ID", (self.project / "AGENTS.md").read_text())

    def test_dangling_sources_and_dependencies_are_reported(self):
        self.bootstrap()
        (self.project / "src/api.py").unlink()
        result = INDEX.check_project(self.project)
        self.assertEqual(result["status"], "needs_review")
        self.assertTrue(any("missing module source" in issue for issue in result["issues"]))
        manifest = self.manifest()
        manifest["modules"][0]["dependencies"][0]["module"] = "unknown"
        self.write(INDEX.MANIFEST_PATH, json.dumps(manifest))
        self.assertTrue(any("unknown or self dependency" in issue for issue in INDEX.check_project(self.project)["issues"]))

    def test_stale_source_and_guidance_preimage_do_not_mutate_any_target(self):
        for stale in ("source", "guidance"):
            with self.subTest(stale=stale):
                plan = self.plan()
                if stale == "source":
                    self.write("src/api.py", "changed source\n")
                else:
                    self.write("AGENTS.md", "concurrent user guidance\n")
                before = {record["path"]: INDEX.file_hash(self.project / record["path"]) for record in plan["files"]}
                result = INDEX.apply_plan(self.project, plan, self.work)
                self.assertEqual(result["status"], "pending")
                self.assertEqual(before, {path: INDEX.file_hash(self.project / path) for path in before})

    def test_invalid_candidate_is_rejected_before_any_write(self):
        plan = self.plan()
        next(record for record in plan["files"] if record["path"].endswith("/modules/api.md"))["content"] = "See [missing](absent.md)."
        result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "pending")
        self.assertIn("missing document link", result["reason"])
        self.assertFalse((self.project / "AGENTS.md").exists())

    def test_linked_subdocuments_are_checked_and_hashed_without_following_source_docs(self):
        self.bootstrap()
        detail = f"{INDEX.INDEX_DIRECTORY}/modules/request-details.md"
        self.write(detail, "# Request details\nSee [API](api.md) and [source](../../../../src/AGENTS.md).\n")
        self.write(f"{INDEX.INDEX_DIRECTORY}/modules/api.md", "# API\nRead [request details](request-details.md).\n")
        self.write("src/AGENTS.md", "Scoped source guide with [a source-only link](not-indexed.md).\n")
        checked = self.cli("inspect", "--phase", "end")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["guidance_hashes"][detail], INDEX.file_hash(self.project / detail))
        self.write(detail, "# Request details\nSee [missing](absent.md).\n")
        checked = self.cli("check")
        self.assertEqual(checked.returncode, 2)
        self.assertIn("missing document link", checked.stdout)

    def test_machine_local_links_cannot_enter_an_existing_project_index(self):
        self.bootstrap()
        original = (self.project / INDEX.INDEX_DIRECTORY / "modules/api.md").read_bytes()
        asset = self.project / "assets/original.txt"
        for link in (asset.as_uri(), asset.as_posix(), "C:/another-checkout/source.txt"):
            with self.subTest(link=link):
                plan = self.plan()
                next(record for record in plan["files"] if record["path"].endswith("/modules/api.md"))["content"] = f"# API\nRead [source](<{link}>).\n"
                result = INDEX.apply_plan(self.project, plan, self.work)
                self.assertEqual(result["status"], "pending", result)
                self.assertIn("project-relative", result["reason"])
                self.assertEqual((self.project / INDEX.INDEX_DIRECTORY / "modules/api.md").read_bytes(), original)

    def test_every_proposed_guidance_document_is_validated_before_bootstrap(self):
        plan = self.plan()
        extra = f"{INDEX.INDEX_DIRECTORY}/modules/extra.md"
        plan["files"].append({"path": extra, "expected_sha256": None, "content": "# Extra\nRead [missing](absent.md).\n"})
        result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "pending", result)
        self.assertIn("missing document link", result["reason"])
        self.assertFalse((self.project / "AGENTS.md").exists())
        self.assertFalse((self.project / extra).exists())

    def test_skill_requires_a_real_description_before_creation(self):
        plan = self.plan()
        skill = next(record for record in plan["files"] if record["path"] == INDEX.SKILL_PATH)
        skill["content"] = skill["content"].replace("description: Route project work to its owning instructions.", 'description: ""')
        result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "pending")
        self.assertIn("nonempty frontmatter description", result["reason"])
        self.assertFalse((self.project / "AGENTS.md").exists())

    def test_new_project_indexes_its_proposed_guidance_without_invented_code(self):
        empty = self.base / "empty-project"
        empty.mkdir()
        plan = self.plan()
        plan.update({"project_root": str(empty), "evidence": {}})
        manifest = self.manifest()
        manifest["modules"] = [{"id": "project", "summary": "Initial project scope", "document": f"{INDEX.INDEX_DIRECTORY}/modules/api.md", "sources": ["AGENTS.md"], "dependencies": []}]
        next(record for record in plan["files"] if record["path"] == INDEX.MANIFEST_PATH)["content"] = json.dumps(manifest)
        result = INDEX.apply_plan(empty, plan, self.work)
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(INDEX.route_module(empty, "project")["sources"], ["AGENTS.md"])
        self.assertFalse((empty / "src").exists())

    def test_replaying_bootstrap_preimages_is_pending_not_blindly_retried(self):
        plan = self.plan()
        self.assertEqual(INDEX.apply_plan(self.project, plan, self.work)["status"], "complete")
        result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "pending")
        self.assertIn("preimage changed", result["reason"])
        self.assertEqual(INDEX.check_project(self.project)["status"], "ready")

    def test_forbidden_targets_path_aliases_and_empty_content_are_rejected(self):
        for target in ("../outside.md", "src/api.py", "plugins/ai-index/SKILL.md", "src/AGENTS.md", f"{INDEX.INDEX_DIRECTORY}/AGENTS.md", f"{INDEX.INDEX_DIRECTORY}/../escape.md", "C:/AGENTS.md", ".agents\\skills\\ai-index\\SKILL.md"):
            with self.subTest(target=target):
                plan = self.plan()
                plan["files"].append({"path": target, "expected_sha256": None, "content": "prohibited"})
                self.assertEqual(INDEX.apply_plan(self.project, plan, self.work)["status"], "pending")
                self.assertFalse((self.project / "AGENTS.md").exists())
        plan = self.plan()
        plan["files"][0]["content"] = " "
        self.assertEqual(INDEX.apply_plan(self.project, plan, self.work)["status"], "pending")
        plan = self.plan()
        plan["files"].append({"path": f"{INDEX.INDEX_DIRECTORY}/modules/API.md", "expected_sha256": None, "content": "alias"})
        self.assertEqual(INDEX.apply_plan(self.project, plan, self.work)["status"], "pending")

    def test_symlink_target_and_symlink_project_are_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        try:
            (self.project / ".agents").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"host does not permit symlink creation: {error}")
        result = INDEX.apply_plan(self.project, self.plan(), self.work)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(list(outside.iterdir()), [])
        alias = self.base / "alias"
        alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            INDEX.check_project(alias)

    def test_cross_project_plan_and_project_local_recovery_are_rejected(self):
        plan = self.plan()
        plan["project_root"] = str(self.base / "other")
        self.assertEqual(INDEX.apply_plan(self.project, plan, self.work)["status"], "pending")
        with self.assertRaises(ValueError):
            INDEX.apply_plan(self.project, self.plan(), self.project / "Cache")

    def test_write_failure_rolls_back_and_releases_cooperative_lock(self):
        self.write("AGENTS.md", "old root instructions\n")
        plan = self.plan()
        writer = INDEX.write_guidance

        def fail_skill(target, content):
            if target == self.project / INDEX.SKILL_PATH:
                raise OSError("injected write failure")
            writer(target, content)

        with mock.patch.object(INDEX, "write_guidance", side_effect=fail_skill):
            result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["unresolved"], [])
        self.assertEqual((self.project / "AGENTS.md").read_text(), "old root instructions\n")
        self.assertFalse((self.project / ".agents").exists())
        self.assertFalse(list(self.base.glob("artifacts/*/ai-index.lock")))

    def test_rollback_preserves_newer_writer_and_retains_exact_recovery(self):
        self.write("AGENTS.md", "old root instructions\n")
        plan = self.plan()
        writer = INDEX.write_guidance

        def concurrent_failure(target, content):
            if target == self.project / INDEX.SKILL_PATH:
                (self.project / "AGENTS.md").write_text("newer user's edit\n", encoding="utf-8")
                raise OSError("injected failure after external edit")
            writer(target, content)

        with mock.patch.object(INDEX, "write_guidance", side_effect=concurrent_failure):
            result = INDEX.apply_plan(self.project, plan, self.work)
        self.assertEqual(result["unresolved"], ["AGENTS.md"])
        self.assertEqual((self.project / "AGENTS.md").read_text(), "newer user's edit\n")
        saved = json.loads(Path(result["recovery"]).read_text())
        self.assertEqual(saved["project_root"], str(self.project))

    def test_existing_lock_is_pending_without_breaking_another_writer(self):
        owner = INDEX.project_artifact_directory(self.project, create=True)
        lock = owner / "ai-index.lock"
        lock.write_text('{"token":"another-writer","pid":1}', encoding="utf-8")
        result = INDEX.apply_plan(self.project, self.plan(), self.work)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(json.loads(lock.read_text())["token"], "another-writer")
        self.assertFalse((self.project / "AGENTS.md").exists())

    def test_missing_index_inventory_prunes_generated_folders_and_nested_projects(self):
        self.write("data/generated/AGENTS.md", "not project guidance")
        self.write("vendor/package/AGENTS.md", "not project guidance")
        self.write("nested/.git/HEAD", "ref: refs/heads/main")
        self.write("nested/AGENTS.md", "independent project")
        result = INDEX.check_project(self.project)
        self.assertEqual(result["discovery"]["agents_files"], ["src/AGENTS.md"])
        self.assertNotIn("data/", result["structure"])

    def test_noncanonical_existing_skill_is_reviewed_without_replacement(self):
        self.write("AGENTS.md", "Keep current project guidance.\n")
        self.write(INDEX.SKILL_PATH, "Existing custom index without machine manifest.\n")
        before = (self.project / INDEX.SKILL_PATH).read_bytes()
        result = INDEX.check_project(self.project)
        self.assertEqual(result["status"], "needs_review")
        self.assertNotIn("discovery", result)
        self.assertEqual((self.project / INDEX.SKILL_PATH).read_bytes(), before)

    def test_large_root_advisory_never_erases_rules(self):
        self.bootstrap()
        source = (self.project / "AGENTS.md").read_text() + " preserve" * 900
        self.write("AGENTS.md", source)
        result = INDEX.check_project(self.project)
        self.assertTrue(any("AGENTS.md exceeds" in warning for warning in result["advisories"]))
        self.assertEqual((self.project / "AGENTS.md").read_text(), source)


if __name__ == "__main__":
    unittest.main()

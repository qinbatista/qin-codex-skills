import importlib.util
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


SKILLS_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ENTRY_RULE_PATH = SKILLS_ROOT / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
PROJECT_CACHE_POLICY_PATH = SKILLS_ROOT / "workflow-skill" / "references" / "project-cache-artifact-policy.md"
SYNC_SCRIPT_PATH = SKILLS_ROOT / "management-skill" / "scripts" / "sync_global_skills.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_global_skills", SYNC_SCRIPT_PATH)
SYNC = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(SYNC)
ARTIFACT_SCRIPT_PATH = SKILLS_ROOT / "workflow-skill" / "scripts" / "task_artifact_paths.py"
ARTIFACT_SPEC = importlib.util.spec_from_file_location("policy_task_artifact_paths", ARTIFACT_SCRIPT_PATH)
ARTIFACTS = importlib.util.module_from_spec(ARTIFACT_SPEC)
ARTIFACT_SPEC.loader.exec_module(ARTIFACTS)
PRIMARY_SKILLS = (
    "task-analyze-skill",
    "workflow-skill",
    "prompt-skill",
    "code-skill",
    "project-memory-skill",
    "verify-skill",
    "optimization-skill",
    "management-skill",
)
NATIVE_FIXTURE_CLEANUP = (sys.platform == "darwin" or sys.platform.startswith("linux")) and all(shutil.which(tool) for tool in ("lsof", "ps"))


@contextmanager
def external_fixture(task_name="external-policy-test", *, cache_root=None):
    configured = cache_root if cache_root is not None else os.environ.get("CODEX_PROJECT_CACHE_ROOT")
    if not configured and not NATIVE_FIXTURE_CLEANUP:
        raise RuntimeError("Fixture-owned runs need the supported native cleanup probe; supply an existing CODEX_PROJECT_CACHE_ROOT so its caller retains the outer lifecycle")
    task_id = f"{task_name}-{uuid.uuid4().hex}"
    task_root = None
    try:
        task_root = ARTIFACTS.validate_task_directory(configured, SKILLS_ROOT) if configured else ARTIFACTS.resolve_task_artifact_root(SKILLS_ROOT, task_id, create=True)
        if not task_root.is_dir():
            raise ValueError("The configured fixture owner must already exist")
        with tempfile.TemporaryDirectory(prefix="policy-", dir=task_root) as directory:
            yield Path(directory)
    finally:
        if not configured and task_root is not None:
            cleanup = ARTIFACTS.task_cache_cleanup
            result = cleanup.checkpoint(SKILLS_ROOT, task_id, phase="finish", current_run=task_root, apply=True, budget_seconds=5, requested_only=True)
            record = cleanup._registry(task_root.parent, SKILLS_ROOT) / "runs" / (cleanup._key(task_root) + ".json")
            if not result.get("requested_complete") or task_root.exists() or record.exists():
                own = [item for item in result["results"] if item.get("path") == str(task_root) or item.get("record") == str(record)]
                diagnostic = {key: str(value)[:600] for key, value in (own[0] if own else {"reason": "Exact owner not reached before checkpoint budget"}).items() if key in {"action", "reason", "path", "record"}}
                raise AssertionError(f"Fixture owner cleanup pending; root or registry still exists: {task_root}; {diagnostic}")


class ProjectCacheTestCase(unittest.TestCase):
    fixture_task_name = "skill-fixture-tests"

    def run(self, result=None):
        with external_fixture(self.fixture_task_name) as fixture:
            self.fixture_root = fixture
            try:
                return super().run(result)
            finally:
                # unittest skips doCleanups when KeyboardInterrupt escapes run().
                # Drain callbacks before this fixture's owning context closes.
                self.doCleanups()


class ProjectCacheArtifactPolicyTests(unittest.TestCase):
    def test_retired_native_store_cannot_be_reintroduced_as_a_project_owner(self):
        with external_fixture() as fixture:
            home = fixture / "home"
            configured = {"XDG_CACHE_HOME": str(home / "xdg-cache")}
            layouts = {
                "win32": home / "YoFaAI" / "TaskArtifacts",
                "darwin": home / "Library" / "Application Support" / "YoFaAI" / "TaskArtifacts",
                "linux": home / "xdg-cache" / "YoFaAI" / "TaskArtifacts",
            }
            for platform, base in layouts.items():
                for owner in (base, base / "p-old-owner"):
                    run = owner / "Cache" / f"temp-{'a' * 24}-{'b' * 32}"
                    run.mkdir(parents=True)
                    with self.subTest(platform=platform, owner=owner), mock.patch.object(ARTIFACTS.sys, "platform", platform), mock.patch.object(Path, "home", return_value=home):
                        self.assertEqual(ARTIFACTS.legacy_artifact_base(environ=configured), base)
                        self.assertEqual(ARTIFACTS.project_artifact_directory(owner, environ=configured), owner / "Cache")
                        resolved = ARTIFACTS.resolve_task_artifact_root(owner, "read-legacy", run_id="c" * 32, environ=configured)
                        self.assertEqual(resolved.parent, owner / "Cache")
                        with mock.patch.object(Path, "mkdir", side_effect=AssertionError("reject the retired owner before mkdir")), mock.patch.object(ARTIFACTS, "_ensure_cache_backup_exclusion") as exclusion, mock.patch.object(ARTIFACTS.task_cache_cleanup, "checkpoint") as checkpoint, mock.patch.object(ARTIFACTS.task_cache_cleanup, "register_run") as register:
                            with self.assertRaisesRegex(ValueError, "legacy task artifact stores are cleanup-only"):
                                ARTIFACTS.project_artifact_directory(owner, environ=configured, create=True)
                            with self.assertRaisesRegex(ValueError, "legacy task artifact stores are cleanup-only"):
                                ARTIFACTS.resolve_task_artifact_root(owner, "reject-new", environ=configured, create=True)
                            with self.assertRaisesRegex(ValueError, "legacy task artifact stores are cleanup-only"):
                                ARTIFACTS.task_artifact_environment(run, environ=configured, create=True)
                            exclusion.assert_not_called()
                            checkpoint.assert_not_called()
                            register.assert_not_called()
                        self.assertEqual(list(run.iterdir()), [])
            with mock.patch.object(ARTIFACTS.sys, "platform", "linux"), mock.patch.object(Path, "home", return_value=home):
                self.assertEqual(ARTIFACTS.legacy_artifact_base(environ={}), home / ".cache" / "YoFaAI" / "TaskArtifacts")

    def test_native_cli_rejects_retired_store_and_accepts_unrelated_same_name(self):
        with external_fixture() as fixture:
            home = fixture / "home"
            environment = dict(os.environ, XDG_CACHE_HOME=str(home / "xdg-cache"))
            with mock.patch.object(Path, "home", return_value=home):
                legacy = ARTIFACTS.legacy_artifact_base(environ=environment)
            legacy.mkdir(parents=True)
            task_id = "native-owner-allocation"
            launcher = "import runpy,sys\nfrom pathlib import Path\nfrom unittest import mock\nfixture_home,script=sys.argv[1:3]\nsys.argv=sys.argv[2:]\nwith mock.patch.object(Path,'home',return_value=Path(fixture_home)):\n    runpy.run_path(script,run_name='__main__')\n"
            command = [sys.executable, "-B", "-c", launcher, str(home), str(ARTIFACT_SCRIPT_PATH), "--task-id", task_id, "--create", "--project-root"]
            rejected = subprocess.run([*command, str(legacy)], capture_output=True, text=True, env=environment, check=False, **hidden_process_options())
            self.assertEqual(rejected.returncode, 2, rejected)
            self.assertIn("cleanup-only", json.loads(rejected.stderr)["reason"])
            self.assertEqual(json.loads(rejected.stderr)["cleanup"], "not_created")
            self.assertEqual(list(legacy.iterdir()), [])
            alias = legacy.with_name("tAsKaRtIfAcTs")
            if alias.is_dir():
                rejected_alias = subprocess.run([*command, str(alias)], capture_output=True, text=True, env=environment, check=False, **hidden_process_options())
                self.assertEqual(rejected_alias.returncode, 2, rejected_alias)
                self.assertIn("cleanup-only", json.loads(rejected_alias.stderr)["reason"])
                self.assertEqual(list(legacy.iterdir()), [])
            project = home / "projects" / "TaskArtifacts"
            project.mkdir(parents=True)
            created = subprocess.run([*command, str(project)], capture_output=True, text=True, env=environment, check=False, **hidden_process_options())
            self.assertEqual(created.returncode, 0, created)
            root = Path(json.loads(created.stdout)["task_root"])
            self.assertEqual(root.parent, project / "Cache")
            self.assertTrue((root / "tmp").is_dir())
            cleanup = ARTIFACTS.task_cache_cleanup.checkpoint(project, task_id, phase="finish", current_run=root, apply=True, requested_only=True)
            self.assertTrue(cleanup["requested_complete"], cleanup)
            self.assertFalse(root.exists())

    def test_time_machine_dispatch_and_verified_sticky_exclusion(self):
        with external_fixture() as fixture:
            cache = fixture / "Cache"
            cache.mkdir()
            for platform in ("win32", "linux"):
                with self.subTest(platform=platform), mock.patch.object(ARTIFACTS.sys, "platform", platform), mock.patch.object(ARTIFACTS.shutil, "which") as find, mock.patch.object(ARTIFACTS.subprocess, "run") as run:
                    ARTIFACTS._ensure_cache_backup_exclusion(cache)
                    find.assert_not_called()
                    run.assert_not_called()
            included = subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(cache), "IsExcluded": 0}]), b"")
            excluded = subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(cache), "IsExcluded": 1}]), b"")
            added = subprocess.CompletedProcess([], 0, b"", b"")
            for observations in ([excluded], [included, added, excluded]):
                with self.subTest(native_calls=len(observations)), mock.patch.object(ARTIFACTS.sys, "platform", "darwin"), mock.patch.object(ARTIFACTS.shutil, "which", return_value="native-tmutil"), mock.patch.object(ARTIFACTS.subprocess, "run", side_effect=observations) as run:
                    ARTIFACTS._ensure_cache_backup_exclusion(cache)
                    commands = [call.args[0][1:] for call in run.call_args_list]
                    expected = [["isexcluded", "-X", str(cache)]]
                    if len(observations) == 3:
                        expected.extend([["addexclusion", str(cache)], ["isexcluded", "-X", str(cache)]])
                    self.assertEqual(commands, expected)
                    self.assertTrue(all(call.kwargs["timeout"] == 10 and call.kwargs["capture_output"] for call in run.call_args_list))

    def test_time_machine_failures_and_changed_owner_reject_payload(self):
        with external_fixture() as fixture:
            cache, other = fixture / "Cache", fixture / "other"
            cache.mkdir()
            other.mkdir()
            included = subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(cache), "IsExcluded": 0}]), b"")
            added = subprocess.CompletedProcess([], 0, b"", b"")
            failures = {
                "query": [subprocess.CompletedProcess([], 1, b"", b"native read denied")],
                "plist": [subprocess.CompletedProcess([], 0, b"not a plist", b"")],
                "wrong-directory": [subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(other), "IsExcluded": 1}]), b"")],
                "unknown-status": [subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(cache), "IsExcluded": "1"}]), b"")],
                "add": [included, subprocess.CompletedProcess([], 1, b"", b"native add denied")],
                "readback": [included, added, included],
                "timeout": subprocess.TimeoutExpired("tmutil", 10),
                "launch": OSError("native launch denied"),
            }
            for reason, observations in failures.items():
                with self.subTest(reason=reason), mock.patch.object(ARTIFACTS.sys, "platform", "darwin"), mock.patch.object(ARTIFACTS.shutil, "which", return_value="native-tmutil"), mock.patch.object(ARTIFACTS.subprocess, "run", side_effect=observations):
                    with self.assertRaisesRegex(ValueError, "Time Machine exclusion could not be verified"):
                        ARTIFACTS._ensure_cache_backup_exclusion(cache)
            with mock.patch.object(ARTIFACTS.sys, "platform", "darwin"), mock.patch.object(ARTIFACTS.shutil, "which", return_value=None), mock.patch.object(ARTIFACTS.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "tmutil was not found"):
                    ARTIFACTS._ensure_cache_backup_exclusion(cache)
                run.assert_not_called()

            def replace_cache(*args, **kwargs):
                cache.rename(fixture / "original-cache")
                cache.mkdir()
                return subprocess.CompletedProcess([], 0, plistlib.dumps([{"Path": str(cache), "IsExcluded": 1}]), b"")

            with mock.patch.object(ARTIFACTS.sys, "platform", "darwin"), mock.patch.object(ARTIFACTS.shutil, "which", return_value="native-tmutil"), mock.patch.object(ARTIFACTS.subprocess, "run", side_effect=replace_cache):
                with self.assertRaisesRegex(ValueError, "unchanged Cache"):
                    ARTIFACTS._ensure_cache_backup_exclusion(cache)

            project = fixture / "project"
            project.mkdir()
            with mock.patch.object(ARTIFACTS, "_ensure_cache_backup_exclusion", side_effect=ValueError("native exclusion unavailable")), mock.patch.object(ARTIFACTS.task_cache_cleanup, "checkpoint") as checkpoint:
                with self.assertRaisesRegex(ValueError, "native exclusion unavailable"):
                    ARTIFACTS.resolve_task_artifact_root(project, "blocked-before-payload", create=True)
                checkpoint.assert_not_called()
                self.assertEqual(list((project / "Cache").iterdir()), [])

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("tmutil"), "Native Time Machine acceptance requires macOS tmutil")
    def test_native_time_machine_exclusion_survives_cache_recreation(self):
        with external_fixture() as fixture:
            project = fixture / "native-project"
            project.mkdir()
            lower = project / "cache"
            lower.mkdir()
            if not (project / "Cache").exists():
                lower.rmdir()
            for attempt in range(2):
                cache = ARTIFACTS.project_artifact_directory(project, create=True)
                probe = subprocess.run([shutil.which("tmutil"), "isexcluded", "-X", str(cache)], capture_output=True, timeout=10, check=True, **hidden_process_options())
                record = plistlib.loads(probe.stdout)[0]
                self.assertEqual(record["IsExcluded"], 1)
                self.assertTrue(Path(record["Path"]).samefile(cache))
                self.assertEqual(list(cache.iterdir()), [])
                if attempt == 0:
                    cache.rmdir()

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Native fixture owner closure requires lsof/ps on macOS/Linux")
    def test_fixture_owner_closes_after_success_setup_failure_timeout_and_cancel(self):
        observed = []
        cleanup_observations = []

        class FixtureCase(ProjectCacheTestCase):
            fixture_task_name = "fixture-owner-lifecycle-contract"
            outcome = "success"

            def setUp(self):
                observed.append(self.fixture_root.parent)
                marker = self.fixture_root / "active.txt"
                marker.write_bytes(b"active until actual teardown")
                self.addCleanup(lambda: cleanup_observations.append(marker.read_bytes()))
                if self.outcome == "setup-failure":
                    raise RuntimeError("actual setUp failure")

            def runTest(self):
                if self.outcome == "body-failure":
                    self.fail("actual test body failure")
                if self.outcome == "timeout":
                    subprocess.run([sys.executable, "-B", "-c", "import time; time.sleep(5)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=.1, check=True, **hidden_process_options())
                if self.outcome == "cancel":
                    raise KeyboardInterrupt("cooperative test cancellation")
                self.assertEqual((self.fixture_root / "active.txt").read_bytes(), b"active until actual teardown")

            def tearDown(self):
                self.assertTrue((self.fixture_root / "active.txt").is_file())

        with mock.patch.dict(os.environ):
            os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            for outcome in ("success", "setup-failure", "body-failure", "timeout", "cancel"):
                with self.subTest(outcome=outcome):
                    case = FixtureCase()
                    case.outcome = outcome
                    result = unittest.TestResult()
                    if outcome == "cancel":
                        with self.assertRaises(KeyboardInterrupt):
                            case.run(result)
                    else:
                        case.run(result)
                        self.assertEqual(len(result.errors), 0 if outcome in {"success", "body-failure"} else 1, result.errors)
                        self.assertEqual(len(result.failures), 1 if outcome == "body-failure" else 0, result.failures)
                    root = observed[-1]
                    cleanup = ARTIFACTS.task_cache_cleanup
                    record = cleanup._registry(root.parent, SKILLS_ROOT) / "runs" / (cleanup._key(root) + ".json")
                    self.assertFalse(root.exists())
                    self.assertFalse(record.exists())
        self.assertEqual(cleanup_observations, [b"active until actual teardown"] * 5)

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Native fixture concurrency acceptance requires lsof/ps on macOS/Linux")
    def test_fixture_borrowed_owner_and_concurrent_runs_remain_independent(self):
        with external_fixture() as fixture:
            caller = fixture.parent
            marker = fixture / "caller-owned.txt"
            marker.write_bytes(b"keep caller owner")
            cleanup = ARTIFACTS.task_cache_cleanup
            record = cleanup._registry(SKILLS_ROOT / "Cache", SKILLS_ROOT) / "runs" / (cleanup._key(caller) + ".json")
            before = record.read_bytes() if record.exists() else None
            with external_fixture(cache_root=caller) as borrowed:
                (borrowed / "fixture.txt").write_bytes(b"borrowed scratch")
            self.assertFalse(borrowed.exists())
            self.assertTrue(caller.is_dir())
            self.assertEqual(marker.read_bytes(), b"keep caller owner")
            self.assertEqual(record.read_bytes() if record.exists() else None, before)

        ready = threading.Barrier(3, timeout=45)
        released = threading.Event()
        finished = threading.Event()
        paths, failures = {}, []

        def worker(index):
            try:
                with external_fixture("concurrent-fixture-contract") as fixture:
                    paths[index] = fixture
                    (fixture / ".codex-task-resource-ledger.json").write_text("intentional active fixture owner", encoding="utf-8")
                    ready.wait()
                    if index == 1 and not released.wait(45):
                        raise TimeoutError("Concurrent fixture test did not release its owner")
            except BaseException as error:
                failures.append(error)
            finally:
                if index == 0:
                    finished.set()

        with mock.patch.dict(os.environ):
            os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            threads = [threading.Thread(target=worker, args=(index,)) for index in range(2)]
            for thread in threads:
                thread.start()
            try:
                ready.wait()
                self.assertTrue(finished.wait(45))
                self.assertEqual(failures, [])
                self.assertFalse(paths[0].parent.exists())
                self.assertTrue(paths[1].is_dir())
                self.assertTrue((paths[1] / ".codex-task-resource-ledger.json").exists())
                cleanup = ARTIFACTS.task_cache_cleanup
                record = cleanup._registry(paths[1].parent.parent, SKILLS_ROOT) / "runs" / (cleanup._key(paths[1].parent) + ".json")
                self.assertEqual(json.loads(record.read_text())["state"], "working")
            finally:
                released.set()
                for thread in threads:
                    thread.join(45)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(failures, [])
            self.assertTrue(all(not fixture.parent.exists() for fixture in paths.values()))

    def test_canonical_policy_requires_project_cache_first_write_and_owner_preservation(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        required_rules = (
            "owning project's ignored `Cache/temp-<task>/` from their first write",
            "task_artifact_paths.py",
            "TMP`, `TEMP` and `TMPDIR",
            "Reject links and reparse paths",
            "canonical asset originals/history",
            "versioned non-runtime tests",
            "requested final deliverables",
            "Do not blanket move a project's Cache",
            "creation history, file identity and current consumer checks",
            "preserve bytes/hashes",
            "never a way to bypass a rejected deletion",
            "git diff --cached --name-status",
            "Temporary files never enter Git",
            "configured Obsidian vault",
        )
        for required in required_rules:
            with self.subTest(rule=required):
                self.assertIn(required, text)
        self.assertNotIn("outside every project directory and Codex-managed storage", text)

    def test_all_managed_entries_link_the_single_cache_policy_before_support_writes(self):
        for skill in PRIMARY_SKILLS:
            text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("project-cache-artifact-policy.md", text)
                self.assertIn("first write", text)
                self.assertIn("Cache", text)

    def test_installable_entry_preserves_global_agents_and_requires_project_cache(self):
        text = GLOBAL_ENTRY_RULE_PATH.read_text(encoding="utf-8")
        for required in (
            "deploy, pull, and sync preserve user AGENTS.md files",
            "owning project's ignored Cache/temp-<task>/",
            "from their first write",
            "fresh task run for each execution",
            "child TMP/TEMP/TMPDIR",
            "actual runtime or asset owners",
            "temporary files never enter Git",
            "minimum recovery inputs/state",
            "preserve unrelated work",
        ):
            with self.subTest(rule=required):
                self.assertIn(required, text)
        self.assertNotIn("outside every project directory and Codex-managed storage", text)

    @unittest.skipUnless(
        os.environ.get("VERIFY_INSTALLED_GLOBAL_SKILLS") == "1",
        "installed Skill policy is checked after deployment; user AGENTS is preserved",
    )
    def test_installed_skill_entries_have_the_same_external_contract(self):
        installed_root = Path.home() / ".agents" / "skills"
        for skill in PRIMARY_SKILLS:
            expected = (SKILLS_ROOT / skill / "SKILL.md").read_bytes()
            actual = (installed_root / skill / "SKILL.md").read_bytes()
            with self.subTest(skill=skill):
                self.assertEqual(actual, expected)

    def test_resource_cleanup_is_exact_and_preserves_review_recovery_and_other_tasks(self):
        text = (SKILLS_ROOT / "workflow-skill/references/task-resource-lifecycle.md").read_text(encoding="utf-8")
        for required in (
            "project Cache artifact policy",
            "project Cache ledgers remain bound",
            "fresh process or website request",
            "minimum inputs and resumable state",
            "never authorizes indefinite temp retention",
            "bounds-check every deletion target",
            "no unknown files remain",
            "never controls, interrupts, archives, or deletes another",
        ):
            self.assertIn(required, text)
        self.assertNotIn("`Cache/temp-<task>/` scratch", text)
        owners = (
            SKILLS_ROOT / "AGENTS.md",
            SKILLS_ROOT / "workflow-skill/SKILL.md",
            SKILLS_ROOT / "verify-skill/SKILL.md",
            SKILLS_ROOT / "management-skill/SKILL.md",
            GLOBAL_ENTRY_RULE_PATH,
            PROJECT_CACHE_POLICY_PATH,
        )
        for path in owners:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("owner", text)
                self.assertIn("recovery", text)
                self.assertRegex(text, r"review.{0,20}reuse")

    def test_test_and_private_fixture_registry_placement_keeps_source_independent(self):
        text = PROJECT_CACHE_POLICY_PATH.read_text(encoding="utf-8")
        for required in (
            "Remove obsolete and duplicate cases",
            "versioned, non-runtime development area",
            "execute the affected test from its final location",
            "private non-memory registry in a declared external AI resource owner",
            '"schema_version": 2',
            '"scope": "ai_only"',
            "Project source, runtime, tests, package scripts, build, CI, and shipped configuration must never read this registry",
            "compact structural contract, not a project notebook",
        ):
            self.assertIn(required, text)
        self.assertNotIn("Cache/remote-ai-paths/registry.json", text)

    def test_public_readmes_inherit_the_maintained_external_policy(self):
        with external_fixture() as fixture:
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(fixture)}):
                with SYNC.temporary_workspace("readme-policy-") as workspace:
                    SYNC.render_source_readmes(workspace, [SKILLS_ROOT / name for name in PRIMARY_SKILLS])
                    for suffix in ("", ".zh"):
                        template = SKILLS_ROOT / "management-skill/assets/readme" / f"github-readme-template{suffix}.md"
                        rule = next(
                            line for line in template.read_text(encoding="utf-8").splitlines()
                            if "Cache/temp-<task>/" in line
                        )
                        with self.subTest(language=suffix or "en"):
                            published = (workspace / f"README{suffix}.md").read_text(encoding="utf-8")
                            self.assertIn(rule, published)
                            self.assertIn("Cache/temp-<task>/", rule)
                self.assertFalse(workspace.exists())

    def test_resolved_projects_and_tasks_are_isolated_and_preserve_canonical_cache(self):
        with external_fixture() as fixture:
            project_one = fixture / "one" / "game"
            project_two = fixture / "two" / "game"
            project_one.mkdir(parents=True)
            project_two.mkdir(parents=True)
            original = project_one / "Cache" / "remote-assets" / "original.bin"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"canonical asset bytes")
            roots = (
                ARTIFACTS.resolve_task_artifact_root(project_one, "same-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_two, "same-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_one, "other-task", create=True),
                ARTIFACTS.resolve_task_artifact_root(project_one, "same-task", create=True),
            )
            self.assertEqual(len(set(roots)), 4)
            for root, owner in zip(roots, (project_one, project_two, project_one, project_one)):
                self.assertEqual(root.parent, owner / "Cache")
            environment = ARTIFACTS.task_artifact_environment(roots[0], create=True)
            for name in ("TMP", "TEMP", "TMPDIR"):
                self.assertEqual(Path(environment[name]), roots[0] / "tmp")
            self.assertEqual(original.read_bytes(), b"canonical asset bytes")
            self.assertEqual(list(project_one.iterdir()), [project_one / "Cache"])

    def test_continuation_copies_selected_bytes_without_links_overwrites_or_old_builds(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            base = project / "Cache"
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", artifact_root=base, create=True)
            following = ARTIFACTS.resolve_task_artifact_root(project, "chat", artifact_root=base, create=True)
            (previous / "input.bin").write_bytes(b"useful input")
            (previous / "build.bin").write_bytes(b"discard build output")
            receipts = ARTIFACTS.copy_run_inputs(project, previous, following, ["input.bin"])
            self.assertEqual((following / "input.bin").read_bytes(), b"useful input")
            self.assertEqual(receipts, [{"path": "input.bin", "sha256": ARTIFACTS._file_sha256(previous / "input.bin")}])
            self.assertFalse((following / "build.bin").exists())
            for selection in (["../build.bin"], ["input.bin"], ["input.bin", "input.bin"]):
                with self.subTest(selection=selection), self.assertRaises(ValueError):
                    ARTIFACTS.copy_run_inputs(project, previous, following, selection)
            with self.assertRaises(ValueError):
                ARTIFACTS.copy_run_inputs(project, previous, previous, ["input.bin"])
            link = previous / "linked.bin"
            try:
                link.symlink_to(previous / "build.bin")
            except OSError:
                return
            with self.assertRaises(ValueError):
                ARTIFACTS.copy_run_inputs(project, previous, following, ["linked.bin"])
            self.assertFalse((following / "linked.bin").exists())

    def test_cli_continuation_allocates_fresh_run_for_same_chat(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            command = [sys.executable, "-B", str(ARTIFACT_SCRIPT_PATH), "--project-root", str(project), "--task-id", "same-chat", "--create"]
            previous = json.loads(subprocess.run(command, capture_output=True, text=True, check=True, **hidden_process_options()).stdout)
            source = Path(previous["task_root"])
            (source / "fixture.bin").write_bytes(b"continued test input")
            following = json.loads(subprocess.run([*command, "--copy-from", str(source), "--input", "fixture.bin"], capture_output=True, text=True, check=True, **hidden_process_options()).stdout)
            destination = Path(following["task_root"])
            self.assertNotEqual(source, destination)
            self.assertNotEqual(previous["run_id"], following["run_id"])
            self.assertEqual((destination / "fixture.bin").read_bytes(), b"continued test input")
            self.assertEqual(following["temporary_environment"]["TMPDIR"], str(destination / "tmp"))

    def test_failed_cli_copy_removes_new_run_and_keeps_original_inputs(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            (previous / "input.bin").write_bytes(b"keep original input")
            command = [sys.executable, "-B", str(ARTIFACT_SCRIPT_PATH), "--project-root", str(project), "--task-id", "chat", "--create", "--copy-from", str(previous), "--input", "missing.bin"]
            result = subprocess.run(command, capture_output=True, text=True, check=False, **hidden_process_options())
            self.assertEqual(result.returncode, 2)
            failure = json.loads(result.stderr)
            self.assertEqual(failure["cleanup"], "removed")
            self.assertFalse(Path(failure["task_root"]).exists())
            self.assertNotEqual(Path(failure["task_root"]), previous)
            self.assertEqual((previous / "input.bin").read_bytes(), b"keep original input")

    def test_partial_copy_error_rolls_back_only_newly_created_files(self):
        with external_fixture() as fixture:
            project = fixture / "project"
            project.mkdir()
            previous = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            following = ARTIFACTS.resolve_task_artifact_root(project, "chat", create=True)
            (previous / "input.bin").write_bytes(b"keep original")
            sentinel = following / "other.bin"
            sentinel.write_bytes(b"keep unrelated destination")
            def partial_failure(reader, writer):
                writer.write(reader.read(4))
                raise OSError("injected write failure")
            with mock.patch.object(ARTIFACTS.shutil, "copyfileobj", side_effect=partial_failure), self.assertRaises(OSError):
                ARTIFACTS.copy_run_inputs(project, previous, following, ["input.bin"])
            self.assertEqual(list(following.iterdir()), [sentinel])
            self.assertEqual(sentinel.read_bytes(), b"keep unrelated destination")
            self.assertEqual((previous / "input.bin").read_bytes(), b"keep original")

    def test_management_workspace_cleanup_is_scoped_and_keeps_adjacent_resources(self):
        with external_fixture() as fixture:
            retained = fixture / "retained.bin"
            retained.write_bytes(b"keep for user review")
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(fixture)}):
                with SYNC.temporary_workspace("mirror-") as workspace:
                    marker = workspace / "marker.txt"
                    marker.write_text("external support\n", encoding="utf-8")
                    self.assertEqual(workspace.parent, fixture)
                    self.assertTrue(workspace.is_relative_to(SKILLS_ROOT / "Cache"))
                    self.assertEqual(marker.read_text(encoding="utf-8"), "external support\n")
                self.assertFalse(workspace.exists())
                self.assertEqual(retained.read_bytes(), b"keep for user review")

    def test_invalid_management_paths_fail_before_any_scratch_write(self):
        invalid_paths = (
            SKILLS_ROOT / "management-skill",
            Path.home() / ".codex" / "policy-test",
            Path("relative-scratch"),
            Path("%SystemDrive%") / "policy-test",
        )
        for invalid in invalid_paths:
            with self.subTest(invalid=invalid):
                with mock.patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(invalid)}):
                    with mock.patch.object(Path, "mkdir", side_effect=AssertionError("invalid scratch must fail before writing")):
                        with self.assertRaises(ValueError):
                            with SYNC.temporary_workspace("rejected-"):
                                self.fail("invalid scratch was accepted")

    def test_management_default_state_and_support_are_in_project_cache(self):
        self.assertEqual(SYNC.DEFAULT_SOURCE_DIR, SYNC_SCRIPT_PATH.resolve().parents[2])
        self.assertEqual(SYNC.DEFAULT_PROJECT_ROOT, Path.cwd().resolve())
        expected_root = ARTIFACTS.resolve_task_artifact_root(SYNC.DEFAULT_PROJECT_ROOT, "management-skill-sync", run_id=ARTIFACTS.task_artifact_run_id(SYNC.DEFAULT_CACHE_ROOT))
        self.assertEqual(SYNC.DEFAULT_CACHE_ROOT, expected_root)
        self.assertEqual(SYNC.DEFAULT_STATE_FILE, expected_root / "state" / "management-skill-sync.json")
        self.assertEqual(expected_root.parent, SYNC.DEFAULT_PROJECT_ROOT / "Cache")


if __name__ == "__main__":
    unittest.main()

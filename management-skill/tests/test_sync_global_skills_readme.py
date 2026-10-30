import importlib.util
import contextlib
import io
import json
import re
import sys
import tempfile
import threading
import time
import unittest
import unicodedata
import xml.etree.ElementTree as ElementTree
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("sync_global_skills", MODULE_PATH)
sync_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(sync_global_skills)
REAL_RUN_RELEASE_GATE = sync_global_skills.run_release_gate
SKILLS_DIR = Path(__file__).resolve().parents[2]
README_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "readme"



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
        self.codex_sandbox = tempfile.TemporaryDirectory()
        self.addCleanup(self.codex_sandbox.cleanup)
        self.codex_root = Path(self.codex_sandbox.name) / "custom-codex-home"
        codex_environment = mock.patch.dict(sync_global_skills.os.environ, {"CODEX_HOME": str(self.codex_root)})
        codex_environment.start()
        self.addCleanup(codex_environment.stop)
        self.release_gate_patcher = mock.patch.object(sync_global_skills, "run_release_gate")
        self.release_gate = self.release_gate_patcher.start()
        self.addCleanup(self.release_gate_patcher.stop)

    def primary_skill_paths(self):
        return [SKILLS_DIR / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]

    def windows_acl_state(self, paths):
        powershell = sync_global_skills.shutil.which("powershell.exe")
        self.assertIsNotNone(powershell, "Native Windows ACL verification requires PowerShell")
        command = (
            "$ErrorActionPreference = 'Stop'; [Console]::OutputEncoding = [Text.UTF8Encoding]::new(); "
            "$paths = ConvertFrom-Json ([Console]::In.ReadToEnd()); "
            "$states = @(foreach ($path in $paths) { "
            "$acl = if ([IO.Directory]::Exists($path)) { [IO.Directory]::GetAccessControl($path) } "
            "else { [IO.File]::GetAccessControl($path) }; "
            "$readRules = @($acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]) | "
            "Where-Object { $_.IdentityReference.Value -eq 'S-1-5-11' -and $_.IsInherited -and "
            "$_.AccessControlType -eq 'Allow' -and "
            "($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::ReadAndExecute) -eq "
            "[Security.AccessControl.FileSystemRights]::ReadAndExecute }); "
            "[pscustomobject]@{ Path = $path; "
            "Sddl = $acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access); "
            "Protected = $acl.AreAccessRulesProtected; "
            "InheritedRead = [bool]$readRules.Count } }); ConvertTo-Json -InputObject $states -Compress"
        )
        result = sync_global_skills.subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
            input=json.dumps([str(path) for path in paths]), capture_output=True,
            text=True, encoding="utf-8", check=False, timeout=60,
            **sync_global_skills.hidden_process_options(),
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return {state["Path"]: state for state in json.loads(result.stdout)}

    def windows_icacls(self, path, *options):
        executable = sync_global_skills.shutil.which("icacls")
        self.assertIsNotNone(executable, "Native Windows ACL verification requires icacls")
        return sync_global_skills.subprocess.run([executable, str(path), *options], capture_output=True, text=True, check=True, timeout=60, **sync_global_skills.hidden_process_options())

    def test_default_runtime_state_stays_in_project_cache(self):
        self.assertEqual(sync_global_skills.DEFAULT_PROJECT_ROOT, Path.cwd().resolve())
        self.assertEqual(
            sync_global_skills.DEFAULT_STATE_FILE,
            sync_global_skills.DEFAULT_CACHE_ROOT / "state" / "management-skill-sync.json",
        )
        self.assertEqual(sync_global_skills.DEFAULT_CACHE_ROOT.parent, sync_global_skills.DEFAULT_PROJECT_ROOT / "Cache")
        self.assertFalse(sync_global_skills.DEFAULT_CACHE_ROOT.is_relative_to(Path.home() / ".codex"))
        run_id = sync_global_skills.DEFAULT_CACHE_ROOT.name.rsplit("-", 1)[1]
        self.assertEqual(sync_global_skills.DEFAULT_CACHE_ROOT, sync_global_skills.resolve_task_artifact_root(sync_global_skills.DEFAULT_PROJECT_ROOT, "management-skill-sync", run_id=run_id))
        self.assertNotEqual(sync_global_skills.DEFAULT_CACHE_ROOT, sync_global_skills.resolve_task_artifact_root(sync_global_skills.DEFAULT_PROJECT_ROOT, "management-skill-sync"))
        with mock.patch.dict(sync_global_skills.os.environ):
            sync_global_skills.os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            self.assertEqual(sync_global_skills.sync_state_file(), sync_global_skills.DEFAULT_STATE_FILE)
            self.assertEqual(sync_global_skills.sync_state_file(), sync_global_skills.sync_state_file())

    def test_completed_workspace_run_is_removed_while_next_run_is_active(self):
        artifact_base = Path(self.codex_sandbox.name) / "external-runs"
        with mock.patch.dict(sync_global_skills.os.environ, {"YOFA_TASK_ARTIFACT_ROOT": str(artifact_base)}):
            sync_global_skills.os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            with ExitStack() as first_run, ExitStack() as second_run:
                first = first_run.enter_context(sync_global_skills.temporary_workspace("installer-"))
                second = second_run.enter_context(sync_global_skills.temporary_workspace("installer-"))
                second_marker = second / "active.bin"
                second_marker.write_bytes(b"second run remains active")
                self.assertNotEqual(first.parent, second.parent)
                self.assertEqual(first.parent.parent, second.parent.parent)
                self.assertRegex(first.parent.name, r"^temp-[0-9a-f]{24}-[0-9a-f]{32}$")
                self.assertRegex(second.parent.name, r"^temp-[0-9a-f]{24}-[0-9a-f]{32}$")
                first_run.close()
                self.assertFalse(first.exists())
                self.assertFalse(first.parent.exists())
                self.assertEqual(second_marker.read_bytes(), b"second run remains active")
            self.assertFalse(second.exists())
            self.assertFalse(second.parent.exists())
            self.assertTrue(second.parent.parent.is_dir())

    def test_workspace_error_removes_its_owned_run(self):
        artifact_base = Path(self.codex_sandbox.name) / "failed-run"
        with mock.patch.dict(sync_global_skills.os.environ, {"YOFA_TASK_ARTIFACT_ROOT": str(artifact_base)}):
            sync_global_skills.os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            with self.assertRaisesRegex(RuntimeError, "expected installer failure"):
                with sync_global_skills.temporary_workspace("installer-") as workspace:
                    (workspace / "partial.bin").write_bytes(b"discard failed support")
                    raise RuntimeError("expected installer failure")
            self.assertFalse(workspace.exists())
            self.assertFalse(workspace.parent.exists())
            cleanup = sys.modules["task_cache_cleanup"]
            record = workspace.parent.parent / cleanup.REGISTRY / "runs" / (cleanup._key(workspace.parent) + ".json")
            self.assertFalse(record.exists())

    def test_candidate_gate_rebinds_inherited_cache_and_closes_success_and_failure(self):
        project = Path(self.codex_sandbox.name) / "publication-project"
        gate = project / "management-skill" / "scripts" / "global_skill_regression_gate.py"
        gate.parent.mkdir(parents=True)
        code = "import os; from pathlib import Path; p=Path(os.environ['CODEX_PROJECT_CACHE_ROOT']); assert p.parent==Path.cwd()/'Cache'; assert all(Path(os.environ[k])==p/'tmp' for k in ('TMP','TEMP','TMPDIR')); (p/'tmp'/'payload').write_bytes(b'owned candidate support'); print('candidate checked')\n"
        for failure in (False, True):
            diagnostic = "import json; q=p/'global-skill-regression'; q.mkdir(); (q/'latest.json').write_text(json.dumps({'checks':[{'status':'fail','errors':['deliberate child diagnostic']}]})); raise SystemExit(3)\n"
            gate.write_text(code + (diagnostic if failure else ""))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                if failure:
                    with self.assertRaisesRegex(RuntimeError, "regression gate failed"):
                        REAL_RUN_RELEASE_GATE(project, project / "installed", "release")
                else:
                    self.assertEqual(REAL_RUN_RELEASE_GATE(project, project / "installed", "release").returncode, 0)
            if failure:
                self.assertIn("deliberate child diagnostic", output.getvalue())
            self.assertEqual(list((project / "Cache").glob("temp-*")), [])
            self.assertEqual(list((project / "Cache" / "remote-task-cache-registry" / "runs").glob("*.json")), [])

    def test_configured_workspace_owner_and_active_sibling_are_preserved(self):
        owner = Path(self.codex_sandbox.name) / "configured-owner"
        owner.mkdir()
        retained = owner / "retained.bin"
        retained.write_bytes(b"retain useful resources")
        with mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(owner)}):
            with ExitStack() as first_run, ExitStack() as second_run:
                first = first_run.enter_context(sync_global_skills.temporary_workspace("installer-"))
                second = second_run.enter_context(sync_global_skills.temporary_workspace("installer-"))
                self.assertEqual(first.parent, owner)
                self.assertEqual(second.parent, owner)
                self.assertNotEqual(first, second)
                self.assertTrue(first.name.startswith("temp-"))
                (second / "active.bin").write_bytes(b"active sibling")
                first_run.close()
                self.assertFalse(first.exists())
                self.assertEqual((second / "active.bin").read_bytes(), b"active sibling")
                with self.assertRaisesRegex(RuntimeError, "expected configured failure"):
                    with sync_global_skills.temporary_workspace("failed-") as failed:
                        (failed / "partial.bin").write_bytes(b"discard failed support")
                        raise RuntimeError("expected configured failure")
                self.assertFalse(failed.exists())
                self.assertEqual((second / "active.bin").read_bytes(), b"active sibling")
            self.assertFalse(second.exists())
        self.assertEqual(list(owner.iterdir()), [retained])
        self.assertEqual(retained.read_bytes(), b"retain useful resources")

    def test_runtime_exit_removes_only_its_sync_receipt(self):
        artifact_base = Path(self.codex_sandbox.name) / "runtime-receipts"
        artifact_base.mkdir()
        retained = artifact_base / "retained.bin"
        retained.write_bytes(b"retain adjacent resources")
        environment = dict(sync_global_skills.os.environ, YOFA_TASK_ARTIFACT_ROOT=str(artifact_base))
        environment.pop("CODEX_PROJECT_CACHE_ROOT", None)
        command = (
            "import importlib.util,json,sys; from pathlib import Path; "
            "spec=importlib.util.spec_from_file_location('receipt_runtime',sys.argv[1]); "
            "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
            "receipt=module.sync_state_file(); assert receipt==module.sync_state_file(); "
            "module.write_sync_state(receipt,'owner/repository','published-head','',''); "
            "assert json.loads(receipt.read_text(encoding='utf-8'))['remote_head']=='published-head'; "
            "print(json.dumps({'receipt':str(receipt),'run':str(module.DEFAULT_CACHE_ROOT)}))"
        )
        completed = sync_global_skills.subprocess.run([sys.executable, "-B", "-c", command, str(MODULE_PATH)], env=environment, capture_output=True, text=True, check=True, timeout=30, **sync_global_skills.hidden_process_options())
        readback = json.loads(completed.stdout)
        self.assertFalse(Path(readback["receipt"]).exists())
        self.assertFalse(Path(readback["run"]).exists())
        self.assertEqual(retained.read_bytes(), b"retain adjacent resources")

    def test_sync_receipt_cleanup_preserves_changed_bytes_and_other_files(self):
        owner = Path(self.codex_sandbox.name) / "receipt-owner"
        owner.mkdir()
        retained = owner / "retained.bin"
        retained.write_bytes(b"retain owner resources")
        with mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(owner)}), mock.patch.dict(sync_global_skills.SYNC_STATE_RECEIPTS, clear=True), mock.patch.object(sync_global_skills, "SYNC_STATE_DIRECTORIES", set()):
            state_file = sync_global_skills.sync_state_file()
            sync_global_skills.write_sync_state(state_file, "owner/repository", "published-head", "", "")
            state_file.write_bytes(b"changed by another consumer")
            with self.assertRaisesRegex(RuntimeError, "changed after this runtime"):
                sync_global_skills.write_sync_state(state_file, "owner/repository", "unexpected-overwrite", "", "")
            with mock.patch("builtins.print") as printer:
                sync_global_skills.cleanup_sync_state()
            self.assertEqual(state_file.read_bytes(), b"changed by another consumer")
            self.assertEqual(retained.read_bytes(), b"retain owner resources")
            self.assertTrue(printer.call_count)

    def test_sync_receipt_keeps_preexisting_configured_state_and_rejects_collision(self):
        owner = Path(self.codex_sandbox.name) / "existing-state-owner"
        legacy_state = owner / "state" / "management-skill-sync.json"
        legacy_state.parent.mkdir(parents=True)
        legacy_state.write_bytes(b"preexisting configured state")
        with mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(owner)}), mock.patch.dict(sync_global_skills.SYNC_STATE_RECEIPTS, clear=True), mock.patch.object(sync_global_skills, "SYNC_STATE_DIRECTORIES", set()):
            state_file = sync_global_skills.sync_state_file()
            self.assertNotEqual(state_file, legacy_state)
            self.assertEqual(state_file, sync_global_skills.sync_state_file())
            sync_global_skills.write_sync_state(state_file, "owner/repository", "published-head", "", "")
            self.assertEqual(state_file.read_bytes(), sync_global_skills.SYNC_STATE_RECEIPTS[state_file])
            sync_global_skills.write_sync_state(state_file, "owner/repository", "updated-head", "", "")
            self.assertEqual(json.loads(state_file.read_text(encoding="utf-8"))["remote_head"], "updated-head")
            with self.assertRaises(FileExistsError):
                sync_global_skills.write_sync_state(legacy_state, "owner/repository", "unexpected-overwrite", "", "")
            sync_global_skills.cleanup_sync_state()
            self.assertFalse(state_file.parent.parent.exists())
            self.assertEqual(legacy_state.read_bytes(), b"preexisting configured state")

    def test_scratch_override_rejects_project_and_unexpanded_tokens_before_write(self):
        for configured in (str(sync_global_skills.DEFAULT_PROJECT_ROOT / "management-skill"), "%SystemDrive%/scratch"):
            with self.subTest(configured=configured), mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": configured}):
                with mock.patch.object(Path, "mkdir", side_effect=AssertionError("invalid scratch must not write")):
                    with self.assertRaises(ValueError):
                        with sync_global_skills.temporary_workspace("test-"):
                            self.fail("invalid scratch was accepted")

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

    def test_english_readme_uses_template_and_current_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        template = sync_global_skills.ENGLISH_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template
        self.assertEqual(readme, expected)
        self.assertLess(len(template.split()), 600)
        self.assertNotIn("<!-- EXECUTION_DOMAIN_TABLE -->", readme)
        for concept in ("This repository maintains eight global Codex skills", "## What each skill does", "implementation steps", "skip missing memory", "in the active task", "project testing Skills", "real affected-case checks", "unpinned", "Project memories stay isolated", "At completion, summarize actual Skill names, steps and reasons once"):
            self.assertIn(concept, readme)
        self.assertNotIn("Every progress update and phase transition repeats Skill names", readme)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"({skill_name}/SKILL.md)", readme)


    def test_chinese_readme_is_compact_and_has_the_same_policy(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="zh")
        template = sync_global_skills.CHINESE_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template
        self.assertEqual(readme, expected)
        self.assertLess(len(template.splitlines()), 80)
        for concept in ("本仓库维护八个可复用的全局 Codex Skill", "## 各 Skill 的职责", "先简述目标", "缺少匹配记忆时直接跳过", "在当前任务内", "项目测试 Skill", "真实受影响场景", "本地记忆", "项目记忆互相隔离", "结尾一次性汇总实际使用的 Skill"):
            self.assertIn(concept, readme)
        self.assertNotIn("每条进度更新和阶段切换都必须重复列出 Skill", readme)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"({skill_name}/SKILL.md)", readme)

    def test_readme_documents_installation_preservation_and_portable_entry(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        for concept in ("deploy --source-dir .", "py -3 -B", "locking, backup, and recovery", "preserves unrelated skills, user AGENTS, and existing private history", "install-global-agents --source-dir .", "restorable backup", "--include-path", "--include-commit", "configured upstream", "unselected worktree and index changes"):
            self.assertIn(concept, readme)
        self.assertNotIn("/Users/", readme)
        self.assertNotIn("shell=True", readme)


    def test_available_agent_short_descriptions_are_at_most_64_characters(self):
        available_agent_paths = [SKILLS_DIR / skill_name / "agents" / "openai.yaml" for skill_name in sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES if (SKILLS_DIR / skill_name / "agents" / "openai.yaml").exists()]

        self.assertGreaterEqual(len(available_agent_paths), 7)
        for agent_path in available_agent_paths:
            description_match = re.search(r'^  short_description: "([^"]+)"$', agent_path.read_text(encoding="utf-8"), re.M)
            self.assertIsNotNone(description_match, agent_path)
            self.assertLessEqual(len(description_match.group(1)), 64, agent_path)








    def test_repository_snapshot_contains_every_local_readme_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = self.staged_skill_copy(sandbox)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            copied_names = sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            for readme_name in ("README.md", "README.zh.md"):
                readme = (repository_dir / readme_name).read_text(encoding="utf-8")
                references = set(re.findall(r'(?:src="|srcset="|\]\()([^\"#)]+)', readme))
                local_references = {reference for reference in references if not re.match(r"[a-z]+://", reference)}
                self.assertGreaterEqual(len(local_references), len(sync_global_skills.PRIMARY_SKILL_ORDER))
                for reference in local_references:
                    self.assertTrue((repository_dir / reference.removeprefix("./")).exists(), f"Missing README reference: {reference}")

    def test_active_readme_svg_references_are_accessible_and_self_contained(self):
        active_readmes = [sync_global_skills.build_readme(self.primary_skill_paths(), language=language) for language in ("en", "zh")]
        references = {target for readme in active_readmes for target in re.findall(r'(?:src="|srcset="|\]\()([^\"#)]+)', readme) if target.endswith(".svg")}
        for reference in references:
            svg_path = SKILLS_DIR / reference.removeprefix("./")
            root = ElementTree.parse(svg_path).getroot()
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            self.assertIsNotNone(root.find("svg:title", namespace), reference)
            self.assertIsNotNone(root.find("svg:desc", namespace), reference)
            self.assertEqual(root.attrib.get("role"), "img", reference)
            self.assertIn("viewBox", root.attrib, reference)
            self.assertEqual(svg_bounds_issues(svg_path), [], reference)
            for element in root.iter():
                self.assertNotIn(element.tag.rsplit("}", 1)[-1], {"script", "foreignObject"})
                for attribute, value in element.attrib.items():
                    if attribute.rsplit("}", 1)[-1] == "href":
                        self.assertFalse(value.startswith(("http://", "https://")), reference)


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
            with mock.patch.object(sync_global_skills, "load_skill_platform_checker", side_effect=AssertionError("consumer install must not run platform checks")) as platform, mock.patch.object(sync_global_skills, "run_release_gate", side_effect=AssertionError("consumer install must not run release gates")) as gate, mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer install must not run parity checks")) as parity, mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("consumer install must not hash skill trees")) as hasher:
                changed_names = sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertEqual([path.name for path in sync_global_skills.skill_directories(target_dir)], sync_global_skills.PRIMARY_SKILL_ORDER)
            platform.assert_not_called()
            gate.assert_not_called()
            parity.assert_not_called()
            hasher.assert_not_called()

    def test_cli_install_reports_memory_location_and_backup_requirement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_dir = Path(temp_dir) / "skills"
            setup = skills_dir / "project-memory-skill" / "scripts" / "obsidian_vault_setup.py"
            setup.parent.mkdir(parents=True)
            setup.write_text("# setup entry\n", encoding="utf-8")
            payload = {"status": "created", "vault": str(Path(temp_dir) / "Obsidian" / "Memory"),
                       "backup_message": "Back up this entire vault regularly."}
            completed = mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="")
            with mock.patch.object(sync_global_skills.subprocess, "run", return_value=completed) as launched, mock.patch("builtins.print") as printer:
                sync_global_skills.announce_memory_vault(skills_dir)
        self.assertIn(str(setup.resolve()), launched.call_args.args[0])
        printer.assert_any_call(f"Obsidian memory vault: {payload['vault']}")
        printer.assert_any_call(payload["backup_message"])

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

            with mock.patch.object(sync_global_skills, "clone_repository", return_value=repository_dir), mock.patch.object(sync_global_skills, "repository_head", return_value="published-head"), mock.patch.object(sync_global_skills, "write_sync_state") as state_writer, mock.patch.object(sync_global_skills, "load_skill_platform_checker", side_effect=AssertionError("consumer pull must not run platform checks")) as platform, mock.patch.object(sync_global_skills, "assert_public_safe", side_effect=AssertionError("consumer pull must not run public safety")) as public_safety, mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer pull must not check parity")) as parity, mock.patch.object(sync_global_skills, "path_differs", side_effect=AssertionError("consumer pull must not pre-diff")) as differ, mock.patch.object(sync_global_skills, "snapshot_hash", side_effect=AssertionError("consumer pull must not hash trees")) as hasher:
                changed_names = sync_global_skills.pull("owner/repository", target_dir)

            self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertIn("published-latest", old_skill.read_text(encoding="utf-8"))
            self.assertEqual(private_state.read_text(encoding="utf-8"), "private\n")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "unrelated\n")
            self.assertFalse((target_dir.parent / "AGENTS.md").exists())
            state_writer.assert_called_once_with(sync_global_skills.sync_state_file(), "owner/repository", "published-head", "", "")
            for forbidden in (platform, public_safety, parity, differ, hasher, self.release_gate):
                forbidden.assert_not_called()

    def test_consumer_deploy_replaces_previous_opaque_target(self):
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

            sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertFalse(previous_target.is_symlink())
            self.assertTrue((previous_target / "SKILL.md").is_file())
            self.assertEqual(outside_sentinel.read_text(encoding="utf-8"), "outside\n")
            self.release_gate.assert_not_called()

    def test_deploy_preserves_directory_agents_target_without_traversal(self):
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
            self.assertTrue(agents_target.is_dir())
            self.assertEqual((agents_target / "old.txt").read_text(encoding="utf-8"), "old agents directory\n")
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

    def test_consumer_deploy_preserves_global_agents_bytes_without_semantic_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = self.staged_skill_copy(sandbox)
            source_asset = source_dir / sync_global_skills.GLOBAL_AGENTS_ASSET
            source_asset.write_text("# malformed lifecycle\n", encoding="utf-8")
            target_dir = sandbox / "global-skills"
            previous_agents = target_dir.parent / "AGENTS.md"
            previous_agents.write_text("# previous lifecycle\n", encoding="utf-8")
            with mock.patch.object(sync_global_skills, "global_agents_parity", side_effect=AssertionError("consumer install must not validate AGENTS parity")) as parity:
                sync_global_skills.deploy(source_dir, target_dir)

            self.assertEqual(previous_agents.read_text(encoding="utf-8"), "# previous lifecycle\n")
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

    def test_installation_lock_treats_disappearing_lock_directory_as_released(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / "global-skills"
            lock_dir = target_dir.parent / sync_global_skills.INSTALL_LOCK_NAME
            lock_dir.mkdir()
            with mock.patch.object(sync_global_skills, "real_directory_entry", side_effect=FileNotFoundError):
                self.assertTrue(sync_global_skills.clear_stale_installation_lock(lock_dir))

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
            self.assertEqual(global_agents.read_text(encoding="utf-8"), "# stale lifecycle\n")
            self.assertEqual(sync_global_skills.snapshot_hash(self.primary_skill_paths()), sync_global_skills.snapshot_hash([target_dir / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.release_gate.assert_not_called()

    @unittest.skipUnless(sys.platform == "win32", "Native Windows destination ACL regression")
    def test_windows_repeated_deploy_inherits_destination_access_and_preserves_owned_acls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = self.staged_skill_copy(sandbox)
            target_dir = sandbox / "global-skills"
            target_dir.mkdir()
            self.windows_icacls(target_dir, "/grant", "*S-1-5-11:(OI)(CI)RX", "/Q")
            private_state = target_dir / "task-analyze-skill" / "local" / "events.jsonl"
            private_state.parent.mkdir(parents=True)
            private_state.write_bytes(b"private-state\n")
            unrelated = target_dir / "chronicle" / "SKILL.md"
            unrelated.parent.mkdir()
            unrelated.write_bytes(b"unrelated-skill\n")
            global_agents = target_dir.parent / "AGENTS.md"
            global_agents.write_bytes(b"user-global-agents\n")
            for path in (private_state.parent, unrelated.parent, global_agents):
                self.windows_icacls(path, "/inheritance:d", "/Q")
            preserved_paths = [private_state.parent, private_state, unrelated.parent, unrelated, global_agents]
            preserved_acls = self.windows_acl_state(preserved_paths)
            preserved_bytes = {path: path.read_bytes() for path in (private_state, unrelated, global_agents)}
            real_create_workspace = sync_global_skills.create_installation_workspace
            protected_transactions = []

            def create_protected_workspace(skills_dir):
                transaction = real_create_workspace(skills_dir)
                # Reproduce the protected staging parent even on older Python versions.
                self.windows_icacls(transaction, "/inheritance:d", "/Q")
                protected_transactions.append(self.windows_acl_state([transaction])[str(transaction)]["Protected"])
                return transaction

            with mock.patch.object(sync_global_skills, "create_installation_workspace", side_effect=create_protected_workspace):
                for revision in (1, 2):
                    source_skill = source_dir / "management-skill" / "SKILL.md"
                    source_skill.write_text(source_skill.read_text(encoding="utf-8") + f"\nrevision-{revision}\n", encoding="utf-8")
                    changed_names = sync_global_skills.deploy(source_dir, target_dir)
                    self.assertEqual(changed_names, sync_global_skills.PRIMARY_SKILL_ORDER)
                    installed_paths = []
                    for name in changed_names:
                        installed_skill = target_dir / name
                        installed_paths.append(installed_skill)
                        installed_paths.extend(path for path in installed_skill.rglob("*") if "local" not in path.relative_to(installed_skill).parts)
                    installed_acls = self.windows_acl_state(installed_paths)
                    for path, acl in installed_acls.items():
                        self.assertFalse(acl["Protected"], path)
                        self.assertTrue(acl["InheritedRead"], path)
                    self.assertEqual((target_dir / "management-skill" / "SKILL.md").read_bytes(), source_skill.read_bytes())
                    self.assertEqual(self.windows_acl_state(preserved_paths), preserved_acls)
                    self.assertEqual({path: path.read_bytes() for path in preserved_bytes}, preserved_bytes)
                    self.assertFalse(list(target_dir.parent.glob(f"{sync_global_skills.INSTALL_TRANSACTION_PREFIX}*")))
            self.assertEqual(protected_transactions, [True, True])

    def test_permission_reset_failure_restores_previous_installation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            target_dir = sandbox / "global-skills"
            for name in sync_global_skills.PRIMARY_SKILL_ORDER:
                old_skill = target_dir / name / "SKILL.md"
                old_skill.parent.mkdir(parents=True)
                old_skill.write_text(f"previous-{name}\n", encoding="utf-8")
                previous_helper = old_skill.parent / "scripts" / "previous.py"
                previous_helper.parent.mkdir()
                previous_helper.write_text(f"# previous-{name}\n", encoding="utf-8")
            private_state = target_dir / "task-analyze-skill" / "local" / "events.jsonl"
            private_state.parent.mkdir()
            private_state.write_bytes(b"private-state\n")
            unrelated = target_dir / "chronicle" / "SKILL.md"
            unrelated.parent.mkdir()
            unrelated.write_bytes(b"unrelated-skill\n")
            global_agents = target_dir.parent / "AGENTS.md"
            global_agents.write_bytes(b"user-global-agents\n")
            previous_paths = [target_dir, *target_dir.rglob("*"), global_agents]
            previous_bytes = {path: path.read_bytes() for path in previous_paths if path.is_file()}
            previous_acls = self.windows_acl_state(previous_paths) if sys.platform == "win32" else None
            real_reset = sync_global_skills.inherit_installed_skill_permissions
            normalized = []

            def fail_one_permission_reset(skill_dir):
                normalized.append(Path(skill_dir).name)
                if Path(skill_dir).name == "code-skill":
                    raise RuntimeError("injected permission reset failure")
                return real_reset(skill_dir)

            with mock.patch.object(sync_global_skills, "inherit_installed_skill_permissions", side_effect=fail_one_permission_reset), self.assertRaisesRegex(RuntimeError, "previous installation was restored.*injected permission reset failure"):
                sync_global_skills.deploy(SKILLS_DIR, target_dir)

            self.assertEqual(normalized, sync_global_skills.PRIMARY_SKILL_ORDER[:4])
            self.assertEqual({path: path.read_bytes() for path in target_dir.rglob("*") if path.is_file()} | {global_agents: global_agents.read_bytes()}, previous_bytes)
            if previous_acls is not None:
                self.assertEqual(self.windows_acl_state(previous_paths), previous_acls)
            self.assertFalse(list(target_dir.parent.glob(f"{sync_global_skills.INSTALL_TRANSACTION_PREFIX}*")))
            self.assertFalse((target_dir.parent / sync_global_skills.INSTALL_LOCK_NAME).exists())

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
            native_run = sync_global_skills.subprocess.run
            def execute(command, **kwargs):
                if len(command) > 2 and command[2] == str(installed_gate.resolve()):
                    return completed
                return native_run(command, **kwargs)
            with mock.patch.object(sync_global_skills.subprocess, "run", side_effect=execute) as runner:
                REAL_RUN_RELEASE_GATE(source_dir, skills_dir, "deployed")

            command = next(call.args[0] for call in runner.call_args_list if call.kwargs.get("env", {}).get("CODEX_PROJECT_CACHE_ROOT"))
            self.assertEqual(command[1], "-B")
            self.assertEqual(Path(command[2]), installed_gate.resolve())

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
            with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "announce_memory_vault"):
                sync_global_skills.main()
            self.assertEqual(sync_global_skills.snapshot_hash(self.primary_skill_paths()), sync_global_skills.snapshot_hash([target_dir / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.assertFalse((target_dir.parent / "AGENTS.md").exists())

    def test_deploy_cli_defaults_to_real_official_user_skills(self):
        self.assertEqual(sync_global_skills.OFFICIAL_USER_SKILLS_DIRECTORY, Path.home() / ".agents" / "skills")
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_home = Path(temp_dir).resolve()
            official_root = fixture_home / ".agents" / "skills"
            legacy_root = fixture_home / ".codex" / "skills"
            argv = ["sync_global_skills.py", "deploy", "--source-dir", str(SKILLS_DIR)]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "OFFICIAL_USER_SKILLS_DIRECTORY", official_root), mock.patch.object(sync_global_skills, "announce_memory_vault"):
                sync_global_skills.main()
            self.assertEqual(sync_global_skills.snapshot_hash(self.primary_skill_paths()), sync_global_skills.snapshot_hash([official_root / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]))
            self.assertTrue(all(sync_global_skills.real_directory_entry(official_root / name) for name in sync_global_skills.PRIMARY_SKILL_ORDER))
            self.assertFalse(legacy_root.exists())
            self.assertFalse((self.codex_root / "AGENTS.md").exists())

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

    def test_explicit_global_agents_install_targets_only_codex_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"
            target_dir = home_dir / ".agents" / "skills"
            host_agents = home_dir / "AGENTS.md"
            host_agents.parent.mkdir(parents=True)
            host_agents.write_text("# host instructions\n", encoding="utf-8")
            installation = sync_global_skills.install_global_agents(SKILLS_DIR, target_dir)
            expected = sync_global_skills.canonical_global_agents_text(SKILLS_DIR)
            targets = sync_global_skills.global_agents_targets(target_dir)
            self.assertTrue(installation["changed"])
            self.assertEqual(targets, [(self.codex_root / "AGENTS.md").absolute()])
            self.assertEqual([target.read_text(encoding="utf-8") for target in targets], [expected])
            self.assertEqual(host_agents.read_text(encoding="utf-8"), "# host instructions\n")
            self.assertFalse((target_dir.parent / "AGENTS.md").exists())
            self.assertFalse(target_dir.exists())
            parity = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
            self.assertEqual(parity["status"], "pass")
            self.assertEqual(parity["targets"], [str(target) for target in targets])

    def test_explicit_global_agents_install_creates_persistent_backup_and_restores_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir) / ".agents" / "skills"
            target_agents = self.codex_root / "AGENTS.md"
            target_agents.parent.mkdir(parents=True)
            target_agents.write_text("# personal instructions\n", encoding="utf-8")

            installation = sync_global_skills.install_global_agents(SKILLS_DIR, target_dir)

            self.assertTrue(installation["changed"])
            backup_dir = sync_global_skills.global_agents_backup_root(target_dir) / installation["backup_id"]
            self.assertEqual(backup_dir.parent, self.codex_root / "global-agents-backups")
            self.assertTrue((backup_dir / "previous").is_file())
            self.assertEqual((backup_dir / "previous").read_text(encoding="utf-8"), "# personal instructions\n")
            self.assertEqual(target_agents.read_text(encoding="utf-8"), sync_global_skills.canonical_global_agents_text(SKILLS_DIR))
            self.assertEqual(sync_global_skills.list_global_agents_backups(target_dir), [{"id": installation["backup_id"], "state": "installed", "target_existed": True}])

            target_agents.write_text("# changed after install\n", encoding="utf-8")
            restoration = sync_global_skills.restore_global_agents_backup(target_dir, installation["backup_id"])

            self.assertTrue(restoration["changed"])
            self.assertEqual(target_agents.read_text(encoding="utf-8"), "# personal instructions\n")
            self.assertEqual((backup_dir / "replaced-on-restore").read_text(encoding="utf-8"), "# changed after install\n")
            self.assertEqual(sync_global_skills.list_global_agents_backups(target_dir), [{"id": installation["backup_id"], "state": "restored", "target_existed": True}])

    def test_codex_home_fallback_is_independent_of_the_skill_root(self):
        with mock.patch.dict(sync_global_skills.os.environ, {"CODEX_HOME": ""}):
            expected = (Path.home() / ".codex").absolute()
            self.assertEqual(sync_global_skills.codex_home(), expected)
            self.assertEqual(sync_global_skills.global_agents_targets(Path("unrelated-skills")), [expected / "AGENTS.md"])

    def test_startup_only_install_preserves_other_guidance_and_is_idempotent(self):
        target = self.codex_root / "AGENTS.md"
        target.parent.mkdir(parents=True)
        personal = "# Personal rules\nPreserve my exact instructions.\n"
        target.write_text(personal, encoding="utf-8")
        skills = self.codex_root.parent / "skills"
        rule = sync_global_skills.ai_index_startup_rule(SKILLS_DIR)
        self.assertIn("AI-index prompts and maintenance apply only to the current task project", rule)
        self.assertIn("--project-scope reference", rule)
        self.assertIn("Only an explicit change of the main work project", rule)
        first = sync_global_skills.install_global_agents(SKILLS_DIR, skills, startup_only=True)
        self.assertEqual(target.read_text(encoding="utf-8"), rule + "\n\n" + personal)
        self.assertTrue(first["changed"])
        second = sync_global_skills.install_global_agents(SKILLS_DIR, skills, startup_only=True)
        self.assertFalse(second["changed"])
        self.assertIsNone(second["backup_id"])
        restoration = sync_global_skills.restore_global_agents_backup(skills, first["backup_id"])
        self.assertTrue(restoration["changed"])
        self.assertEqual(target.read_text(encoding="utf-8"), personal)

    def test_startup_only_updates_exact_block_and_rejects_ambiguous_markers(self):
        target = self.codex_root / "AGENTS.md"
        target.parent.mkdir(parents=True)
        skills = self.codex_root.parent / "skills"
        rule = sync_global_skills.ai_index_startup_rule(SKILLS_DIR)
        stale = sync_global_skills.AI_INDEX_STARTUP_START + "\nOld managed rule.\n" + sync_global_skills.AI_INDEX_STARTUP_END
        target.write_text("Personal prefix\n\n" + stale + "\n\nPersonal suffix\n", encoding="utf-8")
        sync_global_skills.install_global_agents(SKILLS_DIR, skills, startup_only=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "Personal prefix\n\n" + rule + "\n\nPersonal suffix\n")
        malformed = "Keep this.\n" + sync_global_skills.AI_INDEX_STARTUP_START
        target.write_text(malformed, encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            sync_global_skills.install_global_agents(SKILLS_DIR, skills, startup_only=True)
        self.assertEqual(target.read_text(encoding="utf-8"), malformed)

    def test_startup_activation_detects_missing_entry_and_shadowing_override(self):
        self.assertEqual(sync_global_skills.ai_index_startup_status(SKILLS_DIR), "missing_global_entry")
        target = self.codex_root / "AGENTS.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Legacy global rules\n", encoding="utf-8")
        self.assertEqual(sync_global_skills.ai_index_startup_status(SKILLS_DIR), "startup_rule_missing_or_stale")
        sync_global_skills.install_global_agents(SKILLS_DIR, self.codex_root.parent / "skills", startup_only=True)
        self.assertEqual(sync_global_skills.ai_index_startup_status(SKILLS_DIR), "ready")
        override = self.codex_root / "AGENTS.override.md"
        override.write_text("# Active override\n", encoding="utf-8")
        self.assertEqual(sync_global_skills.ai_index_startup_status(SKILLS_DIR), "shadowed_by_global_override")
        override.write_text("\n", encoding="utf-8")
        self.assertEqual(sync_global_skills.ai_index_startup_status(SKILLS_DIR), "ready")

    def test_official_deploy_reports_pending_startup_without_replacing_personal_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skills = Path(temp_dir) / "skills"
            target = self.codex_root / "AGENTS.md"
            target.parent.mkdir(parents=True)
            personal = "# Personal global guidance\n"
            target.write_text(personal, encoding="utf-8")
            with mock.patch.object(sync_global_skills, "OFFICIAL_USER_SKILLS_DIRECTORY", skills), mock.patch.object(sync_global_skills, "repair_legacy_user_skills"), mock.patch("builtins.print") as messages:
                sync_global_skills.deploy(SKILLS_DIR, skills)
            output = "\n".join(str(call.args[0]) for call in messages.call_args_list if call.args)
            self.assertIn("startup_rule_missing_or_stale", output)
            self.assertIn("--startup-only", output)
            self.assertEqual(target.read_text(encoding="utf-8"), personal)

    def test_startup_only_cli_uses_preserving_installer(self):
        argv = ["sync_global_skills.py", "install-global-agents", "--source-dir", str(SKILLS_DIR), "--startup-only"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "install_global_agents", return_value={"changed": False, "target": self.codex_root / "AGENTS.md"}) as installer:
            sync_global_skills.main()
        installer.assert_called_once_with(SKILLS_DIR, sync_global_skills.OFFICIAL_USER_SKILLS_DIRECTORY, startup_only=True)

    def test_push_cli_defaults_to_the_maintained_repository_source(self):
        argv = ["sync_global_skills.py", "push", "--message", "source-first smoke", "--include-path", "verify-skill/SKILL.md", "--include-path", "README.md"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "push") as publisher:
            sync_global_skills.main()
        publisher.assert_called_once_with(
            sync_global_skills.DEFAULT_REPOSITORY,
            sync_global_skills.DEFAULT_SOURCE_DIR,
            "source-first smoke",
            False,
            Path.home() / ".agents" / "skills",
            ["verify-skill/SKILL.md", "README.md"],
            [],
        )

    def test_publishable_source_paths_exclude_unrelated_or_private_content(self):
        self.assertTrue(sync_global_skills.publishable_source_path(Path("verify-skill/SKILL.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path(".agents/skills/testing-skill/SKILL.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path(".agents/skills/testing-skill/tests/test_catalog.py")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path("AGENTS.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path(".gitignore")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path("README.zh.md")))
        self.assertTrue(sync_global_skills.publishable_source_path(Path(".github/workflows/ci.yml")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("notes.txt")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("Knowledge.md")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".github/workflows/other.yml")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("task-analyze-skill/local/private.json")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path("verify-skill/auth.json")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".agents/skills/other-skill/SKILL.md")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".agents/skills/testing-skill/../other-skill/SKILL.md")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".agents/skills/testing-skill/local/private.json")))
        self.assertFalse(sync_global_skills.publishable_source_path(Path(".agents/skills/testing-skill/auth.json")))
        index_root = sync_global_skills.PROJECT_AI_INDEX_SKILL
        for name in ("SKILL.md", "index.json", "rules/repository.md", "modules/publisher.md", "modules/publisher/validation.md"):
            with self.subTest(index_path=name):
                self.assertTrue(sync_global_skills.publishable_source_path(index_root / name))
        for name in (".", "plan.json", "state.json", "rules/index.json", "plan.md", "plans/update.md", "logs/run.md", "output.log", "local/rules.md", "auth.json", "scripts/update.py", "../other-skill/SKILL.md"):
            with self.subTest(index_path=name):
                self.assertFalse(sync_global_skills.publishable_source_path(index_root / name))

    def test_project_ai_index_publication_stays_local_and_checks_private_content(self):
        source_dir = self.publication_repository()[0]
        index_root = sync_global_skills.PROJECT_AI_INDEX_SKILL
        rule_paths = {name: (index_root / "rules" / f"{name}.md").as_posix() for name in ("repository", "structure", "verification")}
        module_path = index_root / "modules" / "publisher.md"
        manifest = {"schema_version": 1, "rules": rule_paths, "modules": [{"id": "publisher", "summary": "Scoped skill publication", "document": module_path.as_posix(), "sources": ["management-skill/scripts/sync_global_skills.py"], "dependencies": []}]}
        contents = {
            index_root / "SKILL.md": "---\nname: ai-index\ndescription: Route project publication work.\n---\nRead [the route map](index.json).\n",
            index_root / "index.json": json.dumps(manifest, indent=2) + "\n",
            module_path: "# Publisher\nKeep project guidance scoped to its source repository.\n",
            **{Path(path): f"# {name.title()}\nPreserve project ownership.\n" for name, path in rule_paths.items()},
        }
        for path, content in contents.items():
            target = source_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        selected = sync_global_skills.selected_publication_paths(source_dir, [path.as_posix() for path in contents])
        self.assertEqual(selected, list(contents))
        self.assertNotIn("ai-index", sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES)
        with mock.patch("builtins.print"), sync_global_skills.validated_publication_candidate(source_dir, selected) as publication:
            candidate = publication[0]
            for path, content in contents.items():
                self.assertEqual((candidate / path).read_text(encoding="utf-8"), content)
            installed = candidate.parent / "installed-skills"
            self.assertEqual([path.name for path in sync_global_skills.skill_directories(installed)], sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertFalse((installed / "ai-index").exists())
            self.assertFalse((installed / ".agents").exists())
        (source_dir / module_path).write_text('"api_key": "' + "x" * 24 + '"\n', encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "ai-index/modules/publisher.md: secret-like content"):
            with sync_global_skills.validated_publication_candidate(source_dir, selected):
                self.fail("Private project index content must not enter a publication candidate")

    def publication_repository(self, configured_upstream=True, suffix=""):
        sandbox = Path(self.codex_sandbox.name)
        source_dir = sandbox / f"publication-source{suffix}"
        remote_dir = sandbox / f"remote{suffix}.git"
        source_dir.mkdir()
        sync_global_skills.prepare_repository_snapshot(source_dir, SKILLS_DIR)
        (source_dir / "AGENTS.md").write_text("# Publication fixture\n", encoding="utf-8")
        sync_global_skills.run_command(["git", "init"], cwd=source_dir)
        sync_global_skills.run_command(["git", "branch", "-M", "delivery-local"], cwd=source_dir)
        sync_global_skills.run_command(["git", "config", "user.name", "Source Publish Test"], cwd=source_dir)
        sync_global_skills.run_command(["git", "config", "user.email", "source-publish@example.invalid"], cwd=source_dir)
        sync_global_skills.run_command(["git", "config", "core.autocrlf", "false"], cwd=source_dir)
        if sys.platform == "win32":
            sync_global_skills.run_command(["git", "config", "core.longpaths", "true"], cwd=source_dir)
        sync_global_skills.run_command(["git", "add", "--all"], cwd=source_dir)
        sync_global_skills.run_command(["git", "commit", "-m", "initial"], cwd=source_dir)
        sync_global_skills.run_command(["git", "init", "--bare", str(remote_dir)], cwd=sandbox)
        sync_global_skills.run_command(["git", "remote", "add", "publication", str(remote_dir)], cwd=source_dir)
        command = ["git", "push", "publication", "HEAD:refs/heads/release-target"]
        if configured_upstream:
            command.insert(2, "--set-upstream")
        sync_global_skills.run_command(command, cwd=source_dir)
        artifact_owner = sandbox / "publication-artifacts"
        artifact_owner.mkdir(exist_ok=True)
        environment = mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(artifact_owner)})
        environment.start()
        self.addCleanup(environment.stop)
        return source_dir, remote_dir

    def advance_publication_remote(self, remote_dir, relative_path, text):
        editor = remote_dir.parent / f"remote-editor-{time.time_ns()}"
        sync_global_skills.run_command(["git", "clone", "--branch", "release-target", str(remote_dir), str(editor)])
        sync_global_skills.run_command(["git", "config", "user.name", "Remote Fixture"], cwd=editor)
        sync_global_skills.run_command(["git", "config", "user.email", "remote@example.invalid"], cwd=editor)
        target = editor / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        sync_global_skills.run_command(["git", "add", "--", relative_path], cwd=editor)
        sync_global_skills.run_command(["git", "commit", "-m", "Remote advance"], cwd=editor)
        sync_global_skills.run_command(["git", "push", "origin", "HEAD:refs/heads/release-target"], cwd=editor)
        return sync_global_skills.repository_head(editor)

    def test_push_selects_exact_paths_and_preserves_other_index_work_and_stashes(self):
        source_dir, remote_dir = self.publication_repository()
        artifact_owner = Path(sync_global_skills.os.environ["CODEX_PROJECT_CACHE_ROOT"])
        if sys.platform == "win32":
            # Cross MAX_PATH for Git objects without exceeding Git's repository-discovery boundary.
            while len(str(artifact_owner)) < 180:
                artifact_owner /= "nested-owner"
        selected = source_dir / "verify-skill" / "SKILL.md"
        unrelated = source_dir / "workflow-skill" / "SKILL.md"
        original_unrelated = unrelated.read_bytes()
        (source_dir / "old-recovery.txt").write_text("existing recovery\n", encoding="utf-8")
        sync_global_skills.run_command(["git", "stash", "push", "--include-untracked", "-m", "preexisting recovery"], cwd=source_dir)
        previous_stash = sync_global_skills.run_command(["git", "rev-parse", "refs/stash"], cwd=source_dir).stdout.strip()
        unrelated.write_bytes(original_unrelated + b"\nUnrelated staged change.\n")
        sync_global_skills.run_command(["git", "add", "--", "workflow-skill/SKILL.md"], cwd=source_dir)
        staged_unrelated = sync_global_skills.run_command(["git", "show", ":workflow-skill/SKILL.md"], cwd=source_dir).stdout
        unrelated.write_bytes(unrelated.read_bytes() + b"Unrelated unstaged change.\n")
        expected_unrelated = unrelated.read_bytes()
        untracked = source_dir / "code-skill" / "unrelated-note.md"
        untracked.write_text("preserve untracked content\n", encoding="utf-8")
        selected.write_bytes(selected.read_bytes() + b"\nSelected source change.\n")
        added = source_dir / "code-skill" / "selected-example.md"
        added.write_bytes(b"Selected addition.\n")
        candidate_roots = []

        def inspect_real_candidate(candidate, installed, mode):
            candidate_roots.append(candidate)
            if sys.platform == "win32":
                self.assertGreater(max(len(str(path)) for path in (candidate / ".git/objects").rglob("*") if path.is_file()), 260)
            self.assertNotEqual(candidate, source_dir)
            self.assertEqual((candidate / "workflow-skill/SKILL.md").read_bytes(), original_unrelated)
            self.assertEqual((installed / "workflow-skill/SKILL.md").read_bytes(), original_unrelated)
            self.assertFalse((candidate / "code-skill/unrelated-note.md").exists())
            self.assertEqual((candidate / "verify-skill/SKILL.md").read_bytes(), selected.read_bytes())
            self.assertEqual((installed / "verify-skill/SKILL.md").read_bytes(), selected.read_bytes())

        self.release_gate.side_effect = inspect_real_candidate
        with mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(artifact_owner)}), mock.patch("builtins.print"):
            sync_global_skills.push("label/must-not-select-a-remote", source_dir, "Publish selected files", False, include_paths=["verify-skill/SKILL.md", "code-skill/selected-example.md"])
        upstream = sync_global_skills.publication_upstream(source_dir)
        self.assertEqual(upstream["remote"], "publication")
        self.assertEqual(upstream["reference"], "refs/heads/release-target")
        self.assertEqual(sync_global_skills.remote_branch_head(source_dir, upstream), sync_global_skills.repository_head(source_dir))
        self.assertEqual(sync_global_skills.run_command(["git", "branch", "--show-current"], cwd=source_dir).stdout.strip(), "delivery-local")
        self.assertEqual(unrelated.read_bytes(), expected_unrelated)
        self.assertEqual(sync_global_skills.run_command(["git", "show", ":workflow-skill/SKILL.md"], cwd=source_dir).stdout, staged_unrelated)
        self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [Path("workflow-skill/SKILL.md")])
        self.assertEqual(untracked.read_text(encoding="utf-8"), "preserve untracked content\n")
        self.assertEqual(sync_global_skills.run_command(["git", "rev-parse", "refs/stash"], cwd=source_dir).stdout.strip(), previous_stash)
        published = sync_global_skills.run_command(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=source_dir).stdout.splitlines()
        self.assertEqual(set(published), {"verify-skill/SKILL.md", "code-skill/selected-example.md"})
        self.assertEqual(self.release_gate.call_count, 1)
        self.assertTrue(all(not root.exists() for root in candidate_roots))
        self.assertEqual(sync_global_skills.run_command(["git", "ls-remote", str(remote_dir), "refs/heads/delivery-local"], cwd=source_dir).stdout, "")

    def test_push_fetches_before_commit_and_retries_a_real_remote_advance(self):
        source_dir, remote_dir = self.publication_repository()
        selected = source_dir / "verify-skill/SKILL.md"
        selected.write_bytes(selected.read_bytes() + b"\nLocal selected change.\n")
        first_remote = self.advance_publication_remote(remote_dir, "code-skill/upstream-before.md", "before commit\n")
        real_run = sync_global_skills.run_command
        pushed_commands = []
        advanced_heads = []

        def advance_once(command, cwd=None, env=None):
            if command[:3] == ["git", "push", "publication"]:
                pushed_commands.append(command)
                if len(pushed_commands) == 1:
                    advanced_heads.append(self.advance_publication_remote(remote_dir, "code-skill/upstream-during.md", "during push\n"))
            return real_run(command, cwd=cwd, env=env)

        with mock.patch.object(sync_global_skills, "run_command", side_effect=advance_once), mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Publish with integration", False, include_paths=["verify-skill/SKILL.md"])
        head = sync_global_skills.repository_head(source_dir)
        self.assertEqual(sync_global_skills.remote_branch_head(source_dir, sync_global_skills.publication_upstream(source_dir)), head)
        self.assertEqual(len(pushed_commands), 2)
        self.assertEqual(self.release_gate.call_count, 2)
        history = real_run(["git", "rev-list", "HEAD"], cwd=source_dir).stdout.splitlines()
        self.assertIn(first_remote, history)
        self.assertIn(advanced_heads[0], history)
        self.assertEqual((source_dir / "code-skill/upstream-before.md").read_text(), "before commit\n")
        self.assertEqual((source_dir / "code-skill/upstream-during.md").read_text(), "during push\n")
        self.assertEqual(sync_global_skills.source_worktree_paths(source_dir), [])
        self.assertEqual(real_run(["git", "stash", "list"], cwd=source_dir).stdout, "")

    def test_push_missing_upstream_preserves_head_work_and_index(self):
        source_dir, remote_dir = self.publication_repository(configured_upstream=False)
        selected = source_dir / "verify-skill/SKILL.md"
        selected.write_bytes(selected.read_bytes() + b"\nKeep staged work.\n")
        sync_global_skills.run_command(["git", "add", "--", "verify-skill/SKILL.md"], cwd=source_dir)
        original_head = sync_global_skills.repository_head(source_dir)
        original_state = sync_global_skills.dirty_source_signature(source_dir)
        with self.assertRaisesRegex(RuntimeError, "no single configured remote upstream"):
            sync_global_skills.push("not/an-upstream", source_dir, "Must not publish", False, include_paths=["verify-skill/SKILL.md"])
        self.assertEqual(sync_global_skills.repository_head(source_dir), original_head)
        self.assertEqual(sync_global_skills.dirty_source_signature(source_dir), original_state)
        self.release_gate.assert_not_called()

    def test_push_merge_conflict_retains_local_commit_and_exact_recovery_stash(self):
        source_dir, remote_dir = self.publication_repository()
        selected = source_dir / "verify-skill/SKILL.md"
        selected.write_text("Local conflicting content.\n", encoding="utf-8")
        sync_global_skills.run_command(["git", "add", "--", "verify-skill/SKILL.md"], cwd=source_dir)
        sync_global_skills.run_command(["git", "commit", "-m", "Keep local commit"], cwd=source_dir)
        local_head = sync_global_skills.repository_head(source_dir)
        unrelated = source_dir / "recover-me.txt"
        unrelated.write_text("minimum recovery content\n", encoding="utf-8")
        remote_head = self.advance_publication_remote(remote_dir, "verify-skill/SKILL.md", "Remote conflicting content.\n")
        with mock.patch("builtins.print") as printer, self.assertRaisesRegex(RuntimeError, "Upstream integration pending"):
            sync_global_skills.push("label/only", source_dir, "Must preserve conflict", False, include_commits=[local_head])
        self.assertEqual(sync_global_skills.repository_head(source_dir), local_head)
        self.assertEqual(sync_global_skills.active_git_operation(source_dir), "MERGE_HEAD")
        stash_head = sync_global_skills.run_command(["git", "rev-parse", "refs/stash"], cwd=source_dir).stdout.strip()
        self.assertEqual(sync_global_skills.run_command(["git", "show", f"{stash_head}^3:recover-me.txt"], cwd=source_dir).stdout, "minimum recovery content\n")
        self.assertEqual(sync_global_skills.remote_branch_head(source_dir, sync_global_skills.publication_upstream(source_dir)), remote_head)
        self.assertTrue(any(stash_head in str(call) and "not dropped" in str(call) for call in printer.call_args_list))
        self.release_gate.assert_not_called()
        sync_global_skills.run_command(["git", "merge", "--abort"], cwd=source_dir)
        sync_global_skills.run_command(["git", "stash", "apply", "--index", stash_head], cwd=source_dir)
        self.assertEqual(unrelated.read_text(), "minimum recovery content\n")

    def test_push_readme_generation_requires_explicit_file_ownership(self):
        source_dir, remote_dir = self.publication_repository()
        readme = source_dir / "README.md"
        template = source_dir / "management-skill/assets/readme/github-readme-template.md"
        template.write_bytes(template.read_bytes() + b"\nSelected template change.\n")
        readme.write_text("# Deliberate stale input\n", encoding="utf-8")
        with mock.patch("builtins.print"), self.assertRaisesRegex(RuntimeError, "README changes require explicit"):
            sync_global_skills.push("label/only", source_dir, "No implicit README owner", False, include_paths=["management-skill/assets/readme/github-readme-template.md"])
        self.assertEqual(readme.read_text(), "# Deliberate stale input\n")
        self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [])
        with mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Regenerate owned README", False, include_paths=["management-skill/assets/readme/github-readme-template.md", "README.md"])
        self.assertEqual(readme.read_text(encoding="utf-8"), sync_global_skills.build_readme([], source_dir=source_dir))
        self.assertEqual(sync_global_skills.source_worktree_paths(source_dir), [])

    def test_source_worktree_paths_preserves_unusual_names_and_rename_sources(self):
        output = ' M Knowledge.md\0?? local "quoted"\nnotes.md\0R  notes.md\0verify-skill/SKILL.md\0'
        with mock.patch.object(sync_global_skills, "run_command", return_value=mock.Mock(stdout=output)):
            paths = sync_global_skills.source_worktree_paths(Path("fixture"))
        self.assertEqual(paths, [Path("Knowledge.md"), Path('local "quoted"\nnotes.md'), Path("notes.md"), Path("verify-skill/SKILL.md")])

    def test_push_safety_scan_rejects_new_fixture_before_publication_mutations(self):
        source_dir, remote_dir = self.publication_repository()
        unsafe = source_dir / sync_global_skills.PROJECT_TESTING_SKILL / "tests" / "fixtures" / "benchmark-public.json"
        unsafe.parent.mkdir(parents=True, exist_ok=True)
        unsafe.write_text(json.dumps({"sample": "sk-" + "a" * 24}), encoding="utf-8")
        original_head = sync_global_skills.repository_head(source_dir)
        before_readmes = [(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")]
        with mock.patch("builtins.print"), self.assertRaisesRegex(RuntimeError, "benchmark-public.json: secret-like content"):
            sync_global_skills.push("fixture/repository", source_dir, "must not publish", False, include_paths=[unsafe.relative_to(source_dir).as_posix()])
        self.release_gate.assert_not_called()
        self.assertEqual([(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")], before_readmes)
        self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [])
        self.assertEqual(sync_global_skills.repository_head(source_dir), original_head)

    def test_push_gate_failure_precedes_readme_index_commit_and_remote_mutation(self):
        source_dir, remote_dir = self.publication_repository()
        changed = source_dir / "verify-skill" / "SKILL.md"
        changed.write_bytes(changed.read_bytes() + b"\nGate candidate.\n")
        before_readmes = [(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")]
        before_head = sync_global_skills.repository_head(source_dir)
        self.release_gate.side_effect = RuntimeError("full regression failed")
        with mock.patch("builtins.print"), self.assertRaisesRegex(RuntimeError, "full regression failed"):
            sync_global_skills.push("fixture/repository", source_dir, "must not publish", False, include_paths=["verify-skill/SKILL.md"])
        self.assertEqual([(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")], before_readmes)
        self.assertEqual(sync_global_skills.repository_head(source_dir), before_head)
        self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [])

    def test_push_requires_explicit_preexisting_commit_selection(self):
        source_dir, remote_dir = self.publication_repository()
        changed = source_dir / "verify-skill/SKILL.md"
        changed.write_bytes(changed.read_bytes() + b"\nExisting local commit.\n")
        sync_global_skills.run_command(["git", "add", "--", "verify-skill/SKILL.md"], cwd=source_dir)
        sync_global_skills.run_command(["git", "commit", "-m", "Existing local work"], cwd=source_dir)
        local_head = sync_global_skills.repository_head(source_dir)
        with self.assertRaisesRegex(RuntimeError, f"include-commit.*{local_head}"):
            sync_global_skills.push("label/only", source_dir, "Do not infer ownership", False)
        self.release_gate.assert_not_called()
        with mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Deliver selected commit", False, include_commits=[local_head])
        self.assertEqual(sync_global_skills.remote_branch_head(source_dir, sync_global_skills.publication_upstream(source_dir)), local_head)

    def test_push_uses_validated_commit_even_if_local_head_changes_during_push(self):
        real_run = sync_global_skills.run_command
        for trigger in ("head-capture", "push"):
            with self.subTest(trigger=trigger):
                source_dir, remote_dir = self.publication_repository(suffix=f"-{trigger}")
                original_head = sync_global_skills.repository_head(source_dir)
                changed = source_dir / "verify-skill/SKILL.md"
                changed.write_bytes(changed.read_bytes() + b"\nValidated change.\n")
                frozen_heads = []
                fetch_count = 0

                def create_concurrent_commit():
                    (source_dir / "code-skill/late-commit.md").write_text("Unvalidated concurrent commit.\n", encoding="utf-8")
                    real_run(["git", "add", "--", "code-skill/late-commit.md"], cwd=source_dir)
                    real_run(["git", "commit", "-m", "Concurrent work"], cwd=source_dir)

                def commit_after_validation(command, cwd=None, env=None):
                    nonlocal fetch_count
                    if cwd == source_dir and command[:2] == ["git", "fetch"]:
                        fetch_count += 1
                    if command[:3] == ["git", "push", "publication"]:
                        frozen_heads.append(command[3].split(":", 1)[0])
                        if trigger == "push":
                            create_concurrent_commit()
                    result = real_run(command, cwd=cwd, env=env)
                    if trigger == "head-capture" and cwd == source_dir and fetch_count == 2 and command == ["git", "rev-parse", "HEAD^{tree}"]:
                        create_concurrent_commit()
                    return result

                expected_error = "differs from the validated tree" if trigger == "head-capture" else "Remote received only validated commit"
                with mock.patch.object(sync_global_skills, "run_command", side_effect=commit_after_validation), mock.patch("builtins.print"), self.assertRaisesRegex(RuntimeError, expected_error):
                    sync_global_skills.push("label/only", source_dir, "Freeze validated commit", False, include_paths=["verify-skill/SKILL.md"])
                remote_head = sync_global_skills.remote_branch_head(source_dir, sync_global_skills.publication_upstream(source_dir))
                if trigger == "head-capture":
                    self.assertEqual(frozen_heads, [])
                    self.assertEqual(remote_head, original_head)
                else:
                    self.assertEqual(len(frozen_heads), 1)
                    self.assertRegex(frozen_heads[0], r"^[0-9a-f]{40}$")
                    self.assertEqual(remote_head, frozen_heads[0])
                self.assertNotEqual(sync_global_skills.repository_head(source_dir), remote_head)

    def test_push_accepts_staged_deletion_and_both_rename_paths(self):
        source_dir, remote_dir = self.publication_repository()
        removed = "code-skill/references/coding-approach.md"
        old_name = "code-skill/references/parallelization.md"
        new_name = "code-skill/references/concurrency.md"
        sync_global_skills.run_command(["git", "rm", "--", removed], cwd=source_dir)
        sync_global_skills.run_command(["git", "mv", old_name, new_name], cwd=source_dir)
        with mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Selected deletion and rename", False, include_paths=[removed, old_name, new_name])
        self.assertFalse((source_dir / removed).exists())
        self.assertFalse((source_dir / old_name).exists())
        self.assertTrue((source_dir / new_name).is_file())
        self.assertEqual(sync_global_skills.source_worktree_paths(source_dir), [])

    @unittest.skipIf(sys.platform == "win32", "requires a native POSIX executable-bit filesystem")
    def test_push_candidate_preserves_native_executable_mode(self):
        source_dir, remote_dir = self.publication_repository()
        added = source_dir / "code-skill/scripts/executable-example.py"
        added.write_text("print('mode fixture')\n", encoding="utf-8")
        added.chmod(0o755)
        sync_global_skills.run_command(["git", "config", "core.filemode", "true"], cwd=source_dir)
        with mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Native executable mode", False, include_paths=[added.relative_to(source_dir).as_posix()])
        self.assertTrue(sync_global_skills.run_command(["git", "ls-tree", "HEAD", "--", added.relative_to(source_dir).as_posix()], cwd=source_dir).stdout.startswith("100755"))

    def test_push_candidate_preserves_explicit_index_mode_when_filemode_is_false(self):
        source_dir, remote_dir = self.publication_repository()
        relative_path = "code-skill/scripts/code_rule_guard.py"
        sync_global_skills.run_command(["git", "config", "core.filemode", "false"], cwd=source_dir)
        sync_global_skills.run_command(["git", "update-index", "--chmod=+x", "--", relative_path], cwd=source_dir)
        with mock.patch("builtins.print"):
            sync_global_skills.push("label/only", source_dir, "Explicit index mode", False, include_paths=[relative_path])
        self.assertTrue(sync_global_skills.run_command(["git", "ls-tree", "HEAD", "--", relative_path], cwd=source_dir).stdout.startswith("100755"))

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
            sync_global_skills.install_global_agents(SKILLS_DIR, target_dir)
            matching = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
            (self.codex_root / "AGENTS.md").write_text("# stale\n", encoding="utf-8")
            stale = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
        self.assertEqual(matching["status"], "pass")
        self.assertEqual(stale["status"], "fail")
        self.assertIn("differs", stale["reason"])



if __name__ == "__main__":
    unittest.main()

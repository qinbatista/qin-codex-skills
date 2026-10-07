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

    def test_english_readme_uses_template_and_current_contract(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        template = sync_global_skills.ENGLISH_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template
        self.assertEqual(readme, expected)
        self.assertLess(len(template.split()), 600)
        self.assertNotIn("<!-- EXECUTION_DOMAIN_TABLE -->", readme)
        for concept in ("This repository maintains eight global Codex skills", "## What each skill does", "implementation steps", "Missing memory", "in the active task", "project testing Skills", "real affected-case checks", "unpinned", "Project memories stay isolated"):
            self.assertIn(concept, readme)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"({skill_name}/SKILL.md)", readme)


    def test_chinese_readme_is_compact_and_has_the_same_policy(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="zh")
        template = sync_global_skills.CHINESE_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        expected = template
        self.assertEqual(readme, expected)
        self.assertLess(len(template.splitlines()), 80)
        for concept in ("本仓库维护八个可复用的全局 Codex Skill", "## 各 Skill 的职责", "先简述任务目标", "记忆缺失时直接跳过", "在当前任务内", "项目测试 Skill", "真实受影响场景", "本地记忆", "项目记忆互相隔离"):
            self.assertIn(concept, readme)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"({skill_name}/SKILL.md)", readme)

    def test_readme_documents_installation_preservation_and_portable_entry(self):
        readme = sync_global_skills.build_readme(self.primary_skill_paths(), language="en")
        for concept in ("deploy --source-dir .", "py -3 -B", "locking, backup, and recovery", "preserves unrelated skills, user AGENTS, and existing private history", "install-global-agents --source-dir .", "restorable backup", "before staging or remote writes"):
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

            with mock.patch.object(sync_global_skills.subprocess, "run", return_value=completed) as runner:
                REAL_RUN_RELEASE_GATE(source_dir, skills_dir, "deployed")

            command = runner.call_args.args[0]
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

    def test_push_cli_defaults_to_the_maintained_repository_source(self):
        argv = ["sync_global_skills.py", "push", "--message", "source-first smoke"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(sync_global_skills, "push") as publisher:
            sync_global_skills.main()
        publisher.assert_called_once_with(
            sync_global_skills.DEFAULT_REPOSITORY,
            sync_global_skills.DEFAULT_SOURCE_DIR,
            "source-first smoke",
            False,
            Path.home() / ".agents" / "skills",
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

    def test_push_commits_the_source_repository_and_verifies_remote_head(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            source_dir = sandbox / "source"
            remote_dir = sandbox / "remote.git"
            source_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(source_dir, SKILLS_DIR)
            (source_dir / "AGENTS.md").write_text((SKILLS_DIR / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
            local_map = source_dir / "Knowledge.md"
            local_map.write_text("Original project map.\n", encoding="utf-8")
            sync_global_skills.run_command(["git", "init"], cwd=source_dir)
            sync_global_skills.run_command(["git", "branch", "-M", "master"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.name", "Source Publish Test"], cwd=source_dir)
            sync_global_skills.run_command(["git", "config", "user.email", "source-publish@example.invalid"], cwd=source_dir)
            if sys.platform == "win32":
                sync_global_skills.run_command(["git", "config", "core.longpaths", "true"], cwd=source_dir)
            sync_global_skills.run_command(["git", "add", "-A"], cwd=source_dir)
            sync_global_skills.run_command(["git", "commit", "-m", "initial"], cwd=source_dir)
            sync_global_skills.run_command(["git", "init", "--bare", str(remote_dir)], cwd=sandbox)
            if sys.platform == "win32":
                sync_global_skills.run_command(["git", "config", "core.longpaths", "true"], cwd=remote_dir)
            sync_global_skills.run_command(["git", "remote", "add", "origin", str(remote_dir)], cwd=source_dir)
            sync_global_skills.run_command(["git", "push", "-u", "origin", "master"], cwd=source_dir)
            skill_path = source_dir / "verify-skill" / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nSource-first publish smoke.\n", encoding="utf-8")
            testing_skill_path = source_dir / sync_global_skills.PROJECT_TESTING_SKILL / "SKILL.md"
            testing_skill_path.parent.mkdir(parents=True)
            testing_skill_path.write_text("---\nname: testing-skill\ndescription: Project test inventory.\n---\n", encoding="utf-8")
            local_map.write_text("Keep this local project map update.\n", encoding="utf-8")
            local_note = source_dir / "local note with spaces.md"
            local_note.write_text("Keep this unrelated note.\n", encoding="utf-8")
            previous_head = sync_global_skills.repository_head(source_dir)
            task_cache_root = source_dir / "Cache" / "temp-push-state"
            state_file = task_cache_root / "state" / "management-skill-sync.json"
            with mock.patch.object(sync_global_skills, "DEFAULT_PROJECT_ROOT", source_dir), mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(task_cache_root)}), mock.patch("builtins.print") as printer:
                sync_global_skills.push("fixture/repository", source_dir, "Publish source change", False)
            current_head = sync_global_skills.repository_head(source_dir)
            remote_head = sync_global_skills.remote_branch_head(source_dir, "master")
            self.assertNotEqual(previous_head, current_head)
            self.assertEqual(current_head, remote_head)
            self.assertEqual(set(sync_global_skills.source_worktree_paths(source_dir)), {Path("Knowledge.md"), Path(local_note.name)})
            self.assertEqual(local_map.read_text(encoding="utf-8"), "Keep this local project map update.\n")
            self.assertEqual(local_note.read_text(encoding="utf-8"), "Keep this unrelated note.\n")
            self.assertEqual(sync_global_skills.run_command(["git", "show", "HEAD:Knowledge.md"], cwd=source_dir).stdout, "Original project map.\n")
            published_names = sync_global_skills.run_command(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=source_dir).stdout.splitlines()
            self.assertNotIn("Knowledge.md", published_names)
            self.assertNotIn(local_note.name, published_names)
            self.assertIn(testing_skill_path.relative_to(source_dir).as_posix(), published_names)
            self.assertEqual(sync_global_skills.run_command(["git", "show", "HEAD:.agents/skills/testing-skill/SKILL.md"], cwd=source_dir).stdout, testing_skill_path.read_text(encoding="utf-8"))
            printer.assert_any_call("Preserved excluded local changes:")
            self.assertTrue(state_file.is_file())
            real_remote_head = sync_global_skills.remote_branch_head

            def modify_source_after_remote_readback(repository_dir, branch_name):
                observed = real_remote_head(repository_dir, branch_name)
                skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nNew unpublished change.\n", encoding="utf-8")
                return observed

            with mock.patch.object(sync_global_skills, "DEFAULT_PROJECT_ROOT", source_dir), mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(task_cache_root)}), mock.patch.object(sync_global_skills, "remote_branch_head", side_effect=modify_source_after_remote_readback):
                with self.assertRaisesRegex(RuntimeError, "publishable source changes remain"):
                    sync_global_skills.push("fixture/repository", source_dir, "No new change yet", False)
            self.assertEqual(real_remote_head(source_dir, "master"), current_head)
            self.assertIn(Path("verify-skill/SKILL.md"), sync_global_skills.source_worktree_paths(source_dir))
            unrelated_skill_path = source_dir / ".agents" / "skills" / "other-skill" / "SKILL.md"
            unrelated_skill_path.parent.mkdir(parents=True)
            unrelated_skill_path.write_text("---\nname: other-skill\ndescription: Unrelated.\n---\n", encoding="utf-8")
            sync_global_skills.run_command(["git", "add", "--", str(unrelated_skill_path.relative_to(source_dir))], cwd=source_dir)
            with mock.patch.object(sync_global_skills, "DEFAULT_PROJECT_ROOT", source_dir), mock.patch.dict(sync_global_skills.os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(task_cache_root)}):
                with self.assertRaisesRegex(RuntimeError, "non-public or unrelated staged paths"):
                    sync_global_skills.push("fixture/repository", source_dir, "must not publish unrelated skill", False)
            self.assertEqual(real_remote_head(source_dir, "master"), current_head)

    def test_source_worktree_paths_preserves_unusual_names_and_rename_sources(self):
        output = ' M Knowledge.md\0?? local "quoted"\nnotes.md\0R  notes.md\0verify-skill/SKILL.md\0'
        with mock.patch.object(sync_global_skills, "run_command", return_value=mock.Mock(stdout=output)):
            paths = sync_global_skills.source_worktree_paths(Path("fixture"))
        self.assertEqual(paths, [Path("Knowledge.md"), Path('local "quoted"\nnotes.md'), Path("notes.md"), Path("verify-skill/SKILL.md")])

    def test_push_safety_scan_rejects_new_fixture_before_publication_mutations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(source_dir, SKILLS_DIR)
            sync_global_skills.run_command(["git", "init"], cwd=source_dir)
            unsafe = source_dir / sync_global_skills.PROJECT_TESTING_SKILL / "tests" / "fixtures" / "benchmark-public.json"
            unsafe.parent.mkdir(parents=True, exist_ok=True)
            unsafe.write_text(json.dumps({"sample": "sk-" + "a" * 24}), encoding="utf-8")
            before_readmes = [(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")]
            with mock.patch.object(sync_global_skills, "render_source_readmes", wraps=sync_global_skills.render_source_readmes) as renderer, mock.patch.object(sync_global_skills, "run_command", wraps=sync_global_skills.run_command) as runner:
                with self.assertRaisesRegex(RuntimeError, "benchmark-public.json: secret-like content"):
                    sync_global_skills.push("fixture/repository", source_dir, "must not publish", False)
            self.release_gate.assert_called_once()
            renderer.assert_not_called()
            self.assertEqual([(source_dir / name).read_bytes() for name in ("README.md", "README.zh.md")], before_readmes)
            self.assertEqual(sync_global_skills.staged_source_paths(source_dir), [])
            self.assertEqual([call.args[0][1] for call in runner.call_args_list], ["rev-parse"])

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
            if sys.platform == "win32":
                sync_global_skills.run_command(["git", "config", "core.longpaths", "true"], cwd=source_dir)
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
            sync_global_skills.install_global_agents(SKILLS_DIR, target_dir)
            matching = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
            (self.codex_root / "AGENTS.md").write_text("# stale\n", encoding="utf-8")
            stale = sync_global_skills.global_agents_parity(SKILLS_DIR, target_dir)
        self.assertEqual(matching["status"], "pass")
        self.assertEqual(stale["status"], "fail")
        self.assertIn("differs", stale["reason"])



if __name__ == "__main__":
    unittest.main()

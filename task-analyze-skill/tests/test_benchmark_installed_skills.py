import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_installed_skills.py"
SPEC = importlib.util.spec_from_file_location("installed_benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class InstalledBenchmarkTests(unittest.TestCase):
    def test_counterbalanced_default_and_recorded_pilot(self):
        self.assertEqual(benchmark.trial_order(3), [
            (1, "control"), (1, "installed"), (2, "installed"),
            (2, "control"), (3, "control"), (3, "installed")])
        self.assertEqual(benchmark.trial_order(1, "installed"), [(1, "installed")])

    def test_isolation_removes_parent_runtime_but_preserves_user_home(self):
        inherited = {"CODEX_HOME": "/parent", "CODEX_SQLITE_DB": "/parent/state.sqlite",
                     "CODEX_THREAD_ID": "parent", "CODEX_TASK_ANALYZE_ENTRY_CONTEXT": "1",
                     "CODEX_OBSIDIAN_VAULT": "/vault", "HOME": "/user", "USERPROFILE": "user",
                     "PATH": "tools", "OPENAI_API_KEY": "test-placeholder"}
        environment = benchmark.isolated_environment(Path("isolated-codex"), inherited)
        self.assertEqual(environment["CODEX_HOME"], "isolated-codex")
        self.assertEqual(environment["CODEX_SQLITE_HOME"], "isolated-codex")
        for key in ("CODEX_SQLITE_DB", "CODEX_THREAD_ID", "CODEX_TASK_ANALYZE_ENTRY_CONTEXT", "CODEX_OBSIDIAN_VAULT"):
            self.assertNotIn(key, environment)
        self.assertEqual(environment["HOME"], "/user")
        self.assertEqual(environment["USERPROFILE"], "user")
        self.assertEqual(inherited["CODEX_HOME"], "/parent")

    def test_staging_materializes_inert_fixture_and_rejects_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "runner.py.in").write_text("value = 7\n")
            benchmark.stage_fixture(source, root / "workspace")
            self.assertEqual((root / "workspace" / "runner.py").read_text(), "value = 7\n")
            self.assertFalse((root / "workspace" / "runner.py.in").exists())
            (source / "runner.py").write_text("other")
            with self.assertRaisesRegex(ValueError, "collision"):
                benchmark.stage_fixture(source, root / "collision")

    def test_auth_is_linked_without_reading_bytes_and_control_has_no_managed_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth = root / "source-auth.json"
            auth.write_text("test-only-placeholder")
            with patch.object(Path, "read_text", side_effect=AssertionError("auth must not be read")):
                benchmark.materialize_home(root / "runtime", root, False, auth)
            link = root / "runtime" / "auth.json"
            self.assertTrue(link.samefile(auth))
            if os.name != "nt":
                self.assertTrue(link.is_symlink())
            self.assertFalse((root / "runtime" / "skills").exists())
            self.assertFalse((root / "runtime" / "AGENTS.md").exists())
            link.unlink()
            self.assertEqual(auth.read_text(), "test-only-placeholder")

    def test_windows_auth_hardlink_fallback_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth = root / "source-auth.json"
            auth.write_text("test-only-placeholder")
            denied = OSError("Symlink privilege unavailable")
            denied.winerror = 1314
            with patch.object(benchmark.os, "name", "nt"), patch.object(Path, "symlink_to", side_effect=denied), patch.object(Path, "read_text", side_effect=AssertionError("auth must not be read")):
                benchmark.materialize_home(root / "runtime", root, False, auth)
            link = root / "runtime" / "auth.json"
            self.assertFalse(link.is_symlink())
            self.assertTrue(link.samefile(auth))
            link.unlink()
            self.assertEqual(auth.read_text(), "test-only-placeholder")

    def test_command_fixes_model_effort_approval_and_workspace_sandbox(self):
        command = benchmark.codex_command("codex-test.py", "gpt-6-astra", "ultra")
        self.assertEqual(command[:3], [sys.executable, "codex-test.py", "exec"])
        self.assertIn('model_reasoning_effort="ultra"', command)
        self.assertIn('approval_policy="never"', command)
        self.assertIn("workspace-write", command)
        self.assertEqual(command[-1], "-")

    def test_skill_read_requires_successful_completed_read_command(self):
        def event(command, exit_code=0, event_type="item.completed"):
            return json.dumps({"type": event_type, "item": {"type": "command_execution", "command": command,
                                                           "exit_code": exit_code, "aggregated_output": "actual file content"}})
        output = "\n".join([
            event("cat /runtime/skills/code-skill/SKILL.md"),
            event("cat /runtime/skills/workflow-skill/SKILL.md", 1),
            event("echo /runtime/skills/verify-skill/SKILL.md"),
            event("cat /runtime/skills/project-memory-skill/SKILL.md", 0, "item.started")])
        names = ["code-skill/SKILL.md", "workflow-skill/SKILL.md", "verify-skill/SKILL.md", "project-memory-skill/SKILL.md"]
        self.assertEqual(benchmark.skill_read_evidence(output, names), dict(zip(names, [True, False, False, False])))

    def write_session(self, root, name, *, model="gpt-6-astra", tokens=100, complete=True):
        sessions = root / "sessions"
        sessions.mkdir(exist_ok=True)
        events = [
            {"type": "session_meta", "payload": {"id": name, "cli_version": "test", "model_provider": "test"}},
            {"type": "turn_context", "payload": {"model": model, "effort": "ultra"}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
                "input_tokens": tokens, "cached_input_tokens": 20, "output_tokens": 5}}}}]
        if complete:
            events.append({"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 10}})
        (sessions / f"{name}.jsonl").write_text("\n".join(map(json.dumps, events)))

    def test_runtime_identity_and_all_nested_tokens_are_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_session(root, "root")
            stdout = '\n'.join(map(json.dumps, [
                {"type": "thread.started", "thread_id": "root"},
                {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 5}}]))
            result = benchmark.evidence_from_sessions(root, stdout, "gpt-6-astra|ultra")
            self.assertTrue(result["runtime_pass"])
            self.assertEqual(result["tokens"]["total_tokens"], 105)
            self.write_session(root, "nested", tokens=200)
            result = benchmark.evidence_from_sessions(root, stdout, "gpt-6-astra|ultra")
            self.assertFalse(result["runtime_pass"])
            self.assertEqual(result["session_count"], 2)
            self.assertEqual(result["tokens"]["total_tokens"], 310)

    def test_exit_or_output_usage_alone_is_not_model_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            stdout = json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 5}})
            result = benchmark.evidence_from_sessions(Path(directory), stdout, "gpt-6-astra|ultra")
            self.assertFalse(result["runtime_pass"])
            self.assertFalse(result["tokens_complete"])
            self.assertIsNone(result["tokens"]["total_tokens"])
            self.assertEqual(result["event_token_lower_bound"]["total_tokens"], 105)

    def test_wrong_model_or_unfinished_turn_fails(self):
        for model, complete in (("gpt-5.6-luna", True), ("gpt-6-astra", False)):
            with self.subTest(model=model, complete=complete), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_session(root, "root", model=model, complete=complete)
                stdout = '\n'.join(map(json.dumps, [{"type": "thread.started", "thread_id": "root"}, {"type": "turn.completed"}]))
                self.assertFalse(benchmark.evidence_from_sessions(root, stdout, "gpt-6-astra|ultra")["runtime_pass"])

    def test_private_copy_does_not_follow_auth_or_workspace_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "result.txt").write_text("safe")
            private = root / "private"
            private.mkdir()
            (private / "auth.json").write_text("test-placeholder")
            try:
                (source / "linked").symlink_to(private, target_is_directory=True)
            except OSError as error:
                if os.name == "nt" and getattr(error, "winerror", None) == 1314:
                    self.skipTest("Windows requires symlink permission")
                raise
            benchmark.copy_regular_tree(source, root / "retained")
            self.assertEqual((root / "retained" / "result.txt").read_text(), "safe")
            self.assertFalse((root / "retained" / "linked").exists())

    def record(self, arm, seconds, tokens, status="pass"):
        return {"condition": arm, "status": status, "total_seconds": seconds, "tokens_complete": True,
                "tokens": {key: tokens for key in benchmark.TOKEN_FIELDS}}

    def test_win_requires_both_quality_gates_and_both_primary_metrics(self):
        records = [self.record("control", 10, 100), self.record("installed", 8, 80)]
        result = benchmark.summarize(records, 1)
        self.assertTrue(result["installed_wins_time_and_tokens"])
        self.assertEqual(result["token_saving_percent"], 20)
        records[1]["status"] = "fail"
        result = benchmark.summarize(records, 1)
        self.assertFalse(result["installed_wins_time_and_tokens"])
        self.assertIsNone(result["token_saving_percent"])
        result = benchmark.summarize([self.record("control", 10, 100), self.record("installed", 8, 101)], 1)
        self.assertFalse(result["installed_wins_time_and_tokens"])

    def test_single_condition_pilot_never_claims_comparative_win(self):
        result = benchmark.summarize([self.record("installed", 1, 1)], 1, "installed")
        self.assertFalse(result["installed_wins_time_and_tokens"])
        self.assertFalse(result["all_acceptance_passed"])

    def test_hidden_execution_preserves_failure_output_and_timing(self):
        result = benchmark.run_captured([sys.executable, "-c", "import sys; print('evidence'); sys.exit(3)"],
                                       cwd=Path.cwd(), environment=os.environ.copy(), timeout=10)
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual(result["stdout"].strip(), "evidence")
        self.assertGreater(result["elapsed_seconds"], 0)

    def test_unicode_streams_use_utf8_despite_inherited_legacy_python_encoding(self):
        inherited = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="ascii:strict")
        environment = benchmark.isolated_environment(Path("isolated-codex"), inherited)
        payload = "中文 café 🧪\n"
        program = (
            "import json, sys\n"
            "value = sys.stdin.read()\n"
            "print(json.dumps({'input': value, 'stdout_encoding': sys.stdout.encoding}, ensure_ascii=False))\n"
            "print(value, end='', file=sys.stderr)\n"
        )
        result = benchmark.run_captured([sys.executable, "-c", program], cwd=Path.cwd(),
                                       environment=environment, timeout=10, input_text=payload)
        self.assertEqual(result["exit_code"], 0, result["stderr"])
        self.assertIsNone(result["failure"])
        self.assertEqual(json.loads(result["stdout"]), {"input": payload, "stdout_encoding": "utf-8"})
        self.assertEqual(result["stderr"], payload)
        self.assertEqual(inherited["PYTHONIOENCODING"], "ascii:strict")
        for name in ("HOME", "USERPROFILE"):
            self.assertEqual(environment.get(name), inherited.get(name))

    def test_invalid_counts_cannot_pass_or_create_false_savings(self):
        base = {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 5, "total_tokens": 105}
        for mutation in ({"cached_input_tokens": 200}, {"total_tokens": 1}, {"uncached_input_tokens": 1},
                         {"input_tokens": -1}, {"output_tokens": True}, {"output_tokens": 1.5},
                         {"output_tokens": "5"}, {"reasoning_output_tokens": -1}, {"cache_write_input_tokens": False}):
            with self.subTest(mutation=mutation):
                self.assertFalse(benchmark.validated_usage(dict(base, **mutation))["valid"])
        result = benchmark.validated_usage(base)
        self.assertTrue(result["valid"])
        self.assertIsNone(result["counts"]["reasoning_output_tokens"])
        self.assertEqual(result["counts"]["uncached_input_tokens"], 80)

    def test_stdout_rollout_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_session(root, "root")
            stdout = '\n'.join(map(json.dumps, [{"type": "thread.started", "thread_id": "root"},
                {"type": "turn.completed", "usage": {"input_tokens": 500, "cached_input_tokens": 20, "output_tokens": 5}}]))
            evidence = benchmark.evidence_from_sessions(root, stdout, "gpt-6-astra|ultra")
            self.assertFalse(evidence["runtime_pass"])
            self.assertFalse(evidence["stdout_usage_reconciled"])

    def test_intermediate_model_or_effort_changes_fail_even_after_return(self):
        mutations = [
            [{"type": "event_msg", "payload": {"type": "model_reroute", "from_model": "gpt-6-astra", "to_model": "gpt-5.6-luna"}},
             {"type": "event_msg", "payload": {"type": "model_reroute", "from_model": "gpt-5.6-luna", "to_model": "gpt-6-astra"}}],
            [{"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "low"}},
             {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "ultra"}}],
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_session(root, "root")
                path = root / "sessions" / "root.jsonl"
                with path.open("a") as stream:
                    stream.write("\n" + "\n".join(map(json.dumps, mutation)))
                self.assertFalse(benchmark.pair_history(path, "gpt-6-astra|ultra")["valid"])

    def test_listing_echoed_code_and_missing_output_are_not_content_reads(self):
        for command in ("rg --files /skills/code-skill/SKILL.md", "echo cat /skills/code-skill/SKILL.md",
                        'python3 -c "print(\'p.read_text()\')"', "rg -l keyword /skills/code-skill/SKILL.md"):
            with self.subTest(command=command):
                self.assertFalse(benchmark.content_read_command(command))
        for command in ("cat /skills/code-skill/SKILL.md", "rg -n keyword /skills/code-skill/SKILL.md",
                        "python3 -B - <<'PY'\nfrom pathlib import Path\nprint(Path('code-skill/SKILL.md').read_text())\nPY"):
            with self.subTest(command=command):
                self.assertTrue(benchmark.content_read_command(command))
        stdout = json.dumps({"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                             "command": "cat /skills/code-skill/SKILL.md", "aggregated_output": ""}})
        self.assertFalse(benchmark.skill_read_evidence(stdout, ["code-skill/SKILL.md"])["code-skill/SKILL.md"])

    def test_mixed_listing_and_python_content_read_preserves_heredoc(self):
        import shlex
        inner = ("pwd; rg --files -g 'AGENTS.md'; python3 -B - <<'PY'\n"
                 "from pathlib import Path\n"
                 "for relative in ['code-skill/SKILL.md', 'workflow-skill/references/readable-ui.md']:\n"
                 "    print(Path(relative).read_text())\nPY")
        command = "/bin/zsh -lc " + shlex.quote(inner)
        event = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                 "command": command, "aggregated_output": "actual skill contents"}}
        names = ["code-skill/SKILL.md", "workflow-skill/references/readable-ui.md"]
        self.assertEqual(benchmark.skill_read_evidence(json.dumps(event), names), dict.fromkeys(names, True))

    def test_mixed_commands_do_not_attribute_listed_or_echoed_paths_to_other_reads(self):
        name = "code-skill/SKILL.md"
        commands = [f"rg --files {name}; echo done", f"cat other.md; echo {name}",
                    f"printf '%s' ';'; echo cat {name}", f"pwd; rg --files {name}"]
        for command in commands:
            with self.subTest(command=command):
                event = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                         "command": command, "aggregated_output": "some output"}}
                self.assertFalse(benchmark.skill_read_evidence(json.dumps(event), [name])[name])
        event["item"].update(command=f"pwd; cat {name}", aggregated_output="")
        self.assertFalse(benchmark.skill_read_evidence(json.dumps(event), [name])[name])

    def test_windows_wrappers_and_absolute_python_are_host_independent(self):
        commands = [
            'powershell.exe -NoProfile -NonInteractive -Command "Get-Content -Raw code-skill/SKILL.md"',
            'pwsh.exe -NoProfile -COMMAND "Get-Content -Raw code-skill/SKILL.md"',
            r'''"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -Command "Get-Content -Raw 'code-skill\SKILL.md'"''',
            r'''"C:\Program Files\Python\python.exe" -c "from pathlib import Path; print(Path('code-skill/SKILL.md').read_text())"''',
            r'''C:\Python\python.exe -c "from pathlib import Path; print(Path('code-skill/SKILL.md').read_text())"''',
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                         "command": command, "aggregated_output": "actual skill contents"}}
                self.assertTrue(benchmark.skill_read_evidence(json.dumps(event), ["code-skill/SKILL.md"])["code-skill/SKILL.md"])

    def test_windows_wrapped_echo_and_listing_are_not_content_reads(self):
        for body in ["Write-Output 'Get-Content code-skill/SKILL.md'", "echo code-skill/SKILL.md",
                     "Get-ChildItem code-skill/SKILL.md", "rg --files code-skill/SKILL.md"]:
            with self.subTest(body=body):
                event = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0,
                         "command": 'powershell.exe -NoProfile -Command "' + body + '"',
                         "aggregated_output": "some output"}}
                self.assertFalse(benchmark.skill_read_evidence(json.dumps(event), ["code-skill/SKILL.md"])["code-skill/SKILL.md"])

    def test_frozen_checker_imports_and_prompt_use_frozen_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            helper = source / "code-skill" / "scripts" / "hidden_process.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("original helper")
            fixture = source / "task-analyze-skill" / "tests" / "fixture"
            (fixture / "input").mkdir(parents=True)
            (fixture / "input" / "runner.py.in").write_text("input")
            checker = fixture / "check.py"
            checker.write_text("original checker")
            prompt = root / "prompt.txt"
            prompt.write_text(str(checker))
            output = root / "output"
            output.mkdir()
            args = SimpleNamespace(source=source, output_dir=output, fixture=fixture / "input", check_root=fixture,
                                   check_command=["{python}", str(checker)], check_dependency=[], prompt_file=prompt,
                                   model="gpt-6-astra", effort="ultra", sandbox="danger-full-access")
            with patch.object(benchmark, "freeze_source", side_effect=lambda a, b: shutil.copytree(a, b)):
                text = benchmark.prepare_frozen_inputs(args)
            self.assertTrue(benchmark.frozen_inputs_unchanged(args))
            self.assertIn(str(output / "private-source"), text)
            self.assertIn("task assignment; runtime proof", text)
            self.assertIn("gpt-6-astra|ultra", text)
            helper.write_text("later live source edit")
            self.assertTrue(benchmark.frozen_inputs_unchanged(args))
            (args.source / "code-skill" / "scripts" / "hidden_process.py").write_text("changed frozen helper")
            self.assertFalse(benchmark.frozen_inputs_unchanged(args))

    def test_cancellation_stops_owned_process_before_returning_evidence(self):
        process = Mock(pid=123, returncode=-9)
        process.communicate.side_effect = [KeyboardInterrupt(), ("partial output", "partial error")]
        with patch.object(benchmark.subprocess, "Popen", return_value=process), patch.object(benchmark, "stop_owned_process") as stop:
            result = benchmark.run_captured(["test"], cwd=Path.cwd(), environment={}, timeout=10)
        stop.assert_called_once_with(process)
        self.assertEqual(result["failure"], "cancelled")
        self.assertEqual(result["stdout"], "partial output")


if __name__ == "__main__":
    unittest.main()

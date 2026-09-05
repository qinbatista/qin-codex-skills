"""Portable runtime binding tests; no live model calls or interactive windows."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolver = load("executable_binding_tests", "codex_executable.py")
receipt = load("receipt_binding_tests", "model_execution_receipt.py")


class CodexExecutableTests(unittest.TestCase):
    def test_explicit_path_or_explicit_cli_name_is_never_replaced(self):
        with patch.object(resolver, "active_codex_executable", side_effect=AssertionError("no discovery")):
            for argument in ("/configured/older-codex", "fixtures/fake_codex.py", "codex"):
                result = resolver.resolve_codex_executable(argument, explicit=True, environ={resolver.RUNTIME_EXECUTABLE_ENV: "invalid"})
                self.assertEqual(result, {"path": argument, "source": "explicit_argument"})

    def test_configured_native_runtime_precedes_ancestor_and_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "codex.exe"
            executable.write_text("native fixture")
            executable.chmod(0o755)
            with patch.object(resolver, "active_codex_executable", side_effect=AssertionError("no discovery")):
                result = resolver.resolve_codex_executable(environ={resolver.RUNTIME_EXECUTABLE_ENV: str(executable)})
            self.assertEqual(result, {"path": str(executable.resolve()), "source": "configured_runtime"})

    def test_invalid_configured_runtime_does_not_silently_run_stale_path(self):
        with self.assertRaisesRegex(ValueError, "existing native codex executable"):
            resolver.resolve_codex_executable(environ={resolver.RUNTIME_EXECUTABLE_ENV: "a-gui-app"})

    def test_active_runtime_precedes_stale_path(self):
        with patch.object(resolver, "active_codex_executable", return_value="active/codex"), patch.object(resolver.shutil, "which", side_effect=AssertionError("no PATH fallback")):
            self.assertEqual(resolver.resolve_codex_executable(environ={}), {"path": "active/codex", "source": "active_codex_ancestor"})

    def test_unavailable_ancestor_falls_back_to_path_without_installing(self):
        with patch.object(resolver, "active_codex_executable", return_value=None), patch.object(resolver.shutil, "which", return_value="installed/codex"):
            self.assertEqual(resolver.resolve_codex_executable(environ={}), {"path": "installed/codex", "source": "path"})

    def test_ancestor_walk_uses_exact_codex_name_and_stops_at_cycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex = root / "codex"
            codex.write_text("fixture")
            codex.chmod(0o755)
            graph = {30: (20, str(root / "not-codex")), 20: (10, str(codex))}
            with patch.object(resolver.sys, "platform", "darwin"), patch.object(resolver.os, "getppid", return_value=30), patch.object(resolver, "_posix_process", side_effect=lambda pid: graph[pid]):
                self.assertEqual(resolver.active_codex_executable(), str(codex.resolve()))
            with patch.object(resolver.sys, "platform", "darwin"), patch.object(resolver.os, "getppid", return_value=30), patch.object(resolver, "_posix_process", return_value=(30, str(root / "not-codex"))) as lookup:
                self.assertIsNone(resolver.active_codex_executable())
                self.assertEqual(lookup.call_count, 1)

    def test_windows_ancestor_branch_uses_native_process_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex = Path(temporary) / "codex.exe"
            codex.write_text("fixture")
            codex.chmod(0o755)
            with patch.object(resolver.sys, "platform", "win32"), patch.object(resolver.os, "getppid", return_value=30), patch.object(resolver, "_windows_process_table", return_value={30: 20, 20: 1}), patch.object(resolver, "_windows_executable", side_effect=lambda pid: str(codex) if pid == 20 else "not-codex.exe"):
                self.assertEqual(resolver.active_codex_executable(), str(codex.resolve()))

    @unittest.skipUnless(sys.platform in {"darwin", "linux"}, "native POSIX identity")
    def test_native_posix_lookup_reads_current_process_executable(self):
        parent, executable = resolver._posix_process(os.getpid())
        self.assertEqual(parent, os.getppid())
        self.assertTrue(Path(executable).is_file())

    @unittest.skipUnless(sys.platform == "win32", "native Windows identity")
    def test_native_windows_lookup_reads_current_process_executable(self):
        self.assertEqual(resolver._windows_process_table()[os.getpid()], os.getppid())
        executable = resolver._windows_executable(os.getpid())
        # Windows Store Python exposes an execution alias in sys.executable.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
        kernel.GetModuleFileNameW.restype = wintypes.DWORD
        buffer = ctypes.create_unicode_buffer(32768)
        self.assertGreater(kernel.GetModuleFileNameW(None, buffer, len(buffer)), 0)
        self.assertTrue(Path(executable).samefile(buffer.value))

    def test_command_builder_uses_resolved_executable_and_preserves_selected_pair(self):
        args = argparse.Namespace(codex_bin="codex", model="gpt-6-astra", effort="ultra", sandbox="read-only", ignore_user_config=False)
        binding = {"path": "active/codex", "source": "active_codex_ancestor"}
        with patch.object(receipt, "resolve_codex_executable", return_value=binding):
            command = receipt.build_codex_exec_command(args)
        self.assertEqual(command[0], "active/codex")
        self.assertIn("gpt-6-astra", command)
        self.assertIn('model_reasoning_effort="ultra"', command)
        self.assertIn('approval_policy="never"', command)
        self.assertEqual(args.codex_executable_resolution, binding)

    def test_older_client_rejection_is_operational_and_keeps_selected_model(self):
        message = "The gpt-6-astra model requires a newer version of Codex."
        summary = receipt.parse_stdout_events(json.dumps({"type": "turn.failed", "error": {"message": message}}))
        detail = receipt.infer_failure_detail(SimpleNamespace(returncode=1), False, summary, "", None, False, False, False, False)
        self.assertEqual(detail, "client_version_incompatible")
        self.assertEqual(receipt.failure_class_for_detail(detail), "execution")
        self.assertNotIn(message, json.dumps(summary))
        failure = receipt.annotate_operational_fallback({"status": "fail", "turn_completed": False, "failure_class": "execution", "failure_detail": detail, "tokens": {"total_tokens": 0}})
        self.assertFalse(failure["fallback_eligible"])


if __name__ == "__main__":
    unittest.main()

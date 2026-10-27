import importlib.util
from contextlib import redirect_stdout
import io
import json
import os
import subprocess
import tempfile
import threading
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from test_project_cache_artifact_policy import NATIVE_FIXTURE_CLEANUP, ProjectCacheTestCase


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "manage_auth_profiles.py"
MODULE_SPEC = importlib.util.spec_from_file_location("manage_auth_profiles", MODULE_PATH)
manage_auth_profiles = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(manage_auth_profiles)


class ManageAuthProfilesTest(ProjectCacheTestCase):
    def test_requested_login_uses_device_auth_without_opening_browser(self):
        with tempfile.TemporaryDirectory(dir=self.fixture_root) as directory:
            codex_home = Path(directory)
            (codex_home / "auth.json").write_text('{}')
            args = SimpleNamespace(login=True, source=None, codex_home=codex_home, name="test", force=False, dry_run=False)
            with patch.object(manage_auth_profiles.subprocess, "run") as run, redirect_stdout(io.StringIO()):
                manage_auth_profiles.command_add_account(args)
            self.assertEqual(run.call_args.args[0], ["codex", "login", "--device-auth"])
            self.assertTrue(run.call_args.kwargs["check"])

    def test_discover_profiles_collects_account_state_in_parallel(self):
        with tempfile.TemporaryDirectory(dir=self.fixture_root) as temp_dir:
            codex_home = Path(temp_dir)
            auth_map = {
                "auth_alpha.json": "acct-alpha",
                "auth_bravo.json": "acct-bravo",
                "auth_charlie.json": "acct-charlie",
            }
            for filename, account_id in auth_map.items():
                (codex_home / filename).write_text(
                    json.dumps(
                        {
                            "tokens": {"account_id": account_id},
                            "last_refresh": "2026-04-14T00:00:00Z",
                        }
                    )
                )

            barrier = threading.Barrier(len(auth_map))
            thread_names = set()

            def fake_find_snapshot_by_account(*, codex_home, account_id, active_account_id, current_snapshot, limit):
                thread_names.add(threading.current_thread().name)
                barrier.wait(timeout=1)
                return {"account_id": account_id, "source": "test"}

            with (
                patch.object(manage_auth_profiles, "load_recent_rollout_paths", return_value=[]),
                patch.object(manage_auth_profiles, "find_current_active_snapshot", return_value=None),
                patch.object(
                    manage_auth_profiles,
                    "find_snapshot_by_account",
                    side_effect=fake_find_snapshot_by_account,
                ),
            ):
                profiles = manage_auth_profiles.discover_profiles(
                    codex_home=codex_home,
                    threads_limit=10,
                    live=False,
                )

        self.assertEqual([profile["file"] for profile in profiles], sorted(auth_map))
        self.assertEqual(
            [profile["usage"]["account_id"] for profile in profiles],
            [auth_map[filename] for filename in sorted(auth_map)],
        )
        self.assertGreater(len(thread_names), 1)

    def probe(self, outcome="success", borrowed=True):
        auth = self.fixture_root / "source-auth.json"
        auth.write_text('{"tokens":{"account_id":"fake-test-only"}}')
        preserved = self.fixture_root / "caller-owned.txt"
        preserved.write_text("keep caller workspace")
        workdir = self.fixture_root / "workspace"
        workdir.mkdir()
        observed = {}
        native_run = subprocess.run

        def fake_codex(command, **keywords):
            if command[0] != "codex":
                return native_run(command, **keywords)
            home = Path(keywords["env"]["CODEX_HOME"])
            observed.update(home=home, probe_root=home.parent, outer=home.parent.parent, environment=keywords["env"])
            self.assertEqual((home / "auth.json").read_bytes(), auth.read_bytes())
            self.assertTrue(home.is_relative_to(self.fixture_root))
            if outcome == "timeout":
                raise subprocess.TimeoutExpired(command, 180)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with patch.dict(os.environ, {}, clear=False), patch.object(manage_auth_profiles.subprocess, "run", side_effect=fake_codex):
            if borrowed:
                os.environ["CODEX_PROJECT_CACHE_ROOT"] = str(self.fixture_root)
            else:
                os.environ.pop("CODEX_PROJECT_CACHE_ROOT", None)
            result = manage_auth_profiles.run_live_probe(auth, workdir, "Reply exactly OK.")
        self.assertEqual(preserved.read_text(), "keep caller workspace")
        return result, observed

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Requires native exact consumer cleanup")
    def test_live_probe_borrows_outer_owner_and_removes_only_fake_home(self):
        result, observed = self.probe()
        self.assertEqual(result["source"], "live-probe")
        self.assertFalse(observed["home"].exists())
        self.assertTrue(observed["outer"].exists())
        for name in ("TMP", "TEMP", "TMPDIR"):
            self.assertEqual(Path(observed["environment"][name]), observed["probe_root"] / "tmp")
        self.assertEqual(Path(observed["environment"]["CODEX_PROJECT_CACHE_ROOT"]), observed["outer"])
        self.assertFalse(Path(observed["environment"]["CODEX_PROJECT_CACHE_ROOT"]).is_relative_to(observed["home"]))
        self.assertEqual(Path(observed["environment"]["XDG_CACHE_HOME"]), observed["home"] / "cache")

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Requires native exact consumer cleanup")
    def test_live_probe_owned_run_is_registered_and_fully_released(self):
        result, observed = self.probe(borrowed=False)
        self.assertEqual(result["source"], "live-probe")
        self.assertFalse(observed["outer"].exists())

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Requires native exact consumer cleanup")
    def test_live_probe_timeout_still_releases_fake_home_without_real_codex(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.probe(outcome="timeout")
        self.assertEqual((self.fixture_root / "caller-owned.txt").read_text(), "keep caller workspace")
        self.assertFalse(list(self.fixture_root.glob("codex-auth-live-*")))

    @unittest.skipUnless(NATIVE_FIXTURE_CLEANUP, "Requires native exact consumer cleanup")
    def test_live_probe_cleanup_failure_is_visible_and_preserves_borrowed_owner(self):
        cleanup = manage_auth_profiles.task_cache_cleanup
        with patch.object(cleanup, "checkpoint", return_value={"requested_complete": False, "results": [{"action": "pending", "reason": "fixture deletion denied"}]}):
            with self.assertRaisesRegex(RuntimeError, "cleanup pending") as raised:
                self.probe()
        pending = raised.exception.cleanup_pending
        home = Path(pending["fake_codex_home"])
        self.assertTrue(home.is_dir())
        self.assertTrue(self.fixture_root.is_dir())
        self.assertIn("fixture deletion denied", pending["reason"])
        closed = cleanup.checkpoint(pending["project_root"], pending["task_id"], phase="finish", current_run=pending["probe_root"], apply=True, budget_seconds=15, requested_only=True)
        self.assertTrue(closed["requested_complete"])
        self.assertEqual((self.fixture_root / "caller-owned.txt").read_text(), "keep caller workspace")

    def test_unsupported_consumer_probe_blocks_before_fake_home_or_codex(self):
        auth = self.fixture_root / "source-auth.json"
        auth.write_text('{}')
        with patch.dict(os.environ, {"CODEX_PROJECT_CACHE_ROOT": str(self.fixture_root)}), patch.object(manage_auth_profiles.task_cache_cleanup, "probe_activity", return_value={"safe": False, "pending": True, "reason": "native handles unavailable"}), patch.object(manage_auth_profiles.subprocess, "run") as process:
            with self.assertRaisesRegex(RuntimeError, "no fake CODEX_HOME created"):
                manage_auth_profiles.run_live_probe(auth, self.fixture_root, "OK")
        process.assert_not_called()
        self.assertFalse(list(self.fixture_root.glob("codex-auth-live-*")))


if __name__ == "__main__":
    unittest.main()

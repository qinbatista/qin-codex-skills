import importlib.util
import json
import tempfile
import threading
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "manage_auth_profiles.py"
MODULE_SPEC = importlib.util.spec_from_file_location("manage_auth_profiles", MODULE_PATH)
manage_auth_profiles = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(manage_auth_profiles)


class ManageAuthProfilesTest(unittest.TestCase):
    def test_requested_login_uses_device_auth_without_opening_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)
            (codex_home / "auth.json").write_text('{}')
            args = SimpleNamespace(login=True, source=None, codex_home=codex_home, name="test", force=False, dry_run=False)
            with patch.object(manage_auth_profiles.subprocess, "run") as run:
                manage_auth_profiles.command_add_account(args)
            self.assertEqual(run.call_args.args[0], ["codex", "login", "--device-auth"])
            self.assertTrue(run.call_args.kwargs["check"])

    def test_discover_profiles_collects_account_state_in_parallel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
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


if __name__ == "__main__":
    unittest.main()

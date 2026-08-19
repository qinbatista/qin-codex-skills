#!/usr/bin/env python3
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_sqlite.py"
SPEC = importlib.util.spec_from_file_location("test_codex_sqlite", SCRIPT)
SQLITE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SQLITE)


def create_database(path, columns=("id TEXT PRIMARY KEY", "rollout_path TEXT")):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE threads (" + ", ".join(columns) + ")")
    connection.commit()
    connection.close()


class CodexSqliteResolverTests(unittest.TestCase):
    def test_explicit_override_then_sqlite_home_then_codex_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            explicit = root / "explicit.sqlite"
            sqlite_home = root / "runtime"
            codex_home = root / "codex"
            sqlite_home.mkdir()
            codex_home.mkdir()
            create_database(explicit)
            create_database(sqlite_home / "state_6.sqlite")
            create_database(codex_home / "state_5.sqlite")
            environment = {"CODEX_HOME": str(codex_home)}

            self.assertEqual(SQLITE.resolve_codex_sqlite_db(explicit_db=explicit, sqlite_home=sqlite_home, environment=environment), explicit.resolve())
            self.assertEqual(SQLITE.resolve_codex_sqlite_db(sqlite_home=sqlite_home, environment=environment), (sqlite_home / "state_6.sqlite").resolve())
            self.assertEqual(SQLITE.resolve_codex_sqlite_db(environment=environment), (codex_home / "state_5.sqlite").resolve())

    def test_discovery_skips_incompatible_newer_database_and_never_escapes_strict_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            fallback = root / "fallback"
            runtime.mkdir()
            fallback.mkdir()
            create_database(runtime / "state_9.sqlite", ("thread_key TEXT PRIMARY KEY",))
            create_database(runtime / "state_6.sqlite")
            create_database(fallback / "state_99.sqlite")

            resolved = SQLITE.resolve_codex_sqlite_db(sqlite_home=runtime, environment={"CODEX_HOME": str(fallback)})
            self.assertEqual(resolved, (runtime / "state_6.sqlite").resolve())
            self.assertIsNone(SQLITE.resolve_codex_sqlite_db(sqlite_home=root / "empty", strict_sqlite_home=True, environment={"CODEX_HOME": str(fallback)}))

    def test_capability_detection_degrades_missing_optional_thread_columns(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "state_preview.sqlite"
            create_database(database, ("id TEXT PRIMARY KEY",))

            capabilities = SQLITE.thread_column_capabilities(database)
        self.assertEqual(capabilities["path"], database.resolve())
        self.assertEqual(capabilities["available"], ())
        self.assertIn("rollout_path", capabilities["missing"])
        self.assertIn("model", capabilities["missing"])

    def test_explicit_incompatible_database_fails_with_a_clear_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "state_7.sqlite"
            create_database(database, ("thread_key TEXT PRIMARY KEY",))
            with self.assertRaisesRegex(SQLITE.CodexSQLiteResolutionError, "compatible threads table"):
                SQLITE.resolve_codex_sqlite_db(explicit_db=database)


if __name__ == "__main__":
    unittest.main()

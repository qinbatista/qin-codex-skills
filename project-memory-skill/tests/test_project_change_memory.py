import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ARTIFACT_PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT_PROJECT / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root, validate_external_directory


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_change_memory.py"
SPEC = importlib.util.spec_from_file_location("project_change_memory", SCRIPT)
MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEMORY)


class RetiredCodexMemoryTests(unittest.TestCase):
    def setUp(self):
        override = os.environ.get("PROJECT_CHANGE_MEMORY_TEST_CACHE")
        self.cache = validate_external_directory(override, ARTIFACT_PROJECT) if override is not None else resolve_task_artifact_root(ARTIFACT_PROJECT, "project-change-memory-tests", create=True)
        self.cache.mkdir(parents=True, exist_ok=True)
        if override is None:
            self.addCleanup(self.cache.rmdir)

    def test_sprite_tamer_root_uses_declared_owner_without_matching_unregistered_clones(self):
        with mock.patch.object(MEMORY.Path, "home", return_value=Path.cwd()):
            home = Path.cwd()
            self.assertEqual(MEMORY._registered_owner(home / "Documents/YofaGames/SpriteTamer"), "ThisIsMyOregon")
            self.assertEqual(MEMORY._registered_owner(home / "Documents/YofaGames/SpriteTamer/Assets"), "ThisIsMyOregon")
            self.assertIsNone(MEMORY._registered_owner(home / "Documents/Clones/SpriteTamer"))
            self.assertIsNone(MEMORY._registered_owner(home / "Documents/YofaGames/SpriteTamer/Cache/temp-fixture"))

    def test_official_skill_owner_preserves_legacy_history_without_matching_other_roots(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary, mock.patch.object(MEMORY.Path, "home", return_value=Path(temporary)):
            home = Path(temporary)
            for directory in (".agents/skills/project-memory-skill", ".codex/skills/project-memory-skill", "Documents/AIProject/qin-codex-skills"):
                self.assertEqual(MEMORY._registered_owner(home / directory), "Global Codex Skills")
            for directory in (".agents/worktrees/game", ".agents/plugins/plugin", ".agents/cache/session", ".codex/sessions/task", ".codex/plugins/plugin"):
                self.assertIsNone(MEMORY._registered_owner(home / directory))

    def test_legacy_scoped_record_remains_readable_without_rewriting_history(self):
        with tempfile.TemporaryDirectory(prefix="temp-legacy-memory-", dir=self.cache) as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            store = Path(temporary) / "legacy"
            store.mkdir()
            record = {"id": "legacy-result-1", "project": MEMORY._project_identity(project), "module": "memory-closeout", "summary": "Retain completed outcomes", "reason": "Preserve useful history", "result": "The prior project result remains available", "files": ["memory.py"], "verification": [], "decisions": [], "risks": [], "codex_session_key": "5491d61e1213867df58b85d0"}
            index = store / "index.jsonl"
            index.write_text(json.dumps(record) + "\n", encoding="utf-8")
            before = index.read_bytes()
            with mock.patch.dict(os.environ, {"CODEX_TASK_NAME": "", "CODEX_TASK_GROUP": ""}):
                result = MEMORY.search_records(project, module="memory-closeout", store=store, session_id="019f2500-aaaa-7000-8000-123456789abc", inspect_working_line=False)
            self.assertEqual(result["matches"][0]["id"], "legacy-result-1")
            self.assertEqual(result["matches"][0]["relation_reason"], "same_session")
            self.assertEqual(index.read_bytes(), before)

    def test_legacy_writers_refuse_to_create_codex_local_memory(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            store = Path(temporary) / "memory"
            with self.assertRaisesRegex(RuntimeError, "Obsidian"):
                MEMORY.record_change(project, "module", "project", "edit", "Summary", "Reason", "Result", "not-run", ["file.py"], store=store)
            with self.assertRaisesRegex(RuntimeError, "read-only legacy"):
                MEMORY.remove_invalid_record(project, "record-id", "reason", store=store)
            with self.assertRaisesRegex(RuntimeError, "retired"):
                MEMORY.reconcile_projections(project, store=store)
            self.assertFalse(store.exists())

    def test_explicit_existing_vault_is_resolved_without_local_write(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary:
            vault = Path(temporary) / "vault"
            (vault / "AI Memory").mkdir(parents=True)
            (vault / "Projects").mkdir()
            (vault / "AI Memory" / "ai_memory.py").write_text("# runtime\n")
            self.assertEqual(MEMORY._resolve_vault(vault), vault.resolve())
            self.assertFalse((vault / "events.jsonl").exists())

    def test_legacy_search_is_read_only(self):
        with tempfile.TemporaryDirectory(dir=self.cache) as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            store = Path(temporary) / "missing-store"
            result = MEMORY.search_records(project, store=store)
            self.assertEqual(result["matches"], [])
            self.assertFalse(store.exists())


if __name__ == "__main__":
    unittest.main()

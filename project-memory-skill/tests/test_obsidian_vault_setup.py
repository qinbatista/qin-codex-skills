import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("obsidian_vault_setup", SCRIPTS / "obsidian_vault_setup.py")
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


FAKE_GENERATOR = '''
import json
import sys
from pathlib import Path
command = sys.argv[1]
vault = Path(sys.argv[sys.argv.index("--vault") + 1])
if command == "init":
    (vault / "AI Memory").mkdir(parents=True)
    (vault / "Projects").mkdir()
    (vault / "AI Memory" / "ai_memory.py").write_text("# memory runtime\\n")
    (vault / "AI Memory" / "events.jsonl").write_text("")
elif command == "verify" and not (vault / "AI Memory" / "ai_memory.py").is_file():
    sys.exit(1)
print(json.dumps({"status": "written" if command == "init" else "pass"}))
'''


class ObsidianVaultSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vault-setup-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        package = self.source / "qin_llm_wiki"
        package.mkdir(parents=True)
        (package / "__main__.py").write_text(FAKE_GENERATOR, encoding="utf-8")

    def test_creates_vault_outside_codex_and_reuses_it(self):
        vault = self.root / "Obsidian" / "Memory"
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex")}, clear=False):
            created = SETUP.ensure_vault(vault=vault, source=self.source)
            reused = SETUP.ensure_vault(vault=vault, source=self.source)
        self.assertEqual(created["status"], "created")
        self.assertEqual(reused["status"], "ready")
        self.assertEqual(created["vault"], str(vault.resolve()))
        self.assertTrue(created["backup_required"])
        self.assertTrue((vault / "AI Memory" / "ai_memory.py").is_file())
        self.assertTrue((vault / "AI Memory" / "events.jsonl").is_file())
        self.assertFalse((vault / ".git").exists())
        self.assertFalse((self.root / "codex").exists())

    def test_no_configured_vault_uses_durable_default(self):
        target = self.root / "Documents" / "Obsidian" / "LLM Memory"
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": ""}, clear=False):
            with mock.patch.object(SETUP, "DEFAULT_VAULT", target), mock.patch.object(SETUP, "_resolve_vault", return_value=None), mock.patch.object(SETUP, "_obsidian_config_paths", return_value=[]):
                result = SETUP.ensure_vault(source=self.source)
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["vault"], str(target.resolve()))
        self.assertTrue((target / "Projects").is_dir())

    def test_registered_vault_waits_for_sync_instead_of_creating_blank_default(self):
        registered = self.root / "iCloud" / "MyAILLM"
        default = self.root / "Documents" / "Obsidian" / "LLM Memory"
        config = self.root / "obsidian.json"
        config.write_text(json.dumps({"vaults": {"old": {"path": str(registered), "open": True}}}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": ""}, clear=False):
            with mock.patch.object(SETUP, "DEFAULT_VAULT", default), mock.patch.object(SETUP, "_obsidian_config_paths", return_value=[config]):
                result = SETUP.ensure_vault(source=self.source)
        self.assertEqual(result["reason"], "registered_vault_unavailable")
        self.assertEqual(result["vault"], str(registered))
        self.assertFalse(default.exists())
        (registered / "AI Memory").mkdir(parents=True)
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": ""}, clear=False):
            with mock.patch.object(SETUP, "DEFAULT_VAULT", default), mock.patch.object(SETUP, "_obsidian_config_paths", return_value=[config]):
                partial = SETUP.ensure_vault(source=self.source)
        self.assertEqual(partial["reason"], "registered_vault_unavailable")
        self.assertFalse(default.exists())
        (registered / "AI Memory").rmdir()
        (registered / "Projects").mkdir()
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": ""}, clear=False):
            with mock.patch.object(SETUP, "DEFAULT_VAULT", default), mock.patch.object(SETUP, "_obsidian_config_paths", return_value=[config]):
                projects_only = SETUP.ensure_vault(source=self.source)
        self.assertEqual(projects_only["reason"], "registered_vault_unavailable")
        self.assertFalse(default.exists())

    def test_reuses_registered_memory_vault_even_when_not_open(self):
        registered = self.root / "iCloud" / "MyAILLM"
        (registered / "AI Memory").mkdir(parents=True)
        (registered / "Projects").mkdir()
        (registered / "AI Memory" / "ai_memory.py").write_text("# existing vault\n", encoding="utf-8")
        config = self.root / "obsidian.json"
        config.write_text(json.dumps({"vaults": {"old": {"path": str(registered), "open": False}}}), encoding="utf-8")
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": ""}, clear=False):
            with mock.patch.object(SETUP, "_obsidian_config_paths", return_value=[config]):
                result = SETUP.ensure_vault(source=self.source)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["vault"], str(registered.resolve()))

    def test_configured_missing_vault_does_not_create_empty_replacement(self):
        configured = self.root / "iCloud" / "MyAILLM"
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"), "CODEX_OBSIDIAN_VAULT": str(configured)}, clear=False):
            result = SETUP.ensure_vault(source=self.source)
        self.assertEqual(result["reason"], "configured_vault_unavailable")
        self.assertFalse(configured.exists())

    def test_refuses_codex_and_project_locations(self):
        project = self.root / "project"
        project.mkdir()
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex")}, clear=False):
            codex = SETUP.ensure_vault(vault=self.root / "codex" / "memory", source=self.source)
            inside_project = SETUP.ensure_vault(vault=project / "Cache" / "vault", project_root=project, source=self.source)
        self.assertEqual(codex["reason"], "unsafe_vault_location")
        self.assertEqual(inside_project["reason"], "unsafe_vault_location")
        self.assertFalse((project / "Cache").exists())

    def test_preserves_nonempty_directory(self):
        vault = self.root / "other-vault"
        vault.mkdir()
        (vault / "note.md").write_text("keep me", encoding="utf-8")
        result = SETUP.ensure_vault(vault=vault, source=self.source)
        self.assertEqual(result["reason"], "target_is_not_an_empty_memory_vault")
        self.assertEqual((vault / "note.md").read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()

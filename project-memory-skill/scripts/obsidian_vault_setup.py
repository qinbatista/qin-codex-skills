#!/usr/bin/env python3
"""Find or create the user's durable Obsidian memory vault."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from project_change_memory import DEFAULT_VAULT, _obsidian_config_paths, _resolve_vault

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


GENERATOR_URL = "https://github.com/qinbatista/qin-llm-wiki.git"
BACKUP_MESSAGE = "Back up this entire vault regularly. It holds all Codex and project memory; a local installation alone is not a backup."


def _memory_vault(path):
    return path.is_dir() and (path / "AI Memory" / "ai_memory.py").is_file() and (path / "Projects").is_dir()


def _target_path(vault):
    configured = str(os.environ.get("CODEX_OBSIDIAN_VAULT", "")).strip()
    return Path(vault or configured or DEFAULT_VAULT).expanduser().absolute()


def _registered_vaults():
    registered = {}
    for config_path in _obsidian_config_paths():
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        vaults = payload.get("vaults", {}) if isinstance(payload, dict) else {}
        if not isinstance(vaults, dict):
            continue
        for entry in vaults.values():
            if not isinstance(entry, dict):
                continue
            path = Path(str(entry.get("path") or "")).expanduser()
            if path.is_absolute():
                registered[path] = registered.get(path, False) or entry.get("open") is True
    return registered


def _guard_location(target, project_root):
    if target.is_symlink():
        raise ValueError("memory vault target must not be a symlink")
    resolved = target.resolve(strict=False)
    codex_root = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser().resolve()
    if resolved == codex_root or resolved.is_relative_to(codex_root):
        raise ValueError("memory vault must be outside Codex local folders")
    if any(part.casefold() == "cache" for part in resolved.parts):
        raise ValueError("memory vault must be outside Cache folders")
    if project_root is not None:
        project = Path(project_root).expanduser().resolve()
        if resolved == project or resolved.is_relative_to(project):
            raise ValueError("memory vault must be outside the project and its Cache")
    return resolved


def _run(command, *, cwd=None, env=None, timeout=120):
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True,
        check=False, timeout=timeout, **hidden_process_options(),
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip()[:600])
    return result.stdout.strip()


def ensure_vault(*, vault=None, project_root=None, source=None):
    """Return an existing memory vault or install one from qin-llm-wiki."""
    configured = bool(str(os.environ.get("CODEX_OBSIDIAN_VAULT", "")).strip())
    if vault is None and not configured:
        registered = _registered_vaults()
        memory_vaults = [path for path in registered if _memory_vault(path)]
        if len(memory_vaults) > 1:
            open_vaults = [path for path in memory_vaults if registered[path]]
            if len(open_vaults) != 1:
                return {"status": "pending", "reason": "ambiguous_registered_memory_vaults", "created": False}
            memory_vaults = open_vaults
        if memory_vaults:
            try:
                existing = _guard_location(memory_vaults[0], project_root)
            except ValueError as error:
                return {"status": "pending", "reason": "unsafe_vault_location", "detail": str(error), "created": False}
            return {"status": "ready", "vault": str(existing), "created": False,
                    "backup_required": True, "backup_message": BACKUP_MESSAGE}
        for registered_path in registered:
            try:
                entries = list(registered_path.iterdir()) if registered_path.is_dir() else []
            except OSError:
                entries = []
            if (not entries or all(entry.name.startswith(".") for entry in entries)
                    or (registered_path / "AI Memory").exists()
                    or (registered_path / "Projects").exists()):
                return {"status": "pending", "reason": "registered_vault_unavailable", "vault": str(registered_path), "created": False}
        existing = _resolve_vault(project_root=project_root)
        if existing is not None and _memory_vault(existing):
            try:
                _guard_location(existing, project_root)
            except ValueError as error:
                return {"status": "pending", "reason": "unsafe_vault_location", "detail": str(error), "created": False}
            return {"status": "ready", "vault": str(existing), "created": False,
                    "backup_required": True, "backup_message": BACKUP_MESSAGE}
    try:
        target = _guard_location(_target_path(vault), project_root)
    except ValueError as error:
        return {"status": "pending", "reason": "unsafe_vault_location", "detail": str(error), "created": False}
    if _memory_vault(target):
        return {"status": "ready", "vault": str(target), "created": False,
                "backup_required": True, "backup_message": BACKUP_MESSAGE}
    if vault is None and configured:
        return {"status": "pending", "reason": "configured_vault_unavailable", "vault": str(target), "created": False}
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        return {"status": "pending", "reason": "target_is_not_an_empty_memory_vault", "vault": str(target), "created": False}
    source_path = Path(source).expanduser().resolve() if source is not None else None
    if source_path is not None and not (source_path / "qin_llm_wiki" / "__main__.py").is_file():
        return {"status": "pending", "reason": "generator_source_unavailable", "vault": str(target), "created": False}
    if source_path is None and shutil.which("git") is None:
        return {"status": "pending", "reason": "git_unavailable", "vault": str(target), "created": False}
    target_was_empty = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".llm-memory-setup-", dir=target.parent) as temporary:
            staging = Path(temporary)
            if source_path is None:
                source_path = staging / "generator"
                git_env = os.environ.copy()
                git_env["GIT_TERMINAL_PROMPT"] = "0"
                _run([shutil.which("git"), "clone", "--depth", "1", "--", GENERATOR_URL, str(source_path)], env=git_env)
            candidate = staging / "vault"
            generator_env = os.environ.copy()
            generator_env["PYTHONPATH"] = str(source_path)
            _run([sys.executable, "-B", "-m", "qin_llm_wiki", "init", "--vault", str(candidate), "--name", target.name], env=generator_env)
            _run([sys.executable, "-B", "-m", "qin_llm_wiki", "verify", "--vault", str(candidate), "--quick"], env=generator_env)
            if not _memory_vault(candidate):
                raise RuntimeError("generator did not create a usable memory vault")
            if target.exists():
                target.rmdir()
            candidate.rename(target)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        if target_was_empty and not target.exists():
            target.mkdir(exist_ok=True)
        return {"status": "pending", "reason": "vault_setup_failed", "detail": str(error)[:600],
                "vault": str(target), "created": False}
    return {"status": "created", "vault": str(target), "created": True,
            "source": GENERATOR_URL if source is None else str(source_path),
            "backup_required": True, "backup_message": BACKUP_MESSAGE}


def main():
    parser = argparse.ArgumentParser(description="Ensure an Obsidian project memory vault exists.")
    parser.add_argument("--vault", type=Path, help="Explicit durable vault destination")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--source", type=Path, help="Local qin-llm-wiki source for offline setup")
    args = parser.parse_args()
    try:
        result = ensure_vault(vault=args.vault, project_root=args.project_root, source=args.source)
    except ValueError as error:
        result = {"status": "pending", "reason": "unsafe_vault_location", "detail": str(error), "created": False}
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["status"] in {"ready", "created"} else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_REPOSITORY = "qinbatista/qin-codex-skills"
README_TEXT = """# qin-codex-skills

Mirror of Qin's user global Codex skills from `~/.codex/skills`.

This repository stores skill source files only. Do not copy the repository `.git` directory into `~/.codex/skills`.
"""
GITIGNORE_TEXT = """.DS_Store
__pycache__/
*.pyc
*.pyo
*.log
.env
.env.*
data/cache/
"""


def run_command(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def repository_git_url(repository):
    return run_command(["gh", "repo", "view", repository, "--json", "sshUrl", "--jq", ".sshUrl"]).stdout.strip()


def clone_repository(repository, sandbox):
    repository_dir = sandbox / "repo"
    run_command(["git", "clone", "--depth", "1", repository_git_url(repository), str(repository_dir)])
    return repository_dir


def ignored_names(directory, names):
    return {name for name in names if name in {".git", ".github", ".DS_Store", "__pycache__"} or name.endswith((".pyc", ".pyo", ".log"))}


def skill_directories(skills_dir):
    return sorted([path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()], key=lambda path: path.name)


def copy_skill_directory(source_dir, target_dir):
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir, ignore=ignored_names)


def path_differs(source_dir, target_dir):
    if not target_dir.exists():
        return True
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-diff-") as sandbox_name:
        sandbox = Path(sandbox_name)
        copy_skill_directory(source_dir, sandbox / "source")
        copy_skill_directory(target_dir, sandbox / "target")
        return subprocess.run(["git", "diff", "--no-index", "--quiet", str(sandbox / "source"), str(sandbox / "target")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0


def print_lines(title, lines):
    print(title)
    for line in lines:
        print(f"- {line}")


def remote_changes(repository, skills_dir):
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        return [path.name for path in skill_directories(repository_dir) if path_differs(path, skills_dir / path.name)]


def preuse(repository, skills_dir):
    changed_names = remote_changes(repository, skills_dir)
    if changed_names:
        print_lines("Remote skills differ from local global skills:", changed_names)
        print("Run pull before using or editing these skills unless local edits must be preserved.")
    else:
        print("Remote global skills are already reflected locally.")


def pull(repository, skills_dir):
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        changed_paths = [path for path in skill_directories(repository_dir) if path_differs(path, skills_dir / path.name)]
        for path in changed_paths:
            copy_skill_directory(path, skills_dir / path.name)
        if changed_paths:
            print_lines("Copied remote skills into ~/.codex/skills:", [path.name for path in changed_paths])
        else:
            print("No remote skill changes to copy.")


def prepare_repository_snapshot(repository_dir, skills_dir):
    for path in repository_dir.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    (repository_dir / "README.md").write_text(README_TEXT)
    (repository_dir / ".gitignore").write_text(GITIGNORE_TEXT)
    copied_names = []
    for path in skill_directories(skills_dir):
        copy_skill_directory(path, repository_dir / path.name)
        copied_names.append(path.name)
    return copied_names


def push(repository, skills_dir, message, dry_run):
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        copied_names = prepare_repository_snapshot(repository_dir, skills_dir)
        status_text = run_command(["git", "status", "--short"], cwd=repository_dir).stdout.strip()
        if dry_run:
            print_lines("Local skills selected for mirror:", copied_names)
            print(status_text or "No local-to-remote differences.")
            return
        if not status_text:
            print("No global skill changes to push.")
            return
        run_command(["git", "add", "-A"], cwd=repository_dir)
        branch_name = run_command(["git", "branch", "--show-current"], cwd=repository_dir).stdout.strip() or "main"
        run_command(["git", "checkout", "-B", branch_name], cwd=repository_dir)
        run_command(["git", "commit", "-m", message], cwd=repository_dir)
        run_command(["git", "push", "origin", f"HEAD:{branch_name}"], cwd=repository_dir)
        print(f"Pushed global skills to {repository}.")


def main():
    parser = argparse.ArgumentParser(description="Sync user global Codex skills with GitHub without putting .git in ~/.codex/skills.")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".codex" / "skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("preuse")
    subparsers.add_parser("pull")
    subparsers.add_parser("status")
    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--message", default="Update global Codex skills")
    match parser.parse_args():
        case argparse.Namespace(command="preuse", repo=repository, skills_dir=skills_dir):
            preuse(repository, skills_dir)
        case argparse.Namespace(command="pull", repo=repository, skills_dir=skills_dir):
            pull(repository, skills_dir)
        case argparse.Namespace(command="status", repo=repository, skills_dir=skills_dir):
            push(repository, skills_dir, "Update global Codex skills", True)
        case argparse.Namespace(command="push", repo=repository, skills_dir=skills_dir, message=message):
            push(repository, skills_dir, message, False)


if __name__ == "__main__":
    main()

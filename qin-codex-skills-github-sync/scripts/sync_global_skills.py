#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


DEFAULT_REPOSITORY = "qinbatista/qin-codex-skills"
DEFAULT_STATE_FILE = Path.home() / ".codex" / "state" / "qin-codex-skills-github-sync.json"
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


def repository_head(repository_dir):
    return run_command(["git", "rev-parse", "HEAD"], cwd=repository_dir).stdout.strip()


def repository_timestamp(repository_dir):
    return int(run_command(["git", "log", "-1", "--format=%ct"], cwd=repository_dir).stdout.strip())


def ignored_names(directory, names):
    return {name for name in names if name in {".git", ".github", ".DS_Store", "__pycache__"} or name.endswith((".pyc", ".pyo", ".log"))}


def skill_directories(skills_dir):
    return sorted([path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()], key=lambda path: path.name)


def included_files(skill_dir):
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".github", ".DS_Store", "__pycache__"} for part in path.relative_to(skill_dir).parts):
            continue
        if path.name.endswith((".pyc", ".pyo", ".log")):
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(skill_dir).as_posix())


def snapshot_hash(skill_paths):
    digest = hashlib.sha256()
    for skill_path in skill_paths:
        digest.update(f"skill:{skill_path.name}\n".encode())
        for path in included_files(skill_path):
            digest.update(f"file:{skill_path.name}/{path.relative_to(skill_path).as_posix()}\n".encode())
            digest.update(path.read_bytes())
            digest.update(b"\n")
    return digest.hexdigest()


def latest_local_timestamp(skill_paths):
    latest_timestamp = 0
    for skill_path in skill_paths:
        for path in included_files(skill_path):
            latest_timestamp = max(latest_timestamp, int(path.stat().st_mtime))
    return latest_timestamp


def read_sync_state(state_file):
    if not state_file.exists():
        return {}
    return json.loads(state_file.read_text())


def write_sync_state(state_file, repository, remote_head, local_hash, remote_hash):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({
        "repository": repository,
        "remote_head": remote_head,
        "local_hash": local_hash,
        "remote_hash": remote_hash,
        "synced_at": int(time.time())
    }, indent=2) + "\n")


def read_skill_metadata(skill_dir):
    frontmatter_lines = []
    in_frontmatter = False
    for line in (skill_dir / "SKILL.md").read_text().splitlines():
        if line == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter:
            frontmatter_lines.append(line)
    metadata = {}
    current_key = ""
    for line in frontmatter_lines:
        if line.startswith("  ") and current_key:
            metadata[current_key] = f"{metadata[current_key]} {line.strip()}".strip()
            continue
        if ": " in line:
            current_key, current_value = line.split(": ", 1)
            metadata[current_key] = current_value.strip().strip('"')
    return metadata


def build_readme(skill_paths):
    readme_lines = [
        "# qin-codex-skills",
        "",
        "Public mirror of Qin's user global Codex skills from `~/.codex/skills`.",
        "",
        "This repository stores global skill source files only. Do not copy the repository `.git` directory into `~/.codex/skills`.",
        "",
        "## Skills",
        ""
    ]
    for skill_path in skill_paths:
        metadata = read_skill_metadata(skill_path)
        skill_name = metadata.get("name", skill_path.name)
        readme_lines.extend([
            f"### [`{skill_name}`](./{skill_path.name}/)",
            "",
            metadata.get("description", "No description provided."),
            ""
        ])
    return "\n".join(readme_lines)


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


def mirror_repository_to_local(repository_dir, skills_dir):
    remote_paths = skill_directories(repository_dir)
    remote_names = {path.name for path in remote_paths}
    changed_names = []
    for path in skill_directories(skills_dir):
        if path.name not in remote_names:
            shutil.rmtree(path)
            changed_names.append(path.name)
    for path in remote_paths:
        if path_differs(path, skills_dir / path.name):
            copy_skill_directory(path, skills_dir / path.name)
            changed_names.append(path.name)
    return changed_names


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
        changed_names = mirror_repository_to_local(repository_dir, skills_dir)
        write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(repository_dir)))
        if changed_names:
            print_lines("Copied remote skills into ~/.codex/skills:", changed_names)
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
    (repository_dir / ".gitignore").write_text(GITIGNORE_TEXT)
    copied_names = []
    skill_paths = skill_directories(skills_dir)
    (repository_dir / "README.md").write_text(build_readme(skill_paths))
    for path in skill_paths:
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
            write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(skills_dir)))
            print("No global skill changes to push.")
            return
        run_command(["git", "add", "-A"], cwd=repository_dir)
        branch_name = run_command(["git", "branch", "--show-current"], cwd=repository_dir).stdout.strip() or "main"
        run_command(["git", "checkout", "-B", branch_name], cwd=repository_dir)
        run_command(["git", "commit", "-m", message], cwd=repository_dir)
        run_command(["git", "push", "origin", f"HEAD:{branch_name}"], cwd=repository_dir)
        write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(skills_dir)))
        print(f"Pushed global skills to {repository}.")


def sync(repository, skills_dir, message):
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        local_paths = skill_directories(skills_dir)
        remote_paths = skill_directories(repository_dir)
        local_hash = snapshot_hash(local_paths)
        remote_hash = snapshot_hash(remote_paths)
        remote_head = repository_head(repository_dir)
        if local_hash == remote_hash:
            write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, local_hash, remote_hash)
            print("Local and remote global skills are already synced.")
            return
        state = read_sync_state(DEFAULT_STATE_FILE)
        local_changed = local_hash != state.get("local_hash")
        remote_changed = remote_head != state.get("remote_head") or remote_hash != state.get("remote_hash")
        match True:
            case _ if local_changed and not remote_changed:
                print("Local global skills are newer than the last synced state. Pushing to GitHub.")
                push(repository, skills_dir, message, False)
            case _ if remote_changed and not local_changed:
                print("Remote global skills are newer than the last synced state. Pulling into ~/.codex/skills.")
                changed_names = mirror_repository_to_local(repository_dir, skills_dir)
                write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, snapshot_hash(skill_directories(skills_dir)), remote_hash)
                print_lines("Copied remote skills into ~/.codex/skills:", changed_names)
            case _ if latest_local_timestamp(local_paths) >= repository_timestamp(repository_dir):
                print("Both sides differ; local files are newest. Pushing to GitHub.")
                push(repository, skills_dir, message, False)
            case _:
                print("Both sides differ; remote commit is newest. Pulling into ~/.codex/skills.")
                changed_names = mirror_repository_to_local(repository_dir, skills_dir)
                write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, snapshot_hash(skill_directories(skills_dir)), remote_hash)
                print_lines("Copied remote skills into ~/.codex/skills:", changed_names)


def main():
    parser = argparse.ArgumentParser(description="Sync user global Codex skills with GitHub without putting .git in ~/.codex/skills.")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".codex" / "skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--message", default="Sync global Codex skills")
    subparsers.add_parser("preuse")
    subparsers.add_parser("pull")
    subparsers.add_parser("status")
    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--message", default="Update global Codex skills")
    match parser.parse_args():
        case argparse.Namespace(command="sync", repo=repository, skills_dir=skills_dir, message=message):
            sync(repository, skills_dir, message)
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

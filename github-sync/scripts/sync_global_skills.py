#!/usr/bin/env python3
import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


DEFAULT_REPOSITORY = "qinbatista/qin-codex-skills"
DEFAULT_STATE_FILE = Path.home() / ".codex" / "state" / "github-sync.json"
GITIGNORE_TEXT = """.DS_Store
__pycache__/
*.pyc
*.pyo
*.log
.env
.env.*
cache/
outputs/
work/
data/cache/
.venv/
venv/
node_modules/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
"""
EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".DS_Store",
    "__pycache__",
    "cache",
    "outputs",
    "work",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache"
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log")
SENSITIVE_NAME_PATTERNS = (
    ".env",
    ".env.*",
    "auth.json",
    "auth*.json",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_rsa.*",
    "id_ed25519",
    "id_ed25519.*",
    "*credential*.json",
    "*credentials*.json",
    "*secret*.json",
    "*token*.json",
    "*cookie*.json",
    "*.sqlite",
    "*.sqlite3",
    "*.db"
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----"),
    re.compile(r'"(?:access_token|refresh_token|id_token|session_token|api_key|secret|password)"\s*:\s*"[^"\n]{12,}"', re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"\n]{12,}['\"]", re.IGNORECASE)
)
CATEGORY_ORDER = ["Code", "Optimization", "Generation", "Verification", "Testing", "Management", "General"]
CATEGORY_LABELS = {
    "Code": "Code / 代码类",
    "Optimization": "Optimization / 优化类",
    "Generation": "Generation / 生成类",
    "Verification": "Verification / 验证类",
    "Testing": "Testing / 测试类",
    "Management": "Management / 管理类",
    "General": "General / 通用类",
}
SKILL_BRANCHES = {
    "code-skill": [
        ("Prompt generation", "Only for creating, rewriting, or embedding prompts."),
        ("Coding approach", "Use for assumptions, smallest viable implementation, and surgical edits."),
        ("Spark small-task routing", "Use only for obvious bounded low-risk code tasks when an allowed route exists."),
        ("Python rules", "Use for Python modules, scripts, tests, snippets, and Python prompt assignments."),
        ("Unity C# rules", "Use for Unity MonoBehaviours, ScriptableObjects, managers, and gameplay systems."),
        ("Real test/report flow", "After code changes, route real executable evidence through test-skill unless testing is explicitly forbidden."),
    ],
    "optimization-skill": [
        ("Instruction tightening", "Tighten triggers, workflow wording, guardrails, and duplicated requirements."),
        ("References extraction", "Move long stable context into references/ when it should be loaded only when needed."),
        ("Script conversion", "Move repeated deterministic steps into scripts/ when it saves tokens and remains testable."),
        ("Assets/templates", "Store reusable fixtures, templates, or media in assets/ when they are part of the skill."),
        ("No-op decision", "Leave the skill unchanged when optimization is not justified."),
        ("Code-skill gate", "Use code-skill before writing or editing helper code."),
    ],
    "verify-skill": [
        ("UI verification", "Use Taste Skill plus the local problem index for visual/UI checks."),
        ("Local script/process verification", "Run local scripts with concrete cache inputs and inspect outputs."),
        ("Code behavior verification", "Define the behavior that test-skill must prove with real execution."),
        ("Skill/instruction verification", "Check frontmatter, triggers, references, paths, old names, and route behavior."),
        ("Generated artifact review", "Open, render, parse, or inspect generated files and reports."),
        ("Mixed route", "Combine only the relevant verification routes when the task spans artifacts."),
    ],
    "test-skill": [
        ("Code/API/CLI evidence", "Run real commands, API calls, or scripts and record input, used method, output, and pass reason."),
        ("UI/browser evidence", "Capture real screenshots, page states, console/runtime evidence, and viewport details."),
        ("Image evidence", "Use real source/output images and visual artifacts."),
        ("Document/PDF evidence", "Render, parse, or inspect documents and PDFs with local tools."),
        ("Comparison/audit reports", "Show before/after, expected/actual, or audit findings with concrete evidence."),
        ("Evidence contract", "Every passing case needs Input, Used, Output, and Why Pass."),
    ],
    "codex-switch": [
        ("List profiles", "Inspect saved local auth profile files."),
        ("Live usage probes", "Run isolated live checks only when current usage matters."),
        ("Switch profile", "Copy a confirmed saved profile onto auth.json after explicit confirmation."),
        ("Refresh/login backup", "Run browser login and save a refreshed profile backup."),
        ("Save current auth", "Back up the current auth.json under a requested local profile name."),
        ("Import auth file", "Import a user-supplied auth file into a named local profile."),
        ("Privacy guardrails", "Never expose or publish tokens, auth files, account IDs, or raw logs."),
    ],
    "github-sync": [
        ("sync", "Normal before/after route for global skill work."),
        ("status", "Dry-run preview of local-to-remote changes."),
        ("preuse", "Read-only inspection before using or editing skills."),
        ("pull", "Accept remote changes into local global skills."),
        ("push", "Publish local global-skill changes to GitHub."),
        ("public safety scan", "Block auth files, secrets, cache, logs, and generated private artifacts."),
    ],
}


def run_command(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def repository_git_url(repository):
    if repository.startswith(("git@", "ssh://", "https://")):
        return repository
    if shutil.which("gh"):
        return run_command(["gh", "repo", "view", repository, "--json", "sshUrl", "--jq", ".sshUrl"]).stdout.strip()
    return f"git@github.com:{repository}.git"


def clone_repository(repository, sandbox):
    repository_dir = sandbox / "repo"
    run_command(["git", "clone", "--depth", "1", repository_git_url(repository), str(repository_dir)])
    return repository_dir


def repository_head(repository_dir):
    return run_command(["git", "rev-parse", "HEAD"], cwd=repository_dir).stdout.strip()


def repository_timestamp(repository_dir):
    return int(run_command(["git", "log", "-1", "--format=%ct"], cwd=repository_dir).stdout.strip())


def ignored_names(directory, names):
    return {name for name in names if name in EXCLUDED_PARTS or name.endswith(EXCLUDED_SUFFIXES)}


def skill_directories(skills_dir):
    return sorted([path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()], key=lambda path: path.name)


def included_files(skill_dir):
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.relative_to(skill_dir).parts):
            continue
        if path.name.endswith(EXCLUDED_SUFFIXES):
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(skill_dir).as_posix())


def sensitive_name(relative_path):
    lower_path = relative_path.as_posix().lower()
    lower_name = relative_path.name.lower()
    return any(fnmatch.fnmatch(lower_name, pattern) or fnmatch.fnmatch(lower_path, pattern) for pattern in SENSITIVE_NAME_PATTERNS)


def secret_value_issue(path):
    try:
        text = path.read_text(errors="ignore")
    except UnicodeDecodeError:
        return ""
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return ""


def public_safety_issues(skill_paths):
    issues = []
    for skill_path in skill_paths:
        for path in skill_path.rglob("*"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(skill_path)
            if any(part in EXCLUDED_PARTS for part in relative_path.parts) or path.name.endswith(EXCLUDED_SUFFIXES):
                continue
            mirror_path = f"{skill_path.name}/{relative_path.as_posix()}"
            if sensitive_name(relative_path):
                issues.append(f"{mirror_path}: sensitive filename")
                continue
            matched_pattern = secret_value_issue(path)
            if matched_pattern:
                issues.append(f"{mirror_path}: secret-like content matched {matched_pattern}")
    return issues


def assert_public_safe(skill_paths):
    issues = public_safety_issues(skill_paths)
    if issues:
        message = "Refusing to push private or secret-looking data to the public skill mirror:\n"
        message += "\n".join(f"- {issue}" for issue in issues)
        raise RuntimeError(message)


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


def skill_category(skill_name, description):
    text = f"{skill_name} {description}".lower()
    if skill_name == "code-skill":
        return "Code"
    if skill_name == "optimization-skill":
        return "Optimization"
    if skill_name in {"github-sync", "codex-switch"} or "github" in text or "auth" in text:
        return "Management"
    if skill_name == "test-skill":
        return "Testing"
    if skill_name == "verify-skill":
        return "Verification"
    if "testing" in text or "report" in text:
        return "Testing"
    if "verify" in text or "validation" in text:
        return "Verification"
    if "optimization" in text or "optimize" in text:
        return "Optimization"
    if "prompt" in text or "generate" in text:
        return "Generation"
    if "code-related" in text or "coding" in text:
        return "Code"
    return "General"


def mermaid_id(*values):
    return re.sub(r"[^A-Za-z0-9_]+", "_", "_".join(values)).strip("_")


def mermaid_label(value):
    return str(value).replace('"', "'")


def build_skill_graph(rows):
    lines = [
        "```mermaid",
        "flowchart LR",
        "  root((Global Codex Skills))",
    ]
    category_ids = []
    skill_ids = []
    branch_ids = []
    for category in CATEGORY_ORDER:
        category_rows = [row for row in rows if row[0] == category]
        if not category_rows:
            continue
        category_id = f"category_{mermaid_id(category)}"
        category_ids.append(category_id)
        lines.append(f'  root --- {category_id}["{mermaid_label(CATEGORY_LABELS.get(category, category))}"]')
        for _, skill_name, _ in category_rows:
            skill_id = f"skill_{mermaid_id(skill_name)}"
            skill_ids.append(skill_id)
            lines.append(f'  {category_id} --- {skill_id}["{mermaid_label(skill_name)}"]')
            for branch_name, _ in SKILL_BRANCHES.get(skill_name, []):
                branch_id = f"branch_{mermaid_id(skill_name, branch_name)}"
                branch_ids.append(branch_id)
                lines.append(f'  {skill_id} --- {branch_id}["{mermaid_label(branch_name)}"]')
    lines.extend([
        "  classDef root fill:#000,color:#fff,stroke:#111,stroke-width:2px;",
        "  classDef category fill:#2f2f2f,color:#fff,stroke:#555;",
        "  classDef skill fill:#111,color:#fff,stroke:#eee;",
        "  classDef branch fill:#1f1f1f,color:#fff,stroke:#777;",
        "  class root root;",
    ])
    if category_ids:
        lines.append(f"  class {','.join(category_ids)} category;")
    if skill_ids:
        lines.append(f"  class {','.join(skill_ids)} skill;")
    if branch_ids:
        lines.append(f"  class {','.join(branch_ids)} branch;")
    lines.append("```")
    return lines


def build_branch_explanation(rows):
    lines = [
        "## Skill Internal Branches",
        "",
        "Each skill may contain multiple internal branches. These are alternatives selected by the current task, not a checklist to run every time.",
        "",
    ]
    for category in CATEGORY_ORDER:
        category_rows = [row for row in rows if row[0] == category]
        if not category_rows:
            continue
        lines.extend([f"### {CATEGORY_LABELS.get(category, category)}", ""])
        for _, skill_name, _ in category_rows:
            lines.extend([f"#### `{skill_name}`", ""])
            branches = SKILL_BRANCHES.get(skill_name, [])
            if not branches:
                lines.extend(["- No fixed internal branch list is defined yet; choose the narrowest route from the skill body.", ""])
                continue
            for branch_name, branch_description in branches:
                lines.append(f"- **{branch_name}**: {branch_description}")
            lines.append("")
    return lines


def build_overview(skill_paths):
    rows = []
    groups = {}
    for skill_path in skill_paths:
        metadata = read_skill_metadata(skill_path)
        skill_name = metadata.get("name", skill_path.name)
        description = metadata.get("description", "No description provided.")
        category = skill_category(skill_name, description)
        rows.append((category, skill_name, description))
        groups.setdefault(category, []).append(skill_name)

    lines = [
        "# Current Global Codex Skills",
        "",
        *build_skill_graph(rows),
        "",
        f"Generated: {time.strftime('%Y-%m-%d', time.localtime())}",
        "",
        "## Diagram Explanation",
        "",
        "- The center node is the full set of user global Codex skills.",
        "- First-level nodes are skill categories.",
        "- Second-level nodes are the actual skill names that Codex can invoke.",
        "- Third-level nodes are internal branches. Codex should choose only the branch needed for the current task instead of running every branch.",
        "",
        *build_branch_explanation(rows),
        "",
        "## Skill List",
        "",
        "| Category | Skill | Purpose |",
        "|---|---|---|"
    ]
    for category, skill_name, description in rows:
        lines.append(f"| {category} | `{skill_name}` | {description} |")

    lines.extend([
        "",
        "## Structure",
        "",
        "- Code work enters through `code-skill`.",
        "- Repeated fixed workflow optimization enters through `optimization-skill`.",
        "- Verification work enters through `verify-skill`.",
        "- Real tests and report artifacts sit under `test-skill`.",
        "- Auth and GitHub mirror maintenance sit under Management.",
        "- Each skill may contain multiple internal routes; choose only the route needed for the current request instead of running every listed case.",
        "",
        "## Current Notes",
        "",
        "- The old code skills were merged into `code-skill`.",
        "- The old testing skills were merged into `test-skill`.",
        "- UI review was broadened into `verify-skill`.",
        "- The old image workflow skill was deleted."
    ])
    return "\n".join(lines) + "\n"


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
    skill_paths = skill_directories(skills_dir)
    assert_public_safe(skill_paths)
    for path in repository_dir.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    (repository_dir / ".gitignore").write_text(GITIGNORE_TEXT)
    copied_names = []
    (repository_dir / "README.md").write_text(build_readme(skill_paths))
    (repository_dir / "current_global_skills_overview.md").write_text(build_overview(skill_paths))
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

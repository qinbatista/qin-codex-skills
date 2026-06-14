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
CATEGORY_ORDER = ["Workflow", "Code", "Optimization", "Generation", "Verification", "Testing", "Management", "General"]
PRIMARY_SKILL_ORDER = ["workflow-skill", "code-skill", "optimization-skill", "verify-skill", "test-skill", "management-skill"]
SUPPORT_SKILL_NAMES = {"codex-switch", "github-sync"}
CATEGORY_LABEL_WIDTH = 28
SKILL_LABEL_WIDTH = 24
CATEGORY_LABELS = {
    "Workflow": "Workflow / 工作流类",
    "Code": "Code / 代码类",
    "Optimization": "Optimization / 优化类",
    "Generation": "Generation / 生成类",
    "Verification": "Verification / 验证类",
    "Testing": "Testing / 测试类",
    "Management": "Management / 管理类",
    "General": "General / 通用类",
}
SKILL_SUMMARIES = {
    "workflow-skill": "Controls task decomposition, goal checks, routing, iteration, and final evidence for Codex requests.",
    "code-skill": "Combines prompt, coding approach, Python, Unity C#, and small-code content.",
    "optimization-skill": "Turns stable repeated workflows into reusable local scripts, references, or assets when that saves tokens.",
    "verify-skill": "Checks UI, scripts, generated artifacts, skills, and workflows against the user's requirement.",
    "test-skill": "Runs real executable checks and produces evidence-rich PDF reports.",
    "management-skill": "Routes Codex profile management and global skill GitHub sync through the right support skill.",
    "codex-switch": "Manages local Codex auth profiles and account switching without exposing private auth data.",
    "github-sync": "Syncs, commits, and pushes Codex skill changes to the public GitHub mirror with privacy checks.",
}
SKILL_CONTENTS = {
    "workflow-skill": [
        ("Text and Markdown tasks", "Text, markdown, explanation, classification, and rewrite requests with explicit format targets."),
        ("Code tasks", "Code, Python, Unity C#, prompt-in-code, frontend/UI, scripts, and executable behavior requests."),
        ("Visual and generated artifacts", "Image, UI, browser screenshot, document, PDF, report, and generated file tasks."),
        ("Global skill edits", "Create, merge, rename, delete, reorganize, or update global Codex skills."),
        ("Management tasks", "Account/profile switching and global skill GitHub sync through management-skill."),
        ("Final evidence reports", "Evidence PDFs and completion reports when the task needs proof."),
    ],
    "code-skill": [
        ("Prompt Creating", "Prompt generation only: create, rewrite, or embed prompts into the corresponding text or code."),
        ("Karpathy Coding Guidelines", "Code thinking and implementation approach for assumptions, simple design, naming, branching, and surgical edits."),
        ("Python Code Checker", "Python modules, scripts, tests, snippets, prompt assignments, formatting, contracts, error handling, and logging rules."),
        ("Unity C# Minimal Style", "Unity MonoBehaviours, ScriptableObjects, managers, gameplay systems, editor scripts, lifecycle methods, and Unity C# style."),
        ("Easy Code Spark", "Small bounded code tasks that can use the Spark small-task route when the task is obvious and low risk."),
    ],
    "optimization-skill": [
        ("Skill Optimization", "Optimize fixed or repeated skill workflows into local scripts, references, assets, or templates that save tokens."),
        ("Official skill compliance", "Audit skill structure, frontmatter, trigger descriptions, references, scripts, assets, and token-use behavior."),
        ("Local script conversion", "Turn stable repeated test, image, browser, computer-control, report, or generation steps into reusable local code."),
        ("Reference extraction", "Move long stable instructions into references/ so they load only when the task needs them."),
        ("Assets and templates", "Store reusable fixtures, templates, or media in assets/ when those files are part of the optimized skill."),
    ],
    "verify-skill": [
        ("UI Review", "UI/UX, layout, responsive checks, screenshots, frontend polish, browser states, and Taste Skill visual QA."),
        ("Local Script Verification", "Optimized local scripts and workflows with concrete cache inputs, real outputs, rerun behavior, and output paths."),
        ("Skill Verification", "SKILL.md frontmatter, trigger wording, referenced files, old-name cleanup, route behavior, and skill structure."),
        ("Generated Artifact Verification", "Markdown, images, PDFs, documents, reports, data files, and exports through open/render/parse/inspect checks."),
        ("PDF Evidence Review", "Verify generated PDF reports contain real Input, Used, Output, and Why Pass evidence."),
    ],
    "test-skill": [
        ("Done Means Tested", "After code or workflow changes, run a small real usage test with concrete inputs and real outputs."),
        ("Test PDF Report", "Generate a PDF report that records exactly what input was given, what command/tool was used, what output came back, and why it passes."),
        ("Code/API/CLI Tests", "Real scripts, commands, CLI invocations, API calls, local handlers, stdout, files, JSON, and returned values."),
        ("UI/Browser Tests", "Real page states, screenshots, viewport sizes, console/runtime evidence, and interaction results."),
        ("Image/Document/PDF Tests", "Real source/output images, generated files, rendered documents, parsed PDFs, and artifact paths."),
        ("Comparison/Audit Reports", "Before/after, expected/actual, audit findings, and pass/fail evidence with concrete artifacts."),
    ],
    "management-skill": [
        ("Codex Switch", "Local Codex auth profiles, saved profile listing, usage snapshots, login refresh, profile backup/import, and confirmed account switching."),
        ("GitHub Sync", "Global skill mirror status, preuse checks, public-safety scan, sync, pull, push, commit, and remote hash verification."),
        ("Privacy-Safe Management", "Auth files, tokens, cookies, profile IDs, raw logs, cache files, and secrets stay local and are never published."),
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
        ("sync", "Normal before/after route for skill work."),
        ("status", "Dry-run preview of local-to-remote changes."),
        ("preuse", "Read-only inspection before using or editing skills."),
        ("pull", "Accept remote changes into local skills."),
        ("push", "Publish local skill changes to GitHub."),
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
    rows = []
    for skill_path in skill_paths:
        metadata = read_skill_metadata(skill_path)
        skill_name = metadata.get("name", skill_path.name)
        description = metadata.get("description", "No description provided.")
        rows.append((skill_category(skill_name, description), skill_name, description, skill_path.name))
    primary_rows = ordered_primary_rows(rows)

    readme_lines = [
        "# qin-codex-skills",
        "",
        "Codex skill source and routing overview.",
        "",
        "## Skill Map",
        "",
        *build_skill_graph([(category, skill_name, description) for category, skill_name, description, _ in primary_rows]),
        "",
        *build_skill_details(primary_rows),
        "",
        *build_support_skill_details(rows),
    ]
    return "\n".join(readme_lines)


def skill_category(skill_name, description):
    text = f"{skill_name} {description}".lower()
    if skill_name == "workflow-skill":
        return "Workflow"
    if skill_name == "code-skill":
        return "Code"
    if skill_name == "optimization-skill":
        return "Optimization"
    if skill_name == "management-skill":
        return "Management"
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


def display_width(value):
    return sum(2 if ord(character) > 127 else 1 for character in str(value))


def padded_label(value, target_width):
    label = mermaid_label(value)
    missing_width = max(0, target_width - display_width(label))
    side_padding = "&emsp;" * max(1, (missing_width + 3) // 4)
    return f"{side_padding}{label}{side_padding}"


def ordered_primary_rows(rows):
    rows_by_skill = {row[1]: row for row in rows}
    return [rows_by_skill[skill_name] for skill_name in PRIMARY_SKILL_ORDER if skill_name in rows_by_skill]


def short_description(description):
    first_use_split = description.split(". Use ", 1)[0].strip()
    if first_use_split:
        return first_use_split if first_use_split.endswith(".") else f"{first_use_split}."
    first_sentence = description.split(".", 1)[0].strip()
    return f"{first_sentence}." if first_sentence else "No description provided."


def build_skill_graph(rows):
    lines = [
        "```mermaid",
        '%%{init: {"flowchart": {"nodeSpacing": 44, "rankSpacing": 88, "wrappingWidth": 340}}}%%',
        "flowchart LR",
    ]
    category_ids = []
    skill_ids = []
    for category in CATEGORY_ORDER:
        category_rows = [row for row in rows if row[0] == category]
        if not category_rows:
            continue
        category_id = f"category_{mermaid_id(category)}"
        category_ids.append(category_id)
        lines.append(f'  {category_id}["{padded_label(CATEGORY_LABELS.get(category, category), CATEGORY_LABEL_WIDTH)}"]')
        for _, skill_name, _ in category_rows:
            skill_id = f"skill_{mermaid_id(skill_name)}"
            skill_ids.append(skill_id)
            lines.append(f'  {category_id} --> {skill_id}["{padded_label(skill_name, SKILL_LABEL_WIDTH)}"]')
    lines.extend([
        "  classDef category fill:#2f2f2f,color:#fff,stroke:#555;",
        "  classDef skill fill:#111,color:#fff,stroke:#eee;",
    ])
    if category_ids:
        lines.append(f"  class {','.join(category_ids)} category;")
    if skill_ids:
        lines.append(f"  class {','.join(skill_ids)} skill;")
    lines.append("```")
    return lines


def build_support_skill_details(rows):
    support_rows = [row for row in rows if row[1] in SUPPORT_SKILL_NAMES]
    if not support_rows:
        return []
    lines = [
        "## Management Support Skill Contents",
        "",
        "These are real mirrored skills used by `management-skill`, but they are not shown as separate primary map rows.",
        "",
    ]
    for _, skill_name, description, folder_name in support_rows:
        skill_title = f"[`{skill_name}`](./{folder_name}/)"
        lines.extend([f"### {skill_title}", "", SKILL_SUMMARIES.get(skill_name, short_description(description)), ""])
        for content_name, content_description in SKILL_CONTENTS.get(skill_name, []):
            lines.append(f"- **{content_name}**: {content_description}")
        lines.append("")
    return lines


def build_skill_details(rows):
    lines = [
        "## Skill Contents",
        "",
    ]
    for category in CATEGORY_ORDER:
        category_rows = [row for row in rows if row[0] == category]
        if not category_rows:
            continue
        lines.extend([f"### {CATEGORY_LABELS.get(category, category)}", ""])
        for row in category_rows:
            _, skill_name, description = row[:3]
            folder_name = row[3] if len(row) > 3 else ""
            skill_title = f"[`{skill_name}`](./{folder_name}/)" if folder_name else f"`{skill_name}`"
            lines.extend([f"#### {skill_title}", "", SKILL_SUMMARIES.get(skill_name, short_description(description)), ""])
            contents = SKILL_CONTENTS.get(skill_name, [])
            if not contents:
                lines.extend(["- No fixed content list is defined yet; read the skill body for the concrete capability list.", ""])
                continue
            for content_name, content_description in contents:
                lines.append(f"- **{content_name}**: {content_description}")
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
    primary_rows = ordered_primary_rows(rows)

    lines = [
        "# Current Codex Skills",
        "",
        *build_skill_graph(primary_rows),
        "",
        f"Generated: {time.strftime('%Y-%m-%d', time.localtime())}",
        "",
        *build_skill_details(primary_rows),
        "",
        *build_support_skill_details([(category, skill_name, description, skill_name) for category, skill_name, description in rows]),
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
        "- Auth and GitHub mirror maintenance enter through `management-skill`, which selects `codex-switch` or `github-sync` internally.",
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
        if local_changed and not remote_changed:
            print("Local global skills are newer than the last synced state. Pushing to GitHub.")
            push(repository, skills_dir, message, False)
        elif remote_changed and not local_changed:
            print("Remote global skills are newer than the last synced state. Pulling into ~/.codex/skills.")
            changed_names = mirror_repository_to_local(repository_dir, skills_dir)
            write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, snapshot_hash(skill_directories(skills_dir)), remote_hash)
            print_lines("Copied remote skills into ~/.codex/skills:", changed_names)
        elif latest_local_timestamp(local_paths) >= repository_timestamp(repository_dir):
            print("Both sides differ; local files are newest. Pushing to GitHub.")
            push(repository, skills_dir, message, False)
        else:
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
    args = parser.parse_args()
    if args.command == "sync":
        sync(args.repo, args.skills_dir, args.message)
    elif args.command == "preuse":
        preuse(args.repo, args.skills_dir)
    elif args.command == "pull":
        pull(args.repo, args.skills_dir)
    elif args.command == "status":
        push(args.repo, args.skills_dir, "Update global Codex skills", True)
    elif args.command == "push":
        push(args.repo, args.skills_dir, args.message, False)


if __name__ == "__main__":
    main()

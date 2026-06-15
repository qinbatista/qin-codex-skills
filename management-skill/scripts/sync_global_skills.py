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
DEFAULT_STATE_FILE = Path.home() / ".codex" / "state" / "management-skill-sync.json"
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
PRIMARY_SKILL_ORDER = ["workflow-skill", "code-skill", "test-skill", "verify-skill", "optimization-skill", "management-skill"]
SUPPORT_SKILL_NAMES = set()
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
CHINESE_CATEGORY_LABELS = {
    "Workflow": "工作流类 / Workflow",
    "Code": "代码类 / Code",
    "Optimization": "优化类 / Optimization",
    "Generation": "生成类 / Generation",
    "Verification": "验证类 / Verification",
    "Testing": "测试类 / Testing",
    "Management": "管理类 / Management",
    "General": "通用类 / General",
}
SKILL_SUMMARIES = {
    "workflow-skill": "Always starts task execution, defines goals, selects executor skills, routes work, iterates, and checks final evidence.",
    "code-skill": "Executes code work after workflow-skill routes the task, combining prompt, coding approach, Python, Unity C#, and small-code modules.",
    "optimization-skill": "Executes optimization work after workflow-skill routes the task, turning stable repeated workflows into reusable local scripts, references, or assets.",
    "verify-skill": "Executes verification after workflow-skill routes the task, checking UI, scripts, generated artifacts, skills, and workflows against the user's requirement.",
    "test-skill": "Executes real tests and evidence reports after workflow-skill routes the task, combining evidence routes across code, UI, images, documents, or PDFs.",
    "management-skill": "Executes management work after workflow-skill routes the task, covering Codex profiles and global skill GitHub sync.",
}
CHINESE_SKILL_SUMMARIES = {
    "workflow-skill": "永远第一个启动任务执行，定义目标、选择执行者 skill、路由工作、循环验证并检查最终证据。",
    "code-skill": "在 workflow-skill 路由后执行代码工作，组合 prompt、代码思路、Python、Unity C# 和小代码模块。",
    "optimization-skill": "在 workflow-skill 路由后执行优化工作，把稳定重复流程变成本地脚本、引用资料或资产。",
    "verify-skill": "在 workflow-skill 路由后执行验证工作，检查 UI、脚本、生成物、skill 和工作流是否满足用户要求。",
    "test-skill": "在 workflow-skill 路由后执行真实测试和证据报告，跨代码、UI、图片、文档或 PDF 组合证据路线。",
    "management-skill": "在 workflow-skill 路由后执行管理工作，处理 Codex profiles 和全局 skill 的 GitHub 同步。",
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
}
CHINESE_SKILL_CONTENTS = {
    "workflow-skill": [
        ("文本和 Markdown 任务", "文本、Markdown、解释、分类、改写，以及有明确格式要求的内容任务。"),
        ("代码任务", "代码、Python、Unity C#、prompt-in-code、前端/UI、脚本和可执行行为任务。"),
        ("视觉和生成物", "图片、UI、浏览器截图、文档、PDF、报告和生成文件任务。"),
        ("全局 skill 编辑", "创建、合并、重命名、删除、重组或更新全局 Codex skills。"),
        ("管理任务", "通过 management-skill 处理账号/Profile 切换和全局 skill 的 GitHub 同步。"),
        ("最终证据报告", "任务需要证明时生成证据 PDF 和完成报告。"),
    ],
    "code-skill": [
        ("Prompt Creating", "只负责 prompt 生成：创建、重写，或把 prompt 嵌入对应文本或代码。"),
        ("Karpathy Coding Guidelines", "代码思考和实现方式：假设、简单设计、命名、分支和精确修改。"),
        ("Python Code Checker", "Python 模块、脚本、测试、片段、prompt 变量、格式、契约、错误处理和日志规则。"),
        ("Unity C# Minimal Style", "Unity MonoBehaviour、ScriptableObject、manager、玩法系统、编辑器脚本、生命周期方法和 Unity C# 风格。"),
        ("Easy Code Spark", "明显、低风险、小范围的代码任务，可以走 Spark 小任务路线。"),
    ],
    "optimization-skill": [
        ("Skill Optimization", "把固定或重复的 skill 流程优化成本地脚本、引用资料、资产或模板。"),
        ("官方 skill 合规检查", "检查 skill 结构、frontmatter、触发描述、references、scripts、assets 和 token 使用方式。"),
        ("本地脚本转换", "把稳定重复的测试、图片、浏览器、电脑控制、报告或生成步骤转成本地可复用代码。"),
        ("引用资料抽取", "把较长且稳定的说明移到 references/，只在任务需要时加载。"),
        ("资产和模板", "当可复用 fixture、模板或媒体属于 skill 的一部分时，放进 assets/。"),
    ],
    "verify-skill": [
        ("UI Review", "UI/UX、布局、响应式检查、截图、前端 polish、浏览器状态和 Taste Skill 视觉 QA。"),
        ("本地脚本验证", "验证优化后的本地脚本和流程，检查 cache 输入、真实输出、重复运行和输出路径。"),
        ("Skill 验证", "检查 SKILL.md frontmatter、触发说明、引用文件、旧名称清理、路由行为和 skill 结构。"),
        ("生成物验证", "通过打开、渲染、解析或检查来验证 Markdown、图片、PDF、文档、报告、数据文件和导出物。"),
        ("PDF 证据检查", "检查生成的 PDF 报告是否包含真实 Input、Used、Output 和 Why Pass。"),
    ],
    "test-skill": [
        ("Done Means Tested", "代码或工作流改完后，必须用具体输入和真实输出跑一个小的真实使用测试。"),
        ("Test PDF Report", "生成 PDF 报告，写清楚给了什么输入、用了什么命令/工具、得到了什么输出，以及为什么通过。"),
        ("Code/API/CLI Tests", "真实脚本、命令、CLI 调用、API 调用、本地 handler、stdout、文件、JSON 和返回值。"),
        ("UI/Browser Tests", "真实页面状态、截图、viewport 尺寸、console/runtime 证据和交互结果。"),
        ("Image/Document/PDF Tests", "真实输入/输出图片、生成文件、渲染文档、解析 PDF 和 artifact 路径。"),
        ("Comparison/Audit Reports", "before/after、expected/actual、审计发现，以及带具体 artifact 的 pass/fail 证据。"),
    ],
    "management-skill": [
        ("Codex Switch", "本地 Codex auth profile、已保存 profile 列表、使用快照、登录刷新、profile 备份/导入和确认后的账号切换。"),
        ("GitHub Sync", "全局 skill 镜像状态、preuse 检查、公开安全扫描、sync、pull、push、commit 和远端 hash 验证。"),
        ("隐私安全管理", "auth 文件、token、cookie、profile ID、原始日志、cache 文件和 secret 保持本地，不发布出去。"),
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
        text = path.read_text(encoding="utf-8", errors="ignore")
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
    return json.loads(state_file.read_text(encoding="utf-8"))


def write_sync_state(state_file, repository, remote_head, local_hash, remote_hash):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({
        "repository": repository,
        "remote_head": remote_head,
        "local_hash": local_hash,
        "remote_hash": remote_hash,
        "synced_at": int(time.time())
    }, indent=2) + "\n", encoding="utf-8")


def read_skill_metadata(skill_dir):
    frontmatter_lines = []
    in_frontmatter = False
    for line in (skill_dir / "SKILL.md").read_text(encoding="utf-8").splitlines():
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


def build_readme(skill_paths, language="en"):
    rows = []
    for skill_path in skill_paths:
        metadata = read_skill_metadata(skill_path)
        skill_name = metadata.get("name", skill_path.name)
        description = metadata.get("description", "No description provided.")
        rows.append((skill_category(skill_name, description), skill_name, description, skill_path.name))
    primary_rows = ordered_primary_rows(rows)

    if language == "zh":
        readme_lines = [
            "# qin-codex-skills",
            "",
            "英文版: [README.md](./README.md)",
            "",
            "## 技能图",
            "",
            *build_skill_graph([(category, skill_name, description) for category, skill_name, description, _ in primary_rows], language="zh"),
            "",
            "这是全局 Codex skills 的公开镜像和路由说明。`workflow-skill` 永远先启动并选择执行者；其他 skill 都是它路由后的执行者。顶部先展示主图，下面列每个 skill 的角色、大功能、可多选模块和选择规则。",
            "",
            *build_skill_summary_table(primary_rows, language="zh"),
            "",
            *build_support_skill_details(rows, language="zh"),
        ]
        return "\n".join(readme_lines)

    readme_lines = [
        "# qin-codex-skills",
        "",
        "Chinese version: [README.zh.md](./README.zh.md)",
        "",
        "## Skill Map",
        "",
        *build_skill_graph([(category, skill_name, description) for category, skill_name, description, _ in primary_rows], language="en"),
        "",
        "`workflow-skill` is the always-first controller. Every other primary skill is an executor selected by it. This is the Codex skill source and multi-select routing overview.",
        "",
        *build_skill_summary_table(primary_rows, language="en"),
        "",
        *build_support_skill_details(rows, language="en"),
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
    if "github" in text or "auth" in text:
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


def inline_contents(skill_name, language="en"):
    contents_map = CHINESE_SKILL_CONTENTS if language == "zh" else SKILL_CONTENTS
    return "<br>".join(f"**{content_name}**: {content_description}" for content_name, content_description in contents_map.get(skill_name, []))


def skill_modules(skill_name, language="en"):
    contents_map = CHINESE_SKILL_CONTENTS if language == "zh" else SKILL_CONTENTS
    module_names = [content_name for content_name, _ in contents_map.get(skill_name, [])]
    if not module_names:
        return "Read the skill body." if language == "en" else "查看 skill 正文。"
    return "; ".join(module_names)


def skill_role(skill_name, language="en"):
    if language == "zh":
        return "永远第一启动控制器" if skill_name == "workflow-skill" else "由 workflow-skill 路由启动的执行者"
    return "Always-first controller" if skill_name == "workflow-skill" else "Executor started by workflow-skill"


def skill_summary_lines(skill_name, description, language="en"):
    summaries = CHINESE_SKILL_SUMMARIES if language == "zh" else SKILL_SUMMARIES
    summary = summaries.get(skill_name, short_description(description))
    if language == "zh":
        return [
            f"- **角色：** {skill_role(skill_name, language)}",
            f"- **大功能：** {summary}",
            f"- **可多选模块：** {skill_modules(skill_name, language)}",
            "- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。",
        ]
    return [
        f"- **Role:** {skill_role(skill_name, language)}",
        f"- **Big function:** {summary}",
        f"- **Selectable modules (multi-select):** {skill_modules(skill_name, language)}",
        "- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.",
    ]


def build_skill_summary_table(rows, language="en"):
    category_labels = CHINESE_CATEGORY_LABELS if language == "zh" else CATEGORY_LABELS
    title = "### Skill Contents At A Glance" if language == "en" else "### Skill 内容一览"
    lines = [
        title,
        "",
    ]
    for row in rows:
        category, skill_name, description = row[:3]
        folder_name = row[3] if len(row) > 3 else skill_name
        skill_link = f"[`{skill_name}`](./{folder_name}/)"
        lines.extend([f"#### {skill_link} · {category_labels.get(category, category)}", ""])
        lines.extend(skill_summary_lines(skill_name, description, language))
        lines.append("")
    return lines


def build_skill_graph(rows, language="en"):
    contents_map = CHINESE_SKILL_CONTENTS if language == "zh" else SKILL_CONTENTS
    lines = [
        "```mermaid",
        '%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%',
        "flowchart LR",
    ]
    skill_ids = []
    content_ids = []
    for _category, skill_name, _description in rows:
        skill_id = f"skill_{mermaid_id(skill_name)}"
        content_id = f"inside_{mermaid_id(skill_name)}"
        skill_ids.append(skill_id)
        content_ids.append(content_id)
        content_names = [content_name for content_name, _ in contents_map.get(skill_name, [])]
        role_label = "永远第一启动控制器" if language == "zh" and skill_name == "workflow-skill" else "执行者路线" if language == "zh" else "Always-first controller" if skill_name == "workflow-skill" else "Executor routes"
        content_label = "<br/>".join([role_label, ("可多选模块" if language == "zh" else "Multi-select routes"), *[mermaid_label(content_name) for content_name in content_names]])
        lines.append(f'  {skill_id}["{mermaid_label(skill_name)}"] --> {content_id}["{content_label}"]')
    lines.extend([
        "  classDef skill fill:#111,color:#fff,stroke:#eee;",
        "  classDef content fill:#2f2f2f,color:#fff,stroke:#666;",
    ])
    if skill_ids:
        lines.append(f"  class {','.join(skill_ids)} skill;")
    if content_ids:
        lines.append(f"  class {','.join(content_ids)} content;")
    lines.append("```")
    return lines


def build_support_skill_details(rows, language="en"):
    support_rows = [row for row in rows if row[1] in SUPPORT_SKILL_NAMES]
    if not support_rows:
        return []
    if language == "zh":
        lines = [
            "### 管理支持 Skill 内容",
            "",
            "这些也是真实同步到仓库的 skill，由 `management-skill` 调用，但不作为主图里的单独主入口展示。",
            "",
        ]
    else:
        lines = [
            "### Management Support Skill Contents",
            "",
            "These are real mirrored skills used by `management-skill`, but they are not shown as separate primary map rows.",
            "",
        ]
    for _, skill_name, description, folder_name in support_rows:
        skill_title = f"[`{skill_name}`](./{folder_name}/)"
        lines.extend([f"#### {skill_title}", ""])
        lines.extend(skill_summary_lines(skill_name, description, language))
        lines.append("")
    return lines


def build_skill_details(rows, language="en"):
    category_labels = CHINESE_CATEGORY_LABELS if language == "zh" else CATEGORY_LABELS
    lines = [
        "### 技能内容" if language == "zh" else "### Skill Contents",
        "",
    ]
    for category in CATEGORY_ORDER:
        category_rows = [row for row in rows if row[0] == category]
        if not category_rows:
            continue
        lines.extend([f"#### {category_labels.get(category, category)}", ""])
        for row in category_rows:
            _, skill_name, description = row[:3]
            folder_name = row[3] if len(row) > 3 else ""
            skill_title = f"[`{skill_name}`](./{folder_name}/)" if folder_name else f"`{skill_name}`"
            lines.extend([f"##### {skill_title}", ""])
            lines.extend(skill_summary_lines(skill_name, description, language))
            lines.append("")
    return lines


def build_overview(skill_paths, language="en"):
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

    if language == "zh":
        lines = [
            "# 当前 Codex Skills",
            "",
            "英文版: [current_global_skills_overview.md](./current_global_skills_overview.md)",
            "",
            "## 技能图",
            "",
            *build_skill_graph(primary_rows, language="zh"),
            "",
            *build_skill_summary_table(primary_rows, language="zh"),
            "",
            f"生成日期: {time.strftime('%Y-%m-%d', time.localtime())}",
            "",
            *build_skill_details(primary_rows, language="zh"),
            "",
            *build_support_skill_details([(category, skill_name, description, skill_name) for category, skill_name, description in rows], language="zh"),
            "",
            "## Skill 列表",
            "",
            "| 类别 | Skill | 用途 |",
            "|---|---|---|",
        ]
        for category, skill_name, description in rows:
            lines.append(f"| {CHINESE_CATEGORY_LABELS.get(category, category)} | `{skill_name}` | {description} |")
        lines.extend([
            "",
            "## 结构",
            "",
            "- 代码工作进入 `code-skill`。",
            "- 固定重复流程优化进入 `optimization-skill`。",
            "- 验证工作进入 `verify-skill`。",
            "- 真实测试和报告进入 `test-skill`。",
            "- Auth 和 GitHub 镜像维护进入 `management-skill` 内部路由。",
            "- 每个 skill 可能包含多个内部路由；需要哪个就选哪个，同一个任务可以多选，不是单选，也不要运行无关分支。",
            "",
            "## 当前说明",
            "",
            "- 旧代码类 skill 已合并到 `code-skill`。",
            "- 旧测试类 skill 已合并到 `test-skill`。",
            "- UI review 已扩展到 `verify-skill`。",
            "- 旧图片 workflow skill 已删除。",
        ])
        return "\n".join(lines) + "\n"

    lines = [
        "# Current Codex Skills",
        "",
        "Chinese version: [current_global_skills_overview.zh.md](./current_global_skills_overview.zh.md)",
        "",
        "## Skill Map",
        "",
        *build_skill_graph(primary_rows, language="en"),
        "",
        *build_skill_summary_table(primary_rows, language="en"),
        "",
        f"Generated: {time.strftime('%Y-%m-%d', time.localtime())}",
        "",
        *build_skill_details(primary_rows, language="en"),
        "",
        *build_support_skill_details([(category, skill_name, description, skill_name) for category, skill_name, description in rows], language="en"),
        "",
        "## Skill List",
        "",
        "| Category | Skill | Purpose |",
        "|---|---|---|",
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
        "- Auth and GitHub mirror maintenance enter through `management-skill` internal routes.",
        "- Each skill may contain multiple internal routes; select every route needed for the current request. This is multi-select, not one-of, and unrelated cases should not run.",
        "",
        "## Current Notes",
        "",
        "- The old code skills were merged into `code-skill`.",
        "- The old testing skills were merged into `test-skill`.",
        "- UI review was broadened into `verify-skill`.",
        "- The old image workflow skill was deleted.",
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
    (repository_dir / ".gitignore").write_text(GITIGNORE_TEXT, encoding="utf-8")
    copied_names = []
    (repository_dir / "README.md").write_text(build_readme(skill_paths, language="en"), encoding="utf-8")
    (repository_dir / "README.zh.md").write_text(build_readme(skill_paths, language="zh"), encoding="utf-8")
    (repository_dir / "current_global_skills_overview.md").write_text(build_overview(skill_paths, language="en"), encoding="utf-8")
    (repository_dir / "current_global_skills_overview.zh.md").write_text(build_overview(skill_paths, language="zh"), encoding="utf-8")
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

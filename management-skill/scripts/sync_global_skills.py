#!/usr/bin/env python3
import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
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
local/
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
    "local",
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
    re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----"),
    re.compile(r'"(?:access_token|refresh_token|id_token|session_token|api_key|secret|password)"\s*:\s*"[^"\n]{12,}"', re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"\n]{12,}['\"]", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[A-Za-z0-9._-]+/"),
    re.compile(r"(?<![A-Za-z0-9])[A-Z]:\\Users\\[^\\\r\n]+\\", re.IGNORECASE)
)
CATEGORY_ORDER = ["Workflow", "Code", "Optimization", "Generation", "Verification", "Management", "General"]
PRIMARY_SKILL_ORDER = ["task-analyze-skill", "workflow-skill", "prompt-skill", "code-skill", "project-memory-skill", "verify-skill", "optimization-skill", "management-skill"]
APPROVED_GLOBAL_SKILL_NAMES = set(PRIMARY_SKILL_ORDER)
SUPPORT_SKILL_NAMES = set()
ENGLISH_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.md"
CHINESE_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.zh.md"
CATEGORY_LABEL_WIDTH = 28
SKILL_LABEL_WIDTH = 24
CATEGORY_LABELS = {
    "Workflow": "Workflow / 工作流类",
    "Code": "Code / 代码类",
    "Optimization": "Optimization / 优化类",
    "Generation": "Generation / 生成类",
    "Verification": "Verification / 验证类",
    "Management": "Management / 管理类",
    "General": "General / 通用类",
}
CHINESE_CATEGORY_LABELS = {
    "Workflow": "工作流类 / Workflow",
    "Code": "代码类 / Code",
    "Optimization": "优化类 / Optimization",
    "Generation": "生成类 / Generation",
    "Verification": "验证类 / Verification",
    "Management": "管理类 / Management",
    "General": "通用类 / General",
}
SKILL_SUMMARIES = {
    "task-analyze-skill": "Explicit routing, benchmark, and maintenance strategy. The always-loaded hookless bootstrap keeps ordinary work on the current model; the full skill defaults to inline and admits delegation only with comparable end-to-end proof.",
    "workflow-skill": "Executes only a positively admitted Task Analyze route. Ordinary work of any apparent complexity stays inline; admitted nodes keep locked pairs and receipts, present the completed result, then hand verification to Ending Real.",
    "prompt-skill": "The 100% global gate for reusable prompt and durable-instruction creation, review, edit, repair, standardization, testing, summarization, and optimization. It stays inline on the current model and excludes ordinary prose.",
    "code-skill": "Direct inline or admitted-route executor for active registry-owned code domains; Python, plain C#, and Unity C# are built-in examples. Ordinary work keeps the current model; Spark is only an admitted obvious-task route.",
    "project-memory-skill": "Recalls and records project changes by project, functional module, and concrete file, with a private local authority and optional Obsidian projection.",
    "optimization-skill": "Turns explicit, repeated, or clearly reusable workflows into scripts, references, prompts, assets, or templates while preserving behavior.",
    "verify-skill": "Real Verify runs in Ending Task after the completed result is presented and applies its verdict to the original receipt-backed result attempt.",
    "management-skill": "Handles Codex profile operations and global skill GitHub sync while preserving local private folders, local route history, and model-experience files from public mirrors.",
}
CHINESE_SKILL_SUMMARIES = {
    "task-analyze-skill": "显式路由、benchmark 和维护策略：常驻的无 hook inline bootstrap 让普通任务直接使用当前模型；完整 skill 默认仍返回 inline，只有端到端可比证据通过才允许委派。",
    "workflow-skill": "只执行已经通过端到端性能准入的 Task Analyze 锁定路线。无论表面复杂度如何，普通任务都保持 inline；已准入节点保留锁定 pair 和 receipt。",
    "prompt-skill": "可复用 prompt 与持久 AI 指令创建、审查、编辑、修复、标准化、测试、总结和优化的全局 100% 入口。它在当前模型 inline 执行，普通文案不会误触发。",
    "code-skill": "活动注册代码域的 direct-inline 或已准入路线执行者；Python、普通 C#、Unity C# 是内置示例。普通任务保留当前模型；Spark 只用于已准入的明显小任务路线。",
    "project-memory-skill": "按项目、功能模块和具体文件回溯与记录修改，本地私有记录为权威来源，Obsidian 为可选投影。",
    "optimization-skill": "把明确要求、重复多次或明显可复用的流程变成本地脚本、引用资料、prompt、资产或模板，同时保持行为不变。",
    "verify-skill": "完成的主结果先立即展示；Real Verify 之后在 Ending Task 中执行，并把判定回填到原始的 receipt-backed 结果尝试。",
    "management-skill": "处理 Codex profile 操作和全局 skill GitHub 同步，不暴露私人数据，并保留本地私有路由历史。",
}
SKILL_CONTENTS = {"task-analyze-skill": [("Hookless inline bootstrap", "The always-loaded policy keeps every ordinary request on the current model without loading this full skill."), ("Explicit activation boundary", "Load full Task Analyze only for routing/benchmark/maintenance or a graph under consideration; activation still defaults to inline."), ("Performance admission", "Delegation requires current comparable proof that the complete Global path preserves correctness and beats Direct in tokens and time."), ("Admitted route display", "Only admitted single nodes get concise text and admitted dependency graphs get Mermaid plus a numbered model list."), ("Runtime proof", "Raw Direct and Global arms use receipt-backed exact-workload evidence before any savings or delegation claim.")], "workflow-skill": [("Admitted route execution", "Execute only a positively admitted Task Analyze plan with exact locked pairs and matching receipts."), ("Inline rejection", "Reject missing, stale, cross-workload, incomplete, or negative admission and return execution to the current model."), ("Main Goal / Ending Task split", "The admitted main lane completes the requested work, presents the result immediately, and leaves verification to Ending Real."), ("Dependency topology", "Execute only dependency-ready nodes, use one surface per branch, and reserve dispatch for real multi-node graphs."), ("Runtime accounting", "Count the complete entry/controller/child path and never use producer-only savings as delegation proof.")], "prompt-skill": [("100% global prompt gate", "Always load Prompt for reusable prompt or durable-instruction creation, review, edit, repair, standardization, testing, summarization, or optimization across projects."), ("Ordinary-prose exclusion", "Do not trigger merely because an ordinary request is text; the requested artifact or target behavior must itself be a reusable prompt or durable AI instruction."), ("Conditional prompt controls", "Use role, workflow/tools, autonomy, reasoning, verbosity, delimiters, and examples only when they materially improve behavior."), ("Conflict-free contracts", "Require explicit objective, inputs, requirements/constraints, output, success/failure, and verification without visible chain-of-thought or blanket question gates."), ("Result-first prompt testing", "Present the completed prompt first; representative trials and Real Verify run afterward in Ending Task and reopen failures.")], "code-skill": [("Prompt-in-code integration", "Load Prompt first, then apply Python/C#/Unity C# executable-string, formatting, and ownership rules."), ("Karpathy Coding Guidelines", "Code thinking and implementation approach for assumptions, simple design, naming, branching, and surgical edits."), ("Python Code Checker", "Python modules, scripts, tests, snippets, prompt assignments, formatting, contracts, error handling, and logging rules."), ("C# Minimal Style", "C# and Unity C# MonoBehaviours, ScriptableObjects, managers, gameplay systems, editor scripts, lifecycle methods, and C# style."), ("Easy Python/C# Spark", "Ordinary bounded Python/C# work stays on the current user model. Spark-low appears only in an explicit benchmark or a positively admitted tiny route, with the full normal fallback retained.")], "optimization-skill": [("Skill Optimization", "Optimize explicit, repeated-at-least-three-times, or clearly reusable stable workflows into local scripts, references, assets, prompts, or templates that save tokens."), ("Official skill compliance", "Audit skill structure, frontmatter, trigger descriptions, references, scripts, assets, and token-use behavior."), ("Local Script Conversion", "Turn stable repeated verification, image, browser, computer-control, report, or generation steps into reusable local code."), ("Reference extraction", "Move long stable instructions into references/ so they load only when the task needs them."), ("Assets and templates", "Store reusable fixtures, templates, or media in assets/ when those files are part of the optimized skill.")], "verify-skill": [("UI Review", "UI/UX, layout, responsive checks, screenshots, frontend polish, browser states, and Taste Skill visual QA."), ("Local Script Verification", "Optimized local scripts and workflows with concrete cache inputs, real outputs, rerun behavior, and output paths."), ("Skill Verification", "SKILL.md frontmatter, trigger wording, referenced files, old-name cleanup, route behavior, and skill structure."), ("Generated Artifact Verification", "Markdown, images, PDFs, documents, reports, data files, and exports through open/render/parse/inspect checks."), ("Real Evidence And Reports", "Run real checks after result presentation with concrete inputs and outputs, choose chat/Markdown/PDF evidence by complexity, and require Input/Used/Output/Why Pass for reports.")], "management-skill": [("Codex Switch", "Local Codex auth profiles, saved profile listing, usage snapshots, login refresh, profile backup/import, and confirmed account switching."), ("GitHub Sync", "Global skill mirror status, preuse checks, public-safety scan, sync, pull, push, commit, and remote hash verification."), ("Privacy-Safe Management", "Auth files, tokens, cookies, profile IDs, raw logs, cache files, and secrets stay local and are never published.")]}
CHINESE_SKILL_CONTENTS = {"task-analyze-skill": [("无 hook inline bootstrap", "常驻策略让所有普通任务直接使用当前模型，不加载完整 Task Analyze skill。"), ("显式激活边界", "只有路由、benchmark、维护或待评估图谱才加载完整 Task Analyze；激活后默认仍是 inline。"), ("性能准入", "只有完整 Global 路径保持正确并在 token 和时间都优于 Direct 的当前可比证据，才允许委派。"), ("已准入路线显示", "仅已准入的单节点显示精简文本，已准入依赖图显示 Mermaid 和编号模型列表。"), ("运行时证明", "Raw Direct 和 Global 必须有同一 workload 的 receipt 证据后才能声明节省或准入。")], "workflow-skill": [("已准入路线执行", "只执行通过性能准入的 Task Analyze 计划，保留准确锁定 pair 和匹配 receipt。"), ("Inline 回退", "准入证据缺失、过期、跨 workload、不完整或为负时，拒绝委派并回到当前模型 inline。"), ("Main Goal / Ending Task 分流", "已准入主线完成请求后立即显示结果，验证交给之后的 Ending Real。"), ("依赖拓扑", "只执行依赖就绪节点，每个分支使用一个执行面，只有真实多节点图才 dispatch。"), ("运行时计数", "计算完整 entry/controller/child 路径，绝不把 producer-only 节省当作委派证明。")], "prompt-skill": [("全局 100% Prompt 入口", "所有项目中的可复用 prompt 或持久 AI 指令创建、审查、编辑、修复、标准化、测试、总结与优化都必须加载 Prompt。"), ("普通文案排除", "普通请求只是文本时不触发；请求目标本身必须是可复用 prompt 或持久 AI 指令。"), ("条件化 Prompt 控制", "角色、工作流/工具、自主性、推理、详细度、分隔符和示例只有在确实改善行为时才加入。"), ("无冲突契约", "明确目标、输入、要求/约束、输出、成功/失败和验证，不要求展示思维链，也不设置一刀切提问门槛。"), ("结果优先测试", "先展示完成的 prompt；代表性试验和 Real Verify 随后在 Ending Task 中运行，失败则重新打开修复。")], "code-skill": [("Prompt-in-code 集成", "先加载 Prompt，再应用 Python/C#/Unity C# 可执行字符串、格式和代码所有权规则。"), ("Karpathy Coding Guidelines", "代码思考和实现方式：假设、简单设计、命名、分支和精确修改。"), ("Python Code Checker", "Python 模块、脚本、测试、片段、prompt 变量、格式、契约、错误处理和日志规则。"), ("C# Minimal Style", "C# 和 Unity C# MonoBehaviour、ScriptableObject、manager、玩法系统、编辑器脚本、生命周期方法和 C# 风格。"), ("Easy Python/C# Spark", "普通的小范围 Python/C# 工作保留当前用户模型。Spark-low 只会出现在显式 benchmark 或已通过准入的 tiny 路线中，并保留完整常规 fallback。")], "optimization-skill": [("Skill Optimization", "把明确要求、重复至少三次或明显可复用的稳定流程优化成本地脚本、引用资料、资产、prompt 或模板。"), ("官方 skill 合规检查", "检查 skill 结构、frontmatter、触发描述、references、scripts、assets 和 token 使用方式。"), ("本地脚本转换", "把稳定重复的验证、图片、浏览器、电脑控制、报告或生成步骤转成本地可复用代码。"), ("引用资料抽取", "把较长且稳定的说明移到 references/，只在任务需要时加载。"), ("资产和模板", "当可复用 fixture、模板或媒体属于 skill 的一部分时，放进 assets/。")], "verify-skill": [("UI Review", "UI/UX、布局、响应式检查、截图、前端 polish、浏览器状态和 Taste Skill 视觉 QA。"), ("本地脚本验证", "验证优化后的本地脚本和流程，检查 cache 输入、真实输出、重复运行和输出路径。"), ("Skill 验证", "检查 SKILL.md frontmatter、触发说明、引用文件、旧名称清理、路由行为和 skill 结构。"), ("生成物验证", "通过打开、渲染、解析或检查来验证 Markdown、图片、PDF、文档、报告、数据文件和导出物。"), ("真实证据和报告", "主结果展示后再用具体输入和真实输出运行检查，按复杂度选择聊天/Markdown/PDF 证据，并要求报告包含 Input/Used/Output/Why Pass。")], "management-skill": [("Codex Switch", "本地 Codex auth profile、已保存 profile 列表、使用快照、登录刷新、profile 备份/导入和确认后的账号切换。"), ("GitHub Sync", "全局 skill 镜像状态、preuse 检查、公开安全扫描、sync、pull、push、commit 和远端 hash 验证。"), ("隐私安全管理", "auth 文件、token、cookie、profile ID、原始日志、cache 文件和 secret 保持本地，不发布出去。")]}


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


def symlink_issues(paths):
    issues = []
    for root in paths:
        _, root_issues = _scan_tree(Path(root))
        issues.extend(root_issues)
    return sorted(issues, key=lambda path: path.as_posix())


def _scan_tree(root):
    files = []
    issues = []
    if root.is_symlink():
        return files, [root]
    if not root.exists():
        return files, issues
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = directory / entry.name
                if entry.is_symlink():
                    issues.append(path)
                    continue
                relative_path = path.relative_to(root)
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif not any(part in EXCLUDED_PARTS for part in relative_path.parts) and not path.name.endswith(EXCLUDED_SUFFIXES) and entry.is_file(follow_symlinks=False):
                    files.append(path)
    return files, issues


def assert_no_symlinks(paths, label="skill source tree"):
    issues = symlink_issues(paths)
    if issues:
        message = f"Refusing {label} containing symlinks:\n"
        message += "\n".join(f"- {path}" for path in issues)
        raise RuntimeError(message)


def all_skill_directories(skills_dir):
    return sorted([path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()], key=lambda path: path.name)


def skill_directories(skills_dir):
    return [skills_dir / name for name in PRIMARY_SKILL_ORDER if (skills_dir / name / "SKILL.md").exists()]


def included_files(skill_dir):
    skill_dir = Path(skill_dir)
    files, issues = _scan_tree(skill_dir)
    if issues:
        message = f"Refusing skill tree containing symlinks:\n"
        message += "\n".join(f"- {path}" for path in sorted(issues, key=lambda path: path.as_posix()))
        raise RuntimeError(message)
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
        files, symlink_paths = _scan_tree(skill_path)
        for symlink_path in symlink_paths:
            try:
                relative_path = symlink_path.relative_to(skill_path)
            except ValueError:
                relative_path = Path(symlink_path.name)
            issues.append(f"{skill_path.name}/{relative_path.as_posix()}: symlink")
        if symlink_paths:
            continue
        for path in sorted(files, key=lambda path: path.relative_to(skill_path).as_posix()):
            relative_path = path.relative_to(skill_path)
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


def assert_approved_global_skill_set(skill_paths):
    observed_names = {path.name for path in skill_paths}
    unexpected_names = sorted(observed_names - APPROVED_GLOBAL_SKILL_NAMES)
    missing_names = sorted(APPROVED_GLOBAL_SKILL_NAMES - observed_names)
    if unexpected_names or missing_names:
        message = "Refusing to mirror global skills because the approved mirror selection must contain exactly:\n"
        message += "\n".join(f"- {skill_name}" for skill_name in PRIMARY_SKILL_ORDER)
        if unexpected_names:
            message += "\nUnexpected folders found:\n" + "\n".join(f"- {skill_name}" for skill_name in unexpected_names)
        if missing_names:
            message += "\nRequired folders missing:\n" + "\n".join(f"- {skill_name}" for skill_name in missing_names)
        message += "\nUnrelated local skill folders are intentionally ignored and preserved. Check the approved eight before publishing."
        raise RuntimeError(message)


def assert_repository_skill_set(repository_dir):
    observed_names = {path.name for path in all_skill_directories(repository_dir)}
    if observed_names != APPROVED_GLOBAL_SKILL_NAMES:
        unexpected_names = sorted(observed_names - APPROVED_GLOBAL_SKILL_NAMES)
        missing_names = sorted(APPROVED_GLOBAL_SKILL_NAMES - observed_names)
        message = "Refusing to pull because the remote mirror must contain exactly the approved eight skills."
        if unexpected_names:
            message += "\nUnexpected remote skills:\n" + "\n".join(f"- {name}" for name in unexpected_names)
        if missing_names:
            message += "\nMissing remote skills:\n" + "\n".join(f"- {name}" for name in missing_names)
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


def load_staged_routing_policy(skill_paths):
    """Load and validate the registry from the exact staged mirror inputs."""
    by_name = {path.name: path for path in skill_paths}
    task_skill = by_name.get("task-analyze-skill")
    if task_skill is None:
        raise RuntimeError("cannot render execution domains: task-analyze-skill is missing")
    policy_path = task_skill / "scripts" / "routing_policy.py"
    if not policy_path.is_file():
        raise RuntimeError(f"cannot render execution domains: registry is missing: {policy_path}")
    spec = importlib.util.spec_from_file_location("staged_routing_policy", policy_path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot render execution domains: registry loader is unavailable")
    try:
        spec.loader.exec_module(module)
    except (OSError, ValueError) as error:
        raise RuntimeError(f"cannot render execution domains: {error}") from error
    try:
        module.validate_execution_domain_registry(task_skill.parent)
        return module.public_execution_domain_rows()
    except (AttributeError, ValueError) as error:
        raise RuntimeError(f"cannot render execution domains: {error}") from error


def execution_domain_table(rows):
    lines = []
    for row in rows:
        state = "active" if row["active"] else "history-only"
        spark = "yes" if row["spark_first"] else "no"
        lines.append(f"- `{row['id']}` · {row['kind']} · `{row['owner_skill']}` · {state} · Spark: {spark} · [rules](./{row['reference_path']})")
    return "\n".join(lines)


def build_readme(skill_paths, language="en"):
    template_path = CHINESE_README_TEMPLATE if language == "zh" else ENGLISH_README_TEMPLATE
    template = template_path.read_text(encoding="utf-8").rstrip() + "\n"
    marker = "<!-- EXECUTION_DOMAIN_TABLE -->"
    if template.count(marker) != 1:
        raise RuntimeError(f"{template_path.name} must contain exactly one execution-domain marker")
    return template.replace(marker, execution_domain_table(load_staged_routing_policy(skill_paths)))


def skill_category(skill_name, description):
    text = f"{skill_name} {description}".lower()
    if skill_name in {"task-analyze-skill", "workflow-skill"}:
        return "Workflow"
    if skill_name == "code-skill":
        return "Code"
    if skill_name == "optimization-skill":
        return "Optimization"
    if skill_name in {"management-skill", "project-memory-skill"}:
        return "Management"
    if "github" in text or "auth" in text:
        return "Management"
    if skill_name == "verify-skill":
        return "Verification"
    if "testing" in text or "report" in text:
        return "Verification"
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
        if skill_name == "task-analyze-skill":
            return "显式路由与准入策略"
        return "已准入路线执行控制器" if skill_name == "workflow-skill" else "Inline 或已准入路线执行者"
    if skill_name == "task-analyze-skill":
        return "Explicit routing and admission strategy"
    return "Admitted-route controller" if skill_name == "workflow-skill" else "Inline or admitted-route executor"


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
        role_label = skill_role(skill_name, language)
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


def workflow_lane_section(language="en"):
    if language == "zh":
        return ["## Main Goal 和 Ending Task", "", "普通任务无论表面复杂度如何，都由当前模型 inline 完成；完整 Task Analyze 只处理显式路由/benchmark/维护或评估图谱，Workflow 只执行已通过端到端准入的路线。", "", "```mermaid", "flowchart TD", "  A[\"用户请求\"] --> B[\"无 hook inline bootstrap\"]", "  B --> C[\"当前模型执行请求\"]", "  C --> E[\"立即显示已完成的主结果\"]", "  B -->|显式路由 / benchmark / 维护| F[\"Task Analyze\"]", "  F -->|未通过准入| C", "  F -->|通过准入| G[\"workflow-skill 执行锁定节点\"]", "  G --> E", "  E --> I[\"Ending Real 验证与学习\"]", "```", "", "- **Inline：** 默认且适用于所有表面复杂度；不加载完整 Task Analyze 或 Workflow。", "- **主结果：** 任务完成后立即展示，不运行前台 Mini/Fast Verify；first-result 时间在此停止。", "- **Ending Real：** 在展示后做真实验证、失败通知、修复与学习。", "- **Workflow：** 只有完整 Global 路径有当前可比的正确性、token 和时间准入证据时才运行。", ""]
    return ["## Main Goal And Ending Task", "", "Ordinary requests stay inline on the current model regardless of apparent complexity. Full Task Analyze handles explicit routing, benchmarks, maintenance, or graph evaluation; Workflow executes only positively admitted routes.", "", "```mermaid", "flowchart TD", "  A[\"User request\"] --> B[\"Hookless inline bootstrap\"]", "  B --> C[\"Current model executes request\"]", "  C --> E[\"Present completed result immediately\"]", "  B -->|explicit routing / benchmark / maintenance| F[\"Task Analyze\"]", "  F -->|not admitted| C", "  F -->|admitted| G[\"workflow-skill executes locked nodes\"]", "  G --> E", "  E --> I[\"Ending Real verification and learning\"]", "```", "", "- **Inline:** the default for every apparent complexity; it does not load full Task Analyze or Workflow.", "- **Main result:** present it immediately when complete, with no foreground Mini/Fast Verify; first-result time stops there.", "- **Ending Real:** verifies after presentation, then notifies, reopens, repairs, and learns when needed.", "- **Workflow:** runs only when current comparable correctness, token, and time evidence admits the complete Global path.", ""]


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
        lines = ["# 当前 Codex Skills", "", "英文版: [README.md](./README.md)", "", "## 技能图", "", *build_skill_graph(primary_rows, language="zh"), "", *workflow_lane_section(language="zh"), *build_skill_summary_table(primary_rows, language="zh"), "", *build_support_skill_details([(category, skill_name, description, skill_name) for category, skill_name, description in rows], language="zh"), "", "## 运行规则", "", "- 单范围任务由当前模型一次读取、一次输出，完成后立即显示；不运行前台 Mini/Fast Verify。", "- 三个及以上独立非简单部分可由父任务保留最大部分，并只开两个互不重叠的同模型子任务；禁止重复读取和集中复核。", "- 只有显式路由、benchmark、Task Analyze 维护或待评估图谱才加载完整 `task-analyze-skill`；激活后默认仍是 inline。", "- `workflow-skill` 只有完整 Global 路径在相同 workload/config/entry cohort 下通过正确性、token 和时间准入时才运行。", "- first-result 时间在已完成结果展示时停止，排除之后的所有 Ending Real 工作。", "- 正确性是 gate；只有至少两个 Real 通过 pair 在相同 workload hash cohort 中且 token/time 完整时，才按总 token、process time、较弱 rung 排序；否则使用质量边界，不声明节省。", "- 模型降级先降低 effort，再降低 model；升级顺序相反。相似任务一旦找到已验证最佳 pair 就冻结，只有 Ending Real 失败或 profile/ladder 漂移才重新搜索。", "- Ending Real 在结果展示后验证并更新同一个 producer attempt，持久化并冻结 `best_pair`；验证失败则通知、重新打开并修复。", "- 非 tiny 委派路线保留完整 Luna/Terra/Sol ladder；tiny 路线必须是 `Spark-low + 完整常规 fallback`。", "- 每个活动的注册代码域都进入 `code-skill`；Python、普通 C#、Unity C# 是内置示例。", "- benchmark 两边固定相同的 `model|effort`（本次为 `gpt-5.6-sol | ultra`）：Direct 使用 raw `--direct-task`，Global 使用 raw `--bootstrap-task`；两者都在 entry context 外运行，不使用 `LOCKED_ROUTE_NODE`，也不忽略用户配置。", "- 私有 ledger 在 `task-analyze-skill/local/adaptive-routing/model_experience.json`，不进入镜像。"]
        return "\n".join(lines) + "\n"


def copy_skill_directory(source_dir, target_dir, preserve_local=False):
    assert_no_symlinks([source_dir], "source skill tree")
    if target_dir.exists() or target_dir.is_symlink():
        assert_no_symlinks([target_dir], "target skill tree")
    local_source = target_dir / "local"
    if preserve_local and local_source.exists():
        assert_no_symlinks([local_source], "preserved local content")
        with tempfile.TemporaryDirectory(prefix="qin-codex-private-local-") as sandbox_name:
            preserved_local = Path(sandbox_name) / "local"
            shutil.copytree(local_source, preserved_local)
            shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir, ignore=ignored_names)
            shutil.copytree(preserved_local, target_dir / "local")
        return
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
    assert_no_symlinks([repository_dir], "repository tree")
    assert_repository_skill_set(repository_dir)
    remote_paths = skill_directories(repository_dir)
    remote_names = {path.name for path in remote_paths}
    changed_names = []
    for path in skill_directories(skills_dir):
        if path.name not in remote_names:
            assert_no_symlinks([path], "local skill tree")
            shutil.rmtree(path)
            changed_names.append(path.name)
    for path in remote_paths:
        if path_differs(path, skills_dir / path.name):
            copy_skill_directory(path, skills_dir / path.name, preserve_local=path.name == "task-analyze-skill")
            changed_names.append(path.name)
    return changed_names


def remote_changes(repository, skills_dir):
    with tempfile.TemporaryDirectory(prefix="qin-codex-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        remote_by_name = {path.name: path for path in skill_directories(repository_dir)}
        return [name for name in PRIMARY_SKILL_ORDER if name not in remote_by_name or path_differs(remote_by_name[name], skills_dir / name)]


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
    assert_no_symlinks([repository_dir], "repository tree")
    skill_paths = skill_directories(skills_dir)
    assert_approved_global_skill_set(skill_paths)
    assert_no_symlinks(skill_paths, "approved source skill trees")
    load_staged_routing_policy(skill_paths)
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
    (repository_dir / "README.md").write_text(build_readme(skill_paths, language="en"))
    (repository_dir / "README.zh.md").write_text(build_readme(skill_paths, language="zh"))
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
    render_parser = subparsers.add_parser("render-readme")
    render_parser.add_argument("--output", type=Path, required=True)
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
    elif args.command == "render-readme":
        skill_paths = skill_directories(args.skills_dir)
        assert_approved_global_skill_set(skill_paths)
        assert_public_safe(skill_paths)
        args.output.expanduser().resolve().write_text(build_readme(skill_paths, language="en"), encoding="utf-8")
        print(f"Rendered public README: {args.output.expanduser().resolve()}")
    elif args.command == "push":
        push(args.repo, args.skills_dir, args.message, False)


if __name__ == "__main__":
    main()

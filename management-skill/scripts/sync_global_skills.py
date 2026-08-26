#!/usr/bin/env python3
import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path


def load_skill_platform_checker(skills_dir):
    checker_path = Path(skills_dir) / "code-skill" / "scripts" / "skill_platform_check.py"
    module_spec = importlib.util.spec_from_file_location("skill_platform_check", checker_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Refusing to publish because the skill platform gate is unavailable: {checker_path}")
    checker_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(checker_module)
    return checker_module


DEFAULT_REPOSITORY = "qinbatista/qin-codex-skills"
DEFAULT_SOURCE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_ROOT = Path.cwd().resolve()
DEFAULT_CACHE_ROOT = DEFAULT_PROJECT_ROOT / "Cache" / "tmp-management-skill-sync"
DEFAULT_STATE_FILE = DEFAULT_CACHE_ROOT / "state" / "management-skill-sync.json"
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
    "Cache",
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
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[A-Za-z0-9._-]+/", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])\\(?:Users|home)\\[A-Za-z0-9._-]+\\", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])[A-Z]:\\Users\\[^\\\r\n]+\\", re.IGNORECASE)
)
CATEGORY_ORDER = ["Workflow", "Code", "Optimization", "Generation", "Verification", "Management", "General"]
PRIMARY_SKILL_ORDER = ["task-analyze-skill", "workflow-skill", "prompt-skill", "code-skill", "project-memory-skill", "verify-skill", "optimization-skill", "management-skill"]
APPROVED_GLOBAL_SKILL_NAMES = set(PRIMARY_SKILL_ORDER)
SUPPORT_SKILL_NAMES = set()
GLOBAL_AGENTS_ASSET = Path("task-analyze-skill") / "assets" / "global-agents-entry-rule.md"
GLOBAL_AGENTS_DIRECTIVE = "This template is written only by the explicit `install-global-agents` command; deploy, pull, and sync preserve user AGENTS.md files.\n\n"
LEGACY_GLOBAL_AGENTS_DIRECTIVE = "Merge this section into `~/.codex/AGENTS.md` and `~/AGENTS.md`.\n\n"
GLOBAL_AGENTS_BACKUP_DIRECTORY = "global-agents-backups"
GLOBAL_AGENTS_BACKUP_MANIFEST = "manifest.json"
OFFICIAL_USER_SKILLS_DIRECTORY = Path.home() / ".agents" / "skills"
INSTALL_TRANSACTION_PREFIX = ".qin-codex-install-"
INSTALL_MANIFEST_NAME = "install-transaction.json"
INSTALL_LOCK_NAME = ".qin-codex-install.lock"
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
    "task-analyze-skill": "Explicit routing, benchmark, and maintenance strategy. The compact bootstrap sends eligible ordinary production to the saved contextual quality pair; full Task Analyze owns strategy and cost-admitted graphs.",
    "workflow-skill": "Executes only positively admitted locked routes. Producers retain exact pairs and receipts, return the result, then hand bounded checks to one fast Ending.",
    "prompt-skill": "The 100% global gate for reusable prompt and durable-instruction creation, review, edit, repair, standardization, testing, summarization, and optimization. The selected producer loads it; ordinary prose is excluded.",
    "code-skill": "Adaptive or admitted-route executor for active registry-owned code domains; Python, plain C#, and Unity C# are built-in examples. The saved task-strategy pair executes ordinary work; eligible small work reaches Spark only after the same-session outcome gate.",
    "project-memory-skill": "Recalls and records project changes with mandatory project/module/method coverage plus concrete file evidence, using a private local authority and optional native Obsidian projection.",
    "optimization-skill": "Turns explicit, repeated, or clearly reusable workflows into scripts, references, prompts, assets, or templates while preserving behavior.",
    "verify-skill": "One post-result Ending uses fixed Spark-xhigh for the smallest real checks and terminal memory/classification; only explicit availability/capability failure permits Luna-low.",
    "management-skill": "Handles Codex profile operations and source-first global Skill deployment/publication behind a numbered retained-capability regression gate.",
}
CHINESE_SKILL_SUMMARIES = {
    "task-analyze-skill": "显式路由、benchmark 和维护策略：紧凑 bootstrap 把合格普通生产任务交给已保存的上下文质量档；完整 skill 负责策略和成本准入图谱。",
    "workflow-skill": "只执行已通过准入的锁定路线。Producer 保留准确 pair 和 receipt，先返回结果，再把有界检查交给一个快速 Ending。",
    "prompt-skill": "可复用 prompt 与持久 AI 指令创建、审查、编辑、修复、标准化、测试、总结和优化的全局 100% 入口。选中的 producer 加载它；普通文案不会误触发。",
    "code-skill": "活动注册代码域的自适应或已准入路线执行者；Python、普通 C#、Unity C# 是内置示例。普通任务使用任务策略质量档；合格小任务先过同会话结果门再试 Spark。",
    "project-memory-skill": "强制按项目、功能模块和方法建立覆盖，再用具体文件证据回溯与记录修改；本地私有记录为权威来源，Obsidian 为可选原生投影。",
    "optimization-skill": "把明确要求、重复多次或明显可复用的流程变成本地脚本、引用资料、prompt、资产或模板，同时保持行为不变。",
    "verify-skill": "主结果先展示；一个 Ending 固定使用 Spark-xhigh 做最小真实检查与记忆/分类收尾，仅明确不可用时回退 Luna-low。",
    "management-skill": "处理 Codex profile 操作，以及由编号化全能力非回归门禁保护的全局 Skill 本地部署和 GitHub 发布。",
}
SKILL_CONTENTS = {
    "task-analyze-skill": [
        ("Adaptive bootstrap", "Eligible ordinary production executes the saved contextual quality pair without loading the full routing skill."),
        ("Receipt-backed movement", "One Real PASS retains, two matched PASS outcomes try one weaker rung, and quality failure upgrades one rung."),
        ("Session-effort solving routes", "The router excludes the current turn, links prior session routes to verified terminal outcomes, resets after a pass, and gradually strengthens only an unresolved same-topic correction."),
        ("Source-cost admission", "Two or three independent sources choose one producer or a fused graph from byte and session-context estimates before content reads."),
        ("Performance admission", "Open-ended graphs and savings claims require current comparable correctness, token, and time evidence."),
        ("Two-world benchmark", "Direct task has no verifier; Auto returns the task result before a separate Ending check; dispatcher cost remains a disclosed diagnostic."),
    ],
    "workflow-skill": [
        ("Locked route execution", "Execute only a positively admitted plan with exact pairs, dependencies, allowlists, and receipts."),
        ("Single-producer default", "Dependency-coupled work and small independent sources stay with one contextual producer."),
        ("Result-first handoff", "The producer completes one Quick Check, presents the result, then creates a global-only projectless End Task and confirms list_threads reports projectId=null/absent."),
        ("Ending visibility", "PASS, FAIL, and BLOCKED remain visible; Ending tasks and repair handoffs never auto-archive or delete themselves."),
        ("Runtime proof", "Every model-generated node exposes its effective pair and token/time receipt."),
    ],
    "prompt-skill": [
        ("100% global prompt gate", "Always load Prompt for reusable prompt or durable-instruction creation, review, edit, repair, standardization, testing, summarization, or optimization."),
        ("Ordinary-prose exclusion", "Do not trigger merely because an ordinary request is text; the requested artifact must itself be a reusable prompt or durable AI instruction."),
        ("Conditional prompt controls", "Use role, workflow/tools, autonomy, reasoning, verbosity, delimiters, and examples only when they materially improve behavior."),
        ("Conflict-free contracts", "Require explicit objective, inputs, requirements, output, success/failure, and verification without visible chain-of-thought."),
        ("Result-first prompt testing", "Present the completed prompt first; representative trials and evidence checks run afterward in Ending."),
    ],
    "code-skill": [
        ("Prompt-in-code integration", "Load Prompt first, then apply Python, C#, or Unity C# executable-string, formatting, and ownership rules."),
        ("Karpathy Coding Guidelines", "Use explicit assumptions, simple design, clear naming, shallow branching, and surgical edits."),
        ("Proportional Quick Check", "Light local work gets a minimal smoke; heavy/API/large/side-effect work checks syntax, names, imports, and references."),
        ("Adaptive execution", "The task-strategy quality pair executes ordinary code work; Spark is reserved for cost-admitted independent source branches."),
        ("Result ownership", "One producer owns the edit, Quick Check, receipt, and completed result."),
    ],
    "project-memory-skill": [
        ("Working-line recall", "Recall project, module, file, symbol, branch, and version-scoped change history before editing."),
        ("Verified record", "Record only the final verified change after the result is complete."),
        ("Private authority", "Local JSONL is authoritative with optional Obsidian projection; public mirrors exclude private records."),
    ],
    "optimization-skill": [
        ("Skill Optimization", "Optimize explicit, repeated, or clearly reusable workflows into local scripts, references, assets, prompts, or templates."),
        ("Behavior preservation", "Remove deterministic waste without weakening correctness or changing user-visible contracts."),
        ("Evidence separation", "The optimizer presents the finished result and a different Ending session checks immutable evidence."),
        ("Reference extraction", "Move long stable instructions into references so they load only when needed."),
        ("Assets and templates", "Store reusable fixtures, templates, or media when they are part of the optimized skill."),
    ],
    "verify-skill": [
        ("Proportional completion evidence", "The producer owns the bounded Quick Check before presentation."),
        ("Persistent End Task", "Create global-only projectless End Task-<related task>, confirm list_threads reports projectId=null/absent, and keep every terminal status visible."),
        ("Fixed fast executor", "Use Spark-xhigh for every Ending; score scopes checks, and only explicit availability/capability failure permits registry-floor Luna-low."),
        ("Real-check boundary", "Run the smallest supplied real checks once; a failing verifier records evidence and returns repair to the immutable origin."),
        ("Terminal verdict", "One visible verdict closes routing classification, project-result memory when applicable, and the bounded preference scan."),
    ],
    "management-skill": [
        ("Codex Switch", "Manage local Codex auth profiles and confirmed account switching."),
        ("Consumer replacement", "Consumer install/update shallow-clones the published source and replaces only the eight managed Skills with mechanical safety. Global AGENTS installation is explicit, backed up, and recoverable; maintainer push runs the release gate once before publication."),
        ("GitHub Sync", "Run preuse checks, public-safety scan, sync, push, and remote hash verification for both mirrors."),
        ("Privacy-Safe Management", "Auth, tokens, cookies, raw prompts/results, receipts, logs, caches, and private learning stay local."),
    ],
}
CHINESE_SKILL_CONTENTS = {
    "task-analyze-skill": [
        ("自适应 bootstrap", "合格普通生产任务直接执行已保存的上下文质量档，不加载完整路由 skill。"),
        ("Receipt 证据移动", "一次 Real PASS 保留，两次匹配 PASS 降一级，质量失败升一级。"),
        ("Session effort 解题路线", "路由先排除当前 turn，再把历史 route 关联到已验证终态；PASS 重置，只有同主题未解决修正才逐步增强模型；跳题开启独立状态。"),
        ("Source 成本准入", "两个或三个独立 source 在读取前根据 byte 与会话上下文估算选择单 producer 或融合 graph。"),
        ("性能准入", "开放式 graph 与节省声明必须有当前可比的正确性、token 和时间证据。"),
        ("双世界 benchmark", "Direct 主任务无 verifier；Auto 先返回结果再独立 Ending；dispatcher 只作公开诊断。"),
    ],
    "workflow-skill": [
        ("锁定路线执行", "只执行 pair、依赖、allowlist 与 receipt 都准确的已准入计划。"),
        ("单 Producer 默认", "依赖耦合工作和小型独立 source 都使用一个上下文 producer。"),
        ("结果优先交接", "Producer 完成一次 Quick Check、展示结果，再创建全局 projectless End Task，并确认 list_threads 返回 projectId=null/无字段。"),
        ("Ending 可见性", "PASS、FAIL、BLOCKED 都保持可见；Ending task 与修复交接永不自动归档或删除。"),
        ("运行证明", "每个模型节点都公开实际 effective pair 和 token/time receipt。"),
    ],
    "prompt-skill": [
        ("全局 100% Prompt 入口", "所有可复用 prompt 或持久 AI 指令的创建、审查、修改、修复、标准化、测试、总结与优化都加载 Prompt。"),
        ("普通文案排除", "请求只是文字不触发；目标本身必须是可复用 prompt 或持久 AI 指令。"),
        ("条件化控制", "角色、工具、自主性、reasoning、verbosity、分隔符和示例只在确实改善行为时使用。"),
        ("无冲突契约", "明确目标、输入、要求、输出、成功/失败与验证，不要求展示思维链。"),
        ("结果优先测试", "先展示完成 prompt；代表性 trial 与证据检查之后在 Ending 运行。"),
    ],
    "code-skill": [
        ("Prompt-in-code 集成", "先加载 Prompt，再应用 Python、C# 或 Unity C# 的可执行字符串、格式和 ownership 规则。"),
        ("Karpathy Coding Guidelines", "使用明确假设、简单设计、清晰命名、浅分支和精确修改。"),
        ("成比例 Quick Check", "轻量本地工作跑最小 smoke；重型/API/大文件/副作用工作检查语法、名称、import 和引用。"),
        ("自适应执行", "普通代码工作使用任务策略质量档；Spark 只用于成本准入的独立 source 分支。"),
        ("结果所有权", "一个 producer 负责修改、Quick Check、receipt 与完成结果。"),
    ],
    "project-memory-skill": [
        ("工作线回溯", "修改前按项目、模块、文件、symbol、branch 和 version 回溯历史。"),
        ("验证后记录", "只在结果完成并验证后记录最终修改。"),
        ("私有权威", "本地 JSONL 为权威，可选投影到 Obsidian；公共镜像不包含私人记录。"),
    ],
    "optimization-skill": [
        ("Skill Optimization", "把明确、重复或明显可复用流程优化为本地脚本、reference、asset、prompt 或 template。"),
        ("保持行为", "删除确定性浪费，不弱化正确性，也不改变用户可见契约。"),
        ("证据分离", "Optimizer 先展示完成结果，再由不同 Ending session 检查不可变证据。"),
        ("Reference 抽取", "把长且稳定的说明移到 references，仅在需要时加载。"),
        ("Assets 与模板", "属于优化 skill 的可复用 fixture、template 或媒体放入 assets。"),
    ],
    "verify-skill": [
        ("成比例完成证据", "Producer 在展示前负责边界明确的 Quick Check。"),
        ("持久 End Task", "创建并准确命名全局 projectless End Task-<相关任务>，确认 list_threads 返回 projectId=null/无字段；所有终态都保持可见。"),
        ("固定快速执行器", "所有 Ending 首选 Spark-xhigh；分数只控制检查，只有明确不可用时才回退 registry-floor Luna-low。"),
        ("真实检查边界", "最小真实检查只执行一次；失败 verifier 记录证据并把修复退回不可变 origin。"),
        ("终局判定", "一次可见终局完成路由分类、适用的项目结果记忆与有界偏好扫描。"),
    ],
    "management-skill": [
        ("Codex Switch", "管理本地 Codex auth profile 与确认后的账号切换。"),
        ("消费者替换安装", "消费者安装或更新浅克隆已发布源，只做机械安全替换八个受管 Skill 和两个 global AGENTS；维护者 push 在发布前只运行一次完整门禁。"),
        ("GitHub Sync", "对两个镜像运行 preuse、公开安全扫描、sync、push 和远端 hash 校验。"),
        ("隐私安全", "auth、token、cookie、原始 prompt/result、receipt、log、cache 与私人学习保持本地。"),
    ],
}


def run_command(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def lexical_absolute_path(path):
    expanded_path = Path(path).expanduser()
    return Path(os.path.abspath(expanded_path))


def run_release_gate(source_dir, skills_dir, mode):
    source_dir = Path(source_dir).expanduser().resolve()
    skills_dir = Path(skills_dir).expanduser().resolve()
    gate_path = skills_dir / "management-skill" / "scripts" / "global_skill_regression_gate.py" if mode == "deployed" else source_dir / "management-skill" / "scripts" / "global_skill_regression_gate.py"
    if not gate_path.is_file():
        raise RuntimeError(f"Retained-capability validation is unavailable after installation: {gate_path}")
    command = [
        sys.executable,
        str(gate_path),
        "check",
        "--project-root",
        str(source_dir),
        "--skills-dir",
        str(skills_dir),
        "--mode",
        mode,
    ]
    completed = subprocess.run(command, cwd=source_dir, text=True, capture_output=True, check=False, timeout=3600)
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or "no gate output"
        raise RuntimeError(f"Refusing release because the retained-capability regression gate failed in {mode} mode:\n{details}")
    return completed


@contextmanager
def temporary_workspace(prefix):
    cache_root = Path(os.environ.get("CODEX_PROJECT_CACHE_ROOT", DEFAULT_CACHE_ROOT)).expanduser()
    cache_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=prefix, dir=cache_root) as workspace:
        yield Path(workspace)


def repository_git_url(repository, read_only=False):
    if repository.startswith(("git@", "ssh://", "https://")):
        return repository
    if shutil.which("gh"):
        url_field = "url" if read_only else "sshUrl"
        try:
            resolved_url = run_command(["gh", "repo", "view", repository, "--json", url_field, "--jq", f".{url_field}"]).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            resolved_url = ""
        if resolved_url:
            return resolved_url
    return f"https://github.com/{repository}.git" if read_only else f"git@github.com:{repository}.git"


def clone_repository(repository, sandbox, read_only=False):
    repository_dir = sandbox / "repo"
    run_command(["git", "clone", "--depth", "1", repository_git_url(repository, read_only=read_only), str(repository_dir)])
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
        spark = "source-eligible" if row["spark_first"] else "no"
        lines.append(f"- `{row['id']}` · {row['kind']} · `{row['owner_skill']}` · {state} · Spark schedule: {spark} · [rules](./{row['reference_path']})")
    return "\n".join(lines)


def build_readme(skill_paths, language="en"):
    template_path = CHINESE_README_TEMPLATE if language == "zh" else ENGLISH_README_TEMPLATE
    template = template_path.read_text(encoding="utf-8").rstrip() + "\n"
    marker = "<!-- EXECUTION_DOMAIN_TABLE -->"
    if template.count(marker) != 1:
        raise RuntimeError(f"{template_path.name} must contain exactly one execution-domain marker")
    return template.replace(marker, execution_domain_table(load_staged_routing_policy(skill_paths)))


def readme_language_for_output(output_path):
    return "zh" if Path(output_path).name.lower().endswith(".zh.md") else "en"


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
        return [
            "## Main Goal 和 Ending Task",
            "",
            "合格普通生产任务由紧凑 bootstrap 选择上下文质量档并执行；小型多 source 使用单 producer，只有成本或显式 latency 准入才运行 graph。",
            "",
            "```mermaid",
            "flowchart TD",
            '  A["用户请求"] --> B["任务策略质量档"]',
            '  B --> C["自适应 Producer 或成本准入 Graph"]',
            '  C --> Q["成比例 Quick Check"]',
            '  Q --> R["立即展示完成结果"]',
            '  R --> E["新建 End Task"]',
            '  E --> V["只读 Ending 证据审计"]',
            "```",
            "",
            "- **主任务：** 一个 producer 负责结果与 Quick Check；dependency-coupled 多文件绝不强制 fan-out。",
            "- **主结果：** 完成后立即展示；first-result 时间到此停止。",
            "- **Ending：** 新的持久任务只读检查不可变证据；origin 不等待、不轮询、不修复。",
            "- **Workflow：** 只执行已通过成本/性能准入的锁定 graph。",
            "",
        ]
    return [
        "## Main Goal And Ending Task",
        "",
        "Eligible ordinary production uses the compact bootstrap to select and execute a contextual quality pair. Small multi-source work stays with one producer; only cost or explicit latency admission opens a graph.",
        "",
        "```mermaid",
        "flowchart TD",
        '  A["User request"] --> B["Task-strategy quality pair"]',
        '  B --> C["Adaptive producer or cost-admitted graph"]',
        '  C --> Q["Proportional Quick Check"]',
        '  Q --> R["Present completed result immediately"]',
        '  R --> E["Create new End Task"]',
        '  E --> V["Read-only Ending evidence audit"]',
        "```",
        "",
        "- **Main task:** one producer owns result work and Quick Check; dependency-coupled files never force fan-out.",
        "- **Main result:** present it immediately when complete; first-result time stops there.",
        "- **Ending:** a new persistent task audits immutable evidence; the origin never waits, polls, or repairs.",
        "- **Workflow:** executes only a cost/performance-admitted locked graph.",
        "",
    ]



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


def copy_skill_directory(source_dir, target_dir, preserve_local=False):
    assert_no_symlinks([source_dir], "source skill tree")
    if target_dir.exists() or target_dir.is_symlink():
        assert_no_symlinks([target_dir], "target skill tree")
    local_source = target_dir / "local"
    if preserve_local and local_source.exists():
        assert_no_symlinks([local_source], "preserved local content")
        with temporary_workspace("qin-codex-private-local-") as sandbox:
            preserved_local = sandbox / "local"
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
    with temporary_workspace("qin-codex-skills-diff-") as sandbox:
        copy_skill_directory(source_dir, sandbox / "source")
        copy_skill_directory(target_dir, sandbox / "target")
        return subprocess.run(["git", "diff", "--no-index", "--quiet", str(sandbox / "source"), str(sandbox / "target")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0


def canonical_global_agents_text(source_dir):
    asset_path = Path(source_dir).expanduser().resolve() / GLOBAL_AGENTS_ASSET
    if not asset_path.is_file():
        raise RuntimeError(f"global AGENTS entry asset is missing: {asset_path}")
    text = asset_path.read_text(encoding="utf-8")
    if not text.startswith(GLOBAL_AGENTS_DIRECTIVE):
        raise RuntimeError("global AGENTS entry asset is missing its merge directive")
    rendered = text[len(GLOBAL_AGENTS_DIRECTIVE):]
    if not rendered.startswith("# Task Lifecycle\n"):
        raise RuntimeError("global AGENTS entry asset does not render the Task Lifecycle contract")
    return rendered


def materialized_global_agents_text(source_dir):
    asset_path = Path(source_dir).expanduser().resolve() / GLOBAL_AGENTS_ASSET
    if not asset_path.is_file():
        raise RuntimeError(f"global AGENTS entry bytes are unavailable: {asset_path}")
    text = asset_path.read_text(encoding="utf-8")
    return text[len(GLOBAL_AGENTS_DIRECTIVE):] if text.startswith(GLOBAL_AGENTS_DIRECTIVE) else text


def global_agents_targets(skills_dir):
    """Return the documented Codex global-instructions target for this Skill root."""
    skills_root = lexical_absolute_path(skills_dir)
    return [skills_root.parent / "AGENTS.md"]


def legacy_global_agents_targets(skills_dir):
    """Return targets written by installer manifests created before schema version 2."""
    skills_root = lexical_absolute_path(skills_dir)
    codex_root = skills_root.parent
    targets = [codex_root / "AGENTS.md"]
    if codex_root.name == ".codex":
        targets.append(codex_root.parent / "AGENTS.md")
    return targets


def global_agents_backup_root(skills_dir):
    return lexical_absolute_path(skills_dir).parent / GLOBAL_AGENTS_BACKUP_DIRECTORY


def global_agents_target_matches(target, expected_text):
    if not os.path.lexists(target) or target.is_symlink() or not stat.S_ISREG(target.lstat().st_mode):
        return False
    return target.read_text(encoding="utf-8") == expected_text


def create_global_agents_backup(skills_dir, target):
    backup_root = global_agents_backup_root(skills_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = Path(tempfile.mkdtemp(prefix="agents-", dir=backup_root))
    target_existed = os.path.lexists(target)
    manifest = {"schema_version": 1, "target": str(target), "target_existed": target_existed, "state": "prepared", "created_at": time.time(), "previous_entry": "previous"}
    write_atomic_json(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST, manifest)
    return backup_dir, manifest


def load_global_agents_backup(skills_dir, backup_id):
    if not re.fullmatch(r"agents-[A-Za-z0-9._-]+", backup_id):
        raise RuntimeError("The global AGENTS backup ID is invalid.")
    backup_dir = global_agents_backup_root(skills_dir) / backup_id
    if not real_directory_entry(backup_dir):
        raise RuntimeError("The requested global AGENTS backup is unavailable or unsafe.")
    manifest = read_json_if_available(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST)
    target = global_agents_targets(skills_dir)[0]
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("target") != str(target) or not isinstance(manifest.get("target_existed"), bool) or manifest.get("previous_entry") != "previous":
        raise RuntimeError("The requested global AGENTS backup manifest does not match this Skill root.")
    return backup_dir, manifest, target


def _write_global_agents_target(target, rendered):
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".AGENTS.md.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def install_global_agents(source_dir, skills_dir):
    source_dir = Path(source_dir).expanduser().resolve()
    skills_dir = lexical_absolute_path(skills_dir)
    expected_text = canonical_global_agents_text(source_dir)
    target = global_agents_targets(skills_dir)[0]
    with installation_lock(skills_dir):
        if global_agents_target_matches(target, expected_text):
            return {"changed": False, "backup_id": None, "target": target}
        backup_dir, manifest = create_global_agents_backup(skills_dir, target)
        previous_entry = backup_dir / manifest["previous_entry"]
        try:
            if manifest["target_existed"]:
                replace_path_entry(target, previous_entry)
            _write_global_agents_target(target, expected_text)
            manifest["state"] = "installed"
            manifest["installed_at"] = time.time()
            write_atomic_json(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST, manifest)
        except Exception as install_error:
            try:
                failed_entry = backup_dir / "failed-install"
                if os.path.lexists(target):
                    replace_path_entry(target, failed_entry)
                if manifest["target_existed"] and os.path.lexists(previous_entry):
                    replace_path_entry(previous_entry, target)
                manifest["state"] = "restored"
                manifest["restored_at"] = time.time()
                write_atomic_json(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST, manifest)
            except Exception as restore_error:
                raise RuntimeError(f"Global AGENTS installation failed and its persistent backup could not be restored: {restore_error}") from install_error
            raise RuntimeError("Global AGENTS installation failed; the previous target was restored from its persistent backup.") from install_error
    return {"changed": True, "backup_id": backup_dir.name, "target": target}


def restore_global_agents_backup(skills_dir, backup_id):
    skills_dir = lexical_absolute_path(skills_dir)
    with installation_lock(skills_dir):
        backup_dir, manifest, target = load_global_agents_backup(skills_dir, backup_id)
        if manifest.get("state") == "restored":
            return {"changed": False, "backup_id": backup_id, "target": target}
        if manifest.get("state") != "installed":
            raise RuntimeError("The requested global AGENTS backup is not in a restorable installed state.")
        previous_entry = backup_dir / manifest["previous_entry"]
        if manifest["target_existed"] and not os.path.lexists(previous_entry):
            raise RuntimeError("The requested global AGENTS backup is missing its preserved original target.")
        replaced_entry = backup_dir / "replaced-on-restore"
        if os.path.lexists(replaced_entry):
            raise RuntimeError("The requested global AGENTS backup already contains a replacement from a prior restore attempt.")
        try:
            if os.path.lexists(target):
                replace_path_entry(target, replaced_entry)
            if manifest["target_existed"]:
                replace_path_entry(previous_entry, target)
            manifest["state"] = "restored"
            manifest["restored_at"] = time.time()
            write_atomic_json(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST, manifest)
        except Exception as restore_error:
            raise RuntimeError(f"Global AGENTS restore failed; the persistent backup remains available: {restore_error}") from restore_error
    return {"changed": True, "backup_id": backup_id, "target": target}


def list_global_agents_backups(skills_dir):
    backup_root = global_agents_backup_root(skills_dir)
    if not backup_root.is_dir():
        return []
    backups = []
    for backup_dir in sorted(backup_root.iterdir(), key=lambda path: path.name):
        if not real_directory_entry(backup_dir):
            continue
        manifest = read_json_if_available(backup_dir / GLOBAL_AGENTS_BACKUP_MANIFEST)
        if isinstance(manifest, dict):
            backups.append({"id": backup_dir.name, "state": manifest.get("state", "invalid"), "target_existed": manifest.get("target_existed")})
    return backups


def bridge_user_skills(skills_dir, user_skills_dir=OFFICIAL_USER_SKILLS_DIRECTORY, apply=False):
    skills_dir = lexical_absolute_path(skills_dir)
    user_skills_dir = lexical_absolute_path(user_skills_dir)
    missing = [name for name in PRIMARY_SKILL_ORDER if not real_directory_entry(skills_dir / name)]
    if missing:
        raise RuntimeError(f"The legacy Skill root is missing managed Skills: {', '.join(missing)}")
    planned = []
    existing = []
    conflicts = []
    for name in PRIMARY_SKILL_ORDER:
        source = skills_dir / name
        target = user_skills_dir / name
        if not os.path.lexists(target):
            planned.append(name)
        elif target.is_symlink() and target.resolve() == source.resolve():
            existing.append(name)
        else:
            conflicts.append(name)
    if conflicts:
        raise RuntimeError(f"Refusing to replace existing official user Skills: {', '.join(conflicts)}")
    if apply:
        user_skills_dir.mkdir(parents=True, exist_ok=True)
        for name in planned:
            os.symlink(skills_dir / name, user_skills_dir / name, target_is_directory=True)
    return {"applied": apply, "legacy_root": skills_dir, "user_root": user_skills_dir, "planned": planned, "existing": existing}


def deploy_global_agents(source_dir, skills_dir):
    return install_global_agents(source_dir, skills_dir)["changed"]


def global_agents_parity(source_dir, skills_dir):
    expected = canonical_global_agents_text(source_dir)
    targets = global_agents_targets(skills_dir)
    missing = [str(target) for target in targets if not target.is_file()]
    different = [str(target) for target in targets if target.is_file() and target.read_text(encoding="utf-8") != expected]
    target = targets[0]
    if missing:
        reason = f"global AGENTS.md is missing: {', '.join(missing)}"
    elif different:
        reason = f"global AGENTS.md differs from the installed Task Lifecycle asset: {', '.join(different)}"
    else:
        reason = None
    return {
        "status": "pass" if not missing and not different else "fail",
        "target": str(target),
        "targets": [str(target) for target in targets],
        "reason": reason,
    }


def print_lines(title, lines):
    print(title)
    for line in lines:
        print(f"- {line}")


def real_directory_entry(path):
    if not os.path.lexists(path):
        return False
    path_status = Path(path).lstat()
    reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(path_status, "st_file_attributes", 0)
    return stat.S_ISDIR(path_status.st_mode) and not file_attributes & reparse_point


def replace_path_entry(source, target):
    source = Path(source)
    target = Path(target)
    transient_windows_errors = {5, 32, 33}
    for attempt in range(5):
        try:
            os.replace(source, target)
            return
        except OSError as error:
            retryable = os.name == "nt" and getattr(error, "winerror", None) in transient_windows_errors and attempt < 4
            if not retryable:
                raise
            time.sleep(0.05 * (2 ** attempt))


def write_atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def read_json_if_available(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def process_is_running(process_id):
    if not isinstance(process_id, int) or process_id <= 0:
        return False
    if process_id == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        process_handle = kernel.OpenProcess(0x1000, False, process_id)
        if process_handle:
            kernel.CloseHandle(process_handle)
            return True
        return ctypes.get_last_error() == 5
    try:
        os.kill(process_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def try_create_installation_lock(lock_dir, token):
    try:
        lock_dir.mkdir()
    except FileExistsError:
        return False
    write_atomic_json(lock_dir / "owner.json", {"pid": os.getpid(), "token": token, "created_at": time.time()})
    return True


def clear_stale_installation_lock(lock_dir):
    try:
        if not os.path.lexists(lock_dir):
            return True
        if not real_directory_entry(lock_dir):
            raise RuntimeError("The global Skill installation lock is not a safe real directory.")
        owner = read_json_if_available(lock_dir / "owner.json")
        if owner and process_is_running(owner.get("pid")):
            return False
        if owner is None and time.time() - lock_dir.stat().st_mtime < 1.0:
            return False
        shutil.rmtree(lock_dir)
        return True
    except FileNotFoundError:
        return True


def release_installation_lock(lock_dir, token):
    owner = read_json_if_available(lock_dir / "owner.json")
    if owner and owner.get("token") == token and real_directory_entry(lock_dir):
        shutil.rmtree(lock_dir)


@contextmanager
def installation_lock(skills_dir, timeout_seconds=30.0):
    lock_dir = lexical_absolute_path(skills_dir).parent / INSTALL_LOCK_NAME
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    token = f"{os.getpid()}-{time.time_ns()}"
    deadline = time.monotonic() + timeout_seconds
    while not try_create_installation_lock(lock_dir, token):
        if clear_stale_installation_lock(lock_dir):
            continue
        if time.monotonic() >= deadline:
            raise RuntimeError("Another global Skill installation is still active; the safe target lock did not become available.")
        time.sleep(0.1)
    try:
        yield
    finally:
        release_installation_lock(lock_dir, token)


def cleanup_installation_workspace(transaction_root):
    try:
        shutil.rmtree(transaction_root)
    except OSError as error:
        print(f"Disposable installation workspace cleanup will be retried later ({error.__class__.__name__}).")


def create_installation_workspace(skills_dir):
    skills_parent = Path(skills_dir).parent
    skills_parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=INSTALL_TRANSACTION_PREFIX, dir=skills_parent))


def install_source_symlink_issues(source_dir):
    source_dir = Path(source_dir)
    if not real_directory_entry(source_dir):
        return [source_dir]
    issues = []
    pending = [source_dir]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.name in ignored_names(directory, {entry.name}):
                    continue
                path = directory / entry.name
                entry_status = entry.stat(follow_symlinks=False)
                reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                file_attributes = getattr(entry_status, "st_file_attributes", 0)
                if entry.is_symlink() or file_attributes & reparse_point:
                    issues.append(path)
                elif entry.is_dir(follow_symlinks=False):
                    pending.append(path)
    return sorted(issues, key=lambda path: path.as_posix())


def stage_skill_directory(source_dir, target_dir):
    issues = install_source_symlink_issues(source_dir)
    if issues:
        details = "\n".join(f"- {path}" for path in issues)
        raise RuntimeError(f"Managed source bytes cannot be materialized without following a symlink or junction:\n{details}")
    shutil.copytree(source_dir, target_dir, ignore=ignored_names)


def stage_installation_bundle(source_dir, skills_dir, transaction_root):
    skill_paths = skill_directories(source_dir)
    assert_approved_global_skill_set(skill_paths)
    staged_skill_dir = transaction_root / "staged-skills"
    staged_skill_paths = []
    for source_path in skill_paths:
        staged_path = staged_skill_dir / source_path.name
        stage_skill_directory(source_path, staged_path)
        staged_skill_paths.append(staged_path)
    return {"skill_paths": staged_skill_paths, "agent_paths": []}


def new_deployment_snapshot(skills_dir, transaction_root, bundle):
    skills_dir = Path(skills_dir)
    skills_dir_existed = os.path.lexists(skills_dir)
    if skills_dir_existed and not real_directory_entry(skills_dir):
        raise RuntimeError("The global Skill root cannot be replaced safely because it is not a real directory.")
    skills_dir.mkdir(parents=True, exist_ok=True)
    records = []
    targets = [("skill", skills_dir / path.name, path) for path in bundle["skill_paths"]]
    targets.extend(("agents", target, staged_path) for target, staged_path in zip(global_agents_targets(skills_dir), bundle["agent_paths"]))
    for index, (kind, target, staged_path) in enumerate(targets):
        records.append({"kind": kind, "target": target, "staged": staged_path, "backup": transaction_root / "previous" / f"{index:02d}", "existed": os.path.lexists(target), "captured": False, "installed": False})
    task_record = next(record for record in records if record["kind"] == "skill" and record["target"].name == "task-analyze-skill")
    private_local_existed = real_directory_entry(task_record["target"]) and os.path.lexists(task_record["target"] / "local")
    private_local = {"backup": task_record["backup"] / "local", "installed": task_record["target"] / "local", "existed": private_local_existed, "moved": False, "task_staged": task_record["staged"]}
    return {"skills_dir": skills_dir, "skills_dir_existed": skills_dir_existed, "records": records, "transaction_root": transaction_root, "private_local": private_local, "global_agents_included": bool(bundle["agent_paths"])}


def installation_manifest_payload(snapshot, state):
    return {
        "schema_version": 2,
        "state": state,
        "pid": os.getpid(),
        "skills_dir": str(snapshot["skills_dir"]),
        "skills_dir_existed": snapshot["skills_dir_existed"],
        "global_agents_included": snapshot["global_agents_included"],
        "records": [{"kind": record["kind"], "target": str(record["target"]), "staged": str(record["staged"]), "backup": str(record["backup"]), "existed": record["existed"]} for record in snapshot["records"]],
        "private_local": {"backup": str(snapshot["private_local"]["backup"]), "installed": str(snapshot["private_local"]["installed"]), "task_staged": str(snapshot["private_local"]["task_staged"]), "existed": snapshot["private_local"]["existed"]},
        "updated_at": time.time(),
    }


def write_installation_manifest(snapshot, state):
    write_atomic_json(snapshot["transaction_root"] / INSTALL_MANIFEST_NAME, installation_manifest_payload(snapshot, state))


def validate_manifest_record(payload_record, expected_kind, expected_target, expected_staged, expected_backup):
    expected = {"kind": expected_kind, "target": str(expected_target), "staged": str(expected_staged), "backup": str(expected_backup)}
    if not isinstance(payload_record, dict) or any(payload_record.get(key) != value for key, value in expected.items()) or not isinstance(payload_record.get("existed"), bool):
        raise RuntimeError("An interrupted global Skill installation manifest contains unsafe target data.")


def snapshot_from_installation_manifest(transaction_root, payload, skills_dir):
    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2} or payload.get("skills_dir") != str(skills_dir):
        raise RuntimeError("An interrupted global Skill installation manifest does not match the requested target.")
    payload_records = payload.get("records")
    expected_targets = [("skill", skills_dir / name, transaction_root / "staged-skills" / name) for name in PRIMARY_SKILL_ORDER]
    if schema_version == 1:
        agent_targets = legacy_global_agents_targets(skills_dir)
    elif payload.get("global_agents_included") is True:
        agent_targets = global_agents_targets(skills_dir)
    else:
        agent_targets = []
    expected_targets.extend(("agents", target, transaction_root / "staged-agents" / f"{index}.md") for index, target in enumerate(agent_targets))
    if not isinstance(payload_records, list) or len(payload_records) != len(expected_targets):
        raise RuntimeError("An interrupted global Skill installation manifest has an incomplete managed target set.")
    records = []
    for index, ((kind, target, staged), payload_record) in enumerate(zip(expected_targets, payload_records)):
        backup = transaction_root / "previous" / f"{index:02d}"
        validate_manifest_record(payload_record, kind, target, staged, backup)
        reverse_index = len(expected_targets) - 1 - index
        restore_marker = transaction_root / "restore-markers" / f"{reverse_index:02d}.json"
        restored = payload_record["existed"] and not os.path.lexists(backup) and os.path.lexists(restore_marker) and os.path.lexists(target)
        record = {"kind": kind, "target": target, "staged": staged, "backup": backup, "existed": payload_record["existed"], "captured": os.path.lexists(backup), "installed": not os.path.lexists(staged) and not restored}
        if record["existed"] and not os.path.lexists(staged) and not record["captured"] and not restored:
            raise RuntimeError("An interrupted global Skill installation is missing a required recovery backup.")
        records.append(record)
    task_record = next(record for record in records if record["kind"] == "skill" and record["target"].name == "task-analyze-skill")
    private_payload = payload.get("private_local", {})
    expected_private = {"backup": str(task_record["backup"] / "local"), "installed": str(task_record["target"] / "local"), "task_staged": str(task_record["staged"])}
    if any(private_payload.get(key) != value for key, value in expected_private.items()) or not isinstance(private_payload.get("existed"), bool):
        raise RuntimeError("An interrupted global Skill installation manifest has unsafe private-local data.")
    private_moved = private_payload["existed"] and not os.path.lexists(task_record["staged"]) and not os.path.lexists(task_record["backup"] / "local") and os.path.lexists(task_record["target"] / "local")
    private_local = {"backup": task_record["backup"] / "local", "installed": task_record["target"] / "local", "task_staged": task_record["staged"], "existed": private_payload["existed"], "moved": private_moved}
    return {"skills_dir": skills_dir, "skills_dir_existed": payload.get("skills_dir_existed") is True, "records": records, "transaction_root": transaction_root, "private_local": private_local, "global_agents_included": bool(agent_targets)}


def capture_deployment_snapshot(snapshot):
    for record in snapshot["records"]:
        if not os.path.lexists(record["target"]):
            continue
        record["backup"].parent.mkdir(parents=True, exist_ok=True)
        replace_path_entry(record["target"], record["backup"])
        record["captured"] = True


def preserve_private_task_analyze_local(snapshot):
    task_record = next(record for record in snapshot["records"] if record["kind"] == "skill" and record["target"].name == "task-analyze-skill")
    private_local = snapshot["private_local"]
    if not private_local["existed"] or not task_record["captured"] or not real_directory_entry(task_record["backup"]):
        return
    backup_local = private_local["backup"]
    installed_local = private_local["installed"]
    if not os.path.lexists(backup_local):
        return
    if os.path.lexists(installed_local):
        raise RuntimeError("The provisional task-analyze-skill unexpectedly contains local state.")
    replace_path_entry(backup_local, installed_local)
    private_local["moved"] = True


def install_managed_skills(snapshot):
    installed_names = []
    installed_agents = 0
    for record in snapshot["records"]:
        record["target"].parent.mkdir(parents=True, exist_ok=True)
        replace_path_entry(record["staged"], record["target"])
        record["installed"] = True
        if record["kind"] == "skill":
            installed_names.append(record["target"].name)
        else:
            installed_agents += 1
    preserve_private_task_analyze_local(snapshot)
    write_installation_manifest(snapshot, "active")
    return installed_names, installed_agents


def restore_captured_record(record, discard_path, restore_marker):
    write_atomic_json(restore_marker, {"target": str(record["target"]), "started_at": time.time()})
    provisional_moved = False
    if record["installed"] and os.path.lexists(record["target"]):
        discard_path.parent.mkdir(parents=True, exist_ok=True)
        replace_path_entry(record["target"], discard_path)
        provisional_moved = True
    try:
        record["target"].parent.mkdir(parents=True, exist_ok=True)
        replace_path_entry(record["backup"], record["target"])
    except Exception:
        if provisional_moved and os.path.lexists(discard_path) and not os.path.lexists(record["target"]):
            replace_path_entry(discard_path, record["target"])
        raise
    record["captured"] = False
    record["installed"] = False


def discard_new_record(record, discard_path):
    if record["installed"] and os.path.lexists(record["target"]):
        discard_path.parent.mkdir(parents=True, exist_ok=True)
        replace_path_entry(record["target"], discard_path)
    record["installed"] = False


def restore_deployment_snapshot(snapshot):
    private_local = snapshot["private_local"]
    if private_local["moved"]:
        if not os.path.lexists(private_local["installed"]):
            raise RuntimeError("Preserved task-analyze-skill local state is unavailable during restore.")
        replace_path_entry(private_local["installed"], private_local["backup"])
        private_local["moved"] = False
    discard_dir = snapshot["transaction_root"] / "discard"
    for index, record in enumerate(reversed(snapshot["records"])):
        if record["captured"]:
            restore_captured_record(record, discard_dir / f"captured-{index:02d}", snapshot["transaction_root"] / "restore-markers" / f"{index:02d}.json")
    for index, record in enumerate(reversed(snapshot["records"])):
        if not record["captured"] and not record["existed"]:
            discard_new_record(record, discard_dir / f"new-{index:02d}")
    skills_dir = snapshot["skills_dir"]
    if not snapshot["skills_dir_existed"] and real_directory_entry(skills_dir) and not any(skills_dir.iterdir()):
        skills_dir.rmdir()


def restore_installation_or_raise(snapshot, installation_error):
    try:
        restore_deployment_snapshot(snapshot)
        write_installation_manifest(snapshot, "restored")
    except Exception as restore_error:
        raise RuntimeError(f"Provisional installation failed and automatic restore also failed; the recovery snapshot was retained. Failure: {restore_error}") from installation_error


def recover_interrupted_installations(skills_dir):
    skills_dir = lexical_absolute_path(skills_dir)
    skills_parent = skills_dir.parent
    if not skills_parent.is_dir():
        return
    for transaction_root in sorted(skills_parent.glob(f"{INSTALL_TRANSACTION_PREFIX}*")):
        if not real_directory_entry(transaction_root):
            raise RuntimeError("An installer-owned recovery entry is not a safe real directory.")
        payload = read_json_if_available(transaction_root / INSTALL_MANIFEST_NAME)
        if payload is None or payload.get("skills_dir") != str(skills_dir):
            continue
        state = payload.get("state")
        if state in {"materializing", "committed", "restored"}:
            cleanup_installation_workspace(transaction_root)
            continue
        if state not in {"prepared", "active"}:
            raise RuntimeError("An interrupted global Skill installation has an unknown recovery state.")
        snapshot = snapshot_from_installation_manifest(transaction_root, payload, skills_dir)
        restore_deployment_snapshot(snapshot)
        write_installation_manifest(snapshot, "restored")
        cleanup_installation_workspace(transaction_root)


@contextmanager
def provisional_installation_transaction(source_dir, skills_dir):
    with installation_lock(skills_dir):
        recover_interrupted_installations(skills_dir)
        transaction_root = create_installation_workspace(skills_dir)
        snapshot = None
        bundle_prepared = False
        try:
            write_atomic_json(transaction_root / INSTALL_MANIFEST_NAME, {"schema_version": 2, "state": "materializing", "pid": os.getpid(), "skills_dir": str(skills_dir), "global_agents_included": False, "updated_at": time.time()})
            bundle = stage_installation_bundle(source_dir, skills_dir, transaction_root)
            bundle_prepared = True
            snapshot = new_deployment_snapshot(skills_dir, transaction_root, bundle)
            write_installation_manifest(snapshot, "prepared")
            capture_deployment_snapshot(snapshot)
            yield snapshot
            write_installation_manifest(snapshot, "committed")
        except Exception as installation_error:
            captured_count = sum(record["captured"] for record in snapshot["records"]) if snapshot is not None else 0
            installed_count = sum(record["installed"] for record in snapshot["records"]) if snapshot is not None else 0
            if snapshot is not None:
                restore_installation_or_raise(snapshot, installation_error)
            cleanup_installation_workspace(transaction_root)
            if not bundle_prepared:
                raise RuntimeError(f"Installation source bytes could not be materialized safely before replacement. Codex must repair the source and retry automatically. Failure: {installation_error}") from installation_error
            if snapshot is None:
                raise RuntimeError(f"A recoverable backup or safe exact-target write could not be prepared; no managed target was replaced. Codex must resolve the mechanical blocker and retry automatically. Failure: {installation_error}") from installation_error
            raise RuntimeError(f"The provisional transaction failed after capturing {captured_count} target(s) and replacing {installed_count} target(s); the previous installation was restored. Codex must repair the maintained source and reinstall without asking the user to run a gate. Failure: {installation_error}") from installation_error
        cleanup_installation_workspace(transaction_root)


def mirror_repository_to_local(repository_dir, skills_dir):
    return deploy(repository_dir, skills_dir)


def deploy(source_dir, skills_dir):
    source_dir = Path(source_dir).expanduser().resolve()
    skills_dir = lexical_absolute_path(skills_dir)
    with provisional_installation_transaction(source_dir, skills_dir) as snapshot:
        installed_names, installed_agents = install_managed_skills(snapshot)
        print_lines("Replaced managed repository Skills in the local global Skill directory:", installed_names)
        if installed_agents:
            print(f"Replaced {installed_agents} explicit global AGENTS.md target(s) with the repository Task Lifecycle contract.")
    print("Preserved user global AGENTS.md files; use install-global-agents for an explicit, recoverable template installation.")
    print("Installation complete: consumer install/update replaced the published managed source without rerunning validation gates.")
    return installed_names


def remote_changes(repository, skills_dir):
    with temporary_workspace("qin-codex-skills-") as sandbox:
        repository_dir = clone_repository(repository, sandbox, read_only=True)
        remote_by_name = {path.name: path for path in skill_directories(repository_dir)}
        return [name for name in PRIMARY_SKILL_ORDER if name not in remote_by_name or path_differs(remote_by_name[name], skills_dir / name)]


def preuse(repository, skills_dir):
    changed_names = remote_changes(repository, skills_dir)
    if changed_names:
        print_lines("Remote skills differ from local global skills:", changed_names)
        print("Run pull before using or editing these skills unless local edits must be preserved.")
    else:
        print("Remote global skills are already reflected locally.")


def record_pull_state(repository, repository_dir, skills_dir):
    try:
        write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), "", "")
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Installation complete; sync state could not be recorded ({error.__class__.__name__}).")
        return False
    return True


def pull(repository, skills_dir):
    with temporary_workspace("qin-codex-skills-") as sandbox:
        repository_dir = clone_repository(repository, sandbox, read_only=True)
        changed_names = mirror_repository_to_local(repository_dir, skills_dir)
        record_pull_state(repository, repository_dir, skills_dir)
        print_lines("Replaced managed remote skills in ~/.codex/skills:", changed_names)
        return changed_names


def prepare_repository_snapshot(repository_dir, skills_dir):
    assert_no_symlinks([repository_dir], "repository tree")
    skill_paths = skill_directories(skills_dir)
    assert_approved_global_skill_set(skill_paths)
    assert_no_symlinks(skill_paths, "approved source skill trees")
    load_staged_routing_policy(skill_paths)
    assert_public_safe(skill_paths)
    checker_module = load_skill_platform_checker(skills_dir)
    checker_module.assert_skill_platform_safe(skills_dir, Path(skills_dir) / "code-skill" / "assets" / "skill-platform-baseline.json", selected_skill_names=APPROVED_GLOBAL_SKILL_NAMES)
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
    for path in skill_paths:
        copy_skill_directory(path, repository_dir / path.name)
        copied_names.append(path.name)
    return copied_names


def push_global_snapshot(repository, skills_dir, message, dry_run):
    if not dry_run:
        raise RuntimeError("Installed global Skills are not a publication source. Publish the maintained repository with the push command.")
    with temporary_workspace("qin-codex-skills-") as sandbox:
        repository_dir = clone_repository(repository, sandbox, read_only=True)
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


def source_repository_root(source_dir):
    source_dir = Path(source_dir).expanduser().resolve()
    try:
        repository_root = Path(run_command(["git", "rev-parse", "--show-toplevel"], cwd=source_dir).stdout.strip()).resolve()
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Refusing to publish because the maintained source is not a Git repository: {source_dir}. "
            "Run push from the maintained repository or pass --source-dir explicitly."
        ) from error
    if repository_root != source_dir:
        raise RuntimeError(f"Refusing to publish a nested source path; expected repository root {repository_root}, got {source_dir}")
    return repository_root


def publishable_source_path(relative_path):
    relative_path = Path(relative_path)
    if relative_path.as_posix() in {"AGENTS.md", "README.md", "README.zh.md", ".github/workflows/ci.yml"}:
        return True
    if not relative_path.parts or relative_path.parts[0] not in APPROVED_GLOBAL_SKILL_NAMES:
        return False
    skill_relative = Path(*relative_path.parts[1:])
    if not skill_relative.parts:
        return True
    return (
        not any(part in EXCLUDED_PARTS for part in skill_relative.parts)
        and not skill_relative.name.endswith(EXCLUDED_SUFFIXES)
        and not sensitive_name(skill_relative)
    )


def staged_source_paths(source_dir):
    output = run_command(["git", "diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"], cwd=source_dir).stdout
    return [Path(line) for line in output.splitlines() if line.strip()]


def assert_publishable_staged_paths(source_dir):
    staged_paths = staged_source_paths(source_dir)
    refused = [path for path in staged_paths if not publishable_source_path(path)]
    if refused:
        details = "\n".join(f"- {path.as_posix()}" for path in refused)
        raise RuntimeError(f"Refusing to mix non-public or unrelated staged paths into the source publication:\n{details}")
    return staged_paths


def assert_publishable_worktree_paths(source_dir):
    output = run_command(["git", "status", "--porcelain", "--untracked-files=all"], cwd=source_dir).stdout
    paths = []
    for line in output.splitlines():
        if not line.strip():
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(Path(value.strip('"')))
    refused = [path for path in paths if not publishable_source_path(path)]
    if refused:
        details = "\n".join(f"- {path.as_posix()}" for path in refused)
        raise RuntimeError(f"Refusing publication while unrelated or non-public worktree paths are dirty:\n{details}")
    return paths


def render_source_readmes(source_dir, skill_paths, dry_run=False):
    expected = {
        source_dir / "README.md": build_readme(skill_paths, language="en"),
        source_dir / "README.zh.md": build_readme(skill_paths, language="zh"),
    }
    changed = []
    for path, rendered in expected.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
            changed.append(path.name)
            if not dry_run:
                path.write_text(rendered, encoding="utf-8")
    return changed


def remote_branch_head(source_dir, branch_name):
    output = run_command(["git", "ls-remote", "origin", f"refs/heads/{branch_name}"], cwd=source_dir).stdout.strip()
    return output.split()[0] if output else ""


def push(repository, source_dir, message, dry_run, skills_dir=None):
    source_dir = source_repository_root(source_dir)
    if not dry_run:
        run_release_gate(source_dir, skills_dir or Path.home() / ".codex" / "skills", "release")
    skill_paths = skill_directories(source_dir)
    readme_changes = render_source_readmes(source_dir, skill_paths, dry_run=dry_run)
    branch_name = run_command(["git", "branch", "--show-current"], cwd=source_dir).stdout.strip()
    if not branch_name:
        raise RuntimeError("Refusing to publish from a detached source HEAD")
    if dry_run:
        status_text = run_command(["git", "status", "--short", "--branch"], cwd=source_dir).stdout.strip()
        local_head = repository_head(source_dir)
        remote_head = remote_branch_head(source_dir, branch_name)
        print_lines("Repository source skills selected for publication:", [path.name for path in skill_paths])
        if readme_changes:
            print_lines("Generated README changes required:", readme_changes)
        print(status_text or "Source worktree is clean.")
        print(f"Source HEAD: {local_head}")
        print(f"Remote {branch_name}: {remote_head or 'missing'}")
        return
    if readme_changes:
        print_lines("Rendered source README files:", readme_changes)
    publication_paths = ["AGENTS.md", "README.md", "README.zh.md", *PRIMARY_SKILL_ORDER]
    if (source_dir / ".github" / "workflows" / "ci.yml").is_file():
        publication_paths.insert(3, ".github/workflows/ci.yml")
    run_command(["git", "add", "--", *publication_paths], cwd=source_dir)
    staged_paths = assert_publishable_staged_paths(source_dir)
    if staged_paths:
        run_command(["git", "commit", "-m", message], cwd=source_dir)
        print(f"Committed maintained source: {repository_head(source_dir)}")
    local_head = repository_head(source_dir)
    run_command(["git", "push", "origin", f"HEAD:{branch_name}"], cwd=source_dir)
    observed_remote_head = remote_branch_head(source_dir, branch_name)
    if observed_remote_head != local_head:
        raise RuntimeError(
            f"Remote verification failed after push: local {local_head}, remote {observed_remote_head or 'missing'}"
        )
    write_sync_state(DEFAULT_STATE_FILE, repository, local_head, snapshot_hash(skill_paths), snapshot_hash(skill_paths))
    remaining = run_command(["git", "status", "--porcelain", "--untracked-files=all"], cwd=source_dir).stdout.strip()
    if remaining:
        raise RuntimeError(f"Publication reached the remote but the maintained source worktree is not clean:\n{remaining}")
    print(f"Pushed maintained source {local_head} to {repository}:{branch_name} and verified the remote hash.")


def sync(repository, skills_dir, message):
    print("Legacy sync now performs an install-only remote replacement; GitHub publication remains an explicit push action.")
    return pull(repository, skills_dir)


def main():
    parser = argparse.ArgumentParser(description="Sync user global Codex skills with GitHub without putting .git in ~/.codex/skills.")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".codex" / "skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--message", default="Sync global Codex skills")
    subparsers.add_parser("preuse")
    pull_parser = subparsers.add_parser("pull")
    pull_parser.add_argument("--repo", dest="pull_repository", default=argparse.SUPPRESS)
    pull_parser.add_argument("--skills-dir", type=Path, dest="pull_skills_dir", default=argparse.SUPPRESS)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    status_parser.add_argument("--skills-dir", type=Path, dest="status_skills_dir", default=argparse.SUPPRESS)
    deploy_parser = subparsers.add_parser("deploy")
    deploy_parser.add_argument("--source-dir", type=Path, required=True)
    deploy_parser.add_argument("--skills-dir", type=Path, dest="deploy_skills_dir", default=argparse.SUPPRESS)
    install_agents_parser = subparsers.add_parser("install-global-agents")
    install_agents_parser.add_argument("--source-dir", type=Path, required=True)
    install_agents_parser.add_argument("--skills-dir", type=Path, dest="install_agents_skills_dir", default=argparse.SUPPRESS)
    restore_agents_parser = subparsers.add_parser("restore-global-agents")
    restore_agents_parser.add_argument("--backup-id", required=True)
    restore_agents_parser.add_argument("--skills-dir", type=Path, dest="restore_agents_skills_dir", default=argparse.SUPPRESS)
    list_agents_parser = subparsers.add_parser("list-global-agents-backups")
    list_agents_parser.add_argument("--skills-dir", type=Path, dest="list_agents_skills_dir", default=argparse.SUPPRESS)
    bridge_parser = subparsers.add_parser("bridge-user-skills")
    bridge_parser.add_argument("--skills-dir", type=Path, dest="bridge_skills_dir", default=argparse.SUPPRESS)
    bridge_parser.add_argument("--user-skills-dir", type=Path, default=OFFICIAL_USER_SKILLS_DIRECTORY)
    bridge_parser.add_argument("--apply", action="store_true")
    render_parser = subparsers.add_parser("render-readme")
    render_parser.add_argument("--output", type=Path, required=True)
    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    push_parser.add_argument("--message", default="Update global Codex skills")
    args = parser.parse_args()
    if args.command == "sync":
        sync(args.repo, args.skills_dir, args.message)
    elif args.command == "preuse":
        preuse(args.repo, args.skills_dir)
    elif args.command == "pull":
        pull(getattr(args, "pull_repository", args.repo), getattr(args, "pull_skills_dir", args.skills_dir))
    elif args.command == "status":
        status_skills_dir = getattr(args, "status_skills_dir", args.skills_dir)
        source_dir = args.source_dir.expanduser().resolve()
        deployment_differences = [
            name for name in PRIMARY_SKILL_ORDER
            if path_differs(source_dir / name, status_skills_dir.expanduser().resolve() / name)
        ]
        if deployment_differences:
            print_lines("Repository source differs from deployed global skills:", deployment_differences)
        else:
            print("Repository source skills match the deployed global skills.")
        print("User global AGENTS.md files are intentionally outside ordinary deployment parity.")
        push(args.repo, source_dir, "Update global Codex skills", True, status_skills_dir)
        if deployment_differences:
            raise SystemExit(1)
    elif args.command == "deploy":
        deploy(args.source_dir, getattr(args, "deploy_skills_dir", args.skills_dir))
    elif args.command == "install-global-agents":
        installation = install_global_agents(args.source_dir, getattr(args, "install_agents_skills_dir", args.skills_dir))
        if installation["changed"]:
            print(f"Installed the global AGENTS template at {installation['target']} with persistent backup {installation['backup_id']}.")
        else:
            print(f"Global AGENTS template already matches at {installation['target']}; no backup was created.")
    elif args.command == "restore-global-agents":
        restoration = restore_global_agents_backup(getattr(args, "restore_agents_skills_dir", args.skills_dir), args.backup_id)
        if restoration["changed"]:
            print(f"Restored global AGENTS from persistent backup {restoration['backup_id']} at {restoration['target']}.")
        else:
            print(f"Global AGENTS backup {restoration['backup_id']} was already restored.")
    elif args.command == "list-global-agents-backups":
        backups = list_global_agents_backups(getattr(args, "list_agents_skills_dir", args.skills_dir))
        print_lines("Persistent global AGENTS backups:", [f"{backup['id']} ({backup['state']})" for backup in backups] or ["none"])
    elif args.command == "bridge-user-skills":
        bridge = bridge_user_skills(getattr(args, "bridge_skills_dir", args.skills_dir), args.user_skills_dir, args.apply)
        action = "Created" if bridge["applied"] else "Planned"
        print_lines(f"{action} official user Skill links:", bridge["planned"] or ["none"])
        if bridge["existing"]:
            print_lines("Existing matching official user Skill links:", bridge["existing"])
        if not bridge["applied"]:
            print("No user Skill path was changed; rerun with --apply only after confirming the active Codex runtime needs the official user Skill path.")
    elif args.command == "render-readme":
        skill_paths = skill_directories(args.skills_dir)
        assert_approved_global_skill_set(skill_paths)
        assert_public_safe(skill_paths)
        args.output.expanduser().resolve().write_text(build_readme(skill_paths, language=readme_language_for_output(args.output)), encoding="utf-8")
        print(f"Rendered public README: {args.output.expanduser().resolve()}")
    elif args.command == "push":
        push(args.repo, args.source_dir, args.message, False, args.skills_dir)


if __name__ == "__main__":
    main()

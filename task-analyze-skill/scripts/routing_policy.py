#!/usr/bin/env python3
"""Load the shared model ladder and expose deterministic routing helpers."""

import importlib.util
import re
import unicodedata
from pathlib import Path

MODEL_CAPABILITY_CONFIG_PATH = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"
MODEL_REGISTRY_SCRIPT_PATH = Path(__file__).resolve().with_name("model_registry.py")
_MODEL_REGISTRY_SPEC = importlib.util.spec_from_file_location("task_analyze_model_registry", MODEL_REGISTRY_SCRIPT_PATH)
_MODEL_REGISTRY = importlib.util.module_from_spec(_MODEL_REGISTRY_SPEC)
_MODEL_REGISTRY_SPEC.loader.exec_module(_MODEL_REGISTRY)


def _load_model_capability_config(path=MODEL_CAPABILITY_CONFIG_PATH):
    try:
        resolved_path = Path(path).expanduser().resolve()
        if resolved_path == MODEL_CAPABILITY_CONFIG_PATH.resolve():
            payload = _MODEL_REGISTRY.load_registry(resolved_path) if resolved_path.exists() else _MODEL_REGISTRY.ensure_registry(registry_path=resolved_path)["registry"]
        else:
            payload = _MODEL_REGISTRY.load_registry(resolved_path)
        return _MODEL_REGISTRY.validate_registry(payload)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        raise ValueError(f"shared model capability registry is unreadable: {error}") from error


MODEL_CAPABILITY_CONFIG = _load_model_capability_config()
ADAPTIVE_POLICY = dict(MODEL_CAPABILITY_CONFIG["policy"])
ACTIVE_MODEL_ROWS = tuple(dict(row) for row in MODEL_CAPABILITY_CONFIG["models"])
ACTIVE_MODEL_ORDER = [row["id"] for row in ACTIVE_MODEL_ROWS]
ACTIVE_MODEL_DEFINITIONS = {row["id"]: {"efforts": list(row["codex_efforts"])} for row in ACTIVE_MODEL_ROWS}
PRIORITY_PRODUCER_CONFIG = dict(MODEL_CAPABILITY_CONFIG["priority_producer"] or {})
PRIORITY_PRODUCER_MODEL = PRIORITY_PRODUCER_CONFIG.get("id")
PRIORITY_PRODUCER_DEFINITIONS = {PRIORITY_PRODUCER_MODEL: {"efforts": list(PRIORITY_PRODUCER_CONFIG["codex_efforts"])}} if PRIORITY_PRODUCER_MODEL else {}
ENDING_FAST_CONFIG = dict(MODEL_CAPABILITY_CONFIG["ending_fast"])
ENDING_FAST_PRIMARY_PAIR = ENDING_FAST_CONFIG["primary_pair"]
ENDING_FAST_PRIMARY_MODEL, ENDING_FAST_PRIMARY_EFFORT = (None, None)  # Supplied by the selected user pair.
ENDING_FAST_FALLBACK_PAIR = ENDING_FAST_CONFIG.get("availability_fallback_pair")
ENDING_FAST_DEFINITIONS = {model["id"]: {"efforts": list(model["codex_efforts"])} for model in MODEL_CAPABILITY_CONFIG["catalog_models"] if model["id"] == ENDING_FAST_PRIMARY_MODEL}
SPARK_FIRST_CONFIG = PRIORITY_PRODUCER_CONFIG
SPARK_MODEL = PRIORITY_PRODUCER_MODEL
SPARK_MODEL_DEFINITIONS = PRIORITY_PRODUCER_DEFINITIONS
MODEL_DEFINITIONS = {**PRIORITY_PRODUCER_DEFINITIONS, **ENDING_FAST_DEFINITIONS, **ACTIVE_MODEL_DEFINITIONS}

MODEL_ORDER = list(MODEL_DEFINITIONS.keys())
MODEL_EFFORT_ORDER = list(MODEL_CAPABILITY_CONFIG["effort_order"])
MODEL_EFFORTS = {model: set(data["efforts"]) for model, data in MODEL_DEFINITIONS.items()}
ACTIVE_MODEL_EFFORTS = {model: set(data["efforts"]) for model, data in ACTIVE_MODEL_DEFINITIONS.items()}
MODEL_EFFORT_INDEX = {model: {effort: index for index, effort in enumerate(data["efforts"])} for model, data in MODEL_DEFINITIONS.items()}
MODEL_POSITION = {model: index for index, model in enumerate(MODEL_ORDER)}
SPARK_BOOTSTRAP_FAMILIES = {"tiny_text", "tiny_code", "command_generation"}
SPARK_LOW_PAIR = (PRIORITY_PRODUCER_MODEL, PRIORITY_PRODUCER_CONFIG["effort_by_complexity"]["easy"]) if PRIORITY_PRODUCER_MODEL else None
NORMAL_ADAPTIVE_MODELS = list(ACTIVE_MODEL_ORDER)
NORMAL_ADAPTIVE_LADDER = [(model, effort) for model in NORMAL_ADAPTIVE_MODELS for effort in MODEL_DEFINITIONS[model]["efforts"]]
MODEL_ROLE_PAIRS = dict(MODEL_CAPABILITY_CONFIG["role_pairs"])
# Retained only so the legacy local-history reader can parse old records.
LEARNING_FIELDS = ("task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "execution_domain")

# Keep prompt-only admission thresholds in one place. Runtime evidence and an
# explicit caller score remain authoritative over this lightweight classifier.
ROUTING_THRESHOLDS = {
    "fast_path_maximum_score": 24,
    "complex_route_minimum_score": 50,
    "advanced_route_minimum_score": 75,
    "maximum_route_attempts": 2,
    "maximum_ending_repair_rounds": 0,
}
EXECUTION_LIFECYCLE_VERSION = 1
HIGH_RISK_ROUTING_TERMS = ("security", "authentication", "authorization", "payment", "database migration", "production config", "credential", "deployment", "destructive", "安全", "认证", "授权", "支付", "数据迁移", "生产配置", "凭证", "部署", "删除全部", "破坏性")
_UNICODE_ROUTING_TRANSLATION = str.maketrans({"。": ".", "！": "!", "？": "?", "：": ":", "，": ",", "；": ";", "、": ",", "（": "(", "）": ")", "“": '"', "”": '"', "‘": "'", "’": "'"})
_CODE_ACTION_PATTERNS = (
    ("rename", r"\brename\b|重命名|改名|改个名字"),
    ("replace", r"\breplace\b|替换"),
    ("delete", r"\bdelete\b|删除"),
    ("fix", r"\bfix\b|\brepair\b|修复|修正"),
    ("migrate", r"\bmigrat(?:e|ion)\b|迁移(?:系统|数据|数据库|存档|格式)"),
    ("refactor", r"\brefactor\b|重构|拆分|拆成"),
    ("write", r"\b(?:write|implement|add|create)\b|实现|新增|编写"),
    ("edit", r"\b(?:edit|change|modify|update)\b|修改|改成|更改|调整|优化"),
    ("test", r"\btest(?:ing)?\b|测试|验证"),
)
_QUESTION_PATTERNS = (r"^(?:what|who|when|where|which|why|how|calculate|convert|is|are|can|does|do)\b", r"(?:什么|为什么|为何|怎么|如何|是否|哪[个里]|几[个]|干什么|有什么作用|有什么问题|请解释|解释一下|帮我分析|分析一下|是什么意思|天气怎么样)")
_CONCEPT_EXPLANATION_PATTERNS = (r"(?:请解释|解释(?:一下)?|是什么意思|什么是|分别是什么意思|介绍一下|定义是)" , r"\b(?:what is|explain|define|meaning of)\b")
_READ_ONLY_REQUEST_PATTERNS = (r"\b(?:read[- ]only|no edits?|do not (?:edit|modify|change)|without (?:editing|modifying|changing))\b", r"(?:只读|不修改|不要修改|无需修改|禁止修改)")
_CHINESE_MUTATION_ACTION = r"(?:修复|修正|重命名|改名|替换|删除|迁移|重构|编写|实现|新增|创建|修改|改成|更改|调整|优化|强化|更新|部署|安装|提交|推送|发布)"
_CHINESE_STRONG_MUTATION_ACTION = r"(?:修复|修正|重命名|改名|替换|删除|重构|编写|实现|新增|创建|修改|改成|更改|调整|优化|强化|更新|提交|推送|发布)"
_CHINESE_REQUEST_OBJECT = r"(?:(?!如何|怎么|是否|为什么|是什么)[^,.!?;:]){0,32}?"
_MUTATION_REQUEST_PATTERNS = (r"(?:^|[.!?;,:]\s*|\b(?:then|and then)\s+)(?:please\s+)?(?:fix|repair|rename|replace|delete|migrate|refactor|write|implement|add|create|edit|change|modify|update|optimize|strengthen|deploy|install|commit|push|publish)\b|\b(?:can|could|would|will)\s+you\s+(?:please\s+)?(?:fix|repair|rename|replace|delete|migrate|refactor|write|implement|add|create|edit|change|modify|update|optimize|strengthen|deploy|install|commit|push|publish)\b", rf"(?:^|然后|随后|接着|继续|并且|并|再)(?:请|给我|帮我|请帮我)?(?:直接|开始)?{_CHINESE_MUTATION_ACTION}|[,.!?;:](?:(?:请|给我|帮我|请帮我|直接|开始){_CHINESE_MUTATION_ACTION}|{_CHINESE_STRONG_MUTATION_ACTION})|(?:给我|帮我|请帮我)(?:继续)?{_CHINESE_MUTATION_ACTION}|(?:给我|帮我|请帮我){_CHINESE_REQUEST_OBJECT}{_CHINESE_MUTATION_ACTION}")
_MATERIAL_RESULT_STAGE_PATTERNS = (("inspect", (r"\b(?:audit|inspect|review|analyze|investigate)\b", r"(?:分析|查看|检查|审计|调查|排查|核对|查(?:一下)?(?:skill|代码|任务))")), ("simulate", (r"\b(?:simulate|replay|benchmark)\b", r"(?:模拟|重放|回放|基准测试|benchmark)")), ("change", (r"\b(?:fix|repair|rename|replace|delete|migrate|refactor|write|implement|add|create|edit|change|modify|update|optimize|strengthen)\b", r"(?:修复|修正|重命名|改名|替换|删除|迁移|重构|编写|实现|新增|创建|修改|改成|更改|调整|优化|强化|更新)")), ("test", (r"\b(?:test|testing|verify|validate|regression|render|visual verification)\b", r"(?:测试|验证|回归|验收|渲染验收|视觉验收)")), ("deploy", (r"\b(?:deploy|deployment|install|installation)\b", r"(?:部署|安装)")), ("publish", (r"\b(?:commit|push|publish|submit)\b", r"(?:提交|推送|发布)")))
_FILE_PATTERN = re.compile(r"(?<![\w./-])[\w./-]+\.(?:py|cs|js|ts|tsx|json|md|yaml|yml)(?![\w/-])", re.IGNORECASE)


def normalize_routing_input(prompt):
    """Normalize punctuation and spacing before deterministic prompt routing."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(prompt or "")).translate(_UNICODE_ROUTING_TRANSLATION)).strip()


def _routing_text(prompt):
    return normalize_routing_input(prompt).casefold()


def _matches_any(text, patterns):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def infer_prompt_material_stages(prompt):
    """Return bounded output-bearing stages without reading task files."""
    text = _routing_text(prompt)
    return [stage for stage, patterns in _MATERIAL_RESULT_STAGE_PATTERNS if _matches_any(text, patterns)]


def infer_prompt_task_type(prompt):
    """Classify task intent without conflating a question with its complexity."""
    text = _routing_text(prompt)
    if not text:
        return "unknown"
    matched_operations = [operation for operation, pattern in _CODE_ACTION_PATTERNS if re.search(pattern, text, re.IGNORECASE)]
    action_found = any(operation != "test" for operation in matched_operations)
    mutation_requested = _matches_any(text, _MUTATION_REQUEST_PATTERNS)
    read_only_requested = _matches_any(text, _READ_ONLY_REQUEST_PATTERNS)
    question_found = text.endswith(("?", "!")) or _matches_any(text, _QUESTION_PATTERNS)
    if mutation_requested:
        return "code"
    if question_found:
        return "question"
    if _matches_any(text, (r"^(?:analyze|audit|investigate|inspect|review)\b", r"^(?:请)?(?:分析|审计|调查|排查|检查|查看|核对)")):
        return "analysis"
    if action_found and not read_only_requested:
        return "code"
    if _FILE_PATTERN.search(text):
        return "question"
    if _matches_any(text, (r"\b(?:research|investigate)\b", r"调研|研究")):
        return "research"
    if _matches_any(text, (r"\b(?:write|draft|translate)\b", r"写一[篇份]|起草|翻译")):
        return "writing"
    if _matches_any(text, (r"\b(?:analyze|audit|investigate|inspect|review)\b", r"分析|审计|调查|排查|检查|查看|核对")):
        return "analysis"
    return "unknown"


def infer_prompt_operation(prompt, task_type=None):
    """Return a bounded operation label for a normalized prompt."""
    text = _routing_text(prompt)
    resolved_type = task_type or infer_prompt_task_type(prompt)
    if resolved_type == "question":
        return "answer"
    for operation, pattern in _CODE_ACTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return operation
    if resolved_type == "analysis":
        return "analyze"
    if resolved_type == "research":
        return "research"
    if resolved_type == "writing":
        return "write"
    return "work"


def _prompt_file_count(text):
    return len(set(_FILE_PATTERN.findall(text)))


def analyze_prompt_routing(prompt, risk="low", ambiguity="low"):
    """Produce deterministic bilingual task type, score, reasons, and fast-path admission."""
    normalized = normalize_routing_input(prompt)
    text = normalized.casefold()
    explicit = re.search(r"(?:complexity|复杂度)(?:\s*score)?\s*[:=]\s*(100|[1-9]?\d)\b", text, re.IGNORECASE)
    task_type = infer_prompt_task_type(normalized)
    operation = infer_prompt_operation(normalized, task_type)
    material_result_stages = infer_prompt_material_stages(normalized)
    if task_type == "analysis" and not _matches_any(normalized, _MUTATION_REQUEST_PATTERNS):
        material_result_stages = [stage for stage in material_result_stages if stage in {"inspect", "simulate", "test"}]
    coupled_diagnosis_and_change = set(material_result_stages) == {"inspect", "change"}
    result_bearing_request = task_type != "question" or _matches_any(normalized, _MUTATION_REQUEST_PATTERNS)
    graph_required = result_bearing_request and len(material_result_stages) >= 2 and not coupled_diagnosis_and_change
    if explicit:
        score = int(explicit.group(1))
        reasons = ["explicit complexity score"]
    else:
        score = 12 if task_type == "question" else 18 if task_type == "code" else 20
        reasons = ["question baseline" if task_type == "question" else "code baseline" if task_type == "code" else "general baseline"]
        additions = []
        scope_patterns = (r"\b(?:project[- ]wide|entire project|whole project|across the project|cross[- ]project)\b", r"整个项目|全项目|整个\s*unity\s*项目|跨项目")
        multi_file_patterns = (r"\b(?:multi[- ]file|multiple files|(?:\d+|six)[- ]file|across files|cross[- ]file|multiple modules|cross[- ]module)\b", r"多个文件|跨文件|多个模块|跨模块")
        architecture_patterns = (r"\b(?:architecture|refactor|distributed)\b", r"架构|重构|拆分|拆成")
        concern_patterns = (
            ("database", (r"\bdatabase\b", r"数据库"), 5),
            ("migration", (r"\b(?:data(?:base)? migration|migration)\b", r"数据迁移|迁移|存档迁移"), 10),
            ("concurrency", (r"\b(?:concurrency|parallelism|race condition|deadlock|async)\b", r"并发|线程|异步|竞态|死锁"), 10),
            ("rollback", (r"\brollback\b", r"回滚"), 8),
            ("compatibility", (r"\b(?:compatibility|backward compatible)\b", r"兼容|向后兼容|旧存档|旧版本"), 8),
            ("performance", (r"\b(?:performance|optimization|optimize)\b", r"性能|优化"), 8),
            ("security", (r"\b(?:security|authentication|authorization|permission)\b", r"安全|认证|授权|权限"), 10),
            ("validation", (r"\b(?:test(?:ing)?|verification|regression|end-to-end|integration test)\b", r"测试|验证|回归|端到端|集成测试"), 7),
            ("deployment", (r"\b(?:deploy(?:ment)?|\bci\b|\bcd\b)\b", r"部署|持续集成|持续部署"), 7),
            ("integration", (r"\b(?:integration|external api|network|server|client)\b", r"集成|网络|服务器|客户端|addressables|ecs"), 6),
            ("workflow", (r"\b(?:pipeline|workflow graph|orchestration)\b", r"流程图|编排"), 12),
            ("serialization", (r"\b(?:serialization|prefab|addressables|ecs)\b", r"序列化|prefab|addressables|ecs|场景|存档"), 5),
            ("global lifecycle", (r"\b(?:lifecycle|model routing|global skill|global task|ending)\b", r"生命周期|模型路由|全局\s*skill|全局任务|结束验证"), 22),
            ("repair orchestration", (r"\b(?:repair loops?|retry|fresh verifier|fallback|independent (?:checks?|tasks?))\b", r"修复循环|重试|独立验证|回退"), 8),
        )
        if _matches_any(text, scope_patterns):
            additions.append(("project-wide scope", 22))
        if _matches_any(text, multi_file_patterns):
            additions.append(("cross-file scope", 18))
        file_count = _prompt_file_count(text)
        if file_count > 1:
            additions.append((f"{file_count} named files", min(15, (file_count - 1) * 5)))
        if _matches_any(text, architecture_patterns):
            additions.append(("architecture or refactor scope", 10))
        action_count = sum(bool(re.search(pattern, text, re.IGNORECASE)) for _, pattern in _CODE_ACTION_PATTERNS)
        if action_count > 1:
            additions.append(("multiple requested actions", min(12, (action_count - 1) * 4)))
        if graph_required:
            additions.append((f"{len(material_result_stages)} material result stages", min(40, (len(material_result_stages) - 1) * 10)))
        for concern, patterns, weight in concern_patterns:
            if _matches_any(text, patterns):
                additions.append((concern, weight))
        for label, weight in additions:
            score += weight
            reasons.append(f"{label} +{weight}")
        system_terms = sum(term in text for term in ("skill", "script", "validator", "documentation", "tests", "memory", "obsidian", "model", "ending"))
        if task_type == "code" and system_terms >= 3:
            system_weight = min(20, (system_terms - 2) * 4)
            score += system_weight
            reasons.append(f"multi-surface system delivery +{system_weight}")
        direct_small_edit = task_type == "code" and not additions and _matches_any(text, (r"\b(?:one[- ]line|single|small|tiny|typo)\b", r"这一行|一个变量|从\s*\d+\s*改成\s*\d+|拼写错误|改个名字"))
        if direct_small_edit:
            score = min(score, 16)
            reasons.append("bounded single edit cap")
        concept_explanation = task_type == "question" and _matches_any(text, _CONCEPT_EXPLANATION_PATTERNS) and not _matches_any(text, scope_patterns + multi_file_patterns)
        if concept_explanation:
            score = min(score, ROUTING_THRESHOLDS["fast_path_maximum_score"])
            reasons.append("concept explanation cap")
        numeric_signals = sum(marker in text for marker in ("decimal", "round_half_up", "round half up", "tax", "currency", "cents", "percent"))
        if numeric_signals >= 2:
            score += 32
            reasons.append("multi-part numeric correctness +32")
        word_count = len(text.split())
        if word_count >= 80:
            score += 8
            reasons.append("long request +8")
        if word_count >= 160:
            score += 8
            reasons.append("very long request +8")
    normalized_risk = str(risk or "low").strip().casefold()
    risk_override = normalized_risk not in {"", "low"} or _matches_any(text, tuple(re.escape(term) for term in HIGH_RISK_ROUTING_TERMS))
    if risk_override and score <= ROUTING_THRESHOLDS["fast_path_maximum_score"]:
        score = ROUTING_THRESHOLDS["fast_path_maximum_score"] + 1
        reasons.append("risk override exits fast path")
    score = max(0, min(100, score))
    fast_path = score <= ROUTING_THRESHOLDS["fast_path_maximum_score"] and normalized_risk in {"", "low"} and not risk_override and str(ambiguity or "low").strip().casefold() in {"", "low"} and task_type in {"code", "question", "writing"}
    return {"normalized_prompt": normalized, "task_type": task_type, "operation": operation, "complexity_score": score, "reasons": reasons, "fast_path_eligible": fast_path, "risk_override": risk_override, "material_result_stages": material_result_stages, "graph_required": graph_required}


def execution_lifecycle_contract(complexity_score, fast_path_eligible=False, graph_admitted=False, result_node_count=1, risk="low", ambiguity="low"):
    """Return the mandatory direct-or-planned execution and acceptance contract."""
    if isinstance(complexity_score, bool) or not isinstance(complexity_score, int) or not 0 <= complexity_score <= 100:
        raise ValueError("complexity_score must be an integer from 0 to 100")
    if isinstance(result_node_count, bool) or not isinstance(result_node_count, int) or result_node_count < 1:
        raise ValueError("result_node_count must be a positive integer")
    low_risk = str(risk or "low").strip().casefold() in {"", "low"}
    low_ambiguity = str(ambiguity or "low").strip().casefold() in {"", "low"}
    direct = bool(fast_path_eligible and complexity_score <= ROUTING_THRESHOLDS["fast_path_maximum_score"] and low_risk and low_ambiguity and result_node_count == 1 and not graph_admitted)
    mode = "direct" if direct else "planned_graph" if graph_admitted or result_node_count > 1 else "planned_single"
    return {"schema_version": EXECUTION_LIFECYCLE_VERSION, "mode": mode, "plan_required": not direct, "execution_topology": "dependency_graph" if mode == "planned_graph" else "single", "execution_stages": ["execute"] if direct else ["plan", "execute"], "acceptance_policy": "in_task_relevant_verification", "final_aggregate_only": True, "no_surface_action": "intentionally_skipped_simple_task", "model_selection": "user_selected_for_governing_skills_else_adaptive", "repeated_quality_failure": "same_topic_diagnose_then_gradual_model_or_effort_strengthening", "reasoning_effort": "user_selected_for_governing_skills_else_estimated_steps", "operational_failure": "quality_neutral_retry_or_allowed_fallback", "verified_pass": "retain_then_trial_down_after_two", "topic_change": "reset_same_session_state"}

EXECUTION_DOMAIN_REGISTRY_VERSION = 2
EXECUTION_DOMAIN_REGISTRY_DEFAULT = "general"
EXECUTION_DOMAIN_REGISTRY_LEGACY = "code_unspecified"
CODE_GATE_VERSION = 1
CODE_SKILL_ENTRY_REFERENCE = "code-skill/SKILL.md"
CODE_WRITING_PHILOSOPHY_REFERENCE = "code-skill/references/code-writing-philosophy.md"
UNITY_CSHARP_CATEGORY_RULES = (
    {"id": "structure", "label": "Unity structure and ownership", "reference_path": "code-skill/references/unity-game-code-structure-design.md", "patterns": (r"\b(?:architecture|ownership|controller|manager|scriptableobject|factory|object pool|pooling|observer|command|prototype|singleton|design pattern|data flow)\b", r"(?:结构设计|架构|所有权|控制器|管理器|脚本化对象|工厂|对象池|设计模式|数据流)")},
    {"id": "lifecycle_serialization", "label": "Unity lifecycle and serialization", "reference_path": "code-skill/references/unity-lifecycle-and-serialization.md", "patterns": (r"\b(?:awake|onenable|ondisable|ondestroy|fixedupdate|lateupdate|monobehaviour|scene|prefab|component|event|subscription|coroutine|async|main thread|physics|serialize|serialization|inspector)\b|\b(?:start|update)\s*\(", r"(?:生命周期|场景|预制体|组件|事件|订阅|协程|异步|主线程|物理|序列化|检查器)")},
    {"id": "service_integration", "label": "Unity service integration", "reference_path": "code-skill/references/unity-service-integration.md", "patterns": (r"\b(?:unity gaming services|game services|cloud save|authentication|analytics|addressables|sdk|provider|service integration|service initialization|initialize services)\b", r"(?:游戏服务|云存档|认证|分析服务|地址资源|服务集成|服务初始化|提供商)")},
)

EXECUTION_DOMAINS = {
    "general": {
        "display_name": "General",
        "kind": "general",
        "language_aliases": [],
        "owner_skill": "workflow-skill",
        "owner_enforced": False,
        "spark_first": False,
        "reference_path": "task-analyze-skill/references/model-selection.md",
        "active": True,
        "history_only": False,
    },
    "python": {
        "display_name": "Python",
        "kind": "code",
        "language_aliases": ["python", "py", "python3"],
        "owner_skill": "code-skill",
        "owner_enforced": True,
        "spark_first": True,
        "reference_path": "code-skill/references/python-rules.md",
        "active": True,
        "history_only": False,
    },
    "csharp": {
        "display_name": "C# (history only)",
        "kind": "code",
        "language_aliases": [],
        "owner_skill": "code-skill",
        "owner_enforced": False,
        "spark_first": True,
        "reference_path": "code-skill/references/csharp-rules.md",
        "active": False,
        "history_only": True,
    },
    "unity_csharp": {
        "display_name": "Unity C#",
        "kind": "code",
        "language_aliases": ["unity_csharp", "unity-csharp", "unitycsharp", "csharp", "c#", "cs", "unity"],
        "owner_skill": "code-skill",
        "owner_enforced": True,
        "spark_first": True,
        "reference_path": "code-skill/references/unity-csharp-rules.md",
        "active": True,
        "history_only": False,
    },
    "code_unspecified": {
        "display_name": "Unspecified Code",
        "kind": "code",
        "language_aliases": [],
        "owner_skill": "code-skill",
        "owner_enforced": False,
        "spark_first": True,
        "reference_path": "code-skill/references/spark-small-code.md",
        "active": False,
        "history_only": True,
    },
}

PROFILE_PRESET_VERSION = 2


def _profile_model_fields(role_pair):
    return {"static_suggestion": MODEL_ROLE_PAIRS[role_pair], "hard_floor": MODEL_ROLE_PAIRS["floor"]}


PROFILE_PRESETS = {
    "general-answer-easy": {"task_family": "direct", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("weak_default")},
    "summary-easy": {"task_family": "document", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("floor")},
    "analysis-complex": {"task_family": "grounded", "artifact": "report", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_complex")},
    "spreadsheet-easy": {"task_family": "data", "artifact": "document", "scope": "single", "ambiguity": "low", "modality": "mixed", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_default")},
    "spreadsheet-complex": {"task_family": "data", "artifact": "document", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_complex")},
    "document-easy": {"task_family": "document", "artifact": "document", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("weak_default")},
    "document-complex": {"task_family": "document", "artifact": "document", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_complex")},
    "integration-complex": {"task_family": "integration", "artifact": "patch", "scope": "project", "ambiguity": "high", "modality": "mixed", "risk": "medium", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("frontier_complex")},
    "grounded-repository-answer-easy": {"task_family": "grounded", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_default")},
    "grounded-repository-answer-complex": {"task_family": "grounded", "artifact": "answer", "scope": "multi", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", **_profile_model_fields("balanced_complex")},
    "tiny-text": {"task_family": "tiny_text", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": "general", **_profile_model_fields("floor")},
    "command-generation": {"task_family": "command_generation", "artifact": "script", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": "general", **_profile_model_fields("floor")},
    "tiny-code": {"task_family": "tiny_code", "artifact": "patch", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, **_profile_model_fields("floor")},
    "code-easy": {"task_family": "code", "artifact": "patch", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, **_profile_model_fields("balanced_default")},
    "code-complex": {"task_family": "code", "artifact": "patch", "scope": "multi", "ambiguity": "medium", "modality": "text", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, **_profile_model_fields("balanced_complex")},
}


def execution_domain_names():
    return list(EXECUTION_DOMAINS.keys())


def execution_domain_metadata(execution_domain):
    metadata = EXECUTION_DOMAINS.get(execution_domain)
    if metadata is None:
        raise ValueError(f"unknown execution domain: {execution_domain}")
    payload = dict(metadata)
    payload["id"] = execution_domain
    payload["language_aliases"] = list(metadata.get("language_aliases", []))
    return payload


def execution_domain_names_set():
    return set(execution_domain_names())


def is_code_execution_domain(execution_domain):
    return execution_domain_metadata(execution_domain).get("kind") == "code"


def expected_owner_skill(execution_domain):
    metadata = execution_domain_metadata(execution_domain)
    if not metadata.get("owner_enforced", False):
        return None
    return metadata.get("owner_skill")


def requires_spark_first(execution_domain):
    return bool(execution_domain_metadata(execution_domain).get("spark_first"))


def reference_path_for(execution_domain):
    return execution_domain_metadata(execution_domain).get("reference_path")


def _matches_code_category(text, patterns):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def infer_code_execution_domain(task_text="", language=None):
    if language is not None:
        normalized = str(language).strip().lower()
        for domain in execution_domain_names():
            metadata = execution_domain_metadata(domain)
            if metadata.get("active") and metadata.get("kind") == "code" and normalized in metadata.get("language_aliases", []):
                return domain
    normalized_text = normalize_routing_input(task_text).casefold()
    if re.search(r"(?:^|[^\w])[^\s]+\.py(?:$|[^\w])|\bpython(?:3)?\b", normalized_text):
        return "python"
    if re.search(r"(?:^|[^\w])[^\s]+\.cs(?:$|[^\w])|\bc#\b|\bcsharp\b|\bunity\b|(?:统一|合并)?\s*c#|unity\s*c#", normalized_text, re.IGNORECASE):
        return "unity_csharp"
    return None


def code_rule_bundle(execution_domain=None, task_text="", language=None, purpose="", operation=""):
    resolved_domain = execution_domain
    if resolved_domain in {None, "", "general", EXECUTION_DOMAIN_REGISTRY_LEGACY}:
        resolved_domain = infer_code_execution_domain(task_text, language)
    if resolved_domain == "csharp":
        resolved_domain = "unity_csharp"
    if resolved_domain is not None and resolved_domain not in EXECUTION_DOMAINS:
        raise ValueError(f"unknown execution domain {resolved_domain}")
    if resolved_domain is not None and (not execution_domain_is_active(resolved_domain) or not is_code_execution_domain(resolved_domain)):
        resolved_domain = infer_code_execution_domain(task_text, language)
    reference_paths = [CODE_SKILL_ENTRY_REFERENCE, CODE_WRITING_PHILOSOPHY_REFERENCE]
    labels = ["universal code philosophy"]
    categories = []
    if resolved_domain is not None:
        language_reference = reference_path_for(resolved_domain)
        if language_reference not in reference_paths:
            reference_paths.append(language_reference)
        labels.append(execution_domain_metadata(resolved_domain)["display_name"])
        if resolved_domain == "unity_csharp":
            category_text = " ".join(str(value or "") for value in (task_text, purpose, operation))
            for category in UNITY_CSHARP_CATEGORY_RULES:
                if _matches_code_category(category_text, category["patterns"]):
                    categories.append(category["id"])
                    reference_paths.append(category["reference_path"])
                    labels.append(category["label"])
    message = f"Code Gate loaded: {', '.join(labels)}. Enforcing explicit result ownership, direct calls, and one-line code when clear."
    return {"schema_version": CODE_GATE_VERSION, "execution_domain": resolved_domain or "unregistered_code", "entry_reference": CODE_SKILL_ENTRY_REFERENCE, "universal_reference": CODE_WRITING_PHILOSOPHY_REFERENCE, "category_ids": categories, "reference_paths": reference_paths, "labels": labels, "message": message}


def reference_paths_for(execution_domain=None, task_text="", language=None, purpose="", operation=""):
    return code_rule_bundle(execution_domain, task_text, language, purpose, operation)["reference_paths"]


def execution_domain_is_active(execution_domain):
    return bool(execution_domain_metadata(execution_domain).get("active"))


def resolve_execution_domain(owning_skill=None, task_family=None, explicit_domain=None, language=None, purpose=None):
    if explicit_domain is not None:
        explicit_domain = str(explicit_domain).strip()
        if explicit_domain not in EXECUTION_DOMAINS:
            raise ValueError(f"unknown execution domain {explicit_domain}")
        return explicit_domain

    if language is not None:
        normalized = str(language).strip().lower()
        for domain in execution_domain_names():
            aliases = execution_domain_metadata(domain).get("language_aliases", [])
            if normalized in aliases:
                return domain

    if owning_skill == "code-skill":
        return EXECUTION_DOMAIN_REGISTRY_LEGACY

    if task_family in {"code", "tiny_code"}:
        return EXECUTION_DOMAIN_REGISTRY_LEGACY

    return EXECUTION_DOMAIN_REGISTRY_DEFAULT


def infer_execution_domain(owning_skill=None, task_family=None, explicit_domain=None, purpose=None, language=None):
    return resolve_execution_domain(
        owning_skill=owning_skill,
        task_family=task_family,
        explicit_domain=explicit_domain,
        language=language,
        purpose=purpose,
    )


def validate_execution_domain_registry(skills_root=None):
    skills_root = Path(skills_root) if skills_root is not None else Path(__file__).resolve().parents[2]
    if not execution_domain_names():
        raise ValueError("execution domain registry must contain at least one domain")
    if EXECUTION_DOMAIN_REGISTRY_DEFAULT not in execution_domain_names():
        raise ValueError(f"execution domain default is unknown: {EXECUTION_DOMAIN_REGISTRY_DEFAULT}")
    if EXECUTION_DOMAIN_REGISTRY_LEGACY not in execution_domain_names():
        raise ValueError(f"execution domain legacy id is unknown: {EXECUTION_DOMAIN_REGISTRY_LEGACY}")

    seen_aliases = set()
    seen_reference_paths = set()

    def _normalize_reference_path(value, *, domain):
        if not isinstance(value, str) or not value:
            raise ValueError(f"execution domain {domain} has invalid reference_path")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"execution domain {domain} has invalid reference_path")
        reference = Path(normalized)
        has_root = normalized.startswith(("/", "\\"))
        has_drive = len(normalized) >= 2 and normalized[0].isalpha() and normalized[1] == ":"
        if reference.is_absolute() or has_root or has_drive:
            raise ValueError(f"execution domain {domain} reference_path must be relative to the skills root: {normalized}")
        if any(part == ".." for part in reference.parts):
            raise ValueError(f"execution domain {domain} reference_path must not use parent traversal: {normalized}")
        if not reference.as_posix():
            raise ValueError(f"execution domain {domain} has invalid reference_path")
        return normalized

    for domain in execution_domain_names():
        metadata = execution_domain_metadata(domain)
        required = {
            "display_name",
            "kind",
            "language_aliases",
            "owner_skill",
            "owner_enforced",
            "spark_first",
            "reference_path",
            "active",
            "history_only",
        }
        missing = required - set(metadata.keys())
        if missing:
            raise ValueError(f"execution domain {domain} missing metadata: {', '.join(sorted(missing))}")
        if not isinstance(metadata["display_name"], str) or not metadata["display_name"]:
            raise ValueError(f"execution domain {domain} has invalid display_name")
        if metadata["kind"] not in {"general", "code"}:
            raise ValueError(f"execution domain {domain} has invalid kind: {metadata['kind']}")
        if not isinstance(metadata["language_aliases"], list):
            raise ValueError(f"execution domain {domain} language_aliases must be a list")
        aliases = []
        for alias in metadata["language_aliases"]:
            raw_alias = str(alias)
            if raw_alias != raw_alias.strip().lower():
                raise ValueError(f"execution domain {domain} has non-canonical language_alias: {raw_alias}")
            alias = raw_alias
            if not alias:
                raise ValueError(f"execution domain {domain} has empty language_alias")
            if alias in seen_aliases:
                raise ValueError(f"language_alias is reused by registry: {alias}")
            aliases.append(alias)
            seen_aliases.add(alias)
        if not isinstance(metadata["owner_skill"], str) or not metadata["owner_skill"]:
            raise ValueError(f"execution domain {domain} has invalid owner_skill")
        owner_skill_path = skills_root / metadata["owner_skill"] / "SKILL.md"
        if not owner_skill_path.is_file():
            raise ValueError(f"execution domain {domain} owner SKILL.md is missing: {owner_skill_path}")
        if not isinstance(metadata["owner_enforced"], bool):
            raise ValueError(f"execution domain {domain} owner_enforced must be bool")
        if not isinstance(metadata["spark_first"], bool):
            raise ValueError(f"execution domain {domain} spark_first must be bool")
        if not isinstance(metadata["reference_path"], str) or not metadata["reference_path"]:
            raise ValueError(f"execution domain {domain} must include a reference_path")
        normalized_reference = _normalize_reference_path(metadata["reference_path"], domain=domain)
        if normalized_reference in seen_reference_paths:
            raise ValueError(f"execution domain {domain} reuses reference_path")
        seen_reference_paths.add(normalized_reference)
        reference = skills_root / normalized_reference
        if not reference.is_file():
            raise ValueError(f"execution domain {domain} reference file is missing: {reference}")
        if not isinstance(metadata["active"], bool):
            raise ValueError(f"execution domain {domain} active must be bool")
        if not isinstance(metadata["history_only"], bool):
            raise ValueError(f"execution domain {domain} history_only must be bool")
        if metadata["active"] and metadata["history_only"]:
            raise ValueError(f"execution domain {domain} cannot be both active and history-only")
        if metadata["history_only"] and aliases:
            raise ValueError(f"execution domain {domain} history-only rows cannot claim language aliases")
    return True


def public_execution_domain_rows():
    return [
        {
            "id": domain,
            "display_name": metadata.get("display_name"),
            "kind": metadata.get("kind"),
            "language_aliases": list(metadata.get("language_aliases", [])),
            "owner_skill": metadata.get("owner_skill"),
            "owner_enforced": metadata.get("owner_enforced"),
            "spark_first": metadata.get("spark_first"),
            "reference_path": metadata.get("reference_path"),
            "active": metadata.get("active"),
            "history_only": metadata.get("history_only"),
        }
        for domain, metadata in (
            (domain, execution_domain_metadata(domain))
            for domain in execution_domain_names()
        )
    ]


def pair_text(model, effort):
    return f"{model}|{effort}"


def parse_model_effort_pair(value):
    if not isinstance(value, str):
        raise ValueError("model|effort pair must be a string")
    value = value.strip()
    if value.count("|") != 1:
        raise ValueError("model|effort pair must be separated by one |")
    model, effort = (part.strip() for part in value.split("|", 1))
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]*", model) or effort not in {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}:
        raise ValueError("invalid model or effort")
    return model, effort


def parse_pair(value):
    return parse_model_effort_pair(value)


def _ensure_model(model):
    if model not in MODEL_EFFORTS or model not in MODEL_ORDER:
        raise ValueError("unsupported model")


def _ensure_supported_pair(model, effort):
    _ensure_model(model)
    if effort not in MODEL_EFFORTS[model]:
        raise ValueError("unsupported effort")


def compare_pair(left, right):
    if not isinstance(left, tuple) or not isinstance(right, tuple):
        raise ValueError("pairs must be tuples")
    left_model, left_effort = left
    right_model, right_effort = right
    _ensure_supported_pair(left_model, left_effort)
    _ensure_supported_pair(right_model, right_effort)
    left_model_position = MODEL_ORDER.index(left_model)
    right_model_position = MODEL_ORDER.index(right_model)
    if left_model != right_model:
        return -1 if left_model_position < right_model_position else 1
    left_index = MODEL_EFFORT_ORDER.index(left_effort)
    right_index = MODEL_EFFORT_ORDER.index(right_effort)
    if left_index == right_index:
        return 0
    return -1 if left_index < right_index else 1


def _sorted_pairs(values):
    return sorted(values, key=lambda pair: [MODEL_ORDER.index(pair[0]), MODEL_EFFORT_ORDER.index(pair[1])])


def canonical_pairs(values):
    pairs = []
    seen = set()
    for value in values:
        pair = parse_pair(value) if isinstance(value, str) else value
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("pair values must be (model, effort)")
        _ensure_supported_pair(*pair)
        if pair in seen:
            raise ValueError("candidate_ladder must contain unique pairs")
        pairs.append(pair)
        seen.add(pair)
    return _sorted_pairs(pairs)


def normal_adaptive_ladder():
    return list(NORMAL_ADAPTIVE_LADDER)


def normal_adaptive_pair_texts():
    return [pair_text(*pair) for pair in NORMAL_ADAPTIVE_LADDER]


def is_tiny_spark_profile(task_family, modality, risk, complexity="easy", ambiguity="low"):
    """Recognize the former narrow Spark profile for legacy history parsing."""
    return (
        task_family in SPARK_BOOTSTRAP_FAMILIES
        and modality == "text"
        and risk == "low"
        and complexity == "easy"
        and ambiguity == "low"
    )


def adaptive_ladder_for_profile(task_family, modality, risk, complexity="easy", ambiguity="low"):
    return normal_adaptive_ladder()


def priority_first_pair(task_type, modality="text", operation="work", complexity="easy", complexity_score=None, purpose=None):
    """Return the priority producer for a bounded eligible task or task segment."""
    if not PRIORITY_PRODUCER_CONFIG.get("enabled") or PRIORITY_PRODUCER_MODEL is None or modality != "text" or complexity != "easy":
        return None
    maximum_score = PRIORITY_PRODUCER_CONFIG.get("task_segment_maximum_complexity_score", PRIORITY_PRODUCER_CONFIG.get("small_edit_maximum_complexity_score", 24))
    if complexity_score is None or isinstance(complexity_score, bool) or not isinstance(complexity_score, int) or not 0 <= complexity_score <= maximum_score:
        return None
    eligible_task = task_type in PRIORITY_PRODUCER_CONFIG.get("eligible_task_types", [])
    eligible_operation = operation in PRIORITY_PRODUCER_CONFIG.get("eligible_operations", [])
    excluded_operation = operation in PRIORITY_PRODUCER_CONFIG.get("excluded_operations", [])
    eligible_segment = purpose in PRIORITY_PRODUCER_CONFIG.get("task_segment_purposes", [])
    if excluded_operation or not ((eligible_task and eligible_operation) or eligible_segment):
        return None
    effort = PRIORITY_PRODUCER_CONFIG["effort_by_complexity"]["easy"]
    return (PRIORITY_PRODUCER_MODEL, effort)


def spark_first_pair(task_type, modality="text", operation="work", complexity="easy", complexity_score=None, purpose=None):
    return priority_first_pair(task_type, modality, operation, complexity, complexity_score, purpose)


def scheduled_source_pair(complexity="easy"):
    if not PRIORITY_PRODUCER_CONFIG.get("enabled") or PRIORITY_PRODUCER_MODEL is None:
        return None
    effort = PRIORITY_PRODUCER_CONFIG["effort_by_complexity"].get(complexity)
    return (PRIORITY_PRODUCER_MODEL, effort) if effort in PRIORITY_PRODUCER_CONFIG["adaptive_efforts"] else None


def ending_fast_route_fields(selected_model=None, selected_effort=None):
    if not selected_model or not selected_effort:
        raise ValueError("Ending memory requires the user's selected model and effort")
    return {"model": selected_model, "effort": selected_effort, "selection_basis": "user_selected", "allow_fallback": [], "fallback_policy": "none"}


def adaptive_pair_texts_for_profile(task_family, modality, risk, complexity="easy", ambiguity="low"):
    return [pair_text(*pair) for pair in adaptive_ladder_for_profile(task_family, modality, risk, complexity, ambiguity)]


def profile_preset_names():
    return tuple(PROFILE_PRESETS.keys())


def resolve_profile_preset(profile_preset, *, project_family, owning_skill=None, execution_domain=None):
    if profile_preset not in PROFILE_PRESETS:
        raise ValueError(f"unknown profile preset: {profile_preset}")
    if not isinstance(project_family, str) or not project_family.strip():
        raise ValueError("project_family is required")
    preset = PROFILE_PRESETS[profile_preset]
    fixed_owner = preset["owning_skill"]
    if fixed_owner is None:
        if not isinstance(owning_skill, str) or not owning_skill.strip():
            raise ValueError("owning_skill is required for this profile preset")
        resolved_owner = owning_skill
    else:
        if owning_skill is not None and owning_skill != fixed_owner:
            raise ValueError(f"profile preset requires owning_skill={fixed_owner}")
        resolved_owner = fixed_owner
    fixed_domain = preset["execution_domain"]
    if fixed_domain is None:
        if execution_domain is None:
            raise ValueError("an active code execution_domain is required for this profile preset")
        domain_metadata = execution_domain_metadata(execution_domain)
        if not domain_metadata["active"] or domain_metadata["history_only"] or domain_metadata["kind"] != "code":
            raise ValueError("profile preset requires an active code execution_domain")
        resolved_domain = execution_domain
    else:
        if execution_domain is not None and execution_domain != fixed_domain:
            raise ValueError(f"profile preset requires execution_domain={fixed_domain}")
        resolved_domain = fixed_domain
    profile = {field: preset[field] for field in ("task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "verification_shape")}
    profile.update({"owning_skill": resolved_owner, "project_family": project_family, "execution_domain": resolved_domain})
    profile["candidate_ladder"] = adaptive_pair_texts_for_profile(profile["task_family"], profile["modality"], profile["risk"], profile["complexity"], profile["ambiguity"])
    profile["static_suggestion"] = preset["static_suggestion"]
    profile["hard_floor"] = preset["hard_floor"]
    return profile


def public_profile_preset_rows():
    rows = []
    for profile_preset, preset in PROFILE_PRESETS.items():
        condition = {field: preset[field] for field in ("task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "verification_shape")}
        rows.append({"id": profile_preset, "condition": condition, "owning_skill": preset["owning_skill"] or "caller_required", "execution_domain": preset["execution_domain"] or "active_code_domain_required", "static_suggestion": preset["static_suggestion"], "hard_floor": preset["hard_floor"]})
    return rows


def public_model_capability_rows():
    return {
        "schema_version": MODEL_CAPABILITY_CONFIG["schema_version"],
        "registry_id": MODEL_CAPABILITY_CONFIG["registry_id"],
        "scope": MODEL_CAPABILITY_CONFIG["scope"],
        "source": dict(MODEL_CAPABILITY_CONFIG["source"]),
        "active_family": dict(MODEL_CAPABILITY_CONFIG["active_family"]),
        "catalog_models": [dict(row) for row in MODEL_CAPABILITY_CONFIG["catalog_models"]],
        "ladder_direction": MODEL_CAPABILITY_CONFIG["ladder_direction"],
        "role_models": dict(MODEL_CAPABILITY_CONFIG["role_models"]),
        "role_pairs": dict(MODEL_ROLE_PAIRS),
        "policy": dict(ADAPTIVE_POLICY),
        "priority_producer": dict(PRIORITY_PRODUCER_CONFIG) if PRIORITY_PRODUCER_CONFIG else None,
        "ending_fast": dict(ENDING_FAST_CONFIG),
        "spark_first": dict(SPARK_FIRST_CONFIG),
        "private_learning_contract": dict(MODEL_CAPABILITY_CONFIG["private_learning_contract"]),
        "default_cold_start": MODEL_CAPABILITY_CONFIG["default_cold_start"],
        "cold_start_defaults": {key: dict(value) for key, value in MODEL_CAPABILITY_CONFIG["cold_start_defaults"].items()},
        "effort_order": list(MODEL_EFFORT_ORDER),
        "effort_guidance": dict(MODEL_CAPABILITY_CONFIG.get("effort_guidance", {})),
        "models": [dict(row) for row in ACTIVE_MODEL_ROWS],
    }


def validate_profile_preset_registry():
    required = {"task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "verification_shape", "owning_skill", "execution_domain", "static_suggestion", "hard_floor"}
    for profile_preset, preset in PROFILE_PRESETS.items():
        if set(preset) != required:
            raise ValueError(f"profile preset has invalid fields: {profile_preset}")
        sample_owner = preset["owning_skill"] or "workflow-skill"
        sample_domain = preset["execution_domain"] or next(domain for domain in EXECUTION_DOMAINS if execution_domain_metadata(domain)["active"] and execution_domain_metadata(domain)["kind"] == "code")
        resolved = resolve_profile_preset(profile_preset, project_family="global", owning_skill=sample_owner, execution_domain=sample_domain)
        pairs = canonical_pairs(resolved["candidate_ladder"])
        if parse_pair(resolved["static_suggestion"]) not in pairs or parse_pair(resolved["hard_floor"]) not in pairs:
            raise ValueError(f"profile preset pair is outside its canonical ladder: {profile_preset}")
    return True


def validate_model_capability_registry():
    _MODEL_REGISTRY.validate_registry(MODEL_CAPABILITY_CONFIG)
    if set(ACTIVE_MODEL_ORDER) != set(ACTIVE_MODEL_EFFORTS):
        raise ValueError("shared active model registry is inconsistent")
    minimum_pair = parse_pair(ADAPTIVE_POLICY["minimum_pair"])
    if minimum_pair != NORMAL_ADAPTIVE_LADDER[0]:
        raise ValueError("shared minimum pair must be the weakest active ladder pair")
    if PRIORITY_PRODUCER_MODEL and any(model == PRIORITY_PRODUCER_MODEL for model, _ in NORMAL_ADAPTIVE_LADDER):
        raise ValueError("priority producer must stay outside the quality ladder")
    if ACTIVE_MODEL_ORDER != [row["id"] for row in sorted(ACTIVE_MODEL_ROWS, key=lambda row: row["capability_rank"])]:
        raise ValueError("quality models must remain weakest-to-strongest")
    return True


def _eligible_pairs_by_model(pairs, target):
    return [pair for pair in pairs if pair[0] == target]


def downgrade_pair(current, eligible):
    current_pair = current
    if not isinstance(current_pair, tuple):
        raise ValueError("current pair must be a tuple")
    _ensure_supported_pair(*current_pair)
    ordered = canonical_pairs(eligible)
    if not ordered:
        return None
    current_model, current_effort = current_pair
    same_model = _eligible_pairs_by_model(ordered, current_model)
    for pair in reversed(same_model):
        if compare_pair(pair, current_pair) < 0:
            return pair
    current_model_rank = MODEL_POSITION[current_model]
    for model_rank in range(current_model_rank - 1, -1, -1):
        candidate_model = MODEL_ORDER[model_rank]
        candidates = _eligible_pairs_by_model(ordered, candidate_model)
        if candidates:
            return candidates[-1]
    return None


def upgrade_pair(current, eligible):
    current_pair = current
    if not isinstance(current_pair, tuple):
        raise ValueError("current pair must be a tuple")
    _ensure_supported_pair(*current_pair)
    ordered = canonical_pairs(eligible)
    if not ordered:
        return None
    current_model, current_effort = current_pair
    same_model = _eligible_pairs_by_model(ordered, current_model)
    for pair in same_model:
        if compare_pair(pair, current_pair) > 0:
            return pair
    current_model_rank = MODEL_POSITION[current_model]
    for model_rank in range(current_model_rank + 1, len(MODEL_ORDER)):
        candidate_model = MODEL_ORDER[model_rank]
        candidates = _eligible_pairs_by_model(ordered, candidate_model)
        if candidates:
            return candidates[0]
    return None


def canonical_pair_texts(pairs):
    return [pair_text(*pair) for pair in canonical_pairs(pairs)]


validate_execution_domain_registry()
validate_model_capability_registry()
validate_profile_preset_registry()

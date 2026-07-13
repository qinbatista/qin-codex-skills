#!/usr/bin/env python3
"""Load the shared model ladder and expose deterministic routing helpers."""

import json
from pathlib import Path

MODEL_CAPABILITY_CONFIG_PATH = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"


def _load_model_capability_config(path=MODEL_CAPABILITY_CONFIG_PATH):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"shared model capability registry is unreadable: {error}") from error
    required = {"schema_version", "registry_id", "scope", "ladder_direction", "policy", "spark_first", "effort_order", "effort_guidance", "models"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise ValueError("shared model capability registry is incomplete")
    if payload["schema_version"] != 1 or payload["scope"] != "shared_non_personal" or payload["ladder_direction"] != "weakest_to_strongest":
        raise ValueError("shared model capability registry contract is invalid")
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("shared model capability registry has no active models")
    ranks = [row.get("capability_rank") for row in models if isinstance(row, dict)]
    if ranks != list(range(1, len(models) + 1)):
        raise ValueError("shared model capability ranks must be contiguous weakest-to-strongest")
    effort_order = payload.get("effort_order")
    if not isinstance(effort_order, list) or len(effort_order) != len(set(effort_order)):
        raise ValueError("shared effort order must be a unique list")
    seen = set()
    for row in models:
        model = row.get("id")
        efforts = row.get("codex_efforts")
        if not isinstance(model, str) or not model.startswith("gpt-5.6-") or model in seen:
            raise ValueError("shared model ids must be unique GPT-5.6 ids")
        if not isinstance(efforts, list) or not efforts or any(effort not in effort_order for effort in efforts):
            raise ValueError(f"shared model {model} has invalid Codex efforts")
        if efforts != [effort for effort in effort_order if effort in efforts]:
            raise ValueError(f"shared model {model} efforts are not canonical")
        seen.add(model)
    policy = payload.get("policy")
    required_policy = {"enabled", "quality_first", "downgrade_after_real_pass", "upgrade_after_quality_failure", "operational_failures_are_neutral", "freeze_lowest_verified_pair", "minimum_pair"}
    if not isinstance(policy, dict) or not required_policy.issubset(policy) or policy.get("enabled") is not True:
        raise ValueError("shared adaptive policy is disabled or incomplete")
    valid_pairs = {f"{row['id']}|{effort}" for row in models for effort in row["codex_efforts"]}
    if policy.get("minimum_pair") not in valid_pairs:
        raise ValueError("shared minimum pair is not active")
    if payload.get("default_cold_start") not in valid_pairs:
        raise ValueError("shared default cold start is not active")
    cold_starts = payload.get("cold_start_defaults")
    if not isinstance(cold_starts, dict) or not cold_starts:
        raise ValueError("shared cold-start defaults are missing")
    for task_type, levels in cold_starts.items():
        if not isinstance(task_type, str) or not isinstance(levels, dict) or set(levels) != {"easy", "complex"}:
            raise ValueError("shared cold-start defaults are malformed")
        if any(pair not in valid_pairs for pair in levels.values()):
            raise ValueError("shared cold-start pair is not active")
    spark = payload.get("spark_first")
    if (
        not isinstance(spark, dict)
        or spark.get("enabled") is not True
        or spark.get("id") != "gpt-5.3-codex-spark"
        or spark.get("routing_role") != "first_attempt_text_code_producer"
        or spark.get("input_modalities") != ["text"]
        or spark.get("eligible_modalities") != ["text"]
        or spark.get("operational_fallback") != "current_obsidian_5_6_pair"
        or spark.get("quality_failure") != "record_to_obsidian_then_new_5_6_repair_lifecycle"
    ):
        raise ValueError("shared Spark-first contract is invalid")
    spark_efforts = spark.get("codex_efforts")
    adaptive_efforts = spark.get("adaptive_efforts")
    effort_by_complexity = spark.get("effort_by_complexity")
    if (
        not isinstance(spark_efforts, list)
        or spark_efforts != [effort for effort in effort_order if effort in spark_efforts]
        or not isinstance(adaptive_efforts, list)
        or any(effort not in spark_efforts for effort in adaptive_efforts)
        or set(effort_by_complexity or {}) != {"easy", "complex"}
        or any(effort not in adaptive_efforts for effort in effort_by_complexity.values())
    ):
        raise ValueError("shared Spark effort contract is invalid")
    private_contract = payload.get("private_learning_contract")
    if (
        not isinstance(private_contract, dict)
        or private_contract.get("authority") != "obsidian_project_memory"
        or private_contract.get("path_template") != "Projects/<project-key>/ModelExperience"
        or private_contract.get("specificity_order") != ["project_task", "module", "file", "symbol"]
        or private_contract.get("legacy_local_json") != "read_only_inactive"
    ):
        raise ValueError("shared private-learning boundary is invalid")
    return payload


MODEL_CAPABILITY_CONFIG = _load_model_capability_config()
ADAPTIVE_POLICY = dict(MODEL_CAPABILITY_CONFIG["policy"])
ACTIVE_MODEL_ROWS = tuple(dict(row) for row in MODEL_CAPABILITY_CONFIG["models"])
ACTIVE_MODEL_ORDER = [row["id"] for row in ACTIVE_MODEL_ROWS]
ACTIVE_MODEL_DEFINITIONS = {row["id"]: {"efforts": list(row["codex_efforts"])} for row in ACTIVE_MODEL_ROWS}
SPARK_FIRST_CONFIG = dict(MODEL_CAPABILITY_CONFIG["spark_first"])
SPARK_MODEL = SPARK_FIRST_CONFIG["id"]
SPARK_MODEL_DEFINITIONS = {SPARK_MODEL: {"efforts": list(SPARK_FIRST_CONFIG["codex_efforts"])}}
MODEL_DEFINITIONS = {**SPARK_MODEL_DEFINITIONS, **ACTIVE_MODEL_DEFINITIONS}

MODEL_ORDER = list(MODEL_DEFINITIONS.keys())
MODEL_EFFORT_ORDER = list(MODEL_CAPABILITY_CONFIG["effort_order"])
MODEL_EFFORTS = {model: set(data["efforts"]) for model, data in MODEL_DEFINITIONS.items()}
ACTIVE_MODEL_EFFORTS = {model: set(data["efforts"]) for model, data in ACTIVE_MODEL_DEFINITIONS.items()}
MODEL_EFFORT_INDEX = {model: {effort: index for index, effort in enumerate(data["efforts"])} for model, data in MODEL_DEFINITIONS.items()}
MODEL_POSITION = {model: index for index, model in enumerate(MODEL_ORDER)}
SPARK_BOOTSTRAP_FAMILIES = {"tiny_text", "tiny_code", "command_generation"}
SPARK_LOW_PAIR = (SPARK_MODEL, "low")
NORMAL_ADAPTIVE_MODELS = list(ACTIVE_MODEL_ORDER)
NORMAL_ADAPTIVE_LADDER = [(model, effort) for model in NORMAL_ADAPTIVE_MODELS for effort in MODEL_DEFINITIONS[model]["efforts"]]
# Retained only so the legacy local-history reader can parse old records.
LEARNING_FIELDS = ("task_family", "artifact", "scope", "ambiguity", "modality", "risk", "complexity", "execution_domain")

EXECUTION_DOMAIN_REGISTRY_VERSION = 1
EXECUTION_DOMAIN_REGISTRY_DEFAULT = "general"
EXECUTION_DOMAIN_REGISTRY_LEGACY = "code_unspecified"

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
        "display_name": "C#",
        "kind": "code",
        "language_aliases": ["csharp", "c#"],
        "owner_skill": "code-skill",
        "owner_enforced": True,
        "spark_first": True,
        "reference_path": "code-skill/references/csharp-rules.md",
        "active": True,
        "history_only": False,
    },
    "unity_csharp": {
        "display_name": "Unity C#",
        "kind": "code",
        "language_aliases": ["unity_csharp", "unity-csharp", "unitycsharp"],
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
PROFILE_PRESETS = {
    "general-answer-easy": {"task_family": "direct", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-luna|medium", "hard_floor": "gpt-5.6-luna|low"},
    "summary-easy": {"task_family": "document", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.6-luna|low"},
    "analysis-complex": {"task_family": "grounded", "artifact": "report", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|high", "hard_floor": "gpt-5.6-luna|low"},
    "spreadsheet-easy": {"task_family": "data", "artifact": "document", "scope": "single", "ambiguity": "low", "modality": "mixed", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|low", "hard_floor": "gpt-5.6-luna|low"},
    "spreadsheet-complex": {"task_family": "data", "artifact": "document", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|high", "hard_floor": "gpt-5.6-luna|low"},
    "document-easy": {"task_family": "document", "artifact": "document", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-luna|medium", "hard_floor": "gpt-5.6-luna|low"},
    "document-complex": {"task_family": "document", "artifact": "document", "scope": "multi", "ambiguity": "medium", "modality": "mixed", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|high", "hard_floor": "gpt-5.6-luna|low"},
    "integration-complex": {"task_family": "integration", "artifact": "patch", "scope": "project", "ambiguity": "high", "modality": "mixed", "risk": "medium", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-sol|high", "hard_floor": "gpt-5.6-luna|low"},
    "grounded-repository-answer-easy": {"task_family": "grounded", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|medium", "hard_floor": "gpt-5.6-luna|low"},
    "grounded-repository-answer-complex": {"task_family": "grounded", "artifact": "answer", "scope": "multi", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": None, "execution_domain": "general", "static_suggestion": "gpt-5.6-terra|high", "hard_floor": "gpt-5.6-luna|low"},
    "tiny-text": {"task_family": "tiny_text", "artifact": "answer", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": "general", "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.6-luna|low"},
    "command-generation": {"task_family": "command_generation", "artifact": "script", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": "general", "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.6-luna|low"},
    "tiny-code": {"task_family": "tiny_code", "artifact": "patch", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, "static_suggestion": "gpt-5.6-luna|low", "hard_floor": "gpt-5.6-luna|low"},
    "code-easy": {"task_family": "code", "artifact": "patch", "scope": "single", "ambiguity": "low", "modality": "text", "risk": "low", "complexity": "easy", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, "static_suggestion": "gpt-5.6-terra|medium", "hard_floor": "gpt-5.6-luna|low"},
    "code-complex": {"task_family": "code", "artifact": "patch", "scope": "multi", "ambiguity": "medium", "modality": "text", "risk": "low", "complexity": "complex", "verification_shape": "real", "owning_skill": "code-skill", "execution_domain": None, "static_suggestion": "gpt-5.6-terra|high", "hard_floor": "gpt-5.6-luna|low"},
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
        if reference.is_absolute():
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
    _ensure_supported_pair(model, effort)
    return f"{model}|{effort}"


def parse_model_effort_pair(value):
    if not isinstance(value, str):
        raise ValueError("model|effort pair must be a string")
    value = value.strip()
    if value.count("|") != 1:
        raise ValueError("model|effort pair must be separated by one |")
    model, effort = (part.strip() for part in value.split("|", 1))
    _ensure_supported_pair(model, effort)
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


def spark_first_pair(task_type, modality="text", operation="work", complexity="easy"):
    if not SPARK_FIRST_CONFIG.get("enabled"):
        return None
    if task_type not in set(SPARK_FIRST_CONFIG["eligible_task_types"]):
        return None
    if modality not in set(SPARK_FIRST_CONFIG["eligible_modalities"]):
        return None
    if operation in set(SPARK_FIRST_CONFIG["excluded_operations"]):
        return None
    effort = SPARK_FIRST_CONFIG["effort_by_complexity"].get(complexity)
    return (SPARK_MODEL, effort) if effort in SPARK_FIRST_CONFIG["adaptive_efforts"] else None


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
        "ladder_direction": MODEL_CAPABILITY_CONFIG["ladder_direction"],
        "policy": dict(ADAPTIVE_POLICY),
        "spark_first": dict(SPARK_FIRST_CONFIG),
        "private_learning_contract": dict(MODEL_CAPABILITY_CONFIG["private_learning_contract"]),
        "default_cold_start": MODEL_CAPABILITY_CONFIG["default_cold_start"],
        "cold_start_defaults": {key: dict(value) for key, value in MODEL_CAPABILITY_CONFIG["cold_start_defaults"].items()},
        "effort_order": list(MODEL_EFFORT_ORDER),
        "effort_guidance": dict(MODEL_CAPABILITY_CONFIG["effort_guidance"]),
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
    if set(ACTIVE_MODEL_ORDER) != set(ACTIVE_MODEL_EFFORTS):
        raise ValueError("shared active model registry is inconsistent")
    minimum_pair = parse_pair(ADAPTIVE_POLICY["minimum_pair"])
    if minimum_pair != NORMAL_ADAPTIVE_LADDER[0]:
        raise ValueError("shared minimum pair must be the weakest active ladder pair")
    if any(not model.startswith("gpt-5.6-") for model, _ in NORMAL_ADAPTIVE_LADDER):
        raise ValueError("active adaptive ladder must contain only GPT-5.6 models")
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

#!/usr/bin/env python3
"""Single source of truth for model routing metadata used by task-analyze-skill."""

MODEL_DEFINITIONS = {
    "gpt-5.3-codex-spark": {
        "efforts": ["low", "medium", "high", "xhigh"],
    },
    "gpt-5.6-luna": {
        "efforts": ["low", "medium", "high", "xhigh", "max"],
    },
    "gpt-5.6-terra": {
        "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
    "gpt-5.6-sol": {
        "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"],
    },
}

MODEL_ORDER = list(MODEL_DEFINITIONS.keys())
MODEL_EFFORT_ORDER = ["low", "medium", "high", "xhigh", "max", "ultra"]
MODEL_EFFORTS = {model: set(data["efforts"]) for model, data in MODEL_DEFINITIONS.items()}

MODEL_EFFORT_INDEX = {model: {effort: index for index, effort in enumerate(data["efforts"])} for model, data in MODEL_DEFINITIONS.items()}
MODEL_POSITION = {model: index for index, model in enumerate(MODEL_ORDER)}

EXECUTION_DOMAINS = {
    "general": {
        "owner_skill": "workflow-skill",
        "spark_first": False,
        "reference_path": "task-analyze-skill/references/model-selection.md",
    },
    "python": {
        "owner_skill": "code-skill",
        "spark_first": True,
        "reference_path": "code-skill/references/python-rules.md",
    },
    "csharp": {
        "owner_skill": "code-skill",
        "spark_first": True,
        "reference_path": "code-skill/references/unity-csharp-rules.md",
    },
    "unity_csharp": {
        "owner_skill": "code-skill",
        "spark_first": True,
        "reference_path": "code-skill/references/unity-csharp-rules.md",
    },
    "code_unspecified": {
        "owner_skill": "code-skill",
        "spark_first": True,
        "reference_path": "code-skill/references/spark-small-code.md",
    },
}


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


def infer_execution_domain(owning_skill=None, task_family=None, explicit_domain=None):
    if explicit_domain is not None:
        if explicit_domain not in EXECUTION_DOMAINS:
            raise ValueError(f"unknown execution domain {explicit_domain}")
        return explicit_domain
    if owning_skill == "code-skill":
        return "code_unspecified"
    if task_family in {"code", "tiny_code"}:
        return "code_unspecified"
    return "general"

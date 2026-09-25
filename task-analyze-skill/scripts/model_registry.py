#!/usr/bin/env python3
"""Build and maintain the shared model registry from the Codex model catalog."""

import hashlib
import json
import os
import string
import tempfile
from pathlib import Path


REGISTRY_SCHEMA_VERSION = 2
REGISTRY_ID = "dynamic-codex-model-capability-ladder"
CANONICAL_EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max", "ultra")
ACTIVE_MODEL_IDS = ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")
DEFAULT_MODELS_CACHE_PATH = Path.home() / ".codex" / "models_cache.json"
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"
TASK_TYPES = ("question", "summary", "spreadsheet", "document", "code", "debug", "integration", "prompt", "script", "visual", "normal-script-update", "code-design", "finding-bugs", "documentation-instructions")
MODEL_SWITCH_CATEGORIES = ("normal-script-update", "code-design", "finding-bugs", "tests-verification", "documentation-instructions", "general-work")
COMPLEXITY_BANDS = ({"id": "small", "minimum": 0, "maximum": 24}, {"id": "standard", "minimum": 25, "maximum": 49}, {"id": "complex", "minimum": 50, "maximum": 74}, {"id": "advanced", "minimum": 75, "maximum": 100})
SEMANTIC_MODEL_FIELDS = ("slug", "display_name", "description", "default_reasoning_level", "visibility", "supported_in_api", "priority", "additional_speed_tiers", "input_modalities", "context_window")


def _selected_catalog_models(catalog):
    visible_models = [
        model
        for model in catalog["models"]
        if isinstance(model, dict)
        and model.get("visibility") == "list"
        and isinstance(model.get("supported_reasoning_levels"), list)
        and model["supported_reasoning_levels"]
        and isinstance(model.get("slug"), str)
        and model.get("slug")
        and not isinstance(model.get("priority"), bool)
        and isinstance(model.get("priority"), (int, float))
    ]
    return [model for model in visible_models if model["slug"] in ACTIVE_MODEL_IDS]


def semantic_catalog_sha256(catalog):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("client_version"), str) or not isinstance(catalog.get("models"), list):
        raise ValueError("Codex model catalog is incomplete")
    semantic_models = []
    for model in _selected_catalog_models(catalog):
        if not isinstance(model, dict):
            semantic_models.append(model)
            continue
        supported_levels = model.get("supported_reasoning_levels")
        supported_efforts = [level.get("effort") if isinstance(level, dict) else None for level in supported_levels] if isinstance(supported_levels, list) else supported_levels
        semantic_models.append({**{field: model.get(field) for field in SEMANTIC_MODEL_FIELDS}, "supported_reasoning_efforts": supported_efforts})
    semantic_models.sort(key=lambda model: json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    semantic_catalog = {"client_version": catalog["client_version"], "models": semantic_models}
    canonical_bytes = json.dumps(semantic_catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def load_catalog(models_cache_path=DEFAULT_MODELS_CACHE_PATH):
    models_cache_path = Path(models_cache_path).expanduser().resolve()
    catalog_bytes = models_cache_path.read_bytes()
    catalog = json.loads(catalog_bytes.decode("utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("client_version"), str) or not isinstance(catalog.get("fetched_at"), str) or not isinstance(catalog.get("models"), list):
        raise ValueError("Codex model catalog is incomplete")
    return catalog, semantic_catalog_sha256(catalog)


def _supported_efforts(model, effort_order):
    supported_levels = model.get("supported_reasoning_levels")
    if not isinstance(supported_levels, list) or not supported_levels:
        return []
    efforts = []
    for level in supported_levels:
        effort = level.get("effort") if isinstance(level, dict) else None
        if isinstance(effort, str) and effort and effort not in efforts:
            efforts.append(effort)
    return [effort for effort in effort_order if effort in efforts]


def _catalog_effort_order(models):
    observed = []
    for model in models:
        for level in model.get("supported_reasoning_levels", []):
            effort = level.get("effort") if isinstance(level, dict) else None
            if isinstance(effort, str) and effort and effort not in observed:
                observed.append(effort)
    canonical = [effort for effort in CANONICAL_EFFORT_ORDER if effort in observed]
    return canonical + sorted(effort for effort in observed if effort not in CANONICAL_EFFORT_ORDER)


def _preferred_effort(efforts, preferred):
    return preferred if preferred in efforts else efforts[-1]


def _model_metadata(model, effort_order):
    efforts = _supported_efforts(model, effort_order)
    default_effort = model.get("default_reasoning_level")
    if default_effort not in efforts:
        default_effort = _preferred_effort(efforts, "medium")
    return {"id": model["slug"], "display_name": model.get("display_name", model["slug"]), "provider_priority": model["priority"], "provider_positioning": model.get("description", ""), "supported_in_api": bool(model.get("supported_in_api")), "input_modalities": list(model.get("input_modalities", [])), "context_window": model.get("context_window"), "codex_efforts": efforts, "default_effort": default_effort, "additional_speed_tiers": list(model.get("additional_speed_tiers", []))}


def _model_row(model, rank, effort_order, role_models):
    metadata = _model_metadata(model, effort_order)
    roles = [role for role, slug in role_models.items() if slug == model["slug"]]
    return {**metadata, "capability_rank": rank, "capability_roles": roles}


def build_registry(catalog, catalog_sha256=None):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("client_version"), str) or not isinstance(catalog.get("fetched_at"), str) or not isinstance(catalog.get("models"), list):
        raise ValueError("Codex model catalog is incomplete")
    if catalog_sha256 is None:
        catalog_sha256 = semantic_catalog_sha256(catalog)
    visible_models = _selected_catalog_models(catalog)
    if {model["slug"] for model in visible_models} != set(ACTIVE_MODEL_IDS) or len(visible_models) != len(ACTIVE_MODEL_IDS):
        raise ValueError("Codex model catalog must provide Astra, Sol, and Luna")
    effort_order = _catalog_effort_order(visible_models)
    if not effort_order or any(not _supported_efforts(model, effort_order) for model in visible_models):
        raise ValueError("active Codex models require named supported reasoning levels")
    if any(effort not in CANONICAL_EFFORT_ORDER for effort in effort_order):
        raise ValueError("active Codex models expose an unsupported reasoning effort")
    models_by_slug = {model["slug"]: model for model in visible_models}
    quality_models = [models_by_slug[slug] for slug in ACTIVE_MODEL_IDS]
    role_models = {"weak": "gpt-6-luna", "balanced": "gpt-6-sol", "frontier": "gpt-6-astra"}
    model_rows = [_model_row(model, rank, effort_order, role_models) for rank, model in enumerate(quality_models, start=1)]
    catalog_models = [{**_model_metadata(model, effort_order), "catalog_role": "active_quality"} for model in sorted(visible_models, key=lambda row: row["priority"])]
    models_by_id = {model["id"]: model for model in model_rows}
    weak = models_by_id[role_models["weak"]]
    balanced = models_by_id[role_models["balanced"]]
    frontier = models_by_id[role_models["frontier"]]
    floor_pair = f"{weak['id']}|{weak['codex_efforts'][0]}"
    weak_default_pair = f"{weak['id']}|{weak['default_effort']}"
    balanced_default_pair = f"{balanced['id']}|{balanced['default_effort']}"
    balanced_complex_pair = f"{balanced['id']}|{_preferred_effort(balanced['codex_efforts'], 'high')}"
    frontier_complex_pair = f"{frontier['id']}|{_preferred_effort(frontier['codex_efforts'], 'high')}"
    cold_starts = {"question": {"easy": floor_pair, "complex": balanced_default_pair}, "summary": {"easy": floor_pair, "complex": balanced_default_pair}, "spreadsheet": {"easy": balanced_default_pair, "complex": balanced_complex_pair}, "document": {"easy": weak_default_pair, "complex": balanced_complex_pair}, "code": {"easy": balanced_default_pair, "complex": balanced_complex_pair}, "debug": {"easy": balanced_default_pair, "complex": frontier_complex_pair}, "integration": {"easy": balanced_complex_pair, "complex": frontier_complex_pair}, "prompt": {"easy": balanced_default_pair, "complex": frontier_complex_pair}, "visual": {"easy": balanced_default_pair, "complex": frontier_complex_pair}}
    cold_starts["script"] = cold_starts["code"]
    cold_starts["normal-script-update"] = cold_starts["code"]
    cold_starts["code-design"] = cold_starts["code"]
    cold_starts["finding-bugs"] = cold_starts["debug"]
    cold_starts["documentation-instructions"] = cold_starts["document"]
    return {"schema_version": REGISTRY_SCHEMA_VERSION, "registry_id": REGISTRY_ID, "scope": "shared_non_personal", "source": {"models_cache": "~/.codex/models_cache.json", "client_version": catalog["client_version"], "fetched_at": catalog["fetched_at"], "catalog_sha256": catalog_sha256}, "active_family": {"id": "gpt-6", "numeric_version": [6], "selection": "requested_gpt6_variants", "model_count": 3}, "catalog_models": catalog_models, "ladder_direction": "weakest_to_strongest", "effort_order": effort_order, "complexity_scale": {"minimum": 0, "maximum": 100, "bands": list(COMPLEXITY_BANDS), "quality_complex_threshold": 50}, "role_models": role_models, "role_pairs": {"floor": floor_pair, "weak_default": weak_default_pair, "balanced_default": balanced_default_pair, "balanced_complex": balanced_complex_pair, "frontier_complex": frontier_complex_pair}, "policy": {"enabled": True, "quality_first": True, "downgrade_after_repeated_real_passes": True, "minimum_real_passes_before_downgrade": 2, "upgrade_after_quality_failure": True, "operational_failures_are_neutral": True, "freeze_lowest_verified_pair": True, "skill_governed_model_policy": "user_selected", "memory_model_policy": "user_selected", "adaptive_scope": "skill_independent_only", "priority_producer_first_text_code": False, "priority_producer_first_small_edits": False, "priority_producer_task_segments": False, "priority_producer_scheduled_sources": False, "priority_producer_scheduled_sources_only": False, "minimum_pair": floor_pair}, "priority_producer": None, "private_learning_contract": {"authority": "obsidian_vault", "vault_event_path_template": "AI Memory/Model Routing/events.jsonl", "projection_path_template": "Model Switch.md", "record_path_template": "<owner-routing>/<Category>.md", "native_wikilink_graph": True, "stable_categories": list(MODEL_SWITCH_CATEGORIES), "event_id_dedupe": True, "specificity_order": ["project_task", "module", "file", "symbol"], "fields_only": True, "hierarchy_notes": False, "legacy_local_json": "read_only_inactive"}, "default_cold_start": balanced_default_pair, "cold_start_defaults": cold_starts, "models": model_rows}


def validate_registry(registry):
    if not isinstance(registry, dict) or registry.get("schema_version") != REGISTRY_SCHEMA_VERSION or registry.get("registry_id") != REGISTRY_ID or registry.get("scope") != "shared_non_personal" or registry.get("ladder_direction") != "weakest_to_strongest":
        raise ValueError("model registry header is invalid")
    source = registry.get("source")
    if not isinstance(source, dict) or source.get("models_cache") != "~/.codex/models_cache.json" or not isinstance(source.get("client_version"), str) or not isinstance(source.get("fetched_at"), str) or not isinstance(source.get("catalog_sha256"), str) or len(source["catalog_sha256"]) != 64 or any(character not in string.hexdigits for character in source["catalog_sha256"]):
        raise ValueError("model registry source metadata is invalid")
    effort_order = registry.get("effort_order")
    models = registry.get("models")
    if not isinstance(effort_order, list) or not effort_order or effort_order != [effort for effort in CANONICAL_EFFORT_ORDER if effort in effort_order] or not isinstance(models, list) or len(models) != 3:
        raise ValueError("model registry ladder is incomplete")
    model_ids = []
    valid_pairs = []
    provider_priorities = []
    for rank, model in enumerate(models, start=1):
        if not isinstance(model, dict) or model.get("capability_rank") != rank or not isinstance(model.get("id"), str) or model["id"] in model_ids or isinstance(model.get("provider_priority"), bool) or not isinstance(model.get("provider_priority"), (int, float)):
            raise ValueError("model registry ranks and model ids must be unique and contiguous")
        efforts = model.get("codex_efforts")
        if not isinstance(efforts, list) or not efforts or efforts != [effort for effort in effort_order if effort in efforts]:
            raise ValueError(f"model registry efforts are invalid for {model.get('id')}")
        model_ids.append(model["id"])
        provider_priorities.append(model["provider_priority"])
        valid_pairs.extend(f"{model['id']}|{effort}" for effort in efforts)
    if model_ids != list(ACTIVE_MODEL_IDS) or provider_priorities != sorted(provider_priorities, reverse=True):
        raise ValueError("model registry provider priorities must be weakest-to-strongest")
    active_family = registry.get("active_family")
    if active_family != {"id": "gpt-6", "numeric_version": [6], "selection": "requested_gpt6_variants", "model_count": 3}:
        raise ValueError("model registry active family metadata is invalid")
    catalog_models = registry.get("catalog_models")
    if not isinstance(catalog_models, list) or len(catalog_models) != 3:
        raise ValueError("model registry catalog metadata is missing")
    catalog_ids = []
    catalog_priorities = []
    for model in catalog_models:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str) or model["id"] in catalog_ids or model.get("catalog_role") != "active_quality" or isinstance(model.get("provider_priority"), bool) or not isinstance(model.get("provider_priority"), (int, float)):
            raise ValueError("model registry catalog metadata is invalid")
        efforts = model.get("codex_efforts")
        if not isinstance(efforts, list) or not efforts or efforts != [effort for effort in effort_order if effort in efforts]:
            raise ValueError(f"model registry catalog efforts are invalid for {model.get('id')}")
        catalog_ids.append(model["id"])
        catalog_priorities.append(model["provider_priority"])
    if set(catalog_ids) != set(ACTIVE_MODEL_IDS) or catalog_priorities != sorted(catalog_priorities):
        raise ValueError("model registry catalog metadata must retain provider order")
    role_models = registry.get("role_models")
    if role_models != {"weak": "gpt-6-luna", "balanced": "gpt-6-sol", "frontier": "gpt-6-astra"}:
        raise ValueError("model registry role assignments are invalid")
    complexity_scale = registry.get("complexity_scale")
    expected_bands = list(COMPLEXITY_BANDS)
    if not isinstance(complexity_scale, dict) or complexity_scale.get("minimum") != 0 or complexity_scale.get("maximum") != 100 or complexity_scale.get("quality_complex_threshold") != 50 or complexity_scale.get("bands") != expected_bands:
        raise ValueError("model registry complexity scale is invalid")
    role_pairs = registry.get("role_pairs")
    if not isinstance(role_pairs, dict) or set(role_pairs) != {"floor", "weak_default", "balanced_default", "balanced_complex", "frontier_complex"} or any(pair not in valid_pairs for pair in role_pairs.values()) or role_pairs["floor"] != valid_pairs[0]:
        raise ValueError("model registry role pairs are invalid")
    policy = registry.get("policy")
    if not isinstance(policy, dict) or policy.get("enabled") is not True or policy.get("minimum_pair") != valid_pairs[0]:
        raise ValueError("model registry adaptive policy is invalid")
    if registry.get("default_cold_start") not in valid_pairs:
        raise ValueError("model registry default cold start is invalid")
    cold_starts = registry.get("cold_start_defaults")
    if not isinstance(cold_starts, dict) or set(cold_starts) != set(TASK_TYPES) or any(not isinstance(levels, dict) or set(levels) != {"easy", "complex"} or any(pair not in valid_pairs for pair in levels.values()) for levels in cold_starts.values()):
        raise ValueError("model registry cold starts are invalid")
    if registry.get("priority_producer") is not None or any(policy.get(key) is not False for key in ("priority_producer_first_text_code", "priority_producer_first_small_edits", "priority_producer_task_segments", "priority_producer_scheduled_sources", "priority_producer_scheduled_sources_only")):
        raise ValueError("model registry priority producer admission is inconsistent")
    if policy.get("downgrade_after_repeated_real_passes") is not True or policy.get("minimum_real_passes_before_downgrade") != 2 or policy.get("upgrade_after_quality_failure") is not True:
        raise ValueError("model registry adaptive learning policy is invalid")
    private_contract = registry.get("private_learning_contract")
    if not isinstance(private_contract, dict) or private_contract.get("authority") != "obsidian_vault" or private_contract.get("vault_event_path_template") != "AI Memory/Model Routing/events.jsonl" or private_contract.get("projection_path_template") != "Model Switch.md" or private_contract.get("record_path_template") != "<owner-routing>/<Category>.md" or private_contract.get("native_wikilink_graph") is not True or private_contract.get("stable_categories") != list(MODEL_SWITCH_CATEGORIES) or private_contract.get("event_id_dedupe") is not True or private_contract.get("specificity_order") != ["project_task", "module", "file", "symbol"] or private_contract.get("fields_only") is not True or private_contract.get("hierarchy_notes") is not False or private_contract.get("legacy_local_json") != "read_only_inactive":
        raise ValueError("model registry private learning contract is invalid")
    return registry


def is_valid_registry(registry):
    try:
        validate_registry(registry)
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _registry_without_fetched_at(registry):
    source = {key: value for key, value in registry["source"].items() if key != "fetched_at"}
    return {**registry, "source": source}


def registry_matches_catalog(registry, catalog_sha256, desired_registry=None):
    if not is_valid_registry(registry) or registry["source"]["catalog_sha256"] != catalog_sha256:
        return False
    if desired_registry is None:
        return True
    return is_valid_registry(desired_registry) and desired_registry["source"]["catalog_sha256"] == catalog_sha256 and _registry_without_fetched_at(registry) == _registry_without_fetched_at(desired_registry)


def load_registry(registry_path=DEFAULT_REGISTRY_PATH):
    registry_path = Path(registry_path).expanduser().resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return validate_registry(registry)


def atomic_write_registry(registry_path, registry):
    registry_path = Path(registry_path).expanduser().resolve()
    validate_registry(registry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{registry_path.name}.", suffix=".tmp", dir=registry_path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(registry, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, registry_path.stat().st_mode & 0o777 if registry_path.exists() else 0o644)
        os.replace(temporary_path, registry_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def ensure_registry(registry_path=DEFAULT_REGISTRY_PATH, models_cache_path=DEFAULT_MODELS_CACHE_PATH):
    registry_path = Path(registry_path).expanduser().resolve()
    if registry_path.exists():
        return {"status": "loaded", "registry": load_registry(registry_path)}
    try:
        catalog, catalog_sha256 = load_catalog(models_cache_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"Codex model catalog is unavailable and the saved model registry is missing: {error}") from error
    registry = build_registry(catalog, catalog_sha256)
    atomic_write_registry(registry_path, registry)
    return {"status": "generated", "registry": registry}


def refresh_registry(registry_path=DEFAULT_REGISTRY_PATH, models_cache_path=DEFAULT_MODELS_CACHE_PATH):
    registry_path = Path(registry_path).expanduser().resolve()
    existing_registry = None
    if registry_path.exists():
        try:
            existing_registry = load_registry(registry_path)
        except (KeyError, OSError, TypeError, json.JSONDecodeError, ValueError):
            existing_registry = None
    try:
        catalog, catalog_sha256 = load_catalog(models_cache_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        if existing_registry is not None:
            return {"status": "retained", "registry": existing_registry, "catalog_error": str(error)}
        raise RuntimeError(f"Codex model catalog is unavailable and no valid model registry exists: {error}") from error
    desired_registry = build_registry(catalog, catalog_sha256)
    if registry_matches_catalog(existing_registry, catalog_sha256, desired_registry):
        return {"status": "current", "registry": existing_registry}
    status = "refreshed" if registry_path.exists() else "generated"
    atomic_write_registry(registry_path, desired_registry)
    return {"status": status, "registry": desired_registry}

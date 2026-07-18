#!/usr/bin/env python3
"""Project-scoped adaptive model memory stored only as Obsidian Markdown."""

import argparse
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from tempfile import mkstemp

try:
    import project_change_memory
except ModuleNotFoundError:
    import importlib.util

    _memory_path = Path(__file__).with_name("project_change_memory.py")
    _memory_spec = importlib.util.spec_from_file_location("project_change_memory", _memory_path)
    project_change_memory = importlib.util.module_from_spec(_memory_spec)
    _memory_spec.loader.exec_module(project_change_memory)

try:
    import model_registry
except ModuleNotFoundError:
    import importlib.util

    _registry_path = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "scripts" / "model_registry.py"
    _registry_spec = importlib.util.spec_from_file_location("model_registry", _registry_path)
    model_registry = importlib.util.module_from_spec(_registry_spec)
    _registry_spec.loader.exec_module(model_registry)


SCHEMA_VERSION = 1
MIN_REAL_PASSES_BEFORE_DOWNGRADE = 2
DEFAULT_VAULT = project_change_memory.DEFAULT_VAULT
DEFAULT_LADDER = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "assets" / "model-capability-ladder.json"
QUALITY_FAILURES = {"quality", "correctness"}
OPERATIONAL_FAILURES = {"availability", "timeout", "protocol", "telemetry", "execution", "receipt"}
FAILURE_CLASSES = {"none"} | QUALITY_FAILURES | OPERATIONAL_FAILURES
LEVEL_VALUES = {"low", "medium", "high"}
COMPLEXITY_VALUES = {"easy", "complex"}
MODALITY_VALUES = {"text", "mixed", "image"}
MODEL_SWITCH_CATEGORIES = (
    "normal-script-update",
    "code-design",
    "finding-bugs",
    "documentation-instructions",
    "tests-verification",
    "general-work",
)
MODEL_SWITCH_DIRECTIONS = (
    "initial",
    "upgrade",
    "downgrade",
    "freeze",
    "no_switch",
    "operational_fallback",
)
MODEL_SWITCH_CATEGORY_MARKER = "<!-- generated:model-switch-category -->"
FRONTMATTER_FIELDS = (
    "model_experience_schema",
    "record_id",
    "recorded_at",
    "project_name",
    "project_key",
    "project_owner",
    "task_type",
    "task_summary",
    "module",
    "file",
    "symbol",
    "code_kind",
    "operation",
    "modality",
    "complexity",
    "risk",
    "ambiguity",
    "model",
    "effort",
    "pair",
    "selected_pair",
    "prior_pair",
    "attempt_pair",
    "active_fallback_pair",
    "operational_failure_pairs",
    "real_status",
    "failure_class",
    "receipt_status",
    "model_match",
    "effort_match",
    "turn_completed",
    "trial",
    "selection_reason",
    "recommendation_state",
    "specificity",
    "matched_records",
    "success_pair",
    "failed_pair",
    "workload_prompt_sha256",
    "total_tokens",
    "process_ms",
    "receipt_sha256",
)


def _json_safe(value):
    if isinstance(value, Path):
        return value.expanduser().resolve().as_posix()
    if isinstance(value, dict):
        return {str(key): _json_safe(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(nested) for nested in value]
    return value


def _single_line(value, field, *, required=True, maximum=280):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not text:
        raise ValueError(f"{field} is required")
    if len(text) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return text


def _slug(value, field):
    text = _single_line(value, field, maximum=80).lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", text):
        raise ValueError(f"{field} must be a lowercase slug")
    return text


def _optional_relative_file(project_root, value):
    if not value:
        return ""
    root = Path(project_root).expanduser().resolve()
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        relative = candidate.resolve().relative_to(root)
    else:
        relative = PurePosixPath(candidate.as_posix())
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("file must be project-relative and inside project_root")
    return relative.as_posix()


def load_shared_ladder(path=DEFAULT_LADDER):
    try:
        resolved = Path(path).expanduser().resolve()
        if resolved.exists():
            payload = model_registry.load_registry(resolved)
        elif resolved == DEFAULT_LADDER.expanduser().resolve():
            payload = model_registry.ensure_registry(resolved)["registry"]
        else:
            payload = model_registry.load_registry(resolved)
        model_registry.validate_registry(payload)
    except (OSError, RuntimeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"shared model ladder is unreadable: {error}") from error
    pairs = []
    for row in payload["models"]:
        efforts = row["codex_efforts"]
        pairs.extend(f"{row['id']}|{effort}" for effort in efforts)
    return payload, pairs


def _query(project_root, task_type, module, file_value="", symbol="", code_kind="general", operation="work", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary=""):
    project = project_change_memory._project_identity(project_root)
    if modality not in MODALITY_VALUES or complexity not in COMPLEXITY_VALUES or risk not in LEVEL_VALUES or ambiguity not in LEVEL_VALUES:
        raise ValueError("modality, complexity, risk, or ambiguity is invalid")
    return {
        "project": project,
        "task_type": _slug(task_type, "task_type"),
        "task_summary": _single_line(task_summary, "task_summary", required=False),
        "module": _single_line(module, "module", maximum=160),
        "file": _optional_relative_file(project["root"], file_value),
        "symbol": _single_line(symbol, "symbol", required=False, maximum=180),
        "code_kind": _slug(code_kind, "code_kind"),
        "operation": _slug(operation, "operation"),
        "modality": modality,
        "complexity": complexity,
        "risk": risk,
        "ambiguity": ambiguity,
    }


def _project_switch_directory(vault_path, owner):
    if owner == "Global Codex Skills":
        return vault_path / "Skills"
    return vault_path / "Projects" / owner


def _memory_root_owner(vault_path, owner):
    if owner is None:
        return None
    return _project_switch_directory(vault_path, owner) / "Model Switch.md"


def _is_configured_owner(vault_path, owner):
    if vault_path is None or owner is None:
        return False
    return _project_switch_directory(vault_path, owner).is_dir()


def _memory_root(query, vault):
    vault_path = project_change_memory._resolve_vault(vault)
    if vault_path is None:
        return None, None
    owner = project_change_memory._registered_owner(query["project"]["root"])
    if owner is None:
        return vault_path, None
    return vault_path, _memory_root_owner(vault_path, owner)


def _project_switch_index(vault_path, owner):
    if owner == "Global Codex Skills":
        return None
    return _project_switch_directory(vault_path, owner) / "index.md"


def _ensure_model_switch_index_link(vault_path, owner, memory_root):
    index_path = _project_switch_index(vault_path, owner)
    if index_path is None or not index_path.exists():
        return
    target = _vault_relative_path(vault_path, memory_root).as_posix()
    line = f"- [[{target}]]"
    text = index_path.read_text(encoding="utf-8")
    if line not in text:
        index_path.write_text(text.rstrip() + "\n" + line + "\n", encoding="utf-8")


def _parse_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return None
    block = text.split("\n---\n", 1)[0][4:]
    record = {}
    for line in block.splitlines():
        if ": " not in line:
            return None
        key, raw = line.split(": ", 1)
        try:
            record[key] = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if record.get("model_experience_schema") != SCHEMA_VERSION:
        return None
    return record


def _read_project_records(memory_root):
    if memory_root is None or not memory_root.exists():
        return []
    if memory_root.is_file():
        records = []
        for raw in re.findall(r"<!-- model-experience: (.*?) -->", memory_root.read_text(encoding="utf-8"), flags=re.DOTALL):
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if record.get("model_experience_schema") == SCHEMA_VERSION:
                records.append(_json_safe(record))
        return records
    records = []
    for path in sorted((memory_root / "records").glob("*/*/*.md")):
        record = _parse_frontmatter(path)
        if record is not None:
            records.append(_json_safe(record))
    return records


def _scope_score(record, query):
    if record.get("task_type") != query["task_type"]:
        return None
    module_match = record.get("module") == query["module"]
    file_match = bool(query["file"] and module_match and record.get("file") == query["file"])
    symbol_match = bool(query["symbol"] and file_match and record.get("symbol") == query["symbol"])
    if symbol_match:
        scope_level = 4
    elif file_match:
        scope_level = 3
    elif module_match:
        scope_level = 2
    else:
        scope_level = 1
    score = scope_level * 1_000
    context_weights = {
        "code_kind": 16,
        "operation": 32,
        "modality": 64,
        "complexity": 8,
        "risk": 4,
        "ambiguity": 2,
    }
    for field, weight in context_weights.items():
        if query[field] and record.get(field) == query[field]:
            score += weight
    return scope_level, score


def _best_scope_records(records, query):
    scored = [(*scope_score, record) for record in records if (scope_score := _scope_score(record, query)) is not None]
    if not scored:
        return [], "project_task", 0
    best_scope = max(scope for scope, _, _ in scored)
    scoped = [(score, record) for scope, score, record in scored if scope == best_scope]
    best_score = max(score for score, _ in scoped)
    selected = [record for score, record in scoped if score == best_score]
    level = {1: "project_task", 2: "module", 3: "file", 4: "symbol"}[best_scope]
    return selected, level, best_score


def _cold_start(shared, query, pairs):
    levels = shared.get("cold_start_defaults", {}).get(query["task_type"], {})
    pair = levels.get(query["complexity"], shared["default_cold_start"])
    return pair if pair in pairs else shared["default_cold_start"]


def _quality_verdict(record):
    valid_receipt = record.get("receipt_status") == "pass" and record.get("turn_completed") is True and record.get("model_match") is True and record.get("effort_match") is True
    if not valid_receipt:
        return None
    if record.get("real_status") == "fail" and record.get("failure_class") in QUALITY_FAILURES:
        return "fail"
    if record.get("real_status") == "pass" and record.get("failure_class") == "none":
        return "pass"
    return None


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _cost_evidence(status, pairs, *, shared_hashes=None, scores=None):
    hashes = sorted(shared_hashes or [])
    digest = hashlib.sha256("\n".join(hashes).encode()).hexdigest() if hashes else None
    return {
        "status": status,
        "compared_pairs": list(pairs),
        "shared_cohort_count": len(hashes),
        "shared_cohort_digest": digest,
        "scores": {
            pair: {"median_total_tokens": score[0], "median_process_ms": score[1]}
            for pair, score in (scores or {}).items()
        },
    }


def _like_for_like_cost_scores(records, passing_pairs):
    candidates = list(passing_pairs)
    if len(candidates) < 2:
        return None, _cost_evidence("insufficient_pairs", candidates)
    grouped = {pair: {} for pair in candidates}
    for record in records:
        pair = record.get("pair")
        workload_hash = record.get("workload_prompt_sha256")
        if pair not in grouped or _quality_verdict(record) != "pass" or not isinstance(workload_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", workload_hash):
            continue
        total_tokens = record.get("total_tokens")
        process_ms = record.get("process_ms")
        grouped[pair].setdefault(workload_hash, []).append((total_tokens, process_ms))
    common_hashes = set(grouped[candidates[0]])
    for pair in candidates[1:]:
        common_hashes.intersection_update(grouped[pair])
    if not common_hashes:
        return None, _cost_evidence("no_common_workload", candidates)
    cohort_scores = {pair: [] for pair in candidates}
    for workload_hash in sorted(common_hashes):
        for pair in candidates:
            samples = grouped[pair][workload_hash]
            if any(
                isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0
                or isinstance(elapsed, bool) or not isinstance(elapsed, int) or elapsed < 0
                for tokens, elapsed in samples
            ):
                return None, _cost_evidence("incomplete_metrics", candidates, shared_hashes=common_hashes)
            cohort_scores[pair].append(
                (
                    _median([tokens for tokens, _ in samples]),
                    _median([elapsed for _, elapsed in samples]),
                )
            )
    scores = {
        pair: (
            _median([sample[0] for sample in samples]),
            _median([sample[1] for sample in samples]),
        )
        for pair, samples in cohort_scores.items()
    }
    return scores, _cost_evidence("like_for_like", candidates, shared_hashes=common_hashes, scores=scores)


def _active_recommendation(shared, pairs, query, records):
    verdicts = {}
    pass_counts = {pair: 0 for pair in pairs}
    quality_samples = 0
    for record in records:
        pair = record.get("pair")
        if pair not in pairs:
            continue
        verdict = _quality_verdict(record)
        if verdict is None:
            continue
        quality_samples += 1
        if verdict == "fail":
            verdicts[pair] = "fail"
        elif verdicts.get(pair) != "fail":
            verdicts[pair] = "pass"
            pass_counts[pair] += 1
    failed_pairs = [pair for pair, verdict in verdicts.items() if verdict == "fail"]
    failed_pair = max(failed_pairs, key=pairs.index) if failed_pairs else None
    passing_pairs = [pair for pair, verdict in verdicts.items() if verdict == "pass" and (failed_pair is None or pairs.index(pair) > pairs.index(failed_pair))]
    success_pair = min(passing_pairs, key=pairs.index) if passing_pairs else None
    cost_scores, cost_evidence = _like_for_like_cost_scores(records, passing_pairs)
    selected_pair = None
    trial = False
    state = "cold_start"
    reason = "shared_cold_start"
    if failed_pair is None and success_pair is None:
        selected_pair = _cold_start(shared, query, pairs)
    elif failed_pair is None:
        success_index = pairs.index(success_pair)
        if success_index == 0:
            selected_pair = min(passing_pairs, key=lambda pair: (cost_scores[pair][0], cost_scores[pair][1], pairs.index(pair))) if cost_scores else success_pair
            state = "frozen"
            reason = "receipt_cost_best_verified" if cost_scores else "verified_floor_retained"
        elif pass_counts[success_pair] < MIN_REAL_PASSES_BEFORE_DOWNGRADE:
            selected_pair = success_pair
            state = "collecting_evidence"
            reason = "real_pass_collecting_evidence"
        else:
            selected_pair = pairs[success_index - 1]
            trial = True
            state = "provisional"
            reason = "repeated_real_pass_one_rung_down"
    elif success_pair is None:
        failed_index = pairs.index(failed_pair)
        if failed_index + 1 < len(pairs):
            selected_pair = pairs[failed_index + 1]
            trial = True
            state = "quality_boundary"
            reason = "quality_failure_one_rung_up"
        else:
            state = "blocked"
            reason = "quality_boundary_exhausted"
    else:
        failed_index = pairs.index(failed_pair)
        success_index = pairs.index(success_pair)
        untested = [pair for pair in pairs[failed_index + 1:success_index] if pair not in verdicts]
        if untested:
            selected_pair = untested[0]
            trial = True
            state = "quality_boundary"
            reason = "quality_boundary_gap_trial"
        else:
            selected_pair = min(passing_pairs, key=lambda pair: (cost_scores[pair][0], cost_scores[pair][1], pairs.index(pair))) if cost_scores else success_pair
            state = "frozen"
            reason = "receipt_cost_best_verified" if cost_scores else "verified_quality_boundary"
    return {
        "selected_pair": selected_pair,
        "trial": trial,
        "reason": reason,
        "calibration_state": state,
        "success_model": success_pair,
        "failed_model": failed_pair,
        "quality_samples": quality_samples,
        "pass_counts": {pair: count for pair, count in pass_counts.items() if count},
        "minimum_passes_before_downgrade": MIN_REAL_PASSES_BEFORE_DOWNGRADE,
        "cost_evidence": cost_evidence,
    }


def _priority_producer_pair(shared, query):
    producer = shared.get("priority_producer")
    if not isinstance(producer, dict) or producer.get("enabled") is not True:
        return None
    if (
        query["task_type"] not in set(producer["eligible_task_types"])
        or query["modality"] not in set(producer["eligible_modalities"])
        or query["operation"] in set(producer["excluded_operations"])
    ):
        return None
    effort = producer["effort_by_complexity"].get(query["complexity"])
    if effort not in set(producer["adaptive_efforts"]):
        return None
    return f"{producer['id']}|{effort}"


def _operational_fallback_pair(selected_pair, pairs):
    if selected_pair not in pairs:
        return None
    selected_index = pairs.index(selected_pair)
    return pairs[selected_index + 1] if selected_index + 1 < len(pairs) else None


def recommend_model(project_root, task_type, module, *, file_value="", symbol="", code_kind="general", operation="work", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="", vault=None, ladder=DEFAULT_LADDER):
    shared, pairs = load_shared_ladder(ladder)
    query = _query(project_root, task_type, module, file_value, symbol, code_kind, operation, modality, complexity, risk, ambiguity, task_summary)
    vault_path, memory_root = _memory_root(query, vault)
    owner = project_change_memory._registered_owner(query["project"]["root"])
    memory_configured = _is_configured_owner(vault_path, owner)
    records = [record for record in _read_project_records(memory_root) if project_change_memory._record_matches_project(record, query["project"])]
    records, specificity, score = _best_scope_records(records, query)
    active = _active_recommendation(shared, pairs, query, records)
    selected_pair = active["selected_pair"]
    attempt_pair = selected_pair
    attempt_reason = active["reason"]
    attempt_state = active["calibration_state"]
    attempt_trial = active["trial"]
    operational_fallback_pair = _operational_fallback_pair(selected_pair, pairs)
    if attempt_pair is None:
        attempt_state = "blocked"
    attempt_model, attempt_effort = attempt_pair.split("|", 1) if attempt_pair else (None, None)
    selected_model, selected_effort = selected_pair.split("|", 1) if selected_pair else (None, None)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "obsidian_broad_model_switch",
        "memory_available": memory_configured,
        "shared_model_registry": shared["registry_id"],
        "project_key": query["project"]["key"],
        "task_type": query["task_type"],
        "module": query["module"],
        "file": query["file"],
        "symbol": query["symbol"],
        "code_kind": query["code_kind"],
        "operation": query["operation"],
        "modality": query["modality"],
        "specificity": specificity,
        "specificity_score": score,
        "matched_records": len(records),
        "quality_samples": active["quality_samples"],
        "selected_pair": selected_pair,
        "selected_model": selected_model,
        "selected_effort": selected_effort,
        "attempt_pair": attempt_pair,
        "attempt_model": attempt_model,
        "attempt_effort": attempt_effort,
        "active_fallback_pair": operational_fallback_pair,
        "priority_verdict": None,
        "priority_producer_scope": "scheduled_independent_sources_only",
        "trial": active["trial"],
        "reason": active["reason"],
        "calibration_state": active["calibration_state"],
        "attempt_trial": attempt_trial,
        "attempt_reason": attempt_reason,
        "attempt_calibration_state": attempt_state,
        "success_model": active["success_model"],
        "failed_model": active["failed_model"],
        "pass_counts": active["pass_counts"],
        "minimum_passes_before_downgrade": active["minimum_passes_before_downgrade"],
        "cost_evidence": active["cost_evidence"],
    }


def _receipt_pair(receipt):
    for key in ("executed_pair", "effective_pair", "resolved_pair", "requested_pair"):
        if isinstance(receipt.get(key), str):
            return receipt[key]
    model = receipt.get("effective_model") or receipt.get("resolved_model") or receipt.get("requested_model")
    effort = receipt.get("effective_effort") or receipt.get("resolved_effort") or receipt.get("requested_effort")
    return f"{model}|{effort}" if model and effort else None


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = mkstemp(prefix=f".{path.stem}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _vault_relative_path(vault_path, path):
    canonical_vault = Path(vault_path).expanduser().resolve()
    canonical_path = Path(path).expanduser().resolve()
    try:
        return canonical_path.relative_to(canonical_vault)
    except ValueError as error:
        raise ValueError(f"model experience path must stay inside the Obsidian vault: {canonical_path}") from error
def _task_category(record):
    task_type = str(record.get("task_type") or "").strip().lower()
    code_kind = str(record.get("code_kind") or "").strip().lower()
    operation = str(record.get("operation") or "").strip().lower()
    values = " ".join((task_type, code_kind, operation))
    task_type_tokens = set(re.split(r"[._-]+", task_type))
    if task_type_tokens & {"doc", "docs", "documentation", "instruction", "instructions", "instructional", "prompt", "prompts", "prompting"}:
        return "documentation-instructions"
    if any(term in values for term in ("test", "verify", "validation")):
        return "tests-verification"
    if any(term in values for term in ("document", "instruction", "prompt", "readme", "guide")):
        return "documentation-instructions"
    if any(term in values for term in ("bug", "debug", "find", "diagnos")):
        return "finding-bugs"
    if any(term in values for term in ("design", "architect", "plan")):
        return "code-design"
    if task_type == "script" or code_kind == "script" or operation in {"script_update", "script_edit"} or (operation in {"edit", "update", "implement", "fix"} and code_kind in {"python", "csharp", "code"}):
        return "normal-script-update"
    return "general-work"


def _switch_details(record):
    attempt_pair = record.get("attempt_pair") or None
    selected_pair = record.get("selected_pair") or record.get("active_fallback_pair") or record.get("pair") or None
    effective_pair = record.get("pair") or None
    prior_pair = record.get("prior_pair") or record.get("success_pair") or record.get("failed_pair") or None
    reason = record.get("selection_reason") or "unknown_selection_reason"
    state = record.get("recommendation_state") or "unknown_state"
    operational_failures = record.get("operational_failure_pairs") if isinstance(record.get("operational_failure_pairs"), list) else []
    if operational_failures and effective_pair and attempt_pair and effective_pair != attempt_pair:
        switch_direction = "operational_fallback"
        switch_reason = f"operational fallback after {', '.join(operational_failures)}; selection {reason}"
    elif prior_pair is None:
        switch_direction = "initial"
        switch_reason = reason
    elif "one_rung_down" in reason:
        switch_direction = "downgrade"
        switch_reason = reason
    elif "one_rung_up" in reason or "quality_failure" in reason:
        switch_direction = "upgrade"
        switch_reason = reason
    elif state == "frozen" or "retained" in reason or reason in {"verified_floor_retained", "verified_quality_boundary"}:
        switch_direction = "freeze"
        switch_reason = reason
    else:
        switch_direction = "no_switch"
        switch_reason = reason
    return {"prior_pair": prior_pair, "selected_pair": selected_pair, "effective_pair": effective_pair, "attempt_pair": attempt_pair, "switch_direction": switch_direction, "switch_reason": switch_reason}


def rebuild_model_switches(project_root, *, vault=None):
    project = project_change_memory._project_identity(project_root)
    vault_path = project_change_memory._resolve_vault(vault)
    if vault_path is None:
        return {"status": "unavailable", "written": False, "reason": "obsidian_vault_unavailable"}
    query = _query(project_root, "script", "general")
    _, broad_page = _memory_root(query, vault)
    if broad_page is not None and broad_page.exists():
        page_records = _read_project_records(broad_page)
        records = [record for record in page_records if project_change_memory._record_matches_project(record, project)]
        foreign_records = [record for record in page_records if not project_change_memory._record_matches_project(record, project)]
        project_record_count = len(records)
        heading = "# Model Switch\n\n"
        sections = {"normal-script-update": "Normal Script Update", "code-design": "Code Design", "finding-bugs": "Finding Bugs", "documentation-instructions": "Documentation and Instructions", "tests-verification": "Tests and Verification", "general-work": "General Work"}
        lines = [heading.rstrip(), "", "This page is the private adaptive-learning authority. Structured records are embedded below.", ""]
        for category, label in sections.items():
            lines.extend(["## " + label, "", "| Task type | Module | File / symbol | Model | Prior / selected / effective | Direction / reason | Receipt | Tokens / time | Ending |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
            for record in records:
                if _task_category(record) != category:
                    continue
                detail = _switch_details(record)
                lines.append(f"| {record.get('task_type','')} | {record.get('module','')} | {record.get('file','') or '—'} {record.get('symbol','')} | {record.get('model','')} / {record.get('effort','')} | {detail['prior_pair'] or '—'} / {detail['selected_pair'] or '—'} / {detail['effective_pair'] or '—'} | {detail['switch_direction']} / {detail['switch_reason']} | {record.get('receipt_sha256','')} | {record.get('total_tokens','—')} / {record.get('process_ms','—')} | {record.get('real_status','')} |")
                lines.append("<!-- model-experience: " + json.dumps(_json_safe(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + " -->")
            lines.append("")
        # Preserve unexpected records byte-semantically without displaying them
        # in another project's visible summary table.
        for record in foreign_records:
            lines.append("<!-- model-experience: " + json.dumps(_json_safe(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + " -->")
        _atomic_write(broad_page, "\n".join(lines).rstrip() + "\n")
        return {"status": "rebuilt", "written": True, "project_key": project["key"], "records": project_record_count, "page_records": len(page_records), "summary": _vault_relative_path(vault_path, broad_page).as_posix()}
    return {"status": "no-op", "written": False, "project_key": project["key"], "reason": "broad_model_switch_missing"}


def relink_project(project_root, *, vault=None):
    project = project_change_memory._project_identity(project_root)
    return {"status": "disabled", "written": False, "project_key": project["key"], "reason": "legacy_hierarchy_relink_disabled"}


def record_model_result(project_root, task_type, module, receipt_path, real_status, failure_class, *, file_value="", symbol="", code_kind="general", operation="work", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="", trial=False, vault=None, ladder=DEFAULT_LADDER, recorded_at=None, bound_receipt=None):
    shared, pairs = load_shared_ladder(ladder)
    query = _query(project_root, task_type, module, file_value, symbol, code_kind, operation, modality, complexity, risk, ambiguity, task_summary)
    if real_status not in {"pass", "fail"} or failure_class not in FAILURE_CLASSES:
        raise ValueError("Real status or failure class is invalid")
    receipt_path = Path(receipt_path).expanduser().resolve()
    receipt_bytes = receipt_path.read_bytes()
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    pair = _receipt_pair(receipt)
    priority_producer = shared.get("priority_producer")
    priority_pairs = {f"{priority_producer['id']}|{effort}" for effort in priority_producer["adaptive_efforts"]} if isinstance(priority_producer, dict) and priority_producer.get("enabled") is True else set()
    if pair not in set(pairs) | priority_pairs:
        raise ValueError("receipt pair is outside the shared active producer contract")
    valid_receipt = receipt.get("status") == "pass" and receipt.get("turn_completed") is True and receipt.get("model_match") is True and receipt.get("effort_match") is True
    historical_binding = isinstance(bound_receipt, dict)
    if historical_binding:
        if bound_receipt.get("receipt_sha256") != receipt_sha256 or bound_receipt.get("model_learning_context") != receipt.get("model_learning_context") or bound_receipt.get("executed_pair") not in {None, pair}:
            raise ValueError("bound producer receipt does not match its immutable lifecycle binding")
        matched_route_attempt = next((attempt for attempt in receipt.get("route_attempts", []) if isinstance(attempt, dict) and attempt.get("status") == "pass" and attempt.get("executed_pair") == pair and attempt.get("model_match") is True and attempt.get("effort_match") is True), None)
        if receipt.get("node_type") != "locked-route-node" or receipt.get("node_role") != "result-producer" or receipt.get("result_published") is not True or not matched_route_attempt:
            raise ValueError("bound producer receipt is missing locked-route execution evidence")
    if real_status == "pass" and (failure_class != "none" or not valid_receipt):
        raise ValueError("a Real pass requires a matched passing producer receipt and failure_class=none")
    if failure_class in QUALITY_FAILURES and (real_status != "fail" or not valid_receipt):
        raise ValueError("a quality failure requires Real=fail and a matched passing producer receipt")
    if failure_class in OPERATIONAL_FAILURES and real_status != "fail":
        raise ValueError("an operational failure requires Real=fail")
    vault_path, memory_root = _memory_root(query, vault)
    if vault_path is None:
        return {"status": "unavailable", "written": False, "reason": "obsidian_vault_unavailable"}
    if memory_root is None:
        return {"status": "no-op", "written": False, "reason": "unregistered_or_unknown_project_root"}
    owner = project_change_memory._registered_owner(query["project"]["root"])
    if not _is_configured_owner(vault_path, owner):
        return {
            "status": "no-op",
            "written": False,
            "reason": "unregistered_or_unknown_project_root",
        }
    duplicate = next(
        (
            record
            for record in _read_project_records(memory_root) if project_change_memory._record_matches_project(record, query["project"])
            if record.get("receipt_sha256") == receipt_sha256
            and record.get("real_status") == real_status
            and record.get("failure_class") == failure_class
        ),
        None,
    )
    if duplicate is not None:
        model_switch = rebuild_model_switches(project_root, vault=vault)
        return {"status": "duplicate", "written": True, "record_id": duplicate["record_id"], "project_key": query["project"]["key"], "shared_model_registry": shared["registry_id"], "model_switch": model_switch}
    recommendation = recommend_model(
        project_root,
        task_type,
        module,
        file_value=file_value,
        symbol=symbol,
        code_kind=code_kind,
        operation=operation,
        modality=modality,
        complexity=complexity,
        risk=risk,
        ambiguity=ambiguity,
        task_summary=task_summary,
        vault=vault,
        ladder=ladder,
    )
    priority_attempt_pair = receipt.get("priority_attempt_pair") or receipt.get("requested_pair")
    operational_failure_pairs = receipt.get("operational_failure_pairs") if isinstance(receipt.get("operational_failure_pairs"), list) else []
    operational_failure_pairs = [value for value in operational_failure_pairs if value in set(pairs) | priority_pairs]
    if valid_receipt and not historical_binding and recommendation.get("attempt_pair") != priority_attempt_pair:
        raise ValueError("receipt attempt does not match the current Obsidian recommendation")
    if valid_receipt and not historical_binding and pair not in {recommendation.get("attempt_pair"), recommendation.get("active_fallback_pair")}:
        raise ValueError("receipt result is outside the authorized priority/quality route")
    if valid_receipt and not historical_binding and pair != recommendation.get("attempt_pair") and recommendation.get("attempt_pair") not in operational_failure_pairs:
        raise ValueError("fallback receipt lacks the failed priority attempt")
    timestamp = recorded_at or datetime.now(timezone.utc)
    tokens = receipt.get("tokens") if isinstance(receipt.get("tokens"), dict) else {}
    workload_hash = receipt.get("workload_prompt_sha256")
    if not isinstance(workload_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", workload_hash):
        workload_hash = None
    base = {
        "model_experience_schema": SCHEMA_VERSION,
        "record_id": "",
        "recorded_at": timestamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "project_name": query["project"]["name"],
        "project_key": query["project"]["key"],
        "project_owner": owner,
        "task_type": query["task_type"],
        "task_summary": query["task_summary"],
        "module": query["module"],
        "file": query["file"],
        "symbol": query["symbol"],
        "code_kind": query["code_kind"],
        "operation": query["operation"],
        "modality": query["modality"],
        "complexity": query["complexity"],
        "risk": query["risk"],
        "ambiguity": query["ambiguity"],
        "model": pair.split("|", 1)[0],
        "effort": pair.split("|", 1)[1],
        "pair": pair,
        "selected_pair": receipt.get("selected_pair") or receipt.get("active_fallback_pair") or (pair if historical_binding else recommendation.get("selected_pair")),
        "prior_pair": receipt.get("prior_pair") or (recommendation.get("success_model") or recommendation.get("failed_model")),
        "attempt_pair": priority_attempt_pair,
        "active_fallback_pair": recommendation.get("active_fallback_pair"),
        "operational_failure_pairs": operational_failure_pairs,
        "real_status": real_status,
        "failure_class": failure_class,
        "receipt_status": "pass" if valid_receipt else "fail",
        "model_match": receipt.get("model_match") is True,
        "effort_match": receipt.get("effort_match") is True,
        "turn_completed": receipt.get("turn_completed") is True,
        "trial": receipt.get("trial") if historical_binding and isinstance(receipt.get("trial"), bool) else recommendation["attempt_trial"],
        "selection_reason": receipt.get("selection_reason") or ("bound_historical_receipt" if historical_binding else recommendation["attempt_reason"]),
        "recommendation_state": receipt.get("recommendation_state") or ("bound_historical_receipt" if historical_binding else recommendation["attempt_calibration_state"]),
        "specificity": recommendation["specificity"],
        "matched_records": recommendation["matched_records"],
        "success_pair": recommendation["success_model"],
        "failed_pair": recommendation["failed_model"],
        "workload_prompt_sha256": workload_hash,
        "total_tokens": tokens.get("total_tokens") if isinstance(tokens.get("total_tokens"), int) and tokens.get("total_tokens") >= 0 else None,
        "process_ms": receipt.get("process_elapsed_ms") if isinstance(receipt.get("process_elapsed_ms"), int) and receipt.get("process_elapsed_ms") >= 0 else None,
        "receipt_sha256": receipt_sha256,
    }
    base = _json_safe(base)
    fingerprint_payload = _json_safe({key: base[key] for key in FRONTMATTER_FIELDS if key not in {"record_id", "recorded_at"}})
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    base["record_id"] = f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{fingerprint[:12]}"
    lock_path = Path.home() / ".codex" / "project-change-memory" / ".model-experience.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        duplicate = next((record for record in _read_project_records(memory_root) if project_change_memory._record_matches_project(record, query["project"]) and record.get("receipt_sha256") == base["receipt_sha256"] and record.get("real_status") == real_status and record.get("failure_class") == failure_class), None)
        if duplicate is not None:
            model_switch = rebuild_model_switches(project_root, vault=vault)
            return {"status": "duplicate", "written": True, "record_id": duplicate["record_id"], "project_key": query["project"]["key"], "shared_model_registry": shared["registry_id"], "model_switch": model_switch}
        record_path = memory_root
        records = _read_project_records(record_path)
        records.append(_json_safe(base))
        _atomic_write(record_path, "# Model Switch\n\n" + "\n".join("<!-- model-experience: " + json.dumps(_json_safe(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + " -->" for record in records) + "\n")
        _ensure_model_switch_index_link(vault_path, owner, record_path)
        model_switch = rebuild_model_switches(project_root, vault=vault)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return {"status": "written", "written": True, "record_id": base["record_id"], "project_key": query["project"]["key"], "pair": pair, "real_status": real_status, "failure_class": failure_class, "shared_model_registry": shared["registry_id"], "obsidian_note": _vault_relative_path(vault_path, record_path).as_posix(), "model_switch": model_switch}


def memory_status(project_root=None, *, vault=None, ladder=DEFAULT_LADDER):
    shared, pairs = load_shared_ladder(ladder)
    vault_path = project_change_memory._resolve_vault(vault)
    priority_producer = shared.get("priority_producer")
    priority_pair_count = len(priority_producer["adaptive_efforts"]) if isinstance(priority_producer, dict) and priority_producer.get("enabled") is True else 0
    output = {"status": "ready" if vault_path else "unavailable", "authority": "obsidian_broad_model_switch", "shared_model_registry": shared["registry_id"], "active_pairs": len(pairs) + priority_pair_count, "active_quality_pairs": len(pairs), "priority_attempt_pairs": priority_pair_count, "priority_producer": priority_producer.get("id") if isinstance(priority_producer, dict) else None, "vault": str(vault_path) if vault_path else ""}
    if project_root and vault_path:
        project = project_change_memory._project_identity(project_root)
        owner = project_change_memory._registered_owner(project["root"])
        _, page = _memory_root(_query(project_root, "script", "general"), vault)
        memory_available = _is_configured_owner(vault_path, owner)
        if owner is None:
            reason = "unregistered_or_unknown_project_root"
        elif page is None:
            reason = "unconfigured_project_root"
        elif not page.exists():
            reason = "configured_broad_page_missing"
        else:
            reason = None
        output.update(
            {
                "project_key": project["key"],
                "memory_available": memory_available,
                "broad_page_owner": owner,
                "records": 0 if page is None else len(_read_project_records(page)),
                "page": "" if page is None else _vault_relative_path(vault_path, page).as_posix(),
                "reason": reason,
            }
        )
    return output


def _add_scope_arguments(parser, *, summary_required=False):
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--file", default="")
    parser.add_argument("--symbol", default="")
    parser.add_argument("--code-kind", default="general")
    parser.add_argument("--operation", default="work")
    parser.add_argument("--modality", choices=sorted(MODALITY_VALUES), default="text")
    parser.add_argument("--complexity", choices=sorted(COMPLEXITY_VALUES), default="easy")
    parser.add_argument("--risk", choices=sorted(LEVEL_VALUES), default="low")
    parser.add_argument("--ambiguity", choices=sorted(LEVEL_VALUES), default="low")
    parser.add_argument("--task-summary", required=summary_required, default="")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Read and write project-scoped adaptive model memory in Obsidian")
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--ladder", type=Path, default=DEFAULT_LADDER)
    commands = parser.add_subparsers(dest="command", required=True)
    recommend = commands.add_parser("recommend")
    _add_scope_arguments(recommend)
    record = commands.add_parser("record")
    _add_scope_arguments(record, summary_required=True)
    record.add_argument("--receipt", type=Path, required=True)
    record.add_argument("--real-status", choices=("pass", "fail"), required=True)
    record.add_argument("--failure-class", choices=sorted(FAILURE_CLASSES), default="none")
    record.add_argument("--trial", action="store_true")
    status = commands.add_parser("status")
    status.add_argument("--project-root", type=Path)
    relink = commands.add_parser("relink")
    relink.add_argument("--project-root", type=Path, required=True)
    rebuild = commands.add_parser("rebuild-model-switches")
    rebuild.add_argument("--project-root", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    common = {"vault": args.vault, "ladder": args.ladder}
    if args.command == "status":
        output = memory_status(args.project_root, **common)
    elif args.command == "relink":
        output = relink_project(args.project_root, vault=args.vault)
    elif args.command == "rebuild-model-switches":
        output = rebuild_model_switches(args.project_root, vault=args.vault)
    else:
        scope = {"file_value": args.file, "symbol": args.symbol, "code_kind": args.code_kind, "operation": args.operation, "modality": args.modality, "complexity": args.complexity, "risk": args.risk, "ambiguity": args.ambiguity, "task_summary": args.task_summary, **common}
        if args.command == "recommend":
            output = recommend_model(args.project_root, args.task_type, args.module, **scope)
        else:
            output = record_model_result(args.project_root, args.task_type, args.module, args.receipt, args.real_status, args.failure_class, trial=args.trial, **scope)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output.get("status") not in {"unavailable"} and output.get("calibration_state") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())

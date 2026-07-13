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


SCHEMA_VERSION = 1
DEFAULT_VAULT = project_change_memory.DEFAULT_VAULT
DEFAULT_LADDER = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "assets" / "model-capability-ladder.json"
QUALITY_FAILURES = {"quality", "correctness"}
OPERATIONAL_FAILURES = {"availability", "timeout", "protocol", "telemetry", "execution", "receipt"}
FAILURE_CLASSES = {"none"} | QUALITY_FAILURES | OPERATIONAL_FAILURES
LEVEL_VALUES = {"low", "medium", "high"}
COMPLEXITY_VALUES = {"easy", "complex"}
MODALITY_VALUES = {"text", "mixed", "image"}
FRONTMATTER_FIELDS = (
    "model_experience_schema",
    "record_id",
    "recorded_at",
    "project_name",
    "project_key",
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
        payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"shared model ladder is unreadable: {error}") from error
    models = payload.get("models") if isinstance(payload, dict) else None
    effort_order = payload.get("effort_order") if isinstance(payload, dict) else None
    if payload.get("schema_version") != 1 or payload.get("scope") != "shared_non_personal":
        raise ValueError("shared model ladder contract is invalid")
    if not isinstance(models, list) or not isinstance(effort_order, list):
        raise ValueError("shared model ladder is incomplete")
    pairs = []
    expected_rank = 1
    for row in models:
        if row.get("capability_rank") != expected_rank or not str(row.get("id", "")).startswith("gpt-5.6-"):
            raise ValueError("shared model capability order is invalid")
        efforts = row.get("codex_efforts")
        if not isinstance(efforts, list) or efforts != [effort for effort in effort_order if effort in efforts]:
            raise ValueError("shared model effort order is invalid")
        pairs.extend(f"{row['id']}|{effort}" for effort in efforts)
        expected_rank += 1
    if not pairs or payload.get("policy", {}).get("minimum_pair") != pairs[0]:
        raise ValueError("shared model floor is invalid")
    private_contract = payload.get("private_learning_contract")
    if (
        not isinstance(private_contract, dict)
        or private_contract.get("authority") != "obsidian_project_memory"
        or private_contract.get("path_template") != "Projects/<project-key>/ModelExperience"
        or private_contract.get("specificity_order") != ["project_task", "module", "file", "symbol"]
        or private_contract.get("legacy_local_json") != "read_only_inactive"
    ):
        raise ValueError("shared private-learning contract is invalid")
    valid_pairs = set(pairs)
    default_pair = payload.get("default_cold_start")
    if default_pair not in valid_pairs:
        raise ValueError("shared default cold start is invalid")
    cold_starts = payload.get("cold_start_defaults")
    if not isinstance(cold_starts, dict):
        raise ValueError("shared cold-start map is missing")
    for task_type, levels in cold_starts.items():
        if not isinstance(levels, dict) or any(pair not in valid_pairs for pair in levels.values()):
            raise ValueError(f"shared cold-start map is invalid for {task_type}")
    spark = payload.get("spark_first")
    if (
        not isinstance(spark, dict)
        or spark.get("enabled") is not True
        or spark.get("id") != "gpt-5.3-codex-spark"
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
        or not isinstance(adaptive_efforts, list)
        or any(effort not in spark_efforts for effort in adaptive_efforts)
        or set(effort_by_complexity or {}) != COMPLEXITY_VALUES
        or any(effort not in adaptive_efforts for effort in effort_by_complexity.values())
    ):
        raise ValueError("shared Spark effort contract is invalid")
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


def _memory_root(query, vault):
    vault_path = project_change_memory._resolve_vault(vault)
    if vault_path is None:
        return None, None
    return vault_path, vault_path / "Projects" / query["project"]["key"] / "ModelExperience"


def _frontmatter(record):
    lines = ["---"]
    for field in FRONTMATTER_FIELDS:
        lines.append(f"{field}: {json.dumps(record.get(field), ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


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
    records = []
    for path in sorted((memory_root / "records").glob("*/*/*.md")):
        record = _parse_frontmatter(path)
        if record is not None:
            record["_path"] = path
            records.append(record)
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


def _active_recommendation(shared, pairs, query, records):
    verdicts = {}
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
    failed_pairs = [pair for pair, verdict in verdicts.items() if verdict == "fail"]
    failed_pair = max(failed_pairs, key=pairs.index) if failed_pairs else None
    passing_pairs = [pair for pair, verdict in verdicts.items() if verdict == "pass" and (failed_pair is None or pairs.index(pair) > pairs.index(failed_pair))]
    success_pair = min(passing_pairs, key=pairs.index) if passing_pairs else None
    selected_pair = None
    trial = False
    state = "cold_start"
    reason = "shared_cold_start"
    if failed_pair is None and success_pair is None:
        selected_pair = _cold_start(shared, query, pairs)
    elif failed_pair is None:
        success_index = pairs.index(success_pair)
        if success_index == 0:
            selected_pair = success_pair
            state = "frozen"
            reason = "verified_floor_retained"
        else:
            selected_pair = pairs[success_index - 1]
            trial = True
            state = "provisional"
            reason = "real_pass_one_rung_down"
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
            selected_pair = success_pair
            state = "frozen"
            reason = "verified_quality_boundary"
    return {
        "selected_pair": selected_pair,
        "trial": trial,
        "reason": reason,
        "calibration_state": state,
        "success_model": success_pair,
        "failed_model": failed_pair,
        "quality_samples": quality_samples,
    }


def _spark_priority_pair(shared, query):
    spark = shared["spark_first"]
    if (
        query["task_type"] not in set(spark["eligible_task_types"])
        or query["modality"] not in set(spark["eligible_modalities"])
        or query["operation"] in set(spark["excluded_operations"])
    ):
        return None
    effort = spark["effort_by_complexity"].get(query["complexity"])
    if effort not in set(spark["adaptive_efforts"]):
        return None
    return f"{spark['id']}|{effort}"


def _latest_record(records):
    return max(records, key=lambda record: str(record.get("recorded_at") or ""), default=None)


def recommend_model(project_root, task_type, module, *, file_value="", symbol="", code_kind="general", operation="work", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="", vault=None, ladder=DEFAULT_LADDER):
    shared, pairs = load_shared_ladder(ladder)
    query = _query(project_root, task_type, module, file_value, symbol, code_kind, operation, modality, complexity, risk, ambiguity, task_summary)
    vault_path, memory_root = _memory_root(query, vault)
    records, specificity, score = _best_scope_records(_read_project_records(memory_root), query)
    active = _active_recommendation(shared, pairs, query, records)
    selected_pair = active["selected_pair"]
    attempt_pair = selected_pair
    attempt_reason = active["reason"]
    attempt_state = active["calibration_state"]
    attempt_trial = active["trial"]
    spark_pair = _spark_priority_pair(shared, query)
    spark_verdict = None
    if spark_pair:
        spark_verdicts = [_quality_verdict(record) for record in records if record.get("pair") == spark_pair]
        spark_verdict = "fail" if "fail" in spark_verdicts else "pass" if "pass" in spark_verdicts else None
        latest = _latest_record(records)
        latest_operational = latest.get("operational_failure_pairs") if isinstance(latest, dict) else []
        skip_for_repair = bool(
            isinstance(latest, dict)
            and latest.get("real_status") == "fail"
            and isinstance(latest_operational, list)
            and spark_pair in latest_operational
        )
        if spark_verdict == "pass":
            attempt_pair = spark_pair
            attempt_reason = "verified_spark_retained"
            attempt_state = "frozen"
            attempt_trial = False
        elif spark_verdict == "fail":
            attempt_reason = "spark_quality_failure_to_5_6"
            attempt_state = "quality_boundary" if selected_pair else "blocked"
            attempt_trial = selected_pair is not None
        elif skip_for_repair:
            attempt_reason = "spark_operational_failure_to_5_6_repair"
            attempt_state = "quality_boundary" if selected_pair else "blocked"
            attempt_trial = selected_pair is not None
        else:
            attempt_pair = spark_pair
            attempt_reason = "spark_first_text_code"
            attempt_state = "cold_start"
            attempt_trial = True
    if attempt_pair is None:
        attempt_state = "blocked"
    attempt_model, attempt_effort = attempt_pair.split("|", 1) if attempt_pair else (None, None)
    selected_model, selected_effort = selected_pair.split("|", 1) if selected_pair else (None, None)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "obsidian_project_memory",
        "memory_available": vault_path is not None,
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
        "quality_samples": active["quality_samples"] + (1 if spark_verdict else 0),
        "selected_pair": selected_pair,
        "selected_model": selected_model,
        "selected_effort": selected_effort,
        "attempt_pair": attempt_pair,
        "attempt_model": attempt_model,
        "attempt_effort": attempt_effort,
        "active_fallback_pair": selected_pair if attempt_pair and attempt_pair != selected_pair else None,
        "spark_verdict": spark_verdict,
        "trial": active["trial"],
        "reason": active["reason"],
        "calibration_state": active["calibration_state"],
        "attempt_trial": attempt_trial,
        "attempt_reason": attempt_reason,
        "attempt_calibration_state": attempt_state,
        "success_model": active["success_model"],
        "failed_model": active["failed_model"],
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


def _append_index(path, title, line):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else f"# {title}\n\n"
    if line not in text:
        _atomic_write(path, text.rstrip() + "\n\n" + line + "\n")


def _index_paths(memory_root, query):
    paths = [(memory_root / "index.md", f"{query['project']['name']} Model Experience")]
    paths.append((memory_root / "tasks" / f"{project_change_memory._slug(query['task_type'], 'task')}.md", f"Task: {query['task_type']}"))
    paths.append((memory_root / "modules" / f"{project_change_memory._slug(query['module'], 'module')}.md", f"Module: {query['module']}"))
    if query["file"]:
        parts = [project_change_memory._slug(part, "path") for part in PurePosixPath(query["file"]).parts]
        paths.append((memory_root / "files" / Path(*parts[:-1]) / f"{parts[-1]}.md", f"File: {query['file']}"))
    if query["symbol"]:
        symbol_hash = hashlib.sha256(f"{query['file']}::{query['symbol']}".encode()).hexdigest()[:10]
        symbol_name = project_change_memory._slug(query["symbol"], "symbol")
        paths.append((memory_root / "symbols" / project_change_memory._slug(query["module"], "module") / f"{symbol_name}-{symbol_hash}.md", f"Symbol: {query['symbol']}"))
    return paths


def record_model_result(project_root, task_type, module, receipt_path, real_status, failure_class, *, file_value="", symbol="", code_kind="general", operation="work", modality="text", complexity="easy", risk="low", ambiguity="low", task_summary="", trial=False, vault=None, ladder=DEFAULT_LADDER, recorded_at=None):
    shared, pairs = load_shared_ladder(ladder)
    query = _query(project_root, task_type, module, file_value, symbol, code_kind, operation, modality, complexity, risk, ambiguity, task_summary)
    if real_status not in {"pass", "fail"} or failure_class not in FAILURE_CLASSES:
        raise ValueError("Real status or failure class is invalid")
    receipt_path = Path(receipt_path).expanduser().resolve()
    receipt_bytes = receipt_path.read_bytes()
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    pair = _receipt_pair(receipt)
    spark = shared["spark_first"]
    spark_pairs = {f"{spark['id']}|{effort}" for effort in spark["adaptive_efforts"]}
    if pair not in set(pairs) | spark_pairs:
        raise ValueError("receipt pair is outside the shared active producer contract")
    valid_receipt = receipt.get("status") == "pass" and receipt.get("turn_completed") is True and receipt.get("model_match") is True and receipt.get("effort_match") is True
    if real_status == "pass" and (failure_class != "none" or not valid_receipt):
        raise ValueError("a Real pass requires a matched passing producer receipt and failure_class=none")
    if failure_class in QUALITY_FAILURES and (real_status != "fail" or not valid_receipt):
        raise ValueError("a quality failure requires Real=fail and a matched passing producer receipt")
    if failure_class in OPERATIONAL_FAILURES and real_status != "fail":
        raise ValueError("an operational failure requires Real=fail")
    vault_path, memory_root = _memory_root(query, vault)
    if vault_path is None:
        return {"status": "unavailable", "written": False, "reason": "obsidian_vault_unavailable"}
    duplicate = next(
        (
            record
            for record in _read_project_records(memory_root)
            if record.get("receipt_sha256") == receipt_sha256
            and record.get("real_status") == real_status
            and record.get("failure_class") == failure_class
        ),
        None,
    )
    if duplicate is not None:
        return {"status": "duplicate", "written": True, "record_id": duplicate["record_id"], "project_key": query["project"]["key"], "shared_model_registry": shared["registry_id"]}
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
    operational_failure_pairs = [value for value in operational_failure_pairs if value in set(pairs) | spark_pairs]
    if valid_receipt and recommendation.get("attempt_pair") != priority_attempt_pair:
        raise ValueError("receipt attempt does not match the current Obsidian recommendation")
    if valid_receipt and pair not in {recommendation.get("attempt_pair"), recommendation.get("active_fallback_pair")}:
        raise ValueError("receipt result is outside the authorized Spark/5.6 route")
    if valid_receipt and pair != recommendation.get("attempt_pair") and recommendation.get("attempt_pair") not in operational_failure_pairs:
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
        "attempt_pair": priority_attempt_pair,
        "active_fallback_pair": recommendation.get("active_fallback_pair"),
        "operational_failure_pairs": operational_failure_pairs,
        "real_status": real_status,
        "failure_class": failure_class,
        "receipt_status": "pass" if valid_receipt else "fail",
        "model_match": receipt.get("model_match") is True,
        "effort_match": receipt.get("effort_match") is True,
        "turn_completed": receipt.get("turn_completed") is True,
        "trial": recommendation["attempt_trial"],
        "selection_reason": recommendation["attempt_reason"],
        "recommendation_state": recommendation["attempt_calibration_state"],
        "specificity": recommendation["specificity"],
        "matched_records": recommendation["matched_records"],
        "success_pair": recommendation["success_model"],
        "failed_pair": recommendation["failed_model"],
        "workload_prompt_sha256": workload_hash,
        "total_tokens": tokens.get("total_tokens") if isinstance(tokens.get("total_tokens"), int) and tokens.get("total_tokens") >= 0 else None,
        "process_ms": receipt.get("process_elapsed_ms") if isinstance(receipt.get("process_elapsed_ms"), int) and receipt.get("process_elapsed_ms") >= 0 else None,
        "receipt_sha256": receipt_sha256,
    }
    fingerprint_payload = {key: base[key] for key in FRONTMATTER_FIELDS if key not in {"record_id", "recorded_at"}}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    base["record_id"] = f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{fingerprint[:12]}"
    lock_path = memory_root / ".model-experience.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        duplicate = next((record for record in _read_project_records(memory_root) if record.get("receipt_sha256") == base["receipt_sha256"] and record.get("real_status") == real_status and record.get("failure_class") == failure_class), None)
        if duplicate is not None:
            return {"status": "duplicate", "written": True, "record_id": duplicate["record_id"], "project_key": query["project"]["key"], "shared_model_registry": shared["registry_id"]}
        record_path = memory_root / "records" / timestamp.strftime("%Y") / timestamp.strftime("%m") / f"{base['record_id']}.md"
        body = (
            f"{_frontmatter(base)}\n\n"
            f"# {query['task_type']} — {query['module']}\n\n"
            f"- Scope: project `{query['project']['key']}`; module `{query['module']}`; file `{query['file'] or 'project/module'}`; symbol `{query['symbol'] or 'none'}`\n"
            f"- Work: `{query['operation']}` / `{query['code_kind']}` / `{query['modality']}` / `{query['complexity']}`\n"
            f"- Producer: attempt `{base['attempt_pair']}`; result `{pair}`; fallback `{base['active_fallback_pair']}`; operational failures `{base['operational_failure_pairs']}`\n"
            f"- Real: `{real_status}`; failure `{failure_class}`; trial `{str(base['trial']).lower()}`\n"
            f"- Selection: `{base['selection_reason']}`; state `{base['recommendation_state']}`; specificity `{base['specificity']}`; prior pass `{base['success_pair']}`; prior fail `{base['failed_pair']}`\n"
            f"- Summary: {query['task_summary'] or 'No sanitized summary supplied.'}\n"
            f"- Evidence: matched receipt `{base['receipt_status']}`; tokens `{base['total_tokens']}`; process ms `{base['process_ms']}`\n"
        )
        _atomic_write(record_path, body)
        relative_note = record_path.relative_to(vault_path).with_suffix("").as_posix()
        label = f"{base['recorded_at']} — {query['task_type']} / {query['module']} / {query['symbol'] or query['file'] or 'project'}"
        line = f"- [[{relative_note}|{label}]] — `{pair}` — Real `{real_status}` — `{failure_class}` — `{base['selection_reason']}`"
        for index_path, title in _index_paths(memory_root, query):
            _append_index(index_path, title, line)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return {"status": "written", "written": True, "record_id": base["record_id"], "project_key": query["project"]["key"], "pair": pair, "real_status": real_status, "failure_class": failure_class, "shared_model_registry": shared["registry_id"], "obsidian_note": record_path.relative_to(vault_path).as_posix()}


def memory_status(project_root=None, *, vault=None, ladder=DEFAULT_LADDER):
    shared, pairs = load_shared_ladder(ladder)
    vault_path = project_change_memory._resolve_vault(vault)
    spark = shared["spark_first"]
    output = {"status": "ready" if vault_path else "unavailable", "authority": "obsidian_project_memory", "shared_model_registry": shared["registry_id"], "active_pairs": len(pairs) + len(spark["adaptive_efforts"]), "active_5_6_pairs": len(pairs), "spark_attempt_pairs": len(spark["adaptive_efforts"]), "vault": str(vault_path) if vault_path else ""}
    if project_root and vault_path:
        project = project_change_memory._project_identity(project_root)
        root = vault_path / "Projects" / project["key"] / "ModelExperience"
        output.update({"project_key": project["key"], "records": len(_read_project_records(root))})
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
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    common = {"vault": args.vault, "ladder": args.ladder}
    if args.command == "status":
        output = memory_status(args.project_root, **common)
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

#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_VAULT = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "MyAILLM"
SEARCH_FOLDERS = ("TaskModelExperience", "Skills", "Projects", "AestheticTaste", "KnowledgeAreas", "DailyLog", "wiki")
STOP_WORDS = {"about", "after", "also", "and", "any", "for", "from", "have", "into", "like", "more", "need", "only", "other", "should", "task", "that", "the", "then", "this", "use", "user", "with"}
SENSITIVE_PATTERN = re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|api[_-]?key|password|token\s*=|-----BEGIN|/Users/|/home/|[A-Za-z]:\\)", re.IGNORECASE)
PAIR_PATTERN = re.compile(r"^(?:gpt-[a-zA-Z0-9.-]+)\|(?:low|medium|high|xhigh|max|ultra)$")


def resolve_vault(vault=None):
    selected = Path(vault).expanduser() if vault else Path(os.environ.get("CODEX_OBSIDIAN_VAULT", DEFAULT_VAULT)).expanduser()
    return selected.resolve() if selected.exists() and selected.is_dir() else None


def _query_terms(query):
    terms = []
    for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", query.lower()):
        if len(word) >= 3 and word not in STOP_WORDS and word not in terms:
            terms.append(word)
    return terms[:12]


def _bounded_text(path, limit=65536):
    try:
        size = path.stat().st_size
        with path.open(encoding="utf-8", errors="ignore") as handle:
            if size <= limit:
                return handle.read()
            head = handle.read(limit * 3 // 4)
            handle.seek(max(size - limit // 4, 0))
            return head + "\n" + handle.read(limit // 4)
    except OSError:
        return ""


def _path_priority(relative_path):
    root = relative_path.parts[0] if relative_path.parts else ""
    return {"TaskModelExperience": 100, "Skills": 30, "Projects": 30, "AestheticTaste": 26, "KnowledgeAreas": 26, "DailyLog": 12, "wiki": 8}.get(root, 0)


def _best_snippets(text, terms, limit=2):
    scored_lines = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line or SENSITIVE_PATTERN.search(line):
            continue
        lowered = line.lower()
        hits = sum(1 for term in terms if term in lowered)
        if hits:
            scored_lines.append((hits, -line_number, line[:280]))
    scored_lines.sort(reverse=True)
    return [line for _, _, line in scored_lines[:limit]]


def search_memory(query, vault=None, max_results=6, max_chars=3500):
    vault_path = resolve_vault(vault)
    if vault_path is None:
        return {"status": "unavailable", "provider": "none", "matches": [], "digest": ""}
    terms = _query_terms(query)
    if not terms:
        return {"status": "no_matches", "provider": "obsidian", "matches": [], "digest": ""}
    candidates = []
    for folder_name in SEARCH_FOLDERS:
        folder = vault_path / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*.md"))[:500]:
            relative_path = path.relative_to(vault_path)
            if SENSITIVE_PATTERN.search(relative_path.as_posix()):
                continue
            text = _bounded_text(path)
            lowered_text = text.lower()
            path_text = str(relative_path).lower()
            content_hits = sum(min(lowered_text.count(term), 5) for term in terms)
            path_hits = sum(1 for term in terms if term in path_text)
            unique_hits = sum(1 for term in terms if term in lowered_text or term in path_text)
            if not content_hits and not path_hits:
                continue
            if relative_path.parts[0] == "TaskModelExperience" and unique_hits < 2:
                continue
            snippets = _best_snippets(text, terms)
            score = _path_priority(relative_path) + unique_hits * 8 + path_hits * 12 + content_hits * 2
            candidates.append({"path": relative_path.as_posix(), "score": score, "snippets": snippets})
    candidates.sort(key=lambda match: (-match["score"], match["path"]))
    matches = candidates[:max(1, min(max_results, 12))]
    digest_lines = []
    used_chars = 0
    for match in matches:
        snippet = match["snippets"][0] if match["snippets"] else "Related page title/path match."
        line = f"[{match['path']}] {snippet}"
        if used_chars + len(line) > max_chars:
            break
        digest_lines.append(line)
        used_chars += len(line) + 1
    return {"status": "ok" if matches else "no_matches", "provider": "obsidian", "query_terms": terms, "matches": matches, "digest": "\n".join(digest_lines)}


def _sanitize_field(value, field_name, max_length=240):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if SENSITIVE_PATTERN.search(text):
        raise ValueError(f"{field_name} contains sensitive or path-like content")
    return text[:max_length]


def _validate_pair(value, field_name, allow_empty=True):
    text = _sanitize_field(value, field_name, 80)
    if not text and allow_empty:
        return ""
    if not PAIR_PATTERN.fullmatch(text):
        raise ValueError(f"{field_name} must be model|effort")
    return text


def initialize_task_model_experience(vault=None):
    vault_path = resolve_vault(vault)
    if vault_path is None:
        return {"status": "unavailable", "provider": "none"}
    root = vault_path / "TaskModelExperience"
    root.mkdir(parents=True, exist_ok=True)
    instruction_path = root / "instruction.md"
    index_path = root / "index.md"
    if not instruction_path.exists():
        instruction_path.write_text("# TaskModelExperience Instruction\n\nUse this folder for sanitized, human-readable model and effort switching lessons written after Ending Real Verify. New records contain only the durable Real pass/fail verdict; legacy Mini fields are read-only migration history. Search it during Task Analyze only when relevant. The private `model_experience.json` ledger remains the machine authority. Never store raw prompts, results, paths, thread IDs, receipt bodies, credentials, or secrets. If Obsidian is unavailable, skip search and recording without blocking the task.\n", encoding="utf-8")
    if not index_path.exists():
        index_path.write_text("# Task Model Experience\n\n## Purpose\n\nShare concise verified model-switch lessons with Task Analyze and other skills. Exact pair selection remains in the private adaptive-routing ledger.\n\n## Records\n\n", encoding="utf-8")
    return {"status": "ready", "provider": "obsidian", "root": "TaskModelExperience"}


def record_model_experience(task_summary, task_family, complexity, execution_domain, owning_skill, selected_pair, real_status, calibration_state, best_pair="", failed_pair="", previous_pair="", switch_direction="none", switch_reason="", total_tokens=None, process_ms=None, comparison_status="not_evaluated", vault=None, recorded_at=None):
    initialization = initialize_task_model_experience(vault)
    if initialization["status"] == "unavailable":
        return {"status": "unavailable", "provider": "none", "written": False}
    vault_path = resolve_vault(vault)
    timestamp = recorded_at or datetime.now(timezone.utc)
    summary = _sanitize_field(task_summary, "task_summary")
    real_verdict = _sanitize_field(real_status, "real_status", 20)
    if real_verdict not in {"pass", "fail"}:
        raise ValueError("real_status must be pass or fail")
    fields = {"task_family": _sanitize_field(task_family, "task_family", 80), "complexity": _sanitize_field(complexity, "complexity", 40), "execution_domain": _sanitize_field(execution_domain, "execution_domain", 80), "owning_skill": _sanitize_field(owning_skill, "owning_skill", 80), "selected_pair": _validate_pair(selected_pair, "selected_pair", False), "real_status": real_verdict, "calibration_state": _sanitize_field(calibration_state, "calibration_state", 40), "best_pair": _validate_pair(best_pair, "best_pair"), "failed_pair": _validate_pair(failed_pair, "failed_pair"), "previous_pair": _validate_pair(previous_pair, "previous_pair"), "switch_direction": _sanitize_field(switch_direction, "switch_direction", 40), "switch_reason": _sanitize_field(switch_reason, "switch_reason", 160), "comparison_status": _sanitize_field(comparison_status, "comparison_status", 60)}
    year_dir = vault_path / "TaskModelExperience" / timestamp.strftime("%Y")
    year_dir.mkdir(parents=True, exist_ok=True)
    record_path = year_dir / f"{timestamp.strftime('%Y-%m')}.md"
    if not record_path.exists():
        record_path.write_text(f"# Task Model Experience {timestamp.strftime('%Y-%m')}\n\n", encoding="utf-8")
    metric_text = f"tokens={int(total_tokens)}; process_ms={int(process_ms)}" if total_tokens is not None and process_ms is not None else "metrics=not-comparable-or-unavailable"
    entry = f"## {timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n- Task profile: {fields['task_family']} | {fields['complexity']} | {fields['execution_domain']} | {fields['owning_skill']}\n- Summary: {summary}\n- Producer: {fields['selected_pair']} | Real={fields['real_status']}\n- Switch: {fields['previous_pair'] or 'none'} -> {fields['selected_pair']} | {fields['switch_direction']} | {fields['switch_reason'] or 'no switch'}\n- Learned boundary: best={fields['best_pair'] or 'unverified'} | failed={fields['failed_pair'] or 'none'} | state={fields['calibration_state']}\n- Cost evidence: {fields['comparison_status']} | {metric_text}\n\n"
    with record_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    index_path = vault_path / "TaskModelExperience" / "index.md"
    relative_link = f"TaskModelExperience/{timestamp.strftime('%Y/%Y-%m')}"
    index_text = index_path.read_text(encoding="utf-8")
    link_line = f"- [[{relative_link}]]"
    if link_line not in index_text:
        with index_path.open("a", encoding="utf-8") as handle:
            handle.write(link_line + "\n")
    return {"status": "written", "provider": "obsidian", "written": True, "record": record_path.relative_to(vault_path).as_posix()}


def main():
    parser = argparse.ArgumentParser(description="Optional bounded Obsidian memory search and model-experience recorder")
    parser.add_argument("--vault", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--max-results", type=int, default=6)
    search_parser.add_argument("--max-chars", type=int, default=3500)
    subparsers.add_parser("init")
    record_parser = subparsers.add_parser("record-model")
    for name in ("task-summary", "task-family", "complexity", "execution-domain", "owning-skill", "selected-pair", "real-status", "calibration-state"):
        record_parser.add_argument(f"--{name}", required=True)
    for name in ("best-pair", "failed-pair", "previous-pair", "switch-direction", "switch-reason", "comparison-status"):
        record_parser.add_argument(f"--{name}", default="")
    record_parser.add_argument("--total-tokens", type=int)
    record_parser.add_argument("--process-ms", type=int)
    args = parser.parse_args()
    if args.command == "search":
        output = search_memory(args.query, args.vault, args.max_results, args.max_chars)
    elif args.command == "init":
        output = initialize_task_model_experience(args.vault)
    else:
        output = record_model_experience(args.task_summary, args.task_family, args.complexity, args.execution_domain, args.owning_skill, args.selected_pair, args.real_status, args.calibration_state, args.best_pair, args.failed_pair, args.previous_pair, args.switch_direction or "none", args.switch_reason, args.total_tokens, args.process_ms, args.comparison_status or "not_evaluated", args.vault)
    print(json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()

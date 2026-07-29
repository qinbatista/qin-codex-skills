#!/usr/bin/env python3
"""Resolve and validate Task Analyze disclosures on Windows, macOS, and Linux."""

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_model_registry():
    try:
        from model_registry import load_registry
        return load_registry
    except ModuleNotFoundError:
        registry_path = SCRIPT_DIR / "model_registry.py"
        registry_spec = importlib.util.spec_from_file_location("task_analyze_disclosure_registry", registry_path)
        registry_module = importlib.util.module_from_spec(registry_spec)
        sys.modules[registry_spec.name] = registry_module
        registry_spec.loader.exec_module(registry_module)
        return registry_module.load_registry


load_registry = _load_model_registry()
DISCLOSURE_EVIDENCE_LABELS = {"runtime receipt": ("runtime_receipt", "runtime_receipt"), "verified entry (no runtime receipt)": ("verified_entry", "UNVERIFIED (no runtime receipt)"), "task assignment (no runtime receipt)": ("task_assignment", "UNVERIFIED (no runtime receipt)"), "configured selection (no runtime receipt)": ("configured_selection", "UNVERIFIED (no runtime receipt)"), "unavailable": ("unavailable", "unavailable")}
DISCLOSURE_ROUTE_LABELS = {"upgrade": "upgrade", "downgrade": "downgrade", "frozen": "freeze", "no switch": "no_switch", "fallback": "operational_fallback"}
DISCLOSURE_PATTERN = re.compile(r"^Complexity:\s*(?P<score>\d+)/100 \((?P<band>small|standard|complex|advanced)\) · Model:\s*(?P<current_model>[^|\s]+)\|(?P<current_effort>[^|\s]+) · Route:\s*(?P<route_label>upgrade|downgrade|frozen|no switch|fallback)\s*$(?:\n^Model path:\s*(?P<model_path>[^\n]+?)\s*$)?\n^Evidence:\s*(?P<evidence_label>runtime receipt|verified entry \(no runtime receipt\)|task assignment \(no runtime receipt\)|configured selection \(no runtime receipt\)|unavailable)\s*$", re.MULTILINE)


def _allowed_pairs(registry=None):
    active_registry = registry or load_registry()
    active_model_ids = {pair.split("|", 1)[0] for pair in active_registry["role_pairs"].values()}
    allowed = {f"{model['id']}|{effort}" for model in active_registry["models"] if model["id"] in active_model_ids for effort in model["codex_efforts"]}
    priority_producer = active_registry.get("priority_producer")
    if isinstance(priority_producer, dict):
        allowed.update(f"{priority_producer['id']}|{effort}" for effort in priority_producer["codex_efforts"])
    return allowed


def _pair_from_fields(value, prefix):
    pair = value.get(f"{prefix}_pair") if isinstance(value, dict) else None
    if isinstance(pair, str) and "|" in pair:
        return pair
    model = value.get(f"{prefix}_model") if isinstance(value, dict) else None
    effort = value.get(f"{prefix}_effort") if isinstance(value, dict) else None
    return f"{model}|{effort}" if isinstance(model, str) and isinstance(effort, str) else None


def _receipt_pairs(runtime_receipt):
    if not isinstance(runtime_receipt, dict):
        return None
    has_receipt_identity = any(runtime_receipt.get(field) for field in ("requested_pair", "resolved_pair", "effective_pair", "requested_model", "resolved_model", "effective_model"))
    if not has_receipt_identity:
        return None
    effective_pair = _pair_from_fields(runtime_receipt, "effective")
    resolved_pair = _pair_from_fields(runtime_receipt, "resolved") or effective_pair
    requested_pair = _pair_from_fields(runtime_receipt, "requested") or resolved_pair
    if not all(isinstance(pair, str) for pair in (requested_pair, resolved_pair, effective_pair)):
        raise ValueError("runtime receipt model identity is incomplete")
    return requested_pair, resolved_pair, effective_pair


def resolve_disclosure_identity(runtime_receipt=None, entry_resolution=None, registry=None):
    receipt_pairs = _receipt_pairs(runtime_receipt)
    if receipt_pairs is not None:
        for pair in receipt_pairs:
            if pair not in _allowed_pairs(registry):
                raise ValueError(f"runtime receipt uses unsupported model pair: {pair}")
        return {"source": "runtime_receipt", "requested_pair": receipt_pairs[0], "resolved_pair": receipt_pairs[1], "effective_pair": receipt_pairs[2]}
    if not isinstance(entry_resolution, dict):
        raise ValueError("verified entry resolution is required when no runtime receipt exists")
    if entry_resolution.get("status") == "verified":
        model = entry_resolution.get("model")
        effort = entry_resolution.get("effort")
        entry_pair = f"{model}|{effort}" if isinstance(model, str) and isinstance(effort, str) else None
        if entry_pair not in _allowed_pairs(registry):
            raise ValueError(f"verified entry uses unsupported model pair: {entry_pair}")
        return {"source": "verified_entry", "requested_pair": entry_pair, "resolved_pair": entry_pair, "effective_pair": entry_pair}
    if entry_resolution.get("status") == "unavailable":
        return {"source": "unavailable", "requested_pair": "unknown|unknown", "resolved_pair": "unknown|unknown", "effective_pair": "unknown|unknown"}
    raise ValueError("entry resolver did not verify a model identity")


def _complexity_band(score):
    if 0 <= score <= 24:
        return "small"
    if score <= 49:
        return "standard"
    if score <= 74:
        return "complex"
    if score <= 100:
        return "advanced"
    raise ValueError("complexity score must be between 0 and 100")


def render_disclosure(complexity_score, runtime_receipt=None, entry_resolution=None, registry=None):
    identity = resolve_disclosure_identity(runtime_receipt, entry_resolution, registry)
    requested_pair = identity["requested_pair"]
    resolved_pair = identity["resolved_pair"]
    effective_pair = identity["effective_pair"]
    model_path = []
    if identity["source"] == "runtime_receipt":
        evidence_label = "runtime receipt"
        if requested_pair != resolved_pair or resolved_pair != effective_pair:
            route_label = "fallback"
            for pair in (requested_pair, resolved_pair, effective_pair):
                if not model_path or model_path[-1] != pair:
                    model_path.append(pair)
        else:
            switch_direction = runtime_receipt.get("switch_direction") if isinstance(runtime_receipt, dict) else None
            switch_change = runtime_receipt.get("switch_change") if isinstance(runtime_receipt, dict) else None
            switch_pairs = [pair.strip() for pair in switch_change.split("->")] if isinstance(switch_change, str) else []
            valid_switch = (
                switch_direction in {"upgrade", "downgrade"}
                and len(switch_pairs) >= 2
                and switch_pairs[-1] == effective_pair
                and all(pair in _allowed_pairs(registry) for pair in switch_pairs)
            )
            if valid_switch:
                route_label = switch_direction
                for pair in switch_pairs:
                    if not model_path or model_path[-1] != pair:
                        model_path.append(pair)
            else:
                route_label = "frozen" if switch_direction == "freeze" else "no switch"
    elif identity["source"] == "verified_entry":
        evidence_label = "verified entry (no runtime receipt)"
        route_label = "no switch"
    else:
        evidence_label = "unavailable"
        route_label = "no switch"
    lines = [f"Complexity: {complexity_score}/100 ({_complexity_band(complexity_score)}) · Model: {effective_pair} · Route: {route_label}"]
    if model_path:
        lines.append(f"Model path: {' -> '.join(model_path)}")
    lines.append(f"Evidence: {evidence_label}")
    return "\n".join(lines)


def normalize_result_disclosure(result_text, complexity_score, runtime_receipt=None, entry_resolution=None, registry=None):
    canonical = render_disclosure(
        complexity_score,
        runtime_receipt=runtime_receipt,
        entry_resolution=entry_resolution,
        registry=registry,
    )
    text = str(result_text or "").lstrip("\ufeff")
    compact_match = DISCLOSURE_PATTERN.search(text)
    if compact_match:
        return text[:compact_match.start()] + canonical + text[compact_match.end():]
    if text.startswith("Complexity:"):
        paragraph_end = text.find("\n\n")
        return canonical if paragraph_end < 0 else canonical + text[paragraph_end:]
    return canonical + ("\n\n" + text if text else "")


def validate_disclosure(disclosure_text, registry=None):
    match = DISCLOSURE_PATTERN.search(disclosure_text)
    if not match:
        return ["missing or invalid compact model disclosure"]
    values = match.groupdict()
    failures = []
    if int(values["score"]) > 100:
        failures.append("Complexity score must be between 0 and 100")
    expected_band = _complexity_band(int(values["score"])) if not failures else None
    if expected_band and values["band"] != expected_band:
        failures.append("Complexity band must match the score")
    current_pair = f"{values['current_model'].strip()}|{values['current_effort'].strip()}"
    evidence, evidence_level = DISCLOSURE_EVIDENCE_LABELS[values["evidence_label"]]
    route_change = DISCLOSURE_ROUTE_LABELS[values["route_label"]]
    model_path = values.get("model_path")
    path_pairs = [pair.strip() for pair in model_path.split("->")] if model_path else []
    known_pairs = (current_pair, *path_pairs)
    if "unknown|unknown" in known_pairs:
        if any(pair != "unknown|unknown" for pair in known_pairs) or evidence != "unavailable" or evidence_level != "unavailable":
            failures.append("unknown | unknown is valid only when the resolver explicitly reports unavailable")
    else:
        allowed_pairs = _allowed_pairs(registry)
        unsupported_pairs = [pair for pair in known_pairs if pair not in allowed_pairs]
        if unsupported_pairs:
            failures.append(f"model disclosure contains unsupported model pair: {unsupported_pairs[0]}")
        if evidence == "unavailable" or evidence_level == "unavailable":
            failures.append("known Current model requires non-unavailable evidence")
        if evidence == "runtime_receipt" and evidence_level != "runtime_receipt":
            failures.append("runtime receipt evidence requires runtime_receipt evidence-level")
        if evidence != "runtime_receipt" and evidence != "unavailable" and evidence_level != "UNVERIFIED (no runtime receipt)":
            failures.append("non-receipt model evidence requires UNVERIFIED (no runtime receipt) evidence-level")
    if route_change in {"no_switch", "freeze"} and path_pairs:
        failures.append("no switch or frozen route must omit Model path")
    if route_change in {"upgrade", "downgrade", "operational_fallback"}:
        if len(path_pairs) < 2:
            failures.append("a changed route requires a Model path with at least two distinct pairs")
        elif path_pairs[-1] != current_pair:
            failures.append("Model must match the final Model path pair")
        elif any(left == right for left, right in zip(path_pairs, path_pairs[1:])):
            failures.append("Model path must collapse consecutive duplicate pairs")
    return failures


def _load_entry_resolver():
    resolver_path = SCRIPT_DIR / "resolve_entry_model.py"
    resolver_spec = importlib.util.spec_from_file_location("task_analyze_disclosure_entry_resolver", resolver_path)
    resolver_module = importlib.util.module_from_spec(resolver_spec)
    sys.modules[resolver_spec.name] = resolver_module
    resolver_spec.loader.exec_module(resolver_module)
    return resolver_module


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render or validate one deterministic Task Analyze model disclosure")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--complexity-score", type=int, required=True)
    render_parser.add_argument("--receipt", type=Path)
    render_parser.add_argument("--thread-id", default=os.environ.get("CODEX_THREAD_ID"))
    render_parser.add_argument("--sessions-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    subparsers.add_parser("validate")
    args = parser.parse_args(argv)
    if args.command == "validate":
        failures = validate_disclosure(sys.stdin.read())
        print(json.dumps({"status": "pass" if not failures else "fail", "failures": failures}, ensure_ascii=False, separators=(",", ":")))
        return 0 if not failures else 1
    runtime_receipt = json.loads(args.receipt.expanduser().resolve().read_text(encoding="utf-8")) if args.receipt else None
    entry_resolution = None if runtime_receipt else _load_entry_resolver().resolve_entry_model(args.thread_id, args.sessions_dir)
    print(render_disclosure(args.complexity_score, runtime_receipt=runtime_receipt, entry_resolution=entry_resolution))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

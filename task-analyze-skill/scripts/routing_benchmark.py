#!/usr/bin/env python3
"""Run a frozen, deterministic routing benchmark without calling a model."""

import argparse
import importlib.util
import json
import os
import statistics
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_CASE_FILE = SKILL_ROOT / "assets" / "routing-benchmark-cases.json"
DEFAULT_OUTPUT = SKILL_ROOT.parent / "Cache" / "tmp-routing-benchmark" / "routing-benchmark.json"


def _load_routing_policy():
    specification = importlib.util.spec_from_file_location("routing_benchmark_policy", SCRIPT_DIR / "routing_policy.py")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


ROUTING_POLICY = _load_routing_policy()


class RoutingBenchmarkError(ValueError):
    """Raised when a frozen benchmark corpus or expectation is invalid."""


def _load_cases(case_file):
    try:
        payload = json.loads(Path(case_file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RoutingBenchmarkError("routing benchmark corpus is unreadable") from error
    cases = payload.get("cases") if isinstance(payload, dict) and payload.get("schema_version") == 1 else None
    if not isinstance(cases, list) or not cases:
        raise RoutingBenchmarkError("routing benchmark corpus requires schema 1 and non-empty cases")
    identifiers = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"] or case["id"] in identifiers or not isinstance(case.get("cohort"), str) or not isinstance(case.get("prompt"), str) or not isinstance(case.get("expect"), dict):
            raise RoutingBenchmarkError("routing benchmark case is invalid")
        identifiers.add(case["id"])
    return cases


def _expectation_failures(observed, expected):
    failures = []
    for field in ("task_type", "operation"):
        if field in expected and observed.get(field) != expected[field]:
            failures.append(f"{field}_mismatch")
    if "fast_path" in expected and observed.get("fast_path_eligible") is not expected["fast_path"]:
        failures.append("fast_path_mismatch")
    score = observed.get("complexity_score")
    if score < expected.get("minimum_score", 0):
        failures.append("score_below_minimum")
    if score > expected.get("maximum_score", 100):
        failures.append("score_above_maximum")
    return failures


def _routing_tier(observed):
    complexity = "complex" if observed["complexity_score"] >= ROUTING_POLICY.ROUTING_THRESHOLDS["complex_route_minimum_score"] else "easy"
    pair = ROUTING_POLICY.priority_first_pair(observed["task_type"], "text", observed["operation"], complexity, observed["complexity_score"])
    return "fast_priority" if observed["fast_path_eligible"] and pair is not None else "normal"


def _atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_benchmark(case_file=DEFAULT_CASE_FILE, iterations=50):
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 10_000:
        raise RoutingBenchmarkError("iterations must be an integer from 1 to 10000")
    cases = _load_cases(case_file)
    samples_ns = []
    outcomes = []
    cohort_counts = defaultdict(lambda: {"case_count": 0, "passed": 0, "fast_priority": 0, "normal": 0})
    benchmark_started_ns = time.perf_counter_ns()
    for case in cases:
        observed = None
        for _ in range(iterations):
            started_ns = time.perf_counter_ns()
            observed = ROUTING_POLICY.analyze_prompt_routing(case["prompt"])
            samples_ns.append(time.perf_counter_ns() - started_ns)
        failures = _expectation_failures(observed, case["expect"])
        tier = _routing_tier(observed)
        cohort = cohort_counts[case["cohort"]]
        cohort["case_count"] += 1
        cohort[tier] += 1
        if not failures:
            cohort["passed"] += 1
        # Prompts are deliberately omitted from artifacts, leaving the frozen
        # corpus as test-only input and the report safe to share.
        outcomes.append(
            {
                "id": case["id"],
                "cohort": case["cohort"],
                "task_type": observed["task_type"],
                "operation": observed["operation"],
                "complexity_score": observed["complexity_score"],
                "fast_path": observed["fast_path_eligible"],
                "routing_tier": tier,
                "reason_count": len(observed["reasons"]),
                "expectation_failures": failures,
            }
        )
    wall_ms = round((time.perf_counter_ns() - benchmark_started_ns) / 1_000_000, 3)
    passed = sum(not outcome["expectation_failures"] for outcome in outcomes)
    return {
        "schema_version": 1,
        "kind": "deterministic_routing_classification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_file": Path(case_file).name,
        "model_execution": "not_run",
        "iterations_per_case": iterations,
        "case_count": len(outcomes),
        "passed_case_count": passed,
        "status": "pass" if passed == len(outcomes) else "fail",
        "metrics": {
            "classification_sample_count": len(samples_ns),
            "median_classification_ms": round(statistics.median(samples_ns) / 1_000_000, 4),
            "total_wall_ms": wall_ms,
            "time_to_first_result_ms": None,
            "total_tokens": None,
            "controller_overhead_ms": None,
            "ending_overhead_ms": None,
            "repair_overhead_ms": None,
        },
        "thresholds": dict(ROUTING_POLICY.ROUTING_THRESHOLDS),
        "cohorts": {name: dict(values) for name, values in sorted(cohort_counts.items())},
        "outcomes": outcomes,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the frozen deterministic routing benchmark.")
    parser.add_argument("--case-file", type=Path, default=DEFAULT_CASE_FILE)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = run_benchmark(args.case_file, args.iterations)
    _atomic_write_json(args.output, report)
    print(json.dumps({"status": report["status"], "case_count": report["case_count"], "passed_case_count": report["passed_case_count"], "output": str(args.output)}, ensure_ascii=False, separators=(",", ":")))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

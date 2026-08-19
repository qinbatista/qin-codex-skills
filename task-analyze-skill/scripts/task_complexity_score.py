#!/usr/bin/env python3
"""Return the universal 0-100 task complexity score without executing a model."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path


RUNNER_PATH = Path(__file__).with_name("obsidian_adaptive_model_runner.py")
SPEC = importlib.util.spec_from_file_location("task_complexity_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score one task prompt without executing a model.")
    parser.add_argument("prompt", nargs="?")
    arguments = parser.parse_args(argv)
    prompt = arguments.prompt if arguments.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        print(json.dumps({"status": "fail", "reason": "prompt_required"}, separators=(",", ":")))
        return 1
    # Keep the long-standing runner entry points as the score/operation
    # contract.  The richer routing object adds metadata without bypassing
    # callers that instrument or wrap these public helpers.
    score = RUNNER.infer_complexity_score(prompt)
    operation = RUNNER.infer_operation(prompt)
    routing = RUNNER.routing_policy.analyze_prompt_routing(prompt)
    band = RUNNER.obsidian_model_memory.complexity_band(score)
    print(json.dumps({"status": "pass", "task_type": routing["task_type"], "complexity_score": score, "complexity_band": band, "operation": operation, "fast_path_eligible": routing["fast_path_eligible"] and score <= RUNNER.routing_policy.ROUTING_THRESHOLDS["fast_path_maximum_score"], "routing_reasons": routing["reasons"]}, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Mini Test and Benchmark Evidence

Status: PASS

This report is the current, reproducible evidence for the global Mini Test and detached Ending-thread contract.

## Contract checks

| Check | Result |
| --- | --- |
| `test_validate_task_analyze_skill.py` | PASS — 39 tests |
| `validate_task_analyze_skill.py` | PASS — all supported model/effort route fixtures and 4/4 graduated prompt scenarios |
| Full Task Analyze test discovery | PASS — 421 tests discovered and completed successfully |

The direct validator checks that the global bootstrap and its source asset match exactly, remain within the compact limit, run a Mini Test for light local code, skip heavy API/large-file/expensive/side-effect execution in favor of syntax and changed-name checks, create a separate `End Task-{task name}` thread, and rerun the benchmark after structural changes.

## Simple to complex benchmark checks

| Benchmark layer | Result | What it proves |
| --- | --- | --- |
| `test_benchmark_suite_gate.py` | PASS — 37 tests | Correct simple, medium, and complex tier acceptance; frozen inputs; exact result/receipt/evidence checks; Ending excluded from first-result metrics. |
| `test_benchmark_suite_runner.py` | PASS — 29 tests | Alternating Direct/Global arms, per-tier repeat planning, result-ready timing, runtime census, resume behavior, and fail-closed drift handling. |

Run these checks from the `task-analyze-skill` parent directory:

```bash
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_validate_task_analyze_skill.py' -q
python3 task-analyze-skill/scripts/validate_task_analyze_skill.py --skill-dir task-analyze-skill --global-agents ../AGENTS.md --global-skills-root ..
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_benchmark_suite_gate.py' -q
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_benchmark_suite_runner.py' -q
```

This is structural benchmark evidence, not a live API performance claim. A live Direct/Global performance claim still requires a new frozen, repeated cohort with real model receipts for each simple, medium, and complex workload.

# Adaptive Model Test and Benchmark Evidence

Implementation status: PASS

Correctness status: PASS

Steady-state performance hypothesis: PASS for this frozen cohort

End-to-end first-result diagnostic: FAIL — reported separately and excluded from the steady-state claim

This report is the current reproducible evidence for step-capability model memory, bidirectional entry-aware routing, real-test Ending, and the Direct-versus-Auto benchmark. The primary performance claim is deliberately narrow: after the correct route is already frozen, compare only selected producer/graph execution. Entry matching, controller work, calibration failures, retry/fallback/repair, and Ending are disclosed separately and are not presented as saved time or tokens.

## Contract and regression checks

| Check | Result |
| --- | --- |
| `test_validate_task_analyze_skill.py` | PASS — 39 tests |
| `validate_task_analyze_skill.py` | PASS — 34 supported model/effort route fixtures and 4/4 graduated prompt scenarios |
| Full Task Analyze test discovery | PASS — 500 tests |
| Project model/change memory | PASS — 55 tests |
| Real-test Ending and repair lifecycle | PASS — 20 focused tests; executable checks capture real stdout/stderr/exit status, score each verifier, split independent checks, emit exact repair handoffs, and require fresh verification |
| `test_benchmark_suite_gate.py` | PASS — 41 tests |
| `test_benchmark_suite_runner.py` | PASS — 29 tests |

The routing tests cover both entry directions. A Sol-ultra entry can assign a very similar proven step to a lower pair, while a Luna-max-or-lower entry can jump directly to the stronger pair that previously recovered the same capability. When multiple pairs passed, token/time cost evidence stays diagnostic: the selector keeps the lowest passing rung above the strongest failed rung even if a stronger passing pair happened to use fewer tokens. Compound requests keep separate fingerprints and histories for steps such as implementation, local testing, image-generation control, and visual verification.

## Frozen real benchmark v47

The formal cohort is `benchmark-suite-c194f8ed76d58f82`: Direct uses fixed `gpt-5.6-sol|ultra` without the skill; Auto enters through `gpt-5.6-luna|max`, then applies the route already frozen by exact step-capability history. Direct counts the fixed producer. Auto counts the selected producer or graph critical path and all selected graph tokens. Entry/controller work is measured separately. Each tier has two paired repetitions, for 12 formal runs total.

- Exact task result: 12/12 PASS.
- Separate Ending: 12/12 PASS.
- `all_correct=true`; all 12 manifests are complete with complete metrics.
- Retry, fallback, and repair counts are all zero.
- Formal calibration attempt/failure counts are zero; the route was frozen before measurement.
- Auto effective routes were Spark-low for simple work, history-frozen Terra-medium for medium work, and two Spark-low source nodes followed by a Luna-low merge for complex work.
- Three out-of-arm Sol-ultra entry probes all produced the exact same result, route signature, and capability assignment as the Luna-max entry: 3/3 PASS.

| Tier | Direct steady tokens | Auto steady tokens | Token savings | Direct steady execution | Auto steady execution | Time savings | Tier diagnostic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Simple | 32,654 | 93,448 | -186.176% | 22.896 s | 17.561 s | +23.301% | token regression |
| Medium | 49,451 | 91,398 | -84.825% | 27.676 s | 28.057 s | -1.377% | token/time regression |
| Complex | 538,903 | 273,442 | +49.260% | 67.047 s | 45.481 s | +32.165% | PASS |
| **All tiers** | **621,008** | **458,288** | **+26.203%** | **117.619 s** | **91.099 s** | **+22.547%** | **aggregate PASS** |

The steady-state aggregate therefore passes for this cohort: after route selection is removed, Auto saved 26.520 seconds and 162,720 logical tokens. The actual end-to-end first-result total was slower, `117.619 s → 211.145 s` (`-79.516%` savings), because the six Auto entries spent 120.046 seconds in route/controller work. Those 120.046 seconds and 220,607 controller tokens are visible diagnostics, not part of the steady-state savings claim. The latest persisted Ending gate pass consumed another 6.050 seconds across both arms (Direct 2.817 seconds; Auto 3.233 seconds) and remains separate. Simple and medium token regressions are also retained rather than averaged away in the tier table. These measurements are evidence for this frozen workload cohort, not a universal future-runtime guarantee or a billing-price claim.

The sanitized evidence asset is `assets/model-routing-benchmark-example.json`. Raw manifests, receipts, runtime censuses, and rendered desktop/mobile summaries remain in the project-local benchmark Cache and are re-evaluated before export.

## Reproduce the structural checks

Run from the global skills directory:

```bash
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_validate_task_analyze_skill.py' -q
python3 task-analyze-skill/scripts/validate_task_analyze_skill.py --skill-dir task-analyze-skill --global-agents ../AGENTS.md --global-skills-root .
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_benchmark_suite_gate.py' -q
python3 -m unittest discover -s task-analyze-skill/tests -p 'test_benchmark_suite_runner.py' -q
python3 -m unittest discover -s project-memory-skill/tests -p 'test_*.py' -q
```

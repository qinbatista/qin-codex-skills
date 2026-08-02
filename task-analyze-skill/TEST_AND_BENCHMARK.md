# Adaptive Model Test and Benchmark Evidence

Implementation status: PASS

Correctness status: PASS

Performance hypothesis: FAIL

This report is the current reproducible evidence for step-capability model memory, bidirectional entry-aware routing, real-test Ending, and the Direct-versus-Auto benchmark. A failed performance hypothesis does not invalidate correctness: it means the measured strategy must not be advertised as universally faster or cheaper.

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

The routing tests cover both entry directions. A Sol-ultra entry can assign a very similar proven step to a lower pair, while a Luna-max-or-lower entry can jump directly to the stronger pair that previously recovered the same capability. Compound requests keep separate fingerprints and histories for steps such as implementation, local testing, image-generation control, and visual verification.

## Frozen real benchmark v46

The formal cohort is `benchmark-suite-f8f19e6e034ad677`: Direct uses fixed `gpt-5.6-sol|ultra` without the skill; Auto enters through `gpt-5.6-luna|max`, then applies adaptive child/graph routing. The Luna entry controller is excluded, but all foreground adaptive child/graph sessions are counted. Each tier has two paired repetitions, for 12 runs total.

- Exact task result: 12/12 PASS.
- Separate Ending: 12/12 PASS.
- `all_correct=true`; all 12 manifests are complete with complete metrics.
- Retry, fallback, and repair counts are all zero.
- Auto effective routes included Spark-low for simple steps, history-frozen Terra-medium for medium steps, and Luna-max graph orchestration for complex work.

| Tier | Direct median tokens | Auto median tokens | Paired token savings | Direct median first result | Auto median first result | Paired time savings | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Simple | 25,881.5 | 29,091.5 | -30.064% | 13,430 ms | 19,831 ms | -50.694% | FAIL |
| Medium | 16,366 | 36,632.5 | -123.834% | 10,545 ms | 34,323 ms | -225.472% | FAIL |
| Complex | 263,445.5 | 138,267 | +44.428% | 32,375 ms | 56,927 ms | -79.224% | PASS |

The benchmark therefore rejects the universal savings hypothesis. Complex work saved 44.428% task tokens in this cohort, but took longer; simple and medium work used more tokens and took longer because routing and subprocess overhead outweighed model savings. These are real empirical measurements for the frozen workloads, not a universal future-runtime guarantee or a billing-price claim.

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

# Installed skills: real workflow benchmark

**The tested rules were applied, but installed skills did not save time or logical tokens in either comparison.** Both conditions used **GPT-6 Astra / ultra** in fresh macOS workspaces; control had none of the eight managed skills. Every attempted trial is retained.

The [fictional replay fixture](../../../task-analyze-skill/tests/fixtures/workflow_benchmark/README.md) repairs a responsive review dashboard and a portable Python process runner, then calculates exact ledger totals. Both conditions receive the same fully specified brief. These are real model executions on isolated examples, not changes to a live product.

Logical tokens include cached input; cached tokens are not added twice. Time includes setup, actual model execution, focused checks, evidence retention, and cleanup. Parent visual review, native Windows checks, publication/deployment, and the shared memory Ending are outside this timing.

## V1: original three paired rounds

| Trial | Condition | Logical tokens | Cached input | Seconds | Raw | Accepted |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | control | 298,308 | 263,424 | 273.50 | PASS | PASS |
| 1 | installed | 466,855 | 415,232 | 386.00 | PASS | PASS |
| 2 | installed | 306,775 | 205,440 | 279.35 | PASS | PASS |
| 2 | control | 270,621 | 230,784 | 257.24 | PASS | PASS |
| 3 | control | 199,681 | 168,320 | 221.38 | PASS | PASS |
| 3 | installed | 339,928 | 259,200 | 323.37 | FAIL | PASS |

One original FAIL was a content-read classifier false negative: a successful combined command contained the complete frozen skill texts. All six original logs were uniformly reanalyzed; the original failure and measured time/tokens remain unchanged. Accepted status includes that documented adjudication and independent runtime/output/visual gates.

| Aggregate | Logical tokens | Seconds | Median seconds | Accepted |
| --- | ---: | ---: | ---: | --- |
| control | 768,610 | 752.11 | 257.24 | 3/3 |
| installed | 1,113,558 | 988.72 | 323.37 | 3/3 |

Installed used **44.88% more logical tokens** and was **31.46% slower** in this sample. It did not beat control on both metrics.

## V2: one prospective revision pair

| Trial | Condition | Logical tokens | Cached input | Seconds | Raw | Accepted |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | control | 271,203 | 214,272 | 278.46 | PASS | PASS |
| 1 | installed | 344,268 | 286,464 | 310.86 | PASS | PASS |

| Aggregate | Logical tokens | Seconds | Median seconds | Accepted |
| --- | ---: | ---: | ---: | --- |
| control | 271,203 | 278.46 | 278.46 | 1/1 |
| installed | 344,268 | 310.86 | 310.86 | 1/1 |

Installed used **26.94% more logical tokens** and was **11.63% slower** in this sample. It did not beat control on both metrics.

V2 clarified Verify Finish: reuse adequate coverage, add only missing checks, avoid overlapping tests, and rerun the style check after a formatting-only repair. It also includes disclosed UTF-8 setup and read-classifier corrections with native Windows/evidence regressions; macOS already used UTF-8. Task, model/effort, tools, output checker, and acceptance remain fixed when the revision-control gates pass. The installed V2 run additionally must show a completed content read of the new Verify rule. The studies are not pooled; one new pair cannot isolate causality or establish a stable advantage.

Development pilot: **333,360 tokens, 325.28 s**, retained separately under an earlier oracle. It is excluded from both comparisons.

## Functional workflow proof

Prior live task: **59/100 (complex)**. This separate check demonstrated actual model distribution and a visible memory-only Ending; it is not included in benchmark timings.

| Goal | Score / band | Actual model / effort | Dependency | Result |
| --- | --- | --- | --- | --- |
| Skill-governed code review | 20 / small | gpt-6-astra / ultra | Entry | PASS |
| Independent data calculation | 20 / small | gpt-5.6-luna / low | Entry | PASS |
| Result integration | 20 / small | gpt-6-astra / ultra | Skill-governed code review, Independent data calculation | PASS |
| Memory-only Ending | 28 / standard | gpt-6-astra / ultra | Verified final result | PASS |

The eight skill entry documents shrank from **24,126 to 3,777 words (84.34%)**. This is document compression, not runtime savings.

Native Windows preflight: **73 passed, one expected POSIX-only skip**, outside macOS timing. A later hidden native PowerShell read also preserved exact Unicode content and passed the corrected read classifier. Actual console-free child/runtime checks ran through noninteractive SSH; the interactive desktop was not observed. The earlier pilot's native check and prior UI/PDF examples do not prove every later candidate or every application.

Acceptance combines runtime/model identity, successful required skill-content reads, exact behavior and headless geometry/interaction checks, and parent desktop/narrow visual review. Missing or failed evidence cannot yield an all-pass or efficiency-win claim. Small samples, provider cache/latency, and local load limit interpretation; no pricing or general savings is inferred.

[Structured measurements and evidence gates](current-workflow-benchmark.json). The single-controller harness is [benchmark_installed_skills.py](../../../task-analyze-skill/scripts/benchmark_installed_skills.py); see its `--help` and the fixture guide for runtime bindings.

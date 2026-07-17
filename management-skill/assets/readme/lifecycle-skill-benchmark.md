# Real adaptive lifecycle benchmark

Frozen cohort date: 2026-07-17

## Answer first

Both arms entered `gpt-5.6-sol | ultra`. Direct stayed on Sol-ultra and stopped after the requested main job. Auto used a receipt-proven adaptive producer, returned the main result, and only then ran a separate read-only Ending session.

Across six real A/B pairs, Auto used **14.500% fewer foreground logical tokens** and reached the first result **41.808% faster**. Background Ending added 276,079 tokens and 114.770s afterward. Including that later cost, Auto remained **24.955% faster sequentially**, while whole-lifecycle tokens were **2.956% higher**.

All 12 main results were exact, all local Mini Tests passed, and all six Auto-only Ending sessions returned PASS. Direct had **zero** verifier sessions, verifier tokens, and verifier time.

> **Finish job first → return the completed result → background verify in a new End Task. Ending never gates the usable main result.**

![Direct main-only bars versus Auto foreground bars with striped Auto-only Ending extensions](./lifecycle-skill-benchmark.svg)

## Cohort totals

| Tier | Real task | Auto producer | Direct foreground tokens | Auto foreground tokens | Token change | Direct first result | Auto first result | Time change | Auto Ending tokens / time | Auto whole tokens / sequential time |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Simple | `normalize_tags`; 4 tests | `gpt-5.3-codex-spark \| low` | 231,823 | 319,126 | 37.659% more | 94.280s | 94.657s | 0.400% slower | 90,588 / 26.633s | 409,714 / 121.290s |
| Medium | Decimal invoice; 6 tests | `gpt-5.6-terra \| medium` | 444,426 | 286,645 | **35.502% fewer** | 173.706s | 89.014s | **48.756% faster** | 94,981 / 43.947s | 381,626 / 132.961s |
| Complex | Six-file quote pipeline; 8 tests | `gpt-5.6-terra \| medium` | 905,339 | 746,484 | **17.546% fewer** | 413.022s | 212.619s | **48.521% faster** | 90,510 / 44.190s | 836,994 / 256.809s |
| **All** | **6 pairs / 12 main runs** | Spark-low + Terra-medium | **1,581,588** | **1,352,255** | **14.500% fewer** | **681.008s** | **396.290s** | **41.808% faster** | **276,079 / 114.770s** | **1,628,334 / 511.060s** |

Medium and complex won both pairs. Simple won one pair and lost one, so no simple-tier savings claim is made. The short-task result exposes the fixed dispatch cost and tool-turn variance instead of hiding them inside the overall total.

## Every run

| Tier | Pair | Arm | Sol entry tokens | Child tokens | Foreground tokens | First result | Ending tokens | Ending time | Whole tokens | Sequential whole | Effective child |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Simple | 1 | Direct | 148,448 | 0 | 148,448 | 71.387s | 0 | 0 | 148,448 | 71.387s | — |
| Simple | 1 | Auto | 44,177 | 93,792 | 137,969 | 28.343s | 46,469 | 11.948s | 184,438 | 40.291s | `gpt-5.3-codex-spark \| low` |
| Simple | 2 | Direct | 83,375 | 0 | 83,375 | 22.893s | 0 | 0 | 83,375 | 22.893s | — |
| Simple | 2 | Auto | 75,838 | 105,319 | 181,157 | 66.314s | 44,119 | 14.685s | 225,276 | 80.999s | `gpt-5.3-codex-spark \| low` |
| Medium | 1 | Direct | 201,861 | 0 | 201,861 | 84.672s | 0 | 0 | 201,861 | 84.672s | — |
| Medium | 1 | Auto | 89,416 | 69,753 | 159,169 | 49.835s | 46,702 | 20.977s | 205,871 | 70.812s | `gpt-5.6-terra \| medium` |
| Medium | 2 | Direct | 242,565 | 0 | 242,565 | 89.034s | 0 | 0 | 242,565 | 89.034s | — |
| Medium | 2 | Auto | 61,978 | 65,498 | 127,476 | 39.179s | 48,279 | 22.970s | 175,755 | 62.149s | `gpt-5.6-terra \| medium` |
| Complex | 1 | Direct | 516,214 | 0 | 516,214 | 246.788s | 0 | 0 | 516,214 | 246.788s | — |
| Complex | 1 | Auto | 369,064 | 109,738 | 478,802 | 140.248s | 45,539 | 20.286s | 524,341 | 160.534s | `gpt-5.6-terra \| medium` |
| Complex | 2 | Direct | 389,125 | 0 | 389,125 | 166.234s | 0 | 0 | 389,125 | 166.234s | — |
| Complex | 2 | Auto | 83,245 | 184,437 | 267,682 | 72.371s | 44,971 | 23.904s | 312,653 | 96.275s | `gpt-5.6-terra \| medium` |

The simple pair-2 Auto producer corrected one mistyped local-test workdir and then passed 4/4. This visible recovered tool invocation explains much of that outlier; it was not a model reroute, fallback, or separate repair lifecycle.

## Measurement contract

- **Real tasks:** local code edits with deterministic `unittest` Mini Tests: 4, 6, and 8 tests.
- **Pairs:** two A/B pairs per tier, alternating arm order; 12 main sessions total.
- **Entry:** every arm starts `gpt-5.6-sol | ultra`; Direct stays fixed.
- **Auto foreground tokens:** Sol entry receipt + exactly one non-Sol adaptive-child receipt.
- **First-result time:** controller-stamped result-ready time, excluding receipt cleanup and Ending.
- **Ending:** six separate later Sol-ultra read-only sessions; no additional tests, APIs, writes, repairs, questions, or waits.
- **Correctness:** exact JSON output, allowed-file changes, and passing local Mini Tests for every main run.
- **Privacy:** raw prompts, receipts, session IDs, personal paths, and private model memory remain local and are not published.

## What changed before this accepted cohort

The repaired global contract now routes before loading skills, memory, or task files; supports a zero-argument stdin runner; infers easy versus complex effort from task text; binds the producer to the canonical workdir; and never emulates thread creation through app-server internals. When real thread tools exist, the host creates `End Task-{task name}` and returns without waiting.

Earlier diagnostic cohorts were excluded: one lacked the registered frozen routing context, and one sent every task through the easy route. Only the fresh frozen post-repair cohort is shown here.

## Limits

- Logical tokens are operational usage including cached input, not billing tokens or a dollar-cost claim.
- Two pairs per tier are optimization confirmation, not the six-pair-per-condition evidence required for durable performance admission.
- Simple work is not yet performance-admitted; medium, complex, and overall foreground results won in this cohort.
- Whole-lifecycle tokens are slightly higher because Auto deliberately buys six background audits that Direct does not perform.

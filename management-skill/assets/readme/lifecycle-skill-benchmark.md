# Real adaptive lifecycle benchmark v26

Date: 2026-07-17  
Frozen cohort: `real-adaptive-schedule-benchmark-v26`  
Entry model in both arms: `gpt-5.6-sol | ultra`

## Result first

The current lifecycle is functionally correct and materially faster to the first usable result, but it does **not** pass the token strategy gate.

- **Correctness:** 12/12 main runs returned the exact required result; every local Mini Test passed; 6/6 independent Ending audits returned PASS.
- **First-result speed:** Auto returned the completed foreground result in **353.661s**, versus **460.525s** Direct: **23.205% faster**.
- **Foreground tokens:** Auto used **1,657,752** logical tokens, versus **1,263,980** Direct: **31.153% more**.
- **Why:** Auto's producer/schedule used **1,165,130** tokens, **7.821% fewer** than Direct. The separate Sol-ultra routing controller added **492,622** tokens and reversed the total.
- **Ending:** the six later background verification tasks added **304,094 tokens / 188.627s**. Direct has no verifier, so its verification cost is exactly zero.

> **FINISH JOB FIRST → RETURN THE COMPLETED RESULT → BACKGROUND VERIFY IN A NEW `End Task-*`. Ending never gates the usable main result.**

![Real v26 A/B benchmark with Direct, Auto controller, adaptive producer or schedule, and Auto-only Ending costs](./lifecycle-skill-benchmark.svg)

## Whole picture

| Tier | Auto route | Direct foreground tokens | Auto controller | Auto producer / schedule | Auto foreground | Token result | Direct first result | Auto first result | Time result | Auto Ending | Auto whole sequential |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Simple · 4 tests | Spark-low | 291,499 | 179,430 | 252,534 | 431,964 | 48.187% more | 134.659s | 100.856s | **25.103% faster** | 92,114 / 82.598s | 524,078 / 183.454s |
| Medium · 6 tests | Spark-high | 464,397 | 176,040 | 467,556 | 643,596 | 38.587% more | 167.086s | 145.307s | **13.035% faster** | 92,658 / 39.845s | 736,254 / 185.152s |
| Complex · 3 sources | 3× Spark-low → Terra-medium merge | 508,084 | 137,152 | 445,040 | 582,192 | 14.586% more | 158.780s | 107.498s | **32.298% faster** | 119,322 / 66.184s | 701,514 / 173.682s |
| **All 6 pairs** | **receipt-proven adaptive graph** | **1,263,980** | **492,622** | **1,165,130** | **1,657,752** | **31.153% more** | **460.525s** | **353.661s** | **23.205% faster** | **304,094 / 188.627s** | **1,961,846 / 542.288s** |

Whole sequential Auto is **55.212% more tokens** and **17.754% slower** than Direct because it includes six verification sessions that Direct never runs. This sequential diagnostic does not mean the user waited: the main result had already been returned.

## Did auto model switch and scheduling work?

**Yes.** Every Auto run started from Sol-ultra, produced a routing receipt, and executed the selected child or graph. The complex route was:

```text
Sol-ultra controller
  ├─ source 1 → Spark-low
  ├─ source 2 → Spark-low
  ├─ source 3 → Spark-low
  └─ merge     → Terra-medium
```

The complex schedule's producer-only total was **445,040 tokens**, **12.408% fewer** than Direct's 508,084. Its two-run recorded critical-path process total was **43.532s**, **72.583% faster** than Direct's 158.780s. The user-visible Auto foreground still includes the controller, so it became 582,192 tokens and a 107.498s first result. That is a large latency win, but not a foreground token win.

This distinction fixes the misleading old chart. It had hidden the controller inside one Auto bar and labeled one child as if it were a schedule. v26 exposes all stages and does not claim a universal token win.

## Every measured main and Ending run

Auto foreground tokens are `controller + producer/schedule`. Direct has neither a child nor a verifier. Ending is shown only behind Auto and never contributes to first-result time.

| Tier | Pair | Arm | Controller | Producer / schedule | Foreground tokens | First result | Ending tokens | Ending time | Whole tokens | Whole sequential | Result |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Simple | 1 | Direct | — | — | 171,308 | 68.279s | 0 | 0 | 171,308 | 68.279s | exact + 4/4 |
| Simple | 1 | Auto | 114,514 | 131,663 | 246,177 | 58.391s | 46,179 | 22.720s | 292,356 | 81.111s | exact + 4/4; Ending PASS |
| Simple | 2 | Auto | 64,916 | 120,871 | 185,787 | 42.465s | 45,935 | 59.878s | 231,722 | 102.343s | exact + 4/4; Ending PASS |
| Simple | 2 | Direct | — | — | 120,191 | 66.380s | 0 | 0 | 120,191 | 66.380s | exact + 4/4 |
| Medium | 1 | Direct | — | — | 300,698 | 110.468s | 0 | 0 | 300,698 | 110.468s | exact + 6/6 |
| Medium | 1 | Auto | 65,554 | 185,811 | 251,365 | 56.978s | 46,988 | 21.385s | 298,353 | 78.363s | exact + 6/6; Ending PASS |
| Medium | 2 | Auto | 110,486 | 281,745 | 392,231 | 88.329s | 45,670 | 18.460s | 437,901 | 106.789s | exact + 6/6; Ending PASS |
| Medium | 2 | Direct | — | — | 163,699 | 56.618s | 0 | 0 | 163,699 | 56.618s | exact + 6/6 |
| Complex | 1 | Direct | — | — | 223,710 | 60.998s | 0 | 0 | 223,710 | 60.998s | exact + semantic gate |
| Complex | 1 | Auto | 69,849 | 184,237 | 254,086 | 58.970s | 49,250 | 29.101s | 303,336 | 88.071s | exact + semantic gate; Ending PASS |
| Complex | 2 | Auto | 67,303 | 260,803 | 328,106 | 48.528s | 70,072 | 37.083s | 398,178 | 85.611s | exact + semantic gate; Ending PASS |
| Complex | 2 | Direct | — | — | 284,374 | 97.782s | 0 | 0 | 284,374 | 97.782s | exact + semantic gate |

## Complex graph receipts

The complex benchmark is a real three-source audit with a semantic JSON merge gate. The sources are independent, so the route can schedule them concurrently. These are the recorded child receipts, not estimated allocations.

| Pair | Stage | Effective model | Logical tokens | Process time |
|---:|---|---|---:|---:|
| 1 | Source 1 | Spark-low | 59,009 | 10.863s |
| 1 | Source 2 | Spark-low | 54,403 | 10.254s |
| 1 | Source 3 | Spark-low | 35,535 | 7.377s |
| 1 | Merge | Terra-medium | 35,290 | 12.300s |
| 2 | Source 1 | Spark-low | 69,435 | 7.160s |
| 2 | Source 2 | Spark-low | 121,808 | 8.726s |
| 2 | Source 3 | Spark-low | 34,128 | 6.694s |
| 2 | Merge | Terra-medium | 35,432 | 12.493s |

## What was wrong and what changed

The goal recovered from the skill's Git history was: preserve correctness, reduce task tokens through model routing and scheduling, return the usable result before verification, and make Ending independent. The implementation had drifted in several places:

1. **Unsafe exact-task fan-out.** Dependent exact-expression manifests could be split. They now use one Sol-high producer with source-specific contracts.
2. **Hard-coded schedule branch model.** Priority branches could use the old floor pair. They now derive the current adaptive priority model and bind each independent source to low effort.
3. **Dispatcher rejection.** Locked priority producer nodes could be rejected and recursively re-enter the router. A narrow receipt-authorized admission now allows only the exact read-only, one-source, model-matching producer shape.
4. **False terminal failure.** A transient stream error could survive even after `turn.completed`. The parser now treats the latest terminal event as authoritative.
5. **Benchmark contamination.** Earlier harnesses pointed `CODEX_PROJECT_ROOT` at the private global skill history, causing valid historical quality routing to override a cold-start benchmark. v26 uses a disposable project and preserved private history untouched.
6. **Misleading visualization.** The previous graphic merged controller and producer costs, then overstated the complex token win. v26 shows controller, producer/schedule, first result, and Ending separately.

## Measurement contract

- Both Direct and Auto outer sessions start from `gpt-5.6-sol | ultra`.
- Direct remains on that model, completes the requested task and Mini Test, then stops. Direct verification is zero.
- Auto must provide a routing receipt proving the effective child or graph.
- First-result time ends when the exact completed result is available. It excludes Ending.
- Ending is a separate, later, evidence-only task. It does not edit, repair, call APIs, repeat expensive tests, ask the main task to wait, or block delivery.
- Light functions receive the smallest meaningful local Mini Test. API-heavy, large-file, expensive, or side-effecting work receives syntax/name/reference checks only.
- Logical tokens are runtime usage including cached input; they are not a billing or dollar-cost claim.
- Two pairs per tier confirm this code change. They do not satisfy the six-pair-per-condition threshold for durable performance admission.

## Frozen evidence

- Cohort: `work/real-adaptive-schedule-benchmark-v26/`
- Summary: `benchmark-summary.json`
- Runner SHA-256: `8b26bdbcd549cc165bd64bd599334783b7f2d94295066e7980d938efb15eb0e3`
- Adaptive runner SHA-256: `ca6a1cd3191465d340794e414dbb0ad7a01dac237f279ef5ffc4d126ffd53a86`
- Global `AGENTS.md` SHA-256: `f2cc6f6f7ea15decaf6470217499b335c889cc8f2a584add1966af35270797ff`
- Complex expected-result SHA-256: `a4c877ca8d531dd4410d7fe5b24b65d2d9b45be13d6eb25b300804ca69578023`

Raw prompts, private routing memory, session receipts, and model transcripts remain local by design. The public report publishes the complete aggregate and per-run evidence without leaking private artifacts.

## Publication validation

The final code, documentation, and graphic were checked again after v26 was frozen:

| Check | Result |
|---|---|
| Adaptive runner focused suite | 22/22 passed |
| Model execution receipt suite | 33/33 passed |
| Route dispatcher suite | 70/70 passed |
| Management README/report/visual suite | 25/25 passed |
| Task Analyze generated plans | all catalog pairs passed; graduated prompts 4/4 |
| Workflow routes / gates / traces / graduated prompts | 11/11 · 2/2 · 3/3 · 4/4 |
| Changed Python entry points | `py_compile` passed |
| Public benchmark graphic | XML parse, layout bounds test, and rendered PNG inspection passed |
| Compact global bootstrap | 1,145 bytes; public entry-rule mirror byte-identical |

## Decision

- **Correctness gate:** passes.
- **Foreground first-result gate:** wins in this cohort.
- **Foreground token strategy gate:** fails because controller overhead exceeds producer savings.
- **Lifecycle contract:** keep. Returning the finished result before an independent background verifier is useful even when the verifier adds cost.
- **Next optimization target:** reduce or eliminate the 492,622-token Sol controller cost; do not weaken the producer schedule or hide the overhead.

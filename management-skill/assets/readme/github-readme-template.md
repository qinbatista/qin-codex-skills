<div align="center">

# 🚀 Auto Best Model

**Codex-only · finish the job first · verify afterward in a separate background task**

[中文说明](./README.zh.md)

Saved highest-family quality ladder · refreshed only when you request a local model update

Current catalog-derived priority producer: `gpt-5.3-codex-spark` · easy=`low` · complex=`high`

</div>

## 🔄 Core flow

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow.svg" alt="Core flow: finish and return the main job first, then start a separate nonblocking background Ending task">
</picture>

## ✅ Finish first. Verify in background.

This is the lifecycle’s most important structural rule:

1. **Main task finishes the requested job** and runs only the proportional local check that belongs to implementation.
2. **Return the completed result immediately.** The user is not held inside a verifier, poll loop, or repair cycle.
3. **Start `End Task-<task name>` as a separate background Codex task.** It audits existing evidence read-only and never blocks the completed main result.
4. **Ending reports PASS or the exact failure.** It does not ask the user questions, wait, poll, call heavy APIs, or repair inside the Ending task; a failure reopens a new repair task.

Main work and Ending verification are deliberately different task sessions. “Background” means the user can continue working as soon as the main result is returned—it does not mean verification is skipped.

## ⚡ Models & private learning

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Catalog-derived priority producer and full quality ladder with private Obsidian learning">
</picture>

- **Priority:** Eligible text/code uses the adaptive catalog priority producer: easy `low`, complex `high`; exact read-only, image/mixed, and tool-only work stays inline.
- **Operational:** With zero result and zero tokens, use the current contextual Obsidian-selected quality pair.
- **Quality:** A completed result returns first; the separate background Ending task logs a receipt-backed failure before a new repair task uses a different verifier.
- **Learning:** Ending outcomes update broad project/Skills `Model Switch.md` pages; project/task/module/file/symbol are fields only—no hierarchy notes.

## Rules

- **Producer:** Eligible text/code uses the adaptive catalog priority producer; exact read-only, image/mixed, and tool-only work stays inline.
- **Prompt:** Reusable prompts and durable AI instructions load Prompt Skill.
- **Route:** Delegate only on explicit request or current end-to-end proof.
- **Deliver:** Finish and return the completed main result before background verification.
- **Verify:** Launch a separate, nonblocking `End Task-<task name>` after delivery; first-result time excludes it.
- **Files:** Recall project/module/file history before editing; record the verified change after.
- **Memory:** Change history is local JSONL + optional Obsidian; private learning uses broad project/Skills `Model Switch.md`: fields only; no hierarchy notes.
- **Models:** Ordinary tasks use saved JSON; explicit local update selects the highest numeric GPT family, while unavailable cache keeps the saved list.
- **Privacy:** Secrets, raw prompts/results, receipts, ledgers, caches, and work artifacts stay local.

## 📊 Full lifecycle benchmark: main task + Ending task

**Technical summary:** The current global skill preserved correctness but did not improve performance on this tiny exact-output workload. Across six paired runs, the skill-enabled lifecycle was slower in five pairs, increased median whole-lifecycle time by **17.6%**, and increased median token use by **46.1%**.

![Full lifecycle benchmark showing main task, Ending task, whole time, tokens, and all six paired runs](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

### Main work and background verification cost

| Mode | Main tokens | Verify tokens behind main | Cohort tokens | Main time | Verify time behind main | Cohort time |
|---|---:|---:|---:|---:|---:|---:|
| Without global skill | 78,102 | 78,585 (50.2%) | 156,687 | 19.153 s | 18.039 s (48.5%) | 37.192 s |
| With global skill | 114,826 | 114,727 (50.0%) | 229,553 | 22.138 s | 24.628 s (52.7%) | 46.766 s |

The visual deliberately places the striped verification segment **behind the main-task segment**. Ending does not block delivery, but its time and tokens are still real lifecycle cost. This benchmark did not capture first-visible-result latency, so it does not pretend that full main-session duration is first-result time.

### Whole picture

| Mode | Main session median | Ending session median | Whole lifecycle median | Total-token median | Whole-lifecycle wins |
|---|---:|---:|---:|---:|---:|
| Without global skill | 2.773 s | 2.778 s | 6.091 s | 26,113 | Baseline |
| With global skill | 3.322 s | 3.473 s | 7.164 s | 38,163 | 1 of 6 |
| Skill overhead | +19.8% | +25.0% | +17.6% | +46.1% | Slower in 5 of 6 |

“Whole lifecycle” is main + Ending within each run, followed by the median of those six totals. It is not the sum of separately calculated stage medians.

### All six paired runs

| Run | Without: main | Without: Ending | Without: whole | With: main | With: Ending | With: whole | Faster whole |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 5.135 s | 2.918 s | 8.053 s | 3.226 s | 3.236 s | 6.462 s | With skill |
| 2 | 2.256 s | 2.635 s | 4.891 s | 5.478 s | 3.628 s | 9.106 s | Without skill |
| 3 | 2.629 s | 4.201 s | 6.830 s | 3.561 s | 4.111 s | 7.672 s | Without skill |
| 4 | 2.508 s | 2.729 s | 5.237 s | 3.230 s | 3.318 s | 6.548 s | Without skill |
| 5 | 2.916 s | 2.801 s | 5.717 s | 3.242 s | 7.081 s | 10.323 s | Without skill |
| 6 | 3.709 s | 2.755 s | 6.464 s | 3.401 s | 3.254 s | 6.655 s | Without skill |

### Token evidence

| Run | Without: main | Without: Ending | Without: total | With: main | With: Ending | With: total |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 13,017 | 13,101 | 26,118 | 19,044 | 19,119 | 38,163 |
| 2 | 13,017 | 13,092 | 26,109 | 19,044 | 19,119 | 38,163 |
| 3 | 13,017 | 13,092 | 26,109 | 19,606 | 19,131 | 38,737 |
| 4 | 13,017 | 13,093 | 26,110 | 19,044 | 19,119 | 38,163 |
| 5 | 13,017 | 13,109 | 26,126 | 19,044 | 19,120 | 38,164 |
| 6 | 13,017 | 13,098 | 26,115 | 19,044 | 19,119 | 38,163 |
| **Median** | **13,017** | **13,096** | **26,113** | **19,044** | **19,119** | **38,163** |

### Method and evidence

- **Cohort:** 6 paired comparisons, 24 independent sessions (`main + Ending` in both modes), same `gpt-5.6-luna | low` model and same exact workload.
- **Order control:** Runs 1, 3, and 5 executed without skill first; runs 2, 4, and 6 executed with skill first.
- **Without skill:** User configuration/global skills were disabled, but the harness still launched a second clean audit session so both modes kept the same two-session topology.
- **With skill:** Current global configuration loaded; Ending ran as an independent `ENDING_TASK_WORKER` session.
- **Correctness:** 12/12 main sessions PASS, 12/12 Ending audits PASS, 0 reroutes.
- **Identity controls:** Main workload SHA-256 `6ed46ac3699918ac054b2bf8e9d9da2be31628443a4d142848a121432f905c2b`; Ending workload SHA-256 `9ffe75646e4ecb36f6426026ad6005dd8947d2635c435dde36bb4fe5b89fee6a`; identical main output SHA-256 `7ba6fb88894e1d0faf389562cd4639eae0d733bcae056d8788d606a8777a5121`.
- **Timing definition:** Full session/process duration—not first-visible-result latency. All runs used a read-only sandbox.

### Decision and limitation

The skill is **not performance-admitted for this tiny workload**: it returned the same correct result but cost more time and tokens. This is descriptive lifecycle-overhead evidence, not proof about complex coding quality. The public report omits raw prompts, private paths, receipts, and session IDs.

## 🧩 Eight public Skills

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — route strategy, benchmarks, and admission.
- [`Workflow`](./workflow-skill/SKILL.md) — admitted locked-route execution.
- [`Prompt`](./prompt-skill/SKILL.md) — reusable prompt and durable AI-instruction gate.
- [`Code`](./code-skill/SKILL.md) — Python, C#, Unity C#, and registered code domains.
- [`Project Memory`](./project-memory-skill/SKILL.md) — project/module/file recall and verified records.
- [`Verify`](./verify-skill/SKILL.md) — post-result Real Verify and regression evidence.
- [`Optimization`](./optimization-skill/SKILL.md) — stable repeated work into reusable tools.
- [`Management`](./management-skill/SKILL.md) — private profiles and public mirror management.

## 🛠️ Registered execution domains

<!-- EXECUTION_DOMAIN_TABLE -->

## Install

1. Put the eight Skill folders under `~/.codex/skills/`.
2. Merge [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into `~/.codex/AGENTS.md`.
3. Start Codex normally; no lifecycle hook is installed.

**Privacy:** The mirror excludes auth, secrets, private ledgers, routing history, caches, raw prompts/results, receipts, and work artifacts; every publish runs a safety scan.

**Mirrors:** `qin-codex-skills` · `auto-best-model`

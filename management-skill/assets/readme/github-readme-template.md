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

## 📊 Real adaptive benchmark: finish first, verify in background

Both arms enter `gpt-5.6-sol | ultra`. **Without skill** stays on Sol-ultra, finishes the requested job, and stops: verification tokens/time are exactly **0**. **With skill** uses a receipt-proven adaptive producer, returns the completed main result, then starts a separate read-only Ending task.

![Six real A/B pairs showing Direct main-only bars, Auto foreground bars, and striped Auto-only Ending cost](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

| Tier | Auto child | Direct foreground tokens | Auto foreground | Token result | Direct first result | Auto first result | Time result | Auto Ending |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Simple · 4 tests | `Spark \| low` | 231,823 | 319,126 | 37.659% more | 94.280s | 94.657s | 0.400% slower | 90,588 / 26.633s |
| Medium · 6 tests | `Terra \| medium` | 444,426 | 286,645 | **35.502% fewer** | 173.706s | 89.014s | **48.756% faster** | 94,981 / 43.947s |
| Complex · 8 tests | `Terra \| medium` | 905,339 | 746,484 | **17.546% fewer** | 413.022s | 212.619s | **48.521% faster** | 90,510 / 44.190s |
| **All 6 pairs** | Spark + Terra | **1,581,588** | **1,352,255** | **14.500% fewer** | **681.008s** | **396.290s** | **41.808% faster** | **276,079 / 114.770s** |

After adding the six later Ending sessions, Auto is still **24.955% faster sequentially**; whole-lifecycle tokens are **2.956% higher** because Direct buys no verifier. Medium and complex each won both pairs. Simple won one and lost one, so no simple-tier savings claim is made.

**Correctness:** 12/12 exact main results, local Mini Tests `4/4`, `6/6`, and `8/8`, plus 6/6 separate Ending PASS results. Two pairs per tier are optimization confirmation, not six-pair performance admission. Logical tokens are operational usage, not billing tokens.

[Read the full benchmark report and every run.](./management-skill/assets/readme/lifecycle-skill-benchmark.md)

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

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

## 📊 Current benchmark

**Benchmark v6** · `gpt-5.6-sol | ultra` in both arms · **6 A/B pairs · 12 runs · 0 retries · 0 fallbacks · 0 repairs**

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg">
  <img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Current GPT-5.6 Direct versus Global benchmark with a failed strategy-performance gate">
</picture>

> **85.284% fewer task tokens** · **8.629% faster** overall first result · all 12 results correct · strategy gate **FAIL**: Medium won 1/2 timing pairs

> Frozen read-only bootstrap cohort; Spark was not eligible here · not billing tokens · Ending Real excluded

[Sanitized benchmark evidence](./task-analyze-skill/assets/model-routing-benchmark-example.json)

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

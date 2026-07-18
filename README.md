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

Both arms enter `gpt-5.6-sol | ultra`. **Without skill** finishes and stops; verification cost is **0**. **With skill** returns a receipt-proven result, then launches a separate read-only Ending task that never blocks delivery.

![Six real A/B pairs separating Direct, Auto controller, adaptive producer or schedule, and striped Auto-only Ending cost](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

| Tier | Auto route | Direct tokens | Auto controller | Auto producer | Auto foreground | Token result | Direct time | Auto time | Time result | Auto Ending |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Simple · 4 tests | Spark-low | 291,499 | 179,430 | 252,534 | 431,964 | 48.187% more | 134.659s | 100.856s | **25.103% faster** | 92,114 / 82.598s |
| Medium · 6 tests | Spark-high | 464,397 | 176,040 | 467,556 | 643,596 | 38.587% more | 167.086s | 145.307s | **13.035% faster** | 92,658 / 39.845s |
| Complex · 3 sources | 3× Spark-low → Terra-medium | 508,084 | 137,152 | 445,040 | 582,192 | 14.586% more | 158.780s | 107.498s | **32.298% faster** | 119,322 / 66.184s |
| **All 6 pairs** | receipt-proven graph | **1,263,980** | **492,622** | **1,165,130** | **1,657,752** | **31.153% more** | **460.525s** | **353.661s** | **23.205% faster** | **304,094 / 188.627s** |

**The switch and schedule work.** Producers alone use **7.821% fewer tokens overall**; the complex graph uses **12.408% fewer** with a **72.583% faster critical path**. The Sol controller adds 492,622 tokens, so the honest foreground strategy result is token **FAIL**. Whole sequential Auto is **55.212% more tokens** and **17.754% slower** after Ending; delivery happened earlier.

**Correctness:** 12/12 exact results, all Mini Tests, and 6/6 Ending audits passed. Two pairs per tier confirm this change, not performance admission. Logical tokens are not billing tokens.

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

- `general` · general · `workflow-skill` · active · Spark: no · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · Spark: yes · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · active · Spark: yes · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · Spark: yes · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · Spark: yes · [rules](./code-skill/references/spark-small-code.md)

## Install

1. Put the eight Skill folders under `~/.codex/skills/`.
2. Merge [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into `~/.codex/AGENTS.md`.
3. Start Codex normally; no lifecycle hook is installed.

**Privacy:** The mirror excludes auth, secrets, private ledgers, routing history, caches, raw prompts/results, receipts, and work artifacts; every publish runs a safety scan.

**Mirrors:** `qin-codex-skills` · `auto-best-model`

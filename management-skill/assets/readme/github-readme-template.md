<div align="center">

# 🚀 Auto Best Model

**Codex-only · finish the job first · verify afterward in a separate background task**

[中文说明](./README.zh.md)

Saved highest-family quality ladder · refreshed only when you request a local model update

Ordinary Auto starts from the task-strategy quality pair, not Sol-ultra · Spark is schedule-branch-only

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
4. **Ending reports PASS or the exact failure.** It does not ask the user questions, wait, poll, call heavy APIs, or repair inside the Ending task; a failure reopens a new repair task with a different verifier.

Main work and Ending verification are deliberately different task sessions. “Background” means the user can continue working as soon as the main result is returned—it does not mean verification is skipped.

## ⚡ Models & private learning

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Task-strategy quality ladder that retains, downgrades, or upgrades one receipt-proven rung at a time">
</picture>

- **Cold start:** Task type and complexity select a saved Luna/Terra/Sol quality pair; ordinary work never defaults to Spark or permanently stays on Sol-ultra.
- **Learning:** One receipt-valid Real PASS retains the pair; two matched PASS outcomes try one weaker rung; a quality failure upgrades one rung immediately.
- **Operational:** A zero-result failure gets one stronger fallback and is not learned as a quality failure.
- **Scheduling:** Spark is limited to independent source branches after a pre-read cost gate. Small multi-file work stays with one contextual producer when fan-out would repeat session context.
- **Memory:** Ending outcomes update broad project/Skills `Model Switch.md` pages; project/task/module/file/symbol are fields only—no hierarchy notes.

## Rules

- **Producer:** Use the saved task-strategy pair; 1 PASS retains, 2 matched PASS descend one rung, and quality failure climbs one rung.
- **Prompt:** Reusable prompts and durable AI instructions load Prompt Skill.
- **Route:** Delegate only on explicit request or current end-to-end proof.
- **Deliver:** Finish and return the completed main result before background verification.
- **Verify:** Launch a separate, nonblocking `End Task-<task name>` after delivery; first-result time excludes it.
- **Files:** Recall project/module/file history before editing; record the verified change after.
- **Memory:** Change history is local JSONL + optional Obsidian; private learning uses broad project/Skills `Model Switch.md`: fields only; no hierarchy notes.
- **Models:** Use saved JSON; explicit model update refreshes the highest GPT family; Spark is schedule-only; missing cache preserves the list.
- **Privacy:** Secrets, raw prompts/results, receipts, ledgers, caches, and work artifacts stay local.

## 📊 Real adaptive benchmark: finish first, verify in background

Both arms enter `gpt-5.6-sol | ultra`. **Without skill** finishes and stops; verification cost is **0**. **With skill** executes the task on the receipt-proven dynamic pair, returns it, then launches a separate read-only Ending task that never blocks delivery.

![Six real A/B pairs comparing Direct task, Auto task, and striped Auto-only Ending cost](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

| Tier | Auto task pair | Direct task | Auto task | Separate Ending | Auto task + check | Task savings | Whole savings |
|---|---|---:|---:|---:|---:|---:|---:|
| Simple · 4 tests | Terra-medium | 343,459 / 131.842s | 200,522 / 52.861s | 78,818 / 18.864s | 279,340 / 71.725s | **41.617% tokens / 59.906% time** | **18.669% / 45.598%** |
| Medium · 6 tests | Terra-high | 472,575 / 199.180s | 211,128 / 56.713s | 94,741 / 23.940s | 305,869 / 80.653s | **55.324% tokens / 71.527% time** | **35.276% / 59.507%** |
| Complex · 3 sources | Luna-low · one producer | 451,856 / 137.654s | 141,012 / 40.999s | 96,997 / 23.709s | 238,009 / 64.708s | **68.793% tokens / 70.216% time** | **47.326% / 52.992%** |
| **All 6 pairs** | **receipt-proven dynamic pairs** | **1,267,890 / 468.676s** | **552,662 / 150.573s** | **270,556 / 66.513s** | **823,218 / 217.086s** | **56.411% tokens / 67.873% time** | **35.072% / 53.681%** |

**Why the complex win is now large:** v34 estimates session-context cost before reading sources. The 68,483-byte complex fixture estimated **53,121 input tokens** for one producer versus **125,121** for a three-session schedule, so Auto correctly chose one Luna-low producer. Fan-out remains available for context pressure above 180,000 bytes or an explicit latency-critical parallel contract.

**Correctness:** 12/12 exact results, all Mini Tests/gates, and 6/6 Ending audits passed, with 0 retry/fallback/repair. The common Sol-ultra dispatcher is excluded from the requested task/check worlds but disclosed in the full report as **404,598 tokens / 361.038s**. Two pairs per tier confirm this change, not performance admission. Logical tokens are not billing tokens.

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

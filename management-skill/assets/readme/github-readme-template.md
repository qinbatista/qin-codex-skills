<div align="center">

# 🚀 Auto Best Model

**Codex-only · score every task · finish first · Ending only for real evidence**

[中文说明](./README.zh.md)

Saved highest-family quality ladder · refreshed only when you request a local model update

Small 0–24 low-risk edits try Spark-low after same-session outcome gate · larger work uses the saved quality ladder

</div>

## 🔄 Core flow

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow.svg" alt="Core result-first lifecycle">
</picture>

## ✅ Finish first. End only when there is real evidence.

Lifecycle:

1. **Score every submission from 0–100, load the relevant Skills, then finish the requested job.** For code, run exactly one smallest local Quick Check.
2. **Return the completed result immediately.**
3. **A result emits `ending-required` only when it exposes `real_test`, `information_update`, or `memory_update`; a no-surface result records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update`, regardless of score, risk, or stage count.** Surface, not score/risk/stage count, decides Ending creation. A low-risk, single-result small task with no surface also skips Ending. Producer publishes `CODE READY` after Quick Check; broad tests/builds/UI/full lint/log cleanup/release gates/repeated review never block the first result.
4. **The one Ending runs the smallest real/completion checks and one terminal closeout; all required checks must PASS.** `gpt-5.3-codex-spark|xhigh` is sole controller. It runs deterministic checks; saved Terra/Sol `ENDING_CHECK_WORKER` nodes run semantic checks. Workers read listed Skills, write evidence, and never edit, repair, route, or own lifecycle. Create exactly one global-only projectless `End Task-<task name>` with `create_thread.target={"type":"projectless"}`; the origin project stays execution context and is never attached to the thread. `list_threads` readback must show `projectId=null` or absent before acknowledgement. Project/current-task/same-task-subtask placement or missing readback is BLOCKED. Failure sends exact evidence through `codex_app__send_message_to_thread` to the immutable origin for a fresh Spark-first Ending. PASS/FAIL/BLOCKED stays visible; the 0–100 score only scopes checks. Controller unavailability permits the registry-floor `gpt-5.6-luna|low` fallback. Reuse a current immutable release report by checking its digest and final state. Closeout writes routing classification/model history; nothing auto-archives or deletes itself.

## ⚡ Models & private learning

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Receipt-proven model routing">
</picture>

- **Cold start / entry-aware:** Step-capability/difficulty history chooses the lowest correct pair. Sol/high may route down; Luna-max/lower may route up. Without a match, start at or below entry; eligible 0–24 work tries Spark-low only after the same-session outcome gate.
- **Learning:** A receipt-valid Real PASS retains the pair; two matched PASS outcomes may try one weaker rung; quality failure upgrades one rung. Recovered pairs are reused for exact matches; implementation and local-test steps keep separate histories.
- **Operational:** A zero-result failure gets one stronger fallback and is not learned as a quality failure.
- **Scheduling:** Compound requests split into quantifiable owned steps; each step routes independently. Two or three read-only sources are cost-admitted before reads; dependent multi-file work stays with one contextual producer.
- **Memory:** Change history is local JSONL + optional Obsidian; Native project → Model Switch → category → shared-category links hold every terminal Ending record; no JSON sidecar or full-history read. Receipt-backed outcomes may move routing; known assignments without receipts remain visible, non-learning observations; context kept as fields.

## Rules

- **Producer:** Show score/band and entry/selected route; reuse the frozen lowest-correct pair. Two PASS descend; quality FAIL ascends.
- **Prompt:** Reusable prompts and durable AI instructions load Prompt Skill.
- **Route:** Delegate only on explicit request or current end-to-end proof.
- **Deliver:** Finish and return the completed main result before background verification.
- **Verify:** real_test/information_update/memory_update => Ending; else record skip. Spark-xhigh; workers check semantics; PASS.
- **Files:** Recall project/module/file history before editing; record the verified change after.
- **Memory:** Local JSONL + optional Obsidian; project/module + code symbols required.
- **Models:** Use saved ladder; explicit update refreshes highest GPT family; small edits pass same-session gate before Spark-low; missing cache preserves it.
- **Privacy:** Secrets, raw prompts/results, receipts, ledgers, caches, and work artifacts stay local.

## 📊 Real adaptive benchmark: finish first, verify in background

Frozen v48: **Without skill** `gpt-5.6-sol | ultra`; **With skill** `gpt-5.6-luna | max` entry. Primary is complete selected execution; entry/controller, failures, first-result; Ending separate.

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Current Direct versus Auto benchmark: all four tiers lower complete steady-state execution time and logical tokens; Ending is shown after and excluded from the primary metrics"></picture>

**10 A/B pairs · 20 runs · 20/20 expected results and evidence gates PASS · 4/4 Sol-entry route probes PASS · 0 retries/fallbacks/repairs**

| Tier | Direct steady tokens | Auto steady tokens | Saved | Direct steady execution | Auto steady execution | Saved |
|---|---:|---:|---:|---:|---:|---:|
| Simple | 146,062 | 94,622 | **+35.218%** | 79.212s | 30.568s | **+61.410%** |
| Standard | 73,474 | 47,806 | **+34.935%** | 25.346s | 16.588s | **+34.554%** |
| Complex | 644,587 | 87,297 | **+86.457%** | 65.990s | 20.642s | **+68.720%** |
| Advanced | 788,882 | 88,074 | **+88.836%** | 97.144s | 26.736s | **+72.478%** |
| **All** | **1,653,005** | **317,799** | **+80.774%** | **267.692s** | **94.534s** | **+64.686%** |

**Result: every tier and the aggregate lower both primary metrics.** Execution saved 173.158s and 1,335,206 logical tokens. First result was slower overall (`265.243s → 294.040s`): simple/standard lost to routing overhead, complex tied, advanced won. Ending stays after the primary benchmark and is excluded (`0.687s` Direct, `0.691s` Auto, `1.378s` combined). Logical tokens are not billing tokens; this cohort is not universal.

[Read the exact v48 report.](./task-analyze-skill/TEST_AND_BENCHMARK.md) · [Open sanitized benchmark evidence.](./task-analyze-skill/assets/model-routing-benchmark-example.json)
**Latest routing check (2026-08-19):** **46/46 ×100=4,600; 0.0872 ms median; 417.156 ms total.** Local-only classifier. Release: 31/31, 1,696/1,696; projectless Ending PASS.

## 🧩 Eight public Skills

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — route strategy, benchmarks, and admission.
- [`Workflow`](./workflow-skill/SKILL.md) — admitted locked-route execution.
- [`Prompt`](./prompt-skill/SKILL.md) — reusable prompt and durable AI-instruction gate.
- [`Code`](./code-skill/SKILL.md) — Python, C#, Unity C#, and registered code domains.
- [`Project Memory`](./project-memory-skill/SKILL.md) — mandatory project/module/method coverage, file recall, and verified records.
- [`Verify`](./verify-skill/SKILL.md) — post-result Real Verify and regression evidence.
- [`Optimization`](./optimization-skill/SKILL.md) — stable repeated work into reusable tools.
- [`Management`](./management-skill/SKILL.md) — private profiles and public mirror management.

## 🛠️ Registered execution domains

<!-- EXECUTION_DOMAIN_TABLE -->

## Install

1. Put the eight Skill folders under `~/.codex/skills/`.
2. Deploy [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into both `~/.codex/AGENTS.md` and the host-discoverable user-level `~/AGENTS.md`.
3. Start Codex normally; no lifecycle hook is installed.

**Privacy:** The mirror excludes auth, secrets, private ledgers, routing history, caches, raw prompts/results, receipts, and work artifacts; every publish runs a safety scan.

**Mirrors:** `qin-codex-skills` · `auto-best-model`

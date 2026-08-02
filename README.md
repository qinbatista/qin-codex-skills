<div align="center">

# 🚀 Auto Best Model

**Codex-only · score every task · finish the job first · prove it with mandatory Ending tasks**

[中文说明](./README.zh.md)

Saved highest-family quality ladder · refreshed only when you request a local model update

Small low-risk edits scoring 0–24 try Spark-low first · larger work uses the saved quality ladder

</div>

## 🔄 Core flow

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow.svg" alt="Core flow: score and finish the main job, then run mandatory scored Ending tasks for independent real checks">
</picture>

## ✅ Finish first. Run mandatory real verification.

This is the lifecycle’s most important structural rule:

1. **Score every submission from 0–100, then finish the requested job** and run the proportional implementation check.
2. **Return the completed result immediately.** The user is not held inside a verifier, poll loop, or repair cycle.
3. **Start one scored/model-routed global projectless `End Task-<task name>-<check>` per real check.** Absolute paths provide access without project membership.
4. **Every Ending runs its assigned real check and all required checks must PASS.** PASS writes durable evidence, then self-archives; the archive may end the turn. FAIL/BLOCKED stays visible; failure creates a projectless Fix Task with the exact error, then a fresh End Task reruns the check, for up to three repairs.

Main work and Ending verification are deliberately different task sessions. A summary is never verification: heavy changes need real tests, API evidence, builds, renders, or visual checks appropriate to the change.

## ⚡ Models & private learning

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Task-strategy quality ladder that retains, downgrades, or upgrades one receipt-proven rung at a time">
</picture>

- **Cold start / entry-aware:** Exact step-capability fingerprint plus difficulty history chooses the lowest correct pair. Sol/high may route down; Luna-max/lower may route up. Without a match, start at or below entry; eligible 0–24 work still tries Spark-low.
- **Learning:** A receipt-valid Real PASS retains the pair; two matched PASS outcomes may try one weaker rung; quality failure upgrades one rung. A recovered stronger pair is reused directly for the next exact match, while implementation and local-test steps keep separate histories.
- **Operational:** A zero-result failure gets one stronger fallback and is not learned as a quality failure.
- **Scheduling:** Compound requests split into quantifiable owned steps; each step routes independently. Two or three read-only sources are cost-admitted before reads; dependent multi-file work stays with one contextual producer.
- **Memory:** Ending outcomes update broad project/Skills `Model Switch.md` pages; project/task/module/file/symbol are fields only—no hierarchy notes.

## Rules

- **Producer:** Show score/band and entry/selected route; reuse the frozen lowest-correct pair. Two PASS descend; quality FAIL ascends.
- **Prompt:** Reusable prompts and durable AI instructions load Prompt Skill.
- **Route:** Delegate only on explicit request or current end-to-end proof.
- **Deliver:** Finish and return the completed main result before background verification.
- **Verify:** Mandatory: one scored/model-routed End Task per independent check; all must PASS. FAIL → Fix Task + fresh End Task, up to three.
- **Files:** Recall project/module/file history before editing; record the verified change after.
- **Memory:** Change history is local JSONL + optional Obsidian; private learning uses broad project/Skills `Model Switch.md`: fields only; no hierarchy notes.
- **Models:** Use saved ladder; explicit update refreshes the highest GPT family; eligible small edits prioritize Spark-low; missing cache preserves it.
- **Privacy:** Secrets, raw prompts/results, receipts, ledgers, caches, and work artifacts stay local.

## 📊 Real adaptive benchmark: finish first, verify in background

Current frozen v46 compares **Without skill** fixed at `gpt-5.6-sol | ultra` with **With skill** entering at `gpt-5.6-luna | max`, then routing each step from frozen history. Every adaptive child/graph is counted; only the Luna entry controller is excluded.

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Current Direct versus Auto benchmark: every result and Ending passes, while the strategy performance gate fails"></picture>

**6 A/B pairs · 12 runs · 12/12 exact results and 12/12 Endings PASS · 0 retries · 0 fallbacks · 0 repairs**

| Tier | Direct median tokens | Auto median tokens | Paired token savings | Direct first result | Auto first result | Paired time savings |
|---|---:|---:|---:|---:|---:|---:|
| Simple | 25,881.5 | 29,091.5 | -30.064% | 13.430s | 19.831s | -50.694% |
| Medium | 16,366 | 36,632.5 | -123.834% | 10.545s | 34.323s | -225.472% |
| Complex | 263,445.5 | 138,267 | **+44.428%** | 32.375s | 56.927s | -79.224% |

**Measured result: correctness PASS; strategy-performance FAIL.** Aggregate task tokens fell 33.269%, driven by complex work, but Auto was 97.127% slower overall and simple/medium both regressed. The evidence rejects a universal savings claim; logical tokens are not billing tokens.

[Read the exact v46 report.](./task-analyze-skill/TEST_AND_BENCHMARK.md) · [Open sanitized benchmark evidence.](./task-analyze-skill/assets/model-routing-benchmark-example.json)

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

- `general` · general · `workflow-skill` · active · Spark schedule: no · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · Spark schedule: source-eligible · [rules](./code-skill/references/spark-small-code.md)

## Install

1. Put the eight Skill folders under `~/.codex/skills/`.
2. Merge [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into `~/.codex/AGENTS.md`.
3. Start Codex normally; no lifecycle hook is installed.

**Privacy:** The mirror excludes auth, secrets, private ledgers, routing history, caches, raw prompts/results, receipts, and work artifacts; every publish runs a safety scan.

**Mirrors:** `qin-codex-skills` · `auto-best-model`

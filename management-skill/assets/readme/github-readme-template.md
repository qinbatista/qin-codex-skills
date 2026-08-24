<div align="center">

# 🚀 Auto Best Model

**Codex-only · score every task · finish first · Ending only for real evidence**

**Why use it:** fast small tasks, the lowest-correct model for harder work, result-first delivery, private learning, and independent evidence. Saved highest-family quality ladder · refreshed only when you request a local model update · Small 0–24 low-risk edits try Spark-low after same-session outcome gate · larger work uses the saved quality ladder

| Score | Band | Default behavior |
|---:|---|---|
| 0–24 | Simple | Eligible small, low-risk work tries `gpt-5.3-codex-spark|low` after the same-session outcome gate |
| 25–49 | Standard | Saved lowest-correct quality pair |
| 50–74 | Complex | Capability-aware saved pair; dependent work stays contextual |
| 75–100 | Advanced | Stronger saved pair and compound-task graph when needed |

**Frozen v48 benchmark:** Direct `gpt-5.6-sol|ultra` → Auto Best Model entry `gpt-5.6-luna|max`; 20 runs, 0 retries/fallbacks/repairs, 4/4 Sol-entry probes PASS. Steady execution `267.692s → 94.534s` (**+64.686%**); logical tokens `1,653,005 → 317,799` (**+80.774%**).

[中文说明](./README.zh.md)

</div>

## 🔄 Core flow

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow.svg" alt="Score and finish the result first; create one independent projectless Ending only for real evidence">
</picture>

## ✅ Finish first. End only when there is real evidence.

1. Score every task 0–100, load relevant Skills, and finish the requested result. Code runs one smallest Quick Check, then returns `CODE READY`.
2. Only `real_test`, `information_update`, or `memory_update` emits `ending-required`; otherwise record `intentionally_skipped_simple_task` and `ending_skip_reason=no_real_test_or_information_or_memory_update`. A low-risk, single-result small task also skips Ending when it has no surface.
3. Create exactly one global-only projectless `End Task-<task name>` on `gpt-5.3-codex-spark|xhigh` with `create_thread.target={"type":"projectless"}`. `list_threads` readback must show `projectId=null` or absent. Project/current-task/same-task-subtask placement or missing readback is BLOCKED; the 0–100 score only scopes checks. Controller unavailability permits the registry-floor `gpt-5.6-luna|low` fallback.
4. The one Ending runs the smallest real/completion checks and one terminal closeout; all required checks must PASS. Terra/Sol workers write semantic evidence but never edit or repair. Failure returns exact evidence to the immutable origin. Reuse a current immutable release report by checking its digest and final state. PASS/FAIL/BLOCKED stays visible; closeout writes routing classification/model history, and nothing auto-archives or deletes itself.

## ⚡ Models & private learning

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Receipt-backed lowest-correct model routing">
</picture>

- **Cold start:** Step capability and difficulty history choose the lowest-correct pair; Sol/high may descend and Luna-max/lower may upgrade.
- **Learning:** One Real PASS retains a pair; two matched PASS results may trial one rung down; quality failure ascends one rung.
- **Operational:** A zero-result failure gets one stronger fallback and is not learned as a quality failure; compound steps route independently.
- **Memory:** Change history is local JSONL + optional Obsidian. Native project → Model Switch → category → shared-category links hold records; no JSON sidecar or full-history read; context kept as fields.

## Rules

- **Producer:** Show score/band and route; reuse the frozen lowest-correct pair.
- **Prompt:** Reusable prompts and durable AI instructions load Prompt Skill.
- **Route:** Delegate only on explicit request or current end-to-end proof.
- **Deliver:** Finish and return the main result before background verification.
- **Verify:** Real surfaces create Ending; no surface records the explicit skip.
- **Files:** Recall project/module/file history before editing; record the verified change after.
- **Memory:** Local JSONL plus optional Obsidian; require project/module and code symbols.
- **Models:** Use saved ladder; explicit update refreshes highest GPT family; missing cache preserves it.
- **Privacy:** Secrets, raw prompts/results, receipts, ledgers, caches, and work artifacts stay local.

## 📊 Real adaptive benchmark: finish first, verify in background

Frozen v48 compares Direct `gpt-5.6-sol|ultra` with Auto Best Model entering on `gpt-5.6-luna|max`. Primary metrics count clean steady selected execution; other overhead stays separate.

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Frozen v48 Direct versus Auto benchmark across four score bands"></picture>

**10 A/B pairs · 20 runs · 20/20 expected results and evidence gates PASS · 4/4 Sol-entry route probes PASS · 0 retries/fallbacks/repairs**

| Band | Direct tokens | Auto tokens | Token saving | Direct time | Auto time | Time saving |
|---|---:|---:|---:|---:|---:|---:|
| Simple | 146,062 | 94,622 | **+35.218%** | 79.212s | 30.568s | **+61.410%** |
| Standard | 73,474 | 47,806 | **+34.935%** | 25.346s | 16.588s | **+34.554%** |
| Complex | 644,587 | 87,297 | **+86.457%** | 65.990s | 20.642s | **+68.720%** |
| Advanced | 788,882 | 88,074 | **+88.836%** | 97.144s | 26.736s | **+72.478%** |
| **All** | **1,653,005** | **317,799** | **+80.774%** | **267.692s** | **94.534s** | **+64.686%** |

**Result: every tier and the aggregate lower both primary metrics.** First result was slower overall (`265.243s → 294.040s`). Ending stays after the primary benchmark and is excluded (`0.687s` Direct, `0.691s` Auto, `1.378s` combined). Logical tokens are usage proxies, not billing tokens; this frozen cohort is not universal. The [method report](./task-analyze-skill/TEST_AND_BENCHMARK.md) is currently labeled v47; use the [sanitized v48 JSON evidence](./task-analyze-skill/assets/model-routing-benchmark-example.json) for exact v48 values until alignment is repaired.

## 🧩 Eight public Skills

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — score, route, benchmark, and admit.
- [`Workflow`](./workflow-skill/SKILL.md) — execute admitted locked routes.
- [`Prompt`](./prompt-skill/SKILL.md) — govern reusable prompts and durable AI instructions.
- [`Code`](./code-skill/SKILL.md) — govern Python, C#, Unity C#, and registered code domains.
- [`Project Memory`](./project-memory-skill/SKILL.md) — cover, recall, and record verified project changes.
- [`Verify`](./verify-skill/SKILL.md) — run post-result Real Verify and regression evidence.
- [`Optimization`](./optimization-skill/SKILL.md) — turn stable repeated work into tools.
- [`Management`](./management-skill/SKILL.md) — manage private profiles and the public mirror.

## 🛠️ Registered execution domains

<!-- EXECUTION_DOMAIN_TABLE -->

## Install or update

Maintainer-gated releases install/update by fresh replacement without unit, platform, regression, parity, attestation, or Ending validation.

- **macOS/Linux, first install or update:** `stage="$(mktemp -d)" && git clone --depth 1 https://github.com/qinbatista/qin-codex-skills.git "$stage/qin-codex-skills" && python3 "$stage/qin-codex-skills/management-skill/scripts/sync_global_skills.py" deploy --source-dir "$stage/qin-codex-skills" && rm -rf "$stage"`.
- **Windows PowerShell, first install or update:** `$ErrorActionPreference='Stop'; $stage=Join-Path $env:TEMP ("qin-codex-skills-"+[guid]::NewGuid()); try { git clone --depth 1 https://github.com/qinbatista/qin-codex-skills.git $stage; if ($LASTEXITCODE) { throw 'clone failed' }; py -3 "$stage\management-skill\scripts\sync_global_skills.py" deploy --source-dir $stage; if ($LASTEXITCODE) { throw 'deploy failed' } } finally { if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force } }`. Preserves unrelated Skills and private `task-analyze-skill/local/` state.

**Privacy:** The public mirror contains exactly the eight Skills above and excludes auth, secrets, private ledgers, routing history, caches, raw prompts/results, receipts, and work artifacts; every publish runs a safety scan. **Mirrors:** `qin-codex-skills` · `auto-best-model`

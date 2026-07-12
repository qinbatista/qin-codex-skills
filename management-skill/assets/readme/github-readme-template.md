<div align="center">

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/qin-codex-skills-hero-mobile.svg">
  <img src="./management-skill/assets/readme/qin-codex-skills-hero.svg" alt="qin-codex-skills hookless inline workflow">
</picture>

# qin-codex-skills

**⚡ Inline by default · 🧭 route only when proven · 📣 present the result immediately · 🌙 verify and learn afterward**

[![Skills](https://img.shields.io/badge/public_skills-7-38bdf8)](#-seven-independent-skills)
[![Entry](https://img.shields.io/badge/entry-hookless_inline-2dd4bf)](#-hookless-first-result)
[![Proof](https://img.shields.io/badge/benchmark_v5-historical-f59e0b)](#-generated-real-ab)

</div>

## ✨ Hookless first result

The tiny policy in `AGENTS.md` applies to every task. Ordinary work stays on the **current user model**: use the fewest tool rounds and narrowest sufficient evidence, finish the requested work, and present the completed result immediately. No hook, route preamble, Task Analyze load, Workflow load, child model, receipt, memory search, foreground verifier, or model verifier is added by default.

Every reusable prompt or durable AI-instruction task loads [`Prompt`](./prompt-skill/SKILL.md) inline on the current model; ordinary non-prompt prose does not trigger it.

Load full [`Task Analyze`](./task-analyze-skill/SKILL.md) and [`Workflow`](./workflow-skill/SKILL.md) only for an explicit routing/model request, routing maintenance, or a complex dependency graph whose complete strategy has passed performance admission. Missing evidence means inline.

**First Result Principle:** finish requested work → present the completed result immediately → run genuinely needed Real/optimization/record work in Ending Task. First-result time stops at presentation and excludes Ending. A later correctness failure notifies, reopens, and repairs the task.

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/task-lifecycle-mobile.svg">
  <img src="./management-skill/assets/readme/task-lifecycle.svg" alt="Inline task or admitted route presenting the completed result before Ending Real">
</picture>

## 🧩 Seven independent skills

| Skill | Responsibility |
|---|---|
| 🧭 [`Task Analyze`](./task-analyze-skill/SKILL.md) | Explicit/admitted model strategy, topology, and performance decision. |
| 🗺️ [`Workflow`](./workflow-skill/SKILL.md) | Execute an admitted locked graph and release its first result. |
| ✍️ [`Prompt`](./prompt-skill/SKILL.md) | 100% global gate for reusable prompts and durable AI instructions; ordinary prose is excluded. |
| 💻 [`Code`](./code-skill/SKILL.md) | Python, C#, Unity C#, probes, expandable domains, and the Spark obvious-only route. |
| 🧪 [`Verify`](./verify-skill/SKILL.md) | Post-result Real, visual, UI, artifact, and regression proof. |
| ⚡ [`Optimization`](./optimization-skill/SKILL.md) | Turn stable repeated work into smaller scripts, references, assets, or templates. |
| 🔐 [`Management`](./management-skill/SKILL.md) | Private learning, profiles, README generation, privacy checks, and the seven-skill mirror. |

## 🤖 Dynamic model + effort

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Dynamic model and effort learning with inline fallback">
</picture>

Roles are cold-start hints, not permanent code/writing mappings. The expandable ladder is `Spark-low` for eligible tiny work, then every Luna effort, Terra effort, and Sol effort through `Sol-ultra`. **Downgrade effort first, then model; upgrade in reverse.** Correctness gates eligibility, Real-passing experience freezes the best pair, and verified failure reopens its boundary.

No foreground task is sacrificed for exploration. A delegated pair must be frozen, Real-passing, and `trial=false`; otherwise the current model works inline.

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-experience-mobile.svg">
  <img src="./management-skill/assets/readme/model-experience.svg" alt="Private condition-keyed model experience and lazy memory">
</picture>

Private `task-analyze-skill/local/adaptive-routing/model_experience.json` is condition-keyed and never mirrored. Ordinary tasks do not search memory. Full routing performs one bounded `related-memory` lookup only when prior requirements or failures matter; after Real Verify, an optional sanitized `TaskModelExperience/` note may be written. Missing memory is a no-op.

## 🚦 Strategy admission

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/runtime-receipt-mobile.svg">
  <img src="./management-skill/assets/readme/runtime-receipt.svg" alt="Receipt and generated-gate evidence for complete strategy cost">
</picture>

Delegation needs at least six comparable Real-passing pairs for the same condition. It has no arbitrary savings-percentage target: logical task tokens must have lower Global cohort totals and raw medians with non-negative paired savings. Simple timing stays inside the Direct cohort's measured noise envelope; Medium requires lower totals/raw medians and a strict majority of faster pairs; Complex time is diagnostic. Keep optimizing only while repeated evidence exposes deterministic waste, then stop when the remaining difference is runtime noise or no correctness-preserving change remains. The comparison includes entry/controller, children, retries, and all foreground execution through result presentation—not producer-only cost. Ending/verification time and tokens are separate diagnostics. Missing, stale, incomplete, cross-workload, or negative evidence stays inline. The A/B below evaluates the always-loaded **inline bootstrap**, not child-model delegation.

Benchmark manifests and summaries come from the generated receipt/source/expected-result gate. Before publication, the exporter re-evaluates every run from raw files and exact-matches the regenerated evidence; missing, stale, or tampered raw evidence fails closed. This replaced earlier hand-authored manifests that could incorrectly label mismatched or incomplete work as complete.

## 📊 Generated real A/B

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg">
  <img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Historical benchmark v5 for simple, medium, and complex Global strategy behavior">
</picture>

Benchmark v5 predates the 2026-07-12 global Prompt gate, so it is historical evidence—not proof of the current exact configuration. It used the same frozen source, workload, sandbox, `config.toml`, model cache, memory snapshot, acceptance, and `gpt-5.6-sol | ultra` in both arms; only the Direct-versus-Global `AGENTS.md` treatment differed. Direct used raw `--direct-task`; Global used raw `--bootstrap-task`. Twelve runs formed six A/B pairs, two per tier. Generated gates verified every selected result and receipt with **0 retries, 0 fallbacks, and 0 repairs**. This is an optimization-confirmation cohort; the separate delegation gate still requires six pairs for one exact condition.

| Tier | Pairs | Task tokens, Direct → Global | Total saving · wins | First-result time, Direct → Global | Total saving · wins | Result |
|---|---:|---:|---:|---:|---:|---|
| Simple | 2 | `118,821 → 95,467` | **19.655% · 1/2** | `26.760s → 27.913s` | **-4.309% · 1/2** | ✅ noise-bound |
| Medium | 2 | `281,493 → 98,341` | **65.064% · 2/2** | `58.012s → 39.010s` | **32.755% · 2/2** | ✅ improved |
| Complex | 2 | `1,133,713 → 154,543` | **86.368% · 2/2** | `298.277s → 203.265s` | **31.854% · 2/2** | ✅ improved |

> **Historical cohort: Global used 77.292% fewer task tokens and reached first results 29.464% faster across the six selected pairs.** Medium won both pairs after member-anchored reads replaced class/call-site overread. Simple saved tokens and its time difference stayed inside measured Direct variance; Complex time remained diagnostic but also improved.

This records one controlled historical cohort, not the current exact configuration, universal per-task dominance, or six-pair delegation admission. Runtime varies, and a task already executed optimally may have nothing left to remove. “Task tokens” include cached input, exclude Ending/verification sessions, and are an operational usage measure—not billing tokens, price, or cryptographic attestation. [`Sanitized evidence`](./task-analyze-skill/assets/model-routing-benchmark-example.json) contains the publishable gate summary; raw prompts, paths, session IDs, and receipts stay local.

## 🧪 Verify after the result

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/verification-topologies-mobile.svg">
  <img src="./management-skill/assets/readme/verification-topologies.svg" alt="Completed result presented before post-result Ending Real verification">
</picture>

| Stage | Timing | Purpose |
|---|---|---|
| 📣 Result | Immediately when requested work is complete | Present the completed result; the first-result clock stops here. |
| 🌙 Ending Real | After presentation | Exact, syntax, compile, focused I/O, regression, integration, visual replay, optimization proof, and verified learning when needed. |

Obvious reversible actions execute tool-only, then Ending Real checks the stop state after presentation. Graduated examples grow from opening Chrome → opening YouTube → searching CCTV → building a YouTube-like site. The last has a real dependency graph, but it still stays inline unless the complete delegated strategy is performance-admitted.

<!-- EXECUTION_DOMAIN_TABLE -->

Add Python, C#, Unity C#, or another domain through the [`router extension guide`](./task-analyze-skill/references/router-extension-guide.md); keep owner, reference, style, safety floor, and tests explicit.

## 🛠️ Install + privacy

1. Put exactly the seven public skill folders under `~/.codex/skills/`.
2. Merge [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into `~/.codex/AGENTS.md`.
3. Start tasks normally—no lifecycle hook is installed.

The mirror excludes `local/` learning, auth, secrets, state databases, caches, raw prompts/results, receipts, logs, and work artifacts. Pull preserves unrelated local skills. Publishing requires an explicit current user request and a clean public-safety scan.

Useful contracts: [`Task Analyze validator`](./task-analyze-skill/scripts/validate_task_analyze_skill.py) · [`Workflow validator`](./workflow-skill/scripts/validate_workflow_skill.py) · [`receipt runner`](./task-analyze-skill/scripts/model_execution_receipt.py) · [`mirror`](./management-skill/scripts/sync_global_skills.py)

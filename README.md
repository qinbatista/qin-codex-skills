<div align="center">

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/qin-codex-skills-hero-mobile.svg">
  <img src="./management-skill/assets/readme/qin-codex-skills-hero.svg" alt="qin-codex-skills hookless workflow">
</picture>

# qin-codex-skills

**🧭 Analyze once · 🤖 route per node · 🧪 prove the result · 🌙 finish deeply**

[![Skills](https://img.shields.io/badge/public_skills-6-38bdf8)](#-six-independent-skills)
[![Entry](https://img.shields.io/badge/entry-hookless_100%25-2dd4bf)](#-hookless-first-result-principle)
[![Proof](https://img.shields.io/badge/benchmark-honest-f97316)](#-real-receipt-backed-ab)

</div>

## ✨ Hookless First Result Principle

Every request starts at [`task-analyze-skill`](./task-analyze-skill/SKILL.md): a **hookless, 100% entry**. The user-selected entry model and effort analyze and route only; downstream work gets its own per-node `model | effort`.

**First Result Principle:** finish the task → run the smallest meaningful Mini Verify → show the basically verified result → continue deeper work in Ending Task. A later correctness failure reopens and repairs the task.

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/task-lifecycle-mobile.svg">
  <img src="./management-skill/assets/readme/task-lifecycle.svg" alt="Task Analyze through Mini Verify, result, and Ending Task">
</picture>

## 🧩 Six independent skills

| Skill | Main goal | Submodules |
|---|---|---|
| 🧭 [`Task Analyze`](./task-analyze-skill/SKILL.md) | Classify and lock every route. | entry resolver · topology · skill resolver · adaptive pair · receipt handoff |
| 🗺️ [`Workflow`](./workflow-skill/SKILL.md) | Execute the locked route and release the first result. | plan lock · runners · dependencies · Mini gate · Ending handoff |
| 💻 [`Code`](./code-skill/SKILL.md) | Deliver registry-owned code and probes. | Python · C# · Unity C# · prompt-in-code · Spark obvious-only route |
| 🧪 [`Verify`](./verify-skill/SKILL.md) | Prove results proportionally. | Mini · Real · UI/visual/artifact review · receipt match |
| ⚡ [`Optimization`](./optimization-skill/SKILL.md) | Simplify stable work without behavior drift. | scripts · references · assets · templates · independent proof |
| 🔐 [`Management`](./management-skill/SKILL.md) | Manage learning, profiles, and safe publishing. | records · auth/profile · README · privacy scan · mirror |

## 🤖 Dynamic model + effort

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="Dynamic per-node model and effort router">
</picture>

Model roles are **cold-start hints, never fixed model mappings**. Correctness comes first; verified experience finds the best pair for each similar condition, then ranks comparable Real-passing pairs by tokens and time.

| Family | Cold-start role | Rungs |
|---|---|---|
| Sol | Ambiguous architecture or difficult judgment | `low → medium → high → xhigh → max → ultra` |
| Terra | Grounded repository work and realistic testing | `low → medium → high → xhigh → max → ultra` |
| Luna | Normal bounded work | `low → medium → high → xhigh → max` |
| Spark | Obvious low-risk tiny text/code/commands | `low` only, then normal fallback |

Every non-tiny model route carries exactly `Luna-low → all Luna efforts → Terra → Sol-ultra`. Tiny eligible routes carry exactly `Spark-low + full normal fallback`; Spark-medium/high/xhigh remain capabilities, not routing rungs. **Downgrade effort then model, upgrade in reverse**, then reuse the frozen dynamic learned pair until verified failure or profile drift.

## 🧠 Learn only from verified outcomes

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-experience-mobile.svg">
  <img src="./management-skill/assets/readme/model-experience.svg" alt="Condition-keyed learning from verified outcomes">
</picture>

The private `task-analyze-skill/local/adaptive-routing/model_experience.json` ledger is **condition-keyed**, not a global ranking. It keeps prompt-free workload hashes and quality boundaries; it never enters the public mirror. Ending Real updates the same producer attempt, persists `best_pair`, and freezes unchanged profiles.

Rank tokens, then process time, then weaker rung only when two Real-passing pairs share the same exact workload hash with complete metrics. Cross-workload or incomplete evidence uses the quality boundary and makes no savings claim. Operational failures stay diagnostics, not quality learning.

Optional related-memory supplies only relevant requirements, failures, and retry lessons. If memory is missing, routing continues. After Real Verify, sanitized `TaskModelExperience/` notes may help other skills; the private ledger remains authoritative.

## 📟 Real receipt-backed A/B

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/runtime-receipt-mobile.svg">
  <img src="./management-skill/assets/readme/runtime-receipt.svg" alt="Sanitized runtime receipt with actual model, tokens, time, and status">
</picture>

A route label is not proof. Every model run emits a sanitized runtime receipt. Savings require **like-for-like** task text, inputs, working directory, user configuration, sandbox, output contract, and acceptance. Totals deduplicate entry plus descendants; time uses the critical path. Receipts are local operational evidence, not cryptographic attestation.

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg">
  <img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="Honest real benchmark showing an overall token win but slower Global execution">
</picture>

This real single-run smoke comparison used the same workload, working directory, sandbox, and user configuration in both arms. Direct ran `gpt-5.6-sol | ultra` with `LOCKED_ROUTE_NODE` bypassing only Task Analyze. Global started with the same pair, ran Task Analyze, then used its selected downstream pair. Acceptance combined deterministic output verification with local operational receipts; all six arms completed and passed.

| Workload | Direct → Global route | Correctness | Tokens, direct → global | Time, direct → global | Goal |
|---|---|---|---:|---:|---|
| Simple | Sol-ultra → Sol-ultra direct action | exact pass | `53,781 → 120,452` **(+123.968%)** | `12.612s → 52.979s` **(+320.068%)** | ❌ |
| Medium | Sol-ultra → Sol-ultra entry + Terra-high producer | exact pass | `117,772 → 178,211` **(+51.319%)** | `45.499s → 134.447s` **(+195.494%)** | ❌ |
| Complex | Sol-ultra → Sol-ultra entry + learned Sol-max producer | exact pass | `1,232,629 → 902,163` **(−26.810%)** | `325.546s → 346.572s` **(+6.459%)** | ⚠ token win only |
| **Suite** | three exact A/B pairs | **all pass** | **`1,404,182 → 1,200,826` (−14.482%)** | **`383.657s → 533.998s` (+39.186%)** | ✅ tokens · ❌ speed |

> **Suite token goal: MET — 203,356 logical runtime tokens saved. Speed goal: NOT MET — 150.341s slower.** Logical runtime tokens include cached input and are not a billing-token claim. The corrected Complex schema separates conditional-serial `resolve_structure` from parallel `extract_names`; both outputs matched the expected result exactly.

[`Sanitized evidence`](./task-analyze-skill/assets/model-routing-benchmark-example.json) records model pairs, correctness, tokens, time, controls, and suite totals. Raw receipts, prompts, results, paths, private IDs, hashes, and learner data stay local. One run is repair evidence, not a durable performance claim.

## 🧪 Verify, then finish

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/verification-topologies-mobile.svg">
  <img src="./management-skill/assets/readme/verification-topologies.svg" alt="Mini Verify before result and Real Verify in Ending Task">
</picture>

| Gate | When | Proof |
|---|---|---|
| 🧪 Mini Verify | **Before the result** | Smallest meaningful changed-line, syntax, focused I/O, schema, render, or receipt gate. |
| 🌙 Real Verify | Ending Task | Real Verify runs in background Ending Task for regression, integration, visual, replay, and learning evidence. |

Optimization needs a **different** [`verify-skill`](./verify-skill/SKILL.md) worker. If independent proof cannot run, the result is blocked—not self-certified.

## ⚡ Direct actions + extensible code

One obvious reversible action with no dependency graph stays tool-only: no child model, cached plan, fabricated receipt, or learner sample.

| Example | Route | Mini proof |
|---|---|---|
| Open Chrome | `chrome:control-chrome` | Chrome is open |
| Open YouTube | browser action | YouTube loaded |
| Search CCTV on YouTube | browser interaction | query + results match |
| Design a YouTube-like website | complex frontend route | UI, console, navigation, accessibility, visual review |

| Domain | Kind | Owner | Spark obvious-task eligible | Reference |
|---|---|---|---|---|
| `general` (active) | general | `workflow-skill` | no | [`task-analyze-skill/references/model-selection.md`](./task-analyze-skill/references/model-selection.md) |
| `python` (active) | code | `code-skill` | yes | [`code-skill/references/python-rules.md`](./code-skill/references/python-rules.md) |
| `csharp` (active) | code | `code-skill` | yes | [`code-skill/references/csharp-rules.md`](./code-skill/references/csharp-rules.md) |
| `unity_csharp` (active) | code | `code-skill` | yes | [`code-skill/references/unity-csharp-rules.md`](./code-skill/references/unity-csharp-rules.md) |
| `code_unspecified` (history-only) | code | `code-skill` | yes | [`code-skill/references/spark-small-code.md`](./code-skill/references/spark-small-code.md) |

Add Python, C#, Unity C#, or future domains through the [`router extension guide`](./task-analyze-skill/references/router-extension-guide.md). The generated table above is injected at the exact `EXECUTION_DOMAIN_TABLE` marker.

## 🛠️ Install + privacy

1. Put the exactly six public skills under `~/.codex/skills/`.
2. Merge [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) into `AGENTS.md`.
3. Start a task normally; no lifecycle hook is required.

The mirror excludes local learning, caches, work outputs, auth, secrets, raw prompts, private logs, and receipts. Editing or testing never authorizes a push; [`management-skill`](./management-skill/SKILL.md) publishes only after an explicit current request.

Useful contracts: [`route validator`](./task-analyze-skill/scripts/validate_task_analyze_skill.py) · [`workflow validator`](./workflow-skill/scripts/validate_workflow_skill.py) · [`dispatcher`](./task-analyze-skill/scripts/task_route_dispatcher.py) · [`receipt runner`](./task-analyze-skill/scripts/model_execution_receipt.py) · [`mirror`](./management-skill/scripts/sync_global_skills.py)

---

<div align="center">

**🧭 Route · 🤖 execute · 🧪 prove · ✅ show · 🌙 learn**

</div>

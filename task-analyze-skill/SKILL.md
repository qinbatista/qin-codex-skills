---
name: task-analyze-skill
description: "Use only for explicit model-routing or strategy requests, admitted delegation or dependency graphs, and Task Analyze maintenance or benchmarking. Ordinary requests remain on the already-loaded inline bootstrap regardless of apparent complexity and must not invoke this full skill."
---

# Task Analyze Skill

This is the full routing and model-strategy skill. The hookless bootstrap in `~/.codex/AGENTS.md` combines the shared Spark-first producer contract and GPT-5.6 ladder with matching project-scoped Obsidian `Projects/<project-key>/ModelExperience`; full visible routing still requires explicit activation. The mandatory post-result Ending lifecycle always applies.

Prompts beginning with `LOCKED_ROUTE_NODE` or `ENDING_TASK_WORKER` already belong to an active lifecycle and must not restart Task Analyze. An `ENDING_TASK_WORKER` does not recursively launch Ending for verification bookkeeping; if it repairs or produces a corrected artifact, that repair becomes a new result task with its own lifecycle and a different Ending verifier. Remove or relocate nested cache/fixture `SKILL.md` files under user skill folders; preserve the official `.system` subtree.

## Activation Boundary

Load this full skill only when at least one condition is true:

1. the user explicitly requests model choice, routing strategy, receipts, or an A/B benchmark;
2. the task has a real complex delegation or dependency graph that may justify another model session;
3. Task Analyze, Workflow, adaptive routing, verification routing, or their documentation is being maintained.

For anything else, stop loading routing material and use the inline bootstrap contract below. Complexity alone does not authorize delegation.

## Ordinary Inline Bootstrap

The always-loaded policy applies inline before this file would be selected:

1. Classify eligible ordinary work once from its project/task/module/file/symbol/code context. Text/code production tries Spark (`low` for easy, `high` for complex); a zero-result operational failure immediately tries the Obsidian-selected 5.6 pair. Image/mixed and exact read-only work skip Spark. Run `scripts/obsidian_adaptive_model_runner.py`; unavailable memory stays inline.
2. Use one direct task action or one direct execution surface. Batch bounded reads, edits, or commands when safe.
3. Present the completed result immediately. Do not run Mini/Fast Verify before first presentation.
4. Immediately after presentation, write a lifecycle start receipt with `verify-skill/scripts/ending_task_ledger.py` and launch an independent Ending subagent for every task level. This post-result worker is mandatory and bypasses result-producer performance admission.
5. Run isolated non-result logs, reports, and documentation alongside Real Verify when safe. Keep final project memory, shared-state writes, and verdict-dependent work ordered.
6. Final requires lifecycle `PASS` or explicit `BLOCKED`. A failure is logged before repair; repair is a new child lifecycle, its corrected result is presented, and a different Ending verifier runs again.

Prompt work is the one ordinary skill-load exception and still runs inline on the current user model. Every task that creates, reviews, edits, repairs, standardizes, tests, summarizes, optimizes, or changes a reusable prompt or durable AI instruction must load `prompt-skill` before prompt work. Ordinary prose does not trigger it merely because it is text. Prompt-in-code also loads the owning code executor. Present the completed prompt first; trials and Real Verify follow in Ending Task.

Exact-scoped read-only result work stays on the current model inline with no foreground producer subagent, route, or plan pass. For an exact named-source audit, first run one bounded `rg` per authoritative file for every exact user-named target and direct definition, then answer once. Anchor named members directly; never add enclosing-class or call-site anchors or guess identifier prefixes or families. Do not add pre-tool planning, a broad search, whole-file read, reread, or pre-result check. Present immediately, then always launch the independent Ending subagent.

When bounded multi-file evidence has an exact allowlist, make that one broad search a boundary-labelled batch across the allowed files and overread enough context to include complete target blocks and direct dependencies. If the evidence cannot be safely bounded in one output, use the smallest correctness-preserving batched chunk plan inline; never start with complete files or parallel subagents merely to avoid choosing the needed ranges.

Ordinary work must not read this full `SKILL.md`, show a pre-result route, or deliberate broadly. The compact bootstrap may invoke one receipt-backed Spark-first producer route through `scripts/obsidian_adaptive_model_runner.py`; only a zero-result operational Spark failure may start its selected 5.6 fallback. It never launches `verify-skill` before presentation. After presentation, the lifecycle ledger and independent Ending subagent are required regardless of complexity.

Eligible ordinary requests use one project-scoped Obsidian context lookup with no visible plan; exact read-only and ineligible work remain inline. After the final source read, emit the requested output immediately with no separate foreground self-review, Mini, or verification pass.

## Result-Producer Performance Admission

There are two distinct admissions. User-enabled adaptive quality learning may launch one 5.6 producer from the shared ladder even while its project/context boundary is cold or provisional. Multi-node strategy JSON routing and any claim that Global is faster or smaller still require comparable end-to-end performance evidence. Mandatory post-result Ending subagents are outside both gates.

Admission requires all of the following:

- the selected child pair is frozen, receipt-backed, Real-passing, and `trial=false`;
- prompt/inputs, cwd, sandbox, user/project configuration, frozen model-visible catalogs and memory snapshot, output contract, and acceptance match the direct cohort;
- the evidence includes the current entry pair and the complete foreground path, not only producer cost;
- correctness and metrics pass for every arm; Global foreground logical tokens have a lower cohort total and raw median with a non-negative paired-savings median; pairwise token regressions are diagnostics rather than arbitrary percentage vetoes; Simple first-result time stays inside the Direct cohort's measured median-absolute-deviation noise envelope, Medium requires lower total/raw median, non-negative paired savings, and a strict majority of faster pairs, and Complex time is diagnostic; all post-result Ending/verification time and tokens are excluded;
- evidence is complete, current, and workload-comparable.

The admitted cohort must prove fewer foreground logical tokens under those governing rules. Do not turn one chosen percentage into the optimization target: keep removing reproducible deterministic waste until repeated comparisons show only runtime noise or no correctness-preserving change remains. Cohort totals and raw medians must pass; individual regressions remain visible diagnostics. Simple timing uses its measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex timing is disclosed without vetoing a correct token-saving route. Ending Real time and tokens are diagnostic and never delay, charge, or invalidate the first presentation.

`scripts/strategy_performance.py` is the private authority for this separate decision. Its key includes the quality-profile fingerprint, current entry `model|effort`, configuration cohort, sandbox, strategy version, producer-contract version, and exact workload hash. Delegation needs at least six comparable paired samples. Every arm must have passing correctness and complete metrics. Logical tokens require a lower Global cohort total and raw median with non-negative paired-median savings. First-result latency requires lower Global cohort total/raw median, non-negative paired-median savings, and a strict majority of faster pairs; individual regressions remain diagnostics. Total-wall/Ending latency is retained only as a diagnostic. Otherwise it returns `inline_entry`.

Missing or negative performance evidence forbids a savings claim or multi-node strategy route, but it does not disable Obsidian-backed contextual quality selection. One foreground 5.6 pair may be the current cold start, one-rung downgrade, one-rung upgrade, or frozen reuse; Ending Real supplies its verdict. A suite aggregate cannot hide a losing class. None of these conditions may suppress the mandatory Ending lifecycle.

## Full Routing Preflight

Only after activation and before an admitted delegated route:

1. Call `scripts/resolve_entry_model.py` if exact observable entry metadata is needed. Preserve the verified pair or use `unverified`; never guess.
2. Perform at most one quick bounded related-memory lookup only when prior requirements or failures materially affect this explicit route, following `references/related-memory.md`. Missing memory providers are a successful no-op.
3. Classify owner/domain, safety, authority, modality, project, language, dependencies, and acceptance.
4. Apply adaptive quality admission for one producer, or performance admission for a multi-node strategy/savings claim. If neither applies, execute inline.

The entry model may either execute inline or coordinate an admitted route. There is no controller-only entry invariant.

## Human Route For Admitted Work

- **Single admitted node:** one concise human route with the exact selected `model | effort`, owner, result boundary, and post-result Ending Real Verify.
- **Complex admitted graph:** a task-specific Mermaid plus a numbered `Workflow with models` list. Show real dependencies, Main Goal Done Gate, immediate result release, and post-result Ending Task Real Verify.

Never show private schema JSON, `LOCKED_ROUTE_NODE`, environment markers, or machine plan data. The route is shown only after full routing was explicitly activated; ordinary inline work has no pre-result route.

## Model Selection

Apply owner/domain and safety floors before private experience:

- Sol: missing context, open-ended architecture, or difficult cross-system judgment.
- Terra: grounded repository, integration, testing, and evidence work.
- Luna: bounded non-code work and concise verification judgment.
Every adaptive profile reads `assets/model-capability-ladder.json`. Eligible text/code result producers try Spark first; easy uses `low`, complex uses `high`. The active quality ladder remains Luna-to-Sol. Old local `model_experience.json` stays legacy read-only. Move effort before model while downgrading and reverse that order while upgrading.

## Obsidian Adaptive Routing

The mechanism has two distinct authorities. `assets/model-capability-ladder.json` is shared and mirrorable: model ranks, supported Codex efforts, strengths, and movement policy only. Obsidian `Projects/<project-key>/ModelExperience` is the contextual experience authority, keyed by project/task/module/file/symbol/code context. Old local `model_experience.json` remains legacy read-only only and is never used for active selection or writes.

Model-quality learning is keyed by exact project/task/module/file/symbol/code context, with artifact, scope, ambiguity, modality, risk, complexity, execution domain, owning skill, and verification shape retained as supporting context. End-to-end performance admission remains a separate evidence system for strategy-level multi-node JSON and speed/token claims.

- No prior quality success: keep the route inline unless an explicit benchmark is running.
- A receipt-matched Real pass trials exactly one lower effort on the same model before moving to a weaker model; a quality failure reverses that order.
- A receipt-matched Spark quality/correctness failure is written first, then the next recommendation starts a new repair lifecycle on the contextual 5.6 pair. Operational Spark failure is quality-neutral and may fallback only before any result with zero tokens.
- A frozen matching project/code-context profile reuses its lowest Real-passing pair with `trial=false` until verified failure or material profile/policy drift.
- Cost ranking between child pairs still requires complete Real-passing evidence in the same workload cohort, but that ranking does not itself admit delegation.

Ending Real alone records receipt-backed producer pass/fail evidence to Obsidian `Projects/<project-key>/ModelExperience`; producers and ordinary runners never write learning. Operational failures remain neutral and inline execution never fabricates a receipt.

## Delegated Execution

After admission, continue through `workflow-skill` in the same task.

- One result producer uses its resolved Obsidian context through `scripts/obsidian_adaptive_model_runner.py` and `scripts/model_execution_receipt.py`; eligible text/code work tries Spark, then at most its authorized 5.6 operational fallback, and emits the first completed result without a foreground verification gate.
- `obsidian_adaptive_model_runner.py` reads learning but never writes it. Spark quality failure never triggers foreground fallback; Ending records it before a new 5.6 repair lifecycle. `strategy_performance.py` separately gates multi-node strategy JSON routing and Global-versus-Direct claims.
- A true multi-node dependency graph may save private schema-version-2 JSON with only `result` and `ending` phases, then call `scripts/task_route_dispatcher.py run-plan <plan-file>` once.
- Use exactly one execution surface per branch. Do not combine collaboration and dispatcher execution for the same work.
- Registry-owned delegated Python, C#, and Unity C# implementation or authored probes load `code-skill` and their domain rules.
- A launch/access/transport failure may use only the receipt-backed 5.6 fallback when no result was published and total tokens are zero; otherwise it stops and reopens rather than duplicating work.

For grounded JSON, present the producer result first. Ending Task may then use the matching `grounded_result_gate.py` preset for Real Verify. Pass no source root with `json-object`; source roots belong only to source-aware presets. The Real gate never delays first presentation.

## First Result And Mandatory Ending

There is no Mini/Fast Verify gate before first presentation. When the requested result is complete, show it immediately in commentary so the user can continue while Ending runs.

For a dispatched graph, enforce `run-plan` -> completed result -> show result -> `release-main-result` -> `run-ending`. For ordinary inline work, enforce result presentation -> lifecycle `start` receipt -> independent Ending subagent. Ending owns Real Verify, broader regression, optimization proof, reports, logs, related memory, and the only receipt-backed pass/fail write to Obsidian after the result. Safe isolated branches run concurrently. A correctness failure first records lifecycle error evidence and any failed durable project state, then launches a repair child with a new lifecycle. Present the corrected result and launch a different Ending verifier; never let a repair self-certify.

## Runtime Proof And A/B Policy

A model label is not proof. Delegated nodes require sanitized runtime receipts matching requested, resolved, and effective model/effort. Inline current-model execution does not fabricate a child receipt.

For strategy comparisons, keep prompt, inputs, cwd, sandbox, configuration, output contract, and acceptance identical. Count each foreground session once. User-visible performance runs from task start until the parent controller receives the flushed event emitted immediately after the atomic completed-result write; receipt finalization, telemetry, and post-result Ending Real are excluded, as are all Ending/verification tokens. Every tier requires matching correctness and fewer foreground tokens; Simple time uses the Direct cohort's measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex time is diagnostic.

Benchmark first-result authority is the controller-stamped sanitized `result-ready` event emitted immediately after the atomic result write. File polling and the child process's local monotonic clock are not timing authority; the gate requires the runner-owned receipt and evidence timestamps to match exactly.

`scripts/benchmark_suite_gate.py`—not a caller-authored manifest—derives correctness, completion, receipt/session coverage, tokens, first-result time, total-wall time, retry/fallback/repair counts, and per-tier verdicts. Overall PASS is exactly `simple AND medium AND complex`; one tier failing any cohort or correctness gate fails the suite.

## Generated Files

Put plans, prompts, receipts, logs, and benchmarks in active task/project `cache/` or `work/`. Legacy compatibility history under `local/` is read-only; active model experience belongs only in Obsidian `Projects/<project-key>/ModelExperience`. Put final deliverables only in the requested output location.

## Verification

After contract changes:

1. Run `scripts/sync_model_capabilities.py --check`.
2. Run `scripts/validate_task_analyze_skill.py` and focused tests.
3. Run Workflow validation for admitted complex routes.
4. Prove ordinary tasks present the completed result without a foreground child/model verifier or Mini, and that Ending Real begins only afterward.
5. Promote a performance claim only after like-for-like repeated evidence passes every task class independently.

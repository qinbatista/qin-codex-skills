---
name: task-analyze-skill
description: "Use only for explicit model-routing or strategy requests, admitted delegation or dependency graphs, and Task Analyze maintenance or benchmarking. Ordinary requests remain on the already-loaded inline bootstrap regardless of apparent complexity and must not invoke this full skill."
---

# Task Analyze Skill

This is the full routing and model-strategy skill. It is an individual global skill, but it is not the ordinary task bootstrap. The hookless 100% inline policy already loaded from `~/.codex/AGENTS.md` handles ordinary work without paying a separate controller turn or a foreground verification turn.

Prompts beginning with `LOCKED_ROUTE_NODE` or `ENDING_TASK_WORKER` already belong to an admitted route and must not restart Task Analyze. Remove or relocate nested cache/fixture `SKILL.md` files under user skill folders; preserve the official `.system` subtree.

## Activation Boundary

Load this full skill only when at least one condition is true:

1. the user explicitly requests model choice, routing strategy, receipts, or an A/B benchmark;
2. the task has a real complex delegation or dependency graph that may justify another model session;
3. Task Analyze, Workflow, adaptive routing, verification routing, or their documentation is being maintained.

For anything else, stop loading routing material and use the inline bootstrap contract below. Complexity alone does not authorize delegation.

## Ordinary Inline Bootstrap

The always-loaded policy applies inline before this file would be selected:

1. Execute the ordinary task on the user's current model, regardless of apparent complexity; the current model may perform the actual work and is not a route-only controller.
2. Use one direct task action or one direct execution surface. Batch bounded reads, edits, or commands when safe.
3. Present the completed result immediately. Do not run Mini/Fast Verify before first presentation.
4. After presentation, let Ending Task run one proportional Real Verify. A failure notifies the user, reopens the task, repairs, and presents the correction.

Prompt work is the one ordinary skill-load exception and still runs inline on the current user model. Every task that creates, reviews, edits, repairs, standardizes, tests, summarizes, optimizes, or changes a reusable prompt or durable AI instruction must load `prompt-skill` before prompt work. Ordinary prose does not trigger it merely because it is text. Prompt-in-code also loads the owning code executor. Present the completed prompt first; trials and Real Verify follow in Ending Task.

Exact-scoped read-only work stays on the current model inline with no subagent, route, or plan pass. For an exact named-source audit, first run one bounded `rg` per authoritative file for every exact user-named target and direct definition, then answer once. Anchor named members directly; never add enclosing-class or call-site anchors or guess identifier prefixes or families. Do not add pre-tool planning, a broad search, whole-file read, reread, or pre-result check. Present immediately; any check follows presentation in Ending Real.

When bounded multi-file evidence has an exact allowlist, make that one broad search a boundary-labelled batch across the allowed files and overread enough context to include complete target blocks and direct dependencies. If the evidence cannot be safely bounded in one output, use the smallest correctness-preserving batched chunk plan inline; never start with complete files or parallel subagents merely to avoid choosing the needed ranges.

Ordinary work must not read this full `SKILL.md`, show a pre-result route, resolve the entry model, search memory, load `workflow-skill`, launch a child model, create a receipt, or launch `verify-skill` before presenting the result merely to complete the response. Apparent complexity does not add a foreground controller, child, or verification pass.

Ordinary requests remain inline regardless of apparent complexity. Unless the request explicitly asks for routing/benchmarking and includes a concrete performance-admission check, do not deliberate about routing. After the final source read, use one reasoning pass to emit the requested output immediately. The output-producing pass is the only foreground reasoning pass, with no separate planning, self-review, Mini, or verification pass.

## End-to-End Performance Admission

Full Task Analyze still defaults to inline. A different-pair child or dispatcher is allowed only when comparable end-to-end evidence admits delegation.

Admission requires all of the following:

- the selected child pair is frozen, receipt-backed, Real-passing, and `trial=false`;
- prompt/inputs, cwd, sandbox, user/project configuration, frozen model-visible catalogs and memory snapshot, output contract, and acceptance match the direct cohort;
- the evidence includes the current entry pair and the complete foreground path, not only producer cost;
- correctness and metrics pass for every arm; Global foreground logical tokens have a lower cohort total and raw median with a non-negative paired-savings median; pairwise token regressions are diagnostics rather than arbitrary percentage vetoes; Simple first-result time stays inside the Direct cohort's measured median-absolute-deviation noise envelope, Medium requires lower total/raw median, non-negative paired savings, and a strict majority of faster pairs, and Complex time is diagnostic; all post-result Ending/verification time and tokens are excluded;
- evidence is complete, current, and workload-comparable.

The admitted cohort must prove fewer foreground logical tokens under those governing rules. Do not turn one chosen percentage into the optimization target: keep removing reproducible deterministic waste until repeated comparisons show only runtime noise or no correctness-preserving change remains. Cohort totals and raw medians must pass; individual regressions remain visible diagnostics. Simple timing uses its measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex timing is disclosed without vetoing a correct token-saving route. Ending Real time and tokens are diagnostic and never delay, charge, or invalidate the first presentation.

`scripts/strategy_performance.py` is the private authority for this separate decision. Its key includes the quality-profile fingerprint, current entry `model|effort`, configuration cohort, sandbox, strategy version, producer-contract version, and exact workload hash. Delegation needs at least six comparable paired samples. Every arm must have passing correctness and complete metrics. Logical tokens require a lower Global cohort total and raw median with non-negative paired-median savings. First-result latency requires lower Global cohort total/raw median, non-negative paired-median savings, and a strict majority of faster pairs; individual regressions remain diagnostics. Total-wall/Ending latency is retained only as a diagnostic. Otherwise it returns `inline_entry`.

Missing, stale, cross-workload, incomplete, or negative evidence means inline. Producer-only savings never authorize a child. Foreground downgrade or upgrade trials are forbidden; exploration belongs only to an explicit benchmark or authorized post-result work. A suite aggregate cannot hide a simple, medium, or complex class that loses either metric.

## Full Routing Preflight

Only after activation and before an admitted delegated route:

1. Call `scripts/resolve_entry_model.py` if exact observable entry metadata is needed. Preserve the verified pair or use `unverified`; never guess.
2. Perform at most one quick bounded related-memory lookup only when prior requirements or failures materially affect this explicit route, following `references/related-memory.md`. Missing memory providers are a successful no-op.
3. Classify owner/domain, safety, authority, modality, project, language, dependencies, and acceptance.
4. Apply performance admission. If it does not pass, execute inline and do not load Workflow.

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
- Spark-low: only obvious bounded low-risk easy low-ambiguity `tiny_text`, `tiny_code`, or `command_generation` work through `code-skill`.

Every non-tiny delegated profile retains the Luna-to-Sol ladder without Spark. Tiny eligible profiles prepend Spark-low. Move effort before model while downgrading and reverse that order while upgrading.

## Private Adaptive Routing

Personal routing evidence lives only in `local/adaptive-routing/model_experience.json` and is never mirrored. It stores controlled conditions, generalized summaries, receipt-matched producer pairs, prompt-free workload hashes, post-result Real verdicts, quality boundaries, tokens, and time—never raw prompts, results, paths, IDs, secrets, or private content.

Model-quality learning remains task/profile keyed. End-to-end performance admission is a separate decision keyed by the quality profile plus current entry pair and comparable execution conditions, because controller cost changes with the selected entry model and effort.

- No prior quality success: keep the route inline unless an explicit benchmark is running.
- Explicit benchmark exploration may trial exactly one lower effort on the same model before moving to a weaker model.
- Receipt-matched post-result Real correctness failure upgrades in reverse; operational failures remain neutral.
- A frozen exact profile reuses its Real-passing pair with `trial=false` until verified failure or profile drift.
- Cost ranking between child pairs still requires complete Real-passing evidence in the same workload cohort, but that ranking does not itself admit delegation.

Optional Obsidian `TaskModelExperience/` remains a sanitized readable projection after Real Verify. The private ledger remains model-quality authority.

## Delegated Execution

After admission, continue through `workflow-skill` in the same task.

- One result producer uses one named profile preset through `scripts/adaptive_model_runner.py`; it selects the frozen pair, invokes `scripts/model_execution_receipt.py` once, and emits the completed result immediately without a foreground verification gate.
- `adaptive_model_runner.py` checks `strategy_performance.py` before launching a child. Missing admission returns `inline_entry` without a model launch. `--benchmark-calibration` is an explicit benchmark-only evidence-collection bypass and is forbidden for ordinary foreground routing.
- A true multi-node dependency graph may save private schema-version-2 JSON with only `result` and `ending` phases, then call `scripts/task_route_dispatcher.py run-plan <plan-file>` once.
- Use exactly one execution surface per branch. Do not combine collaboration and dispatcher execution for the same work.
- Registry-owned delegated Python, C#, and Unity C# implementation or authored probes load `code-skill` and their domain rules.
- A launch or transport failure is operational evidence, not permission for an unreceipted fixed-pair fallback.

For grounded JSON, present the producer result first. Ending Task may then use the matching `grounded_result_gate.py` preset for Real Verify. Pass no source root with `json-object`; source roots belong only to source-aware presets. The Real gate never delays first presentation.

## First Result And Ending

There is no Mini/Fast Verify gate before first presentation. When the requested result is complete, show it immediately.

For a dispatched graph, enforce `run-plan` -> completed result -> show result -> `release-main-result` -> `run-ending`. Ending Task owns Real Verify, broader regression, optimization proof, reports, logs, and related memory after the result. A later correctness failure notifies the user, reopens, repairs, and presents the corrected result; do not add a new foreground Mini.

## Runtime Proof And A/B Policy

A model label is not proof. Delegated nodes require sanitized runtime receipts matching requested, resolved, and effective model/effort. Inline current-model execution does not fabricate a child receipt.

For strategy comparisons, keep prompt, inputs, cwd, sandbox, configuration, output contract, and acceptance identical. Count each foreground session once. User-visible performance runs from task start until the parent controller receives the flushed event emitted immediately after the atomic completed-result write; receipt finalization, telemetry, and post-result Ending Real are excluded, as are all Ending/verification tokens. Every tier requires matching correctness and fewer foreground tokens; Simple time uses the Direct cohort's measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex time is diagnostic.

Benchmark first-result authority is the controller-stamped sanitized `result-ready` event emitted immediately after the atomic result write. File polling and the child process's local monotonic clock are not timing authority; the gate requires the runner-owned receipt and evidence timestamps to match exactly.

`scripts/benchmark_suite_gate.py`—not a caller-authored manifest—derives correctness, completion, receipt/session coverage, tokens, first-result time, total-wall time, retry/fallback/repair counts, and per-tier verdicts. Overall PASS is exactly `simple AND medium AND complex`; one tier failing any cohort or correctness gate fails the suite.

## Generated Files

Put plans, prompts, receipts, logs, and benchmarks in active task/project `cache/` or `work/`. Keep adaptive history under `local/`. Put final deliverables only in the requested output location.

## Verification

After contract changes:

1. Run `scripts/sync_model_capabilities.py --check`.
2. Run `scripts/validate_task_analyze_skill.py` and focused tests.
3. Run Workflow validation for admitted complex routes.
4. Prove ordinary tasks present the completed result without a foreground child/model verifier or Mini, and that Ending Real begins only afterward.
5. Promote a performance claim only after like-for-like repeated evidence passes every task class independently.

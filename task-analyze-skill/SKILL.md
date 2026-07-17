---
name: task-analyze-skill
description: "Use only for explicit model-routing or strategy requests, admitted delegation or dependency graphs, and Task Analyze maintenance or benchmarking. Ordinary requests remain on the already-loaded inline bootstrap regardless of apparent complexity and must not invoke this full skill."
---

# Task Analyze Skill

This is the full routing and model-strategy skill. The hookless bootstrap in `~/.codex/AGENTS.md` combines the saved catalog-derived priority producer and highest-version quality family with matching project-scoped broad Obsidian `Model Switch.md` records; explicit multi-node routing still requires activation. The mandatory post-result Ending lifecycle always applies.

Prompts beginning with `LOCKED_ROUTE_NODE` or `ENDING_TASK_WORKER` already belong to an active lifecycle and must not restart Task Analyze. An `ENDING_TASK_WORKER` does not recursively launch Ending for verification bookkeeping; if it repairs or produces a corrected artifact, that repair becomes a new result task with its own lifecycle and a different Ending verifier. Remove or relocate nested cache/fixture `SKILL.md` files under user skill folders; preserve the official `.system` subtree.

## Entry Parent Fast Path

For eligible text/code, the current entry parent routes before loading an owning skill, project memory, task files, or implementation references. Pipe the exact task to `~/.codex/skills/task-analyze-skill/scripts/obsidian_adaptive_model_runner.py` once in a non-TTY command. Its zero-argument stdin fast path derives private receipt/result paths, infers the saved easy/complex effort class from the task text without reading files, and binds the child to the canonical current workdir; pass explicit metadata only when the user requested routing evidence. Do not start an interactive runner and send EOF later. Give the first command its full bounded yield; if it returns an ongoing session, use one empty `write_stdin` poll with up to 60 seconds. The selected producer owns skill loading, memory recall, file reads/edits, Quick Check, and its result receipt. The entry parent never duplicates implementation, tests, file reads, or verification, and never performs repeated 30-second model-turn polling. Publish the saved child result and return.

Exact read-only, tool-only, image/mixed, `LOCKED_ROUTE_NODE`, and `ENDING_TASK_WORKER` requests do not enter this producer fast path.

## Activation Boundary

Load this full skill only when at least one condition is true:

1. the user explicitly requests model choice, routing strategy, receipts, or an A/B benchmark;
2. the task has a real complex delegation or dependency graph that may justify another model session;
3. Task Analyze, Workflow, adaptive routing, verification routing, or their documentation is being maintained.

For anything else, stop loading routing material and use the inline bootstrap contract below. Complexity alone does not authorize delegation.

## Ordinary Inline Bootstrap

The always-loaded policy applies inline before this file would be selected:

1. Classify eligible ordinary work once from its project/task/module/file/symbol/code context without reading task files. Every eligible text/code production task must run `scripts/obsidian_adaptive_model_runner.py` through the Entry Parent Fast Path: it tries the saved catalog-selected priority producer (`low` for easy, `high` for complex when supported), then the Obsidian-selected quality pair only after a zero-result operational failure. Image/mixed, tool-only, and exact read-only work stay inline. Ordinary work reads the saved ladder unchanged. A missing ladder may bootstrap once from the local Codex cache without network access; only an explicit user model-update request may rescan that cache and replace a valid ladder. If the cache is unavailable, keep the last valid ladder. Unavailable Obsidian remains an explicit non-learning inline boundary.
2. Use one direct task action or one direct execution surface. Batch bounded reads, edits, or commands when safe.
3. After code implementation, run one bounded producer Quick Check (the user-facing Mini Test). Light/local work gets the smallest safe function smoke; external-API, large-file, expensive-build, destructive, or side-effect-heavy work skips the heavy path and checks syntax plus changed function, variable, import, and direct-reference names. Then present `CODE READY` with PASS or SKIPPED evidence. Quick Check is included in first-result time.
4. Immediately after presentation, write a lifecycle start receipt with `verify-skill/scripts/ending_task_ledger.py`; bind `--producer-receipt` whenever the adaptive runner produced the result. When `create_thread` is callable, call it, then `set_thread_title` with exactly `End Task-{concise related task name}`. Pass the lifecycle/producer receipts, Quick Check evidence, acceptance target, project root, and touched files. Link it and return without waiting or polling; never substitute a same-task subtask. In a headless, worker, or benchmark execution surface where `create_thread` is not callable, emit the completed main result plus the exact Ending handoff for the outer host and return immediately. Never inspect or invoke app-server internals, emulate task creation, poll for a tool, or self-run Ending; the outer host must create the persistent End Task. This host-boundary fallback does not waive Ending. Ending is a <=60-second, evidence-only handoff audit: no broad tests, API calls, user questions, waits, or automatic repair. A concurrent state change records terminal BLOCKED and exits; it never gates the presented result. On audit pass, the Ending thread automatically writes that producer's Real verdict to Obsidian.
5. Run isolated non-result logs, reports, and documentation alongside Real Verify when safe. Keep final project memory, shared-state writes, and verdict-dependent work ordered.
6. The origin final is complete after the result presentation and never waits for the audit. The End Task thread final requires lifecycle `PASS` or explicit `BLOCKED`; concurrent or missing evidence is terminal BLOCKED, not a user question. A repair is never automatic: it requires a new user request after a concrete recorded failure.

Prompt work is the one ordinary skill-load exception and still runs inline on the current user model. Every task that creates, reviews, edits, repairs, standardizes, tests, summarizes, optimizes, or changes a reusable prompt or durable AI instruction must load `prompt-skill` before prompt work. Ordinary prose does not trigger it merely because it is text. Prompt-in-code also loads the owning code executor. Present the completed prompt first; trials and Real Verify follow in Ending Task.

Exact-scoped read-only result work stays on the current model inline with no foreground producer subagent, route, or plan pass. For an exact named-source audit, first run one bounded `rg` per authoritative file for every exact user-named target and direct definition, then answer once. Anchor named members directly; never add enclosing-class or call-site anchors or guess identifier prefixes or families. Do not add pre-tool planning, a broad search, whole-file read, reread, or pre-result check. Present immediately. Create and return from a separate `End Task-{concise related task name}` only when thread tools are callable; otherwise emit its handoff and return so the outer host creates it. Never use a same-task Ending subagent.

When bounded multi-file evidence has an exact allowlist, make that one broad search a boundary-labelled batch across the allowed files and overread enough context to include complete target blocks and direct dependencies. If the evidence cannot be safely bounded in one output, use the smallest correctness-preserving batched chunk plan inline; never start with complete files or parallel subagents merely to avoid choosing the needed ranges.

Ordinary work must not read this full `SKILL.md`, show a pre-result route, or deliberate broadly. For every eligible production task the compact bootstrap invokes exactly one receipt-backed priority-first route through `scripts/obsidian_adaptive_model_runner.py`; only a zero-result operational priority-producer failure may start its selected quality fallback. Code producers apply only the bounded Quick Check before presentation. After presentation, the producer receipt is bound to the lifecycle ledger and a separate persistent End Task thread is required regardless of complexity.

Eligible ordinary requests use one project-scoped Obsidian context lookup with no visible plan; exact read-only and ineligible work remain inline. After the final source read, emit the requested output immediately with no separate foreground self-review, Mini, or verification pass.

## Result-Producer Performance Admission

There are two distinct admissions. User-enabled adaptive quality learning launches one producer from the current catalog-derived ladder even while its project/context boundary is cold or provisional. Multi-node strategy JSON routing and any claim that Global is faster or smaller still require comparable end-to-end performance evidence. Mandatory post-result Ending subagents are outside both gates.

Admission requires all of the following:

- the selected child pair is frozen, receipt-backed, Real-passing, and `trial=false`;
- prompt/inputs, cwd, sandbox, user/project configuration, frozen model-visible catalogs and memory snapshot, output contract, and acceptance match the direct cohort;
- the evidence includes the current entry pair and the complete foreground path, not only producer cost;
- correctness and metrics pass for every arm; Global foreground logical tokens have a lower cohort total and raw median with a non-negative paired-savings median; pairwise token regressions are diagnostics rather than arbitrary percentage vetoes; Simple first-result time stays inside the Direct cohort's measured median-absolute-deviation noise envelope, Medium requires lower total/raw median, non-negative paired savings, and a strict majority of faster pairs, and Complex time is diagnostic; all post-result Ending/verification time and tokens are excluded;
- evidence is complete, current, and workload-comparable.

The admitted cohort must prove fewer foreground logical tokens under those governing rules. Do not turn one chosen percentage into the optimization target: keep removing reproducible deterministic waste until repeated comparisons show only runtime noise or no correctness-preserving change remains. Cohort totals and raw medians must pass; individual regressions remain visible diagnostics. Simple timing uses its measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex timing is disclosed without vetoing a correct token-saving route. Ending Real time and tokens are diagnostic and never delay, charge, or invalidate the first presentation.

`scripts/strategy_performance.py` is the private authority for this separate decision. Its key includes the quality-profile fingerprint, current entry `model|effort`, configuration cohort, sandbox, strategy version, producer-contract version, and exact workload hash. Delegation needs at least six comparable paired samples. Every arm must have passing correctness and complete metrics. Logical tokens require a lower Global cohort total and raw median with non-negative paired-median savings. First-result latency requires lower Global cohort total/raw median, non-negative paired-median savings, and a strict majority of faster pairs; individual regressions remain diagnostics. Total-wall/Ending latency is retained only as a diagnostic. Otherwise it returns `inline_entry`.

Missing or negative performance evidence forbids a savings claim or multi-node strategy route, but it does not disable Obsidian-backed contextual quality selection. One foreground quality pair may be the current cold start, one-rung downgrade, one-rung upgrade, or frozen reuse; Ending Real supplies its verdict. A suite aggregate cannot hide a losing class. None of these conditions may suppress the mandatory Ending lifecycle.

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

- Use the catalog's strongest quality model for missing context, open-ended architecture, or difficult cross-system judgment.
- Use the catalog's balanced quality model for grounded repository, integration, testing, and evidence work.
- Use weaker catalog models only for bounded work after cold-start policy or verified descent permits them.
Every adaptive profile reads `assets/model-capability-ladder.json`. The file is the saved local-catalog snapshot, and only its highest numeric GPT family participates in quality movement. Eligible text/code result producers try the optional priority producer first; easy uses `low`, complex uses `high` when those efforts exist. Move effort before model while downgrading and reverse that order while upgrading.

## Obsidian Adaptive Routing

The mechanism has two distinct authorities. `assets/model-capability-ladder.json` is shared and mirrorable: the last explicitly refreshed local Codex model catalog, ranks, supported efforts, source digest, and movement policy only. It may bootstrap locally when missing, but ordinary task loading never refreshes it. Only an explicit user model-update request may replace it from the local cache; no network fetch is allowed, and an unavailable cache preserves the last valid ladder. Obsidian broad `Model Switch.md` pages are the sole current contextual experience authority, keyed by project/task/module/file/symbol/code context as record fields only.

Model-quality learning is keyed by exact project/task/module/file/symbol/code context, with artifact, scope, ambiguity, modality, risk, complexity, execution domain, owning skill, and verification shape retained as supporting context. End-to-end performance admission remains a separate evidence system for strategy-level multi-node JSON and speed/token claims.

- No prior quality success: eligible production runs the catalog cold-start pair with `trial=true`; this bootstrap sample is what allows later descent, ascent, or freezing. Ineligible/tool-only/exact-read-only work remains inline.
- A receipt-matched Real pass trials exactly one lower effort on the same model before moving to a weaker model; a quality failure reverses that order.
- A receipt-matched priority-producer quality/correctness failure is written first, then the next recommendation starts a new repair lifecycle on the contextual quality pair. Operational failure is quality-neutral and may fallback only before any result with zero tokens.
- A frozen matching project/code-context profile reuses its lowest Real-passing pair with `trial=false` until verified failure or material profile/policy drift.
- Cost ranking between child pairs still requires complete Real-passing evidence in the same workload cohort, but that ranking does not itself admit delegation.

Ending Real alone records receipt-backed producer pass/fail evidence to the canonical broad Obsidian `Model Switch.md`; producers and ordinary runners never write learning. Operational failures remain neutral and inline execution never fabricates a receipt.

Each receipt-backed Ending terminal record is rendered once under the matching category in a broad page. The six categories are `normal-script-update`, `code-design`, `finding-bugs`, `tests-verification`, `documentation-instructions`, and `general-work`; switch direction remains one of `initial`, `upgrade`, `downgrade`, `freeze`, `no_switch`, or `operational_fallback`, and context remains fields, never pages or wikilinks.

## Delegated Execution

After admission, continue through `workflow-skill` in the same task.

- One result producer uses its resolved Obsidian context through `scripts/obsidian_adaptive_model_runner.py` and `scripts/model_execution_receipt.py`; eligible text/code work tries the optional priority producer, then at most its authorized quality fallback, and emits the first completed result without a foreground verification gate.
- `obsidian_adaptive_model_runner.py` reads learning but never writes it. Priority-producer quality failure never triggers foreground fallback; Ending records it before a new quality-pair repair lifecycle. `strategy_performance.py` separately gates multi-node strategy JSON routing and Global-versus-Direct claims.
- A true multi-node dependency graph may save private schema-version-2 JSON with only `result` and `ending` phases, then call `scripts/task_route_dispatcher.py run-plan <plan-file>` once.
- Use exactly one execution surface per branch. Do not combine collaboration and dispatcher execution for the same work.
- Registry-owned delegated Python, C#, and Unity C# implementation or authored probes load `code-skill` and their domain rules.
- A launch/access/transport failure may use only the receipt-backed contextual quality fallback when no result was published and total tokens are zero; otherwise it stops and reopens rather than duplicating work.

For grounded JSON, present the producer result first. Ending Task may then use the matching `grounded_result_gate.py` preset for Real Verify. Pass no source root with `json-object`; source roots belong only to source-aware presets. The Real gate never delays first presentation.

## First Result And Mandatory Ending

For code, producer completion includes the bounded Quick Check; it is not independent Real Verify. Show the requested result immediately after that check so the user can continue while detached Ending runs.

For a dispatched graph, enforce `run-plan` -> completed result -> bounded Quick Check when code -> show result -> `release-main-result` -> create and rename `End Task-{concise related task name}` when the thread tools are callable. Pass the dispatcher handoff to that thread; only the new thread may call `run-ending`. For ordinary work, enforce Quick Check when code -> result presentation -> lifecycle `start --producer-receipt <receipt>` when routed -> create/rename/link End Task -> return without waiting. If thread tools are absent, stop at the released result and outer-host Ending handoff; never search for a hidden task API or keep the result session alive. Ending owns only a <=60-second read-only handoff audit and the receipt-backed pass/fail write to Obsidian after the result; broader regression, API verification, optimization proof, reports, and repair happen only when the user expressly asks. A concurrent state change logs terminal BLOCKED and exits; Ending never asks the user to unblock it or self-starts repair.

## Runtime Proof And A/B Policy

A model label is not proof. Delegated nodes require sanitized runtime receipts matching requested, resolved, and effective model/effort. Inline current-model execution does not fabricate a child receipt.

For strategy comparisons, keep prompt, inputs, cwd, sandbox, configuration, output contract, acceptance, and Quick Check policy identical. Every benchmark entry starts from the user-selected `gpt-5.6-sol|ultra` pair. Direct remains on that fixed entry pair; Global starts on the same entry pair and must produce a receipt proving the actual adaptive producer attempt/effective pair. A fixed same-pair Global arm, an ineligible exact read/audit task, or a Global arm that falls back to Sol inline is not evidence of Auto Best Model savings. Count each foreground session once. User-visible performance runs from task start through required Quick Check and completed-result presentation; receipt finalization, telemetry, and detached Ending Real are excluded, as are all Ending/verification tokens. Every tier requires matching correctness and fewer foreground tokens; Simple time uses the Direct cohort's measured noise envelope, Medium keeps the strict speed direction and majority gate, and Complex time is diagnostic. Show separately whether the optional background Ending diagnostic would preserve or erase the foreground token/time win; never use it to decide the foreground winner.

Benchmark first-result authority is the controller-stamped sanitized `result-ready` event emitted immediately after the atomic result write. File polling and the child process's local monotonic clock are not timing authority; the gate requires the runner-owned receipt and evidence timestamps to match exactly.

Any structural change to this routing/skill contract reruns the same simple, medium, and complex benchmark cohort. The benchmark is a post-edit acceptance check; it does not delay the first result or replace the detached Ending thread.

`scripts/benchmark_suite_gate.py`—not a caller-authored manifest—derives correctness, completion, receipt/session coverage, tokens, first-result time, total-wall time, retry/fallback/repair counts, and per-tier verdicts. Overall PASS is exactly `simple AND medium AND complex`; one tier failing any cohort or correctness gate fails the suite.

## Generated Files

Put plans, prompts, receipts, logs, and benchmarks in active task/project `cache/` or `work/`. Current contextual model evidence belongs only in the canonical broad Obsidian `Model Switch.md` page. The generated shared ladder contains no personal evidence and is safe to mirror. Put final deliverables only in the requested output location.

## Verification

After contract changes:

1. Run `scripts/sync_model_capabilities.py --check`.
2. Run `scripts/validate_task_analyze_skill.py` and focused tests.
3. Run Workflow validation for admitted complex routes.
4. Prove ordinary code tasks run only one proportional producer Quick Check, present immediately afterward, create a separately titled End Task thread, and return without waiting or using a same-task Ending subagent.
5. Promote a performance claim only after like-for-like repeated evidence passes every task class independently.

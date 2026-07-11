---
name: task-analyze-skill
description: "Use at the start of every Codex user task as the independent 100%-trigger entry skill. The selected entry model and effort analyze and route only. It selects installed skills plus exact downstream models/efforts, applies private receipt-backed experience, plans Mini Verify and post-result Ending work, then hands execution to workflow-skill."
---

# Task Analyze Skill

Use this skill first for every user task. It is an individual global skill and the hookless global entry mechanism. It covers answers, reads, commands, edits, code, prompts, visuals, documents, verification, optimization, management, and mixed work.

Prompts beginning with `LOCKED_ROUTE_NODE` or `ENDING_TASK_WORKER` already belong to a route and must not restart Task Analyze. Remove or relocate nested cache/fixture `SKILL.md` files under user skill folders; preserve the official `.system` subtree.

## Entry Boundary

The entry can be any supported pair. During the smallest read-only preflight call `scripts/resolve_entry_model.py`; preserve the exact verified pair or show `unverified`. The entry model/effort perform route coordination only. After the route, every downstream node uses its planned model and effort and the entry never becomes a workflow-wide default.

Read this Task Analyze skill completely, then batch `python3 scripts/resolve_entry_model.py` and at most one quick bounded related-memory lookup in the first tool round. Do not load Workflow, the selected downstream skill, Verify, or code-language rules in the entry; the bounded downstream node reads its own owning skill. The entry is exempt from full Obsidian/project-memory bootstrap: do not walk vault indexes or load whole project, daily, aesthetic, or wiki pages here. Inject only related facts and defer broader memory to the producer or Ending. Missing memory providers are a successful no-op; clearly irrelevant memory is also skipped.

The entry is a bounded controller. It does not inspect task sources, load broad references, duplicate downstream work, or combine collaboration and dispatcher execution for the same branch. Every collaboration child prompt starts with `LOCKED_ROUTE_NODE`.

## Easy Deterministic Fast Path

This section is the complete contract for an obvious bounded source lookup, exact text transform, tiny code/text edit, or command generation.

If the entire requested answer is a literal value/assignment/file-state extraction that one read-only tool command can produce and one exact local comparison can verify, use the exact local tool path. After this skill is read, show the easy route and launch one combined `python3 resolve_entry_model.py` + bounded read-only evidence command in that same response turn; return the literal tool-derived answer after local Mini. Do not load Workflow/owner/Verify/memory, launch a child model, create a receipt, consult/update adaptive history, or add an Ending worker. This exception cannot interpret control flow, summarize semantics, author code/prose, or make judgment.

Otherwise use the adaptive model path:

1. Resolve entry and optional memory in one preflight batch.
2. Show the easy text route.
3. Select one named profile preset. Use `grounded-repository-answer-easy|complex`, `tiny-text`, `command-generation`, or `tiny-code|code-easy|code-complex`. The preset derives the complete candidate ladder, static suggestion, hard floor, and controlled condition fields; callers never construct or serialize a candidate ladder. An unambiguous installed short skill name is canonicalized to its catalog ID. Tiny eligible code/text/command work starts Spark-low; use the planned normal fallback only for an operational Spark failure.
4. Show the route once, then launch one blocking `scripts/adaptive_model_runner.py --emit-result` call in that same response turn; do not insert a second model commentary/decision turn before the tool. It must select the pair from private experience, invoke the receipt runner, run any named grounded Mini, and return the passing bounded result in the same stdout summary; the entry may not substitute its static suggestion or make a second result read. Put the exact owning-skill path, bounded sources, output contract, and self-check in the stdin prompt. In read-only mode pipe with shell `printf '%s'`; never use a heredoc or `/tmp`. Write receipt/result only to the pre-existing active task cache. Use one long-lived session with no PTY; if the tool yields, poll no more often than every 55 seconds.
5. Perform one local deterministic Mini Verify for literal source/schema/string/syntax/file/command acceptance, then show the main result immediately.
6. Ending Task is deferred/no-op unless unresolved semantic risk remains.

The complete runner shape is `printf '%s' <prompt> | adaptive_model_runner.py --profile-preset <id> --project-family <slug> --owning-skill <installed-id-or-short-name> --task-summary <sanitized-summary> --workload-id <id> --receipt-output <cwd/cache/file> --result-output <cwd/cache/file> --workdir <root> --sandbox <mode> --timeout <seconds> [--ignore-user-config] [--grounded-gate-preset json-object] [--grounded-gate-preset grounded-source-json-v1|workflow-graph-json-v1|workflow-graph-json-v2 --grounded-source-root <root>] --emit-result`. Never pass `--grounded-source-root` with `json-object`; that preset has no source pointer and rejects the unused root. Use workflow-graph v2 when the contract separates always-returned from optional keys or contains conditional-serial stages; keep v1 for its exact legacy six-key contract. A bounded read-only child prompt already names the exact owner skill path and must pass `--ignore-user-config` so it does not reload the global entry/memory contract; the child reads only its named owner instructions. The runner creates output parents; use the deterministic `cwd/cache` path and do not `find`, `ls`, or inspect cache first. Do not call runner `--help`, inspect runner/history/receipt implementation, search memories or prior sessions for examples, create collaboration children, reread the result, launch a model Mini, or run Real Verify before the result. When orchestration uses `functions.exec`, start the source with `// @exec: {"yield_time_ms": 60000}`; use a 30-second initial nested launch and 55-second `write_stdin` polls so the outer wrapper does not create an extra `functions.wait` turn. A runner summary with `status=pass` and `mini_status=pass` is the stop condition: call no more tools, do not inspect task sources, do not author another verifier, and return the emitted result immediately once in final. Never print the full result in commentary and repeat it in final. A local Mini does not select or load `verify-skill`. The entry must not read the task source; that is the receipt-backed producer's work. A launch/transport failure permits one corrected invocation only; then return the operational failure, never an unreceipted or fixed-pair fallback.

## Standard Route

Use the standard route when deterministic fast-path proof is insufficient. This core file is the complete ordinary routing contract. Do not read model-selection, adaptive-routing, route-contract, runtime-receipt, dispatcher source, fixtures, or archived skills merely to construct a route; those references are for editing/debugging the routing system. Load the selected downstream skill and only its task-relevant references.

Grounded low-risk read-only text answers use one result producer by default. Complexity alone never requires a dispatcher: one result producer plus local deterministic Mini uses one direct receipt call. Multiple model nodes require a real dependency reason; multiple result branches require pairwise-disjoint `source_allowlist` values and a main merge with `reads_dependency_results_only=true`. Choose collaboration or dispatcher once per branch, never both.

New dispatched plans set `first_result_timeout_seconds`: normally 180 seconds for easy and 600 seconds for complex. The dispatcher gets one foreground invocation and one repair budget. Deadline exhaustion stops new nodes/fallbacks and returns the best result plus preserved partial evidence.

## Visible Route

- **Easy:** concise text, not Mermaid. Show Task Analyze -> direct task -> Mini Verify -> Main result -> Ending Task, with model/effort on model-executed nodes. A local Mini is labeled local and has no fabricated receipt.
- **Complex:** task-specific Mermaid plus a numbered `Workflow with models` list. Show real dependencies, Mini, Main Goal Done Gate, result release, and post-result Ending.

Show only the human route. Internal schema-1 JSON stays in task cache and is never conversation output. After the route, continue in the same task through `workflow-skill`; never strand the task at planning.

## Model Selection

Apply owner/domain, safety, authority, modality, project, language, and code-style floors before experience:

Classify the requested artifact, not the language of inspected files. A read-only repository workflow reconstruction is a `grounded`/`answer` profile in the owning project skill with `execution_domain=general`; inspecting Python, C#, or Unity C# does not turn that answer into a code task. Use a code preset only when the node creates, changes, executes, or verifies code as code.

- Sol: missing context, open-ended architecture, or difficult cross-system judgment.
- Terra: grounded repository/integration/testing/evidence work.
- Luna: bounded non-code work, concise results, and verification judgment.
- Spark-low: only obvious bounded low-risk easy low-ambiguity text-only `tiny_text`, `tiny_code`, or `command_generation` through `code-skill`.

Every non-tiny profile retains the full Luna-low-to-Sol-ultra ladder without Spark. Tiny eligible profiles prepend Spark-low. Move effort before model in both directions.

## Private Adaptive Routing

Personal routing evidence lives only in `local/adaptive-routing/model_experience.json` and is never mirrored. `scripts/model_routing_history.py` stores controlled profile fields, generalized summaries, producer pair/receipt, prompt-free workload hash, Mini/Real verdict, success/failed pair boundaries, tokens, and time—never raw prompts, results, paths, IDs, secrets, or private content.

Every non-dispatched adaptive producer runs through `scripts/adaptive_model_runner.py` with one stable named profile preset. The wrapper expands the preset, derives the ladder internally, calls routing history itself, fails closed when no valid above-floor pair exists, and executes exactly the returned pair with `LOCKED_ROUTE_NODE`; the entry cannot skip or override experience. A dispatcher result producer is allowed only after the dispatcher recomputes the same learner recommendation and matches the locked pair, trial flag, fingerprint, and proof fields immediately before execution. Its optional named grounded gate runs and records Mini inside that same invocation. Fixed-pair benchmark baselines alone call `scripts/model_execution_receipt.py` directly outside entry context.

- No prior success: use the static suggestion, except the tiny Spark-low rule.
- After a receipt-matched pass, trial exactly one lower effort on the same model; only then move to a weaker model.
- Receipt-matched Mini/Real quality failure upgrades in reverse. Operational timeout/availability/protocol/receipt failures are neutral.
- For `mini_real`, Mini is provisional; Ending Real updates the same producer attempt and freezes/reopens the exact profile.
- Cost-rank only complete Real-passing pairs in the same exact `workload_prompt_sha256` cohort: total tokens first, process time second, weaker rung last.

Optional Obsidian `TaskModelExperience/` is a sanitized readable projection after Real Verify; the private ledger remains authority.

## First Result And Ending

Mini Verify is the smallest meaningful first-result gate. Finish the requested work, Mini-check it, and show the main result immediately. Before release, formatting/order/literal-schema checks should be deterministic and at most one bounded repair may run.

For dispatch, enforce: `task_route_dispatcher.py run-plan` -> read Mini-passed result -> show result -> `release-main-result` -> `run-ending`. If a nested/non-interactive surface buffers output, return after Mini with Ending pending instead of running Real synchronously. Inside an entry-task receipt process, never launch an Ending worker, Real verifier, or post-Real repair before returning the outer result.

For a grounded read-only producer returning JSON, use the adaptive runner's matching named gate preset, or its strict config input when no preset matches, instead of a separate gate launch or task-specific probe. It calls `scripts/grounded_result_gate.py` inside the producer invocation, binds the saved result to its passing runtime receipt, checks only declared JSON structure/order/sorting and referenced-file containment/existence, and never reads semantic source content. Do not retry wildcard quoting, custom AST/source probes, or separate gate commands before the first result; semantic source replay belongs to Ending.

Ending Task owns Real Verify, broader regression, independent optimization proof, reports, docs, logs, and related memory. A later correctness failure notifies, reopens, repairs, reruns Mini, and presents a corrected result.

## Direct Tool Boundary

One obvious reversible external app/tool state action with no model-authored answer and no graph uses its installed tool skill directly after the route, with no cached plan, child model, runtime receipt, or adaptive sample. The same boundary includes the exact literal local-read path above when its whole answer is deterministic tool evidence rather than semantic model authorship. Mini checks the observable stop condition or exact literal comparison. All other source-backed answers are model work and need an adaptive receipt.

## Runtime Proof

Non-dispatched adaptive producers use `scripts/adaptive_model_runner.py`, which owns selection and calls `scripts/model_execution_receipt.py` exactly once. A dispatcher adaptive producer must freshly recompute and match its locked recommendation before receiving its distinct result authorization. Fixed nodes and fixed-pair benchmark baselines use the receipt runner directly. Requested/resolved/effective pair and completion must match before claiming execution. Timeout receipts preserve elapsed time and partial token lower bounds.

An outer `model_execution_receipt.py --entry-task` launch installs an inherited entry-context marker. Under that marker, a result producer is accepted through either the adaptive runner's in-process authorization or the dispatcher's distinct freshly recomputed adaptive-recommendation authorization; a direct fixed or forged result receipt fails closed. Dispatcher verification, repair, and ending nodes use separate matching in-process role authorization. Fixed benchmark baselines remain valid outside entry context. Receipts record the sanitized node role and authorization source, never the marker value or environment.

For savings, keep prompt, cwd, sandbox, configuration, output contract, and acceptance identical. Bypass only Task Analyze with a `LOCKED_ROUTE_NODE` baseline on the entry pair; do not use `--ignore-user-config` as the baseline. Count each unique entry/collaboration/dispatcher/retry session once and report Mini-passed first-result cost separately from Ending.

## Generated Files

Put plans, prompts, receipts, logs, and benchmarks in active task/project `cache/` or `work/`. Keep adaptive history only under `local/`. Put final deliverables only in the requested output location.

## Verification

After changes:

1. Run `scripts/sync_model_capabilities.py --check`.
2. Run `scripts/validate_task_analyze_skill.py` and all tests.
3. Run Workflow validation and representative easy/complex routes.
4. Prove a downstream receipt differs from entry when routed.
5. Run a like-for-like first-result comparison and bounded related-memory checks.

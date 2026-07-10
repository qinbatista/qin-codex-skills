---
name: task-analyze-skill
description: "Use at the start of every Codex user task as the independent 100%-trigger entry skill. The selected entry model and effort analyze and route only. It classifies complexity, selects installed skills plus exact downstream models and efforts, applies private receipt-backed routing history, plans Mini Verify and post-result Ending Task work, then hands execution to workflow-skill. Easy tasks show concise text; complex tasks show Mermaid."
---

# Task Analyze Skill

Use this skill first for every user task: direct answers, reads, commands, edits, code, prompts, visuals, documents, verification, optimization, management, and mixed work. It is an individual global skill, not a phase hidden inside `workflow-skill`. This is a 100 percent entry contract, not a lifecycle hook and not a recursive phase.

## 100% Task-Start Contract

The always-loaded `~/.codex/AGENTS.md` contains the Task Entry Rule from `assets/global-agents-entry-rule.md`. That instruction plus this skill's loader description is the hookless global entry mechanism.

Do not create, require, or use lifecycle hooks for this workflow. Do not print an internal machine plan or plan marker in chat. The route must never strand the task at a route display.

Prompts already marked `LOCKED_ROUTE_NODE` or direct bounded `ENDING_TASK_WORKER` prompts belong to an existing route. Execute those nodes directly without restarting Task Analyze.

Remove or relocate nested cache/fixture `SKILL.md` files under user skill folders in `~/.codex/skills`, because the loader discovers them recursively. Preserve the official `.system` subtree.

## Entry Model Boundary

The model and reasoning effort selected when the user starts a task run Task Analyze and route coordination only. The entry can be any supported pair. During bounded read-only preflight, call `scripts/resolve_entry_model.py` and use its exact verified pair; use `unverified` only if exact resolution fails. That pair is never a workflow-wide default.

Preserve observable entry metadata exactly. If it is unavailable, show `unverified` instead of guessing. After the route is visible:

- every downstream node uses its planned model and effort;
- `workflow-skill` executes the locked route without inheriting the entry pair;
- result-bearing model work runs through a selectable model surface with a sanitized runtime receipt;
- a visible model label without a matching receipt is `planned only`.

The entry model may coordinate tools needed to launch and collect downstream nodes, but it must not replace their result-bearing reasoning with its own.

## Before The Visible Route

Perform only the smallest read-only preflight needed to classify the task and select a safe route. Supplied artifacts, directly related instructions, active source root, relevant history, and installed-skill names are allowed.

Do not edit, generate, push, deploy, send, or start result-bearing executor work before the route is visible. Stop gathering when the route is knowable.

After the route is visible, continue the same task through `workflow-skill`; do not end the response at the route.

## Complexity And Visible Output

- **Easy:** one direct, bounded, low-risk result with obvious inputs and stop condition. Show concise text, not Mermaid.
- **Complex:** multiple dependent or parallel nodes, behavior-changing file work, code/prompt logic, UI/generated artifacts, broad ambiguity, or meaningful risk. Show a task-specific Mermaid workflow plus a numbered `Workflow with models` list.

Every model-executed, verification, merge, gate, result, dispatch, and Ending Task node displays its exact model and effort. A direct tool-only action uses its installed skill and observable Mini check without a child model or model receipt. Read `references/route-contract.md` for the required shapes.

For easy tasks, keep the complete visible node set: Task Analyze -> direct task -> Mini Verify -> Main result -> Ending Task.

## Locked Route Contract

Create the route before side effects. It contains:

- task complexity and display mode;
- observable entry model and effort;
- every real node's purpose, owning installed skill, model, effort, dependencies, inputs, output, and stop condition;
- sequential, parallel, or mixed topology;
- Mini Verify target, Main Goal Done Gate, and first-result node;
- post-result Ending Task branches;
- allowed fallbacks with concrete triggers;
- runtime-receipt requirements.

Show only the human route. When machine execution needs a structured plan, save schema-1 JSON privately inside the active task cache and pass its file path to `scripts/task_route_dispatcher.py run-plan`. Never paste that JSON into the conversation.

Use only installed skills. Every active registry-owned code-domain implementation or authored probe loads `code-skill`, follows its rules, and uses Spark first unless a visible supported fallback is triggered.

## Model And Effort Choice

Read `references/model-capabilities.md`, `references/model-selection.md`, and `references/adaptive-routing.md` before selecting downstream nodes.

Static role floors:

- Sol: missing context, open-ended synthesis, ambiguous architecture, or genuinely difficult judgment.
- Terra: grounded source-rich work, integration, repository archaeology, realistic testing, or evidence-heavy review.
- Luna: direct bounded non-code work, concise results, Mini Verify judgment, and lightweight records.
- Spark first: text-only work in any active registry-owned code domain through `code-skill`; current examples are Python, plain C#, and Unity C#. `code_unspecified` is migration/history-only.

Choose the lowest effort that can reliably satisfy the node. Then consult the private routing history for the same sanitized task profile. Static safety, authority, modality, project, and skill floors always override learned cost reductions.

## First Result Principle

Finish the user requested task, run the smallest meaningful Mini Verify, and show the basically verified result immediately. After the result is shown, continue deeper Real Verify, broader regression checks, optimization proof, reports, logs, documentation, and routing learning in Ending Task. If later verification finds a correctness problem, notify the user, reopen the task, fix it, rerun Mini Verify, and present the corrected result. Never delay a basically verified result for optional deep closeout, and never describe Mini Verify as exhaustive proof.

## Private Adaptive Routing

Personal routing evidence lives under `task-analyze-skill/local/adaptive-routing/` and never enters the public skill mirror.

`scripts/model_routing_history.py` creates `local/adaptive-routing/model_experience.json` locally when absent. It records controlled task-profile enums, a generalized one-line task summary, requested/resolved/effective model and effort, receipt status, Mini/Real verdict, failure class, tokens, timing, and explicit `success_model`/`failed_model` ranges. It is never mirrored. Raw prompts, results, paths, secrets, thread/session IDs, and private task content are forbidden.

For the same task profile, including `execution_domain`:

1. With no prior success, use the static suggestion; the sole automatic exception is safe, low-risk, text-only `tiny_text`, `tiny_code`, or `command_generation` work, which starts at Spark-low when eligible.
2. A runtime Spark failure for that exception uses the static suggestion and does not become a quality penalty. A result node retries only its explicit `model|effort` fallback pairs, in order; Mini/Ending verdict failures never trigger a model retry.
3. Treat calibration as a bounded search for the best complete `model|effort` pair for this exact sanitized task profile. After a receipt-matched verification pass, trial exactly one lower effort on the same model. Only after that model's eligible efforts are exhausted, trial the next weaker eligible model.
4. When adjacent pass/fail evidence establishes the selected eligible pair, or a receipt-matched pass proves the current hard floor, derive that calibrated/frozen selection from the bounds and reuse it with `trial=false`; do not keep searching while trial is closed.
5. Reopen calibration only when a receipt-matched Mini or Real correctness/quality failure invalidates the calibrated pair, or when the eligible candidate ladder or hard floor changes. Upgrade in reverse order: raise effort on the same model first, then move to the next stronger eligible model only after that model's efforts are exhausted. If no stronger current candidate exists, return an exhausted result with no selected pair. Never overwrite a failed attempt with a later pass under the same route-run ID; a genuine retry uses a new ID.
6. Runtime availability, timeout, telemetry, execution, or receipt failures and unverified/mismatched receipts are temporary diagnostic evidence. They may trigger an allowed execution fallback, but they never change the learned quality best, success boundary, or failed boundary.
7. Record the result-producer receipt after Mini Verify, then update the same route-run attempt after Real Verify; Real Verify failure overrides an earlier Mini pass. Direct non-dispatch routes invoke the same recorder.

Correctness boundaries control selection first: the weakest verified complete pair is the boundary floor to move above on failure, and a stronger or faster pair can never bypass that boundary. Receipts are used for like-for-like optimization evidence after correctness gates are met. The recorder does not run active median-ranking across all candidates. Its recommendation output is `selected_pair`, `reason`, `trial`, `success_model`, and `failed_model`; the calibrated/frozen selection is derived from those bounds and reused with `trial=false`. Never claim a field or ranking that the recorder does not produce. Do not assume that crossing models means cheaper.

## Easy Direct-Action Boundary

Task Analyze always runs, but the internal dispatcher does not for one obvious reversible action with no graph. After the concise visible route, execute the installed tool skill directly and perform only a minimal observable-state Mini Verify. Do not create a cached plan, launch a model child, or call `task_route_dispatcher.py` for a direct tool action. Do not fabricate downstream model receipts for tool-only actions. Examples include opening Chrome, loading YouTube, or searching CCTV on YouTube; their stop conditions are respectively Chrome open, `youtube.com` loaded, and the query plus visible results.

Complex work uses locked dispatched model|effort nodes, dependency topology, receipts, Mini Verify, Main Result, then Ending Task.

## Mini Verify, Main Result, And Ending Task

1. Complete the requested result-bearing nodes on their planned models.
2. Run proportional Mini Verify.
3. Repair and rerun when Mini Verify fails.
4. When Mini Verify passes, cross `Main Goal Done Gate` and show the main result immediately.
5. After the result is shown, execute this enforced sequence: `run-plan` -> read the Mini-passed result -> show the self-contained basically verified result -> `release-main-result <handoff>` -> `run-ending <handoff>`. Ending Task must never be released before the main result is actually shown.

Ending Task must not delay the first Mini-verified result. A later correctness failure notifies the user and reopens the task.

## Runtime Proof And Savings

Use `scripts/model_execution_receipt.py run` for every downstream model node when a selectable surface is callable. The receipt must match requested versus resolved/effective model and effort before claiming that node ran as planned.

Use identical bounded workload prompts, inputs, topology, sandbox, acceptance criteria, and `workload_prompt_sha256` for like-for-like savings checks. One pair is a smoke result; repeated alternating runs and medians are required for a durable benchmark.

To add or change execution-domain routing, follow the [router extension guide](references/router-extension-guide.md).

## Workflow Execution

After showing the route, load `workflow-skill` and continue in the same task.

- Direct bounded work may invoke `model_execution_receipt.py run` per node.
- Multi-node sequential/parallel/mixed work may save an internal plan in the task cache and call `task_route_dispatcher.py run-plan <plan-file>`.
- Every child prompt receives `LOCKED_ROUTE_NODE`; Ending workers receive `ENDING_TASK_WORKER`.
- After Mini, call `model_routing_history.py record` with the main result-producer receipt and route-run ID. After Real, call it again with that same receipt and route-run ID; do not record the verifier's model as the producer attempt.
- Enforce `run-plan` -> read Mini-passed result -> show self-contained basically verified result -> `release-main-result <handoff>` -> `run-ending <handoff>`; never release Ending before the user-facing result is shown.

Do not recursively launch another Task Analyze. Do not expose raw dispatcher plans, stdout, stderr, prompts, or secrets.

## Generated File Placement

Put temporary plans, receipts, benchmarks, prompts, logs, and validation output in the active task/project `cache/` or `work/` area. Keep private adaptive history only in `task-analyze-skill/local/adaptive-routing/`. Put final deliverables only in the requested location or active workspace `outputs/`.

## Verification

After editing this skill:

1. Run `python3 scripts/sync_model_capabilities.py --check`.
2. Run `python3 scripts/validate_task_analyze_skill.py`.
3. Run all Python unit tests under `tests/`.
4. Confirm no lifecycle dependency, raw-plan mandate, or chat JSON handoff remains.
5. Replay one easy and one complex route.
6. Capture a receipt proving a downstream pair differs from the verified entry pair when the route plans a different pair.
7. Run a like-for-like receipt comparison using `workload_prompt_sha256` and verified acceptance evidence.

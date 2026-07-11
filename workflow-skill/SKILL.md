---
name: workflow-skill
description: "Use when independent task-analyze-skill has returned a locked route. Validates and executes the per-node skill/model/effort plan, preserves dependencies and topology, routes active registry-owned code domains through code-skill, runs proportional Mini Verify, releases the main result, then dispatches background Ending Task work such as Real Verify, independent optimization verification, reports, logs, docs, and memory."
---

# Workflow Skill

Use this skill only after `task-analyze-skill` has shown a visible locked route. `task-analyze-skill` is the 100%-trigger individual entry skill; `workflow-skill` is the downstream controller selected inside that route. Continue in the same task after the route is shown. Do not wait for a lifecycle hook and do not expose an internal machine plan in chat.

## Authority Boundary

The observable entry model and effort belong only to Task Analyze and route coordination. Workflow receives an explicit model and effort for every downstream node and must not silently inherit the entry selection, choose a new major model, or redraw a different route. The entry pair is resolved during Task Analyze preflight, never assumed from a fixed model.

If a planned model-selectable surface is callable, execute the node with that exact model and effort and keep a sanitized runtime receipt. If selection or metadata is unavailable, mark the node `planned only`; never claim the model ran merely because the diagram names it.

## Plan-Lock Gate

Before side effects, confirm the returned plan includes:

- easy/complex classification and visible route;
- every executable node's purpose, installed owning skill, exact model ID, effort, dependencies, input, output, and stop condition;
- sequential, parallel, or mixed topology;
- Mini Verify placement;
- Main Goal Done Gate followed by the main-result node;
- post-result Ending Task branches and fallbacks;
- runtime-receipt requirement when model execution must be proved.

Reject the plan back to `task-analyze-skill` for one bounded repair if it invents a skill, uses an unsupported model/effort, omits a node label, leaves a dependency unresolved, routes an active registry-owned code domain around `code-skill`, puts Main Result before Mini Verify, or places Real Verify/optimization closeout before the first result. Do not repair route semantics by silently reselecting models inside Workflow.

## Visible Route Contract

Task Analyze owns the first user-facing route display:

- Easy task: concise text explanation with model and effort for every real task. No forced diagram.
- Complex task: task-specific Mermaid plus a numbered `Workflow with models` list.

Workflow may report a model switch or repair, but it does not repeat the whole route unless the plan changed. Any changed plan must return to Task Analyze and be shown before affected side effects.

## Execution Rules

1. Execute only nodes whose dependencies are satisfied.
2. Run independent branches in parallel when the callable tool policy and task safety allow it.
3. Keep ordered, shared-state, irreversible, or output-dependent work sequential.
4. Load every owning skill named by the plan before that executor node.
5. Preserve the exact planned model and effort on each node. A fallback must be allowed by the plan, visibly reported, and recorded in runtime metadata.
6. Use the smallest relevant file/source allowlist. Exclude cache, backup, generated, and stale fixture trees unless they are the target.
7. Preserve unrelated user work and do not broaden authorization.
8. Do not push, publish, deploy, message, switch profiles, or perform an irreversible action unless the user explicitly authorized that action.
9. Preserve a bounded Task Analyze related-memory digest only for nodes that need it. Treat memory as advisory and recheck live sources when freshness matters; missing memory never blocks execution.

For a direct model node, use `../task-analyze-skill/scripts/model_execution_receipt.py run` with the exact planned pair and call `../task-analyze-skill/scripts/model_routing_history.py record` after Mini using the result-producer receipt; call it again after Real with the same route-run ID and producer receipt. A direct tool-only node uses its installed tool skill and observable Mini check: no child model, receipt, or adaptive sample. For a multi-node sequential, parallel, or mixed route, save the structured plan only in the active task cache and run `../task-analyze-skill/scripts/task_route_dispatcher.py run-plan <plan-file>`; it records after Mini and updates after Real. Enforce `run-plan` -> read Mini-passed result -> show self-contained basically verified result -> `release-main-result <handoff>` -> `run-ending <handoff>`; no Ending node may run before release. Child prompts use `LOCKED_ROUTE_NODE`; no lifecycle hook is involved.

Local commands use the local runner, but the planned model/effort still owns command selection, interpretation, and any authored probe. Labeling a runner `LOCAL` does not remove the node's model/effort requirement.

## Internal Route Selection

### Executor Routing

Use every planned executor that matches; do not run unrelated branches.

| Work | Required route |
|---|---|
| Active registry-owned code domain, debugging/refactoring, prompt-in-code, or authored code probe | `code-skill` |
| Tests, QA, artifact inspection, UI/visual review, Mini Verify, or Real Verify | `verify-skill` |
| Explicit/repeated reusable workflow improvement | `optimization-skill`, with a different verifier in Ending Task |
| Global skill scope, auth/profile work, or approved mirror operations | `management-skill` |
| Prompt/instruction behavior | Prompt Task Gate below, plus `code-skill` only when embedded in Python/C# |
| Other production work | The relevant installed production skill returned by Task Analyze |

Every active registry-owned code-domain node loads `code-skill`. Spark-low is first only for obvious bounded low-risk easy low-ambiguity text-only tiny implementation and authored-probe work; its exact candidate route is Spark-low plus the full normal fallback ladder. Every non-tiny model route uses the exact full Luna/Terra/Sol ladder with no Spark, regardless of easy/complex classification. Never raise Spark effort as a fallback.

### Prompt Task Gate

When the task changes or tests prompt behavior, prompt wording, templates, strings/constants, system/developer/user instructions, model/agent rules, AI output behavior, or trigger behavior:

1. Show `Prompt idea -> Prompt goal -> Problems -> Solution`.
2. Inspect the current prompt/instruction when it exists.
3. Fix the smallest complete missing logic instead of stacking case-specific warnings.
4. Use `code-skill` only when the prompt is embedded in Python/C# executable behavior.
5. Give the prompt update a representative Mini Verify; planned realistic prompt replay belongs to Ending Task Real Verify.

Read `references/routing-matrix.md` for multi-artifact routes. Read `references/image-generation.md` for image-related work or when a generated visual materially improves the requested result.

## First Result Principle

Finish the requested task, run the smallest meaningful Mini Verify, and show the basically verified result immediately. Afterward, Ending Task owns deeper Real Verify, broader regression, optimization proof, reports, logs, documentation, and routing learning. A later correctness problem must notify the user, reopen the task, repair, rerun Mini Verify, and present the corrected result. Mini Verify is not exhaustive proof.

## Direct Action Boundary

Task Analyze always runs. For one obvious reversible action with no graph, Workflow executes the installed tool skill directly after the visible route, without a cached plan, model child, or internal dispatcher; Mini Verify checks the observable state and no downstream model receipt is fabricated. Complex work uses dispatched model|effort nodes, dependency topology, receipts, Mini Verify, Main Result, then Ending Task.

## Mini Verify And Main Result

Mini Verify is the basic proportional result gate for every task. For a tiny easy task, Mini Verify may be the minimal confirmation that the requested state or answer is present. For complex work, follow the returned topology:

- fully independent result branches receive branch Mini Verify before merge;
- sequential work receives one consolidated Mini Verify after the final dependent step;
- mixed work receives an integration Mini Verify after merge, plus branch checks only when integration cannot expose an isolated basic failure.

Mini Verify may use syntax, compile, lint, schema, existence, changed-line, parse, basic render, or one focused input/output check when that evidence matches the task. It proves basic readiness, not realistic or exhaustive correctness.

When Mini Verify fails, repair the affected result-bearing node and rerun the relevant Mini Verify. When every planned Mini Verify passes and the requested work is complete:

1. cross `Main Goal Done Gate`;
2. show the main result immediately;
3. state that deeper Ending Task proof is running when relevant;
4. only after the result is actually shown, call `release-main-result <handoff>` and then `run-ending <handoff>`.

Do not claim Real Verify, independent optimization verification, report completion, or memory completion before those background branches report.

## Ending Task

Ending Task starts after the main result. It owns only planned related closeout:

- Real Verify and realistic behavior replay;
- broader regression, visual, browser, integration, or source checks;
- optimization implementation when it is a post-result improvement;
- a verifier distinct from the optimization implementer;
- each optimization node names exactly one Ending `verify-skill` node through `verifies_node`; that verifier runs on a different receipt-backed worker, and an Ending optimization/verifier pair executes in dependency-ready waves;
- reports, logs, docs, Markdown, DailyLog/wiki/Obsidian memory;
- directly related sanitized memory only; optional `TaskModelExperience/` recording follows Real Verify and never replaces the private routing ledger;
- sanitized private adaptive-routing outcome records after receipt-backed Mini and then Real Verify, always against the original result producer rather than the verifier. For `mini_real`, Mini PASS is provisional; Ending Real updates the same producer run, recomputes/persists `best_pair`, and returns `routing_learning` without a decorative Luna controller call;
- remote/status/hash proof when publishing was explicitly authorized;
- no-op inventory when a planned branch has nothing relevant to change.

Dispatch independent purposes as sibling background workers when callable. Report each worker's name/id, model, effort, bounded purpose, and running/completed state. An Ending worker:

- executes its bounded purpose directly;
- does not restart `task-analyze-skill` or `workflow-skill`;
- does not spawn nested Ending workers;
- does not change the already-delivered core result silently;
- reports checked sources and remaining items when blocked or no-op.

Prefix bounded downstream model-runner prompts with `LOCKED_ROUTE_NODE`. Explicitly label Ending prompts as direct bounded workers. These markers prevent the always-loaded global entry rule from recursively starting a new Task Analyze inside an already-routed node.

If an Ending correctness check fails, notify the user and reopen the task. The first result remains honestly labeled as Mini-verified; do not conceal the later failure.

When subagent tools are unavailable or higher-priority policy forbids dispatch, report `Ending Task blocked: no background worker` with the concrete reason. Do not fake delegation.

## Runtime Receipt Gate

When the plan requires proof of model routing, use the [runtime receipt contract](../task-analyze-skill/references/runtime-receipts.md) owned by `task-analyze-skill`.

- Requested model/effort must match resolved/effective runtime metadata or an explicitly allowed recorded reroute.
- Record tokens and elapsed time without storing raw prompts, responses, auth data, environment, or rate-limit details.
- Do not add cached input to input tokens again or reasoning output to output tokens again.
- Do not claim savings without a like-for-like baseline.
- For parallel work, compare critical-path elapsed time rather than summing branch durations.

## Generated File Placement

Put task scratch data, logs, previews, receipts, and caches in the active task/project `cache/` or `work/` area. Put final user-facing deliverables only in the requested location or active workspace `outputs/`. Do not scatter generated artifacts across Desktop or unrelated home folders.

## Safety And Authorization

Task routing never broadens permission. Before the affected action, obtain required user input or authorization for credentials, destructive changes, public publishing, external messages, profile switches, payments, private data, production actions, or irreversible operations. These are preconditions, not Ending verification.

## Representative Routes

- Direct answer/read: Task Analyze text route -> Workflow direct node -> lightweight Mini Verify -> Main Result -> relevant Ending Task.
- Active code-domain change: Task Analyze -> Workflow -> `code-skill` on an exact Spark-low-plus-normal tiny route or an exact full normal no-Spark route -> Mini Verify -> Main Result -> Real Verify in Ending Task.
- Global skill update: Task Analyze -> Workflow -> `management-skill` for authoritative scope -> `code-skill` for Python helpers -> Mini Verify -> Main Result -> Ending Real Verify/docs/memory. Push only if explicitly requested.
- Explicit optimization: Task Analyze -> Workflow result-bearing implementation -> Mini Verify -> Main Result -> separate optimization verifier in Ending Task. Report the optimization as independently verified only after that worker passes.
- UI/image/document: Task Analyze complex Mermaid route -> relevant production skill -> Mini Verify -> Main Result -> rendered/realistic review in Ending Task.

## Verification

After editing this skill:

1. Run `python3 scripts/validate_workflow_skill.py`.
2. Run the `task-analyze-skill` validator and tests.
3. Replay one easy text route and one complex Mermaid route.
4. Replay Python/C# routing through `code-skill`, including exact Spark-low-plus-normal tiny routing and exact full normal no-Spark routing for every non-tiny case.
5. Confirm the Main Result depends on Mini Verify only and every Real Verify/optimization-verification node is downstream of Main Result.
6. Capture runtime receipts for major model-routing changes.

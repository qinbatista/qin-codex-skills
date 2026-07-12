---
name: workflow-skill
description: "Execute only a Task Analyze route that was explicitly activated and passed end-to-end performance admission. Ordinary requests stay inline regardless of apparent complexity and must not load Workflow."
---

# Workflow Skill

Use this only after full `task-analyze-skill` has been explicitly activated and returned an admitted locked route. Ordinary inline work never enters Workflow. Continue in the same task. Do not wait for a lifecycle hook, and never print the private machine plan.

## Admission Gate

Before any child launch, confirm that Task Analyze supplied comparable end-to-end admission evidence:

- direct and Global cohorts share prompt/inputs, cwd, sandbox, user/project configuration, output contract, and acceptance;
- the complete Global foreground path includes entry/controller plus child costs;
- correctness passes and Global uses fewer total tokens and less critical-path time;
- the selected pair is frozen, receipt-backed, Real-passing, and `trial=false`;
- evidence is current, complete, and workload-comparable.

If any item is missing, stale, cross-workload, incomplete, or negative, reject delegation and return to inline execution. Producer-only savings are insufficient. Workflow never runs a foreground downgrade/upgrade trial.

## Authority

The current entry model may execute inline or coordinate admitted work; it is not controller-only. Workflow receives an exact model and effort for each delegated node and must not silently substitute another pair.

Every delegated model node needs a matching sanitized receipt. A route label is planned only until runtime metadata proves requested, resolved, effective pair, and completion. Tool-only/local inline work uses observable state rather than a fabricated receipt.

## Locked Plan Gate

Before side effects, confirm installed owning skills, exact pairs, dependencies, inputs, outputs, stop conditions, Main Result, and post-result Real Verify. Every active registry-owned code-domain node loads `code-skill` when delegated.

Reject once to inline execution when the route invents a skill, breaks dependencies, omits a pair, bypasses `code-skill`, puts Ending work before Main Result, or lacks end-to-end performance admission.

Task Analyze owns route display only for admitted work:

- one admitted node: concise human text;
- complex admitted graph: task-specific Mermaid plus `Workflow with models`.

Workflow reports only an actual fallback or post-result repair. It never adds a pre-result route to ordinary inline work.

## Inline Boundary

Ordinary tasks of any apparent complexity, uncalibrated profiles, and any task without positive admission remain inline on the current model. The always-loaded bootstrap does not load Workflow, call `adaptive_model_runner.py`, create a child receipt, or launch foreground verification.

Inline work uses one direct task action or direct execution surface, then shows the completed main result immediately. Ending Real Verify starts only afterward.

## Admitted Execution

1. Execute only dependency-ready nodes. Parallelize safe independent branches; keep ordered, shared-state, irreversible, or output-dependent work sequential.
2. Load each owning skill and only task-relevant references. Preserve user work and the smallest source allowlist.
3. Use one execution surface per branch. Collaboration prompts start `LOCKED_ROUTE_NODE`; do not repeat that branch in a dispatcher.
4. One admitted producer runs once through `adaptive_model_runner.py --emit-result` with its frozen pair and emits the completed result without a foreground gate.
5. Only a real graph with at least two model-executed nodes saves private schema-2 JSON and calls `task_route_dispatcher.py run-plan <plan-file>` once.
6. Respect authority. Do not push, publish, deploy, message, switch profiles, or perform irreversible work without user authorization.

The adaptive producer rechecks the frozen recommendation before execution. A failed launch is operational evidence and may not be replaced by an unreceipted or fixed-pair child. Explicit benchmark baselines remain outside entry context.

## First Result Before Verification

Do not run Mini/Fast Verify before the user first sees the result. When requested work is complete:

1. cross Main Goal Done Gate based on task completion, not a verification claim;
2. show the main result immediately;
3. only after it is shown, release the Ending Real handoff.

For adaptive or dispatched execution, launch the CLI as an ongoing session and read its newline-delimited `stage=result-ready` event. That event is emitted only after the public result path has been atomically written. Read and show that file immediately while the receipt/session continues; then collect the final receipt/manifest. A post-presentation receipt or protocol failure must notify and reopen instead of retracting or silently replacing the presented result.

For a dispatcher use ongoing `run-plan` session -> `result-ready` event -> show the public result file -> collect final run manifest -> `release-main-result` -> `run-ending`. Never wait for the final receipt manifest before showing an emitted result. Never call `release-main-result` until the result has actually been shown and the final run manifest passes. A later Real correctness failure notifies the user, reopens, repairs, and explicitly presents the corrected result without inserting a new foreground Mini.

## Ending Task

Ending Task begins only after the main result. It owns the single proportional Real Verify plus any genuinely needed broader regression, visual replay, independent optimization verification, reports, logs, docs, and sanitized learning. Missing memory is a successful no-op.

An Ending worker starts `ENDING_TASK_WORKER` or `LOCKED_ROUTE_NODE`, never restarts Task Analyze/Workflow, and never silently changes the delivered result. Do not run Ending merely to fill one final response.

## Runtime Receipt And Learning

Use runtime receipts only for delegated model nodes, explicit routing proof, or benchmarking. A timeout remains a failure with elapsed time and partial token lower bounds.

`model_routing_history.py record` handles quality/model learning only after Ending Real on the same route-run ID and producer attempt. Operational failures are neutral. End-to-end admission is separate: it must compare the complete Global path against current-model direct execution for the same cohort before future delegation.

Savings claims count every session once and test simple, medium, and complex separately. User-visible latency ends at the first completed result; Ending Real time is separate. A suite total never converts a losing class into a pass.

## Prompt And Code Rules

Delegated code nodes retain `code-skill`; Spark-low is only for eligible tiny profiles in an explicit benchmark or admitted route. Local execution does not fabricate model metadata.

## Files And Verification

Put plans, receipts, logs, and temporary outputs in active task `cache/` or `work/`; final deliverables go only to the requested location. After editing Workflow, run `scripts/validate_workflow_skill.py`, Task Analyze validators/tests, one inline contract check, and one admitted complex route check. Confirm no ordinary task loads Workflow, Main Result depends only on requested work, and Real Verify begins after presentation.

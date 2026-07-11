---
name: workflow-skill
description: "Execute the locked task-analyze-skill route. Preserve each downstream model and effort, run the proportional Mini Verify, release the main result first, then hand related deeper checks and learning to Ending Task."
---

# Workflow Skill

Use this only after `task-analyze-skill`, the 100%-trigger individual entry skill, has shown a locked route. Continue in the same task. Do not wait for a lifecycle hook and never print the private machine plan.

## Authority

The observable entry model and effort belong only to Task Analyze and route coordination. Workflow receives an explicit model and effort for every downstream node and must not silently inherit the entry selection. It executes the shown topology; it does not redraw the route or silently select a different major model.

Every model-executed node needs a matching sanitized receipt. A diagram label is planned only until runtime metadata proves requested, resolved, effective model, effort, and completion. Tool-only actions use observable state instead of a fabricated model receipt.

## Locked Plan Gate

Before side effects, confirm the route has installed owning skills, exact model/effort pairs, dependencies, inputs, outputs, stop conditions, Mini Verify, Main Result, and post-result Ending Task. Every active registry-owned code-domain node loads `code-skill`. Reject one time to Task Analyze when the plan invents a skill, breaks dependencies, omits a required model/effort, bypasses `code-skill`, or puts Ending work before Main Result.

Task Analyze owns the display:

- Easy task: concise text explanation.
- Complex task: task-specific Mermaid plus `Workflow with models`.

Workflow reports only an actual fallback or repair; a changed route must be shown before affected work.

## One-Call Easy Path

An exact literal local read handled by Task Analyze's direct boundary never enters Workflow. It has one bounded read-only tool command, local exact Mini, no child/receipt/history sample, and no semantic inference.

For an obvious bounded source lookup, literal transform, exact schema/string check, tiny edit, or command generation:

1. Use the named profile preset locked by Task Analyze; it derives the pair and eligible tiny text/code/command work starts Spark-low.
2. Run one blocking `../task-analyze-skill/scripts/adaptive_model_runner.py --emit-result` call. It canonicalizes the installed owner, reads private experience itself, invokes the selected pair once with `LOCKED_ROUTE_NODE`, applies any named local gate, and returns the passing bounded result; Workflow and the entry may not override that pair. The stdin prompt contains the exact owning-skill path, bounded source allowlist, output contract, and self-check. A bounded read-only child passes `--ignore-user-config` and reads only that named owner instead of reloading the global entry contract. Use shell `printf '%s'` piping, never a heredoc or `/tmp`, and keep outputs in the deterministic task `cache/` path.
3. The Task Analyze core contains the complete CLI and orchestration template. Do not call help, inspect runner/history/receipt implementation, search memories/sessions for examples, allocate a PTY, use short polls, dispatch collaborators, create a plan, reread the result, or launch model verifier sessions. With `functions.exec`, set its outer yield to 60 seconds, use a 30-second initial launch, and use 55-second `write_stdin` polls without a second `functions.wait` layer. When the passing result arrives, return it once in final instead of duplicating it in commentary. One transport failure may be corrected once; a second returns the operational failure and never falls back to an unreceipted or fixed-pair child.
4. Run one local deterministic Mini Verify and show the main result immediately.
5. Leave Ending Task pending/no-op unless unresolved semantic risk remains.

This section is complete for the easy path; no routing/reference document is needed. A literal read-only source lookup also does not load code-language references or `verify-skill`; its local Mini is Workflow-owned. Receipt-backed grounded JSON uses `../task-analyze-skill/scripts/grounded_result_gate.py` and never a custom source-analysis probe before result release. The entry never reads the task source or substitutes itself for the selected producer.

## Standard Execution

Use this path when local deterministic proof is insufficient.

1. Execute only dependency-ready nodes. Parallelize safe independent work; keep ordered, shared-state, irreversible, or output-dependent work sequential.
2. Load each owning skill and only task-relevant references. Preserve user work and the smallest source allowlist.
3. Use exactly one execution surface for each branch. Collaboration prompts begin `LOCKED_ROUTE_NODE`; a collaboration branch is not repeated in a dispatcher plan. Grounded read-only answers use one producer unless branch allowlists are pairwise disjoint and the merge reads only dependency results.
4. Direct model nodes use `model_execution_receipt.py run`. A complex label alone does not justify dispatch: one result producer plus local Mini stays direct. Only a real graph with at least two model-executed result/verification nodes saves schema-1 JSON privately and calls `task_route_dispatcher.py run-plan <plan-file>` once. Never inspect dispatcher source or fixtures to construct the plan.
5. New plans normally set `first_result_timeout_seconds` to 180 for easy and 600 for complex. Deadline exhaustion stops new nodes/fallbacks while preserving partial evidence. Mini failure permits at most one bounded foreground repair.
6. Respect authority. Do not push, publish, deploy, message, switch profiles, or perform irreversible work unless explicitly authorized.

Every non-dispatched adaptive result producer uses `adaptive_model_runner.py`; it calls recommendation logic before execution so neither Task Analyze nor Workflow can skip experience. A dispatcher result producer recomputes the current learner recommendation immediately before execution and must match the locked pair, trial flag, fingerprint, and proof fields. When its grounded local gate is configured, it calls `model_routing_history.py record` for the same receipt and route-run ID after Mini. Other Mini gates call `model_routing_history.py record` themselves: it records after Mini and updates after Real using the same route-run ID and same producer attempt. Dispatcher routes do this internally. Operational failures are neutral; correctness evidence determines routing eligibility. Direct fixed-pair benchmark baselines still use `model_execution_receipt.py` outside entry context.

The entry receipt installs an inherited entry-context marker. Inside it, direct fixed or forged result-producer receipts are rejected; the role requires either adaptive-runner authorization or distinct dispatcher authorization backed by a freshly matched learner recommendation. Dispatcher verification, repair, and ending roles use their own matching in-process authorization. A failed adaptive launch returns an operational failure and may not be replaced by a fixed producer.

## Mini Verify And First Result

Mini Verify is the basic proportional result gate for every task. It is the smallest meaningful check that requested work exists and is basically ready: exact comparison, parse, schema, syntax, compile, existence, focused input/output, or basic render as appropriate.

When requested work and Mini pass:

1. cross Main Goal Done Gate;
2. show the main result immediately;
3. only after it is shown, release the Ending handoff.

For dispatcher work the order is `run-plan` -> read Mini-passed result -> show result -> `release-main-result` -> `run-ending`. A nested surface that buffers output must return the Mini-passed result with Ending pending instead of synchronously hiding it behind Real work. Inside an entry-task receipt process, any Ending worker, Real verifier, or post-Real repair before return is a routing failure. A later correctness failure reopens the task, repairs, reruns Mini, and presents the corrected result.

## Ending Task

Ending Task starts after the main result. It owns only related Real Verify, broader regressions, realistic or visual replay, independent optimization verification, reports, logs, docs, and sanitized memory/routing learning. Optimization is certified by a different receipt-backed verifier. Missing memory is a successful no-op.

Bounded Ending workers begin `ENDING_TASK_WORKER` or `LOCKED_ROUTE_NODE`, do not restart Task Analyze/Workflow, do not spawn nested Ending workers, and never silently change the delivered result. If no background surface exists, return the result with an honest pending/block reason.

## Runtime Receipt Gate

Use the receipt contract in `../task-analyze-skill/references/runtime-receipts.md` only when routing proof or benchmarking is required. A timeout receipt keeps elapsed time and partial token lower bounds and remains a failure.

Savings claims require identical prompt, cwd, configuration, output contract, and acceptance. The fair direct baseline keeps user configuration and bypasses only Task Analyze using `LOCKED_ROUTE_NODE` on the entry pair. Count each unique entry, collaboration, dispatcher, retry, and Ending session once. Report Mini-passed first-result tokens/time separately from Ending; use critical-path time for parallel branches.

## Prompt And Code Rules

Prompt changes show `Prompt idea -> Prompt goal -> Problems -> Solution`, merge the smallest complete rule, and receive representative Mini proof. Code nodes retain `code-skill`; Spark-low is only for eligible tiny work, while every non-tiny route uses the full Luna-to-Sol ladder with no Spark. Local execution does not remove the planned model/effort owner.

## Files And Verification

Put plans, receipts, logs, and temporary outputs in the active task `cache/` or `work/`; final deliverables go only to the requested location. After editing this skill, run `scripts/validate_workflow_skill.py`, the Task Analyze validators/tests, one easy route, and one complex route. Confirm Main Result depends only on Mini and all Real/optimization checks follow it.

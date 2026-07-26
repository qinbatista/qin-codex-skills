---
name: workflow-skill
description: "Execute one Obsidian-context producer or a dynamically scored dependency graph. Every task still launches the mandatory post-result Ending lifecycle."
---

# Workflow Skill

Use result-producing Workflow for one Obsidian-context adaptive quality producer with a one-rung-stronger operational fallback, or after full `task-analyze-skill` returns a dynamically scored locked multi-node route. Ineligible ordinary work remains inline, and every task uses the universal Ending lifecycle after presentation. Continue in the same task; no hook is used; never print the private machine plan.

## Graph And Claim Gates

Admit a task graph when at least two bounded result segments have distinct owners, outputs, model needs, or safe dependency-ready concurrency. Each node must carry its own 0-100 score, band, exact model/effort, purpose, dependencies, sandbox, and stop condition. Do not split one dependency-coupled implementation by file count alone.

Before making a savings claim, confirm that Task Analyze supplied comparable end-to-end evidence:

- direct and Global cohorts share prompt/inputs, cwd, sandbox, user/project configuration, output contract, and acceptance;
- public evidence compares exactly Direct task versus Auto task, then Direct task versus Auto task + Ending; entry/controller cost is a disclosed but excluded routing diagnostic;
- correctness passes and Global uses fewer total tokens and less critical-path time;
- the selected pair is frozen, receipt-backed, Real-passing, and `trial=false`;
- evidence is current, complete, and workload-comparable.

If any performance item is missing, stale, cross-workload, incomplete, or negative, reject the savings claim, not a structurally valid task graph. Independent read-only sources keep their byte-cost admission and disjoint merge rules. Writable nodes must have non-overlapping ownership to run concurrently; shared files, mutable state, or output dependencies stay ordered. The generated shared ladder plus matching Obsidian broad `Model Switch.md` context still admits one ordinary producer at cold start, one-rung downgrade/upgrade trial, or frozen reuse; missing Obsidian uses the shared cold start without learning and never blocks.

## Authority

The current entry model may execute inline or coordinate admitted work; it is not controller-only. Workflow receives an exact model and effort for each delegated node and must not silently substitute another pair.

Every delegated model node needs a matching sanitized receipt. A route label is planned only until runtime metadata proves requested, resolved, effective pair, and completion. Tool-only/local inline work uses observable state rather than a fabricated receipt.

## Locked Plan Gate

Before side effects, confirm installed owning skills, exact pairs, dependencies, inputs, outputs, stop conditions, Main Result, and post-result Real Verify. Every active registry-owned code-domain node loads `code-skill` when delegated.

Reject once to inline execution when the route invents a skill, breaks dependencies, omits a node score/band/pair, bypasses `code-skill`, arbitrarily splits shared state, or puts Ending work before Main Result.

Task Analyze owns route display only for admitted work:

- one admitted node: concise human text;
- complex admitted graph: task-specific Mermaid plus `Workflow with models`.

Workflow reports only an actual fallback or post-result repair. It never adds a pre-result route to ordinary inline work.

## Inline Boundary

Eligible single-node production tasks get one project/task/module/file/symbol/code lookup and call `obsidian_adaptive_model_runner.py` once, including cold start. A multi-node request instead materializes one `dynamic_task_graph` and calls the dispatcher once. The parent score never forces all nodes onto one pair. Spark-low is first for every eligible low-risk, low-ambiguity text/code/write/execute node scoring 0-24, including downstream nodes inside a complex graph; a concrete exception is required when it is unsuitable.

Inline work uses one direct task action or direct execution surface, then shows the completed main result immediately. Ending Real Verify starts only afterward.

## Admitted Execution

1. Execute only dependency-ready nodes. Parallelize safe independent branches; keep ordered, shared-state, irreversible, or output-dependent work sequential.
2. Require each result and Ending node to retain its own score, band, selected pair, selection basis, purpose, dependencies, and stop condition in its receipt. Load each owning skill and only task-relevant references.
3. Use one execution surface per branch. Collaboration prompts start `LOCKED_ROUTE_NODE`; do not repeat that branch in a dispatcher.
4. One admitted producer runs through `obsidian_adaptive_model_runner.py --emit-result`; ordinary text/code starts on its contextual quality pair. One Real PASS retains the pair, two Real PASS results trial one rung down, and quality FAIL upgrades one rung. Code completion includes one bounded Quick Check before presentation, never a separate verifier.
5. Only a real graph with at least two model-executed result nodes saves private schema-2 `dynamic_task_graph` JSON and calls `task_route_dispatcher.py run-plan <plan-file>` once. Independent writable nodes declare non-overlapping outputs; any shared target introduces an explicit dependency. Read-only source graphs additionally retain disjoint allowlists and dependency-only-or-fused merge rules.
6. Respect authority. Do not push, publish, deploy, message, switch profiles, or perform irreversible work without user authorization.

The adaptive producer reads the saved shared contract unchanged and checks the matching Obsidian project context before execution. Ordinary tasks do not scan or refresh the local model cache. Only an explicit user model-update request may refresh the shared contract from local `models_cache.json`; never fetch models over the network, and preserve the saved contract when the local cache is unavailable. It never writes learning. Selected-pair launch/access/transport failure can use one stronger quality pair only before any published result and with zero tokens; all attempts stay in one route receipt. Explicit benchmark baselines remain outside entry context.

## Quick Check, First Result, Then Detached Ending

When requested work is complete:

1. cross Main Goal Done Gate based on task completion, not an independent verification claim;
2. for code, run the smallest safe local smoke, or skip a heavy/API/large-file path and check syntax plus changed function, variable, import, and direct-reference names;
3. show `CODE READY` or `MAIN RESULT READY` immediately with Quick Check PASS/SKIPPED evidence;
4. release the Ending Real handoff; when `create_thread` is callable, create a global projectless Codex task with target `{"type":"projectless"}`, rename it exactly `End Task-{concise related task name}`, link it, and return without waiting. Pass absolute project paths in its prompt and never attach it to the source project. If thread tools are unavailable, return the completed result and exact handoff immediately so the outer host creates the End Task; never inspect app-server schemas/commands, emulate task creation, poll, or self-run Ending.

## Result Model Disclosure

Every user-facing origin result and each result/Ending node includes `Complexity: <int>/100 (<band>)`, `Current model: <model> | <effort>`, `Model pairs (requested / resolved / effective): requested=<model>|<effort> -> resolved=<model>|<effort> -> effective=<model>|<effort>` (or `effective=UNVERIFIED (no runtime receipt)`), `Previous model: <model | effort|none|unverified>`, `Route change: upgrade|downgrade|freeze|no_switch|operational_fallback`, and `Reason:` in 20 words or fewer. `Current model` is actual user-visible execution; planned labels are not effective proof. Inline uses verified entry metadata or `unverified`, never guesses. A no-switch result includes every field.

For adaptive or dispatched execution, launch the CLI as an ongoing session and read its newline-delimited `stage=result-ready` event. That event is emitted only after the public result path has been atomically written. Read and show that file immediately while the receipt/session continues; then collect the final receipt/manifest. A post-presentation receipt or protocol failure must notify and reopen instead of retracting or silently replacing the presented result.

For a dispatcher use ongoing `run-plan` session -> `result-ready` event -> bounded Quick Check when code -> show the public result file -> collect final run manifest -> `release-main-result` -> create/rename/link End Task when thread tools are callable, or emit its handoff when they are absent -> origin returns. Only the End Task thread may call `run-ending`. Never use a same-task Ending subagent or wait for the Ending verdict in the origin. A later Real correctness failure is owned and reported by the End Task thread.

## Mandatory Ending Task

Ending begins only after the main result and is mandatory. For verification-needed results, build `ending_verification_plan.py` and create one persistent `End Task-{task}-{check}` per independent real unit/integration/API/build/render/state check. Each check has its own `0-100` score and quality-ladder model/effort; all required checks must PASS. The result-producing surface creates tasks only when thread tools are callable; otherwise it emits BLOCKED handoffs for the outer host. Start the local lifecycle with score, plan, and `--producer-receipt` when present.

The End Task thread starts its worker prompt with `ENDING_TASK_WORKER`; any locked-route metadata follows that marker. It never restarts Task Analyze/Workflow, silently changes the delivered result, asks the user to resolve external state, or waits/polls. A concurrent state change records terminal `BLOCKED` and exits. The origin returns after creating and linking the thread with its result complete. After a durable lifecycle PASS, the worker calls `set_thread_archived(archived=true)` on itself; an accepted archive may terminate the turn. FAIL/BLOCKED remains unarchived; unavailable PASS cleanup returns explicit BLOCKED.

Do not run broad verification before the user first sees the result; show the main result after Quick Check. Ending bypasses result-producing performance admission. The Ending worker starts with `ENDING_TASK_WORKER` and runs its assigned real check. PASS requires the expected observable result. FAIL records exact command/output/error and creates a separate repair task; the repaired result gets a fresh Ending task. Continue for up to three repairs. BLOCKED never counts as verified.

On real-check failure, persist terminal FAIL evidence and emit the repair handoff automatically. Only unavailable infrastructure, external state, timeout, or exhausted repairs is BLOCKED.

## Runtime Receipt And Learning

Use runtime receipts only for delegated model nodes, explicit routing proof, or benchmarking. A timeout remains a failure with elapsed time and partial token lower bounds.

`obsidian_adaptive_model_runner.py` reads the shared contract and matching project/task/module/file/symbol/code experience but never writes learning. It embeds a sanitized learning context in the private receipt. Ending Real's terminal ledger event writes the effective producer result and initial-attempt evidence to Obsidian automatically. The broad `Model Switch.md` page is the sole current contextual experience authority. Operational failures are quality-neutral. End-to-end performance admission remains separate.

Savings claims count every session once and test simple, medium, and complex separately. User-visible latency includes any required producer Quick Check and ends at completed-result presentation; detached Ending Real time is separate. A scheduled graph reports every branch and merge pair/token/time, not only its merge. A suite total never converts a losing class into a pass.

## Prompt And Code Rules

Delegated code nodes retain `code-skill`. Eligible small low-risk code, write, command, probe, transform, and execute segments use the catalog Spark priority producer from their node score, regardless of parent score; other production executes its score role or saved contextual quality pair. Ending verifiers use score-derived quality pairs, never Spark. Local execution does not fabricate producer metadata.

## Files And Verification

Put plans, receipts, logs, and temporary outputs in active task `cache/` or `work/`; final deliverables go only to the requested location. After editing Workflow, run `scripts/validate_workflow_skill.py`, Task Analyze validators/tests, one single-node contract check, and real sequential, parallel, and mixed graph checks. Confirm every node score/pair is receipted, only dependency-ready nodes overlap, Main Result depends transitively on every result node, and Real Verify begins after presentation.

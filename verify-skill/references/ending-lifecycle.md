# Mandatory Post-Result Ending Lifecycle

A low-risk single-result small task (`0-24`) records `intentionally_skipped_simple_task` and does not create an Ending. Code/file edits, bug fixes, generated artifacts, UI/render work, integrations, external actions, standard/complex/advanced work, and any medium/high-risk or multi-stage task are Ending-required: the producer emits `ending-required` and the parent creates one separate persistent projectless Codex task after the main result. Ending-required work executes the smallest real proportional checks; simple work never fabricates a test. The bounded personal-memory scan runs inside an Ending, but an empty candidate set remains a strict no-op for preference memory. Prior prose alone cannot PASS; a current immutable PASS report may be digest/state-checked instead of rerunning its exhaustive producer gate.

## Parent sequence

1. Complete the result and run the producer Quick Check for code.
2. Present `CODE READY` or `MAIN RESULT READY` with paths, complexity score/band, route change, and Quick Check evidence.
3. Define observable acceptance commands and the semantic acceptance statement. Use `scripts/ending_verification_plan.py plan` with one check per independent unit, integration/API, build, render/visual, or live-state surface, plus the exact immutable origin session (`thread_id`, `host_id`, project ID, and project root). Durable project-file changes also pass one sanitized `project_memory_closeout` intent; non-persistent work explicitly uses `mode=none`.
4. Give every check its own complexity score for scope and classification only. The Ending primary is always `gpt-5.3-codex-spark|xhigh`. Only an explicit model/effort/scheduler or required-modality availability failure permits the single registry-floor fallback, currently `gpt-5.6-luna|low`; test or acceptance failure never changes the Ending model.
5. Start the local lifecycle with `--verification-required --verification-plan`, score/band, the exact origin session, and `--producer-receipt` when present.
6. Resolve the exact saved project by canonical root, then create one persistent projectless `End Task-{task}` for the plan in the global task list. Preserve the project ID binding and pass all exact bounded `run-check` commands, lifecycle/receipt paths, originating project root, touched files, and repair boundary. Safe independent checks may run concurrently inside the task; shared-state checks stay ordered.
7. Link the task and return the origin without polling. Missing task creation is terminal BLOCKED and is not verification.

## Real check PASS

The one Ending worker runs `ending_verification_plan.py run-check` for every saved check. It records each real command, exit code, stdout/stderr, elapsed time, score/band, actual pair, fallback provenance, and semantic acceptance. PASS requires the expected observable result; a command that exits successfully but leaves the final artifact or state different from the original request is converted to `FAIL` with `ending_verification_plan.py mismatch --evidence ... --summary ...`. Every required check must PASS before the lifecycle final gate passes. Every terminal event writes a project-linked model record to Obsidian. A receipt-backed producer event is learning-eligible; without a receipt the known verifier assignment is an observation only and is never mislabeled as the producer. The worker then prints the ledger's structured `model_assessment`, including attempt count, first/retry pass, suitability, producer next action/pair, fixed verifier next action, and record link/status. It never calls `set_thread_archived` or deletes itself; every terminal Ending and repair handoff remains visible.

After the real check, the worker performs the personal-memory scan. It creates the project-relative candidate JSON only when a supported explicit preference, repeated correction, or verified working pattern exists; otherwise it omits the file and the ledger receives no memory write. A candidate terminal event passes that file to `ending_task_ledger.py --memory-candidates-file`, which validates and projects it through the root-first Preferences owner without changing the result.

For a durable result, the same worker separately compares three authorities: the active Skill/process contract, fresh execution evidence, and the bounded effective project-result memory. It writes `task-ending.project-memory-consistency.json` with schema version 1 and passes it through `ending_task_ledger.py event --memory-consistency-file`. This project-result flow is independent from both model-routing memory and the personal-memory candidate flow.

The consistency classifier is deterministic:

| Classification | Required evidence state | Action | Terminal status |
|---|---|---|---|
| `aligned` | process PASS, execution PASS, effective memory matches | append current verified result | PASS after effective local readback and available-vault projection readback |
| `no_prior_memory` | process PASS, execution PASS, no prior result | append current verified result | PASS after effective local readback and available-vault projection readback |
| `memory_record_defect` | process PASS, execution PASS, result memory mismatches | append a correction with `supersedes` | PASS after effective correction readback |
| `memory_projection_defect` | correct local record, missing/mismatched Obsidian projection | reconcile the same `record_id` | PASS after verified projection, or pending only when Obsidian is unavailable |
| `skill_contract_defect` | active process contract fails fresh evidence | send repair to immutable origin; Ending edits nothing | FAIL |
| `execution_drift` | process contract passes, producer execution fails it | send repair to immutable origin; do not rewrite memory | FAIL |
| `insufficient_evidence` | responsibility cannot be proven because evidence is unavailable | write nothing | BLOCKED |

Corrections are append-only and preserve the wrong event as superseded history. Reconciliation repairs projection transport without creating a second semantic result. A durable PASS requires the result record to be effective in bounded local recall. When Obsidian is available, its projection receipt must also report readback verified; if the vault is unavailable, local memory remains authoritative and the terminal record is `projection-pending` for the next bounded reconciliation. An available-but-stale projection never becomes a false PASS. On the next task, recall excludes superseded records by default, then current source and the active Skill contract remain authoritative if old history disagrees.

## Real check FAIL and repair

1. Record lifecycle FAIL with the exact failing command, exit code, stdout/stderr, failure class, stable error fingerprint, and semantic acceptance gap.
2. Use the emitted `repair_handoff.repair_dispatch` to automatically call `codex_app__send_message_to_thread` with the immutable origin `threadId`, `hostId`, and generated `repair_prompt`. Missing origin metadata or failed submission is BLOCKED.
3. The origin session reads the original request and current result, repairs only the authorized producer scope, runs Quick Check, and presents the corrected result and new producer receipt. It supplies the failed parent lifecycle ID through `ending_verification_plan.py plan --repair-of-lifecycle-id <id>` or `create-launches --repair-of-lifecycle-id <id>`; malformed IDs or conflicting plan/launch values are rejected. The resulting launch spec and worker prompt preserve that ID, and the fresh Spark-first worker must start `ending_task_ledger.py` with the exact `--repair-of-lifecycle-id <id>` before rerunning the original acceptance checks.
4. Continue source-session repair then fresh verification for at most three attempts. Never let a failing verifier repair its own target, create a replacement repair session, or claim PASS from earlier evidence.
5. If all repair attempts fail, or the source session cannot be resumed, record BLOCKED with the final exact error and attempt history. BLOCKED never counts as verified.
6. FAIL and BLOCKED Ending tasks and every repair handoff remain visible so their exact evidence and source-session chain stay auditable; nothing auto-archives or deletes itself.

## Split and model boundary

- Keep independent acceptance surfaces as explicit check records inside the one Ending so one vague summary cannot hide a failure.
- Keep the fixed fast Ending primary independent from task/check score; score only bounds the check scope and classification.
- Keep checks focused and proportional; do not run unrelated exhaustive suites.
- Order checks that share mutable state. Parallelize only independent safe checks.
- A simple conversational answer may have a score/history-only Ending record when no observable verification is applicable; never fabricate a test.

## Status

- `PASS`: all required real checks passed.
- `FAIL`: a real check found a defect and a repair handoff was created.
- `BLOCKED`: task creation, verification infrastructure, external state, timeout, or the repair limit prevented PASS.

Local lifecycle history always records the score, check, selected pair, evidence, and repair chain. Every terminal event syncs a same-ID record to the matching project Obsidian category page and refreshes its Model Switch/shared-category links; only receipt-backed producer evidence may move routing.

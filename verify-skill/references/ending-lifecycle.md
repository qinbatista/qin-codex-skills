# Mandatory Post-Result Ending Lifecycle

Ending is required when the released result exposes `real_test`, `information_update`, or `memory_update`, or is classified as a material structural, non-trivial code, conceptual, or process update. Material updates require durable project-memory closeout. Only explicit `trivial_value_only` work with no other surface may record `intentionally_skipped_simple_task` and `ending_skip_reason=no_real_test_or_information_or_memory_or_material_update`. The producer runs exactly one smallest Quick Check when the result is code and presents immediately; only after the whole result flow is settled and the final aggregate receipt is released does the parent create one persistent global projectless Ending. A child/subprocess receipt never triggers it. Spark-xhigh is the first controller; a durably recorded quota/five-hour/provider restriction temporarily selects the next stronger supported controller. Saved Terra/Sol `ENDING_CHECK_WORKER` nodes remain evidence-only.

## Parent sequence

1. Complete the result and run the producer Quick Check for code.
2. Present `CODE READY` or `MAIN RESULT READY` with paths, complexity score/band, route change, and Quick Check evidence.
3. Define observable acceptance commands and the semantic acceptance statement. Use `scripts/ending_verification_plan.py plan` with one check per independent surface. Captured origin metadata is optional immutable context and is never a repair target. Every material update passes one sanitized durable `project_memory_closeout` intent; non-persistent work explicitly uses `mode=none`.
4. Give every check its own complexity score, verification surface, execution mode, and required Skills. Spark-xhigh is first. When `create_thread` reports a real quota, five-hour limit, provider rate limit, or trusted retry-after, run `record-controller-restriction` once, regenerate `create-launches`, and use the selected stronger controller. Never retry a cooling model or create cooldown from quality failure.
5. Start the local lifecycle only with the final passing published aggregate `--producer-receipt`, which marks every result node and subprocess settled, plus `--verification-required --verification-plan` and score/band.
6. Resolve the exact saved project by canonical root only for execution/repair binding. Create one persistent global projectless `End Task-{task}` by invoking the generated `codex_app__create_thread` arguments unchanged: target exactly `{"type":"projectless"}`, with no project ID, environment, current-thread, parent-thread, or same-task-subtask attachment. Read the exact returned thread through `codex_app__list_threads`; require its project context to be null/absent, represent that as `--thread-project-id null`, then acknowledge the origin project binding separately. Any other placement is BLOCKED. Its initial prompt points to the saved plan rather than embedding it; the same task takes one bounded saved check or closeout action per continuation. Safe independent checks may run concurrently inside the task; shared-state checks stay ordered.
7. Link the task and return the origin without polling. Missing task creation is terminal BLOCKED and is not verification.

## Capability-routed check workers

- `command`, `syntax`, `unit`, `api_state`, and `file_state` checks run directly on Spark.
- `runtime_semantics`, `integration_semantics`, `code_quality`, `prompt_semantics`, `ui_visual`, and `artifact_visual` checks use the plan's Terra/Sol `ENDING_CHECK_WORKER` pair.
- A check worker begins with `ENDING_CHECK_WORKER`, reads every listed Skill, executes exactly one saved check, writes fresh evidence under Cache, and exits. It never edits producer files, launches routing or another Ending, records terminal lifecycle, or repairs.
- The controller accepts only the assigned evidence file and owns PASS/FAIL/BLOCKED. It creates any repair as a fresh independent global projectless session and never contacts the immutable origin.

## Real check PASS

The Spark controller runs every direct check and launches only saved dependency-ready check workers for delegated checks. Each path uses `ending_verification_plan.py run-check` and records the real command, exit code, stdout/stderr, elapsed time, score/band, controller pair, optional worker pair, and semantic acceptance. PASS requires every fresh evidence file; worker prose alone is invalid. The controller owns one terminal event and never edits the producer result.

After the real check, the worker performs the personal-memory scan. It creates the project-relative candidate JSON only when a supported explicit preference, repeated correction, or verified working pattern exists; otherwise it omits the file and the ledger receives no memory write. A candidate terminal event passes that file to `ending_task_ledger.py --memory-candidates-file`, which validates and projects it through the root-first Preferences owner without changing the result.

For a durable result, the same worker separately compares three authorities: the active Skill/process contract, fresh execution evidence, and the bounded effective project-result memory. It writes `task-ending.project-memory-consistency.json` with schema version 1 and passes it through `ending_task_ledger.py event --memory-consistency-file`. This project-result flow is independent from both model-routing memory and the personal-memory candidate flow.

The consistency classifier is deterministic:

| Classification | Required evidence state | Action | Terminal status |
|---|---|---|---|
| `aligned` | process PASS, execution PASS, effective memory matches | append current verified result | PASS after effective local readback and available-vault projection readback |
| `no_prior_memory` | process PASS, execution PASS, no prior result | append current verified result | PASS after effective local readback and available-vault projection readback |
| `memory_record_defect` | process PASS, execution PASS, result memory mismatches | append a correction with `supersedes` | PASS after effective correction readback |
| `memory_projection_defect` | correct local record, missing/mismatched Obsidian projection | reconcile the same `record_id` | PASS after verified projection, or pending only when Obsidian is unavailable |
| `skill_contract_defect` | active process contract fails fresh evidence | create isolated Repair Task; Ending edits nothing | FAIL |
| `execution_drift` | process contract passes, producer execution fails it | create isolated Repair Task; do not rewrite memory | FAIL |
| `insufficient_evidence` | responsibility cannot be proven because evidence is unavailable | write nothing | BLOCKED |

Corrections are append-only and preserve the wrong event as superseded history. Reconciliation repairs projection transport without creating a second semantic result. A durable PASS requires the result record to be effective in bounded local recall. When Obsidian is available, its projection receipt must also report readback verified; if the vault is unavailable, local memory remains authoritative and the terminal record is `projection-pending` for the next bounded reconciliation. An available-but-stale projection never becomes a false PASS. On the next task, recall excludes superseded records by default, then current source and the active Skill contract remain authoritative if old history disagrees.

## Real check FAIL and repair

1. Record lifecycle FAIL with the exact failing command, exit code, stdout/stderr, failure class, stable error fingerprint, and semantic acceptance gap.
2. Use `repair_handoff.repair_launch` to call `codex_app__create_thread` with exact projectless target. The request contains no existing `threadId`/`hostId`, and its prompt forbids send, steer, interrupt, terminate, handoff, move, or mutation of every existing task/session.
3. The independent Repair checks ownership read-only. If an active task owns a required write surface, it records `waiting_for_active_task_release` and waits without messaging or interruption. After release it repairs only the authorized scope, runs Quick Check, presents the corrected result and new producer receipt, and supplies the failed parent lifecycle ID through `--repair-of-lifecycle-id <id>` for a fresh Ending.
4. Continue isolated repair then fresh verification for at most three attempts. Never let the failing verifier repair its own target or reuse earlier evidence.
5. If all attempts fail or external state is unavailable, record BLOCKED with exact history. Active-task ownership remains WAITING and never authorizes interruption.
6. FAIL/BLOCKED Endings and every Repair Task remain visible; nothing auto-archives or deletes itself.

## Split and model boundary

- Keep independent acceptance surfaces as explicit check records inside the one Ending so one vague summary cannot hide a failure.
- Keep controller selection independent from task/check score: Spark first, restriction-aware stronger fallback only while cooling; score and surface may select only a bounded check-worker pair.
- Keep checks focused and proportional; do not run unrelated exhaustive suites.
- Order checks that share mutable state. Parallelize only independent safe checks.
- A simple conversational answer with no observable test, information, or memory surface skips Ending; record `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_or_material_update` and never fabricate a test.

## Status

- `PASS`: all required real checks passed.
- `FAIL`: a real check found a defect and a repair handoff was created.
- `BLOCKED`: task creation, verification infrastructure, external state, timeout, or the repair limit prevented PASS.

Local lifecycle history always records the score, check, selected pair, evidence, and repair chain. Every terminal event syncs a same-ID record to the matching project Obsidian category page and refreshes its Model Switch/shared-category links; only receipt-backed producer evidence may move routing.

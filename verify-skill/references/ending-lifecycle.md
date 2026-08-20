# Mandatory Post-Result Ending Lifecycle

Ending is required only when the released result exposes `real_test`, `information_update`, or `memory_update`. A no-surface result records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update`; score, risk, stage count, or prose complexity cannot manufacture an Ending. The producer runs exactly one smallest Quick Check when the result is code and presents immediately; only after the whole result flow is settled and the final aggregate receipt is released does the parent create one persistent global projectless Ending. A child/subprocess receipt never triggers it. Its fixed Spark-xhigh controller runs direct checks and may use saved Terra/Sol `ENDING_CHECK_WORKER` nodes for semantic runtime, integration, code-quality, prompt, UI, or visual evidence. Prior prose cannot PASS; a current immutable PASS report may be digest/state-checked.

## Parent sequence

1. Complete the result and run the producer Quick Check for code.
2. Present `CODE READY` or `MAIN RESULT READY` with paths, complexity score/band, route change, and Quick Check evidence.
3. Define observable acceptance commands and the semantic acceptance statement. Use `scripts/ending_verification_plan.py plan` with one check per independent unit, integration/API, build, render/visual, or live-state surface, plus the exact immutable origin session (`thread_id`, `host_id`, project ID, and project root). Durable project-file changes also pass one sanitized `project_memory_closeout` intent; non-persistent work explicitly uses `mode=none`.
4. Give every check its own complexity score, verification surface, execution mode, and required Skills. The Ending controller is always `gpt-5.3-codex-spark|xhigh`; only controller availability permits registry-floor Luna-low. Direct deterministic checks stay on Spark, while semantic checks may use the plan-saved Terra/Sol check-worker pair.
5. Start the local lifecycle only with the final passing published aggregate `--producer-receipt`, which marks every result node and subprocess settled, plus `--verification-required --verification-plan`, score/band, and the exact origin session.
6. Resolve the exact saved project by canonical root only for execution/repair binding. Create one persistent global projectless `End Task-{task}` by invoking the generated `codex_app__create_thread` arguments unchanged: target exactly `{"type":"projectless"}`, with no project ID, environment, current-thread, parent-thread, or same-task-subtask attachment. Read the exact returned thread through `codex_app__list_threads`; require its project context to be null/absent, represent that as `--thread-project-id null`, then acknowledge the origin project binding separately. Any other placement is BLOCKED. Its initial prompt points to the saved plan rather than embedding it; the same task takes one bounded saved check or closeout action per continuation. Safe independent checks may run concurrently inside the task; shared-state checks stay ordered.
7. Link the task and return the origin without polling. Missing task creation is terminal BLOCKED and is not verification.

## Capability-routed check workers

- `command`, `syntax`, `unit`, `api_state`, and `file_state` checks run directly on Spark.
- `runtime_semantics`, `integration_semantics`, `code_quality`, `prompt_semantics`, `ui_visual`, and `artifact_visual` checks use the plan's Terra/Sol `ENDING_CHECK_WORKER` pair.
- A check worker begins with `ENDING_CHECK_WORKER`, reads every listed Skill, executes exactly one saved check, writes fresh evidence under Cache, and exits. It never edits producer files, launches routing or another Ending, records terminal lifecycle, or repairs.
- The Spark controller accepts only the assigned evidence file, owns PASS/FAIL/BLOCKED, and sends any repair to the immutable origin.

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
| `skill_contract_defect` | active process contract fails fresh evidence | send repair to immutable origin; Ending edits nothing | FAIL |
| `execution_drift` | process contract passes, producer execution fails it | send repair to immutable origin; do not rewrite memory | FAIL |
| `insufficient_evidence` | responsibility cannot be proven because evidence is unavailable | write nothing | BLOCKED |

Corrections are append-only and preserve the wrong event as superseded history. Reconciliation repairs projection transport without creating a second semantic result. A durable PASS requires the result record to be effective in bounded local recall. When Obsidian is available, its projection receipt must also report readback verified; if the vault is unavailable, local memory remains authoritative and the terminal record is `projection-pending` for the next bounded reconciliation. An available-but-stale projection never becomes a false PASS. On the next task, recall excludes superseded records by default, then current source and the active Skill contract remain authoritative if old history disagrees.

## Real check FAIL and repair

1. Record lifecycle FAIL with the exact failing command, exit code, stdout/stderr, failure class, stable error fingerprint, and semantic acceptance gap.
2. Use the emitted `repair_handoff.repair_dispatch` to automatically call `codex_app__send_message_to_thread` with the immutable origin `threadId`, `hostId`, and generated `repair_prompt`. Missing origin metadata or failed submission is BLOCKED.
3. The origin session reads the original request and current result, repairs only the authorized producer scope, runs Quick Check, and presents the corrected result and new producer receipt. It supplies the failed parent lifecycle ID through `ending_verification_plan.py plan --repair-of-lifecycle-id <id>` or `create-launches --repair-of-lifecycle-id <id>`; malformed IDs or conflicting plan/launch values are rejected. The resulting launch spec and worker prompt preserve that ID, and the fresh Spark-first worker must start `ending_task_ledger.py` with the exact `--repair-of-lifecycle-id <id>` before rerunning the original acceptance checks. If a later independent release check discovers a mismatch after an earlier PASS, the same linkage is allowed only with a concise `--late-repair-reason`; the ledger records `post_pass_repair_started`, so a passing lifecycle cannot be silently reused or spuriously attached.
4. Continue source-session repair then fresh verification for at most three attempts. Never let a failing verifier repair its own target, create a replacement repair session, or claim PASS from earlier evidence.
5. If all repair attempts fail, or the source session cannot be resumed, record BLOCKED with the final exact error and attempt history. BLOCKED never counts as verified.
6. FAIL and BLOCKED Ending tasks and every repair handoff remain visible so their exact evidence and source-session chain stay auditable; nothing auto-archives or deletes itself.

## Split and model boundary

- Keep independent acceptance surfaces as explicit check records inside the one Ending so one vague summary cannot hide a failure.
- Keep the fixed Spark Ending controller independent from task/check score; score and surface may select only a bounded check-worker pair.
- Keep checks focused and proportional; do not run unrelated exhaustive suites.
- Order checks that share mutable state. Parallelize only independent safe checks.
- A simple conversational answer with no observable test, information, or memory surface skips Ending; record `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update` and never fabricate a test.

## Status

- `PASS`: all required real checks passed.
- `FAIL`: a real check found a defect and a repair handoff was created.
- `BLOCKED`: task creation, verification infrastructure, external state, timeout, or the repair limit prevented PASS.

Local lifecycle history always records the score, check, selected pair, evidence, and repair chain. Every terminal event syncs a same-ID record to the matching project Obsidian category page and refreshes its Model Switch/shared-category links; only receipt-backed producer evidence may move routing.

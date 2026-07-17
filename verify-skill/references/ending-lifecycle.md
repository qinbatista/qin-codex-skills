# Mandatory Ending Lifecycle

Every user task, from a tiny read-only answer to a complex write, releases its completed main result and then creates one separate persistent Codex task for Ending. Code work first runs one bounded producer Quick Check. Ending is a <=60-second, read-only handoff audit; it is not a general regression, API, repair, or user-input worker.

## Parent sequence

1. Complete the requested result. For code, run the `code-skill` Quick Check: smallest safe local smoke for light work, or syntax/name/reference checks with the heavy path skipped.
2. Show it immediately in a user-visible commentary update beginning `CODE READY` for code or `MAIN RESULT READY` otherwise. Include the usable outcome, artifact links, Quick Check PASS/SKIPPED evidence when applicable, and `Delivery: complete — background audit starting`; a progress sentence is not a result presentation.
3. Start a lifecycle with `scripts/ending_task_ledger.py start --producer-receipt <path>` when an eligible adaptive producer ran; omit the flag only when no producer receipt exists. Require `status=written`, `local.written=true`, and the expected receipt binding.
4. Call `create_thread`, then `set_thread_title` with exactly `End Task-{concise related task name}`. Pass the lifecycle receipt, producer receipt, Quick Check evidence, absolute project/artifact paths, touched files, a read-only boundary, and origin task ID when available.
5. State `Ending mode: BACKGROUND AUDIT`, link or identify the new task, and return the origin immediately with `Delivery: complete`. Do not wait, poll, or launch a same-task subagent. The background task must finish within 60 seconds with terminal `PASS` or `BLOCKED`; it never asks the user a question.
6. If persistent task creation fails, report `Background audit unavailable`; the delivered result remains complete. Never substitute a same-task subagent.

## Audit pass

The independent auditor records `event --event pass` after checking the supplied handoff and one bounded read-only evidence item. It does not rerun tests or call APIs. With a bound producer receipt, the ledger first writes its sanitized PASS outcome to Obsidian and only then commits the terminal event; duplicate learning writes are idempotent. Ineligible inline work never fabricates a model receipt.

## Blocked audit

1. On a missing handoff, timeout, external Git/state change, or unavailable evidence, record `event --event blocked` with the concrete reason and exit immediately.
2. Do not ask the user who changed Git, wait for confirmation, poll, start broad tests, or repair.
3. The audit's `BLOCKED` is terminal and never reopens or downgrades the already-delivered main result.
4. A correctness repair requires a new explicit user request; it is a new result task with its own Mini Test and Ending audit.

## Parallel boundary

The audit is read-only and must not duplicate testing or compete for shared state. Any change to the user-visible result requires a new explicit result-producing task; no Ending repair is authorized.

## Status and waiting

- `MAIN RESULT READY` means producer completion and delivered result.
- `PASS` means the Ending handoff audit completed.
- `BLOCKED` means the audit ended because evidence was unavailable or state changed.
- Do not describe `BLOCKED` as blocking the delivered result.
- Do not narrate waits, poll unchanged state, or ask the user for confirmation. End with PASS or BLOCKED inside the 60-second budget.

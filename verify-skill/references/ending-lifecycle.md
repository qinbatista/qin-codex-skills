# Mandatory Ending Lifecycle

Every user task, from a tiny read-only answer to a complex write, releases its completed main result and then creates one separate persistent Codex task for Ending. Code work first runs one bounded producer Quick Check. `ENDING_TASK_WORKER` verification bookkeeping is non-recursive; a worker that repairs or produces a corrected artifact becomes a new repair task and must receive its own independent Ending verifier inside the End Task thread.

## Parent sequence

1. Complete the requested result. For code, run the `code-skill` Quick Check: smallest safe local smoke for light work, or syntax/name/reference checks with the heavy path skipped.
2. Show it immediately in a user-visible commentary update beginning `CODE READY` for code or `MAIN RESULT READY` otherwise. Include the usable outcome, artifact links, Quick Check PASS/SKIPPED evidence when applicable, and `Acceptance: PENDING — End Task is starting`; a progress sentence is not a result presentation.
3. Start a lifecycle with `scripts/ending_task_ledger.py start --producer-receipt <path>` when an eligible adaptive producer ran; omit the flag only when no producer receipt exists. Require `status=written`, `local.written=true`, and the expected receipt binding.
4. Call `create_thread`, then `set_thread_title` with exactly `End Task-{concise related task name}`. Pass the lifecycle receipt, producer receipt, Quick Check evidence, exact acceptance contract, absolute project/artifact paths, touched files, allowed repair scope, and origin task ID when available.
5. State `Ending mode: BACKGROUND`, link or identify the new task, and return the origin immediately with `Acceptance: PENDING`. Do not wait, poll, or launch a same-task subagent. The background task owns terminal `PASS` or `BLOCKED` reporting and any authorized repair.
6. If persistent task creation fails, report `BLOCKED: Ending task creation failed`. Never substitute a same-task subagent.

## Pass

The independent verifier records `event --event pass` with realistic evidence. With a bound producer receipt, the ledger first writes its sanitized Real PASS outcome to Obsidian and only then commits the terminal event; duplicate learning writes are idempotent. Durable project changes then receive one `project-memory-skill` passed record containing every touched file. Ineligible inline work never fabricates a model receipt.

## Failure and repair

1. Record `event --event fail --failure-class <class>` before any repair starts and show `REPAIRING` to the user. With a bound producer receipt, the ledger records the failed model outcome before committing the terminal event.
2. If failed durable changes remain, write a `project-memory-skill` record with `verification-status=failed`; otherwise keep the error only in this lifecycle ledger.
3. Notify the user in commentary and start a repair lifecycle with `start --repair-of-lifecycle-id <failed-id>`.
4. Launch one repair producer under the owning skill. The verifier does not silently self-certify its own repair, and no extra diagnostic agents are launched unless the recorded failure identifies a concrete information gap.
5. Show the corrected result immediately, then launch a different Ending verifier for the repair lifecycle.
6. A passed repair project record uses `--supersedes <failed-record-id>`. Every root ledger state stores `max_repair_attempts=3`; repair children inherit that limit. Exceeding it records lifecycle `BLOCKED` and stops further repair instead of looping silently.

## Parallel boundary

Verification and isolated bookkeeping may run concurrently only when they do not duplicate testing or compete for shared state. Final project-change memory depends on the Real verdict. Failure logging precedes repair. Repair precedes its new independent verification. Any change to the user-visible result is a new result-producing task, not bookkeeping.

## Status and waiting

- `MAIN RESULT READY` means producer completion, not acceptance.
- `PASS` means Ending accepted the result.
- `REPAIRING` means the presented candidate was rejected and bounded repair is active.
- `BLOCKED` means acceptance could not be established.
- Do not use unqualified `done` or `finished` while acceptance is pending.
- Do not narrate fixed-interval waits or repeatedly poll unchanged state. Wait on worker/status changes when the host supports it; otherwise report only meaningful state transitions.

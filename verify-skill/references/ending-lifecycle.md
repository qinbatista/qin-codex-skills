# Mandatory Ending Lifecycle

Every user task, from a tiny read-only answer to a complex write, releases its completed main result before Ending work and then starts one independent Ending lifecycle. `ENDING_TASK_WORKER` verification bookkeeping is the only non-recursive worker role; a worker that repairs or produces a corrected artifact becomes a new repair task and must receive its own independent Ending verifier.

## Parent sequence

1. Complete the requested result and show it immediately in a user-visible commentary update.
2. Start a lifecycle with `scripts/ending_task_ledger.py start`; require `status=written` and `local.written=true`.
3. Immediately spawn an independent Ending subagent. Result-producing delegation performance admission does not apply to this post-result worker.
4. Start safe non-result log, report, or documentation workers alongside verification when they have isolated outputs. Shared-state or verdict-dependent records stay ordered.
5. Keep the parent task active. Final may be sent only when `audit` reports `final_gate_passed=true`; the already-visible main result means this wait does not delay the first result.

## Pass

The independent verifier records `event --event pass` with realistic evidence. Durable project changes then receive one `project-memory-skill` passed record containing every touched file. Inline work never fabricates a model receipt; routed producer learning uses only its real receipt.

## Failure and repair

1. Record `event --event fail` before any repair starts.
2. If failed durable changes remain, write a `project-memory-skill` record with `verification-status=failed`; otherwise keep the error only in this lifecycle ledger.
3. Notify the user in commentary and start a repair lifecycle with `start --repair-of-lifecycle-id <failed-id>`.
4. Launch a repair subagent under the owning skill. The verifier does not silently self-certify its own repair.
5. Show the corrected result immediately, then launch a different Ending verifier for the repair lifecycle.
6. A passed repair project record uses `--supersedes <failed-record-id>`. Every root ledger state stores `max_repair_attempts=3`; repair children inherit that limit. Exceeding it records lifecycle `BLOCKED` and stops further repair instead of looping silently.

## Parallel boundary

Verification and isolated bookkeeping may run concurrently. Final project-change memory depends on the Real verdict. Failure logging precedes repair. Repair precedes its new independent verification. Any background change to the user-visible result is a new result-producing task, not bookkeeping.
